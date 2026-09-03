"""逆合成 + 回环控制环节的实测回归（真实 HTTP / 真实 MCP stdio / 真实进程并发）。

跑法：.venv/bin/python -m pytest -m live tests/live/test_live_loop.py -v

覆盖离线测试碰不到的三块：
1. retro server 的 MCP stdio 协议层 + http provider 真实路径（含 500/超时/畸形 JSON 注入）
2. loopctl 账本在 50 进程混合并发下的零丢失与 kill -9 后的锁释放
3. parallel_run.sh 的真实调度（并发上限、子进程 stdin 隔离、后端预检、报错路径）

这里的 mock ASKCOS 后端是真的 socket 上的 HTTP server，retro 走的是真的 httpx 请求；
parallel_run.sh 用「假 codex 二进制注入 PATH」测调度逻辑，不打真实网络。
"""
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

pytestmark = pytest.mark.live

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

from server.core import retro  # noqa: E402

LOOPCTL = os.path.join(ROOT, "tools", "loopctl.py")
PARALLEL_RUN = os.path.join(ROOT, "tools", "parallel_run.sh")
API_KEY = "test-key"


# --------------------------------------------------------------------------
# mock ASKCOS 风格后端（真实 socket，按 server/core/retro.py 的约定收发）
# --------------------------------------------------------------------------

class _MockBackend:
    """线程内 HTTP server；requests 记录每条请求供「key 透传」取证。"""

    def __init__(self, slow_seconds: float = 3.0, expected_key: str = API_KEY):
        self.requests: list[dict] = []
        self._lock = threading.Lock()
        outer = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):
                pass

            def _send(self, code: int, payload: bytes):
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(n).decode() if n else ""
                with outer._lock:
                    outer.requests.append({
                        "path": self.path,
                        "authorization": self.headers.get("Authorization"),
                        "content_type": self.headers.get("Content-Type"),
                        "body": raw,
                    })
                try:
                    req = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    req = {}

                if self.path.startswith("/retro/500"):
                    return self._send(500, b'{"error":"internal predictor failure"}')
                if self.path.startswith("/retro/slow"):
                    time.sleep(slow_seconds)
                    return self._send(200, b'{"route_id":"too-late"}')
                if self.path.startswith("/retro/badjson"):
                    return self._send(200, b'{"steps": [ {"step": 1, ')
                if self.path.startswith("/retro/notdict"):
                    return self._send(200, b'["not","a","dict"]')
                if self.path.startswith("/retro/needkey"):
                    if not self.headers.get("Authorization"):
                        return self._send(401, b'{"error":"missing api key"}')
                if expected_key and self.headers.get("Authorization") != \
                        f"Bearer {expected_key}":
                    return self._send(403, b'{"error":"bad api key"}')

                depth = int(req.get("max_depth", 3) or 3)
                steps = [
                    {"step": 1, "reaction": "amide coupling (EDC/HOBt)",
                     "precursors": ["OC(=O)c1ccccc1", "NCC1CC1"],
                     "confidence": 0.81},
                    {"step": 2, "reaction": "Friedel-Crafts acylation",
                     "precursors": ["c1ccccc1", "CC(=O)Cl"], "confidence": 0.64},
                    {"step": 3, "reaction": "commercial building block",
                     "precursors": ["CC(=O)Cl"], "confidence": 0.95},
                ][:depth]
                self._send(200, json.dumps({
                    "target_smiles": req.get("target_smiles", ""),
                    "route_id": "mock-askcos-1",
                    "verified": True,
                    "engine": "mock-askcos/1.0",
                    "steps": steps,
                }).encode())

        self._srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self._srv.server_address[1]
        self._th = threading.Thread(target=self._srv.serve_forever, daemon=True)
        self._th.start()

    def url(self, path="/retro/predict") -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def close(self):
        self._srv.shutdown()
        self._srv.server_close()


@pytest.fixture
def backend():
    b = _MockBackend()
    try:
        yield b
    finally:
        b.close()


@pytest.fixture
def http_env(backend, monkeypatch):
    """把 retro 切到 http provider，指向 mock 后端。"""
    monkeypatch.setenv("GOAI_RETRO_PROVIDER", "http")
    monkeypatch.setenv("GOAI_RETRO_API_KEY", API_KEY)
    monkeypatch.setenv("GOAI_RETRO_TIMEOUT", "5")
    monkeypatch.setenv("GOAI_RETRO_API_URL", backend.url())
    return backend


# --------------------------------------------------------------------------
# MCP stdio 协议层
# --------------------------------------------------------------------------

def mcp_chain(env_extra: dict, smiles: str, max_depth: int,
              objective: str = "live test") -> dict:
    """起真实 stdio server 走 provider_status → predict_retro → make_experiment_plan。"""
    import asyncio

    params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(ROOT, "server", "retro_server.py")],
        env={**os.environ, **env_extra},
    )

    def text(res) -> str:
        return "".join(getattr(c, "text", "") for c in res.content)

    async def _run():
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                init = await s.initialize()
                tools = await s.list_tools()
                status = json.loads(text(await s.call_tool("provider_status", {})))
                route = json.loads(text(await s.call_tool(
                    "predict_retro",
                    {"target_smiles": smiles, "max_depth": max_depth})))
                plan = json.loads(text(await s.call_tool(
                    "make_experiment_plan",
                    {"route_json": json.dumps(route), "objective": objective})))
                info = getattr(init, "server_info", None) or init.serverInfo
                return {"server_name": info.name,
                        "tools": sorted(t.name for t in tools.tools),
                        "status": status, "route": route, "plan": plan}

    return asyncio.run(_run())


def test_mcp_stdio_stub_full_chain():
    """stub provider 经真实 MCP stdio 协议走完整回环。"""
    out = mcp_chain({"GOAI_RETRO_PROVIDER": "stub"},
                    "CC(=O)Oc1ccccc1C(=O)O", 2)
    assert out["server_name"] == "goai-retro"
    assert out["tools"] == ["inorganic_model_status", "make_experiment_plan",
                            "predict_precursor_routes", "predict_retro",
                            "provider_status"]
    assert out["status"]["provider"] == "stub"
    assert out["status"]["trusted"] is False
    route, plan = out["route"], out["plan"]
    assert route["provider"] == "stub" and route["verified"] is False
    assert len(route["steps"]) == 2
    assert plan["provider_verified"] is False        # stub 不得冒充可信
    assert len(plan["steps"]) == 2
    assert all(s["safety"] for s in plan["steps"])
    assert len(plan["review_gates"]) == 4


