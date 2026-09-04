# Build notes (2026-09-03 rebuild)

`main.pdf` is a genuine TeX build of `main.tex` (xelatex → bibtex → xelatex ×2 via `scripts/build_tex.sh`): 19 pages, SHA256 `02edc4ab154d5637fa25f94027776457757c45e549aefed4e025cfe8f75afe88`, `tools/pdf_guard.py` PASS, 3 Overfull boxes (all ≤ 6.5 pt), 0 LaTeX errors.

It replaces the 2026-09-03 headless-Chrome render (Producer `Skia/PDF`) that had no abstract block, no numbered headings, system fonts and black citations.

Source repairs applied before the rebuild (scientific content unchanged):
- bibliography pruned to the keys actually cited in the text; the complete screened corpus is kept as `../evidence/references_corpus.bib` (bib_guard: 100 % integration);
- `tools/bib_polish.py`: redundant `url` dropped where a DOI exists, chemical formulas / acronyms / element prefixes brace-protected, spaced formulas merged, bare `&` escaped;
- `tools/tex_polish.py`: breakable prose slashes, `\\bibliography{references}`;
- figures rebuilt from the figspec sources recovered from this run's MCP trace (`../figures/{figspec,svg,drawio,pdf}/`) and embedded as vector PDF instead of SVG/PNG previews;
- LaTeX errors the browser render had silently swallowed (stray `$`, missing table row terminator) fixed; a 514-key "grouped citation" dump replaced by a role/count coverage table where present.

Gates on this folder: tex_guard PASS · bib_guard PASS · academic_language_guard PASS · pdf_guard PASS.
