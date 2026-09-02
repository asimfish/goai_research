"""aesthetics —— figspec 美学 lint：把 figure-studio skill 里的视觉规范机械化。

排版 lint（figspec.lint）管「读得清」；本模块管「像不像顶刊图」：
1. 配色克制：非中性色按色相聚成色系，≤2 主题色 + 1 强调色；≥4 色系 = error
2. 彩虹泳道：≥2 个分组用饱和底色且色系不同 = error（学术图用浅灰/淡色分区）
3. 饱和色块比例：饱和填充的节点占比过高 = warning（应为白/淡底 + 中饱和描边）
4. 近失对齐：并排/竖排节点坐标差 1–8px（差一点对齐）= warning
5. 兄弟尺寸：同组同形状节点尺寸差 <12% 且非零 = warning（要么相等要么明显不同）
6. 越界 / 留白失衡：内容超出画布 = error；单侧留白 >18% 且另一侧紧 = warning
7. 间距过密：同组相邻节点间隙 < 0.7×字号 = warning
8. 连线穿节点：边的直线段穿过非端点节点 = warning
9. 交叉过多：边两两交叉数超过阈值 = warning
10. 描边粗细超过 2 档 / 标题字号不是全图最大 = warning

所有阈值集中在 AESTHETIC，与 skills/goai-figure-studio/SKILL.md 的合同条款一一对应。
"""
from __future__ import annotations

import colorsys
import itertools
from typing import Any

AESTHETIC = {
    "neutral_sat": 0.12,            # 饱和度低于此 = 灰阶/中性
    "neutral_light_hi": 0.93,       # 亮度高于此 = 近白（淡底色不计色系）
    "neutral_light_lo": 0.12,       # 亮度低于此 = 近黑
    "hue_bucket_deg": 30,           # 色相聚类桶宽
    "hue_families_ok": 2,           # ≤2 主题色无提示
    "hue_families_warn": 3,         # 3 = 含 1 强调色 → warning
    "lane_sat": 0.22,               # 分组底色饱和度超过此 = 彩色泳道
    "lane_light_max": 0.90,
    "sat_node_sat": 0.45,           # 节点填充判饱和色块
    "sat_node_light_max": 0.82,
    "sat_node_frac_warn": 0.40,     # 饱和色块节点占比告警线
    "align_tol_px": 8.0,            # 近失对齐上限（更大视为有意错开）
    "align_min_px": 1.0,            # 亚像素差肉眼不可见，不报
    "size_tol_ratio": 0.12,         # 兄弟尺寸「近似而不相等」阈值
    "margin_warn_ratio": 0.18,      # 单侧留白占画布比例
    "min_gap_font_ratio": 0.7,      # 同组节点最小间隙（×字号）
    "crossings_warn_min": 3,
    "crossings_warn_ratio": 0.35,   # 交叉数 > max(min, ratio×边数) → warning
    "max_reports_per_check": 6,     # 每类问题最多列出几条，避免刷屏
    "badge_area_ratio": 0.35,       # 面积比低于此 = 徽章/芯片从属母卡，不参与对齐与间距检查
}

_NAMED = {"white": "#FFFFFF", "black": "#000000", "gray": "#808080",
          "grey": "#808080", "none": None, "transparent": None}


