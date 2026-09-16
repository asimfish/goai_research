"""scene.json for fig02 F01 (上下三层：工艺列 → 统一实验记录 → 表征卡), measured from the 1536×1024 S5 raster."""
import sys
from PIL import Image
sys.path.insert(0, '/root/lyf/goai/final_round/figstudio')
from i2p_scene import Scene, INK, TEAL, OCHRE, PANEL, PANEL_LINE, GRAY
JOB = '/root/lyf/goai/final_round/figstudio/jobs/fig02'
src = Image.open(JOB + '/pages/page_001/source.png').convert('RGB')
sc = Scene(1536, 1024, source='pages/page_001/source.png', notes='图 2 不同合成方法的条件比较与产物表征（super_teaser S5 F01 → super_img2ppt 重建）')
J = 'connector joints, visible in source'
HEAD = {'length': 16, 'width': 13}
# ---- five route columns
cols = [('r1', 49, 326, '外加助熔', ['溶解', '保温', '慢冷分离'], '配比·温度'), ('r2', 348, 617, '自熔/熔体', ['均化', '自发成核', '受控冷却'], '熔体·容器'),
        ('r3', 640, 899, '固相陶瓷', ['混合压片', '煅烧复磨', '烧结'], '混合·煅烧'), ('r4', 919, 1188, '机械化学预活化', ['高能研磨', '活化', '后续成相'], '研磨·污染'),
        ('r5', 1210, 1490, 'Czochralski', ['预烧熔化', '籽晶提拉', '退火'], '籽晶·退火')]
pill_x = [(109, 267), (403, 564), (688, 848), (973, 1135), (1267, 1427)]
for k, (rid, x0, x1, head, toks, pill) in enumerate(cols):
    dashed = rid == 'r5'; w = x1 - x0
    sc.shape(rid, [x0, 28, w, 280], fill=PANEL, stroke=(GRAY if dashed else PANEL_LINE), stroke_width=2.5, radius=16, dash=([14, 9] if dashed else None))
    if not dashed:
        sc.shape(rid + '_h', [x0, 28, w, 58], fill=TEAL, stroke=None, radius=16, container=rid)
        sc.text(rid + '_ht', [x0 + 10, 34, w - 20, 46], head, 30, bold=True, color='#FFFFFF', container=rid + '_h', font_group='colhead')
        tys = [104, 182, 260]
    else:
        sc.text(rid + '_ht', [x0 + 10, 40, w - 20, 44], head, 30, bold=True, color='#5A6470', container=rid, font_group='colhead')
        sc.shape(rid + '_tag', [1295, 84, 110, 34], fill=OCHRE, stroke=None, radius=6, container=rid)
        sc.text(rid + '_tagt', [1298, 86, 104, 30], '工艺参照', 19, bold=True, color='#FFFFFF', container=rid + '_tag')
        tys = [128, 195, 262]
    tx0, tx1 = (x0 + 31, x1 - 29) if not dashed else (1240, 1460)
    cx = (x0 + x1) / 2
    for i, (t, ty) in enumerate(zip(toks, tys)):
        tid = f'{rid}_t{i}'
        sc.shape(tid, [tx0, ty, tx1 - tx0, 42], fill='#FFFFFF', stroke=('#9AA5AD' if dashed else '#B5BDC4'), stroke_width=2, radius=8, container=rid)
        sc.text(tid + '_t', [tx0 + 6, ty + 3, tx1 - tx0 - 12, 36], t, 24, bold=True, color=('#5A6470' if dashed else INK), container=tid, font_group='token')
        if i < 2:
            sc.line(f'{rid}_a{i}', [(cx, ty + 44), (cx, tys[i + 1] - 2)], stroke=INK, width=3, arrow=True, head={'length': 12, 'width': 10}, container=rid)
    # column → pill → ledger
    px0, px1 = pill_x[k]
    sc.line(rid + '_d1', [(cx, 310), (cx, 375)], stroke=INK, width=3, arrow=True, head=HEAD)
    sc.shape(rid + '_p', [px0, 377, px1 - px0, 42], fill='#FFFFFF', stroke='#B5BDC4', stroke_width=2, radius=21)
    sc.text(rid + '_pt', [px0 + 8, 380, px1 - px0 - 16, 36], pill, 23, bold=True, container=rid + '_p', font_group='pill')
    sc.line(rid + '_d2', [(cx, 421), (cx, 464)], stroke=INK, width=3, arrow=True, head=HEAD)
