"""Round-5 reconstructions of the candidates the author picked.

Picks (2026-09-14):
  图 1 证据适用范围  F02 嵌套容器      三栏纵向分组
  图 2 条件比较与表征 F01 分层横带      三条横带
  图 3 研究路线      F02 嵌套容器      紧凑四段分区
  路线图            F02 嵌套容器      3+3 编号卡
  分类框架          F02 双栏对照      左右双栏 + 中心枢纽

Repairs applied here that the generated raster did not do (each was already an S4 must-fix or an S3 high finding):
  * 分类框架: every branch arrow now points hub → branch. The raster drew the four 实验方法 arrows into the hub,
    which reads as "four kinds of evidence add up to the target phase" — the reverse of the classification.
  * 分类框架: 判读 was drawn double-headed; the line style budget allows one meaning per style, so it is one-way.
  * 图 2: 产物表征 band returns to the teal family. Amber is reserved for caveats and unverified items.
  * 图 3: the fork after 前驱体筛选 feeds BOTH lanes. The raster only fed 高温溶液法晶体生长, dropping the edge the
    paper states for 固相反应.
  * 路线图: 06 keeps one glyph (checklist); the raster merged a balance and a checklist into one mark.

usage: python3 scenes_r5.py [fig01|fig02|fig03|roadmap|taxonomy|all]
"""
import pathlib
import sys
# --- paths -------------------------------------------------------------------
# The design system lives in the repo; the job dir is where scene.json files are written and where
# super_img2ppt reads them from. Override with GOAI_FIGSTUDIO_JOBS when building somewhere else.
import os
_REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / 'skills' / 'goai-figure-studio'))
JOBS_DIR = pathlib.Path(os.environ.get('GOAI_FIGSTUDIO_JOBS', _REPO.parent / 'final_round/figstudio/jobs'))

from lib import Figure as R5, FAM

BASE = str(JOBS_DIR)


# ====================================================================== 图 1
def fig01():
    r = R5(1536, 1024, notes='图 1 不同文献对目标化合物合成研究的适用范围（第五轮 F02 嵌套容器 → super_img2ppt 重建）')
    zL = r.zone('zL', [110, 50, 462, 806], '文献证据', 'lit')
    zE = r.zone('zE', [592, 50, 440, 806], '实验方法', 'exp')
    zQ = r.zone('zQ', [1052, 50, 458, 806], '可回答的问题', 'note')

    ev = [('a1', 150, '目标化合物直接报道', 'doc'), ('a2', 262, '同类 Ba–Y 四方硅酸盐', 'polyhedron'),
          ('a3', 374, '结构相关化合物', 'lattice'), ('a4', 486, '工艺参照研究', 'crucible')]
    for cid, y, title, g in ev:
        r.card_stack(cid, [130, y, 420, 102], title, [], fam='lit', glyph=g, container=zL,
                     title_size=24, glyph_w=40, pad=16)
    r.card_stack('a5', [130, 700, 420, 112], '非相关资料', [], fam='mute', glyph='doc_struck', dashed=True,
                 container=zL, title_size=24, glyph_w=40, pad=18)
    r.axis('ax', 62, 150, 812, label='与目标相的距离', container=None, label_x=42)

    r.card('led', [620, 150, 382, 540], fam='exp', container=zE)
    r.m.draw('grid', 'led_g', [648, 178, 44, 44], container='led')
    r.sc.text('led_t', [704, 178, 282, 44], '相同实验项目下比较', 25, bold=True, color=FAM['exp']['text'],
              align='left', container='led', font_group='r5title')
    r.check_rows('ledr', [648, 248, 330, 414],
                 ['原料与配比', '热历史', '气氛', '容器与助熔剂', '冷却与分离', '产物表征'], container='led', size=20, gap=10)

    q = [('u1', 150, '直接条件复现', 'flask'), ('u2', 282, '系列内相图与结构比较', 'polyhedron'),
         ('u3', 414, '方法与变量结构', 'balance')]
    for cid, y, title, g in q:
        r.card_stack(cid, [1076, y, 410, 112], title, [], fam='note', glyph=g, container=zQ,
                     title_size=24, glyph_w=40, pad=18)
    r.pill('cav', 1281, 600, '近邻条件 ≠ 已验证配方', size=19, fam='note')
    r.card_stack('u4', [1076, 700, 410, 112], '划定研究范围', [], fam='mute', glyph='target', dashed=True,
                 container=zQ, title_size=24, glyph_w=40, pad=18)

    for cid, y, *_ in ev:
        r.conn('br_' + cid, [(554, y + 51), (584, y + 51)], arrow=False)
    r.conn('brv', [(584, 201), (584, 537)], arrow=False)
    r.conn('brh', [(584, 369), (616, 369)])
    r.conn('fan0', [(1006, 420), (1030, 420)], arrow=False)
    r.conn('fanv', [(1030, 206), (1030, 470)], arrow=False)
    for k, y in enumerate((206, 338, 470)):
        r.conn(f'fan{k + 1}', [(1030, y), (1072, y)])
    r.conn('ex', [(554, 756), (1072, 756)], dashed=True, label='排除', label_at=(813, 756), label_size=19)

    r.finish([zL, zE, zQ]); r.write(f'{BASE}/fig01_r5/scene.json'); return r


