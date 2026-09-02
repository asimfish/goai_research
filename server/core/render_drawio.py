"""figspec → draw.io (mxGraph) XML 确定性渲染。

产物为原生 .drawio 文件：
- group → 容器 vertex（container=1，子节点相对坐标，拖动整组）
- node  → vertex（形状/配色/虚线与 SVG 渲染一致）
- edge  → orthogonalEdgeStyle 边，支持 label / 虚线 / waypoints
可直接用 draw.io Desktop / app.diagrams.net / 官方 @drawio/mcp 的
open_drawio_xml 打开继续编辑。
"""
from __future__ import annotations

from typing import Any
from xml.sax.saxutils import escape, quoteattr

from .figspec import DEFAULTS, edge_style_of, style_of, wrap_lines

# 与 render_svg.TEXT_WIDTH_RATIO 同步：各形状的有效文本宽度比例
_TEXT_WIDTH_RATIO = {
    "diamond": 0.55, "hexagon": 0.70, "ellipse": 0.72, "cloud": 0.62,
    "parallelogram": 0.78, "document": 0.85, "cylinder": 0.85,
    "rect": 0.90, "rounded": 0.90, "stadium": 0.86,
}


def _html_lines(text: str, w: float, font_size: float, bold: bool = False) -> str:
    """文字 → 显式 <br/> 折行的 HTML（html=1 会折叠 "\\n"，必须转成 <br/>）。

    行由 figspec.wrap_lines 决定（Helvetica 真实字宽 + 粗体系数），与 SVG 渲染和
    lint 完全一致：draw.io 自己的 whiteSpace=wrap 只作兜底，不再产生与 lint
    估算不同的行数。
    """
    return "<br/>".join(escape(line) for line in wrap_lines(text, w, font_size, bold))

_SHAPE_STYLE = {
    "rect": "rounded=0;whiteSpace=wrap;html=1;",
    "rounded": "rounded=1;whiteSpace=wrap;html=1;arcSize=12;",
    "stadium": "rounded=1;whiteSpace=wrap;html=1;arcSize=50;spacing=6;",
    # 斜边/弧边形状加 spacing，文字不贴边（与 SVG 渲染器的有效文本区一致）
    "ellipse": "ellipse;whiteSpace=wrap;html=1;spacing=8;",
    "diamond": "rhombus;whiteSpace=wrap;html=1;spacing=12;",
    "hexagon": ("shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;"
                "html=1;spacing=10;"),
    "parallelogram": ("shape=parallelogram;perimeter=parallelogramPerimeter;"
                      "whiteSpace=wrap;html=1;spacing=8;"),
    "cylinder": ("shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;"
                 "backgroundOutline=1;size=9;"),
    "document": "shape=document;whiteSpace=wrap;html=1;boundedLbl=1;",
    "cloud": "ellipse;shape=cloud;whiteSpace=wrap;html=1;spacing=10;",
}

SUBLABEL_RATIO = 0.85   # 与 render_svg 同步
SUBLABEL_MIN = 10.5


def _cell(cell_id: str, value: str, style: str, x: float, y: float,
          w: float, h: float, parent: str = "1") -> str:
    return (
        f'        <mxCell id={quoteattr(cell_id)} value={quoteattr(value)} '
        f'style={quoteattr(style)} vertex="1" parent={quoteattr(parent)}>\n'
        f'          <mxGeometry x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" '
        f'as="geometry" />\n'
        f'        </mxCell>')


