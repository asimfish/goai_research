"""goai-figure 图纸环节 live 实测：真实 MCP stdio 协议 + 真实 draw.io Desktop CLI。

跑法:
    .venv/bin/python -m pytest -m live tests/live/test_live_figure.py -v

证据模式（产物落盘到指定 workspace 而非 pytest tmp，便于报告引用）:
    GOAI_FIGURE_LIVE_WS=$REPO/workspace_live/figure \
        .venv/bin/python -m pytest -m live tests/live/test_live_figure.py -v

drawio CLI 不存在时相关用例自动 skip（其余 MCP/渲染/逆向用例照跑）。
"""
import asyncio
import json
import os
import struct
import sys
import time
import xml.etree.ElementTree as ET

import pytest

pytestmark = pytest.mark.live

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from server import figure_server  # noqa: E402

DRAWIO_CLI = figure_server._find_drawio_cli()

# ---------------------------------------------------------------------------
# 测试用 figspec：模拟真实综述 pipeline 图
# 12 节点（含 8 种 shape）/ 3 分组（1 dashed）/ 13 边（全带 label，3 dashed，
# 2 带 waypoints）/ 2 独立 texts
# ---------------------------------------------------------------------------
PIPELINE_SPEC = {
    "title": "LLM-based Literature Survey Multi-Agent Pipeline",
    "canvas": {"width": 1280, "height": 720},
    "defaults": {"font_size": 13},
    "groups": [
        {"id": "g_retrieval", "label": "Stage 1 — Retrieval & Curation",
         "x": 40, "y": 80, "w": 380, "h": 560, "fill": "#F2F7FF", "stroke": "#7A9CC6"},
        {"id": "g_synthesis", "label": "Stage 2 — Synthesis",
         "x": 470, "y": 80, "w": 360, "h": 400, "fill": "#F4FBF4", "stroke": "#82B366"},
        {"id": "g_review", "label": "Stage 3 — Review Loop",
         "x": 880, "y": 80, "w": 360, "h": 400, "fill": "#FFF8EE", "stroke": "#D6B656",
         "dashed": True},
    ],
    "nodes": [
        {"id": "query", "label": "Research Query", "x": 70, "y": 130, "w": 150, "h": 52,
         "shape": "stadium", "fill": "#FFFFFF", "stroke": "#7A9CC6", "group": "g_retrieval"},
        {"id": "litsearch", "label": "LitSearch Agent", "sublabel": "arXiv / S2 / OpenAlex",
         "x": 70, "y": 230, "w": 150, "h": 64, "shape": "rounded", "fill": "#DAE8FC",
         "stroke": "#6C8EBF", "group": "g_retrieval"},
        {"id": "dedup", "label": "Dedup & Rank", "x": 70, "y": 350, "w": 150, "h": 52,
         "shape": "parallelogram", "fill": "#DAE8FC", "stroke": "#6C8EBF",
         "group": "g_retrieval"},
        {"id": "library", "label": "Paper Library", "sublabel": "papers.jsonl",
         "x": 250, "y": 470, "w": 140, "h": 70, "shape": "cylinder", "fill": "#E1D5E7",
         "stroke": "#9673A6", "group": "g_retrieval"},
        {"id": "outline", "label": "Outline Agent", "x": 510, "y": 130, "w": 150, "h": 56,
         "shape": "rounded", "fill": "#D5E8D4", "stroke": "#82B366", "group": "g_synthesis"},
        {"id": "writer", "label": "Section Writer", "sublabel": "per-section drafting",
         "x": 510, "y": 240, "w": 150, "h": 64, "shape": "rounded", "fill": "#D5E8D4",
         "stroke": "#82B366", "group": "g_synthesis"},
        {"id": "figgen", "label": "Figure Agent", "sublabel": "figspec -> SVG+drawio",
         "x": 660, "y": 380, "w": 150, "h": 64, "shape": "rounded", "fill": "#D5E8D4",
         "stroke": "#82B366", "group": "g_synthesis"},
        {"id": "refcheck", "label": "RefCheck Agent", "x": 920, "y": 130, "w": 150, "h": 56,
         "shape": "rounded", "fill": "#FFE6CC", "stroke": "#D79B00", "group": "g_review"},
        {"id": "reviewer", "label": "Reviewer Agent", "sublabel": "rubric scoring",
         "x": 920, "y": 240, "w": 150, "h": 64, "shape": "rounded", "fill": "#FFE6CC",
         "stroke": "#D79B00", "group": "g_review"},
        {"id": "gate", "label": "Accept?", "x": 935, "y": 360, "w": 120, "h": 80,
         "shape": "diamond", "fill": "#FFF2CC", "stroke": "#D6B656", "group": "g_review"},
        {"id": "draft", "label": "Survey Draft", "sublabel": "LaTeX", "x": 545, "y": 560,
         "w": 150, "h": 60, "shape": "document", "fill": "#FFFFFF", "stroke": "#666666"},
        {"id": "final", "label": "Camera-Ready", "x": 1060, "y": 560, "w": 150, "h": 56,
         "shape": "stadium", "fill": "#D5E8D4", "stroke": "#82B366"},
    ],
    "edges": [
        {"id": "e1", "from": "query", "to": "litsearch", "label": "keywords"},
        {"id": "e2", "from": "litsearch", "to": "dedup", "label": "hits"},
        {"id": "e3", "from": "dedup", "to": "library", "label": "curated set"},
        {"id": "e4", "from": "library", "to": "outline", "label": "corpus"},
        {"id": "e5", "from": "outline", "to": "writer", "label": "section plan"},
        {"id": "e6", "from": "writer", "to": "figgen", "label": "figspec",
         "dashed": True, "arrow": "open"},
        {"id": "e7", "from": "writer", "to": "draft", "label": "sections"},
        {"id": "e8", "from": "figgen", "to": "draft", "label": "figures", "dashed": True},
        {"id": "e9", "from": "draft", "to": "refcheck", "label": "cites",
         "waypoints": [[760, 590], [995, 590]]},
        {"id": "e10", "from": "refcheck", "to": "reviewer", "label": "verified bib"},
        {"id": "e11", "from": "reviewer", "to": "gate", "label": "scores"},
        {"id": "e12", "from": "gate", "to": "writer", "label": "revise", "dashed": True,
         "arrow": "open", "waypoints": [[995, 640], [585, 640]]},
        {"id": "e13", "from": "gate", "to": "final", "label": "pass"},
    ],
    "texts": [
        {"id": "t1", "text": "dashed = feedback / async path", "x": 640, "y": 690,
         "font_size": 11, "color": "#666666"},
        {"id": "t2", "text": "single figspec renders SVG + editable drawio",
         "x": 640, "y": 55, "font_size": 12, "color": "#444444", "bold": True},
    ],
}

