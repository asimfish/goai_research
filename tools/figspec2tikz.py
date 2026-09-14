r"""Render a figspec JSON (groups / nodes / edges / texts on a pixel canvas) as a standalone TikZ document.

usage: python3 figspec2tikz.py <spec.json> <out.tex> [--labels labels_en.json] [--lang zh|en] [--font-scale 1.5] [--no-title]
 - labels file (optional): {"title":..., "groups":{id:{label}}, "nodes":{id:{label,sublabel}}, "edges":{id:{label}}, "texts":{id:{text}}}
 - the canvas (e.g. 1500 x 900 px) is mapped to a 5.5 in wide box (NeurIPS text width); fonts are scaled by --font-scale
   so that labels end up >= 7 pt at final size (spec fonts are 17-20 px, i.e. 4.5-5.3 pt at 5.5 in -> x1.5 gives 7-8 pt).
 - zh: ctexart + Noto Sans CJK; en: article + Helvetica-like (TeX Gyre Heros).  Compile with xelatex.
 - drawing order: group boxes -> node boxes -> edges -> node labels -> free texts, so no box ever covers a label.
"""
import json, re, sys, math, argparse

ap = argparse.ArgumentParser()
ap.add_argument('spec'); ap.add_argument('out')
ap.add_argument('--labels'); ap.add_argument('--lang', default='zh'); ap.add_argument('--font-scale', type=float, default=1.35)
ap.add_argument('--no-title', action='store_true'); ap.add_argument('--width-in', type=float, default=5.5)
a = ap.parse_args()
spec = json.load(open(a.spec, encoding='utf-8'))
lab = json.load(open(a.labels, encoding='utf-8')) if a.labels else {}
W, H = spec['canvas']['width'], spec['canvas']['height']
PT = a.width_in * 72.27 / W                       # pt per px at final width
D = spec.get('defaults', {})
SUB = {'₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9', '₊': '+', '₋': '-'}


def tex(s):
    """escape text; unicode subscripts -> math subscripts; keep newlines as \\\\"""
    if not s: return ''
    s = s.replace('\\', '\\textbackslash{}').replace('&', '\\&').replace('%', '\\%').replace('#', '\\#').replace('_', '\\_').replace('{', '\\{').replace('}', '\\}')
    out = ''; i = 0
    while i < len(s):
        if s[i] in SUB:
            j = i
            while j < len(s) and s[j] in SUB: j += 1
            out += '$_{' + ''.join(SUB[c] for c in s[i:j]) + '}$'; i = j
        else: out += s[i]; i += 1
    out = re.sub(r'(?<![\\w$])((?:[A-Z][a-z]?\d*|\[|\]|\(|\))+)(?![\\w$])', lambda m: re.sub(r'([A-Za-z\]\)])(\d+)', r'\1$_{\2}$', m.group(1)) if re.search(r'[A-Z][a-z]?\d', m.group(1)) and re.search(r'\d', m.group(1)) else m.group(1), out)
    out = out.replace('→', '$\\rightarrow$').replace('≥', '$\\geq$').replace('≤', '$\\leq$').replace('×', '$\\times$').replace('−', '--').replace('–', '--')
    # keep short CJK terms (2-6 chars) on one line: '结构'/'谱系'/'复磨' must not break in half
    out = re.sub(r'(?<![\u4e00-\u9fff])([\u4e00-\u9fff]{2,6})(?![\u4e00-\u9fff])', r'\\mbox{\1}', out)
    return out.replace('\n', '\\\\')


def fs(px, scale=None):
    """font size in pt at final width, scaled"""
    return max(6.0, px * PT * (scale or a.font_scale))


def X(x): return x * PT / 72.27          # inches → we use pt directly via 'pt' units; keep px->pt
def P(x, y): return '(%.2fpt,%.2fpt)' % (x * PT, (H - y) * PT)


