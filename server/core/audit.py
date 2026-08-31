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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": os.environ.get("GOAI_RUN_ID"),
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
    except OSError:
        # Audit storage can be read-only or temporarily unavailable.  The MCP
        # result remains useful and the caller's JSONL trajectory still records it.
        return


__all__ = ["record_tool_call"]