def test_mcp_stdio_http_full_chain(backend):
    """http provider 经 MCP 协议层打到真实 HTTP 后端，路线落进实验方案。"""
    out = mcp_chain({"GOAI_RETRO_PROVIDER": "http",
                     "GOAI_RETRO_API_URL": backend.url(),
                     "GOAI_RETRO_API_KEY": API_KEY,
                     "GOAI_RETRO_TIMEOUT": "10"},
                    "CC(=O)Nc1ccc(O)cc1", 3)
    assert out["status"]["provider"] == "http"
    assert out["status"]["trusted"] is True
    route = out["route"]
    assert route["ok"] is True
    assert route["engine"] == "mock-askcos/1.0"
    assert len(route["steps"]) == 3                  # 后端遵守 max_depth
    plan = out["plan"]
    assert plan["provider_verified"] is True         # 后端自称 verified
    assert plan["steps"][0]["inputs"] == ["OC(=O)c1ccccc1", "NCC1CC1"]
    assert len(backend.requests) >= 1


def test_mcp_stdio_http_backend_500_no_crash(backend):
    """后端 500 时协议层不得抛裸异常，且失败路线不能被标记为已验证。"""
    out = mcp_chain({"GOAI_RETRO_PROVIDER": "http",
                     "GOAI_RETRO_API_URL": backend.url("/retro/500"),
                     "GOAI_RETRO_API_KEY": API_KEY,
                     "GOAI_RETRO_TIMEOUT": "10"},
                    "CCO", 2)
    assert out["route"]["ok"] is False
    assert "500" in out["route"]["error"]
    assert out["plan"]["provider_verified"] is False
    assert out["plan"]["steps"] == []


# --------------------------------------------------------------------------
# http provider：真实请求 / key 透传 / 故障注入
# --------------------------------------------------------------------------

def test_http_provider_happy_path_and_key_passthrough(http_env):
    b = http_env
    route = retro.predict("CC(=O)Oc1ccccc1C(=O)O", 2)
    assert route["ok"] is True and route["provider"] == "http"
    assert route["engine"] == "mock-askcos/1.0"
    assert len(route["steps"]) == 2

    req = b.requests[-1]
    assert req["authorization"] == f"Bearer {API_KEY}"   # key 确实带上了
    assert req["content_type"] == "application/json"
    assert json.loads(req["body"]) == {
        "target_smiles": "CC(=O)Oc1ccccc1C(=O)O", "max_depth": 2}


def test_http_provider_no_key_when_unset(backend, monkeypatch):
    monkeypatch.setenv("GOAI_RETRO_PROVIDER", "http")
    monkeypatch.setenv("GOAI_RETRO_API_URL", backend.url("/retro/needkey"))
    monkeypatch.delenv("GOAI_RETRO_API_KEY", raising=False)
    r = retro.predict("CCO", 1)
    assert r["ok"] is False and "401" in r["error"]      # 后端拒绝，且不抛异常
    assert backend.requests[-1]["authorization"] is None


@pytest.mark.parametrize("path,expect", [
    ("/retro/500", "HTTP 500"),
    ("/retro/badjson", "不是合法 JSON"),
    ("/retro/notdict", "顶层应为对象"),
])
def test_http_fault_injection_returns_structured_error(http_env, path, expect):
    """500 / 畸形 JSON / 非 dict JSON 都必须收敛为 ok=False，不抛异常。"""
    os.environ["GOAI_RETRO_API_URL"] = http_env.url(path)
    r = retro.predict("CCO", 2)
    assert isinstance(r, dict)
    assert r["ok"] is False and r["verified"] is False
    assert expect in r["error"]


# --------------------------------------------------------------------------
# http provider：JSON 合法但结构不合约定（后端版本漂移 / 网关改写）
# --------------------------------------------------------------------------

# 这些响应都能过 json.loads 与顶层 dict 校验，带着 ok=true 流到下游。
# 旧实现直接迭代 steps，在 MCP 工具层抛裸 AttributeError/TypeError，
# 调用方只看到 "Error executing tool make_experiment_plan"。
MALFORMED_ROUTES = {
    "steps_是字符串": {"route_id": "r1", "steps": "oops-not-a-list"},
    "steps_是对象": {"route_id": "r2", "steps": {"2": {"reaction": "b"},
                                                "1": {"reaction": "a"}}},
    "steps_是null": {"route_id": "r3", "steps": None},
    "steps_元素是字符串": {"route_id": "r4", "steps": ["one", "two"]},
    "steps_元素是数字": {"route_id": "r5", "steps": [1, 2, 3]},
    "完全没有steps": {"route_id": "r6"},
}


@pytest.mark.parametrize("label", sorted(MALFORMED_ROUTES))
def test_plan_survives_structurally_invalid_steps(label):
    """结构错位的路线必须收敛为可读方案，且绝不自称 provider_verified。"""
    route = {"provider": "http", "ok": True, **MALFORMED_ROUTES[label]}
    plan = retro.experiment_plan_skeleton(route, "结构错位取证")
    assert isinstance(plan["steps"], list)
    assert plan["provider_verified"] is False, \
        f"{label}: 读不全的路线不得声称已验证"
    assert all(isinstance(s, dict) for s in plan["steps"])


def test_plan_flattens_dict_steps_in_key_order():
    """{"1":..,"2":..} 形态按 key 排序摊平，并如实记录 route_problems。"""
    route = {"provider": "http", "ok": True, "route_id": "r",
             "steps": {"2": {"step": 2, "reaction": "second"},
                       "1": {"step": 1, "reaction": "first"}}}
    plan = retro.experiment_plan_skeleton(route)
    assert [s["reaction"] for s in plan["steps"]] == ["first", "second"]
    assert any("steps 是对象" in p for p in plan["route_problems"])
    assert plan["provider_verified"] is False


