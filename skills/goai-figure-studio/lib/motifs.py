"""One line-art glyph family, drawn as native scene primitives.

Round 3 used raster crops of the generated image as icons: their stroke weights, optical sizes and backgrounds differed
from glyph to glyph, which is what broke the figures' visual consistency. These motifs are drawn instead from the scene's
own shapes and lines, so every glyph shares one ink colour and one stroke weight, scales cleanly in the PDF and stays
editable in PowerPoint. Each motif is authored in a normalised 100x100 cell and mapped onto the requested box.

Style follows the skill's vector library (`assets/vector-library/.../ppt_safe/*.svg`): monochrome, no fill, uniform
stroke, flat geometry, no baked text.
"""
INK = '#1F2937'


class Motifs:
    def __init__(self, sc, ink=INK, width=2.0):
        self.sc = sc; self.ink = ink; self.w = width

    # ---------------------------------------------------------------- helpers
    def _m(self, box):
        x, y, w, h = box; s = min(w, h) / 100.0
        ox = x + (w - 100 * s) / 2; oy = y + (h - 100 * s) / 2
        return (lambda px, py: (ox + px * s, oy + py * s)), s

    def _line(self, gid, pts, p, s, dash=None, width=None):
        """Polyline as consecutive 2-point segments (the scene schema allows only two points per line);
        the joints between them are declared so the geometry check reads them as one stroke."""
        q = [p(a, b) for a, b in pts]
        ids = []
        for k in range(len(q) - 1):
            sid = f'{gid}_{k}' if len(q) > 2 else gid
            self.sc.line(sid, [q[k], q[k + 1]], stroke=self.ink, width=(width or self.w) * max(s, 0.85),
                         dash=([d * s for d in dash] if dash else None))
            ids.append(sid)
        if len(ids) > 1:
            for el in self.sc.els:
                if el['id'] in ids:
                    el['allow_overlap_with'] = sorted(set(el.get('allow_overlap_with', []) + [i for i in ids if i != el['id']]))
                    el['overlap_reason'] = 'joints of one line-art glyph stroke'
        return ids

    def _rect(self, gid, box, p, s, dash=None, shape='rect', radius=0, fill=None):
        x0, y0, x1, y1 = box; a = p(x0, y0); b = p(x1, y1)
        self.sc.shape(gid, [a[0], a[1], b[0] - a[0], b[1] - a[1]], shape=shape, fill=fill, stroke=self.ink,
                      stroke_width=self.w * max(s, 0.85), radius=radius * s,
                      dash=([d * s for d in dash] if dash else None))

    def _dot(self, gid, cx, cy, r, p, s, fill=None):
        a = p(cx - r, cy - r); b = p(cx + r, cy + r)
        self.sc.shape(gid, [a[0], a[1], b[0] - a[0], b[1] - a[1]], shape='ellipse', fill=fill,
                      stroke=(None if fill else self.ink), stroke_width=self.w * max(s, 0.85))

    def draw(self, name, gid, box, container=None):
        """Draw one glyph and declare it as a single visual unit: its own strokes may overlap each other and, when a
        container is given, the card that holds it."""
        before = {e['id'] for e in self.sc.els}
        NAMES[name](self, gid, box)
        ids = [e['id'] for e in self.sc.els if e['id'] not in before]
        for el in self.sc.els:
            if el['id'] in ids:
                mates = [i for i in ids if i != el['id']] + ([container] if container else [])
                el['allow_overlap_with'] = sorted(set(el.get('allow_overlap_with', []) + mates))
                el['overlap_reason'] = 'strokes of one line-art glyph'
                if container: el['container'] = container
        if container:
            for el in self.sc.els:
                if el['id'] == container:
                    el['allow_overlap_with'] = sorted(set(el.get('allow_overlap_with', []) + ids))
                    el['overlap_reason'] = 'line-art glyph drawn inside the card'
        return ids

    # ---------------------------------------------------------------- glyphs
    def doc(self, gid, box, n=1, struck=False, question=False):
        """document sheet / stack of sheets / struck-out sheet"""
        p, s = self._m(box)
        for k in range(n - 1, -1, -1):
            o = k * 9
            self._rect(f'{gid}_s{k}', (18 + o, 14 + o, 66 + o, 86 + o), p, s, radius=3)
        self._line(gid + '_l1', [(30, 40), (62, 40)], p, s)
        self._line(gid + '_l2', [(30, 54), (62, 54)], p, s)
        self._line(gid + '_l3', [(30, 68), (52, 68)], p, s)
        if struck: self._line(gid + '_x', [(14, 90), (86, 10)], p, s)
        if question: self._line(gid + '_q', [(40, 44), (56, 44), (56, 60), (48, 60), (48, 70)], p, s)

    def polyhedron(self, gid, box):
        p, s = self._m(box)
        self._line(gid + '_o', [(50, 8), (90, 34), (72, 88), (28, 88), (10, 34), (50, 8)], p, s)
        self._line(gid + '_a', [(50, 8), (50, 88)], p, s)
        self._line(gid + '_b', [(10, 34), (90, 34)], p, s)

    def crucible(self, gid, box, crystal=False):
        p, s = self._m(box)
        self._line(gid + '_b', [(22, 30), (32, 84), (68, 84), (78, 30)], p, s)
        self._line(gid + '_r', [(16, 30), (84, 30)], p, s)
        if crystal:
            self._line(gid + '_c', [(50, 8), (62, 22), (50, 30), (38, 22), (50, 8)], p, s)

    def flame(self, gid, box):
        p, s = self._m(box)
        self._line(gid + '_f', [(50, 10), (66, 34), (58, 42), (50, 32), (42, 42), (34, 34), (50, 10)], p, s)
        self._line(gid + '_b', [(24, 56), (32, 88), (68, 88), (76, 56)], p, s)
        self._line(gid + '_r', [(18, 56), (82, 56)], p, s)

    def pellet(self, gid, box):
        p, s = self._m(box)
        self._rect(gid + '_e1', (16, 26, 84, 46), p, s, shape='ellipse')
        self._line(gid + '_s1', [(16, 36), (16, 64)], p, s)
        self._line(gid + '_s2', [(84, 36), (84, 64)], p, s)
        self._rect(gid + '_e2', (16, 54, 84, 74), p, s, shape='ellipse')

    def mill(self, gid, box):
        p, s = self._m(box)
        self._rect(gid + '_j', (20, 22, 80, 86), p, s, shape='round_rect', radius=10)
        self._line(gid + '_c', [(20, 34), (80, 34)], p, s)
        for k, (cx, cy) in enumerate(((36, 56), (58, 50), (50, 72))):
            self._dot(f'{gid}_b{k}', cx, cy, 8, p, s)

    def pull(self, gid, box):
        p, s = self._m(box)
        self._line(gid + '_r', [(50, 6), (50, 34)], p, s)
        self._line(gid + '_c', [(50, 34), (64, 52), (50, 70), (36, 52), (50, 34)], p, s)
        self._line(gid + '_m', [(24, 76), (30, 92), (70, 92), (76, 76)], p, s)
        self._line(gid + '_t', [(18, 76), (82, 76)], p, s)

    def furnace(self, gid, box):
        p, s = self._m(box)
        self._rect(gid + '_b', (12, 24, 88, 84), p, s, radius=4)
        self._line(gid + '_d', [(34, 24), (34, 84)], p, s)
        for k, x in enumerate((52, 64, 76)):
            self._line(f'{gid}_h{k}', [(x, 44), (x - 6, 54), (x, 64)], p, s)

    def grid(self, gid, box, rows=3, cols=3):
        p, s = self._m(box)
        self._rect(gid + '_b', (12, 18, 88, 84), p, s, radius=3)
        for k in range(1, rows):
            y = 18 + k * (66 / rows); self._line(f'{gid}_r{k}', [(12, y), (88, y)], p, s)
        for k in range(1, cols):
            x = 12 + k * (76 / cols); self._line(f'{gid}_c{k}', [(x, 18), (x, 84)], p, s)

    def trace(self, gid, box, check=False):
        p, s = self._m(box)
        self._line(gid + '_a', [(10, 82), (26, 82), (32, 34), (38, 82), (50, 82), (56, 50), (62, 82), (74, 82), (78, 62), (82, 82), (92, 82)], p, s)
        if check: self._line(gid + '_k', [(64, 24), (72, 34), (90, 10)], p, s)

    def dots(self, gid, box):
        p, s = self._m(box)
        for k, (cx, r) in enumerate(((24, 14), (50, 10), (76, 7))):
            self._dot(f'{gid}_d{k}', cx, 50, r, p, s, fill=self.ink)

    def curve(self, gid, box):
        p, s = self._m(box)
        self._line(gid + '_a', [(10, 84), (28, 84), (42, 26), (66, 26), (80, 84), (92, 84)], p, s)

    def thermo(self, gid, box):
        p, s = self._m(box)
        self._rect(gid + '_t', (40, 8, 60, 66), p, s, shape='round_rect', radius=10)
        self._dot(gid + '_b', 50, 80, 16, p, s)
        for k, y in enumerate((24, 36, 48)):
            self._line(f'{gid}_m{k}', [(62, y), (74, y)], p, s)

    def balance(self, gid, box):
        p, s = self._m(box)
        self._line(gid + '_p', [(50, 14), (50, 78)], p, s)
        self._line(gid + '_b', [(16, 28), (84, 28)], p, s)
        self._line(gid + '_l', [(16, 28), (6, 50), (26, 50), (16, 28)], p, s)
        self._line(gid + '_r', [(84, 28), (74, 50), (94, 50), (84, 28)], p, s)
        self._line(gid + '_f', [(30, 86), (70, 86)], p, s)

    def checklist(self, gid, box):
        p, s = self._m(box)
        for k, y in enumerate((20, 46, 72)):
            self._rect(f'{gid}_b{k}', (12, y, 32, y + 20), p, s, radius=3)
            self._line(f'{gid}_l{k}', [(44, y + 10), (90, y + 10)], p, s)
            if k < 2: self._line(f'{gid}_k{k}', [(16, y + 11), (21, y + 16), (30, y + 4)], p, s)

    def lattice(self, gid, box, sub=True):
        p, s = self._m(box)
        for k, v in enumerate((18, 50, 82)):
            self._line(f'{gid}_h{k}', [(18, v), (82, v)], p, s)
            self._line(f'{gid}_v{k}', [(v, 18), (v, 82)], p, s)
        for i, cx in enumerate((18, 50, 82)):
            for j, cy in enumerate((18, 50, 82)):
                filled = sub and i == 1 and j == 1
                self._dot(f'{gid}_d{i}{j}', cx, cy, 7, p, s, fill=(self.ink if filled else '#FFFFFF'))

    def droplet(self, gid, box):
        p, s = self._m(box)
        self._line(gid + '_d', [(50, 10), (74, 46), (62, 68), (38, 68), (26, 46), (50, 10)], p, s)
        for k, (cx, cy) in enumerate(((36, 84), (54, 88), (70, 80))):
            self._dot(f'{gid}_n{k}', cx, cy, 6, p, s, fill=self.ink)

    def funnel(self, gid, box):
        p, s = self._m(box)
        self._line(gid + '_f', [(12, 18), (88, 18), (58, 58), (58, 88), (42, 88), (42, 58), (12, 18)], p, s)

    def cycle(self, gid, box):
        p, s = self._m(box)
        self._rect(gid + '_o', (16, 16, 84, 84), p, s, shape='ellipse')
        self._line(gid + '_a', [(72, 22), (86, 26), (82, 40)], p, s)

    def triangle(self, gid, box):
        p, s = self._m(box)
        self._line(gid + '_t', [(50, 10), (90, 86), (10, 86), (50, 10)], p, s)
        self._line(gid + '_i', [(50, 10), (62, 60), (10, 86)], p, s)
        self._dot(gid + '_d', 68, 68, 6, p, s, fill=self.ink)

    def flow(self, gid, box):
        p, s = self._m(box)
        self._rect(gid + '_a', (34, 10, 66, 32), p, s, radius=3)
        self._rect(gid + '_b', (8, 62, 40, 84), p, s, radius=3)
        self._rect(gid + '_c', (60, 62, 92, 84), p, s, radius=3)
        self._line(gid + '_s', [(50, 32), (50, 48)], p, s)
        self._line(gid + '_h', [(24, 48), (76, 48)], p, s)
        self._line(gid + '_l', [(24, 48), (24, 62)], p, s)
        self._line(gid + '_r', [(76, 48), (76, 62)], p, s)

    def boundary(self, gid, box):
        p, s = self._m(box)
        self._rect(gid + '_b', (12, 20, 88, 82), p, s, radius=4, dash=[7, 6])

    # ---- round 5 additions: the two marks the picked layouts use as ledger affordances
    def checkbox(self, gid, box):
        p, s = self._m(box)
        self._rect(gid + '_b', (8, 8, 92, 92), p, s, radius=8)
        self._line(gid + '_k', [(26, 52), (44, 70), (76, 30)], p, s, width=self.w * 1.3)

    def tick_circle(self, gid, box):
        p, s = self._m(box)
        self._rect(gid + '_c', (8, 8, 92, 92), p, s, shape='ellipse')
        self._line(gid + '_k', [(28, 52), (44, 68), (74, 32)], p, s, width=self.w * 1.3)

    def target(self, gid, box):
        p, s = self._m(box)
        self._rect(gid + '_o', (20, 20, 80, 80), p, s, shape='ellipse')
        self._rect(gid + '_i', (40, 40, 60, 60), p, s, shape='ellipse')
        for a, b, c, d in ((50, 6, 50, 22), (50, 78, 50, 94), (6, 50, 22, 50), (78, 50, 94, 50)):
            self._line(f'{gid}_t{a}{b}', [(a, b), (c, d)], p, s)

    def cubes(self, gid, box):
        p, s = self._m(box)
        self._rect(gid + '_a', (36, 8, 64, 36), p, s, radius=3)
        self._rect(gid + '_b', (6, 60, 34, 88), p, s, radius=3)
        self._rect(gid + '_c', (66, 60, 94, 88), p, s, radius=3)
        self._line(gid + '_l', [(50, 36), (20, 60)], p, s)
        self._line(gid + '_r', [(50, 36), (80, 60)], p, s)

    def layers(self, gid, box):
        p, s = self._m(box)
        for k, dy in enumerate((0, 22, 44)):
            self._line(f'{gid}_d{k}', [(50, 14 + dy), (88, 32 + dy), (50, 50 + dy), (12, 32 + dy), (50, 14 + dy)], p, s)

    def crystals(self, gid, box):
        p, s = self._m(box)
        self._line(gid + '_a', [(38, 92), (24, 46), (40, 20), (52, 50), (38, 92)], p, s)
        self._line(gid + '_b', [(62, 92), (54, 54), (68, 34), (80, 58), (72, 92)], p, s)

    def flask(self, gid, box):
        p, s = self._m(box)
        self._line(gid + '_n', [(40, 10), (40, 38), (14, 88), (86, 88), (60, 38), (60, 10)], p, s)
        self._line(gid + '_m', [(36, 10), (64, 10)], p, s)
        self._dot(gid + '_d1', 42, 70, 4, p, s)
        self._dot(gid + '_d2', 58, 76, 3, p, s)

    def beaker(self, gid, box):
        p, s = self._m(box)
        self._line(gid + '_b', [(24, 12), (24, 84), (36, 92), (64, 92), (76, 84), (76, 12)], p, s)
        self._line(gid + '_t', [(18, 12), (82, 12)], p, s)
        self._dot(gid + '_d1', 42, 60, 4, p, s)
        self._dot(gid + '_d2', 58, 70, 3, p, s)

    def bowl(self, gid, box):
        p, s = self._m(box)
        self._line(gid + '_b', [(12, 26), (24, 88), (76, 88), (88, 26)], p, s)
        self._line(gid + '_r', [(6, 26), (94, 26)], p, s)
        self._line(gid + '_w', [(20, 48), (34, 40), (50, 48), (66, 40), (80, 48)], p, s)


