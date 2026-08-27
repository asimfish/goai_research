"""引用核查环节真实网络实测（B_refcheck）。

覆盖：
1. MCP stdio 协议层（真实起 server/refcheck_server.py 子进程）
2. verify_entry 判定矩阵（真实论文 + 人为损坏混合，10 条）
3. verify_bib_file 整文件核查（3 条混合，验证汇总与落盘）
4. deep_audit_info 结构
5. 三个稿侧闸门（bib_guard / tex_guard / bank_check）真实规模样例
6. 错误路径（空 bib / 缺右括号 / 不存在路径）结构化不崩溃

跑法：
  .venv/bin/python -m pytest -m live tests/live/test_live_refcheck.py -v

网络预算：每次全量运行 = 矩阵 10 条 + 整文件 3 条 = 13 次条目核查
（每条打 Crossref/OpenAlex/arXiv/DBLP 中的 1-3 个源，server/core/http.py
自带同主机 1s 节流与 429 有界重试）。矩阵结果落盘
$GOAI_WORKSPACE/artifacts/matrix_results.jsonl 供报告引用。
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.live

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import _fixtures as fx  # noqa: E402

PY = sys.executable
SERVER = os.path.join(ROOT, "server", "refcheck_server.py")
WS = os.environ.get("GOAI_WORKSPACE") or os.path.join(
    ROOT, "workspace_live", "refcheck")
ART = os.path.join(WS, "artifacts")
FIX = os.path.join(WS, "fixtures")
GATES = os.path.join(WS, "gates")
SCRATCH = os.path.join(WS, "scratch")
MATRIX_JSONL = os.path.join(ART, "matrix_results.jsonl")

for _d in (ART, FIX, GATES, SCRATCH):
    os.makedirs(_d, exist_ok=True)


# ---------- MCP stdio 驱动 ----------

async def _mcp_roundtrip(calls: list[tuple[str, dict]],
                         timeout_s: float = 180.0) -> list[dict]:
    """真实起 stdio server，一个会话内顺序调用工具，返回解析后的 JSON 列表。"""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command=PY, args=[SERVER],
        env={**os.environ, "GOAI_WORKSPACE": WS},
        cwd=SCRATCH,  # 故意不用仓库根：默认产物路径不许依赖 server CWD
    )
    out: list[dict] = []
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for tool, args in calls:
                # mcp 2.x: read_timeout_seconds 为秒数 float（1.x 是 timedelta）
                res = await session.call_tool(
                    tool, args, read_timeout_seconds=timeout_s)
                assert not res.is_error, f"{tool} 工具层报错: {res}"
                assert res.content and res.content[0].type == "text"
                out.append(json.loads(res.content[0].text))
    return out


def mcp_call(tool: str, args: dict, timeout_s: float = 180.0) -> dict:
    return asyncio.run(_mcp_roundtrip([(tool, args)], timeout_s))[0]


def _run_cli(tool: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, os.path.join(ROOT, "tools", tool), *map(str, args)],
        capture_output=True, text=True, cwd=ROOT)


# ---------- 1. MCP stdio 协议层 ----------

def test_stdio_handshake_and_tool_surface():
    async def _probe():
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        params = StdioServerParameters(
            command=PY, args=[SERVER],
            env={**os.environ, "GOAI_WORKSPACE": WS}, cwd=SCRATCH)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                tools = await session.list_tools()
                return init, tools
    init, tools = asyncio.run(_probe())
    assert init.server_info.name == "goai-refcheck"
    names = {t.name for t in tools.tools}
    assert names == {"verify_entry", "verify_bib_file", "deep_audit_info"}
    by_name = {t.name: t for t in tools.tools}
    assert "bibtex_entry" in json.dumps(by_name["verify_entry"].input_schema)
    assert by_name["verify_entry"].description


# ---------- 4. deep_audit_info ----------

def test_deep_audit_info_structure():
    r = mcp_call("deep_audit_info", {})
    assert isinstance(r["available"], bool)
    assert isinstance(r["path"], str) and r["path"]
    assert isinstance(r["usage"], list) and r["usage"]
    assert "when_to_use" in r
    if r["available"]:  # 可用时 usage 必须是可执行指引（含 citationctl 步骤）
        assert any("citationctl" in u for u in r["usage"])
    else:
        assert any("super_ref" in u for u in r["usage"])


# ---------- 6. 错误路径（零网络） ----------

def test_error_verify_entry_unparseable():
    assert mcp_call("verify_entry", {"bibtex_entry": ""})["verdict"] == "ERROR"
    r = mcp_call("verify_entry", {"bibtex_entry": "not bibtex at all"})
    assert r["verdict"] == "ERROR" and r["error"]


def test_error_bibfile_missing_empty_broken():
    empty = os.path.join(FIX, "empty.bib")
    open(empty, "w").close()
    truncated = os.path.join(FIX, "truncated.bib")
    with open(truncated, "w", encoding="utf-8") as f:
        f.write("@article{broken2026")  # 缺右括号且无字段，解析不出条目
    rs = asyncio.run(_mcp_roundtrip([
        ("verify_bib_file", {"bib_path": os.path.join(FIX, "no_such.bib")}),
        ("verify_bib_file", {"bib_path": empty}),
        ("verify_bib_file", {"bib_path": truncated}),
    ]))
    assert rs[0]["ok"] is False and "不存在" in rs[0]["error"]
    assert rs[1]["ok"] is False and "空" in rs[1]["error"]
    assert rs[2]["ok"] is False  # 坏文件同走 fail-closed 结构化报错


def test_broken_brace_parse_keeps_value_intact():
    """缺右括号的条目：解析容错且不丢尾字符（修复回归锚点）。"""
    from server.core import bibtex as bib
    e = bib.parse_bibtex("@article{broken2026,\n  title = {Half open sentence")
    assert e and e[0]["fields"]["title"] == "Half open sentence"


# ---------- 2. verify_entry 判定矩阵（真实网络） ----------

@pytest.mark.parametrize("case", fx.MATRIX, ids=[m["id"] for m in fx.MATRIX])
def test_verdict_matrix(case):
    r = mcp_call("verify_entry", {"bibtex_entry": case["bibtex"]})
    row = {"id": case["id"], "note": case["note"],
           "expect_verdicts": sorted(case["expect_verdicts"]),
           "expect_issues": case["expect_issues"],
           "actual_verdict": r.get("verdict"),
           "actual_issues": [(i.get("axis"), i.get("type"))
                             for i in r.get("issues", [])],
           "raw": r}
    with open(MATRIX_JSONL, "a", encoding="utf-8") as f:  # 断言前先落盘
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

    assert r.get("verdict") in case["expect_verdicts"], (
        f"{case['id']} 期望 {case['expect_verdicts']} 实得 {r.get('verdict')}\n"
        f"{json.dumps(r, ensure_ascii=False, indent=1)[:1500]}")
    got = {(i.get("axis"), i.get("type")) for i in r.get("issues", [])}
    for need in case["expect_issues"]:
        assert tuple(need) in got, (
            f"{case['id']} 缺少期望问题 {need}，实得 {sorted(got)}\n"
            f"{json.dumps(r, ensure_ascii=False, indent=1)[:1500]}")
    if r.get("verdict") in ("FIX", "MISMATCH") and case["id"] != "M8_doi_points_elsewhere":
        assert r.get("suggested_bibtex"), f"{case['id']} FIX/MISMATCH 应给修正建议"


# ---------- 3. verify_bib_file 整文件核查（真实网络） ----------

def test_verify_bib_file_mixed_summary_and_artifacts():
    bib_path = os.path.join(FIX, "mixed.bib")
    with open(bib_path, "w", encoding="utf-8") as f:
        f.write(fx.mixed_bib_text())
    # 不传 out_dir：验证默认产物锚定 $GOAI_WORKSPACE/state 而非 server CWD
    r = mcp_call("verify_bib_file", {"bib_path": bib_path}, timeout_s=420)
    assert r["total"] == 3
    assert r["counts"]["PASS"] == 1, r["counts"]
    assert r["counts"]["MISMATCH"] == 1, r["counts"]
    assert r["counts"]["UNVERIFIED"] == 1, r["counts"]
    assert r["gate"] == "FAIL"
    expected_dir = os.path.join(WS, "state")
    assert os.path.dirname(r["report_json"]) == expected_dir, r["report_json"]
    audit = json.load(open(r["report_json"], encoding="utf-8"))
    assert audit["total"] == 3 and len(audit["per_entry"]) == 3
    assert audit["counts"] == r["counts"]
    md = open(r["report_md"], encoding="utf-8").read()
    assert "he2016deep_fakeauthor" in md and "marlowe2024recursive" in md
    assert "## PASS:" not in md  # PASS 条目不进人读报告（只列问题条目）


# ---------- 5. 三个稿侧闸门（真实规模样例，离线） ----------

@pytest.fixture(scope="module")
def gate_project():
    return fx.write_gate_project(GATES)


def test_bib_guard_realistic_numbers(gate_project):
    p = gate_project
    r = _run_cli("bib_guard.py", p["drafts"], p["bib"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "引用调用: 24" in r.stdout and "去重 key: 12" in r.stdout, r.stdout
    assert "bib 条目: 12" in r.stdout and "整合率: 100%" in r.stdout, r.stdout
    density = float(r.stdout.split("引用密度:")[1].split("次/千词")[0])
    assert 20 <= density <= 60, f"600+ 词 24 次引用的密度应在合理带内: {density}"

    # 未定义 key 阻塞（真实文本里混入一个幻觉 key）
    undef_dir = os.path.join(GATES, "drafts_undef")
    os.makedirs(undef_dir, exist_ok=True)
    with open(os.path.join(p["sections"], "01_intro.tex"), encoding="utf-8") as f:
        intro = f.read()
    with open(os.path.join(undef_dir, "01_intro.tex"), "w", encoding="utf-8") as f:
        f.write(intro + "\nGhost claims \\cite{ghost2026nonexistent} here.\n")
    r2 = _run_cli("bib_guard.py", undef_dir, p["bib"])
    assert r2.returncode == 1 and "ghost2026nonexistent" in r2.stdout
    assert "未定义引用" in r2.stdout

    # 整合率阻塞（库里塞 3 条孤儿 → 12/15 = 80% < 90%）
    fat_bib = os.path.join(GATES, "fat.bib")
    orphans = "\n".join(
        f"@misc{{orphan{i},\n  title = {{Orphan {i}}},\n  author = {{A B}},\n"
        f"  year = {{2025}}\n}}" for i in range(3))
    with open(fat_bib, "w", encoding="utf-8") as f:
        f.write(fx.GATES_BIB + "\n" + orphans + "\n")
    r3 = _run_cli("bib_guard.py", p["drafts"], fat_bib)
    assert r3.returncode == 1 and "整合率 80%" in r3.stdout, r3.stdout


def test_tex_guard_realistic(gate_project):
    p = gate_project
    r = _run_cli("tex_guard.py", p["drafts"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "labels: 3" in r.stdout and "refs: 3" in r.stdout, r.stdout
    assert r.stdout.rstrip().endswith("PASS")

    r2 = _run_cli("tex_guard.py", p["broken"])
    assert r2.returncode == 1
    for frag in ("占位残留", "99_missing", "ghost_figure", "sec:nowhere"):
        assert frag in r2.stdout, f"缺 {frag}\n{r2.stdout}"
    assert ("未闭合" in r2.stdout) or ("环境错配" in r2.stdout), r2.stdout


def test_bank_check_realistic(gate_project):
    p = gate_project
    r = _run_cli("bank_check.py", p["bank_ok"], p["bib"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "bank 条目: 7" in r.stdout and "近三年占比: 86%" in r.stdout, r.stdout

    r2 = _run_cli("bank_check.py", p["bank_bad"], p["bib"])
    assert r2.returncode == 1
    for frag in ("ghost2030survey", "强度", "过短", "近三年"):
        assert frag in r2.stdout, f"缺 {frag}\n{r2.stdout}"

    r3 = _run_cli("bank_check.py", p["bank_ok"], p["bib"],
                  "--target-cites", "10")
    assert r3.returncode == 1 and "候选量 7 < 目标 10" in r3.stdout, r3.stdout


def test_cli_missing_paths_structured(gate_project):
    p = gate_project
    r = _run_cli("bib_guard.py", p["drafts"], "/nonexistent/refs.bib")
    assert r.returncode != 0 and "未找到 bib 文件" in (r.stdout + r.stderr)
    assert "Traceback" not in r.stderr
    r2 = _run_cli("bank_check.py", "/nonexistent/bank.md", p["bib"])
    assert r2.returncode != 0 and "未找到 citation bank" in (r2.stdout + r2.stderr)
    assert "Traceback" not in r2.stderr
    r3 = _run_cli("tex_guard.py", "/nonexistent_dir")
    assert r3.returncode != 0 and "未找到 .tex 文件" in (r3.stdout + r3.stderr)
    assert "Traceback" not in r3.stderr


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v", "-m", "live"]))