INVALID_SPEC = {
    "canvas": {"width": 800, "height": 600},
    "nodes": [
        {"id": "a", "label": "A", "x": 10, "y": 10, "w": 100, "h": 50,
         "shape": "warp_core"},
        {"id": "b", "label": "B", "x": 50, "y": 30, "w": 100, "h": 50},
    ],
    "edges": [{"id": "e1", "from": "a", "to": "ghost"}],
}

# 「更难」的 SVG：嵌套 translate、scale（已知不支持）、polyline 边、
# tspan 多行文本、贝塞尔曲线 path（应跳过）
HARDER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400">
  <g transform="translate(40, 30)">
    <rect x="0" y="0" width="120" height="50" fill="#eeeeee" stroke="#333333"/>
    <text x="60" y="25">Outer A</text>
    <g transform="translate(200, 10)">
      <rect x="0" y="0" width="120" height="50" fill="#eeeeee" stroke="#333333"/>
      <text x="60" y="25">Nested B</text>
    </g>
  </g>
  <polyline points="160,55 200,55 200,65 240,65" fill="none" stroke="#333333"
    marker-end="url(#arrow)"/>
  <text x="420" y="200" font-size="12"><tspan x="420" dy="0">line one</tspan><tspan
    x="420" dy="14">line two</tspan></text>
  <g transform="scale(2)">
    <rect x="10" y="150" width="40" height="20" stroke="#990000" fill="none"/>
  </g>
  <path d="M 100 300 C 150 250 200 350 250 300" stroke="#333333" fill="none"/>
