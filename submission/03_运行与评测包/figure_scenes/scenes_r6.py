"""第六轮：按印刷字号重排五张图（中英同源）。

第五轮的问题，在编好的论文里量出来的：
  · 正文字印出来只有 4.8–6.0 pt（下限 7，顶会图一般 8–9），连线标签 4.8–5.4 pt；
  · 同一角色跨图差到两倍（卡片标题 6.4–8.0 pt，步骤号 4.8 / 10.6 pt）；
  · 全部文字加粗，标题和正文分不出层次；
  · 卡片内容只占卡片面积的 14–48%，空白是字小的根源。

这一轮的做法：
  · 字号由设计系统按「印刷 pt × 角色」给出（正文 8、标题 9、分组 9.5、步骤号 12、标签 7.5），
    本文件不写死任何 px 字号；
  · 只有分组名、卡片标题、步骤号加粗，其余一律常规体；
  · 卡片尺寸由内容算出：先量字，再定卡片宽高，放不下一行的标题/条目折成两行，
    所以中英两版是同一份代码、各自的几何，而不是把中文几何硬塞英文字串。

usage: python3 scenes_r6.py [fig01|fig02|fig03|roadmap|taxonomy|all] [zh|en|both]
"""
import ast
import math
import os
import pathlib
import sys

_REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / 'skills' / 'goai-figure-studio'))
JOBS_DIR = pathlib.Path(os.environ.get('GOAI_FIGSTUDIO_JOBS', _REPO.parent / 'final_round/figstudio/jobs'))

from lib import Figure, FAM, Scene, ITEM, CONN, W_STEP, TYPE_PT, TYPE_PT_EN  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent

# 图在论文里的放置宽度——从编好的 PDF 里读嵌入图的实际边界得到（不要用正文行宽去估，会偏 8%）。
# 只随模板语言变：两篇中文都是 435.2 pt，两篇英文都是 451.4 pt。
PRINT_W = {'zh': 435.2, 'en': 451.4}

# 第五轮的英文表按中文原文做键；第六轮只新增了这几条
EXTRA_TR = {
    '距目标相由近及远': 'nearest to farthest from the target',
}


