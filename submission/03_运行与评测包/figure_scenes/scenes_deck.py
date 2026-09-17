"""答辩 PPT · 两页「多智能体并行回环」框架图（原生重建：1536×864 画布 = 一整页 16:9，标题栏留给模板）。

  deck_loop_parallel  账本驱动的状态机与并行分派 —— S1 最高分版式 SC4「账本为轴」
  deck_loop_converge  四条互搏通道与机械闸门收敛 —— S1 最高分版式 SC2「单主干闭环」

字号按「幻灯片 pt × 角色」给出（分组 16 / 标题 14 / 步骤号 18 / 正文 12 / 标签 11），
与模板正文用的 11–14 pt 同档；只有分组名、卡片标题加粗。内容区避开模板的标题栏（y < 122 px）。
super_img2ppt 把 1536 px 画布映射到 960 pt 页宽，所以这一页的形状可以 1:1 复制进模板
（tools/deck_merge.py）。契约与证据锚点见 final_round/figstudio/figure-studio-runs/deck_loop_*/outputs/S0、S1。

usage: python3 scenes_deck.py [parallel|converge|all]
"""
import os
import pathlib
import sys

_REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / 'skills' / 'goai-figure-studio'))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
JOBS_DIR = pathlib.Path(os.environ.get('GOAI_FIGSTUDIO_JOBS', _REPO.parent / 'final_round/figstudio/jobs'))

from lib import Figure, FAM, ITEM, CONN, W_STEP  # noqa: E402
from scenes_r6 import W, box_h, text  # noqa: E402

SLIDE_W_PT = 960                       # img2ppt 页宽；1536 px 画布 → 0.625 pt/px
TYPE_PT_SLIDE = {'group': 16.0, 'title': 14.0, 'number': 18.0, 'body': 12.0, 'label': 11.0}
SMALL = {'length': 9, 'width': 8}      # 卡内短箭头
TEAL, SLATE, AMBER, MUTE = 'exp', 'lit', 'note', 'mute'


def new_fig(notes):
    return Figure(1536, 864, notes=f'{notes} [slide 16:9; content below the template title bar]',
                  print_width_pt=SLIDE_W_PT, crop_px=0, type_scale=TYPE_PT_SLIDE)


def zone_top(f, zy):
    return zy + 10 + int(f.T['group'] * 1.6) + 4 + 10


def card_head(f, cid, box, title, *, fam, glyph=None, sub=None, container=None, dashed=False, gw=32, pad=12, bar=6,
              sub_size=None):
    """卡片 + 顶部一行：图元、加粗标题、（放得下就同行的）常规副标题。返回 (内容左 x, 内容起始 y, 内容宽)。"""
    x, y, w, h = box
    T = f.T
    f.card(cid, box, fam=fam, dashed=dashed, container=container, bar=(0 if dashed else bar))
    left = x + (0 if dashed else bar) + pad
    tx, ty = left, y + 9
    th = box_h(T['title'], 1)
    if glyph:
        f.m.draw(glyph, cid + '_g', [tx, ty, gw, gw], container=cid)
        tx += gw + 8
    row_h = max(gw if glyph else 0, th)
    tw = W(title, T['title'], True) + 4
    text(f, cid + '_t', [tx, ty + (row_h - th) / 2, tw, th], title, T['title'], bold=True, color=FAM[fam]['text'],
         container=cid)
    inner_w = x + w - pad - left
    if sub:
        ss = sub_size or T['body']
        sh = box_h(ss, 1)
        sw = W(sub, ss) + 4
        if tx + tw + 12 + sw <= x + w - pad:
            text(f, cid + '_s', [tx + tw + 12, ty + (row_h - sh) / 2, sw, sh], sub, ss, bold=False, container=cid)
            return left, ty + row_h + 8, inner_w
        text(f, cid + '_s', [left, ty + row_h + 2, inner_w, sh], sub, ss, bold=False, container=cid)
        return left, ty + row_h + 2 + sh + 6, inner_w
    return left, ty + row_h + 8, inner_w


