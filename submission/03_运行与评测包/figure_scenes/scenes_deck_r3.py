"""答辩 PPT · 「多智能体并行闭环」· 第三轮：与整套 PPT 统一（品牌蓝 / 青色数字 / 橙色返修），内容落到化学流程上，用词专业化。

作者从第二轮的 S2 候选里点了两种构图，图一各出一份最终可编辑页，供挑选：
  * parallel_bands()  —— 候选 C01：三条横向相位带，编排器在左侧分派，账本轨与 KPI 在下；
  * parallel_ring()   —— 候选 C03：编排器 + 运行账本居中，三个相位绕一圈成环（顺时针），橙色返修弧闭环；
  * converge()        —— 图二（交叉核验 → 问题路由 → 程序化放行）同一套主题与用词，证据条换成真实账本数字。

数字全部取自 `正式案例_BYZSO冷启动/ledger.json`：29 批 / 40 项子任务 / 134 次审计调用；问题 I1–I4（生产阶段，3 blocker + 1 major）、
I5–I9（第 1 轮评审，1 blocker + 3 major + 1 minor）、I10–I11（第 2 轮终审，2 minor，当轮关闭）；九道闸门 PASS 6 · WARN 3。

usage: python3 scenes_deck_r3.py [bands|ring|converge|all] [--art <dir>]
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import deckstyle as DS  # noqa: E402

DS.use_theme('sagemat')
from deckstyle import Deck, TONE, SZ, KIND  # noqa: E402

INK, MUTED, NAVY = DS.INK, DS.MUTED, DS.NAVY
_REPO = pathlib.Path(__file__).resolve().parents[3]
JOBS_DIR = pathlib.Path(os.environ.get('GOAI_FIGSTUDIO_JOBS', _REPO.parent / 'final_round/figstudio/jobs'))
ART = None          # set by --art: a directory of PNG assets named as in A() below

LEGEND_1 = [('main', '主流程'), ('dispatch', '任务分派'), ('retry', '定向返修'), ('keep', '通过放行'), ('write', '记录入账')]
# gate → (短名, 账本里的状态)；顺序同 check-done 的必需闸门表
GATES = [('范围确认', 'PASS'), ('文献覆盖', 'WARN'), ('范式库', 'WARN'), ('引用完整', 'PASS'), ('证据分类', 'PASS'), ('图表就绪', 'PASS'),
         ('方案评审', 'WARN'), ('稿件完成', 'PASS'), ('终审通过', 'PASS')]
KPIS = [('29', '批', '并行批次', 'blue'), ('40', '项子任务', '各写各的分片', 'teal'), ('≤4', '路并行', '单批并发上限', 'green'),
        ('134', '次工具调用', 'MCP · 服务端审计', 'peach')]


# ------------------------------------------------------------------------------------------------ building blocks
def A(name):
    """(path, provenance) for an art slot, or None in blueprint mode / when the asset is missing."""
    if not ART:
        return None
    p = pathlib.Path(ART) / f'{name}.png'
    return (f'art/{name}.png', f'cropped from the image-model asset sheet, cell "{name}" (Codex image_gen)') if p.exists() else None


def slot(d, cid, box, name, container=None):
    """Art slot: the picture in final mode, a faint placeholder ring in blueprint mode."""
    a = A(name)
    if a:
        d.art(cid, box, a[0], a[1], container=container)
    else:
        x, y, w, h = box
        d.sc.shape(cid, [x + w * 0.1, y + h * 0.1, w * 0.8, h * 0.8], shape='ellipse', fill='#F3F4F6', stroke='#D1D5DB', stroke_width=1.5,
                   dash=[6, 5], container=container)


def hcard(d, cid, box, title, lines, art, container, art_w=76, ts=None, ls=16):
    """Card with the art on the left: art | bold title / one or two grey lines (left-aligned, vertically centred)."""
    x, y, w, h = box
    ts = ts or SZ['title']
    d.card(cid, box, '', None, container=container)
    slot(d, cid + '_art', [x + 8, y + 8, art_w, h - 16], art, container=cid)
    tx = x + 8 + art_w + 8
    tw = w - (tx - x) - 8
    th, lh = int(ts * 1.5) + 1, int(ls * 1.5) + 1
    ty = y + (h - th - lh * len(lines)) / 2
    d.sc.text(cid + '_t', [tx, ty, tw, th], title, ts, bold=True, color=INK, align='left', container=cid, fit='shrink', min_font_size=ts - 6)
    for k, ln in enumerate(lines):
        d.sc.text(f'{cid}_s{k}', [tx, ty + th + k * lh, tw, lh], ln, ls, color=MUTED, align='left', container=cid, fit='shrink',
                  min_font_size=ls - 4)


def vcard(d, cid, box, title, lines, art, container, art_h=64, ts=21, ls=15):
    """Card with the art on top: art, bold title, one or two grey lines — all centred."""
    x, y, w, h = box
    d.card(cid, box, '', None, container=container)
    th, lh = int(ts * 1.5) + 1, int(ls * 1.5) + 1
    block = art_h + 4 + th + lh * len(lines)
    ay = y + (h - block) / 2
    slot(d, cid + '_art', [x + 8, ay, w - 16, art_h], art, container=cid)
    d.sc.text(cid + '_t', [x + 6, ay + art_h + 4, w - 12, th], title, ts, bold=True, color=INK, container=cid, fit='shrink', min_font_size=ts - 6)
    for k, ln in enumerate(lines):
        d.sc.text(f'{cid}_s{k}', [x + 6, ay + art_h + 4 + th + k * lh, w - 12, lh], ln, ls, color=MUTED, container=cid, fit='shrink',
                  min_font_size=ls - 4)


def tcard(d, cid, box, title, lines, container=None, ts=24, ls=16):
    """Text-only card, centred."""
    x, y, w, h = box
    d.card(cid, box, '', None, container=container)
    th, lh = int(ts * 1.5) + 1, int(ls * 1.5) + 2
    ty = y + (h - th - lh * len(lines)) / 2
    d.sc.text(cid + '_t', [x + 6, ty, w - 12, th], title, ts, bold=True, color=INK, container=cid)
    for k, ln in enumerate(lines):
        d.sc.text(f'{cid}_s{k}', [x + 6, ty + th + k * lh, w - 12, lh], ln, ls, color=MUTED, container=cid, fit='shrink', min_font_size=ls - 4)


def pgroup(d, gid, box, count, container, strip=True):
    """「并行」分组：蓝色虚线框住同时执行的子任务；左侧窄条竖排「并行 ×N」。返回组内第一张卡片的 x。"""
    x, y, w, h = box
    blue = KIND['dispatch']['color']
    d.sc.shape(gid, box, fill='#F7FAFE', stroke=blue, stroke_width=1.8, radius=14, dash=[7, 5], container=container)
    if not strip:
        return x + 8
    top = y + (h - 3 * 27) / 2
    for k, ch in enumerate(('并', '行', f'×{count}')):
        d.sc.text(f'{gid}_l{k}', [x + 5, top + k * 27, 30, 27], ch, 17 if k < 2 else 16, bold=True, color=blue, container=gid)
    return x + 8 + 30


def gate_tile(d, gid, box, name, status, container, size=13, inline=False):
    t = TONE['green' if status == 'PASS' else 'amber']
    mark = '✓' if status == 'PASS' else '△'
    x, y, w, h = box
    d.sc.shape(gid, box, fill=t['fill'], stroke=t['stroke'], stroke_width=1.5, radius=9, container=container)
    if inline:
        d.sc.text(gid + '_t', [x + 2, y, w - 4, h], f'{mark} {name}', size, bold=True, color=t['text'], container=gid, fit='shrink',
                  min_font_size=size - 3)
    else:
        d.sc.text(gid + '_c', [x, y + 3, w, h / 2 - 2], mark, size + 5, bold=True, color=t['accent'], container=gid)
        d.sc.text(gid + '_t', [x + 2, y + h / 2, w - 4, h / 2 - 3], name, size, bold=True, color=t['text'], container=gid, fit='shrink',
                  min_font_size=size - 3)


def allow(d, ids, others, why):
    for e in d.sc.els:
        if e['id'] in ids:
            e['allow_overlap_with'] = sorted(set(e.get('allow_overlap_with', [])) | set(others))
            e.setdefault('overlap_reason', why)


def deliver_card(d, cid, box, icons, container=None):
    """交付物：综述 + 合成方案 → OpenLab（与 PPT 的「方案 → 工作流 → 自动化实验室」主线接上）。"""
    x, y, w, h = box
    d.card(cid, box, '', None, container=container)
    for e in d.sc.els:
        if e['id'] == cid:
            e['stroke'], e['stroke_width'] = KIND['keep']['color'], 2.4
    d.sc.text(cid + '_t', [x + 14, y + 5, w - 28, 36], '交付', SZ['title'], bold=True, color=INK, align='left', container=cid)
    d.sc.text(cid + '_s0', [x + 14, y + 40, w - 28, 24], '综述 PDF 23 页 · 引用核验 51/51', 16, color=MUTED, align='left', container=cid,
              fit='shrink', min_font_size=13)
    d.sc.text(cid + '_s1', [x + 14, y + 64, w - 28, 24], '合成方案 → OpenLab 工作流', 16, color=MUTED, align='left', container=cid,
              fit='shrink', min_font_size=13)
    iw = (w - 28 - 8 * (len(icons) - 1)) / len(icons)
    for k, name in enumerate(icons):
        slot(d, f'{cid}_i{k}', [x + 14 + k * (iw + 8), y + 92, iw, h - 100], name, container=cid)


def write(d, job):
    p = JOBS_DIR / job / 'scene.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    d.write(p)


# ================================================================================================ 1/2 · 构图 A：三条横向相位带（C01）
def parallel_bands():
    d = Deck('多智能体并行闭环 1/2 · 构图 A：三条横向相位带（S2 候选 C01），编排器在左分派，运行账本与 KPI 在下（round 3, deck theme）')
    sc = d.sc
    d.headline_bar('完成判定由程序执行，而非模型自述', None, x=40, y=118)
    d.hlegend('lg', 1496, 118, LEGEND_1)

    # ---- 左列：研究课题 → 编排器
    LX, LW = 40, 196
    lcx = LX + LW / 2
    vcard(d, 'topic', [LX, 176, LW, 140], '研究课题', ['Ba–Y–Zn–Si–O 新相合成'], 'structure', None, art_h=62, ts=22, ls=15)
    d.flow('f_topic', [(lcx, 321), (lcx, 348)], 'main')
    slot(d, 'orc_art', [LX + 12, 358, LW - 24, 178], 'orchestrator')
    tcard(d, 'orc', [LX, 542, LW, 130], '编排器', ['建账 · 任务分派', '闸门校验 · 问题路由'])

    # ---- 三条相位带
    BX, BW, BH = 276, 1140, 144
    Y1, Y2, Y3 = 176, 360, 532
    IX, IR = BX + 8 + 76 + 12, BX + BW - 14                 # inner left / right
    G = 32                                                   # gap that holds one arrow
    CH = BH - 28                                             # card height
    b1 = d.band('b1', [BX, Y1, BW, BH], '1', ['文献', '取证'], 'blue')
    b2 = d.band('b2', [BX, Y2, BW, BH], '2', ['并行', '生产'], 'teal')
    b3 = d.band('b3', [BX, Y3, BW, BH], '3', ['评审', '放行'], 'green')
    for k, (ya, yb) in enumerate(((Y1 + BH, Y2), (Y2 + BH, Y3))):   # 1 → 2 → 3
        d.flow(f'f_seq{k}', [(BX + 46, ya + 3), (BX + 46, yb - 3)], 'main')

    def arrow(fid, x0, x1, y):
        d.flow(fid, [(x0 + 5, y), (x1 - 7, y)], 'main')

    # 带 1：体系界定 → [文献检索 ∥ 综述范式库] → 引用核验
    y, cy = Y1 + 14, Y1 + BH / 2
    hcard(d, 'scope', [IX, y, 226, CH], '体系界定', ['目标相与近邻', '相图与热力学'], 'phasediagram', b1)
    gx = IX + 226 + G
    cx0 = pgroup(d, 'g1', [gx, y - 8, 512, CH + 16], 2, b1)
    hcard(d, 'lit', [cx0, y, 228, CH], '文献检索', ['五源与本地全文库', '分片并发 ≥3 路'], 'litdb', 'g1', art_w=72, ls=15)
    hcard(d, 'style', [cx0 + 238, y, 228, CH], '综述范式库', ['30 篇高水平综述', '结构与写作规范'], 'style', 'g1', ts=21)
    rx = gx + 512 + G
    hcard(d, 'ref', [rx, y, 226, CH], '引用核验', ['引用 51/51 条', '比对 DOI 与原文'], 'refguard', b1, art_w=72, ls=15)
    arrow('f_1a', IX + 226, gx, cy)
    arrow('f_1b', gx + 512, rx, cy)

    # 带 2：证据分类（合成条件表）→ [图表制作 ∥ 综述撰写 ∥ 合成方案构想]
    y, cy = Y2 + 14, Y2 + BH / 2
    hcard(d, 'tax', [IX, y, 236, CH], '证据分类', ['路线×条件×表征', '合成条件表'], 'condtable', b2)
    gx = IX + 236 + G
    gw = IR - gx
    cx0 = pgroup(d, 'g2', [gx, y - 8, gw, CH + 16], 3, b2)
    cw = (gw - 8 - 30 - 8 - 20) / 3
    lanes = [('fig', '图表制作', ['可编辑矢量图', '路线图 · 分类图'], 'figure', 76),
             ('draft', '综述撰写', ['按章节并行', '论断逐条绑定引用'], 'writer', 76),
             ('idea', '合成方案构想', ['RECIPE 前驱体预测', 'BaCO₃ · Y₂O₃', 'ZnO · SiO₂'], 'precursors', 62)]
    for k, (cid, t, ls_, art, aw) in enumerate(lanes):
        hcard(d, cid, [cx0 + k * (cw + 10), y, cw, CH], t, ls_, art, 'g2', art_w=aw, ts=21, ls=15)
    arrow('f_2a', IX + 236, gx, cy)

    # 带 3：[领域专家 ∥ 方法审查 ∥ 期刊编辑] → 评审意见 → 裁决
    y, cy = Y3 + 14, Y3 + BH / 2
    cx0 = pgroup(d, 'g3', [IX, y - 8, 642, CH + 16], 3, b3)
    revs = [('rv0', '领域专家', ['覆盖缺口', '分类合理性'], 'researcher'), ('rv1', '方法审查', ['论断–引用绑定', '条件表数值'], 'reviewer'),
            ('rv2', '期刊编辑', ['版面与图表', '逐页审读 PDF'], 'pdf')]
    for k, (cid, t, ls_, art) in enumerate(revs):
        hcard(d, cid, [cx0 + k * 202, y, 192, CH], t, ls_, art, 'g3', art_w=62, ts=22, ls=15)
    ix = IX + 642 + G
    hcard(d, 'iss', [ix, y, 200, CH], '评审意见', ['按严重度分级', '标注责任阶段'], 'route', b3, art_w=60)
    vx = IR - 59
    d.diamond('verdict', vx, cy, 118, 104, '裁决', container=b3)
    arrow('f_3a', IX + 642, ix, cy)
    arrow('f_3b', ix + 200, vx - 59, cy)

    # 任务分派（蓝虚线）：编排器 → 三条带
    tx = 254
    c1, c2, c3 = Y1 + BH / 2, Y2 + BH / 2, Y3 + BH / 2
    d.flow('f_d1', [(LX + LW - 2, c2), (BX - 3, c2)], 'dispatch')
    d.flow('f_d0', [(tx, c2), (tx, c1), (BX - 3, c1)], 'dispatch')
    d.flow('f_d2', [(tx, c2), (tx, c3), (BX - 3, c3)], 'dispatch')

    # 定向返修（橙色回路）：裁决 → 右侧 → 带 1/2 之间 → 证据分类
    ry = 336
    d.rflow('ret', [(IR + 6, c3), (1462, c3), (1462, ry), (IX + 118, ry), (IX + 118, Y2 + 14 - 6)], 'retry', r=24)
    d.tag('t_ret', 930, ry, '评审意见定向返修 · 仅重跑责任阶段 · 至多 5 轮', 'retry', size=15)

    # 通过放行（绿色）：裁决 → 交付
    DY = 700
    d.flow('f_pass', [(vx, c3 + 52 + 5), (vx, DY - 7)], 'keep')
    d.tag('t_pass', vx - 146, 684, 'PASS：blocker = 0 且 major = 0', 'keep', size=13)
    for e in sc.els:                                        # Latin bold sets wider in the renderer than the estimate
        if e['id'] in ('t_pass', 't_pass_t'):
            e['box'][0] -= 10
            e['box'][2] += 20
    deliver_card(d, 'deliver', [1170, DY, 326, 154], ['pdf', 'plan', 'workflow', 'robotlab'])

    # 运行账本：九道闸门
    sc.shape('rail', [40, DY, 1110, 72], fill='#FFFFFF', stroke=NAVY, stroke_width=2, radius=14)
    slot(d, 'rail_art', [50, DY + 6, 60, 60], 'ledger', 'rail')
    sc.text('rail_t', [118, DY + 7, 262, 32], '运行账本 ledger.json', 21, bold=True, color=INK, align='left', container='rail')
    sc.text('rail_s', [118, DY + 39, 266, 26], '✓ PASS 6 · △ WARN 3 · 降级须入账', 14, color=MUTED, align='left', container='rail',
            fit='shrink', min_font_size=12)
    gx0, gw_ = 392, 78
    for k, (name, st) in enumerate(GATES):
        gate_tile(d, f'gate{k}', [gx0 + k * (gw_ + 6), DY + 8, gw_, 56], name, st, 'rail')
    for k, px in enumerate((470, 760, 1040)):
        d.flow(f'f_w{k}', [(px, Y3 + BH + 3), (px, DY - 4)], 'write')
    d.flow('f_w3', [(lcx, 542 + 130 + 5), (lcx, DY - 4)], 'write')

    # KPI 条（PPT 第 12 页的数字卡样式：浅色卡 + 顶部色条 + 青色大数字）
    for k, (big, unit, cap, rule) in enumerate(KPIS):
        d.tile(f'kpi{k}', [40 + k * 280.6, 782, 268, 72], big, unit, cap, tone='teal', rule=rule, big_size=44, unit_size=20)
    write(d, 'deck_loop_parallel_r3a')


# ================================================================================================ 1/2 · 构图 B：账本居中成环（C03）
def mini(d, cid, box, title, line, art, container, art_w=44, ts=19, ls=13):
    """Slim row card for stacked parallel lanes: art | title / one line."""
    hcard(d, cid, box, title, [line] if line else [], art, container, art_w=art_w, ts=ts, ls=ls)


def parallel_ring():
    d = Deck('多智能体并行闭环 1/2 · 构图 B：编排器 + 运行账本居中，三个相位顺时针成环（S2 候选 C03），橙色返修弧闭环（round 3, deck theme）')
    sc = d.sc
    d.headline_bar('完成判定由程序执行，而非模型自述', None, x=40, y=118)
    d.hlegend('lg', 1496, 118, LEGEND_1)

    P1, P2 = [40, 196, 500, 282], [996, 196, 500, 282]
    HUB = [586, 232, 364, 334]
    P3 = [240, 596, 1056, 166]
    p1 = d.panel('p1', P1, '1 · 文献取证', 'blue')
    p2 = d.panel('p2', P2, '2 · 并行生产', 'teal')
    p3 = d.panel('p3', P3, '3 · 评审放行', 'green')
    CY0, CHH = 258, 204                                          # tall single cards in P1/P2
    cym = CY0 + CHH / 2

    def arrow(fid, x0, x1, y, rev=False):
        d.flow(fid, [(x1 - 5, y), (x0 + 7, y)] if rev else [(x0 + 5, y), (x1 - 7, y)], 'main')

    def group_tag(tid, gid, cx, y, n, panel):
        d.tag(tid, cx, y, f'并行 ×{n}', 'dispatch', size=14)
        allow(d, (tid, tid + '_t'), [gid, panel], 'the parallel badge sits on the dashed group border')
        allow(d, (gid,), [tid, tid + '_t'], 'the parallel badge sits on the dashed group border')

    # P1：体系界定 → [文献检索 ∥ 综述范式库] → 引用核验
    x = P1[0] + 12
    vcard(d, 'scope', [x, CY0, 120, CHH], '体系界定', ['目标相与近邻', '相图与热力学'], 'phasediagram', p1, art_h=84)
    g1 = [x + 156, 266, 164, 204]
    pgroup(d, 'g1', g1, 2, p1, strip=False)
    mini(d, 'lit', [g1[0] + 8, 288, 148, 84], '文献检索', '五源与全文库', 'litdb', 'g1', art_w=38, ts=18)
    mini(d, 'style', [g1[0] + 8, 378, 148, 84], '范式库', '30 篇范文', 'style', 'g1', art_w=38, ts=18)
    group_tag('g1_tag', 'g1', g1[0] + g1[2] / 2, 266, 2, p1)
    vcard(d, 'ref', [x + 356, CY0, 120, CHH], '引用核验', ['引用 51/51 条', '逐条比对原文'], 'refguard', p1, art_h=84, ls=14)
    arrow('f_1a', x + 120, g1[0], cym)
    arrow('f_1b', g1[0] + g1[2], x + 356, cym)

    # P2：证据分类 → [图表制作 ∥ 综述撰写 ∥ 合成方案构想]
    x = P2[0] + 12
    vcard(d, 'tax', [x, CY0, 120, CHH], '证据分类', ['路线·条件·表征', '合成条件表'], 'condtable', p2, art_h=84, ls=14)
    g2 = [x + 156, 266, 320, 204]
    pgroup(d, 'g2', g2, 3, p2, strip=False)
    lanes = [('fig', '图表制作', '可编辑矢量图 · 路线图与分类图', 'figure'), ('draft', '综述撰写', '按章节并行 · 论断逐条绑定引用', 'writer'),
             ('idea', '合成方案构想', 'RECIPE 前驱体预测 · 内部质询', 'precursors')]
    for k, (cid, t, ln, art) in enumerate(lanes):
        mini(d, cid, [g2[0] + 8, 287 + k * 60, 304, 55], t, ln, art, 'g2', art_w=50)
    group_tag('g2_tag', 'g2', g2[0] + g2[2] / 2, 266, 3, p2)
    arrow('f_2a', x + 120, g2[0], cym)

    # P3（自右向左，顺时针）：[三视角评审] → 评审意见 → 裁决
    y3, ch3 = P3[1] + 56, 100
    cy3 = y3 + ch3 / 2
    il, ir = P3[0] + 12, P3[0] + P3[2] - 12
    g3 = [642, y3 - 6, ir - 642, ch3 + 12]
    cx0 = pgroup(d, 'g3', g3, 3, p3)
    cw = (g3[2] - 8 - 30 - 8 - 20) / 3
    revs = [('rv0', '领域专家', ['覆盖缺口', '分类合理性'], 'researcher'), ('rv1', '方法审查', ['论断–引用绑定', '条件表数值'], 'reviewer'),
            ('rv2', '期刊编辑', ['版面与图表', '逐页审读 PDF'], 'pdf')]
    for k, (cid, t, ls_, art) in enumerate(revs):
        hcard(d, cid, [cx0 + k * (cw + 10), y3, cw, ch3], t, ls_, art, 'g3', art_w=58, ts=21, ls=14)
    hcard(d, 'iss', [406, y3, 200, ch3], '评审意见', ['按严重度分级', '标注责任阶段'], 'route', p3, art_w=58, ts=21, ls=15)
    vx = il + 59
    d.diamond('verdict', vx, cy3, 118, 96, '裁决', container=p3)
    arrow('f_3a', 606, 642, cy3, rev=True)
    arrow('f_3b', vx + 59, 406, cy3, rev=True)

    # 中央：编排器 + 运行账本
    hx, hy, hw, hh = HUB
    sc.shape('hub_sh', [hx + 2, hy + 5, hw, hh], fill=DS.SHADOW, radius=18, overlap=['hub'], reason='soft offset shadow, decoration only')
    sc.els[-1]['role'] = 'decoration'
    sc.shape('hub', HUB, fill='#FFFFFF', stroke=NAVY, stroke_width=2.4, radius=18, overlap=['hub_sh'], reason='hub sits on its own soft shadow')
    slot(d, 'hub_orc', [hx + 12, hy + 10, 124, 136], 'orchestrator', 'hub')
    sc.text('hub_t', [hx + 144, hy + 22, hw - 156, 40], '编排器', 25, bold=True, color=INK, align='left', container='hub')
    sc.text('hub_s0', [hx + 144, hy + 64, hw - 156, 26], '建账 · 任务分派', 16, color=MUTED, align='left', container='hub')
    sc.text('hub_s1', [hx + 144, hy + 90, hw - 156, 26], '闸门校验 · 问题路由', 16, color=MUTED, align='left', container='hub')
    sc.line('hub_div', [(hx + 14, hy + 152), (hx + hw - 14, hy + 152)], stroke=DS.NODE_STROKE, width=2, container='hub')
    slot(d, 'hub_led', [hx + 14, hy + 160, 52, 44], 'ledger', 'hub')
    sc.text('hub_lt', [hx + 74, hy + 156, hw - 86, 30], '运行账本 ledger.json', 19, bold=True, color=INK, align='left', container='hub')
    sc.text('hub_ls', [hx + 74, hy + 186, hw - 86, 24], '✓ PASS 6 · △ WARN 3 · 降级须入账', 14, color=MUTED, align='left',
            container='hub', fit='shrink', min_font_size=12)
    gw_ = (hw - 28 - 16) / 3
    for k, (name, st) in enumerate(GATES):
        gate_tile(d, f'gate{k}', [hx + 14 + (k % 3) * (gw_ + 8), hy + 216 + (k // 3) * 38, gw_, 32], name, st, 'hub', size=14, inline=True)
    allow(d, ('hub_sh',), [e['id'] for e in sc.els if e.get('container') == 'hub' or e['id'].startswith('gate')], 'soft offset shadow under the hub')

    # 顺时针主环：P1 → P2（上）、P2 → P3（右下弧）、P3 → P1（左下弧 = 定向返修）
    d.flow('f_12', [(P1[0] + P1[2] + 5, 212), (P2[0] - 7, 212)], 'main')
    d.tag('t_12', (P1[0] + P1[2] + P2[0]) / 2, 212, '闸门通过后进入下一阶段', 'main', bold=False, size=15)
    px2 = P2[0] + P2[2] - 110
    d.curve('f_23', (px2, P2[1] + P2[3] + 5), (px2, 640), (px2 + 30, cy3), (P3[0] + P3[2] + 7, cy3), 'main')
    px1 = P1[0] + 110
    px1 = P1[0] + 70
    d.curve('ret', (P3[0] - 5, cy3), (px1 - 10, cy3), (px1, 670), (px1, P1[1] + P1[3] + 8), 'retry')
    d.tag('t_ret', 300, 520, '评审意见定向返修', 'retry', size=16)
    d.tag('t_ret2', 300, 558, '仅重跑责任阶段 · 至多 5 轮', 'retry', bold=False, size=14)

    # 轮辐：任务分派（蓝虚线，出）与记录入账（灰，入）
    d.flow('f_d1', [(hx - 4, 300), (P1[0] + P1[2] + 5, 300)], 'dispatch')
    d.flow('f_d2', [(hx + hw + 4, 300), (P2[0] - 5, 300)], 'dispatch')
    d.flow('f_d3', [(hx + 110, hy + hh + 4), (hx + 110, P3[1] - 4)], 'dispatch')
    d.flow('f_w1', [(P1[0] + P1[2] + 4, 440), (hx - 5, 440)], 'write')
    d.flow('f_w2', [(P2[0] - 4, 440), (hx + hw + 5, 440)], 'write')
    d.flow('f_w3', [(hx + hw - 110, P3[1] - 4), (hx + hw - 110, hy + hh + 5)], 'write')

    # 通过放行 → 交付；KPI
    BY = 790
    d.flow('f_pass', [(vx, cy3 + 48 + 5), (vx, BY - 7)], 'keep')
    d.tag('t_pass', vx + 58, 772, 'PASS', 'keep', size=14)
    allow(d, ('t_pass', 't_pass_t'), ['p3'], 'the tag sits on the panel edge next to its arrow')
    bx, bw = 60, 520
    d.card('deliver', [bx, BY, bw, 64], '', None)
    for e in sc.els:
        if e['id'] == 'deliver':
            e['stroke'], e['stroke_width'] = KIND['keep']['color'], 2.4
    for k, name in enumerate(('pdf', 'plan', 'robotlab')):
        slot(d, f'deliver_i{k}', [bx + 10 + k * 58, BY + 6, 52, 52], name, 'deliver')
    sc.text('deliver_t', [bx + 190, BY + 5, bw - 200, 28], '交付 · 综述 PDF 23 页 · 引用 51/51', 17, bold=True, color=INK, align='left',
            container='deliver', fit='shrink', min_font_size=14)
    sc.text('deliver_s', [bx + 190, BY + 33, bw - 200, 26], '合成方案 → OpenLab 工作流 → 自动化实验', 15, color=MUTED, align='left',
            container='deliver', fit='shrink', min_font_size=13)
    kx, kw = bx + bw + 20, (1496 - (bx + bw + 20) - 3 * 10) / 4
    for k, (big, unit, cap, rule) in enumerate(KPIS):
        d.tile(f'kpi{k}', [kx + k * (kw + 10), BY, kw, 64], big, unit, cap.split(' · ')[-1], tone='teal', rule=rule, big_size=38, unit_size=17)
    write(d, 'deck_loop_parallel_r3b')


# ================================================================================================ 2/2 · 交叉核验与程序化放行
def pcard(d, cid, box, title, line, art, container, art_w=160, art_h=92, ts=21):
    """Pair card: bold title and one grey line on top, a wide art slot underneath."""
    x, y, w, h = box
    d.card(cid, box, '', None, container=container)
    th, lh = int(ts * 1.5) + 1, int(SZ['line'] * 1.5) + 1
    d.sc.text(cid + '_t', [x + 8, y + 8, w - 16, th], title, ts, bold=True, color=INK, container=cid, fit='shrink', min_font_size=ts - 5)
    d.sc.text(cid + '_s', [x + 8, y + 8 + th, w - 16, lh], line, SZ['line'], color=MUTED, container=cid, fit='shrink', min_font_size=SZ['line'] - 4)
    ay = y + 8 + th + lh + 4
    slot(d, cid + '_art', [x + (w - art_w) / 2, ay, art_w, min(art_h, y + h - 8 - ay)], art, container=cid)


def round_tile(d, sid, box, head, big, caption, tone, art=None):
    """轮次证据卡（PPT 数字卡样式）：浅色卡 + 顶部状态色条 + 小标题 + 大数字 + 一行说明。"""
    t = TONE[tone]
    x, y, w, h = box
    d.sc.shape(sid, box, fill='#EEF2F8', radius=8)
    d.sc.shape(sid + '_r', [x, y, w, 6], shape='rect', fill=t['accent'], container=sid)
    d.sc.text(sid + '_h', [x + 14, y + 12, w - 28, 28], head, 17, bold=True, color=INK, align='left', container=sid, fit='shrink',
              min_font_size=14)
    bw = d.sc.measure(big, SZ['big'], True) + 8
    d.sc.text(sid + '_b', [x + 14, y + 40, bw, 72], big, SZ['big'], bold=True, color=t['accent'], align='left', container=sid)
    d.sc.text(sid + '_u', [x + 14 + bw + 4, y + 66, 60, 34], '项', 20, bold=True, color=INK, align='left', container=sid)
    if art:
        d.art(sid + '_art', [x + w - 78, y + 42, 64, 64], art[0], art[1], container=sid)
    d.sc.text(sid + '_c', [x + 12, y + 112, w - 20, 28], caption, 13, color=MUTED, align='left', container=sid, fit='shrink', min_font_size=12)


def converge():
    d = Deck('多智能体并行闭环 2/2 · 交叉核验 → 问题路由与返修 → 程序化放行（round 3, deck theme；数字取自 BYZSO 正式案例账本）')
    sc = d.sc
    hx = d.headline_bar('交叉核验发现问题，定向返修逐项关闭', None, x=40, y=118)
    sc.text('hl_n', [hx + 20, 118, d.sc.measure('11 项问题 · 2 轮闭环', 25, True) + 8, 46], '11 项问题 · 2 轮闭环', 25, bold=True,
            color=TONE['peach']['accent'], align='left')
    d.hlegend('lg', 1496, 118, [('main', '主流程'), ('retry', '定向返修'), ('keep', '程序化放行'), ('escalate', '转人工裁决')])

    # ---- 三个相位
    P1 = [236, 182, 446, 410]
    P2 = [706, 322, 392, 270]
    P3 = [1116, 182, 380, 246]
    p1 = d.panel('p1', P1, '1 · 交叉核验', 'blue')
    p2 = d.panel('p2', P2, '2 · 问题路由与返修', 'teal')
    p3 = d.panel('p3', P3, '3 · 程序化放行', 'green')

    # 本轮产物（左）
    PB = [40, 262, 162, 236]
    vcard(d, 'prod', PB, '本轮产物', ['综述稿 · 图表', '合成方案 · 引用库'], 'products', None, art_h=112, ts=23, ls=16)
    d.flow('f_in', [(PB[0] + PB[2] + 6, 380), (P1[0] - 3, 380)], 'main')

    # P1：四条核验通道 2×2
    cw, chh = 200, 166
    x0, y0 = P1[0] + 16, P1[1] + 56
    pairs = [('c1', '执行者 ⇄ 评审者', '独立上下文 · 三视角', 'duo_review'), ('c2', '提案者 ⇄ 质询者', '合成方案内部质询', 'duo_attack'),
             ('c3', '候选图 ⇄ 审计', '图表两轮候选制', 'duo_audit'), ('c4', '稿件 ⇄ 程序检查', 'bib · tex · pdf 守卫', 'guard')]
    for k, (cid, tt, ln, art) in enumerate(pairs):
        pcard(d, cid, [x0 + (k % 2) * (cw + 14), y0 + (k // 2) * (chh + 12), cw, chh], tt, ln, art, p1)

    # P2：评审意见路由 → 级联失效
    rx, ry, rw, rh = P2[0] + 14, P2[1] + 54, 166, 200
    cx2 = rx + rw + 32
    vcard(d, 'route', [rx, ry, rw, rh], '意见路由', ['target → 责任阶段', '只重跑受影响链路'], 'route', p2, art_h=92, ts=21, ls=15)
    vcard(d, 'cas', [cx2, ry, rw, rh], '级联失效', ['产物指纹变更', '下游闸门 → 待复核'], 'cascade', p2, art_h=92, ts=21, ls=15)
    d.flow('f_rc', [(rx + rw + 6, ry + rh / 2), (cx2 - 6, ry + rh / 2)], 'main')
    d.flow('f_p1r', [(P1[0] + P1[2] + 4, ry + rh / 2), (rx - 7, ry + rh / 2)], 'main')

    # P3：check-done → 交付
    x3, w3 = P3[0] + 16, P3[2] - 32
    y_cd, y_out = P3[1] + 54, P3[1] + 54 + 72 + 34
    hcard(d, 'cd', [x3, y_cd, w3, 72], 'check-done', ['九道闸门全部入账 · 退出码 0'], 'checkdone', p3, art_w=54, ls=15)
    hcard(d, 'out', [x3, y_out, w3, 72], '交付', ['综述 PDF · 合成方案 → OpenLab'], 'plan', p3, art_w=54, ls=15)
    d.flow('f_out', [(x3 + w3 / 2, y_cd + 72 + 7), (x3 + w3 / 2, y_out - 7)], 'keep')
    gy = y_cd + 36
    d.flow('f_keep', [(P1[0] + P1[2] + 4, gy), (x3 - 7, gy)], 'keep')
    d.tag('t_keep', 900, gy, 'blocker = 0 且 major = 0', 'keep', size=16)

    # loopctl 拒绝入账 + 转人工裁决
    hcard(d, 'lc', [1116, 444, 380, 72], 'loopctl 拒绝入账', ['跳过阶段 · 无回执的 PASS → 写入被拒'], 'padlock', None, art_w=52, ls=15)
    hcard(d, 'human', [1116, 528, 380, 72], '转人工裁决', ['同一问题三轮未收敛 · 轮次用尽'], 'human', None, art_w=52, ls=15)
    for e in sc.els:
        if e['id'] == 'human':
            e['fill'], e['stroke'] = TONE['red']['fill'], TONE['red']['stroke']
    ex = cx2 + rw - 26
    d.flow('f_esc', [(ex, ry + rh + 6), (ex, 636), (1306, 636), (1306, 608)], 'escalate')
    d.tag('t_esc', 1190, 636, '未收敛', 'escalate', size=14)

    # 定向返修大回路：级联失效 → 本轮产物
    d.ubend('ret', (cx2 + rw / 2 - 20, ry + rh + 6), (PB[0] + PB[2] / 2, PB[1] + PB[3] + 8), 118, 'retry', depth2=182)
    d.tag('t_ret', 560, 662, '仅重跑责任阶段 · 至多 5 轮', 'retry')

    # 证据条：一个真实问题 + 四个轮次
    EY = 704
    EX = [40, EY, 440, 148]
    sc.shape('ex', EX, fill='#FFFFFF', stroke=TONE['red']['accent'], stroke_width=2, radius=10)
    sc.shape('ex_b', [EX[0] + 12, EY + 10, 266, 30], fill=TONE['red']['accent'], radius=15, container='ex')
    sc.text('ex_h', [EX[0] + 12, EY + 10, 266, 30], '实例 · I5 · blocker → 写作阶段', 15, bold=True, color='#FFFFFF', container='ex_b')
    slot(d, 'ex_art', [EX[0] + 12, EY + 50, 84, 88], 'condtable', 'ex')
    body = ['合成条件表逐字段核对：原文为固相合成，', '表中误标为熔体法 → 路由至写作阶段，', '回核实验段后重建条件表，第 2 轮关闭。']
    for k, ln in enumerate(body):
        sc.text(f'ex_l{k}', [EX[0] + 104, EY + 48 + k * 30, 328, 28], ln, 16, color=INK, align='left', container='ex', fit='shrink',
                min_font_size=13)
    rounds = [('生产阶段 · 闸门拦截', '4', '3 blocker · 1 major', 'red'), ('第 1 轮评审', '5', '1 blocker · 3 major · 1 minor', 'amber'),
              ('第 2 轮终审', '2', '仅 minor · 当轮关闭', 'green'), ('check-done · 未决问题', '0', '11/11 已关闭 · 退出码 0', 'green')]
    icons = ['padlock', 'route', 'ledger', 'pdf']
    for k, (hd, big, cap, tone) in enumerate(rounds):
        round_tile(d, f'rd{k}', [496 + k * 252, EY, 240, 148], hd, big, cap, tone, art=A(icons[k]))
    write(d, 'deck_loop_converge_r3')


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--art' in args:
        ART = args[args.index('--art') + 1]
        args = [a for a in args if a not in ('--art', ART)]
    which = args[0] if args else 'all'
    if which in ('bands', 'all'):
        parallel_bands()
    if which in ('ring', 'all'):
        parallel_ring()
    if which in ('converge', 'all'):
        converge()
