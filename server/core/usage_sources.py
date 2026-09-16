"""Read-only trace import plus a durable, idempotent usage receipt endpoint.

Only accounting fields survive parsing; prompts, tool arguments, and responses
are never copied into the billing cache. File fingerprints avoid reparsing old
multi-megabyte traces on every console refresh.
"""
from __future__ import annotations

from contextlib import contextmanager
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading
from uuid import uuid4

from .usage_cost import PriceBook, DEFAULT_PRICES, digest, normalize_usage, summarize

PARSER_VERSION = 2


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def research_id(path: Path) -> str:
    return hashlib.sha1(str(path.absolute()).encode()).hexdigest()[:10]


def _iso(ns: int | None) -> str | None:
    return datetime.fromtimestamp(ns / 1e9, timezone.utc).isoformat() if ns else None


def _identifier(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 240 or any(ord(c) < 32 for c in value):
        raise ValueError("编号必须为 1–240 个非控制字符")
    return value


@contextmanager
def _lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def atomic_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def initialize_billing(workspace: Path, prices: Path = DEFAULT_PRICES, task_id: str | None = None) -> dict:
    """Called at launch. Never overwrite a research's chosen tariff snapshot."""
    workspace = Path(workspace).absolute()
    with _lock(workspace / "state/billing.lock"):
        path = workspace / "state/billing_context.json"
        context = read_json(path)
        if context is not None:
            return context
        book = PriceBook.load(prices)
        rid = research_id(workspace)
        context = {"schema": "goai-billing-context/1", "research_id": rid,
                   "task_id": _identifier(task_id or rid), "created_at": datetime.now(timezone.utc).isoformat(),
                   "price_revision": book.revision}
        atomic_json(workspace / "state/billing_prices.json", book.config)
        atomic_json(path, context)
        return context


def append_usage(workspace: Path, receipt: dict) -> dict:
    """One provider request (or explicit aggregate), identified by event_id.

    The same receipt can be retried safely. A changed receipt with the same ID
    is rejected. Raw usage counters are retained so prices remain auditable.
    """
    workspace = Path(workspace).absolute()
    if not isinstance(receipt, dict):
        raise ValueError("用量收据必须为 JSON 对象")
    for key in ("event_id", "model", "session_id"):
        _identifier(receipt.get(key))
    normalized = normalize_usage(receipt.get("usage"), receipt.get("format", "auto"))
    if receipt.get("usage_scope", "request") not in ("request", "turn", "session"):
        raise ValueError("usage_scope 必须为 request / turn / session")
    if receipt.get("request_input_tokens") is not None:
        from .usage_cost import tokens
        tokens(receipt["request_input_tokens"])
    allowed = ("event_id", "model", "session_id", "task_id", "agent_task_id", "usage", "format", "timestamp",
               "usage_scope", "service_tier", "request_input_tokens", "parent_tool_call_id", "usage_mode")
    value = {k: receipt[k] for k in allowed if k in receipt}
    if value.get("usage_mode", "delta") != "delta":
        raise ValueError("收据入口只接收单次增量用量；累计值请先转换为差值")
    for key in ("task_id", "agent_task_id", "parent_tool_call_id", "service_tier"):
        if value.get(key) is not None:
            _identifier(value[key])
    value.setdefault("usage_scope", "request")
    value.setdefault("format", "auto")
    if value.get("timestamp") is not None:
        if not isinstance(value["timestamp"], str):
            raise ValueError("用量时间必须为带时区的 ISO 字符串")
        instant = datetime.fromisoformat(value["timestamp"].replace("Z", "+00:00"))
        if instant.tzinfo is None:
            raise ValueError("用量时间必须带时区")
    path = workspace / "state/usage_events.jsonl"
    with _lock(workspace / "state/usage_events.lock"):
        if path.exists():
            with path.open() as stream:
                for line in stream:
                    old = json.loads(line)
                    if old["event_id"] == value["event_id"]:
                        if {k: v for k, v in old.items() if k != "recorded_at"} != value:
                            raise ValueError("同一 event_id 已有不同用量")
                        return {"recorded": False, "duplicate": True, "event_id": value["event_id"]}
        value["recorded_at"] = datetime.now(timezone.utc).isoformat()
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(value, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    return {"recorded": True, "duplicate": False, "event_id": value["event_id"], "tokens": normalized["tokens"]}


class BillingReader:
    def __init__(self, cache: Path, prices: Path = DEFAULT_PRICES):
        self.cache = Path(cache)
        self.prices = Path(prices)
        self.mutex = threading.RLock()
        self.cache.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.cache) as con:
            con.execute("CREATE TABLE IF NOT EXISTS traces (path TEXT PRIMARY KEY, fingerprint TEXT, payload TEXT)")

    def update_prices(self, config: dict, expected_revision: str) -> dict:
        book = PriceBook(config)
        with self.mutex, _lock(self.cache.with_suffix(".prices.lock")):
            current = PriceBook.load(self.prices)
            if current.revision != expected_revision:
                raise ValueError("价格表已被修改，请重新加载后再保存")
            snapshots = self.cache.parent / "price_history"
            atomic_json(snapshots / (current.revision + ".json"), current.config)
            atomic_json(self.prices, book.config)
        return {"config": book.config, "revision": book.revision}

    def _cached(self, path: Path, metadata: dict, parser):
        stat = path.stat()
        fingerprint = digest([PARSER_VERSION, stat.st_ino, stat.st_mtime_ns, stat.st_size, metadata])
        with self.mutex, sqlite3.connect(self.cache, timeout=30) as con:
            row = con.execute("SELECT fingerprint,payload FROM traces WHERE path=?", (str(path),)).fetchone()
            if row and row[0] == fingerprint:
                return json.loads(row[1])
            payload = parser(path, metadata)
            # A growing trace's final partial line is ignored and retried when its
            # size changes. Never cache prompt content or the original JSON text.
            con.execute("INSERT OR REPLACE INTO traces VALUES (?,?,?)", (str(path), fingerprint, json.dumps(payload)))
            return payload

    @staticmethod
    def _lines(path: Path):
        with path.open(encoding="utf-8") as stream:
            for index, line in enumerate(stream, 1):
                if not line.endswith("\n"):
                    break
                try:
                    value = json.loads(line)
                except ValueError:
                    yield index, {"type": "billing.invalid_line"}
                    continue
                if isinstance(value, dict):
                    yield index, value

    def _trace(self, path: Path, meta: dict) -> list[dict]:
        session = "unreported:" + digest(str(path))[:16]
        turn = 0
        records = []
        final_usage = False
        base = {**meta, "source": str(path), "warnings": []}
        for line, event in self._lines(path):
            etype = event.get("type")
            if etype == "thread.started":
                session = event.get("thread_id") or session
            elif etype == "turn.started":
                turn += 1
                final_usage = False
            elif etype in ("turn.completed", "response.completed", "usage.reported") and event.get("usage"):
                usage = event["usage"]
                event_id = event.get("event_id") or event.get("response_id") or f"codex:{session}:turn:{turn}:{digest(usage)[:16]}"
                record = {**base, "kind": "usage", "event_id": event_id, "session_id": session,
                          "usage": usage, "model": event.get("model") or meta.get("model"),
                          "timestamp": event.get("timestamp") or meta.get("timestamp"), "line": line,
                          "usage_scope": "turn" if etype == "turn.completed" else event.get("usage_scope", "request"),
                          "service_tier": event.get("service_tier") or meta.get("service_tier")}
                try:
                    normalize_usage(usage)
                except (ValueError, TypeError) as exc:
                    record.update(kind="missing", reason="invalid_usage: " + str(exc))
                records.append(record)
                final_usage = True
            elif etype == "item.completed":
                item = event.get("item") or {}
                if item.get("type") == "mcp_tool_call":
                    records.append({**base, "kind": "tool", "event_id": f"mcp:{session}:{item.get('id', line)}",
                        "session_id": session, "line": line, "server": item.get("server") or "unknown",
                        "tool": item.get("tool") or "unknown", "duration_ms": item.get("duration_ms"),
                        "failed": item.get("status") == "failed" or bool(item.get("error"))})
            elif etype == "billing.invalid_line":
                records.append({**base, "kind": "missing", "event_id": f"invalid:{session}:{line}",
                    "session_id": session, "reason": "invalid_trace_line", "line": line})
        if not final_usage:
            records.append({**base, "kind": "missing", "event_id": f"missing:{session}:turn:{turn}",
                "session_id": session, "reason": "usage_not_reported"})
        return records

    def _reported(self, path: Path, meta: dict) -> list[dict]:
        rows = []
        for line, event in self._lines(path):
            row = {**meta, **event, "kind": "usage", "source": str(path), "line": line,
                "research_id": meta["research_id"], "task_id": event.get("task_id") or meta["task_id"],
                "timestamp": event.get("timestamp"), "warnings": []}
            try:
                normalize_usage(event.get("usage"), event.get("format", "auto"))
                _identifier(event.get("event_id"))
                _identifier(event.get("session_id"))
                _identifier(event.get("model"))
            except ValueError:
                row.update(kind="missing", reason="invalid_usage_receipt", event_id="invalid-receipt:" + digest([str(path), line]),
                           session_id=event.get("session_id") or "unknown")
            rows.append(row)
        return rows

    def _audit(self, path: Path, meta: dict) -> list[dict]:
        rows = []
        for line, event in self._lines(path):
            if not event.get("tool"):
                continue
            ident = event.get("event_id") or "audit:" + digest(event)[:24]
            agent = event.get("run_id") or "unattributed"
            rows.append({**meta, "kind": "tool", "event_id": ident, "session_id": event.get("session_id") or "audit:" + agent,
                "task_id": event.get("billing_task_id") or meta["task_id"], "agent_task_id": agent,
                "source": str(path), "line": line, "server": event.get("server") or "goai-audit",
                "tool": event["tool"], "duration_ms": event.get("duration_ms"), "local_tool": True,
                "timestamp": event.get("timestamp"), "warnings": ["mcp_attribution_missing"] if agent == "unattributed" else []})
        return rows

    def workspace(self, workspace: Path) -> list[dict]:
        workspace = Path(workspace).absolute()
        context = read_json(workspace / "state/billing_context.json", {})
        rid = research_id(workspace)
        base = {"research_id": rid, "task_id": context.get("task_id") or rid}
        launcher = read_json(workspace / "launcher.json", {})
        traces = []
        for path in sorted((workspace / "state/orchestrator").glob("*.jsonl")):
            per_call = read_json(path.with_suffix(".billing.json"), {})
            traces.append((path, {**base, "agent_task_id": "orchestrator/" + path.stem,
                "model": per_call.get("model") or launcher.get("model"),
                "service_tier": per_call.get("service_tier"),
                "timestamp": per_call.get("started_at") or launcher.get("started_at")}))
        for path in sorted((workspace / "state/parallel").glob("*/*.jsonl")):
            info = read_json(path.parent / "RUN_INFO.json", {})
            traces.append((path, {**base, "agent_task_id": path.parent.name + "/" + path.stem,
                "task_id": info.get("billing_task_id") or base["task_id"],
                "model": info.get("model") or launcher.get("model"), "service_tier": info.get("service_tier"),
                "timestamp": info.get("started_at")}))
        for path in sorted((workspace / "model_runs").glob("*/events.jsonl")):
            info = read_json(path.parent / "invocation.json", {})
            traces.append((path, {**base, "agent_task_id": info.get("run_id") or path.parent.name,
                "task_id": info.get("billing_task_id") or base["task_id"],
                "model": info.get("model"), "service_tier": info.get("service_tier"), "timestamp": _iso(info.get("started_ns"))}))
        records = []
        for path, meta in traces:
            records.extend(self._cached(path, meta, self._trace))
        reported = workspace / "state/usage_events.jsonl"
        if reported.exists():
            records.extend(self._cached(reported, base, self._reported))
        errors = workspace / "state/billing_errors.jsonl"
        if errors.exists():
            for line, error in self._lines(errors):
                records.append({**base, **error, "kind": "missing", "session_id": "tool-model:" + str(error.get("agent_task_id")),
                    "task_id": error.get("task_id") or base["task_id"],
                    "source": str(errors), "line": line, "event_id": error.get("event_id") or "billing-error:" + str(line),
                    "reason": "tool_usage_recording_failed"})
        # Service audit and the client trace describe the same MCP invocation.
        # Prefer audited duration where both exist; do not add both populations.
        audit = workspace / "state/tool_calls.jsonl"
        if audit.exists():
            audits = self._cached(audit, base, self._audit)
            client_groups = {}
            for r in records:
                if r["kind"] == "tool":
                    client_groups.setdefault((r.get("agent_task_id"), r["tool"]), []).append(r)
            # Associate by ordered occurrence within a task/tool pair. Counts
            # differing between client and server remain visible as extra calls.
            used = Counter()
            for r in audits:
                key = (r["agent_task_id"], r["tool"])
                candidates = client_groups.get(key, [])
                index = used[key]
                if index < len(candidates):
                    candidates[index]["duration_ms"] = r.get("duration_ms")
                    candidates[index]["audit_source"] = r["source"]
                    candidates[index]["local_tool"] = True
                else:
                    records.append(r)
                used[key] += 1
        # Internal model calls and server-only audit rows belong to their host
        # Codex session when a task has exactly one observed thread. Never guess
        # between multiple resumed threads.
        sessions = {}
        for r in records:
            sid = r["session_id"]
            if r.get("agent_task_id") and not sid.startswith(("audit:", "tool-model:", "unreported:")):
                sessions.setdefault(r["agent_task_id"], set()).add(sid)
        for r in records:
            if r["session_id"].startswith(("audit:", "tool-model:")):
                candidates = sessions.get(r.get("agent_task_id"), set())
                if len(candidates) == 1:
                    r["session_id"] = next(iter(candidates))
        snapshot = workspace / "state/billing_prices.json"
        book = PriceBook.load(snapshot if snapshot.exists() else self.prices)
        for r in records:
            if not snapshot.exists():
                r["warnings"] = [*r.get("warnings", []), "current_tariff_for_historical_usage"]
        return [book.price(r) for r in records]

    def report(self, workspaces: list[Path], *, task_id: str | None = None, session_id: str | None = None,
               include_records: bool = False) -> dict:
        rows = []
        for workspace in workspaces:
            rows.extend(self.workspace(workspace))
        if task_id is not None:
            rows = [r for r in rows if r["task_id"] == task_id]
        if session_id is not None:
            rows = [r for r in rows if r["session_id"] == session_id]
        result = {"schema": "goai-cost-report/1", "generated_at": datetime.now(timezone.utc).isoformat(),
                  "price_config": str(self.prices), **summarize(rows)}
        if not include_records:
            result.pop("records")
        return result
