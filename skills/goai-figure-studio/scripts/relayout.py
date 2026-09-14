"""Re-type a finished scene into another language without re-authoring the layout.

A scene is geometry plus strings, so a second language is a string map plus a re-fit — same topology, same
hierarchy, same palette, same repairs. Latin runs roughly 1.6x wider than the CJK it replaces, which is what
breaks naive translation: pills reach their neighbours, titles overflow, and the last connector label falls off
the page. Each of those has a specific fix here.

    from relayout import retype
    missing = retype(slide, TR)          # slide = doc['slides'][0]
    if missing: ...                      # report, never ship the untranslated string

Anything absent from the map is returned rather than silently left in the source language.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import Scene, pack_pill_rows

CJK_RANGE = re.compile(r'[　-鿿＀-￯]')
PILL_TEXT = re.compile(r'(.+_p)_t$')


def _is_capsule(shape):
    """A pill is fully rounded; a record token has a small corner radius."""
    return shape.get('radius', 0) * 2 >= shape['box'][3] - 1


def _bbox(el):
    if el['kind'] == 'line':
        xs = [q[0] for q in el['points']]
        ys = [q[1] for q in el['points']]
        w = el.get('stroke_width', 2)
        return [min(xs) - w, min(ys) - w, max(xs) + w, max(ys) + w]
    x, y, w, h = el['box']
    return [x, y, x + w, y + h]


def _relayout_label(el):
    """Zone label: grow the box to the right for the longer string (rotated labels keep their frame)."""
    if el.get('rotation'):
        return
    el['box'][2] = int(Scene.measure(el['text'], el['font_size']) + 26)


def _relayout_pill(slide, el, pill_id, page_w, padx=16):
    """Pill: re-measure shape and text together, keeping the pill's centre, height and page bounds."""
    shape = next((e for e in slide['elements'] if e['id'] == pill_id), None)
    if shape is None or not _is_capsule(shape):
        return
    cx = shape['box'][0] + shape['box'][2] / 2
    tw = Scene.measure(el['text'], el['font_size']) + 2 * padx
    left = min(max(6, cx - tw / 2), max(6, page_w - 6 - tw))   # a wider pill must stay on the page
    shape['box'][0] = int(round(left))
    shape['box'][2] = int(round(tw))
    el['box'][0] = int(round(shape['box'][0] + padx - 6))
    el['box'][2] = int(round(tw - 2 * padx + 12))


def _reexempt_pills(slide):
    """A label pill masks whatever it sits on; after re-measuring, declare the overlaps its new width created."""
    els = slide['elements']
    for cap in [e for e in els if e['kind'] == 'shape' and _is_capsule(e)]:
        family = {cap['id'], cap['id'] + '_t'}
        for el in [e for e in els if e['id'] in family]:
            eb = _bbox(el)
            for other in els:
                if other['id'] in family:
                    continue
                ob = _bbox(other)
                if eb[0] < ob[2] and eb[2] > ob[0] and eb[1] < ob[3] and eb[3] > ob[1]:
                    for a, b in ((el, other), (other, el)):
                        a['allow_overlap_with'] = sorted(set(a.get('allow_overlap_with', []) + [b['id']]))
                        a['overlap_reason'] = 'connector label sits on what it annotates, visible in source'


def retype(slide, tr, free_pills=(), source_script=CJK_RANGE, floor=12, wrap_ratio=2.1):
    """Map every visible string through `tr` and re-fit the type. Returns the strings `tr` did not cover.

    `free_pills` names the text ids of standalone pills (a caveat or a legend, not a connector label) — they
    size themselves from their own string like connector labels do, but their ids do not end in `_p_t`.
    """
    missing = []
    for el in slide['elements']:
        if el['kind'] != 'text':
            continue
        src = el['text']
        if not source_script.search(src):
            continue                      # already in the target script (formulas, PXRD/Rietveld, step numbers)
        dst = tr.get(src)
        if dst is None:
            missing.append(src)
            continue
        el['text'] = dst
        size = el['font_size']
        # the replacement runs wider at the same point size: let it shrink, but not below readable print size
        el['fit'] = 'shrink'
        el['min_font_size'] = max(floor, min(el.get('min_font_size', size), size - 8))
        # a font_group shrinks its members together, so the longest string would hold the whole group at the
        # original size; boxes fit independently instead (the floor keeps the spread small)
        el.pop('font_group', None)
        m = PILL_TEXT.match(el['id'])
        if el['id'].endswith('_l'):
            _relayout_label(el)
        elif m:
            # a connector label lives in the gutter between two connectors; drop it one step before
            # re-measuring or the pill reaches the next connector
            el['font_size'] = max(15, size - 2)
            el['min_font_size'] = min(el['min_font_size'], el['font_size'])
            _relayout_pill(slide, el, m.group(1), slide['width'])
        elif el['id'] in free_pills:
            _relayout_pill(slide, el, el['id'][:-2], slide['width'])
        elif el['box'][3] >= size * wrap_ratio:
            el['wrap'] = True             # the box has room for a second line
    # the source row fitted where it was authored; the wider pills need the row packed again
    pack_pill_rows(slide['elements'], slide['width'])
    _reexempt_pills(slide)
    return missing
