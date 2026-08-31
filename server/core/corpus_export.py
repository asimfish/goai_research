"""Export an allow-listed, redistributable subset of the private corpus.

The public package is built from an explicit JSON manifest.  Source paths are
validated against ``GOAI_LOCAL_CORPUS_ROOTS`` and are never written to the
public manifest, so this command cannot accidentally publish the NAS layout.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Iterable

from .local_corpus import _allowed_path, configured_roots
from .parquet_corpus import COMPACT_FORMAT, normalize_doi


_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_items(manifest_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = payload.get("documents") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ValueError("manifest must be a JSON list or contain a 'documents' list")
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not item.get("source_path"):
            raise ValueError(f"documents[{index}] must contain source_path")
    return items


def _public_name(item: dict[str, Any], source: Path, digest: str) -> str:
    requested = str(item.get("document_id") or item.get("citation_key") or source.stem)
    safe = _SAFE_ID.sub("-", requested).strip("-._") or digest[:12]
    return f"{safe}-{digest[:12]}{source.suffix.lower()}"


def export_public_subset(
    manifest_path: str | Path,
    output_dir: str | Path,
    *,
    roots: Iterable[str | Path] | None = None,
    output_format: str = "files",
) -> dict[str, Any]:
    """Export allow-listed text as files or one self-contained Parquet package.

    Every copied item must explicitly set ``redistributable`` to true and
    provide a non-empty ``license`` value.  Non-redistributable entries remain
    as DOI/link-only metadata records.
    """
    manifest = Path(manifest_path).expanduser().resolve()
    output = Path(output_dir).expanduser().resolve()
    if output_format not in {"files", "compact-parquet"}:
        raise ValueError("output_format must be 'files' or 'compact-parquet'")
    allowed_roots = configured_roots(roots)
    if not allowed_roots:
        raise ValueError("no local corpus roots are configured")
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    items = _load_items(manifest)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(
            "output_dir must be absent or empty; use a fresh directory so stale private "
            "documents cannot leak into the public package"
        )
    output.mkdir(parents=True, exist_ok=True)
    files_dir = output / "documents"
    if output_format == "files":
        files_dir.mkdir(parents=True, exist_ok=True)

    exported: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    parquet_rows: list[tuple[str, str, str, str, str, str, bool]] = []
    seen_names: set[str] = set()
    for index, item in enumerate(items):
        source = _allowed_path(item["source_path"], allowed_roots)
        public_metadata = {
            key: item[key]
            for key in ("document_id", "citation_key", "doi", "url", "title", "license")
            if item.get(key) not in (None, "")
        }
        if item.get("redistributable") is not True:
            skipped.append({
                **public_metadata,
                "redistributable": False,
                "reason": "not explicitly marked redistributable; file not copied",
            })
            continue
        if not str(item.get("license") or "").strip():
            raise ValueError(
                f"documents[{index}] is redistributable but has no license declaration"
            )
        digest = _sha256(source)
        filename = _public_name(item, source, digest)
        if filename in seen_names:
            raise ValueError(f"duplicate public filename: {filename}")
        seen_names.add(filename)
        if output_format == "files":
            destination = files_dir / filename
            if destination.exists():
                if _sha256(destination) != digest:
                    raise FileExistsError(f"refusing to overwrite different file: {destination}")
            else:
                shutil.copy2(source, destination)
            public_path = f"documents/{filename}"
        else:
            if source.suffix.casefold() not in {".md", ".markdown", ".txt"}:
                raise ValueError(
                    f"compact-parquet only accepts UTF-8 text/Markdown sources: {source.name}"
                )
            markdown = source.read_text(encoding="utf-8")
            doi = normalize_doi(str(item.get("doi") or ""))
            document_id = str(item.get("document_id") or "").strip()
            uuid = document_id or (
                hashlib.md5(doi.encode("utf-8")).hexdigest() if doi else digest[:32]
            )
            parquet_rows.append((
                uuid,
                doi,
                str(item.get("title") or source.stem),
                str(item.get("publisher_group") or "public-release"),
                markdown,
                str(item["license"]),
                bool(item.get("synthetic", False)),
            ))
            public_path = f"corpus.parquet#{uuid}"
        exported.append({
            **public_metadata,
            "redistributable": True,
            "path": public_path,
            "sha256": digest,
            "bytes": source.stat().st_size,
        })

    result: dict[str, Any] = {
        "schema_version": 1,
        "source_manifest_sha256": _sha256(manifest),
        "output_format": output_format,
        "exported_count": len(exported),
        "metadata_only_count": len(skipped),
        "documents": exported,
        "metadata_only": skipped,
    }
    if output_format == "compact-parquet":
        try:
            import duckdb
        except ImportError as exc:  # pragma: no cover - normal install includes it
            raise RuntimeError("compact-parquet export requires duckdb") from exc
        parquet_path = output / "corpus.parquet"
        connection = duckdb.connect(database=":memory:")
        try:
            connection.execute(
                "CREATE TABLE documents(uuid VARCHAR, doi_normalized VARCHAR, "
                "title VARCHAR, publisher_group VARCHAR, markdown VARCHAR, "
                "license VARCHAR, synthetic BOOLEAN)"
            )
            if parquet_rows:
                connection.executemany(
                    "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?)", parquet_rows
                )
            connection.execute("COPY documents TO ? (FORMAT PARQUET)", [str(parquet_path)])
        finally:
            connection.close()
        result.update({
            "corpus_format": COMPACT_FORMAT,
            "package_id": str(
                manifest_payload.get("package_id", output.name)
                if isinstance(manifest_payload, dict) else output.name
            ),
            "document_count": len(parquet_rows),
            "parquet_files": ["corpus.parquet"],
            "parquet_sha256": _sha256(parquet_path),
            "synthetic": bool(parquet_rows) and all(row[-1] for row in parquet_rows),
            "citable": bool(parquet_rows) and all(not row[-1] for row in parquet_rows),
            "required_columns": [
                "uuid", "doi_normalized", "title", "publisher_group", "markdown",
            ],
        })
        public_manifest = output / "corpus_manifest.json"
    else:
        public_manifest = output / "MANIFEST.json"
    public_manifest.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {**result, "manifest_path": str(public_manifest)}


__all__ = ["export_public_subset"]