def render(spec: dict[str, Any], page_name: str = "Page-1") -> str:
    W = spec["canvas"]["width"]
    H = spec["canvas"]["height"]
    groups = {g["id"]: g for g in spec.get("groups", [])}
    cells: list[str] = []

    if spec.get("title"):
        ts = spec.get("title_style") or {}
        t_fs = ts.get("font_size", 22)
        t_y = ts.get("y", 24)
        t_style = (f"text;html=1;align=center;verticalAlign=middle;fontSize={t_fs};"
                   f"fontColor={ts.get('color', '#1a1a1a')};"
                   "strokeColor=none;fillColor=none;")
        if ts.get("bold", True):
            t_style += "fontStyle=1;"
        cells.append(_cell("goai-title", escape(spec["title"]), t_style,
                           W / 2 - 240, t_y - 16, 480, 32))

    for g in spec.get("groups", []):
        style = (
            f"rounded=1;absoluteArcSize=1;arcSize={g.get('arc', 10)};"
            "whiteSpace=wrap;html=1;verticalAlign=top;"
            f"align=left;spacingLeft=10;spacingTop=4;"
            f"fontSize={g.get('font_size', 15)};fontStyle=1;"
            "container=1;collapsible=0;"
            f"fillColor={g.get('fill', '#F7F9FC')};"
            f"strokeColor={g.get('stroke', '#B9C4D0')};"
            f"strokeWidth={g.get('stroke_width', 1.2)};"
            f"fontColor={g.get('label_color', g.get('stroke', '#6B7A89'))};")
        if g.get("dashed"):
            style += "dashed=1;"
        if g.get("shadow"):
            style += "shadow=1;"
        cells.append(_cell(g["id"], escape(g.get("label", "")), style,
                           g["x"], g["y"], g["w"], g["h"]))

    for nd in spec.get("nodes", []):
        shape = nd.get("shape", "rect")
        style = _SHAPE_STYLE.get(shape, _SHAPE_STYLE["rect"])
        style += (f"fillColor={style_of(nd, spec, 'fill', DEFAULTS['fill'])};"
                  f"strokeColor={style_of(nd, spec, 'stroke', DEFAULTS['stroke'])};"
                  f"strokeWidth={style_of(nd, spec, 'stroke_width', 1.5)};"
                  f"fontSize={style_of(nd, spec, 'font_size', DEFAULTS['font_size'])};")
        if shape == "rounded" and nd.get("arc") is not None:
            style += f"absoluteArcSize=1;arcSize={nd['arc']};"
        if nd.get("label_color"):
            style += f"fontColor={nd['label_color']};"
        # 主标默认加粗；有 sublabel 时由 <b> 只包主标，避免副文一起变粗
        if nd.get("label_bold", True) and not nd.get("sublabel"):
            style += "fontStyle=1;"
        if nd.get("dashed"):
            style += "dashed=1;"
        if nd.get("shadow"):
            style += "shadow=1;"
        nd_fs = style_of(nd, spec, "font_size", DEFAULTS["font_size"])
        text_w = nd["w"] * _TEXT_WIDTH_RATIO.get(shape, 0.90)
        lab_bold = bool(nd.get("label_bold", True)) or bool(nd.get("sublabel"))
        value = _html_lines(nd.get("label", ""), text_w, nd_fs, bold=lab_bold)
        if nd.get("sublabel"):
            sub_px = max(nd_fs * SUBLABEL_RATIO, SUBLABEL_MIN)
            value = (f"<b>{value}</b><br/>"
                     f"<font style='font-size:{sub_px:g}px' "
                     f"color='{nd.get('sublabel_color', '#555555')}'>"
                     f"{_html_lines(nd['sublabel'], text_w, sub_px)}</font>")
        parent = "1"
        x, y = nd["x"], nd["y"]
        if nd.get("group") and nd["group"] in groups:
            parent = nd["group"]
            g = groups[parent]
            x, y = nd["x"] - g["x"], nd["y"] - g["y"]
        cells.append(_cell(nd["id"], value, style, x, y, nd["w"], nd["h"], parent))

    arrow_map = {"block": "endArrow=block;endFill=1;",
                 "open": "endArrow=open;endFill=0;",
                 "none": "endArrow=none;"}
    for i, e in enumerate(spec.get("edges", [])):
        eid = e.get("id") or f"edge-{i}"
        style = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;"
                 "jettySize=auto;orthogonalLoop=1;"
                 + arrow_map.get(e.get("arrow", "block"), arrow_map["block"])
                 + f"strokeColor={edge_style_of(e, spec, 'color', DEFAULTS['edge_color'])};"
                 + f"strokeWidth={edge_style_of(e, spec, 'width', DEFAULTS['edge_width'])};"
                 + f"fontSize={style_of(e, spec, 'font_size', 12.5)};")
        if e.get("dashed"):
            style += "dashed=1;"
        wps = e.get("waypoints") or []
        points = ""
        if wps:
            pts = "\n".join(
                f'              <mxPoint x="{p[0]:g}" y="{p[1]:g}" />' for p in wps)
            points = (f'\n            <Array as="points">\n{pts}\n'
                      f'            </Array>')
        label_html = "<br/>".join(escape(ln) for ln in (e.get("label") or "").split("\n"))
        cells.append(
            f'        <mxCell id={quoteattr(eid)} value={quoteattr(label_html)} '
            f'style={quoteattr(style)} edge="1" parent="1" '
            f'source={quoteattr(e["from"])} target={quoteattr(e["to"])}>\n'
            f'          <mxGeometry relative="1" as="geometry">{points}\n'
            f'          </mxGeometry>\n'
            f'        </mxCell>')

    for i, t in enumerate(spec.get("texts", [])):
        align = t.get("align", "center")
        style = (f"text;html=1;align={align};verticalAlign=middle;"
                 f"fontSize={t.get('font_size', 13)};"
                 f"fontColor={t.get('color', '#1a1a1a')};"
                 "strokeColor=none;fillColor=none;")
        if t.get("bold"):
            style += "fontStyle=1;"
        n_lines = t.get("text", "").count("\n") + 1
        est_w = max(max(len(ln) for ln in t.get("text", "").split("\n"))
                    * t.get("font_size", 12) * 0.7, 60)
        est_h = max(24, n_lines * t.get("font_size", 12) * 1.3)
        tx = t["x"] if align == "left" else (
            t["x"] - est_w if align == "right" else t["x"] - est_w / 2)
        text_html = "<br/>".join(escape(ln) for ln in t.get("text", "").split("\n"))
        cells.append(_cell(t.get("id") or f"text-{i}", text_html, style,
                           tx, t["y"] - est_h / 2, est_w, est_h))

    body = "\n".join(cells)
    return f'''<mxfile host="goai-research" agent="goai-figure-mcp" version="24.0.0">
  <diagram id="goai-0" name="{page_name}">
    <mxGraphModel dx="0" dy="0" grid="1" gridSize="10" guides="1" tooltips="1"
        connect="1" arrows="1" fold="1" page="1" pageScale="1"
        pageWidth="{W:g}" pageHeight="{H:g}" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
{body}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
'''
