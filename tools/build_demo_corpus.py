#!/usr/bin/env python3
"""Deterministically build the tiny, non-citable compact-Parquet demo corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.core.parquet_corpus import COMPACT_FORMAT, REQUIRED_COLUMNS, normalize_doi


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(source: Path, output_dir: Path) -> dict[str, object]:
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - regular install includes it
        raise RuntimeError("building the demo corpus requires duckdb") from exc

    payload = json.loads(source.read_text(encoding="utf-8"))
    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, list) or not records:
        raise ValueError("demo_records.json must contain a non-empty records list")
    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = output_dir / "corpus.parquet"
    rows: list[tuple[str, str, str, str, str, str, bool]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"records[{index}] must be an object")
        doi = normalize_doi(str(record.get("doi_normalized") or ""))
        markdown = str(record.get("markdown") or "")
        if not doi or not markdown:
            raise ValueError(f"records[{index}] needs doi_normalized and markdown")
        rows.append((
            hashlib.md5(doi.encode("utf-8")).hexdigest(),
            doi,
            str(record.get("title") or f"Synthetic record {index + 1}"),
            str(record.get("publisher_group") or "goai-demo"),
            markdown,
            "CC0-1.0 synthetic fixture",
            True,
        ))

    connection = duckdb.connect(database=":memory:")
    try:
        connection.execute(
            "CREATE TABLE documents(uuid VARCHAR, doi_normalized VARCHAR, "
            "title VARCHAR, publisher_group VARCHAR, markdown VARCHAR, "
            "license VARCHAR, synthetic BOOLEAN)"
        )
        connection.executemany("INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
        connection.execute("COPY documents TO ? (FORMAT PARQUET)", [str(parquet_path)])
    finally:
        connection.close()

    manifest: dict[str, object] = {
        "schema_version": 1,
        "corpus_format": COMPACT_FORMAT,
        "package_id": str(payload.get("package_id") or "goai-synthetic-demo-corpus"),
        "document_count": len(rows),
        "parquet_files": [parquet_path.name],
        "parquet_sha256": sha256(parquet_path),
        "synthetic": True,
        "citable": False,
        "required_columns": sorted(REQUIRED_COLUMNS),
        "notice": "Synthetic interface fixture only; do not cite as scientific evidence.",
    }
    manifest_path = output_dir / "corpus_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT / "examples" / "demo_corpus" / "demo_records.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "examples" / "demo_corpus",
    )
    args = parser.parse_args()
    result = build(args.source.resolve(), args.output_dir.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
