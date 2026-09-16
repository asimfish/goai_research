"""Round-2 composites for super_img2ppt scenes: concentric bands (bull's-eye), numbered cards, radial layouts, labelled thin arrows.
All output elements are native scene objects (shape/text/line); icons are added by the caller as exact source crops."""
import math
from i2p_scene import Scene, INK, TEAL, OCHRE, PANEL, PANEL_LINE, GRAY

SLATE = '#4A5158'; TOKEN_LINE = '#C9CFD4'; TITLE = '#1F2326'; SUB = '#3A4046'


def bullseye(sc, cx, cy, radii, fills, strokes, labels, label_size=24, label_color=INK, dashed_outer=True, label_dys=None):
    """Concentric full circles drawn from the largest to the smallest; each band label is horizontal text placed inside the band on the right side.
    radii: descending list (outermost first); fills/strokes: same length; labels: outermost first (None for the centre disc)."""
    n = len(radii); ids = []; label_ids = [f'ring{i}_t' for i, l in enumerate(labels) if l]
    for i, r in enumerate(radii):
        cid = f'ring{i}'; dash = [14, 9] if (dashed_outer and i == 0) else None
        sc.shape(cid, [cx - r, cy - r, 2 * r, 2 * r], shape='ellipse', fill=fills[i], stroke=strokes[i], stroke_width=2.5, dash=dash,
                 overlap=[f'ring{k}' for k in range(n) if k != i] + label_ids, reason='concentric bands, visible in source')
        ids.append(cid)
    # labels: band i (between radii[i] and radii[i+1]) → text box centred on the right part of the band along the horizontal centre line
    # band i lies between radii[i] (outer) and radii[i+1] (inner); its label is horizontal text on the right side of the band.
    # A band is only (r_out - r_in) wide horizontally, which is usually narrower than the label, so the label is centred on the
    # band's horizontal run and may extend over neighbouring bands' area: the container is the OUTERMOST ring (which contains it) and
    # overlaps with inner rings are declared (visible in source: text printed across the bands).
    # Labels are staggered vertically (dy per band) so that they never overlap each other; each label box is placed on the right side of
    # its band at the given vertical offset from the centre line.
    m = len([l for l in labels if l]); k = 0
    for i, lab in enumerate(labels):
        if not lab: continue
        r_out = radii[i]; r_in = radii[i + 1] if i + 1 < n else 0
        h = int(label_size * 1.5); tw = Scene.measure(lab, label_size) + 10
        dy = (label_dys[i] if label_dys else (k - (m - 1) / 2) * (h + 6)); k += 1
        import math as _m
        xin = _m.sqrt(max(r_in * r_in - dy * dy, 0)); xout = _m.sqrt(max(r_out * r_out - dy * dy, 0))
        x0 = cx + (xin + xout) / 2 - tw / 2; x0 = min(x0, cx + xout - 8 - tw)
        if label_dys: x0 = cx - tw / 2  # top-of-band labels are centred on the vertical axis (corners stay inside the outer circle)
        sc.text(f'ring{i}_t', [x0, cy + dy - h / 2, tw, h], lab, label_size, bold=True, color=label_color, container='ring0', font_group='band',
                overlap=[f'ring{q}' for q in range(1, n)], reason='band labels printed across the concentric bands, visible in source')
    return ids


def numbered_card(sc, cid, box, number, title, sub, stroke=SLATE, fill='#FFFFFF', title_size=34, sub_size=24, num_size=20, radius=14, motif_box=None):
    x, y, w, h = box
    sc.shape(cid, box, fill=fill, stroke=stroke, stroke_width=2.5, radius=radius)
    sc.text(cid + '_n', [x + 14, y + 10, 60, int(num_size * 1.5)], number, num_size, bold=True, color='#8A9199', align='left', container=cid, font_group='num')
    th = int(title_size * 1.5); sh = int(sub_size * 1.5)
    ty = y + 10 + int(num_size * 1.5) + 8
    sc.text(cid + '_t', [x + 12, ty, w - 24, th], title, title_size, bold=True, color=TITLE, container=cid, font_group='title', fit='shrink', min_font_size=title_size - 6)
    sc.text(cid + '_s', [x + 12, ty + th + 4, w - 24, sh], sub, sub_size, color=SUB, container=cid, font_group='sub', fit='shrink', min_font_size=sub_size - 4)
    return cid


def labelled_arrow_above(sc, aid, p0, p1, label, size=20, width=3, head=None, color=TEAL, label_color=SUB, gap=8):
    """Thin arrow between two points with its label as plain text centred above (horizontal) or beside (vertical) the shaft."""
    (x0, y0), (x1, y1) = p0, p1
    sc.line(aid, [(x0, y0), (x1, y1)], stroke=color, width=width, arrow=True, head=head or {'length': 14, 'width': 12})
    h = int(size * 1.5); tw = Scene.measure(label, size) + 8
    if y0 == y1:
        cx = (x0 + x1) / 2; sc.text(aid + '_l', [cx - tw / 2, y0 - gap - h, tw, h], label, size, color=label_color, font_group='edge')
    else:
        cy = (y0 + y1) / 2; sc.text(aid + '_l', [x0 + gap, cy - h / 2, tw, h], label, size, color=label_color, align='left', font_group='edge')
    return aid


def radial_positions(cx, cy, R, n, start_deg=-90):
    """n points on a circle, clockwise from the top."""
    return [(cx + R * math.cos(math.radians(start_deg + 360 * k / n)), cy + R * math.sin(math.radians(start_deg + 360 * k / n))) for k in range(n)]


def spoke_with_pill(sc, sid, p_hub, p_card, label, pill_w=110, pill_h=42, color=TEAL, dash=None, size=22, width=3, pill_fill='#FFFFFF', pill_stroke=None, text_color=None):
    """Straight spoke from the hub edge to the card edge, split around a label pill at mid-length. Returns nothing; ids sid, sid+'b', sid+'_p'."""
    (x0, y0), (x1, y1) = p_hub, p_card; mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
    half = math.hypot(pill_w / 2 * abs(ux), pill_h / 2 * abs(uy)) + 4  # conservative half-length of the pill along the spoke
    half = max(half, pill_w / 2 * abs(ux) + pill_h / 2 * abs(uy) + 4)
    a1 = (mx - ux * half, my - uy * half); a2 = (mx + ux * half, my + uy * half)
    sc.line(sid, [(x0, y0), a1], stroke=color, width=width, dash=dash)
    if dash: sc.line(sid + 'b', [a2, (x1, y1)], stroke=color, width=width, dash=dash, arrow=True)
    else: sc.line(sid + 'b', [a2, (x1, y1)], stroke=color, width=width, arrow=True, head={'length': 16, 'width': 14})
    sc.shape(sid + '_p', [mx - pill_w / 2, my - pill_h / 2, pill_w, pill_h], fill=pill_fill, stroke=(pill_stroke or color), stroke_width=2.5, radius=pill_h / 2)
    sc.text(sid + '_pt', [mx - pill_w / 2 + 6, my - pill_h / 2 + 3, pill_w - 12, pill_h - 6], label, size, bold=True, color=(text_color or color), container=sid + '_p', font_group='pill')
