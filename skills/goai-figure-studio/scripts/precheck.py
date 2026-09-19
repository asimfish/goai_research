"""Local pre-flight for scene.json: predicts the super_img2ppt findings that cost a remote round-trip.

Adds a printed-size gate for scenes that declare [print_width_pt=…], and reproduces, conservatively, four of the validator's checks — text_overflow, text_shrunk, outside_container and
unintended_overlap — using the same width model as i2p_scene.Scene.measure. Text boxes are compared on their
measured ink (placed by align/valign) so that frame-only overlaps are reported separately, as the validator does.

usage: python3 skills/goai-figure-studio/scripts/precheck.py jobs/<fig>/scene.json [...]
"""
import json, math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib import Scene, MIN_PRINT_PT, PRINT_TAG

RESERVE = 1.0


def ink(el):
    """Ink bbox of an element: measured text extent for text, box for shapes, stroked span for lines."""
    if el['kind'] == 'text':
        x, y, w, h = el['box']
        tw = min(Scene.measure(el['text'], el['font_size'], el.get('bold')), w)
        th = el['font_size'] * 1.25
        a = el.get('align', 'center'); v = el.get('valign', 'middle')
        if el.get('rotation') in (90, -90, 270, -270):
            tw, th = th, tw
            tw = min(tw, w)
        tx = x if a == 'left' else (x + w - tw if a == 'right' else x + (w - tw) / 2)
        ty = y if v == 'top' else (y + h - th if v == 'bottom' else y + (h - th) / 2)
        if el.get('rotation') in (90, -90, 270, -270):
            cx, cy = x + w / 2, y + h / 2
            return [cx - tw / 2, cy - th / 2, cx + tw / 2, cy + th / 2]
        return [tx, ty, tx + tw, ty + th]
    if el['kind'] == 'line':
        xs = [p[0] for p in el['points']]; ys = [p[1] for p in el['points']]; s = el.get('stroke_width', 2) / 2 + 1
        return [min(xs) - s, min(ys) - s, max(xs) + s, max(ys) + s]
    x, y, w, h = el['box']; return [x, y, x + w, y + h]


def frame(el):
    if el['kind'] == 'line': return ink(el)
    x, y, w, h = el['box']; return [x, y, x + w, y + h]


def isect(a, b):
    return min(a[2], b[2]) - max(a[0], b[0]) > 0 and min(a[3], b[3]) - max(a[1], b[1]) > 0


def main(paths):
    bad = 0
    for path in paths:
        doc = json.load(open(path))
        sl = doc['slides'][0] if 'slides' in doc else doc
        els = sl['elements']
        for e in els:
            if e.get('kind') == 'text' and 'runs' in e and 'text' not in e:
                e['text'] = ''.join(r.get('text', '') for r in e['runs'])   # runs: measure the concatenation
        by = {e['id']: e for e in els}
        out = []
        # printed size: a scene that declares its print width must not set any text below MIN_PRINT_PT on paper
        # (fit=shrink may take a string down to min_font_size, so that is the size that has to clear the floor)
        m = PRINT_TAG.search(sl.get('notes', ''))
        if m:
            ppx = float(m.group(1)) / (sl['width'] - 24)
            for e in els:
                if e['kind'] != 'text':
                    continue
                low = e.get('min_font_size', e['font_size']) if e.get('fit') == 'shrink' else e['font_size']
                if low * ppx < MIN_PRINT_PT - 0.05:
                    out.append(('print_too_small', f"{e['id']} can print at {low * ppx:.1f} pt "
                                f"(< {MIN_PRINT_PT:g}) — '{e['text'][:24]}'"))
        for e in els:
            if e['kind'] == 'text':
                x, y, w, h = e['box']
                need_w = Scene.measure(e['text'], e['font_size'], e.get('bold')) + RESERVE
                need_h = e['font_size'] * 1.25 + RESERVE
                if e.get('wrap') and ' ' in e['text']:
                    parts = e['text'].split(' ')
                    need_w = max(Scene.measure(p, e['font_size'], e.get('bold')) for p in parts) + RESERVE
                    lines = max(1, math.ceil((Scene.measure(e['text'], e['font_size'], e.get('bold')) + RESERVE) / max(w, 1)))
                    need_h = lines * e['font_size'] * 1.35 + RESERVE
                if e.get('rotation'): continue   # the renderer measures rotated text in its own frame
                floor = e.get('min_font_size') if e.get('fit') == 'shrink' else e['font_size']
                if need_w > w or need_h > h:
                    fits = floor and Scene.measure(e['text'], floor, e.get('bold')) + RESERVE <= w and floor * 1.25 + RESERVE <= h
                    out.append(('text_shrunk' if fits else 'text_overflow',
                                f"{e['id']} needs {need_w:.0f}x{need_h:.0f} in {w}x{h} — '{e['text'][:26]}'"))
            c = e.get('container')
            if c and c in by and not e['id'].endswith('_a') and not e.get('rotation'):
                cb = frame(by[c]); eb = ink(e)
                if eb[0] < cb[0] - 1 or eb[1] < cb[1] - 1 or eb[2] > cb[2] + 1 or eb[3] > cb[3] + 1:
                    out.append(('outside_container', f"{e['id']} {['%.0f' % v for v in eb]} not inside {c} {cb}"))

        def anc(i, d=0):
            s = set()
            while i in by and by[i].get('container') and d < 8:
                i = by[i]['container']; s.add(i); d += 1
            return s
        for i, a in enumerate(els):
            ea = anc(a['id']); xa = set(a.get('allow_overlap_with', []))
            for b in els[i + 1:]:
                if b['id'] in ea or a['id'] in anc(b['id']): continue
                if b['id'] in xa or a['id'] in set(b.get('allow_overlap_with', [])): continue
                if ea & anc(b['id']) and (a['kind'] == 'line' or b['kind'] == 'line'): pass
                if not isect(frame(a), frame(b)): continue
                kind = 'unintended_overlap' if isect(ink(a), ink(b)) else 'text_frame_overlap_only'
                if kind == 'unintended_overlap' or 'text' in (a['kind'], b['kind']):
                    out.append((kind, f"{a['id']} × {b['id']}"))
        hard = [o for o in out if o[0] in ('text_overflow', 'outside_container', 'unintended_overlap', 'print_too_small')]
        soft = [o for o in out if o not in hard]
        print(f"== {path}: {len(hard)} hard, {len(soft)} soft ({len(els)} elements)")
        for code, msg in hard: print('   !', code, msg)
        for code, msg in soft[:6]: print('   .', code, msg)
        bad += len(hard)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