def get(sec, it, key):
    return lab.get(sec, {}).get(it.get('id', ''), {}).get(key, it.get(key, ''))



def _plain(t):
    """text as it will appear, for width estimation"""
    t = re.sub(r'\\[a-zA-Z]+\*?', '', t)
    return re.sub(r'[{}$^~]', '', t)


# rendered as math (\rightarrow, \geq, \times ...): about one em plus a thin space on each side
WIDE = set('\u2192\u2190\u2194\u2260\u2265\u2264\u00d7\u00b1\u2014\u2013\u2225\u2016')
SUBDIG = set('\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089\u208a\u208b')
NARROW = set('ijlt.,;:!|\'`()[]{}/ ')
CAP = set('ABCDEFGHKLNOPQRSTUVXYZ')      # I and J are narrow; M and W are wider
# advance widths in em for a Helvetica/Times-like face; chemical formulas are mostly capitals,
# digits and brackets, which a flat 0.52 em badly underestimates (the text then spills out of the box)


def cw(c, fpt):
    """rendered width of one character, in pt, at font size fpt"""
    if c in WIDE: return 1.15 * fpt
    if c in SUBDIG: return 0.34 * fpt
    if ord(c) > 0x2e80: return fpt
    if c in NARROW: return 0.32 * fpt
    if c in 'MW': return 0.85 * fpt
    if c in CAP: return 0.68 * fpt
    if c.isdigit(): return 0.55 * fpt
    return 0.50 * fpt


def n_lines(t, fpt, tw):
    """how many rendered lines a string needs in a tw-wide box at font size fpt"""
    if not t or tw <= 0: return 0
    total = 0
    for seg in _plain(t).split('\n'):
        w = sum(cw(c, fpt) for c in seg)
        total += max(1, math.ceil(w / (tw * 0.92) - 1e-6))   # 8% safety: CJK wraps anywhere, Latin only at spaces
    return total



def widest_token(t, fpt):
    """width in pt of the widest unbreakable token (formula/acronym) in t"""
    if not t: return 0.0
    best = 0.0
    for seg in _plain(t).replace('\n', ' ').split(' '):
        best = max(best, sum(cw(c, fpt) for c in seg))
    return best


def fit(label, sub, f1, f2, tw, box_h, floor=4.8):
    """shrink both font sizes until label+sublabel fit the box height

    budget = box height - 4pt inner sep - 3pt slack; the text block itself also carries the
    first line's ascender and the last line's descender beyond the baseline skips."""
    for _ in range(40):
        h = 0.25 * max(f1, f2)
        if label: h += n_lines(label, f1, tw) * f1 * 1.18
        if sub: h += (f1 * 0.3 if label else 0.0) + n_lines(sub, f2, tw) * f2 * 1.2
        if h <= box_h - 7.0 or f1 <= floor: break
        f1 *= 0.96; f2 *= 0.96
    return max(floor, f1), max(floor - 0.4, f2)


def clearance(n, allnodes, groups, cap=64.0):
    """px a node may grow on each side before touching a neighbour or leaving its group"""
    x0, y0, x1, y1 = n['x'], n['y'], n['x'] + n['w'], n['y'] + n['h']
    L = R = U = D = cap
    for m in allnodes:
        if m is n: continue
        mx0, my0, mx1, my1 = m['x'], m['y'], m['x'] + m['w'], m['y'] + m['h']
        if my0 < y1 and my1 > y0:                       # side by side -> horizontal neighbour
            if mx1 <= x0: L = min(L, x0 - mx1)
            elif mx0 >= x1: R = min(R, mx0 - x1)
        if mx0 < x1 and mx1 > x0:                       # stacked -> vertical neighbour
            if my1 <= y0: U = min(U, y0 - my1)
            elif my0 >= y1: D = min(D, my0 - y1)
    for g in groups:                                    # stay inside the enclosing group
        gx0, gy0, gx1, gy1 = g['x'], g['y'], g['x'] + g['w'], g['y'] + g['h']
        if gx0 <= x0 and gy0 <= y0 and gx1 >= x1 and gy1 >= y1:
            L = min(L, x0 - gx0); R = min(R, gx1 - x1)
            U = min(U, y0 - gy0); D = min(D, gy1 - y1)
    return max(0.0, L), max(0.0, R), max(0.0, U), max(0.0, D)


