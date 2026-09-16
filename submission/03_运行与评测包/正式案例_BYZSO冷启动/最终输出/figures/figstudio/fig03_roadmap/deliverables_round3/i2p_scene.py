"""Helpers to author super_img2ppt scene.json files for figure-studio outputs (source-pixel coordinates, top-left origin).
Every element is native (text / shape / line); no raster is reused.  Fonts: Latin 'Noto Sans' fallback → 'DejaVu Sans'; CJK 'Noto Sans CJK SC'.
usage: from i2p_scene import Scene; sc = Scene(1536, 1024, source='pages/page_001/source.png'); sc.card(...); sc.write('scene.json')
"""
import json
from pathlib import Path

INK = '#2B2F33'; TEAL = '#1F6F78'; OCHRE = '#B8862B'; PANEL = '#F3F5F6'; PANEL_LINE = '#C9CFD4'; GRAY = '#8A9199'; TEAL_TINT = '#E4F0F1'; OCHRE_TINT = '#FBF3E3'
CJK = 'Noto Sans CJK SC'; LATIN = 'DejaVu Sans'


class Scene:
    def __init__(self, w, h, source=None, background='#FFFFFF', notes=''):
        self.w, self.h = w, h; self.z = 0; self.els = []; self.source = source; self.bg = background; self.notes = notes

    def _z(self):
        self.z += 1; return self.z

    def shape(self, id, box, shape='round_rect', fill=None, stroke=None, stroke_width=2, radius=14, dash=None, container=None, z=None, overlap=None, reason=None):
        el = {'id': id, 'kind': 'shape', 'z': z or self._z(), 'box': [int(round(v)) for v in box], 'shape': shape}
        if overlap: el['allow_overlap_with'] = overlap; el['overlap_reason'] = reason or 'visible in source'
        if fill: el['fill'] = fill
        if stroke: el['stroke'] = stroke; el['stroke_width'] = stroke_width
        if shape == 'round_rect': el['radius'] = radius
        if dash: el['dash'] = dash
        if container: el['container'] = container
        self.els.append(el); return id

    def text(self, id, box, text, size, bold=False, color=INK, align='center', valign='middle', container=None, wrap=False, fit='strict', font_group=None, line_height=None, min_font_size=None, padding=None, cjk=CJK, latin=LATIN, overlap=None, reason=None):
        el = {'id': id, 'kind': 'text', 'z': self._z(), 'box': [int(round(v)) for v in box], 'text': text, 'font_size': size, 'font_family': latin, 'cjk_font_family': cjk,
              'bold': bold, 'color': color, 'align': align, 'valign': valign, 'wrap': wrap, 'fit': fit}
        if container: el['container'] = container
        if overlap: el['allow_overlap_with'] = overlap; el['overlap_reason'] = reason or 'visible in source'
        if font_group: el['font_group'] = font_group
        if line_height: el['line_height'] = line_height
        if min_font_size: el['min_font_size'] = min_font_size
        if padding: el['padding'] = padding
        self.els.append(el); return id

    def line(self, id, points, stroke=INK, width=3, arrow=False, head=None, dash=None, container=None, overlap=None, reason=None):
        el = {'id': id, 'kind': 'line', 'z': self._z(), 'points': [[int(round(x)), int(round(y))] for x, y in points], 'stroke': stroke, 'stroke_width': width}
        if container: el['container'] = container
        if overlap: el['allow_overlap_with'] = overlap; el['overlap_reason'] = reason or 'visible in source'
        if arrow:
            el['arrow'] = True
            if head: el['arrow_head'] = head
        if dash: el['dash'] = dash
        self.els.append(el); return id

    # ---- composites
    def card(self, id, box, title, sub=None, fill='#FFFFFF', stroke=PANEL_LINE, stroke_width=2, radius=14, dash=None, title_size=30, sub_size=22, title_color=INK, sub_color='#4A5158', bold=True, pad=16, gap=6, align='center', container=None):
        x, y, w, h = box
        self.shape(id, box, fill=fill, stroke=stroke, stroke_width=stroke_width, radius=radius, dash=dash, container=container)
        th = int(title_size * 1.35); sh = int(sub_size * 1.35 * (sub.count('\n') + 1)) if sub else 0
        tot = th + (gap + sh if sub else 0); ty = y + (h - tot) / 2
        self.text(id + '_t', [x + pad, ty, w - 2 * pad, th], title, title_size, bold=bold, color=title_color, align=align, container=id, font_group='card_title')
        if sub: self.text(id + '_s', [x + pad, ty + th + gap, w - 2 * pad, sh], sub, sub_size, color=sub_color, align=align, container=id, font_group='card_sub')
        return id

    def pill(self, id, cx, cy, text, size=20, fill='#FFFFFF', stroke=PANEL_LINE, color=INK, bold=False, padx=14, pady=6, stroke_width=1.5):
        tw = self.measure(text, size); w = tw + 2 * padx; h = int(size * 1.35) + 2 * pady
        box = [cx - w / 2, cy - h / 2, w, h]
        self.shape(id, box, fill=fill, stroke=stroke, stroke_width=stroke_width, radius=h / 2)
        self.text(id + '_t', [box[0] + padx, box[1] + pady, tw, h - 2 * pady], text, size, bold=bold, color=color, container=id, font_group='pill')
        return box

    @staticmethod
    def measure(text, size):
        # conservative width estimate: CJK ≈ 1.0 em, Latin/digits ≈ 0.62 em, spaces 0.3 em
        w = 0
        for ch in text:
            o = ord(ch)
            w += size * (1.0 if o > 0x2E80 else (0.3 if ch == ' ' else 0.62))
        return int(w) + 4

    def write(self, path, slide_id='page_001', reviewed=True):
        slide = {'id': slide_id, 'width': self.w, 'height': self.h, 'background': self.bg, 'reviewed': reviewed, 'elements': self.els}
        if self.source: slide['source'] = self.source
        if self.notes: slide['notes'] = self.notes
        doc = {'version': 1, 'fonts': {'latin': [LATIN, 'Liberation Sans'], 'cjk': [CJK, 'Noto Sans CJK JP', 'Droid Sans Fallback']}, 'slides': [slide]}
        Path(path).write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8'); return path
