#!/usr/bin/env python3
"""Reaction-slot cross-attention reranker.

Stage-1 probabilities are reused from the two-stage formula Transformer run.
This file only changes Stage-2. The model is deliberately target-conditioned:
reaction slots query candidate-set element tokens under a target-derived
context, and a weak coverage reconstruction objective replaces hard coverage
rules with a learned auxiliary signal.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import gzip
import json
import logging
import os
import sys
import time
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
EXP_ROOT = PACKAGE_ROOT
PROJECT_ROOT = PACKAGE_ROOT

from .env import ExpertEnv  # noqa: E402
from .data import default_charge_path, prepare_data  # noqa: E402
from .chemistry import ChemistryPriorV2, TOTAL_FEAT_DIM  # noqa: E402
from .stage1 import (  # noqa: E402
    FormulaTransformerEncoder,
    FormulaListDataset,
    build_stage2_data,
    jsonable_args,
    load_precursor_charge_matrix,
    make_data_args,
    make_rank_cache,
)


logger = logging.getLogger(__name__)


def release_large_cache(name: str, cache) -> None:
    """Release materialized Stage-2 candidate caches as soon as they are no longer needed."""
    try:
        n = len(cache) if cache is not None else 0
    except TypeError:
        n = -1
    logger.info("Releasing %s cache from memory: samples=%s", name, n)
    del cache
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def current_rss_mb() -> float:
    """Return current process resident memory in MB without requiring psutil."""
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except OSError:
        return -1.0
    return -1.0


def peak_rss_mb() -> float:
    """Return the process high-water resident memory in MB on Linux."""
    try:
        with open("/proc/self/status", "r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("VmHWM:"):
                    return float(line.split()[1]) / 1024.0
    except OSError:
        return -1.0
    return -1.0


def cuda_memory_mb(device: str) -> tuple[float, float]:
    if not device.startswith("cuda") or not torch.cuda.is_available():
        return -1.0, -1.0
    allocated = torch.cuda.memory_allocated() / 1024.0 / 1024.0
    reserved = torch.cuda.memory_reserved() / 1024.0 / 1024.0
    return allocated, reserved


def _digest_value(value) -> str:
    h = hashlib.sha256()
    if torch.is_tensor(value):
        arr = value.detach().cpu().contiguous().numpy()
    else:
        arr = np.ascontiguousarray(value)
    h.update(str(arr.shape).encode("utf-8"))
    h.update(str(arr.dtype).encode("utf-8"))
    h.update(arr.tobytes())
    return h.hexdigest()[:16]


def _digest_batch(batch) -> str:
    h = hashlib.sha256()
    for item in batch:
        h.update(_digest_value(item).encode("utf-8"))
    return h.hexdigest()[:16]


def _digest_model(model: nn.Module) -> str:
    h = hashlib.sha256()
    for name, tensor in model.state_dict().items():
        h.update(name.encode("utf-8"))
        arr = tensor.detach().cpu().contiguous().numpy()
        h.update(str(arr.shape).encode("utf-8"))
        h.update(str(arr.dtype).encode("utf-8"))
        h.update(arr.tobytes())
    return h.hexdigest()[:16]


def configure_deterministic_training(args) -> None:
    if not args.deterministic_training:
        return
    # Must be set before CUDA matmul kernels are selected; this is best-effort
    # because the module has already imported torch but CUDA is not initialized yet.
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    if hasattr(torch.backends.cuda, "enable_flash_sdp"):
        torch.backends.cuda.enable_flash_sdp(False)
    if hasattr(torch.backends.cuda, "enable_mem_efficient_sdp"):
        torch.backends.cuda.enable_mem_efficient_sdp(False)
    if hasattr(torch.backends.cuda, "enable_math_sdp"):
        torch.backends.cuda.enable_math_sdp(True)
    torch.use_deterministic_algorithms(True, warn_only=True)


def _cuda_sdp_status() -> dict[str, object]:
    status = {}
    for name in ["flash_sdp_enabled", "mem_efficient_sdp_enabled", "math_sdp_enabled"]:
        fn = getattr(torch.backends.cuda, name, None)
        status[name] = fn() if callable(fn) else None
    return status


FEATURE_GROUPS = {
    # Base 362-d detailed features from learned_chemrank_v4.
    "prob": [0, 6, 7],  # geometric mean, max prob, min prob
    "chemrank_scalar": [1, 2, 3, 4, 5],  # kc, mc, unwanted count, perfect flag, set size
    "elem_coverage": list(range(8, 126)),
    "elem_target": list(range(126, 244)),
    "elem_unwanted": list(range(244, 362)),
    # Extra 12-d ChemistryPriorV2 features.
    "mapping_stoich": [362, 363, 364, 368, 371],  # mapping entropy, multi-source, stoich, size, overlap
    "train_prior": [365, 370],  # pair co-occurrence, precursor frequency; computed from train split only
    "train_derived": [365, 367, 370],  # train-only co-occurrence, type-rate leavability, precursor frequency
    "anion_type": [366, 367],  # type consistency, anion leavability
    "type_consistency": [366],
    "anion_leavability": [367],
    "coverage_prior": [368],  # uncovered fraction
    "chem_prob": [372, 373],  # prob gap, prob entropy
    "chem_mapping_entropy": [362],
    "chem_multi_source": [363],
    "stoich_cosine": [364],
    "cooccurrence": [365],
    "precursor_frequency": [370],
    "size_match": [369],
    "metal_overlap": [371],
    "prob_gap": [372],
    "prob_entropy": [373],
}
FEATURE_GROUPS["elem_blocks"] = (
    FEATURE_GROUPS["elem_coverage"]
    + FEATURE_GROUPS["elem_target"]
    + FEATURE_GROUPS["elem_unwanted"]
)
FEATURE_GROUPS["base_scalars"] = list(range(8))
FEATURE_GROUPS["scalars_plus_elem_coverage"] = FEATURE_GROUPS["base_scalars"] + FEATURE_GROUPS["elem_coverage"]
FEATURE_GROUPS["scalars_plus_elem_target"] = FEATURE_GROUPS["base_scalars"] + FEATURE_GROUPS["elem_target"]
FEATURE_GROUPS["scalars_plus_elem_unwanted"] = FEATURE_GROUPS["base_scalars"] + FEATURE_GROUPS["elem_unwanted"]
FEATURE_GROUPS["scalars_plus_elem_blocks"] = FEATURE_GROUPS["base_scalars"] + FEATURE_GROUPS["elem_blocks"]
FEATURE_GROUPS["base362"] = list(range(362))
FEATURE_GROUPS["chem12"] = list(range(362, 374))
FEATURE_GROUPS["chem_first6"] = list(range(362, 368))
FEATURE_GROUPS["chem_last6"] = list(range(368, 374))
FEATURE_GROUPS["chem_last_left3"] = [368, 369, 370]  # uncovered, size, precursor frequency
FEATURE_GROUPS["chem_last_right3"] = [371, 372, 373]  # overlap, probability gap/entropy
FEATURE_GROUPS["size_coverage"] = [368, 369]
FEATURE_GROUPS["size_coverage_chem_prob"] = (
    FEATURE_GROUPS["size_coverage"] + FEATURE_GROUPS["chem_prob"]
)
FEATURE_GROUPS["train_derived_plus_mapping_entropy"] = FEATURE_GROUPS["train_derived"] + [362]
FEATURE_GROUPS["train_derived_plus_multi_source"] = FEATURE_GROUPS["train_derived"] + [363]
FEATURE_GROUPS["train_derived_plus_stoich"] = FEATURE_GROUPS["train_derived"] + [364]
FEATURE_GROUPS["train_derived_plus_type_consistency"] = FEATURE_GROUPS["train_derived"] + [366]
FEATURE_GROUPS["train_derived_plus_metal_overlap"] = FEATURE_GROUPS["train_derived"] + [371]
FEATURE_GROUPS["train_derived_plus_stoich_mapping_entropy"] = FEATURE_GROUPS["train_derived"] + [364, 362]
FEATURE_GROUPS["train_derived_plus_stoich_multi_source"] = FEATURE_GROUPS["train_derived"] + [364, 363]
FEATURE_GROUPS["train_derived_plus_stoich_type_consistency"] = FEATURE_GROUPS["train_derived"] + [364, 366]
FEATURE_GROUPS["train_derived_plus_stoich_metal_overlap"] = FEATURE_GROUPS["train_derived"] + [364, 371]
FEATURE_GROUPS["all_prob"] = FEATURE_GROUPS["prob"] + FEATURE_GROUPS["chem_prob"]
FEATURE_GROUPS["cooccurrence_all_prob"] = sorted(set(
    FEATURE_GROUPS["cooccurrence"] + FEATURE_GROUPS["all_prob"]
))
FEATURE_GROUPS["cooccurrence_all_prob_size"] = sorted(set(
    FEATURE_GROUPS["cooccurrence_all_prob"] + [5, 369]
))
FEATURE_GROUPS["compact_scalars"] = sorted(set(
    FEATURE_GROUPS["base_scalars"] + FEATURE_GROUPS["chem12"]
))
FEATURE_GROUPS["coverage_semantic"] = sorted(set(
    [1, 2, 4, 368] + FEATURE_GROUPS["elem_coverage"]
))
FEATURE_GROUPS["unwanted_semantic"] = sorted(set(
    [3, 4] + FEATURE_GROUPS["elem_unwanted"]
))

# Mutually exclusive, exhaustive partition matching Appendix
# "Candidate-Set Descriptor Groups".  The hybrid is_perfect flag (index 4)
# is assigned to coverage/target overlap because its primary role is to mark
# an exact target-coverage pattern.  These six groups must cover all 374
# descriptor positions exactly once.
APPENDIX_FEATURE_GROUPS = {
    "appendix_generator_probability": [0, 6, 7, 372, 373],
    "appendix_element_coverage_target_overlap": (
        [1, 2, 4]
        + list(range(8, 126))
        + list(range(126, 244))
        + [368]
    ),
    "appendix_unwanted_element": [3] + list(range(244, 362)),
    "appendix_cooccurrence_precursor_priors": [365, 366, 367, 370],
    "appendix_stoichiometric": [5, 364, 369],
    "appendix_mapping_style": [362, 363, 371],
}
MODEL_SIDE_FEATURE_ABLATIONS = frozenset({
    "no_appendix_generator_probability",
    "no_appendix_generator_probability_descriptor_only",
})
_appendix_positions = [
    index
    for indices in APPENDIX_FEATURE_GROUPS.values()
    for index in indices
]
if sorted(_appendix_positions) != list(range(TOTAL_FEAT_DIM)):
    raise RuntimeError(
        "Appendix feature groups must partition all descriptor positions "
        f"exactly once; got {len(_appendix_positions)} assignments."
    )
FEATURE_GROUPS.update(APPENDIX_FEATURE_GROUPS)
FEATURE_GROUPS["appendix_generator_probability_descriptor_only"] = (
    APPENDIX_FEATURE_GROUPS["appendix_generator_probability"]
)

for _group in [
    "chem_first6",
    "chem_last6",
    "chem_last_left3",
    "chem_last_right3",
    "size_coverage",
    "size_coverage_chem_prob",
    "chem_mapping_entropy",
    "chem_multi_source",
    "stoich_cosine",
    "cooccurrence",
    "precursor_frequency",
    "type_consistency",
    "anion_leavability",
    "coverage_prior",
    "size_match",
    "metal_overlap",
    "prob_gap",
    "prob_entropy",
    "chem_prob",
    "train_prior",
    "train_derived",
    "train_derived_plus_mapping_entropy",
    "train_derived_plus_multi_source",
    "train_derived_plus_stoich",
    "train_derived_plus_type_consistency",
    "train_derived_plus_metal_overlap",
    "train_derived_plus_stoich_mapping_entropy",
    "train_derived_plus_stoich_multi_source",
    "train_derived_plus_stoich_type_consistency",
    "train_derived_plus_stoich_metal_overlap",
    "anion_type",
    "mapping_stoich",
]:
    FEATURE_GROUPS[f"base_plus_{_group}"] = FEATURE_GROUPS["base362"] + FEATURE_GROUPS[_group]


FEATURE_GROUPS["cum_prob"] = [0, 6, 7, 372, 373]
FEATURE_GROUPS["cum_size"] = sorted(set(FEATURE_GROUPS["cum_prob"] + [5, 369]))
FEATURE_GROUPS["cum_coverage"] = sorted(
    set(FEATURE_GROUPS["cum_size"] + [1, 2, 4, 368] + list(range(8, 126)))
)
FEATURE_GROUPS["cum_target"] = sorted(
    set(FEATURE_GROUPS["cum_coverage"] + list(range(126, 244)))
)
FEATURE_GROUPS["cum_unwanted"] = sorted(
    set(FEATURE_GROUPS["cum_target"] + [3] + list(range(244, 362)))
)
FEATURE_GROUPS["cum_mapstoich"] = sorted(
    set(FEATURE_GROUPS["cum_unwanted"] + [362, 363, 364, 366, 371])
)
FEATURE_GROUPS["cum_full"] = list(range(TOTAL_FEAT_DIM))
FEATURE_GROUPS["cumb_probcov"] = sorted(
    set(FEATURE_GROUPS["cum_prob"] + [1, 2, 4, 368] + list(range(8, 126)))
)
FEATURE_GROUPS["cumb_target"] = sorted(
    set(FEATURE_GROUPS["cumb_probcov"] + list(range(126, 244)))
)
FEATURE_GROUPS["cumb_unwanted"] = sorted(
    set(FEATURE_GROUPS["cumb_target"] + [3] + list(range(244, 362)))
)


def feature_ablation_mask(mode: str) -> np.ndarray | None:
    if mode == "none":
        return None
    mask = np.ones(TOTAL_FEAT_DIM, dtype=np.float32)
    if mode.startswith("no_"):
        group = mode[3:]
        if group not in FEATURE_GROUPS:
            raise ValueError(f"Unknown feature ablation group: {group}")
        mask[FEATURE_GROUPS[group]] = 0.0
        return mask
    if mode.startswith("only_"):
        group = mode[5:]
        if group not in FEATURE_GROUPS:
            raise ValueError(f"Unknown feature ablation group: {group}")
        mask[:] = 0.0
        mask[FEATURE_GROUPS[group]] = 1.0
        return mask
    raise ValueError(f"Unknown feature_ablation mode: {mode}")


def apply_feature_ablation_array(feats: np.ndarray, mask: np.ndarray | None) -> np.ndarray:
    if mask is None:
        return feats
    return feats * mask


def apply_feature_ablation_dataset(data: dict, mask: np.ndarray | None) -> dict:
    if mask is not None:
        data["feats"] = apply_feature_ablation_array(data["feats"], mask)
    return data


def apply_feature_ablation_cache(cache: list[dict], mask: np.ndarray | None) -> list[dict]:
    if mask is not None:
        for sample in cache:
            sample["feats"] = apply_feature_ablation_array(sample["feats"], mask)
    return cache


def feature_ablation_is_model_side(mode: str) -> bool:
    """Whether raw features must be retained for a separate scoring branch."""
    return mode in MODEL_SIDE_FEATURE_ABLATIONS


def apply_anion_prior_mode(chem_prior: ChemistryPriorV2, y_train: np.ndarray, mode: str) -> dict[str, float]:
    """Replace manual leavability with train-only type statistics when requested."""
    if mode == "manual":
        return {}

    type_scores: dict[str, float]
    all_types = set(chem_prior.precursor_type.values())

    if mode == "zero":
        type_scores = {ptype: 0.0 for ptype in all_types}
    else:
        type_occ = Counter()
        type_vocab = Counter(chem_prior.precursor_type.values())
        for row in y_train:
            for pid in np.where(row > 0)[0].tolist():
                type_occ[chem_prior.precursor_type.get(int(pid), "other")] += 1
        all_types |= set(type_occ)

        raw = {}
        if mode == "train_type_freq":
            for ptype in all_types:
                raw[ptype] = np.log1p(type_occ.get(ptype, 0))
        elif mode == "train_type_rate":
            for ptype in all_types:
                # Average positive use per precursor of this type, with light smoothing.
                raw[ptype] = np.log1p((type_occ.get(ptype, 0) + 1.0) / (type_vocab.get(ptype, 0) + 2.0))
        else:
            raise ValueError(f"Unknown anion_prior_mode: {mode}")

        max_raw = max(raw.values()) if raw else 1.0
        type_scores = {ptype: float(val / max_raw) if max_raw > 0 else 0.0 for ptype, val in raw.items()}

    for pid, ptype in chem_prior.precursor_type.items():
        chem_prior.precursor_leavability[pid] = type_scores.get(ptype, 0.0)
    return type_scores


def apply_formula_train_stats_source(
    chem_prior: ChemistryPriorV2,
    target_precursor_id_mapping: Mapping[str, object],
    cache_dir: str | Path,
    target_dataset: str,
    source_dataset: str,
    anion_prior_mode: str,
    transfer_groups: str = "all",
) -> dict[str, int | str]:
    """Transfer train-derived stats by exact precursor formula for diagnostics."""
    if source_dataset == "self" or source_dataset == target_dataset:
        return {"source": "self", "status": "skipped_same_dataset"}

    valid_groups = {"pair_freq", "precursor_freq", "anion_leavability"}
    if transfer_groups == "all":
        groups = valid_groups
    else:
        groups = {group.strip() for group in transfer_groups.split(",") if group.strip()}
        unknown = groups - valid_groups
        if unknown:
            raise ValueError(
                f"Unknown train stats transfer groups: {sorted(unknown)}; "
                f"valid groups are {sorted(valid_groups)} or 'all'."
            )

    source_data = prepare_data(make_data_args(cache_dir, source_dataset, None), "cpu")
    source_env = ExpertEnv(precursor_features=source_data["precursor_X"], max_precursors=8)
    source_prior = ChemistryPriorV2(
        source_env,
        source_data["precursor_id_mapping"],
        source_data["X_train"],
        source_data["y_train"],
    )

    source_pid_to_formula = {
        int(pid): str(value[0])
        for pid, value in source_data["precursor_id_mapping"].items()
    }
    source_formula_to_pid = {}
    for pid, formula in source_pid_to_formula.items():
        source_formula_to_pid.setdefault(formula, pid)

    target_formula_to_pid = {
        str(value[0]): int(pid)
        for pid, value in target_precursor_id_mapping.items()
    }

    new_precursor_freq = Counter()
    for formula, target_pid in target_formula_to_pid.items():
        source_pid = source_formula_to_pid.get(formula)
        if source_pid is not None and source_prior.precursor_freq.get(source_pid, 0):
            new_precursor_freq[target_pid] = source_prior.precursor_freq[source_pid]

    new_pair_freq = Counter()
    for (source_a, source_b), freq in source_prior.pair_freq.items():
        formula_a = source_pid_to_formula.get(source_a)
        formula_b = source_pid_to_formula.get(source_b)
        if formula_a not in target_formula_to_pid or formula_b not in target_formula_to_pid:
            continue
        target_a = target_formula_to_pid[formula_a]
        target_b = target_formula_to_pid[formula_b]
        if target_a != target_b:
            new_pair_freq[tuple(sorted((target_a, target_b)))] += freq

    if "precursor_freq" in groups:
        chem_prior.precursor_freq = new_precursor_freq
    if "pair_freq" in groups:
        chem_prior.pair_freq = new_pair_freq

    transferred_type_scores = 0
    if "anion_leavability" in groups and anion_prior_mode != "manual":
        source_type_scores = apply_anion_prior_mode(
            source_prior,
            source_data["y_train"],
            anion_prior_mode,
        )
        for pid, ptype in chem_prior.precursor_type.items():
            if ptype in source_type_scores:
                chem_prior.precursor_leavability[pid] = source_type_scores[ptype]
                transferred_type_scores += 1

    return {
        "source": source_dataset,
        "status": "transferred",
        "transfer_groups": ",".join(sorted(groups)),
        "matched_precursors": len(new_precursor_freq),
        "matched_pairs": len(new_pair_freq),
        "matched_type_scores": transferred_type_scores,
    }


class MixtureOfPooling(nn.Module):
    def __init__(self, d_model: int, dropout: float = 0.1):
        super().__init__()
        self.attn_pool = nn.Linear(d_model, 1)
        self.target_query = nn.Linear(d_model, d_model)
        self.gate = nn.Sequential(
            nn.Linear(d_model * 5, d_model),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, 5),
        )

    def forward(self, tokens, mask, target_emb, slot_states):
        mask_f = mask.float().unsqueeze(-1)
        mean_pool = (tokens * mask_f).sum(dim=1) / mask_f.sum(dim=1).clamp(min=1.0)
        max_pool = tokens.masked_fill(~mask.unsqueeze(-1), -1e9).max(dim=1).values

        attn = self.attn_pool(tokens).squeeze(-1).masked_fill(~mask, -1e9)
        attn_pool = (tokens * torch.softmax(attn, dim=-1).unsqueeze(-1)).sum(dim=1)

        tq = self.target_query(target_emb).unsqueeze(1)
        target_scores = (tokens * tq).sum(dim=-1) / (tokens.size(-1) ** 0.5)
        target_scores = target_scores.masked_fill(~mask, -1e9)
        target_pool = (tokens * torch.softmax(target_scores, dim=-1).unsqueeze(-1)).sum(dim=1)

        slot_pool = slot_states.mean(dim=1)
        all_pools = torch.stack([mean_pool, max_pool, attn_pool, target_pool, slot_pool], dim=1)
        gate_in = torch.cat([mean_pool, max_pool, attn_pool, target_pool, slot_pool], dim=-1)
        weights = torch.softmax(self.gate(gate_in), dim=-1).unsqueeze(-1)
        return (all_pools * weights).sum(dim=1), weights.squeeze(-1)


class ReactionSlotSetEncoder(nn.Module):
    def __init__(
        self,
        d_formula=64,
        num_heads=4,
        num_slots=4,
        dropout=0.15,
        use_slot_cross=True,
        use_mixture_pool=True,
        use_candidate_mean_pool=False,
    ):
        super().__init__()
        self.token_encoder = FormulaTransformerEncoder(
            d_model=d_formula,
            num_heads=num_heads,
            num_layers=2,
            dropout=dropout,
        )
        self.num_slots = num_slots
        self.use_slot_cross = use_slot_cross
        self.use_mixture_pool = use_mixture_pool
        self.use_candidate_mean_pool = use_candidate_mean_pool
        self.reaction_slots = nn.Parameter(torch.randn(num_slots, d_formula) * 0.02)
        self.target_to_slot = nn.Sequential(
            nn.Linear(d_formula, d_formula),
            nn.LayerNorm(d_formula),
            nn.GELU(),
        )
        self.slot_cross_attn = nn.MultiheadAttention(
            d_formula, num_heads, dropout=dropout, batch_first=True)
        self.slot_norm = nn.LayerNorm(d_formula)
        self.slot_ffn = nn.Sequential(
            nn.Linear(d_formula, d_formula * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_formula * 2, d_formula),
        )
        self.pooling = MixtureOfPooling(d_formula, dropout=dropout)

    def encode_tokens(self, elem, frac, mask):
        tok = torch.cat([
            self.token_encoder.elem_emb(elem.long()),
            self.token_encoder.phys_table[elem.long()],
            frac.float().unsqueeze(-1),
        ], dim=-1)
        h = self.token_encoder.input_proj(tok)
        cls = self.token_encoder.cls.expand(h.size(0), -1, -1)
        h = torch.cat([cls, h], dim=1)
        key_pad = torch.cat([
            torch.zeros(h.size(0), 1, dtype=torch.bool, device=h.device),
            ~mask.bool(),
        ], dim=1)
        h = self.token_encoder.encoder(h, src_key_padding_mask=key_pad)
        valid_mask = torch.cat([
            torch.ones(h.size(0), 1, dtype=torch.bool, device=h.device),
            mask.bool(),
        ], dim=1)
        return self.token_encoder.out_norm(h), valid_mask

    def forward(self, target_elem, target_frac, target_mask, cand_elem, cand_frac, cand_mask):
        target_tokens, target_valid = self.encode_tokens(
            target_elem.long(), target_frac.float(), target_mask.bool())
        target_emb = target_tokens[:, 0]

        cand_tokens, cand_valid = self.encode_tokens(
            cand_elem.long(), cand_frac.float(), cand_mask.bool())
        slot_seed = self.reaction_slots.unsqueeze(0).expand(cand_tokens.size(0), -1, -1)
        target_cond = self.target_to_slot(target_emb).unsqueeze(1)
        slots = slot_seed + target_cond
        if self.use_slot_cross:
            slot_ctx, _ = self.slot_cross_attn(
                slots,
                cand_tokens,
                cand_tokens,
                key_padding_mask=~cand_valid,
                need_weights=False,
            )
            slots = self.slot_norm(slots + slot_ctx)
        else:
            slots = self.slot_norm(slots)
        slots = self.slot_norm(slots + self.slot_ffn(slots))
        if self.use_mixture_pool:
            set_emb, pool_weights = self.pooling(cand_tokens, cand_valid, target_emb, slots)
        elif self.use_candidate_mean_pool:
            valid = cand_valid.float().unsqueeze(-1)
            set_emb = (cand_tokens * valid).sum(dim=1) / valid.sum(dim=1).clamp(min=1.0)
            pool_weights = torch.zeros(cand_tokens.size(0), 5, device=cand_tokens.device)
            pool_weights[:, 0] = 1.0
        else:
            set_emb = slots.mean(dim=1)
            pool_weights = torch.zeros(cand_tokens.size(0), 5, device=cand_tokens.device)
            pool_weights[:, -1] = 1.0
        return {
            "target_emb": target_emb,
            "target_tokens": target_tokens,
            "target_valid": target_valid,
            "set_emb": set_emb,
            "slot_states": slots,
            "pool_weights": pool_weights,
        }


class Stage2SlotCrossReranker(nn.Module):
    def __init__(
        self,
        feat_dim=TOTAL_FEAT_DIM,
        d_formula=64,
        d_token=192,
        num_heads=4,
        num_layers=2,
        dropout=0.15,
        charge_scale=0.1,
        num_slots=4,
        use_mixture_pool=True,
        use_slot_cross=True,
        use_features=True,
        use_charge=True,
        use_prob_residual=True,
        prob_residual_init=0.05,
        freeze_prob_residual=False,
        feature_mask=None,
    ):
        super().__init__()
        self.set_encoder = ReactionSlotSetEncoder(
            d_formula=d_formula,
            num_heads=num_heads,
            num_slots=num_slots,
            dropout=dropout,
            use_slot_cross=use_slot_cross,
            use_mixture_pool=use_mixture_pool,
        )
        self.use_mixture_pool = use_mixture_pool
        self.use_features = use_features
        self.use_charge = use_charge
        self.use_prob_residual = use_prob_residual
        mask_tensor = (
            None
            if feature_mask is None
            else torch.as_tensor(feature_mask, dtype=torch.float32).view(1, 1, -1)
        )
        self.register_buffer(
            "descriptor_feature_mask",
            mask_tensor,
            persistent=False,
        )
        self.feature_proj = nn.Sequential(
            nn.Linear(feat_dim, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, 128),
            nn.LayerNorm(128),
            nn.GELU(),
        )
        self.size_proj = nn.Sequential(nn.Linear(1, 16), nn.GELU(), nn.Linear(16, 16))
        self.charge_proj = nn.Sequential(nn.Linear(118, 32), nn.LayerNorm(32), nn.GELU())
        self.charge_scale = nn.Parameter(torch.tensor(float(charge_scale)))
        self.coverage_head = nn.Sequential(
            nn.LayerNorm(d_formula),
            nn.Linear(d_formula, d_formula),
            nn.GELU(),
            nn.Linear(d_formula, 118),
        )
        self.count_head = nn.Sequential(
            nn.LayerNorm(d_token),
            nn.Linear(d_token, d_token // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_token // 2, 1),
        )
        pair_dim = 128 + d_formula * 4 + 16 + 32
        self.pair_proj = nn.Sequential(
            nn.Linear(pair_dim, d_token),
            nn.LayerNorm(d_token),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        layer = nn.TransformerEncoderLayer(
            d_model=d_token,
            nhead=num_heads,
            dim_feedforward=d_token * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.list_encoder = nn.TransformerEncoder(layer, num_layers=num_layers)
        self.score_head = nn.Sequential(
            nn.LayerNorm(d_token),
            nn.Linear(d_token, d_token // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_token // 2, 1),
        )
        self.prob_residual = nn.Parameter(
            torch.tensor(float(prob_residual_init)),
            requires_grad=not freeze_prob_residual,
        )

    def forward(self, feats, target_elem, target_frac, target_mask,
                cand_elem, cand_frac, cand_mask, sizes, cand_charge=None):
        if feats.dim() == 2:
            feats = feats.unsqueeze(0)
            cand_elem = cand_elem.unsqueeze(0)
            cand_frac = cand_frac.unsqueeze(0)
            cand_mask = cand_mask.unsqueeze(0)
            sizes = sizes.unsqueeze(0)
            if cand_charge is not None:
                cand_charge = cand_charge.unsqueeze(0)
        if target_elem.dim() == 1:
            target_elem = target_elem.unsqueeze(0)
            target_frac = target_frac.unsqueeze(0)
            target_mask = target_mask.unsqueeze(0)

        bsz, list_len, _ = feats.shape
        flat_elem = cand_elem.reshape(bsz * list_len, -1)
        flat_frac = cand_frac.reshape(bsz * list_len, -1)
        flat_mask = cand_mask.reshape(bsz * list_len, -1)
        target_elem_flat = target_elem.unsqueeze(1).expand(-1, list_len, -1).reshape(bsz * list_len, -1)
        target_frac_flat = target_frac.unsqueeze(1).expand(-1, list_len, -1).reshape(bsz * list_len, -1)
        target_mask_flat = target_mask.unsqueeze(1).expand(-1, list_len, -1).reshape(bsz * list_len, -1)

        enc = self.set_encoder(
            target_elem_flat,
            target_frac_flat,
            target_mask_flat,
            flat_elem,
            flat_frac,
            flat_mask,
        )
        target_emb = enc["target_emb"].view(bsz, list_len, -1)
        set_emb = enc["set_emb"].view(bsz, list_len, -1)
        slot_states = enc["slot_states"].view(bsz, list_len, enc["slot_states"].size(1), -1)

        descriptor_feats = feats.float()
        if self.descriptor_feature_mask is not None:
            descriptor_feats = descriptor_feats * self.descriptor_feature_mask
        if self.use_features:
            feat_emb = self.feature_proj(descriptor_feats)
        else:
            feat_emb = torch.zeros(bsz, list_len, 128, device=feats.device)
        size_emb = self.size_proj((sizes.float() / 8.0).unsqueeze(-1))
        if cand_charge is None or not self.use_charge:
            charge_emb = torch.zeros(bsz, list_len, 32, device=feats.device)
        else:
            charge_emb = self.charge_scale * self.charge_proj(cand_charge.float())
        pair = torch.cat([
            feat_emb,
            target_emb,
            set_emb,
            torch.abs(target_emb - set_emb),
            target_emb * set_emb,
            size_emb,
            charge_emb,
        ], dim=-1)
        tokens = self.list_encoder(self.pair_proj(pair))
        scores = self.score_head(tokens).squeeze(-1)
        if self.use_prob_residual:
            base_prob = feats[..., 0].clamp(min=1e-8)
            scores = scores + self.prob_residual * torch.log(base_prob)
        coverage_logits = self.coverage_head(slot_states.mean(dim=2))
        count_logits = self.count_head(tokens).squeeze(-1)
        return scores, coverage_logits, count_logits


class DescriptorMLPReranker(nn.Module):
    """Independent candidate scorer using only the shared 374-d descriptors."""

    def __init__(
        self,
        feat_dim=TOTAL_FEAT_DIM,
        dropout=0.15,
        use_prob_residual=False,
        prob_residual_init=0.05,
        freeze_prob_residual=False,
        hidden_dims=(256, 128),
        feature_mask=None,
        **_,
    ):
        super().__init__()
        self.use_prob_residual = use_prob_residual
        mask_tensor = (
            None
            if feature_mask is None
            else torch.as_tensor(feature_mask, dtype=torch.float32).view(1, 1, -1)
        )
        self.register_buffer(
            "descriptor_feature_mask",
            mask_tensor,
            persistent=False,
        )
        layers = []
        in_dim = feat_dim
        for width in hidden_dims:
            layers.extend(
                [
                    nn.Linear(in_dim, width),
                    nn.LayerNorm(width),
                    nn.GELU(),
                    nn.Dropout(dropout),
                ]
            )
            in_dim = width
        layers.append(nn.Linear(in_dim, 1))
        self.score_mlp = nn.Sequential(*layers)
        self.prob_residual = nn.Parameter(
            torch.tensor(float(prob_residual_init)),
            requires_grad=not freeze_prob_residual,
        )

    def forward(self, feats, target_elem, target_frac, target_mask,
                cand_elem, cand_frac, cand_mask, sizes, cand_charge=None):
        if feats.dim() == 2:
            feats = feats.unsqueeze(0)
        descriptor_feats = feats.float()
        if self.descriptor_feature_mask is not None:
            descriptor_feats = descriptor_feats * self.descriptor_feature_mask
        scores = self.score_mlp(descriptor_feats).squeeze(-1)
        if self.use_prob_residual:
            scores = scores + self.prob_residual * torch.log(feats[..., 0].clamp(min=1e-8))
        coverage_logits = torch.zeros(
            *scores.shape, 118, dtype=feats.dtype, device=feats.device
        )
        count_logits = torch.zeros_like(scores)
        return scores, coverage_logits, count_logits


class LinearDescriptorReranker(nn.Module):
    """Linear pointwise scorer for controlled descriptor-only baselines."""

    def __init__(
        self,
        feat_dim=TOTAL_FEAT_DIM,
        use_prob_residual=False,
        prob_residual_init=0.05,
        freeze_prob_residual=False,
        feature_mask=None,
        **_,
    ):
        super().__init__()
        self.use_prob_residual = use_prob_residual
        mask_tensor = (
            None
            if feature_mask is None
            else torch.as_tensor(feature_mask, dtype=torch.float32).view(1, 1, -1)
        )
        self.register_buffer(
            "descriptor_feature_mask",
            mask_tensor,
            persistent=False,
        )
        self.score_linear = nn.Linear(feat_dim, 1)
        self.prob_residual = nn.Parameter(
            torch.tensor(float(prob_residual_init)),
            requires_grad=not freeze_prob_residual,
        )

    def forward(self, feats, target_elem, target_frac, target_mask,
                cand_elem, cand_frac, cand_mask, sizes, cand_charge=None):
        if feats.dim() == 2:
            feats = feats.unsqueeze(0)
        descriptor_feats = feats.float()
        if self.descriptor_feature_mask is not None:
            descriptor_feats = descriptor_feats * self.descriptor_feature_mask
        scores = self.score_linear(descriptor_feats).squeeze(-1)
        if self.use_prob_residual:
            scores = scores + self.prob_residual * torch.log(
                feats[..., 0].clamp(min=1e-8)
            )
        coverage_logits = torch.zeros(
            *scores.shape, 118, dtype=feats.dtype, device=feats.device
        )
        count_logits = torch.zeros_like(scores)
        return scores, coverage_logits, count_logits


class PointwiseSetTokenReranker(Stage2SlotCrossReranker):
    """Full target/set encoder without cross-candidate list contextualization."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_encoder.use_candidate_mean_pool = True
        self.list_encoder = nn.Identity()


