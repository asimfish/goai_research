# LLZO diagnostic adversarial review

## Review status

**FAIL / return for routed repair: 0 blocker, 4 major, 0 minor.** This is a fresh-session same-model cold-start review; **同模型审稿，独立性受限**. It is provisional and cannot independently support final release. `review_pass` was deliberately not set.

## Structured findings

### RD-01 — major — target: taxonomy

- Location: `workspace/notes/taxonomy.md:9-14`; `workspace/notes/taxonomy_validation.md:3,30`
- Dimension: taxonomy organization and validation
- Finding: The claimed process-chain/MECE taxonomy mixes serial process stages, a cross-cutting environment layer, and a structure/performance evidence-readout layer. A unique primary assignment of papers does not prove that the categories themselves are mutually exclusive. The validation report's headline `PASS` covers only mechanical key/count checks and can be mistaken for semantic MECE validation.
- Required resolution: separate process stages from cross-cutting modifiers and outcome/evidence dimensions, or explicitly present a faceted taxonomy; rename/scope the validation result so mechanical PASS is not semantic PASS; add explicit boundary tests for ambiguous pairs such as A1/B3, C3/D1, and D/E.
- Evidence: the taxonomy itself defines D as boundary conditions and E as cross-process evidence, while the validator disclaims semantic checking.

### RD-02 — major — target: figures

- Location: `workspace/figures/figspec/llzo_process_map.json:274-313`; `workspace/notes/figure_plan.md:59-60,88,94-97`
- Dimension: figure–text consistency and cross-file state
- Finding: The generic process narrative is drawn only through the middle chips (`syn2→ph2→den2→out2`), visually privileging one route in each family while leaving sibling routes disconnected. The environment narrative says D1–D3 frame sintering, but `env1` has no edge. The plan/ledger also say no PNG was produced although a PNG artifact exists.
- Required resolution: connect stage/group semantics without selecting arbitrary middle leaves (or explicitly label the shown path as an example), represent the D1 boundary relation consistently, and synchronize artifact/provenance statements with the actual files. Revalidate both SVG and drawio from one figspec.
- Evidence: rendered figure inspection plus the explicit figspec endpoints and caption.

### RD-03 — major — target: ideas

- Location: `workspace/ideas/experiment_llzo_diagnostic.json:4-8,24-33`; `workspace/ideas/proposal_llzo_diagnostic.md:7,30`; ledger events at 10:40:02Z and 10:50:24Z
- Dimension: cross-file state consistency
- Finding: Provider and plan state are contradictory: the experiment file reports top-level provider `stub` but the selected route/plan report `local_two_stage_inorganic` and `provider_verified=true`; the proposal simultaneously describes an empty Top-1 plan skeleton and a repaired one-step plan. These cannot all describe the current diagnostic state.
- Required resolution: choose a single current-state schema, distinguish historical pre-repair observations from current outputs, regenerate the derived proposal/status fields, and make provider trust/readiness terminology consistent across retro, experiment, proposal, and ledger.

### RD-04 — major — target: ideas

- Location: `workspace/ideas/proposal_llzo_diagnostic.md:9-33`; `workspace/ideas/experiment_llzo_diagnostic.json:35-56`; `workspace/ideas/retro_llzo_top5.json`
- Dimension: evidence, novelty, feasibility, and safety
- Finding: The artifacts establish an adapter/model smoke test, not yet a reviewable scientific idea or experiment proposal. The conventional-looking Top-1 precursor set is chemically unverified; conditions, controls, discriminating hypothesis, quantitative acceptance criteria, and route-specific evidence are absent. The proposal itself does not claim a literature gap. Safety handling is appropriately conservative and is not the defect.
- Required resolution: either relabel the deliverable strictly as infrastructure diagnostics, or formulate a falsifiable research question with verified route-specific evidence, comparators/controls, feasibility constraints, measurable thresholds, and human-approved safety/waste handling. Do not infer novelty from model rank. Resolve `LiHO`/`La(HO)3` entity normalization before any chemistry use.

## Citation assessment

`CITATION_AUDIT` reports 46 PASS, 0 non-PASS. Taxonomy keys are explicitly candidate anchors rather than claim-level proof. The proposal's two citations have canonical titles consistent with its limited background statements. No fake-reference or wrong-context issue is substantiated, and no additional `verify_entry` call was necessary. Metadata PASS still does not replace later full-text claim–citation validation.

## Safety assessment

No safety blocker: the route is marked chemically unverified, conditions remain null, each step has a nonempty safety warning, the proposal says `NOT FOR LAB USE`, and human materials-chemistry approval is mandatory. The current safe disposition must remain until route evidence and detailed hazard/waste review exist.

## What is strong

The artifacts use unusually disciplined uncertainty labels: title/abstract-level taxonomy support is not promoted to factual mechanism, the figure explicitly denies proven causality, model scores are not called reaction-success probabilities, and the experimental diagnostic is fail-closed. The SVG is legible and the required SVG/drawio pair exists. These strengths should be preserved during repair.

## Decision

Four majors require routed repair. No `review_pass` gate change is authorized or made. A later independent-model review remains necessary for a non-provisional release decision.
