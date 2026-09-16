"""scene.json for fig03 round-2 F03 (并行双支，两级配色), measured from the 1536×1024 S5 raster.
Connector corrections as in round 1: the fork is fed only by 模型筛选的前驱体; the dashed feedback returns to 结构假设."""
import sys
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene import Scene, INK, GRAY
# colours sampled from the S5 raster (median of teal / ochre / dark-outline / light-outline pixels)
TEAL = '#0F7A88'; OCHRE = '#B4741A'; SLATE = '#3B4952'; TOKEN_LINE = '#B5BDC4'; TITLE = '#19232C'; SUB = '#2F3840'
# tinted regions (author: 参考 F01 的颜色，但更美观): cool-gray modules, warm-cream hypothesis card, light-teal lanes, cream question tags
MOD_FILL = '#F2F5F7'; HYP_FILL = '#FBF1DC'; HYP_EDGE = '#B4741A'; LANE_FILL = '#E1EFF1'; LANE_EDGE = '#1F6F78'; LANE_TITLE = '#145159'; TAG_FILL = '#FFF7E6'
JOB = '/root/lyf/goai/final_round/figstudio/jobs/fig03_r2'
sc = Scene(1536, 1024, source='pages/page_001/source.png', notes='图 3 本文的研究路线（super_teaser 第二轮 F03，两级配色 → super_img2ppt 重建；两处连线按论文修正）')
J = 'connector joints, visible in source'; HEAD = {'length': 18, 'width': 16}; LW = 5
OCH_DARK = '#8A5A0E'


def token(id, box, text, container, size=23, stroke=TOKEN_LINE, color=SUB, fill='#FFFFFF', group='token'):
    x, y, w, h = box
    sc.shape(id, box, fill=fill, stroke=stroke, stroke_width=1.5, radius=8, container=container)
    sc.text(id + '_t', [x + 6, y + 3, w - 12, h - 6], text, size, bold=False, color=color, container=id, font_group=group, fit='shrink', min_font_size=19)


def module(id, box, title, ty=14, fill=MOD_FILL, edge=SLATE, tcolor=TITLE):
    sc.shape(id, box, fill=fill, stroke=edge, stroke_width=3, radius=14)
    sc.text(id + '_t', [box[0] + 12, box[1] + ty, box[2] - 24, 44], title, 28, bold=True, color=tcolor, container=id, font_group='title')


# ---- left column
module('c1', [27, 38, 314, 245], '文献依据')
for i, t in enumerate(['Ba–Y–Si–O 谱系', 'Ba–Zn–Si–O 结构近邻', 'Y–Si–O 工艺参照']): token(f'c1_k{i}', [43, 97 + 58.5 * i, 283, 51], t, 'c1')
sc.line('c1_c2', [(182, 285), (182, 330)], stroke=TEAL, width=LW, arrow=True, head=HEAD)
module('c2', [28, 332, 312, 250], '结构假设', fill=HYP_FILL, edge=HYP_EDGE, tcolor='#6B4A0F')
for i, t in enumerate(['局部组成网格', 'Zn–Y–氧计量耦合', '竞争相与玻璃区']): token(f'c2_k{i}', [44, 394 + 59 * i, 280, 51], t, 'c2')
sc.line('c2_c3', [(182, 584), (182, 626)], stroke=TEAL, width=LW, arrow=True, head=HEAD)
module('c3', [29, 628, 311, 264], '模型筛选的前驱体')
token('c3_k0', [45, 695, 279, 53], 'BaCO3 + Y2O3 + SiO2', 'c3'); token('c3_k1', [45, 756, 279, 53], 'ZnO / MgO / Co3O4', 'c3')
token('c3_tag', [45, 819, 279, 54], '模型排序 ≠ 验证', 'c3', fill='#F6E7C6', stroke=OCHRE, color='#8A5A0E')
# ---- fork from the precursor module only
sc.line('fk_stub', [(342, 760), (400, 760)], stroke=TEAL, width=LW, overlap=['fk_v'], reason=J)
sc.line('fk_v', [(400, 451), (400, 760)], stroke=TEAL, width=LW, overlap=['fk_stub', 'fk_a', 'fk_b'], reason=J)
sc.line('fk_a', [(400, 451), (449, 451)], stroke=TEAL, width=LW, arrow=True, head=HEAD, overlap=['fk_v'], reason=J)
sc.line('fk_b', [(400, 703), (448, 703)], stroke=TEAL, width=LW, arrow=True, head=HEAD, overlap=['fk_v'], reason=J)
# ---- lanes (white panels, slate outline, bold title)
lanes = [('l1', [451, 378, 758, 147], '固相成相', [('分段煅烧', 472, 623), ('复磨', 658, 782), ('退火', 817, 940), ('批量相区与相纯度', 974, 1189)], 442),
         ('l2', [450, 632, 759, 142], '高温溶液长晶', [('助熔', 472, 598), ('保温', 632, 753), ('慢冷', 787, 905), ('单晶结构与液相选择性', 941, 1192)], 695)]
