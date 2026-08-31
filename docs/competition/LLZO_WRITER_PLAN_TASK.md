# LLZO final-survey planning task

Act as `goai-survey-writer`. Read `AGENTS.md`,
`skills/goai-survey-writer/SKILL.md`, `workspace/inputs/{topic,scope}.md`,
`workspace/library/papers.jsonl`, `workspace/library/references.bib`, all current
`workspace/notes/search_*.md`, `workspace/style_bank/writing_style_cards.md`,
`workspace/state/CITATION_AUDIT.md`, and the two open reviewer issues in
`workspace/state/review_diagnostic.md`.

The user has now explicitly requested the final PDF. The host therefore adopts
the previously recommended contribution bundle A+B+C so the pipeline may
continue. Record that assumption clearly. Do not claim that the current
46-paper standard-scale collection is comprehensive.

Required work:

1. Rewrite `workspace/notes/contribution.md` as a confirmed A+B+C contribution.
2. Refactor `workspace/notes/taxonomy.md` into a faceted framework:
   - primary process chain: powder synthesis -> phase/composition control ->
     thermal treatment/densification -> structure/transport readout;
   - composition/environment modifiers as a cross-cutting facet;
   - comparability/reproducibility as an evidence facet.
   Do not call the complete faceted framework a single MECE tree. Preserve DOI
   and citation-key traceability.
3. Build `workspace/notes/citation_bank.md`. Every key must come from the
   audited BibTeX. Claims based only on title/abstract must say so and avoid
   unsupported quantitative/mechanistic assertions.
4. Build `workspace/notes/research_gaps.md` with at least five gaps. Each gap
   needs at least two audited citation keys, source provenance, the observed
   evidence limitation, and a falsifiable next action. Do not present a missing
   metadata field as proof that no experiment exists.
5. Build `workspace/drafts/blueprint.md` for an English, evidence-limited,
   8--12 page review. It must support A+B+C, include the existing LLZO process
   map, and include a clearly boxed model-assisted precursor diagnostic whose
   chemical routes are unverified and NOT FOR LAB USE.
6. Run the applicable deterministic checks and write
   `workspace/state/llzo_writer_plan_validation.md` with commands, results,
   limitations, and exact handoff instructions for the manuscript writer.

Do not write the manuscript in this task. Do not add bibliography entries or
invent facts. Use `apply_patch` for edits.
