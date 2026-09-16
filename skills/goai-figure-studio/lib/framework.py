"""The four-tier framework builder: the hierarchy the figure-studio policies ask for, as native scene objects.

Tier 1 macro group  -> `zone()`      light tint, hairline border, small group label
Tier 2 primary module -> `module()`  white card, 6 px accent bar, one line-art glyph, bold title
Tier 3 internal mechanism -> `chain()` / `ledger()` inside the card: small tokens joined by short arrows, or a
                                       record grid with tick marks — never a bulleted list of sentences
Tier 4 labels -> `conn(label=...)` / `tag()`: variables, record items and caveats ride on connectors, ports and tags

References: academic-framework-hierarchy-and-asset-mirroring-policy-v3210 (tiers, artifact-as-block guard,
connector bundling), core-submodule-detail-policy-v313 (visible internal mechanism, main-flow dominance),
edge-label-first-and-internal-motif-policy-v3211 (labels before boxes).
"""
import math
import re
from collections import Counter
from .scene import Scene
from .motifs import Motifs

FAM = {
    'lit':  {'zone': '#EEF2F7', 'edge': '#5B7592', 'text': '#2B3E57', 'accent': '#5B7592'},
    'exp':  {'zone': '#E6F2F3', 'edge': '#1F7F8C', 'text': '#0F4F58', 'accent': '#1F7F8C'},
    'note': {'zone': '#FFF6E3', 'edge': '#C48A24', 'text': '#7A5410', 'accent': '#C48A24'},
    'mute': {'zone': '#F5F6F7', 'edge': '#9AA3AB', 'text': '#5B6570', 'accent': '#9AA3AB'},
}
CONN = '#3C4753'; ITEM = '#27303A'; HAIR = '#CBD5DE'; TOKEN_EDGE = '#AEBBC7'; TOKEN_FILL = '#F4F7FA'; INK = '#111A24'
# one step heavier than the print-hairline weights the first rounds used: the PPTX and the on-screen PDF
# both read washed out at 1.2-1.8 px with regular-weight body text.
W_ZONE, W_CARD, W_TOKEN, W_CONN, W_STEP, W_PILL, W_RULE = 1.6, 1.9, 1.6, 2.5, 2.2, 1.6, 1.6
HEAD = {'length': 15, 'width': 12}

# Type scale in PRINTED points, one size per role. A figure that declares its printed width gets its px sizes
# from here, so every figure in every paper sets the same role at the same size on paper.
#   body 8 pt sits a step under the 9 pt caption; nothing prints below MIN_PRINT_PT.
TYPE_PT = {'group': 9.5, 'title': 9.0, 'number': 12.0, 'body': 8.0, 'label': 7.5}
# Latin needs less than CJK to stay legible (CJK strokes are dense; Nature sets figure text at 5–7 pt),
# and English runs ~1.6x wider, so English figures use a scale one step down — still one scale for every figure.
TYPE_PT_EN = {'group': 8.5, 'title': 8.0, 'number': 11.0, 'body': 7.0, 'label': 7.0}
MIN_PRINT_PT = 7.0
# Two weights only. Bold marks structure (group, card title, step number); everything read as content is
# regular. Making every string bold (round 5) erased the difference between a heading and the text under it.
BOLD_ROLES = {'group', 'title', 'number'}
PRINT_TAG = re.compile(r'\[print_width_pt=([\d.]+)\]')



