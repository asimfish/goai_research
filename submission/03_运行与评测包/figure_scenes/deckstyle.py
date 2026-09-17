"""Deck style — native building blocks for talk slides in the loop-engineering look (ARIS /method-figure palette).

The paper design system (lib.Figure) is deliberately restrained; a talk slide is a different medium. This module keeps
the same guarantees (every text/box/arrow is a native, editable object; sizes are declared in slide points) and adds
what the medium needs:

  panel()   numbered pastel phase panel with a bold coloured title
  card()    white node card with a soft offset shadow, bold title + one grey line, optional art on the left
  flow()    connector by KIND — main (thick navy) / keep (green) / retry (bold orange) / dispatch (blue dashed) /
            write (thin grey) / escalate (red dashed); one colour per meaning, mirrored in legend()
  arc()     a curved connector sampled into short segments (img2ppt lines are two-point), the hero RETRY loop
  tag()     label pill that sits on a connector, tinted by kind
  legend()  the arrow kinds, drawn with the same strokes
  stat()    evidence tile: a big number + a caption (KPI strip / round cards)
  art()     raster illustration cropped from the picked image-model figure (characters, thumbnails) — kept as an
            independent picture asset so PowerPoint users can move or delete it

Canvas: 1536×864 px = one 16:9 page at img2ppt's 960 pt (0.625 pt/px). Sizes below are px with the slide pt in comments.
"""
import math
import sys
import pathlib

_REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / 'skills' / 'goai-figure-studio'))
from lib import Scene  # noqa: E402

PT = 0.625                                     # slide pt per px
SZ = dict(headline=32, panel=27, title=23, line=17, tag=17, legend=16, big=54, cap=16, mono=15)   # 20/17/14.5/10.5/…/34 pt
INK, MUTED, NAVY, NODE_STROKE, SHADOW = '#1F2937', '#6B7280', '#1F2A44', '#CBD2DC', '#E4E9F0'
TONE = dict(
    blue=dict(fill='#E8F1FD', stroke='#9DBDEB', accent='#2563EB', text='#1D4ED8'),
    green=dict(fill='#E3F6EA', stroke='#9BD9B0', accent='#0E9F6E', text='#0B7A55'),
    violet=dict(fill='#EFEBFE', stroke='#C4B5FD', accent='#7C3AED', text='#5B21B6'),
    peach=dict(fill='#FDEEDD', stroke='#F4C18A', accent='#EA580C', text='#C2410C'),
    amber=dict(fill='#FEF3C7', stroke='#FCD34D', accent='#D97706', text='#B45309'),
    red=dict(fill='#FDE8E8', stroke='#F5A3A3', accent='#DC2626', text='#B91C1C'),
    grey=dict(fill='#F3F4F6', stroke='#D1D5DB', accent='#6B7280', text='#4B5563'),
)
KIND = dict(
    main=dict(color=NAVY, width=5, head={'length': 20, 'width': 17}),
    keep=dict(color=TONE['green']['accent'], width=5, head={'length': 20, 'width': 17}),
    retry=dict(color=TONE['peach']['accent'], width=6, head={'length': 24, 'width': 20}),
    dispatch=dict(color=TONE['blue']['accent'], width=3, dash=[10, 7]),
    write=dict(color='#9CA3AF', width=2, head={'length': 12, 'width': 10}),
    escalate=dict(color=TONE['red']['accent'], width=3, dash=[10, 7]),
)
TAG_TONE = dict(main='grey', keep='green', retry='peach', dispatch='blue', write='grey', escalate='red')


