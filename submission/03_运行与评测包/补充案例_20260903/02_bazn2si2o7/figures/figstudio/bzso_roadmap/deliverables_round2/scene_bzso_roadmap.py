"""scene.json for bzso_roadmap F02 (蛇形双行六步链), measured from the 1536×1024 S5 raster."""
import sys
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene import Scene, INK, TEAL, OCHRE, PANEL, PANEL_LINE, OCHRE_TINT
JOB = '/root/lyf/goai/final_round/figstudio/jobs/bzso_roadmap'
sc = Scene(1536, 1024, source='pages/page_001/source.png', notes='BaZn2Si2O7 综述路线图（super_teaser S5 F02 → super_img2ppt 重建）')
J = 'connector joints, visible in source'; HEAD = {'length': 18, 'width': 22}; LW = 9
cards = {'n1': ([34, 115, 329, 250], '结构基础', '低温与高温多晶型', PANEL, PANEL_LINE), 'n2': ([549, 115, 330, 250], '合成路线', '固相 · 溶胶—凝胶', PANEL, PANEL_LINE), 'n3': ([1057, 115, 325, 249], '相控制', '组成 · 热处理', PANEL, PANEL_LINE),
         'n4': ([1072, 646, 335, 244], '近邻体系', 'Ba–Sr–Zn–Si', PANEL, PANEL_LINE), 'n5': ([548, 646, 347, 244], '类似物判据', 'Ba5Y12Zn[O(SiO4)]8', OCHRE_TINT, OCHRE), 'n6': ([34, 647, 335, 243], '实验优先级', '相图 · 结构 · 热力学', PANEL, PANEL_LINE)}
for cid, (box, t, s, fill, stroke) in cards.items():
    x, y, w, h = box
    sc.shape(cid, box, fill=fill, stroke=stroke, stroke_width=3, radius=18)
    sc.text(cid + '_t', [x + 14, y + 52, w - 28, 66], t, 46, bold=True, container=cid, font_group='title', fit='shrink', min_font_size=40)
    sc.text(cid + '_s', [x + 14, y + 128, w - 28, 48], s, 30, color='#3A4046', container=cid, font_group='sub', fit='shrink', min_font_size=26)
def labelled_arrow(id, p0, p1, label, pill_center, pill_w=124):
    # teal arrow split around a white label pill (horizontal or vertical run)
    (x0, y0), (x1, y1) = p0, p1; cx, cy = pill_center; ph = 48
    if y0 == y1:
        sign = 1 if x1 > x0 else -1
        sc.line(id + 'a', [(x0, y0), (cx - sign * (pill_w / 2 + 2), y0)], stroke=TEAL, width=LW)
        sc.line(id + 'b', [(cx + sign * (pill_w / 2 + 2), y0), (x1, y1)], stroke=TEAL, width=LW, arrow=True, head=HEAD)
    else:
        sc.line(id + 'a', [(x0, y0), (x0, cy - ph / 2 - 2)], stroke=TEAL, width=LW)
        sc.line(id + 'b', [(x0, cy + ph / 2 + 2), (x1, y1)], stroke=TEAL, width=LW, arrow=True, head=HEAD)
    sc.shape(id + '_p', [cx - pill_w / 2, cy - ph / 2, pill_w, ph], fill='#FFFFFF', stroke=TEAL, stroke_width=2.5, radius=ph / 2)
    sc.text(id + '_pt', [cx - pill_w / 2 + 8, cy - ph / 2 + 4, pill_w - 16, ph - 8], label, 24, bold=True, color=TEAL, container=id + '_p', font_group='pill')
labelled_arrow('e1', (364, 240), (547, 240), '结构约束', (456, 240))
labelled_arrow('e2', (880, 240), (1055, 240), '条件窗口', (968, 240))
# turn: n3 right edge → right → down → left into n4
sc.line('e3a', [(1383, 240), (1440, 240)], stroke=TEAL, width=LW, overlap=['e3b'], reason=J)
sc.line('e3b', [(1440, 240), (1440, 466)], stroke=TEAL, width=LW, overlap=['e3a'], reason=J)
sc.shape('e3_p', [1360, 468, 160, 48], fill='#FFFFFF', stroke=TEAL, stroke_width=2.5, radius=24)
sc.text('e3_pt', [1368, 472, 144, 40], '可迁移变量', 24, bold=True, color=TEAL, container='e3_p', font_group='pill')
sc.line('e3c', [(1440, 518), (1440, 767)], stroke=TEAL, width=LW, overlap=['e3d'], reason=J)
sc.line('e3d', [(1440, 767), (1409, 767)], stroke=TEAL, width=LW, arrow=True, head={'length': 22, 'width': 24}, overlap=['e3c'], reason=J)
labelled_arrow('e4', (1070, 767), (897, 767), '比较边界', (983, 767))
labelled_arrow('e5', (546, 767), (371, 767), '缺口驱动', (458, 767))
sc.write(JOB + '/scene.json'); print('wrote', len(sc.els), 'elements')