def test_mcp_make_experiment_plan_no_opaque_tool_error():
    """回归守卫：结构错位路线经真实 MCP 协议层不得只回一句 Error executing tool。"""
    import asyncio

    params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(ROOT, "server", "retro_server.py")],
        env={**os.environ, "GOAI_RETRO_PROVIDER": "stub"},
    )
    bad = {"provider": "http", "ok": True, "route_id": "r-bad",
           "steps": {"1": {"reaction": "amide coupling"}}}

    async def _run():
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                res = await s.call_tool("make_experiment_plan",
                                        {"route_json": json.dumps(bad),
                                         "objective": "mcp 结构错位"})
                return "".join(getattr(c, "text", "") for c in res.content)

    out = asyncio.run(_run())
    assert "Error executing tool" not in out, out[:200]
    plan = json.loads(out)
    assert plan["provider_verified"] is False
    assert len(plan["steps"]) == 1
    assert plan["route_problems"]


def test_http_timeout_env_honored(http_env):
    """GOAI_RETRO_TIMEOUT 必须真实生效（后端 sleep 3s，超时设 1s）。"""
    os.environ["GOAI_RETRO_API_URL"] = http_env.url("/retro/slow")
    os.environ["GOAI_RETRO_TIMEOUT"] = "1"
    t0 = time.monotonic()
    r = retro.predict("CCO", 2)
    elapsed = time.monotonic() - t0
    assert r["ok"] is False and "未响应" in r["error"]
    assert elapsed < 2.5, f"超时未生效，耗时 {elapsed:.2f}s"


def test_http_connection_refused_is_structured(monkeypatch):
    monkeypatch.setenv("GOAI_RETRO_PROVIDER", "http")
    monkeypatch.setenv("GOAI_RETRO_API_URL", "http://127.0.0.1:9/retro/predict")
    monkeypatch.setenv("GOAI_RETRO_TIMEOUT", "5")
    r = retro.predict("CCO", 1)
    assert r["ok"] is False
    assert "连接逆合成后端失败" in r["error"]


def test_http_loopback_ignores_system_proxy(http_env, monkeypatch):
    """回归守卫：本机后端不得被环境/系统代理劫持（httpx 不自动 bypass localhost）。"""
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:1")
    r = retro.predict("CCO", 1)
    assert r["ok"] is True, f"localhost 后端被代理劫持: {r.get('error')}"

    # 显式要求走代理时应当尊重配置（此处代理是死端口 → 结构化连接失败）
    monkeypatch.setenv("GOAI_RETRO_TRUST_ENV", "1")
    monkeypatch.delenv("NO_PROXY", raising=False)
    monkeypatch.delenv("no_proxy", raising=False)
    r2 = retro.predict("CCO", 1)
    assert r2["ok"] is False
    assert ("连接逆合成后端失败" in r2["error"]
            or "HTTP 500" in r2["error"]), r2["error"]


# --------------------------------------------------------------------------
# loopctl 高并发
# --------------------------------------------------------------------------

def _loopctl(ws, *args, timeout=60):
    return subprocess.run([sys.executable, LOOPCTL, *args],
                          capture_output=True, text=True,
                          env={**os.environ, "GOAI_WORKSPACE": str(ws)},
                          timeout=timeout)


def test_loopctl_50_process_mixed_concurrency(tmp_path):
    """50 进程混合 log/gate/issue 并发：零丢失、账本恒为合法 JSON、无死锁。"""
    ws = tmp_path / "ws"
    ws.mkdir()
    ledger = ws / "state" / "ledger.json"
    assert _loopctl(ws, "init", "--topic", "并发压测").returncode == 0

    n = 50
    ops = []
    for i in range(n):
        if i % 3 == 0:
            ops.append(["log", "--stage", "writing", "--agent", f"w{i}",
                        "--event", "draft", "--detail", f"S-LOG-{i}"])
        elif i % 3 == 1:
            ops.append(["gate", "--name", f"s_gate_{i}", "--status", "PASS",
                        "--detail", f"S-GATE-{i}"])
        else:
            ops.append(["issue", "add", "--from-agent", f"a{i}",
                        "--target", "writing", "--severity", "minor",
                        "--text", f"S-ISSUE-{i}"])
    n_log = sum(1 for i in range(n) if i % 3 == 0)
    n_gate = sum(1 for i in range(n) if i % 3 == 1)
    n_issue = n - n_log - n_gate

    # 哨兵线程：并发读账本，验证 save() 的原子替换从不暴露撕裂中间态
    bad_reads = []
    stop = threading.Event()

    def poll():
        while not stop.is_set():
            try:
                with open(ledger, encoding="utf-8") as f:
                    json.load(f)
            except FileNotFoundError:
                pass
            except Exception as e:  # noqa: BLE001
                bad_reads.append(f"{type(e).__name__}: {e}")
            time.sleep(0.002)

    th = threading.Thread(target=poll, daemon=True)
    th.start()

    env = {**os.environ, "GOAI_WORKSPACE": str(ws)}
    t0 = time.monotonic()
    procs = [subprocess.Popen([sys.executable, LOOPCTL, *a], env=env,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.PIPE, text=True) for a in ops]
    deadline = t0 + 90          # 总超时兜底，防死锁把测试挂住
    for p in procs:
        p.wait(timeout=max(0.1, deadline - time.monotonic()))
    elapsed = time.monotonic() - t0
    stop.set()
    th.join(timeout=2)

    assert all(p.returncode == 0 for p in procs), \
        [p.stderr.read() for p in procs if p.returncode != 0][:3]
    assert not bad_reads, bad_reads[:3]

    lg = json.loads(ledger.read_text(encoding="utf-8"))
    details = {e.get("detail") for e in lg["log"]}
    texts = {i["text"] for i in lg["issues"]}
    assert all(f"S-LOG-{i}" in details for i in range(n) if i % 3 == 0)
    assert all(f"s_gate_{i}" in lg["gates"] for i in range(n) if i % 3 == 1)
    assert all(f"S-ISSUE-{i}" in texts for i in range(n) if i % 3 == 2)
    # gate 命令自身也写一条 log，故总日志数 = log 数 + gate 数
    assert len(lg["log"]) == n_log + n_gate
    assert len(lg["gates"]) == n_gate
    assert len(lg["issues"]) == n_issue
    ids = [i["id"] for i in lg["issues"]]
    assert len(set(ids)) == len(ids)                       # issue id 无重号
    assert sorted(int(x[1:]) for x in ids) == list(range(1, n_issue + 1))
    assert lg["next_issue_id"] == n_issue + 1
    assert elapsed < 30, f"50 并发耗时 {elapsed:.2f}s 超预算"


