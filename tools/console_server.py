#!/usr/bin/env python3
"""goai console 后端 —— 角色说明 / 发起与终止研究运行 / 历史工作区浏览 / 实时观察。

  python3 tools/console_server.py --port 5051 \
      [--codex-home ~/.codex_rev] [--runs-root workspace_runs/console] \
      [--workspace-glob '/home/gaojing/goai_cold_*/workspace' ...] \
      [--private-corpus-env configs/private_corpus.env]

前端是 tools/console/（Vite + Vue 3 + Naive UI），构建产物 tools/console/dist/ 由本服务托管；
观察部分复用 tools/live_view.py 的 Monitor（只读解析 Codex 事件流 / 账本 / MCP 审计）。

运行控制沿用 scripts/run_three_synthesis_topics.sh 的落盘约定，历史浏览因此能同时识别
脚本启动与控制台启动的工作区：
  <ws>/topic_only.txt            唯一研究输入
  <ws>/launcher.started|.pid|.exit|.finished|.status|.stopped
  <ws>/launcher.stdout.log|.stderr.log
启动 = 后台运行 `bash scripts/reproduce_core.sh --topic <主题> --workdir <ws>`（独立会话）；
终止 = 向该会话进程组发 SIGTERM，8 秒后仍在则 SIGKILL（编排器、子 agent、MCP server 同组）。
只绑定 127.0.0.1；远程使用请走 SSH 端口转发。
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import glob
import hashlib
import json
import mimetypes
import os
import re
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import live_view  # noqa: E402  (同目录)

# ----------------------------------------------------------------------------- 角色
# 与 skills/*/SKILL.md 一一对应；description 从 frontmatter 读，这里只放 skill 里没有的结构信息。
ROLE_EXTRA = {
    "goai-orchestrator": {"stage": "intake → final（全程）", "gate": "check-done", "server": None,
                          "tools": ["tools/loopctl.py", "tools/parallel_run.sh"],
                          "brief": "只做四件事：建账本 → 分派 → 验闸门 → 路由返工。自己不检索、不写、不画。"},
    "goai-lit-search": {"stage": "lit_search", "gate": "lit_coverage", "server": "goai-litsearch",
                        "tools": ["local_corpus_status", "grep_local_corpus", "read_local_document", "lookup_local_doi",
                                  "search_papers", "snowball", "lookup", "save_to_library", "coverage_report",
                                  "download_pdf", "export_bibtex"],
                        "brief": "查全导向：本地全文语料优先，多源检索 + 引文滚雪球，材料主题必做近邻体系与相图两条检索面。"},
    "goai-style-bank": {"stage": "style_bank（与 lit_search 并行）", "gate": "style_bank_ready", "server": "goai-litsearch",
                        "tools": ["search_papers", "download_pdf"],
                        "brief": "学 30 篇经典综述：写作风格卡 + 图纸风格卡 + 范图库，供写作与图纸阶段消费。"},
    "goai-ref-guard": {"stage": "ref_gate", "gate": "ref_integrity", "server": "goai-refcheck",
                       "tools": ["verify_bib_file", "verify_entry", "deep_audit_info"],
                       "brief": "引用零信任：存在性 / 元数据 / 作者名单与顺序三轴核验，fail-closed，不放行可疑引用。"},
    "goai-survey-writer": {"stage": "taxonomy → writing", "gate": "taxonomy_ready · draft_complete", "server": None,
                           "tools": ["tools/bank_check.py", "tools/bib_guard.py", "tools/tex_guard.py",
                                     "tools/academic_language_guard.py", "scripts/build_tex.sh", "tools/pdf_guard.py"],
                           "brief": "贡献先行五步流水线：taxonomy → 引用支持库 → 章节蓝图 → 逐节写作 → 组装精修，claim 级引用绑定，TeX 编译 PDF。"},
    "goai-figure-studio": {"stage": "figures（与 writing/ideas 并行）", "gate": "figures_ready", "server": "goai-figure",
                           "tools": ["figspec_schema", "validate_figspec", "render_figure", "drawio_export", "list_figures"],
                           "brief": "策略合同 → AI 生图两轮候选 → figspec 可编辑化重建，产物恒为 svg + drawio，美学 lint 是闸门。"},
    "goai-figure-editable": {"stage": "figures", "gate": "figures_ready", "server": "goai-figure",
                             "tools": ["svg_file_to_drawio", "drawio_export"],
                             "brief": "把现成矢量图逆向为 figspec 并转成 draw.io 可编辑文件。"},
    "goai-idea-forge": {"stage": "ideas（与 figures/writing 并行）", "gate": "ideas_reviewed", "server": "goai-retro",
                        "tools": ["provider_status", "inorganic_model_status", "predict_precursor_routes",
                                  "predict_retro", "make_experiment_plan"],
                        "brief": "从缺口 / 矛盾 / 组合空位提炼提案，无机材料调用两步前驱体模型，方案经对抗审核 + 引用二审。"},
    "goai-reviewer": {"stage": "review", "gate": "review_pass", "server": None,
                      "tools": ["codex exec（独立模型）", "tools/loopctl.py issue add"],
                      "brief": "对抗审稿：跨模型优先，产出可路由的结构化 issue，翻最终 PDF 做制作质量审计，不改稿。"},
}
ROLE_ORDER = ["goai-orchestrator", "goai-lit-search", "goai-style-bank", "goai-ref-guard", "goai-survey-writer",
              "goai-figure-studio", "goai-figure-editable", "goai-idea-forge", "goai-reviewer"]


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    out = {}
    if not m:
        return out
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def load_roles(repo: str) -> list[dict]:
    roles = []
    for rid in ROLE_ORDER:
        path = os.path.join(repo, "skills", rid, "SKILL.md")
        text = live_view.read_text(path)
        fm = parse_frontmatter(text)
        icon, label, _ = live_view.ROLE_META.get(rid, live_view.ROLE_META["unknown"])
        extra = ROLE_EXTRA.get(rid, {})
        roles.append({
            "id": rid, "label": label, "icon": icon, "name": fm.get("name", rid),
            "description": fm.get("description", ""), "brief": extra.get("brief", ""),
            "stage": extra.get("stage", ""), "gate": extra.get("gate", ""), "server": extra.get("server"),
            "tools": extra.get("tools", []), "skill_path": os.path.relpath(path, repo),
            "skill_lines": text.count("\n"), "exists": bool(text),
        })
    return roles


# ----------------------------------------------------------------------------- 工作区
def ws_id(path: str) -> str:
    return hashlib.sha1(os.path.abspath(path).encode()).hexdigest()[:10]


def _read_json(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _pid_alive(pid) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError, TypeError):
        return False


def _iso(ts):
    return dt.datetime.fromtimestamp(ts).isoformat(timespec="seconds") if ts else None


class Workspaces:
    """发现并描述所有工作区（历史 + 运行中），按需创建 live_view.Monitor。"""

    def __init__(self, repo: str, runs_root: str, extra_globs: list[str]):
        self.repo = repo
        self.runs_root = runs_root
        self.extra_globs = extra_globs
        self.monitors: dict[str, live_view.Monitor] = {}
        self.monitor_touch: dict[str, float] = {}
        self.launched: dict[str, subprocess.Popen] = {}
        self.lock = threading.Lock()

    # -- 发现 -----------------------------------------------------------------
    def candidate_paths(self) -> list[str]:
        pats = [
            os.path.join(self.repo, "workspace"),
            os.path.join(self.repo, "workspace_repro_*"),
            os.path.join(self.repo, "workspace_runs", "*"),
            os.path.join(self.repo, "workspace_runs", "*", "*"),
            os.path.join(self.runs_root, "*"),
        ] + self.extra_globs
        seen, out = set(), []
        for pat in pats:
            for p in sorted(glob.glob(os.path.expanduser(pat))):
                p = os.path.abspath(p)
                if p in seen or not os.path.isdir(os.path.join(p, "state")):
                    continue
                seen.add(p)
                out.append(p)
        return out

    def describe(self, path: str, light: bool = True) -> dict:
        state = os.path.join(path, "state")
        ledger = _read_json(os.path.join(state, "ledger.json")) or {}
        topic = (live_view.read_text(os.path.join(path, "topic_only.txt")).strip()
                 or live_view.read_text(os.path.join(path, "inputs", "topic_input.txt")).strip()
                 or ledger.get("topic") or "")
        topic = re.sub(r"^调研主题：", "", topic)
        launcher = {
            "started": live_view.read_text(os.path.join(path, "launcher.started")).strip() or None,
            "pid": live_view.read_text(os.path.join(path, "launcher.pid")).strip() or None,
            "exit": live_view.read_text(os.path.join(path, "launcher.exit")).strip() or None,
            "finished": live_view.read_text(os.path.join(path, "launcher.finished")).strip() or None,
            "status": live_view.read_text(os.path.join(path, "launcher.status")).strip() or None,
            "stopped": live_view.read_text(os.path.join(path, "launcher.stopped")).strip() or None,
            "meta": _read_json(os.path.join(path, "launcher.json")) or {},
        }
        launcher["alive"] = _pid_alive(launcher["pid"]) if launcher["pid"] else False
        # 批次 / 任务统计（轻量：只数文件）
        pdir = os.path.join(state, "parallel")
        batches = sorted(d for d in os.listdir(pdir)) if os.path.isdir(pdir) else []
        n_tasks = n_running = 0
        last_activity = 0.0
        for b in batches:
            bd = os.path.join(pdir, b)
            try:
                files = os.listdir(bd)
            except OSError:
                continue
            names = {f[:-6] for f in files if f.endswith(".jsonl")}
            n_tasks += len(names)
            for n in names:
                if f"{n}.exit" not in files:
                    n_running += 1
                m = live_view.mtime(os.path.join(bd, n + ".jsonl")) or 0
                last_activity = max(last_activity, m)
        for f in glob.glob(os.path.join(state, "orchestrator", "*.jsonl")):
            last_activity = max(last_activity, live_view.mtime(f) or 0)
        last_activity = max(last_activity, live_view.mtime(os.path.join(state, "ledger.json")) or 0)
        gates = {k: (v or {}).get("status") for k, v in (ledger.get("gates") or {}).items()}
        receipt = _read_json(os.path.join(state, "REPRODUCTION_RECEIPT.json"))
        final_pdf = os.path.join(path, "drafts", "main.pdf")
        pdf_ok = os.path.exists(final_pdf)
        # 状态判定
        if launcher["alive"]:
            status = "running"
        elif launcher["stopped"]:
            status = "stopped"
        elif launcher["exit"] is not None:
            status = "done" if launcher["exit"] == "0" else "failed"
        elif receipt and receipt.get("status") == "PASS":
            status = "done"
        elif ledger.get("stage") == "final":
            status = "done"
        elif n_running and last_activity and time.time() - last_activity < 900:
            status = "running"
        elif ledger or batches:
            status = "ended"
        else:
            status = "empty"
        created = ledger.get("created")
        if not created:
            m = live_view.mtime(os.path.join(path, "inputs", "topic_input.txt")) or live_view.mtime(state)
            created = _iso(m)
        info = {
            "id": ws_id(path), "path": path, "label": os.path.basename(path.rstrip("/")),
            "parent": os.path.basename(os.path.dirname(path.rstrip("/"))),
            "topic": topic, "created": created, "stage": ledger.get("stage"), "round": ledger.get("round"),
            "max_rounds": ledger.get("max_rounds"), "effort": ledger.get("effort"), "strictness": ledger.get("strictness"),
            "gates": gates, "gate_counts": dict(collections.Counter(gates.values())),
            "batches": len(batches), "tasks": n_tasks, "tasks_running": n_running,
            "last_activity": last_activity or None, "status": status, "launcher": launcher,
            "final_pdf": pdf_ok, "final_pdf_bytes": os.path.getsize(final_pdf) if pdf_ok else 0,
            "receipt": {k: receipt.get(k) for k in ("status", "verified_at_utc", "model", "reasoning_effort")} if receipt else None,
            "open_issues": sum(1 for i in (ledger.get("issues") or []) if (i.get("status") or "open") == "open"),
            "is_launchable_dir": path.startswith(os.path.abspath(self.runs_root)),
        }
        return info

    def list(self) -> list[dict]:
        rows = [self.describe(p) for p in self.candidate_paths()]
        rows.sort(key=lambda r: (r["status"] != "running", -(r["last_activity"] or 0)))
        return rows

    def find(self, wid: str) -> str | None:
        for p in self.candidate_paths():
            if ws_id(p) == wid:
                return p
        return None

    # -- 观察器 -----------------------------------------------------------------
    def monitor(self, wid: str) -> live_view.Monitor | None:
        path = self.find(wid)
        if not path:
            return None
        with self.lock:
            mon = self.monitors.get(wid)
            if mon is None:
                mon = live_view.Monitor(path, show_all=True)
                mon.poll()
                self.monitors[wid] = mon
            self.monitor_touch[wid] = time.time()
        return mon

    def poll_active(self) -> None:
        with self.lock:
            active = [w for w, t in self.monitor_touch.items() if time.time() - t < 120]
        for w in active:
            mon = self.monitors.get(w)
            if mon:
                try:
                    mon.poll()
                except Exception as exc:  # 观察器不能拖垮控制台
                    print(f"[console] monitor {w} poll error: {exc}", file=sys.stderr)

    # -- 运行控制 ---------------------------------------------------------------
    def launch(self, topic: str, corpus: str, model: str, effort: str, codex_home: str,
               private_env: dict, slug: str | None = None) -> dict:
        topic = topic.strip()
        if not topic:
            raise ValueError("主题不能为空")
        if corpus not in ("public", "private"):
            raise ValueError("corpus 只能是 public / private")
        if corpus == "private" and not private_env.get("GOAI_LOCAL_CORPUS_ROOTS"):
            raise ValueError("服务端未配置私有语料（--private-corpus-env 或 GOAI_LOCAL_CORPUS_ROOTS）")
        stamp = time.strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_-]+", "_", (slug or topic))[:40].strip("_") or "run"
        ws = os.path.join(self.runs_root, f"{stamp}_{slug}")
        os.makedirs(os.path.join(ws, "state"), exist_ok=True)
        with open(os.path.join(ws, "topic_only.txt"), "w", encoding="utf-8") as f:
            f.write(topic + "\n")
        env = {**os.environ, "CODEX_HOME": os.path.expanduser(codex_home), "GOAI_CORPUS": corpus,
               "GOAI_MODEL": model, "GOAI_REASONING_EFFORT": effort}
        if corpus == "private":
            env.update(private_env)
        cmd = ["bash", "scripts/reproduce_core.sh", "--topic", topic, "--workdir", ws]
        out = open(os.path.join(ws, "launcher.stdout.log"), "ab")
        err = open(os.path.join(ws, "launcher.stderr.log"), "ab")
        proc = subprocess.Popen(cmd, cwd=self.repo, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                start_new_session=True)
        with open(os.path.join(ws, "launcher.started"), "w", encoding="utf-8") as f:
            f.write(f"START {os.path.basename(ws)}\t{dt.datetime.now().astimezone().isoformat(timespec='seconds')}\n")
        with open(os.path.join(ws, "launcher.pid"), "w") as f:
            f.write(f"{proc.pid}\n")
        with open(os.path.join(ws, "launcher.json"), "w", encoding="utf-8") as f:
            json.dump({"topic": topic, "corpus": corpus, "model": model, "effort": effort, "codex_home": codex_home,
                       "cmd": cmd, "pid": proc.pid, "started_at": _iso(time.time()), "launched_by": "console"},
                      f, ensure_ascii=False, indent=2)
        wid = ws_id(ws)
        self.launched[wid] = proc
        threading.Thread(target=self._reap, args=(wid, ws, proc), daemon=True).start()
        return {"id": wid, "path": ws, "pid": proc.pid}

    def _reap(self, wid: str, ws: str, proc: subprocess.Popen) -> None:
        rc = proc.wait()
        with open(os.path.join(ws, "launcher.exit"), "w") as f:
            f.write(f"{rc}\n")
        with open(os.path.join(ws, "launcher.finished"), "w") as f:
            f.write(dt.datetime.now().astimezone().isoformat(timespec="seconds") + "\n")
        stopped = os.path.exists(os.path.join(ws, "launcher.stopped"))
        with open(os.path.join(ws, "launcher.status"), "w") as f:
            f.write(("STOPPED" if stopped else ("PASS" if rc == 0 else "FAIL")) + "\n")
        self.launched.pop(wid, None)

    def stop(self, wid: str, grace: float = 8.0) -> dict:
        path = self.find(wid)
        if not path:
            raise KeyError("workspace not found")
        pid_txt = live_view.read_text(os.path.join(path, "launcher.pid")).strip()
        if not pid_txt or not _pid_alive(pid_txt):
            return {"ok": False, "message": "没有存活的启动进程（可能已结束或不是由控制台/脚本启动）"}
        pid = int(pid_txt)
        with open(os.path.join(path, "launcher.stopped"), "w", encoding="utf-8") as f:
            f.write(dt.datetime.now().astimezone().isoformat(timespec="seconds") + "\n")
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            return {"ok": True, "message": "进程已不存在"}
        deadline = time.time() + grace
        while time.time() < deadline and _pid_alive(pid):
            time.sleep(0.3)
        killed = False
        if _pid_alive(pid):
            try:
                os.killpg(pid, signal.SIGKILL)
                killed = True
            except ProcessLookupError:
                pass
        if wid not in self.launched:  # 不是本进程的孩子：手动补落盘
            time.sleep(0.5)
            if not os.path.exists(os.path.join(path, "launcher.exit")):
                with open(os.path.join(path, "launcher.exit"), "w") as f:
                    f.write("143\n")
                with open(os.path.join(path, "launcher.finished"), "w") as f:
                    f.write(dt.datetime.now().astimezone().isoformat(timespec="seconds") + "\n")
                with open(os.path.join(path, "launcher.status"), "w") as f:
                    f.write("STOPPED\n")
        return {"ok": True, "message": "已发送 SIGKILL" if killed else "已终止（SIGTERM）", "pid": pid}


# ----------------------------------------------------------------------------- HTTP
def read_env_file(path: str) -> dict:
    out = {}
    for line in live_view.read_text(path).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        line = re.sub(r"^export\s+", "", line)
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def make_handler(ws: Workspaces, cfg: dict, dist: str, fallback_html: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code=200) -> None:
            self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"),
                       "application/json; charset=utf-8")

        def _static(self, rel: str) -> None:
            rel = rel.lstrip("/") or "index.html"
            path = os.path.normpath(os.path.join(dist, rel))
            if not path.startswith(os.path.abspath(dist)) or not os.path.isfile(path):
                path = os.path.join(dist, "index.html")  # SPA 回退
            if not os.path.isfile(path):
                return self._send(200, fallback_html.encode("utf-8"), "text/html; charset=utf-8")
            ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
            with open(path, "rb") as f:
                data = f.read()
            self._send(200, data, ctype if not ctype.startswith("text/") else ctype + "; charset=utf-8")

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b""
            try:
                return json.loads(raw or b"{}")
            except ValueError:
                return {}

        # -- GET ----------------------------------------------------------------
        def do_GET(self):  # noqa: N802
            u = urlparse(self.path)
            q = parse_qs(u.query)
            parts = [unquote(p) for p in u.path.strip("/").split("/") if p]
            if not parts or parts[0] != "api":
                return self._static(u.path)
            try:
                if parts[1:] == ["config"]:
                    return self._json(cfg_public(cfg))
                if parts[1:] == ["roles"]:
                    return self._json({"roles": load_roles(ws.repo)})
                if len(parts) == 4 and parts[1] == "roles" and parts[3] == "skill":
                    rid = parts[2]
                    if rid not in ROLE_ORDER:
                        return self._json({"error": "unknown role"}, 404)
                    text = live_view.read_text(os.path.join(ws.repo, "skills", rid, "SKILL.md"))
                    return self._json({"id": rid, "markdown": text})
                if parts[1:] == ["workspaces"]:
                    return self._json({"workspaces": ws.list(), "now": time.time()})
                if len(parts) >= 3 and parts[1] == "workspaces":
                    wid, sub = parts[2], parts[3] if len(parts) > 3 else "info"
                    path = ws.find(wid)
                    if not path:
                        return self._json({"error": "workspace not found"}, 404)
                    if sub == "info":
                        return self._json(ws.describe(path))
                    if sub == "state":
                        mon = ws.monitor(wid)
                        st = mon.state(recent=int(q.get("recent", ["30"])[0]), show_all=True)
                        st["workspace_info"] = ws.describe(path)
                        return self._json(st)
                    if sub == "feed":
                        mon = ws.monitor(wid)
                        after = int(q.get("after", ["0"])[0])
                        return self._json({"seq": mon.seq, "events": mon.feed_since(after)})
                    if sub == "task":
                        mon = ws.monitor(wid)
                        d = mon.task_detail(q.get("key", [""])[0])
                        return self._json(d if d else {"error": "no such task"}, 200 if d else 404)
                    if sub == "launcher-log":
                        tail = int(q.get("tail", ["4000"])[0])
                        return self._json({
                            "stdout": live_view.read_text(os.path.join(path, "launcher.stdout.log"), tail=tail),
                            "stderr": live_view.read_text(os.path.join(path, "launcher.stderr.log"), tail=tail),
                            "orchestrator_final": live_view.read_text(os.path.join(path, "state", "orchestrator", "orchestrator.final.md"), tail=tail),
                        })
                    if sub == "pdf":
                        pdf = os.path.join(path, "drafts", "main.pdf")
                        if not os.path.exists(pdf):
                            return self._json({"error": "no pdf"}, 404)
                        with open(pdf, "rb") as f:
                            data = f.read()
                        return self._send(200, data, "application/pdf", {"Content-Disposition": "inline; filename=main.pdf"})
                    if sub == "artifacts":
                        return self._json(list_artifacts(path))
                    if sub == "file":
                        rel = q.get("path", [""])[0]
                        full = os.path.normpath(os.path.join(path, rel))
                        if not full.startswith(os.path.abspath(path)) or not os.path.isfile(full):
                            return self._json({"error": "not found"}, 404)
                        if os.path.getsize(full) > 2_000_000:
                            return self._json({"error": "file too large"}, 413)
                        return self._json({"path": rel, "text": live_view.read_text(full)})
                return self._json({"error": "not found"}, 404)
            except Exception as exc:  # 把异常变成 JSON，别让前端只看到断线
                return self._json({"error": f"{type(exc).__name__}: {exc}"}, 500)

        # -- POST ---------------------------------------------------------------
        def do_POST(self):  # noqa: N802
            u = urlparse(self.path)
            parts = [unquote(p) for p in u.path.strip("/").split("/") if p]
            body = self._body()
            try:
                if parts[1:] == ["runs"]:
                    res = ws.launch(
                        topic=body.get("topic", ""), corpus=body.get("corpus", "public"),
                        model=body.get("model") or cfg["model"], effort=body.get("effort") or cfg["effort"],
                        codex_home=cfg["codex_home"], private_env=cfg["private_env"], slug=body.get("slug"),
                    )
                    return self._json({"ok": True, **res})
                if len(parts) == 4 and parts[1] == "workspaces" and parts[3] == "stop":
                    return self._json(ws.stop(parts[2]))
                return self._json({"error": "not found"}, 404)
            except (ValueError, KeyError) as exc:
                return self._json({"ok": False, "error": str(exc)}, 400)
            except Exception as exc:
                return self._json({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, 500)

    return Handler


def list_artifacts(path: str) -> dict:
    out = {}
    for label, rel in (("final_pdf", "drafts/main.pdf"), ("main_tex", "drafts/main.tex"),
                       ("references_bib", "library/references.bib"), ("papers_jsonl", "library/papers.jsonl"),
                       ("citation_audit", "state/CITATION_AUDIT.md"), ("scope", "inputs/scope.md"),
                       ("taxonomy", "notes/taxonomy.md"), ("blueprint", "drafts/blueprint.md"),
                       ("receipt", "state/REPRODUCTION_RECEIPT.json"), ("ledger", "state/ledger.json")):
        full = os.path.join(path, rel)
        if os.path.exists(full):
            out[label] = {"path": rel, "bytes": os.path.getsize(full), "mtime": live_view.mtime(full)}
    out["figures_svg"] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(path, "figures", "svg", "*.svg")))
    out["sections"] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(path, "drafts", "sections", "*.tex")))
    out["reviews"] = sorted(os.path.basename(p) for p in glob.glob(os.path.join(path, "state", "review_round*.md")))
    return out


def cfg_public(cfg: dict) -> dict:
    return {
        "repo": cfg["repo"], "runs_root": cfg["runs_root"], "codex_home": cfg["codex_home"],
        "codex_login": cfg.get("codex_login"), "codex_version": cfg.get("codex_version"),
        "model": cfg["model"], "effort": cfg["effort"],
        "private_corpus_available": bool(cfg["private_env"].get("GOAI_LOCAL_CORPUS_ROOTS")),
        "private_corpus_roots": cfg["private_env"].get("GOAI_LOCAL_CORPUS_ROOTS"),
        "public_corpus": os.path.join(cfg["repo"], "submission", "02_研究数据与证据包", "corpus_release"),
        "models": ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-5.5", "gpt-5.4-mini"],
        "efforts": ["low", "medium", "high", "xhigh", "max"],
    }


def codex_probe(codex_home: str) -> tuple[str | None, str | None]:
    env = {**os.environ, "CODEX_HOME": os.path.expanduser(codex_home)}
    try:
        ver = subprocess.run(["bash", "-lc", "codex --version"], capture_output=True, text=True, env=env, timeout=20).stdout.strip()
    except Exception:
        ver = None
    try:
        r = subprocess.run(["bash", "-lc", "codex login status"], capture_output=True, text=True, env=env, timeout=30)
        login = (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else None
    except Exception:
        login = None
    return ver, login


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="goai console 后端")
    ap.add_argument("--repo", default=os.path.dirname(HERE), help="仓库根（默认 tools/ 的上级）")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5051)
    ap.add_argument("--codex-home", default=os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex"))
    ap.add_argument("--runs-root", default=None, help="控制台新建运行的工作区目录（默认 <repo>/workspace_runs/console）")
    ap.add_argument("--workspace-glob", action="append", default=[], help="额外的历史工作区 glob（可重复）")
    ap.add_argument("--private-corpus-env", default=None,
                    help="KEY=VALUE 文件，提供 GOAI_LOCAL_CORPUS_ROOTS / _EXPECTED_INDEX / _SHARD_ROOT（不入库）")
    ap.add_argument("--model", default=os.environ.get("GOAI_MODEL", "gpt-5.6-sol"))
    ap.add_argument("--effort", default=os.environ.get("GOAI_REASONING_EFFORT", "xhigh"))
    ap.add_argument("--dist", default=os.path.join(HERE, "console", "dist"))
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--no-probe", action="store_true", help="启动时不探测 codex 版本/登录状态")
    args = ap.parse_args(argv)

    repo = os.path.abspath(args.repo)
    runs_root = os.path.abspath(args.runs_root or os.path.join(repo, "workspace_runs", "console"))
    os.makedirs(runs_root, exist_ok=True)
    private_env = {k: v for k, v in os.environ.items() if k.startswith("GOAI_LOCAL_CORPUS")}
    if args.private_corpus_env:
        private_env.update({k: v for k, v in read_env_file(args.private_corpus_env).items() if k.startswith("GOAI_LOCAL_CORPUS")})
    cfg = {"repo": repo, "runs_root": runs_root, "codex_home": args.codex_home, "model": args.model,
           "effort": args.effort, "private_env": private_env}
    if not args.no_probe:
        cfg["codex_version"], cfg["codex_login"] = codex_probe(args.codex_home)
    ws = Workspaces(repo, runs_root, args.workspace_glob)
    fallback = live_view.read_text(os.path.join(HERE, "live_view_ui.html")) or "<p>console dist 未构建</p>"
    httpd = ThreadingHTTPServer((args.host, args.port), make_handler(ws, cfg, os.path.abspath(args.dist), fallback))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print(f"goai console: http://{args.host}:{args.port}  repo={repo}  runs_root={runs_root}  codex_home={args.codex_home}"
          f"  codex={cfg.get('codex_version')} / {cfg.get('codex_login')}  private_corpus={'yes' if private_env.get('GOAI_LOCAL_CORPUS_ROOTS') else 'no'}"
          f"  dist={'ok' if os.path.exists(os.path.join(args.dist, 'index.html')) else 'missing → fallback page'}", flush=True)
    try:
        while True:
            ws.poll_active()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
