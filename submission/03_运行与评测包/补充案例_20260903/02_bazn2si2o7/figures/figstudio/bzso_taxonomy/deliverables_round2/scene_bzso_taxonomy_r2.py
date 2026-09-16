"""scene.json for bzso_taxonomy round-2 F04 (辐射式，内外两层), measured from the 1536×1024 S5 raster."""
import sys, math
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene import Scene, INK
from i2p_scene_r2 import spoke_with_pill
# colours sampled from the S5 raster; strokes heavier so the figure does not read too light
TEAL = '#1B717D'; OCHRE = '#B8781E'; SLATE = '#3F4A53'; HUB_EDGE = '#145159'; TITLE = '#10171F'; SUB = '#2B333A'; PILL_FILL = '#1B717D'
# richer treatment (author: 太浅，没有质感): solid teal hub with white text, cool-gray card fills, solid teal label pills with white text, cream analog card
CARD_FILL = '#F2F5F7'; ANALOG_FILL = '#FBF1DC'
JOB = '/root/lyf/goai/final_round/figstudio/jobs/bzso_taxonomy_r2'
sc = Scene(1536, 1024, source='pages/page_001/source.png', notes='BaZn2Si2O7 合成与相控制分类框架（super_teaser 第二轮 F04 → super_img2ppt 重建）')
HX, HY, HR = 768, 449, 127
# hub
sc.shape('hub', [HX - HR, HY - HR, 2 * HR, 2 * HR], shape='ellipse', fill=TEAL, stroke=HUB_EDGE, stroke_width=4)
sc.text('hub_t', [HX - 113, HY - 50, 226, 100], 'BaZn2Si2O7\n目标相', 32, bold=True, color='#FFFFFF', container='hub', line_height=1.45)
# cards: (id, box, title, sub, tip point of the spoke on the card edge)
cards = [('k1', [235, 48, 407, 166], '结构与多晶型', '相变 · 配位', (535, 216), '结构'), ('k2', [894, 48, 408, 166], '合成路线', '固相 · 溶胶—凝胶', (1000, 216), '制备'),
         ('k3', [26, 372, 341, 163], '近邻体系', 'Ba2ZnSi2O7 等', (369, 449), '近邻'), ('k4', [1168, 372, 342, 163], '证据边界', '直接 / 近邻 / 推断', (1166, 449), '判读'),
         ('k5', [202, 689, 376, 165], '组成与热处理', 'Ba/Sr · Zn 位', (500, 687), '变量'), ('k6', [958, 689, 376, 165], '玻璃析晶', '成核 · 生长', (1035, 687), '晶化')]
for cid, box, t, s, tip, lab in cards:
    x, y, w, h = box
    sc.shape(cid, box, fill=CARD_FILL, stroke=SLATE, stroke_width=3.5, radius=14)
    sc.text(cid + '_t', [x + 12, y + 26, w - 24, 58], t, 40, bold=True, color=TITLE, container=cid, font_group='title', fit='shrink', min_font_size=34)
    sc.text(cid + '_s', [x + 12, y + 94, w - 24, 42], s, 27, color=SUB, container=cid, font_group='sub', fit='shrink', min_font_size=23)
    dx, dy = tip[0] - HX, tip[1] - HY; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
    p_hub = (HX + ux * (HR + 3), HY + uy * (HR + 3))
    spoke_with_pill(sc, 's_' + cid, p_hub, tip, lab, pill_w=112, pill_h=50, size=24, color=TEAL, width=4, pill_fill=PILL_FILL, pill_stroke=HUB_EDGE, text_color='#FFFFFF')
# analog card (dashed ochre) straight below the hub
sc.shape('k7', [594, 810, 360, 170], fill=ANALOG_FILL, stroke=OCHRE, stroke_width=3.5, radius=14, dash=[16, 10])
sc.text('k7_t', [604, 840, 340, 50], 'Ba5Y12Zn[O(SiO4)]8', 28, bold=True, color=TITLE, container='k7', font_group='analog')
sc.text('k7_s', [604, 904, 340, 42], '未见直接报道', 27, color=SUB, container='k7', font_group='sub')
sc.line('s_k7', [(HX, HY + HR + 3), (HX, 640)], stroke=OCHRE, width=3.5, dash=[14, 9])
sc.shape('s_k7_p', [712, 642, 112, 50], fill=OCHRE, stroke='#8A5A10', stroke_width=2.5, radius=25)
sc.text('s_k7_pt', [718, 645, 100, 44], '类比', 24, bold=True, color='#FFFFFF', container='s_k7_p', font_group='pill')
sc.line('s_k7b', [(HX, 694), (HX, 807)], stroke=OCHRE, width=3.5, dash=[14, 9], arrow=True)
sc.write(JOB + '/scene.json'); print('wrote', len(sc.els), 'elements')
