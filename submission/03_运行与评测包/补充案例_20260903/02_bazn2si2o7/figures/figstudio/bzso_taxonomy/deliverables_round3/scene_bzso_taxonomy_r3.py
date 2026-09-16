"""scene.json for bzso_taxonomy round-3 R04 (左中心 + 实验方法/文献证据两分区).
Content and reading order follow the generated raster; positions snapped to the design grid; icons are exact crops.
All seven relations start at the hub, as in the paper: four into the experimental branches, three into the
comparison branches (the comparison bundle is routed below the zones so no spoke crosses a card)."""
import sys
from PIL import Image
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene_r3 import R3, FAM

JOB = '/root/lyf/goai/final_round/figstudio/jobs/bzso_taxonomy_r3'
src = Image.open(JOB + '/pages/page_001/source.png').convert('RGB'); W, H = src.size
r = R3(W, H, source='pages/page_001/source.png', icon_src=src, job=JOB,
       notes='BaZn2Si2O7 合成与相控制分类框架（super_teaser 第三轮 R04 → super_img2ppt 重建）')

zE = r.zone('zE', [491, 73, 560, 700], '实验方法', 'exp')
zL = r.zone('zL', [1194, 73, 543, 700], '文献证据', 'lit')

# ---- hub
r.card('hub', [35, 73, 294, 700], 'BaZn2Si2O7', ['目标相'], fam='exp', title_size=34, item_size=26,
       pad=300, padx=16, rules=False, strip=True, title_only_center=True)
r.sc.els[-1]['align'] = 'center'

# ---- experimental branches
exp = [('e1', 140, '结构与多晶型', '相变 · 配位', (566, 182, 60, 80), '结构'),
       ('e2', 295, '合成路线', '固相 · 溶胶—凝胶', (562, 376, 90, 80), '制备'),
       ('e3', 450, '组成与热处理', 'Ba/Sr · Zn 位', (580, 508, 58, 110), '变量'),
       ('e4', 605, '玻璃析晶', '成核 · 生长', (584, 668, 54, 74), '晶化')]
for cid, y, title, sub, crop, lab in exp:
    r.card(cid, [519, y, 502, 140], title, [sub], fam='exp', icon_crop=crop, title_size=27, item_size=21,
           pad=22, padx=18, rules=False, container=zE)

# ---- comparison branches
lit = [('l1', 150, '近邻体系', 'Ba2ZnSi2O7 等', (1264, 204, 108, 110), '近邻', False),
       ('l2', 340, '证据边界', '直接 / 近邻 / 推断', (1264, 410, 108, 110), '判读', False),
       ('l3', 530, 'Ba5Y12Zn[O(SiO4)]8', '未见直接报道', (1270, 618, 104, 118), '类比', True)]
for cid, y, title, sub, crop, lab, dashed in lit:
    r.card(cid, [1226, y, 483, 150], title, [sub], fam=('note' if dashed else 'lit'), icon_crop=crop,
           dashed=dashed, title_size=27, item_size=21, pad=24, padx=18, rules=False, container=zL)

# ---- spokes: hub → experimental branches
r.conn('t0', [(329, 440), (410, 440)], arrow=False)
r.conn('tv', [(410, 210), (410, 675)], arrow=False)
for k, (cid, y, *_rest) in enumerate(exp):
    lab = exp[k][5]
    r.conn(f's{k}', [(410, y + 70), (517, y + 70)], label=lab, label_at=(463, y + 70), label_size=18, label_split=False)

# ---- spokes: hub → comparison branches (bundle routed below the zones)
r.conn('u0', [(182, 775), (182, 822), (1150, 822)], arrow=False)
r.conn('uv', [(1150, 225), (1150, 822)], arrow=False)
for k, (cid, y, *_rest) in enumerate(lit):
    lab = lit[k][5]; dashed = lit[k][6]
    r.conn(f'v{k}', [(1150, y + 75), (1224, y + 75)], dashed=dashed, label=lab, label_at=(1187, y + 75),
           label_size=18, label_split=False,
           color=(FAM['note']['edge'] if dashed else None) or '#4B5563')

r.joints()
r.label_overlaps()
r.cross([zE, zL])
r.write(JOB + '/scene.json')
print('wrote', len(r.sc.els), 'elements', W, H)