class Deck:
    def __init__(self, notes=''):
        self.sc = Scene(1536, 864, notes=f'{notes} [deck style; slide 16:9; pt_per_px={PT}]')
        self.panels, self.tags = [], []

    # ------------------------------------------------------------------ containers
    def panel(self, pid, box, title, tone, bar=True):
        """Phase panel. bar=True puts the numbered title in a solid header bar (white on the panel's accent)."""
        t = TONE[tone]
        self.sc.shape(pid, box, fill=t['fill'], stroke=t['stroke'], stroke_width=2, radius=20)
        x, y, w, h = box
        if bar:
            self.sc.shape(pid + '_b', [x + 8, y + 8, w - 16, 40], fill=t['accent'], radius=14, container=pid)
            self.sc.text(pid + '_l', [x + 24, y + 8, w - 48, 40], title, SZ['panel'] - 2, bold=True, color='#FFFFFF', align='left',
                         container=pid + '_b')
        else:
            self.sc.text(pid + '_l', [x + 18, y + 10, Scene.measure(title, SZ['panel'], True) + 8, int(SZ['panel'] * 1.6)], title,
                         SZ['panel'], bold=True, color=t['text'], align='left', container=pid)
        self.panels.append(pid)
        return pid

    def card(self, cid, box, title, line=None, tone='blue', container=None, art=None, art_w=0, stroke=None, title_size=None,
             align='left'):
        """White card + soft shadow. art=(path, provenance) puts a picture in a square slot on the left."""
        x, y, w, h = box
        self.sc.shape(cid + '_sh', [x + 2, y + 5, w, h], fill=SHADOW, radius=14, container=container,
                      overlap=[cid], reason='soft offset shadow under the card, decoration only')
        self.sc.els[-1]['role'] = 'decoration'
        self.sc.shape(cid, box, fill='#FFFFFF', stroke=stroke or NODE_STROKE, stroke_width=1.8, radius=14, container=container,
                      overlap=[cid + '_sh'], reason='card sits on its own soft shadow')
        tx, tw = x + 14, w - 28
        if art:
            self.art(cid + '_art', [x + 10, y + (h - art_w) / 2, art_w, art_w], art[0], art[1], container=cid)
            tx, tw = x + 10 + art_w + 10, w - art_w - 34
        ts = title_size or SZ['title']
        th, lh = int(ts * 1.5), int(SZ['line'] * 1.55)
        block = th + (lh + 2 if line else 0)
        ty = y + (h - block) / 2
        if title:
            self.sc.text(cid + '_t', [tx, ty, tw, th], title, ts, bold=True, color=INK, align=align, container=cid,
                         fit='shrink', min_font_size=ts - 4)
        if line:
            self.sc.text(cid + '_s', [tx, ty + th + 2, tw, lh], line, SZ['line'], color=MUTED, align=align, container=cid,
                         fit='shrink', min_font_size=SZ['line'] - 3)
        return cid

    def diamond(self, did, cx, cy, w, h, title, tone='amber', container=None):
        """Decision node. Only a short title fits: the text box is the diamond's inscribed rectangle (half its size)."""
        t = TONE[tone]
        self.sc.shape(did, [cx - w / 2, cy - h / 2, w, h], shape='diamond', fill=t['fill'], stroke=t['accent'], stroke_width=2.4,
                      container=container)
        self.sc.text(did + '_t', [cx - w / 4 + 2, cy - h / 4 + 2, w / 2 - 4, h / 2 - 4], title, SZ['title'], bold=True, color=INK,
                     container=did, fit='shrink', min_font_size=SZ['title'] - 5)
        return did

    # ------------------------------------------------------------------ connectors
    def _seg(self, sid, p0, p1, k, arrow):
        kw = dict(stroke=k['color'], width=k['width'])
        if k.get('dash'):
            self.sc.line(sid, [p0, p1], arrow=arrow, dash=k['dash'], **kw)
        else:
            head = k.get('head') if arrow else None
            if head:
                # img2ppt refuses a head that is not shorter than its segment: fit the head to a short segment
                seg = math.dist(p0, p1)
                if head['length'] > seg - 3:
                    f = max(0.3, (seg - 3) / head['length'])
                    head = {'length': max(5.0, round(head['length'] * f, 1)), 'width': max(k['width'] + 1.0, round(head['width'] * f, 1))}
            self.sc.line(sid, [p0, p1], arrow=arrow, head=head, **kw)

    def flow(self, fid, pts, kind='main', arrow=True):
        k = KIND[kind]
        pts = [(float(a), float(b)) for a, b in pts]
        for i, (p0, p1) in enumerate(zip(pts[:-1], pts[1:])):
            self._seg(f'{fid}_{i}', p0, p1, k, arrow and i == len(pts) - 2)
        return fid

    def arc(self, aid, p0, p1, bulge, kind='retry', n=18):
        """Quadratic curve p0→p1 bowed by `bulge` px (perpendicular, + = to the left of the direction of travel),
        sampled into n segments; the last one is kept long enough for its arrow head."""
        k = KIND[kind]
        (x0, y0), (x1, y1) = p0, p1
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        d = math.hypot(dx, dy) or 1
        cx, cy = mx - dy / d * bulge, my + dx / d * bulge
        pts = []
        for i in range(n + 1):
            t = i / n
            pts.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1))
        need = (k.get('head') or {'length': 16})['length'] + 8
        while len(pts) > 2 and math.dist(pts[-2], pts[-1]) < need:
            pts.pop(-2)
        for i, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
            self._seg(f'{aid}_{i}', a, b, k, i == len(pts) - 2)
        return pts

    def ubend(self, uid, p0, p3, depth, kind='retry', n=22, depth2=None):
        """U-shaped loop: leaves p0 straight down, returns into p3 straight up (cubic, control points `depth` px below each
        end), sampled into segments; the last one is kept long enough for its arrow head. depth < 0 bends upward."""
        k = KIND[kind]
        (x0, y0), (x3, y3) = p0, p3
        c1, c2 = (x0, y0 + depth), (x3, y3 + (depth if depth2 is None else depth2))
        pts = []
        for i in range(n + 1):
            t = i / n
            u = 1 - t
            pts.append((u ** 3 * x0 + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * x3,
                        u ** 3 * y0 + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * y3))
        need = (k.get('head') or {'length': 16})['length'] + 8
        while len(pts) > 2 and math.dist(pts[-2], pts[-1]) < need:
            pts.pop(-2)
        for i, (a, b) in enumerate(zip(pts[:-1], pts[1:])):
            self._seg(f'{uid}_{i}', a, b, k, i == len(pts) - 2)
        return pts

    def tag(self, tid, cx, cy, text, kind='main', bold=True, size=None):
        t = TONE[TAG_TONE[kind]]
        size = size or SZ['tag']
        w, h = Scene.measure(text, size, bold) + 28, int(size * 1.5) + 12
        self.sc.shape(tid, [cx - w / 2, cy - h / 2, w, h], fill='#FFFFFF', stroke=t['accent'], stroke_width=1.8, radius=h / 2)
        self.sc.text(tid + '_t', [cx - w / 2 + 10, cy - h / 2 + 5, w - 20, h - 10], text, size, bold=bold, color=t['text'], container=tid)
        self.tags.append(tid)
        return [cx - w / 2, cy - h / 2, w, h]

    # ------------------------------------------------------------------ evidence + legend + art
    def stat(self, sid, box, big, caption, tone='blue', head=None, art=None, art_w=64):
        """Evidence tile: optional small head line, a big number, a caption."""
        t = TONE[tone]
        x, y, w, h = box
        self.sc.shape(sid + '_sh', [x + 2, y + 5, w, h], fill=SHADOW, radius=14, overlap=[sid], reason='soft offset shadow, decoration only')
        self.sc.els[-1]['role'] = 'decoration'
        self.sc.shape(sid, box, fill=t['fill'], stroke=t['accent'], stroke_width=2, radius=14, overlap=[sid + '_sh'],
                      reason='tile sits on its own soft shadow')
        yy = y + 8
        if head:
            hh = int(SZ['cap'] * 1.5)
            self.sc.text(sid + '_h', [x + 12, yy, w - 24, hh], head, SZ['cap'], bold=True, color=t['text'], container=sid)
            yy += hh
        bh = int(SZ['big'] * 1.32)
        ch = h - (yy - y) - bh - 8
        if art:      # number on the left half, a small illustration on the right half
            self.sc.text(sid + '_b', [x + 8, yy, w * 0.56 - 8, bh], big, SZ['big'], bold=True, color=t['accent'], container=sid)
            self.art(sid + '_art', [x + w * 0.58, yy + (bh - art_w) / 2, art_w, art_w], art[0], art[1], container=sid)
        else:
            self.sc.text(sid + '_b', [x + 8, yy, w - 16, bh], big, SZ['big'], bold=True, color=t['accent'], container=sid)
        self.sc.text(sid + '_c', [x + 10, yy + bh, w - 20, ch], caption, SZ['cap'], color=INK, container=sid, wrap=True,
                     fit='shrink', min_font_size=SZ['cap'] - 3, valign='top')
        return sid

    def legend(self, lid, box, items, title='图例'):
        x, y, w, h = box
        self.sc.shape(lid, box, fill='#FFFFFF', stroke=NAVY, stroke_width=1.8, radius=12)
        th = int(SZ['legend'] * 1.6)
        top = y + 8
        if title:
            self.sc.text(lid + '_t', [x + 14, top, w - 28, th], title, SZ['legend'], bold=True, color=INK, align='left', container=lid)
            top += th
        row = (y + h - 8 - top) / len(items)
        for i, (kind, label) in enumerate(items):
            yy = top + row * (i + 0.5)
            k = KIND[kind]
            self._seg(f'{lid}_k{i}', (x + 16, yy), (x + 76, yy), k, True)
            self.sc.els[-1]['container'] = lid
            self.sc.text(f'{lid}_l{i}', [x + 88, yy - th / 2, w - 100, th], label, SZ['legend'], color=INK, align='left', container=lid)
        return lid

    def art(self, aid, box, path, provenance, container=None):
        el = {'id': aid, 'kind': 'image', 'z': self.sc._z(), 'box': [int(round(v)) for v in box], 'path': path,
              'image_fit': 'contain', 'provenance': provenance, 'contains_text': False}
        if container:
            el['container'] = container
        self.sc.els.append(el)
        return aid

    def headline(self, claim, number=None, x=44, y=126):
        w = Scene.measure(claim, SZ['headline'], True) + 8
        self.sc.text('hl', [x, y, w, int(SZ['headline'] * 1.5)], claim, SZ['headline'], bold=True, color=NAVY, align='left')
        if number:
            self.sc.text('hl_n', [x + w + 18, y + 4, Scene.measure(number, SZ['title'], True) + 8, int(SZ['headline'] * 1.5) - 4], number,
                         SZ['title'], bold=True, color=TONE['peach']['accent'], align='left')

    # ------------------------------------------------------------------ finish
    def finish(self):
        """Declare the intended overlaps: connectors cross panels and meet at joints; tags sit on connectors and panels."""
        els = self.sc.els
        lines = [e for e in els if e['kind'] == 'line']
        under = set(self.panels)

        def allow(a, ids, why):
            a['allow_overlap_with'] = sorted(set(a.get('allow_overlap_with', [])) | set(ids))
            a.setdefault('overlap_reason', why)
        for ln in lines:
            allow(ln, list(under) + [o['id'] for o in lines if o is not ln], 'connectors cross phase panels and join each other')
        tagset = set(self.tags) | {t + '_t' for t in self.tags}
        for e in els:
            if e['id'] in tagset:
                allow(e, list(under) + [ln['id'] for ln in lines], 'label pill sits on its connector over the panel tint')
        for ln in lines:
            allow(ln, list(tagset), 'connector passes under its own label pill')
        # a card's soft shadow lies under everything the card contains
        parent = {e['id']: e.get('container') for e in els}

        def inside(i, root):
            while i:
                if i == root:
                    return True
                i = parent.get(i)
            return False
        for e in els:
            if e['id'].endswith('_sh'):
                root = e['id'][:-3]
                allow(e, [o['id'] for o in els if o is not e and inside(o['id'], root)], 'soft offset shadow under the card')
                allow(e, [ln['id'] for ln in lines], 'connectors start and end at the card edge, over its shadow')
        for e in els:
            if e['id'] in under:
                allow(e, [ln['id'] for ln in lines] + list(tagset), 'phase panel is a backdrop for connectors and their labels')

    def write(self, path):
        self.finish()
        self.sc.write(str(path))
        print('wrote', path, f'({len(self.sc.els)} elements)')
