"""figspec → SVG 确定性渲染（无第三方依赖）。"""
from __future__ import annotations

from typing import Any
from xml.sax.saxutils import escape

from .figspec import DEFAULTS, border_point, center, edge_style_of, style_of

FONT = "'Helvetica Neue', Helvetica, Arial, sans-serif"


def _shape_svg(nd: dict[str, Any], fill: str, stroke: str, dashed: bool,
               stroke_width: float = 1.5) -> str:
    x, y, w, h = nd["x"], nd["y"], nd["w"], nd["h"]
    shape = nd.get("shape", "rect")
    dash = ' stroke-dasharray="6,4"' if dashed else ""
    shadow = ' filter="url(#goai-shadow)"' if nd.get("shadow") else ""
    common = (f'fill="{fill}" stroke="{stroke}" '
              f'stroke-width="{stroke_width}"{dash}{shadow}')
    if shape in ("rect", "rounded", "stadium"):
        rx = 0 if shape == "rect" else (
            h / 2 if shape == "stadium" else nd.get("arc", 8))
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" {common}/>'
    if shape == "ellipse":
        return (f'<ellipse cx="{x + w / 2}" cy="{y + h / 2}" rx="{w / 2}" '
                f'ry="{h / 2}" {common}/>')
    if shape == "diamond":
        pts = f"{x + w / 2},{y} {x + w},{y + h / 2} {x + w / 2},{y + h} {x},{y + h / 2}"
        return f'<polygon points="{pts}" {common}/>'
    if shape == "hexagon":
        k = min(w * 0.2, h / 2)
        pts = (f"{x + k},{y} {x + w - k},{y} {x + w},{y + h / 2} "
               f"{x + w - k},{y + h} {x + k},{y + h} {x},{y + h / 2}")
        return f'<polygon points="{pts}" {common}/>'
    if shape == "parallelogram":
        k = min(w * 0.18, 24)
        pts = f"{x + k},{y} {x + w},{y} {x + w - k},{y + h} {x},{y + h}"
        return f'<polygon points="{pts}" {common}/>'
    if shape == "cylinder":
        ry = min(h * 0.15, 12)
        return (
            f'<path d="M {x} {y + ry} A {w / 2} {ry} 0 0 1 {x + w} {y + ry} '
            f'L {x + w} {y + h - ry} A {w / 2} {ry} 0 0 1 {x} {y + h - ry} Z" {common}/>'
            f'<ellipse cx="{x + w / 2}" cy="{y + ry}" rx="{w / 2}" ry="{ry}" {common}/>')
    if shape == "document":
        dip = min(h * 0.12, 10)
        return (f'<path d="M {x} {y} L {x + w} {y} L {x + w} {y + h - dip} '
                f'Q {x + w * 0.75} {y + h - 2 * dip} {x + w / 2} {y + h - dip} '
                f'Q {x + w * 0.25} {y + h} {x} {y + h - dip} Z" {common}/>')
    if shape == "cloud":
        r = h / 3
        return (
            f'<path d="M {x + r} {y + h * 0.7} '
            f'A {r} {r} 0 1 1 {x + w * 0.28} {y + h * 0.35} '
            f'A {r * 1.1} {r * 1.1} 0 1 1 {x + w * 0.62} {y + h * 0.3} '
            f'A {r} {r} 0 1 1 {x + w - r * 0.8} {y + h * 0.65} '
            f'A {r * 0.9} {r * 0.9} 0 0 1 {x + w - r} {y + h * 0.95} '
            f'L {x + r} {y + h * 0.95} A {r * 0.9} {r * 0.9} 0 0 1 {x + r} {y + h * 0.7} Z" '
            f'{common}/>')
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {common}/>'


def _wrap_label(label: str, w: float, font_size: float) -> list[str]:
    """按宽度粗略折行（CJK 记 1 字宽，拉丁按 0.55 字宽估算）。"""
    max_units = max(int(w / (font_size * 0.62)), 4)
    lines: list[str] = []
    for hard in (label or "").split("\n"):
        cur, units = "", 0.0
        for ch in hard:
            u = 1.0 if ord(ch) > 0x2E7F else 0.55
            if units + u > max_units and cur:
                lines.append(cur)
                cur, units = ch, u
            else:
                cur += ch
                units += u
        lines.append(cur)
    return lines or [""]


def _text_block(cx: float, cy: float, label: str, w: float, font_size: float,
                color: str = "#1a1a1a", bold: bool = False,
                anchor: str = "middle") -> str:
    lines = _wrap_label(label, w, font_size)
    lh = font_size * 1.25
    y0 = cy - lh * (len(lines) - 1) / 2
    weight = ' font-weight="bold"' if bold else ""
    spans = "".join(
        f'<text x="{cx}" y="{y0 + i * lh}" text-anchor="{anchor}" '
        f'dominant-baseline="middle" font-family="{FONT}" '
        f'font-size="{font_size}" fill="{color}"{weight}>{escape(line)}</text>'
        for i, line in enumerate(lines))
    return spans


