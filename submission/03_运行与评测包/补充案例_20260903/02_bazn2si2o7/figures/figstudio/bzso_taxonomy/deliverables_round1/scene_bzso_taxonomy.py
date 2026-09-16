"""scene.json for bzso_taxonomy F01 (左根树), measured from the 1536×1024 S5 raster."""
import sys
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene import Scene, INK, TEAL, OCHRE, PANEL, PANEL_LINE, GRAY, OCHRE_TINT
JOB = '/root/lyf/goai/final_round/figstudio/jobs/bzso_taxonomy'
sc = Scene(1536, 1024, source='pages/page_001/source.png', notes='BaZn2Si2O7 合成与相控制分类框架（super_teaser S5 F01 → super_img2ppt 重建）')
J = 'connector joints, visible in source'; HEAD = {'length': 18, 'width': 15}
# hub
sc.shape('hub', [70, 274, 250, 460], fill=TEAL, stroke=None, radius=18)
sc.text('hub_t', [74, 436, 242, 130], 'BaZn2Si2O7\n目标相', 34, bold=True, color='#FFFFFF', container='hub', line_height=1.5)
# trunk and branches
ys = [84, 220, 355, 490, 626, 762]
sc.line('stub', [(322, 504), (364, 504)], stroke=TEAL, width=5, overlap=['trunk'], reason=J)
sc.line('trunk', [(364, 84), (364, 762)], stroke=TEAL, width=5, overlap=['stub'] + [f'br{i}' for i in range(6)] + ['br6'], reason=J)
cards = [('结构与多晶型', '相变 · 配位', '结构'), ('合成路线', '固相 · 溶胶—凝胶', '制备'), ('组成与热处理', 'Ba/Sr · Zn 位', '变量'), ('玻璃析晶', '成核 · 生长', '晶化'), ('近邻体系', 'Ba2ZnSi2O7 等', '近邻'), ('证据边界', '直接 / 近邻 / 推断', '判读')]
tops = [23, 158, 294, 429, 565, 701]
for i, ((t, s, lab), top, cy) in enumerate(zip(cards, tops, ys)):
    sc.line(f'br{i}', [(364, cy), (474, cy)], stroke=TEAL, width=5, overlap=['trunk'], reason=J)
    sc.line(f'br{i}b', [(602, cy), (772, cy)], stroke=TEAL, width=5, arrow=True, head=HEAD)
    sc.shape(f'pill{i}', [476, cy - 22, 124, 44], fill='#FFFFFF', stroke=TEAL, stroke_width=2.5, radius=22)
    sc.text(f'pill{i}_t', [482, cy - 19, 112, 38], lab, 24, bold=True, color=TEAL, container=f'pill{i}', font_group='pill')
    sc.shape(f'card{i}', [774, top, 697, 123], fill=PANEL, stroke=PANEL_LINE, stroke_width=2.5, radius=14)
    sc.text(f'card{i}_t', [810, top + 14, 640, 58], t, 36, bold=True, align='left', container=f'card{i}', font_group='title')
    sc.text(f'card{i}_s', [810, top + 72, 640, 40], s, 27, color='#4A5158', align='left', container=f'card{i}', font_group='sub')
# dashed analog branch + card
sc.line('br6a', [(364, 767), (364, 903)], stroke=OCHRE, width=4, dash=[16, 10], overlap=['trunk', 'br6'], reason=J)
sc.line('br6', [(364, 903), (474, 903)], stroke=OCHRE, width=4, dash=[16, 10], overlap=['br6a'], reason=J)
sc.line('br6b', [(602, 903), (772, 903)], stroke=OCHRE, width=4, dash=[16, 10], arrow=True)
sc.shape('pill6', [476, 881, 124, 44], fill='#FFFFFF', stroke=OCHRE, stroke_width=2.5, radius=22)
sc.text('pill6_t', [482, 884, 112, 38], '类比', 24, bold=True, color=OCHRE, container='pill6', font_group='pill')
sc.shape('card6', [774, 842, 697, 123], fill=PANEL, stroke=OCHRE, stroke_width=2.5, radius=14, dash=[16, 10])
sc.text('card6_t', [810, 856, 640, 58], 'Ba5Y12Zn[O(SiO4)]8', 36, bold=True, align='left', container='card6', font_group='title')
sc.text('card6_s', [810, 914, 640, 40], '未见直接报道', 27, color='#4A5158', align='left', container='card6', font_group='sub')
sc.write(JOB + '/scene.json'); print('wrote', len(sc.els), 'elements')
