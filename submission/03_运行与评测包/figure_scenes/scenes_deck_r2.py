"""答辩 PPT · 「多智能体并行回环」两页 · 第二轮（loop-engineering 风格，deckstyle 构件）。

同一份几何有两个用途：
  * blueprint 模式（ART=None）：带标签的线框，喂给生图模型当条件图（语义由它锁定：哪里并行、回环从哪出发到哪去）；
  * final 模式（ART=<素材目录>）：同一套原生对象 + 从生图结果裁出的角色/小插画（独立图片素材），即交付的可编辑页。

usage: python3 scenes_deck_r2.py [parallel|converge|all] [--art <dir>]
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from deckstyle import Deck, TONE, SZ, INK, MUTED, NAVY  # noqa: E402

_REPO = pathlib.Path(__file__).resolve().parents[3]
JOBS_DIR = pathlib.Path(os.environ.get('GOAI_FIGSTUDIO_JOBS', _REPO.parent / 'final_round/figstudio/jobs'))
ART = None          # set by --art: a directory of PNG assets named as in A() below


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


def vcard(d, cid, box, title, line, art, container, art_h=64, title_size=None, line2=None):
    """Card with the art on top (parallel lanes side by side): art, bold title, one grey line — all centred."""
    x, y, w, h = box
    d.card(cid, box, '', None, container=container)          # shell + shadow (empty title removed below)
    d.sc.els = [e for e in d.sc.els if e['id'] != cid + '_t']
    slot(d, cid + '_art', [x + (w - art_h) / 2, y + 8, art_h, art_h], art, container=cid)
    ts = title_size or SZ['title']
    th, lh = int(ts * 1.45), int(SZ['line'] * 1.5)
    ty = y + 8 + art_h + 2
    d.sc.text(cid + '_t', [x + 6, ty, w - 12, th], title, ts, bold=True, color=INK, container=cid, fit='shrink', min_font_size=ts - 5)
    d.sc.text(cid + '_s', [x + 6, ty + th, w - 12, lh], line, SZ['line'], color=MUTED, container=cid, fit='shrink', min_font_size=SZ['line'] - 4)
    if line2:
        d.sc.text(cid + '_s2', [x + 6, ty + th + lh - 2, w - 12, lh], line2, SZ['line'], color=MUTED, container=cid, fit='shrink',
                  min_font_size=SZ['line'] - 4)


def hcard(d, cid, box, title, line, art, container, art_w=60):
    """Card with the art on the left: art | bold title / grey line."""
    x, y, w, h = box
    d.card(cid, box, title, line, container=container)
    # shift the text right to make room for the slot
    for e in d.sc.els:
        if e['id'] in (cid + '_t', cid + '_s'):
            e['box'][0] += art_w + 6
            e['box'][2] -= art_w + 6
    slot(d, cid + '_art', [x + 10, y + (h - art_w) / 2, art_w, art_w], art, container=cid)


def stat_h(d, sid, box, big, unit, caption, tone):
    """Horizontal KPI tile: big number + unit on the left, caption under the unit."""
    t = TONE[tone]
    x, y, w, h = box
    d.sc.shape(sid, box, fill=t['fill'], stroke=t['stroke'], stroke_width=1.8, radius=14)
    bw = d.sc.measure(big, SZ['big'], True) + 10
    d.sc.text(sid + '_b', [x + 16, y + 4, bw, h - 8], big, SZ['big'], bold=True, color=t['accent'], align='left', container=sid)
    ux = x + 16 + bw + 6
    uh = int(SZ['title'] * 1.7)
    d.sc.text(sid + '_u', [ux, y + 8, w - (ux - x) - 10, uh], unit, SZ['title'], bold=True, color=INK, align='left', container=sid)
    d.sc.text(sid + '_c', [ux, y + 8 + uh, w - (ux - x) - 10, int(SZ['cap'] * 1.7)], caption, SZ['cap'], color=MUTED, align='left',
              container=sid)


def write(d, job):
    p = JOBS_DIR / job / 'scene.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    d.write(p)


# ================================================================================================ 1/2 并行分派
def parallel():
    d = Deck('多智能体并行回环 1/2 · 账本状态机与并行分派（round 2, side-by-side phase panels）')
    sc = d.sc
    # ---- 顶行：论断 + 编排器 + 图例
    d.headline('完成与否由程序判定，不由模型自报', None, x=44, y=120)
    sc.text('hl_n', [44, 166, 520, 40], '9 道闸门 · 29 批 / 40 个子任务', 26, bold=True, color=TONE['blue']['accent'], align='left')
    hcard(d, 'orc', [640, 122, 470, 84], '编排器', '建账本 · 分派 · 验闸门 · 路由返工', 'orchestrator', None, art_w=76)
    d.legend('lg', [1258, 118, 238, 100], [('main', '主流程'), ('dispatch', '并行分派'), ('retry', '返工回路'), ('write', '落账')], title=None)

    # ---- 三个相位
    PY, PH = 236, 392
    P1, P2, P3 = [250, PY, 400, PH], [670, PY, 400, PH], [1090, PY, 406, PH]
    p1 = d.panel('p1', P1, '1 · 立项取证', 'blue')
    p2 = d.panel('p2', P2, '2 · 并行生产', 'green')
    p3 = d.panel('p3', P3, '3 · 对抗审稿与交付', 'violet')
    r1, r2, r3 = PY + 56, PY + 56 + 66 + 32, PY + PH - 16 - 66      # row tops: single / parallel / single
    ph_ = r3 - 32 - r2                                                 # parallel row height

    # 研究主题（左）
    vcard(d, 'topic', [40, PY + 70, 190, 190], '研究主题', '一行输入', 'researcher', None, art_h=104)
    d.flow('f_topic', [(235, r1 + 33), (261, r1 + 33)], 'main')

    # P1：范围界定 → [文献检索 ∥ 风格库] → 引用核查
    x1, w1 = P1[0] + 16, P1[2] - 32
    hcard(d, 'scope', [x1, r1, w1, 66], '范围界定', '子主题与边界', 'scope', p1)
    cw = (w1 - 14) / 2
    vcard(d, 'lit', [x1, r2, cw, ph_], '文献检索', '≥3 路分片并发', 'search', p1, art_h=56)
    vcard(d, 'style', [x1 + cw + 14, r2, cw, ph_], '风格库', '30 篇范文', 'style', p1, art_h=56)
    hcard(d, 'ref', [x1, r3, w1, 66], '引用核查', '51/51 逐条核对', 'refguard', p1)
    for k, cx in enumerate((x1 + cw / 2, x1 + cw + 14 + cw / 2)):
        d.flow(f'f_p1a{k}', [(cx, r1 + 66 + 5), (cx, r2 - 6)], 'main')
        d.flow(f'f_p1b{k}', [(cx, r2 + ph_ + 6), (cx, r3 - 6)], 'main')

    # P1 → P2：引用核查 → 分类法（Z 形）
    x2, w2 = P2[0] + 16, P2[2] - 32
    gx = (P1[0] + P1[2] + P2[0]) / 2
    d.flow('f_12', [(x1 + w1 + 6, r3 + 33), (gx, r3 + 33), (gx, r1 + 33), (x2 - 7, r1 + 33)], 'main')

    # P2：分类法 → [图件 ∥ 写作 ∥ 实验构想]
    hcard(d, 'tax', [x2, r1, w2, 66], '分类法', '每叶 ≥3 篇', 'taxonomy', p2)
    tw = (w2 - 2 * 10) / 3
    lanes = [('fig', '图件', '可编辑三件套', 'figure'), ('write', '写作', '按章节并发', 'writer'), ('idea', '实验构想', '前驱体预测', 'idea')]
    band2 = PY + PH - 16 - r2
    ph2 = 176
    ly = r2 + (band2 - ph2) / 2
    for k, (cid, t, s, art) in enumerate(lanes):
        lx = x2 + k * (tw + 10)
        vcard(d, cid, [lx, ly, tw, ph2], t, s, art, p2, art_h=96, title_size=21)
        d.flow(f'f_p2a{k}', [(lx + tw / 2, r1 + 66 + 5), (lx + tw / 2, ly - 6)], 'main')

    # P2 → P3：三路并入 → 对抗审稿
    x3, w3 = P3[0] + 16, P3[2] - 32
    gx2 = (P2[0] + P2[2] + P3[0]) / 2
    ym = ly + ph2 / 2
    d.flow('f_23', [(x2 + w2 + 6, ym), (gx2, ym), (gx2, r1 + 40), (x3 - 7, r1 + 40)], 'main')

    # P3：对抗审稿 → 裁决 → PASS → 终稿交付
    hcard(d, 'review', [x3, r1, w3, 80], '对抗审稿', '独立上下文 · 三视角', 'reviewer', p3, art_w=72)
    vx, vy = x3 + 76, ly + ph2 / 2
    d.diamond('verdict', vx, vy, 146, 108, '裁决', container=p3)
    d.flow('f_rv', [(vx, r1 + 80 + 5), (vx, vy - 54 - 7)], 'main')
    d.tag('v_q', vx + 10, vy + 54 + 22, '0 blocker/major ?', 'main', bold=False, size=15)
    dx = x3 + 216
    vcard(d, 'deliver', [dx, vy - 84, x3 + w3 - dx, 168], '终稿交付', 'tex · pdf · bib', 'deliver', p3, art_h=70, title_size=21)
    d.flow('f_pass', [(vx + 73 + 6, vy), (dx - 7, vy)], 'keep')
    d.tag('t_pass', (vx + 73 + dx) / 2, vy - 30, 'PASS', 'keep', size=14)
    for e in sc.els:
        if e['id'] in ('t_pass', 't_pass_t'):
            e['allow_overlap_with'] = ['verdict']
            e['overlap_reason'] = 'the tag sits in the empty corner of the diamond bounding box'

    # 分派（蓝虚线）：编排器 → 三个相位
    oy = 122 + 84 + 4
    for k, px in enumerate((P1[0] + P1[2] / 2, P2[0] + P2[2] / 2, P3[0] + 84)):      # the third stays clear of the legend
        ox = 875 + (k - 1) * 120
        d.flow(f'f_d{k}', [(ox, oy), (ox, 213), (px, 213), (px, PY - 3)] if abs(px - ox) > 4 else [(ox, oy), (px, PY - 3)], 'dispatch')
    d.tag('t_disp', 590, 213, '分派', 'dispatch')

    # 返工回路（橙色弧）：裁决 → 回到生产阶段
    LY = PY + PH
    d.ubend('ret', (vx + 10, vy + 54 + 42), (P2[0] + 96, LY + 6), 74, 'retry', depth2=62)
    d.tag('t_ret', 985, LY + 33, 'issue 路由返工 · 最多 5 轮', 'retry')

    # 账本轨：九道闸门
    RY = 684
    sc.shape('rail', [40, RY, 1456, 80], fill='#FFFFFF', stroke=NAVY, stroke_width=2, radius=16)
    slot(d, 'rail_art', [52, RY + 10, 60, 60], 'ledger', 'rail')
    sc.text('rail_t', [120, RY + 10, 262, 34], '回环账本 ledger.json', 22, bold=True, color=INK, align='left', container='rail')
    sc.text('rail_s', [120, RY + 44, 250, 28], '九道闸门落账 · 文件锁 · 产物指纹', 15, color=MUTED, align='left', container='rail')
    gates = ['scope_confirmed', 'lit_coverage', 'style_bank_ready', 'ref_integrity', 'taxonomy_ready', 'figures_ready', 'draft_complete',
             'ideas_reviewed', 'review_pass']
    gw, gx0 = 117, 384
    g = TONE['green']
    for k, name in enumerate(gates):
        bx = gx0 + k * (gw + 6)
        sc.shape(f'gate{k}', [bx, RY + 8, gw, 64], fill=g['fill'], stroke=g['stroke'], stroke_width=1.5, radius=10, container='rail')
        sc.text(f'gate{k}_c', [bx, RY + 10, gw, 30], '✓', 22, bold=True, color=g['accent'], container=f'gate{k}')
        sc.text(f'gate{k}_t', [bx + 2, RY + 40, gw - 4, 26], name, 12, color=INK, container=f'gate{k}', fit='shrink', min_font_size=10)
    for k, px in enumerate((P1[0] + 60, P2[0] + 60, P3[0] + P3[2] - 50)):
        d.flow(f'f_w{k}', [(px, LY + 5), (px, RY - 6)], 'write')
    d.tag('t_w', P1[0] + 112, LY + 28, '落账', 'write', bold=False, size=15)

    # KPI 条
    KY = 772
    for k, (big, unit, cap, tone) in enumerate([('29', '批', '并行批次', 'blue'), ('40', '个子任务', '各写自己的分片', 'green'),
                                                ('≤4', '路并行', '单批并发上限', 'violet'), ('134', '次工具调用', 'MCP · 全程留痕', 'peach')]):
        stat_h(d, f'kpi{k}', [40 + k * 366, KY, 352, 84], big, unit, cap, tone)
    write(d, 'deck_loop_parallel_r2')


def pcard(d, cid, box, title, line, art, container, art_w=120, art_h=78, title_size=21):
    """Pair card: bold title and one grey line on top, a wide art slot underneath."""
    x, y, w, h = box
    d.card(cid, box, '', None, container=container)
    th, lh = int(title_size * 1.45), int(SZ['line'] * 1.5)
    d.sc.text(cid + '_t', [x + 8, y + 8, w - 16, th], title, title_size, bold=True, color=INK, container=cid, fit='shrink',
              min_font_size=title_size - 4)
    d.sc.text(cid + '_s', [x + 8, y + 8 + th, w - 16, lh], line, SZ['line'], color=MUTED, container=cid, fit='shrink',
              min_font_size=SZ['line'] - 4)
    ay = y + 8 + th + lh + 4
    slot(d, cid + '_art', [x + (w - art_w) / 2, ay, art_w, min(art_h, y + h - 8 - ay)], art, container=cid)


# ================================================================================================ 2/2 回环为什么收敛
def converge():
    d = Deck('多智能体并行回环 2/2 · 互搏通道与机械闸门（round 2, one big retry loop + round cards）')
    sc = d.sc
    d.headline('模型说了不算：检查不过即返工', None, x=44, y=122)
    sc.text('hl_n', [620, 120, 520, 50], '7 → 0 项 issue（两轮）', 34, bold=True, color=TONE['peach']['accent'], align='left')

    # ---- 三个相位
    P1 = [236, 182, 446, 410]
    P2 = [698, 322, 400, 270]
    P3 = [1116, 182, 380, 246]
    p1 = d.panel('p1', P1, '1 · 互搏挑错', 'blue')
    p2 = d.panel('p2', P2, '2 · 路由返工', 'green')
    p3 = d.panel('p3', P3, '3 · 机械放行', 'violet')

    # 本轮产物（左）
    PB = [40, 262, 176, 236]
    vcard(d, 'prod', PB, '本轮产物', '稿件 · 图件', 'products', None, art_h=112, line2='方案 · 引用库')
    d.flow('f_in', [(PB[0] + PB[2] + 6, 380), (P1[0] - 3, 380)], 'main')

    # P1：四条互搏通道 2×2
    cw, chh = 200, 166
    x0, y0 = P1[0] + 16, P1[1] + 56
    pairs = [('c1', '执行者 ⇄ 审稿人', '独立上下文 · 三视角', 'duo_review'), ('c2', '提案者 ⇄ 攻击者', '实验构想内部对抗', 'duo_attack'),
             ('c3', '候选 ⇄ 审计', '图件两轮候选制', 'duo_audit'), ('c4', '稿件 ⇄ 机械守卫', 'bib · tex · pdf 守卫', 'guard')]
    for k, (cid, tt, ln, art) in enumerate(pairs):
        pcard(d, cid, [x0 + (k % 2) * (cw + 14), y0 + (k // 2) * (chh + 12), cw, chh], tt, ln, art, p1, art_w=160, art_h=92)

    # P2：issue 路由表 → 级联失效
    rx, ry, rw, rh = P2[0] + 14, P2[1] + 54, 176, 200
    cx2 = rx + rw + 20
    vcard(d, 'route', [rx, ry, rw, rh], 'issue 路由表', 'target → 责任阶段', 'route', p2, art_h=96, title_size=21)
    vcard(d, 'cas', [cx2, ry, rw, rh], '级联失效', '指纹变 → PENDING', 'cascade', p2, art_h=96, title_size=21)
    d.flow('f_rc', [(rx + rw + 6, ry + rh / 2), (cx2 - 6, ry + rh / 2)], 'main')
    d.flow('f_p1r', [(P1[0] + P1[2] + 4, ry + rh / 2), (rx - 7, ry + rh / 2)], 'main')

    # P3：check-done → 交付（上下两张）
    x3, w3 = P3[0] + 16, P3[2] - 32
    y_cd, y_out = P3[1] + 54, P3[1] + 54 + 72 + 34
    hcard(d, 'cd', [x3, y_cd, w3, 72], 'check-done', '九道闸门全过 · 退出码 0', 'checkdone', p3, art_w=54)
    hcard(d, 'out', [x3, y_out, w3, 72], '交付', '23 页 PDF · 51/51 引用', 'pdf', p3, art_w=54)
    d.flow('f_out', [(x3 + w3 / 2, y_cd + 72 + 7), (x3 + w3 / 2, y_out - 7)], 'keep')
    # 机械放行：P1 → check-done（绿色，走在 P2 上方）
    gy = y_cd + 36
    d.flow('f_keep', [(P1[0] + P1[2] + 4, gy), (x3 - 7, gy)], 'keep')
    d.tag('t_keep', 900, gy, '0 blocker / major', 'keep')

    # loopctl 拒绝写入 + 升级人类（P3 下方）
    hcard(d, 'lc', [1116, 444, 380, 72], 'loopctl 拒绝写入', '跳阶段 · 单轮审稿 → 写不进去', 'padlock', None, art_w=52)
    hcard(d, 'human', [1116, 528, 380, 72], '升级人类', '三轮未收敛 / 轮次用尽', 'human', None, art_w=52)
    for e in sc.els:
        if e['id'] == 'human':
            e['fill'], e['stroke'] = TONE['red']['fill'], TONE['red']['stroke']
    ex = cx2 + rw - 26
    d.flow('f_esc', [(ex, ry + rh + 6), (ex, 636), (1306, 636), (1306, 608)], 'escalate')
    d.tag('t_esc', 1190, 636, '不收敛', 'escalate', size=14)

    # 返工大回环：级联失效 → 本轮产物
    d.ubend('ret', (cx2 + rw / 2 - 20, ry + rh + 6), (PB[0] + PB[2] / 2, PB[1] + PB[3] + 8), 118, 'retry', depth2=182)
    d.tag('t_ret', 560, 662, '只重跑责任阶段 · 最多 5 轮', 'retry')

    # 证据条：四轮
    EY = 704
    d.legend('lg', [40, EY, 236, 148], [('main', '主流程'), ('retry', '返工回路'), ('keep', '机械放行'), ('escalate', '升级人类')])
    rounds = [('生产阶段', '4', '闸门拦下 · 3 blocker · 1 major', 'red'), ('第 1 轮审稿', '7', '1 blocker · 3 major · 3 minor', 'amber'),
              ('第 2 轮审稿', '0', '0 · 0 · 0 → review_pass', 'green'), ('check-done', '= 0', '23 页 PDF · 51/51 引用', 'green')]
    icons = ['padlock', 'route', 'ledger', 'pdf']
    for k, (hd, big, cap, tone) in enumerate(rounds):
        d.stat(f'rd{k}', [296 + k * 302, EY, 290, 148], big, cap, tone, head=hd, art=A(icons[k]))
    write(d, 'deck_loop_converge_r2')


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--art' in args:
        ART = args[args.index('--art') + 1]
        args = [a for a in args if a not in ('--art', ART)]
    which = args[0] if args else 'all'
    if which in ('parallel', 'all'):
        parallel()
    if which in ('converge', 'all'):
        converge()