# ---- ledger
sc.shape('ledger', [44, 466, 1449, 172], fill='#FFFFFF', stroke=TEAL, stroke_width=3, radius=16)
sc.shape('ledger_h', [44, 466, 1449, 70], fill=TEAL, stroke=None, radius=16, container='ledger')
sc.text('ledger_t', [560, 476, 420, 52], '统一实验记录', 34, bold=True, color='#FFFFFF', container='ledger_h', font_group='ledgerhead')
sc.shape('btag', [1246, 476, 231, 45], fill=OCHRE, stroke=None, radius=8, container='ledger_h')
sc.text('btag_t', [1252, 479, 219, 40], '抽取框架 ≠ 实验处方', 22, bold=True, color='#FFFFFF', container='btag')
cells = [(64, 407, '配比与原料'), (419, 762, '温度—时间与气氛'), (774, 1118, '坩埚与助熔剂'), (1129, 1474, '冷却、生长与分离')]
lower = [(160, 284, '结构'), (524, 649, '相组成'), (884, 1011, '成分'), (1253, 1377, '高温')]
cards = [(47, 397, '单晶结构', '结构身份与位点占据'), (412, 760, 'PXRD / Rietveld', '批量相纯与杂相'), (776, 1124, '成分与污染', '名义—局域—体平均'), (1140, 1490, '高温稳定性', '原位高温 ≠ 冷却回收')]
for k, ((cx0, cx1, ct), (lx0, lx1, lt), (kx0, kx1, kt, ks)) in enumerate(zip(cells, lower, cards)):
    sc.shape(f'cell{k}', [cx0, 541, cx1 - cx0, 78], fill=PANEL, stroke=PANEL_LINE, stroke_width=2, radius=10, container='ledger')
    sc.text(f'cell{k}_t', [cx0 + 10, 552, cx1 - cx0 - 20, 56], ct, 27, bold=True, container=f'cell{k}', font_group='cell')
    mx = (cx0 + cx1) / 2
    sc.line(f'l{k}_a1', [(mx, 640), (mx, 669)], stroke=INK, width=3, arrow=True, head=HEAD)
    sc.shape(f'l{k}_p', [lx0, 671, lx1 - lx0, 40], fill='#FFFFFF', stroke='#B5BDC4', stroke_width=2, radius=19)
    sc.text(f'l{k}_pt', [lx0 + 8, 674, lx1 - lx0 - 16, 34], lt, 21, bold=True, container=f'l{k}_p', font_group='pill')
    sc.line(f'l{k}_a2', [(mx, 713), (mx, 736)], stroke=INK, width=3, arrow=True, head=HEAD)
    sc.shape(f'card{k}', [kx0, 738, kx1 - kx0, 244], fill=PANEL, stroke=PANEL_LINE, stroke_width=2.5, radius=16)
    sc.text(f'card{k}_t', [kx0 + 12, 750, kx1 - kx0 - 24, 46], kt, 30, bold=True, container=f'card{k}', font_group='cardtitle')
    sc.text(f'card{k}_s', [kx0 + 12, 798, kx1 - kx0 - 24, 34], ks, 22, color='#4A5158', container=f'card{k}', font_group='cardsub')
# ---- icons: exact crops of the source (schematic line motifs) and native dots
def crop(name, box):
    x, y, w, h = box; src.crop((x, y, x + w, y + h)).save(f'{JOB}/assets/{name}.png'); return f'assets/{name}.png'
sc.els.append({'id': 'icon_poly', 'kind': 'image', 'z': sc._z(), 'box': [148, 834, 144, 142], 'path': crop('poly', (148, 834, 144, 142)), 'provenance': 'exact crop of source page_001 (schematic polyhedron motif)', 'contains_text': False, 'image_fit': 'contain', 'container': 'card0'})
sc.els.append({'id': 'icon_peaks', 'kind': 'image', 'z': sc._z(), 'box': [428, 834, 318, 126], 'path': crop('peaks', (428, 834, 318, 126)), 'provenance': 'exact crop of source page_001 (schematic diffraction trace)', 'contains_text': False, 'image_fit': 'contain', 'container': 'card1'})
for i, (dx, r, col) in enumerate([(866, 30, '#3E464D'), (953, 24, '#6B747C'), (1031, 18, '#9AA3AB')]):
    sc.shape(f'dot{i}', [dx - r, 905 - r, 2 * r, 2 * r], shape='ellipse', fill=col, stroke=None, container='card2')
sc.els.append({'id': 'icon_curve', 'kind': 'image', 'z': sc._z(), 'box': [1170, 856, 292, 108], 'path': crop('curve', (1170, 856, 292, 108)), 'provenance': 'exact crop of source page_001 (schematic temperature curve)', 'contains_text': False, 'image_fit': 'contain', 'container': 'card3'})
sc.write(JOB + '/scene.json'); print('wrote', len(sc.els), 'elements')