def pair(f, cid, x, y, a, b, container, h=None):
    """互搏通道的机理：一对角色 token + 一个双向短箭头。返回右端 x。"""
    T = f.T
    h = h or box_h(T['body'], 1) + 4
    wa, wb, gap = W(a, T['body']) + 20, W(b, T['body']) + 20, 38
    f.token(cid + '_a', [x, y, wa, h], a, container=container)
    f.token(cid + '_b', [x + wa + gap, y, wb, h], b, container=container)
    x0, x1, ym = x + wa + 5, x + wa + gap - 5, y + h / 2
    f.sc.line(cid + '_l', [(x0, ym), (x1, ym)], stroke=CONN, width=W_STEP, arrow=True, head=SMALL, container=container)
    f.sc.line(cid + '_r', [(x1, ym), (x0, ym)], stroke=CONN, width=W_STEP, arrow=True, head=SMALL, container=container)
    return x + wa + gap + wb


def down_arrow(f, cid, x, y0, y1, container=None):
    f.sc.line(cid, [(x, y0), (x, y1)], stroke=CONN, width=W_STEP, arrow=True, head=SMALL, container=container)


def both_ways(f, cid, pts, label=None, label_at=None):
    """双向连线：整条正向画一次；反向只补起点处 20 px 带箭头的一段（整条反画会和正向大面积重叠）。"""
    f.conn(cid + '_f', pts, label=label, label_at=label_at)
    (x0, y0), (x1, y1) = pts[0], pts[1]
    d = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    k = min(1.0, 20 / d)
    f.conn(cid + '_b', [(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k), (x0, y0)])


def write(f, zones, job):
    f.finish(zones)
    p = JOBS_DIR / job / 'scene.json'
    f.write(str(p))
    print('wrote', p, f'({len(f.sc.els)} elements)')


