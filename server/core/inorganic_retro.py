"""Inference adapter for the vendored two-stage inorganic retro model.

Input is one inorganic target formula.  Stage 1 ranks individual precursor
labels; Stage 2 enumerates precursor sets of size 2--5 and reranks them.  The
default output is the top five precursor-set routes.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .audit import record_tool_call


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_ROOT = REPO_ROOT / "vendor" / "two_stage_retro"
EXPECTED_SHA256 = {
    "stage1": "f302cb315a607eaf461281ef65585489eb814b1db7c5e41e56aaa9193965a53e",
    "stage2": "373ee6bdaf562f4ee70b06e515d5b84a18db8c6dbd2d4e2fd7dea864272465de",
}
_PREDICTORS: dict[tuple[str, str], "TwoStagePredictor"] = {}


def model_root() -> Path:
    return Path(os.environ.get("GOAI_INORGANIC_RETRO_ROOT", DEFAULT_MODEL_ROOT)).expanduser().resolve()


def _paths(root: Path | None = None) -> dict[str, Path]:
    root = root or model_root()
    checkpoints = root / "checkpoints"
    data = root / "data"
    return {
        "root": root,
        "stage1_checkpoint": Path(os.environ.get(
            "GOAI_RETRO_STAGE1_CHECKPOINT", checkpoints / "stage1_retriever.pt"
        )),
        "stage1_summary": Path(os.environ.get(
            "GOAI_RETRO_STAGE1_SUMMARY", checkpoints / "stage1_summary.json"
        )),
        "stage2_checkpoint": Path(os.environ.get(
            "GOAI_RETRO_STAGE2_CHECKPOINT", checkpoints / "stage2_reranker.pt"
        )),
        "stage2_summary": Path(os.environ.get(
            "GOAI_RETRO_STAGE2_SUMMARY", checkpoints / "stage2_summary.json"
        )),
        "data_path": Path(os.environ.get("GOAI_RETRO_DATA_PATH", data / "retro_split.csv")),
        "precursor_id_mapping": data / "retro_precursor_id.json",
        "charge_path": Path(os.environ.get(
            "GOAI_RETRO_CHARGE_PATH", data / "retro_deepseek_charge.csv"
        )),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def status() -> dict[str, Any]:
    paths = _paths()
    dependency_names = ("torch", "numpy", "pandas", "pymatgen")
    dependencies = {name: importlib.util.find_spec(name) is not None for name in dependency_names}
    assets = {
        name: path.is_file()
        for name, path in paths.items()
        if name not in {"root"}
    }
    hashes: dict[str, str | None] = {"stage1": None, "stage2": None}
    if assets.get("stage1_checkpoint"):
        hashes["stage1"] = _sha256(paths["stage1_checkpoint"])
    if assets.get("stage2_checkpoint"):
        hashes["stage2"] = _sha256(paths["stage2_checkpoint"])
    hash_ok = {
        name: hashes[name] == EXPECTED_SHA256[name]
        for name in EXPECTED_SHA256
    }
    return {
        "provider": "local_two_stage_inorganic",
        "available": all(dependencies.values()) and all(assets.values()) and all(hash_ok.values()),
        "dependencies": dependencies,
        "assets": assets,
        "checkpoint_sha256": hashes,
        "checkpoint_hash_ok": hash_ok,
        "protocol": {
            "input": "inorganic target formula",
            "stage1": "formula-token precursor Top-K retriever",
            "stage2": "precursor combination enumeration + learned set reranker",
            "default_top_m": 30,
            "default_pool_cap": 15,
            "set_sizes": [2, 3, 4, 5],
            "default_routes": 5,
        },
    }


def _torch_load(torch, path: Path):
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:  # torch < 2.0
        return torch.load(path, map_location="cpu")


class TwoStagePredictor:
    def __init__(self, root: Path, requested_device: str):
        import numpy as np
        import torch
        from pymatgen.core import Element
        from pymatgen.core.composition import Composition

        from vendor.two_stage_retro.chemistry import ChemistryPriorV2
        from vendor.two_stage_retro.data import make_data_args, prepare_data
        from vendor.two_stage_retro.env import ExpertEnv, VOLATILE_ELEMENTS
        from vendor.two_stage_retro.stage1 import (
            Stage1Retriever,
            combos_to_arrays,
            comp_to_sparse_arrays,
            load_precursor_charge_matrix,
            precursor_tensors,
            predict_retriever,
        )
        from vendor.two_stage_retro.stage2 import (
            apply_anion_prior_mode,
            build_stage2_model,
            score_sample,
        )

        self.np = np
        self.torch = torch
        self.Element = Element
        self.Composition = Composition
        self.VOLATILE_ELEMENTS = VOLATILE_ELEMENTS
        self.combos_to_arrays = combos_to_arrays
        self.comp_to_sparse_arrays = comp_to_sparse_arrays
        self.predict_retriever = predict_retriever
        self.score_sample = score_sample
        self.paths = _paths(root)
        self.device = requested_device if requested_device.startswith("cuda") and torch.cuda.is_available() else "cpu"
        workspace = Path(os.environ.get("GOAI_WORKSPACE", "workspace"))
        cache_dir = Path(os.environ.get(
            "GOAI_RETRO_CACHE_DIR", workspace / "cache" / "two_stage_retro"
        ))

        self.data = prepare_data(make_data_args(
            cache_dir=cache_dir,
            data_path=self.paths["data_path"],
            dataset="retro",
        ), device="cpu")
        self.precursor_mapping = self.data["precursor_id_mapping"]
        self.precursor_names = {
            int(pid): str(value[0] if isinstance(value, list) else value)
            for pid, value in self.precursor_mapping.items()
        }

        stage1_args = json.loads(self.paths["stage1_summary"].read_text(encoding="utf-8"))["args"]
        use_physical = bool(
            (stage1_args.get("enable_phys_features") or stage1_args.get("enable_physical_features"))
            and not stage1_args.get("disable_physical_features")
        )
        use_valence = bool(
            (stage1_args.get("enable_phys_features") or stage1_args.get("enable_valence_features"))
            and not stage1_args.get("disable_valence_features")
        )
        if stage1_args.get("disable_phys_features"):
            use_physical = use_valence = False
        self.max_elems = int(stage1_args.get("max_elems", 12))
        self.stage1 = Stage1Retriever(
            num_precursors=self.data["num_classes"],
            d_formula=stage1_args.get("d_formula", 96),
            d_model=stage1_args.get("d_model", 192),
            dropout=stage1_args.get("dropout", 0.12),
            use_element_embedding=not stage1_args.get("disable_element_embedding", False),
            use_phys_features=use_physical or use_valence,
            use_physical_features=use_physical,
            use_valence_features=use_valence,
            use_fraction=stage1_args.get("enable_fraction", True)
            and not stage1_args.get("disable_fraction", False),
            share_formula_encoder=not stage1_args.get("separate_formula_encoders", True),
            hybrid_formula_encoder=stage1_args.get("hybrid_formula_encoder", False),
            hybrid_formula_encoder_mode=stage1_args.get("hybrid_formula_encoder_mode", "concat"),
            hybrid_private_scale=stage1_args.get("hybrid_private_scale_end", 1.0),
            use_formula_self_attention=not stage1_args.get("disable_formula_self_attention", False),
            charge_integration=stage1_args.get("stage1_charge_integration", "add"),
            charge_scale_init=stage1_args.get("stage1_charge_scale_init", 0.1),
        )
        checkpoint = _torch_load(torch, self.paths["stage1_checkpoint"])
        state = checkpoint.get("model_state_dict", checkpoint)
        self.stage1.load_state_dict(state, strict=True)
        self.stage1 = self.stage1.to(self.device).eval()
        self.precursor_pack = precursor_tensors(
            self.data, None, self.max_elems, self.device
        )

        stage2_payload = json.loads(self.paths["stage2_summary"].read_text(encoding="utf-8"))
        self.stage2_args = stage2_payload["args"]
        self.stage2 = build_stage2_model(SimpleNamespace(**self.stage2_args))
        checkpoint = _torch_load(torch, self.paths["stage2_checkpoint"])
        state = checkpoint.get("model_state_dict", checkpoint)
        self.stage2.load_state_dict(state, strict=True)
        self.stage2 = self.stage2.to(self.device).eval()

        self.env = ExpertEnv(precursor_features=self.data["precursor_X"], max_precursors=8)
        self.chem_prior = ChemistryPriorV2(
            self.env,
            self.precursor_mapping,
            self.data["X_train"],
            self.data["y_train"],
        )
        apply_anion_prior_mode(
            self.chem_prior,
            self.data["y_train"],
            self.stage2_args.get("anion_prior_mode", "train_type_rate"),
        )
        self.charge = load_precursor_charge_matrix(
            self.paths["charge_path"],
            self.precursor_mapping,
            self.data["num_classes"],
        )

    def composition_features(self, formula: str):
        comp = self.Composition(formula)
        if not comp or sum(comp.values()) <= 0:
            raise ValueError(f"empty composition: {formula!r}")
        total = float(sum(comp.values()))
        vector = self.np.asarray(
            [comp.get(element, 0) / total for element in list(self.Element)],
            dtype=self.np.float32,
        )
        return comp, vector

    def predict(self, target_formula: str, *, top_k: int, top_m: int,
                pool_cap: int, min_set_size: int, max_set_size: int) -> dict[str, Any]:
        from itertools import combinations

        comp, target_vec = self.composition_features(target_formula)
        x = self.np.asarray([target_vec], dtype=self.np.float32)
        stage1_probs = self.predict_retriever(
            self.stage1, x, self.precursor_pack, self.device,
            self.max_elems, batch_size=1,
        )[0]
        raw_pool = self.np.argsort(-stage1_probs)[:top_m].tolist()
        target_metals = set(self.np.where(target_vec > 0)[0].tolist()) - self.VOLATILE_ELEMENTS
        pool = [
            int(pid) for pid in raw_pool
            if self.env.precursor_metals[int(pid)].issubset(target_metals)
        ]
        used_filter_fallback = False
        if len(pool) < min_set_size:
            pool = [int(pid) for pid in raw_pool[:max(pool_cap, min_set_size)]]
            used_filter_fallback = True
        if pool_cap > 0:
            pool = pool[:pool_cap]

        combos: list[list[int]] = []
        for size in range(min_set_size, min(max_set_size, len(pool)) + 1):
            combos.extend([list(combo) for combo in combinations(pool, size)])
        if not combos:
            raise RuntimeError("candidate generation produced no precursor combinations")

        arrays = self.combos_to_arrays(
            combos,
            stage1_probs,
            target_vec,
            self.env.precursor_key_elements,
            self.env.precursor_metals,
            self.chem_prior,
            self.data["precursor_X"],
            self.charge,
            self.max_elems,
        )
        target_elem, target_frac, target_mask = self.comp_to_sparse_arrays(
            target_vec, self.max_elems
        )
        sample = {
            "correct_idx": None,
            "gt_ids": [],
            "combos": combos,
            "target_elem": target_elem,
            "target_frac": target_frac,
            "target_mask": target_mask,
            **arrays,
        }
        scores = self.score_sample(self.stage2, sample, self.device, chunk=512)
        shifted = scores - self.np.max(scores)
        exp_values = self.np.exp(shifted)
        probabilities = exp_values / self.np.sum(exp_values)
        order = self.np.argsort(-scores)[:top_k]

        routes = []
        normalized_target = comp.reduced_formula
        for rank, combo_idx in enumerate(order, 1):
            precursor_ids = [int(pid) for pid in combos[int(combo_idx)]]
            route_key = normalized_target + "|" + "+".join(map(str, precursor_ids))
            routes.append({
                "rank": rank,
                "route_id": "two-stage-" + hashlib.sha256(route_key.encode()).hexdigest()[:12],
                "provider": "local_two_stage_inorganic",
                "model_output_verified": True,
                "chemical_route_verified": False,
                "target_formula": normalized_target,
                "precursors": [
                    {
                        "id": pid,
                        "formula": self.precursor_names.get(pid, str(pid)),
                        "stage1_probability": float(stage1_probs[pid]),
                    }
                    for pid in precursor_ids
                ],
                "stage1_probability_product": float(self.np.prod(stage1_probs[precursor_ids])),
                "stage2_score": float(scores[int(combo_idx)]),
                "route_probability_within_candidate_pool": float(probabilities[int(combo_idx)]),
            })

        return {
            "ok": True,
            "provider": "local_two_stage_inorganic",
            "target_formula_input": target_formula,
            "target_formula_normalized": normalized_target,
            "top_k": top_k,
            "routes": routes,
            "candidate_generation": {
                "top_m": top_m,
                "pool_cap": pool_cap,
                "raw_pool_size": len(raw_pool),
                "filtered_pool_size": len(pool),
                "enumerated_route_count": len(combos),
                "set_sizes": list(range(min_set_size, max_set_size + 1)),
                "hard_metal_filter": True,
                "filter_fallback_used": used_filter_fallback,
            },
            "model": {
                "stage1": "formula-token precursor retriever, seed 20260504",
                "stage2": "no-mixture-pool set reranker, seed 20260504",
                "checkpoint_sha256": EXPECTED_SHA256,
                "reference_test_metrics": {
                    "stage1_top20": 95.78,
                    "stage2_combo1_full": 71.81,
                    "stage2_combo20_full": 89.21,
                    "stage2_mrr_full": 0.7748,
                },
            },
            "model_output_verified": True,
            "chemical_route_verified": False,
            "warning": (
                "These are model-ranked precursor sets, not experimentally validated routes. "
                "Conditions and scientific claims require literature evidence and reviewer approval."
            ),
        }


def predict_precursor_routes(
    target_formula: str,
    *,
    top_k: int = 5,
    top_m: int = 30,
    pool_cap: int = 15,
    min_set_size: int = 2,
    max_set_size: int = 5,
    device: str | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    request = {
        "target_formula": target_formula,
        "top_k": top_k,
        "top_m": top_m,
        "pool_cap": pool_cap,
        "min_set_size": min_set_size,
        "max_set_size": max_set_size,
        "device": device,
    }
    try:
        top_k = min(max(int(top_k), 1), 20)
        top_m = min(max(int(top_m), 5), 50)
        pool_cap = min(max(int(pool_cap), 2), 20)
        min_set_size = min(max(int(min_set_size), 1), 5)
        max_set_size = min(max(int(max_set_size), min_set_size), 5)
        requested_device = device or os.environ.get("GOAI_RETRO_DEVICE", "cpu")
        root = model_root()
        key = (str(root), requested_device)
        if key not in _PREDICTORS:
            readiness = status()
            if not readiness["available"]:
                raise RuntimeError(f"local retro model is unavailable: {readiness}")
            _PREDICTORS[key] = TwoStagePredictor(root, requested_device)
        result = _PREDICTORS[key].predict(
            target_formula,
            top_k=top_k,
            top_m=top_m,
            pool_cap=pool_cap,
            min_set_size=min_set_size,
            max_set_size=max_set_size,
        )
        result["runtime"] = {
            "device": _PREDICTORS[key].device,
            "duration_ms": round((time.monotonic() - started) * 1000, 3),
        }
    except Exception as exc:  # MCP boundary: return structured failures
        result = {
            "ok": False,
            "provider": "local_two_stage_inorganic",
            "target_formula_input": target_formula,
            "error": f"{type(exc).__name__}: {exc}",
        }
    record_tool_call(
        "predict_precursor_routes",
        request,
        result,
        duration_ms=(time.monotonic() - started) * 1000,
    )
    return result


__all__ = ["status", "predict_precursor_routes", "TwoStagePredictor"]
