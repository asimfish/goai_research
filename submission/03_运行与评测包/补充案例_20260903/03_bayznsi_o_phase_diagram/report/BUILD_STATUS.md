# Build status (2026-09-03)

**PDF intentionally not shipped yet.** The earlier `main.pdf` in this folder was an HTML→headless-Chrome render (Producer `Skia/PDF`): no abstract block, no numbered headings, system fonts, black citations. It fails `tools/pdf_guard.py` and has been removed rather than passed off as a compiled manuscript.

Source state after the 2026-09-03 repair (all deterministic gates PASS on this folder):
`tex_guard` PASS · `bib_guard` PASS (100 % integration) · `academic_language_guard` PASS · full xelatex build succeeds with placeholder figures (0 errors).

Fixes applied to the sources: bibliography pruned to the keys actually cited in the text (the complete screened corpus is kept as `../evidence/references_corpus.bib`); `bib_polish` (drop redundant `url`, brace-protect formulas/acronyms, escape `&`); `tex_polish` (breakable prose slashes, `\\bibliography{references}`); figure includes switched from SVG/PNG to vector PDF paths; LaTeX syntax errors that the Chrome render had silently swallowed were corrected.

To produce the deliverable PDF, export the figures from their figspec/drawio sources (kept in the run workspace) to `../figures/pdf/` — required files: figures/pdf/phase_bottlenecks.pdf figures/pdf/roadmap.pdf figures/pdf/taxonomy_overview.pdf — then run:

```bash
bash scripts/build_tex.sh "submission/03_运行与评测包/补充案例_20260903/03_bayznsi_o_phase_diagram/report"
```

which compiles (xelatex → bibtex → xelatex ×2) and runs `pdf_guard`. A PDF that does not pass `pdf_guard` must not be placed here.
