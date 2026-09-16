"""scene.json for bzso_roadmap round-3 R01 (单行六卡，分区着色).
Content and reading order follow the generated raster; positions snapped to the design grid; icons are exact crops."""
import sys
from PIL import Image
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene_r3 import R3

JOB = '/root/lyf/goai/final_round/figstudio/jobs/bzso_roadmap_r3'
src = Image.open(JOB + '/pages/page_001/source.png').convert('RGB'); W, H = src.size
r = R3(W, H, source='pages/page_001/source.png', icon_src=src, job=JOB,
       notes='BaZn2Si2O7 综述路线图（super_teaser 第三轮 R01 → super_img2ppt 重建）')

zA = r.zone('zA', [40, 112, 980, 545], '文献证据', 'lit')
zB = r.zone('zB', [1044, 112, 980, 545], '实验方法', 'exp')

CARDS = [('n1', 70, '01', '结构基础', '低温与高温多晶型', 'lit', (95, 290, 190, 112), zA),
         ('n2', 423, '02', '合成路线', '固相 · 溶胶—凝胶', 'lit', (470, 314, 104, 94), zA),
         ('n3', 776, '03', '相控制', '组成 · 热处理', 'lit', (790, 288, 134, 116), zA),
         ('n4', 1074, '04', '近邻体系', 'Ba–Sr–Zn–Si', 'exp', (1136, 286, 122, 118), zB),
         ('n5', 1427, '05', '类似物判据', 'Ba5Y12Zn[O(SiO4)]8', 'note', (1470, 286, 124, 118), zB),
         ('n6', 1780, '06', '实验优先级', '相图 · 结构 · 热力学', 'exp', (1822, 286, 100, 118), zB)]
CW, CY, CH = 214, 190, 420
for cid, x, num, title, sub, fam, crop, zone in CARDS:
    r.card(cid, [x, CY, CW, CH], title, [sub], fam=fam, icon_crop=None, title_size=25, item_size=19,
           pad=52, padx=14, rules=False, container=zone)
    # step number in the corner, icon below the subtitle (the raster's card rhythm)
    r.sc.text(cid + '_n', [x + 16, CY + 18, 56, 28], num, 19, bold=True, color='#8A9199', align='left', container=cid)
    r.icon(cid + '_ic', [x + (CW - 118) / 2, CY + 230, 118, 150], crop, container=cid)

LABELS = ['结构约束', '条件窗口', '可迁移变量', '比较边界', '缺口驱动']
for k, lab in enumerate(LABELS):
    x0 = CARDS[k][1] + CW; x1 = CARDS[k + 1][1]
    r.conn(f'e{k}', [(x0 + 4, CY + CH / 2), (x1 - 4, CY + CH / 2)], label=lab, label_at=((x0 + x1) / 2, CY + CH / 2),
           label_size=18, label_split=False)

r.joints()
r.label_overlaps()
r.cross([zA, zB])
r.write(JOB + '/scene.json')
print('wrote', len(r.sc.els), 'elements', W, H)
