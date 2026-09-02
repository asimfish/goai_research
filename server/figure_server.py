"""goai-figure MCP server —— 论文图纸：figspec 校验/渲染（SVG+drawio 双输出）、
SVG→drawio 可编辑转换、draw.io Desktop CLI 导出。

figspec 是单一事实源：同一份 JSON 同时产出论文用 SVG 和 drawio 原生可编辑文件，
两者永远一致。要接 draw.io 编辑器，直接打开 .drawio 文件，或配合官方
@drawio/mcp 的 open_drawio_xml 在浏览器中打开。
"""
from __future__ import annotations

import contextlib
import glob
import json
import os
import signal
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.core.mcp_compat import FastMCP

from server.core import figspec as fs
from server.core import render_drawio, render_svg
from server.core.svg2drawio import svg_to_figspec

mcp = FastMCP("goai-figure")

DRAWIO_CLI_CANDIDATES = [
    os.environ.get("GOAI_DRAWIO_CLI", ""),
    "/Applications/draw.io.app/Contents/MacOS/draw.io",
    "drawio",
]


def _dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _default_out_dir() -> str:
    # README 承诺 GOAI_WORKSPACE 是所有产物的落盘位置；stdio 启动的 server
    # CWD 不可控，缺省 out_dir 必须跟随该环境变量而非硬编码相对路径。
    return os.path.join(os.environ.get("GOAI_WORKSPACE", "workspace"), "figures")


def _find_drawio_cli() -> str | None:
    for c in DRAWIO_CLI_CANDIDATES:
        if not c:
            continue
        if os.path.sep in c and os.path.exists(c):
            return c
        from shutil import which
        if which(c):
            return c
    return None


@mcp.tool()
def figspec_schema() -> str:
    """返回 figspec 的 schema 说明与一个最小示例（画新图前先读这个）。"""
    example = {
        "title": "Method Overview",
        "canvas": {"width": 1100, "height": 560},
        "defaults": {"font_size": 13},
        "groups": [
            {"id": "g_train", "label": "Training", "x": 40, "y": 70,
             "w": 480, "h": 420, "fill": "#F2F7FF", "stroke": "#7A9CC6"},
        ],
        "nodes": [
            {"id": "enc", "label": "Encoder", "sublabel": "ViT-L", "group": "g_train",
             "x": 80, "y": 150, "w": 150, "h": 64, "shape": "rounded",
             "fill": "#DAE8FC", "stroke": "#6C8EBF"},
            {"id": "dec", "label": "Decoder", "group": "g_train",
             "x": 320, "y": 150, "w": 150, "h": 64, "shape": "rounded",
             "fill": "#D5E8D4", "stroke": "#82B366"},
            {"id": "loss", "label": "L_task", "x": 640, "y": 158, "w": 120,
             "h": 48, "shape": "stadium", "fill": "#FFF2CC", "stroke": "#D6B656"},
        ],
        "edges": [
            {"id": "e1", "from": "enc", "to": "dec", "label": "z_t"},
            {"id": "e2", "from": "dec", "to": "loss", "dashed": True,
             "arrow": "open"},
        ],
        "texts": [{"id": "note1", "text": "dashed = gradient-free",
                   "x": 640, "y": 260, "font_size": 11, "color": "#666666"}],
    }
    return _dumps({
        "shapes": sorted(fs.SHAPES), "arrows": sorted(fs.ARROWS),
        "coordinate_system": "x/y 为左上角；画布原点在左上",
        "rules": [
            "每条边的 from/to 必须指向已定义节点 id；变量/指标放边 label，不做同级盒子",
            "同一分组的节点设置 group 字段，drawio 输出会成为可整体拖动的容器",
            "节点不得互相重叠（validate 会拦截）",
            "配色克制：一主一辅色，避免 AI 风霓虹渐变（参考 figure-studio 的 human palette）",
        ],
        "example": example})


