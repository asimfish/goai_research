"""scene.json for bzso_roadmap round-2 F03 (单行六卡 + 步序号 + 线稿图标), measured from the 2172×724 S5 raster.
Icons are exact crops of the source (schematic line motifs); everything else is native."""
import sys
from PIL import Image
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene import Scene, INK, TEAL, OCHRE
from i2p_scene_r2 import SLATE, TITLE, SUB
JOB = '/root/lyf/goai/final_round/figstudio/jobs/bzso_roadmap_r2'
src = Image.open(JOB + '/pages/page_001/source.png').convert('RGB'); W, H = src.size
sc = Scene(W, H, source='pages/page_001/source.png', notes='BaZn2Si2O7 综述路线图（super_teaser 第二轮 F03 → super_img2ppt 重建）')
cards = [('n1', 41, 283, '01', '结构基础', '低温与高温多晶型', (60, 375, 210, 145)), ('n2', 398, 650, '02', '合成路线', '固相 · 溶胶—凝胶', (455, 387, 140, 135)),
         ('n3', 765, 1015, '03', '相控制', '组成 · 热处理', (797, 367, 186, 158)), ('n4', 1137, 1385, '04', '近邻体系', 'Ba–Sr–Zn–Si', (1186, 375, 152, 140)),
         ('n5', 1499, 1767, '05', '类似物判据', 'Ba5Y12Zn[O(SiO4)]8', (1543, 373, 183, 152)), ('n6', 1882, 2133, '06', '实验优先级', '相图 · 结构 · 热力学', (1926, 373, 190, 150))]
Y0, Y1 = 156, 547


def crop(name, box):
    x, y, w, h = box; src.crop((x, y, x + w, y + h)).save(f'{JOB}/assets/{name}.png'); return f'assets/{name}.png'


for cid, x0, x1, num, title, sub, icon in cards:
    w = x1 - x0; ochre = cid == 'n5'
    sc.shape(cid, [x0, Y0, w, Y1 - Y0], fill='#FFFFFF', stroke=(OCHRE if ochre else SLATE), stroke_width=2.5, radius=14)
    sc.text(cid + '_n', [x0 + 16, Y0 + 12, 70, 34], num, 22, bold=True, color='#8A9199', align='left', container=cid, font_group='num')
    sc.text(cid + '_t', [x0 + 10, 228, w - 20, 60], title, 40, bold=True, color=TITLE, container=cid, font_group='title', fit='shrink', min_font_size=34)
    sc.text(cid + '_s', [x0 + 8, 296, w - 16, 40], sub, 25, color=SUB, container=cid, font_group='sub', fit='shrink', min_font_size=21)
    ix, iy, iw, ih = icon
    sc.els.append({'id': cid + '_i', 'kind': 'image', 'z': sc._z(), 'box': [ix, iy, iw, ih], 'path': crop(cid + '_icon', icon), 'provenance': 'exact crop of source page_001 (monochrome line motif)', 'contains_text': False, 'image_fit': 'contain', 'container': cid})
# arrows between cards with labels above
labels = ['结构约束', '条件窗口', '可迁移变量', '比较边界', '缺口驱动']
for k in range(5):
    xa, xb = cards[k][2] + 10, cards[k + 1][1] - 10; cx = (xa + xb) / 2
    sc.line(f'e{k}', [(xa, 332), (xb, 332)], stroke=TEAL, width=5, arrow=True, head={'length': 18, 'width': 18})
    tw = Scene.measure(labels[k], 20) + 10
    sc.text(f'e{k}_l', [cx - tw / 2, 286, tw, 32], labels[k], 20, color=SUB, font_group='edge')
# baseline
sc.line('base', [(37, 572), (2134, 572)], stroke='#C9CFD4', width=4)
sc.write(JOB + '/scene.json'); print('wrote', len(sc.els), 'elements', W, H)
