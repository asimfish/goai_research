# Round 1 diagnostic adversarial review — raw trace

## Independence and scope

This review was performed as a fresh-session, same-model cold-start review because no independent cross-model review channel was used. **同模型审稿，独立性受限。** The artifacts were read before the ledger history. This result may open issues or reject readiness, but it is not an independent final-release decision and must not set `review_pass`.

Read set: `taxonomy.md`, `contribution.md`, `taxonomy_validation.md`, `figure_plan.md`, `llzo_process_map.json`, rendered SVG (including a visual inspection of the available PNG rendering), `retro_llzo_top5.json`, `experiment_llzo_diagnostic.json`, `proposal_llzo_diagnostic.md`; then `CITATION_AUDIT.md/.json` and the structured ledger history.

## Raw adversarial observations

1. The taxonomy calls its organizing axis a process chain and calls the result MECE, but it mixes manufacturing stages (A–D) with an evidence/readout layer (E). D is explicitly cross-cutting rather than a serial stage. The primary-assignment rule can make a paper inventory unique, but uniqueness of assigned papers is not the same as semantic mutual exclusivity of the categories. `taxonomy_validation.md` nevertheless headlines `PASS` while admitting that it checks only key existence and leaf counts. This is a semantic-validation gap, not a citation-fabrication finding.

2. The taxonomy is careful about citation limits: leaf keys are candidate literature anchors based mainly on title/abstract, not asserted claim-level evidence. `CITATION_AUDIT` reports 46/46 metadata PASS. The two citations in the diagnostic proposal have canonical titles matching the low-strength background statements made there. No concrete fake-reference or wrong-context allegation is justified. No `verify_entry` call was used; repeating the already-PASS metadata check would not establish claim context.

3. The figure is legible after the visual repair, and the evidence disclaimer is prominent. However, the solid process chain is implemented as `syn2→ph2→den2→out2`. It therefore visually selects sol–gel, Zr-site substitution, pressure/field assistance, and ionic transport while the other chips float unconnected. That contradicts the caption's generic claim that the map links route/control/readout families. Similarly, only `env2` and `env3` have dashed checks; `env1` (sintering additives) has none despite the plan saying D1–D3 directly frame sintering. This is a topology/semantics defect, not mere polish.

4. Figure-state provenance is also stale: `figure_plan.md` and the ledger state that PNG is unavailable / not produced, while `workspace/figures/png/llzo_process_map.png` is present and was visually inspectable. This does not invalidate the required SVG+drawio delivery, but the plan/ledger no longer fully describe the artifact set. It should be corrected together with the figure topology rather than opened as a cosmetic issue.

5. The idea artifacts correctly and repeatedly state `chemical_route_verified=false`, `conditions=null`, and `NOT FOR LAB USE`. Every experimental step has a nonempty safety warning and the whole diagnostic is blocked on human safety review. There is no unmarked executable chemical procedure, so a safety blocker would be unjustified.

6. The idea state is internally inconsistent. `experiment_llzo_diagnostic.json` says `provider_status.provider="stub"` while its top route and plan say `local_two_stage_inorganic` and `provider_verified=true`. The proposal first says the Top-1 plan skeleton has an empty step, but later says the repaired call returned exactly one step. The ledger records the earlier empty-plan state and then a repair, showing that stale text/state was not normalized after repair.

7. The Top-1 ZrO2 + La2O3 + Li2CO3 set is a model-ranked conventional-looking precursor set, not itself a novel research result. The proposal explicitly disclaims an unexplored direction, provides no conditions, no discriminating hypothesis, no comparator/control matrix, and no quantitative success/failure threshold. It is a useful adapter smoke test, but it cannot yet pass evidence, novelty, or feasibility review as a scientific idea or experiment proposal. The suspicious normalized strings `LiHO` and `La(HO)3` further reinforce that downstream chemistry review is still required, though they are not used as executable steps.

## Raw disposition

- Blocker: 0
- Major: 4
- Minor: 0
- Positive findings: cautious citation language; complete metadata audit; clear non-causality figure disclaimer; explicit unverified-route status; nonempty safety warnings and human approval gate.
- Decision: not ready; route four major issues. Do not set `review_pass`.

