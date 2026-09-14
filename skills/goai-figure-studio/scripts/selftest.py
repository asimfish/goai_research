"""Prove the design system still works standalone: build a scene that exercises every tier, then precheck it.

    python3 selftest.py

Run this after touching lib/. It catches the breakages that otherwise surface only after a round trip to the
render host — a glyph that no longer draws, a box multiplier that stopped fitting CJK, a label row that no
longer packs.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from lib import Figure, pack_pill_rows
from lib.motifs import NAMES


def build(path):
    f = Figure(1536, 900, notes='auto-figure selftest')
    zt = f.zone('zT', [26, 28, 1484, 380], '实验方法', 'exp')
    zb = f.zone('zB', [26, 470, 1484, 390], '文献证据', 'lit')

    # tier 2 + 3: three card shapes, each with a visible internal mechanism
    f.card_stack('c1', [60, 96, 420, 270], '结构基础', ['低温与高温多晶型', '四面体链柔性'],
                 fam='exp', glyph='polyhedron', container=zt)
    f.card_step('c2', [520, 96, 420, 270], '02', '合成路线', '固相 · 溶胶—凝胶',
                fam='exp', glyph='crucible', container=zt)
    f.card('c3', [980, 96, 460, 270], fam='mute', dashed=True, container=zt)
    f.vchain('c3c', [1000, 130, 420, 200], ['预烧熔化', '籽晶提拉', '退火'], container='c3', size=19, gap=18)

    # tier 2 + 3: a record ledger
    f.card('led', [60, 540, 1380, 260], fam='lit', container=zb)
    f.row('ledr', [90, 600, 1320, 60], ['配比与原料', '温度—时间与气氛', '坩埚与助熔剂', '冷却与分离'],
          container='led', size=20, gap=16)

    # tier 4: a full row of edge labels — the case that needs packing
    for k, lab in enumerate(['配比 · 温度', '熔体 · 容器', '混合 · 煅烧', '研磨 · 污染', '籽晶 · 退火']):
        x = 150 + k * 290
        f.conn(f'd{k}', [(x, 400), (x, 462)], label=lab, label_at=(x + 140, 432), label_size=18)
    f.pill('cav', 1300, 60, '框架 ≠ 处方', size=18, fam='note')

    f.finish([zt, zb])
    f.write(path)
    return f


def main():
    out = Path(tempfile.mkdtemp()) / 'selftest.json'
    f = build(out)

    # every glyph must draw without raising
    probe = Figure(400, 400)
    for name in sorted(NAMES):
        probe.m.draw(name, f'p_{name}', [10, 10, 48, 48])
    print(f'glyphs drawn: {len(NAMES)}')

    # the label row must end up on one band, in order, on the page
    els = {e['id']: e for e in f.sc.els}
    pills = [els[f'd{k}_p'] for k in range(5)]
    ys = {p['box'][1] for p in pills}
    xs = [p['box'][0] for p in pills]
    assert len(ys) == 1, f'label row not on one band: {ys}'
    assert xs == sorted(xs), f'label row lost its order: {xs}'
    assert all(a['box'][0] + a['box'][2] <= b['box'][0] for a, b in zip(pills, pills[1:])), 'labels overlap'
    assert pills[-1]['box'][0] + pills[-1]['box'][2] <= f.sc.w, 'last label runs off the page'
    print(f'label row packed: {len(pills)} pills on y={ys.pop()}')

    r = subprocess.run([sys.executable, str(HERE / 'precheck.py'), str(out)], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        print('FAIL: precheck reported hard findings')
        return 1
    print('selftest OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
