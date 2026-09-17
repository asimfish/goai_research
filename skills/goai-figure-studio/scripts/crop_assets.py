"""Cut an image-model ASSET SHEET (a grid of text-free illustrations on white) into one PNG per cell.

The model does not centre its drawings on an exact grid, so cells are found from the ink itself: the (rows-1) widest
empty horizontal bands split the sheet into rows, and inside each row the (cols-1) widest empty vertical bands split it
into cells (gaps INSIDE an illustration — three file icons side by side — are narrower than the gaps between cells).
Each cell is cropped to its ink plus a margin, and the white connected to the crop border becomes transparent (flood
fill from the border — white INSIDE the art, a lab coat or a sheet of paper, stays white).

usage: crop_assets.py <project dir> <out dir> [--margin 8] [--white 240] [--keep-white]
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument('project')
ap.add_argument('out')
ap.add_argument('--margin', type=int, default=8)
ap.add_argument('--white', type=int, default=240, help='pixels at or above this value in all channels count as background')
ap.add_argument('--keep-white', action='store_true')
a = ap.parse_args()

root = Path(a.project)
idx = json.loads((root / 'outputs' / 'ASSETS' / 'prompt-index.json').read_text(encoding='utf-8'))
cols, rows = idx['grid']
sheet = Image.open(root / 'outputs' / 'ASSETS' / 'generated' / 'SHEET.png').convert('RGB')
W, H = sheet.size
ink = ImageChops.invert(sheet.convert('L')).point(lambda v: 255 if v > 255 - a.white else 0)


def bands(length, has_ink, want):
    """Split [0, length) into `want` bands at the (want-1) widest ink-free gaps that lie between inked stretches."""
    runs, start = [], None
    for i in range(length):
        if has_ink(i):
            if start is None:
                start = i
        elif start is not None:
            runs.append((start, i)); start = None
    if start is not None:
        runs.append((start, length))
    gaps = sorted(((b0 - a1, a1, b0) for (_a0, a1), (b0, _b1) in zip(runs[:-1], runs[1:])), reverse=True)[:want - 1]
    cuts = sorted((g[1] + g[2]) // 2 for g in gaps)
    edges = [0] + cuts + [length]
    return list(zip(edges[:-1], edges[1:]))


row_bands = bands(H, lambda y: ink.crop((0, y, W, y + 1)).getbbox() is not None, rows)
assert len(row_bands) == rows, f'found {len(row_bands)} rows, expected {rows}'
out = Path(a.out)
out.mkdir(parents=True, exist_ok=True)
names = iter(idx['cells'])
for (y0, y1) in row_bands:
    col_bands = bands(W, lambda x: ink.crop((x, y0, x + 1, y1)).getbbox() is not None, cols)
    assert len(col_bands) == cols, f'row {y0}-{y1}: found {len(col_bands)} cells, expected {cols}'
    for (x0, x1) in col_bands:
        name = next(names)
        bx = ink.crop((x0, y0, x1, y1)).getbbox()
        cx0, cy0 = max(0, x0 + bx[0] - a.margin), max(0, y0 + bx[1] - a.margin)
        cx1, cy1 = min(W, x0 + bx[2] + a.margin), min(H, y0 + bx[3] + a.margin)
        art = sheet.crop((cx0, cy0, cx1, cy1)).convert('RGBA')
        if not a.keep_white:
            w, h = art.size
            seeds = [(x, y) for x in range(0, w, 6) for y in (0, h - 1)] + [(x, y) for y in range(0, h, 6) for x in (0, w - 1)]
            for seed in seeds:
                px = art.getpixel(seed)
                if px[3] and min(px[:3]) >= a.white:
                    ImageDraw.floodfill(art, seed, (255, 255, 255, 0), thresh=40)
        art.save(out / f'{name}.png')
        print(f'  {name:14} {art.size[0]}x{art.size[1]}')
