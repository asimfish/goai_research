# Ink budget and type metrics

These numbers are not taste. Each one was set by an author rejecting the previous value, and the figures the
author finally accepted use exactly this budget. Change one only with a reason, and change it in
`lib/framework.py` so every figure moves together.

## Type scale — in PRINTED points, one size per role

Sizes are declared on paper, not in px. A figure passes `print_width_pt` (its placed width in the paper) and
every builder derives px from this table, so every figure in every paper sets the same role at the same size.
A figure that does not declare its print width is a round-5 legacy scene and keeps its literal px sizes.

| Role | Chinese (`TYPE_PT`) | English (`TYPE_PT_EN`) | Weight |
|---|---|---|---|
| Group label | 9.5 pt | 8.5 pt | bold |
| Card title | 9.0 pt | 8.0 pt | bold |
| Step number | 12.0 pt | 11.0 pt | bold |
| Body / record item | 8.0 pt | 7.0 pt | **regular** |
| Edge label / caveat | 7.5 pt | 7.0 pt | **regular** |
| Floor (incl. `fit=shrink` minimum) | 7.0 pt | 7.0 pt | — |

Why these, measured on the compiled papers (round 5 → round 6):
- body text printed at **5.2–5.8 pt**, labels at 5.2–5.5 pt, and the same role differed by up to 2× between
  figures. The caption is 9 pt; top-venue figure text sits at 7–9 pt.
- **every string was bold** (round 5's answer to "make the text more visible"), which erased the difference
  between a heading and the text under it. The real problem was size, not weight.
- English runs one step smaller: Latin stays legible at 7 pt (Nature sets figure text at 5–7 pt) while CJK
  strokes need more, and English strings are ~1.6× wider.

**Two weights only.** Bold marks structure (group, card title, step number); everything read as content is
regular. `Noto Sans CJK SC Medium` looked like the obvious middle weight, but LibreOffice 7.3 strips "Medium"
from the family name and renders Regular — the PDF embeds only Regular and Bold — and a reader's PowerPoint
may not have Medium installed either.

**Print width is read from the compiled PDF, never estimated.** The placed width of each embedded figure is
`print_audit.py`'s job. Estimating the text width from body lines was 8% off (403.5 pt against a real 435.2 pt).
In these papers the placed width depends only on the template language: Chinese 435.2 pt, English 451.4 pt.

The crop matters too: install_fig crops to the render plus a 14 px margin, so content spanning x 26–1510 of a
1536 canvas prints across `canvas − 24` px. Keep zones on that span or the scale drifts.

## Stroke weights (px, at a 1536-wide canvas)

| Role | Constant | Value | Was |
|---|---|---|---|
| Group zone border | `W_ZONE` | 1.6 | 1.2 |
| Module card border | `W_CARD` | 1.9 | 1.4 |
| Record token border | `W_TOKEN` | 1.6 | 1.2 |
| Connector | `W_CONN` | 2.5 | 1.8 |
| In-card step arrow | `W_STEP` | 2.2 | 1.6 |
| Label pill border | `W_PILL` | 1.6 | 1.1 |
| Hairline rule | `W_RULE` | 1.6 | 1.0 |
| Connector arrow head | `HEAD` | 15 × 12 | 12 × 10 |
| Left accent bar | `card(bar=…)` | 10–13 | 7–10 |
| Glyph stroke | `Motifs(width=…)` | 2.7 | 2.0 |
| Glyph stroke floor | `max(s, 0.85)` in `motifs.py` | 0.85 | 0.5 |

**The floor is the one people miss.** Raising `Motifs(width=…)` alone leaves small glyphs thin, because each
sub-stroke scales by a per-glyph factor `s` and the floor clamps it. A 40 px glyph at floor 0.5 draws at 1.35 px
no matter what the base width says. If icons still look weak after a weight bump, the floor is why.

## Ink colours

| Role | Value | Note |
|---|---|---|
| Glyph / heading ink | `INK` `#111A24` | |
| Body and record text | `ITEM` `#27303A` | regular weight at print size; the old `#3F4854` read washed out |
| Connector | `CONN` `#3C4753` | |
| Hairline | `HAIR` `#CBD5DE` | |
| Token fill / edge | `#F4F7FA` / `#AEBBC7` | edge was `#CBD3DA`, too faint |

Four semantic families in `FAM`, never more: `lit` (evidence, slate blue), `exp` (method, teal), `note`
(caveat, amber), `mute` (out of scope, grey). Amber is reserved for caveats — putting a normal band in amber
was one of the defects a generated candidate introduced.

## CJK type metrics

- Real line height ≈ **1.46 em + 0.5 px**. A box at `size * 1.45` overflows; the builders use 1.6 (body),
  1.7 (step number), 1.72 (title), 1.75 (sub).
- **Bold CJK sets ≈ 5% wider.** `Scene.measure(text, size, bold=True)` applies it. Forgetting this makes the
  local precheck read every bolded string as an overflow.
- Width model: CJK 1.0 em, Latin/digits 0.62 em, space 0.3 em, + 4 px. It lands within 1–2 px of the real
  render for mixed-script strings, which is close enough to size a pill.
- Latin replacing CJK runs roughly 1.6× wider. See `scripts/relayout.py`.

## Print legibility

Run `scripts/print_audit.py --paper <compiled.pdf> <figure.pdf>=<scene.json> …` after every compile. It finds
each figure's placement in the paper and prints the size of every role; it fails below 7 pt. Then look at the
page itself (`pdftoppm` of the paper) — a standalone figure PDF always looks fine.

Larger type needs room, and the room is the empty space inside cards: round 5's cards were only 14–48% filled.
Size cards from their content (measure, then lay out), let a title or item wrap to a second line rather than
shrink it, and let the canvas height follow the content instead of fixing it at 1024.
