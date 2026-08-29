"""figspec —— 论文框架图的结构化中间表示（单一事实源）。

同一份 figspec 确定性渲染为两种产物：
  - SVG（论文排版直接使用）
  - .drawio mxGraph XML（drawio 原生可编辑，含分组容器）

schema（JSON）：
{
  "title": str,
  "title_style": {"font_size": 16, "y": 24, "color": "#1a1a1a", "bold": true},
  "canvas": {"width": int, "height": int},
  "defaults": {"font_size": 13, "fill": "#FFFFFF", "stroke": "#333333",
               "edge_color": "#333333", "edge_width": 1.5},
  "groups": [{"id","label","x","y","w","h","fill","stroke","dashed",
              "stroke_width","arc","shadow","font_size","label_color"}],
  "nodes":  [{"id","label","sublabel","x","y","w","h","shape","fill","stroke",
              "font_size","dashed","group","stroke_width","arc","shadow",
              "label_color","label_bold","sublabel_color"}],
  "edges":  [{"id","from","to","label","dashed","color","width","arrow",
              "waypoints": [[x,y],...]}],
  "texts":  [{"id","text","x","y","font_size","color","bold",
              "align": "left|center|right"}]
}
edge 的 color/width 在 defaults 中对应键为 edge_color/edge_width
（写 color/width 也兼容）；node 的 label_color/label_bold 用于
深色头带白字等样式；shadow 加投影、arc 定 rounded 圆角像素、
stroke_width 定边框粗细；texts.align 的 x 语义随对齐方式变
（left 时 x=左缘）。以上均 SVG 与 drawio 双渲染器同步生效。
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

    # 同义平行线检查：两模块间默认一条捆绑连线，
    # 多条平行边仅当各自携带不同 label（不同的量）时才合法
    seen_pairs: dict[tuple, list[str]] = {}
    for e in spec.get("edges", []):
        pair = (e.get("from"), e.get("to"))
        seen_pairs.setdefault(pair, []).append((e.get("label") or "").strip())
    for (src, dst), labels in seen_pairs.items():
        if len(labels) > 1 and len(set(labels)) < len(labels):
            errs.append(f"同义平行线: {src} → {dst} 有 {len(labels)} 条边"
                        "携带相同 label（应捆绑成一条，或分别标注不同的量）")
    return errs


def loads(text: str) -> dict[str, Any]:
    spec = json.loads(text)
    errs = validate(spec)
    if errs:
        raise ValueError("figspec 校验失败:\n- " + "\n- ".join(errs))
    return spec


# ---------------------------------------------------------------- typography
# 排版 lint：字号按「印刷等效 pt」检查（图以 target_width_pt 排入论文时的实际
# 字号 = px * target_width_pt / canvas_width）。地板对应顶会图最低可读性。
TYPO = {
    "target_width_pt": 468,      # \textwidth（1in margin US letter）
    "body_min_pt": 4.0,          # 正文/边标/脚注：低于此值 = error
    "body_good_pt": 4.6,         # 低于此值 = warning（建议加大）
    "title_min_pt": 5.5,         # 标题 warning 线
    # 各形状的有效文本区（宽比例 × 高比例），与 render_svg.TEXT_WIDTH_RATIO 对齐
    "text_area": {
        "diamond": (0.55, 0.52), "hexagon": (0.70, 0.76), "ellipse": (0.72, 0.70),
        "cloud": (0.62, 0.55), "parallelogram": (0.78, 0.82),
        "document": (0.85, 0.78), "cylinder": (0.85, 0.72),
        "rect": (0.90, 0.86), "rounded": (0.90, 0.86), "stadium": (0.86, 0.80),
    },
}


def _wrap_units(label: str, w: float, font_size: float) -> int:
    """与 render_svg._wrap_label 同步的折行估算 → 行数。"""
    max_units = max(int(w / (font_size * 0.62)), 4)
    n = 0
    for hard in (label or "").split("\n"):
        units, cur = 0.0, False
        for ch in hard:
            u = 1.0 if ord(ch) > 0x2E7F else 0.58
            if units + u > max_units and cur:
                n += 1
                units, cur = u, True
            else:
                units += u
                cur = True
        n += 1
    return max(n, 1)


def _est_text_w(s: str, fs: float) -> float:
    return max((sum(1.0 if ord(c) > 0x2E7F else 0.58 for c in ln) for ln in
                (s or "").split("\n")), default=0) * fs


def lint(spec: dict[str, Any]) -> dict[str, list[str]]:
    """排版质量检查 → {"errors": [...], "warnings": [...]}。

    errors 阻塞出图；warnings 建议修复。validate() 只管结构，本函数管可读性：
    1. 印刷等效字号地板（节点/边标/脚注/组标/标题）
    2. 节点文字竖向溢出（shape 感知有效文本区，与渲染器折行算法一致）
    3. group 标签遮挡组内节点
    4. edge 标签中点落在节点框内（遮挡）
    """
    errors: list[str] = []
    warnings: list[str] = []
    W = (spec.get("canvas") or {}).get("width") or 1
    scale = TYPO["target_width_pt"] / W
    d = spec.get("defaults") or {}

    def check_pt(px: float, what: str, is_title: bool = False) -> None:
        pt = px * scale
        if is_title:
            if pt < TYPO["title_min_pt"]:
                warnings.append(f"{what}: {px}px ≈ {pt:.1f}pt 印刷偏小"
                                f"（标题建议 ≥{TYPO['title_min_pt']}pt）")
            return
        if pt < TYPO["body_min_pt"]:
            errors.append(f"{what}: {px}px ≈ {pt:.1f}pt 印刷不可读"
                          f"（下限 {TYPO['body_min_pt']}pt，请加大字号或缩小画布）")
        elif pt < TYPO["body_good_pt"]:
            warnings.append(f"{what}: {px}px ≈ {pt:.1f}pt 偏小"
                            f"（建议 ≥{TYPO['body_good_pt']}pt）")

    ts = spec.get("title_style") or {}
    if spec.get("title"):
        check_pt(ts.get("font_size", 16), "title", is_title=True)

    sub_ratio, sub_min = 0.85, 10.5
    for nd in spec.get("nodes", []):
        nid = nd.get("id", "?")
        if not all(isinstance(nd.get(k), (int, float)) for k in ("x", "y", "w", "h")):
            continue
        if not (nd.get("label") or nd.get("sublabel")):
            continue  # 纯装饰形状（色块/连接柄）无文字，不做排版检查
        fs = nd.get("font_size", d.get("font_size", DEFAULTS["font_size"]))
        check_pt(fs, f"node {nid} 主标")
        shape = nd.get("shape", "rect")
        wr, hr = TYPO["text_area"].get(shape, (0.90, 0.86))
        tw, th = nd["w"] * wr, nd["h"] * hr
        n_lab = _wrap_units(nd.get("label", ""), tw, fs)
        need = fs * 1.25 * n_lab
        if nd.get("sublabel"):
            sub_fs = max(fs * sub_ratio, sub_min)
            check_pt(sub_fs, f"node {nid} 副文")
            need += fs * 0.30 + sub_fs * 1.25 * _wrap_units(nd["sublabel"], tw, sub_fs)
        if need > th:
            errors.append(f"node {nid} 文字溢出: 需 {need:.0f}px 高，"
                          f"{shape} 有效文本区仅 {th:.0f}px"
                          f"（精简文本 / 加大节点 / 减小字号层级差）")

    for g in spec.get("groups", []):
        gid = g.get("id", "?")
        if g.get("label"):
            g_fs = g.get("font_size", 12.5)
            check_pt(g_fs, f"group {gid} 标签")
            lab_box = (g["x"] + 12, g["y"] + 4,
                       _est_text_w(g["label"], g_fs), g_fs * 1.7)
            for nd in spec.get("nodes", []):
                if nd.get("group") != gid:
                    continue
                if not all(isinstance(nd.get(k), (int, float))
                           for k in ("x", "y", "w", "h")):
                    continue
                if (lab_box[0] < nd["x"] + nd["w"] and nd["x"] < lab_box[0] + lab_box[2]
                        and lab_box[1] < nd["y"] + nd["h"]
                        and nd["y"] < lab_box[1] + lab_box[3]):
                    errors.append(f"group {gid} 标签遮挡节点 {nd.get('id')}"
                                  f"（节点上移或组内留出标题带）")

    nodes_by_id = {nd.get("id"): nd for nd in spec.get("nodes", [])}
    for e in spec.get("edges", []):
        if not e.get("label"):
            continue
        eid = e.get("id") or f"{e.get('from')}->{e.get('to')}"
        e_fs = e.get("font_size", 11)
        check_pt(e_fs, f"edge {eid} 标签")
        wps = e.get("waypoints") or []
        if wps:
            mid = wps[len(wps) // 2]
        else:
            a, b = nodes_by_id.get(e.get("from")), nodes_by_id.get(e.get("to"))
            if not (a and b):
                continue
            mid = ((a["x"] + a["w"] / 2 + b["x"] + b["w"] / 2) / 2,
                   (a["y"] + a["h"] / 2 + b["y"] + b["h"] / 2) / 2)
        lab_w = _est_text_w(e["label"], e_fs)
        for nd in spec.get("nodes", []):
            if nd.get("id") in (e.get("from"), e.get("to")):
                continue
            if not all(isinstance(nd.get(k), (int, float))
                       for k in ("x", "y", "w", "h")):
                continue
            if (mid[0] + lab_w / 2 > nd["x"] and mid[0] - lab_w / 2 < nd["x"] + nd["w"]
                    and mid[1] + e_fs > nd["y"] and mid[1] - e_fs < nd["y"] + nd["h"]):
                warnings.append(f"edge {eid} 标签可能遮挡节点 {nd.get('id')}"
                                f"（移动 waypoint 或缩短标签）")

    for t in spec.get("texts", []):
        check_pt(t.get("font_size", 12), f"text {t.get('id', '?')}")

    return {"errors": errors, "warnings": warnings}


def style_of(item: dict[str, Any], spec: dict[str, Any], key: str, fallback: Any) -> Any:
    return item.get(key, (spec.get("defaults") or {}).get(key, fallback))


def edge_style_of(e: dict[str, Any], spec: dict[str, Any], key: str,
                  fallback: Any) -> Any:
    """edge 样式解析：item 键为 color/width，defaults 键为 edge_color/edge_width
    （兼容 defaults 直接写 color/width 的旧拼法）。"""
    if key in e:
        return e[key]
    d = spec.get("defaults") or {}
    return d.get(f"edge_{key}", d.get(key, fallback))


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
