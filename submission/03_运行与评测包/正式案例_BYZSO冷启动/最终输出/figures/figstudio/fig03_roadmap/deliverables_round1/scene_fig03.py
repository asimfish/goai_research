"""scene.json for fig03 F01 (并行双支为核心), measured from the 1536×1024 S5 raster.
Two connector corrections against the raster (paper-faithful, see S3 record): the fork is fed only by 模型筛选的前驱体 (the raster also
drew a stub from 结构假设), and the dashed feedback 更新组成与工艺 returns to 结构假设 (the raster returned it to the precursor module)."""
import sys
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene import Scene, INK, TEAL, OCHRE, PANEL, PANEL_LINE, OCHRE_TINT, TEAL_TINT
JOB = '/root/lyf/goai/final_round/figstudio/jobs/fig03'
sc = Scene(1536, 1024, source='pages/page_001/source.png', notes='图 3 本文的研究路线（super_teaser S5 F01 → super_img2ppt 重建；两处连线按论文修正）')
J = 'connector joints, visible in source'; HEAD = {'length': 18, 'width': 16}; LW = 5
OCH_DARK = '#7A5A1C'
def token(id, box, text, container, size=24, stroke='#B5BDC4', color=INK, fill='#FFFFFF', group='token'):
    x, y, w, h = box
    sc.shape(id, box, fill=fill, stroke=stroke, stroke_width=2, radius=8, container=container)
    sc.text(id + '_t', [x + 6, y + 3, w - 12, h - 6], text, size, bold=True, color=color, container=id, font_group=group, fit='shrink', min_font_size=20)
# ---- left column
sc.shape('c1', [27, 39, 311, 243], fill=PANEL, stroke=PANEL_LINE, stroke_width=2.5, radius=14)
sc.text('c1_t', [40, 48, 285, 44], '文献依据', 28, bold=True, container='c1', font_group='title')
for i, t in enumerate(['Ba–Y–Si–O 谱系', 'Ba–Zn–Si–O 结构近邻', 'Y–Si–O 工艺参照']): token(f'c1_k{i}', [43, 97 + 59 * i, 282, 51], t, 'c1')
sc.line('c1_c2', [(182, 284), (182, 332)], stroke=TEAL, width=LW, arrow=True, head=HEAD)
sc.shape('c2', [30, 336, 308, 244], fill=OCHRE_TINT, stroke=OCHRE, stroke_width=2.5, radius=14)
sc.text('c2_t', [43, 345, 282, 44], '结构假设', 28, bold=True, color=OCH_DARK, container='c2', font_group='title')
for i, t in enumerate(['局部组成网格', 'Zn–Y–氧计量耦合', '竞争相与玻璃区']): token(f'c2_k{i}', [45, 395 + 58.5 * i, 278, 52], t, 'c2')
sc.line('c2_c3', [(182, 582), (182, 631)], stroke=TEAL, width=LW, arrow=True, head=HEAD)
sc.shape('c3', [31, 635, 305, 257], fill=PANEL, stroke=PANEL_LINE, stroke_width=2.5, radius=14)
sc.text('c3_t', [40, 646, 287, 44], '模型筛选的前驱体', 28, bold=True, container='c3', font_group='title')
token('c3_k0', [45, 698, 278, 52], 'BaCO3 + Y2O3 + SiO2', 'c3'); token('c3_k1', [45, 757, 278, 53], 'ZnO / MgO / Co3O4', 'c3')
token('c3_tag', [45, 822, 278, 53], '模型排序 ≠ 验证', 'c3', stroke=OCHRE, color=OCH_DARK, fill='#F6E7C6')
# ---- fork from the precursor module only
sc.line('fk_stub', [(338, 763), (400, 763)], stroke=TEAL, width=LW, overlap=['fk_v'], reason=J)
sc.line('fk_v', [(400, 459), (400, 763)], stroke=TEAL, width=LW, overlap=['fk_stub', 'fk_a', 'fk_b'], reason=J)
sc.line('fk_a', [(400, 459), (454, 459)], stroke=TEAL, width=LW, arrow=True, head=HEAD, overlap=['fk_v'], reason=J)
sc.line('fk_b', [(400, 706), (454, 706)], stroke=TEAL, width=LW, arrow=True, head=HEAD, overlap=['fk_v'], reason=J)
# ---- lanes
lanes = [('l1', [456, 394, 756, 130], '固相成相', [('分段煅烧', 475, 624), ('复磨', 652, 780), ('退火', 820, 940), ('批量相区与相纯度', 974, 1196)], 449),
         ('l2', [456, 640, 756, 132], '高温溶液长晶', [('助熔', 475, 596), ('保温', 630, 756), ('慢冷', 784, 906), ('单晶结构与液相选择性', 940, 1196)], 696)]
