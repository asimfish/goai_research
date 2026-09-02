#!/usr/bin/env python3
"""Dry run of the vendored two-stage inorganic precursor predictor (RECIPE).

Loads both checkpoints (SHA-256 verified), builds the chemistry prior from the
shipped precursor library, and predicts Top-K complete precursor sets for one or
more target formulas through the exact code path the MCP tool
``predict_precursor_routes`` uses. Exits non-zero if anything fails.

    .venv/bin/python tools/retro_dry_run.py                      # Li7La3Zr2O12 on CPU
    .venv/bin/python tools/retro_dry_run.py Ba5Y12ZnSi8O40 --top-k 5 --json
    GOAI_RETRO_DEVICE=cuda:0 .venv/bin/python tools/retro_dry_run.py LiFePO4

Predictions are model candidates (``chemical_route_verified=false``), not
experimentally validated routes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message="enable_nested_tensor")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("formulas", nargs="*", default=["Li7La3Zr2O12"], help="target formulas (default: Li7La3Zr2O12)")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--device", default=os.environ.get("GOAI_RETRO_DEVICE", "cpu"))
    ap.add_argument("--json", action="store_true", help="print the full tool response as JSON")
    args = ap.parse_args()

    os.environ.setdefault("GOAI_WORKSPACE", str(ROOT / "workspace"))
    from server.core import inorganic_retro as ir

    readiness = ir.status()
    if not readiness.get("available"):
        print(json.dumps(readiness, indent=2, ensure_ascii=False))
        print("retro model unavailable (missing dependency, asset or checkpoint hash mismatch); run `bash install.sh --retro`", file=sys.stderr)
        return 2
    print(f"checkpoints verified: stage1 {readiness['checkpoint_sha256']['stage1'][:12]}… stage2 {readiness['checkpoint_sha256']['stage2'][:12]}…")

    failures = 0
    for formula in args.formulas:
        started = time.monotonic()
        result = ir.predict_precursor_routes(formula, top_k=args.top_k, device=args.device)
        elapsed = time.monotonic() - started
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        if not result.get("ok"):
            failures += 1
            print(f"FAIL {formula}: {result.get('error')}", file=sys.stderr)
            continue
        gen = result["candidate_generation"]
        print(f"\n{formula} -> {result['target_formula_normalized']}  "
              f"(pool {gen['filtered_pool_size']}, {gen['enumerated_route_count']} candidate sets, "
              f"{elapsed:.1f}s on {result['runtime']['device']})")
        for route in result["routes"]:
            precursors = " + ".join(p["formula"] for p in route["precursors"])
            print(f"  #{route['rank']}  {precursors:48s} stage2 score {route['stage2_score']:7.3f}   "
                  f"pool prob {route['route_probability_within_candidate_pool']:.3f}")
        print("  (model candidates only: chemical_route_verified=false)")
    if failures:
        return 1
    print("\nRETRO DRY RUN PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