# ====================================================================== 图 2
def fig02():
    r = R5(1536, 1024, notes='图 2 不同合成方法的条件比较与产物表征（第五轮 F01 分层横带 → super_img2ppt 重建）')
    zT = r.zone('zT', [26, 28, 1484, 402], '实验方法', 'exp')
    zM = r.zone('zM', [26, 452, 1484, 246], '文献证据', 'lit')
    zB = r.zone('zB', [26, 728, 1484, 268], '产物表征', 'exp')
    r.pill('leg', 1392, 60, '虚线＝工艺参照', size=18, fam='mute')

    routes = [('r1', '外加助熔', 'beaker', ['溶解', '保温', '缓冷分离'], False),
              ('r2', '自熔/熔体', 'bowl', ['均化', '自发成核', '受控冷却'], False),
              ('r3', '固相陶瓷', 'pellet', ['混合压片', '煅烧复磨', '烧结'], False),
              ('r4', '机械化学预活化', 'mill', ['高能研磨', '活化', '后续相形成'], False),
              ('r5', 'Czochralski', 'pull', ['预烧熔化', '籽晶提拉', '退火'], True)]
    X0, W, G = 50, 278, 10
    for k, (cid, title, g, steps, dashed) in enumerate(routes):
        x = X0 + k * (W + G)
        r.card(cid, [x, 100, W, 300], fam=('mute' if dashed else 'exp'), dashed=dashed, container=zT, bar=7)
        r.sc.text(cid + '_t', [x + 16, 114, W - 32, 40], title, 24, bold=True,
                  color=FAM['mute' if dashed else 'exp']['text'], align='center', container=cid,
                  font_group='r5title', fit='shrink', min_font_size=19)
        r.m.draw(g, cid + '_g', [x + W / 2 - 29, 160, 58, 58], container=cid)
        r.vchain(f'{cid}c', [x + 18, 234, W - 36, 150], steps, container=cid, size=19, gap=18)

    r.card('led', [50, 514, 1436, 170], fam='lit', container=zM, bar=7)
    r.sc.text('led_t', [78, 530, 300, 42], '统一实验记录', 25, bold=True, color=FAM['lit']['text'],
              align='left', container='led', font_group='r5title')
    cols = [('配比与原料', 'doc'), ('温度—时间与气氛', 'thermo'), ('坩埚与助熔剂', 'crucible'), ('冷却、生长与分离', 'droplet')]
    for k, (lab, g) in enumerate(cols):
        cx = 78 + k * 306
        r.col_item(f'cl{k}', [cx, 576, 286, 96], lab, g, container='led', size=20, glyph_w=46)
        if k:
            r.sc.line(f'cl{k}_s', [(cx - 12, 572), (cx - 12, 668)], stroke='#E3E8ED', width=1.2, container='led')
    r.pill('cav', 1378, 604, '抽取框架 ≠ 实验配方', size=19, fam='note')

    checks = [('k1', '单晶结构', 'lattice', '结构归属与位点占据'), ('k2', 'PXRD / Rietveld', 'trace', '块体相纯与杂相'),
              ('k3', '成分与污染', 'dots', '名义—局域—体平均'), ('k4', '高温稳定性', 'thermo', '原位高温 ≠ 冷却回收')]
    CW = 350
    for k, (cid, title, g, sub) in enumerate(checks):
        x = 50 + k * (CW + 12)
        r.card(cid, [x, 790, CW, 186], fam='exp', container=zB, bar=7)
        r.sc.text(cid + '_t', [x + 16, 804, CW - 32, 40], title, 24, bold=True, color=FAM['exp']['text'],
                  align='center', container=cid, font_group='r5title', fit='shrink', min_font_size=19)
        r.m.draw(g, cid + '_g', [x + CW / 2 - 27, 850, 54, 54], container=cid)
        r.token(cid + '_s', [x + 18, 918, CW - 36, 44], sub, size=19, container=cid)

    for k, lab in enumerate(['配比 · 温度', '熔体 · 容器', '混合 · 煅烧', '研磨 · 污染', '籽晶 · 退火']):
        x = X0 + k * (W + G) + W / 2
        # the label sits in the gutter after its connector, so the short stub and its arrow head stay visible
        # labels ride the gutter after their connector; the last one has no gutter, so it sits under its arrow
        at = (x, 470) if k == len(routes) - 1 else (x + 144, 426)
        r.conn(f'd{k}', [(x, 404), (x, 448)], label=lab, label_at=at, label_size=18, dashed=(k == 4))
    for k, lab in enumerate(['结构', '相组成', '成分', '高温']):
        x = 50 + k * (CW + 12) + CW / 2
        at = (x, 748) if k == len(checks) - 1 else (x + 181, 713)
        r.conn(f'c{k}', [(x, 702), (x, 724)], label=lab, label_at=at, label_size=18)

    r.finish([zT, zM, zB]); r.write(f'{BASE}/fig02_r5/scene.json'); return r


