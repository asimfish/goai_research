"""Read-only full-text search over local Markdown or Parquet corpora.

The private deployment points ``GOAI_LOCAL_CORPUS_ROOTS`` at the large NAS
corpus.  A public release can point the same tool at a small, redistributable
subset without changing code or output schema.
"""
from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Iterable

from .audit import record_tool_call
from . import parquet_corpus


DEFAULT_GLOB = "*.md"
MAX_RESULTS = 100
MAX_CONTEXT_LINES = 10
MAX_READ_LINES = 500
DEFAULT_MATCH_TEXT_CHARS = 1200


def _clip_text(text: str, limit: int) -> tuple[str, bool]:
    """Bound MCP transport size while preserving whether evidence was clipped."""
    if len(text) <= limit:
        return text, False
    return text[:limit].rstrip() + " …[truncated]", True


def configured_roots(roots: Iterable[str | Path] | None = None) -> list[Path]:
    if roots is None:
        raw = os.environ.get("GOAI_LOCAL_CORPUS_ROOTS", "")
        values = [part for part in raw.split(os.pathsep) if part.strip()]
        if not values:
            public_root = Path(os.environ.get("GOAI_WORKSPACE", "workspace")) / "library" / "corpus"
            values = [str(public_root)] if public_root.exists() else []
    else:
        values = [str(value) for value in roots]

    resolved: list[Path] = []
    for value in values:
        path = Path(value).expanduser().resolve()
        if (path.is_dir() or (path.is_file() and path.suffix.casefold() == ".parquet")) \
                and path not in resolved:
            resolved.append(path)
    return resolved


def corpus_status(roots: Iterable[str | Path] | None = None) -> dict[str, Any]:
    paths = configured_roots(roots)
    parquet_files = parquet_corpus.discover_files(paths)
    engine = "duckdb-parquet" if parquet_files else "ripgrep"
    engine_ok = parquet_corpus.available() if parquet_files else shutil.which("rg") is not None
    manifest = parquet_corpus.load_manifest(paths) if paths else None
    schema = parquet_corpus.inspect_schema(parquet_files) if parquet_files and engine_ok else None
    explicit_roots = bool(os.environ.get("GOAI_LOCAL_CORPUS_ROOTS", "").strip())
    if manifest and manifest.get("ok") and manifest.get("corpus_format") == parquet_corpus.COMPACT_FORMAT:
        mode = "synthetic-demo-parquet" if manifest.get("synthetic") else "public-compact-parquet"
    elif explicit_roots:
        mode = "private-full-corpus"
    else:
        mode = "public-subset"
    manifest_ok = manifest is None or bool(manifest.get("ok"))
    ok = (bool(paths) and engine_ok and manifest_ok
          and (schema is None or bool(schema.get("ok"))))
    return {
        "ok": ok,
        "engine": engine,
        "rg_path": shutil.which("rg"),
        "parquet_files": len(parquet_files),
        "roots": [str(path) for path in paths],
        "mode": mode,
        "package": manifest,
        "schema": schema,
        "hint": None if paths else (
            "Set GOAI_LOCAL_CORPUS_ROOTS to an os.pathsep-separated list of corpus directories, "
            "or place a Markdown/compact-Parquet subset under $GOAI_WORKSPACE/library/corpus."
        ),
    }


def _context(path: Path, line_number: int, radius: int,
             text_limit: int) -> list[dict[str, Any]]:
    first = max(1, line_number - radius)
    last = line_number + radius
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            for number, text in enumerate(handle, 1):
                if number < first:
                    continue
                if number > last:
                    break
                clipped, truncated = _clip_text(text.rstrip("\r\n"), text_limit)
                row = {"line": number, "text": clipped}
                if truncated:
                    row["text_truncated"] = True
                rows.append(row)
    except OSError:
        return []
    return rows