NAMES = {
    'checkbox': lambda m, g, b: m.checkbox(g, b), 'tick_circle': lambda m, g, b: m.tick_circle(g, b),
    'target': lambda m, g, b: m.target(g, b), 'cubes': lambda m, g, b: m.cubes(g, b),
    'layers': lambda m, g, b: m.layers(g, b), 'crystals': lambda m, g, b: m.crystals(g, b),
    'flask': lambda m, g, b: m.flask(g, b), 'beaker': lambda m, g, b: m.beaker(g, b),
    'bowl': lambda m, g, b: m.bowl(g, b),
    'doc': lambda m, g, b: m.doc(g, b, 1), 'docs': lambda m, g, b: m.doc(g, b, 3),
    'doc_struck': lambda m, g, b: m.doc(g, b, 1, struck=True), 'doc_q': lambda m, g, b: m.doc(g, b, 1, question=True),
    'polyhedron': lambda m, g, b: m.polyhedron(g, b), 'crucible': lambda m, g, b: m.crucible(g, b),
    'crucible_crystal': lambda m, g, b: m.crucible(g, b, crystal=True), 'flame': lambda m, g, b: m.flame(g, b),
    'pellet': lambda m, g, b: m.pellet(g, b), 'mill': lambda m, g, b: m.mill(g, b), 'pull': lambda m, g, b: m.pull(g, b),
    'furnace': lambda m, g, b: m.furnace(g, b), 'grid': lambda m, g, b: m.grid(g, b),
    'trace': lambda m, g, b: m.trace(g, b), 'trace_check': lambda m, g, b: m.trace(g, b, check=True),
    'dots': lambda m, g, b: m.dots(g, b), 'curve': lambda m, g, b: m.curve(g, b), 'thermo': lambda m, g, b: m.thermo(g, b),
    'balance': lambda m, g, b: m.balance(g, b), 'checklist': lambda m, g, b: m.checklist(g, b),
    'lattice': lambda m, g, b: m.lattice(g, b), 'droplet': lambda m, g, b: m.droplet(g, b),
    'funnel': lambda m, g, b: m.funnel(g, b), 'cycle': lambda m, g, b: m.cycle(g, b),
    'triangle': lambda m, g, b: m.triangle(g, b), 'flow': lambda m, g, b: m.flow(g, b),
    'boundary': lambda m, g, b: m.boundary(g, b),
}
