#!/usr/bin/env python3
"""Summarize Codex ``--json`` traces and flag recurring integration failures."""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Any

KNOWN_TOOLS = (
    "search_papers", "snowball", "lookup", "download_pdf", "save_to_library", "export_bibtex",
    "coverage_report", "local_corpus_status", "grep_local_corpus", "read_local_document",
    "lookup_local_doi", "verify_entry", "verify_bib_file", "deep_audit_info", "validate_figspec",
    "render_figure", "svg_file_to_drawio", "drawio_export", "predict_precursor_routes",
    "predict_retro", "make_experiment_plan", "inorganic_model_status",
)


def analyze(path: Path) -> dict[str, Any]:
    event_counts: collections.Counter[str] = collections.Counter()
    mcp_tools: collections.Counter[str] = collections.Counter()
    # Tool functions of the four servers invoked through a shell/python command instead of
    # the MCP protocol (same code path, audited by server.core.audit.record_tool_call).
    cli_tools: collections.Counter[str] = collections.Counter()
    item_types: collections.Counter[str] = collections.Counter()
    failed_mcp: list[str] = []
    failed_commands: list[dict[str, Any]] = []
    non_json = 0
    max_event = 0
    max_command_output = 0
    usage: dict[str, int] = {}

    for line_no, line in enumerate(path.open(encoding="utf-8", errors="replace"), 1):
        max_event = max(max_event, len(line.encode("utf-8")))
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            non_json += 1
            continue
        event_type = str(event.get("type") or "unknown")
        event_counts[event_type] += 1
        item = event.get("item") or {}
        item_type = item.get("type")
        if event_type == "item.completed" and item_type:
            item_types[str(item_type)] += 1
        if event_type == "item.completed" and item_type == "command_execution":
            command = str(item.get("command") or "")
            for tool in KNOWN_TOOLS:
                if tool in command:
                    cli_tools[tool] += 1
        if event_type == "item.completed" and item_type == "mcp_tool_call":
            tool = str(item.get("tool") or "unknown")
            mcp_tools[tool] += 1
            if item.get("status") == "failed" or item.get("error"):
                failed_mcp.append(tool)
        if event_type == "item.completed" and item_type == "command_execution":
            output = str(item.get("aggregated_output") or item.get("output") or "")
            max_command_output = max(max_command_output, len(output.encode("utf-8")))
            if item.get("status") == "failed" or item.get("exit_code") not in (None, 0):
                failed_commands.append({
                    "line": line_no,
                    "exit_code": item.get("exit_code"),
                    "command": str(item.get("command") or "")[:240],
                })
        if event_type == "turn.completed":
            usage = event.get("usage") or usage

    stem = path.stem
    exit_path = path.with_suffix(".exit")
    final_path = path.with_suffix(".final.md")
    stderr_path = path.with_suffix(".stderr.log")
    exit_code = None
    if exit_path.exists():
        try:
            exit_code = int(exit_path.read_text().strip())
        except ValueError:
            exit_code = "invalid"
    flags = []
    input_tokens = int(usage.get("input_tokens") or 0)
    if non_json:
        flags.append("NON_JSON_LINES")
    if failed_mcp:
        flags.append("MCP_FAILURE")
    if failed_commands:
        flags.append("COMMAND_FAILURE")
    if max_event > 200_000:
        flags.append("OVERSIZED_EVENT")
    if input_tokens > 300_000:
        flags.append("HIGH_INPUT_TOKENS")
    if exit_code not in (None, 0):
        flags.append("NONZERO_EXIT")
    if not final_path.exists() or final_path.stat().st_size == 0:
        flags.append("MISSING_FINAL")

    return {
        "task": stem,
        "trace": str(path),
        "bytes": path.stat().st_size,
        "events": sum(event_counts.values()),
        "non_json_lines": non_json,
        "exit_code": exit_code,
        "final_bytes": final_path.stat().st_size if final_path.exists() else 0,
        "stderr_bytes": stderr_path.stat().st_size if stderr_path.exists() else 0,
        "mcp_calls": sum(mcp_tools.values()),
        "mcp_tools": dict(mcp_tools),
        "tool_calls_via_command": sum(cli_tools.values()),
        "tools_via_command": dict(cli_tools),
        "web_searches": item_types.get("web_search", 0),
        "item_types": dict(item_types),
        "failed_mcp": failed_mcp,
        "failed_commands": failed_commands,
        "max_event_bytes": max_event,
        "max_command_output_bytes": max_command_output,
        "usage": usage,
        "flags": flags,
    }


def markdown(rows: list[dict[str, Any]]) -> str:
    out = [
        "# Agent trace audit",
        "",
        "| Task | Exit | MCP | Tool fn via cmd | Web search | Failed commands | Input tokens | Max event | Flags |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        out.append(
            f"| `{row['task']}` | {row['exit_code']} | {row['mcp_calls']} | "
            f"{row['tool_calls_via_command']} | {row['web_searches']} | "
            f"{len(row['failed_commands'])} | {row['usage'].get('input_tokens', 0)} | "
            f"{row['max_event_bytes']} | {', '.join(row['flags']) or '—'} |"
        )
    totals = collections.Counter(flag for row in rows for flag in row["flags"])
    out.extend(["", "## Flag counts", ""])
    if totals:
        out.extend(f"- `{flag}`: {count}" for flag, count in sorted(totals.items()))
    else:
        out.append("- No flags.")
    out.extend([
        "",
        "Thresholds: oversized event >200 KB; high input >300k tokens. Command failures are",
        "reported even when the agent recovered and the overall turn exited successfully.",
    ])
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace_root", type=Path)
    parser.add_argument("--json", dest="json_path", type=Path)
    parser.add_argument("--md", dest="md_path", type=Path)
    args = parser.parse_args()

    paths = sorted(args.trace_root.glob("**/*.jsonl"))
    rows = [analyze(path) for path in paths]
    payload = {"trace_root": str(args.trace_root), "tasks": rows}
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    report = markdown(rows)
    if args.md_path:
        args.md_path.parent.mkdir(parents=True, exist_ok=True)
        args.md_path.write_text(report)
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
