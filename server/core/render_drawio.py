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
from xml.sax.saxutils import quoteattr

from .figspec import DEFAULTS, style_of

_SHAPE_STYLE = {
    "rect": "rounded=0;whiteSpace=wrap;html=1;",
    "rounded": "rounded=1;whiteSpace=wrap;html=1;arcSize=12;",
    "stadium": "rounded=1;whiteSpace=wrap;html=1;arcSize=50;",
    "ellipse": "ellipse;whiteSpace=wrap;html=1;",
    "diamond": "rhombus;whiteSpace=wrap;html=1;",
    "hexagon": "shape=hexagon;perimeter=hexagonPerimeter2;whiteSpace=wrap;html=1;",
    "parallelogram": ("shape=parallelogram;perimeter=parallelogramPerimeter;"
                      "whiteSpace=wrap;html=1;"),
    "cylinder": ("shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;"
                 "backgroundOutline=1;size=9;"),
    "document": "shape=document;whiteSpace=wrap;html=1;boundedLbl=1;",
    "cloud": "ellipse;shape=cloud;whiteSpace=wrap;html=1;",
}


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
        cells.append(_cell(
            "goai-title", spec["title"],
            "text;html=1;align=center;verticalAlign=middle;fontSize=16;"
            "fontStyle=1;strokeColor=none;fillColor=none;",
            W / 2 - 240, 4, 480, 32))

    for g in spec.get("groups", []):
        style = (
            "rounded=1;arcSize=6;whiteSpace=wrap;html=1;verticalAlign=top;"
            "align=left;spacingLeft=10;spacingTop=4;fontSize=12;fontStyle=1;"
            "container=1;collapsible=0;"
            f"fillColor={g.get('fill', '#F7F9FC')};"
            f"strokeColor={g.get('stroke', '#B9C4D0')};"
            f"fontColor={g.get('stroke', '#6B7A89')};")
        if g.get("dashed"):
            style += "dashed=1;"
        cells.append(_cell(g["id"], g.get("label", ""), style,
                           g["x"], g["y"], g["w"], g["h"]))

    for nd in spec.get("nodes", []):
        shape = nd.get("shape", "rect")
        style = _SHAPE_STYLE.get(shape, _SHAPE_STYLE["rect"])
        style += (f"fillColor={style_of(nd, spec, 'fill', DEFAULTS['fill'])};"
                  f"strokeColor={style_of(nd, spec, 'stroke', DEFAULTS['stroke'])};"
                  f"fontSize={style_of(nd, spec, 'font_size', DEFAULTS['font_size'])};")
        if nd.get("dashed"):
            style += "dashed=1;"
        value = nd.get("label", "")
        if nd.get("sublabel"):
            value = (f"<b>{nd.get('label', '')}</b><br/>"
                     f"<font style='font-size:0.85em' color='#555555'>"
                     f"{nd['sublabel']}</font>")
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
                 + f"strokeColor={style_of(e, spec, 'color', DEFAULTS['edge_color'])};"
                 + f"strokeWidth={style_of(e, spec, 'width', DEFAULTS['edge_width'])};"
                 + f"fontSize={style_of(e, spec, 'font_size', 11)};")
        if e.get("dashed"):
            style += "dashed=1;"
        wps = e.get("waypoints") or []
        points = ""
        if wps:
            pts = "\n".join(
                f'              <mxPoint x="{p[0]:g}" y="{p[1]:g}" />' for p in wps)
            points = (f'\n            <Array as="points">\n{pts}\n'
                      f'            </Array>')
        cells.append(
            f'        <mxCell id={quoteattr(eid)} value={quoteattr(e.get("label", ""))} '
            f'style={quoteattr(style)} edge="1" parent="1" '
            f'source={quoteattr(e["from"])} target={quoteattr(e["to"])}>\n'
            f'          <mxGeometry relative="1" as="geometry">{points}\n'
            f'          </mxGeometry>\n'
            f'        </mxCell>')

    for i, t in enumerate(spec.get("texts", [])):
        style = ("text;html=1;align=center;verticalAlign=middle;"
                 f"fontSize={t.get('font_size', 12)};"
                 f"fontColor={t.get('color', '#1a1a1a')};"
                 "strokeColor=none;fillColor=none;")
        if t.get("bold"):
            style += "fontStyle=1;"
        est_w = max(len(t.get("text", "")) * t.get("font_size", 12) * 0.7, 60)
        cells.append(_cell(t.get("id") or f"text-{i}", t.get("text", ""), style,
                           t["x"] - est_w / 2, t["y"] - 12, est_w, 24))

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
