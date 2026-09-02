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

DEFAULTS = {"font_size": 15, "fill": "#FFFFFF", "stroke": "#333333",
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
    "body_min_pt": 4.5,          # 正文/边标/脚注：低于此值 = error
    "body_good_pt": 5.2,         # 低于此值 = warning（建议加大）
    "title_min_pt": 7.0,         # 标题 warning 线
    # 各形状的有效文本区（宽比例 × 高比例），与 render_svg.TEXT_WIDTH_RATIO 对齐
    "text_area": {
        "diamond": (0.55, 0.52), "hexagon": (0.70, 0.76), "ellipse": (0.72, 0.70),
        "cloud": (0.62, 0.55), "parallelogram": (0.78, 0.82),
        "document": (0.85, 0.78), "cylinder": (0.85, 0.72),
        "rect": (0.90, 0.86), "rounded": (0.90, 0.86), "stadium": (0.86, 0.80),
    },
}


# Helvetica 字宽表（em 单位，常规体；draw.io 与 SVG 渲染器都用 Helvetica 系）。
# 统一按 0.61em 估算会对大写/符号密集的粗体短语（"FWHM ≤ 1.3× · SSA ≥"）
# 乐观 20–30%，draw.io 按真实字宽折行就多出一行、文字顶出卡片。
_W_LOWER = {"a": .556, "b": .556, "c": .500, "d": .556, "e": .556, "f": .278, "g": .556,
            "h": .556, "i": .222, "j": .222, "k": .500, "l": .222, "m": .833, "n": .556,
            "o": .556, "p": .556, "q": .556, "r": .333, "s": .500, "t": .278, "u": .556,
            "v": .500, "w": .722, "x": .500, "y": .500, "z": .500}
_W_UPPER = {"A": .667, "B": .667, "C": .722, "D": .722, "E": .667, "F": .611, "G": .778,
            "H": .722, "I": .278, "J": .500, "K": .667, "L": .556, "M": .833, "N": .722,
            "O": .778, "P": .667, "Q": .778, "R": .722, "S": .667, "T": .611, "U": .722,
            "V": .667, "W": .944, "X": .667, "Y": .667, "Z": .611}
_W_OTHER = {" ": .278, ".": .278, ",": .278, ":": .278, ";": .278, "!": .278, "|": .260,
            "'": .191, "`": .333, "/": .278, "(": .333, ")": .333, "[": .278, "]": .278,
            "{": .334, "}": .334, "-": .333, "*": .389, "+": .584, "=": .584, "<": .584,
            ">": .584, "%": .889, "&": .667, "@": 1.015, "#": .556, "$": .556, "?": .556,
            '"': .355, "_": .556, "~": .584, "^": .469, "\\": .278,
            "–": .556, "—": 1.0, "·": .278, "•": .350, "×": .584, "÷": .584, "≤": .584,
            "≥": .584, "≈": .584, "±": .584, "≠": .584, "°": .400, "→": 1.0, "←": 1.0,
            "↑": .584, "↓": .584, "…": 1.0, "’": .222, "‘": .222, "“": .333, "”": .333,
            "′": .25, "″": .4, "∙": .35, "∞": .8, "√": .6, "∑": .7, "Δ": .667, "Φ": .8,
            "μ": .556, "τ": .45, "λ": .5, "ν": .5, "η": .556, "θ": .55, "π": .58,
            "σ": .58, "ε": .5, "α": .6, "β": .58, "γ": .5, "δ": .55, "ω": .72}
_BOLD_FACTOR = 1.08


def _char_units(ch: str, bold: bool = False) -> float:
    o = ord(ch)
    if ch in _W_LOWER:
        u = _W_LOWER[ch]
    elif ch in _W_UPPER:
        u = _W_UPPER[ch]
    elif ch in _W_OTHER:
        u = _W_OTHER[ch]
    elif ch.isdigit():
        u = .556
    elif 0x2080 <= o <= 0x209F or 0x2070 <= o <= 0x207F:   # 上下标数字/符号
        u = .40
    elif o > 0x2E7F:                                         # CJK 等全角
        return 1.0
    else:
        u = .60
    return u * _BOLD_FACTOR if bold else u


def text_units(s: str, bold: bool = False) -> float:
    """一行文字的宽度（em 单位）。"""
    return sum(_char_units(c, bold) for c in s)


def wrap_lines(text: str, w: float, font_size: float, bold: bool = False) -> list[str]:
    """单一折行实现：SVG 渲染、drawio 渲染（显式 <br/>）与 lint 三方共用。

    按**单词**折行（与 draw.io 的 whiteSpace=wrap 一致），单个超长词或无空格的
    CJK 串退化为逐字符硬切；figspec 里的 "\\n" 是硬换行。字宽按 Helvetica 真实
    字宽表逐字符累加（粗体 ×1.08）。三方行数一致，lint 的溢出判定才对最终
    产物负责——此前 SVG/lint 按字符均一宽度切、drawio 按真实字宽切，行数不同，
    lint 放过的卡片在 drawio 导出里文字会顶出边框。
    """
    max_units = max(w / font_size, 2.5)
    space = _char_units(" ", bold)
    lines: list[str] = []
    for hard in (text or "").split("\n"):
        cur, units = "", 0.0
        for word in hard.split(" "):
            wu = text_units(word, bold)
            if wu > max_units:                      # 超长词：逐字符硬切
                if cur:
                    lines.append(cur)
                    cur, units = "", 0.0
                for ch in word:
                    u = _char_units(ch, bold)
                    if cur and units + u > max_units:
                        lines.append(cur)
                        cur, units = "", 0.0
                    cur += ch
                    units += u
                continue
            if cur and units + space + wu > max_units:
                lines.append(cur)
                cur, units = word, wu
            elif cur:
                cur += " " + word
                units += space + wu
            else:
                cur, units = word, wu
        lines.append(cur)
    return lines or [""]


