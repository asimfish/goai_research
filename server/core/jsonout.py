"""MCP 工具统一的 JSON 输出。

默认 `indent=2` 便于人读；设 `GOAI_MCP_COMPACT_JSON=1` 后改为无缩进紧凑输出——
同一份 search_papers 结果可少约 20–30% 的 token（缩进与换行全部进模型上下文）。
"""
from __future__ import annotations

import json
import os
from typing import Any


def dumps(obj: Any) -> str:
    if os.environ.get("GOAI_MCP_COMPACT_JSON", "").lower() in {"1", "true", "yes"}:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(obj, ensure_ascii=False, indent=2)


__all__ = ["dumps"]