def _stage2_arg(args, name, default):
    if isinstance(args, Mapping):
        value = args.get(name, default)
    else:
        value = getattr(args, name, default)
    if isinstance(default, bool) and isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "y"}
    return value


def build_stage2_model(args) -> nn.Module:
    """Build a Stage-2 architecture from CLI or checkpoint arguments."""
    arch = str(_stage2_arg(args, "reranker_arch", "slot_cross"))
    feature_ablation = str(_stage2_arg(args, "feature_ablation", "none"))
    model_feature_mask = (
        feature_ablation_mask(feature_ablation)
        if feature_ablation_is_model_side(feature_ablation)
        else None
    )
    common = {
        "dropout": float(_stage2_arg(args, "dropout", 0.12)),
        "use_prob_residual": not _stage2_arg(args, "disable_prob_residual", False),
        "prob_residual_init": float(_stage2_arg(args, "prob_residual_init", 0.05)),
        "freeze_prob_residual": _stage2_arg(args, "freeze_prob_residual", False),
        "feature_mask": model_feature_mask,
    }
    if arch == "descriptor_mlp":
        hidden_spec = str(_stage2_arg(args, "descriptor_mlp_hidden", "256,128"))
        hidden_dims = tuple(
            int(part) for part in hidden_spec.split(",") if part.strip()
        )
        return DescriptorMLPReranker(hidden_dims=hidden_dims, **common)
    if arch == "linear_descriptor":
        return LinearDescriptorReranker(**common)

    formula_common = {
        **common,
        "charge_scale": float(_stage2_arg(args, "charge_scale", 0.1)),
        "num_slots": int(_stage2_arg(args, "num_slots", 4)),
        "use_mixture_pool": not _stage2_arg(args, "disable_mixture_pool", False),
        "use_slot_cross": not _stage2_arg(args, "disable_slot_cross", False),
        "use_features": not _stage2_arg(args, "disable_features", False),
        "use_charge": not _stage2_arg(args, "disable_charge", False),
    }
    if arch == "slot_cross":
        return Stage2SlotCrossReranker(**formula_common)
    if arch == "pointwise_set_token":
        return PointwiseSetTokenReranker(**formula_common)
    raise ValueError(f"Unknown reranker architecture: {arch}")


