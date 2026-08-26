"""figspec —— 论文框架图的结构化中间表示（单一事实源）。

同一份 figspec 确定性渲染为两种产物：
  - SVG（论文排版直接使用）
  - .drawio mxGraph XML（drawio 原生可编辑，含分组容器）

schema（JSON）：
{
  "title": str,
  "canvas": {"width": int, "height": int},
  "defaults": {"font_size": 13, "fill": "#FFFFFF", "stroke": "#333333"},
  "groups": [{"id","label","x","y","w","h","fill","stroke","dashed"}],
  "nodes":  [{"id","label","sublabel","x","y","w","h","shape","fill","stroke",
              "font_size","dashed","group"}],
  "edges":  [{"id","from","to","label","dashed","color","width","arrow",
              "waypoints": [[x,y],...]}],
  "texts":  [{"id","text","x","y","font_size","color","bold"}]
}
shape ∈ {rect, rounded, stadium, ellipse, diamond, hexagon, parallelogram,
         cylinder, document, cloud}
坐标系：x/y 为左上角，画布左上为原点。
"""
from __future__ import annotations

import json
from typing import Any

SHAPES = {"rect", "rounded", "stadium", "ellipse", "diamond", "hexagon",
          "parallelogram", "cylinder", "document", "cloud"}
ARROWS = {"block", "open", "none"}

DEFAULTS = {"font_size": 13, "fill": "#FFFFFF", "stroke": "#333333",
            "edge_color": "#333333", "edge_width": 1.5}


def validate(spec: dict[str, Any]) -> list[str]:
    """返回问题列表；空列表 = 通过。"""
    errs: list[str] = []
    if not isinstance(spec, dict):
        return ["figspec 必须是 JSON 对象"]
    canvas = spec.get("canvas") or {}
    if not (isinstance(canvas.get("width"), (int, float))
            and isinstance(canvas.get("height"), (int, float))):
        errs.append("canvas.width / canvas.height 必须为数字")

    ids: set[str] = set()
    group_ids: set[str] = set()
    for g in spec.get("groups", []):
        gid = g.get("id")
        if not gid:
            errs.append("group 缺少 id")
            continue
        if gid in ids:
            errs.append(f"id 重复: {gid}")
        ids.add(gid)
        group_ids.add(gid)
        for k in ("x", "y", "w", "h"):
            if not isinstance(g.get(k), (int, float)):
                errs.append(f"group {gid} 缺少数值字段 {k}")

    node_ids: set[str] = set()
    for nd in spec.get("nodes", []):
        nid = nd.get("id")
        if not nid:
            errs.append("node 缺少 id")
            continue
        if nid in ids:
            errs.append(f"id 重复: {nid}")
        ids.add(nid)
        node_ids.add(nid)
        for k in ("x", "y", "w", "h"):
            if not isinstance(nd.get(k), (int, float)):
                errs.append(f"node {nid} 缺少数值字段 {k}")
        shape = nd.get("shape", "rect")
        if shape not in SHAPES:
            errs.append(f"node {nid} 的 shape『{shape}』不在支持列表 {sorted(SHAPES)}")
        if nd.get("group") and nd["group"] not in group_ids:
            errs.append(f"node {nid} 引用了不存在的 group {nd['group']}")

    for e in spec.get("edges", []):
        eid = e.get("id") or f"{e.get('from')}->{e.get('to')}"
        if e.get("from") not in node_ids:
            errs.append(f"edge {eid} 的 from『{e.get('from')}』不是已知节点")
        if e.get("to") not in node_ids:
            errs.append(f"edge {eid} 的 to『{e.get('to')}』不是已知节点")
        if e.get("arrow", "block") not in ARROWS:
            errs.append(f"edge {eid} 的 arrow 必须是 {sorted(ARROWS)}")
        for wp in e.get("waypoints") or []:
            if not (isinstance(wp, (list, tuple)) and len(wp) == 2):
                errs.append(f"edge {eid} 的 waypoint 必须是 [x, y]")

    # 节点重叠检查（同层重叠通常是布局错误）
    nodes = spec.get("nodes", [])
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = nodes[i], nodes[j]
            if not all(isinstance(v.get(k), (int, float))
                       for v in (a, b) for k in ("x", "y", "w", "h")):
                continue
            if (a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"]
                    and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]):
                errs.append(f"节点重叠: {a['id']} 与 {b['id']}")
    return errs


def loads(text: str) -> dict[str, Any]:
    spec = json.loads(text)
    errs = validate(spec)
    if errs:
        raise ValueError("figspec 校验失败:\n- " + "\n- ".join(errs))
    return spec


def style_of(item: dict[str, Any], spec: dict[str, Any], key: str, fallback: Any) -> Any:
    return item.get(key, (spec.get("defaults") or {}).get(key, fallback))


def border_point(nd: dict[str, Any], toward: tuple[float, float]) -> tuple[float, float]:
    """从节点中心指向 toward 的射线与节点边框的交点（矩形近似）。"""
    cx, cy = nd["x"] + nd["w"] / 2, nd["y"] + nd["h"] / 2
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    scale_x = (nd["w"] / 2) / abs(dx) if dx else float("inf")
    scale_y = (nd["h"] / 2) / abs(dy) if dy else float("inf")
    s = min(scale_x, scale_y)
    return cx + dx * s, cy + dy * s


def center(nd: dict[str, Any]) -> tuple[float, float]:
    return nd["x"] + nd["w"] / 2, nd["y"] + nd["h"] / 2