def pack_pill_rows(els, page_w, gap=12, band=64, margin=6):
    """De-collide a row of connector labels.

    Each `conn(label=...)` places its pill on its own, so a row of them can collide or run off the page once the
    text grows (a longer term, or the English pass). Cluster the pills of one connector family into rows, put every
    member back on the row's dominant y — a label that had been pushed down into the next band comes back up — then
    shift them horizontally, in order, until none overlaps and all are on the page.
    """
    by = {e['id']: e for e in els}
    pills = [e for e in els if e['kind'] == 'shape' and e['id'].endswith('_p') and e['id'] + '_t' in by]
    fams = {}
    for e in pills:
        fams.setdefault(re.sub(r'\d+$', '', e['id'][:-2]), []).append(e)
    for members in fams.values():
        members.sort(key=lambda e: e['box'][1])
        rows = [[members[0]]]
        for e in members[1:]:
            if e['box'][1] - rows[-1][-1]['box'][1] <= band:
                rows[-1].append(e)
            else:
                rows.append([e])
        for row in rows:
            if len(row) < 2:
                continue
            y = Counter(e['box'][1] for e in row).most_common(1)[0][0]
            row.sort(key=lambda e: e['box'][0] + e['box'][2] / 2)
            w = [e['box'][2] for e in row]
            if sum(w) + gap * (len(row) - 1) > page_w - 2 * margin:
                continue          # the row cannot hold them all; leave the author's placement alone
            x = [e['box'][0] for e in row]
            for i in range(len(row)):
                x[i] = max(x[i], margin if i == 0 else x[i - 1] + w[i - 1] + gap)
            for i in range(len(row) - 1, -1, -1):
                x[i] = min(x[i], page_w - margin - w[i] if i == len(row) - 1 else x[i + 1] - w[i] - gap)
            for e, nx in zip(row, x):
                dx, dy = int(round(nx)) - e['box'][0], y - e['box'][1]
                t = by[e['id'] + '_t']
                e['box'][0] += dx
                e['box'][1] += dy
                t['box'][0] += dx
                t['box'][1] += dy


