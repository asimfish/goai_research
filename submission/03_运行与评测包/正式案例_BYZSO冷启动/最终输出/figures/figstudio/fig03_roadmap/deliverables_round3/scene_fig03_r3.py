"""scene.json for fig03 round-3 R02 (水平主线 + 反馈弧 + 问题行).
Content and reading order follow the generated raster; positions snapped to the design grid; icons are exact crops.
Paper-faithful routing kept from earlier rounds: the fork is fed only by 模型筛选的前驱体 and the dashed feedback
returns to 结构假设."""
import sys
from PIL import Image
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene_r3 import R3

JOB = '/root/lyf/goai/final_round/figstudio/jobs/fig03_r3'
src = Image.open(JOB + '/pages/page_001/source.png').convert('RGB'); W, H = src.size
r = R3(W, H, source='pages/page_001/source.png', icon_src=src, job=JOB,
       notes='图 3 本文的研究路线（super_teaser 第三轮 R02 → super_img2ppt 重建；分叉只由前驱体驱动、反馈回结构假设）')

zL = r.zone('zL', [27, 30, 933, 517], '文献证据', 'lit')
zE = r.zone('zE', [999, 29, 439, 518], '实验方法', 'exp')
zR = r.zone('zR', [1477, 30, 412, 517], '结果反馈', 'lit')
zQ = r.zone('zQ', [29, 615, 1858, 180], '判断提醒', 'note')

# ---- evidence chain
r.card('c1', [51, 131, 270, 320], '文献依据', ['Ba–Y–Si–O 谱系', 'Ba–Zn–Si–O 结构近邻', 'Y–Si–O 工艺参照'],
       fam='lit', icon_crop=(86, 156, 64, 84), title_size=26, item_size=20, item_gap=16, pad=16, container=zL)
r.card('c2', [353, 131, 278, 320], '结构假设', ['局部组成网格', 'Zn–Y–氧计量耦合', '竞争相与玻璃区'],
       fam='lit', icon_crop=(388, 156, 64, 84), title_size=26, item_size=20, item_gap=16, pad=16, container=zL)
r.card('c3', [657, 131, 278, 320], '模型筛选的前驱体', ['BaCO3 + Y2O3 + SiO2', 'ZnO / MgO / Co3O4'],
       fam='lit', icon_crop=(692, 156, 64, 84), title_size=26, item_size=20, item_gap=16, pad=16,
       tag='模型排序 ≠ 验证', tag_size=19, container=zL)

# ---- two parallel experiment lanes
r.card('l1', [1038, 105, 367, 195], '固相成相', ['分段煅烧 → 复磨 → 退火', '批量相区与相纯度'],
       fam='exp', icon_crop=(1074, 126, 88, 62), title_size=26, item_size=20, item_gap=14, pad=16, container=zE)
r.card('l2', [1038, 317, 367, 212], '高温溶液长晶', ['助熔 → 保温 → 慢冷', '单晶结构与液相选择性'],
       fam='exp', icon_crop=(1074, 330, 76, 86), title_size=26, item_size=20, item_gap=14, pad=16, container=zE)

# ---- feedback card
r.card('c5', [1509, 130, 355, 367], '结果反馈', ['PXRD / Rietveld', 'SCXRD', 'EDS / EPMA / ICP', '高温相与冷却产物'],
       fam='lit', icon_crop=(1536, 156, 120, 88), title_size=26, item_size=20, item_gap=20, pad=16, container=zR)

# ---- open questions
qs = [('q1', 105, 'Zn 是否进入并与氧计量耦合？'), ('q2', 703, '稳定相区还是液相选择性？'), ('q3', 1292, '实际组成与结构信号如何对应？')]
for qid, x, text in qs:
    w = 539 if qid != 'q3' else 556
    r.card(qid, [x, 672, w, 96], text, fam='note', strip=False, title_size=24, pad=24, title_only_center=True,
           fill='#FFFFFF', container=zQ)

# ---- connectors
r.conn('e1', [(321, 291), (351, 291)])
r.conn('e2', [(631, 291), (655, 291)])
r.conn('fk0', [(935, 291), (985, 291)], arrow=False)
r.conn('fkv', [(985, 202), (985, 423)], arrow=False)
r.conn('fk1', [(985, 202), (1036, 202)])
r.conn('fk2', [(985, 423), (1036, 423)])
r.conn('mg1', [(1405, 202), (1455, 202)], arrow=False)
r.conn('mg2', [(1405, 423), (1455, 423)], arrow=False)
r.conn('mgv', [(1455, 202), (1455, 423)], arrow=False)
r.conn('mg3', [(1455, 313), (1507, 313)])
r.conn('fb', [(1686, 497), (1686, 585), (492, 585), (492, 453)], dashed=True,
       label='更新组成与工艺', label_at=(1028, 585), label_size=20)

r.joints()
r.cross([zL, zE, zR, zQ])
r.write(JOB + '/scene.json')
print('wrote', len(r.sc.els), 'elements', W, H)
