"""scene.json for fig01 round-2 F03 (同心圆环 + 账本), measured from the 1536×1024 S5 raster."""
import sys
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene import Scene, INK, TEAL, OCHRE, PANEL, PANEL_LINE, GRAY
from i2p_scene_r2 import bullseye, SLATE, TOKEN_LINE, TITLE, SUB
JOB = '/root/lyf/goai/final_round/figstudio/jobs/fig01_r2'
sc = Scene(1536, 1024, source='pages/page_001/source.png', notes='图 1 不同文献对目标化合物合成研究的适用范围（super_teaser 第二轮 F03 → super_img2ppt 重建）')
J = 'connector joints, visible in source'; HEAD = {'length': 20, 'width': 18}
CX, CY = 303, 452
# ---- concentric bands (outer → inner) + centre disc
bullseye(sc, CX, CY, [277, 213, 154, 104, 53], ['#FFFFFF', '#F3F5F6', '#FFFFFF', '#F3F5F6', '#E3E7EA'], ['#8A9199', '#B5BDC4', '#B5BDC4', '#B5BDC4', '#B5BDC4'],
         ['非相关资料', '工艺参照研究', '结构相关化合物', None, None], label_size=24, label_dys={0: -245, 1: -183, 2: -128})
sc.shape('disc', [CX - 27, CY - 27, 54, 54], shape='ellipse', fill='#3A4046', stroke=None, overlap=['ring4'], reason='centre disc inside the innermost band, visible in source')
# inner two band labels sit lower-right / bottom as in the raster (band 3 = 结构相关化合物…104..154 already labelled at top; band 4 = 目标化合物直接报道, band 2 = 同类)
sc.text('lab_direct', [330, 486, 232, 36], '目标化合物直接报道', 24, bold=True, container='ring0', overlap=['ring1', 'ring2', 'ring3', 'ring4'], reason='band label printed across the bands, visible in source')
sc.text('lab_lineage', [165, 582, 276, 36], '同类 Ba–Y 四方硅酸盐', 24, bold=True, container='ring0')
# ---- distance axis (diagonal to the upper right) with 近 / 远 and a horizontal axis label beside it
sc.line('axis', [(CX + 22, CY - 22), (540, 240)], stroke=INK, width=2.5, arrow=True, head={'length': 16, 'width': 13}, overlap=['ring1', 'ring2', 'ring3', 'ring4'], reason='axis drawn across the bands, visible in source')
sc.text('axis_near', [360, 418, 40, 34], '近', 22, bold=True, container='ring0', overlap=['ring3', 'ring4'], reason='axis mark across bands, visible in source')
sc.text('axis_far', [548, 222, 40, 34], '远', 22, bold=True)
sc.text('axis_lab', [470, 332, 142, 30], '与目标相的距离', 19, color=SUB)
# ---- bundled arrow → caveat tag → ledger
sc.line('bundle_a', [(334, 452), (549, 452)], stroke=TEAL, width=6)
sc.shape('tag', [552, 416, 251, 51], fill='#FFFFFF', stroke=OCHRE, stroke_width=2.5, radius=8)
sc.text('tag_t', [560, 421, 235, 41], '近邻条件 ≠ 已验证配方', 22, bold=True, color='#7A5A1C', container='tag')
sc.line('bundle_b', [(805, 452), (831, 452)], stroke=TEAL, width=6, arrow=True, head=HEAD)
# ---- ledger card with title and six row tokens
sc.shape('ledger', [833, 186, 322, 505], fill='#FFFFFF', stroke=SLATE, stroke_width=2.5, radius=14)
sc.text('ledger_t', [845, 200, 298, 48], '相同实验项目下比较', 30, bold=True, color=TITLE, container='ledger', font_group='title')
rows = ['原料与配比', '热史', '气氛', '容器与助熔剂', '冷却与分离', '产物表征']
for k, (label, ry) in enumerate(zip(rows, [262, 331, 400, 470, 540, 609])):
    sc.shape(f'row{k}', [851, ry, 287, 60], fill='#FFFFFF', stroke=TOKEN_LINE, stroke_width=1.5, radius=8, container='ledger')
    sc.text(f'row{k}_t', [859, ry + 10, 271, 40], label, 26, bold=True, color=SUB, container=f'row{k}', font_group='rows')
# ---- fan-out to the three uses
sc.line('fan_trunk', [(1157, 452), (1215, 452)], stroke=TEAL, width=6, overlap=['fan_v'], reason=J)
sc.line('fan_v', [(1215, 287), (1215, 610)], stroke=TEAL, width=6, overlap=['fan_trunk', 'u1_a', 'u2_a', 'u3_a'], reason=J)
uses = [('u1', [1273, 236, 237, 102], '直接条件复现', 287), ('u2', [1274, 399, 237, 105], '谱系内相图与\n结构比较', 452), ('u3', [1275, 559, 235, 102], '方法与变量结构', 610)]
for uid, box, label, ay in uses:
    sc.line(uid + '_a', [(1215, ay), (box[0] - 2, ay)], stroke=TEAL, width=6, arrow=True, head=HEAD, overlap=['fan_v'], reason=J)
    sc.shape(uid, box, fill='#FFFFFF', stroke=SLATE, stroke_width=2.5, radius=14)
    sc.text(uid + '_t', [box[0] + 10, box[1] + 10, box[2] - 20, box[3] - 20], label, 26, bold=True, color=TITLE, container=uid, font_group='cards', line_height=1.4)
# ---- exclusion path: outer band → down → right → 排除 pill → 划定研究范围
sc.line('ex1', [(220, 728), (220, 806)], stroke=GRAY, width=3, dash=[14, 10], overlap=['ex2'], reason=J)
sc.line('ex2', [(220, 806), (898, 806)], stroke=GRAY, width=3, dash=[14, 10], overlap=['ex1'], reason=J)
sc.shape('expill', [900, 781, 123, 50], fill='#FFFFFF', stroke='#B5BDC4', stroke_width=2, radius=25)
sc.text('expill_t', [908, 787, 107, 38], '排除', 24, bold=True, color=SUB, container='expill')
sc.line('ex3', [(1025, 806), (1274, 806)], stroke=GRAY, width=3, dash=[14, 10], arrow=True)
sc.shape('u4', [1276, 757, 234, 102], fill='#FFFFFF', stroke=SLATE, stroke_width=2.5, radius=14)
sc.text('u4_t', [1286, 767, 214, 82], '划定研究范围', 26, bold=True, color=TITLE, container='u4', font_group='cards')
# ---- mutual overlap declarations between the ring stack and everything drawn on top of it
RINGS = ['ring0', 'ring1', 'ring2', 'ring3', 'ring4']
INSIDE = ['disc', 'axis', 'axis_near', 'axis_lab', 'lab_direct', 'lab_lineage', 'bundle_a', 'tag', 'tag_t', 'ring0_t', 'ring1_t', 'ring2_t']
for el in sc.els:
    if el['id'] in RINGS:
        el['allow_overlap_with'] = sorted(set(el.get('allow_overlap_with', []) + [i for i in INSIDE if i != el['id']] + [r for r in RINGS if r != el['id']])); el['overlap_reason'] = 'concentric bands with labels, axis, disc and the bundled arrow drawn over them, visible in source'
    elif el['id'] in INSIDE:
        el['allow_overlap_with'] = sorted(set(el.get('allow_overlap_with', []) + RINGS)); el['overlap_reason'] = 'drawn over the concentric bands, visible in source'
sc.write(JOB + '/scene.json'); print('wrote', len(sc.els), 'elements')
