#!/usr/bin/env python3
"""Report/import actual usage without invoking models or running experiments."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from server.core.usage_cost import DEFAULT_PRICES
from server.core.usage_sources import BillingReader, append_usage, atomic_json, initialize_billing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["report", "record", "init", "attempt"])
    parser.add_argument("--workspace", action="append", type=Path, required=True)
    parser.add_argument("--prices", type=Path, default=Path(os.environ.get("GOAI_PRICE_CONFIG", str(DEFAULT_PRICES))))
    parser.add_argument("--task-id")
    parser.add_argument("--session-id")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--service-tier", default=os.environ.get("GOAI_SERVICE_TIER"))
    args = parser.parse_args()
    if args.command == "init":
        result = initialize_billing(args.workspace[0], args.prices, args.task_id or os.environ.get("GOAI_BILLING_TASK_ID"))
    elif args.command == "record":
        if args.receipt is None:
            parser.error("record 需要 --receipt")
        result = append_usage(args.workspace[0], json.loads(args.receipt.read_text()))
    elif args.command == "attempt":
        if not args.trace or not args.model:
            parser.error("attempt 需要 --trace 和 --model")
        result = {"model": args.model, "service_tier": args.service_tier, "started_at": datetime.now(timezone.utc).isoformat()}
        atomic_json(args.trace.with_suffix(".billing.json"), result)
    else:
        reader = BillingReader(REPO / "workspace/.billing/cache.sqlite3", args.prices)
        result = reader.report(args.workspace, task_id=args.task_id, session_id=args.session_id, include_records=True)
    if args.output:
        atomic_json(args.output, result)
        print(json.dumps({"output": str(args.output), "summary": result.get("summary", result)}, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
