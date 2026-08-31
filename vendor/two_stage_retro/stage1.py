#!/usr/bin/env python3
"""Two-stage formula-token Transformer retriever and reranker.

This experiment deliberately does not import or instantiate CrabNetEncoder.
It keeps the useful idea (element tokens + stoichiometry + physical/valence
features + Transformer blocks) but implements the block locally.
"""
from __future__ import annotations

import argparse
import ast
import itertools
import json
import logging
import math
import os
import random
import sys
import time
import warnings
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Sequence

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
EXP_ROOT = PACKAGE_ROOT
PROJECT_ROOT = PACKAGE_ROOT

from .env import ExpertEnv, VOLATILE_ELEMENTS  # noqa: E402
from .data import default_charge_path, prepare_data  # noqa: E402
from .chemistry import ChemistryPriorV2, TOTAL_FEAT_DIM, extract_full_features  # noqa: E402


logger = logging.getLogger(__name__)
NUM_ELEMENTS = 118
PHYSICAL_FEATURE_IDXS = [0, 1, 2, 3]
VALENCE_FEATURE_IDXS = [4, 5, 6, 7, 8, 9]
MAIN_KS = (1, 3, 5, 10, 20)
_TRAIN_STATE = {}
_CACHE_STATE = {}


def jsonable_args(args) -> Dict[str, object]:
    out = {}
    for key, value in vars(args).items():
        out[key] = str(value) if isinstance(value, Path) else value
    return out


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def build_element_phys_table() -> np.ndarray:
    """Build a physical/valence table without depending on CrabNet code."""
    warnings.filterwarnings("ignore", message="No Pauling electronegativity")
    table = np.zeros((NUM_ELEMENTS + 1, 10), dtype=np.float32)
    try:
        from pymatgen.core import Element
    except Exception:
        for z in range(1, NUM_ELEMENTS + 1):
            table[z, 0] = z / 118.0
        return table

    xs, rs, masses = [], [], []
    for z in range(1, NUM_ELEMENTS + 1):
        try:
            e = Element.from_Z(z)
            if e.X is not None and not (isinstance(e.X, float) and np.isnan(e.X)):
                xs.append(float(e.X))
            if e.atomic_radius is not None:
                rs.append(float(e.atomic_radius))
            if e.atomic_mass is not None:
                masses.append(float(e.atomic_mass))
        except Exception:
            pass
    x_mean = float(np.mean(xs)) if xs else 1.8
    r_mean = float(np.mean(rs)) if rs else 1.5
    m_mean = float(np.mean(masses)) if masses else 100.0

    for z in range(1, NUM_ELEMENTS + 1):
        try:
            e = Element.from_Z(z)
            x = float(e.X) if e.X is not None and not (isinstance(e.X, float) and np.isnan(e.X)) else x_mean
            radius = float(e.atomic_radius) if e.atomic_radius is not None else r_mean
            mass = float(e.atomic_mass) if e.atomic_mass is not None else m_mean
            group = int(e.group) if e.group is not None else 0
            row = int(e.row) if e.row is not None else 0
            try:
                valence = int(e.valence[1]) if e.valence is not None else 0
            except Exception:
                valence = 0
            table[z] = [
                z / 118.0,
                x / 4.0,
                radius / 3.0,
                mass / 300.0,
                group / 18.0,
                row / 9.0,
                valence / 8.0,
                float(e.is_metal),
                float(e.is_transition_metal),
                float(e.is_alkali or e.is_alkaline),
            ]
        except Exception:
            table[z] = [z / 118.0, x_mean / 4.0, r_mean / 3.0, m_mean / 300.0, 0, 0, 0, 0, 0, 0]
    return table


def composition_to_sparse(comp_vec: np.ndarray, max_elems: int = 12, eps: float = 1e-6):
    comp = comp_vec / comp_vec.sum() if comp_vec.sum() > 0 else comp_vec
    idxs = np.where(comp > eps)[0]
    fracs = comp[idxs]
    order = np.argsort(-fracs)[:max_elems]
    return idxs[order] + 1, fracs[order]


def comp_to_sparse_arrays(comp: np.ndarray, max_elems: int = 12):
    elem, frac = composition_to_sparse(comp, max_elems=max_elems)
    elem_out = np.zeros(max_elems, dtype=np.int64)
    frac_out = np.zeros(max_elems, dtype=np.float32)
    mask_out = np.zeros(max_elems, dtype=bool)
    n = len(elem)
    if n:
        elem_out[:n] = elem
        frac_out[:n] = frac
        mask_out[:n] = True
    return elem_out, frac_out, mask_out


def dense_to_sparse_batch(X: np.ndarray, max_elems: int = 12):
    elems, fracs, masks = [], [], []
    for row in X:
        e, f, m = comp_to_sparse_arrays(row, max_elems=max_elems)
        elems.append(e)
        fracs.append(f)
        masks.append(m)
    return (
        np.asarray(elems, dtype=np.int64),
        np.asarray(fracs, dtype=np.float32),
        np.asarray(masks, dtype=bool),
    )


def set_to_composition_vec(pset: Sequence[int], precursor_x: np.ndarray) -> np.ndarray:
    if not pset:
        return np.zeros(precursor_x.shape[1], dtype=np.float32)
    return np.sum([precursor_x[p] for p in pset], axis=0).astype(np.float32)


def set_to_charge_vec(pset: Sequence[int], charge_x: np.ndarray | None) -> np.ndarray:
    if charge_x is None or not pset:
        return np.zeros(118, dtype=np.float32)
    return np.mean([charge_x[p] for p in pset], axis=0).astype(np.float32)


