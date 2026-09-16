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
