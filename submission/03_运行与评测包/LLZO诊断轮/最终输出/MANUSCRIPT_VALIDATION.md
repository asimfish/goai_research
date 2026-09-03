# LLZO manuscript validation

## Deliverable status (rebuilt 2026-09-03 with TeX)

`main.pdf` is now a genuine TeX build of `main.tex` (xelatex → bibtex → xelatex ×2,
Producer `MiKTeX-dvipdfmx`, 16 pages, 151003 bytes, SHA256 `47b9555e0a4f49a5c45f8f6ff4014a53cb68e145e378868f09b0f8e983f8f8ad`), replacing the
2026-08-29 headless-Chrome render that had no abstract block, no numbered headings,
system fonts and black citations. Gates passed on the shipped sources:
`tex_guard` PASS (0 blocking), `bib_guard` PASS (46/46 keys integrated, 15.7 cites per
1,000 words, 0 field-hygiene warnings after `tools/bib_polish.py`),
`academic_language_guard` PASS, `tools/pdf_guard.py` PASS (TeX producer, NewTX/TeX Gyre
Termes fonts, fresh against sources, Abstract block, numbered headings).
Changes made for the rebuild: figure embedded from `figures/pdf/llzo_process_map.pdf`
(exported from the same `.drawio`) instead of `\includesvg`; bibliography titles brace-
protected and redundant `url` fields dropped (`bib_polish`); prose slashes made breakable
(`tex_polish`), which removed all Overfull boxes. Scientific content unchanged.

## Historical record (superseded)

The source bundle and host-rendered PDF are complete. The primary deliverable is
`final_report.pdf`; `main.pdf` and `LLZO_Synthesis_Survey.pdf` are byte-identical
aliases for the pipeline and descriptive naming conventions.

- Rendered: 2026-08-29 with local headless Google Chrome 142 from
  `report.html`.
- PDF: A4, 10 pages, 474,968 bytes, tagged, unencrypted, embedded fonts.
- Visual inspection: pages 1--4 and 7--10 checked from rasterized output; title,
  table, process map, warning box, and complete reference list were not clipped.
- SHA256: `095c39e58e690d478d3f6796f9a9a74acac905c54737ff1d5722555c71faf2cb`.
- Text audit: the extracted PDF contains the 46-record boundary, complete
  model-warning fields, and the `NOT FOR LAB USE` statement.

## Evidence and citation integration

- Audited bibliography: 46 entries, copied byte-for-byte from
  `workspace/library/references.bib`.
- TeX integration: 46/46 unique audited keys, or 100% integration.
- TeX citation density: 15.8 cited keys per 1,000 words under the repository
  `bib_guard.py` counter (93 cited-key occurrences; 5,886 regex-counted section
  tokens).
- Undefined TeX citation keys: 0.
- HTML references: 46 numbered entries; 46 unique in-text reference targets;
  all citation links resolve to an entry in the same file.
- Claim policy: the 25 records with stored abstracts support only statements
  represented in those abstracts. The 21 title-only records are used only for
  topic placement. No title-only record carries a numerical, mechanistic, or
  superiority claim.

Deterministic TeX citation check:

```bash
python3 tools/bib_guard.py submission/llzo_survey/sections \
  submission/llzo_survey/references.bib \
  --min-integration 0.9 --min-cites-per-1k 8
```

Expected result: `PASS`, 46/46 unique keys, 100% integration, and 15.8 cited
keys per 1,000 words.

## Word count and alignment

- TeX narrative: 5,552 whitespace-delimited source tokens (189 in the abstract
  and 5,363 across the eleven section files). This count includes LaTeX markup
  tokens and is recorded for reproducibility rather than presented as a
  publisher word count.
- Repository citation-density denominator: 5,886 regex-counted section tokens.
- HTML argument before the reference list: 2,673 alphanumeric word tokens.
- TeX and HTML contain the same title, authorship, evidence boundary, A+B+C
  contribution bundle, process-map argument, three route families, composition
  and densification analysis, cross-cutting modifiers, minimum comparison
  record, six gaps, model Top-5 diagnostic, limitations, and conclusion. The HTML
  is a condensed rendering, not an independent scientific argument.

## Structural validation

The repository completeness gate was run on the staged manuscript:

```bash
python3 tools/tex_guard.py workspace/drafts
```

Result: `PASS`; 12 TeX files checked, three labels, two references, no blocking
placeholder, missing input/figure, dangling reference, or delimiter error.

The process-map SVG, editable drawio, and figspec are copied without
modification from the existing figure bundle. The HTML uses the SVG; TeX uses
the same SVG through `\includesvg`. The PNG is included only as a rendering
fallback, not as figure provenance.

## Unresolved evidence limitations

1. The 46-record collection is standard-scale and non-comprehensive. It is not
   a systematic-search completeness claim.
2. Only 25 records contain locally stored abstracts; 21 are title-only, and
   full-text checking was selective. Metadata integrity does not validate claim
   context.
3. Only two audited records fall in 2024--2026. The manuscript does not claim
   adequate coverage of the newest literature.
4. Numerical performance meta-analysis was not attempted because composition,
   thermal history, density basis, conductivity definition, test temperature,
   and uncertainty are not uniformly available.
5. The six research gaps are limitations of discrimination in this collection,
   not proof that the field has never performed the proposed experiments.
6. `style_bank_ready` remains WARN-level, and `super_library` was unavailable.
7. Reviewer issue I4 remains open. Manuscript warning language does not close or
   resolve the underlying idea-artifact evidence/safety issue.

## Model diagnostic status

- Actual Top-1 set: `ZrO2 + La2O3 + Li2CO3`.
- The five displayed sets exactly match `data/retro_llzo_top5.json` and are
  reported only as model-ranked sets.
- `LiHO` and `La(HO)3` remain visible nomenclature/entity-normalization warnings.
- `model_output_verified=true`.
- `chemical_route_verified=false`.
- `conditions=null`.
- Status in the companion diagnostic remains
  `BLOCKED_PENDING_HUMAN_SAFETY_AND_REVIEW`.
- `NOT FOR LAB USE`; the box is not an experimentally actionable idea.

## Exact render instructions

### TeX to the expected `main.pdf`

Requirements: XeLaTeX, BibTeX, the LaTeX packages imported by `main.tex`, and
Inkscape available to the `svg` package.

```bash
cd submission/llzo_survey
xelatex -shell-escape -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -shell-escape -interaction=nonstopmode -halt-on-error main.tex
xelatex -shell-escape -interaction=nonstopmode -halt-on-error main.tex
```

Equivalent `latexmk` command:

```bash
cd submission/llzo_survey
latexmk -xelatex -shell-escape -interaction=nonstopmode -halt-on-error main.tex
```

### HTML to a print PDF

Open `report.html` in a current browser and use Print → Save as PDF with A4,
100% scale, and background graphics enabled. A Chromium command-line equivalent
is:

```bash
cd submission/llzo_survey
chromium --headless --disable-gpu \
  --print-to-pdf=report.pdf report.html
```

The host executed the equivalent local command with Google Chrome and
`--no-pdf-header-footer`. A TeX-native PDF was not compiled on this host because
XeLaTeX/BibTeX are unavailable; the validated TeX sources are retained for a
TeX-enabled environment.
