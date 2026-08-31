# LLZO final manuscript task

Act as `goai-survey-writer` in manuscript and assembly stages. Read fully:

- `AGENTS.md` and `skills/goai-survey-writer/SKILL.md`;
- `workspace/inputs/{topic,scope}.md`;
- `workspace/notes/{contribution,taxonomy,citation_bank,research_gaps,style_notes}.md`;
- `workspace/drafts/blueprint.md`;
- `workspace/library/papers.jsonl` and `workspace/library/references.bib`;
- `workspace/state/{CITATION_AUDIT,llzo_writer_plan_validation}.md`;
- `workspace/ideas/{retro_llzo_top5,experiment_llzo_diagnostic}.json` and
  `workspace/ideas/proposal_llzo_diagnostic.md`;
- `workspace/notes/figure_plan.md`.

Write the evidence-limited final manuscript. It is an English, standard-scale
evidence-mapped review, not a comprehensive review. Do not imply full-text
verification where only titles/abstracts were read. Do not invent numerical
performance values, mechanisms, experimental conditions, or bibliography.

## Deliverables

Create a self-contained, version-controlled bundle in
`submission/llzo_survey/`:

1. `main.tex` plus `sections/*.tex`, following the repository survey style.
2. `references.bib`, containing the exact audited 46-entry library.
3. `report.html`, a print-ready standalone HTML rendering of the same argument.
   Use numbered in-text citations linked to a complete 46-entry reference list.
4. `MANUSCRIPT_VALIDATION.md`, recording citation integration, word count,
   unresolved evidence limitations, model diagnostic status, and exact render
   instructions.
5. `README.md`, identifying the PDF and all source files.

Use the authors and affiliations supplied by the team:

- Jing Gao — Shanghai Jiao Tong University — doctoral researcher;
- Dingyang Lü — University of Chinese Academy of Sciences — doctoral researcher;
- Yufeng Li — Shanghai Jiao Tong University — doctoral researcher.

## Required structure and content

- Balanced 2--3 line title and an abstract that says 46 audited records.
- Scope and evidence method.
- The A+B+C contribution bundle.
- Faceted framework overview with the existing process-map figure.
- Powder-synthesis routes.
- Composition/phase stabilization.
- Thermal treatment and densification.
- Cross-cutting process environment/additives.
- Structure--transport evidence and the minimum comparability record.
- Six evidence-bounded research gaps.
- A boxed model-assisted precursor diagnostic. Report the real Top-1 set
  ZrO2 + La2O3 + Li2CO3 and the actual Top-5 output only as model-ranked sets.
  Explicitly flag `LiHO` and `La(HO)3` as nomenclature/entity-normalization
  warnings. State `chemical_route_verified=false`, `conditions=null`, and
  `NOT FOR LAB USE`.
- Limitations and conclusion.
- Complete references.

Integrate at least 42 of 46 unique audited keys in the manuscript. Every factual
claim needs a nearby citation. Prefer calibrated synthesis and comparison over
claim-heavy prose. Keep HTML and TeX substantively aligned. Do not call I4
closed and do not claim an experimentally actionable idea.

Use `apply_patch` for authored text. Existing generated figure assets may be
copied into the submission bundle without modification. Do not compile PDF in
this task; the host will render and inspect it.
