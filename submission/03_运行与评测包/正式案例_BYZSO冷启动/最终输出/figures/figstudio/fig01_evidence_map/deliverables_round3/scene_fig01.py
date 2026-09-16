"""scene.json for fig01 F01 (文献条 + 比较表), measured from the 1536×1024 S5 raster (component scan, see run log)."""
import sys
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene import Scene, INK, TEAL, OCHRE, PANEL, PANEL_LINE, GRAY, TEAL_TINT
sc = Scene(1536, 1024, source='pages/page_001/source.png', notes='图 1 不同文献对目标化合物合成研究的适用范围（super_teaser S5 F01 → super_img2ppt 重建；文字按论文原文校对）')
# ---- distance axis
sc.line('axis_up', [(52, 478), (52, 138)], stroke=INK, width=3, arrow=True, head={'length': 18, 'width': 14})
sc.line('axis_dn', [(52, 480), (52, 819)], stroke=INK, width=3, arrow=True, head={'length': 18, 'width': 14})
sc.text('axis_near', [20, 80, 64, 54], '近', 30, bold=True)
sc.text('axis_far', [20, 824, 64, 54], '远', 30, bold=True)
sc.text('axis_lab', [6, 320, 42, 320], '与\n目\n标\n相\n的\n距\n离', 24, bold=False, color='#3A4046', line_height=1.6)
# ---- left cards with document icons
def sheet(id, x, y, w=44, h=56, stroke=INK, dash=None, fill='#FFFFFF', container=None, overlap=None):
    sc.shape(id, [x, y, w, h], shape='round_rect', radius=4, fill=fill, stroke=stroke, stroke_width=3, dash=dash, container=container, overlap=overlap, reason='stacked document sheets, visible in source')
    sc.line(id + '_l1', [(x + 12, y + h * 0.42), (x + w - 12, y + h * 0.42)], stroke=stroke, width=3, dash=dash, container=id)
    sc.line(id + '_l2', [(x + 12, y + h * 0.62), (x + w - 12, y + h * 0.62)], stroke=stroke, width=3, dash=dash, container=id)
def stack(id, x, y, n, stroke=INK, dash=None, container=None):
    ids = [f'{id}_{k}' for k in range(n)]
    for k in range(n):
        off = (n - 1 - k) * 14
        others = [i for i in ids if i != ids[k]]; others += [o + '_l1' for o in others] + [o + '_l2' for o in others]
        sheet(ids[k], x + off, y + off, stroke=stroke, dash=dash, container=container, overlap=others if n > 1 else None)
cards = [('c1', [90, 112, 400, 124], '目标化合物直接报道', TEAL_TINT, TEAL, 3, None, 1),
         ('c2', [92, 259, 398, 130], '同类 Ba–Y 四方硅酸盐', PANEL, '#7A8A93', 3, None, 3),
         ('c3', [92, 410, 398, 128], '结构相关化合物', PANEL, '#9AA5AD', 2.5, None, 3),
         ('c4', [92, 561, 398, 138], '工艺参照研究', PANEL, '#B5BDC4', 2.5, None, 3),
         ('c5', [92, 727, 398, 138], '非相关资料', PANEL, GRAY, 2.5, [12, 8], 3)]
for cid, box, label, fill, stroke, sw, dash, n in cards:
    x, y, w, h = box
    sc.shape(cid, box, fill=fill, stroke=stroke, stroke_width=sw, radius=14, dash=dash)
    ix, iy = x + 20, y + (h - 56 - (n - 1) * 14) / 2
    stack(cid + '_doc', ix, iy, n, stroke=(GRAY if cid == 'c5' else INK), dash=([8, 6] if cid == 'c5' else None), container=cid)
    tx = x + 20 + 44 + (n - 1) * 14 + 8
    sc.text(cid + '_t', [tx, y + 16, x + w - 12 - tx, h - 32], label, 26, bold=True, color=(GRAY if cid == 'c5' else INK), align='left', container=cid, font_group='cardlabel', fit='shrink', min_font_size=22)
