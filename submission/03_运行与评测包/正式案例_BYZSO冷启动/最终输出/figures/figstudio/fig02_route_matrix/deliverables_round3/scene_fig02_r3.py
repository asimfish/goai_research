"""scene.json for fig02 round-3 R01 (三层：路线区 → 统一实验记录 → 表征区).
Content and reading order follow the generated raster; positions snapped to the design grid; icons are exact crops."""
import sys
from PIL import Image
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene_r3 import R3

JOB = '/root/lyf/goai/final_round/figstudio/jobs/fig02_r3'
src = Image.open(JOB + '/pages/page_001/source.png').convert('RGB'); W, H = src.size
r = R3(W, H, source='pages/page_001/source.png', icon_src=src, job=JOB,
       notes='图 2 不同合成方法的条件比较与产物表征（super_teaser 第三轮 R01 → super_img2ppt 重建）')

# ---- three horizontal zones
zT = r.zone('zT', [32, 48, 1472, 340], '实验方法', 'exp')
zM = r.zone('zM', [32, 462, 1472, 252], '文献证据', 'lit')
zB = r.zone('zB', [32, 780, 1472, 212], None, 'exp')

# ---- five synthesis routes
routes = [('r1', '外加助熔', ['溶解', '保温', '慢冷分离'], (85, 150, 58, 52), False, None),
          ('r2', '自熔/熔体', ['均化', '自发成核', '受控冷却'], (373, 126, 58, 76), False, None),
          ('r3', '固相陶瓷', ['混合压片', '煅烧复磨', '烧结'], (662, 140, 58, 62), False, None),
          ('r4', '机械化学预活化', ['高能研磨', '活化', '后续成相'], (947, 135, 54, 66), False, None),
          ('r5', 'Czochralski', ['预烧熔化', '籽晶提拉', '退火'], (1232, 130, 52, 76), True, '工艺参照')]
RX0, RW, RGAP = 52, 274, 14
for k, (cid, title, items, crop, dashed, tag) in enumerate(routes):
    x = RX0 + k * (RW + RGAP)
    r.card(cid, [x, 108, RW, 252], title, items, fam=('mute' if dashed else 'exp'), icon_crop=crop, dashed=dashed,
           title_size=25, item_size=20, item_gap=10, pad=14, tag=tag, container=zT)

# ---- unified record ledger (one wide card with four columns)
r.card('led', [52, 520, 1432, 172], '统一实验记录', fam='lit', icon_crop=(89, 552, 81, 58), title_size=27,
       pad=16, rules=False, tag='抽取框架 ≠ 实验处方', tag_size=19, tag_at='title', container=zM)
CELLW = 330
for k, t in enumerate(['配比与原料', '温度—时间与气氛', '坩埚与助熔剂', '冷却、生长与分离']):
    cx = 74 + k * (CELLW + 14)
    r.card(f'cell{k}', [cx, 604, CELLW, 62], t, fam='lit', strip=False, title_size=21, pad=18,
           title_only_center=True, fill='#FFFFFF', container='led')

# ---- four complementary characterizations
checks = [('k1', '单晶结构', ['结构身份与位点占据'], (92, 852, 50, 60)),
          ('k2', 'PXRD / Rietveld', ['批量相纯与杂相'], (440, 852, 92, 54)),
          ('k3', '成分与污染', ['名义—局域—体平均'], (800, 856, 92, 46)),
          ('k4', '高温稳定性', ['原位高温 ≠ 冷却回收'], (1163, 854, 78, 54))]
for k, (cid, title, items, crop) in enumerate(checks):
    x = 52 + k * (346 + 15)
    r.card(cid, [x, 836, 346, 140], title, items, fam='exp', icon_crop=crop, title_size=24, item_size=20,
           pad=14, container=zB)

# ---- connectors: routes → ledger, ledger → checks
for k, lab in enumerate(['配比·温度', '熔体·容器', '混合·煅烧', '研磨·污染', '籽晶·退火']):
    x = RX0 + k * (RW + RGAP) + RW / 2
    r.conn(f'd{k}', [(x, 362), (x, 518)], label=lab, label_at=(x, 440), label_size=19, dashed=(k == 4))
for k, lab in enumerate(['结构', '相组成', '成分', '高温']):
    x = 52 + k * (346 + 15) + 173
    r.conn(f'c{k}', [(x, 694), (x, 834)], label=lab, label_at=(x, 764), label_size=19)

r.joints()
r.cross([zT, zM, zB])
r.write(JOB + '/scene.json')
print('wrote', len(r.sc.els), 'elements', W, H)