@pytest.mark.parametrize("args", [
    ["status"],
    ["log", "--stage", "writing", "--agent", "a", "--event", "e"],
    ["gate", "--name", "g", "--status", "PASS"],
    ["issue", "add", "--text", "x"],
    ["check-done"],
    ["advance", "--to", "writing"],
    ["next-round"],
])
def test_loopctl_uninitialized_gives_actionable_error(tmp_path, args):
    """未 init 时必须给可执行提示，而不是 12 行 Python traceback。

    多 agent 通过本工具交接，调用方（含 LLM）只读 stderr 尾行，
    裸 FileNotFoundError 分不清「忘了 init」和「GOAI_WORKSPACE 指错」。
    """
    ws = tmp_path / "never_init"
    ws.mkdir()
    r = _loopctl(ws, *args)
    assert r.returncode != 0
    assert "Traceback" not in r.stderr, r.stderr
    assert "账本不存在" in r.stderr
    assert "init --topic" in r.stderr
    assert str(ws) in r.stderr              # 回显当前 workspace，便于排查指错
    assert len(r.stderr.strip().splitlines()) <= 3


def test_loopctl_corrupt_ledger_gives_actionable_error(tmp_path):
    ws = tmp_path / "corrupt"
    (ws / "state").mkdir(parents=True)
    (ws / "state" / "ledger.json").write_text('{"topic": "x", ',
                                              encoding="utf-8")
    r = _loopctl(ws, "status")
    assert r.returncode != 0
    assert "Traceback" not in r.stderr, r.stderr
    assert "账本 JSON 已损坏" in r.stderr
    assert "init --force" in r.stderr


def test_loopctl_lock_released_after_sigkill(tmp_path):
    """持锁进程被 kill -9：flock 由内核释放，账本不被永久锁死。"""
    ws = tmp_path / "ws"
    ws.mkdir()
    assert _loopctl(ws, "init", "--topic", "kill9").returncode == 0
    lock = str(ws / "state" / "ledger.json.lock")

    hijack = (f"import fcntl\nlk = open({lock!r}, 'w')\n"
              "fcntl.flock(lk, fcntl.LOCK_EX)\n"
              "print('HELD', flush=True)\nimport time; time.sleep(600)\n")
    hij = subprocess.Popen([sys.executable, "-c", hijack],
                           stdout=subprocess.PIPE, text=True)
    assert hij.stdout.readline().strip() == "HELD"

    with pytest.raises(subprocess.TimeoutExpired):   # 锁真实生效 → 阻塞
        _loopctl(ws, "log", "--stage", "writing", "--agent", "blocked",
                 "--event", "x", "--detail", "SHOULD-BLOCK", timeout=3)

    hij.kill()
    hij.wait(timeout=10)

    t0 = time.monotonic()
    r = _loopctl(ws, "log", "--stage", "writing", "--agent", "recovered",
                 "--event", "after_kill", "--detail", "AFTER-KILL-9",
                 timeout=15)
    assert r.returncode == 0, r.stderr
    assert time.monotonic() - t0 < 5                 # 立刻恢复，无残留锁

    lg = json.loads((ws / "state" / "ledger.json").read_text(encoding="utf-8"))
    details = [e.get("detail") for e in lg["log"]]
    assert "AFTER-KILL-9" in details
    assert "SHOULD-BLOCK" not in details             # 被阻塞的写入没污染账本


# --------------------------------------------------------------------------
# parallel_run.sh 真实调度
# --------------------------------------------------------------------------

FAKE_CODEX = '''#!{python}
"""假 codex：记录 START/END 供并发度计算；prompt 里的 EXIT <n> 决定退出码。

prompt 含 HANG 时模拟「断网后无限重连」的真实卡死形态（不自行退出）。
"""
import fcntl, os, re, sys, time

TRACE = os.environ["FAKE_CODEX_TRACE"]
DRAIN = os.environ.get("FAKE_CODEX_DRAIN_STDIN") == "1"


def rec(event, label, extra=""):
    with open(TRACE, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write("%s\\t%.6f\\t%s\\t%s\\n" % (event, time.time(), label, extra))
        fcntl.flock(f, fcntl.LOCK_UN)


argv = sys.argv[1:]
if not argv or argv[0] != "exec":
    sys.exit(64)
prompt = argv[-1]
m = re.search(r"TASK (\\S+)", prompt)
label = m.group(1) if m else "unknown"
stolen = sys.stdin.read() if DRAIN else ""
rec("START", label, "stdin=%d" % len(stolen))
m_write = re.search(r"WRITE (\\S+)", prompt)
if m_write:
    os.makedirs(os.path.dirname(m_write.group(1)), exist_ok=True)
    with open(m_write.group(1), "w") as f:
        f.write("fresh artifact\\n")
if "HANG" in prompt:
    print("Reconnecting... waiting for network", flush=True)
    time.sleep(600)
time.sleep(float(os.environ.get("FAKE_CODEX_SLEEP", "0.8")))
rec("END", label)
m2 = re.search(r"EXIT (\\d+)", prompt)
sys.exit(int(m2.group(1)) if m2 else 0)
'''


def _fake_backend_dir(tmp_path, name="codex"):
    d = tmp_path / "fakebin"
    d.mkdir(exist_ok=True)
    p = d / name
    p.write_text(FAKE_CODEX.format(python=sys.executable), encoding="utf-8")
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return str(d)


