#!/usr/bin/env python3
"""Build the public compact-Parquet corpus from exactly the references a report cites.

The private full-text corpus cannot be published.  For the competition package we
therefore export only the Markdown full text of the documents that the final
report actually cites (every entry in its ``references.bib``), looked up by DOI
through the same ``lookup_doi`` code path the MCP tool ``lookup_local_doi`` uses.

Cited papers whose full text is *not* in the private corpus are kept as
metadata-only records (citation key, DOI, official URL) in the package
manifest, so the evidence chain stays complete even when the text is absent.

The resulting directory is a self-contained ``goai-compact-parquet-v1`` package
that ``grep_local_corpus`` / ``read_local_document`` / ``lookup_local_doi`` can
serve when ``GOAI_LOCAL_CORPUS_ROOTS`` points at it.

Environment (private side only; nothing from it is written into the package)::

    GOAI_LOCAL_CORPUS_ROOTS           private Parquet package root(s)
    GOAI_LOCAL_CORPUS_EXPECTED_INDEX  private SQLite DOI index
    GOAI_LOCAL_CORPUS_SHARD_ROOT      private shard directory

Usage::

    .venv/bin/python tools/build_cited_corpus.py \
        --bib submission/03_运行与评测包/正式案例_BYZSO冷启动/最终输出/references.bib \
        --out submission/02_研究数据与证据包/corpus_release \
        --license "review-only; publisher copyright retained"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.core.bibtex import parse_bibtex  # noqa: E402
from server.core.corpus_export import export_public_subset  # noqa: E402
from server.core.local_corpus import configured_roots  # noqa: E402
from server.core import parquet_corpus  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bib", required=True, help="references.bib of the final report")
    ap.add_argument("--out", required=True, help="output package directory (must be absent or empty)")
    ap.add_argument("--license", default="review-only; publisher copyright retained; provided solely for competition reproduction, no redistribution",
                    help="license string recorded for every exported full text")
    ap.add_argument("--publisher-group", default="goai-cited-release")
    ap.add_argument("--keep-staging", action="store_true", help="keep the staging directory of extracted Markdown files")
    args = ap.parse_args()

    bib_path = Path(args.bib).resolve()
    entries = parse_bibtex(bib_path.read_text(encoding="utf-8"))
    roots = configured_roots(None)
    if not roots:
        print("GOAI_LOCAL_CORPUS_ROOTS is not configured (private corpus needed to extract text)", file=sys.stderr)
        return 2
    files = parquet_corpus.discover_files(roots)

    staging = Path(tempfile.mkdtemp(prefix="goai-cited-corpus-"))
    documents: list[dict] = []
    found, missing, no_doi = 0, 0, 0
    for entry in entries:
        key = entry.get("key") or entry.get("id") or ""
        fields = entry.get("fields") or entry
        doi = str(fields.get("doi") or "").strip()
        title = str(fields.get("title") or "").strip().strip("{}")
        url = str(fields.get("url") or (f"https://doi.org/{doi}" if doi else "")).strip()
        record = {
            "citation_key": key,
            "doi": doi,
            "url": url,
            "title": title,
            "year": str(fields.get("year") or ""),
        }
        if not doi:
            no_doi += 1
            record.update({"redistributable": False, "reason": "no DOI in bib entry"})
            documents.append(record)
            continue
        result = parquet_corpus.lookup_doi(doi, roots=roots, files=files, start_line=1, end_line=10_000_000)
        if not (result.get("ok") and result.get("found")):
            missing += 1
            record.update({"redistributable": False,
                           "reason": "full text not in private corpus" if result.get("ok") else result.get("error", "lookup error")})
            documents.append(record)
            continue
        markdown = "\n".join(line["text"] for line in result["lines"]) + "\n"
        md_path = staging / f"{key}.md"
        md_path.write_text(markdown, encoding="utf-8")
        found += 1
        record.update({
            "source_path": str(md_path),
            # keep the private uuid (md5 of the normalised DOI) so lookups agree across packages
            "document_id": hashlib.md5(parquet_corpus.normalize_doi(doi).encode("utf-8")).hexdigest(),
            "title": result.get("title") or title,
            "publisher_group": args.publisher_group,
            "license": args.license,
            "redistributable": True,
            "synthetic": False,
            "private_lookup_engine": result.get("lookup_engine"),
        })
        documents.append(record)
        print(f"  found  {key:40s} {doi}", flush=True)
    for rec in documents:
        if not rec.get("redistributable"):
            print(f"  MISSING {rec['citation_key']:40s} {rec.get('doi','-')}  ({rec.get('reason')})")

    # The exporter validates source paths against the corpus roots; the staging dir is the root here.
    # Metadata-only references have no file, so they are recorded in the companion index instead.
    manifest_path = staging / "selection.json"
    manifest_path.write_text(json.dumps({"documents": [
        {k: v for k, v in d.items() if k not in {"reason", "private_lookup_engine", "year"}}
        for d in documents if d.get("redistributable")
    ]}, ensure_ascii=False, indent=2), encoding="utf-8")
    out = Path(args.out).resolve()
    result = export_public_subset(manifest_path, out, roots=[staging], output_format="compact-parquet")

    # Companion index: one row per cited reference, full text present or not.
    index_rows = [{
        "citation_key": d["citation_key"], "doi": d.get("doi", ""), "url": d.get("url", ""),
        "title": d.get("title", ""), "year": d.get("year", ""),
        "full_text_in_package": bool(d.get("redistributable")),
        "document_id": d.get("document_id", ""),
        "note": d.get("reason", ""),
    } for d in documents]
    (out / "cited_references_index.json").write_text(
        json.dumps({
            "bib": bib_path.name, "n_references": len(entries), "n_full_text": found,
            "n_metadata_only": missing + no_doi, "license": args.license,
            "documents": index_rows,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {"n_references": len(entries), "full_text_exported": found, "metadata_only": missing, "no_doi": no_doi,
               "output": str(out), "export": {k: v for k, v in result.items() if k != "documents"}}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.keep_staging:
        print(f"staging kept at {staging}")
    else:
        shutil.rmtree(staging, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