</svg>
"""


def _payload(result):
    """CallToolResult → (payload dict|None, is_error)。"""
    is_err = bool(getattr(result, "isError", getattr(result, "is_error", False)))
    text = result.content[0].text if result.content else ""
    try:
        return json.loads(text), is_err
    except (json.JSONDecodeError, TypeError):
        return {"_raw": text}, is_err


async def _drive(ws: str) -> dict:
    """单个 stdio session 跑完全部场景，返回原始结果供各用例断言。"""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    raw_dir = os.path.join(ws, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    R: dict = {"ws": ws, "timings": {}}

    params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(ROOT, "server", "figure_server.py")],
        env={**os.environ,
             "GOAI_WORKSPACE": ws,
             # macOS: cairosvg 依赖 brew libcairo；不存在时 server 自动降级
             "DYLD_FALLBACK_LIBRARY_PATH": "/opt/homebrew/lib"},
        cwd=ws,
    )

    async def call(session, tool, args, tag):
        t0 = time.monotonic()
        try:
            out = await session.call_tool(tool, args)
            payload, is_err = _payload(out)
        except Exception as exc:  # 协议层异常也如实记录
            payload, is_err = {"_exception": f"{type(exc).__name__}: {exc}"}, True
        R["timings"][tag] = round(time.monotonic() - t0, 2)
        rec = {"tool": tool, "args": {k: (v[:400] + "…" if isinstance(v, str)
                                          and len(v) > 400 else v)
                                      for k, v in args.items()},
               "elapsed_s": R["timings"][tag], "isError": is_err, "payload": payload}
        with open(os.path.join(raw_dir, f"{tag}.json"), "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        return payload, is_err

    spec_json = json.dumps(PIPELINE_SPEC, ensure_ascii=False)
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            info = await s.initialize()
            R["server_name"] = info.serverInfo.name if hasattr(info, "serverInfo") \
                else info.server_info.name
            tools = await s.list_tools()
            R["tools"] = sorted(t.name for t in tools.tools)

            R["schema"] = await call(s, "figspec_schema", {}, "01_schema")
            R["validate_ok"] = await call(
                s, "validate_figspec", {"figspec_json": spec_json}, "02_validate_ok")
            R["validate_bad"] = await call(
                s, "validate_figspec",
                {"figspec_json": json.dumps(INVALID_SPEC)}, "03_validate_bad")
            R["validate_nonjson"] = await call(
                s, "validate_figspec", {"figspec_json": "{not json"},
                "04_validate_nonjson")

            # out_dir 留空 → 必须落到 GOAI_WORKSPACE/figures（回归 env 修复）
            R["render"] = await call(
                s, "render_figure",
                {"figspec_json": spec_json, "name": "fig_pipeline"}, "05_render")
            R["list"] = await call(s, "list_figures", {}, "06_list")

            # 渲染前必须被 validate 拦截：非法 spec 直接 render → isError，
            # 且 session 必须存活（下一调用成功）
            R["render_invalid"] = await call(
                s, "render_figure",
                {"figspec_json": json.dumps(INVALID_SPEC), "name": "should_fail"},
                "07_render_invalid")
            R["alive_after_error"] = await call(s, "list_figures", {},
                                                "08_alive_after_error")

            svg_path = (R["render"][0] or {}).get("svg", "")
            R["roundtrip"] = await call(
                s, "svg_file_to_drawio", {"svg_path": svg_path}, "09_roundtrip")
            R["svg2drawio_missing"] = await call(
                s, "svg_file_to_drawio",
                {"svg_path": os.path.join(ws, "nope.svg")}, "10_svg2drawio_missing")

            harder_path = os.path.join(ws, "harder.svg")
            with open(harder_path, "w", encoding="utf-8") as f:
                f.write(HARDER_SVG)
            R["harder"] = await call(
                s, "svg_file_to_drawio", {"svg_path": harder_path}, "11_harder_svg")

            drawio_path = (R["render"][0] or {}).get("drawio", "")
            if DRAWIO_CLI:
                R["export_png"] = await call(
                    s, "drawio_export", {"drawio_path": drawio_path, "fmt": "png"},
                    "12_export_png")
                R["export_pdf"] = await call(
                    s, "drawio_export", {"drawio_path": drawio_path, "fmt": "pdf"},
                    "13_export_pdf")
            R["export_missing"] = await call(
                s, "drawio_export",
                {"drawio_path": os.path.join(ws, "ghost.drawio")}, "14_export_missing")
            R["export_badfmt"] = await call(
                s, "drawio_export", {"drawio_path": drawio_path, "fmt": "bmp"},
                "15_export_badfmt")
    return R


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    ws = os.environ.get("GOAI_FIGURE_LIVE_WS") or str(
        tmp_path_factory.mktemp("figure_live"))
    return asyncio.run(_drive(ws))


# ---------------------------------------------------------------------------
# 1. MCP stdio 协议层
# ---------------------------------------------------------------------------

def test_mcp_handshake_and_tool_inventory(live):
    assert live["server_name"] == "goai-figure"
    assert live["tools"] == ["drawio_export", "figspec_schema", "list_figures",
                             "render_figure", "svg_file_to_drawio",
                             "validate_figspec"]


def test_figspec_schema_tool(live):
    payload, is_err = live["schema"]
    assert not is_err
    assert set(payload["example"]) >= {"canvas", "nodes", "edges"}
    assert "rounded" in payload["shapes"]


def test_validate_accepts_good_spec(live):
    payload, is_err = live["validate_ok"]
    assert not is_err and payload["ok"] is True and payload["errors"] == []


def test_validate_catches_bad_spec(live):
    payload, _ = live["validate_bad"]
    assert payload["ok"] is False
    joined = "\n".join(payload["errors"])
    assert "warp_core" in joined          # 非法 shape
    assert "ghost" in joined              # 未知边端点
    assert "重叠" in joined               # 节点重叠


def test_validate_rejects_non_json(live):
    payload, _ = live["validate_nonjson"]
    assert payload["ok"] is False and "JSON" in payload["errors"][0]


# ---------------------------------------------------------------------------
# 2. render_figure 全链路 + GOAI_WORKSPACE 落盘
# ---------------------------------------------------------------------------

def test_render_writes_under_goai_workspace(live):
    payload, is_err = live["render"]
    assert not is_err and payload["ok"]
    for key in ("figspec", "svg", "drawio"):
        path = payload[key]
        assert path.startswith(live["ws"]), \
            f"{key} 未落在 GOAI_WORKSPACE 下: {path}"
        assert os.path.getsize(path) > 0


def test_rendered_svg_structure(live):
    svg_path = live["render"][0]["svg"]
    root = ET.parse(svg_path).getroot()          # XML 合法性
    assert root.tag.endswith("svg")
    texts = {(el.text or "").strip() for el in root.iter()
             if el.tag.endswith("text")}
    for nd in PIPELINE_SPEC["nodes"]:            # 12 个节点 label 齐全
        assert nd["label"] in texts, f"节点 label 丢失: {nd['label']}"
    for e in PIPELINE_SPEC["edges"]:             # 13 条边 label 齐全
        assert e["label"] in texts, f"边 label 丢失: {e['label']}"
    for g in PIPELINE_SPEC["groups"]:
        assert g["label"] in texts
    body = open(svg_path, encoding="utf-8").read()
    assert body.count("marker-end") == 13        # 全部边带箭头
    assert "stroke-dasharray" in body            # dashed 边/组生效


def test_rendered_drawio_structure(live):
    drawio_path = live["render"][0]["drawio"]
    root = ET.parse(drawio_path).getroot()
    assert root.tag == "mxfile"
    model = root.find("./diagram/mxGraphModel")
    assert model is not None
    cells = {c.get("id"): c for c in model.findall("./root/mxCell")}

    for g in PIPELINE_SPEC["groups"]:            # 分组是 container vertex
        c = cells[g["id"]]
        assert c.get("vertex") == "1" and "container=1" in c.get("style")
    for nd in PIPELINE_SPEC["nodes"]:            # 节点 parent 正确
        c = cells[nd["id"]]
        assert c.get("vertex") == "1"
        expect_parent = nd.get("group", "1")
        assert c.get("parent") == expect_parent, nd["id"]
        if nd.get("group"):                      # 容器内坐标为相对坐标
            g = next(gg for gg in PIPELINE_SPEC["groups"]
                     if gg["id"] == nd["group"])
            geo = c.find("mxGeometry")
            assert float(geo.get("x")) == nd["x"] - g["x"]
            assert float(geo.get("y")) == nd["y"] - g["y"]
    for e in PIPELINE_SPEC["edges"]:             # 边绑定 source/target
        c = cells[e["id"]]
        assert c.get("edge") == "1"
        assert c.get("source") == e["from"] and c.get("target") == e["to"]
        if e.get("dashed"):
            assert "dashed=1" in c.get("style")
        if e.get("waypoints"):
            pts = c.findall("./mxGeometry/Array/mxPoint")
            assert len(pts) == len(e["waypoints"])


def test_list_figures_inventory(live):
    payload, _ = live["list"]
    row = next(r for r in payload["figures"] if r["name"] == "fig_pipeline")
    assert row["figspec"] and row["svg"] and row["drawio"]


def test_render_invalid_spec_blocked_and_server_survives(live):
    payload, is_err = live["render_invalid"]
    assert not is_err, "应结构化报错而非裸异常（SDK 会吞掉异常详情）"
    assert payload["ok"] is False and "校验失败" in payload["error"]
    assert "warp_core" in payload["error"], "校验详情必须透出给调用方"
    payload2, is_err2 = live["alive_after_error"]
    assert not is_err2 and "figures" in payload2, "错误后 server 应继续存活"


# ---------------------------------------------------------------------------
# 3. 逆向往返
# ---------------------------------------------------------------------------

def test_roundtrip_fidelity(live):
    payload, is_err = live["roundtrip"]
    assert not is_err and payload["ok"]
    rec = json.load(open(payload["figspec_recovered"], encoding="utf-8"))

    n_nodes, n_groups, n_edges = (len(rec["nodes"]), len(rec["groups"]),
                                  len(rec["edges"]))
    orig_edge_labels = [e["label"] for e in PIPELINE_SPEC["edges"]]
    rec_edge_labels = [(e.get("label") or "") for e in rec["edges"]]
    label_hits = sum(1 for l in orig_edge_labels
                     if any(l in rl for rl in rec_edge_labels))
    orig_node_labels = [nd["label"] for nd in PIPELINE_SPEC["nodes"]]
    rec_node_text = " | ".join((nd.get("label") or "") for nd in rec["nodes"])
    node_label_hits = sum(1 for l in orig_node_labels if l in rec_node_text)

    live["roundtrip_stats"] = {
        "nodes": f"{n_nodes}/12", "groups": f"{n_groups}/3",
        "edges": f"{n_edges}/13", "edge_label_hits": f"{label_hits}/13",
        "node_label_hits": f"{node_label_hits}/12"}
    print("\n[roundtrip]", live["roundtrip_stats"])

    # 已知能力边界：document/cylinder 形状由曲线 path 构成，逆向会丢失/退化，
    # 因此下限按「除特殊形状外全保留」设定
    assert n_groups == 3
    assert n_nodes >= 10
    assert n_edges >= 10
    assert label_hits >= 10
    assert node_label_hits >= 10

    # 逆向产物 drawio 结构合法
    root = ET.parse(payload["drawio"]).getroot()
    assert root.tag == "mxfile"
    cells = root.findall("./diagram/mxGraphModel/root/mxCell")
    assert sum(1 for c in cells if c.get("vertex") == "1") >= n_nodes
    assert sum(1 for c in cells if c.get("edge") == "1") == n_edges


def test_harder_svg_boundaries(live):
    payload, is_err = live["harder"]
    assert not is_err and payload["ok"]
    rec = json.load(open(payload["figspec_recovered"], encoding="utf-8"))
    nodes = {(nd["x"], nd["y"]): nd for nd in rec["nodes"]}

    # 嵌套 translate 正确累计：A@(40,30)，B@(240,40)
    assert (40, 30) in nodes and "Outer A" in nodes[(40, 30)]["label"]
    assert (240, 40) in nodes and "Nested B" in nodes[(240, 40)]["label"]
    # polyline → 边 A→B，中间点保留为 waypoints
    assert len(rec["edges"]) == 1
    edge = rec["edges"][0]
    assert edge["from"] == nodes[(40, 30)]["id"]
    assert edge["to"] == nodes[(240, 40)]["id"]
    assert edge.get("waypoints") == [[200.0, 55.0], [200.0, 65.0]]
    # tspan 多行文本：内容保留（换行会丢，如实断言现状）
    all_text = " ".join(t["text"] for t in rec["texts"])
    assert "line one" in all_text
    # 已知边界 1：scale(2) 不被应用（仅累计 translate）
    assert (10, 150) in nodes, "scale 变换应被忽略（能力边界，如实固化）"
    # 已知边界 2：贝塞尔曲线 path 不产生边（仅 1 条 polyline 边）
    assert len(rec["edges"]) == 1


def test_svg2drawio_missing_file_structured_error(live):
    payload, is_err = live["svg2drawio_missing"]
    assert not is_err                      # 结构化错误而非异常
    assert payload["ok"] is False and "不存在" in payload["error"]


# ---------------------------------------------------------------------------
# 4. draw.io Desktop CLI 真实导出
# ---------------------------------------------------------------------------

needs_cli = pytest.mark.skipif(not DRAWIO_CLI, reason="draw.io Desktop CLI 不存在")


@needs_cli
def test_drawio_export_png_real_cli(live):
    payload, is_err = live["export_png"]
    assert not is_err and payload["ok"], payload
    out = payload["out"]
    data = open(out, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "PNG magic bytes"
    w_px, h_px = struct.unpack(">II", data[16:24])
    # -s 2 生效：内容包围盒 ≈ 1204x700（scale 1），2x 后必然超过画布宽 1280
    assert w_px > PIPELINE_SPEC["canvas"]["width"], (w_px, h_px)
    assert len(data) > 10_000
    print(f"\n[drawio png] {out} {len(data)}B {w_px}x{h_px} "
          f"elapsed={live['timings']['12_export_png']}s")


@needs_cli
def test_drawio_export_pdf_real_cli(live):
    payload, is_err = live["export_pdf"]
    assert not is_err and payload["ok"], payload
    data = open(payload["out"], "rb").read()
    assert data[:5] == b"%PDF-", "PDF magic bytes"
    assert len(data) > 5_000


@needs_cli
def test_drawio_export_missing_input_structured(live):
    payload, is_err = live["export_missing"]
    assert not is_err
    assert payload["ok"] is False and "不存在" in payload["error"]


def test_drawio_export_rejects_bad_format(live):
    payload, _ = live["export_badfmt"]
    assert payload["ok"] is False and "不支持" in payload.get("error", "")


@needs_cli
def test_drawio_export_timeout_structured(live, monkeypatch):
    """极短 timeout 触发超时路径：结构化报错、不留残余进程/半成品。

    timeout 从 env 读且 server 进程 env 在 spawn 时已固化，故本用例直接
    in-process 调工具函数（subprocess 仍是真实 CLI）。
    """
    monkeypatch.setenv("GOAI_DRAWIO_TIMEOUT", "0.05")
    drawio_path = live["render"][0]["drawio"]
    out = json.loads(figure_server.drawio_export(drawio_path, "png"))
    assert out["ok"] is False and "超时" in out["error"]
    monkeypatch.delenv("GOAI_DRAWIO_TIMEOUT")
    # 恢复现场：重新真实导出，确认超时未破坏后续导出能力
    out2 = json.loads(figure_server.drawio_export(drawio_path, "png"))
    assert out2["ok"] is True


@needs_cli
def test_drawio_export_stale_output_not_reported_as_success(live, tmp_path):
    """exit-0 怪癖防御：目标文件已存在 + 本次导出失败 → 必须报失败。"""
    bad = tmp_path / "broken.drawio"
    bad.write_text("this is not xml")
    stale = tmp_path / "broken.png"
    stale.write_bytes(b"\x89PNG stale")
    out = json.loads(figure_server.drawio_export(str(bad), "png"))
    assert out["ok"] is False, "旧产物存在时失败导出不得误报成功"
    assert not stale.exists(), "应先清掉旧产物"


# ---------------------------------------------------------------------------
# 5. preview 自检（cairosvg）
# ---------------------------------------------------------------------------

def test_preview_png_selfcheck(live):
    payload, _ = live["render"]
    png = payload.get("png")
    if not png:
        pytest.skip(f"cairosvg/libcairo 不可用: {payload.get('png_hint', '未安装')}")
    data = open(png, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(data) > 10_000