def _wrap_units(label: str, w: float, font_size: float, bold: bool = False) -> int:
    """折行后的行数（与渲染器同一实现）。"""
    return len(wrap_lines(label, w, font_size, bold))


def _est_text_w(s: str, fs: float, bold: bool = False) -> float:
    return max((text_units(ln, bold) for ln in (s or "").split("\n")), default=0) * fs


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
        check_pt(ts.get("font_size", 22), "title", is_title=True)

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
        n_lab = _wrap_units(nd.get("label", ""), tw, fs, bold=nd.get("label_bold", True))
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
            g_fs = g.get("font_size", 15)
            check_pt(g_fs, f"group {gid} 标签")
            member_fs = [nd.get("font_size", d.get("font_size",
                                                   DEFAULTS["font_size"]))
                         for nd in spec.get("nodes", [])
                         if nd.get("group") == gid
                         and (nd.get("label") or nd.get("sublabel"))]
            if member_fs and g_fs < max(member_fs):
                warnings.append(
                    f"group {gid} 标签 {g_fs}px 小于组内节点主标 "
                    f"{max(member_fs)}px（小标题字号应 ≥ 正文，建议加大）")
            lab_box = (g["x"] + 12, g["y"] + 4,
                       _est_text_w(g["label"], g_fs, bold=True), g_fs * 1.7)
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
        e_fs = e.get("font_size", 12.5)
        check_pt(e_fs, f"edge {eid} 标签")
        wps = e.get("waypoints") or []
        pts = edge_points(e, nodes_by_id)
        if not pts:
            continue
        mid = edge_label_point(pts)      # 与渲染器同一锚点算法
        lab_w = _est_text_w(e["label"], e_fs)
        lab_h = e_fs * 1.25 * len(str(e["label"]).split("\n"))
        if not wps:
            # 无 waypoint 的边，标签落在两端点连线中点：端点间距容不下标签高/宽时
            # 文字会压在卡片边框上（Lane 内相邻卡片的短边最常见）
            for nd in (nodes_by_id.get(e.get("from")), nodes_by_id.get(e.get("to"))):
                if not (nd and all(isinstance(nd.get(k), (int, float))
                                   for k in ("x", "y", "w", "h"))):
                    continue
                if (mid[0] + lab_w / 2 > nd["x"] and mid[0] - lab_w / 2 < nd["x"] + nd["w"]
                        and mid[1] + lab_h / 2 > nd["y"]
                        and mid[1] - lab_h / 2 < nd["y"] + nd["h"]):
                    warnings.append(
                        f"edge {eid} 标签与端点 {nd.get('id')} 重叠（标签约 "
                        f"{lab_w:.0f}×{lab_h:.0f}px，端点间距不足）——拉开两节点、"
                        "缩短标签或加 waypoint 把标签引到空处")
                    break
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
        check_pt(t.get("font_size", 13), f"text {t.get('id', '?')}")

    # 美学 lint（配色克制/对齐/尺寸/留白/间距/连线/层级）与排版 lint 合并输出：
    # render_figure 只认一个 errors 列表，花哨与不可读同样阻塞出图
    from server.core.aesthetics import lint_aesthetics
    aes = lint_aesthetics(spec)
    errors += aes["errors"]
    warnings += aes["warnings"]

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


def edge_points(e: dict[str, Any], nodes_by_id: dict[str, dict[str, Any]]
                ) -> list[tuple[float, float]]:
    """边的折线点列：[起点边框交点, *waypoints, 终点边框交点]。
    渲染器与 lint 共用，标签位置由 edge_label_point 从同一点列推出。"""
    src, dst = nodes_by_id.get(e.get("from")), nodes_by_id.get(e.get("to"))
    if not (src and dst):
        return []
    for nd in (src, dst):
        if not all(isinstance(nd.get(k), (int, float)) for k in ("x", "y", "w", "h")):
            return []
    wps = [(float(p[0]), float(p[1])) for p in (e.get("waypoints") or [])
           if isinstance(p, (list, tuple)) and len(p) == 2]
    p_start = border_point(src, wps[0] if wps else center(dst))
    p_end = border_point(dst, wps[-1] if wps else center(src))
    return [p_start, *wps, p_end]


def edge_label_point(pts: list[tuple[float, float]]) -> tuple[float, float]:
    """标签锚点：点数为奇取中间点，为偶取中间两点均值（与渲染器一致）。"""
    n = len(pts)
    if n % 2 == 1:
        return pts[n // 2]
    a, b = pts[n // 2 - 1], pts[n // 2]
    return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