# ====================================================================== 图 3
def fig03():
    r = R5(1536, 1024, notes='图 3 本文的研究路线（第五轮 F02 嵌套容器 → super_img2ppt 重建；分叉同时进入两条通道）')
    zL = r.zone('zL', [26, 26, 1484, 362], '文献证据', 'lit')
    zE = r.zone('zE', [26, 418, 1484, 232], '实验方法', 'exp')
    zR = r.zone('zR', [26, 680, 1484, 176], '结果反馈', 'lit')
    zQ = r.zone('zQ', [26, 880, 1484, 136], '判断提醒', 'note')

    ev = [('c1', 60, '文献依据', 'docs', ['Ba–Y–Si–O 系列', 'Ba–Zn–Si–O 结构相关化合物', 'Y–Si–O 工艺参照']),
          ('c2', 560, '结构假设', 'polyhedron', ['局部组成网格', 'Zn–Y–氧计量耦合', '竞争相与玻璃区']),
          ('c3', 1060, '前驱体筛选', 'funnel', ['BaCO3 + Y2O3 + SiO2', 'ZnO / MgO / Co3O4', '模型排序的候选'])]
    for cid, x, title, g, items in ev:
        r.card_stack(cid, [x, 92, 450, 262], title, items, fam='lit', glyph=g, container=zL,
                     title_size=25, item_size=19, glyph_w=42, pad=16, gap=9)
    r.pill('cav', 1290, 372, '模型排序 ≠ 验证', size=18, fam='note')

    lanes = [('l1', 60, '固相反应', 'furnace', ['分段煅烧', '复磨', '退火'], '块体相区与相纯度'),
             ('l2', 820, '高温溶液法晶体生长', 'flask', ['助熔', '保温', '缓冷'], '单晶结构与液相选择性')]
    for cid, x, title, g, steps, out in lanes:
        r.card(cid, [x, 480, 620, 142], fam='exp', container=zE, bar=8)
        r.m.draw(g, cid + '_g', [x + 22, 496, 40, 40], container=cid)
        r.sc.text(cid + '_t', [x + 76, 494, 260, 44], title, 25, bold=True, color=FAM['exp']['text'],
                  align='left', container=cid, font_group='r5title')
        r.row(f'{cid}r', [x + 22, 552, 330, 50], steps, container=cid, size=19, gap=20)
        r.token(f'{cid}_o', [x + 364, 552, 234, 50], out, size=19, container=cid, fam='exp', strong=True)

    r.card('c5', [380, 706, 780, 130], fam='lit', container=zR, bar=8)
    r.m.draw('trace_check', 'c5_g', [404, 722, 40, 40], container='c5')
    r.sc.text('c5_t', [456, 720, 240, 44], '表征手段', 25, bold=True, color=FAM['lit']['text'],
              align='left', container='c5', font_group='r5title')
    r.row('c5r', [404, 776, 736, 44], ['PXRD / Rietveld', 'SCXRD', 'EDS / EPMA / ICP', '高温相与冷却产物'],
          container='c5', size=18, gap=12, arrow=False)

    for qid, x, text in [('q1', 60, 'Zn 是否进入并与氧计量耦合？'), ('q2', 560, '稳定相区还是液相选择性？'),
                         ('q3', 1060, '实际组成与结构信号如何对应？')]:
        r.card(qid, [x, 936, 450, 66], fam='note', container=zQ, bar=8)
        r.sc.text(qid + '_t', [x + 20, 940, 410, 58], text, 21, bold=True, color=FAM['note']['text'], align='center',
                  container=qid, font_group='r5q', fit='shrink', min_font_size=17)

    r.conn('e1', [(514, 223), (556, 223)])
    r.conn('e2', [(1014, 223), (1056, 223)])
    # the fork after 前驱体筛选 feeds both lanes (the raster fed only one)
    r.conn('fk0', [(1285, 358), (1285, 444)], arrow=False)
    r.conn('fkh', [(370, 444), (1285, 444)], arrow=False)
    r.conn('fk1', [(370, 444), (370, 476)])
    r.conn('fk2', [(1130, 444), (1130, 476)])
    r.conn('mg1', [(370, 626), (370, 662)], arrow=False)
    r.conn('mg2', [(1130, 626), (1130, 662)], arrow=False)
    r.conn('mgh', [(370, 662), (1130, 662)], arrow=False)
    r.conn('mg3', [(770, 662), (770, 702)])
    r.conn('fb', [(1164, 771), (1475, 771), (1475, 403), (785, 403), (785, 358)], dashed=True,
           label='更新组成与工艺', label_at=(880, 403), label_size=19)

    r.finish([zL, zE, zR, zQ]); r.write(f'{BASE}/fig03_r5/scene.json'); return r


