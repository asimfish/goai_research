"""litsearch 实测回归（真实网络 / 真实 MCP stdio）。

跑法：.venv/bin/python -m pytest -m live tests/live/test_live_litsearch.py -v
礼貌预算：全套 ≤ 每源 3 次查询；S2 无 key 时 429/500 属已知限流，相关断言容忍降级。
"""
import asyncio
import json
import os
import subprocess
import sys
import textwrap

import pytest

pytestmark = pytest.mark.live

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402


def _params(workspace: str) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(ROOT, "server", "litsearch_server.py")],
        env={**os.environ, "GOAI_WORKSPACE": workspace,
             "GOAI_EMAIL": "goai-livetest@example.com"},
        cwd=workspace,
    )


def mcp_calls(workspace: str, calls: list[tuple[str, dict]]) -> list[dict]:
    """起真实 stdio server，顺序调用工具，返回解析后的 JSON 列表。"""
    async def _run():
        out = []
        async with stdio_client(_params(workspace)) as (r, w):
            async with ClientSession(r, w) as s:
                await s.initialize()
                for name, args in calls:
                    res = await s.call_tool(name, args)
                    assert not getattr(res, "is_error", False), \
                        f"{name} 协议层报错: {res.content}"
                    out.append(json.loads(res.content[0].text))
        return out
    return asyncio.run(_run())


REQUIRED_FIELDS = ("title", "authors", "year", "doi", "arxiv_id",
                   "url", "citation_count", "sources")


# ---------- 协议层 + arXiv 检索 ----------

def test_mcp_stdio_search_arxiv(tmp_path):
    (res,) = mcp_calls(str(tmp_path), [
        ("search_papers", {"query": "retrieval augmented generation",
                           "sources": "arxiv", "limit_per_source": 5}),
    ])
    assert res["total"] >= 3, res
    assert not res["errors"]
    for p in res["papers"]:
        for f in REQUIRED_FIELDS:
            assert f in p, f"record 缺字段 {f}: {p.keys()}"
        assert p["title"] and p["authors"] and p["arxiv_id"]
        assert p["sources"] == ["arxiv"]
        # 修复回归：作者名不得带首尾空白
        assert all(a == a.strip() for a in p["authors"]), p["authors"]


# ---------- lookup：arXiv 代发 DOI / arXiv id / 坏 DOI ----------

def test_lookup_arxiv_datacite_doi(tmp_path):
    """修复回归：10.48550/arXiv.X 此前 found=False（S2/OpenAlex 都不认）。"""
    (res,) = mcp_calls(str(tmp_path), [
        ("lookup", {"identifier": "10.48550/arXiv.1706.03762"}),
    ])
    assert res["found"] is True
    rec = res["records"][0]
    assert rec["title"] == "Attention Is All You Need"
    assert rec["arxiv_id"] == "1706.03762"
    assert len(rec["authors"]) == 8


def test_lookup_bad_doi_structured(tmp_path):
    (res,) = mcp_calls(str(tmp_path), [
        ("lookup", {"identifier": "10.9999/goai-nonexistent-doi-live"}),
    ])
    assert res == {"identifier": "10.9999/goai-nonexistent-doi-live",
                   "found": False, "records": []}


# ---------- snowball：S2 主路 + OpenAlex 兜底 ----------

def test_snowball_real_citations(tmp_path):
    """ResNet DOI 滚雪球：S2 可用走 S2；S2 限流则 OpenAlex 兜底，总之要拿到真实被引。"""
    (res,) = mcp_calls(str(tmp_path), [
        ("snowball", {"seed": "10.1109/CVPR.2016.90",
                      "direction": "citations", "limit": 5}),
    ])
    assert len(res["citations"]) >= 3, res
    top = res["citations"][0]
    assert top["title"] and "sources" not in top  # snowball 返回原始 record（含 source）
    if res["errors"]:  # S2 降级时必须有兜底说明
        assert "fallback" in res, res


# ---------- download_pdf ----------

def test_download_pdf_magic_bytes(tmp_path):
    pdf_dir = str(tmp_path / "pdfs")
    (res,) = mcp_calls(str(tmp_path), [
        ("download_pdf", {"url": "1706.03762",
                          "filename": "vaswani2017attention", "out_dir": pdf_dir}),
    ])
    assert res["ok"] is True and res["bytes"] > 100_000
    path = os.path.join(pdf_dir, "vaswani2017attention.pdf")
    assert os.path.exists(path)
    with open(path, "rb") as f:
        assert f.read(5) == b"%PDF-"


# ---------- 库链路（网络仅 1 次 openalex 检索） ----------

