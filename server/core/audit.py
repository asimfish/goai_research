"""Append-only audit log for deterministic MCP tool calls.

The competition requires tool inputs, intermediate outputs, failures, and model
versions to remain traceable.  Tool logging must never make the actual tool
fail, so this module intentionally treats audit I/O as best effort.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def _audit_path() -> Path:
    explicit = os.environ.get("GOAI_TOOL_AUDIT_LOG")
    if explicit:
        return Path(explicit).expanduser()
    workspace = Path(os.environ.get("GOAI_WORKSPACE", "workspace"))
    return workspace / "state" / "tool_calls.jsonl"


def record_tool_call(
    tool: str,
    request: dict[str, Any],
    response: dict[str, Any],
    *,
    duration_ms: float,
) -> None:
    """Append one machine-readable tool event without leaking credentials."""
    if os.environ.get("GOAI_DISABLE_TOOL_AUDIT", "").lower() in {"1", "true", "yes"}:
        return
    event = {
        "event_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": os.environ.get("GOAI_RUN_ID"),
        "billing_task_id": os.environ.get("GOAI_BILLING_TASK_ID"),
        "session_id": os.environ.get("GOAI_SESSION_ID"),
        "tool": tool,
        "duration_ms": round(float(duration_ms), 3),
        "request": request,
        "response": response,
    }
    path = _audit_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            try:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            except (ImportError, OSError):
                pass
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            try:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except (ImportError, OSError):
                pass
        # If the tool itself called a model, account for that provider's usage.
        # Host model tokens for reading this tool's output are already in Codex's
        # turn receipt and must not be submitted again here.
        reports = response.get("billing_usage")
        if reports is None and response.get("usage") and response.get("model"):
            reports = [{"model": response["model"], "usage": response["usage"],
                        "event_id": response.get("id") or event["event_id"] + ":model",
                        "service_tier": response.get("service_tier")}]
        if reports:
            from .usage_sources import append_usage
            workspace = Path(os.environ.get("GOAI_WORKSPACE", "workspace"))
            for index, receipt in enumerate(reports if isinstance(reports, list) else [reports]):
                append_usage(workspace, {"event_id": event["event_id"] + f":model:{index}",
                    "session_id": os.environ.get("GOAI_SESSION_ID") or "tool-model:" + str(event["run_id"]),
                    "agent_task_id": event["run_id"], "timestamp": event["timestamp"],
                    "task_id": event["billing_task_id"],
                    "parent_tool_call_id": event["event_id"], **receipt})
    except (OSError, ValueError, TypeError, KeyError) as exc:
        # Audit storage can be read-only or temporarily unavailable.  The MCP
        # result remains useful and the caller's JSONL trajectory still records it.
        # Preserve a missing-metering marker if accounting validation failed;
        # swallowing it would incorrectly make a paid tool look free.
        if isinstance(response, dict) and (response.get("billing_usage") or response.get("usage")):
            try:
                issue_path = Path(os.environ.get("GOAI_WORKSPACE", "workspace")) / "state/billing_errors.jsonl"
                issue_path.parent.mkdir(parents=True, exist_ok=True)
                with issue_path.open("a", encoding="utf-8") as stream:
                    fcntl.flock(stream, fcntl.LOCK_EX)
                    stream.write(json.dumps({"event_id": event["event_id"] + ":metering-error",
                        "agent_task_id": event["run_id"], "timestamp": event["timestamp"],
                        "task_id": event["billing_task_id"],
                        "reason": "tool_usage_recording_failed", "error_type": type(exc).__name__}) + "\n")
            except (OSError, NameError):
                pass
        return


__all__ = ["record_tool_call"]