# ---- bracket + bundled arrow into the ledger
J = 'connector joints, visible in source'
sc.line('br_v', [(508, 150), (508, 660)], stroke=TEAL, width=4, overlap=['br_t', 'br_b', 'br_arrow'], reason=J)
sc.line('br_t', [(494, 150), (508, 150)], stroke=TEAL, width=4, overlap=['br_v'], reason=J)
sc.line('br_b', [(494, 660), (508, 660)], stroke=TEAL, width=4, overlap=['br_v'], reason=J)
sc.line('br_arrow', [(508, 445), (671, 445)], stroke=TEAL, width=5, arrow=True, head={'length': 22, 'width': 18}, overlap=['br_v'], reason=J)
sc.shape('tag', [530, 349, 138, 84], fill=OCHRE, stroke=None, radius=8)
sc.text('tag_t', [538, 355, 122, 72], '近邻条件 ≠\n已验证配方', 21, bold=True, color='#FFFFFF', container='tag', line_height=1.4)
# ---- ledger
sc.shape('ledger', [673, 120, 414, 587], fill='#FFFFFF', stroke=TEAL, stroke_width=3, radius=14)
sc.shape('ledger_head', [673, 120, 414, 87], fill=TEAL, stroke=None, radius=14, container='ledger')
sc.text('ledger_title', [690, 132, 380, 63], '相同实验项目下比较', 34, bold=True, color='#FFFFFF', container='ledger_head')
rules = [293, 370, 453, 534, 616]
for k, ry in enumerate(rules):
    sc.line(f'rule{k}', [(690, ry), (1070, ry)], stroke='#D5DADF', width=2, container='ledger')
rows = ['原料与配比', '热史', '气氛', '容器与助熔剂', '冷却与分离', '产物表征']
bounds = [207] + rules + [707]
for k, label in enumerate(rows):
    y0, y1 = bounds[k], bounds[k + 1]
    sc.text(f'row{k}', [700, y0 + 12, 360, y1 - y0 - 24], label, 28, bold=True, align='left', container='ledger', font_group='rows')
# ---- fan-out to uses
sc.line('fan_trunk', [(1089, 445), (1140, 445)], stroke=TEAL, width=5, overlap=['fan_v'], reason=J)
sc.line('fan_v', [(1140, 228), (1140, 625)], stroke=TEAL, width=5, overlap=['fan_trunk', 'u1_a', 'u2_a', 'u3_a'], reason=J)
uses = [('u1', [1199, 165, 306, 127], '直接条件复现', 228), ('u2', [1200, 364, 307, 128], '谱系内相图与结构比较', 428), ('u3', [1200, 561, 306, 129], '方法与变量结构', 625)]
for uid, box, label, ay in uses:
    sc.line(uid + '_a', [(1140, ay), (box[0] - 2, ay)], stroke=TEAL, width=5, arrow=True, head={'length': 22, 'width': 18}, overlap=['fan_v'], reason=J)
    sc.shape(uid, box, fill=PANEL, stroke='#9AA5AD', stroke_width=2.5, radius=14)
    sc.text(uid + '_t', [box[0] + 14, box[1] + 18, box[2] - 28, box[3] - 36], label, 26, bold=True, container=uid, font_group='cardlabel', fit='shrink', min_font_size=22)
# ---- exclusion path
sc.line('ex1', [(492, 792), (789, 792)], stroke=GRAY, width=3, dash=[14, 10])
sc.shape('expill', [791, 769, 112, 51], fill='#E9ECEF', stroke='#C9CFD4', stroke_width=1.5, radius=25)
sc.text('expill_t', [799, 775, 96, 39], '排除', 24, color='#4A5158', container='expill')
sc.line('ex2', [(905, 792), (1160, 792)], stroke=GRAY, width=3, dash=[14, 10], arrow=True)
sc.shape('u4', [1162, 733, 343, 123], fill='#E3E7EA', stroke='#8A9199', stroke_width=2.5, radius=14)
sc.text('u4_t', [1176, 751, 315, 87], '划定研究范围', 26, bold=True, color='#3A4046', container='u4', font_group='cardlabel')
out = sys.argv[1] if len(sys.argv) > 1 else '/root/lyf/goai/final_round/figstudio/jobs/fig01/scene.json'
sc.write(out); print('wrote', out, len(sc.els), 'elements')
