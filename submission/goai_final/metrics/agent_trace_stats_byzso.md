# Agent trace audit

| Task | Exit | MCP | Tool fn via cmd | Web search | Failed commands | Input tokens | Max event | Flags |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `lit_identity_structure` | 0 | 0 | 20 | 26 | 0 | 0 | 18440 | MISSING_FINAL |
| `lit_substitution_evidence` | 0 | 0 | 24 | 35 | 0 | 6730088 | 16208 | HIGH_INPUT_TOKENS |
| `lit_synthesis_routes` | 0 | 0 | 27 | 37 | 4 | 0 | 16394 | COMMAND_FAILURE, MISSING_FINAL |
| `style_bank` | 124 | 0 | 19 | 22 | 1 | 0 | 57762 | COMMAND_FAILURE, NONZERO_EXIT, MISSING_FINAL |
| `style_bank_retry` | 124 | 0 | 8 | 25 | 0 | 0 | 34320 | NONZERO_EXIT, MISSING_FINAL |
| `lit_merge_serial` | 0 | 0 | 9 | 1 | 0 | 1361740 | 20472 | HIGH_INPUT_TOKENS |
| `ref_guard` | 0 | 0 | 13 | 3 | 2 | 1497756 | 17839 | COMMAND_FAILURE, HIGH_INPUT_TOKENS |
| `ref_guard_retry` | None | 0 | 11 | 9 | 0 | 0 | 30062 | MISSING_FINAL |
| `ref_guard_serial` | 0 | 0 | 7 | 7 | 2 | 3000843 | 17644 | COMMAND_FAILURE, HIGH_INPUT_TOKENS |
| `ref_guard_resolution` | 0 | 0 | 5 | 0 | 2 | 0 | 1175079 | COMMAND_FAILURE, OVERSIZED_EVENT, MISSING_FINAL |
| `ref_guard_finalize` | 124 | 0 | 0 | 0 | 1 | 0 | 20579 | COMMAND_FAILURE, NONZERO_EXIT, MISSING_FINAL |
| `ref_guard_serial_finalize` | 0 | 0 | 0 | 0 | 1 | 351719 | 6321 | COMMAND_FAILURE, HIGH_INPUT_TOKENS |
| `taxonomy` | 0 | 0 | 0 | 0 | 0 | 0 | 17501 | MISSING_FINAL |
| `citation_bank` | 0 | 0 | 0 | 0 | 1 | 2116279 | 38601 | COMMAND_FAILURE, HIGH_INPUT_TOKENS |
| `fig01_evidence_map` | 124 | 0 | 4 | 0 | 0 | 0 | 27437 | NONZERO_EXIT, MISSING_FINAL |
| `fig02_route_variables` | 0 | 0 | 9 | 0 | 0 | 3057115 | 33660 | HIGH_INPUT_TOKENS |
| `fig01_phase_c_retry` | 0 | 0 | 14 | 0 | 0 | 2417169 | 34300 | HIGH_INPUT_TOKENS |
| `fig01_quality_fix` | 0 | 0 | 9 | 0 | 1 | 1075957 | 26995 | COMMAND_FAILURE, HIGH_INPUT_TOKENS |
| `figure_merge` | 3 | 0 | 1 | 0 | 0 | 1364973 | 42081 | HIGH_INPUT_TOKENS, NONZERO_EXIT |
| `blueprint_retrydep` | 0 | 0 | 0 | 0 | 0 | 1236211 | 18532 | HIGH_INPUT_TOKENS |
| `figure_merge_retry` | 0 | 0 | 0 | 0 | 0 | 665478 | 32611 | HIGH_INPUT_TOKENS |
| `write_conditions_neighbors` | 0 | 0 | 0 | 0 | 5 | 2754912 | 24097 | COMMAND_FAILURE, HIGH_INPUT_TOKENS |
| `write_identity_evidence` | 0 | 0 | 0 | 0 | 0 | 1280985 | 47886 | HIGH_INPUT_TOKENS |
| `write_validation_limits` | 0 | 0 | 0 | 0 | 0 | 1825615 | 32972 | HIGH_INPUT_TOKENS |
| `assemble_draft` | 124 | 0 | 0 | 0 | 16 | 0 | 179576 | COMMAND_FAILURE, NONZERO_EXIT, MISSING_FINAL |
| `assemble_draft_retry` | 0 | 0 | 0 | 2 | 8 | 0 | 312166 | COMMAND_FAILURE, OVERSIZED_EVENT, MISSING_FINAL |
| `review_round1` | 0 | 0 | 1 | 1 | 2 | 0 | 1057556 | COMMAND_FAILURE, OVERSIZED_EVENT, MISSING_FINAL |
| `review_round1_retry` | 124 | 0 | 6 | 17 | 1 | 0 | 20911 | COMMAND_FAILURE, NONZERO_EXIT, MISSING_FINAL |
| `review_round1_adjudicate` | 0 | 0 | 0 | 0 | 2 | 759976 | 26959 | COMMAND_FAILURE, HIGH_INPUT_TOKENS |
| `coverage_repair` | 0 | 0 | 17 | 1 | 0 | 1888734 | 25831 | HIGH_INPUT_TOKENS |
| `taxonomy_repair` | 0 | 0 | 0 | 0 | 0 | 354560 | 24947 | HIGH_INPUT_TOKENS |
| `ref_deduplicate` | 124 | 0 | 7 | 2 | 3 | 0 | 63226 | COMMAND_FAILURE, NONZERO_EXIT, MISSING_FINAL |
| `writing_repair` | 0 | 0 | 3 | 8 | 7 | 11535333 | 42974 | COMMAND_FAILURE, HIGH_INPUT_TOKENS |
| `review_round2_final` | 124 | 0 | 3 | 9 | 0 | 0 | 38438 | NONZERO_EXIT, MISSING_FINAL |
| `define_strength_axis` | 0 | 0 | 0 | 0 | 0 | 723345 | 42629 | HIGH_INPUT_TOKENS |
| `refresh_citation_audit` | 0 | 0 | 0 | 0 | 0 | 517327 | 6404 | HIGH_INPUT_TOKENS |
| `review_round2_adjudicate` | 124 | 0 | 0 | 0 | 0 | 0 | 22756 | NONZERO_EXIT, MISSING_FINAL |
| `figure_academic_repolish` | 0 | 0 | 7 | 0 | 0 | 10699456 | 52634 | HIGH_INPUT_TOKENS |
| `text_academic_repolish` | 0 | 0 | 0 | 0 | 0 | 5395523 | 79557 | HIGH_INPUT_TOKENS |
| `assemble_academic_repolish` | 0 | 0 | 0 | 0 | 1 | 8228383 | 46182 | COMMAND_FAILURE, HIGH_INPUT_TOKENS |

## Flag counts

- `COMMAND_FAILURE`: 18
- `HIGH_INPUT_TOKENS`: 24
- `MISSING_FINAL`: 16
- `NONZERO_EXIT`: 10
- `OVERSIZED_EVENT`: 3

Thresholds: oversized event >200 KB; high input >300k tokens. Command failures are
reported even when the agent recovered and the overall turn exited successfully.