class Framework:
    def __init__(self, w, h, source=None, notes='', print_width_pt=None, crop_px=24, type_scale=None):
        # print_width_pt: the width the figure is printed at (\\linewidth of the paper). With it, sizes come from
        # TYPE_PT and body text is regular; without it (round-5 scenes) the literal sizes and all-bold remain.
        # crop_px: install_fig crops the render to its content plus a margin, so the printed width maps onto
        # roughly the canvas less this much.
        self.print_width_pt = print_width_pt
        if print_width_pt:
            self.pt_per_px = print_width_pt / (w - crop_px)
            self.floor_px = math.ceil(MIN_PRINT_PT / self.pt_per_px - 1e-9)
            # rounding must never take a role below the printed floor
            self.T = {role: max(int(round(pt / self.pt_per_px)), self.floor_px)
                      for role, pt in (type_scale or TYPE_PT).items()}
            notes = f'{notes} [print_width_pt={print_width_pt:g}]'.strip()
        else:
            self.pt_per_px, self.T, self.floor_px = None, None, None
        self.sc = Scene(w, h, source=source, notes=notes)
        self.pills = []
        self.m = Motifs(self.sc, ink=INK, width=2.7)
        self.w, self.h = w, h

    # ------------------------------------------------------------------ type scale
    def size(self, role, legacy=None):
        """px size for a role — from the printed type scale when the figure declares its print width."""
        return self.T[role] if self.T else legacy

    def bold(self, role):
        return role in BOLD_ROLES if self.T else True

    def shrink_floor(self, size, drop):
        """Smallest size fit=shrink may reach: never below the printed floor once a print width is known."""
        return max(size - drop, self.floor_px) if self.floor_px else size - drop

    # ------------------------------------------------------------------ tier 1
    def zone(self, zid, box, label=None, fam='lit', label_size=None, label_pos='top'):
        label_size = label_size or self.size('group', 21)
        f = FAM[fam]
        self.sc.shape(zid, box, fill=f['zone'], stroke=f['edge'], stroke_width=W_ZONE, radius=14)
        if label:
            x, y, w, h = box
            tw = Scene.measure(label, label_size) + 26; lh = int(label_size * 1.6) + 4
            ly = y + 10 if label_pos == 'top' else y + h - 10 - lh
            extra = {}
            if self.T and tw > w - 36:          # a long (English) label must stay inside its zone
                tw = w - 36
                extra = dict(fit='shrink', min_font_size=self.floor_px)
            self.sc.text(zid + '_l', [x + 18, ly, tw, lh], label, label_size, bold=True,
                         color=f['text'], align='left', container=zid, font_group='zone', **extra)
        return zid

    # ------------------------------------------------------------------ tier 2
    def module(self, cid, box, title, fam='lit', glyph=None, dashed=False, accent=True, title_size=None,
               pad=14, padx=None, container=None, tag=None, tag_fam='note', tag_size=18, glyph_w=34,
               title_align='left', glyph_above=False, tag_at='bottom', title_valign='top'):
        title_size = title_size or self.size('title', 26)
        tag_size = self.size('label', tag_size) if self.T else tag_size
        f = FAM[fam]; x, y, w, h = box
        padx = pad if padx is None else padx
        accent = accent and not dashed
        self.sc.shape(cid, box, fill='#FFFFFF', stroke=f['edge'], stroke_width=W_CARD, radius=9,
                      dash=[12, 8] if dashed else None, container=container)
        if accent:
            self.sc.shape(cid + '_a', [x, y, w, 6], fill=f['accent'], stroke=None, radius=3, container=cid)
        th = int(title_size * 1.45)
        gh = (glyph_w + 10) if (glyph and glyph_above) else 0
        ty = (y + (6 if accent else 0) + pad if title_valign == 'top'
              else y + (6 if accent else 0) + (h - (6 if accent else 0) - th - gh) / 2)
        tx = x + padx
        tw_avail = w - 2 * padx
        if glyph and glyph_above:
            self.m.draw(glyph, cid + '_g', [x + (w - glyph_w) / 2, ty, glyph_w, glyph_w], container=cid)
            ty += glyph_w + 10
            title_align = 'center'
        elif glyph:
            self.m.draw(glyph, cid + '_g', [tx, ty + (th - glyph_w) / 2, glyph_w, glyph_w], container=cid)
            tx += glyph_w + 10; tw_avail = x + w - padx - tx
        if tag and tag_at == 'title':
            tw_avail -= Scene.measure(tag, tag_size) + 34
        self.sc.text(cid + '_t', [tx, ty, tw_avail, th], title, title_size, bold=True, color=f['text'],
                     align=title_align, container=cid, font_group='modtitle', fit='shrink',
                     min_font_size=self.shrink_floor(title_size, 5))
        if tag:
            g = FAM[tag_fam]; tw = Scene.measure(tag, tag_size) + 26; thh = int(tag_size * 1.5) + 12
            bx = x + w - padx - tw
            by = ty + (th - thh) / 2 if tag_at == 'title' else y + h - 12 - thh
            self.sc.shape(cid + '_tg', [bx, by, tw, thh], fill=g['zone'], stroke=g['edge'], stroke_width=W_PILL,
                          radius=thh / 2, container=cid)
            self.sc.text(cid + '_tgt', [bx + 8, by + 4, tw - 16, thh - 8], tag, tag_size, bold=self.bold('label'),
                         color=g['text'],
                         container=cid + '_tg', font_group='tag')
        return ty + th + 10   # y where the internal mechanism may start

    # ------------------------------------------------------------------ tier 3
    def token(self, tid, box, text, size=None, container=None, fam=None, strong=False, align='center', wrap=False):
        size = size or self.size('body', 19)
        f = FAM[fam] if fam else None
        self.sc.shape(tid, box, fill=(f['zone'] if f else TOKEN_FILL), stroke=(f['edge'] if f else TOKEN_EDGE),
                      stroke_width=W_TOKEN, radius=6, container=container)
        # regular weight once sizes follow the printed scale (strong=True keeps an outcome token bold);
        # round-5 scenes stay all-bold
        self.sc.text(tid + '_t', [box[0] + 7, box[1] + 4, box[2] - 14, box[3] - 8], text, size,
                     bold=(True if (strong and self.T) else self.bold('body')),
                     color=(f['text'] if f else ITEM), container=tid, font_group='token', fit='shrink',
                     min_font_size=self.shrink_floor(size, 4), align=align, wrap=wrap)
        return tid

    def vstack(self, cid, box, items, container=None, size=None, gap=12, fam=None, strong_last=False):
        """Vertical stack of record tokens filling the box — the module's recorded items."""
        size = size or self.size('body', 19)
        x, y, w, h = box; n = len(items); th = (h - gap * (n - 1)) / n
        return [self.token(f'{cid}_t{k}', [x, y + k * (th + gap), w, th], t, size=size, container=container,
                           fam=(fam if (strong_last and k == n - 1) else None), strong=(strong_last and k == n - 1))
                for k, t in enumerate(items)]

    def vchain(self, cid, box, steps, container=None, size=None, gap=20):
        """Vertical mini-chain: tokens joined by short down arrows — input → operation → output."""
        size = size or self.size('body', 19)
        x, y, w, h = box; n = len(steps); th = (h - gap * (n - 1)) / n
        ids = []
        for k, s in enumerate(steps):
            ty = y + k * (th + gap)
            ids.append(self.token(f'{cid}_t{k}', [x, ty, w, th], s, size=size, container=container))
            if k:
                # the previous token's box was rounded on its own, so take its real edge rather than ty - gap
                ay0 = int(round(y + (k - 1) * (th + gap))) + int(round(th)) + 3; ay1 = int(round(ty)) - 3
                hl = max(4.0, min(9.0, (ay1 - ay0) * 0.55))
                self.sc.line(f'{cid}_a{k}', [(x + w / 2, ay0), (x + w / 2, ay1)], stroke=CONN, width=W_STEP,
                             arrow=True, head={'length': hl, 'width': max(4.0, hl * 0.9)}, container=container)
        return ids

    def chain(self, cid, box, steps, container=None, size=None, gap=20, outcome=None, outcome_fam=None, height=None):
        """Horizontal mini-chain: tokens joined by short arrows — the module's input → operation → output."""
        size = size or self.size('body', 19)
        x, y, w, h = box; th = height or h
        items = list(steps) + ([outcome] if outcome else [])
        n = len(items)
        tw = (w - gap * (n - 1)) / n
        ids = []
        for k, s in enumerate(items):
            tx = x + k * (tw + gap)
            last = outcome and k == n - 1
            ids.append(self.token(f'{cid}_t{k}', [tx, y, tw, th], s, size=size, container=container,
                                  fam=(outcome_fam if last else None), strong=bool(last)))
            if k:
                # same rounding care as vchain: start from the previous token's real right edge
                ax0 = int(round(x + (k - 1) * (tw + gap))) + int(round(tw)) + 3; ax1 = int(round(tx)) - 3
                hl = max(4.0, min(9.0, (ax1 - ax0) * 0.55))
                self.sc.line(f'{cid}_a{k}', [(ax0, y + th / 2), (ax1, y + th / 2)], stroke=CONN, width=W_STEP,
                             arrow=True, head={'length': hl, 'width': max(4.0, hl * 0.9)}, container=container)
        return ids

    def ledger(self, cid, box, rows, container=None, size=None, gap=10, cols=1, tick=True):
        """Record grid: one token per recorded item, each with a tick mark, laid out in `cols` columns."""
        size = size or self.size('body', 20)
        x, y, w, h = box
        per = math.ceil(len(rows) / cols)
        cw = (w - 16 * (cols - 1)) / cols
        rh = (h - gap * (per - 1)) / per
        for k, r in enumerate(rows):
            c = k // per; i = k % per
            tx = x + c * (cw + 16); ty = y + i * (rh + gap)
            self.token(f'{cid}_r{k}', [tx, ty, cw, rh], r, size=size, container=container)
            if tick:
                m = ty + rh / 2
                self.sc.line(f'{cid}_k{k}a', [(tx + cw - 26, m), (tx + cw - 20, m + 6)], stroke=CONN, width=W_STEP, container=f'{cid}_r{k}')
                self.sc.line(f'{cid}_k{k}b', [(tx + cw - 20, m + 6), (tx + cw - 10, m - 7)], stroke=CONN, width=W_STEP, container=f'{cid}_r{k}')
                pair = {f'{cid}_k{k}a': f'{cid}_k{k}b', f'{cid}_k{k}b': f'{cid}_k{k}a'}
                for el in self.sc.els:
                    if el['id'] in pair:
                        el['allow_overlap_with'] = sorted(set(el.get('allow_overlap_with', []) + [pair[el['id']], f'{cid}_r{k}']))
                        el['overlap_reason'] = 'tick mark drawn inside its record token'

    # ------------------------------------------------------------------ tier 4
    def pill(self, pid, cx, cy, text, size=None, fam=None, padx=16, pady=6, max_w=None, container=None):
        """Capsule label. With max_w, a label wider than that breaks onto two lines instead of reaching
        the next connector (English runs ~1.6x wider than the Chinese it replaces)."""
        size = size or self.size('label', 18)
        f = FAM[fam] if fam else None
        tw = Scene.measure(text, size) + 2 * padx; th = int(size * 1.5) + 2 * pady
        lines = 1
        if max_w and tw > max_w and ' ' in text:
            words = text.split(' ')
            best = min(range(1, len(words)), key=lambda k: max(Scene.measure(' '.join(words[:k]), size),
                                                                Scene.measure(' '.join(words[k:]), size)))
            half = max(Scene.measure(' '.join(words[:best]), size), Scene.measure(' '.join(words[best:]), size))
            tw = half + 2 * padx + 8
            th = int(size * 3.1) + 2 * pady
            lines = 2
        box = [cx - tw / 2, cy - th / 2, tw, th]
        self.sc.shape(pid, box, fill=(f['zone'] if f else '#FFFFFF'), stroke=(f['edge'] if f else '#CBD3DA'),
                      stroke_width=W_PILL, radius=th / 2, container=container)
        self.sc.text(pid + '_t', [box[0] + padx - 6, box[1] + pady - 2, tw - 2 * padx + 12, th - 2 * pady + 4],
                     text, size, bold=self.bold('label'), color=(f['text'] if f else ITEM), container=pid,
                     font_group='edgelabel', wrap=lines > 1)
        self.pills.append(pid)
        return box

    def conn(self, cid, pts, dashed=False, arrow=True, width=W_CONN, color=CONN, label=None, label_at=None,
             label_size=None, label_fam=None, label_max_w=None):
        label_size = label_size or self.size('label', 18)
        ids = []; pts = [(float(a), float(b)) for a, b in pts]
        segs = list(zip(pts[:-1], pts[1:]))
        for k, (p0, p1) in enumerate(segs):
            sid = f'{cid}_{k}'; last = k == len(segs) - 1
            self.sc.line(sid, [p0, p1], stroke=color, width=width, dash=[11, 7] if dashed else None,
                         arrow=(last and arrow), head=(HEAD if (last and arrow and not dashed) else None))
            ids.append(sid)
        # the label is drawn last so it masks the connector it annotates instead of being struck through by it
        pbox = self.pill(cid + '_p', *(label_at or segs[len(segs) // 2][0]), label, size=label_size, fam=label_fam,
                         max_w=label_max_w) if label else None
        mates = ids + ([cid + '_p'] if pbox else [])
        for el in self.sc.els:
            if el['id'] in mates:
                el['allow_overlap_with'] = sorted(set(el.get('allow_overlap_with', []) + [i for i in mates if i != el['id']]))
                el['overlap_reason'] = 'connector joints and its label, visible in source'
        return ids

    def axis(self, aid, x, y0, y1, near='近', far='远', label=None, size=None, container=None, label_x=None):
        size = size or self.size('label', 18)
        ends = self.size('body', size)
        mid = (y0 + y1) / 2
        self.sc.line(aid + '_u', [(x, mid - 42), (x, y0 + 24)], stroke=ITEM, width=W_STEP, arrow=True,
                     head={'length': 14, 'width': 11}, container=container)
        self.sc.line(aid + '_d', [(x, mid + 42), (x, y1 - 24)], stroke=ITEM, width=W_STEP, arrow=True,
                     head={'length': 14, 'width': 11}, container=container)
        eh = int(ends * 1.75) if self.T else 34
        self.sc.text(aid + '_n', [x - 24, y0 - 12, 48, eh], near, ends, bold=True, color=ITEM, container=container)
        self.sc.text(aid + '_f', [x - 24, y1 - 24, 48, eh], far, ends, bold=True, color=ITEM, container=container)
        if label:
            lw = Scene.measure(label, size) + 20; lh = int(size * 1.75)
            self.sc.text(aid + '_l', [(label_x if label_x is not None else x) - lw / 2, mid - lh / 2, lw, lh],
                         label, size, bold=self.bold('label'), color=ITEM, rotation=-90, container=container,
                         font_group='axis')

    # ------------------------------------------------------------------ finishing
    @staticmethod
    def _bbox(el):
        if el['kind'] == 'line':
            xs = [p[0] for p in el['points']]; ys = [p[1] for p in el['points']]; w = el.get('stroke_width', 2)
            return [min(xs) - w, min(ys) - w, max(xs) + w, max(ys) + w]
        x, y, w, h = el['box']; return [x, y, x + w, y + h]

    def finish(self, zone_ids):
        """Declare the intentional overlaps: connector joints, label pills over lines and cards, connectors crossing zones."""
        pack_pill_rows(self.sc.els, self.sc.w)
        lines = [e for e in self.sc.els if e['kind'] == 'line']
        for i, a in enumerate(lines):
            ba = self._bbox(a)
            for b in lines[i + 1:]:
                bb = self._bbox(b)
                ox = min(ba[2], bb[2]) - max(ba[0], bb[0]); oy = min(ba[3], bb[3]) - max(ba[1], bb[1])
                if ox > 0 and oy > 0 and ox * oy <= 300:
                    for x, y in ((a, b), (b, a)):
                        x['allow_overlap_with'] = sorted(set(x.get('allow_overlap_with', []) + [y['id']]))
                        x['overlap_reason'] = 'connector joints, visible in source'
        fam = set(self.pills) | {p + '_t' for p in self.pills}
        pills = [e for e in self.sc.els if e['id'] in fam]
        # A pill masks the line it annotates and may sit on a zone's tint — that is intended. Once a figure
        # follows the printed type scale, a pill over anyone else's text or card is NOT declared: it stays a
        # finding, so a label pushed onto a hub title or out of its zone fails the precheck instead of
        # shipping. (Round-5 scenes keep the old blanket exemption so they still rebuild byte-identically.)
        zone_set = set(zone_ids)
        for a in pills:
            ba = self._bbox(a)
            for b in self.sc.els:
                if b['id'] == a['id'] or b['id'] in fam or b['id'] == a['id'].replace('_t', ''): continue
                if self.T and not (b['kind'] == 'line' or b['id'] in zone_set):
                    continue
                bb = self._bbox(b)
                if ba[0] < bb[2] and ba[2] > bb[0] and ba[1] < bb[3] and ba[3] > bb[1]:
                    for x, y in ((a, b), (b, a)):
                        x['allow_overlap_with'] = sorted(set(x.get('allow_overlap_with', []) + [y['id']]))
                        x['overlap_reason'] = 'connector label sits on its connector, visible in source'
        zones = {e['id']: self._bbox(e) for e in self.sc.els if e['id'] in zone_ids}
        parent = {e['id']: e.get('container') for e in self.sc.els}

        def root(i, d=0):
            while parent.get(i) and d < 8: i = parent[i]; d += 1
            return i
        for el in self.sc.els:
            if el['id'] in zone_ids or root(el['id']) in zone_ids: continue
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


R4 = Framework   # the name this class carried while it lived in the BYZSO project
