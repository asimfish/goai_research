"""SVG → figspec（近似逆向）→ 可再渲染为 .drawio 可编辑文件。

适用范围：结构化 SVG（矢量框图 —— rect/ellipse/circle/polygon/line/
polyline/path(简单 M..L)/text/tspan）。对复杂路径与位图内容无能为力，
该场景请走 goai-figure-editable skill 的「视觉重建 figspec」路线
（参考 image-to-editable-ppt 的重建→自检→修正回环）。
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any, Optional

_SVG_NS = "{http://www.w3.org/2000/svg}"


def _tag(el: ET.Element) -> str:
    return el.tag.replace(_SVG_NS, "")


def _f(el: ET.Element, attr: str, default: float = 0.0) -> float:
    try:
        return float(re.sub(r"[^0-9.eE+-]", "", el.get(attr, "") or "") or default)
    except ValueError:
        return default


def _style_attr(el: ET.Element, name: str) -> Optional[str]:
    if el.get(name):
        return el.get(name)
    style = el.get("style", "")
    m = re.search(rf"(?:^|;)\s*{name}\s*:\s*([^;]+)", style)
    return m.group(1).strip() if m else None


def _walk(el: ET.Element, transform: tuple[float, float] = (0.0, 0.0)):
    """扁平化遍历，只累计 translate 平移（常见导出器的主要变换）。"""
    tx, ty = transform
    t = el.get("transform", "")
    m = re.search(r"translate\(\s*([0-9.eE+-]+)[ ,]*([0-9.eE+-]+)?\s*\)", t)
    if m:
        tx += float(m.group(1))
        ty += float(m.group(2) or 0)
    yield el, (tx, ty)
    for child in el:
        yield from _walk(child, (tx, ty))


def svg_to_figspec(svg_text: str) -> dict[str, Any]:
    root = ET.fromstring(svg_text)
    width = _f(root, "width", 1200) or 1200
    height = _f(root, "height", 800) or 800

    nodes: list[dict[str, Any]] = []
    lines: list[dict[str, Any]] = []
    texts: list[dict[str, Any]] = []
    nid = 0

    for el, (tx, ty) in _walk(root):
        tag = _tag(el)
        fill = _style_attr(el, "fill") or "#FFFFFF"
        stroke = _style_attr(el, "stroke") or "#333333"
        dashed = bool(_style_attr(el, "stroke-dasharray"))
        if tag == "rect":
            w, h = _f(el, "width"), _f(el, "height")
            if w >= width * 0.98 and h >= height * 0.98:
                continue  # 背景板
            if _style_attr(el, "stroke") is None:
                continue  # 无描边矩形是装饰/label 底衬，不是节点
            nid += 1
            rx = _f(el, "rx")
            shape = "rect" if rx == 0 else ("stadium" if rx >= h / 2 - 1 else "rounded")
            nodes.append({"id": f"n{nid}", "label": "", "shape": shape,
                          "x": _f(el, "x") + tx, "y": _f(el, "y") + ty,
                          "w": w, "h": h, "fill": fill, "stroke": stroke,
                          "dashed": dashed})
        elif tag in ("ellipse", "circle"):
            nid += 1
            if tag == "circle":
                r = _f(el, "r")
                rx_, ry_ = r, r
            else:
                rx_, ry_ = _f(el, "rx"), _f(el, "ry")
            nodes.append({"id": f"n{nid}", "label": "", "shape": "ellipse",
                          "x": _f(el, "cx") + tx - rx_, "y": _f(el, "cy") + ty - ry_,
                          "w": rx_ * 2, "h": ry_ * 2, "fill": fill,
                          "stroke": stroke, "dashed": dashed})
        elif tag == "polygon":
            pts = _parse_points(el.get("points", ""))
            if len(pts) < 3:
                continue
            nid += 1
            xs = [p[0] + tx for p in pts]
            ys = [p[1] + ty for p in pts]
            shape = {4: "diamond", 6: "hexagon"}.get(len(pts), "rect")
            if len(pts) == 4 and _is_axis_aligned_quad(pts):
                shape = "parallelogram"
            nodes.append({"id": f"n{nid}", "label": "", "shape": shape,
                          "x": min(xs), "y": min(ys),
                          "w": max(xs) - min(xs), "h": max(ys) - min(ys),
                          "fill": fill, "stroke": stroke, "dashed": dashed})
        elif tag == "line":
            lines.append({"pts": [(_f(el, "x1") + tx, _f(el, "y1") + ty),
                                  (_f(el, "x2") + tx, _f(el, "y2") + ty)],
                          "color": stroke, "dashed": dashed,
                          "arrow": "block" if el.get("marker-end") else "none"})
        elif tag == "polyline":
            pts = [(p[0] + tx, p[1] + ty) for p in _parse_points(el.get("points", ""))]
            if len(pts) >= 2:
                lines.append({"pts": pts, "color": stroke, "dashed": dashed,
                              "arrow": "block" if el.get("marker-end") else "none"})
        elif tag == "path":
            d = el.get("d", "")
            pts = _simple_path_points(d)
            filled = (_style_attr(el, "fill") or "none").lower()
            if pts and len(pts) >= 2 and filled in ("none", "transparent"):
                lines.append({"pts": [(p[0] + tx, p[1] + ty) for p in pts],
                              "color": stroke, "dashed": dashed,
                              "arrow": "block" if el.get("marker-end") else "none"})
        elif tag == "text":
            content = "".join(el.itertext()).strip()
            if not content:
                continue
            texts.append({"x": _f(el, "x") + tx, "y": _f(el, "y") + ty,
                          "text": content,
                          "font_size": _f(el, "font-size", 12) or 12,
                          "bold": (_style_attr(el, "font-weight") or "") == "bold"})

    # 容器识别：完全包含其他节点的矩形是分组底板，不是节点
    # （render_svg 的 group 即此形态；不识别会与成员判「节点重叠」）
    containers: list[dict[str, Any]] = []
    for ndd in list(nodes):
        if ndd["shape"] not in ("rect", "rounded", "stadium"):
            continue
        inner = [o for o in nodes if o is not ndd and _contains(ndd, o)]
        big = all(ndd["w"] * ndd["h"] >= 3 * o["w"] * o["h"] for o in inner)
        if inner and (len(inner) >= 2 or big):
            containers.append(ndd)
            nodes.remove(ndd)
    groups = []
    for i, c in enumerate(containers):
        gid = f"g{i + 1}"
        # 成员归属：包含该节点的最小容器（支持容器并排/嵌套）
        for ndd in nodes:
            mine = [cc for cc in containers if _contains(cc, ndd)]
            if mine and min(mine, key=lambda cc: cc["w"] * cc["h"]) is c:
                ndd["group"] = gid
        groups.append({"id": gid, "label": c["label"], "x": c["x"], "y": c["y"],
                       "w": c["w"], "h": c["h"], "fill": c["fill"],
                       "stroke": c["stroke"], "dashed": c["dashed"]})

    # 线段 → 边：端点各自吸附最近节点（容器不参与）
    edges = []
    edge_mids: list[tuple[float, float, dict[str, Any]]] = []
    for i, ln in enumerate(lines):
        src = _nearest_node(nodes, ln["pts"][0])
        dst = _nearest_node(nodes, ln["pts"][-1])
        if src is None or dst is None or src["id"] == dst["id"]:
            continue
        mid = ln["pts"][1:-1]
        e = {"id": f"e{i}", "from": src["id"], "to": dst["id"],
             "color": ln["color"], "dashed": ln["dashed"],
             "arrow": ln["arrow"],
             **({"waypoints": [[p[0], p[1]] for p in mid]} if mid else {})}
        edges.append(e)
        pts = ln["pts"]
        m = pts[len(pts) // 2] if len(pts) % 2 == 1 else (
            (pts[len(pts) // 2 - 1][0] + pts[len(pts) // 2][0]) / 2,
            (pts[len(pts) // 2 - 1][1] + pts[len(pts) // 2][1]) / 2)
        edge_mids.append((m[0], m[1], e))

    # 文本吸附优先级：最小包含节点 → 邻近边中点(edge label) → 最小包含组 → 独立文本
    free_texts = []
    for t in texts:
        hosts = [ndd for ndd in nodes
                 if (ndd["x"] <= t["x"] <= ndd["x"] + ndd["w"]
                     and ndd["y"] <= t["y"] <= ndd["y"] + ndd["h"])]
        if hosts:
            host = min(hosts, key=lambda n: n["w"] * n["h"])
            host["label"] = (host["label"] + "\n" + t["text"]).strip()
            continue
        near = [(abs(t["x"] - mx) + abs(t["y"] - my), e)
                for mx, my, e in edge_mids
                if abs(t["x"] - mx) + abs(t["y"] - my) <= 3 * t.get("font_size", 12)]
        if near:
            e = min(near)[1]
            e["label"] = (e.get("label", "") + " " + t["text"]).strip()
            continue
        g_hosts = [g for g in groups
                   if (g["x"] <= t["x"] <= g["x"] + g["w"]
                       and g["y"] <= t["y"] <= g["y"] + g["h"])]
        if g_hosts:
            g = min(g_hosts, key=lambda gg: gg["w"] * gg["h"])
            g["label"] = (g["label"] + " " + t["text"]).strip()
        else:
            free_texts.append(t)

    return {"title": "", "canvas": {"width": width, "height": height},
            "groups": groups, "nodes": nodes, "edges": edges,
            "texts": [{"id": f"t{i}", **t} for i, t in enumerate(free_texts)]}


def _contains(outer: dict[str, Any], inner: dict[str, Any], eps: float = 1.0) -> bool:
    return (outer["x"] - eps <= inner["x"]
            and outer["y"] - eps <= inner["y"]
            and inner["x"] + inner["w"] <= outer["x"] + outer["w"] + eps
            and inner["y"] + inner["h"] <= outer["y"] + outer["h"] + eps)


def _parse_points(s: str) -> list[tuple[float, float]]:
    vals = [float(v) for v in re.findall(r"[-0-9.eE+]+", s)]
    return list(zip(vals[::2], vals[1::2]))


def _simple_path_points(d: str) -> Optional[list[tuple[float, float]]]:
    """仅解析 M/L（绝对）折线路径；含曲线/闭合的返回 None。"""
    if re.search(r"[CcQqAaSsTtZzHhVv]", d):
        return None
    vals = [float(v) for v in re.findall(r"[-0-9.eE+]+", d)]
    if len(vals) < 4 or len(vals) % 2:
        return None
    return list(zip(vals[::2], vals[1::2]))


def _is_axis_aligned_quad(pts: list[tuple[float, float]]) -> bool:
    ys = sorted({round(p[1], 1) for p in pts})
    return len(ys) == 2  # 上下两条水平边 → 平行四边形


def _nearest_node(nodes: list[dict[str, Any]],
                  pt: tuple[float, float], max_dist: float = 60.0):
    best, best_d = None, max_dist
    for ndd in nodes:
        cx, cy = ndd["x"] + ndd["w"] / 2, ndd["y"] + ndd["h"] / 2
        dx = max(abs(pt[0] - cx) - ndd["w"] / 2, 0)
        dy = max(abs(pt[1] - cy) - ndd["h"] / 2, 0)
        d = (dx * dx + dy * dy) ** 0.5
        if d < best_d:
            best, best_d = ndd, d
    return best