# ================================================================================================ 图一 · 并行分派
def parallel():
    f = new_fig('多智能体并行回环（一）账本驱动的状态机与并行分派 —— SC4 账本为轴')
    T = f.T
    # ---- 三段：控制层带（上）/ 认知层主干（中）/ 回环账本（下）
    ZC = (38, 122, 1460, 172)
    ZA = (38, 312, 1460, 352)
    LG = (60, 682, 1438, 170)
    zc = f.zone('zC', list(ZC), '控制层', TEAL)
    za = f.zone('zA', list(ZA), '认知层', SLATE)

    # ---- 控制层：编排器 / 并行 runner / 统计
    cy0 = zone_top(f, ZC[1])
    ch = 100
    ox, ow = 60, 470
    lx, y1, iw = card_head(f, 'orc', [ox, cy0, ow, ch], '编排器', fam=TEAL, glyph='flow', sub='goai-orchestrator', container=zc)
    f.chain('orc_c', [lx, y1, iw, box_h(T['body'], 1) + 4], ['建账本', '分派', '验闸门', '路由返工'], container='orc', gap=16)
    rx, rw = 560, 560
    lx, y1, iw = card_head(f, 'run', [rx, cy0, rw, ch], '并行 runner', fam=TEAL, glyph='layers', sub='parallel_run.sh', container=zc)
    f.row('run_c', [lx, y1, iw, box_h(T['body'], 1) + 4], ['tasks.tsv', '子进程', '各写自己的分片文件', '汇合'], container='run',
          gap=16, widths=[126, 86, 200, 66])
    f.pill('stat', 1312, cy0 + ch / 2, '正式运行：29 批 · 40 个子任务 · 单批 ≤4 路 · 134 次 MCP 调用', fam=MUTE, max_w=350, padx=30)

    # ---- 认知层：六列主干，两个分叉
    CW, GAP = 206, 36
    cols = [60 + k * (CW + GAP) for k in range(6)]
    top = zone_top(f, ZA[1])
    CH, SG = 85, 10
    CH1 = 124                       # 文献检索卡：多一行三路分片 token
    stack_h = 3 * CH + 2 * SG
    y_single = top + (stack_h - CH) / 2
    y_two = [top + (stack_h - (CH1 + CH + SG)) / 2, top + (stack_h - (CH1 + CH + SG)) / 2 + CH1 + SG]
    y_three = [top + k * (CH + SG) for k in range(3)]
    mid = y_single + CH / 2
    stages = [
        ('s0', 0, y_single, '范围界定', 'goai-orchestrator', 'boundary'),
        ('s1', 1, y_two[0], '文献检索', 'goai-lit-search', 'docs'),
        ('s2', 1, y_two[1], '风格库', 'goai-style-bank', 'doc'),
        ('s3', 2, y_single, '引用核查', 'goai-ref-guard', 'trace_check'),
        ('s4', 3, y_single, '分类法', 'goai-survey-writer', 'cubes'),
        ('s5', 4, y_three[0], '图件', 'goai-figure-studio', 'curve'),
        ('s6', 4, y_three[1], '写作', 'goai-survey-writer', 'doc'),
        ('s7', 4, y_three[2], '实验构想', 'goai-idea-forge', 'flask'),
        ('s8', 5, y_single, '对抗审稿', 'goai-reviewer', 'doc_q'),
    ]
    for cid, c, y, title, skill, g in stages:
        h = CH1 if cid == 's1' else CH
        lx, y1, iw = card_head(f, cid, [cols[c], y, CW, h], title, fam=SLATE, glyph=g, sub=skill, container=za,
                               sub_size=15)
        if cid == 's1':   # 三路分片 token（无箭头）：并发证据 —— 「子主题 [1][2][3]」
            th = box_h(T['label'], 1) + 4
            lw = W('子主题', T['label']) + 4
            text(f, 's1_kl', [lx, y1 - 2, lw, th], '子主题', T['label'], bold=False, container='s1')
            for k in range(3):
                f.token(f's1_k{k}', [lx + lw + 6 + k * 38, y1 - 2, 32, th], str(k + 1), size=T['label'], container='s1')

    def right(c):
        return cols[c] + CW

    # 分叉 1：范围界定 → {文献检索, 风格库}
    bx = right(0) + 14
    f.conn('f1t', [(right(0) + 5, mid), (bx, mid)], arrow=False)
    cy2 = [y_two[0] + CH1 / 2, y_two[1] + CH / 2]
    f.conn('f1b', [(bx, cy2[0]), (bx, cy2[1])], arrow=False)
    for k in range(2):
        f.conn(f'f1a{k}', [(bx, cy2[k]), (cols[1] - 5, cy2[k])])
    # 汇合 1 → 引用核查 → 分类法
    mx = right(1) + 14
    for k in range(2):
        f.conn(f'm1a{k}', [(right(1) + 5, cy2[k]), (mx, cy2[k])], arrow=False)
    f.conn('m1b', [(mx, cy2[0]), (mx, cy2[1])], arrow=False)
    f.conn('m1t', [(mx, mid), (cols[2] - 5, mid)])
    f.conn('e23', [(right(2) + 5, mid), (cols[3] - 5, mid)])
    # 分叉 2：分类法 → {图件, 写作, 实验构想}
    bx2 = right(3) + 14
    f.conn('f2t', [(right(3) + 5, mid), (bx2, mid)], arrow=False)
    f.conn('f2b', [(bx2, y_three[0] + CH / 2), (bx2, y_three[2] + CH / 2)], arrow=False)
    for k in range(3):
        f.conn(f'f2a{k}', [(bx2, y_three[k] + CH / 2), (cols[4] - 5, y_three[k] + CH / 2)])
    # 汇合 2 → 对抗审稿
    mx2 = right(4) + 14
    for k in range(3):
        f.conn(f'm2a{k}', [(right(4) + 5, y_three[k] + CH / 2), (mx2, y_three[k] + CH / 2)], arrow=False)
    f.conn('m2b', [(mx2, y_three[0] + CH / 2), (mx2, y_three[2] + CH / 2)], arrow=False)
    f.conn('m2t', [(mx2, mid), (cols[5] - 5, mid)])
    # 并发证据标签：坐在分叉列上方的分组标题行里，同时是 runner 两条线的终点
    hy = ZA[1] + 41
    f.pill('ev1', bx + 40, hy, '≥3 路分片 · 各记一条 done', fam=TEAL)
    f.pill('ev2', bx2, hy, '按图 · 按章节 · 按目标 并发', fam=TEAL)
    f.conn('r1', [(rx + 60, cy0 + ch + 5), (rx + 60, 303), (bx + 40, 303), (bx + 40, hy - 20)])
    f.conn('r2', [(rx + rw - 60, cy0 + ch + 5), (rx + rw - 60, 303), (bx2, 303), (bx2, hy - 20)])
    # 编排器 → 范围界定（分派）
    f.conn('dsp', [(ox + 140, cy0 + ch + 5), (ox + 140, y_single - 5)], label='分派', label_at=(ox + 140, 398))
    # 对抗审稿 ⇢ 主干（issue 路由返工，回到第二个分叉点之前）
    rc = cols[5] + CW / 2
    f.conn('ret', [(rc, y_single - 5), (rc, 372), (cols[3] + CW / 2, 372), (cols[3] + CW / 2, y_single - 5)],
           dashed=True, label='issue 路由返工', label_at=(1332, 372))

    # ---- 回环账本：宽卡；闸门药丸与阶段列对齐；主干在这里收尾
    lx, y1, iw = card_head(f, 'led', list(LG), '回环账本', fam=TEAL, glyph='grid', sub='ledger.json')
    recs = ['闸门 gates', '问题 issues', '日志 log']
    rh = box_h(T['body'], 1) + 2
    x = 420
    for k, r in enumerate(recs):
        w_ = W(r, T['body']) + 20
        f.m.draw('checkbox', f'led_c{k}', [x, LG[1] + 14, 22, 22], container='led')
        f.token(f'led_r{k}', [x + 26, LG[1] + 12, w_, rh], r, container='led')
        x += 26 + w_ + 18
    gates = {0: ['scope_confirmed'], 1: ['lit_coverage', 'style_bank_ready'], 2: ['ref_integrity'], 3: ['taxonomy_ready'],
             4: ['figures_ready', 'draft_complete', 'ideas_reviewed']}
    ph = int(T['label'] * 1.5) + 8
    py = LG[1] + 56 + ph / 2
    rows_y = [py + k * (ph + 4) for k in range(3)]
    for c, names in gates.items():
        cx = cols[c] + CW / 2
        n = len(names)
        ys = rows_y[:n] if n == 3 else ([rows_y[1]] if n == 1 else [rows_y[0] + (ph + 4) / 2, rows_y[1] + (ph + 4) / 2])
        for name, yy in zip(names, ys):
            f.pill(f'g_{name}', cx + (8 if c == 0 else 0), yy, name, fam=TEAL, pady=4, container='led')
    # 主干终点：对抗审稿 → review_pass 落账 → check-done → 终稿交付
    rc5 = cols[5] + CW / 2
    f.conn('e_end', [(rc5, y_single + CH + 5), (rc5, LG[1] - 5)])
    ends = ['review_pass', 'check-done 退出码 0', '终稿交付']
    ey = [LG[1] + 26, LG[1] + 26 + ph + 26, LG[1] + 26 + 2 * (ph + 26)]
    for k, (t, yy) in enumerate(zip(ends, ey)):
        if k < 2:
            f.pill(f'end{k}', rc5, yy, t, fam=TEAL, pady=4, container='led')
        else:
            w_ = W(t, T['body'], True) + 26
            f.token('end2', [rc5 - w_ / 2, yy - ph / 2, w_, ph], t, container='led', fam=SLATE, strong=True)
        if k:
            down_arrow(f, f'end_a{k}', rc5, ey[k - 1] + ph / 2 + 5, yy - ph / 2 - 5, container='led')
    # 编排器 ⇄ 账本：沿左页边下去，loopctl 读写 · 文件锁
    both_ways(f, 'lk', [(ox - 5, cy0 + 50), (38, cy0 + 50), (38, LG[1] + 60), (LG[0] - 5, LG[1] + 60)],
              label='loopctl 读写 · 文件锁', label_at=(150, 600))
    write(f, [zc, za], 'deck_loop_parallel')


