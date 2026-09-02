"""DuckDB-backed access to full-size and compact Parquet text corpora.

Both deployments use the same minimal schema.  A private installation may add
an external DOI index for fast lookup across tens of millions of rows, while a
small public package is self-contained and resolves DOI queries directly from
its Parquet file.  No private path or corpus size is part of the public API.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote, unquote, urlsplit


PARQUET_SCHEME = "parquet"
COMPACT_FORMAT = "goai-compact-parquet-v1"
MANIFEST_NAMES = ("corpus_manifest.json", "CORPUS_MANIFEST.json")
REQUIRED_COLUMNS = {
    "uuid", "doi_normalized", "title", "publisher_group", "markdown",
}


def _duckdb():
    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - exercised through status
        raise RuntimeError(
            "Parquet corpus requires duckdb; install the project dependencies"
        ) from exc
    return duckdb


def discover_files(roots: Iterable[Path]) -> list[Path]:
    """Find compact-package Parquet files without walking unrelated NAS trees."""
    found: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix.casefold() == ".parquet":
            candidates = [root]
        elif root.is_dir():
            candidates = [*root.glob("*.parquet"), *root.glob("publisher_group=*/*.parquet")]
        else:
            candidates = []
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in found:
                found.append(resolved)
    return sorted(found)


def load_manifest(roots: Iterable[Path]) -> dict[str, Any] | None:
    """Load the first corpus package manifest without following outside paths."""
    for root in roots:
        directory = root if root.is_dir() else root.parent
        for name in MANIFEST_NAMES:
            candidate = directory / name
            if not candidate.is_file():
                continue
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                return {
                    "ok": False,
                    "path": str(candidate.resolve()),
                    "error": f"invalid corpus manifest: {type(exc).__name__}: {exc}",
                }
            if not isinstance(payload, dict):
                return {
                    "ok": False,
                    "path": str(candidate.resolve()),
                    "error": "invalid corpus manifest: top level must be an object",
                }
            # Runtime-owned fields come last so a package cannot forge ok/path.
            return {**payload, "ok": True, "path": str(candidate.resolve())}
    return None


def inspect_schema(files: list[Path]) -> dict[str, Any]:
    """Return a cheap metadata-only compatibility check for a Parquet package."""
    if not files:
        return {"ok": False, "columns": [], "missing_columns": sorted(REQUIRED_COLUMNS)}
    duckdb = _duckdb()
    connection = duckdb.connect(database=":memory:")
    try:
        rows = connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?, union_by_name=true, "
            "hive_partitioning=true)",
            [[str(path) for path in files]],
        ).fetchall()
    except Exception as exc:
        return {
            "ok": False,
            "columns": [],
            "missing_columns": sorted(REQUIRED_COLUMNS),
            "error": f"cannot inspect Parquet schema: {type(exc).__name__}: {exc}",
        }
    finally:
        connection.close()
    columns = [str(row[0]) for row in rows]
    missing = sorted(REQUIRED_COLUMNS.difference(columns))
    return {"ok": not missing, "columns": columns, "missing_columns": missing}


def _require_schema(files: list[Path]) -> dict[str, Any]:
    schema = inspect_schema(files)
    if not schema["ok"]:
        detail = schema.get("error") or (
            "missing required columns: " + ", ".join(schema["missing_columns"])
        )
        raise RuntimeError(f"incompatible Parquet corpus: {detail}")
    return schema


def _package_citable(roots: list[Path], synthetic: bool) -> bool:
    manifest = load_manifest(roots)
    if manifest and manifest.get("ok") and "citable" in manifest:
        return bool(manifest["citable"]) and not synthetic
    return not synthetic


def available() -> bool:
    try:
        _duckdb()
    except RuntimeError:
        return False
    return True


def make_document_ref(path: Path, uuid: str) -> str:
    return f"{PARQUET_SCHEME}://{quote(str(path.resolve()), safe='/')}#{quote(uuid)}"


def parse_document_ref(value: str) -> tuple[Path, str]:
    parsed = urlsplit(value)
    if parsed.scheme != PARQUET_SCHEME or not parsed.path or not parsed.fragment:
        raise ValueError("invalid parquet document reference")
    return Path(unquote(parsed.path)).resolve(), unquote(parsed.fragment)


def _inside_roots(path: Path, roots: Iterable[Path]) -> bool:
    for root in roots:
        resolved = root.resolve()
        if path == resolved or (resolved.is_dir() and path.is_relative_to(resolved)):
            return True
    return False


def _context(
    markdown: str,
    query: str,
    *,
    radius: int,
    case_sensitive: bool,
    regex: bool,
    text_limit: int,
) -> tuple[int, str, bool, list[dict[str, Any]]]:
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(query if regex else re.escape(query), flags)
    lines = markdown.splitlines()
    match_index = next((index for index, line in enumerate(lines) if pattern.search(line)), 0)
    raw = lines[match_index] if lines else ""

    def clipped(value: str) -> tuple[str, bool]:
        if len(value) <= text_limit:
            return value, False
        return value[:text_limit].rstrip() + " …[truncated]", True

    text, was_clipped = clipped(raw)
    rows: list[dict[str, Any]] = []
    for index in range(max(0, match_index - radius), min(len(lines), match_index + radius + 1)):
        row_text, row_clipped = clipped(lines[index])
        row: dict[str, Any] = {"line": index + 1, "text": row_text}
        if row_clipped:
            row["text_truncated"] = True
        rows.append(row)
    return match_index + 1, text, was_clipped, rows


def _run_with_timeout(connection: Any, sql: str, params: list[Any], timeout: float):
    expired = threading.Event()

    def interrupt() -> None:
        expired.set()
        connection.interrupt()

    timer = threading.Timer(max(timeout, 0.1), interrupt)
    timer.daemon = True
    timer.start()
    try:
        return connection.execute(sql, params).fetchall(), False
    except Exception:
        if expired.is_set():
            return [], True
        raise
    finally:
        timer.cancel()


def search(
    query: str,
    *,
    files: list[Path],
    roots: list[Path],
    max_results: int,
    context_lines: int,
    case_sensitive: bool,
    regex: bool,
    timeout_seconds: float,
    text_limit: int,
) -> dict[str, Any]:
    schema = _require_schema(files)
    columns = set(schema["columns"])
    duckdb = _duckdb()
    connection = duckdb.connect(database=":memory:")
    connection.execute(
        f"SET threads={max(1, int(os.environ.get('GOAI_LOCAL_CORPUS_THREADS', '8')))}"
    )
    if regex:
        # Compile locally for an immediate, clear invalid-regex error.
        re.compile(query, 0 if case_sensitive else re.IGNORECASE)
        predicate = "regexp_matches(markdown, ?, 'c')" if case_sensitive else "regexp_matches(markdown, ?, 'i')"
    else:
        predicate = "contains(markdown, ?)" if case_sensitive else "contains(lower(markdown), lower(?))"
    synthetic_expr = "coalesce(synthetic, false)" if "synthetic" in columns else "false"
    license_expr = "license" if "license" in columns else "NULL::VARCHAR"
    sql = f"""
        SELECT uuid, doi_normalized, title, publisher_group, markdown, filename,
               {synthetic_expr} AS synthetic, {license_expr} AS license
        FROM read_parquet(?, hive_partitioning=true, union_by_name=true, filename=true)
        WHERE {predicate}
        LIMIT ?
    """
    try:
        rows, timed_out = _run_with_timeout(
            connection,
            sql,
            [[str(path) for path in files], query, max_results + 1],
            timeout_seconds,
        )
    finally:
        connection.close()
    truncated = len(rows) > max_results
    rows = rows[:max_results]
    matches: list[dict[str, Any]] = []
    for uuid, doi, title, publisher, markdown, filename, synthetic, license_name in rows:
        source = Path(filename).resolve()
        if not _inside_roots(source, roots):
            continue
        line, text, clipped, context = _context(
            markdown,
            query,
            radius=context_lines,
            case_sensitive=case_sensitive,
            regex=regex,
            text_limit=text_limit,
        )
        match: dict[str, Any] = {
            "path": make_document_ref(source, uuid),
            "document_id": uuid,
            "doi": doi,
            "title": title,
            "publisher_group": publisher,
            "synthetic": bool(synthetic),
            "citable": _package_citable(roots, bool(synthetic)),
            "line": line,
            "text": text,
            "context": context,
        }
        if clipped:
            match["text_truncated"] = True
        if license_name:
            match["license"] = license_name
        matches.append(match)
    return {
        "ok": bool(matches) or not timed_out,
        "engine": "duckdb-parquet",
        "query": query,
        "total_returned": len(matches),
        "truncated": truncated,
        "timed_out": timed_out,
        "timeout_seconds": timeout_seconds,
        "roots": [str(path) for path in roots],
        "parquet_files": len(files),
        "matches": matches,
    }


def _fetch_markdown(path: Path, uuid: str) -> tuple[Any, ...] | None:
    schema = _require_schema([path])
    columns = set(schema["columns"])
    synthetic_expr = "coalesce(synthetic, false)" if "synthetic" in columns else "false"
    license_expr = "license" if "license" in columns else "NULL::VARCHAR"
    duckdb = _duckdb()
    connection = duckdb.connect(database=":memory:")
    try:
        return connection.execute(
            "SELECT uuid, doi_normalized, title, publisher_group, markdown, "
            f"{synthetic_expr} AS synthetic, {license_expr} AS license "
            "FROM read_parquet(?) WHERE uuid=? LIMIT 1",
            [str(path), uuid],
        ).fetchone()
    finally:
        connection.close()


def _lookup_compact_doi(
    normalized: str,
    *,
    uuid: str,
    files: list[Path],
    roots: list[Path],
    start_line: int,
    end_line: int,
) -> dict[str, Any]:
    schema = _require_schema(files)
    columns = set(schema["columns"])
    synthetic_expr = "coalesce(synthetic, false)" if "synthetic" in columns else "false"
    license_expr = "license" if "license" in columns else "NULL::VARCHAR"
    duckdb = _duckdb()
    connection = duckdb.connect(database=":memory:")
    try:
        row = connection.execute(
            "SELECT uuid, doi_normalized, title, publisher_group, markdown, filename, "
            f"{synthetic_expr} AS synthetic, {license_expr} AS license "
            "FROM read_parquet(?, union_by_name=true, hive_partitioning=true, "
            "filename=true) WHERE lower(doi_normalized)=? OR uuid=? LIMIT 1",
            [[str(path) for path in files], normalized, uuid],
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return {"ok": True, "found": False, "doi": normalized, "document_id": uuid,
                "lookup_engine": "compact-parquet"}
    (stored_uuid, stored_doi, title, publisher, markdown, filename,
     synthetic, license_name) = row
    source = Path(filename).resolve()
    if not _inside_roots(source, roots):
        raise ValueError("matched Parquet path is outside configured corpus roots")
    all_lines = markdown.splitlines()
    lines = [
        {"line": number, "text": all_lines[number - 1]}
        for number in range(start_line, min(end_line, len(all_lines)) + 1)
    ]
    result = {
        "ok": True,
        "found": True,
        "doi": stored_doi or normalized,
        "document_id": stored_uuid,
        "title": title,
        "publisher_group": publisher,
        "synthetic": bool(synthetic),
        "citable": _package_citable(roots, bool(synthetic)),
        "path": make_document_ref(source, stored_uuid),
        "lookup_engine": "compact-parquet",
        "start_line": start_line,
        "end_line": lines[-1]["line"] if lines else start_line - 1,
        "lines": lines,
    }
    if license_name:
        result["license"] = license_name
    return result


def read_document(
    reference: str,
    *,
    roots: list[Path],
    start_line: int,
    end_line: int,
) -> dict[str, Any]:
    path, uuid = parse_document_ref(reference)
    if not _inside_roots(path, roots):
        raise ValueError("path is outside GOAI_LOCAL_CORPUS_ROOTS")
    if not path.is_file():
        raise FileNotFoundError(path)
    row = _fetch_markdown(path, uuid)
    if row is None:
        raise FileNotFoundError(f"document {uuid} in {path}")
    _, doi, title, publisher, markdown, synthetic, license_name = row
    all_lines = markdown.splitlines()
    lines = [
        {"line": number, "text": all_lines[number - 1]}
        for number in range(start_line, min(end_line, len(all_lines)) + 1)
    ]
    result = {
        "ok": True,
        "path": reference,
        "document_id": uuid,
        "doi": doi,
        "title": title,
        "publisher_group": publisher,
        "synthetic": bool(synthetic),
        "citable": _package_citable(roots, bool(synthetic)),
        "start_line": start_line,
        "end_line": lines[-1]["line"] if lines else start_line - 1,
        "lines": lines,
    }
    if license_name:
        result["license"] = license_name
    return result


def normalize_doi(value: str) -> str:
    doi = value.strip().casefold()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    return doi.removeprefix("doi:").strip()


def lookup_doi(
    doi: str,
    *,
    roots: list[Path],
    files: list[Path],
    start_line: int,
    end_line: int,
) -> dict[str, Any]:
    """Resolve a DOI via a private index or a self-contained compact package."""
    normalized = normalize_doi(doi)
    uuid = hashlib.md5(normalized.encode("utf-8")).hexdigest()
    index_value = os.environ.get("GOAI_LOCAL_CORPUS_EXPECTED_INDEX", "").strip()
    shard_value = os.environ.get("GOAI_LOCAL_CORPUS_SHARD_ROOT", "").strip()
    if bool(index_value) != bool(shard_value):
        return {
            "ok": False,
            "doi": normalized,
            "error": (
                "GOAI_LOCAL_CORPUS_EXPECTED_INDEX and GOAI_LOCAL_CORPUS_SHARD_ROOT "
                "must be configured together"
            ),
        }
    if not index_value and not shard_value:
        manifest = load_manifest(roots)
        if manifest and manifest.get("ok") and manifest.get("corpus_format") == COMPACT_FORMAT:
            return _lookup_compact_doi(
                normalized,
                uuid=uuid,
                files=files,
                roots=roots,
                start_line=start_line,
                end_line=end_line,
            )
        # A private full corpus may be distributed as publisher-partitioned
        # Parquet without the optional DOI SQLite adapter.  The same exact DOI
        # predicate is still safe and correct; DuckDB prunes/streams the
        # configured files, while the optional index remains the fast path for
        # deployments that provide the expected_members schema.
        if files:
            result = _lookup_compact_doi(
                normalized,
                uuid=uuid,
                files=files,
                roots=roots,
                start_line=start_line,
                end_line=end_line,
            )
            if result.get("lookup_engine") == "compact-parquet":
                result["lookup_engine"] = "full-parquet-scan"
            return result
        return {
            "ok": False,
            "doi": normalized,
            "error": (
                "large/private corpus DOI lookup needs GOAI_LOCAL_CORPUS_EXPECTED_INDEX "
                "and GOAI_LOCAL_CORPUS_SHARD_ROOT; a compact public package instead needs "
                f"a corpus_manifest.json with corpus_format={COMPACT_FORMAT}"
            ),
        }
    index_path = Path(index_value).expanduser().resolve()
    shard_root = Path(shard_value).expanduser().resolve()
    if not index_path.is_file() or not shard_root.is_dir():
        return {"ok": False, "doi": normalized, "error": "configured DOI index/shard root is unavailable"}
    connection = sqlite3.connect(f"file:{index_path}?mode=ro&immutable=1", uri=True)
    try:
        try:
            hit = connection.execute(
                "SELECT archive_name FROM expected_members WHERE uuid=?", (uuid,)
            ).fetchone()
        except sqlite3.OperationalError as exc:
            # Older/private indexes may expose DOI rows under another schema.
            # Do not turn a recoverable lookup mismatch into an MCP crash: use
            # the authoritative Parquet DOI column and retain the reason in the
            # response for auditability.
            if not files:
                return {
                    "ok": False,
                    "doi": normalized,
                    "error": f"configured DOI index lacks expected_members: {exc}",
                }
            result = _lookup_compact_doi(
                normalized,
                uuid=uuid,
                files=files,
                roots=roots,
                start_line=start_line,
                end_line=end_line,
            )
            result["lookup_engine"] = "full-parquet-scan-index-fallback"
            result["index_fallback"] = f"expected_members unavailable: {exc}"
            return result
    finally:
        connection.close()
    if hit is None:
        return {"ok": True, "found": False, "doi": normalized, "document_id": uuid}
    parquet_path = (shard_root / f"{hit[0]}.parquet").resolve()
    if not parquet_path.is_file():
        return {"ok": False, "doi": normalized, "error": f"missing ingest shard: {parquet_path.name}"}
    # DOI lookup is explicitly configured separately from compact search roots.
    row = _fetch_markdown(parquet_path, uuid)
    if row is None:
        return {"ok": True, "found": False, "doi": normalized, "document_id": uuid}
    _, stored_doi, title, publisher, markdown, synthetic, license_name = row
    all_lines = markdown.splitlines()
    lines = [
        {"line": number, "text": all_lines[number - 1]}
        for number in range(start_line, min(end_line, len(all_lines)) + 1)
    ]
    result = {
        "ok": True,
        "found": True,
        "doi": stored_doi or normalized,
        "document_id": uuid,
        "title": title,
        "publisher_group": publisher,
        "synthetic": bool(synthetic),
        "citable": _package_citable(roots, bool(synthetic)),
        "source_archive": hit[0],
        "lookup_engine": "private-sqlite-shard-index",
        "start_line": start_line,
        "end_line": lines[-1]["line"] if lines else start_line - 1,
        "lines": lines,
    }
    if license_name:
        result["license"] = license_name
    return result


__all__ = [
    "available",
    "COMPACT_FORMAT",
    "discover_files",
    "inspect_schema",
    "load_manifest",
    "lookup_doi",
    "make_document_ref",
    "parse_document_ref",
    "read_document",
    "search",
]