def _tasks_file(tmp_path, rows, name="tasks.tsv"):
    p = tmp_path / name
    p.write_text("".join(f"{n}\t{pr}\n" for n, pr in rows), encoding="utf-8")
    return str(p)


def _run_parallel(tmp_path, tasks, *args, path_prefix=None, extra_env=None,
                  timeout=180):
    ws = tmp_path / "ws"
    ws.mkdir(exist_ok=True)
    env = {**os.environ, "GOAI_WORKSPACE": str(ws),
           "FAKE_CODEX_TRACE": str(tmp_path / "trace.log")}
    if path_prefix:
        env["PATH"] = f"{path_prefix}:{env['PATH']}"
    env.update(extra_env or {})
    (tmp_path / "trace.log").write_text("", encoding="utf-8")
    r = subprocess.run(["bash", PARALLEL_RUN, *args, tasks],
                       capture_output=True, text=True, env=env, timeout=timeout)
    return r, ws


def _peak_concurrency(trace_path):
    events = []
    for line in open(trace_path):
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 3:
            continue
        events.append((float(parts[1]), 1 if parts[0] == "START" else -1))
    events.sort(key=lambda x: (x[0], -x[1]))
    cur = peak = 0
    for _ts, delta in events:
        cur += delta
        peak = max(peak, cur)
    starts = sum(1 for _t, d in events if d == 1)
    return peak, starts


def test_parallel_run_enforces_jobs_cap(tmp_path):
    """--jobs 上限必须真实生效（macOS bash 3.2 无 wait -n，旧实现会全量并发）。"""
    tasks = _tasks_file(tmp_path, [
        ("t1", "TASK t1 EXIT 0"), ("t2", "TASK t2 EXIT 0"),
        ("t3", "TASK t3 EXIT 3"), ("t4", "TASK t4 EXIT 0"),
        ("t5", "TASK t5 EXIT 7"),
    ])
    r, ws = _run_parallel(tmp_path, tasks, "--backend", "codex", "--jobs", "2",
                          path_prefix=_fake_backend_dir(tmp_path))
    peak, starts = _peak_concurrency(tmp_path / "trace.log")
    assert starts == 5, f"应执行 5 个任务，实际 {starts}\n{r.stdout}"
    assert peak <= 2, f"并发上限失效：峰值 {peak} > 2\n{r.stdout}"

    logdir = next((ws / "state" / "parallel").iterdir())
    exits = {p.stem: p.read_text().strip() for p in logdir.glob("*.exit")}
    assert exits == {"t1": "0", "t2": "0", "t3": "3", "t4": "0", "t5": "7"}
    assert len(list(logdir.glob("*.log"))) == 5
    assert "FAIL  t3 (exit=3)" in r.stdout and "FAIL  t5 (exit=7)" in r.stdout
    assert r.stdout.count("PASS  ") == 3
    assert r.returncode == 1              # 有失败任务 → 整批非零


def test_parallel_run_child_stdin_isolated_from_tasks_file(tmp_path):
    """子进程 stdin 必须隔离：codex exec 会读 stdin，否则会吞掉后续任务行。"""
    tasks = _tasks_file(tmp_path, [(f"t{i}", f"TASK t{i} EXIT 0")
                                   for i in range(1, 6)])
    r, ws = _run_parallel(tmp_path, tasks, "--backend", "codex", "--jobs", "2",
                          path_prefix=_fake_backend_dir(tmp_path),
                          extra_env={"FAKE_CODEX_DRAIN_STDIN": "1",
                                     "FAKE_CODEX_SLEEP": "0.5"})
    _peak, starts = _peak_concurrency(tmp_path / "trace.log")
    assert starts == 5, f"任务被 stdin 吞掉：只执行了 {starts}/5\n{r.stdout}"
    stolen = [ln.split("\t")[3] for ln in
              open(tmp_path / "trace.log").read().splitlines()
              if ln.startswith("START")]
    assert set(stolen) == {"stdin=0"}, f"子进程读到了 tasks 文件内容: {stolen}"
    logdir = next((ws / "state" / "parallel").iterdir())
    assert len(list(logdir.glob("*.exit"))) == 5


def test_parallel_run_runs_last_line_without_trailing_newline(tmp_path):
    """末行缺换行符时不得丢任务（多数编辑器不补末尾换行）。

    旧实现：`while read` 在 EOF 前丢掉未终止的末行，该任务从未执行，
    汇总却只列前两个任务并以 0 退出 —— 静默少跑，无任何警告。
    """
    p = tmp_path / "tasks.tsv"
    p.write_text("a\tTASK a EXIT 0\nb\tTASK b EXIT 0\nc\tTASK c EXIT 0",
                 encoding="utf-8")          # 故意不写末尾 \n
    r, ws = _run_parallel(tmp_path, str(p), "--backend", "codex", "--jobs", "3",
                          path_prefix=_fake_backend_dir(tmp_path))
    _peak, starts = _peak_concurrency(tmp_path / "trace.log")
    assert starts == 3, f"末行任务被吞：只执行了 {starts}/3\n{r.stdout}"
    logdir = next((ws / "state" / "parallel").iterdir())
    assert {q.stem for q in logdir.glob("*.exit")} == {"a", "b", "c"}
    assert "任务数: 3" in r.stdout
    assert r.returncode == 0


def test_parallel_run_rejects_duplicate_task_names(tmp_path):
    """重名任务必须启动前拒绝：否则并发写同一 .exit，失败被吞成假绿。

    旧实现实测：dup 两行分别 exit 9 / exit 0，汇总只剩一行 PASS dup，
    整批退出 0 —— 真实失败完全消失。
    """
    tasks = _tasks_file(tmp_path, [("dup", "TASK dup1 EXIT 9"),
                                   ("dup", "TASK dup2 EXIT 0"),
                                   ("solo", "TASK solo EXIT 0")])
    r, ws = _run_parallel(tmp_path, tasks, "--backend", "codex", "--jobs", "2",
                          path_prefix=_fake_backend_dir(tmp_path))
    assert r.returncode == 2, f"{r.stdout}\n{r.stderr}"
    assert "任务名重复" in r.stderr and "dup" in r.stderr
    parallel = ws / "state" / "parallel"
    assert not (list(parallel.rglob("*.log")) if parallel.exists() else []), \
        "预检失败却仍起了任务"


