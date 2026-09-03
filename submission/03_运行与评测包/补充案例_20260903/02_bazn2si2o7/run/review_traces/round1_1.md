# Round 1 independent-review trace

Model: same-model cold-start fallback (no cross-model channel available)

## Review prompt

Read `drafts/main.tex`, all `drafts/sections/*.tex`, `drafts/main.pdf`, `inputs/scope.md`, `notes/taxonomy.md`, `notes/figure_plan.md`, and `state/CITATION_AUDIT.md`. Review as three independent perspectives: inorganic-materials expert, methods/claim-citation auditor, and journal production editor. Do not use the writer's self-evaluation. Check coverage, structural-analogue claim strength, literature support, figure/text consistency, language, tables, and every page of the final PDF.

## Raw response

### Domain expert

The core distinction between direct BaZn2Si2O7 evidence and the unverified Ba5Y12Zn[O(SiO4)]8 target is appropriately conservative. The manuscript covers polymorphism, Ba/Sr and Zn-site substitution, glass crystallization, phase-diagram gaps, and analogue criteria. A remaining weakness is that the PDF is shorter than the LaTeX manuscript and omits several details present in the sections; the deliverable PDF therefore does not faithfully represent the source.

### Methods and citation auditor

The LaTeX source binds factual claims to 32 verified bibliography keys, with 100% integration and no undefined citations. However, the fallback HTML/PDF strips all numerical citation markers; readers cannot connect claims to the reference list. This is a major reproducibility and production defect, even though the underlying TeX is correctly cited.

### Journal production editor

Both figures are legible and use restrained colors. The first page has a browser-generated date/time header and a local file path footer; all pages show browser headers/footers. These are unacceptable in a publication-style PDF. The bibliography is present but the PDF is only three pages and is a condensed HTML rendering, not the complete LaTeX article. The environment limitation is legitimate, but the final PDF still needs clean page furniture and visible citation markers.

### Verdict

0 blocker, 2 major, 0 minor. Route both issues to writing/production, then re-review the regenerated PDF page by page. Because this is a same-model fallback, any later PASS is provisional pending independent-model review.