def test_library_chain(tmp_path):
    lib = str(tmp_path / "papers.jsonl")
    bib_path = str(tmp_path / "references.bib")
    search, saved, saved_again, exported, coverage = mcp_calls(str(tmp_path), [
        ("search_papers", {"query": "diffusion model image synthesis",
                           "sources": "openalex", "limit_per_source": 5}),
        # save/export/coverage 用固定 papers_json（可复现），与 search 结果独立
        ("save_to_library", {"papers_json": json.dumps({"papers": [
            {"source": "openalex", "title": "Deep Residual Learning for Image Recognition",
             "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
             "year": 2016, "doi": "10.1109/cvpr.2016.90",
             "sources": ["crossref", "openalex"], "citation_count": 172299},
            {"source": "arxiv", "title": "Attention Is All You Need",
             "authors": ["Ashish Vaswani"], "year": 2017,
             "arxiv_id": "1706.03762", "venue": "arXiv"},
        ]}), "library_path": lib}),
        ("save_to_library", {"papers_json": json.dumps({"papers": [
            {"source": "openalex", "title": "Attention Is All You Need",
             "doi": "10.48550/arxiv.1706.03762", "abstract": "rich abstract",
             "year": 2017},
        ]}), "library_path": lib}),
        ("export_bibtex", {"library_path": lib, "out_path": bib_path}),
        ("coverage_report", {"subtopics": json.dumps([
            {"name": "residual", "keywords": ["residual"]},
            {"name": "missing-topic", "keywords": ["quantum gravity"]},
        ]), "library_path": lib}),
    ])
    assert search["total"] >= 3 and not search["errors"]

    assert saved["ok"] and saved["total"] == 2
    # 修复回归 1：多源出处不丢失；
    # 修复回归 2：arXiv 代发 DOI 与 arxiv_id 判定为同一篇（第二次 save 合并而非新增）
    assert saved_again["added"] == 0 and saved_again["total"] == 2
    rows = [json.loads(l) for l in open(lib, encoding="utf-8")]
    resnet = next(r for r in rows if "Residual" in r["title"])
    attention = next(r for r in rows if "Attention" in r["title"])
    assert resnet["sources"] == ["crossref", "openalex"]
    assert set(attention["sources"]) == {"arxiv", "openalex"}
    assert attention["abstract"] == "rich abstract"  # 后见记录补空字段

    assert exported["ok"] and exported["entries"] == 2
    from server.core import bibtex as bibmod
    entries = bibmod.parse_bibtex(open(bib_path, encoding="utf-8").read())
    assert len(entries) == 2
    keys = {e["key"] for e in entries}
    assert "he2016deep" in keys and "vaswani2017attention" in keys

    assert coverage["verdict"] == "GAPS_FOUND"
    assert "missing-topic" in coverage["gaps"]
    by_name = {t["subtopic"]: t for t in coverage["subtopics"]}
    assert by_name["residual"]["hits"] == 1
    assert by_name["missing-topic"]["hits"] == 0


# ---------- 错误路径（零网络） ----------

def test_error_paths_no_crash(tmp_path):
    empty, unknown = mcp_calls(str(tmp_path), [
        ("search_papers", {"query": "   ", "sources": "arxiv"}),
        ("search_papers", {"query": "x", "sources": "bogus_source"}),
    ])
    assert empty["total"] == 0 and "query" in empty["errors"]
    assert unknown["total"] == 0 and "bogus_source" in unknown["errors"]


# ---------- 限流器（本地 http.server，零外网） ----------

RATELIMIT_SNIPPET = textwrap.dedent("""
    import json, os, sys, threading, time
    from http.server import BaseHTTPRequestHandler, HTTPServer
    sys.path.insert(0, os.environ["GOAI_ROOT"])
    from server.core import http as ghttp

    arrivals = []
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            arrivals.append(time.monotonic())
            self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        def log_message(self, *a): pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    for i in range(3):
        ghttp.get(f"http://127.0.0.1:{port}/{i}")
    gaps = [arrivals[i] - arrivals[i-1] for i in range(1, len(arrivals))]

    ghttp.get(f"http://127.0.0.1:{port}/warm")
    res = {}
    def hit(tag, url):
        t = time.monotonic(); ghttp.get(url); res[tag] = time.monotonic() - t
    ta = threading.Thread(target=hit, args=("same", f"http://127.0.0.1:{port}/x"))
    tb = threading.Thread(target=hit, args=("other", f"http://localhost:{port}/y"))
    ta.start(); time.sleep(0.05); tb.start(); ta.join(); tb.join()
    print(json.dumps({"gaps": gaps, "same": res["same"], "other": res["other"]}))
""")


def test_ratelimit_same_host_spacing_and_no_cross_host_block():
    env = {**os.environ, "GOAI_ROOT": ROOT, "GOAI_HTTP_MIN_INTERVAL": "1.0"}
    r = subprocess.run([sys.executable, "-c", RATELIMIT_SNIPPET],
                       capture_output=True, text=True, env=env, timeout=60)
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout.strip().splitlines()[-1])
    # 同 host 到达间隔 ~MIN_INTERVAL（vs 不节流的 ~10ms；阈值放宽抗机器负载抖动）
    assert all(g >= 0.9 for g in data["gaps"]), data
    # 同 host 需等冷却 ~1s；异 host 不得被拖住（修复回归：原实现持锁睡眠会阻塞 ~1s，
    # other≈same；修复后 other≪same。用相对比较抗负载抖动）
    assert data["same"] >= 0.9, data
    assert data["other"] < data["same"] * 0.5, data