def search_local_corpus(
    query: str,
    *,
    max_results: int = 20,
    context_lines: int = 1,
    case_sensitive: bool = False,
    regex: bool = False,
    file_glob: str = DEFAULT_GLOB,
    timeout_seconds: float | None = None,
    roots: Iterable[str | Path] | None = None,
) -> dict[str, Any]:
    """Search Parquet privately or stream ripgrep over a public Markdown subset."""
    started = time.monotonic()
    query = (query or "").strip()
    max_results = min(max(int(max_results), 1), MAX_RESULTS)
    context_lines = min(max(int(context_lines), 0), MAX_CONTEXT_LINES)
    timeout_seconds = float(
        timeout_seconds if timeout_seconds is not None
        else os.environ.get("GOAI_LOCAL_CORPUS_TIMEOUT", "30")
    )
    text_limit = max(200, int(os.environ.get(
        "GOAI_LOCAL_MATCH_TEXT_CHARS", str(DEFAULT_MATCH_TEXT_CHARS)
    )))
    paths = configured_roots(roots)
    parquet_files = parquet_corpus.discover_files(paths)
    request = {
        "query": query,
        "max_results": max_results,
        "context_lines": context_lines,
        "case_sensitive": case_sensitive,
        "regex": regex,
        "file_glob": file_glob,
        "roots": [str(path) for path in paths],
    }

    if not query:
        result = {"ok": False, "error": "query must not be empty", "matches": []}
    elif not paths:
        result = {"ok": False, "error": corpus_status(roots)["hint"], "matches": []}
    elif parquet_files:
        try:
            result = parquet_corpus.search(
                query,
                files=parquet_files,
                roots=paths,
                max_results=max_results,
                context_lines=context_lines,
                case_sensitive=case_sensitive,
                regex=regex,
                timeout_seconds=timeout_seconds,
                text_limit=text_limit,
            )
        except (RuntimeError, ValueError) as exc:
            result = {"ok": False, "error": f"{type(exc).__name__}: {exc}", "matches": []}
    elif shutil.which("rg") is None:
        result = {"ok": False, "error": "ripgrep (rg) is not installed", "matches": []}
    else:
        cmd_prefix = [
            "rg", "--json", "--line-buffered", "--line-number", "--no-messages",
            "--glob", file_glob,
        ]
        cmd_prefix.append("--case-sensitive" if case_sensitive else "--ignore-case")
        if not regex:
            cmd_prefix.append("--fixed-strings")
        cmd_prefix.extend(["--", query])

        # One rg process per root prevents a slow early year shard from hiding
        # fast matches in later shards.  This is especially important on the
        # NAS corpus, whose four year roots have very different traversal cost.
        processes: list[subprocess.Popen[str]] = []
        events_queue: queue.Queue[tuple[str, subprocess.Popen[str], str | None]] = queue.Queue(
            maxsize=10000
        )

        def pump_matches(proc: subprocess.Popen[str]) -> None:
            assert proc.stdout is not None
            try:
                for raw in proc.stdout:
                    # rg emits begin/end records for every file.  Discard them
                    # in the reader thread so a large corpus cannot fill RAM.
                    if '"type":"match"' in raw:
                        events_queue.put(("match", proc, raw))
            finally:
                events_queue.put(("eof", proc, None))

        readers: list[threading.Thread] = []
        for root in paths:
            proc = subprocess.Popen(
                [*cmd_prefix, str(root)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            processes.append(proc)
            reader = threading.Thread(target=pump_matches, args=(proc,), daemon=True)
            reader.start()
            readers.append(reader)
        matches: list[dict[str, Any]] = []
        deadline = started + max(timeout_seconds, 0.1)
        timed_out = False
        truncated = False

        def consume(raw: str) -> None:
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                return
            if event.get("type") != "match":
                return
            data = event["data"]
            path = Path(data["path"]["text"]).resolve()
            line_number = int(data.get("line_number") or 0)
            raw_text = data.get("lines", {}).get("text", "").rstrip("\r\n")
            clipped_text, text_truncated = _clip_text(raw_text, text_limit)
            match = {
                "path": str(path),
                "document_id": path.stem,
                "line": line_number,
                "text": clipped_text,
                "submatches": [
                    {"start": int(item["start"]), "end": int(item["end"])}
                    for item in data.get("submatches", [])
                ],
                "context": _context(path, line_number, context_lines, text_limit),
            }
            if text_truncated:
                match["text_truncated"] = True
            matches.append(match)

        try:
            finished = 0
            while finished < len(processes):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    for proc in processes:
                        if proc.poll() is None:
                            proc.terminate()
                    break
                try:
                    event_type, _proc, raw = events_queue.get(
                        timeout=min(0.25, remaining)
                    )
                except queue.Empty:
                    continue
                if event_type == "eof":
                    finished += 1
                    continue
                assert raw is not None
                consume(raw)
                if len(matches) >= max_results:
                    truncated = True
                    for proc in processes:
                        if proc.poll() is None:
                            proc.terminate()
                    break
        finally:
            for proc in processes:
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            for reader in readers:
                reader.join(timeout=0.2)
        stderr_parts = []
        for root, proc in zip(paths, processes):
            stderr = proc.stderr.read().strip() if proc.stderr is not None else ""
            if stderr:
                stderr_parts.append(f"{root}: {stderr}")
        return_codes = [proc.returncode for proc in processes]
        result = {
            "ok": bool(matches) or (
                not timed_out and all(code in {0, 1, -15} for code in return_codes)
            ),
            "query": query,
            "total_returned": len(matches),
            "truncated": truncated,
            "timed_out": timed_out,
            "timeout_seconds": timeout_seconds,
            "roots": [str(path) for path in paths],
            "matches": matches,
        }
        if stderr_parts:
            result["stderr"] = "\n".join(stderr_parts)[:1000]

    record_tool_call(
        "grep_local_corpus",
        request,
        result,
        duration_ms=(time.monotonic() - started) * 1000,
    )
    return result


def _allowed_path(path: str | Path, roots: Iterable[str | Path] | None = None) -> Path:
    candidate = Path(path).expanduser().resolve()
    allowed = configured_roots(roots)
    if not any(candidate.is_relative_to(root) for root in allowed):
        raise ValueError("path is outside GOAI_LOCAL_CORPUS_ROOTS")
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


def read_local_document(
    path: str,
    *,
    start_line: int = 1,
    end_line: int = 200,
    roots: Iterable[str | Path] | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    start_line = max(int(start_line), 1)
    end_line = max(int(end_line), start_line)
    if end_line - start_line + 1 > MAX_READ_LINES:
        end_line = start_line + MAX_READ_LINES - 1
    request = {"path": path, "start_line": start_line, "end_line": end_line}
    try:
        if path.startswith("parquet://"):
            result = parquet_corpus.read_document(
                path,
                roots=configured_roots(roots),
                start_line=start_line,
                end_line=end_line,
            )
        else:
            resolved = _allowed_path(path, roots)
            lines: list[dict[str, Any]] = []
            with resolved.open(encoding="utf-8", errors="replace") as handle:
                for number, text in enumerate(handle, 1):
                    if number < start_line:
                        continue
                    if number > end_line:
                        break
                    lines.append({"line": number, "text": text.rstrip("\r\n")})
            result = {
                "ok": True,
                "path": str(resolved),
                "document_id": resolved.stem,
                "start_line": start_line,
                "end_line": lines[-1]["line"] if lines else start_line - 1,
                "lines": lines,
            }
    except (OSError, RuntimeError, ValueError) as exc:
        result = {"ok": False, "error": f"{type(exc).__name__}: {exc}", "lines": []}
    record_tool_call(
        "read_local_document",
        request,
        result,
        duration_ms=(time.monotonic() - started) * 1000,
    )
    return result


def lookup_local_doi(
    doi: str,
    *,
    start_line: int = 1,
    end_line: int = 200,
    roots: Iterable[str | Path] | None = None,
) -> dict[str, Any]:
    """Read a DOI directly through the private corpus index and ingest shard."""
    started = time.monotonic()
    start_line = max(int(start_line), 1)
    end_line = max(int(end_line), start_line)
    if end_line - start_line + 1 > MAX_READ_LINES:
        end_line = start_line + MAX_READ_LINES - 1
    request = {"doi": doi, "start_line": start_line, "end_line": end_line}
    try:
        result = parquet_corpus.lookup_doi(
            doi,
            roots=configured_roots(roots),
            files=parquet_corpus.discover_files(configured_roots(roots)),
            start_line=start_line,
            end_line=end_line,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        result = {"ok": False, "error": f"{type(exc).__name__}: {exc}", "lines": []}
    record_tool_call(
        "lookup_local_doi",
        request,
        result,
        duration_ms=(time.monotonic() - started) * 1000,
    )
    return result


__all__ = [
    "configured_roots",
    "corpus_status",
    "search_local_corpus",
    "read_local_document",
    "lookup_local_doi",
]