def load_stage2_checkpoint(checkpoint_path, device):
    """Load the architecture recorded in a Stage-2 checkpoint."""
    checkpoint = torch.load(checkpoint_path, map_location=device)
    saved_args = checkpoint.get("args", {})
    model = build_stage2_model(saved_args).to(device)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    return model, checkpoint


def target_presence(target_elem, target_mask):
    out = torch.zeros(target_elem.size(0), 118, device=target_elem.device)
    idx = (target_elem.long() - 1).clamp(min=0, max=117)
    out.scatter_(1, idx, target_mask.float())
    return out


def score_sample(model, sample, device, chunk=512):
    scores_all = []
    target_elem = torch.as_tensor(sample["target_elem"], device=device)
    target_frac = torch.as_tensor(sample["target_frac"], dtype=torch.float32, device=device)
    target_mask = torch.as_tensor(sample["target_mask"], dtype=torch.bool, device=device)
    for start in range(0, sample["feats"].shape[0], chunk):
        end = min(start + chunk, sample["feats"].shape[0])
        feats = torch.as_tensor(sample["feats"][start:end], dtype=torch.float32, device=device)
        ce = torch.as_tensor(sample["cand_elem"][start:end], device=device)
        cf = torch.as_tensor(sample["cand_frac"][start:end], dtype=torch.float32, device=device)
        cm = torch.as_tensor(sample["cand_mask"][start:end], dtype=torch.bool, device=device)
        sizes = torch.as_tensor(sample["sizes"][start:end], dtype=torch.float32, device=device)
        cc = torch.as_tensor(sample["cand_charge"][start:end], dtype=torch.float32, device=device)
        scores, _, _ = model(feats, target_elem, target_frac, target_mask, ce, cf, cm, sizes, cc)
        scores_all.append(scores.squeeze(0).detach().cpu().numpy())
    scores = np.concatenate(scores_all)
    if not np.isfinite(scores).all():
        bad = int((~np.isfinite(scores)).sum())
        raise FloatingPointError(f"Stage-2 produced {bad} non-finite candidate scores")
    return scores


