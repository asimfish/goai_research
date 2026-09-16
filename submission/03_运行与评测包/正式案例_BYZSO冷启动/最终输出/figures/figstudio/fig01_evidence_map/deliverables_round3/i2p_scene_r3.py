"""Round-3 design-system builder for super_img2ppt scenes.

The round-3 figures share one visual system (tinted group zones + white cards with a header strip, a small line icon and
short item lines + thin connectors with pill labels). This module turns a declarative spec into native scene objects, so a
figure is described by its structure instead of by hand-placed boxes. Icons are exact crops of the generated raster.

Families: 'lit' (slate-blue, 文献证据), 'exp' (teal, 实验方法), 'note' (amber, 判断提醒), 'mute' (gray, excluded/reference-only).
"""
import math
from i2p_scene import Scene

FAM = {
    'lit':  {'zone': '#EEF2F7', 'edge': '#5B7592', 'text': '#2B3E57', 'strip': '#5B7592'},
    'exp':  {'zone': '#E6F2F3', 'edge': '#1F7F8C', 'text': '#0F4F58', 'strip': '#1F7F8C'},
    'note': {'zone': '#FFF6E3', 'edge': '#C48A24', 'text': '#7A5410', 'strip': '#C48A24'},
    'mute': {'zone': '#F5F6F7', 'edge': '#9AA3AB', 'text': '#5B6570', 'strip': '#9AA3AB'},
}
CONN = '#4B5563'; ITEM = '#3F4854'; RULE = '#DCE2E8'; CARD_FILL = '#FFFFFF'