# ================================================================================================ 图二 · 收敛
def converge():
    f = new_fig('多智能体并行回环（二）四条互搏通道与机械闸门收敛 —— SC2 单主干闭环')
    T = f.T
    bh = box_h(T['body'], 1)          # 19 px 正文的单行框 32 px；token 再加 2
    TK = bh + 2
    HEAD_H = 9 + 32 + 8               # 卡片顶行（图元 32）

    # ---- 互搏通道区（中）：四张卡纵向堆叠，卡内一对角色 token + 双向短箭头 + 判据
    ZX, ZW = 278, 470
    CX, CW = 294, 438
    chans = [
        ('c1', '执行者', '审稿人', 'doc_q', ['独立上下文 · 三视角 · 两轮起']),
        ('c2', '提案者', '攻击者', 'flask', ['实验构想内部对抗 · 引用二审']),
        ('c3', '候选', '审计', 'curve', ['图件两轮候选制 · issue 台账']),
        ('c4', '稿件', '机械守卫', 'checklist', ['bib_guard · tex_guard · pdf_guard', '语言守卫 · 检查不过即返工，模型说了不算']),
    ]
    heads = [HEAD_H + len(crit) * (bh + 2) + 10 for *_, crit in chans]
    SG = 10
    stack = sum(heads) + SG * 3
    zh = 65 + stack + 12
    zt = int(122 + (718 - zh) / 2)
    zx = f.zone('zX', [ZX, zt, ZW, zh], '互搏通道', SLATE)
    y = zone_top(f, zt)
    centres = []
    for (cid, a, b, g, crit), h in zip(chans, heads):
        f.card(cid, [CX, y, CW, h], fam=SLATE, container=zx, bar=6)
        f.m.draw(g, cid + '_g', [CX + 18, y + 9, 32, 32], container=cid)
        pair(f, cid + '_p', CX + 18 + 32 + 8, y + 9 + (32 - TK) / 2, a, b, cid, h=TK)
        for k, c in enumerate(crit):
            text(f, f'{cid}_k{k}', [CX + 18, y + HEAD_H + k * (bh + 2), CW - 30, bh], c, T['body'], bold=False,
                 container=cid)
        centres.append(y + h / 2)
        y += h + SG
    mainline = zt + 65 + stack / 2

    # ---- 本轮产物（左，主干起点）
    PX, PW = 38, 210
    items = ['稿件', '图件', '实验方案', '引用库']
    ph_ = HEAD_H + 4 * TK + 3 * 6 + 10
    py = int(mainline - ph_ / 2)
    lx, y1, iw = card_head(f, 'prod', [PX, py, PW, ph_], '本轮产物', fam=SLATE, glyph='docs')
    f.vstack('prod_v', [lx, y1, iw, 4 * TK + 3 * 6], items, container='prod', gap=6)
    bx = CX - 26
    f.conn('p_t', [(PX + PW + 5, mainline), (bx, mainline)], arrow=False)
    f.conn('p_b', [(bx, centres[0]), (bx, centres[-1])], arrow=False)
    for k, cy in enumerate(centres):
        f.conn(f'p_a{k}', [(bx, cy), (CX - 5, cy)])

    # ---- 正式运行统计（左上，灰虚线卡）
    st_h = HEAD_H + 3 * TK + 2 * 6 + 10
    lx, y1, iw = card_head(f, 'stat', [PX, 150, 224, st_h], '正式运行', fam=MUTE, glyph='docs', dashed=True)
    f.vstack('stat_v', [lx, y1, iw, 3 * TK + 2 * 6], ['2 轮收敛', '首轮 7 项，第二轮 0', '11 个 issue 全关闭'], container='stat', gap=6)

    # ---- 路由与返工（中右）
    RX, RW = 790, 330
    rows = ['覆盖缺口 → 文献检索', '引用可疑 → 引用核查', '分类不 MECE → 分类法', '图文不符 → 图件', '无证据断言 → 写作', '未落到前驱体 → 实验构想']
    RT_Y = 150
    lx, y1, iw = card_head(f, 'rt', [RX, RT_Y, RW, 10], 'issue 路由表', fam=TEAL, glyph='grid', sub='issue 带 target · severity')
    rt_h = (y1 - RT_Y) + 6 * TK + 5 * 4 + 10
    f.sc.els[[e['id'] for e in f.sc.els].index('rt')]['box'][3] = rt_h
    f.vstack('rt_v', [lx, y1, iw, 6 * TK + 5 * 4], rows, container='rt', gap=4)
    cas = ['上游产物变更', '指纹重算', '下游闸门置回 PENDING', '复核']
    cs_h = HEAD_H + 4 * TK + 3 * 14 + 10
    CS_Y = RT_Y + rt_h + 30
    lx, y1, iw = card_head(f, 'cas', [RX, CS_Y, RW, cs_h], '级联失效', fam=TEAL, glyph='cycle')
    f.vchain('cas_v', [lx + 30, y1, iw - 60, 4 * TK + 3 * 14], cas, container='cas', gap=14)
    # 通道 → 路由表（四路并入一束）
    mx = CX + CW + 18
    for k, cy in enumerate(centres):
        f.conn(f'q_a{k}', [(CX + CW + 5, cy), (mx, cy)], arrow=False)
    f.conn('q_b', [(mx, centres[0]), (mx, centres[-1])], arrow=False)
    f.conn('q_t', [(mx, centres[0]), (RX - 5, centres[0])])
    # 路由表 → 级联失效 ⇢ 本轮产物（虚线闭环）
    LOOP_Y = 758
    f.conn('r_c', [(RX + RW / 2, RT_Y + rt_h + 5), (RX + RW / 2, CS_Y - 5)])
    f.conn('loop', [(RX + RW / 2, CS_Y + cs_h + 5), (RX + RW / 2, LOOP_Y), (150, LOOP_Y), (150, py + ph_ + 5)], dashed=True,
           label='只重跑责任阶段 · 下一轮', label_at=(540, LOOP_Y))

    # ---- 机械放行（右）
    MX, MW = 1144, 354
    rej = ['跳阶段', '缺并发证据', '单轮审稿', '无回执', '非 TeX 编译的 PDF']
    lc_h = HEAD_H + 5 * 30 + 4 * 4 + 8
    cd_steps = ['九个闸门全部落账', '无未关闭的 blocker/major', '回执指向真实审稿记录', '指纹未变']
    cd_h = HEAD_H + 5 * TK + 3 * 14 + 18 + 10
    zm_h = 65 + lc_h + 30 + cd_h + 12
    ZM_Y = 140
    zm = f.zone('zM', [MX, ZM_Y, MW, zm_h], '机械放行', TEAL)
    y = zone_top(f, ZM_Y)
    lx, y1, iw = card_head(f, 'lc', [MX + 16, y, MW - 32, lc_h], 'loopctl 拒绝写入', fam=TEAL, glyph='boundary', container=zm)
    f.check_rows('lc_r', [lx, y1, iw, 5 * 30 + 4 * 4], rej, container='lc', gap=4)
    y += lc_h + 30
    CD_Y = y
    lx, y1, iw = card_head(f, 'cd', [MX + 16, y, MW - 32, cd_h], 'check-done', fam=TEAL, glyph='tick_circle', container=zm)
    vh = 4 * TK + 3 * 14
    f.vchain('cd_v', [lx + 6, y1, iw - 12, vh], cd_steps, container='cd', gap=14)
    oy = y1 + vh + 18
    ow = W('退出码 0 → 交付', T['body'], True) + 30
    f.token('cd_o', [lx + (iw - ow) / 2, oy, ow, TK], '退出码 0 → 交付', container='cd', fam=TEAL, strong=True)
    down_arrow(f, 'cd_oa', lx + iw / 2, oy - 18 + 3, oy - 3, container='cd')
    # 路由表 → check-done（无 issue 时）：从路由表右侧出，拐到 check-done 左侧
    ry = RT_Y + rt_h - 40
    f.conn('r_d', [(RX + RW + 5, ry), (1130, ry), (1130, CD_Y + 60), (MX + 16 - 5, CD_Y + 60)])

    # ---- 终止旁路（底部横条，回环之外）
    TB = (38, 780, 1460, 60)
    lx, y1, iw = card_head(f, 'tb', list(TB), '终止旁路', fam=MUTE, glyph='target', dashed=True)
    stops = ['轮次上限 → 带遗留清单交付', '同一问题三轮未收敛 → 升级人类', '连续两次无新增日志 → 空转，换策略']
    x = lx + W('终止旁路', T['title'], True) + 32 + 8 + 24
    for k, t in enumerate(stops):
        w_ = W(t, T['body']) + 22
        f.token(f'tb_t{k}', [x, TB[1] + (TB[3] - TK) / 2, w_, TK], t, container='tb')
        x += w_ + 16
    f.conn('to_tb', [(RX + RW - 60, CS_Y + cs_h + 5), (RX + RW - 60, TB[1] - 5)])
    write(f, [zx, zm], 'deck_loop_converge')


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('parallel', 'all'):
        parallel()
    if which in ('converge', 'all'):
        converge()