@torch.no_grad()
def evaluate(model, cache, full_n, device, chunk=512, label="test"):
    model.eval()
    ks = [1, 3, 5, 10, 20]
    hits = {k: 0 for k in ks}
    average_tie_hits = {k: 0 for k in ks}
    worst_tie_hits = {k: 0 for k in ks}
    valid = 0
    rr_sum = 0.0
    average_tie_rr_sum = 0.0
    worst_tie_rr_sum = 0.0
    ranks = []
    correct_score_tie_sizes = []
    for i, sample in enumerate(cache, 1):
        ci = sample["correct_idx"]
        if ci is None:
            continue
        valid += 1
        scores = score_sample(model, sample, device, chunk)
        correct_score = scores[ci]
        rank = int(np.sum(scores > correct_score))
        tie_size = int(np.sum(scores == correct_score))
        rank_1based = rank + 1
        average_tie_rank = rank + (tie_size + 1.0) / 2.0
        worst_tie_rank = rank + tie_size
        rr_sum += 1.0 / rank_1based
        average_tie_rr_sum += 1.0 / average_tie_rank
        worst_tie_rr_sum += 1.0 / worst_tie_rank
        ranks.append(rank_1based)
        correct_score_tie_sizes.append(tie_size)
        for k in ks:
            if rank < k:
                hits[k] += 1
            if average_tie_rank <= k:
                average_tie_hits[k] += 1
            if worst_tie_rank <= k:
                worst_tie_hits[k] += 1
        if i % 200 == 0:
            logger.info("  %s eval %d/%d", label, i, len(cache))
    metrics = {}
    for k in ks:
        metrics[f"combo_{k}_valid"] = hits[k] / max(valid, 1) * 100
        metrics[f"combo_{k}_full"] = hits[k] / max(full_n, 1) * 100
        metrics[f"combo_{k}_full_tie_average"] = (
            average_tie_hits[k] / max(full_n, 1) * 100
        )
        metrics[f"combo_{k}_full_tie_worst"] = (
            worst_tie_hits[k] / max(full_n, 1) * 100
        )
    metrics["valid"] = valid
    metrics["full_denominator"] = full_n
    metrics["combo_mrr_valid"] = rr_sum / max(valid, 1)
    metrics["combo_mrr_full"] = rr_sum / max(full_n, 1)
    metrics["combo_mrr_full_tie_average"] = (
        average_tie_rr_sum / max(full_n, 1)
    )
    metrics["combo_mrr_full_tie_worst"] = (
        worst_tie_rr_sum / max(full_n, 1)
    )
    metrics["mean_rank_valid"] = float(np.mean(ranks)) if ranks else 0.0
    metrics["median_rank_valid"] = float(np.median(ranks)) if ranks else 0.0
    metrics["correct_score_tied_target_count"] = int(
        sum(size > 1 for size in correct_score_tie_sizes)
    )
    metrics["correct_score_tie_size_mean"] = (
        float(np.mean(correct_score_tie_sizes))
        if correct_score_tie_sizes else 0.0
    )
    metrics["correct_score_tie_size_max"] = (
        int(max(correct_score_tie_sizes))
        if correct_score_tie_sizes else 0
    )
    logger.info("%s metrics: %s", label, metrics)
    return metrics


