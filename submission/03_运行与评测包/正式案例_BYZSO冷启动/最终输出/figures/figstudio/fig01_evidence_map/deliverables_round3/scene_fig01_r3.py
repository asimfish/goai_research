"""scene.json for fig01 round-3 R01 (三区：证据阶梯 → 比较账本 → 可回答问题).
Structure, content and reading order follow the generated raster; positions are snapped to the design system's grid
(equal card widths, equal gutters) and the icons are exact crops of that raster."""
import sys
from PIL import Image
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene_r3 import R3, CONN

JOB = '/root/lyf/goai/final_round/figstudio/jobs/fig01_r3'
src = Image.open(JOB + '/pages/page_001/source.png').convert('RGB'); W, H = src.size
r = R3(W, H, source='pages/page_001/source.png', icon_src=src, job=JOB,
       notes='图 1 不同文献对目标化合物合成研究的适用范围（super_teaser 第三轮 R01 → super_img2ppt 重建）')

# ---- group zones
zA = r.zone('zA', [28, 36, 672, 815], '文献证据', 'lit')
zB = r.zone('zB', [720, 36, 470, 815], '实验方法', 'exp')
zC = r.zone('zC', [1240, 36, 506, 815], None, 'lit')

# ---- left column: evidence ladder (four comparable classes + one excluded class)
LX, LW = 100, 370
left = [('a1', 118, '目标化合物直接报道', (145, 150, 51, 64), 'lit', False),
        ('a2', 246, '同类 Ba–Y 四方硅酸盐', (142, 274, 60, 72), 'lit', False),
        ('a3', 374, '结构相关化合物', (146, 401, 66, 80), 'lit', False),
        ('a4', 502, '工艺参照研究', (147, 537, 71, 74), 'lit', False),
        ('a5', 660, '非相关资料', (139, 695, 79, 82), 'mute', True)]
for cid, y, title, crop, fam, dashed in left:
    r.card(cid, [LX, y, LW, 110], title, fam=fam, icon_crop=crop, dashed=dashed, pad=26, title_size=26, container=zA)
r.axis('ax', 76, 118, 770, label='与目标相的距离', container=zA, label_x=44)

# ---- comparison ledger
r.card('led', [800, 150, 368, 560], '相同实验项目下比较',
       ['原料与配比', '热史', '气氛', '容器与助熔剂', '冷却与分离', '产物表征'],
       fam='exp', icon_crop=(820, 161, 67, 69), item_size=22, item_gap=40, pad=20, container=zB)

# ---- bracket: the four comparable classes feed the ledger through one bundled connector
for k, (cid, y, *_rest) in enumerate(left[:4]):
    r.conn(f'br{k}', [(LX + LW, y + 55), (512, y + 55)], arrow=False, width=2)
r.conn('brv', [(512, 173), (512, 557)], arrow=False, width=2)
r.conn('brh', [(512, 365), (798, 365)], label='近邻条件 ≠ 已验证配方', label_at=(656, 365), label_size=18, label_fam='note')

# ---- fan-out to the answerable questions
RX, RW = 1300, 416
right = [('u1', 118, '直接条件复现', (1345, 148, 92, 94), 'lit', False),
         ('u2', 310, '谱系内相图与结构比较', (1336, 333, 101, 91), 'lit', False),
         ('u3', 502, '方法与变量结构', (1341, 515, 94, 91), 'lit', False),
         ('u4', 660, '划定研究范围', (1345, 697, 92, 84), 'mute', True)]
for cid, y, title, crop, fam, dashed in right:
    r.card(cid, [RX, y, RW, 110], title, fam=fam, icon_crop=crop, dashed=dashed, pad=26, title_size=26, container=zC)
r.conn('fan0', [(1168, 365), (1215, 365)], arrow=False, width=2)
r.conn('fanv', [(1215, 173), (1215, 557)], arrow=False, width=2)
for k, y in enumerate((173, 365, 557)):
    r.conn(f'fan{k + 1}', [(1215, y), (RX - 2, y)], width=2)

# ---- excluded class bypasses the ledger
r.conn('ex', [(LX + LW, 715), (540, 715), (540, 806), (1266, 806), (1266, 715), (RX - 2, 715)], dashed=True,
       label='排除', label_at=(880, 806), label_size=20)

r.joints()
r.cross([zA, zB, zC])
r.write(JOB + '/scene.json')
print('wrote', len(r.sc.els), 'elements', W, H)
