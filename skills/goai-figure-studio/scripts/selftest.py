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
from lib import Figure, pack_pill_rows, TYPE_PT, TYPE_PT_EN, MIN_PRINT_PT, BOLD_ROLES
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


def fake_build(root, lang):
    """The files install_fig.py reads from an img2ppt build, with a per-language marker in each record."""
    import json
    import pypdfium2 as pdfium
    from PIL import Image, ImageDraw
    b = root / f'build_{lang}'
    (b / 'render').mkdir(parents=True)
    (b / 'svg').mkdir()
    im = Image.new('RGB', (400, 300), 'white')
    ImageDraw.Draw(im).rectangle([40, 40, 360, 260], fill='black')
    im.save(b / 'render' / 'page_001.png')
    doc = pdfium.PdfDocument.new()
    doc.new_page(400, 300)
    doc.save(str(b / 'render' / 'editable.pdf'))
    (b / 'svg' / 'page_001.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    (b / 'editable.pptx').write_bytes(lang.encode())
    for rec in ('scene.resolved.json', 'validation.json', 'fonts.json'):
        (b / rec).write_text(json.dumps({'lang': lang}))
    return b


def install_both(root):
    import json
    fig, media = root / 'fig', root / 'media'
    fig.mkdir()
    for lang, name in (('zh', 'demo'), ('en', 'demo_en')):
        b = fake_build(root, lang)
        subprocess.run([sys.executable, str(HERE / 'install_fig.py'), '--build', str(b),
                        '--s5', str(b / 'render' / 'page_001.png'), '--project', 'demo', '--name', name,
                        '--figdir', str(fig), '--crop', 'render', '--media', str(media)],
                       check=True, capture_output=True)
    d, m = fig / 'figstudio' / 'demo' / 'deliverables', media / 'demo'
    for lang, sfx in (('zh', ''), ('en', '_en')):
        for rec in ('scene.resolved', 'validation', 'fonts'):
            got = json.loads((d / f'{rec}{sfx}.json').read_text())['lang']
            assert got == lang, f'{rec}{sfx}.json holds the {got} record'
        assert (m / f'render{sfx}.png').exists(), f'render{sfx}.png missing from the gallery'


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

    # print-scale mode: sizes come from the printed table, only headings are bold, nothing prints under the floor
    for scale, pw in ((TYPE_PT, 435.2), (TYPE_PT_EN, 451.4)):
        g = Figure(1536, 400, print_width_pt=pw, type_scale=scale)
        for role, pt in scale.items():
            got = g.T[role] * g.pt_per_px
            assert abs(got - max(pt, MIN_PRINT_PT)) < 0.25, f'{role}: {got:.2f} pt, wanted {pt}'
            assert got >= MIN_PRINT_PT - 0.05, f'{role} prints below the floor'
        assert g.bold('title') and g.bold('group') and g.bold('number')
        assert not g.bold('body') and not g.bold('label'), 'body/label must be regular in print-scale mode'
        z = g.zone('z', [26, 20, 1484, 360], '分组', 'lit')
        g.card_stack('c', [60, 90, 600, 200], '标题', ['条目一', '条目二'], fam='lit', container=z)
        weights = {e['id']: e.get('bold') for e in g.sc.els if e['kind'] == 'text'}
        assert weights['c_t'] and weights['z_l'] and not weights['c_i0_t'], weights
    print('print scale: sizes, floor and two-weight hierarchy OK')

    # the printed-size gate must reject a scene whose text would print below the floor
    tiny = Figure(1536, 300, print_width_pt=435.2)
    tiny.sc.text('t', [40, 40, 600, 40], '太小的字', 18, color='#27303A')
    tiny_path = out.with_name('tiny.json')
    tiny.write(tiny_path)
    r = subprocess.run([sys.executable, str(HERE / 'precheck.py'), str(tiny_path)], capture_output=True, text=True)
    assert r.returncode and 'print_too_small' in r.stdout, 'precheck let 5 pt text through'
    print('precheck rejects text below the printed floor')

    # installing the Chinese and English variants into one project must keep both sets of records
    install_both(out.parent)
    print('install keeps the Chinese and English records apart')

    r = subprocess.run([sys.executable, str(HERE / 'precheck.py'), str(out)], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        print('FAIL: precheck reported hard findings')
        return 1
    print('selftest OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
