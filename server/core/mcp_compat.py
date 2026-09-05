"""MCP SDK 版本兼容 + 全工具统一审计。

兼容：2.x 的 MCPServer 与 1.x 的 FastMCP 接口一致（tool 装饰器 / run 默认 stdio），
只有类名与模块路径变了。

审计：四个 server 的每个 `@mcp.tool()` 都经本模块注册，因此在这里给工具函数套一层
`record_tool_call`，使 `state/tool_calls.jsonl` 覆盖全部工具，而不只是核心层自带审计的
4 个（grep_local_corpus / read_local_document / lookup_local_doi / predict_precursor_routes，
这 4 个在 server/core 内部记录，此处跳过避免重复）。无论工具是被 Codex 经 MCP 协议调用，
还是被子 agent 在 shell 里 `from server.xxx_server import tool` 直接调用，都会留下同一格式
的审计行；run_id 取自环境变量 GOAI_RUN_ID（parallel_run.sh 注入；MCP server 需在 codex
配置里声明 env_vars 透传），tools/live_view.py 据此把调用归到具体角色任务。
响应只记摘要（字节数 / ok / verdict / 条数 …），请求参数按 2000 字符截断，防止
figspec、BibTeX 全文等大参数把审计文件撑爆。
"""
from __future__ import annotations

import functools
import inspect
import json
import time

try:  # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as _BaseServer
except ModuleNotFoundError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as _BaseServer

from .audit import record_tool_call

# 这些工具在 server/core 内部已经调用 record_tool_call，包装层不再重复记录。
CORE_AUDITED_TOOLS = frozenset({
    "grep_local_corpus", "read_local_document", "lookup_local_doi",
    "predict_precursor_routes",
})
_REQUEST_STR_LIMIT = 2000
_SUMMARY_SCALAR_KEYS = ("ok", "verdict", "gate", "total", "found", "added", "before",
                        "entries", "library_size", "returncode", "error", "provider")
_SUMMARY_LIST_KEYS = ("papers", "references", "citations", "matches", "records",
                      "results", "subtopics", "gaps", "issues", "errors", "warnings",
                      "typo_errors", "typo_warnings", "routes", "steps", "figures")


def _bound_request(fn, args, kwargs) -> dict:
    try:
        bound = inspect.signature(fn).bind_partial(*args, **kwargs)
        bound.apply_defaults()
        request = dict(bound.arguments)
    except TypeError:
        request = {"args": [str(a) for a in args], **kwargs}
    out = {}
    for key, value in request.items():
        if isinstance(value, str) and len(value) > _REQUEST_STR_LIMIT:
            out[key] = value[:_REQUEST_STR_LIMIT] + f"…[truncated {len(value)} chars]"
        elif isinstance(value, (str, int, float, bool)) or value is None:
            out[key] = value
        else:
            out[key] = str(value)[:_REQUEST_STR_LIMIT]
    return out


def _summarize_response(result) -> dict:
    """工具函数统一返回 JSON 字符串；这里只保留判断性字段与规模，不存正文。"""
    if not isinstance(result, str):
        return {"type": type(result).__name__}
    summary: dict = {"bytes": len(result)}
    try:
        data = json.loads(result)
    except ValueError:
        summary["preview"] = result[:300]
        return summary
    if isinstance(data, dict):
        for key in _SUMMARY_SCALAR_KEYS:
            if key in data and isinstance(data[key], (str, int, float, bool, type(None))):
                summary[key] = data[key] if not isinstance(data[key], str) else data[key][:300]
        for key in _SUMMARY_LIST_KEYS:
            value = data.get(key)
            if isinstance(value, (list, dict)):
                summary[f"n_{key}"] = len(value)
    elif isinstance(data, list):
        summary["n_items"] = len(data)
    return summary


class FastMCP(_BaseServer):
    """与上游同名，额外给每个注册的工具套统一审计。"""

    def tool(self, *dargs, **dkwargs):  # type: ignore[override]
        register = super().tool(*dargs, **dkwargs)

        def decorator(fn):
            if fn.__name__ in CORE_AUDITED_TOOLS or inspect.iscoroutinefunction(fn):
                return register(fn)

            @functools.wraps(fn)
            def audited(*args, **kwargs):
                started = time.perf_counter()
                try:
                    result = fn(*args, **kwargs)
                except Exception as exc:  # 记录后原样抛出，不改变工具语义
                    record_tool_call(
                        fn.__name__, _bound_request(fn, args, kwargs),
                        {"ok": False, "exception": f"{type(exc).__name__}: {exc}"[:500]},
                        duration_ms=(time.perf_counter() - started) * 1000,
                    )
                    raise
                record_tool_call(
                    fn.__name__, _bound_request(fn, args, kwargs), _summarize_response(result),
                    duration_ms=(time.perf_counter() - started) * 1000,
                )
                return result

            return register(audited)

        return decorator


__all__ = ["FastMCP", "CORE_AUDITED_TOOLS"]
