#!/usr/bin/env python3
"""Export a finished GoAI run workspace into the competition submission bundle.

The runtime workspace (``workspace/``) is git-ignored because it holds private
full text and multi-megabyte agent traces.  For the competition the reviewers
must nevertheless be able to walk the chain

    code version -> configuration -> data -> run logs / agent traces -> result files

so this tool copies the *reviewable* subset of a run into
``submission/goai_final/`` with a fixed layout, redacts obvious secrets, and
writes machine-readable manifests (run inventory + SHA-256 of every file).

Layout written under ``--out``::

    report/      final PDF, LaTeX sources, BibTeX, figure sources (svg/drawio/figspec/png/pdf)
    evidence/    papers.jsonl, citation bank, condition source trace, citation audit, notes
    run/         inputs, task files, ledger, MCP tool-call log, review traces, ideas,
                 traces/runtime/parallel/<batch>/  (Codex CLI --json traces of every agent task)
                 traces/runtime/orchestrator/      (top-level orchestrator streams, may be truncated)
                 RUN_MANIFEST.json
    run_llzo/    same for the secondary LLZO case (traces + ledger + tool calls)
    traces/development/   development-phase agent trajectory (whalent gateway export, gzip JSONL)
    MANIFEST.sha256

Usage::

    .venv/bin/python tools/export_submission_bundle.py \
        --cold-workspace /path/to/goai_cold_full_byzso_m2gfJJ \
        --llzo-workspace /path/to/goai_research/workspace \
        --dev-trace-dir /tmp/conv85/detail \
        --out submission/goai_final
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

SECRET_PATTERNS = [
    re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9]{20,}\b"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{12,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)(\"?\s*[:=]\s*\"?)([A-Za-z0-9._-]{12,})"),
]
TEXT_SUFFIXES = {".jsonl", ".json", ".md", ".log", ".txt", ".tsv", ".toml", ".tex", ".bib", ".status", ".exit", ".started", ".process_exit"}


def scrub_text(text: str) -> tuple[str, int]:
    hits = 0
    for pat in SECRET_PATTERNS:
        def _sub(m: re.Match) -> str:
            nonlocal hits
            hits += 1
            if m.lastindex and m.lastindex >= 3:
                return f"{m.group(1)}{m.group(2)}[REDACTED]"
            return "[REDACTED]"
        text = pat.sub(_sub, text)
    return text, hits


def copy_tree(src: Path, dst: Path, *, redact: bool, log: list[str]) -> int:
    n = 0
    if not src.exists():
        log.append(f"missing source skipped: {src}")
        return 0
    for path in sorted(src.rglob("*")):
        if path.is_dir() or path.name.endswith(".lock") or path.name.startswith("."):
            continue
        rel = path.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if redact and path.suffix in TEXT_SUFFIXES:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                shutil.copy2(path, target)
                n += 1
                continue
            text, hits = scrub_text(text)
            if hits:
                log.append(f"redacted {hits} secret-like token(s) in {rel}")
            target.write_text(text, encoding="utf-8")
            shutil.copystat(path, target)
        else:
            shutil.copy2(path, target)
        n += 1
    return n


def copy_file(src: Path, dst: Path, log: list[str]) -> bool:
    if not src.exists():
        log.append(f"missing file skipped: {src}")
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def run_inventory(parallel_dir: Path) -> list[dict]:
    batches = []
    for batch in sorted(p for p in parallel_dir.iterdir() if p.is_dir()) if parallel_dir.exists() else []:
        tasks = []
        for jsonl in sorted(batch.glob("*.jsonl")):
            stem = jsonl.stem
            def _read(suffix: str) -> str | None:
                p = batch / f"{stem}{suffix}"
                return p.read_text(encoding="utf-8", errors="replace").strip() if p.exists() else None
            mcp_calls, agent_msgs, cmd = 0, 0, 0
            model = None
            usage = None
            for line in jsonl.open(encoding="utf-8", errors="replace"):
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                item = ev.get("item") or {}
                if ev.get("type") == "item.completed":
                    t = item.get("type")
                    if t == "mcp_tool_call":
                        mcp_calls += 1
                    elif t == "agent_message":
                        agent_msgs += 1
                    elif t == "command_execution":
                        cmd += 1
                if ev.get("type") == "turn.completed":
                    usage = ev.get("usage") or usage
                if ev.get("type") == "thread.started" and not model:
                    model = ev.get("model")
            tasks.append({
                "task": stem,
                "trace": str(jsonl.relative_to(parallel_dir.parent.parent)),
                "bytes": jsonl.stat().st_size,
                "status": _read(".status"),
                "exit": _read(".exit"),
                "process_exit": _read(".process_exit"),
                "started": _read(".started"),
                "mcp_tool_calls": mcp_calls,
                "command_executions": cmd,
                "agent_messages": agent_msgs,
                "usage": usage,
            })
        batches.append({"batch_id": batch.name, "tasks": tasks})
    return batches


def export_dev_trace(detail_dir: Path, out_dir: Path, log: list[str]) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(detail_dir.glob("*.json"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0)
    if not files:
        log.append(f"no development trace messages found in {detail_dir}")
        return {}
    composer = None
    counts: dict[str, int] = {}
    redactions = 0
    first_ts = last_ts = None
    out_path = out_dir / "whalent_codex_conversation.jsonl.gz"
    with gzip.open(out_path, "wt", encoding="utf-8") as sink:
        for f in files:
            payload = json.loads(f.read_text(encoding="utf-8"))
            msg = payload.get("message", payload)
            composer = composer or msg.get("composer_id")
            counts[msg.get("type", "?")] = counts.get(msg.get("type", "?"), 0) + 1
            ts = msg.get("created_at")
            if ts:
                first_ts = ts if first_ts is None else min(first_ts, ts)
                last_ts = ts if last_ts is None else max(last_ts, ts)
            line = json.dumps(msg, ensure_ascii=False)
            line, hits = scrub_text(line)
            redactions += hits
            sink.write(line + "\n")
    info = {
        "file": out_path.name,
        "conversation_id": composer,
        "messages": len(files),
        "message_types": counts,
        "first_message_ms": first_ts,
        "last_message_ms": last_ts,
        "redacted_tokens": redactions,
        "sha256": hashlib.sha256(out_path.read_bytes()).hexdigest(),
    }
    (out_dir / "trace_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return info


def export_codex_sessions(sessions_dir: Path, out: Path, log: list[str]) -> dict:
    """Copy native Codex CLI rollout files (``$CODEX_HOME/sessions``), scrubbed and gzipped.

    Rollouts whose ``session_meta.originator`` is the interactive harness (``whalent``)
    are the *development* trajectory; ``codex exec`` rollouts (``codex_cli_rs``) are
    runtime sub-agent sessions and are grouped by the working directory they ran in.
    """
    dev_dir = out / "traces" / "development"
    rt_dir = out / "traces" / "runtime_native_sessions"
    info = {"development": [], "runtime": []}
    for path in sorted(sessions_dir.rglob("rollout-*.jsonl")):
        with path.open(encoding="utf-8", errors="replace") as fh:
            first = fh.readline()
        try:
            meta = json.loads(first).get("payload", {})
        except json.JSONDecodeError:
            log.append(f"unreadable rollout skipped: {path.name}")
            continue
        originator = meta.get("originator", "")
        cwd = meta.get("cwd", "")
        text = path.read_text(encoding="utf-8", errors="replace")
        text, hits = scrub_text(text)
        model = effort = None
        turns = 0
        for line in text.splitlines():
            if '"turn_context"' in line:
                try:
                    p = json.loads(line).get("payload", {})
                except json.JSONDecodeError:
                    continue
                turns += 1
                model = model or p.get("model")
                effort = effort or p.get("effort")
        rec = {"file": path.name + ".gz", "session_id": meta.get("session_id"), "originator": originator,
               "cli_version": meta.get("cli_version"), "cwd": cwd, "started": meta.get("timestamp"),
               "model": model, "reasoning_effort": effort, "turns": turns, "bytes_raw": path.stat().st_size,
               "redacted_tokens": hits}
        if originator == "whalent":
            target_dir = dev_dir
            info["development"].append(rec)
        else:
            target_dir = rt_dir / (Path(cwd).name if cwd else "unknown_cwd")
            info["runtime"].append(rec)
        target_dir.mkdir(parents=True, exist_ok=True)
        with gzip.open(target_dir / (path.name + ".gz"), "wt", encoding="utf-8") as sink:
            sink.write(text)
    (out / "traces" / "codex_sessions_index.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    log.append(f"codex rollouts exported: {len(info['development'])} development, {len(info['runtime'])} runtime")
    return info


def write_sha_manifest(root: Path) -> int:
    lines = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            h = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{h}  {path.relative_to(root).as_posix()}")
    (root / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cold-workspace", required=True, help="repository clone that ran the formal cold-start case (contains workspace/, tasks_*.tsv, final PDF)")
    ap.add_argument("--final-pdf", default="Ba5Y12Zn_合成调研_学术润色版.pdf", help="final PDF filename inside --cold-workspace")
    ap.add_argument("--llzo-workspace", default=None, help="workspace/ of the LLZO diagnostic run (secondary case)")
    ap.add_argument("--dev-trace-dir", default=None, help="directory of exported gateway messages (<id>.json) for the development phase")
    ap.add_argument("--codex-sessions-dir", default=None, help="$CODEX_HOME/sessions directory holding native Codex rollout-*.jsonl files")
    ap.add_argument("--out", default="submission/goai_final")
    args = ap.parse_args()

    cold = Path(args.cold_workspace).resolve()
    ws = cold / "workspace"
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    log: list[str] = []

    # ---- report ---------------------------------------------------------------
    report = out / "report"
    copy_file(cold / args.final_pdf, report / args.final_pdf, log)
    for name in ("main.tex", "revision_log.md", "blueprint.md"):
        copy_file(ws / "drafts" / name, report / name, log)
    copy_tree(ws / "drafts" / "sections", report / "sections", redact=False, log=log)
    copy_file(ws / "library" / "references.bib", report / "references.bib", log)
    for sub in ("svg", "drawio", "figspec", "png", "pdf", "candidates"):
        copy_tree(ws / "figures" / sub, report / "figures" / sub, redact=False, log=log)
    copy_file(ws / "figures" / "build_fig03_headfigure.py", report / "figures" / "build_fig03_headfigure.py", log)

    # ---- evidence -------------------------------------------------------------
    evidence = out / "evidence"
    copy_file(ws / "library" / "papers.jsonl", evidence / "papers.jsonl", log)
    copy_file(ws / "library" / "references.bib", evidence / "references.bib", log)
    copy_tree(ws / "notes", evidence / "notes", redact=True, log=log)
    for name in ("CITATION_AUDIT.json", "CITATION_AUDIT.md", "ref_gate_resolution.md"):
        copy_file(ws / "state" / name, evidence / name, log)

    # ---- run (formal case) ----------------------------------------------------
    run = out / "run"
    copy_tree(ws / "inputs", run / "inputs", redact=False, log=log)
    for tsv in sorted(cold.glob("tasks_*.tsv")):
        copy_file(tsv, run / "tasks" / tsv.name, log)
    for name in ("ledger.json", "tool_calls.jsonl", "review_round1.md", "review_round2.md"):
        copy_file(ws / "state" / name, run / name, log)
    copy_tree(ws / "state" / "review_traces", run / "review_traces", redact=True, log=log)
    copy_tree(ws / "ideas", run / "ideas", redact=False, log=log)
    n_traces = copy_tree(ws / "state" / "parallel", run / "traces" / "runtime" / "parallel", redact=True, log=log)
    log.append(f"copied {n_traces} runtime trace files for the formal case")
    # top-level orchestrator streams captured by the gateway (may be truncated)
    orch_dir = run / "traces" / "runtime" / "orchestrator"
    orch_info = []
    if args.dev_trace_dir:
        for f in sorted(Path(args.dev_trace_dir).glob("*.json"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0):
            msg = json.loads(f.read_text(encoding="utf-8")).get("message", {})
            ti = msg.get("tool_input") or ""
            if "codex" in ti and "--json" in ti and cold.name in ti and "exec" in ti:
                out_txt = msg.get("tool_output") or ""
                if not out_txt:
                    continue
                m = re.search(r"-o\s+\S*/([\w.-]+)\.final\.md", ti)
                stem = m.group(1) if m else f"orchestrator_{msg.get('id')}"
                truncated = "[whalent truncated" in out_txt
                orch_dir.mkdir(parents=True, exist_ok=True)
                target = orch_dir / f"{stem}.{msg.get('id')}{'.partial' if truncated else ''}.jsonl"
                text, hits = scrub_text(out_txt)
                target.write_text(text, encoding="utf-8")
                orch_info.append({"file": target.name, "gateway_message_id": msg.get("id"), "truncated_by_gateway": truncated,
                                  "json_event_lines": sum(1 for l in text.splitlines() if l.startswith("{"))})
    logs_dir = cold.parent / "goai_cold_logs"
    profile = cold.name.removeprefix("goai_")  # codex profile name used for the cold run
    for final_md in sorted(logs_dir.glob(f"{profile}*.final.md")) if logs_dir.exists() else []:
        copy_file(final_md, orch_dir / final_md.name, log)

    run_manifest = {
        "formal_case": cold.name,
        "topic_input": (ws / "inputs" / "topic.md").read_text(encoding="utf-8") if (ws / "inputs" / "topic.md").exists() else None,
        "parallel_batches": run_inventory(ws / "state" / "parallel"),
        "orchestrator_streams": orch_info,
        "mcp_tool_calls": sum(1 for _ in (ws / "state" / "tool_calls.jsonl").open(encoding="utf-8")) if (ws / "state" / "tool_calls.jsonl").exists() else 0,
    }
    (run / "RUN_MANIFEST.json").write_text(json.dumps(run_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- secondary LLZO case -------------------------------------------------
    if args.llzo_workspace:
        lws = Path(args.llzo_workspace).resolve()
        llzo = out / "run_llzo"
        for name in ("ledger.json", "tool_calls.jsonl", "AGENT_TRACE_AUDIT.md", "AGENT_TRACE_AUDIT.json",
                     "CITATION_AUDIT.json", "CITATION_AUDIT.md", "review_diagnostic.md", "ref_guard_summary.md"):
            copy_file(lws / "state" / name, llzo / name, log)
        for tsv in sorted((lws / "state").glob("*.tsv")):
            copy_file(tsv, llzo / "tasks" / tsv.name, log)
        copy_tree(lws / "state" / "review_traces", llzo / "review_traces", redact=True, log=log)
        copy_tree(lws / "state" / "parallel", llzo / "traces" / "runtime" / "parallel", redact=True, log=log)
        copy_tree(lws / "ideas", llzo / "ideas", redact=False, log=log)
        copy_file(lws / "library" / "references.bib", llzo / "references.bib", log)
        (llzo / "RUN_MANIFEST.json").write_text(json.dumps({
            "case": "LLZO diagnostic run (2026-08-29)",
            "parallel_batches": run_inventory(lws / "state" / "parallel"),
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- development trace ----------------------------------------------------
    dev_info = {}
    if args.dev_trace_dir:
        dev_info = export_dev_trace(Path(args.dev_trace_dir), out / "traces" / "development", log)
    sessions_info = {}
    if args.codex_sessions_dir:
        sessions_info = export_codex_sessions(Path(args.codex_sessions_dir), out, log)

    n_files = write_sha_manifest(out)
    summary = {"out": str(out), "files": n_files, "dev_trace": dev_info,
               "codex_sessions": {k: len(v) for k, v in sessions_info.items()}, "log": log}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