def _load_tr():
    tree = ast.parse((HERE / 'r5_en.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, 'id', None) == 'TR' for t in node.targets):
            table = ast.literal_eval(node.value)
            table.update(EXTRA_TR)
            return table
    raise SystemExit('r5_en.py 里找不到 TR 表')


TR = _load_tr()
# 第六轮字号更大，Mechanochemical 这个不可断的长词放不进路线卡；固态化学里的同义标准说法是 mechanical activation
TR['机械化学预活化'] = 'Mechanical Activation'

SCALE = {'zh': TYPE_PT, 'en': TYPE_PT_EN}


def new_fig(lang, h, notes, paper):
    # paper 只作记录：放置宽度由模板语言决定
    return Figure(1536, h, notes=f'{notes} [paper={paper}]', print_width_pt=PRINT_W[lang], type_scale=SCALE[lang])


_CJK = __import__('re').compile(r'[\u3000-\u9fff\uff00-\uffef]')


def tr(lang):
    if lang == 'zh':
        return lambda s: s
    # 本来就是拉丁字母的串（Czochralski、化学式、编号）原样通过；含中文而表里没有的直接 KeyError，
    # 绝不把中文漏进英文版
    return lambda s: TR[s] if _CJK.search(s) else s


# ------------------------------------------------------------------------------------------------ 量字与折行
RESERVE = 3


def W(text, size, bold=False):
    return Scene.measure(text, size, bold) + RESERVE


def nlines(text, size, room, bold=False):
    """在 room 宽度内需要几行（英文按词折，中文按字折）。"""
    if W(text, size, bold) <= room:
        return 1
    if ' ' in text:
        n, cur = 1, ''
        for word in text.split(' '):
            t = f'{cur} {word}'.strip()
            if W(t, size, bold) <= room:
                cur = t
            else:
                n, cur = n + 1, word
        return n
    return math.ceil(W(text, size, bold) / room)


def box_h(size, lines, single=1.72):
    """文字框高度：单行沿用设计系统的 1.72 em；多行按 CJK 实测 1.46 em 行高再留余量。"""
    return int(size * single) if lines == 1 else int(size * (1.52 * lines + 0.45))


def text(f, tid, box, s, size, *, bold, color=ITEM, align='left', container=None, lines=1, valign='middle'):
    f.sc.text(tid, box, s, size, bold=bold, color=color, align=align, valign=valign, container=container,
              wrap=lines > 1, fit='shrink', min_font_size=f.shrink_floor(size, 3))


def zone_top(f, zy):
    """分组标题带之下、内容开始的 y。"""
    return zy + 10 + int(f.T['group'] * 1.6) + 4 + 10


def head_card(f, cid, box, title, *, fam, glyph=None, container=None, dashed=False, fill=None,
              sub=None, lines=1, sub_lines=1, gw=40, bar=6, padl=12, padr=12, gap=10):
    """左色条卡：图元 + 标题（可折行）+ 可选副行，整体在卡片内垂直居中。"""
    x, y, w, h = box
    T = f.T
    f.card(cid, box, fam=fam, dashed=dashed, container=container, bar=(0 if dashed else bar), fill=fill)
    tx = x + bar + padl
    th = box_h(T['title'], lines)
    sh = box_h(T['body'], sub_lines, single=1.7) if sub else 0
    block = th + (sh + 2 if sub else 0)
    ty = y + (h - block) / 2
    if glyph:
        f.m.draw(glyph, cid + '_g', [tx, y + (h - gw) / 2, gw, gw], container=cid)
        tx += gw + gap
    tw = x + w - padr - tx
    text(f, cid + '_t', [tx, ty, tw, th], title, T['title'], bold=True, color=FAM[fam]['text'],
         container=cid, lines=lines)
    if sub:
        text(f, cid + '_s', [tx, ty + th + 2, tw, sh], sub, T['body'], bold=False, container=cid,
             lines=sub_lines)
    return tw


def card_title_room(w, gw=40, bar=6, padl=12, padr=12, gap=10):
    return w - bar - padl - gw - gap - padr


def finish(f, zones, height, path):
    f.sc.h = f.h = int(height)
    f.finish(zones)
    f.write(str(path))
    return f


def out_path(job, lang):
    return JOBS_DIR / (job if lang == 'zh' else job + '_en') / 'scene.json'


# ================================================================================================ 图 1
def fig01(lang='zh'):
    S = tr(lang)
    f = new_fig(lang, 800, '图 1 不同文献对目标化合物合成研究的适用范围（第六轮：印刷字号 + 内容定尺寸）', 'byzso')
    T = f.T
    lane = 56 if lang == 'zh' else 86
    zL = (26, 536)
    zE = (586, 400)
    zQ = (1010, 500)
    y0 = zone_top(f, 26)

    ev = [('a1', '目标化合物直接报道', 'doc'), ('a2', '同类 Ba–Y 四方硅酸盐', 'polyhedron'),
          ('a3', '结构相关化合物', 'lattice'), ('a4', '工艺参照研究', 'crucible')]
    qs = [('u1', '直接条件复现', 'flask'), ('u2', '系列内相图与结构比较', 'polyhedron'),
          ('u3', '方法与变量结构', 'balance')]

    ev_x = zL[0] + 16 + lane
    ev_w = zL[0] + zL[1] - 16 - ev_x
    q_x = zQ[0] + 16
    q_w = zQ[1] - 32
    ev_lines = max(nlines(S(t), T['title'], card_title_room(ev_w), True) for _, t, _ in ev + [('', '非相关资料', '')])
    q_lines = max(nlines(S(t), T['title'], card_title_room(q_w), True) for _, t, _ in qs + [('', '划定研究范围', '')])
    ev_h = box_h(T['title'], ev_lines) + 30
    q_h = box_h(T['title'], q_lines) + 30

    # 实验方法：图元在标题上方，标题可折行，六行勾选记录
    led_x, led_w = zE[0] + 16, zE[1] - 32
    led_title = S('相同实验项目下比较')
    led_lines = nlines(led_title, T['title'], led_w - 6 - 28, True)
    rows = ['原料与配比', '热历史', '气氛', '容器与助熔剂', '冷却与分离', '产物表征']
    row_room = led_w - 6 - 28 - int(T['body'] * 0.8) - 24 - 14
    row_lines = max(nlines(S(r), T['body'], row_room) for r in rows)
    row_h = max(54, box_h(T['body'], row_lines, single=1.78) + 2)
    led_head = 16 + 44 + 8 + box_h(T['title'], led_lines) + 12
    led_h = led_head + 6 * row_h + 5 * 6 + 16

    # 三列等高：卡片按列高均分（间距固定），不让空白堆在卡片之间
    CARD_GAP = 24
    body_h = max(led_h, 4 * ev_h + 3 * CARD_GAP)
    led_h = body_h
    ev_h = q_h = max(ev_h, q_h, min(150, (body_h - 3 * CARD_GAP) / 4))
    ev_gap = (body_h - 4 * ev_h) / 3
    ev_y = [y0 + k * (ev_h + ev_gap) for k in range(4)]

    ex_y = y0 + body_h + 36                 # 排除行：在账本之下横穿「实验方法」列
    ex_h = max(ev_h, q_h)
    zone_h = ex_y + ex_h + 18 - 26
    zl = f.zone('zL', [zL[0], 26, zL[1], zone_h], S('文献证据'), 'lit')
    ze = f.zone('zE', [zE[0], 26, zE[1], zone_h], S('实验方法'), 'exp')
    zq = f.zone('zQ', [zQ[0], 26, zQ[1], zone_h], S('可回答的问题'), 'note')

    for (cid, t, g), y in zip(ev, ev_y):
        head_card(f, cid, [ev_x, y, ev_w, ev_h], S(t), fam='lit', glyph=g, container=zl, lines=ev_lines)
    head_card(f, 'a5', [ev_x, ex_y, ev_w, ex_h], S('非相关资料'), fam='mute', glyph='doc_struck', dashed=True,
              container=zl, lines=ev_lines)

    # 距离轴：「近」在上、「远」在下，轴名竖排嵌在轴线中段
    ax_cx = zL[0] + 16 + lane / 2
    near, far = S('近'), S('远')
    end_h = int(T['label'] * 1.7)
    end_w = lane - 4
    f.sc.text('ax_n', [ax_cx - end_w / 2, ev_y[0], end_w, end_h], near, T['label'], bold=False, color=ITEM,
              container=zl)
    f.sc.text('ax_f', [ax_cx - end_w / 2, ev_y[3] + ev_h - end_h, end_w, end_h], far, T['label'], bold=False,
              color=ITEM, container=zl)
    lab = S('与目标相的距离')
    lw = W(lab, T['label']) + 10
    lh = int(T['label'] * 1.75)
    top, bot = ev_y[0] + end_h + 6, ev_y[3] + ev_h - end_h - 6
    mid = (top + bot) / 2
    f.sc.text('ax_l', [ax_cx - lw / 2, mid - lh / 2, lw, lh], lab, T['label'], bold=False, color=ITEM,
              rotation=-90, container=zl, font_group='axis')
    if mid - lw / 2 - 8 - top > 12:
        f.sc.line('ax_u', [(ax_cx, top), (ax_cx, mid - lw / 2 - 8)], stroke=ITEM, width=W_STEP, container=zl)
        f.sc.line('ax_d', [(ax_cx, mid + lw / 2 + 8), (ax_cx, bot)], stroke=ITEM, width=W_STEP, arrow=True,
                  head={'length': 13, 'width': 10}, container=zl)

    # 账本
    f.card('led', [led_x, y0, led_w, led_h], fam='exp', container=ze, bar=6)
    f.m.draw('grid', 'led_g', [led_x + 6 + (led_w - 6) / 2 - 22, y0 + 16, 44, 44], container='led')
    lt_h = box_h(T['title'], led_lines)
    text(f, 'led_t', [led_x + 6 + 14, y0 + 16 + 44 + 8, led_w - 6 - 28, lt_h], led_title, T['title'],
         bold=True, color=FAM['exp']['text'], align='center', container='led', lines=led_lines)
    rows_top = y0 + led_head
    rows_h = led_h - led_head - 16
    f.check_rows('ledr', [led_x + 6 + 14, rows_top, led_w - 6 - 28, rows_h], [S(r) for r in rows],
                 container='led', gap=6)
    if row_lines > 1:
        for e in f.sc.els:
            if e['id'].startswith('ledr_x'):
                e['wrap'] = True

    q_y = [y0 + k * (q_h + ev_gap) for k in range(3)]
    for (cid, t, g), y in zip(qs, q_y):
        head_card(f, cid, [q_x, y, q_w, q_h], S(t), fam='note', glyph=g, container=zq, lines=q_lines)
    cav_y = (q_y[2] + q_h + y0 + body_h) / 2          # 警示放在第三张问题卡之下的剩余空间正中
    f.pill('cav', q_x + q_w / 2, cav_y, S('近邻条件 ≠ 已验证配方'), fam='note', max_w=q_w)
    head_card(f, 'u4', [q_x, ex_y, q_w, ex_h], S('划定研究范围'), fam='mute', glyph='target', dashed=True,
              container=zq, lines=q_lines)

    # 证据 → 账本（汇流），账本 → 问题（分发），非相关资料 --排除--> 划定研究范围
    g1 = (zL[0] + zL[1] + zE[0]) / 2
    g2 = (zE[0] + zE[1] + zQ[0]) / 2
    for (cid, *_), y in zip(ev, ev_y):
        f.conn('br_' + cid, [(ev_x + ev_w + 5, y + ev_h / 2), (g1, y + ev_h / 2)], arrow=False)
    f.conn('brv', [(g1, ev_y[0] + ev_h / 2), (g1, ev_y[3] + ev_h / 2)], arrow=False)
    f.conn('brh', [(g1, y0 + led_h / 2), (led_x - 3, y0 + led_h / 2)])
    f.conn('fan0', [(led_x + led_w + 5, y0 + led_h / 2), (g2, y0 + led_h / 2)], arrow=False)
    lo, hi = min(q_y[0] + q_h / 2, y0 + led_h / 2), max(q_y[2] + q_h / 2, y0 + led_h / 2)
    f.conn('fanv', [(g2, lo), (g2, hi)], arrow=False)
    for k, y in enumerate(q_y):
        f.conn(f'fan{k + 1}', [(g2, y + q_h / 2), (q_x - 3, y + q_h / 2)])
    ey = ex_y + ex_h / 2
    f.conn('ex', [(ev_x + ev_w + 5, ey), (q_x - 4, ey)], dashed=True, label=S('排除'),
           label_at=(zE[0] + zE[1] / 2, ey))

    return finish(f, [zl, ze, zq], zone_h + 26 + 26, out_path('fig01_r6', lang))


# ================================================================================================ 图 2
def fig02(lang='zh'):
    S = tr(lang)
    f = new_fig(lang, 1200, '图 2 不同合成方法的条件比较与产物表征（第六轮：印刷字号 + 内容定尺寸）', 'byzso')
    T = f.T
    X0, INNER = 42, 1452

    routes = [('r1', '外加助熔', 'beaker', ['溶解', '保温', '缓冷分离'], False),
              ('r2', '自熔/熔体', 'bowl', ['均化', '自发成核', '受控冷却'], False),
              ('r3', '固相陶瓷', 'pellet', ['混合压片', '煅烧复磨', '烧结'], False),
              ('r4', '机械化学预活化', 'mill', ['高能研磨', '活化', '后续相形成'], False),
              ('r5', 'Czochralski', 'pull', ['预烧熔化', '籽晶提拉', '退火'], True)]
    RG = 10
    RW = (INNER - 4 * RG) // 5
    r_title_room = RW - 6 - 20
    r_lines = max(nlines(S(t), T['title'], r_title_room, True) for _, t, *_ in routes)
    step_room = RW - 6 - 20 - 14
    s_lines = max(nlines(S(s), T['body'], step_room) for *_, steps, _ in routes for s in steps)
    step_h = box_h(T['body'], s_lines, single=1.72) + 8
    GL = 48
    r_title_h = box_h(T['title'], r_lines)
    r_h = 12 + r_title_h + 6 + GL + 12 + 3 * step_h + 2 * 18 + 14

    zT_y = 26
    y0 = zone_top(f, zT_y)
    zT_h = (y0 - zT_y) + r_h + 16
    zt = f.zone('zT', [26, zT_y, 1484, zT_h], S('实验方法'), 'exp')
    leg = S('虚线＝工艺参照')
    f.pill('leg', 1494 - (W(leg, T['label']) + 32) / 2, zT_y + 10 + int(T['group'] * 1.6) / 2 + 2, leg, fam='mute')

    for k, (cid, t, g, steps, dashed) in enumerate(routes):
        x = X0 + k * (RW + RG)
        fam = 'mute' if dashed else 'exp'
        f.card(cid, [x, y0, RW, r_h], fam=fam, dashed=dashed, container=zt, bar=(0 if dashed else 6))
        text(f, cid + '_t', [x + 6 + 10, y0 + 12, r_title_room, r_title_h], S(t), T['title'], bold=True,
             color=FAM[fam]['text'], align='center', container=cid, lines=r_lines)
        gy = y0 + 12 + r_title_h + 6
        f.m.draw(g, cid + '_g', [x + 3 + RW / 2 - GL / 2, gy, GL, GL], container=cid)
        f.vchain(f'{cid}c', [x + 6 + 10, gy + GL + 12, RW - 6 - 20, 3 * step_h + 2 * 18],
                 [S(s) for s in steps], container=cid, gap=18)
        if s_lines > 1:
            for e in f.sc.els:
                if e['id'].startswith(f'{cid}c_t') and e['kind'] == 'text':
                    e['wrap'] = True

    # 文献证据：统一实验记录
    GAP = 96                                   # 标签直接压在各自的箭头上，箭头上下各露出一段
    GAP_TM = GAP if lang == 'zh' else 150      # 英文标签折两行，箭头要更长才露得出来
    zM_y = zT_y + zT_h + GAP_TM
    yM = zone_top(f, zM_y)
    cols = [('配比与原料', 'doc'), ('温度—时间与气氛', 'thermo'), ('坩埚与助熔剂', 'crucible'),
            ('冷却、生长与分离', 'droplet')]
    led_x, led_w = X0, INNER
    CW = (led_w - 6 - 28 - 3 * 24) / 4
    c_lines = max(nlines(S(c), T['body'], CW - 8) for c, _ in cols)
    c_label_h = box_h(T['body'], c_lines, single=1.7)
    led_title = S('统一实验记录')
    lt_h = box_h(T['title'], 1)
    led_h = 14 + lt_h + 10 + 46 + 10 + c_label_h + 16
    zM_h = (yM - zM_y) + led_h + 16
    zm = f.zone('zM', [26, zM_y, 1484, zM_h], S('文献证据'), 'lit')
    f.card('led', [led_x, yM, led_w, led_h], fam='lit', container=zm, bar=6)
    text(f, 'led_t', [led_x + 6 + 14, yM + 14, W(led_title, T['title'], True) + 6, lt_h], led_title, T['title'],
         bold=True, color=FAM['lit']['text'], container='led')
    cav = S('抽取框架 ≠ 实验配方')
    cav_w = W(cav, T['label']) + 32
    f.pill('cav', led_x + led_w - 14 - cav_w / 2, yM + 14 + lt_h / 2, cav, fam='note', container='led')
    cy = yM + 14 + lt_h + 10
    for k, (lab, g) in enumerate(cols):
        cx = led_x + 6 + 14 + k * (CW + 24)
        f.m.draw(g, f'cl{k}_g', [cx + CW / 2 - 46 - 6, cy, 46, 46], container='led')
        f.m.draw('tick_circle', f'cl{k}_k', [cx + CW / 2 + 10, cy + 6, 34, 34], container='led')
        text(f, f'cl{k}_t', [cx, cy + 46 + 10, CW, c_label_h], S(lab), T['body'], bold=False, align='center',
             container='led', lines=c_lines)
        if k:
            f.sc.line(f'cl{k}_s', [(cx - 12, cy - 2), (cx - 12, cy + 46 + 10 + c_label_h)], stroke='#E3E8ED',
                      width=1.2, container='led')

    # 产物表征
    zB_y = zM_y + zM_h + GAP
    yB = zone_top(f, zB_y)
    checks = [('k1', '单晶结构', 'lattice', '结构归属与位点占据'), ('k2', 'PXRD / Rietveld', 'trace', '块体相纯与杂相'),
              ('k3', '成分与污染', 'dots', '名义—局域—体平均'), ('k4', '高温稳定性', 'thermo', '原位高温 ≠ 冷却回收')]
    KG = 12
    KW = (INNER - 3 * KG) // 4
    k_lines = max(nlines(S(t), T['title'], KW - 6 - 20, True) for _, t, *_ in checks)
    ks_lines = max(nlines(S(s), T['body'], KW - 6 - 20 - 14) for *_, s in checks)
    k_title_h = box_h(T['title'], k_lines)
    ks_h = box_h(T['body'], ks_lines, single=1.72) + 8
    k_h = 12 + k_title_h + 6 + GL + 10 + ks_h + 14
    zB_h = (yB - zB_y) + k_h + 16
    zb = f.zone('zB', [26, zB_y, 1484, zB_h], S('产物表征'), 'exp')
    for k, (cid, t, g, sub) in enumerate(checks):
        x = X0 + k * (KW + KG)
        f.card(cid, [x, yB, KW, k_h], fam='exp', container=zb, bar=6)
        text(f, cid + '_t', [x + 6 + 10, yB + 12, KW - 6 - 20, k_title_h], S(t), T['title'], bold=True,
             color=FAM['exp']['text'], align='center', container=cid, lines=k_lines)
        gy = yB + 12 + k_title_h + 6
        f.m.draw(g, cid + '_g', [x + 3 + KW / 2 - GL / 2, gy, GL, GL], container=cid)
        f.token(cid + '_s', [x + 6 + 10, gy + GL + 10, KW - 6 - 20, ks_h], S(sub), container=cid,
                wrap=ks_lines > 1)

    # 带间连线：标签压在各自箭头的中段（不再挤在两箭头之间的空当里）
    for k, lab in enumerate(['配比 · 温度', '熔体 · 容器', '混合 · 煅烧', '研磨 · 污染', '籽晶 · 退火']):
        x = X0 + k * (RW + RG) + RW / 2
        mid = zT_y + zT_h + GAP_TM / 2
        f.conn(f'd{k}', [(x, zT_y + zT_h - 11), (x, zM_y + 2)], label=S(lab),
               label_at=(x, mid), dashed=(k == 4), label_max_w=RW - 12)
    for k, lab in enumerate(['结构', '相组成', '成分', '高温']):
        x = X0 + k * (KW + KG) + KW / 2
        mid = zM_y + zM_h + GAP / 2
        f.conn(f'c{k}', [(x, zM_y + zM_h - 11), (x, zB_y + 2)], label=S(lab),
               label_at=(x, mid), label_max_w=KW - 12)

    return finish(f, [zt, zm, zb], zB_y + zB_h + 26, out_path('fig02_r6', lang))


# ================================================================================================ 图 3
def fig03(lang='zh'):
    S = tr(lang)
    f = new_fig(lang, 1200, '图 3 本文的研究路线（第六轮：印刷字号 + 内容定尺寸；分叉同时进入两条通道）', 'byzso')
    T = f.T
    X0, INNER = 42, 1452

    # 文献证据：三张带三条记录的卡，卡间主流程箭头
    ev = [('c1', '文献依据', 'docs', ['Ba–Y–Si–O 系列', 'Ba–Zn–Si–O 结构相关化合物', 'Y–Si–O 工艺参照']),
          ('c2', '结构假设', 'polyhedron', ['局部组成网格', 'Zn–Y–氧计量耦合', '竞争相与玻璃区']),
          ('c3', '前驱体筛选', 'funnel', ['BaCO3 + Y2O3 + SiO2', 'ZnO / MgO / Co3O4', '模型排序的候选'])]
    AG = 40
    EW = (INNER - 2 * AG) // 3
    i_room = EW - 6 - 22 - 14
    i_lines = max(nlines(S(i), T['body'], i_room) for *_, items in ev for i in items)
    i_h = box_h(T['body'], i_lines, single=1.72) + 8
    t_lines = max(nlines(S(t), T['title'], card_title_room(EW, gw=42, padl=11, padr=11), True) for _, t, *_ in ev)
    e_title_h = box_h(T['title'], t_lines)
    e_h = 14 + e_title_h + 10 + 3 * i_h + 2 * 9 + 14

    zL_y = 26
    y0 = zone_top(f, zL_y)
    zL_h = (y0 - zL_y) + e_h + 16
    zl = f.zone('zL', [26, zL_y, 1484, zL_h], S('文献证据'), 'lit')
    # 警示放进分组标题带（不压在分叉连线上）
    cav = S('模型排序 ≠ 验证')
    f.pill('cav', 1494 - (W(cav, T['label']) + 32) / 2, zL_y + 10 + int(T['group'] * 1.6) / 2 + 2, cav, fam='note')
    ex = []
    for k, (cid, t, g, items) in enumerate(ev):
        x = X0 + k * (EW + AG)
        ex.append(x)
        f.card_stack(cid, [x, y0, EW, e_h], S(t), [S(i) for i in items], fam='lit', glyph=g, container=zl,
                     glyph_w=42, pad=11, bar=6, gap=9, title_lines=t_lines)
        if i_lines > 1:
            for e in f.sc.els:
                if e['id'].startswith(f'{cid}_i') and e['kind'] == 'text':
                    e['wrap'] = True
    for k in range(2):
        yy = y0 + e_h / 2
        f.conn(f'e{k + 1}', [(ex[k] + EW + 4, yy), (ex[k + 1] - 4, yy)])

    # 实验方法：两条通道，各自「步骤链 → 产出」
    # 两带之间有两条横线：上面是反馈虚线（带标签），下面是分叉线。间距按反馈标签的实际高度来定，
    # 英文标签折两行时不能蹭进上方的证据卡。
    fb_lab = S('更新组成与工艺')
    fb_max = (X0 + 2 * (EW + AG) + EW / 2) - (X0 + (EW + AG) + EW / 2) - 60
    fb_lines = 1 if W(fb_lab, T['label']) + 32 <= fb_max else 2
    fb_ph = int(T['label'] * (1.5 if fb_lines == 1 else 3.1)) + 12
    FB_DY = max(26, fb_ph / 2 + 4)                 # 反馈线离证据带下沿
    FK_DY = FB_DY + max(32, fb_ph / 2 + 14)         # 分叉线离证据带下沿
    GAP1 = int(FK_DY + 26)
    zE_y = zL_y + zL_h + GAP1
    yE = zone_top(f, zE_y)
    lanes = [('l1', '固相反应', 'furnace', ['分段煅烧', '复磨', '退火'], '块体相区与相纯度'),
             ('l2', '高温溶液法晶体生长', 'flask', ['助熔', '保温', '缓冷'], '单晶结构与液相选择性')]
    LG = 20
    LW = (INNER - LG) // 2
    step_w = {}
    for _, _, _, steps, out in lanes:
        for s in steps:
            step_w[s] = W(S(s), T['body']) + 22
    row_lines = 1
    usable = LW - 6 - 28
    lane_rows = []
    for cid, t, g, steps, out in lanes:
        widths = [step_w[s] for s in steps]
        steps_w = sum(widths) + 2 * 24
        out_w = usable - steps_w - 16
        o_lines = nlines(S(out), T['body'], out_w - 14)
        row_lines = max(row_lines, o_lines)
        lane_rows.append((widths, steps_w, out_w, o_lines))
    l_title_lines = max(nlines(S(t), T['title'], usable - 40 - 10, True) for _, t, *_ in lanes)
    l_title_h = box_h(T['title'], l_title_lines)
    # 英文的产出放不进步骤行右侧：整行放到步骤行下方
    stack_out = lang != 'zh'
    out_h = 0
    if stack_out:
        o_lines = max(nlines(S(out), T['body'], usable - 14) for *_, out in lanes)
        out_h = box_h(T['body'], o_lines, single=1.72) + 8
        lane_rows = [(w, sw, usable, o_lines) for (w, sw, _, _) in lane_rows]
        row_lines = 1
    row_h = box_h(T['body'], row_lines, single=1.72) + 8
    l_h = 14 + l_title_h + 10 + row_h + 14 + ((10 + out_h) if stack_out else 0)
    zE_h = (yE - zE_y) + l_h + 16
    ze = f.zone('zE', [26, zE_y, 1484, zE_h], S('实验方法'), 'exp')
    lx = []
    for (cid, t, g, steps, out), (widths, steps_w, out_w, o_lines) in zip(lanes, lane_rows):
        x = X0 + len(lx) * (LW + LG)
        lx.append(x)
        f.card(cid, [x, yE, LW, l_h], fam='exp', container=ze, bar=6)
        f.m.draw(g, cid + '_g', [x + 6 + 14, yE + 14 + (l_title_h - 40) / 2, 40, 40], container=cid)
        text(f, cid + '_t', [x + 6 + 14 + 50, yE + 14, usable - 50, l_title_h], S(t), T['title'], bold=True,
             color=FAM['exp']['text'], container=cid, lines=l_title_lines)
        ry = yE + 14 + l_title_h + 10
        f.row(f'{cid}r', [x + 6 + 14, ry, steps_w, row_h], [S(s) for s in steps], container=cid, gap=24,
              widths=widths)
        if stack_out:
            f.token(f'{cid}_o', [x + 6 + 14, ry + row_h + 10, usable, out_h], S(out), container=cid, fam='exp',
                    wrap=o_lines > 1)
        else:
            f.token(f'{cid}_o', [x + 6 + 14 + steps_w + 16, ry, out_w, row_h], S(out), container=cid, fam='exp',
                    wrap=o_lines > 1)

    # 结果反馈：表征手段一行排开
    GAP2 = 64
    zR_y = zE_y + zE_h + GAP2
    yR = zone_top(f, zR_y)
    tools = ['PXRD / Rietveld', 'SCXRD', 'EDS / EPMA / ICP', '高温相与冷却产物']
    tw = [W(S(t), T['body']) + 22 for t in tools]
    c5_title = S('表征手段')
    c5_head = 42 + 10 + W(c5_title, T['title'], True) + 6
    c5_row = sum(tw) + 3 * 12
    c5_w = 6 + 18 + c5_head + 20 + c5_row + 18
    t_row_lines = 1
    if c5_w > INNER:                        # 英文：标题一行，工具一行
        c5_w = INNER
        c5_row_w = INNER - 6 - 36
        scale = (c5_row_w - 3 * 12) / sum(tw)
        tw = [w * scale for w in tw]
        t_row_lines = max(nlines(S(t), T['body'], w - 14) for t, w in zip(tools, tw))
        c5_h = 14 + box_h(T['title'], 1) + 10 + box_h(T['body'], t_row_lines, single=1.72) + 8 + 14
        stacked = True
    else:
        c5_h = 14 + box_h(T['title'], 1) + 14
        stacked = False
    zR_h = (yR - zR_y) + c5_h + 16
    zr = f.zone('zR', [26, zR_y, 1484, zR_h], S('结果反馈'), 'lit')
    c5_x = 26 + (1484 - c5_w) / 2
    f.card('c5', [c5_x, yR, c5_w, c5_h], fam='lit', container=zr, bar=6)
    t_h = box_h(T['title'], 1)
    f.m.draw('trace_check', 'c5_g', [c5_x + 6 + 18, yR + 14 + (t_h - 42) / 2, 42, 42], container='c5')
    text(f, 'c5_t', [c5_x + 6 + 18 + 52, yR + 14, W(c5_title, T['title'], True) + 6, t_h], c5_title,
         T['title'], bold=True, color=FAM['lit']['text'], container='c5')
    if stacked:
        rx, ry = c5_x + 6 + 18, yR + 14 + t_h + 10
        rh = box_h(T['body'], t_row_lines, single=1.72) + 8
    else:
        rx, ry, rh = c5_x + 6 + 18 + c5_head + 20, yR + 14 + (t_h - (box_h(T['body'], 1) + 8)) / 2, \
            box_h(T['body'], 1) + 8
    f.row('c5r', [rx, ry, sum(tw) + 36, rh], [S(t) for t in tools], container='c5', gap=12, arrow=False,
          widths=tw)
    if t_row_lines > 1:
        for e in f.sc.els:
            if e['id'].startswith('c5r_t') and e['kind'] == 'text':
                e['wrap'] = True

    # 判断提醒：三问
    GAP3 = 28
    zQ_y = zR_y + zR_h + GAP3
    yQ = zone_top(f, zQ_y)
    qs = [('q1', 'Zn 是否进入并与氧计量耦合？'), ('q2', '稳定相区还是液相选择性？'), ('q3', '实际组成与结构信号如何对应？')]
    QG = 20
    QW = (INNER - 2 * QG) // 3
    q_lines = max(nlines(S(q), T['body'], QW - 6 - 28) for _, q in qs)
    q_h = box_h(T['body'], q_lines, single=1.72) + 28
    zQ_h = (yQ - zQ_y) + q_h + 16
    zq = f.zone('zQ', [26, zQ_y, 1484, zQ_h], S('判断提醒'), 'note')
    for k, (qid, q) in enumerate(qs):
        x = X0 + k * (QW + QG)
        f.card(qid, [x, yQ, QW, q_h], fam='note', container=zq, bar=6)
        text(f, qid + '_t', [x + 6 + 14, yQ + 14, QW - 6 - 28, q_h - 28], S(q), T['body'], bold=False,
             color=FAM['note']['text'], align='center', container=qid, lines=q_lines)

    # 分叉：前驱体筛选 → 两条通道；汇合：两条通道 → 表征
    fx = ex[2] + EW / 2
    fy = zL_y + zL_h + FK_DY
    l1c, l2c = lx[0] + LW / 2, lx[1] + LW / 2
    f.conn('fk0', [(fx, y0 + e_h + 5), (fx, fy)], arrow=False)
    f.conn('fkh', [(l1c, fy), (fx, fy)], arrow=False)
    f.conn('fk1', [(l1c, fy), (l1c, zE_y + 2)])
    f.conn('fk2', [(l2c if abs(l2c - fx) > 4 else fx, fy), (l2c if abs(l2c - fx) > 4 else fx, zE_y + 2)])
    my = zE_y + zE_h + GAP2 / 2
    f.conn('mg1', [(l1c, yE + l_h + 5), (l1c, my)], arrow=False)
    f.conn('mg2', [(l2c, yE + l_h + 5), (l2c, my)], arrow=False)
    f.conn('mgh', [(l1c, my), (l2c, my)], arrow=False)
    f.conn('mg3', [(768, my), (768, zR_y + 2)])
    # 反馈环：表征 → 回到结构假设（虚线，沿右侧走，在两带之间的空当横穿）
    rx_ = 1502
    by_ = zL_y + zL_h + FB_DY
    f.conn('fb', [(c5_x + c5_w + 5, yR + c5_h / 2), (rx_, yR + c5_h / 2), (rx_, by_),
                  (ex[1] + EW / 2, by_), (ex[1] + EW / 2, y0 + e_h + 6)], dashed=True,
           label=S('更新组成与工艺'),
           label_at=(ex[1] + EW / 2 + min(W(S('更新组成与工艺'), T['label']) + 32, fx - ex[1] - EW / 2 - 60) / 2 + 14,
                     by_),
           label_max_w=fx - ex[1] - EW / 2 - 60)

    return finish(f, [zl, ze, zr, zq], zQ_y + zQ_h + 26, out_path('fig03_r6', lang))


# ================================================================================================ 路线图
def roadmap(lang='zh'):
    S = tr(lang)
    f = new_fig(lang, 800, 'BaZn2Si2O7 本文的行文路线图（第六轮：印刷字号 + 内容定尺寸；3+3 两行）', 'bzso')
    T = f.T
    X0, INNER = 42, 1452
    cards = [('n1', '01', '结构基础', '低温与高温多晶型', 'lit', 'polyhedron', None),
             ('n2', '02', '合成路线', '固相 · 溶胶—凝胶', 'lit', 'crucible', None),
             ('n3', '03', '相控制', '组成 · 热处理', 'lit', 'layers', None),
             ('n4', '04', '近邻体系', 'Ba–Sr–Zn–Si', 'exp', 'cubes', None),
             ('n5', '05', '类似物判据', 'Ba5Y12Zn[O(SiO4)]8', 'note', 'balance', '#FFFAF0'),
             ('n6', '06', '实验优先级', '相图 · 结构 · 热力学', 'exp', 'checklist', None)]
    CG = 66
    CW = (INNER - 2 * CG) // 3
    t_lines = max(nlines(S(t), T['title'], CW - 10 - 36, True) for _, _, t, *_ in cards)
    p_lines = max(nlines(S(p), T['body'], CW - 10 - 36 - 14) for *_, p, _, _, _ in cards)
    GLW = 64
    num_h = int(T['number'] * 1.7)
    top_h = max(num_h, GLW)
    tt_h = box_h(T['title'], t_lines, single=1.6)
    pt_h = box_h(T['body'], p_lines, single=1.8)
    C_H = 18 + top_h + 8 + tt_h + 12 + 2 + 12 + pt_h + 18

    def band(zid, zy, label, fam):
        y0 = zone_top(f, zy)
        zh = (y0 - zy) + C_H + 18
        return f.zone(zid, [26, zy, 1484, zh], S(label), fam), y0, zh

    zA, yA, hA = band('zA', 26, '文献证据', 'lit')
    GAPB = 78
    zB_y = 26 + hA + GAPB
    zB, yB, hB = band('zB', zB_y, '实验方法', 'exp')

    pos = []
    for k, (cid, num, t, p, fam, g, fill) in enumerate(cards):
        row, col = divmod(k, 3)
        x = X0 + col * (CW + CG)
        y = (yA, yB)[row]
        pos.append((x, y))
        f.card(cid, [x, y, CW, C_H], fam=fam, container=(zA, zB)[row], bar=10, fill=fill)
        text(f, cid + '_n', [x + 10 + 18, y + 18, 110, num_h], num, T['number'], bold=True,
             color=FAM[fam]['text'], container=cid)
        f.m.draw(g, cid + '_g', [x + CW - 18 - GLW, y + 18 + (top_h - GLW) / 2, GLW, GLW], container=cid)
        ty = y + 18 + top_h + 8
        text(f, cid + '_t', [x + 10 + 18, ty, CW - 10 - 36, tt_h], S(t), T['title'], bold=True,
             color=FAM[fam]['text'], align='center', container=cid, lines=t_lines)
        ry = ty + tt_h + 12
        f.sc.line(cid + '_r', [(x + 10 + 24, ry), (x + CW - 24, ry)], stroke='#CBD5DE', width=1.6, container=cid)
        f.token(cid + '_p', [x + 10 + 18, ry + 14, CW - 10 - 36, pt_h], S(p), container=cid, wrap=p_lines > 1)

    # 分组标题右端：卡间标签与折线都不能压到它（英文标题长）
    def band_label_right(label):
        return 26 + 18 + min(W(S(label), T['group'], True) + 26, 1484 - 36)

    # 03 → 04 折到第二行：下行段落在第二带标题右侧（先定它，第二带的卡间标签要给它让位）
    (x3, y3), (x4, y4) = pos[2], pos[3]
    wy = 26 + hA + GAPB / 2
    dx = max(x4 + CW / 2, band_label_right('实验方法') + 30)

    # 同一行的卡间箭头；标签挂在分组标题带里、正对卡间空当（英文标签宽，放不进空当）
    for k, lab in ((0, '结构约束'), (1, '条件窗口'), (3, '比较边界'), (4, '缺口驱动')):
        (x0, y), (x1, _) = pos[k], pos[k + 1]
        ay = y + C_H / 2
        gx = (x0 + CW + x1) / 2
        pw = W(S(lab), T['label']) + 32
        if k == 0:
            gx = max(gx, band_label_right('文献证据') + 16 + pw / 2)
        if k == 3:     # 既不压第二带标题，也不压折线的下行段
            gx = max(gx, band_label_right('实验方法') + 16 + pw / 2, dx + 20 + pw / 2)
        band_y = (26 if k < 3 else zB_y) + 10 + int(T['group'] * 1.6) / 2 + 2
        f.conn(f'e{k}', [(x0 + CW + 6, ay), (x1 - 6, ay)], label=S(lab), label_at=(gx, band_y))
    f.conn('e2', [(x3 + CW / 2, y3 + C_H + 4), (x3 + CW / 2, wy), (dx, wy), (dx, y4 - 4)],
           label=S('可迁移变量'), label_at=(768, wy))

    return finish(f, [zA, zB], zB_y + hB + 26, out_path('bzso_roadmap_r6', lang))


# ================================================================================================ 分类框架
def taxonomy(lang='zh'):
    S = tr(lang)
    f = new_fig(lang, 1000, 'BaZn2Si2O7 合成与相控制的分类框架（第六轮：印刷字号 + 内容定尺寸；'
                            '箭头一律由枢纽指向分支，全图只有一段虚线）', 'bzso')
    T = f.T
    exp = [('e1', '结构与多晶型', '相变 · 配位', 'lattice', '结构'),
           ('e2', '合成路线', '固相 · 溶胶—凝胶', 'flask', '制备'),
           ('e3', '组成与热处理', 'Ba/Sr · Zn 位', 'thermo', '变量'),
           ('e4', '玻璃析晶', '成核 · 生长', 'crystals', '晶化')]
    lit = [('l1', '近邻体系', 'Ba2ZnSi2O7 等', 'cubes', '近邻', False),
           ('l2', '证据边界', '直接 / 近邻 / 推断', 'boundary', '判读', False),
           ('l3', 'Ba5Y12Zn[O(SiO4)]8', '未见直接报道', 'cubes', '类比', True)]

    # 列宽固定：两种语言同一套骨架，只有卡片高度随折行变化
    ZE_W, HUB_W, ZL_W, GAP, LANE, GW = 548, 240, 632, 32, 110, 48
    zE = (26, ZE_W)
    hub_x = 26 + ZE_W + GAP
    zL = (hub_x + HUB_W + GAP, ZL_W)
    left_card = ZE_W - 32 - LANE
    right_card = ZL_W - 32 - LANE

    room_l = card_title_room(left_card, gw=GW)
    room_r = card_title_room(right_card, gw=GW)
    lt = max(nlines(S(t), T['title'], room_l, True) for _, t, *_ in exp)
    ls = max(nlines(S(x), T['body'], room_l) for _, _, x, *_ in exp)
    rt = max(nlines(S(t), T['title'], room_r, True) for _, t, *_ in lit)
    rs = max(nlines(S(x), T['body'], room_r) for _, _, x, *_ in lit)
    left_h = box_h(T['title'], lt) + box_h(T['body'], ls, single=1.7) + 2 + 34
    right_h = box_h(T['title'], rt) + box_h(T['body'], rs, single=1.7) + 2 + 34

    # 分支标签：放得进连线通道就压在分支上方；放不进（英文）就放到卡片上方的空当里
    pill_h = int(T['label'] * 1.5) + 12
    labels = [S(e[4]) for e in exp] + [S(l[4]) for l in lit]
    in_lane = all(W(lb, T['label']) + 32 <= LANE - 12 for lb in labels)
    LG = 24 if in_lane else pill_h + 18
    top_pad = 0 if in_lane else pill_h + 12

    y0 = zone_top(f, 26) + top_pad
    body = 4 * left_h + 3 * LG
    right_h = max(right_h, min((body - 2 * max(LG, 40)) / 3, right_h + 70))
    RG = (body - 3 * right_h) / 2
    zone_h = (y0 - 26) + body + 18
    ze = f.zone('zE', [zE[0], 26, zE[1], zone_h], S('实验方法'), 'exp')
    zl = f.zone('zL', [zL[0], 26, zL[1], zone_h], S('文献证据'), 'lit')

    # 枢纽
    th = box_h(T['title'], 1)
    sh = box_h(T['body'], 1, single=1.7)
    hub_h = 22 + 100 + 10 + th + sh + 22
    hy = y0 + (body - hub_h) / 2
    f.card('hub', [hub_x, hy, HUB_W, hub_h], fam='exp', bar=0)
    f.m.draw('lattice', 'hub_g', [hub_x + HUB_W / 2 - 50, hy + 22, 100, 100], container='hub')
    text(f, 'hub_t', [hub_x + 12, hy + 22 + 100 + 10, HUB_W - 24, th], 'BaZn2Si2O7', T['title'], bold=True,
         color=FAM['exp']['text'], align='center', container='hub')
    text(f, 'hub_s', [hub_x + 12, hy + 22 + 100 + 10 + th, HUB_W - 24, sh], S('目标相'), T['body'], bold=False,
         color=FAM['exp']['text'], align='center', container='hub')
    hub_mid = hy + hub_h / 2

    lcx = zE[0] + 16
    ey = [y0 + k * (left_h + LG) for k in range(4)]
    for (cid, t, x, g, _), y in zip(exp, ey):
        head_card(f, cid, [lcx, y, left_card, left_h], S(t), fam='exp', glyph=g, container=ze, sub=S(x),
                  lines=lt, sub_lines=ls, gw=GW)
    rcx = zL[0] + 16 + LANE
    ry = [y0 + k * (right_h + RG) for k in range(3)]
    for (cid, t, x, g, _, dashed), y in zip(lit, ry):
        head_card(f, cid, [rcx, y, right_card, right_h], S(t), fam=('note' if dashed else 'lit'), glyph=g,
                  dashed=dashed, container=zl, sub=S(x), lines=rt, sub_lines=rs, gw=GW,
                  fill=('#FFFAF0' if dashed else None))

    def label_pos(lab, trunk_x, card_y, arrow_y, side):
        """side = -1：通道在卡片右侧（左分组）；+1：通道在卡片左侧（右分组）。"""
        pw = W(lab, T['label']) + 32
        if in_lane:
            return (trunk_x + side * (LANE - 14) / 2, arrow_y - pill_h / 2 - 8)
        gap_mid = card_y - (LG if card_y > y0 + 1 else top_pad) / 2
        cx = trunk_x - 12 - pw / 2 if side < 0 else trunk_x + 12 + pw / 2
        return (cx, gap_mid)

    # 分支一律由枢纽出发
    sx = lcx + left_card + LANE - 14
    f.conn('sl', [(hub_x - 5, hub_mid), (sx, hub_mid)], arrow=False)
    f.conn('slv', [(sx, ey[0] + left_h / 2), (sx, ey[3] + left_h / 2)], arrow=False)
    for (cid, *_r, lab), y in zip(exp, ey):
        yy = y + left_h / 2
        f.conn(f's_{cid}', [(sx, yy), (lcx + left_card + 4, yy)], label=S(lab),
               label_at=label_pos(S(lab), sx, y, yy, -1))
    vx = zL[0] + 16 + 14
    f.conn('sr', [(hub_x + HUB_W + 5, hub_mid), (vx, hub_mid)], arrow=False)
    f.conn('srv', [(vx, ry[0] + right_h / 2), (vx, ry[2] + right_h / 2)], arrow=False)
    for (cid, _t, _x, _g, lab, dashed), y in zip(lit, ry):
        yy = y + right_h / 2
        f.conn(f'v_{cid}', [(vx, yy), (rcx - 4, yy)], dashed=dashed, label=S(lab),
               label_at=label_pos(S(lab), vx, y, yy, +1),
               label_fam=('note' if dashed else None), color=(FAM['note']['edge'] if dashed else '#4B5563'))

    return finish(f, [ze, zl], 26 + zone_h + 26, out_path('bzso_taxonomy_r6', lang))


FIGS = {'fig01': fig01, 'fig02': fig02, 'fig03': fig03, 'roadmap': roadmap, 'taxonomy': taxonomy}

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    langs = {'zh': ['zh'], 'en': ['en'], 'both': ['zh', 'en']}[sys.argv[2] if len(sys.argv) > 2 else 'both']
    for name, fn in FIGS.items():
        if which in ('all', name):
            for lang in langs:
                r = fn(lang)
                print(f'{name:<9} {lang}  {r.sc.w}×{r.sc.h}  {len(r.sc.els)} elements  T={r.T}')
