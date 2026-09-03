# Review round 1, trace 1

Review initiated 2026-09-03. Product-first inspection in progress.

## Product-first evidence

- `python3 tools/loopctl.py status` showed round 1, stage `review`, and no open
  issues at start. `GOAI_WORKSPACE` resolved to
  `<HOME>
- File inventory confirmed `drafts/main.tex`, 11 section files, `drafts/main.pdf`,
  `notes/figure_plan.md`, and three SVG/Draw.io pairs.
- `pdfinfo drafts/main.pdf`: 25 pages, 612×792 pt letter, ReportLab producer,
  unembedded WinAnsi/Type1 fonts. `pdfimages -list` found three raster images at
  1300 px wide and about 194 dpi (pages 2, 3, and 6).
- `pdftotext -layout` was run for the full PDF and then separately for pages 1–25.
  Anomaly scan found `[t]`, `[Figure]`, “the corresponding figure or section”,
  `P0.23P0.25...`, and `G=_i n_i_i(T,P,x)` on the manuscript pages; replacement
  glyph `■` occurred on reference pages 9–21 and 24–25.
- All 25 page renders were placed in a contact sheet and visually checked. High
  resolution visual checks confirmed: page 1 placeholder text in the Introduction;
  page 2 malformed Gibbs expression; page 4 serialized/flattened prior-results and
  thermodynamics tables; page 6 tiny raster bottleneck map and parser artifacts;
  pages 9, 24, and 25 black replacement glyphs in bibliography metadata.
- SVGs were rendered to temporary PNGs for visual inspection. Roadmap is clear;
  taxonomy is legible but repeats the `structure motif` edge label; bottleneck map
  is generally legible with dense edge labels. No out-of-bounds content was seen.
- Draw.io XML parse: `phase_bottlenecks` 7 vertices/9 edges, `roadmap` 8/5,
  `taxonomy_overview` 13/11; every edge had both `source` and `target`.

## Checks run

Commands (using `.venv/bin/python` where applicable):

```
.venv/bin/python tools/bib_guard.py "$GOAI_WORKSPACE/drafts" "$GOAI_WORKSPACE/library/references.bib"
.venv/bin/python tools/tex_guard.py "$GOAI_WORKSPACE/drafts"
.venv/bin/python tools/academic_language_guard.py "$GOAI_WORKSPACE/drafts"
```

Results: bib guard PASS (745 citation calls, 511 unique keys, 100% integration)
with 704 field-hygiene warnings; TeX guard PASS; academic-language guard PASS.
The figure MCP validator returned `ok=true`, empty `errors`, `typo_errors`, and
`typo_warnings` for all three figspecs; figure inventory returned all three
figspec/SVG/Draw.io triplets present.

## Historical comparison and routing

Only after the product checks, `revision_log.md`, scope/coverage/taxonomy/contribution
notes, and the prior idea-review note were read. The prior note was a provisional
same-model idea review and did not audit this final manuscript/PDF. Six issues were
then routed with `loopctl issue add`: I1 writing major, I2 figures major, I3 ref_gate
major, I4 writing major, I5 ideas major, and I6 figures minor. No source artifact was
edited. Because the required cross-model channel was unavailable, this trace records
a cold-start self-review rather than a fabricated independent-model exchange.