lines = []
if a.lang == 'zh':
    lines += ['\\documentclass[tikz,border=2pt]{standalone}', '\\usepackage{xeCJK}', '\\providecommand{\\goainotopath}{/usr/share/fonts/noto-cjk/}',
              '\\setCJKmainfont[Path=\\goainotopath,BoldFont=NotoSansCJKsc-Bold.otf]{NotoSansCJKsc-Regular.otf}', '\\setCJKsansfont[Path=\\goainotopath,BoldFont=NotoSansCJKsc-Bold.otf]{NotoSansCJKsc-Regular.otf}',
              '\\xeCJKsetup{CJKecglue={\\hskip 0.18em}}']
else:
    lines += ['\\documentclass[tikz,border=2pt]{standalone}']
lines += ['\\usepackage{fontspec}', '\\setmainfont{texgyreheros}[Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic]', '\\renewcommand{\\familydefault}{\\rmdefault}',
          '\\usepackage{amsmath}', '\\usetikzlibrary{arrows.meta,calc,positioning}', '\\begin{document}', '\\begin{tikzpicture}[x=1pt,y=1pt, every node/.style={inner sep=0pt}]']
# groups
for g in spec.get('groups', []):
    x, y, w, h = g['x'], g['y'], g['w'], g['h']
    lines.append('\\fill[%s, rounded corners=%.1fpt] %s rectangle %s;' % (col(g['fill']) if False else 'color=' + 'gfill', 6 * PT, P(x, y), P(x + w, y + h))) if False else None
    lines.append('\\definecolor{gf}{HTML}{%s}\\definecolor{gs}{HTML}{%s}' % (g.get('fill', '#F5F5F5')[1:], g.get('stroke', '#234456')[1:]))
    lines.append('\\filldraw[fill=gf, draw=gs, line width=%.2fpt, rounded corners=%.1fpt] %s rectangle %s;' % (g.get('stroke_width', 1.2) * PT, 8 * PT, P(x, y), P(x + w, y + h)))
    gl = get('groups', g, 'label')
    if gl: lines.append('\\node[anchor=north west, font=\\bfseries\\fontsize{%.1f}{%.1f}\\selectfont, text=gs, fill=gf, inner xsep=3pt, inner ysep=1pt] at %s {%s};' % (fs(g.get('font_size', 20)), fs(g.get('font_size', 20)) * 1.2, P(x + 11, y + 9), tex(gl)))
