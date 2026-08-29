# Deliverables — full_run_20260828

Topic: Covalent Organic Frameworks for Photocatalytic Hydrogen Evolution:
Linkage Chemistry, Band-Structure Engineering, and the Path to Scalable Solar Fuels

Loop: round 1/5, stage final, 12/12 gates PASS (`state/ledger.json`).

## Final manuscript

| Artifact | Path | Note |
|---|---|---|
| Survey PDF (26 pp) | `paper/main.pdf` | xelatex 4-pass, 0 undefined refs, Times stack, blue citations |
| LaTeX source | `paper/main.tex` + `paper/sections/01..08_*.tex` | 8 sections, paper-orchestra typography |
| Bibliography | `paper/references.bib` | 143 entries, DOI 100%, & escaped, title case protected |

Writing metrics (bib_guard): 330 cite calls, 51.2 cites/1k words,
integration 143/143 = 100%. tex_guard PASS (17 labels, 13 refs).

## Figures (four-artifact sets, Draw.io editable)

| Figure | figspec | SVG | Draw.io | PDF | PNG |
|---|---|---|---|---|---|
| Fig 1 factor chain | `figures/figspec/fig1_factor_chain.json` | `figures/svg/…svg` | `figures/drawio/…drawio` | `figures/pdf/…pdf` | `figures/png/…png` |
| Fig 2 TpPa-1 idea route | `figures/figspec/fig2_tppa1_idea.json` | `figures/svg/…svg` | `figures/drawio/…drawio` | `figures/pdf/…pdf` | `figures/png/…png` |

AI candidate rounds preserved in `figures/candidates/`. Render pipeline:
`reports/render_figures.py` (figspec → svg/drawio → draw.io CLI pdf+png).

## Literature corpus

| Artifact | Path | Note |
|---|---|---|
| Audited records | `library/papers.jsonl` | 143 papers, 6 subtopics, all quotas met |
| BibTeX | `library/references.bib` | Crossref/S2 verified, 2 bad entries dropped |
| Audit trail | `reports/ref_audit_per_entry.jsonl`, `reports/ref_audit_corrections.md` | per-entry evidence |
| Coverage report | `reports/lit_coverage_pre_audit.json` | comprehensive tier PASS |
| Search logs | `notes/search_log.md`, `reports/search_query_log.json` | multi-source queries |

Known limitation: full-text PDFs not bulk-downloaded (`library/pdfs/` empty);
audit was metadata-level with 100% DOI verification.

## Style bank

- `style_bank/writing_style_cards.md` — writing rules distilled from 30 classic surveys
- `style_bank/figure_style_cards.md` — figure style rules
- `style_bank/exemplar_surveys.jsonl` — 30 exemplar survey records
- `style_bank/pdfs/` — 4 open-access exemplar PDFs (paywall limited)

## Idea (pre-registered)

- `ideas/idea_tppa1_route.md` — mixed-linker D–A doping of TpPa-1;
  gates G1–G4, pre-committed fallbacks, safety plan. Paper Section 6 + Fig 2.

## Citation support bank

- `notes/citation_bank.md` — 236 claims / 143 keys, 63% recent
- generator: `reports/build_citation_bank.py` (bank_check PASS)

## Gate evidence

- `reports/tex_guard_out.txt`, `reports/bib_guard_out.txt`, `reports/bank_check_out.txt`
- `state/ledger.json` — 12 gates, full audit timeline

## System fixes fed back to repo (this run)

1. `tools/bib_guard.py` — cross-line `\cite{...}` parsing (line-scan → full-text scan)
2. bib sanitation: bare `&` escaping + title-case protection for 56 titles
   (workspace data; escaping to be folded into `server/core/bibtex.py` emitter)
