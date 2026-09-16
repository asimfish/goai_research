"""The default figure builder: the four-tier framework plus the card surface an author picked over five rounds.

The chosen candidates moved the module accent from a top bar to a LEFT bar, made group labels larger and
bolder, and put the glyph inline with the title (or above it) rather than always left of it. This subclass adds
those, plus the two card shapes the picked layouts use:

  card_stack  — glyph + title row, then light item tokens filling the rest (fig01 evidence, fig03 evidence)
  card_step   — big step number, centred glyph, centred title, one hairline, one key-point strip (roadmap)

Everything else (zone / chain / vchain / ledger / token / pill / conn / axis / finish) comes from Framework unchanged.
"""
from .scene import Scene
from .framework import (Framework, FAM, CONN, ITEM, TOKEN_EDGE, TOKEN_FILL, INK,  # noqa: F401
                          W_CARD, W_TOKEN, W_STEP, W_RULE)

HAIR = '#CBD5DE'


class Figure(Framework):
    # ------------------------------------------------------------------ tier 1
    def zone(self, zid, box, label=None, fam='lit', label_size=None, label_pos='top'):
        """Group band. Labels are noticeably larger and bolder than round 4's."""
        label_size = label_size or self.size('group', 26)
        return super().zone(zid, box, label=label, fam=fam, label_size=label_size, label_pos=label_pos)

    # ------------------------------------------------------------------ tier 2
    def card(self, cid, box, fam='lit', dashed=False, container=None, bar=11, fill=None):
        """Bare module card with a left accent bar — the shape every picked candidate uses."""
        f = FAM[fam]
        x, y, w, h = box
        self.sc.shape(cid, box, fill=(fill or '#FFFFFF'), stroke=f['edge'], stroke_width=W_CARD, radius=9,
                      dash=[12, 8] if dashed else None, container=container)
        if not dashed and bar > 0:
            self.sc.shape(cid + '_b', [x, y, bar, h], fill=f['accent'], stroke=None, radius=3, container=cid)
        return cid

    def card_stack(self, cid, box, title, items, fam='lit', glyph=None, dashed=False, container=None,
                   title_size=None, item_size=None, glyph_w=40, pad=16, bar=8, fill=None, gap=10, sub=None,
                   title_lines=1, item_align='center'):
        """Left-bar card: glyph + title on one row, then light item tokens filling the rest of the card."""
        title_size = title_size or self.size('title', 25)
        item_size = item_size or self.size('body', 19)
        f = FAM[fam]
        x, y, w, h = box
        self.card(cid, box, fam=fam, dashed=dashed, container=container, bar=bar, fill=fill)
        tx = x + bar + pad
        th = int(title_size * 1.72) if title_lines == 1 else int(title_size * 1.42 * title_lines + title_size * 0.4)
        sh = int(item_size * 1.75) if sub else 0
        # only a card with item tokens stacks from the top; title (+subtitle) alone is centred in the card
        ty = y + pad if items else y + (h - th - (sh + 4 if sub else 0)) / 2
        if glyph:
            self.m.draw(glyph, cid + '_g', [tx, ty + (th - glyph_w) / 2, glyph_w, glyph_w], container=cid)
            tx += glyph_w + 12
        self.sc.text(cid + '_t', [tx, ty, x + w - pad - tx, th], title, title_size, bold=True, color=f['text'],
                     align='left', container=cid, font_group='r5title', fit='shrink',
                     min_font_size=self.shrink_floor(title_size, 5), wrap=title_lines > 1)
        cy = ty + th
        if sub:
            self.sc.text(cid + '_s', [tx, cy + 4, x + w - pad - tx, sh], sub, item_size, color=ITEM,
                         bold=self.bold('body'), align='left', container=cid, font_group='r5sub', fit='shrink',
                         min_font_size=self.shrink_floor(item_size, 4))
            cy += sh + 4
        if items:
            top = cy + gap
            n = len(items)
            ih = (y + h - pad - top - gap * (n - 1)) / n
            ix = x + bar + pad
            for k, it in enumerate(items):
                self.token(f'{cid}_i{k}', [ix, top + k * (ih + gap), x + w - pad - ix, ih], it,
                           size=item_size, container=cid, align=item_align)
        return cid

    def card_step(self, cid, box, num, title, point, fam='lit', glyph=None, container=None,
                  num_size=None, title_size=None, point_size=None, glyph_w=96, pad=20, bar=13, fill=None):
        """Numbered step card: number top-left, glyph beside it, centred title, hairline, key-point strip."""
        num_size = num_size or self.size('number', 38)
        title_size = title_size or self.size('title', 28)
        point_size = point_size or self.size('body', 20)
        f = FAM[fam]
        x, y, w, h = box
        self.card(cid, box, fam=fam, container=container, bar=bar, fill=fill)
        self.sc.text(cid + '_n', [x + bar + pad, y + pad, 92, int(num_size * 1.7)], num, num_size, bold=True,
                     color=f['text'], align='left', container=cid, font_group='r5num')
        if glyph:
            self.m.draw(glyph, cid + '_g', [x + w - pad - glyph_w - 18, y + pad - 4, glyph_w, glyph_w], container=cid)
        th = int(title_size * 1.6)
        ty = y + pad + glyph_w + 6
        self.sc.text(cid + '_t', [x + bar + pad, ty, w - bar - 2 * pad, th], title, title_size, bold=True,
                     color=f['text'], align='center', container=cid, font_group='r5steptitle')
        ry = ty + th + 14
        self.sc.line(cid + '_r', [(x + bar + pad + 6, ry), (x + w - pad - 6, ry)], stroke=HAIR, width=W_RULE,
                     container=cid)
        ph = int(point_size * 1.8)
        self.token(cid + '_p', [x + bar + pad, y + h - pad - ph, w - bar - 2 * pad, ph], point,
                   size=point_size, container=cid)
        return cid

    # ------------------------------------------------------------------ tier 3
    def row(self, rid, box, items, container=None, size=None, gap=12, arrow=True, widths=None):
        """Horizontal token row; with arrow=True the tokens are joined by short arrows (a source-grounded chain).

        widths: optional per-token widths (px). Without them the row splits evenly, which starves a long item.
        """
        size = size or self.size('body', 19)
        x, y, w, h = box
        n = len(items)
        if widths is None:
            widths = [(w - gap * (n - 1)) / n] * n
        tx = x
        for k, it in enumerate(items):
            tw = widths[k]
            if k:
                tx += widths[k - 1] + gap
            self.token(f'{rid}_t{k}', [tx, y, tw, h], it, size=size, container=container)
            if k and arrow:
                a0, a1 = tx - gap + 5, tx - 5
                hl = max(4.0, min(9.0, (a1 - a0) * 0.55))
                self.sc.line(f'{rid}_a{k}', [(a0, y + h / 2), (a1, y + h / 2)], stroke=CONN, width=W_STEP,
                             arrow=True, head={'length': hl, 'width': max(4.0, hl * 0.9)}, container=container)

    def check_rows(self, rid, box, items, container=None, size=None, gap=10):
        """Ledger rows with a leading checkbox glyph — fig01's 相同实验项目下比较."""
        size = size or self.size('body', 20)
        x, y, w, h = box
        n = len(items)
        ih = (h - gap * (n - 1)) / n
        for k, it in enumerate(items):
            ty = y + k * (ih + gap)
            self.sc.shape(f'{rid}_r{k}', [x, ty, w, ih], fill=TOKEN_FILL, stroke=TOKEN_EDGE, stroke_width=W_TOKEN, radius=6, container=container)
            bs = min(int(size * 0.8) if self.T else 22, ih - 10)
            self.m.draw('checkbox', f'{rid}_c{k}', [x + 12, ty + (ih - bs) / 2, bs, bs], container=f'{rid}_r{k}')
            lh = max(int(size * 1.75), int(ih - 6)) if self.T else int(size * 1.75)
            self.sc.text(f'{rid}_x{k}', [x + 12 + bs + 12, ty + (ih - lh) / 2, w - bs - 40, lh],
                         it, size, color=ITEM, bold=self.bold('body'), align='left', container=f'{rid}_r{k}',
                         font_group='r5ledger')

    def col_item(self, cid, box, label, glyph, container=None, size=None, glyph_w=46):
        """One ledger column: glyph + tick on top, label under — fig02's 统一实验记录."""
        size = size or self.size('body', 20)
        x, y, w, h = box
        self.m.draw(glyph, cid + '_g', [x + w / 2 - glyph_w - 8, y, glyph_w, glyph_w], container=container)
        self.m.draw('tick_circle', cid + '_k', [x + w / 2 + 12, y + 6, 34, 34], container=container)
        self.sc.text(cid + '_t', [x, y + glyph_w + 12, w, int(size * 1.6)], label, size, color=ITEM,
                     bold=self.bold('body'), align='center', container=container, font_group='r5col', fit='shrink',
                     min_font_size=self.shrink_floor(size, 4))


R5 = Figure   # the name this class carried while it lived in the BYZSO project