class FormulaTransformerEncoder(nn.Module):
    """Local formula-token Transformer block, inspired by but not using CrabNet.

    The 10-d element table is split into physical properties
    (Z/electronegativity/radius/mass) and valence/periodic/type features
    (group/row/valence/metal flags) for ablation.
    """

    def __init__(
        self,
        d_emb=32,
        d_model=96,
        num_heads=4,
        num_layers=2,
        dropout=0.1,
        use_element_embedding=True,
        use_phys_features=True,
        use_physical_features=None,
        use_valence_features=None,
        use_fraction=True,
        use_self_attention=True,
    ):
        super().__init__()
        self.elem_emb = nn.Embedding(NUM_ELEMENTS + 1, d_emb, padding_idx=0)
        self.register_buffer("phys_table", torch.tensor(build_element_phys_table(), dtype=torch.float32))
        self.use_element_embedding = use_element_embedding
        self.use_phys_features = use_phys_features
        if use_physical_features is None:
            use_physical_features = use_phys_features
        if use_valence_features is None:
            use_valence_features = use_phys_features
        self.use_physical_features = use_physical_features
        self.use_valence_features = use_valence_features
        feature_mask = torch.zeros(10, dtype=torch.float32)
        if use_physical_features:
            feature_mask[PHYSICAL_FEATURE_IDXS] = 1.0
        if use_valence_features:
            feature_mask[VALENCE_FEATURE_IDXS] = 1.0
        self.register_buffer("phys_feature_mask", feature_mask.view(1, 1, -1))
        self.use_fraction = use_fraction
        self.use_self_attention = use_self_attention
        self.input_proj = nn.Sequential(
            nn.Linear(d_emb + 10 + 1, d_model),
            nn.LayerNorm(d_model),
            nn.GELU(),
        )
        self.cls = nn.Parameter(torch.randn(1, 1, d_model) * 0.02)
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=num_heads,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=num_layers)
        self.out_norm = nn.LayerNorm(d_model)

    def forward(self, elem_idx: torch.Tensor, fracs: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        elem_part = self.elem_emb(elem_idx.long())
        if not self.use_element_embedding:
            elem_part = torch.zeros_like(elem_part)
        phys_part = self.phys_table[elem_idx.long()]
        phys_part = phys_part * self.phys_feature_mask.to(phys_part.dtype)
        frac_part = fracs.float().unsqueeze(-1)
        if not self.use_fraction:
            frac_part = torch.zeros_like(frac_part)
        tok = torch.cat([elem_part, phys_part, frac_part], dim=-1)
        h = self.input_proj(tok)
        if not self.use_self_attention:
            weights = mask.float().unsqueeze(-1)
            pooled = (h * weights).sum(dim=1) / weights.sum(dim=1).clamp_min(1.0)
            return self.out_norm(pooled)
        cls = self.cls.expand(h.size(0), -1, -1)
        h = torch.cat([cls, h], dim=1)
        key_pad = torch.cat([
            torch.zeros(h.size(0), 1, dtype=torch.bool, device=h.device),
            ~mask.bool(),
        ], dim=1)
        h = self.encoder(h, src_key_padding_mask=key_pad)
        return self.out_norm(h[:, 0])


class Stage1Retriever(nn.Module):
    def __init__(
        self,
        num_precursors: int,
        d_formula=96,
        d_model=192,
        dropout=0.1,
        use_element_embedding=True,
        use_phys_features=True,
        use_physical_features=None,
        use_valence_features=None,
        use_fraction=True,
        share_formula_encoder=True,
        hybrid_formula_encoder=False,
        hybrid_formula_encoder_mode="concat",
        hybrid_private_scale=1.0,
        use_formula_self_attention=True,
        charge_integration="add",
        charge_scale_init=0.1,
    ):
        super().__init__()
        self.hybrid_formula_encoder = hybrid_formula_encoder
        if hybrid_formula_encoder_mode not in {"concat", "residual", "logit_fusion"}:
            raise ValueError(f"Unknown hybrid_formula_encoder_mode={hybrid_formula_encoder_mode!r}")
        self.hybrid_formula_encoder_mode = hybrid_formula_encoder_mode
        self.hybrid_private_scale = float(hybrid_private_scale)
        if charge_integration not in {"add", "gated"}:
            raise ValueError(f"Unknown charge_integration={charge_integration!r}")
        self.charge_integration = charge_integration
        encoder_kwargs = dict(
            d_model=d_formula,
            dropout=dropout,
            use_element_embedding=use_element_embedding,
            use_phys_features=use_phys_features,
            use_physical_features=use_physical_features,
            use_valence_features=use_valence_features,
            use_fraction=use_fraction,
            use_self_attention=use_formula_self_attention,
        )
        self.target_encoder = FormulaTransformerEncoder(**encoder_kwargs)
        self.target_private_encoder = FormulaTransformerEncoder(**encoder_kwargs) if hybrid_formula_encoder else None
        self.precursor_encoder = (
            FormulaTransformerEncoder(**encoder_kwargs)
            if hybrid_formula_encoder or not share_formula_encoder
            else None
        )
        formula_dim = d_formula * 2 if hybrid_formula_encoder and hybrid_formula_encoder_mode == "concat" else d_formula
        self.target_proj = nn.Sequential(nn.Linear(formula_dim, d_model), nn.LayerNorm(d_model), nn.GELU())
        self.precursor_proj = nn.Sequential(nn.Linear(formula_dim, d_model), nn.LayerNorm(d_model), nn.GELU())
        if hybrid_formula_encoder and hybrid_formula_encoder_mode == "logit_fusion":
            self.target_private_proj = nn.Sequential(nn.Linear(d_formula, d_model), nn.LayerNorm(d_model), nn.GELU())
            self.precursor_private_proj = nn.Sequential(nn.Linear(d_formula, d_model), nn.LayerNorm(d_model), nn.GELU())
            self.private_scale = nn.Parameter(torch.tensor(d_model ** -0.5))
            self.private_bias = nn.Parameter(torch.zeros(num_precursors))
            self.private_gate = nn.Sequential(nn.Linear(d_model * 2, d_model), nn.GELU(), nn.Linear(d_model, 1))
            self.logit_fusion_alpha = nn.Parameter(torch.tensor(0.0))
        else:
            self.target_private_proj = None
            self.precursor_private_proj = None
            self.private_scale = None
            self.private_bias = None
            self.private_gate = None
            self.logit_fusion_alpha = None
        self.charge_proj = nn.Sequential(nn.Linear(118, d_model), nn.LayerNorm(d_model), nn.GELU())
        self.charge_gate = nn.Sequential(nn.Linear(d_model * 2, d_model), nn.GELU(), nn.Linear(d_model, 1))
        self.charge_scale = nn.Parameter(torch.tensor(float(charge_scale_init)))
        self.scale = nn.Parameter(torch.tensor(d_model ** -0.5))
        self.bias = nn.Parameter(torch.zeros(num_precursors))
        self.gate = nn.Sequential(nn.Linear(d_model * 2, d_model), nn.GELU(), nn.Linear(d_model, 1))

    def set_hybrid_private_scale(self, scale: float) -> None:
        self.hybrid_private_scale = float(scale)

    def apply_charge(self, memory: torch.Tensor, charge: torch.Tensor | None) -> torch.Tensor:
        if charge is None:
            return memory
        charge_emb = self.charge_proj(charge.float())
        if self.charge_integration == "gated":
            gate = torch.sigmoid(self.charge_gate(torch.cat([memory, charge_emb], dim=-1)))
            charge_emb = gate * charge_emb
        return memory + self.charge_scale * charge_emb

    def encode_target(self, elem, frac, mask):
        shared = self.target_encoder(elem, frac, mask)
        if self.hybrid_formula_encoder:
            assert self.target_private_encoder is not None
            private = self.hybrid_private_scale * self.target_private_encoder(elem, frac, mask)
            if self.hybrid_formula_encoder_mode == "concat":
                shared = torch.cat([shared, private], dim=-1)
            else:
                shared = shared + private
        return self.target_proj(shared)

    def encode_precursors(self, elem, frac, mask, charge=None):
        if self.hybrid_formula_encoder:
            assert self.precursor_encoder is not None
            shared = self.target_encoder(elem, frac, mask)
            private = self.hybrid_private_scale * self.precursor_encoder(elem, frac, mask)
            if self.hybrid_formula_encoder_mode == "concat":
                formula_repr = torch.cat([shared, private], dim=-1)
            else:
                formula_repr = shared + private
        else:
            encoder = self.target_encoder if self.precursor_encoder is None else self.precursor_encoder
            formula_repr = encoder(elem, frac, mask)
        mem = self.precursor_proj(formula_repr)
        return self.apply_charge(mem, charge)

    def logits_from_memory(self, target_emb, precursor_memory, scale=None, bias=None, gate=None):
        scale = self.scale if scale is None else scale
        bias = self.bias if bias is None else bias
        gate = self.gate if gate is None else gate
        dot = torch.matmul(target_emb, precursor_memory.t()) * scale
        target_rep = target_emb.unsqueeze(1).expand(-1, precursor_memory.size(0), -1)
        precursor_rep = precursor_memory.unsqueeze(0).expand(target_emb.size(0), -1, -1)
        return dot + gate(torch.cat([target_rep, precursor_rep], dim=-1)).squeeze(-1) + bias

    def forward(self, target_elem, target_frac, target_mask, precursor_elem, precursor_frac, precursor_mask, charge=None):
        if self.hybrid_formula_encoder and self.hybrid_formula_encoder_mode == "logit_fusion":
            assert self.target_private_encoder is not None
            assert self.precursor_encoder is not None
            assert self.target_private_proj is not None
            assert self.precursor_private_proj is not None
            assert self.private_scale is not None
            assert self.private_bias is not None
            assert self.private_gate is not None
            assert self.logit_fusion_alpha is not None

            shared_target = self.target_proj(self.target_encoder(target_elem, target_frac, target_mask))
            shared_memory = self.precursor_proj(self.target_encoder(precursor_elem, precursor_frac, precursor_mask))
            private_target = self.target_private_proj(
                self.target_private_encoder(target_elem, target_frac, target_mask)
            )
            private_memory = self.precursor_private_proj(
                self.precursor_encoder(precursor_elem, precursor_frac, precursor_mask)
            )
            if charge is not None:
                shared_memory = self.apply_charge(shared_memory, charge)
                private_memory = self.apply_charge(private_memory, charge)
            shared_logits = self.logits_from_memory(shared_target, shared_memory)
            private_logits = self.logits_from_memory(
                private_target,
                private_memory,
                scale=self.private_scale,
                bias=self.private_bias,
                gate=self.private_gate,
            )
            alpha = self.hybrid_private_scale * torch.sigmoid(self.logit_fusion_alpha)
            return (1.0 - alpha) * shared_logits + alpha * private_logits

        target_emb = self.encode_target(target_elem, target_frac, target_mask)
        memory = self.encode_precursors(precursor_elem, precursor_frac, precursor_mask, charge)
        return self.logits_from_memory(target_emb, memory)


class Stage2FormulaSetReranker(nn.Module):
    def __init__(self, feat_dim=TOTAL_FEAT_DIM, d_formula=64, d_token=192, num_heads=4,
                 num_layers=2, dropout=0.15, charge_scale=0.0):
        super().__init__()
        self.encoder = FormulaTransformerEncoder(d_model=d_formula, num_heads=num_heads, dropout=dropout)
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
        pair_dim = 128 + d_formula * 4 + 16 + 32
        self.pair_proj = nn.Sequential(nn.Linear(pair_dim, d_token), nn.LayerNorm(d_token), nn.GELU(), nn.Dropout(dropout))
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
        self.score_head = nn.Sequential(nn.LayerNorm(d_token), nn.Linear(d_token, d_token // 2), nn.GELU(), nn.Dropout(dropout), nn.Linear(d_token // 2, 1))
        self.prob_residual = nn.Parameter(torch.tensor(0.05))

    def forward(self, feats, target_elem, target_frac, target_mask, cand_elem, cand_frac, cand_mask, sizes, cand_charge=None):
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
        target_emb = self.encoder(target_elem.long(), target_frac.float(), target_mask.bool())
        target_rep = target_emb.unsqueeze(1).expand(bsz, list_len, -1)
        flat_elem = cand_elem.reshape(bsz * list_len, -1).long()
        flat_frac = cand_frac.reshape(bsz * list_len, -1).float()
        flat_mask = cand_mask.reshape(bsz * list_len, -1).bool()
        cand_emb = self.encoder(flat_elem, flat_frac, flat_mask).view(bsz, list_len, -1)
        feat_emb = self.feature_proj(feats.float())
        size_emb = self.size_proj((sizes.float() / 8.0).unsqueeze(-1))
        if cand_charge is None:
            charge_emb = torch.zeros(bsz, list_len, 32, device=feats.device)
        else:
            charge_emb = self.charge_scale * self.charge_proj(cand_charge.float())
        pair = torch.cat([
            feat_emb,
            target_rep,
            cand_emb,
            torch.abs(target_rep - cand_emb),
            target_rep * cand_emb,
            size_emb,
            charge_emb,
        ], dim=-1)
        tokens = self.list_encoder(self.pair_proj(pair))
        scores = self.score_head(tokens).squeeze(-1)
        base_prob = feats[..., 0].clamp(min=1e-8)
        return scores + self.prob_residual * torch.log(base_prob)


class RetrievalDataset(Dataset):
    def __init__(self, X: np.ndarray, y: np.ndarray, max_elems=12):
        self.elem, self.frac, self.mask = dense_to_sparse_batch(X, max_elems)
        self.y = y.astype(np.float32)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.elem[idx], self.frac[idx], self.mask[idx], self.y[idx]


class FormulaListDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data["feats"])

    def __getitem__(self, idx):
        return (
            self.data["feats"][idx],
            self.data["target_elem"][idx],
            self.data["target_frac"][idx],
            self.data["target_mask"][idx],
            self.data["cand_elem"][idx],
            self.data["cand_frac"][idx],
            self.data["cand_mask"][idx],
            self.data["sizes"][idx],
            self.data["cand_charge"][idx],
            np.int64(0),
        )


def make_candidate_arrays(combos, max_set_size=6):
    ids = np.zeros((len(combos), max_set_size), dtype=np.int64)
    mask = np.zeros((len(combos), max_set_size), dtype=bool)
    for i, combo in enumerate(combos):
        combo = list(combo)[:max_set_size]
        if combo:
            ids[i, :len(combo)] = combo
            mask[i, :len(combo)] = True
    return ids, mask


def combos_to_arrays(combos, probs, target_features, pke, pm, chem_prior, precursor_x, charge_x=None, max_elems=12):
    feats, elems, fracs, masks, sizes, charges = [], [], [], [], [], []
    for combo in combos:
        combo = list(combo)
        feats.append(extract_full_features(combo, probs, target_features, pke, pm, chem_prior))
        comp = set_to_composition_vec(combo, precursor_x)
        elem, frac, mask = comp_to_sparse_arrays(comp, max_elems=max_elems)
        elems.append(elem)
        fracs.append(frac)
        masks.append(mask)
        sizes.append(len(combo))
        charges.append(set_to_charge_vec(combo, charge_x))
    return {
        "feats": np.asarray(feats, dtype=np.float32),
        "cand_elem": np.asarray(elems, dtype=np.int64),
        "cand_frac": np.asarray(fracs, dtype=np.float32),
        "cand_mask": np.asarray(masks, dtype=bool),
        "sizes": np.asarray(sizes, dtype=np.float32),
        "cand_charge": np.asarray(charges, dtype=np.float32),
    }


def load_precursor_charge_matrix(charge_csv, precursor_id_map, num_precursors):
    if not charge_csv:
        return np.zeros((num_precursors, 118), dtype=np.float32)
    from pymatgen.core import Element
    df = pd.read_csv(charge_csv)
    charge_mat = np.zeros((num_precursors, 118), dtype=np.float32)
    matched = mismatched = 0
    for _, row in df.iterrows():
        pid = int(row.iloc[0])
        if pid < 0 or pid >= num_precursors:
            continue
        formula = str(row["formula"])
        expected = precursor_id_map.get(str(pid), [""])[0]
        if expected and formula != expected:
            mismatched += 1
        else:
            matched += 1
        try:
            elements = ast.literal_eval(row["elements"])
            counts = ast.literal_eval(row["counts"])
            charges = ast.literal_eval(row["charges"])
        except Exception:
            continue
        acc, weight = {}, {}
        for elem, count, charge in zip(elements, counts, charges):
            try:
                z = Element(str(elem)).Z - 1
                c = float(count)
                q = float(charge)
            except Exception:
                continue
            acc[z] = acc.get(z, 0.0) + c * q
            weight[z] = weight.get(z, 0.0) + abs(c)
        for z, val in acc.items():
            if weight.get(z, 0.0) > 0:
                charge_mat[pid, z] = np.clip(val / weight[z] / 8.0, -2.0, 2.0)
    logger.info("Loaded charge memory: matched=%d mismatched=%d nonzero=%d", matched, mismatched, int(np.count_nonzero(charge_mat)))
    return charge_mat


def make_data_args(cache_dir, dataset="retro", data_path=None):
    a = SimpleNamespace()
    a.dataset = dataset
    a.cache_dir = str(cache_dir)
    a.data_path = data_path or str(PACKAGE_ROOT / "data" / f"{dataset}_split.csv")
    return a


def precursor_tensors(data, charge_matrix, max_elems, device):
    e, f, m = dense_to_sparse_batch(data["precursor_X"], max_elems=max_elems)
    charge_tensor = None
    if charge_matrix is not None:
        charge_tensor = torch.as_tensor(charge_matrix, dtype=torch.float32, device=device)
    return (
        torch.as_tensor(e, device=device),
        torch.as_tensor(f, dtype=torch.float32, device=device),
        torch.as_tensor(m, dtype=torch.bool, device=device),
        charge_tensor,
    )


@torch.no_grad()
def predict_retriever(model, X, precursor_pack, device, max_elems=12, batch_size=256):
    model.eval()
    elems, fracs, masks = dense_to_sparse_batch(X, max_elems=max_elems)
    pe, pf, pm, pc = precursor_pack
    out = []
    for i in range(0, len(X), batch_size):
        te = torch.as_tensor(elems[i:i + batch_size], device=device)
        tf = torch.as_tensor(fracs[i:i + batch_size], dtype=torch.float32, device=device)
        tm = torch.as_tensor(masks[i:i + batch_size], dtype=torch.bool, device=device)
        logits = model(te, tf, tm, pe, pf, pm, pc)
        out.append(torch.sigmoid(logits).cpu().numpy())
    return np.concatenate(out, axis=0)


def precursor_topk_metrics(y, probs, topks=MAIN_KS, use_pred_threshold=False, pred_threshold=0.5):
    """Top-k precursor coverage.

    By default this follows final_experiments with use_pred_threshold=False:
    the true precursor count is used as the minimum number of ranked labels to
    inspect, i.e. check_k = max(k, true_set_size). Threshold mode is retained
    only for legacy diagnostics.
    """
    metrics = {}
    valid = sum(1 for row in y if np.sum(row > 0) > 0)
    for k in topks:
        hit = 0
        for i in range(len(y)):
            true_ids = set(np.where(y[i] > 0)[0].tolist())
            if not true_ids:
                continue
            check_k = k
            if use_pred_threshold:
                pred_labels = np.where(probs[i] > pred_threshold)[0]
                if len(pred_labels) != len(true_ids):
                    continue
                check_k = max(k, len(pred_labels))
            else:
                check_k = max(k, len(true_ids))
            if true_ids.issubset(set(np.argsort(-probs[i])[:check_k].tolist())):
                hit += 1
        metrics[f"top_{k}"] = hit / max(len(y), 1) * 100
        metrics[f"top_{k}_valid"] = hit / max(valid, 1) * 100
    metrics["valid"] = valid
    metrics["full_denominator"] = len(y)
    metrics["use_pred_threshold"] = use_pred_threshold
    metrics["pred_threshold"] = pred_threshold
    return metrics


def coverage_topk_metrics(y, probs, topks=MAIN_KS):
    """Length-agnostic coverage metric retained for validation checkpoint choice."""
    return precursor_topk_metrics(y, probs, topks)


def oracle_metrics(y, probs, topks=(20, 50)):
    """Backward-compatible candidate coverage metrics used by existing reports."""
    metrics = {}
    valid = sum(1 for row in y if np.sum(row > 0) >= 2)
    for k in topks:
        hit = 0
        for i in range(len(y)):
            true_ids = set(np.where(y[i] > 0)[0].tolist())
            if len(true_ids) < 2:
                continue
            if true_ids.issubset(set(np.argsort(-probs[i])[:k].tolist())):
                hit += 1
        metrics[f"oracle@{k}"] = hit / max(valid, 1) * 100
    metrics["valid"] = valid
    return metrics


def stage1_combo_metrics(env, X, y, probs, chem_prior, precursor_x, charge_x, args, split):
    """Rank precursor sets with the Stage-1 precursor probabilities."""
    if getattr(args, "use_pred_threshold_metrics", False):
        top_candidates = int(getattr(args, "eval_pool_cap", 0) or getattr(args, "top_m", 20))
        return threshold_combo_metrics(
            y,
            probs,
            topks=MAIN_KS,
            top_candidates=top_candidates,
            pred_threshold=float(getattr(args, "pred_threshold", 0.5)),
        )
    cache, valid = make_rank_cache(env, X, y, probs, chem_prior, precursor_x, charge_x, args, split)
    hits = {k: 0 for k in MAIN_KS}
    rr_sum = 0.0
    scored = 0
    ranks = []
    for i, sample in enumerate(cache, 1):
        ci = sample["correct_idx"]
        if ci is None:
            continue
        scored += 1
        # In threshold mode this is the product of probabilities, matching
        # final_experiments/ours/utils/general_utils.py.
        scores = sample.get("product_scores", sample["feats"][:, 0])
        rank = int(np.sum(scores > scores[ci]))
        rank_1based = rank + 1
        rr_sum += 1.0 / rank_1based
        ranks.append(rank_1based)
        for k in MAIN_KS:
            if rank < k:
                hits[k] += 1
        if i % 200 == 0:
            logger.info("  %s stage1-combo eval %d/%d", split, i, len(cache))

    metrics = {}
    for k in MAIN_KS:
        metrics[f"combo_{k}"] = hits[k] / max(len(y), 1) * 100
        metrics[f"combo_{k}_valid"] = hits[k] / max(valid, 1) * 100
        metrics[f"combo_{k}_scored"] = hits[k] / max(scored, 1) * 100
    metrics["mrr"] = rr_sum / max(len(y), 1)
    metrics["mrr_valid"] = rr_sum / max(valid, 1)
    metrics["mrr_scored"] = rr_sum / max(scored, 1)
    metrics["valid"] = valid
    metrics["scored"] = scored
    metrics["full_denominator"] = len(y)
    metrics["avg_candidates"] = int(np.mean([len(sample["combos"]) for sample in cache])) if cache else 0
    metrics["mean_rank_scored"] = float(np.mean(ranks)) if ranks else 0.0
    metrics["median_rank_scored"] = float(np.median(ranks)) if ranks else 0.0
    logger.info("%s stage1-combo metrics: %s", split, metrics)
    return metrics


def threshold_combo_metrics(y, probs, topks=MAIN_KS, top_candidates=20, pred_threshold=0.5):
    """Combo-k aligned with final_experiments calculate_combination_accuracy.

    The predicted set size is inferred from p > pred_threshold. If that size
    differs from the true set size, the sample misses every k. Candidate labels
    are the top `top_candidates` probabilities without chemistry filtering.
    Combinations of the inferred size are ranked by probability product.
    """
    max_k = max(topks)
    hits = {k: 0 for k in topks}
    rr_sum = 0.0
    ranks = []
    valid = 0
    scored = 0
    candidate_counts = []

    for i in range(len(y)):
        true_idx = np.where(y[i] > 0)[0]
        if len(true_idx) == 0:
            continue
        valid += 1
        true_set = tuple(sorted(true_idx.tolist()))
        pred_labels = np.where(probs[i] > pred_threshold)[0]
        if len(pred_labels) != len(true_set):
            continue
        combination_size = len(pred_labels)
        candidates = np.argsort(-probs[i])[: min(top_candidates, probs.shape[1])]
        if combination_size <= 0 or combination_size > len(candidates):
            continue

        combos = list(itertools.combinations(candidates.tolist(), combination_size))
        candidate_counts.append(len(combos))
        if not combos:
            continue
        normalized_combos = [tuple(sorted(combo)) for combo in combos]
        try:
            correct_idx = normalized_combos.index(true_set)
        except ValueError:
            continue
        product_values = np.asarray([float(np.prod(probs[i, list(combo)])) for combo in combos], dtype=np.float64)
        rank = int(np.sum(product_values > product_values[correct_idx]))
        scored += 1
        rank_1based = rank + 1
        ranks.append(rank_1based)
        rr_sum += 1.0 / rank_1based
        for k in topks:
            if rank < k:
                hits[k] += 1

    metrics = {}
    for k in topks:
        metrics[f"combo_{k}"] = hits[k] / max(len(y), 1) * 100
        metrics[f"combo_{k}_valid"] = hits[k] / max(valid, 1) * 100
        metrics[f"combo_{k}_scored"] = hits[k] / max(scored, 1) * 100
    metrics["mrr"] = rr_sum / max(len(y), 1)
    metrics["mrr_valid"] = rr_sum / max(valid, 1)
    metrics["mrr_scored"] = rr_sum / max(scored, 1)
    metrics["valid"] = valid
    metrics["scored"] = scored
    metrics["full_denominator"] = len(y)
    metrics["avg_candidates"] = int(np.mean(candidate_counts)) if candidate_counts else 0
    metrics["mean_rank_scored"] = float(np.mean(ranks)) if ranks else 0.0
    metrics["median_rank_scored"] = float(np.median(ranks)) if ranks else 0.0
    metrics["top_candidates"] = top_candidates
    metrics["pred_threshold"] = pred_threshold
    return metrics


def merge_stage1_metrics(top_metrics, combo_metrics):
    metrics = dict(top_metrics)
    metrics.update(combo_metrics)
    metrics["main_metrics_11"] = {
        **{f"top_{k}": metrics[f"top_{k}"] for k in MAIN_KS},
        **{f"combo_{k}": metrics[f"combo_{k}"] for k in MAIN_KS},
        "mrr": metrics["mrr"],
    }
    return metrics


def stage1_selection_score(y, probs, metric: str) -> float:
    if metric == "top_20":
        return coverage_topk_metrics(y, probs, (20,))["top_20"]
    if metric == "oracle_20":
        return oracle_metrics(y, probs, (20,))["oracle@20"]
    if metric == "oracle_50":
        return oracle_metrics(y, probs, (50,))["oracle@50"]
    raise ValueError(f"Unknown stage1_select_metric: {metric}")


def train_stage1(args):
    if args.hybrid_formula_encoder and args.separate_formula_encoders:
        raise ValueError(
            "--hybrid_formula_encoder already includes role-specific private encoders; "
            "do not combine it with --separate_formula_encoders."
        )
    device = args.device if args.device.startswith("cuda") and torch.cuda.is_available() else "cpu"
    data = prepare_data(make_data_args(args.cache_dir, args.dataset, args.data_path), device)
    charge = load_precursor_charge_matrix(args.precursor_charge_csv, data["precursor_id_mapping"], data["num_classes"])
    if args.stage1_charge_mode == "zero":
        logger.info("Stage1 charge control: using all-zero charge memory.")
        charge = np.zeros_like(charge)
    elif args.stage1_charge_mode == "shuffle":
        logger.info("Stage1 charge control: using row-shuffled charge memory.")
        rng = np.random.default_rng(args.seed)
        charge = charge[rng.permutation(len(charge))]
    elif args.stage1_charge_mode == "none":
        logger.info("Stage1 charge control: disabling charge memory.")
        charge = None
    else:
        logger.info("Stage1 charge control: using real aligned charge memory.")
    ppack = precursor_tensors(data, charge, args.max_elems, device)
    ds = RetrievalDataset(data["X_train"], data["y_train"], args.max_elems)
    if args.sample_limit:
        ds = torch.utils.data.Subset(ds, list(range(min(args.sample_limit, len(ds)))))
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=True, num_workers=args.loader_workers, pin_memory=False)
    use_physical_features = (args.enable_phys_features or args.enable_physical_features) and not args.disable_physical_features
    use_valence_features = (args.enable_phys_features or args.enable_valence_features) and not args.disable_valence_features
    if args.disable_phys_features:
        use_physical_features = False
        use_valence_features = False
    use_fraction = args.enable_fraction and not args.disable_fraction
    logger.info(
        "Stage1 feature toggles: element_embedding=%s physical=%s valence=%s fraction=%s charge_mode=%s charge_integration=%s charge_scale_init=%s",
        not args.disable_element_embedding,
        use_physical_features,
        use_valence_features,
        use_fraction,
        args.stage1_charge_mode,
        args.stage1_charge_integration,
        args.stage1_charge_scale_init,
    )
    logger.info(
        "Stage1 architecture toggles: shared_formula_encoder=%s hybrid_formula_encoder=%s hybrid_mode=%s formula_self_attention=%s",
        not args.separate_formula_encoders,
        args.hybrid_formula_encoder,
        args.hybrid_formula_encoder_mode,
        not args.disable_formula_self_attention,
    )
    model = Stage1Retriever(
        data["num_classes"],
        d_formula=args.d_formula,
        d_model=args.d_model,
        dropout=args.dropout,
        use_element_embedding=not args.disable_element_embedding,
        use_phys_features=use_physical_features or use_valence_features,
        use_physical_features=use_physical_features,
        use_valence_features=use_valence_features,
        use_fraction=use_fraction,
        share_formula_encoder=not args.separate_formula_encoders,
        hybrid_formula_encoder=args.hybrid_formula_encoder,
        hybrid_formula_encoder_mode=args.hybrid_formula_encoder_mode,
        hybrid_private_scale=args.hybrid_private_scale_start,
        use_formula_self_attention=not args.disable_formula_self_attention,
        charge_integration=args.stage1_charge_integration,
        charge_scale_init=args.stage1_charge_scale_init,
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    best = -1.0
    best_state = None
    for ep in range(args.epochs):
        if args.hybrid_formula_encoder:
            if args.hybrid_private_warmup_epochs > 0:
                denom = max(args.hybrid_private_warmup_epochs - 1, 1)
                progress = min(max(ep / denom, 0.0), 1.0)
                private_scale = args.hybrid_private_scale_start + (
                    args.hybrid_private_scale_end - args.hybrid_private_scale_start
                ) * progress
            else:
                private_scale = args.hybrid_private_scale_end
            model.set_hybrid_private_scale(private_scale)
        model.train()
        total = n = 0
        for elem, frac, mask, y in loader:
            elem = elem.to(device)
            frac = frac.to(device)
            mask = mask.to(device)
            y = y.to(device)
            logits = model(elem, frac, mask, *ppack)
            loss = F.binary_cross_entropy_with_logits(logits, y.float())
            opt.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            total += float(loss.detach().cpu()) * y.size(0)
            n += y.size(0)
        val_probs = predict_retriever(model, data["X_val"], ppack, device, args.max_elems)
        metrics = precursor_topk_metrics(
            data["y_val"],
            val_probs,
        )
        select_score = stage1_selection_score(data["y_val"], val_probs, args.stage1_select_metric)
        logger.info("[stage1] epoch=%d loss=%.4f metrics=%s", ep + 1, total / max(n, 1), metrics)
        if select_score > best:
            best = select_score
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}
    if best_state is not None:
        model.load_state_dict(best_state)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "args": jsonable_args(args),
            "best_val_score": best,
            "stage1_select_metric": args.stage1_select_metric,
        },
        args.output_dir / "stage1_retriever.pt",
    )
    probs = {
        "train": predict_retriever(model, data["X_train"], ppack, device, args.max_elems),
        "val": predict_retriever(model, data["X_val"], ppack, device, args.max_elems),
        "test": predict_retriever(model, data["X_test"], ppack, device, args.max_elems),
    }
    np.savez_compressed(args.output_dir / "stage1_probs.npz", train=probs["train"], val=probs["val"], test=probs["test"])
    env = ExpertEnv(precursor_features=data["precursor_X"], max_precursors=8)
    chem_prior = ChemistryPriorV2(env, data["precursor_id_mapping"], data["X_train"], data["y_train"])
    val_top = precursor_topk_metrics(
        data["y_val"],
        probs["val"],
    )
    test_top = precursor_topk_metrics(
        data["y_test"],
        probs["test"],
    )
    val_combo = stage1_combo_metrics(
        env, data["X_val"], data["y_val"], probs["val"], chem_prior, data["precursor_X"], charge, args, "val")
    test_combo = stage1_combo_metrics(
        env, data["X_test"], data["y_test"], probs["test"], chem_prior, data["precursor_X"], charge, args, "test")
    summary = {
        "best_val_score": best,
        "stage1_select_metric": args.stage1_select_metric,
        "best_val_oracle50": oracle_metrics(data["y_val"], probs["val"])["oracle@50"],
        "val_metrics": merge_stage1_metrics(val_top, val_combo),
        "test_metrics": merge_stage1_metrics(test_top, test_combo),
        "legacy_oracle_metrics": {
            "val": oracle_metrics(data["y_val"], probs["val"]),
            "test": oracle_metrics(data["y_test"], probs["test"]),
        },
        "args": jsonable_args(args),
    }
    (args.output_dir / "stage1_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("[stage1] summary=%s", summary)


def _init_train_worker(X, y, all_probs, pke, pm, chem_prior, precursor_x, charge_x,
                       top_m, list_size, n_augment, max_elems, seed, hard_fraction,
                       use_hard_metal_filter):
    global _TRAIN_STATE
    _TRAIN_STATE = locals()


def _build_train_sample(idx):
    s = _TRAIN_STATE
    X, y, all_probs = s["X"], s["y"], s["all_probs"]
    pke, pm, chem_prior = s["pke"], s["pm"], s["chem_prior"]
    precursor_x, charge_x = s["precursor_x"], s["charge_x"]
    top_m, list_size, n_augment = s["top_m"], s["list_size"], s["n_augment"]
    max_elems, hard_fraction = s["max_elems"], s["hard_fraction"]
    use_hard_metal_filter = s["use_hard_metal_filter"]
    rng = random.Random(int(s["seed"]) + idx * 9973)
    true_ids = set(np.where(y[idx] > 0)[0].tolist())
    if len(true_ids) < 2:
        return []
    target = X[idx]
    probs = all_probs[idx]
    order = np.argsort(-probs)
    raw_pool = order[:top_m].tolist()
    if use_hard_metal_filter:
        target_metals = set(np.where(target > 0)[0].tolist()) - VOLATILE_ELEMENTS
        pool = [p for p in raw_pool if pm[p].issubset(target_metals)]
        if len(pool) < 5:
            pool = raw_pool[:15]
    else:
        pool = raw_pool
    if len(pool) > 20:
        keep = [p for p in pool if p in true_ids]
        rest = [p for p in pool if p not in true_ids]
        pool = keep + rest[:20 - len(keep)]
    true_list = sorted(true_ids)
    same_pool = [p for p in pool if p not in true_ids and probs[p] > 0]
    if not same_pool:
        same_pool = [p for p in pool if p not in true_ids][:10]
    if not same_pool:
        return []
    target_elem, target_frac, target_mask = comp_to_sparse_arrays(target, max_elems)
    out = []
    logp = np.log(np.clip(probs, 1e-9, 1.0))
    hard_negs = []
    hard_target = int(round((list_size - 1) * hard_fraction))
    if hard_target:
        scored = []
        hard_pool = pool[:min(len(pool), 12)]
        for sz in range(2, min(5, len(hard_pool)) + 1):
            for combo in itertools.combinations(hard_pool, sz):
                combo = tuple(sorted(combo))
                if set(combo) == true_ids:
                    continue
                scored.append((float(np.mean([logp[p] for p in combo])), combo))
        hard_negs = [c for _, c in sorted(scored, key=lambda x: x[0], reverse=True)[:hard_target]]
    for aug in range(n_augment):
        seen = set(hard_negs)
        negs = list(hard_negs)
        for _ in range(list_size * 5):
            r = rng.random()
            if r < 0.45:
                sz = min(rng.randint(2, 5), len(pool))
                combo = tuple(sorted(rng.sample(pool, sz)))
            elif r < 0.8 and len(true_list) >= 2:
                combo = tuple(sorted((true_ids - {rng.choice(true_list)}) | {rng.choice(same_pool)}))
            else:
                top_k = order[:min(12, len(order))].tolist()
                sz = min(rng.randint(2, 5), len(top_k))
                combo = tuple(sorted(rng.sample(top_k, sz)))
            if set(combo) == true_ids or combo in seen:
                continue
            seen.add(combo)
            negs.append(combo)
            if len(negs) >= list_size - 1:
                break
        if len(negs) < 5:
            continue
        while len(negs) < list_size - 1:
            negs.append(negs[rng.randint(0, len(negs) - 1)])
        combos = [true_list] + [list(c) for c in negs[:list_size - 1]]
        arr = combos_to_arrays(combos, probs, target, pke, pm, chem_prior, precursor_x, charge_x, max_elems)
        out.append({
            "feats": arr["feats"],
            "target_elem": target_elem,
            "target_frac": target_frac,
            "target_mask": target_mask,
            "cand_elem": arr["cand_elem"],
            "cand_frac": arr["cand_frac"],
            "cand_mask": arr["cand_mask"],
            "sizes": arr["sizes"],
            "cand_charge": arr["cand_charge"],
        })
    return out


def _build_train_chunk(indices):
    return [(idx, _build_train_sample(idx)) for idx in indices]


def _iter_chunks(n_items, chunk_size):
    chunk_size = max(int(chunk_size), 1)
    for start in range(0, n_items, chunk_size):
        yield list(range(start, min(start + chunk_size, n_items)))


def _bounded_chunk_results(executor, chunks, fn, max_in_flight):
    """Submit chunks lazily and yield results in the original chunk order."""
    chunk_iter = iter(chunks)
    futures = {}
    buffered = {}
    max_in_flight = max(int(max_in_flight), 1)
    next_submit = 0
    next_yield = 0

    def submit_next():
        nonlocal next_submit
        try:
            chunk = next(chunk_iter)
        except StopIteration:
            return False
        futures[executor.submit(fn, chunk)] = next_submit
        next_submit += 1
        return True

    for _ in range(max_in_flight):
        if not submit_next():
            break

    while futures:
        done, _ = wait(futures, return_when=FIRST_COMPLETED)
        for future in done:
            chunk_id = futures.pop(future)
            buffered[chunk_id] = future.result()
            submit_next()
        while next_yield in buffered:
            yield buffered.pop(next_yield)
            next_yield += 1


def build_stage2_data(env, X, y, probs, chem_prior, precursor_x, charge_x, args):
    pke, pm = env.precursor_key_elements, env.precursor_metals
    worker_args = (
        X, y, probs, pke, pm, chem_prior, precursor_x, charge_x,
        args.top_m, args.list_size, args.n_augment, args.max_elems, args.seed, args.hard_negative_fraction,
        getattr(args, "use_hard_metal_filter", True),
    )
    logger.info("Build stage2 data workers=%d chunk=%d", args.num_workers, args.worker_chunk_size)
    parts = {k: [] for k in ["feats", "target_elem", "target_frac", "target_mask", "cand_elem", "cand_frac", "cand_mask", "sizes", "cand_charge"]}
    t0 = time.time()
    if args.num_workers <= 0:
        _init_train_worker(*worker_args)
        result_iter = map(_build_train_sample, range(len(X)))
        for i, samples in enumerate(result_iter, 1):
            for sample in samples:
                for k in parts:
                    parts[k].append(sample[k])
            if i % 2000 == 0:
                logger.info("  stage2 data %d/%d samples=%d elapsed=%.0fs", i, len(X), len(parts["feats"]), time.time() - t0)
    else:
        executor = ProcessPoolExecutor(max_workers=args.num_workers, initializer=_init_train_worker, initargs=worker_args)
        chunks = _iter_chunks(len(X), args.worker_chunk_size)
        max_in_flight = max(1, args.num_workers * 4)
        try:
            logger.info("  bounded stage2 data inflight_chunks=%d", max_in_flight)
            done_items = 0
            for chunk_result in _bounded_chunk_results(executor, chunks, _build_train_chunk, max_in_flight):
                for _, samples in chunk_result:
                    done_items += 1
                    for sample in samples:
                        for k in parts:
                            parts[k].append(sample[k])
                if done_items % 2000 == 0 or done_items == len(X):
                    logger.info("  stage2 data %d/%d samples=%d elapsed=%.0fs",
                                done_items, len(X), len(parts["feats"]), time.time() - t0)
        finally:
            executor.shutdown(wait=True, cancel_futures=False)
    data = {
        "feats": np.stack(parts["feats"]).astype(np.float32),
        "target_elem": np.stack(parts["target_elem"]).astype(np.int64),
        "target_frac": np.stack(parts["target_frac"]).astype(np.float32),
        "target_mask": np.stack(parts["target_mask"]).astype(bool),
        "cand_elem": np.stack(parts["cand_elem"]).astype(np.int64),
        "cand_frac": np.stack(parts["cand_frac"]).astype(np.float32),
        "cand_mask": np.stack(parts["cand_mask"]).astype(bool),
        "sizes": np.stack(parts["sizes"]).astype(np.float32),
        "cand_charge": np.stack(parts["cand_charge"]).astype(np.float32),
    }
    logger.info("Stage2 data: %s feature_mem=%.1fGB", data["feats"].shape, data["feats"].nbytes / 1e9)
    return data


def _init_cache_worker(X, y, probs, pke, pm, chem_prior, precursor_x, charge_x,
                       top_m, max_elems, eval_pool_cap, eval_keep_gt_for_cap,
                       use_pred_threshold_metrics, pred_threshold, use_hard_metal_filter,
                       eval_min_set_size, eval_max_set_size):
    global _CACHE_STATE
    _CACHE_STATE = locals()


def _build_cache_sample(idx):
    s = _CACHE_STATE
    X, y, probs = s["X"], s["y"], s["probs"]
    pke, pm, chem_prior = s["pke"], s["pm"], s["chem_prior"]
    precursor_x, charge_x = s["precursor_x"], s["charge_x"]
    top_m, max_elems = s["top_m"], s["max_elems"]
    eval_pool_cap = s["eval_pool_cap"]
    eval_keep_gt_for_cap = s["eval_keep_gt_for_cap"]
    use_pred_threshold_metrics = s["use_pred_threshold_metrics"]
    pred_threshold = s["pred_threshold"]
    use_hard_metal_filter = s["use_hard_metal_filter"]
    eval_min_set_size = s["eval_min_set_size"]
    eval_max_set_size = s["eval_max_set_size"]
    true_ids = set(np.where(y[idx] > 0)[0].tolist())
    if len(true_ids) == 0:
        return {"valid": 0, "sample": None, "oracle": 0, "n": 0}
    target = X[idx]
    row_probs = probs[idx]
    raw_pool = np.argsort(-row_probs)[:top_m].tolist()
    if use_hard_metal_filter:
        target_metals = set(np.where(target > 0)[0].tolist()) - VOLATILE_ELEMENTS
        pool = [p for p in raw_pool if pm[p].issubset(target_metals)]
        if len(pool) < 2:
            pool = raw_pool[:10]
    else:
        pool = raw_pool
    if eval_pool_cap > 0 and len(pool) > eval_pool_cap:
        if eval_keep_gt_for_cap:
            # Legacy diagnostics only: this is label-aware and must not be used
            # for unbiased test reporting.
            keep = [p for p in pool if p in true_ids]
            rest = [p for p in pool if p not in true_ids]
            pool = (keep + rest)[:eval_pool_cap]
        else:
            pool = pool[:eval_pool_cap]
    combos = []
    if use_pred_threshold_metrics:
        pred_labels = np.where(row_probs > pred_threshold)[0]
        if len(pred_labels) != len(true_ids):
            return {"valid": 1, "sample": None, "oracle": 0, "n": 0}
        combination_size = len(pred_labels)
        if combination_size <= 0 or combination_size > len(pool):
            return {"valid": 1, "sample": None, "oracle": int(true_ids.issubset(set(pool))), "n": 0}
        combos.extend(list(c) for c in itertools.combinations(pool, combination_size))
    else:
        for sz in range(eval_min_set_size, min(eval_max_set_size, len(pool)) + 1):
            combos.extend(list(c) for c in itertools.combinations(pool, sz))
    correct_idx = None
    for ci, combo in enumerate(combos):
        if set(combo) == true_ids:
            correct_idx = ci
            break
    if not combos:
        return {"valid": 1, "sample": None, "oracle": int(true_ids.issubset(set(pool))), "n": 0}
    arr = combos_to_arrays(combos, row_probs, target, pke, pm, chem_prior, precursor_x, charge_x, max_elems)
    combo_log_scores = np.asarray([
        float(np.sum(np.log(np.asarray([row_probs[p] for p in combo], dtype=np.float64).clip(min=1e-300))))
        for combo in combos
    ], dtype=np.float64)
    product_scores = np.exp(combo_log_scores).astype(np.float32)
    te, tf, tm = comp_to_sparse_arrays(target, max_elems)
    return {
        "valid": 1,
        "oracle": int(true_ids.issubset(set(pool))),
        "n": len(combos),
        "sample": {
            "target_idx": idx,
            "correct_idx": correct_idx,
            "gt_ids": sorted(true_ids),
            "pool_ids": [int(p) for p in pool],
            "pool_probs": [float(row_probs[p]) for p in pool],
            "combos": [list(c) for c in combos],
            "product_scores": product_scores,
            "sum_log_scores": combo_log_scores,
            "target_elem": te,
            "target_frac": tf,
            "target_mask": tm,
            **arr,
        },
    }


def _build_cache_chunk(indices):
    return [(idx, _build_cache_sample(idx)) for idx in indices]


def make_rank_cache(env, X, y, probs, chem_prior, precursor_x, charge_x, args, split):
    pke, pm = env.precursor_key_elements, env.precursor_metals
    worker_args = (
        X, y, probs, pke, pm, chem_prior, precursor_x, charge_x,
        args.top_m, args.max_elems, args.eval_pool_cap, args.eval_keep_gt_for_cap,
        getattr(args, "use_pred_threshold_metrics", False),
        getattr(args, "pred_threshold", 0.5),
        getattr(args, "use_hard_metal_filter", True),
        getattr(args, "eval_min_set_size", 2),
        getattr(args, "eval_max_set_size", 5),
    )
    cache, valid, oracle, total = [], 0, 0, 0
    t0 = time.time()
    if args.num_workers <= 0:
        _init_cache_worker(*worker_args)
        for i, idx in enumerate(range(len(X)), 1):
            r = _build_cache_sample(idx)
            valid += r["valid"]
            oracle += r["oracle"]
            total += r["n"]
            if r["sample"] is not None:
                cache.append(r["sample"])
            if i % 300 == 0:
                logger.info("  %s cache %d/%d oracle=%.1f%% avg=%d elapsed=%.0fs", split, i, len(X), oracle / max(valid, 1) * 100, total // max(len(cache), 1), time.time() - t0)
    else:
        executor = ProcessPoolExecutor(max_workers=args.num_workers, initializer=_init_cache_worker, initargs=worker_args)
        try:
            chunk_size = max(1, args.worker_chunk_size)
            chunks = _iter_chunks(len(X), chunk_size)
            max_in_flight = max(1, args.num_workers * 4)
            logger.info("  bounded %s cache inflight_chunks=%d", split, max_in_flight)
            for i, chunk_result in enumerate(_bounded_chunk_results(executor, chunks, _build_cache_chunk, max_in_flight), 1):
                for _, r in chunk_result:
                    valid += r["valid"]
                    oracle += r["oracle"]
                    total += r["n"]
                    if r["sample"] is not None:
                        cache.append(r["sample"])
                done_items = min(i * chunk_size, len(X))
                if done_items % 300 == 0 or done_items == len(X):
                    logger.info("  %s cache %d/%d oracle=%.1f%% avg=%d elapsed=%.0fs", split, done_items, len(X), oracle / max(valid, 1) * 100, total // max(len(cache), 1), time.time() - t0)
        finally:
            executor.shutdown(wait=True, cancel_futures=False)
    logger.info("%s cache: samples=%d valid=%d Oracle@%d=%.2f%% (%d/%d) total=%d avg=%d elapsed=%.0fs",
                split, len(cache), valid, args.top_m, oracle / max(valid, 1) * 100, oracle, valid,
                total, total // max(len(cache), 1), time.time() - t0)
    return cache, valid


@torch.no_grad()
def score_sample(model, sample, device, chunk=512):
    scores = []
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
        scores.append(model(feats, target_elem, target_frac, target_mask, ce, cf, cm, sizes, cc).squeeze(0).cpu().numpy())
    return np.concatenate(scores)


@torch.no_grad()
def evaluate_stage2(model, cache, full_n, device, chunk=512, label="test"):
    model.eval()
    ks = [1, 3, 5, 10, 20]
    hits = {k: 0 for k in ks}
    valid = 0
    for i, sample in enumerate(cache, 1):
        ci = sample["correct_idx"]
        if ci is None:
            continue
        valid += 1
        scores = score_sample(model, sample, device, chunk)
        rank = int(np.sum(scores > scores[ci]))
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
    logger.info("%s metrics: %s", label, metrics)
    return metrics


@torch.no_grad()
def evaluate_stage2_stream(model, env, X, y, probs, chem_prior, precursor_x, charge_x, args, device, label="test"):
    """Evaluate one target at a time to avoid materializing the full rank cache."""
    model.eval()
    pke, pm = env.precursor_key_elements, env.precursor_metals
    worker_args = (
        X, y, probs, pke, pm, chem_prior, precursor_x, charge_x,
        args.top_m, args.max_elems, args.eval_pool_cap, args.eval_keep_gt_for_cap,
        getattr(args, "use_pred_threshold_metrics", False),
        getattr(args, "pred_threshold", 0.5),
        getattr(args, "use_hard_metal_filter", True),
        getattr(args, "eval_min_set_size", 2),
        getattr(args, "eval_max_set_size", 5),
    )
    _init_cache_worker(*worker_args)

    ks = [1, 3, 5, 10, 20]
    hits = {k: 0 for k in ks}
    valid = oracle = total = scored = 0
    t0 = time.time()
    for i in range(len(X)):
        r = _build_cache_sample(i)
        valid += r["valid"]
        oracle += r["oracle"]
        total += r["n"]
        sample = r["sample"]
        if sample is None or sample["correct_idx"] is None:
            if (i + 1) % 300 == 0:
                logger.info(
                    "  %s stream %d/%d oracle=%.1f%% scored=%d avg=%d elapsed=%.0fs",
                    label, i + 1, len(X), oracle / max(valid, 1) * 100,
                    scored, total // max(scored, 1), time.time() - t0,
                )
            continue
        scored += 1
        scores = score_sample(model, sample, device, args.eval_chunk_size)
        ci = sample["correct_idx"]
        rank = int(np.sum(scores > scores[ci]))
        for k in ks:
            if rank < k:
                hits[k] += 1
        if (i + 1) % 300 == 0:
            logger.info(
                "  %s stream %d/%d oracle=%.1f%% scored=%d avg=%d elapsed=%.0fs",
                label, i + 1, len(X), oracle / max(valid, 1) * 100,
                scored, total // max(scored, 1), time.time() - t0,
            )

    metrics = {}
    for k in ks:
        metrics[f"combo_{k}_valid"] = hits[k] / max(scored, 1) * 100
        metrics[f"combo_{k}_full"] = hits[k] / max(len(y), 1) * 100
    metrics["valid"] = scored
    metrics["full_denominator"] = len(y)
    metrics["oracle_at_top_m"] = oracle / max(valid, 1) * 100
    metrics["avg_candidates"] = total // max(scored, 1)
    logger.info("%s stream metrics: %s", label, metrics)
    return metrics


def train_stage2(args):
    device = args.device if args.device.startswith("cuda") and torch.cuda.is_available() else "cpu"
    data = prepare_data(make_data_args(args.cache_dir, args.dataset, args.data_path), device)
    probs = np.load(args.probs_path)
    charge = load_precursor_charge_matrix(args.precursor_charge_csv, data["precursor_id_mapping"], data["num_classes"])
    env = ExpertEnv(precursor_features=data["precursor_X"], max_precursors=8)
    chem_prior = ChemistryPriorV2(env, data["precursor_id_mapping"], data["X_train"], data["y_train"])
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
    train_data = build_stage2_data(env, train_x, train_y, train_probs, chem_prior, data["precursor_X"], charge, args)
    train_ds = FormulaListDataset(train_data)
    loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0, pin_memory=False, drop_last=True)
    model = Stage2FormulaSetReranker(dropout=args.dropout, charge_scale=args.charge_scale).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    best_c1 = -1.0
    best_state = None
    for ep in range(args.epochs):
        model.train()
        total = correct = n = 0
        for batch in loader:
            feats, te, tf, tm, ce, cf, cm, sizes, cc, labels = [torch.as_tensor(x, device=device) for x in batch]
            scores = model(feats, te, tf, tm, ce, cf, cm, sizes, cc)
            log_probs = F.log_softmax(scores / 2.0, dim=-1)
            target = torch.full_like(log_probs, 0.03 / (scores.size(1) - 1))
            target.scatter_(1, labels.long().unsqueeze(1), 0.97)
            loss = -(target * log_probs).sum(dim=-1).mean()
            pos = scores.gather(1, labels.long().unsqueeze(1)).squeeze(1)
            neg = scores.masked_fill(torch.eye(scores.size(1), device=device, dtype=torch.bool)[labels.long()], -1e9).max(dim=-1).values
            loss = loss + args.margin_weight * F.relu(0.3 + neg - pos).mean()
            opt.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            total += float(loss.detach().cpu()) * feats.size(0)
            correct += (scores.argmax(dim=-1) == labels.long()).sum().item()
            n += feats.size(0)
        val_metrics = evaluate_stage2_stream(
            model, env, val_x, val_y, val_probs, chem_prior, data["precursor_X"], charge, args, device, "val")
        logger.info("[stage2] epoch=%d loss=%.4f train_acc=%.1f val_c1=%.2f", ep + 1, total / max(n, 1), correct / max(n, 1) * 100, val_metrics["combo_1_valid"])
        if val_metrics["combo_1_valid"] > best_c1:
            best_c1 = val_metrics["combo_1_valid"]
            best_state = {k: v.detach().cpu() for k, v in model.state_dict().items()}
    if best_state is not None:
        model.load_state_dict(best_state)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state_dict": model.state_dict(), "args": vars(args), "best_val_c1": best_c1}, args.output_dir / "stage2_reranker.pt")
    metrics = evaluate_stage2_stream(
        model, env, test_x, test_y, test_probs, chem_prior, data["precursor_X"], charge, args, device, "test")
    summary = {"best_val_c1": best_c1, "test_metrics": metrics, "args": jsonable_args(args)}
    (args.output_dir / "stage2_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("[stage2] summary=%s", summary)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["stage1", "stage2"], required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--dataset", choices=["retro", "ceder"], default="retro")
    parser.add_argument("--data_path", default=None)
    parser.add_argument("--cache_dir", default=str(PACKAGE_ROOT / "artifacts" / "cache"))
    parser.add_argument("--output_dir", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=20260502)
    parser.add_argument("--max_elems", type=int, default=12)
    parser.add_argument("--d_formula", type=int, default=96)
    parser.add_argument("--d_model", type=int, default=192)
    parser.add_argument("--dropout", type=float, default=0.12)
    parser.add_argument("--batch_size", type=int, default=128)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--loader_workers", type=int, default=0)
    parser.add_argument("--sample_limit", type=int, default=0)
    parser.add_argument("--precursor_charge_csv", default=None)
    parser.add_argument("--stage1_charge_mode", choices=["real", "zero", "shuffle", "none"], default="none")
    parser.add_argument(
        "--stage1_charge_integration",
        choices=["add", "gated"],
        default="add",
        help="How Stage-1 injects precursor charge memory into precursor formula embeddings.",
    )
    parser.add_argument(
        "--stage1_charge_scale_init",
        type=float,
        default=0.1,
        help="Initial scalar for Stage-1 charge residual. Use 0.0 for safe gated charge warm-start.",
    )
    parser.add_argument("--disable_element_embedding", action="store_true")
    parser.add_argument("--disable_phys_features", action="store_true")
    parser.add_argument("--disable_physical_features", action="store_true")
    parser.add_argument("--disable_valence_features", action="store_true")
    parser.add_argument("--disable_fraction", action="store_true")
    parser.add_argument("--enable_phys_features", action="store_true")
    parser.add_argument("--enable_physical_features", action="store_true")
    parser.add_argument("--enable_valence_features", action="store_true")
    parser.add_argument("--enable_fraction", action="store_true", default=True)
    parser.add_argument("--separate_formula_encoders", action="store_true")
    parser.add_argument(
        "--hybrid_formula_encoder",
        action="store_true",
        help="Use one shared FormulaTransformer plus target/precursor private FormulaTransformer branches in a single model.",
    )
    parser.add_argument(
        "--hybrid_formula_encoder_mode",
        choices=["concat", "residual", "logit_fusion"],
        default="concat",
        help="How to merge shared and private formula branches when --hybrid_formula_encoder is enabled.",
    )
    parser.add_argument("--hybrid_private_scale_start", type=float, default=1.0)
    parser.add_argument("--hybrid_private_scale_end", type=float, default=1.0)
    parser.add_argument(
        "--hybrid_private_warmup_epochs",
        type=int,
        default=0,
        help="Linearly schedule private branch scale from start to end over this many epochs.",
    )
    parser.add_argument("--disable_formula_self_attention", action="store_true")
    parser.add_argument(
        "--stage1_select_metric",
        choices=["top_20", "oracle_20", "oracle_50"],
        default="top_20",
        help="Validation metric used to select the Stage-1 checkpoint.",
    )
    parser.add_argument("--probs_path", type=Path, default=None)
    parser.add_argument("--top_m", type=int, default=30)
    parser.add_argument("--list_size", type=int, default=96)
    parser.add_argument("--n_augment", type=int, default=2)
    parser.add_argument("--num_workers", type=int, default=24)
    parser.add_argument("--worker_chunk_size", type=int, default=4)
    parser.add_argument("--hard_negative_fraction", type=float, default=0.25)
    parser.add_argument("--charge_scale", type=float, default=0.0)
    parser.add_argument("--margin_weight", type=float, default=0.08)
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
    parser.add_argument("--pred_threshold", type=float, default=0.5)
    parser.add_argument(
        "--disable_pred_threshold_metrics",
        action="store_true",
        help="Use legacy length-agnostic Combo@k instead of p>threshold predicted set size.",
    )
    parser.add_argument(
        "--eval_keep_gt_for_cap",
        action="store_true",
        help="Legacy label-aware eval cap. Do not use for unbiased test metrics.",
    )
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.eval_min_set_size < 1 or args.eval_max_set_size < args.eval_min_set_size:
        parser.error("--eval_min_set_size must be >=1 and <= --eval_max_set_size")
    args.use_pred_threshold_metrics = not args.disable_pred_threshold_metrics
    if args.output_dir is None:
        args.output_dir = PACKAGE_ROOT / "artifacts" / "runs" / args.dataset / args.mode
    if args.precursor_charge_csv is None:
        args.precursor_charge_csv = str(default_charge_path(args.dataset))
    if args.probs_path is None:
        args.probs_path = PACKAGE_ROOT / "artifacts" / "runs" / args.dataset / "stage1" / "stage1_probs.npz"
    if args.smoke:
        args.output_dir = args.output_dir / "smoke"
        args.epochs = min(args.epochs, 1)
        args.sample_limit = args.sample_limit or 512
        args.list_size = min(args.list_size, 32)
        args.n_augment = 1
    args.output_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    fh = logging.FileHandler(args.output_dir / f"{args.mode}.log")
    fh.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logging.getLogger().addHandler(fh)
    seed_everything(args.seed)
    logger.info("Args: %s", vars(args))
    logger.info("Custom transformer block: no CrabNetEncoder import/use.")
    if args.mode == "stage1":
        train_stage1(args)
    else:
        train_stage2(args)


if __name__ == "__main__":
    main()