# ====================================================================== 路线图
def roadmap():
    r = R5(1536, 900, notes='BaZn2Si2O7 本文的行文路线图（第五轮 F02 → super_img2ppt 重建；3+3 两行，印刷可读优先）')
    zA = r.zone('zA', [30, 40, 1476, 382], '文献证据', 'lit')
    zB = r.zone('zB', [30, 470, 1476, 390], '实验方法', 'exp')
    cards = [('n1', 70, 112, '01', '结构基础', '低温与高温多晶型', 'lit', 'polyhedron', zA, None),
             ('n2', 570, 112, '02', '合成路线', '固相 · 溶胶—凝胶', 'lit', 'crucible', zA, None),
             ('n3', 1070, 112, '03', '相控制', '组成 · 热处理', 'lit', 'layers', zA, None),
             ('n4', 70, 542, '04', '近邻体系', 'Ba–Sr–Zn–Si', 'exp', 'cubes', zB, None),
             ('n5', 570, 542, '05', '类似物判据', 'Ba5Y12Zn[O(SiO4)]8', 'note', 'balance', zB, '#FFFAF0'),
             ('n6', 1070, 542, '06', '实验优先级', '相图 · 结构 · 热力学', 'exp', 'checklist', zB, None)]
    for cid, x, y, num, title, point, fam, g, zone, fill in cards:
        r.card_step(cid, [x, y, 420, 278], num, title, point, fam=fam, glyph=g, container=zone,
                    num_size=36, title_size=27, point_size=20, glyph_w=92, pad=18, bar=10, fill=fill)

    # the label rides the band's top margin, not the card gap: an English pill is twice the Chinese width and
    # would otherwise sit on both neighbouring cards
    for k, lab, y, ly in ((0, '结构约束', 251, 78), (1, '条件窗口', 251, 78),
                          (3, '比较边界', 681, 508), (4, '缺口驱动', 681, 508)):
        x0 = cards[k][1] + 420
        x1 = cards[k + 1][1]
        r.conn(f'e{k}', [(x0 + 8, y), (x1 - 8, y)], label=lab, label_at=((x0 + x1) / 2, ly), label_size=18)
    # 03 -> 04 wraps to the second row; the label rides the horizontal run in the band gap
    # the wrap descends right of the band label so a long English label cannot be crossed by it
    r.conn('e2', [(1280, 394), (1280, 446), (360, 446), (360, 538)], label='可迁移变量', label_at=(820, 446),
           label_size=18)

    r.finish([zA, zB]); r.write(f'{BASE}/bzso_roadmap_r5/scene.json'); return r


