# Ink budget and type metrics

These numbers are not taste. Each one was set by an author rejecting the previous value, and the figures the
author finally accepted use exactly this budget. Change one only with a reason, and change it in
`lib/framework.py` so every figure moves together.

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
| Body and record text | `ITEM` `#27303A` | **bold**; regular `#3F4854` read washed out |
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

At `\linewidth` on a 1536 px canvas, 19 px text lands near 6 pt. Below that, re-compose — a single wide row
becomes 3+3. Check the figure **in the compiled page** (`pdftoppm` of the paper), never only in the standalone
figure PDF: the standalone always looks fine.
