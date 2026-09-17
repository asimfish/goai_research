# Pitfalls

Every entry cost at least one round trip. Read before debugging something that looks new.

## Validator findings that are NOT defects

- **`renderer_font_substitution` on any Chinese figure.** LibreOffice embeds the Noto CJK subset as
  `NotoSansCJKsc-Bold-VKana`; the font-identity check compares name-table entries 1/4/6/16 and calls it a
  substitution. Same font file. This alone makes `validation.json` report `status: fail` for every CJK figure —
  an all-Latin figure of the same scene passes. Do not chase it, and do not report the figure as failed.
- **`rendered_ink_width_drift` on mixed-script strings** (`同类 Ba–Y 四方硅酸盐`, `配比 · 温度`). LibreOffice
  inserts automatic spacing between CJK and Latin runs, so rendered ink is 3–11% wider than the validator's own
  font-metric measurement. It is a review-level warning, not an overflow: check the box actually holds the
  rendered width before acting (it did every time so far).

## Layout

- **A row of connector labels must be packed, not placed one by one.** `conn(label=…)` positions each pill
  from its own anchor, so the row collides or falls off the page as soon as a string grows — a longer term, or
  a language change. `pack_pill_rows()` in `lib/framework.py` runs automatically inside `finish()`; call it
  again by hand after any pass that re-measures pills (the language pass does).
- **A label pill must be created after its connector segments**, or the line is drawn through the text.
- **On a stub shorter than ~2× the pill**, put the label above the line instead — otherwise the arrow head
  disappears under the pill.
- **Chain arrow heads need `head.length < segment length`.** Compute it from the gap:
  `hl = max(4.0, min(9.0, (a1 - a0) * 0.55))`.
- **A zero-width accent bar must be skipped, not drawn** (`if not dashed and bar > 0`).
- **Ledger tick marks must not list themselves** in `allow_overlap_with` — the checker rejects it as
  `invalid element reference`.
- **Caveat pills belong in the group header band**, not on top of a card. `zone(label_pos='bottom')` frees the
  header band when edge labels need it.
- **`font_group` shrinks its members together.** That is what you want for a row of sibling titles in one
  language, and exactly what you do not want after re-typing: the longest string would hold the whole group at
  the original size. The language pass drops `font_group` and gives each box its own floor.

## Fidelity

- **Generated candidates invent content.** They produce plausible-looking sub-steps that appear nowhere in the
  source (`文献检索 / 信息提取 / 关键数据` …). Diff every string against the paper and drop what is not
  grounded. Record the audit in the S3 record — the reconstruction is where this gets fixed.
- **Generated candidates also get direction wrong.** Observed: taxonomy branch arrows pointing into the hub
  instead of out of it; a fork feeding only one of two lanes; a band coloured amber that is not a caveat. The
  reconstruction is authored from the paper, not traced from the raster, so fix these rather than mirror them.
- **Never crop an icon out of the generated PNG.** Raster icon crops are what made the icon family look
  inconsistent across rounds 1–3. Use `lib/motifs.py`: one ink, one stroke weight, native geometry.

## Pipeline

- **Run the local precheck before shipping to the render host.** `scripts/precheck.py` predicts
  `text_overflow` / `text_shrunk` / `outside_container` / `unintended_overlap` with the same width model, so a
  bad box costs a second, not a round trip. Ship only at **0 hard findings**.
- **Crop from the reconstruction, not the raster** (`install_fig.py --crop render`) once the rebuild sets its
  own canvas usage. Cropping to the raster's bbox clipped a connector routed outside it (fig03 at x=14).
- **Remove stale `trim=…,clip`** from `\includegraphics` when replacing older figures — trims tuned for a
  loose PDF will cut a tight one.
- **Re-check the figure in the compiled paper page.** A standalone figure PDF always looks right.

## Round 6 (print-scale type)

- **A label pill over someone else's text is a defect, not an intended overlap.** `finish()` used to declare every
  pill overlap intentional, so a lane label pushed onto the hub title — or out of its zone by a sign error — still
  passed precheck. In print-scale mode a pill is exempt only against lines and zone tints; if it genuinely
  belongs to a card (a caveat in the card header), pass `pill(container=…)`.
- **Leave 5 px between a connector end and the card it leaves.** The stroke is 2.5 px wide; starting 2 px out puts
  half the line inside the card and the checker reports `unintended_overlap`.
- **Estimate line counts one reserve above the real width.** A measure that is 1 px conservative turns a
  one-line item into a two-line box and doubles the token height; check the render, not just the precheck.
- **Break long English terms where the language does, before shrinking.** `Mechanochemical` does not fit a
  route card at print size and cannot wrap; the standard two-word term `Mechanical Activation` does. A string
  with a hand-placed space inside a hyphenated word renders correctly but fails `rendered_text_mismatch`.
