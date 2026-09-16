"""Printed-size acceptance for figures, read from the compiled paper.

The only trustworthy source for "how big does this text print" is the compiled PDF: it knows where each figure
was placed and how wide. (Estimating the text width from body lines was off by 8% in practice.) For every
figure this finds its placement, then reports the printed point size of every role in the figure's scene.

    python3 print_audit.py --paper main_zh3.pdf  fig01.pdf=jobs/fig01/scene.json  fig02.pdf=...

Exit code 1 if any text can print below the floor (7 pt, including a fit=shrink minimum).
"""
import argparse
import collections
import json
import pathlib
import re
import sys

import pypdfium2 as pdfium
import pypdfium2.raw as raw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib import MIN_PRINT_PT, BOLD_ROLES  # noqa: E402

ROLE_NAMES = {'group': '分组标题', 'title': '卡片标题', 'number': '步骤编号', 'body': '正文/条目', 'label': '标签'}


def placements(paper):
    doc = pdfium.PdfDocument(str(paper))
    out = []
    for i in range(len(doc)):
        for obj in doc[i].get_objects(max_depth=1):
            if obj.type == raw.FPDF_PAGEOBJ_FORM:
                l, b, r, t = obj.get_bounds()
                if r - l > 100 and t - b > 40:
                    out.append((i + 1, r - l, t - b))
    return out


def role_of(el, by):
    """Role from the scene's own conventions (ids and weight), matching the lib's builders.

    A label is text inside a capsule (radius = half the height). A step card's key-point token shares the
    `_p_t` id suffix with connector labels but sits in a square-cornered token, so it is body text.
    """
    i = el['id']
    if i.endswith('_l') and not i.startswith('ax'):
        return 'group'
    parent = by.get(el.get('container'))
    capsule = bool(parent and parent.get('kind') == 'shape'
                   and parent.get('radius', 0) * 2 >= parent['box'][3] - 1)
    if capsule or i.startswith('ax_'):
        return 'label'
    if i.endswith('_n') and el.get('bold'):
        return 'number'
    if el.get('bold'):
        return 'title'
    return 'body'


def audit(paper, pairs):
    places = placements(paper)
    worst = 99.0
    for fig, scene in pairs:
        fw, fh = pdfium.PdfDocument(str(fig))[0].get_size()
        ar = fw / fh
        match = [p for p in places if abs(p[1] / p[2] - ar) / ar < 0.03]
        if not match:
            print(f'  ?? {fig.name}: not found in {paper.name}')
            continue
        page, pw, _ = min(match, key=lambda p: abs(p[1] / p[2] - ar))
        sl = json.loads(scene.read_text(encoding='utf-8'))['slides'][0]
        ppx = (960 / sl['width']) * (pw / fw)
        rows = collections.defaultdict(list)
        by = {e['id']: e for e in sl['elements']}
        for e in sl['elements']:
            if e['kind'] != 'text':
                continue
            low = e.get('min_font_size', e['font_size']) if e.get('fit') == 'shrink' else e['font_size']
            rows[role_of(e, by)].append((e['font_size'] * ppx, low * ppx, bool(e.get('bold'))))
        cells = []
        for r in ('group', 'title', 'number', 'body', 'label'):
            if r not in rows:
                continue
            sizes = sorted({round(s, 1) for s, _, _ in rows[r]})
            low = min(l for _, l, _ in rows[r])
            worst = min(worst, low)
            nb = sum(b for *_, b in rows[r])
            weight = '粗' if nb == len(rows[r]) else ('常' if nb == 0 else f'粗{nb}/{len(rows[r])}')
            flag = ' ✗' if low < MIN_PRINT_PT - 0.05 else ''
            cells.append(f'{ROLE_NAMES[r]} {"/".join(f"{x:g}" for x in sizes)}pt {weight}{flag}')
        print(f'  {fig.stem:<34} p{page:<3} 放置 {pw:.1f}pt  ' + '  '.join(cells))
    return worst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--paper', required=True, type=pathlib.Path)
    ap.add_argument('pairs', nargs='+', help='figure.pdf=scene.json')
    a = ap.parse_args()
    pairs = [(pathlib.Path(x.split('=', 1)[0]), pathlib.Path(x.split('=', 1)[1])) for x in a.pairs]
    worst = audit(a.paper, pairs)
    print(f'  最小可印字号 {worst:.2f} pt（下限 {MIN_PRINT_PT:g}）')
    return 0 if worst >= MIN_PRINT_PT - 0.05 else 1


if __name__ == '__main__':
    sys.exit(main())