def test_parallel_run_rejects_slash_in_task_name(tmp_path):
    """任务名带 / 会让日志落到不存在的子目录，退出码丢失 → 启动前拒绝。

    旧实现实测：lit/diffusion 真实以 exit 1 结束，却因 .exit 写不进去
    而从汇总里消失，整批仍报 rc=0。
    """
    tasks = _tasks_file(tmp_path, [("lit/diffusion", "TASK a EXIT 0"),
                                   ("ok_task", "TASK b EXIT 0")])
    r, _ws = _run_parallel(tmp_path, tasks, "--backend", "codex",
                           "--jobs", "2",
                           path_prefix=_fake_backend_dir(tmp_path))
    assert r.returncode == 2, f"{r.stdout}\n{r.stderr}"
    assert "任务名不能包含 /" in r.stderr


def test_parallel_run_reports_task_whose_exit_never_landed(tmp_path):
    """汇总必须与「已启动任务」对账：退出码没落盘的任务要显式报失败。

    取证用超长任务名（文件名过长 → .exit 写失败）。旧实现靠 glob *.exit
    拼汇总，这类任务凭空消失且整批 rc=0。
    """
    long_name = "L" * 300
    tasks = _tasks_file(tmp_path, [(long_name, "TASK long EXIT 0"),
                                   ("short", "TASK short EXIT 0")])
    r, _ws = _run_parallel(tmp_path, tasks, "--backend", "codex",
                           "--jobs", "2",
                           path_prefix=_fake_backend_dir(tmp_path))
    assert "退出码未落盘" in r.stdout, r.stdout
    assert "PASS  short" in r.stdout
    assert "任务数: 2  失败: 1" in r.stdout
    assert r.returncode == 1, "任务未收尾却报整批成功"


def test_parallel_run_timeout_kills_hung_backend(tmp_path):
    """RUNNER_TIMEOUT 必须能救回卡死的后端，且不留孤儿进程。

    实测依据：真实 codex 断网后只无限打印 "Reconnecting... waiting for
    network"，7 分钟不退出；无超时看护时整批 wait 永久挂死。
    """
    tasks = _tasks_file(tmp_path, [("hang", "TASK HANG forever"),
                                   ("normal", "TASK normal EXIT 0")])
    t0 = time.monotonic()
    r, ws = _run_parallel(tmp_path, tasks, "--backend", "codex", "--jobs", "2",
                          path_prefix=_fake_backend_dir(tmp_path),
                          extra_env={"RUNNER_TIMEOUT": "3"}, timeout=90)
    elapsed = time.monotonic() - t0
    assert elapsed < 45, f"超时看护未生效，整批耗时 {elapsed:.1f}s"
    logdir = next((ws / "state" / "parallel").iterdir())
    exits = {q.stem: q.read_text().strip() for q in logdir.glob("*.exit")}
    assert exits == {"hang": "124", "normal": "0"}, exits
    assert "已强杀" in (logdir / "hang.stderr.log").read_text(errors="replace")
    assert r.returncode == 1
    # 孤儿检查：卡死进程必须已被回收
    ps = subprocess.run(["ps", "-ax", "-o", "command"],
                        capture_output=True, text=True, timeout=30)
    assert "TASK HANG forever" not in ps.stdout


def test_parallel_run_accepts_fresh_artifact_after_process_timeout(tmp_path):
    """产物已完整写出但收尾卡死时，保留 process=124，同时以 WARN 放行。"""
    artifact = tmp_path / "completed.md"
    tasks = tmp_path / "tasks.tsv"
    tasks.write_text(
        f"writer\tTASK writer WRITE {artifact} HANG\t{artifact}\n",
        encoding="utf-8",
    )
    r, ws = _run_parallel(
        tmp_path,
        str(tasks),
        "--backend", "codex", "--jobs", "1",
        path_prefix=_fake_backend_dir(tmp_path),
        extra_env={"RUNNER_TIMEOUT": "3"},
        timeout=90,
    )
    logdir = next((ws / "state" / "parallel").iterdir())
    assert artifact.read_text() == "fresh artifact\n"
    assert (logdir / "writer.process_exit").read_text().strip() == "124"
    assert (logdir / "writer.exit").read_text().strip() == "0"
    assert (logdir / "writer.status").read_text().strip() == \
        "WARN_ARTIFACT_PASS_AFTER_TIMEOUT"
    assert "WARN  writer" in r.stdout
    assert r.returncode == 0


def test_parallel_run_dependencies_order_and_block(tmp_path):
    """第四列形成真实 ready gate；失败依赖不得启动消费者。"""
    tasks = tmp_path / "tasks.tsv"
    tasks.write_text(
        "producer\tTASK producer EXIT 0\t\t\n"
        "consumer\tTASK consumer EXIT 0\t\tproducer\n"
        "failed\tTASK failed EXIT 7\t\t\n"
        "blocked\tTASK blocked EXIT 0\t\tfailed\n",
        encoding="utf-8",
    )
    r, ws = _run_parallel(
        tmp_path,
        str(tasks),
        "--backend", "codex", "--jobs", "4",
        path_prefix=_fake_backend_dir(tmp_path),
    )
    events = [
        line.split("\t")
        for line in (tmp_path / "trace.log").read_text().splitlines()
    ]
    producer_end = next(
        float(row[1]) for row in events
        if row[0] == "END" and row[2] == "producer"
    )
    consumer_start = next(
        float(row[1]) for row in events
        if row[0] == "START" and row[2] == "consumer"
    )
    assert consumer_start >= producer_end
    assert not any(row[0] == "START" and row[2] == "blocked" for row in events)
    logdir = next((ws / "state" / "parallel").iterdir())
    assert (logdir / "blocked.exit").read_text().strip() == "4"
    assert (logdir / "blocked.status").read_text().strip() == "BLOCKED_DEPENDENCY"
    assert "依赖任务失败" in (logdir / "blocked.validation.log").read_text()
    assert r.returncode == 1


