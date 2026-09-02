# Agent trace audit

| Task | Exit | MCP | Tool fn via cmd | Web search | Failed commands | Input tokens | Max event | Flags |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `lit_additive_property` | 0 | 0 | 0 | 0 | 0 | 0 | 465 | NON_JSON_LINES |
| `lit_doping_sintering` | 0 | 0 | 0 | 0 | 0 | 0 | 4400 | NON_JSON_LINES |
| `lit_precursor_powder` | 0 | 0 | 0 | 0 | 0 | 0 | 396 | NON_JSON_LINES |
| `style_llzo` | 0 | 9 | 2 | 0 | 0 | 345955 | 70745 | NON_JSON_LINES, HIGH_INPUT_TOKENS |
| `lit_doping_repair` | 0 | 6 | 1 | 0 | 0 | 708103 | 63548 | HIGH_INPUT_TOKENS |
| `lit_precursor_repair` | 0 | 5 | 1 | 0 | 1 | 340783 | 62679 | COMMAND_FAILURE, HIGH_INPUT_TOKENS |
| `lit_property_repair` | 0 | 5 | 4 | 0 | 2 | 729110 | 58569 | COMMAND_FAILURE, HIGH_INPUT_TOKENS |
| `style_llzo_repair` | 0 | 0 | 2 | 0 | 0 | 789970 | 1102172 | OVERSIZED_EVENT, HIGH_INPUT_TOKENS |
| `lit_gather` | 0 | 2 | 2 | 0 | 0 | 221430 | 10647 | — |
| `ref_guard_llzo` | 0 | 4 | 2 | 0 | 0 | 301524 | 5223 | HIGH_INPUT_TOKENS |
| `ref_guard_rerun` | 0 | 1 | 1 | 0 | 0 | 247422 | 4502 | — |
| `writer_taxonomy_llzo` | 0 | 0 | 0 | 0 | 0 | 239090 | 21332 | — |
| `figure_llzo_diagnostic` | 0 | 6 | 0 | 0 | 0 | 577525 | 13383 | HIGH_INPUT_TOKENS |
| `idea_llzo_diagnostic` | 0 | 4 | 1 | 0 | 0 | 268088 | 11712 | — |
| `figure_llzo_visual_repair` | 0 | 4 | 2 | 0 | 0 | 435439 | 13383 | HIGH_INPUT_TOKENS |
| `idea_llzo_plan_repair` | 0 | 0 | 13 | 0 | 2 | 665324 | 14945 | COMMAND_FAILURE, HIGH_INPUT_TOKENS |
| `reviewer_llzo_diagnostic` | 0 | 0 | 0 | 0 | 0 | 452451 | 24098 | HIGH_INPUT_TOKENS |
| `figure_issue_i2` | 0 | 3 | 2 | 0 | 1 | 612312 | 13934 | COMMAND_FAILURE, HIGH_INPUT_TOKENS |
| `idea_issue_i3` | 3 | 0 | 0 | 0 | 0 | 158270 | 14277 | NONZERO_EXIT |
| `idea_i3_validation` | 0 | 0 | 0 | 0 | 0 | 210528 | 166087 | — |
| `reviewer_i2_i3_recheck` | 0 | 0 | 0 | 0 | 0 | 188871 | 7231 | — |
| `llzo_writer_plan` | 0 | 0 | 0 | 7 | 0 | 3795691 | 19393 | HIGH_INPUT_TOKENS |
| `llzo_manuscript` | 0 | 0 | 0 | 0 | 0 | 3303496 | 19393 | HIGH_INPUT_TOKENS |

## Flag counts

- `COMMAND_FAILURE`: 4
- `HIGH_INPUT_TOKENS`: 13
- `NONZERO_EXIT`: 1
- `NON_JSON_LINES`: 4
- `OVERSIZED_EVENT`: 1

Thresholds: oversized event >200 KB; high input >300k tokens. Command failures are
reported even when the agent recovered and the overall turn exited successfully.
