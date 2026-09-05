#!/usr/bin/env python3
"""live_view.py —— 按角色实时查看 goai 多 agent 运行（只读，纯标准库）。

数据源（全部只读，与 parallel_run.sh / reproduce_core.sh 的落盘约定一致）：
  <ws>/state/parallel/<run_id>/<task>.jsonl          子 agent 的 Codex `exec --json` 事件流
  <ws>/state/parallel/<run_id>/<task>.{started,status,exit,process_exit,final.md,
                                       stderr.log,validation.log,prompt.txt,meta.json}
  <ws>/state/parallel/<run_id>/RUN_INFO.json         批次信息（新版 parallel_run.sh 写入）
  <ws>/state/orchestrator/*.jsonl                    编排器事件流（reproduce_core.sh 的 tee 输出）
  <ws>/state/ledger.json                             回环账本（阶段 / 闸门 / issue / 日志）
  <ws>/state/tool_calls.jsonl                        MCP 服务端审计（run_id 由 GOAI_RUN_ID 归因）

用法：
  python3 tools/live_view.py                    # 快照：当前批次每个角色的状态表 + 账本 + 最近 MCP 调用
  python3 tools/live_view.py --follow           # 终端实时流：每条事件带 [角色/任务] 前缀，Ctrl-C 结束并打印汇总
  python3 tools/live_view.py --serve 5051       # 浏览器看板 http://127.0.0.1:5051（每个角色一张卡，1s 刷新）
  python3 tools/live_view.py --run-id <id>      # 只看某一批（可重复；回放历史轨迹）
  python3 tools/live_view.py --all              # 所有批次（回放整场运行）
  GOAI_WORKSPACE=/path python3 tools/live_view.py --follow   # 指定工作区（或 --workspace）

默认只显示「活动集合」：仍有任务在跑的批次 + 最近一批 + 编排器流。
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import signal
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

# ----------------------------------------------------------------------------- 角色
# (icon, 中文名, ANSI 256 色)
ROLE_META = {
    "goai-orchestrator": ("🧭", "编排", "38;5;214"),
    "goai-lit-search": ("🔎", "文献检索", "38;5;75"),
    "goai-style-bank": ("🎨", "风格库", "38;5;141"),
    "goai-ref-guard": ("🛡", "引用核查", "38;5;203"),
    "goai-survey-writer": ("✍", "写作", "38;5;114"),
    "goai-figure-studio": ("🖼", "图纸", "38;5;180"),
    "goai-figure-editable": ("✎", "图纸可编辑化", "38;5;180"),
    "goai-idea-forge": ("💡", "想法生成", "38;5;220"),
    "goai-reviewer": ("⚖", "对抗审稿", "38;5;168"),
    "unknown": ("•", "未识别角色", "38;5;245"),
}
ROLE_ORDER = list(ROLE_META)
SKILL_RE = re.compile(r"goai-(orchestrator|lit-search|style-bank|ref-guard|survey-writer|"
                      r"figure-studio|figure-editable|idea-forge|reviewer)")
# 任务名前缀兜底（正式运行 40 个任务名全部可由此归类）
ROLE_NAME_RULES = [
    (re.compile(r"^(orch|orchestrator)", re.I), "goai-orchestrator"),
    (re.compile(r"^(lit|search|coverage|snowball|corpus|paper)", re.I), "goai-lit-search"),
    (re.compile(r"^(style)", re.I), "goai-style-bank"),
    (re.compile(r"^(ref|cit|bib|refresh_citation|dedup|ref_deduplicate)", re.I), "goai-ref-guard"),
    (re.compile(r"^(editable|drawio|svg2)", re.I), "goai-figure-editable"),
    (re.compile(r"^(fig|figure|roadmap|diagram|plot)", re.I), "goai-figure-studio"),
    (re.compile(r"^(idea|proposal|retro|route|precursor|experiment)", re.I), "goai-idea-forge"),
    (re.compile(r"^(review|audit|adjudicat|referee)", re.I), "goai-reviewer"),
    (re.compile(r"^(writ|taxonomy|assemble|blueprint|draft|text|section|define|repolish|"
                r"polish|bank|contribution|conclusion|intro)", re.I), "goai-survey-writer"),
]

STATUS_ICON = {
    "RUNNING": "▶", "PASS": "✅", "WARN": "⚠", "FAIL": "❌", "BLOCKED": "⛔",
    "DONE": "✅", "STALE": "…", "PENDING": "·",
}


def infer_role(name: str, *texts: str) -> str:
    for t in texts:
        if not t:
            continue
        m = SKILL_RE.search(t)
        if m:
            return "goai-" + m.group(1)
    for rx, role in ROLE_NAME_RULES:
        if rx.search(name):
            return role
    return "unknown"


# ----------------------------------------------------------------------------- 小工具
def clip(s, n: int) -> str:
    if s is None:
        return ""
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def one_line(s, n: int = 160) -> str:
    return clip(" ".join(str(s or "").split()), n)


def fmt_dur(sec) -> str:
    if sec is None:
        return "—"
    sec = int(max(0, sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h{m:02d}m" if h else (f"{m}m{s:02d}s" if m else f"{s}s")


def fmt_tokens(n) -> str:
    if not n:
        return "0"
    n = float(n)
    for unit, div in (("M", 1e6), ("k", 1e3)):
        if n >= div:
            return f"{n / div:.1f}{unit}"
    return str(int(n))


def read_text(path: str, tail: int | None = None) -> str:
    try:
        with open(path, "rb") as f:
            if tail:
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - tail))
                data = f.read()
                if size > tail:
                    data = data.split(b"\n", 1)[-1]
            else:
                data = f.read()
        return data.decode("utf-8", "replace")
    except OSError:
        return ""


def mtime(path: str):
    try:
        return os.path.getmtime(path)
    except OSError:
        return None


def hhmmss(ts) -> str:
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts else "        "


def dwidth(s: str) -> int:
    """终端显示宽度（CJK 全角算 2）。"""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in s)


def pad(s, width: int, right: bool = False) -> str:
    s = str(s)
    while dwidth(s) > width:
        s = s[:-1]
    fill = " " * (width - dwidth(s))
    return fill + s if right else s + fill


class Tail:
    """增量读取一个持续追加的文本文件；半行缓存，文件被截断则从头重读。"""

    def __init__(self, path: str):
        self.path = path
        self.pos = 0
        self.buf = b""

    def read_new(self) -> list[str]:
        try:
            size = os.path.getsize(self.path)
        except OSError:
            return []
        if size < self.pos:
            self.pos, self.buf = 0, b""
        if size == self.pos:
            return []
        with open(self.path, "rb") as f:
            f.seek(self.pos)
            data = f.read(size - self.pos)
            self.pos = size
        parts = (self.buf + data).split(b"\n")
        self.buf = parts.pop()
        return [p.decode("utf-8", "replace") for p in parts if p.strip()]


# ----------------------------------------------------------------------------- 事件归一化
def normalize(line: str) -> dict:
    """把 Codex `exec --json` 的一行转成扁平事件；无法解析的行原样保留。"""
    try:
        ev = json.loads(line)
    except ValueError:
        return {"kind": "raw", "text": clip(line, 2000)}
    if not isinstance(ev, dict):
        return {"kind": "raw", "text": clip(line, 2000)}
    t = str(ev.get("type", ""))
    if t == "thread.started":
        return {"kind": "thread", "text": ev.get("thread_id", "")}
    if t == "turn.started":
        return {"kind": "turn_start"}
    if t == "turn.completed":
        return {"kind": "usage", "usage": ev.get("usage") or {}}
    if t == "turn.failed":
        err = ev.get("error") or {}
        return {"kind": "error", "text": err.get("message") if isinstance(err, dict) else str(err)}
    if t == "error":
        return {"kind": "error", "text": ev.get("message") or json.dumps(ev, ensure_ascii=False)}
    if t == "unparsed_raw":
        return {"kind": "raw", "text": clip(ev.get("raw", ""), 2000)}
    if t.startswith("item."):
        phase = t.split(".", 1)[1]
        it = ev.get("item") or {}
        k = it.get("type")
        base = {"phase": phase, "item_id": it.get("id"), "status": it.get("status")}
        if k == "agent_message":
            return {**base, "kind": "message", "text": it.get("text", "")}
        if k == "reasoning":
            return {**base, "kind": "reasoning", "text": it.get("text", "")}
        if k == "command_execution":
            return {**base, "kind": "command", "command": it.get("command", ""),
                    "output": clip(it.get("aggregated_output", ""), 4000),
                    "exit_code": it.get("exit_code")}
        if k == "file_change":
            return {**base, "kind": "file_change", "changes": it.get("changes") or []}
        if k == "mcp_tool_call":
            err = it.get("error")
            result = it.get("result")
            return {**base, "kind": "mcp", "server": it.get("server"), "tool": it.get("tool"),
                    "arguments": clip(json.dumps(it.get("arguments"), ensure_ascii=False), 1200),
                    "result": clip(json.dumps(result, ensure_ascii=False), 2000) if result is not None else None,
                    "error": err.get("message") if isinstance(err, dict) else err}
        if k == "web_search":
            return {**base, "kind": "web_search", "query": it.get("query", "")}
        if k == "todo_list":
            return {**base, "kind": "todo", "items": it.get("items") or []}
        if k == "error":
            return {**base, "kind": "error", "text": it.get("message", "")}
        return {**base, "kind": "other", "text": clip(json.dumps(it, ensure_ascii=False), 1000)}
    return {"kind": "other", "text": clip(json.dumps(ev, ensure_ascii=False), 1000)}


# ----------------------------------------------------------------------------- 任务
class Task:
    """一个角色实例 = 一个 Codex 进程的事件流 + runner 落盘的状态文件。"""

    def __init__(self, run_id: str, name: str, jsonl_path: str, kind: str = "parallel"):
        self.run_id = run_id
        self.name = name
        self.kind = kind  # parallel | orchestrator
        self.dir = os.path.dirname(jsonl_path)
        self.jsonl = jsonl_path
        self.tail = Tail(jsonl_path)
        self.items: "collections.OrderedDict[str, dict]" = collections.OrderedDict()
        self.max_items = 4000
        self._synthetic = 0
        self.status = "PENDING"
        self.exit = None
        self.process_exit = None
        self.started = mtime(self._f("started")) or mtime(jsonl_path)
        self.ended = None
        self.usage = {}
        self.counts = collections.Counter()
        self.last_message = ""
        self.current_command = None
        self.todo = []
        self.thread_id = ""
        self.meta = self._load_json(self._f("meta.json"))
        self.prompt = read_text(self._f("prompt.txt")) if os.path.exists(self._f("prompt.txt")) else ""
        self.role = infer_role(name, self.meta.get("skill", ""), self.prompt[:4000])
        self.turn_done = False
        self.first_seen = time.time()

    # -- 文件约定 ---------------------------------------------------------------
    def _f(self, suffix: str) -> str:
        return os.path.join(self.dir, f"{self.name}.{suffix}")

    @staticmethod
    def _load_json(path: str) -> dict:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    @property
    def key(self) -> str:
        return f"{self.run_id}/{self.name}"

    # -- 状态刷新 ---------------------------------------------------------------
    def refresh_status(self) -> None:
        if self.kind == "orchestrator":
            if self.turn_done or os.path.exists(self._f("final.md")):
                self.status, self.ended = "DONE", self.ended or mtime(self._f("final.md")) or mtime(self.jsonl)
            else:
                idle = time.time() - (mtime(self.jsonl) or time.time())
                self.status = "RUNNING" if idle < 600 else "STALE"
            return
        exit_file = self._f("exit")
        if os.path.exists(exit_file):
            self.exit = read_text(exit_file).strip()
            self.process_exit = read_text(self._f("process_exit")).strip() or None
            status = read_text(self._f("status")).strip()
            if not status:
                status = "PASS" if self.exit == "0" else "FAIL"
            self.status = status
            self.ended = mtime(exit_file)
        elif os.path.exists(self._f("started")) or os.path.exists(self.jsonl):
            self.status = "RUNNING"
            self.started = self.started or mtime(self._f("started")) or mtime(self.jsonl)
        if not self.prompt and os.path.exists(self._f("prompt.txt")):
            self.prompt = read_text(self._f("prompt.txt"))
            self.role = infer_role(self.name, self.meta.get("skill", ""), self.prompt[:4000])

    @property
    def status_group(self) -> str:
        s = self.status
        if s.startswith("WARN"):
            return "WARN"
        if s.startswith("FAIL"):
            return "FAIL"
        if s.startswith("BLOCKED"):
            return "BLOCKED"
        return s

    def elapsed(self):
        if not self.started:
            return None
        return (self.ended or time.time()) - self.started

    def last_activity(self):
        return mtime(self.jsonl)

    # -- 事件吸收 ---------------------------------------------------------------
    def pump(self) -> list[dict]:
        """读新行，更新状态，返回本轮新事件（供 follow / feed 用）。"""
        new = []
        for line in self.tail.read_new():
            ev = normalize(line)
            ev["ts"] = time.time()
            self._absorb(ev)
            new.append(ev)
        return new

    def _absorb(self, ev: dict) -> None:
        kind = ev["kind"]
        item_id = ev.get("item_id")
        if not item_id:
            self._synthetic += 1
            item_id = f"_ev{self._synthetic}"
            ev["item_id"] = item_id
        phase = ev.get("phase")
        if item_id in self.items:
            self.items[item_id].update(ev)
            self.items.move_to_end(item_id)
        else:
            self.items[item_id] = dict(ev)
            if phase in (None, "started", "completed") and kind not in ("turn_start",):
                self.counts[kind] += 1
        while len(self.items) > self.max_items:
            self.items.popitem(last=False)
        if kind == "message" and ev.get("text"):
            self.last_message = ev["text"]
        elif kind == "reasoning" and ev.get("text") and not self.last_message:
            self.last_message = ev["text"]
        elif kind == "command":
            self.current_command = ev.get("command") if phase == "started" else None
        elif kind == "usage":
            self.usage = ev.get("usage") or {}
            self.turn_done = True
        elif kind == "todo":
            self.todo = ev.get("items") or []
        elif kind == "thread":
            self.thread_id = ev.get("text", "")
        if self.role == "unknown" and kind in ("message", "reasoning"):
            self.role = infer_role(self.name, ev.get("text", ""))

    # -- 序列化 -----------------------------------------------------------------
    def summary(self) -> dict:
        u = self.usage or {}
        return {
            "key": self.key, "run_id": self.run_id, "name": self.name, "kind": self.kind,
            "role": self.role, "status": self.status, "status_group": self.status_group,
            "exit": self.exit, "process_exit": self.process_exit,
            "started": self.started, "ended": self.ended, "elapsed": self.elapsed(),
            "last_activity": self.last_activity(),
            "tokens_in": u.get("input_tokens"), "tokens_cached": u.get("cached_input_tokens"),
            "tokens_out": u.get("output_tokens"), "tokens_reasoning": u.get("reasoning_output_tokens"),
            "counts": dict(self.counts), "last_message": clip(self.last_message, 700),
            "current_command": clip(self.current_command, 300) if self.current_command else None,
            "todo": self.todo[:12], "thread_id": self.thread_id,
            "expected": self.meta.get("expected") or [], "dependencies": self.meta.get("dependencies") or [],
            "validation": one_line(read_text(self._f("validation.log")), 300) if os.path.exists(self._f("validation.log")) else "",
            "final": clip(read_text(self._f("final.md"), tail=6000), 6000) if os.path.exists(self._f("final.md")) else "",
            "stderr": clip(read_text(self._f("stderr.log"), tail=1500), 1500) if os.path.exists(self._f("stderr.log")) else "",
            "prompt": clip(self.prompt, 1200),
            "items_total": len(self.items),
        }

    def recent_items(self, n: int = 40) -> list[dict]:
        items = list(self.items.values())
        return [_public_item(it) for it in items[-n:]]

    def all_items(self) -> list[dict]:
        return [_public_item(it) for it in self.items.values()]


def _public_item(it: dict) -> dict:
    out = dict(it)
    out.pop("phase", None)
    return out


# ----------------------------------------------------------------------------- 账本 / 审计
class LedgerWatch:
    def __init__(self, path: str):
        self.path = path
        self._mtime = None
        self.data = {}
        self._log_seen = 0
        self._gates = {}

    def poll(self) -> list[dict]:
        """返回本轮账本变化事件（阶段/闸门/issue/log 增量）。"""
        m = mtime(self.path)
        if m is None or m == self._mtime:
            return []
        self._mtime = m
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return []
        events = []
        old_stage = self.data.get("stage")
        if data.get("stage") != old_stage and old_stage is not None:
            events.append({"kind": "ledger", "text": f"stage {old_stage} → {data.get('stage')} (round {data.get('round')})"})
        gates = data.get("gates") or {}
        for name, g in gates.items():
            st = (g or {}).get("status")
            if self._gates.get(name) != st and self._gates:
                events.append({"kind": "ledger", "text": f"gate {name}: {self._gates.get(name, 'PENDING')} → {st}  {one_line((g or {}).get('detail'), 140)}"})
        self._gates = {k: (v or {}).get("status") for k, v in gates.items()}
        log = data.get("log") or []
        if self.data:
            for entry in log[self._log_seen:]:
                events.append({"kind": "ledger", "text": "log " + one_line(json.dumps(entry, ensure_ascii=False), 200)})
        self._log_seen = len(log)
        self.data = data
        return events

    def summary(self) -> dict:
        d = self.data
        if not d:
            return {}
        issues = d.get("issues") or []
        open_issues = [i for i in issues if (i.get("status") or "open") == "open"]
        sev = collections.Counter(i.get("severity") for i in open_issues)
        return {
            "topic": d.get("topic"), "stage": d.get("stage"), "round": d.get("round"),
            "max_rounds": d.get("max_rounds"), "effort": d.get("effort"), "strictness": d.get("strictness"),
            "gates": {k: {"status": (v or {}).get("status"), "detail": one_line((v or {}).get("detail"), 220),
                          "round": (v or {}).get("round")} for k, v in (d.get("gates") or {}).items()},
            "open_issues": [{"id": i.get("id"), "severity": i.get("severity"), "target": i.get("target"),
                             "from": i.get("from"), "text": one_line(i.get("text"), 220)} for i in open_issues],
            "issue_counts": dict(sev), "issues_total": len(issues),
            "log_tail": [one_line(json.dumps(e, ensure_ascii=False), 220) for e in (d.get("log") or [])[-12:]],
            "updated": self._mtime,
        }


class AuditWatch:
    def __init__(self, path: str):
        self.path = path
        self.tail = Tail(path)
        self.records: collections.deque = collections.deque(maxlen=400)
        self.total = 0
        self.by_tool = collections.Counter()
        self.by_run = collections.Counter()

    def poll(self) -> list[dict]:
        events = []
        for line in self.tail.read_new():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue
            self.total += 1
            tool = rec.get("tool")
            self.by_tool[tool] += 1
            self.by_run[rec.get("run_id") or "(未归因)"] += 1
            resp = rec.get("response") or {}
            ok = resp.get("ok") if isinstance(resp, dict) else None
            row = {"ts": rec.get("timestamp"), "tool": tool, "duration_ms": rec.get("duration_ms"),
                   "run_id": rec.get("run_id"), "ok": ok,
                   "request": one_line(json.dumps(rec.get("request"), ensure_ascii=False), 200)}
            self.records.append(row)
            events.append({"kind": "audit", **row})
        return events

    def summary(self) -> dict:
        return {"total": self.total, "by_tool": dict(self.by_tool.most_common()),
                "by_run": dict(self.by_run.most_common(30)), "recent": list(self.records)[-40:]}


# ----------------------------------------------------------------------------- 监控器
class Monitor:
    def __init__(self, workspace: str, run_ids=(), show_all=False, orch_logs=(), feed_max=6000):
        self.ws = os.path.abspath(workspace)
        self.parallel_dir = os.path.join(self.ws, "state", "parallel")
        self.orch_dir = os.path.join(self.ws, "state", "orchestrator")
        self.run_ids = set(run_ids or ())
        self.show_all = show_all
        self.extra_orch = list(orch_logs)
        self.tasks: dict[str, Task] = {}
        self.run_info: dict[str, dict] = {}
        self.ledger = LedgerWatch(os.path.join(self.ws, "state", "ledger.json"))
        self.audit = AuditWatch(os.path.join(self.ws, "state", "tool_calls.jsonl"))
        self.feed: collections.deque = collections.deque(maxlen=feed_max)
        self.seq = 0
        self.lock = threading.Lock()
        self.started_at = time.time()

    # -- 发现 -----------------------------------------------------------------
    def _discover(self) -> None:
        if os.path.isdir(self.parallel_dir):
            for run_id in sorted(os.listdir(self.parallel_dir)):
                rdir = os.path.join(self.parallel_dir, run_id)
                if not os.path.isdir(rdir):
                    continue
                if self.run_ids and run_id not in self.run_ids:
                    continue
                info_path = os.path.join(rdir, "RUN_INFO.json")
                if run_id not in self.run_info and os.path.exists(info_path):
                    self.run_info[run_id] = Task._load_json(info_path)
                for fn in os.listdir(rdir):
                    name = None
                    for suf in (".jsonl", ".started", ".exit"):
                        if fn.endswith(suf):
                            name = fn[: -len(suf)]
                            break
                    if not name or name.endswith(".stderr") or name.endswith(".final"):
                        continue
                    key = f"{run_id}/{name}"
                    if key not in self.tasks:
                        self.tasks[key] = Task(run_id, name, os.path.join(rdir, name + ".jsonl"))
        orch_files = []
        if os.path.isdir(self.orch_dir):
            orch_files += [os.path.join(self.orch_dir, f) for f in sorted(os.listdir(self.orch_dir)) if f.endswith(".jsonl")]
        orch_files += [p for p in self.extra_orch if os.path.exists(p)]
        for path in orch_files:
            name = os.path.basename(path)[:-6]
            key = f"orchestrator/{name}"
            if key not in self.tasks:
                t = Task("orchestrator", name, path, kind="orchestrator")
                t.role = "goai-orchestrator"
                self.tasks[key] = t

    def _active_runs(self) -> set[str]:
        """默认展示集合：有任务在跑的批次 + 最近修改的一批。"""
        runs = {t.run_id for t in self.tasks.values() if t.status == "RUNNING" and t.kind == "parallel"}
        latest, latest_m = None, -1
        for t in self.tasks.values():
            if t.kind != "parallel":
                continue
            m = max(t.last_activity() or 0, t.ended or 0, t.started or 0)
            if m > latest_m:
                latest, latest_m = t.run_id, m
        if latest:
            runs.add(latest)
        return runs

    def visible_tasks(self, runs=None, show_all=None) -> list[Task]:
        show_all = self.show_all if show_all is None else show_all
        runs = set(runs) if runs else None
        if runs:
            tasks = [t for t in self.tasks.values() if t.kind == "orchestrator" or t.run_id in runs]
        elif show_all or self.run_ids:
            tasks = list(self.tasks.values())
        else:
            active = self._active_runs()
            tasks = [t for t in self.tasks.values() if t.kind == "orchestrator" or t.run_id in active]
        return sorted(tasks, key=lambda t: (t.kind != "orchestrator", t.run_id, t.started or 0, t.name))

    # -- 轮询 -----------------------------------------------------------------
    def poll(self) -> list[tuple]:
        """扫一遍所有数据源；返回 [(seq, task_or_None, event), ...]。"""
        out = []
        with self.lock:
            self._discover()
            for t in list(self.tasks.values()):
                before = t.status
                t.refresh_status()
                for ev in t.pump():
                    out.append(self._push(t, ev))
                t.refresh_status()
                if before != t.status and before != "PENDING":
                    out.append(self._push(t, {"kind": "status", "text": t.status, "ts": time.time()}))
                elif before == "PENDING" and t.status != "PENDING":
                    out.append(self._push(t, {"kind": "status", "text": "started" if t.status == "RUNNING" else t.status, "ts": time.time()}))
            for ev in self.ledger.poll():
                ev["ts"] = time.time()
                out.append(self._push(None, ev))
            for ev in self.audit.poll():
                ev["ts"] = time.time()
                out.append(self._push(None, ev))
        return out

    def _push(self, task, ev: dict) -> tuple:
        self.seq += 1
        row = (self.seq, task, ev)
        self.feed.append(row)
        return row

    # -- 序列化 ---------------------------------------------------------------
    def state(self, recent: int = 30, runs=None, show_all=None) -> dict:
        with self.lock:
            tasks = self.visible_tasks(runs=runs, show_all=show_all)
            groups = collections.Counter(t.status_group for t in tasks if t.kind == "parallel")
            return {
                "workspace": self.ws, "now": time.time(), "seq": self.seq,
                "runs": sorted({t.run_id for t in tasks if t.kind == "parallel"}),
                "run_info": {r: self.run_info.get(r, {}) for r in {t.run_id for t in tasks}},
                "counts": dict(groups), "roles": ROLE_ORDER,
                "role_meta": {k: {"icon": v[0], "label": v[1]} for k, v in ROLE_META.items()},
                "tasks": [{**t.summary(), "audit_calls": self.audit.by_run.get(t.key, 0),
                           "recent": t.recent_items(recent)} for t in tasks],
                "ledger": self.ledger.summary(), "audit": self.audit.summary(),
                "all_runs": sorted({t.run_id for t in self.tasks.values() if t.kind == "parallel"}),
            }

    def feed_since(self, after: int, limit: int = 500) -> list[dict]:
        with self.lock:
            rows = [r for r in self.feed if r[0] > after][:limit]
        return [{"seq": s, "task": t.key if t else None, "role": t.role if t else None,
                 "name": t.name if t else None, **ev} for s, t, ev in rows]

    def task_detail(self, key: str) -> dict | None:
        with self.lock:
            t = self.tasks.get(key)
            if not t:
                return None
            return {**t.summary(), "items": t.all_items(), "prompt_full": t.prompt}


# ----------------------------------------------------------------------------- 终端渲染
def _color(role: str, text: str, tty: bool) -> str:
    if not tty:
        return text
    return f"\033[{ROLE_META.get(role, ROLE_META['unknown'])[2]}m{text}\033[0m"


def role_label(role: str, short=False) -> str:
    icon, label, _ = ROLE_META.get(role, ROLE_META["unknown"])
    return icon if short else f"{icon} {label}"


def fmt_event(task, ev: dict, tty: bool) -> str | None:
    kind = ev["kind"]
    ts = hhmmss(ev.get("ts"))
    if task is None:
        if kind == "ledger":
            return f"{ts} 📒 账本        {ev['text']}"
        if kind == "audit":
            ok = "" if ev.get("ok") is None else (" ok" if ev["ok"] else " FAIL")
            run = f" ← {ev['run_id']}" if ev.get("run_id") else ""
            return f"{ts} 🔧 MCP审计     {ev['tool']} {fmt_dur((ev.get('duration_ms') or 0) / 1000)}{ok}{run}  {ev.get('request', '')}"
        return None
    head = _color(task.role, f"{role_label(task.role, short=True)} {task.name[:26]:<26}", tty)
    phase = ev.get("phase")
    if kind == "status":
        s = ev["text"]
        extra = ""
        if s not in ("started", "RUNNING"):
            u = task.usage or {}
            extra = f"  exit={task.exit} · {fmt_dur(task.elapsed())} · in {fmt_tokens(u.get('input_tokens'))} / out {fmt_tokens(u.get('output_tokens'))}"
        return f"{ts} {head} {STATUS_ICON.get(task.status_group, '■') if s != 'started' else '▶'} {s}{extra}"
    if kind == "message":
        if phase == "started":
            return None
        return f"{ts} {head} 💬 {one_line(ev.get('text'), 400)}"
    if kind == "reasoning":
        if phase != "completed":
            return None
        return f"{ts} {head} 🧠 {one_line(ev.get('text'), 240)}"
    if kind == "command":
        if phase == "started":
            return f"{ts} {head} $  {one_line(ev.get('command'), 220)}"
        if phase == "completed":
            out = one_line(ev.get("output"), 160)
            return f"{ts} {head} ↳  exit {ev.get('exit_code')}  {out}"
        return None
    if kind == "mcp":
        if phase == "started":
            return f"{ts} {head} 🔧 {ev.get('server')}.{ev.get('tool')}({one_line(ev.get('arguments'), 160)})"
        if phase == "completed":
            res = f"error: {ev['error']}" if ev.get("error") else one_line(ev.get("result"), 160)
            return f"{ts} {head} ↳  {ev.get('tool')} {ev.get('status')}  {res}"
        return None
    if kind == "web_search":
        if phase == "completed" or (phase == "started" and ev.get("query")):
            return f"{ts} {head} 🌐 {one_line(ev.get('query'), 200)}" if phase == "completed" else None
        return None
    if kind == "file_change":
        if phase != "completed":
            return None
        ch = ", ".join(f"{c.get('kind', '')}:{os.path.basename(str(c.get('path', '')))}" for c in ev.get("changes", [])[:6])
        return f"{ts} {head} ✎  {ch}"
    if kind == "todo":
        items = ev.get("items") or []
        done = sum(1 for i in items if i.get("completed"))
        nxt = next((i.get("text") for i in items if not i.get("completed")), "")
        return f"{ts} {head} ☑  {done}/{len(items)}  下一步: {one_line(nxt, 120)}"
    if kind == "usage":
        u = ev.get("usage") or {}
        return f"{ts} {head} Σ  in {fmt_tokens(u.get('input_tokens'))} (cached {fmt_tokens(u.get('cached_input_tokens'))}) · out {fmt_tokens(u.get('output_tokens'))} · reasoning {fmt_tokens(u.get('reasoning_output_tokens'))}"
    if kind == "error":
        return f"{ts} {head} ⚠  {one_line(ev.get('text'), 300)}"
    if kind == "thread":
        return f"{ts} {head} ▶  session {ev.get('text')}"
    if kind == "raw":
        return f"{ts} {head} ·  {one_line(ev.get('text'), 200)}"
    return None


def render_snapshot(mon: Monitor, tty: bool) -> str:
    st = mon.state(recent=0)
    lines = []
    lines.append(f"workspace: {st['workspace']}")
    runs = st["runs"]
    lines.append(f"批次: {', '.join(runs) if runs else '（无并行批次）'}   "
                 f"任务 {sum(st['counts'].values())}：" + "  ".join(f"{k} {v}" for k, v in sorted(st["counts"].items())))
    for r in runs:
        info = st["run_info"].get(r) or {}
        if info:
            lines.append(f"  {r}: backend={info.get('backend')} jobs={info.get('jobs')} profile={info.get('profile') or '—'} "
                         f"model={info.get('model') or '—'} sandbox={info.get('sandbox')} timeout={info.get('timeout')}s tasks={info.get('tasks_file')}")
    lines.append("")
    hdr = (pad("角色", 14) + " " + pad("任务", 30) + " " + pad("状态", 10) + " " + pad("耗时", 7, True) + " "
           + pad("in/out tok", 14, True) + "  cmd mcp/审计  web file  最近输出")
    lines.append(hdr)
    lines.append("-" * 150)
    for t in st["tasks"]:
        c = t["counts"]
        role = ROLE_META.get(t["role"], ROLE_META["unknown"])
        last = one_line(t["current_command"] and ("$ " + t["current_command"]) or t["last_message"], 70)
        row = (pad(f"{role[0]} {role[1]}", 14) + " " + pad(t["name"], 30) + " "
               + pad(f"{STATUS_ICON.get(t['status_group'], '■')} {t['status_group']}", 10) + " "
               + pad(fmt_dur(t["elapsed"]), 7, True) + " "
               + pad(fmt_tokens(t["tokens_in"]) + "/" + fmt_tokens(t["tokens_out"]), 14, True)
               + f" {c.get('command', 0):>4} {str(c.get('mcp', 0)) + '/' + str(t.get('audit_calls', 0)):>8} "
               + f"{c.get('web_search', 0):>4} {c.get('file_change', 0):>4}  {last}")
        lines.append(_color(t["role"], row, tty))
        if t["status"] not in (t["status_group"], "RUNNING", "PASS", "DONE"):
            lines.append(f"{'':<15} status={t['status']}  exit={t['exit']} process_exit={t['process_exit']}")
        if t["validation"]:
            lines.append(f"{'':<15} ⛔ {t['validation']}")
    led = st["ledger"]
    lines.append("")
    if led:
        gates = " ".join(f"{k}={v['status']}" for k, v in led["gates"].items())
        lines.append(f"账本: stage={led['stage']} round={led['round']}/{led['max_rounds']} effort={led['effort']} strictness={led['strictness']}")
        lines.append(f"  gates: {gates}")
        if led["open_issues"]:
            lines.append(f"  open issues ({len(led['open_issues'])}): " + "; ".join(f"{i['id']}[{i['severity']}→{i['target']}] {one_line(i['text'], 80)}" for i in led["open_issues"][:6]))
    else:
        lines.append("账本: （无 state/ledger.json）")
    au = st["audit"]
    if au["total"]:
        tools = ", ".join(f"{k} {v}" for k, v in list(au["by_tool"].items())[:8])
        unattr = au["by_run"].get("(未归因)", 0)
        lines.append(f"MCP 审计: {au['total']} 次（{tools}）；未归因到任务 {unattr} 次")
        if au["recent"]:
            r = au["recent"][-1]
            lines.append(f"  最近: {r['ts']} {r['tool']} {fmt_dur((r['duration_ms'] or 0) / 1000)} run_id={r['run_id']} {r['request']}")
    else:
        lines.append("MCP 审计: （无 state/tool_calls.jsonl 记录）")
    return "\n".join(lines)


def follow(mon: Monitor, interval: float, tty: bool, quiet_kinds: set[str]) -> None:
    print(render_snapshot(mon, tty))
    print("\n—— 实时流开始（Ctrl-C 结束）——\n", flush=True)
    stop = threading.Event()

    def _sig(*_):
        stop.set()

    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)
    # main() 已预热过一轮 poll：已有历史不刷屏，这里只打印此后新增的事件
    while not stop.is_set():
        for _, task, ev in mon.poll():
            if ev["kind"] in quiet_kinds:
                continue
            line = fmt_event(task, ev, tty)
            if line:
                print(line, flush=True)
        stop.wait(interval)
    print("\n—— 汇总 ——")
    print(render_snapshot(mon, tty))


# ----------------------------------------------------------------------------- Web 看板
def _ui_html() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "live_view_ui.html")
    if os.path.exists(path):
        return read_text(path)
    return ("<!doctype html><meta charset=utf-8><title>live_view</title>"
            "<p>缺少 live_view_ui.html；请查看 <a href='/api/state'>/api/state</a>。</p>")


def serve(mon: Monitor, host: str, port: int, interval: float) -> None:
    ui = _ui_html()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):  # 安静
            pass

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code=200) -> None:
            self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"), "application/json; charset=utf-8")

        def do_GET(self):  # noqa: N802
            u = urlparse(self.path)
            q = parse_qs(u.query)
            if u.path in ("/", "/index.html"):
                return self._send(200, ui.encode("utf-8"), "text/html; charset=utf-8")
            if u.path == "/api/state":
                recent = int(q.get("recent", ["30"])[0])
                runs = q.get("run") or None
                show_all = True if q.get("all") else None
                return self._json(mon.state(recent=recent, runs=runs, show_all=show_all))
            if u.path == "/api/feed":
                after = int(q.get("after", ["0"])[0])
                return self._json({"seq": mon.seq, "events": mon.feed_since(after)})
            if u.path == "/api/task":
                key = q.get("key", [""])[0]
                d = mon.task_detail(key)
                return self._json(d if d else {"error": "no such task"}, 200 if d else 404)
            return self._json({"error": "not found"}, 404)

    httpd = ThreadingHTTPServer((host, port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print(f"live_view 看板: http://{host}:{port}   (workspace={mon.ws}, 每 {interval}s 扫描；Ctrl-C 结束)", flush=True)
    try:
        while True:
            mon.poll()
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()


# ----------------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="按角色实时查看 goai 多 agent 运行（只读）")
    ap.add_argument("--workspace", default=os.environ.get("GOAI_WORKSPACE", "workspace"), help="工作区目录（默认 $GOAI_WORKSPACE 或 workspace）")
    ap.add_argument("--run-id", action="append", default=[], help="只看指定批次（可重复）")
    ap.add_argument("--all", action="store_true", help="显示所有批次（回放整场运行）")
    ap.add_argument("--orchestrator-log", action="append", default=[], help="额外的编排器 JSONL（如 goai_cold_logs/*.jsonl）")
    ap.add_argument("--follow", "-f", action="store_true", help="终端实时流")
    ap.add_argument("--serve", metavar="[HOST:]PORT", help="启动浏览器看板")
    ap.add_argument("--interval", type=float, default=1.0, help="扫描间隔秒（默认 1）")
    ap.add_argument("--quiet", default="", help="follow 模式屏蔽的事件类型，逗号分隔（如 reasoning,audit,web_search）")
    ap.add_argument("--json", action="store_true", help="快照以 JSON 输出（含最近事件）")
    ap.add_argument("--no-color", action="store_true")
    args = ap.parse_args(argv)

    ws = args.workspace
    if not os.path.isdir(os.path.join(ws, "state")):
        print(f"工作区缺少 state/ 目录: {ws}（用 --workspace 或 GOAI_WORKSPACE 指定）", file=sys.stderr)
        return 2
    mon = Monitor(ws, run_ids=args.run_id, show_all=args.all, orch_logs=args.orchestrator_log)
    tty = sys.stdout.isatty() and not args.no_color
    mon.poll()
    if args.serve:
        host, _, port = args.serve.rpartition(":")
        serve(mon, host or "127.0.0.1", int(port), args.interval)
        return 0
    if args.follow:
        follow(mon, args.interval, tty, {k for k in args.quiet.split(",") if k})
        return 0
    if args.json:
        print(json.dumps(mon.state(recent=30), ensure_ascii=False, indent=2, default=str))
        return 0
    print(render_snapshot(mon, tty))
    return 0


if __name__ == "__main__":
    sys.exit(main())