def test_parallel_run_rejects_forward_dependency(tmp_path):
    tasks = tmp_path / "tasks.tsv"
    tasks.write_text(
        "consumer\tTASK consumer EXIT 0\t\tproducer\n"
        "producer\tTASK producer EXIT 0\t\t\n",
        encoding="utf-8",
    )
    r, _ws = _run_parallel(
        tmp_path,
        str(tasks),
        "--backend", "codex", "--jobs", "2",
        path_prefix=_fake_backend_dir(tmp_path),
    )
    assert r.returncode == 2
    assert "按拓扑顺序" in r.stderr


def test_parallel_run_rejects_stale_expected_artifact(tmp_path):
    """第三列产物若只是沿用旧文件，后端 exit=0 也必须改判 exit=3。"""
    artifact = tmp_path / "artifact.md"
    artifact.write_text("old\n", encoding="utf-8")
    tasks = tmp_path / "tasks.tsv"
    tasks.write_text(f"stale\tTASK stale EXIT 0\t{artifact}\n", encoding="utf-8")
    r, ws = _run_parallel(tmp_path, str(tasks), "--backend", "codex", "--jobs", "1",
                          path_prefix=_fake_backend_dir(tmp_path))
    logdir = next((ws / "state" / "parallel").iterdir())
    assert (logdir / "stale.exit").read_text().strip() == "3"
    assert "本轮未更新" in (logdir / "stale.validation.log").read_text()
    assert r.returncode == 1


def test_parallel_run_accepts_fresh_or_existence_only_artifact(tmp_path):
    fresh = tmp_path / "fresh.md"
    existing = tmp_path / "existing.md"
    existing.write_text("pre-existing\n", encoding="utf-8")
    tasks = tmp_path / "tasks.tsv"
    tasks.write_text(
        f"fresh\tTASK fresh WRITE {fresh} EXIT 0\t{fresh}\n"
        f"existing\tTASK existing EXIT 0\t={existing}\n",
        encoding="utf-8",
    )
    r, ws = _run_parallel(tmp_path, str(tasks), "--backend", "codex", "--jobs", "2",
                          path_prefix=_fake_backend_dir(tmp_path))
    logdir = next((ws / "state" / "parallel").iterdir())
    exits = {p.stem: p.read_text().strip() for p in logdir.glob("*.exit")}
    assert exits == {"fresh": "0", "existing": "0"}
    assert fresh.read_text() == "fresh artifact\n"
    assert r.returncode == 0


def test_parallel_run_rejects_bad_runner_timeout(tmp_path):
    tasks = _tasks_file(tmp_path, [("t1", "TASK t1 EXIT 0")])
    r, _ws = _run_parallel(tmp_path, tasks, "--backend", "codex",
                           path_prefix=_fake_backend_dir(tmp_path),
                           extra_env={"RUNNER_TIMEOUT": "3s"})
    assert r.returncode == 2
    assert "RUNNER_TIMEOUT 需为非负整数秒" in r.stderr


def test_parallel_run_missing_backend_exits_2(tmp_path):
    """后端二进制不在 PATH：必须 exit 2 直接退出，不许空跑一批再报 0 失败。"""
    tasks = _tasks_file(tmp_path, [("t1", "TASK t1 EXIT 0")])
    ws = tmp_path / "ws"
    ws.mkdir(exist_ok=True)
    r = subprocess.run(["bash", PARALLEL_RUN, "--backend", "codex",
                        "--jobs", "2", tasks],
                       capture_output=True, text=True, timeout=60,
                       env={"PATH": "/usr/bin:/bin", "HOME": os.environ["HOME"],
                            "GOAI_WORKSPACE": str(ws)})
    assert r.returncode == 2, f"rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    assert "找不到 codex" in r.stderr
    assert "alias" in r.stderr                     # 提示 alias 在非交互 shell 不可见
    parallel_dir = ws / "state" / "parallel"
    spawned = list(parallel_dir.rglob("*.log")) if parallel_dir.exists() else []
    assert not spawned, f"预检失败却仍然起了任务: {spawned}"


@pytest.mark.parametrize("args,rows,expect_rc,expect_msg", [
    (["--backend", "gpt5"], [("t1", "TASK t1")], 2, "未知 backend"),
    (["--jobs", "abc"], [("t1", "TASK t1")], 2, "需为正整数"),
    ([], [], 2, "没有可执行任务"),
    ([], [("# 注释", "")], 2, "没有可执行任务"),
])
def test_parallel_run_error_paths(tmp_path, args, rows, expect_rc, expect_msg):
    tasks = _tasks_file(tmp_path, rows)
    r, _ws = _run_parallel(tmp_path, tasks, *args,
                           path_prefix=_fake_backend_dir(tmp_path))
    assert r.returncode == expect_rc, f"{r.stdout}\n{r.stderr}"
    assert expect_msg in (r.stdout + r.stderr)


def test_parallel_run_missing_tasks_file_and_no_args(tmp_path):
    fake = _fake_backend_dir(tmp_path)
    env = {**os.environ, "PATH": f"{fake}:{os.environ['PATH']}",
           "GOAI_WORKSPACE": str(tmp_path / "ws")}
    r1 = subprocess.run(["bash", PARALLEL_RUN, str(tmp_path / "nope.tsv")],
                        capture_output=True, text=True, env=env, timeout=60)
    assert r1.returncode == 2 and "tasks 文件不存在" in r1.stderr
    r2 = subprocess.run(["bash", PARALLEL_RUN], capture_output=True, text=True,
                        env=env, timeout=60)
    assert r2.returncode == 2 and "用法" in r2.stderr