for lid, box, title, toks, ty in lanes:
    sc.shape(lid, box, fill=LANE_FILL, stroke=LANE_EDGE, stroke_width=3, radius=14)
    sc.text(lid + '_t', [box[0] + 20, box[1] + 8, 320, 44], title, 28, bold=True, color=LANE_TITLE, align='left', container=lid, font_group='title')
    for i, (t, x0, x1) in enumerate(toks):
        token(f'{lid}_k{i}', [x0, ty, x1 - x0, 61], t, lid, size=22, group='lanetoken')
        if i < 3:
            nx0 = toks[i + 1][1]; sc.line(f'{lid}_a{i}', [(x1 + 3, ty + 30), (nx0 - 3, ty + 30)], stroke=TEAL, width=4, arrow=True, head={'length': 12, 'width': 11}, container=lid)
# ---- merge into 结果反馈
sc.line('mg_a', [(1211, 451), (1236, 451)], stroke=TEAL, width=LW, overlap=['mg_v'], reason=J)
sc.line('mg_b', [(1211, 703), (1236, 703)], stroke=TEAL, width=LW, overlap=['mg_v'], reason=J)
sc.line('mg_v', [(1236, 451), (1236, 703)], stroke=TEAL, width=LW, overlap=['mg_a', 'mg_b', 'mg_out'], reason=J)
sc.line('mg_out', [(1236, 577), (1261, 577)], stroke=TEAL, width=LW, arrow=True, head={'length': 16, 'width': 16}, overlap=['mg_v'], reason=J)
module('c5', [1263, 361, 245, 370], '结果反馈')
for i, t in enumerate(['PXRD / Rietveld', 'SCXRD', 'EDS / EPMA / ICP', '高温相与冷却产物']): token(f'c5_k{i}', [1279, 434 + 71.5 * i, 214, 60], t, 'c5')
# ---- feedback (dashed teal) 结果反馈 → 结构假设 with label pill on the bottom run
sc.line('fb1', [(1386, 733), (1386, 960)], stroke=TEAL, width=4, dash=[16, 10], overlap=['fb2'], reason=J)
sc.line('fb2', [(1386, 960), (800, 960)], stroke=TEAL, width=4, dash=[16, 10], overlap=['fb1'], reason=J)
sc.shape('fb_p', [622, 936, 176, 48], fill='#E1EFF1', stroke=TEAL, stroke_width=2.5, radius=24)
sc.text('fb_pt', [630, 940, 160, 40], '更新组成与工艺', 22, bold=True, color=TEAL, container='fb_p', font_group='pill')
sc.line('fb3', [(620, 960), (14, 960)], stroke=TEAL, width=4, dash=[16, 10], overlap=['fb4'], reason=J)
sc.line('fb4', [(14, 960), (14, 457)], stroke=TEAL, width=4, dash=[16, 10], overlap=['fb3', 'fb5'], reason=J)
sc.line('fb5', [(14, 457), (26, 457)], stroke=TEAL, width=4, dash=[16, 10], arrow=True, overlap=['fb4'], reason=J)


# ---- question tags (only ochre elements)
def qtag(id, box, text, leader, dot, size=22, lh=None):
    sc.shape(id, box, fill=TAG_FILL, stroke=OCHRE, stroke_width=2.5, radius=10)
    sc.text(id + '_t', [box[0] + 10, box[1] + 5, box[2] - 20, box[3] - 10], text, size, bold=True, color=OCH_DARK, container=id, font_group='qtag', line_height=lh)
    sc.line(id + '_l', leader, stroke=OCHRE, width=2.5)
    sc.shape(id + '_d', [dot[0] - 6, dot[1] - 6, 12, 12], shape='ellipse', fill=OCHRE, stroke=None)


qtag('q1', [372, 281, 346, 50], 'Zn 是否进入并与氧计量耦合？', [(386, 332), (362, 340)], (352, 344))
qtag('q2', [639, 552, 335, 52], '稳定相区还是液相选择性？', [(806, 550), (806, 539)], (806, 532))
sc.line('q2_l2', [(806, 606), (806, 616)], stroke=OCHRE, width=2.5); sc.shape('q2_d2', [800, 618, 12, 12], shape='ellipse', fill=OCHRE, stroke=None)
qtag('q3', [1256, 197, 258, 100], '实际组成与结构信号\n如何对应？', [(1385, 299), (1414, 345)], (1420, 353), lh=1.5)
sc.write(JOB + '/scene.json'); print('wrote', len(sc.els), 'elements')