# ====================================================================== 分类框架
def taxonomy():
    r = R5(1536, 1024, notes='BaZn2Si2O7 合成与相控制的分类框架（第五轮 F02 双栏对照 → super_img2ppt 重建；'
                             '箭头一律由枢纽指向分支，全图只有一段虚线）')
    zE = r.zone('zE', [36, 40, 620, 944], '实验方法', 'exp', label_pos='top')
    zL = r.zone('zL', [880, 40, 616, 944], '文献证据', 'lit', label_pos='top')

    r.card('hub', [658, 380, 220, 280], fam='exp', bar=0)
    r.m.draw('lattice', 'hub_g', [718, 420, 100, 100], container='hub')
    r.sc.text('hub_t', [666, 542, 204, 48], 'BaZn2Si2O7', 27, bold=True, color=FAM['exp']['text'],
              align='center', container='hub', font_group='r5hub', fit='shrink', min_font_size=22)
    r.sc.text('hub_s', [678, 594, 180, 36], '目标相', 20, bold=True, color=FAM['exp']['text'], align='center',
              container='hub', font_group='r5hubsub')

    exp = [('e1', 120, '结构与多晶型', '相变 · 配位', 'lattice', '结构'),
           ('e2', 330, '合成路线', '固相 · 溶胶—凝胶', 'flask', '制备'),
           ('e3', 540, '组成与热处理', 'Ba/Sr · Zn 位', 'thermo', '变量'),
           ('e4', 750, '玻璃析晶', '成核 · 生长', 'crystals', '晶化')]
    for cid, y, title, sub, g, lab in exp:
        r.card_stack(cid, [66, y, 460, 176], title, [], fam='exp', glyph=g, container=zE,
                     title_size=25, item_size=20, glyph_w=54, pad=20, sub=sub)

    lit = [('l1', 150, '近邻体系', 'Ba2ZnSi2O7 等', 'cubes', '近邻', False),
           ('l2', 430, '证据边界', '直接 / 近邻 / 推断', 'boundary', '判读', False),
           ('l3', 710, 'Ba5Y12Zn[O(SiO4)]8', '未见直接报道', 'cubes', '类比', True)]
    for cid, y, title, sub, g, lab, dashed in lit:
        r.card_stack(cid, [980, y, 490, 200], title, [], fam=('note' if dashed else 'lit'), glyph=g,
                     dashed=dashed, container=zL, title_size=24, item_size=20, glyph_w=54, pad=20, sub=sub,
                     fill=('#FFFAF0' if dashed else None))

    # every branch arrow leaves the hub — the raster drew the left four pointing into it
    r.conn('sl', [(654, 512), (600, 512)], arrow=False)
    r.conn('slv', [(600, 208), (600, 838)], arrow=False)
    for cid, y, _t, _s, _g, lab in exp:
        r.conn(f's_{cid}', [(600, y + 88), (530, y + 88)], label=lab, label_at=(565, y + 52), label_size=18)
    r.conn('sr', [(882, 512), (900, 512)], arrow=False)
    r.conn('srv', [(900, 250), (900, 810)], arrow=False)
    for cid, y, _t, _s, _g, lab, dashed in lit:
        r.conn(f'v_{cid}', [(900, y + 100), (976, y + 100)], dashed=dashed, label=lab, label_at=(938, y + 64),
               label_size=18, label_fam=('note' if dashed else None),
               color=(FAM['note']['edge'] if dashed else '#4B5563'))

    r.finish([zE, zL]); r.write(f'{BASE}/bzso_taxonomy_r5/scene.json'); return r


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    fns = {'fig01': fig01, 'fig02': fig02, 'fig03': fig03, 'roadmap': roadmap, 'taxonomy': taxonomy}
    for name, fn in fns.items():
        if which in ('all', name):
            r = fn(); print(f'{name}: {len(r.sc.els)} elements')