def _hex_to_hls(color: Any) -> tuple[float, float, float] | None:
    """'#RRGGBB'/'#RGB'/少量颜色名 → (hue°, lightness, saturation)；无法解析返回 None。"""
    if not isinstance(color, str):
        return None
    c = color.strip()
    if c.lower() in _NAMED:
        c = _NAMED[c.lower()]
        if c is None:
            return None
    if not c.startswith("#"):
        return None
    c = c[1:]
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        return None
    try:
        r, g, b = (int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return None
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, l, s


def _is_neutral(hls: tuple[float, float, float]) -> bool:
    _, l, s = hls
    return (s < AESTHETIC["neutral_sat"] or l > AESTHETIC["neutral_light_hi"]
            or l < AESTHETIC["neutral_light_lo"])


def _hue_families(hues: list[float]) -> list[list[float]]:
    """色相（度）聚类：排序后相邻差 < 桶宽归一族（首尾跨 360 合并）。"""
    if not hues:
        return []
    hs = sorted(hues)
    fams: list[list[float]] = [[hs[0]]]
    for h in hs[1:]:
        if h - fams[-1][-1] < AESTHETIC["hue_bucket_deg"]:
            fams[-1].append(h)
        else:
            fams.append([h])
    if len(fams) > 1 and (hs[0] + 360) - fams[-1][-1] < AESTHETIC["hue_bucket_deg"]:
        fams[0] = fams[-1] + fams[0]
        fams.pop()
    return fams


def _is_badge_pair(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """一方面积远小于另一方 = 徽章/芯片贴附母卡（skill 规定外置母卡正下方、间隙≈4px），
    对齐与间距规则不适用。"""
    aa, ab = a["w"] * a["h"], b["w"] * b["h"]
    if min(aa, ab) < AESTHETIC["badge_area_ratio"] * max(aa, ab):
        return True
    # 等宽但很矮的条带贴在卡片上下（端点徽章、状态条）同样是从属关系
    short = min(a["h"], b["h"]) / max(a["h"], b["h"])
    x_overlap = a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"]
    return short < 0.5 and x_overlap


def _geom_ok(item: dict[str, Any]) -> bool:
    return all(isinstance(item.get(k), (int, float)) for k in ("x", "y", "w", "h"))


def _seg_hits_rect(p: tuple[float, float], q: tuple[float, float],
                   rect: tuple[float, float, float, float], shrink: float = 2.0) -> bool:
    """线段 p→q 是否穿过矩形 (x, y, w, h)（内缩 shrink，贴边经过不算）。Liang–Barsky。"""
    x0, y0 = p
    x1, y1 = q
    xmin, ymin = rect[0] + shrink, rect[1] + shrink
    xmax, ymax = rect[0] + rect[2] - shrink, rect[1] + rect[3] - shrink
    if xmax <= xmin or ymax <= ymin:
        return False
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for pk, qk in ((-dx, x0 - xmin), (dx, xmax - x0), (-dy, y0 - ymin), (dy, ymax - y0)):
        if pk == 0:
            if qk < 0:
                return False
            continue
        t = qk / pk
        if pk < 0:
            if t > t1:
                return False
            t0 = max(t0, t)
        else:
            if t < t0:
                return False
            t1 = min(t1, t)
    return t0 < t1


def _segments_cross(a: tuple, b: tuple, c: tuple, d: tuple) -> bool:
    """线段 ab 与 cd 是否严格相交（共端点不算）。"""
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return (o1 * o2 < 0) and (o3 * o4 < 0)


def _edge_key(e: dict[str, Any]) -> str:
    return e.get("id") or f"{e.get('from')}->{e.get('to')}"


def _edge_polyline(e: dict[str, Any],
                   nodes: dict[str, dict[str, Any]]) -> list[tuple[float, float]]:
    """边的折线（与渲染器/排版 lint 共用 figspec.edge_points）。"""
    from server.core.figspec import edge_points
    return edge_points(e, nodes)


def lint_aesthetics(spec: dict[str, Any]) -> dict[str, list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    cap = AESTHETIC["max_reports_per_check"]
    d = spec.get("defaults") or {}
    nodes = [n for n in spec.get("nodes", []) if _geom_ok(n)]
    labeled = [n for n in nodes if n.get("label") or n.get("sublabel")]
    groups = [g for g in spec.get("groups", []) if _geom_ok(g)]
    edges = spec.get("edges", [])
    texts = spec.get("texts", [])
    by_id = {n.get("id"): n for n in nodes}
    canvas = spec.get("canvas") or {}
    W, H = canvas.get("width"), canvas.get("height")
    base_fs = d.get("font_size", 15)

    # ---- 1. 配色克制 ----
    color_uses: list[tuple[Any, str]] = []
    for n in nodes:
        for k in ("fill", "stroke", "label_color"):
            color_uses.append((n.get(k, d.get(k)), f"node {n.get('id')}.{k}"))
    for g in groups:
        for k in ("fill", "stroke", "label_color"):
            color_uses.append((g.get(k), f"group {g.get('id')}.{k}"))
    for e in edges:
        color_uses.append((e.get("color", d.get("edge_color")), f"edge {_edge_key(e)}"))
    for t in texts:
        color_uses.append((t.get("color"), f"text {t.get('id', '?')}"))
    color_uses.append(((spec.get("title_style") or {}).get("color"), "title"))

    chroma: dict[str, tuple[float, list[str]]] = {}   # hex → (hue, where)
    for col, where in color_uses:
        hls = _hex_to_hls(col)
        if hls is None or _is_neutral(hls):
            continue
        chroma.setdefault(col.upper(), (hls[0], []))[1].append(where)
    fams = _hue_families([h for h, _ in chroma.values()])
    if len(fams) >= AESTHETIC["hue_families_warn"]:
        fam_desc = []
        for fam in fams:
            hexes = sorted({k for k, (h, _) in chroma.items() if h in fam})
            fam_desc.append("/".join(hexes[:3]))
        msg = (f"配色用了 {len(fams)} 个色系（{'; '.join(fam_desc)}）——顶刊图基线是 "
               f"≤{AESTHETIC['hue_families_ok']} 主题色 + 1 个强调色，其余信息用灰阶与线型区分")
        (errors if len(fams) > AESTHETIC["hue_families_warn"] else warnings).append(msg)

    # ---- 2. 彩虹泳道 ----
    lane_hues: list[tuple[str, float]] = []
    for g in groups:
        hls = _hex_to_hls(g.get("fill"))
        if hls and hls[2] >= AESTHETIC["lane_sat"] and hls[1] <= AESTHETIC["lane_light_max"]:
            lane_hues.append((g.get("id", "?"), hls[0]))
    if len(lane_hues) >= 2 and len(_hue_families([h for _, h in lane_hues])) >= 2:
        errors.append(
            f"彩虹泳道: 分组 {[gid for gid, _ in lane_hues]} 各铺一种饱和底色——"
            "分区改用浅灰/极淡同色系底 + 描边区分，颜色只留给语义")

    # ---- 3. 饱和色块比例 ----
    if labeled:
        sat_nodes = []
        for n in labeled:
            hls = _hex_to_hls(n.get("fill", d.get("fill")))
            if (hls and hls[2] >= AESTHETIC["sat_node_sat"]
                    and hls[1] <= AESTHETIC["sat_node_light_max"]):
                sat_nodes.append(n.get("id"))
        frac = len(sat_nodes) / len(labeled)
        if frac > AESTHETIC["sat_node_frac_warn"] and len(sat_nodes) >= 3:
            warnings.append(
                f"{len(sat_nodes)}/{len(labeled)} 个节点用饱和填充（{sat_nodes[:cap]}…）——"
                "学术图以白/淡底 + 中饱和描边为主，深底白字只留给标题带/头带")

    # ---- 4. 近失对齐 ----
    tol, lo = AESTHETIC["align_tol_px"], AESTHETIC["align_min_px"]
    near = []
    for a, b in itertools.combinations(labeled, 2):
        if _is_badge_pair(a, b):
            continue
        ax2, bx2 = a["x"] + a["w"], b["x"] + b["w"]
        ay2, by2 = a["y"] + a["h"], b["y"] + b["h"]
        x_overlap = a["x"] < bx2 and b["x"] < ax2
        y_overlap = a["y"] < by2 and b["y"] < ay2
        # 顶/中/底（或左/中/右）任一对齐即视为对齐；全不对齐且最小差落在
        # (lo, tol] 才是「差一点对齐」。高度不同但顶边对齐的并排节点不误报。
        if not x_overlap:   # 并排
            diffs = {"顶边": abs(a["y"] - b["y"]),
                     "中线": abs((a["y"] + a["h"] / 2) - (b["y"] + b["h"] / 2)),
                     "底边": abs(ay2 - by2)}
            if min(diffs.values()) >= lo:
                what, diff = min(diffs.items(), key=lambda kv: kv[1])
                if diff <= tol:
                    near.append(f"{a.get('id')}↔{b.get('id')} {what}差 {diff:.0f}px")
        if not y_overlap:   # 竖排
            diffs = {"左边": abs(a["x"] - b["x"]),
                     "中线": abs((a["x"] + a["w"] / 2) - (b["x"] + b["w"] / 2)),
                     "右边": abs(ax2 - bx2)}
            if min(diffs.values()) >= lo:
                what, diff = min(diffs.items(), key=lambda kv: kv[1])
                if diff <= tol:
                    near.append(f"{a.get('id')}↔{b.get('id')} {what}差 {diff:.0f}px")
    if near:
        warnings.append("近失对齐（差一点对齐最显业余，要么对齐要么明显错开）: "
                        + "; ".join(near[:cap]) + ("…" if len(near) > cap else ""))

    # ---- 5. 兄弟尺寸一致 ----
    sib: dict[tuple, list[dict]] = {}
    for n in labeled:
        sib.setdefault((n.get("group"), n.get("shape", "rect")), []).append(n)
    size_msgs = []
    for (gid, shape), members in sib.items():
        if len(members) < 2:
            continue
        for dim in ("w", "h"):
            vals = sorted({round(m[dim], 1) for m in members})
            if len(vals) < 2:
                continue
            for v1, v2 in itertools.combinations(vals, 2):
                if 0 < abs(v1 - v2) < AESTHETIC["size_tol_ratio"] * max(v1, v2):
                    size_msgs.append(f"group {gid or '(无)'} 的 {shape} 节点 {dim} 有 {v1} 与 {v2}")
                    break
    if size_msgs:
        warnings.append("兄弟节点尺寸近似而不相等（统一尺寸或拉开差距）: "
                        + "; ".join(size_msgs[:cap]))

    # ---- 6. 越界 / 留白失衡 ----
    if isinstance(W, (int, float)) and isinstance(H, (int, float)) and (nodes or groups):
        items = nodes + groups
        minx, maxx = min(i["x"] for i in items), max(i["x"] + i["w"] for i in items)
        miny, maxy = min(i["y"] for i in items), max(i["y"] + i["h"] for i in items)
        if minx < -0.5 or miny < -0.5 or maxx > W + 0.5 or maxy > H + 0.5:
            errors.append(f"内容 bbox x[{minx:.0f},{maxx:.0f}] y[{miny:.0f},{maxy:.0f}] "
                          f"越出画布 {W}×{H}（放大画布或移回内容，越界会被裁切）")
        else:
            margins = {"左": minx, "右": W - maxx, "上": miny, "下": H - maxy}
            r = AESTHETIC["margin_warn_ratio"]
            lopsided = [(k, v) for k, v in margins.items()
                        if v > r * (W if k in ("左", "右") else H)]
            opposite = {"左": "右", "右": "左", "上": "下", "下": "上"}
            for k, v in lopsided:
                opp = opposite[k]
                if margins[opp] < v / 2:
                    warnings.append(f"留白失衡: {k}侧空 {v:.0f}px，{opp}侧仅 "
                                    f"{margins[opp]:.0f}px——内容居中或收缩画布")
            if len(lopsided) == 4:
                warnings.append("画布四周留白都过大——内容显稀疏，等比缩小坐标而不改字号")

    # ---- 7. 间距过密 ----
    gap_min = AESTHETIC["min_gap_font_ratio"] * base_fs
    tight = []
    for a, b in itertools.combinations(labeled, 2):
        if a.get("group") != b.get("group") or _is_badge_pair(a, b):
            continue
        ax2, bx2 = a["x"] + a["w"], b["x"] + b["w"]
        ay2, by2 = a["y"] + a["h"], b["y"] + b["h"]
        x_overlap = a["x"] < bx2 and b["x"] < ax2
        y_overlap = a["y"] < by2 and b["y"] < ay2
        if x_overlap and not y_overlap:
            gap = max(a["y"], b["y"]) - min(ay2, by2)
        elif y_overlap and not x_overlap:
            gap = max(a["x"], b["x"]) - min(ax2, bx2)
        else:
            continue
        if 0 <= gap < gap_min:
            tight.append(f"{a.get('id')}↔{b.get('id')} 间隙 {gap:.0f}px")
    if tight:
        warnings.append(f"节点间距过密（应 ≥ 字号×{AESTHETIC['min_gap_font_ratio']} ≈ "
                        f"{gap_min:.0f}px）: " + "; ".join(tight[:cap])
                        + ("…" if len(tight) > cap else ""))

    # ---- 8. 连线穿节点 & 9. 交叉过多 ----
    polylines: dict[str, list[tuple[float, float]]] = {}
    edge_by_key: dict[str, dict[str, Any]] = {}
    for e in edges:
        pl = _edge_polyline(e, by_id)
        if len(pl) >= 2:
            polylines[_edge_key(e)] = pl
            edge_by_key[_edge_key(e)] = e
    through = []
    for key, pl in polylines.items():
        e = edge_by_key[key]
        for n in labeled:
            if n.get("id") in (e.get("from"), e.get("to")):
                continue
            rect = (n["x"], n["y"], n["w"], n["h"])
            if any(_seg_hits_rect(pl[i], pl[i + 1], rect) for i in range(len(pl) - 1)):
                through.append(f"{key} 穿过 {n.get('id')}")
                break
    if through:
        warnings.append("连线穿过非端点节点（加 waypoint 绕行或重排）: "
                        + "; ".join(through[:cap]) + ("…" if len(through) > cap else ""))
    crossings = 0
    for ki, kj in itertools.combinations(list(polylines), 2):
        ei, ej = edge_by_key[ki], edge_by_key[kj]
        if {ei.get("from"), ei.get("to")} & {ej.get("from"), ej.get("to")}:
            continue    # 共端点的边在节点处相遇，不算交叉
        pa, pb = polylines[ki], polylines[kj]
        if any(_segments_cross(pa[s], pa[s + 1], pb[t], pb[t + 1])
               for s in range(len(pa) - 1) for t in range(len(pb) - 1)):
            crossings += 1
    if edges and crossings > max(AESTHETIC["crossings_warn_min"],
                                 AESTHETIC["crossings_warn_ratio"] * len(edges)):
        warnings.append(f"连线交叉 {crossings} 处（{len(edges)} 条边）——重排节点顺序或"
                        "改用正交路由减少交叉")

    # ---- 10. 描边档数 / 标题层级 ----
    sw = {n.get("stroke_width", d.get("stroke_width", 1.5)) for n in labeled}
    if len(sw) > 2:
        warnings.append(f"节点描边粗细出现 {len(sw)} 档 {sorted(sw)}——只留常规 + 强调两档")
    if spec.get("title"):
        title_fs = (spec.get("title_style") or {}).get("font_size", 22)
        biggest = max([g.get("font_size", 15) for g in groups if g.get("label")]
                      + [n.get("font_size", base_fs) for n in labeled] + [0])
        if title_fs < biggest:
            warnings.append(f"标题 {title_fs}px 小于图内最大字号 {biggest}px——"
                            "标题应是全图最大层级")

    return {"errors": errors, "warnings": warnings}