- **English edge labels do not fit a connector lane.** `pill(max_w=…)` wraps them to two lines; when even that is
  too wide (a single long word), move the label into the gap above the card instead of widening the lane.
- **A two-line label is ~86 px tall.** Size the band gap from the label's real height, or it rides into the cards
  above it and hides the arrow it labels.
- **Both language variants share one project directory.** `install_fig.py` once wrote `scene.resolved.json`,
  `validation.json`, `fonts.json` and the gallery `render.png` under fixed names, so the English install silently
  replaced the Chinese records and the gallery showed the English figure as "中文版". Records not already named
  after the figure now take the variant suffix (`validation_en.json`, `render_en.png`); selftest installs both
  variants and checks each record.

## Slides (deck figures, 2026-09-17)

- **img2ppt rejects an arrow whose head is not shorter than its last segment** (`arrow head must be shorter than the
  line and at least as wide as its stroke`) — the whole build fails, only validation.json comes back. Budget the gap:
  `HEAD` is 15 px, so a branch from a fork bus needs ≥ 20 px; `vchain(gap=10)` leaves a 4 px segment with a 4 px head
  and fails too — use gap ≥ 14. Check locally before shipping: every `arrow` line's last segment vs `arrow_head.length`.
- **A 19 px token is 34 px tall** (`box_h(body) + 2`), not 27: vertical budgets estimated from the font size alone put
  cards on top of each other. Size stacks from `box_h`, and let precheck's `outside_container` catch the rest.
- **A slide is one img2ppt page**: a 1536×864 canvas maps to 960×540 pt, so the shapes copy 1:1 into a 16:9 deck
  (`scripts/deck_merge.py`). Keep y < 122 px empty for the template's title bar; retype to the deck's font (微软雅黑)
  only in the merged copy — the render host has Noto, the author's PC has YaHei.
- **Deck titles at 28 pt wrap past ~24 CJK characters**; a two-line title pushes into the figure.
- **A two-line pill can still overflow by a glyph**: LibreOffice fills line 1 greedily, our split minimises the wider
  half; give wrapped pills `padx=30` or accept a 1 px `rendered_glyph_overflow` on the first glyph.

## Slides, round 2 (loop-engineering style, 2026-09-17)

- **The paper surface style on a talk slide reads as "low quality".** Muted four-family palette, line-art glyphs only and
  ~55 locked strings gave a flat org chart — natively AND from the image model, because the prompts enforced it. A slide
  needs a brief (title + one line per node), numbered pastel panels, flow kinds in colour with a legend, characters or
  small illustrations on core nodes, and an evidence strip. See SKILL.md C4c.
- **Image models keep the look and break the topology.** All eight S2 sketches drew parallel stages as serial chains, moved
  cards between phases or started the retry arc at the wrong node. Lock the semantics with a labelled blueprint render as
  the layout reference; all four conditioned bakes reproduced it.
- **Do not reject a raster over its pixel count.** "1536x1024" in the task made the agent skip four good 1672×941 images.
  Ask for the aspect, register the native size.
- **Asset sheets are not on an exact grid.** Equal-cell cropping cut into neighbours; split rows and columns at the widest
  ink-free bands instead, and flood-fill transparency only from the crop border (white inside the art must stay).
- **img2ppt lines are two-point.** A curved loop is a run of short segments (`Deck.arc` / `Deck.ubend`); the last one must
  stay longer than its arrow head, and a dashed arrow cannot carry a custom head (keep its last segment > 15 px).
- **A card shadow is a second shape**: declare its overlaps (the card, everything inside it, connectors ending at the edge)
  or the checker reports dozens of false overlaps.

## Slides, round 3 (deck theme + domain content, 2026-09-17)

- **img2ppt sets one CJK text line at 1.4565 × font size (+0.5 px reserve).** A `fit='strict'` single-line box lower than
  that fails the WHOLE build (only validation.json comes back). Give such boxes `int(1.5 × size) + 1`. The local precheck
  is looser on height, so "0 hard" locally does not guarantee the build. Digits / Latin lines are lower and unaffected.
- **The renderer sets bold Latin, " + " and " × " wider than `Scene.measure`.** Leave ~6 % slack on the grey one-liners in
  cards and avoid spaced operators ("路线×条件×表征", not "路线 × 条件 × 表征"); `rendered_glyph_overflow` is the symptom.
- Unicode subscripts (BaCO₃, Y₂O₃) render correctly with Noto CJK — keep formulas as editable text.
- Dashed arrows cannot carry a custom head and need a last segment > 15 px; the gap between two phase bands must be
  ≥ 28 px to hold a sequence arrow with a legible head.
- A label pill placed ON a curve hides most of it (layout B's return arc): put the pill beside the line.
- **Re-derive every number from the ledger before it goes on a slide.** Round 2 said "round-1 review 7 issues → round 2: 0";
  `ledger.json` (`round_opened`) says 5 + 2, and three of the nine gates are WARN, not PASS. Draw what the ledger says.