def evaluate_product_rerank(cache, full_n, label="test_product"):
    """Rule-based set rerank using the same enumerated sets as Stage2.

    This isolates candidate-generation/filter effects from the learned reranker:
    the candidate pool and set enumeration are identical to Stage2, but scores are
    just the Stage1 precursor-probability product stored in the rank cache.
    """
    ks = [1, 3, 5, 10, 20]
    hits = {k: 0 for k in ks}
    valid = 0
    rr_sum = 0.0
    ranks = []
    for i, sample in enumerate(cache, 1):
        ci = sample["correct_idx"]
        if ci is None:
            continue
        valid += 1
        scores = np.asarray(sample["product_scores"], dtype=np.float32)
        rank = int(np.sum(scores > scores[ci]))
        rank_1based = rank + 1
        rr_sum += 1.0 / rank_1based
        ranks.append(rank_1based)
        for k in ks:
            if rank < k:
                hits[k] += 1
        if i % 200 == 0:
            logger.info("  %s eval %d/%d", label, i, len(cache))
    metrics = {}
    for k in ks:
        metrics[f"combo_{k}_valid"] = hits[k] / max(valid, 1) * 100
        metrics[f"combo_{k}_full"] = hits[k] / max(full_n, 1) * 100
    metrics["valid"] = valid
    metrics["full_denominator"] = full_n
    metrics["combo_mrr_valid"] = rr_sum / max(valid, 1)
    metrics["combo_mrr_full"] = rr_sum / max(full_n, 1)
    metrics["mean_rank_valid"] = float(np.mean(ranks)) if ranks else 0.0
    metrics["median_rank_valid"] = float(np.median(ranks)) if ranks else 0.0
    logger.info("%s metrics: %s", label, metrics)
    return metrics


def _rank_metrics_from_scores(cache, full_n, score_fn, label):
    ks = [1, 3, 5, 10, 20]
    hits = {k: 0 for k in ks}
    valid = 0
    rr_sum = 0.0
    ranks = []
    size_hits = {}
    size_counts = {}
    for i, sample in enumerate(cache, 1):
        ci = sample["correct_idx"]
        if ci is None:
            continue
        valid += 1
        scores = np.asarray(score_fn(sample), dtype=np.float64)
        rank = int(np.sum(scores > scores[ci]))
        rank_1based = rank + 1
        true_size = int(len(sample["gt_ids"]))
        size_counts[true_size] = size_counts.get(true_size, 0) + 1
        rr_sum += 1.0 / rank_1based
        ranks.append(rank_1based)
        for k in ks:
            if rank < k:
                hits[k] += 1
                size_hits[(true_size, k)] = size_hits.get((true_size, k), 0) + 1
        if i % 200 == 0:
            logger.info("  %s eval %d/%d", label, i, len(cache))
    metrics = {}
    for k in ks:
        metrics[f"combo_{k}_valid"] = hits[k] / max(valid, 1) * 100
        metrics[f"combo_{k}_full"] = hits[k] / max(full_n, 1) * 100
    metrics["valid"] = valid
    metrics["full_denominator"] = full_n
    metrics["combo_mrr_valid"] = rr_sum / max(valid, 1)
    metrics["combo_mrr_full"] = rr_sum / max(full_n, 1)
    metrics["mean_rank_valid"] = float(np.mean(ranks)) if ranks else 0.0
    metrics["median_rank_valid"] = float(np.median(ranks)) if ranks else 0.0
    metrics["by_true_size"] = {
        str(size): {
            "valid": count,
            **{
                f"combo_{k}_valid": size_hits.get((size, k), 0) / max(count, 1) * 100
                for k in ks
            },
        }
        for size, count in sorted(size_counts.items())
    }
    logger.info("%s metrics: %s", label, metrics)
    return metrics


def _log_product_scores(sample):
    if "sum_log_scores" in sample:
        return np.asarray(sample["sum_log_scores"], dtype=np.float64)
    return np.log(np.asarray(sample["product_scores"], dtype=np.float64).clip(min=1e-300))


def evaluate_same_enum_independent_scorers(cache, full_n, size_log_prior=None):
    """Evaluate independent Stage-1 scorers on the exact Stage-2 candidate lists."""
    metrics = {
        "product_prob": _rank_metrics_from_scores(
            cache,
            full_n,
            lambda sample: np.asarray(sample["product_scores"], dtype=np.float64),
            "same_enum_product_prob",
        ),
        "sum_log_prob": _rank_metrics_from_scores(
            cache,
            full_n,
            _log_product_scores,
            "same_enum_sum_log_prob",
        ),
        "mean_log_prob": _rank_metrics_from_scores(
            cache,
            full_n,
            lambda sample: _log_product_scores(sample) / np.maximum(np.asarray(sample["sizes"], dtype=np.float64), 1.0),
            "same_enum_mean_log_prob",
        ),
    }
    if size_log_prior:
        metrics["val_size_prior_log_prob"] = _rank_metrics_from_scores(
            cache,
            full_n,
            lambda sample: _log_product_scores(sample)
            + np.asarray([size_log_prior.get(int(size), -20.0) for size in sample["sizes"]], dtype=np.float64),
            "same_enum_val_size_prior_log_prob",
        )
    return metrics


def size_log_prior_from_labels(y, min_size=2, max_size=5, alpha=1.0):
    counts = {size: alpha for size in range(min_size, max_size + 1)}
    for row in y:
        size = int(np.sum(row > 0))
        if min_size <= size <= max_size:
            counts[size] = counts.get(size, alpha) + 1.0
    total = sum(counts.values())
    return {size: float(np.log(count / total)) for size, count in counts.items()}


