#!/usr/bin/env python3
"""Recompute RECIPE two-stage retrosynthesis metrics on the Retro year-split test set.

This is the "指标与分析代码 / 基线复现" entry for the vendored inorganic precursor
predictor. It reuses exactly the inference path the MCP tool
``predict_precursor_routes`` uses (same checkpoints, same hard metal filter,
same candidate enumeration: top_m=30, pool_cap=15, set sizes 2-5) and reports:

* Stage 1 (Precursor Candidate Generator): Top-k precursor coverage, k in
  {1,3,5,10,20}; a target counts as covered when every ground-truth precursor
  appears in the top max(k, |S*|) individually ranked precursors.
* Stage 2 (Complete-Set Reranker): Combo@k exact-set recovery over the ranked
  candidate *sets* and Combo MRR (reciprocal rank of the exact ground-truth set,
  0 when it is not enumerated). Denominator is the full test set.
* Same-enumeration control: the same enumerated sets ranked by the product of
  Stage 1 probabilities instead of the learned reranker score.

Results are written as JSON (aggregate) and JSONL (per target, including the
rank of the ground-truth set) so that the report tables can be traced back to
individual predictions.

Usage (repository .venv-retro is required; `bash install.sh --retro`)::

    .venv-retro/bin/python tools/eval_retro_benchmark.py \
        --device cuda:0 --out submission/goai_final/metrics/retro_benchmark

    # smoke test on a deterministic 50-target subsample
    .venv-retro/bin/python tools/eval_retro_benchmark.py --limit 50 --device cpu
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import time
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

K_VALUES = (1, 3, 5, 10, 20)


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    except Exception:  # noqa: BLE001 - best effort provenance
        return "unknown"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_test_split(path: Path) -> list[dict]:
    rows = []
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("type") != "test":
                continue
            rows.append({
                "target": row["target"],
                "gt_ids": sorted(int(x) for x in row["precursor_ids"].split(",")),
                "doi": row.get("doi", ""),
                "year": row.get("year", ""),
            })
    return rows


def rank_of(true_set: tuple[int, ...], ranked_sets: list[tuple[int, ...]]) -> int | None:
    try:
        return ranked_sets.index(true_set) + 1
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--device", default=os.environ.get("GOAI_RETRO_DEVICE", "cpu"))
    ap.add_argument("--limit", type=int, default=0, help="evaluate a deterministic random subsample of this size (0 = full test set)")
    ap.add_argument("--seed", type=int, default=20260504, help="subsample seed (only used with --limit)")
    ap.add_argument("--top-m", type=int, default=30)
    ap.add_argument("--pool-cap", type=int, default=15)
    ap.add_argument("--min-set-size", type=int, default=2)
    ap.add_argument("--max-set-size", type=int, default=5)
    ap.add_argument("--out", default="submission/goai_final/metrics/retro_benchmark", help="output prefix (writes <prefix>.json and <prefix>.per_target.jsonl)")
    args = ap.parse_args()

    os.environ.setdefault("GOAI_WORKSPACE", str(REPO / "workspace"))
    from server.core import inorganic_retro as ir

    root = ir.model_root()
    readiness = ir.status()
    if not readiness.get("available"):
        print(json.dumps(readiness, indent=2, ensure_ascii=False))
        print("retro model unavailable; run `bash install.sh --retro`", file=sys.stderr)
        return 2

    predictor = ir.TwoStagePredictor(root, args.device)
    np = predictor.np

    split_path = root / "data" / "retro_split.csv"
    rows = load_test_split(split_path)
    if args.limit and args.limit < len(rows):
        rng = random.Random(args.seed)
        rows = rng.sample(rows, args.limit)
    n = len(rows)
    print(f"evaluating {n} test targets on {predictor.device} (top_m={args.top_m}, pool_cap={args.pool_cap}, sizes {args.min_set_size}-{args.max_set_size})", flush=True)

    out_prefix = Path(args.out)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    per_target_path = out_prefix.with_suffix(".per_target.jsonl")

    stage1_hits = {k: 0 for k in K_VALUES}
    combo_hits = {k: 0 for k in K_VALUES}
    product_hits = {k: 0 for k in K_VALUES}
    combo_rr = 0.0
    product_rr = 0.0
    enumerated = 0
    parse_failures = 0
    started = time.monotonic()

    with per_target_path.open("w", encoding="utf-8") as sink:
        for i, row in enumerate(rows, 1):
            record = {"target": row["target"], "gt_ids": row["gt_ids"], "doi": row["doi"], "year": row["year"]}
            try:
                comp, target_vec = predictor.composition_features(row["target"])
            except Exception as exc:  # noqa: BLE001 - benchmark must not abort on one bad formula
                parse_failures += 1
                record["error"] = f"{type(exc).__name__}: {exc}"
                sink.write(json.dumps(record, ensure_ascii=False) + "\n")
                continue

            x = np.asarray([target_vec], dtype=np.float32)
            stage1_probs = predictor.predict_retriever(
                predictor.stage1, x, predictor.precursor_pack, predictor.device,
                predictor.max_elems, batch_size=1,
            )[0]
            order = np.argsort(-stage1_probs)
            gt = set(row["gt_ids"])
            n_gt = len(gt)
            for k in K_VALUES:
                if gt.issubset(set(order[: max(k, n_gt)].tolist())):
                    stage1_hits[k] += 1
            gt_ranks = [int(np.where(order == pid)[0][0]) + 1 for pid in row["gt_ids"]]
            record["stage1_gt_precursor_ranks"] = gt_ranks

            raw_pool = order[: args.top_m].tolist()
            target_metals = set(np.where(target_vec > 0)[0].tolist()) - predictor.VOLATILE_ELEMENTS
            pool = [int(pid) for pid in raw_pool if predictor.env.precursor_metals[int(pid)].issubset(target_metals)]
            fallback = False
            if len(pool) < args.min_set_size:
                pool = [int(pid) for pid in raw_pool[: max(args.pool_cap, args.min_set_size)]]
                fallback = True
            pool = pool[: args.pool_cap]
            combos: list[list[int]] = []
            for size in range(args.min_set_size, min(args.max_set_size, len(pool)) + 1):
                combos.extend([list(c) for c in combinations(pool, size)])
            record["pool_size"] = len(pool)
            record["filter_fallback"] = fallback
            record["enumerated_sets"] = len(combos)

            true_set = tuple(sorted(gt))
            combo_keys = [tuple(sorted(c)) for c in combos]
            if true_set in combo_keys:
                enumerated += 1
            record["gt_enumerated"] = true_set in combo_keys

            if combos:
                arrays = predictor.combos_to_arrays(
                    combos, stage1_probs, target_vec,
                    predictor.env.precursor_key_elements, predictor.env.precursor_metals,
                    predictor.chem_prior, predictor.data["precursor_X"], predictor.charge,
                    predictor.max_elems,
                )
                te, tf, tm = predictor.comp_to_sparse_arrays(target_vec, predictor.max_elems)
                sample = {"correct_idx": None, "gt_ids": [], "combos": combos,
                          "target_elem": te, "target_frac": tf, "target_mask": tm, **arrays}
                scores = predictor.score_sample(predictor.stage2, sample, predictor.device, chunk=512)
                rerank_order = np.argsort(-scores)
                ranked_sets = [combo_keys[int(j)] for j in rerank_order]
                products = np.asarray([float(np.prod(stage1_probs[list(c)])) for c in combos])
                product_order = np.argsort(-products)
                product_sets = [combo_keys[int(j)] for j in product_order]
            else:
                ranked_sets, product_sets = [], []

            r = rank_of(true_set, ranked_sets)
            rp = rank_of(true_set, product_sets)
            record["reranker_gt_rank"] = r
            record["product_gt_rank"] = rp
            record["reranker_top1"] = [predictor.precursor_names.get(pid, str(pid)) for pid in ranked_sets[0]] if ranked_sets else []
            record["gt_precursors"] = [predictor.precursor_names.get(pid, str(pid)) for pid in row["gt_ids"]]
            if r is not None:
                combo_rr += 1.0 / r
                for k in K_VALUES:
                    if r <= k:
                        combo_hits[k] += 1
            if rp is not None:
                product_rr += 1.0 / rp
                for k in K_VALUES:
                    if rp <= k:
                        product_hits[k] += 1
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            if i % 100 == 0 or i == n:
                el = time.monotonic() - started
                print(f"  {i}/{n}  C@1={100*combo_hits[1]/i:.2f}  C@20={100*combo_hits[20]/i:.2f}  MRR={100*combo_rr/i:.2f}  ({el:.0f}s)", flush=True)

    def pct(v: float) -> float:
        return round(100.0 * v / n, 2)

    summary = {
        "benchmark": "Retrieval-Retro year split (train/val <= 2017, test >= 2018), test split",
        "n_test": n,
        "subsample": {"limit": args.limit, "seed": args.seed} if args.limit else None,
        "parse_failures": parse_failures,
        "protocol": {
            "top_m": args.top_m, "pool_cap": args.pool_cap,
            "set_sizes": list(range(args.min_set_size, args.max_set_size + 1)),
            "hard_metal_filter": True,
            "denominator": "full test set (targets whose exact set is not enumerated count as misses)",
        },
        "stage1_generator": {f"top_{k}_coverage": pct(stage1_hits[k]) for k in K_VALUES},
        "stage2_reranker": {
            **{f"combo_{k}": pct(combo_hits[k]) for k in K_VALUES},
            "combo_mrr": pct(combo_rr),
            "gt_enumerated_rate": pct(enumerated),
        },
        "same_enumeration_product_control": {
            **{f"combo_{k}": pct(product_hits[k]) for k in K_VALUES},
            "combo_mrr": pct(product_rr),
        },
        "reference": {
            "paper": "RECIPE (NeurIPS 2026 submission): Retro test Combo@1 71.70+-0.10, Combo@20 89.82+-1.74, Combo MRR 77.43+-0.69 (3 seeds); Retrieval-Retro baseline Combo@1 60.40, Combo@20 69.00, MRR 63.29",
            "vendored_checkpoint_summary": {
                "stage1_top20": 95.78, "stage2_combo1_full": 71.81,
                "stage2_combo20_full": 89.21, "stage2_mrr_full": 77.48,
            },
        },
        "provenance": {
            "git_commit": _git_commit(),
            "device": predictor.device,
            "python": platform.python_version(),
            "stage1_checkpoint_sha256": _sha256(root / "checkpoints" / "stage1_retriever.pt"),
            "stage2_checkpoint_sha256": _sha256(root / "checkpoints" / "stage2_reranker.pt"),
            "split_csv_sha256": _sha256(split_path),
            "elapsed_s": round(time.monotonic() - started, 1),
        },
    }
    out_json = out_prefix.with_suffix(".json")
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary["stage2_reranker"], indent=2))
    print(f"wrote {out_json} and {per_target_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