def render(spec: dict[str, Any]) -> str:
    W = spec["canvas"]["width"]
    H = spec["canvas"]["height"]
    nodes = {nd["id"]: nd for nd in spec.get("nodes", [])}
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">',
        '<defs>'
        '<marker id="arrow-block" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker>'
        '<marker id="arrow-open" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10" fill="none" stroke="context-stroke" '
        'stroke-width="1.5"/></marker>'
        '<filter id="goai-shadow" x="-20%" y="-20%" width="140%" height="140%">'
        '<feDropShadow dx="0" dy="1.5" stdDeviation="2" flood-color="#2A3B47" '
        'flood-opacity="0.28"/></filter>'
        '</defs>',
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="#FFFFFF"/>',
    ]
    if spec.get("title"):
        ts = spec.get("title_style") or {}
        parts.append(_text_block(
            W / 2, ts.get("y", 24), spec["title"], W,
            ts.get("font_size", 16), ts.get("color", "#1a1a1a"),
            bool(ts.get("bold", True))))

    for g in spec.get("groups", []):
        fill = g.get("fill", "#F7F9FC")
        stroke = g.get("stroke", "#B9C4D0")
        gsw = g.get("stroke_width", 1.2)
        dash = ' stroke-dasharray="6,4"' if g.get("dashed") else ""
        shadow = ' filter="url(#goai-shadow)"' if g.get("shadow") else ""
        parts.append(
            f'<rect x="{g["x"]}" y="{g["y"]}" width="{g["w"]}" height="{g["h"]}" '
            f'rx="{g.get("arc", 10)}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{gsw}"{dash}{shadow}/>')
        if g.get("label"):
            g_fs = g.get("font_size", 12.5)
            parts.append(
                f'<text x="{g["x"] + 12}" y="{g["y"] + g_fs * 1.55}" '
                f'font-family="{FONT}" '
                f'font-size="{g_fs}" font-weight="bold" '
                f'fill="{g.get("label_color", stroke)}">'
                f'{escape(g["label"])}</text>')

    for e in spec.get("edges", []):
        src, dst = nodes[e["from"]], nodes[e["to"]]
        wps = [tuple(p) for p in (e.get("waypoints") or [])]
        p_start = border_point(src, wps[0] if wps else center(dst))
        p_end = border_point(dst, wps[-1] if wps else center(src))
        pts = [p_start, *wps, p_end]
        color = edge_style_of(e, spec, "color", DEFAULTS["edge_color"])
        width = edge_style_of(e, spec, "width", DEFAULTS["edge_width"])
        dash = ' stroke-dasharray="7,5"' if e.get("dashed") else ""
        arrow = e.get("arrow", "block")
        marker = "" if arrow == "none" else f' marker-end="url(#arrow-{arrow})"'
        d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        parts.append(f'<path d="{d}" fill="none" stroke="{color}" '
                     f'stroke-width="{width}"{dash}{marker}/>')
        if e.get("label"):
            mid = pts[len(pts) // 2] if len(pts) % 2 == 1 else (
                (pts[len(pts) // 2 - 1][0] + pts[len(pts) // 2][0]) / 2,
                (pts[len(pts) // 2 - 1][1] + pts[len(pts) // 2][1]) / 2)
            fs = style_of(e, spec, "font_size", 11)
            lab_lines = e["label"].split("\n")
            est_w = max(sum(1.0 if ord(c) > 0x2E7F else 0.55 for c in ln) * fs
                        for ln in lab_lines) + 8
            est_h = fs * 1.25 * (len(lab_lines) - 1) + fs * 1.5
            parts.append(
                f'<rect x="{mid[0] - est_w / 2}" y="{mid[1] - est_h / 2}" '
                f'width="{est_w}" height="{est_h}" fill="#FFFFFF" opacity="0.85"/>')
            parts.append(_text_block(mid[0], mid[1], e["label"], 10 ** 6, fs, color))

    for nd in spec.get("nodes", []):
        fill = style_of(nd, spec, "fill", DEFAULTS["fill"])
        stroke = style_of(nd, spec, "stroke", DEFAULTS["stroke"])
        fs = style_of(nd, spec, "font_size", DEFAULTS["font_size"])
        nsw = style_of(nd, spec, "stroke_width", 1.5)
        parts.append(_shape_svg(nd, fill, stroke, bool(nd.get("dashed")), nsw))
        cx, cy = center(nd)
        label = nd.get("label", "")
        lab_color = nd.get("label_color", "#1a1a1a")
        lab_bold = bool(nd.get("label_bold"))
        if nd.get("sublabel"):
            parts.append(_text_block(cx, cy - fs * 0.55, label, nd["w"], fs,
                                     color=lab_color, bold=True))
            parts.append(_text_block(cx, cy + fs * 0.75, nd["sublabel"], nd["w"],
                                     fs * 0.82,
                                     color=nd.get("sublabel_color", "#555555")))
        else:
            parts.append(_text_block(cx, cy, label, nd["w"], fs,
                                     color=lab_color, bold=lab_bold))

    anchor_map = {"left": "start", "center": "middle", "right": "end"}
    for t in spec.get("texts", []):
        parts.append(_text_block(
            t["x"], t["y"], t.get("text", ""), 10 ** 6,
            t.get("font_size", 12), t.get("color", "#1a1a1a"),
            bool(t.get("bold")),
            anchor_map.get(t.get("align", "center"), "middle")))

    parts.append("</svg>")
    return "\n".join(parts)