def export_same_enum_artifact(cache, full_n, output_path, size_log_prior=None):
    """Persist per-target candidate-list diagnostics without model tensors."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if output_path.suffix == ".gz" else open
    written = 0
    with opener(output_path, "wt", encoding="utf-8") as fh:
        for target_idx, sample in enumerate(cache):
            product_scores = np.asarray(sample["product_scores"], dtype=np.float64)
            log_scores = _log_product_scores(sample)
            sizes = np.asarray(sample["sizes"], dtype=np.int64)
            record = {
                "target_index": int(sample.get("target_idx", target_idx)),
                "full_denominator": full_n,
                "gt_ids": sample["gt_ids"],
                "true_size": int(len(sample["gt_ids"])),
                "correct_idx": sample["correct_idx"],
                "candidate_count": int(len(sample["combos"])),
                "pool_ids": sample.get("pool_ids"),
                "pool_probs": sample.get("pool_probs"),
                "combos": sample["combos"],
                "sizes": sizes.tolist(),
                "product_prob": product_scores.tolist(),
                "sum_log_prob": log_scores.tolist(),
                "mean_log_prob": (log_scores / np.maximum(sizes, 1)).tolist(),
            }
            if size_log_prior:
                record["val_size_prior_log_prob"] = (
                    log_scores
                    + np.asarray([size_log_prior.get(int(size), -20.0) for size in sizes], dtype=np.float64)
                ).tolist()
                record["size_log_prior"] = {str(k): v for k, v in size_log_prior.items()}
            fh.write(json.dumps(record, separators=(",", ":")) + "\n")
            written += 1
    logger.info("Wrote same-enumeration artifact: path=%s records=%d", output_path, written)


def _rank_1based(scores, correct_idx):
    return int(np.sum(np.asarray(scores, dtype=np.float64) > scores[correct_idx])) + 1


def export_same_enum_compact_artifact(cache, full_n, output_path, size_log_prior=None):
    """Persist compact per-target same-enumeration diagnostics for supplemental release."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    opener = gzip.open if output_path.suffix == ".gz" else open
    written = 0
    with opener(output_path, "wt", encoding="utf-8") as fh:
        for target_idx, sample in enumerate(cache):
            ci = sample["correct_idx"]
            log_scores = _log_product_scores(sample)
            sizes = np.asarray(sample["sizes"], dtype=np.int64)
            product_scores = np.asarray(sample["product_scores"], dtype=np.float64)
            mean_log_scores = log_scores / np.maximum(sizes, 1)
            record = {
                "target_index": int(sample.get("target_idx", target_idx)),
                "full_denominator": full_n,
                "available": ci is not None,
                "true_size": int(len(sample["gt_ids"])),
                "candidate_count": int(len(sample["combos"])),
                "correct_idx": None if ci is None else int(ci),
            }
            if ci is not None:
                record.update(
                    {
                        "rank_product_prob": _rank_1based(product_scores, ci),
                        "rank_sum_log_prob": _rank_1based(log_scores, ci),
                        "rank_mean_log_prob": _rank_1based(mean_log_scores, ci),
                    }
                )
                if size_log_prior:
                    size_prior_scores = log_scores + np.asarray(
                        [size_log_prior.get(int(size), -20.0) for size in sizes], dtype=np.float64
                    )
                    record["rank_val_size_prior_log_prob"] = _rank_1based(size_prior_scores, ci)
            fh.write(json.dumps(record, separators=(",", ":")) + "\n")
            written += 1
    logger.info("Wrote compact same-enumeration artifact: path=%s records=%d", output_path, written)


