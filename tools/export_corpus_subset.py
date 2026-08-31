#!/usr/bin/env python3
"""Build the public literature subset from an explicit allow-list."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.core.corpus_export import export_public_subset


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export only explicitly selected and redistributable corpus text. "
            "The compact-parquet format is self-contained and supports search, "
            "bounded reading, and DOI lookup through the same MCP tools as the "
            "private corpus."
        )
    )
    parser.add_argument("manifest", help="private selection manifest JSON")
    parser.add_argument("output_dir", help="public subset output directory")
    parser.add_argument(
        "--format",
        choices=("compact-parquet", "files"),
        default="compact-parquet",
        help="public package format (default: compact-parquet)",
    )
    args = parser.parse_args()
    result = export_public_subset(
        args.manifest, args.output_dir, output_format=args.format
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