for lid, box, title, toks, ty in lanes:
    sc.shape(lid, box, fill=TEAL_TINT, stroke=TEAL, stroke_width=2.5, radius=14)
    sc.text(lid + '_t', [box[0] + 20, box[1] + 6, 300, 44], title, 28, bold=True, color='#155459', align='left', container=lid, font_group='title')
    for i, (t, x0, x1) in enumerate(toks):
        token(f'{lid}_k{i}', [x0, ty, x1 - x0, 59], t, lid, stroke='#9AA5AD', size=23, group='lanetoken')
        if i < 3:
            nx0 = toks[i + 1][1]; sc.line(f'{lid}_a{i}', [(x1 + 3, ty + 29), (nx0 - 3, ty + 29)], stroke=TEAL, width=4, arrow=True, head={'length': 12, 'width': 11}, container=lid)
# ---- merge into 结果反馈
sc.line('mg_a', [(1214, 459), (1240, 459)], stroke=TEAL, width=LW, overlap=['mg_v'], reason=J)
sc.line('mg_b', [(1214, 706), (1240, 706)], stroke=TEAL, width=LW, overlap=['mg_v'], reason=J)
sc.line('mg_v', [(1240, 459), (1240, 706)], stroke=TEAL, width=LW, overlap=['mg_a', 'mg_b', 'mg_out'], reason=J)
sc.line('mg_out', [(1240, 550), (1265, 550)], stroke=TEAL, width=LW, arrow=True, head={'length': 16, 'width': 16}, overlap=['mg_v'], reason=J)
sc.shape('c5', [1267, 368, 239, 365], fill=PANEL, stroke=PANEL_LINE, stroke_width=2.5, radius=14)
sc.text('c5_t', [1280, 380, 213, 44], '结果反馈', 28, bold=True, container='c5', font_group='title')
for i, t in enumerate(['PXRD / Rietveld', 'SCXRD', 'EDS / EPMA / ICP', '高温相与冷却产物']): token(f'c5_k{i}', [1283, 441 + 72 * i, 213, 60], t, 'c5')
# ---- feedback (dashed teal) 结果反馈 → 结构假设, labelled
sc.line('fb1', [(1386, 735), (1386, 960)], stroke=TEAL, width=4, dash=[16, 10], overlap=['fb2'], reason=J)
sc.line('fb2', [(1386, 960), (800, 960)], stroke=TEAL, width=4, dash=[16, 10], overlap=['fb1'], reason=J)
sc.shape('fb_p', [622, 936, 176, 48], fill='#FFFFFF', stroke=TEAL, stroke_width=2, radius=24)
sc.text('fb_pt', [630, 940, 160, 40], '更新组成与工艺', 22, bold=True, color=TEAL, container='fb_p', font_group='pill')
sc.line('fb3', [(620, 960), (14, 960)], stroke=TEAL, width=4, dash=[16, 10], overlap=['fb4'], reason=J)
sc.line('fb4', [(14, 960), (14, 457)], stroke=TEAL, width=4, dash=[16, 10], overlap=['fb3', 'fb5'], reason=J)
sc.line('fb5', [(14, 457), (28, 457)], stroke=TEAL, width=4, dash=[16, 10], arrow=True, overlap=['fb4'], reason=J)
# ---- question tags (ochre outline, thin leaders with dots)
def qtag(id, box, text, leader, dot, size=22, lh=None):
    sc.shape(id, box, fill='#FBF3E3', stroke=OCHRE, stroke_width=2.5, radius=10)
    sc.text(id + '_t', [box[0] + 10, box[1] + 5, box[2] - 20, box[3] - 10], text, size, bold=True, color=OCH_DARK, container=id, font_group='qtag', line_height=lh)
    sc.line(id + '_l', leader, stroke=OCHRE, width=2.5)
    sc.shape(id + '_d', [dot[0] - 6, dot[1] - 6, 12, 12], shape='ellipse', fill=OCHRE, stroke=None)
qtag('q1', [372, 289, 334, 50], 'Zn 是否进入并与氧计量耦合？', [(386, 340), (362, 347)], (352, 350))
qtag('q2', [651, 548, 318, 52], '稳定相区还是液相选择性？', [(810, 546), (810, 540)], (810, 532))
sc.line('q2_l2', [(810, 602), (810, 614)], stroke=OCHRE, width=2.5); sc.shape('q2_d2', [804, 622, 12, 12], shape='ellipse', fill=OCHRE, stroke=None)
qtag('q3', [1267, 214, 245, 100], '实际组成与结构信号\n如何对应？', [(1400, 316), (1431, 351)], (1440, 360), lh=1.5)
sc.write(JOB + '/scene.json'); print('wrote', len(sc.els), 'elements')