def test_parallel_run_skips_row_without_prompt(tmp_path):
    """缺提示词列只应跳过该行（旧实现在 bash 3.2 下 set -u 崩溃）。"""
    p = tmp_path / "tasks.tsv"
    p.write_text("noprompt\ngood\tTASK good EXIT 0\n", encoding="utf-8")
    r, ws = _run_parallel(tmp_path, str(p), "--backend", "codex",
                          "--jobs", "2",
                          path_prefix=_fake_backend_dir(tmp_path))
    assert "缺少提示词列" in r.stderr
    assert "unbound variable" not in (r.stdout + r.stderr)
    assert r.returncode == 0                        # 剩下那个任务成功
    logdir = next((ws / "state" / "parallel").iterdir())
    assert [p.stem for p in logdir.glob("*.exit")] == ["good"]


def test_parallel_run_claude_backend_precheck_in_clean_path(tmp_path):
    """claude 后端预检：净 PATH（launchd/cron 口径）下必须 exit 2 并提示 alias。

    本机实测：claude 在登录 shell 的 PATH 里是真实二进制
    （~/.nvm/.../bin/claude 与 /opt/homebrew/bin/claude），
    zsh alias 只是附加参数，所以「alias 导致非交互不可用」在本机不复现；
    但净 PATH 环境（launchd/cron）确实找不到，预检必须挡住。
    """
    tasks = _tasks_file(tmp_path, [("t1", "TASK t1 EXIT 0")])
    ws = tmp_path / "ws"
    ws.mkdir(exist_ok=True)
    r = subprocess.run(["bash", PARALLEL_RUN, "--backend", "claude",
                        "--jobs", "1", tasks],
                       capture_output=True, text=True, timeout=60,
                       env={"PATH": "/usr/bin:/bin", "HOME": os.environ["HOME"],
                            "GOAI_WORKSPACE": str(ws)})
    assert r.returncode == 2, f"rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    assert "找不到 claude" in r.stderr
    assert "alias" in r.stderr
    parallel = ws / "state" / "parallel"
    assert not (list(parallel.rglob("*.log")) if parallel.exists() else [])


@pytest.mark.skipif(not shutil.which("claude"),
                    reason="claude CLI 不在 PATH")
def test_real_claude_backend_end_to_end(tmp_path):
    """真实 claude CLI 最小任务；未登录/网络不可用时 SKIP 并记录原因。

    脚本调用的是 PATH 上的二进制，交互式 zsh alias 的
    `--effort max --model fable` 不会生效；需要同款参数请用 RUNNER_ARGS。
    """
    tasks = _tasks_file(tmp_path, [("live_ok", "Reply with exactly: LIVE_TEST_OK")])
    ws = tmp_path / "ws"
    ws.mkdir(exist_ok=True)
    try:
        r = subprocess.run(["bash", PARALLEL_RUN, "--backend", "claude",
                            "--jobs", "1", tasks],
                           capture_output=True, text=True, timeout=180,
                           env={**os.environ, "GOAI_WORKSPACE": str(ws)})
    except subprocess.TimeoutExpired:
        pytest.skip("真实 claude 180s 未返回（网络/登录不可用）")
    logs = list((ws / "state" / "parallel").rglob("*.log"))
    body = logs[0].read_text(errors="replace") if logs else ""
    if re.search(r"Not logged in|Please run /login|Invalid API key|"
                 r"credit balance|rate limit", body, re.I):
        # 失败也必须被如实记账，不能静默变绿
        assert r.returncode == 1, f"未登录却报整批成功: {r.stdout}"
        assert "FAIL  live_ok" in r.stdout
        pytest.skip(f"真实 claude 后端未登录/不可用: {body.strip()[:120]}")
    if r.returncode != 0:
        pytest.skip(f"真实 claude 后端不可用: {body.strip()[:200]}")
    assert "LIVE_TEST_OK" in body


@pytest.mark.skipif(not shutil.which("codex"),
                    reason="真实 codex CLI 不在 PATH")
def test_real_codex_backend_end_to_end(tmp_path):
    """真实 codex CLI 最小任务端到端；需要登录+网络，不可用时 SKIP。

    防伪：PATH 上可能有测试用的假 codex（本文件就注入过），
    所以先用 --version 认身份，再要求日志里出现真实 ``--json`` 事件。
    JSON 模式本来就不输出交互式 ``OpenAI Codex`` banner，不能拿 banner
    当健康条件；提示词本身又含 LIVE_TEST_OK，故也不能只做 token 断言。
    """
    ver = subprocess.run(["codex", "--version"], capture_output=True,
                         text=True, timeout=60)
    if "codex-cli" not in (ver.stdout + ver.stderr):
        pytest.skip(f"PATH 上的 codex 不是真实 CLI: {shutil.which('codex')}")

    tasks = _tasks_file(tmp_path, [("live_ok", "Reply with exactly: LIVE_TEST_OK")])
    ws = tmp_path / "ws"
    ws.mkdir(exist_ok=True)
    try:
        r = subprocess.run(["bash", PARALLEL_RUN, "--backend", "codex",
                            "--jobs", "1", tasks],
                           capture_output=True, text=True, timeout=180,
                           env={**os.environ, "GOAI_WORKSPACE": str(ws)})
    except subprocess.TimeoutExpired:
        pytest.skip("真实 codex 180s 未返回（网络/登录不可用）")
    logs = list((ws / "state" / "parallel").rglob("*.jsonl"))
    body = logs[0].read_text(errors="replace") if logs else ""
    events = []
    for line in body.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and isinstance(event.get("type"), str):
            events.append(event)
    event_types = {event["type"] for event in events}
    finals = list((ws / "state" / "parallel").rglob("*.final.md"))
    final_body = finals[0].read_text(errors="replace") if finals else ""
    unavailable = re.search(r"Not logged in|tls handshake|error sending request|"
                            r"waiting for network|Reconnecting|401|403",
                            body + final_body)
    if "thread.started" not in event_types:
        pytest.skip(f"未见真实 codex JSON 事件，后端不可用: {body[:200]}")
    if r.returncode != 0 or "LIVE_TEST_OK" not in final_body:
        if unavailable:
            pytest.skip(f"真实 codex 后端不可用（登录/网络）: {(body + final_body)[:200]}")
        pytest.fail(
            f"codex 返回 {r.returncode}，final={final_body[:200]!r}，"
            f"日志片段: {body[:500]}"
        )
    assert "turn.completed" in event_types