# nodes（两遍：先框后字）
textpass = []
for n in spec['nodes']:
    x, y, w, h = n['x'], n['y'], n['w'], n['h']
    fill = n.get('fill', D.get('fill', '#FFFFFF'))[1:]; stroke = n.get('stroke', D.get('stroke', '#183A4A'))[1:]
    lines.append('\\definecolor{nf}{HTML}{%s}\\definecolor{ns}{HTML}{%s}' % (fill, stroke))
    dash = ', dashed' if n.get('dashed') else ''
    rc = 10 * PT if n.get('shape') == 'rounded' else 3 * PT
    label = get('nodes', n, 'label'); sub = get('nodes', n, 'sublabel')
    if not label and not sub:
        lines.append('\\filldraw[fill=nf, draw=ns, line width=%.2fpt, rounded corners=%.1fpt%s] %s rectangle %s;' % (n.get('stroke_width', 1.6) * PT, rc, dash, P(x, y), P(x + w, y + h))); continue
    lc = n.get('label_color', D.get('stroke', '#183A4A'))[1:]; sc = n.get('sublabel_color', '#536873')[1:]
    lines.append('\\definecolor{lc}{HTML}{%s}\\definecolor{sc}{HTML}{%s}' % (lc, sc))
    base = n.get('font_size', D.get('font_size', 20))
    f1 = fs(base, a.font_scale); f2 = fs(base * 0.80, a.font_scale * 0.90)
    tw = max(12.0, w * PT - 5.0)          # inner sep 2pt on each side + 1pt slack -> node width == w*PT
    # how far this box may grow before it touches a neighbour (half the gap, keeping 4px clear)
    cl, cr, cu, cd = clearance(n, spec['nodes'], spec.get('groups', []))
    grow_x = max(0.0, min(cl, cr) / 2 - 4.0) * PT
    grow_y = max(0.0, min(cu, cd) / 2 - 3.0) * PT
    # an unbreakable token (formula, acronym, short CJK term) may push the box wider, but only
    # into that free space; past it shrink the type instead of spilling onto the neighbours
    room = tw + 2 * grow_x
    for _ in range(40):
        # n_lines() measures against tw*0.92, so an unbreakable token only really fits on one
        # line when it is under that same 0.92 of the widest box we are willing to draw
        if max(widest_token(label, f1), widest_token(sub, f2)) <= room * 0.92 - 2.0 or f1 <= 4.8: break
        f1 *= 0.96; f2 *= 0.96
    tw = min(room, max(tw, widest_token(label, f1) + 2.0, widest_token(sub, f2) + 2.0))
    f1, f2 = fit(label, sub, f1, f2, tw, h * PT + 2 * grow_y)
    bw = max(w * PT, min(tw + 5.0, w * PT + 2 * grow_x))
    cx, cy = x + w / 2, y + h / 2
    body = '\\hyphenpenalty=9000\\exhyphenpenalty=9000\\relax '
    if label: body += '{\\bfseries\\fontsize{%.1f}{%.1f}\\selectfont\\color{lc}%s}' % (f1, f1 * 1.18, tex(label))
    if sub: body += ('\\\\[%.1fpt]' % (f1 * 0.3) if label else '') + '{\\fontsize{%.1f}{%.1f}\\selectfont\\color{sc}%s}' % (f2, f2 * 1.2, tex(sub))
    # the rectangle goes down with the other rectangles; the text is drawn in a second pass on top,
    # so an overhanging line is never painted over by a later box
    # two passes with identical geometry: pass 1 draws the box around invisible text (so TikZ
    # itself sizes the box to the real type, never an estimate), pass 2 paints the text on top
    # of every box and connector, so nothing can be covered up.
    geom = 'minimum width=%.1fpt, minimum height=%.1fpt, text width=%.1fpt, align=center, inner sep=2pt, anchor=center' % (bw, h * PT, tw)
    lines.append('\\node[draw=ns, fill=nf, line width=%.2fpt, rounded corners=%.1fpt%s, %s, text opacity=0] at %s {%s};' % (n.get('stroke_width', 1.6) * PT, rc, dash, geom, P(cx, cy), body))
    textpass.append('\\definecolor{lc}{HTML}{%s}\\definecolor{sc}{HTML}{%s}' % (lc, sc))
    textpass.append('\\node[%s] at %s {%s};' % (geom, P(cx, cy), body))
# edges
nodes = {n['id']: n for n in spec['nodes']}