def train(args):
    device = args.device if args.device.startswith("cuda") and torch.cuda.is_available() else "cpu"
    data = prepare_data(make_data_args(args.cache_dir, args.dataset, args.data_path), device)
    probs = np.load(args.probs_path)
    charge = load_precursor_charge_matrix(
        args.precursor_charge_csv,
        data["precursor_id_mapping"],
        data["num_classes"],
    )
    if args.charge_mode == "zero":
        logger.info("Charge control: using all-zero charge matrix with charge branch enabled.")
        charge = np.zeros_like(charge)
    elif args.charge_mode == "shuffle":
        logger.info("Charge control: using row-shuffled charge matrix with charge branch enabled.")
        rng = np.random.default_rng(args.seed)
        charge = charge[rng.permutation(len(charge))]
    elif args.charge_mode == "none":
        logger.info("Charge control: disabling charge branch entirely.")
        args.disable_charge = True
    else:
        logger.info("Charge control: using real aligned charge matrix.")
    env = ExpertEnv(precursor_features=data["precursor_X"], max_precursors=8)
    chem_prior = ChemistryPriorV2(env, data["precursor_id_mapping"], data["X_train"], data["y_train"])
    anion_type_scores = apply_anion_prior_mode(chem_prior, data["y_train"], args.anion_prior_mode)
    if anion_type_scores:
        logger.info(
            "Anion prior mode=%s train-only type scores=%s",
            args.anion_prior_mode,
            {k: round(v, 4) for k, v in sorted(anion_type_scores.items())},
        )
    stats_transfer = apply_formula_train_stats_source(
        chem_prior,
        data["precursor_id_mapping"],
        args.cache_dir,
        args.dataset,
        args.train_stats_source,
        args.anion_prior_mode,
        args.train_stats_transfer_groups,
    )
    if stats_transfer["status"] != "skipped_same_dataset":
        logger.info("Train stats source transfer: %s", stats_transfer)
    feat_mask = feature_ablation_mask(args.feature_ablation)
    if feat_mask is not None:
        logger.info(
            "Feature ablation mode=%s keeps %d/%d feature dims",
            args.feature_ablation,
            int(feat_mask.sum()),
            TOTAL_FEAT_DIM,
        )
        if feature_ablation_is_model_side(args.feature_ablation):
            logger.info(
                "Feature mask is applied only to the descriptor scorer; "
                "raw generator probability remains available to the "
                "independent residual branch."
            )
    train_x, train_y, train_probs = data["X_train"], data["y_train"], probs["train"]
    val_x, val_y, val_probs = data["X_val"], data["y_val"], probs["val"]
    test_x, test_y, test_probs = data["X_test"], data["y_test"], probs["test"]
    if args.sample_limit:
        train_x = train_x[:args.sample_limit]
        train_y = train_y[:args.sample_limit]
        train_probs = train_probs[:args.sample_limit]
        val_x = val_x[:min(args.sample_limit, len(val_x))]
        val_y = val_y[:min(args.sample_limit, len(val_y))]
        val_probs = val_probs[:min(args.sample_limit, len(val_probs))]
        test_x = test_x[:min(args.sample_limit, len(test_x))]
        test_y = test_y[:min(args.sample_limit, len(test_y))]
        test_probs = test_probs[:min(args.sample_limit, len(test_probs))]

    train_data = build_stage2_data(
        env, train_x, train_y, train_probs, chem_prior, data["precursor_X"], charge, args)
    if not feature_ablation_is_model_side(args.feature_ablation):
        train_data = apply_feature_ablation_dataset(train_data, feat_mask)
    if args.deterministic_training:
        logger.info(
            "[diag] train_data len=%d feats_head=%s cand_head=%s target_head=%s",
            len(train_data["feats"]),
            _digest_value(train_data["feats"][: min(4, len(train_data["feats"]))]),
            _digest_value(train_data["cand_elem"][: min(4, len(train_data["cand_elem"]))]),
            _digest_value(train_data["target_elem"][: min(4, len(train_data["target_elem"]))]),
        )
    train_ds = FormulaListDataset(train_data)
    loader_generator = None
    if args.deterministic_training:
        loader_generator = torch.Generator()
        loader_generator.manual_seed(args.seed + args.dataloader_seed_offset)
    loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=False,
        drop_last=True,
        generator=loader_generator,
    )
    val_cache, val_full_n = make_rank_cache(
        env, val_x, val_y, val_probs, chem_prior, data["precursor_X"], charge, args, "val")
    if not feature_ablation_is_model_side(args.feature_ablation):
        val_cache = apply_feature_ablation_cache(val_cache, feat_mask)

    model = build_stage2_model(args).to(device)
    if args.deterministic_training:
        logger.info("[diag] model_init_digest=%s", _digest_model(model))
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    best_c1 = -1.0
    best_state = None

    train_batches = len(loader)
    logger.info(
        "[slot] train start epochs=%d batches_per_epoch=%d batch_size=%d rss=%.1fMB cuda_alloc=%.1fMB cuda_reserved=%.1fMB",
        args.epochs,
        train_batches,
        args.batch_size,
        current_rss_mb(),
        *cuda_memory_mb(device),
    )
    for ep in range(args.epochs):
        epoch_t0 = time.time()
        logger.info("[slot] epoch=%d train begin", ep + 1)
        model.train()
        total = correct = n = 0
        cov_total = 0.0
        count_total = 0.0
        for step, batch in enumerate(loader, 1):
            if args.deterministic_training and step <= args.diagnostic_batches:
                logger.info("[diag] epoch=%d step=%d batch_digest=%s", ep + 1, step, _digest_batch(batch))
            feats, te, tf, tm, ce, cf, cm, sizes, cc, labels = [
                torch.as_tensor(x, device=device) for x in batch
            ]
            scores, coverage_logits, count_logits = model(feats, te, tf, tm, ce, cf, cm, sizes, cc)
            if getattr(args, "loss_mode", "listwise") == "bce":
                bce_target = torch.zeros_like(scores)
                bce_target.scatter_(1, labels.long().unsqueeze(1), 1.0)
                loss_rank = F.binary_cross_entropy_with_logits(scores, bce_target)
            else:
                log_probs = F.log_softmax(scores / args.temperature, dim=-1)
                target = torch.full_like(log_probs, args.smoothing / (scores.size(1) - 1))
                target.scatter_(1, labels.long().unsqueeze(1), 1.0 - args.smoothing)
                loss_rank = -(target * log_probs).sum(dim=-1).mean()

            pos = scores.gather(1, labels.long().unsqueeze(1)).squeeze(1)
            neg = scores.masked_fill(
                torch.eye(scores.size(1), device=device, dtype=torch.bool)[labels.long()], -1e9
            ).max(dim=-1).values
            loss_margin = F.relu(args.margin + neg - pos).mean()

            cov_target = target_presence(te.long(), tm.bool())
            pos_cov = coverage_logits.gather(
                1,
                labels.long().view(-1, 1, 1).expand(-1, 1, coverage_logits.size(-1)),
            ).squeeze(1)
            loss_cov = F.binary_cross_entropy_with_logits(pos_cov, cov_target.float())

            true_sizes = sizes.gather(1, labels.long().unsqueeze(1)).squeeze(1)
            count_target = (sizes == true_sizes.unsqueeze(1)).float()
            loss_count = F.binary_cross_entropy_with_logits(count_logits, count_target)
            loss = (
                loss_rank
                + args.margin_weight * loss_margin
                + args.coverage_weight * loss_cov
                + args.count_weight * loss_count
            )
            if not torch.isfinite(loss):
                raise FloatingPointError(
                    f"Non-finite Stage-2 loss at epoch={ep + 1} step={step}"
                )

            opt.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            total += float(loss.detach().cpu()) * feats.size(0)
            cov_total += float(loss_cov.detach().cpu()) * feats.size(0)
            count_total += float(loss_count.detach().cpu()) * feats.size(0)
            correct += (scores.argmax(dim=-1) == labels.long()).sum().item()
            n += feats.size(0)
            if (
                args.train_log_interval > 0
                and (step % args.train_log_interval == 0 or step == train_batches)
            ):
                elapsed = time.time() - epoch_t0
                logger.info(
                    "[slot] epoch=%d step=%d/%d elapsed=%.0fs %.2fstep/s loss=%.4f train_acc=%.1f rss=%.1fMB cuda_alloc=%.1fMB cuda_reserved=%.1fMB",
                    ep + 1,
                    step,
                    train_batches,
                    elapsed,
                    step / max(elapsed, 1e-6),
                    total / max(n, 1),
                    correct / max(n, 1) * 100,
                    current_rss_mb(),
                    *cuda_memory_mb(device),
                )

        logger.info("[slot] epoch=%d train finished; starting validation", ep + 1)
        val_metrics = evaluate(model, val_cache, val_full_n, device, args.eval_chunk_size, "val")
        logger.info(
            "[slot] epoch=%d loss=%.4f cov=%.4f count=%.4f train_acc=%.1f val_c1=%.2f",
            ep + 1,
            total / max(n, 1),
            cov_total / max(n, 1),
            count_total / max(n, 1),
            correct / max(n, 1) * 100,
            val_metrics["combo_1_valid"],
        )
        if val_metrics["combo_1_valid"] > best_c1:
            best_c1 = val_metrics["combo_1_valid"]
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    release_large_cache("train_data", train_data)
    release_large_cache("val", val_cache)
    del loader, train_ds, opt, best_state
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"model_state_dict": model.state_dict(), "args": jsonable_args(args), "best_val_c1": best_c1},
        args.output_dir / "slot_cross_reranker.pt",
    )
    test_cache, full_n = make_rank_cache(
        env, test_x, test_y, test_probs, chem_prior, data["precursor_X"], charge, args, "test")
    if not feature_ablation_is_model_side(args.feature_ablation):
        test_cache = apply_feature_ablation_cache(test_cache, feat_mask)
    metrics = evaluate(model, test_cache, full_n, device, args.eval_chunk_size, "test")
    size_log_prior = size_log_prior_from_labels(val_y)
    same_enum_metrics = evaluate_same_enum_independent_scorers(test_cache, full_n, size_log_prior)
    product_metrics = same_enum_metrics["product_prob"]
    if args.export_same_enum_artifact:
        export_same_enum_artifact(test_cache, full_n, args.export_same_enum_artifact, size_log_prior)
    if args.export_same_enum_compact_artifact:
        export_same_enum_compact_artifact(test_cache, full_n, args.export_same_enum_compact_artifact, size_log_prior)
    release_large_cache("test", test_cache)
    summary = {
        "best_val_c1": best_c1,
        "test_metrics": metrics,
        "product_rerank_metrics": product_metrics,
        "same_enum_independent_metrics": same_enum_metrics,
        "same_enum_size_log_prior": size_log_prior,
        "args": jsonable_args(args),
    }
    (args.output_dir / "slot_cross_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("[slot] summary=%s", summary)


def evaluate_checkpoint(args):
    device = args.device if args.device.startswith("cuda") and torch.cuda.is_available() else "cpu"
    data = prepare_data(make_data_args(args.cache_dir, args.dataset, args.data_path), device)
    probs = np.load(args.probs_path)
    charge = load_precursor_charge_matrix(
        args.precursor_charge_csv,
        data["precursor_id_mapping"],
        data["num_classes"],
    )
    if args.charge_mode == "zero":
        logger.info("Charge control: using all-zero charge matrix with charge branch enabled.")
        charge = np.zeros_like(charge)
    elif args.charge_mode == "shuffle":
        logger.info("Charge control: using row-shuffled charge matrix with charge branch enabled.")
        rng = np.random.default_rng(args.seed)
        charge = charge[rng.permutation(len(charge))]
    elif args.charge_mode == "none":
        logger.info("Charge control: disabling charge branch entirely.")
        args.disable_charge = True
    else:
        logger.info("Charge control: using real aligned charge matrix.")

    env = ExpertEnv(precursor_features=data["precursor_X"], max_precursors=8)
    chem_prior = ChemistryPriorV2(env, data["precursor_id_mapping"], data["X_train"], data["y_train"])
    anion_type_scores = apply_anion_prior_mode(chem_prior, data["y_train"], args.anion_prior_mode)
    if anion_type_scores:
        logger.info(
            "Anion prior mode=%s train-only type scores=%s",
            args.anion_prior_mode,
            {k: round(v, 4) for k, v in sorted(anion_type_scores.items())},
        )
    stats_transfer = apply_formula_train_stats_source(
        chem_prior,
        data["precursor_id_mapping"],
        args.cache_dir,
        args.dataset,
        args.train_stats_source,
        args.anion_prior_mode,
        args.train_stats_transfer_groups,
    )
    if stats_transfer["status"] != "skipped_same_dataset":
        logger.info("Train stats source transfer: %s", stats_transfer)

    feat_mask = feature_ablation_mask(args.feature_ablation)
    if feat_mask is not None:
        logger.info(
            "Feature ablation mode=%s keeps %d/%d feature dims",
            args.feature_ablation,
            int(feat_mask.sum()),
            TOTAL_FEAT_DIM,
        )
        if feature_ablation_is_model_side(args.feature_ablation):
            logger.info(
                "Feature mask is applied only to the descriptor scorer; "
                "raw generator probability remains available to the "
                "independent residual branch."
            )

    val_y = data["y_val"]
    test_x, test_y, test_probs = data["X_test"], data["y_test"], probs["test"]
    if args.sample_limit:
        val_y = val_y[:min(args.sample_limit, len(val_y))]
        test_x = test_x[:min(args.sample_limit, len(test_x))]
        test_y = test_y[:min(args.sample_limit, len(test_y))]
        test_probs = test_probs[:min(args.sample_limit, len(test_probs))]

    model, checkpoint = load_stage2_checkpoint(args.eval_checkpoint, device)
    best_c1 = float(checkpoint.get("best_val_c1", -1.0))

    test_cache, full_n = make_rank_cache(
        env, test_x, test_y, test_probs, chem_prior, data["precursor_X"], charge, args, "test")
    if not feature_ablation_is_model_side(args.feature_ablation):
        test_cache = apply_feature_ablation_cache(test_cache, feat_mask)
    metrics = evaluate(model, test_cache, full_n, device, args.eval_chunk_size, "test")
    size_log_prior = size_log_prior_from_labels(val_y)
    same_enum_metrics = evaluate_same_enum_independent_scorers(test_cache, full_n, size_log_prior)
    product_metrics = same_enum_metrics["product_prob"]
    if args.export_same_enum_artifact:
        export_same_enum_artifact(test_cache, full_n, args.export_same_enum_artifact, size_log_prior)
    if args.export_same_enum_compact_artifact:
        export_same_enum_compact_artifact(test_cache, full_n, args.export_same_enum_compact_artifact, size_log_prior)
    release_large_cache("test", test_cache)
    summary = {
        "best_val_c1": best_c1,
        "test_metrics": metrics,
        "product_rerank_metrics": product_metrics,
        "same_enum_independent_metrics": same_enum_metrics,
        "same_enum_size_log_prior": size_log_prior,
        "args": jsonable_args(args),
    }
    (args.output_dir / "slot_cross_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("[slot] eval checkpoint summary=%s", summary)


def evaluate_same_enum_only(args):
    """Build the Stage-2 test enumeration and evaluate model-free independent scorers."""
    device = args.device if args.device.startswith("cuda") and torch.cuda.is_available() else "cpu"
    data = prepare_data(make_data_args(args.cache_dir, args.dataset, args.data_path), device)
    probs = np.load(args.probs_path)
    charge = load_precursor_charge_matrix(
        args.precursor_charge_csv,
        data["precursor_id_mapping"],
        data["num_classes"],
    )
    if args.charge_mode == "zero":
        logger.info("Charge control: using all-zero charge matrix with charge branch enabled.")
        charge = np.zeros_like(charge)
    elif args.charge_mode == "shuffle":
        logger.info("Charge control: using row-shuffled charge matrix with charge branch enabled.")
        rng = np.random.default_rng(args.seed)
        charge = charge[rng.permutation(len(charge))]
    elif args.charge_mode == "none":
        logger.info("Charge control: disabling charge branch entirely.")
        args.disable_charge = True
    else:
        logger.info("Charge control: using real aligned charge matrix.")

    env = ExpertEnv(precursor_features=data["precursor_X"], max_precursors=8)
    chem_prior = ChemistryPriorV2(env, data["precursor_id_mapping"], data["X_train"], data["y_train"])
    apply_anion_prior_mode(chem_prior, data["y_train"], args.anion_prior_mode)
    apply_formula_train_stats_source(
        chem_prior,
        data["precursor_id_mapping"],
        args.cache_dir,
        args.dataset,
        args.train_stats_source,
        args.anion_prior_mode,
        args.train_stats_transfer_groups,
    )

    val_y = data["y_val"]
    test_x, test_y, test_probs = data["X_test"], data["y_test"], probs["test"]
    if args.sample_limit:
        val_y = val_y[:min(args.sample_limit, len(val_y))]
        test_x = test_x[:min(args.sample_limit, len(test_x))]
        test_y = test_y[:min(args.sample_limit, len(test_y))]
        test_probs = test_probs[:min(args.sample_limit, len(test_probs))]

    test_cache, full_n = make_rank_cache(
        env, test_x, test_y, test_probs, chem_prior, data["precursor_X"], charge, args, "test")
    size_log_prior = size_log_prior_from_labels(val_y)
    same_enum_metrics = evaluate_same_enum_independent_scorers(test_cache, full_n, size_log_prior)
    if args.export_same_enum_artifact:
        export_same_enum_artifact(test_cache, full_n, args.export_same_enum_artifact, size_log_prior)
    if args.export_same_enum_compact_artifact:
        export_same_enum_compact_artifact(test_cache, full_n, args.export_same_enum_compact_artifact, size_log_prior)
    release_large_cache("test", test_cache)
    summary = {
        "same_enum_independent_metrics": same_enum_metrics,
        "same_enum_size_log_prior": size_log_prior,
        "args": jsonable_args(args),
    }
    (args.output_dir / "same_enum_independent_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("[slot] same-enum-only summary=%s", summary)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--dataset", choices=["retro", "ceder"], default="retro")
    parser.add_argument("--data_path", default=None)
    parser.add_argument("--cache_dir", default=str(PACKAGE_ROOT / "artifacts" / "cache"))
    parser.add_argument("--output_dir", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=20260502)
    parser.add_argument("--max_elems", type=int, default=12)
    parser.add_argument("--dropout", type=float, default=0.12)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--sample_limit", type=int, default=0)
    parser.add_argument("--precursor_charge_csv", default=None)
    parser.add_argument("--charge_mode", choices=["real", "zero", "shuffle", "none"], default="real")
    parser.add_argument("--probs_path", type=Path, default=None)
    parser.add_argument("--top_m", type=int, default=30)
    parser.add_argument("--list_size", type=int, default=96)
    parser.add_argument("--n_augment", type=int, default=2)
    parser.add_argument("--num_workers", type=int, default=24)
    parser.add_argument("--worker_chunk_size", type=int, default=4)
    parser.add_argument(
        "--train_log_interval",
        type=int,
        default=100,
        help="Log Stage-2 training progress every N batches; set <=0 to disable batch logs.",
    )
    parser.add_argument("--hard_negative_fraction", type=float, default=0.25)
    parser.add_argument("--charge_scale", type=float, default=0.1)
    parser.add_argument("--coverage_weight", type=float, default=0.03)
    parser.add_argument("--count_weight", type=float, default=0.0)
    parser.add_argument(
        "--loss_mode",
        choices=["listwise", "bce"],
        default="listwise",
        help="listwise softmax ranking (paper) or per-candidate BCE control",
    )
    parser.add_argument("--margin_weight", type=float, default=0.08)
    parser.add_argument("--margin", type=float, default=0.3)
    parser.add_argument("--smoothing", type=float, default=0.03)
    parser.add_argument("--temperature", type=float, default=2.0)
    parser.add_argument("--num_slots", type=int, default=4)
    parser.add_argument(
        "--reranker_arch",
        choices=[
            "slot_cross",
            "descriptor_mlp",
            "linear_descriptor",
            "pointwise_set_token",
        ],
        default="slot_cross",
        help="Stage-2 architecture; non-slot-cross options are rebuttal controls.",
    )
    parser.add_argument(
        "--descriptor_mlp_hidden",
        default="256,128",
        help="Comma-separated hidden widths for the descriptor-MLP control.",
    )
    parser.add_argument("--eval_chunk_size", type=int, default=512)
    parser.add_argument("--eval_pool_cap", type=int, default=15)
    parser.add_argument("--eval_min_set_size", type=int, default=2)
    parser.add_argument("--eval_max_set_size", type=int, default=5)
    parser.add_argument(
        "--use_hard_metal_filter",
        action="store_true",
        default=True,
        help="Enable chemistry hard filter for candidate generation. Enabled by default.",
    )
    parser.add_argument(
        "--disable_hard_metal_filter",
        dest="use_hard_metal_filter",
        action="store_false",
        help="Disable chemistry hard filter for candidate generation.",
    )
    parser.add_argument(
        "--eval_keep_gt_for_cap",
        action="store_true",
        help="Legacy label-aware eval cap. Do not use for unbiased test metrics.",
    )
    parser.add_argument("--disable_features", action="store_true")
    parser.add_argument("--disable_charge", action="store_true")
    parser.add_argument("--disable_slot_cross", action="store_true")
    parser.add_argument("--disable_mixture_pool", action="store_true")
    parser.add_argument("--disable_prob_residual", action="store_true")
    parser.add_argument(
        "--anion_prior_mode",
        choices=["manual", "zero", "train_type_freq", "train_type_rate"],
        default="train_type_rate",
        help="How to fill ChemistryPriorV2 anion_leavability: manual heuristic, zero, or train-only type statistics.",
    )
    parser.add_argument(
        "--train_stats_source",
        choices=["self", "retro", "ceder"],
        default="self",
        help="Transfer train-derived chemistry stats from another dataset by exact precursor formula.",
    )
    parser.add_argument(
        "--train_stats_transfer_groups",
        default="all",
        help=(
            "Comma-separated subset of train-derived stats to transfer when train_stats_source "
            "is not self: pair_freq, precursor_freq, anion_leavability, or all."
        ),
    )
    parser.add_argument("--prob_residual_init", type=float, default=0.05)
    parser.add_argument("--freeze_prob_residual", action="store_true")
    parser.add_argument(
        "--feature_ablation",
        choices=(
            ["none"]
            + [f"no_{group}" for group in FEATURE_GROUPS]
            + [f"only_{group}" for group in FEATURE_GROUPS]
        ),
        default="none",
    )
    parser.add_argument(
        "--eval_checkpoint",
        type=Path,
        default=None,
        help="Load an existing slot_cross_reranker.pt and only run test evaluation.",
    )
    parser.add_argument(
        "--same_enum_only",
        action="store_true",
        help="Only build the Stage-2 test enumeration and evaluate/export independent same-enumeration scorers.",
    )
    parser.add_argument(
        "--export_same_enum_artifact",
        type=Path,
        default=None,
        help=(
            "Optional .jsonl or .jsonl.gz path for per-target same-enumeration diagnostics: "
            "candidate sets, Stage-1 pool probabilities, true-set index, and independent-scorer scores."
        ),
    )
    parser.add_argument(
        "--export_same_enum_compact_artifact",
        type=Path,
        default=None,
        help=(
            "Optional compact .jsonl or .jsonl.gz path with per-target ranks for same-enumeration "
            "independent scorers, suitable for supplemental release."
        ),
    )
    parser.add_argument(
        "--deterministic_training",
        action="store_true",
        help="Best-effort deterministic Stage-2 training diagnostics: disable TF32, use deterministic algorithms, and fix DataLoader shuffle generator.",
    )
    parser.add_argument(
        "--dataloader_seed_offset",
        type=int,
        default=0,
        help="Offset added to --seed for the deterministic DataLoader shuffle generator.",
    )
    parser.add_argument(
        "--diagnostic_batches",
        type=int,
        default=0,
        help="When deterministic diagnostics are enabled, log fingerprints for the first N batches per epoch.",
    )
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.output_dir is None:
        args.output_dir = PACKAGE_ROOT / "artifacts" / "runs" / args.dataset / "stage2"
    if args.precursor_charge_csv is None:
        args.precursor_charge_csv = str(default_charge_path(args.dataset))
    if args.probs_path is None:
        args.probs_path = PACKAGE_ROOT / "artifacts" / "runs" / args.dataset / "stage1" / "stage1_probs.npz"
    if args.eval_min_set_size < 1 or args.eval_max_set_size < args.eval_min_set_size:
        parser.error("--eval_min_set_size must be >=1 and <= --eval_max_set_size")
    if args.reranker_arch in {"descriptor_mlp", "linear_descriptor"} and (
        args.coverage_weight != 0.0 or args.count_weight != 0.0
    ):
        parser.error(
            "Descriptor-only rerankers require "
            "--coverage_weight 0 --count_weight 0"
        )
    if args.smoke:
        args.output_dir = args.output_dir / "smoke"
        args.epochs = min(args.epochs, 1)
        args.sample_limit = args.sample_limit or 128
        args.list_size = min(args.list_size, 32)
        args.n_augment = 1
        args.num_workers = min(args.num_workers, 2)
    configure_deterministic_training(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    fh = logging.FileHandler(args.output_dir / "slot_cross.log")
    fh.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logging.getLogger().addHandler(fh)
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    logger.info("Args: %s", vars(args))
    if args.deterministic_training:
        logger.info(
            "[diag] deterministic_training enabled cublas_workspace=%s tf32_matmul=%s tf32_cudnn=%s cudnn_benchmark=%s cudnn_deterministic=%s deterministic_algorithms=%s sdp=%s",
            os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
            torch.backends.cuda.matmul.allow_tf32,
            torch.backends.cudnn.allow_tf32,
            torch.backends.cudnn.benchmark,
            torch.backends.cudnn.deterministic,
            torch.are_deterministic_algorithms_enabled(),
            _cuda_sdp_status(),
        )
    logger.info(
        "Stage2 architecture=%s toggles: features=%s charge=%s slot_cross=%s "
        "mixture_pool=%s prob_residual=%s coverage_weight=%.4f count_weight=%.4f charge_mode=%s",
        args.reranker_arch,
        not args.disable_features,
        not args.disable_charge,
        not args.disable_slot_cross,
        not args.disable_mixture_pool,
        not args.disable_prob_residual,
        args.coverage_weight,
        args.count_weight,
        args.charge_mode,
    )
    logger.info("Feature ablation: %s", args.feature_ablation)
    logger.info(
        "Anion prior mode=%s prob_residual_init=%.4f freeze_prob_residual=%s",
        args.anion_prior_mode,
        args.prob_residual_init,
        args.freeze_prob_residual,
    )
    if args.same_enum_only:
        evaluate_same_enum_only(args)
    elif args.eval_checkpoint is not None:
        evaluate_checkpoint(args)
    else:
        train(args)


if __name__ == "__main__":
    main()