class R3:
    """Wraps a Scene with design-system composites. All coordinates are source pixels."""

    def __init__(self, w, h, source=None, notes='', icon_src=None, job=None):
        self.sc = Scene(w, h, source=source, notes=notes)
        self.icon_src = icon_src   # PIL image of the generated raster, for exact icon crops
        self.job = job             # job dir (assets/ written here)
        self.w, self.h = w, h

    # ---------------------------------------------------------------- primitives
    def zone(self, zid, box, label=None, fam='lit', label_size=22, radius=16):
        f = FAM[fam]
        self.sc.shape(zid, box, fill=f['zone'], stroke=f['edge'], stroke_width=1.5, radius=radius)
        if label:
            x, y, w, h = box
            tw = Scene.measure(label, label_size) + 8
            self.sc.text(zid + '_l', [x + 18, y + 12, tw, int(label_size * 1.5)], label, label_size, bold=True,
                         color=f['text'], align='left', container=zid, font_group='zone')
        return zid

    def icon(self, iid, box, crop, container=None, provenance='exact crop of the generated raster (line motif)'):
        """Place an exact crop of the source raster as an image element (icons only)."""
        if not (self.icon_src and self.job and crop):
            return None
        x, y, w, h = [int(round(v)) for v in crop]
        self.icon_src.crop((x, y, x + w, y + h)).save(f'{self.job}/assets/{iid}.png')
        el = {'id': iid, 'kind': 'image', 'z': self.sc._z(), 'box': [int(round(v)) for v in box],
              'path': f'assets/{iid}.png', 'provenance': provenance, 'contains_text': False, 'image_fit': 'contain'}
        if container: el['container'] = container
        self.sc.els.append(el)
        return iid

    def card(self, cid, box, title, items=(), fam='lit', icon_crop=None, dashed=False, strip=True,
             title_size=28, item_size=21, icon_w=44, pad=16, rules=True, tag=None, tag_fam='note', tag_size=19,
             fill=CARD_FILL, container=None, title_only_center=False, item_gap=6, title_gap=8, tag_at='bottom', padx=None):
        """White card: optional 8 px header strip, icon + bold title, then short item lines separated by thin rules."""
        f = FAM[fam]; x, y, w, h = box
        strip = strip and not dashed   # a dashed (reference-only / excluded) card carries no solid header strip
        self.sc.shape(cid, box, fill=fill, stroke=f['edge'], stroke_width=1.5, radius=10,
                      dash=[13, 8] if dashed else None, container=container)
        if strip:
            self.sc.shape(cid + '_s', [x, y, w, 8], fill=f['strip'], stroke=None, radius=4, container=cid)
        padx = pad if padx is None else padx
        ty = y + (8 if strip else 0) + pad
        th = int(title_size * 1.5)
        tx = x + padx
        if icon_crop is not None:
            self.icon(cid + '_i', [tx, ty + (th - icon_w) / 2, icon_w, icon_w], icon_crop, container=cid)
            tx += icon_w + 12
        self.sc.text(cid + '_t', [tx, ty, x + w - padx - tx, th], title, title_size, bold=True, color=f['text'],
                     align='center' if title_only_center else 'left', container=cid, font_group='cardtitle',
                     fit='shrink', min_font_size=title_size - 6)
        iy = ty + th + title_gap
        ih = int(item_size * 1.55)
        for k, it in enumerate(items):
            if rules and k:
                self.sc.line(f'{cid}_r{k}', [(x + padx, iy - 4), (x + w - padx, iy - 4)], stroke=RULE, width=1, container=cid)
            self.sc.text(f'{cid}_k{k}', [x + padx, iy, w - 2 * padx, ih], it, item_size, color=ITEM, align='left',
                         container=cid, font_group='item', fit='shrink', min_font_size=item_size - 4)
            iy += ih + item_gap
        if tag:
            g = FAM[tag_fam]; tw = Scene.measure(tag, tag_size) + 30; thh = int(tag_size * 1.5) + 14
            bx = x + w - padx - tw
            by = (ty + (th - thh) / 2) if tag_at == 'title' else (y + h - 16 - thh + 4)
            self.sc.shape(cid + '_tg', [bx, by, tw, thh], fill=g['zone'], stroke=g['edge'], stroke_width=1.5,
                          radius=thh / 2, container=cid)
            self.sc.text(cid + '_tgt', [bx + 8, by + 4, tw - 16, thh - 8], tag, tag_size, bold=True, color=g['text'],
                         container=cid + '_tg', font_group='tag')
        return cid

    def pill(self, pid, cx, cy, text, size=20, fam=None, bold=False, padx=18, pady=7):
        """Small white pill with a thin border, used for connector labels."""
        f = FAM[fam] if fam else None
        tw = Scene.measure(text, size) + 2 * padx; th = int(size * 1.5) + 2 * pady
        box = [cx - tw / 2, cy - th / 2, tw, th]
        self.sc.shape(pid, box, fill=(f['zone'] if f else '#FFFFFF'), stroke=(f['edge'] if f else '#C6CCD1'),
                      stroke_width=1.2, radius=th / 2)
        self.sc.text(pid + '_t', [box[0] + padx - 6, box[1] + pady - 2, tw - 2 * padx + 12, th - 2 * pady + 4], text, size, bold=bold,
                     color=(f['text'] if f else ITEM), container=pid, font_group='pilllabel')
        return box

    def conn(self, cid, pts, dashed=False, arrow=True, width=2, color=CONN, label=None, label_at=None,
             label_size=20, label_fam=None, head=None, label_split=True):
        """Polyline connector (elbows allowed). Segments are separate lines with declared joints; optional label pill
        placed at `label_at` (x, y) — the segment crossing the pill is split so the label sits on a clean gap."""
        ids = []
        pts = [(float(a), float(b)) for a, b in pts]
        segs = list(zip(pts[:-1], pts[1:]))
        pbox = None
        if label:
            lx, ly = label_at if label_at else segs[len(segs) // 2][0]
            pbox = self.pill(cid + '_p', lx, ly, label, size=label_size, fam=label_fam)
        n = 0
        for (p0, p1) in segs:
            last = (p0, p1) == segs[-1]
            parts = [(p0, p1)]
            if pbox and label_split:  # split this segment around the pill when it passes through it
                bx, by, bw, bh = pbox
                if p0[1] == p1[1] and by - 4 <= p0[1] <= by + bh + 4 and min(p0[0], p1[0]) < bx and max(p0[0], p1[0]) > bx + bw:
                    lo, hi = (p0, p1) if p0[0] < p1[0] else (p1, p0)
                    parts = [(lo, (bx - 4, lo[1])), ((bx + bw + 4, lo[1]), hi)]
                    if p0[0] > p1[0]: parts = [((bx - 4, lo[1]), lo), (hi, (bx + bw + 4, lo[1]))]
                elif p0[0] == p1[0] and bx - 4 <= p0[0] <= bx + bw + 4 and min(p0[1], p1[1]) < by and max(p0[1], p1[1]) > by + bh:
                    lo, hi = (p0, p1) if p0[1] < p1[1] else (p1, p0)
                    parts = [(lo, (lo[0], by - 4)), ((lo[0], by + bh + 4), hi)]
                    if p0[1] > p1[1]: parts = [((lo[0], by - 4), lo), (hi, (lo[0], by + bh + 4))]
            for q0, q1 in parts:
                sid = f'{cid}_{n}'; n += 1
                is_tip = last and arrow and (q1 == p1)
                self.sc.line(sid, [q0, q1], stroke=color, width=width, dash=[12, 8] if dashed else None,
                             arrow=is_tip, head=(head or {'length': 13, 'width': 11}) if (is_tip and not dashed) else None)
                ids.append(sid)
        if pbox and not label_split:  # the pill sits on top of the unbroken connector, as in the source
            for el in self.sc.els:
                if el['id'] in ids or el['id'] in (cid + '_p', cid + '_p_t'):
                    mates = [i for i in ids + [cid + '_p'] if i != el['id']]
                    el['allow_overlap_with'] = sorted(set(el.get('allow_overlap_with', []) + mates))
                    el['overlap_reason'] = 'label pill drawn over its connector, visible in source'
        # declare the joints between consecutive segments
        for el in self.sc.els:
            if el['id'] in ids:
                el['allow_overlap_with'] = sorted(set(el.get('allow_overlap_with', []) + [i for i in ids if i != el['id']]))
                el['overlap_reason'] = 'connector joints, visible in source'
        return ids

    def axis(self, aid, x, y0, y1, near='近', far='远', label=None, size=20, color=ITEM, container=None, label_x=None):
        """Vertical distance axis: an up arrow, a down arrow, end marks and an optional rotated label."""
        mid = (y0 + y1) / 2
        self.sc.line(aid + '_u', [(x, mid - 44), (x, y0 + 26)], stroke=color, width=2, arrow=True, head={'length': 12, 'width': 10}, container=container)
        self.sc.line(aid + '_d', [(x, mid + 44), (x, y1 - 26)], stroke=color, width=2, arrow=True, head={'length': 12, 'width': 10}, container=container)
        self.sc.text(aid + '_n', [x - 24, y0 - 6, 48, 30], near, size, bold=True, color=color, container=container)
        self.sc.text(aid + '_f', [x - 24, y1 - 24, 48, 30], far, size, bold=True, color=color, container=container)
        if label:
            lw = Scene.measure(label, size) + 12; lh = int(size * 1.5)
            lx = label_x if label_x is not None else x
            self.sc.text(aid + '_l', [lx - lw / 2, mid - lh / 2, lw, lh], label, size, color=color, rotation=-90,
                         font_group='axis', container=container)
        return aid

    @staticmethod
    def _bbox(el):
        if el['kind'] == 'line':
            xs = [p[0] for p in el['points']]; ys = [p[1] for p in el['points']]
            w = el.get('stroke_width', 2)
            return [min(xs) - w, min(ys) - w, max(xs) + w, max(ys) + w]
        x, y, w, h = el['box']; return [x, y, x + w, y + h]

    def joints(self, max_area=260):
        """Declare the small intersections where separate connector polylines meet as joints."""
        lines = [e for e in self.sc.els if e['kind'] == 'line']
        for i, a in enumerate(lines):
            ba = self._bbox(a)
            for b in lines[i + 1:]:
                bb = self._bbox(b)
                ox = min(ba[2], bb[2]) - max(ba[0], bb[0]); oy = min(ba[3], bb[3]) - max(ba[1], bb[1])
                if ox > 0 and oy > 0 and ox * oy <= max_area:
                    for x, y in ((a, b), (b, a)):
                        x['allow_overlap_with'] = sorted(set(x.get('allow_overlap_with', []) + [y['id']]))
                        x['overlap_reason'] = 'connector joints, visible in source'

    def label_overlaps(self, reason='connector label pill sits on the connector between two cards, visible in source'):
        """Declare the small intentional overlaps where a connector's label pill meets the cards it runs between."""
        pills = [e for e in self.sc.els if e['id'].endswith('_p') or e['id'].endswith('_p_t')]
        others = [e for e in self.sc.els if (e['kind'] in ('shape', 'line')) and not e['id'].endswith('_p')]
        for a in pills:
            ba = self._bbox(a)
            for b in others:
                if a['id'].startswith(b['id']): continue
                bb = self._bbox(b)
                if ba[0] < bb[2] and ba[2] > bb[0] and ba[1] < bb[3] and ba[3] > bb[1]:
                    for x, y in ((a, b), (b, a)):
                        x['allow_overlap_with'] = sorted(set(x.get('allow_overlap_with', []) + [y['id']]))
                        x['overlap_reason'] = reason

    def cross(self, zone_ids):
        """Declare mutual overlap between the group zones and any element that visibly crosses them without being
        declared as their child (connectors and their label pills routed between zones)."""
        zones = {e['id']: self._bbox(e) for e in self.sc.els if e['id'] in zone_ids}
        parent = {e['id']: e.get('container') for e in self.sc.els}

        def root(i, depth=0):
            while parent.get(i) and depth < 8:
                i = parent[i]; depth += 1
            return i
        for el in self.sc.els:
            if el['id'] in zone_ids or root(el['id']) in zone_ids:
                continue
            b = self._bbox(el)
            for zid, zb in zones.items():
                if b[0] < zb[2] and b[2] > zb[0] and b[1] < zb[3] and b[3] > zb[1]:
                    el['allow_overlap_with'] = sorted(set(el.get('allow_overlap_with', []) + [zid]))
                    el['overlap_reason'] = 'connector routed across the group zones, visible in source'
                    for z in self.sc.els:
                        if z['id'] == zid:
                            z['allow_overlap_with'] = sorted(set(z.get('allow_overlap_with', []) + [el['id']]))
                            z['overlap_reason'] = 'connectors and labels drawn over the group zone, visible in source'

    def write(self, path):
        return self.sc.write(path)