def anchor_pts(e):
    s, t = nodes[e['from']], nodes[e['to']]
    wp = e.get('waypoints')
    if wp:
        first, last = wp[0], wp[-1]
    else:
        first = last = None
    def border(n, toward):
        cx, cy = n['x'] + n['w'] / 2, n['y'] + n['h'] / 2
        dx, dy = toward[0] - cx, toward[1] - cy
        if abs(dx) * n['h'] > abs(dy) * n['w']:   # exit through left/right side
            return (n['x'] + n['w'] if dx > 0 else n['x'], cy + dy * (n['w'] / 2) / abs(dx) if dx else cy)
        return (cx + dx * (n['h'] / 2) / abs(dy) if dy else cx, n['y'] + n['h'] if dy > 0 else n['y'])
    tc = (t['x'] + t['w'] / 2, t['y'] + t['h'] / 2); scn = (s['x'] + s['w'] / 2, s['y'] + s['h'] / 2)
    p0 = border(s, first or tc); p1 = border(t, last or scn)
    return [p0] + (wp or []) + [p1]


for e in spec.get('edges', []):
    pts = anchor_pts(e)
    colr = e.get('color', D.get('edge_color', '#536B77'))[1:]
    lines.append('\\definecolor{ec}{HTML}{%s}' % colr)
    style = 'draw=ec, line width=%.2fpt, -{Stealth[length=%.1fpt,width=%.1fpt]}' % (e.get('width', D.get('edge_width', 2.2)) * PT, 9 * PT, 7 * PT)
    if e.get('arrow') == 'open': style = style.replace('Stealth', 'Straight Barb')
    if e.get('dashed'): style += ', dashed'
    lines.append('\\draw[%s, rounded corners=%.1fpt] %s;' % (style, 6 * PT, ' -- '.join(P(*p) for p in pts)))
    el = get('edges', e, 'label')
    if el:
        # label on the longest segment, offset perpendicular to it, with an opaque halo
        best = max(range(len(pts) - 1), key=lambda i: abs(pts[i + 1][0] - pts[i][0]) + abs(pts[i + 1][1] - pts[i][1]))
        (x0, y0), (x1, y1) = pts[best], pts[best + 1]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        horiz = abs(x1 - x0) >= abs(y1 - y0)
        f = fs(e.get('font_size', 17), a.font_scale * 0.62)
        seglen = (abs(x1 - x0) + abs(y1 - y0)) * PT
        lw = widest_token(el, f) if len(_plain(el).split(' ')) == 1 else sum((f if ord(c) > 0x2e80 else 0.52 * f) for c in _plain(el))
        while lw > seglen * 0.95 and f > 5.0:
            f *= 0.94; lw *= 0.94
        if lw > seglen * 1.05: continue          # no room between the boxes: the caption carries this label
        # on a vertical run keep the label off the boxes: sit it to the left of the line
        anchor, ox, oy = ('south', 0, -4) if horiz else ('east', -5, 0)
        lines.append('\\node[fill=white, fill opacity=0.92, text opacity=1, inner sep=1.2pt, rounded corners=1pt, font=\\fontsize{%.1f}{%.1f}\\selectfont, text=ec, anchor=%s, align=center] at %s {%s};' % (f, f * 1.12, anchor, P(mx + ox, my + oy), tex(el)))
# node labels on top of every rectangle and connector
lines += textpass
# free texts
for t in spec.get('texts', []):
    txt = get('texts', t, 'text')
    if not txt: continue
    f = fs(t.get('font_size', 18), a.font_scale * 0.9); anc = {'left': 'west', 'right': 'east'}.get(t.get('align', 'center'), 'center')
    lines.append('\\definecolor{tc}{HTML}{%s}' % t.get('color', '#183A4A')[1:])
    lines.append('\\node[anchor=%s, font=%s\\fontsize{%.1f}{%.1f}\\selectfont, text=tc] at %s {%s};' % (anc, '\\bfseries' if t.get('bold') else '', f, f * 1.2, P(t['x'], t['y']), tex(txt)))
lines += ['\\end{tikzpicture}', '\\end{document}']
open(a.out, 'w', encoding='utf-8').write('\n'.join(l for l in lines if l is not None))
print('wrote', a.out, 'nodes', len(spec['nodes']), 'edges', len(spec.get('edges', [])), 'pt/px %.3f' % PT)
