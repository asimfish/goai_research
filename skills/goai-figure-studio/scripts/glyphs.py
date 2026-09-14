"""List the native line-art glyphs, or render a contact sheet of all of them.

    python3 glyphs.py                 # names, one line
    python3 glyphs.py sheet out.json  # a scene.json showing every glyph with its name, to build and look at

Every glyph is drawn from the scene's own line/shape primitives, so the whole family shares one ink and one
stroke weight. That is the point: raster icon crops are what made earlier figures look inconsistent.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import Figure, ITEM
from lib.motifs import NAMES


def sheet(path, cols=6, cell=210, box=64):
    names = sorted(NAMES)
    rows = (len(names) + cols - 1) // cols
    f = Figure(cols * cell + 60, rows * cell + 80, notes='auto-figure glyph inventory')
    for i, name in enumerate(names):
        cx = 30 + (i % cols) * cell + cell / 2
        cy = 50 + (i // cols) * cell + cell / 2 - 14
        f.m.draw(name, f'g{i}', [cx - box / 2, cy - box / 2, box, box])
        f.sc.text(f'g{i}_l', [cx - cell / 2 + 8, cy + box / 2 + 10, cell - 16, 30], name, 17,
                  bold=True, color=ITEM)
    f.finish([])
    f.write(path)
    return len(names)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'sheet':
        out = sys.argv[2] if len(sys.argv) > 2 else 'glyph_sheet.json'
        print(f'{sheet(out)} glyphs -> {out}')
    else:
        print(f'{len(NAMES)} glyphs:')
        print(' '.join(sorted(NAMES)))
