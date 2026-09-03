# LLZO survey submission bundle

> Housekeeping note (2026-09-03): this folder is the final output of run #2 (LLZO diagnostic, 2026-08-29; see docs/competition/SUBMISSION.md §3). Of the three byte-identical PDFs only `main.pdf` is kept; the derived `report.html` was removed. Ledger, MCP audit log, task prompts and per-task JSONL traces of this run are in the parent folder `../`.

This directory is the self-contained source bundle for:

> **From Powder to Comparable Transport Data: A Faceted Review of LLZO
> Synthesis, Phase Control, and Densification**

Authors: Jing Gao (Shanghai Jiao Tong University), Dingyang Lü (University of
Chinese Academy of Sciences), and Yufeng Li (Shanghai Jiao Tong University); all
are identified in the manuscript as doctoral researchers.

## PDF status

The host rendered and visually inspected the manuscript on 2026-08-29:

- `final_report.pdf` — official submission filename;
- `main.pdf` — filename expected by the pipeline protocol;
- `LLZO_Synthesis_Survey.pdf` — descriptive filename.

The three files are byte-identical (SHA256
`095c39e58e690d478d3f6796f9a9a74acac905c54737ff1d5722555c71faf2cb`).
The PDF is A4, 10 pages, and has embedded fonts. Exact source and render details
are recorded in `MANUSCRIPT_VALIDATION.md`.

## Primary files

- `main.tex` — TeX entry point and abstract.
- `report.html` — standalone, print-ready HTML argument with inline CSS,
  numbered linked citations, and the complete 46-entry reference list.
- `references.bib` — exact audited 46-entry bibliography.
- `MANUSCRIPT_VALIDATION.md` — citation, word-count, evidence-limit, model, and
  render record.
- `revision_log.md` — manuscript drafting and refinement record.

## TeX sections

- `sections/01_introduction.tex`
- `sections/02_scope_evidence.tex`
- `sections/03_framework.tex`
- `sections/04_powder_synthesis.tex`
- `sections/05_phase_control.tex`
- `sections/06_densification.tex`
- `sections/07_environment_additives.tex`
- `sections/08_structure_transport.tex`
- `sections/09_research_gaps.tex`
- `sections/10_model_diagnostic.tex`
- `sections/11_limitations_conclusion.tex`

## Figure sources and renderings

- `figures/figspec/llzo_process_map.json` — single-source figure specification.
- `figures/drawio/llzo_process_map.drawio` — editable figure.
- `figures/svg/llzo_process_map.svg` — publication and HTML figure.
- `figures/png/llzo_process_map.png` — preview/fallback only.

The SVG and drawio were generated from the figspec before this manuscript task
and were copied without modification. The figure encodes process order and
boundary-condition checks, not proven causality.

## Model-diagnostic provenance

- `data/retro_llzo_top5.json` — raw model-ranked Top-5 sets.
- `data/experiment_llzo_diagnostic.json` — diagnostic status and null conditions.
- `data/proposal_llzo_diagnostic.md` — unresolved idea-artifact provenance.

These files are included so the boxed diagnostic is auditable. They do not
constitute a chemical route or laboratory protocol. `chemical_route_verified`
remains `false`, `conditions` remains `null`, issue I4 remains open, and all
model-ranked sets are **NOT FOR LAB USE**.