@mcp.tool()
def validate_figspec(figspec_json: str) -> str:
    """校验 figspec JSON：结构 + 排版 + 美学。

    排版：字号印刷等效地板、文字溢出、标签遮挡。美学（顶刊观感机械化）：
    配色 ≤2 主题色 + 1 强调色、无彩虹泳道、无饱和色块铺满、无近失对齐、
    兄弟节点尺寸一致、不越界/留白均衡、间距不过密、连线不穿节点/少交叉、
    描边 ≤2 档、标题为最大层级。
    返回 {ok, errors, typo_errors, typo_warnings}。errors/typo_errors 均阻塞渲染
    （≥4 色系、彩虹泳道、越界属阻塞）；typo_warnings 建议修复。
    """
    try:
        spec = json.loads(figspec_json)
    except json.JSONDecodeError as exc:
        return _dumps({"ok": False, "errors": [f"JSON 解析失败: {exc}"]})
    errs = fs.validate(spec)
    typo = fs.lint(spec) if not errs else {"errors": [], "warnings": []}
    return _dumps({"ok": not errs and not typo["errors"], "errors": errs,
                   "typo_errors": typo["errors"], "typo_warnings": typo["warnings"]})


@mcp.tool()
def render_figure(figspec_json: str, name: str, out_dir: str = "") -> str:
    """把 figspec 渲染为 SVG + .drawio 双输出（同一事实源，保证一致）。

    Args:
        figspec_json: figspec JSON 文本
        name: 图名（文件名前缀，如 fig1_overview）
        out_dir: 输出根目录（自动写入 svg/ drawio/ figspec/ 子目录）；
            缺省为 $GOAI_WORKSPACE/figures（未设 GOAI_WORKSPACE 时 workspace/figures）
    Returns:
        JSON {svg, drawio, figspec, png?}；png 仅在安装 cairosvg 时生成
    """
    out_dir = out_dir or _default_out_dir()
    try:
        spec = fs.loads(figspec_json)
    except (ValueError, json.JSONDecodeError) as exc:
        # 结构化返回校验详情：MCP SDK 会把裸异常吞成
        # 「Error executing tool render_figure」，调用方看不到原因
        return _dumps({"ok": False, "error": str(exc)})
    typo = fs.lint(spec)
    if typo["errors"]:
        return _dumps({"ok": False,
                       "error": "排版/美学 lint 未通过（字号/溢出/遮挡/配色/越界）",
                       "typo_errors": typo["errors"],
                       "hint": "字号印刷等效 = px × 468 / canvas.width，正文需 ≥4.5pt；"
                               "溢出改文本或加大节点；遮挡调坐标；配色收敛到 ≤2 主题色 + "
                               "1 强调色，分组底色改浅灰/极淡；内容不得越出画布。"
                               "修完重新 render。"})
    paths = {}
    if typo["warnings"]:
        # 美学告警不阻塞出图，但 figure-studio 合同要求逐条处理或在 figure_plan 记录理由
        paths["typo_warnings"] = typo["warnings"]
    for sub in ("figspec", "svg", "drawio", "png"):
        os.makedirs(os.path.join(out_dir, sub), exist_ok=True)

    spec_path = os.path.join(out_dir, "figspec", f"{name}.json")
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    paths["figspec"] = spec_path

    svg_text = render_svg.render(spec)
    svg_path = os.path.join(out_dir, "svg", f"{name}.svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_text)
    paths["svg"] = svg_path

    drawio_text = render_drawio.render(spec, page_name=name)
    drawio_path = os.path.join(out_dir, "drawio", f"{name}.drawio")
    with open(drawio_path, "w", encoding="utf-8") as f:
        f.write(drawio_text)
    paths["drawio"] = drawio_path

    try:
        import cairosvg  # type: ignore
        png_path = os.path.join(out_dir, "png", f"{name}.png")
        cairosvg.svg2png(bytestring=svg_text.encode(), write_to=png_path, scale=2.0)
        paths["png"] = png_path
    except ImportError:
        paths["png"] = None
    except OSError:
        # cairosvg 装了但找不到系统 libcairo（macOS 常见）。png 只是自检辅助，
        # 不阻塞 svg/drawio 主产物。
        paths["png"] = None
        paths["png_hint"] = ("libcairo 未被 dyld 找到：brew install cairo，且 MCP "
                             "server 启动 env 需带 DYLD_FALLBACK_LIBRARY_PATH="
                             "/opt/homebrew/lib（见 configs/ 示例）")

    return _dumps({"ok": True, **paths,
                   "next": "用 Read 工具查看 svg/png 自检布局；改 figspec 重渲染即可迭代；"
                           ".drawio 可直接用 draw.io 打开继续手工编辑"})


@mcp.tool()
def svg_file_to_drawio(svg_path: str, out_path: str = "") -> str:
    """把结构化 SVG 逆向为 figspec 并转成 .drawio 可编辑文件。

    适用：矢量框图（rect/ellipse/polygon/line/text）。复杂路径与位图请走
    goai-figure-editable 的视觉重建流程。
    Returns:
        JSON {drawio, figspec_recovered, stats}；figspec 一并返回便于人工修正
    """
    if not os.path.exists(svg_path):
        return _dumps({"ok": False, "error": f"文件不存在: {svg_path}"})
    with open(svg_path, encoding="utf-8") as f:
        spec = svg_to_figspec(f.read())
    out_path = out_path or svg_path.rsplit(".", 1)[0] + ".drawio"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(render_drawio.render(spec))
    spec_path = out_path.rsplit(".", 1)[0] + ".recovered.figspec.json"
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    return _dumps({"ok": True, "drawio": out_path,
                   "figspec_recovered": spec_path,
                   "stats": {"nodes": len(spec["nodes"]),
                             "edges": len(spec["edges"]),
                             "texts": len(spec["texts"])},
                   "note": "逆向是近似过程；请打开 drawio 或复渲染 SVG 对照原图检查"})


@mcp.tool()
def drawio_export(drawio_path: str, fmt: str = "png") -> str:
    """用 draw.io Desktop CLI 把 .drawio 导出为 png/svg/pdf（需本机安装 draw.io）。"""
    cli = _find_drawio_cli()
    if not cli:
        return _dumps({"ok": False,
                       "error": "未找到 draw.io Desktop CLI",
                       "install": "brew install --cask drawio；或设 GOAI_DRAWIO_CLI 指向可执行文件",
                       "fallback": "render_figure 的 SVG 输出可直接用于论文，不依赖 drawio"})
    if fmt not in ("png", "svg", "pdf", "jpg"):
        return _dumps({"ok": False, "error": f"不支持的格式 {fmt}"})
    if not os.path.exists(drawio_path):
        return _dumps({"ok": False, "error": f"文件不存在: {drawio_path}"})
    out_path = drawio_path.rsplit(".", 1)[0] + f".{fmt}"
    # 真机行为（macOS drawio 31.3.2 实测）：成功 rc=0、失败 rc=1，但 rc 语义随
    # 版本漂移（旧版曾失败也回 0），「产物文件存在」才是跨版本可靠的成功信号；
    # 先清掉旧产物防止误判成功。
    if os.path.exists(out_path):
        os.remove(out_path)
    scale = ["-s", "2"] if fmt == "png" else []
    # pdf 必须 --crop：裁到内容 bounding box 且强制单页。否则元素坐标越出
    # 页格（如居中文字左缘为负）时 CLI 会按页格分出空白页，
    # \includegraphics 默认取第 1 页就会嵌进空白。
    crop = ["--crop"] if fmt == "pdf" else []
    cmd = [cli, "-x", "-f", fmt, *scale, *crop, "-o", out_path, drawio_path]
    timeout = float(os.environ.get("GOAI_DRAWIO_TIMEOUT", "120"))
    # start_new_session：实测该 Electron CLI 在 TTY 前台进程组内跑到失败路径时，
    # 退出会连带挂掉整个前台进程组（终端手动起的 server 会被杀）；独立会话彻底
    # 隔离该怪癖，且超时可 killpg 连 GPU/utility 子进程一起清掉。
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, start_new_session=True)
    try:
        _, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        return _dumps({"ok": False, "error": f"drawio CLI 导出超时（{timeout:g}s）"})
    ok = os.path.exists(out_path)
    return _dumps({"ok": ok, "out": out_path if ok else None,
                   "returncode": proc.returncode,
                   "stderr": stderr[-500:] if not ok else ""})


@mcp.tool()
def list_figures(out_dir: str = "") -> str:
    """列出工作区已有图纸（figspec/svg/drawio 三套产物的对齐情况）。

    out_dir 缺省为 $GOAI_WORKSPACE/figures（与 render_figure 一致）。
    """
    out_dir = out_dir or _default_out_dir()
    inventory = {}
    for sub, ext in (("figspec", "json"), ("svg", "svg"),
                     ("drawio", "drawio"), ("png", "png")):
        for p in glob.glob(os.path.join(out_dir, sub, f"*.{ext}")):
            name = os.path.splitext(os.path.basename(p))[0]
            inventory.setdefault(name, {})[sub] = p
    rows = [{"name": k, **{s: s in v for s in ("figspec", "svg", "drawio", "png")}}
            for k, v in sorted(inventory.items())]
    return _dumps({"figures": rows, "detail": inventory})


if __name__ == "__main__":
    mcp.run()
