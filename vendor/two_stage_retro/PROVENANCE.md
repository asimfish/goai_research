# Vendored two-stage inorganic retrosynthesis model

Copied on 2026-08-29 from the read-only working package:

`InorganicSys/InorganicRetroSynthesis/two_stage_retro_package`

The source package was not edited. This directory contains only the minimal
inference code, precursor metadata, Retro split statistics, charge metadata,
and the two selected checkpoints needed by the MCP adapter.

Selected production bundle:

`artifacts/retrofinal/best_setting_combo1_no_mixpool`

| Stage | Selection | SHA256 |
|---|---|---|
| Stage 1 | seed 20260504 formula-token precursor retriever | `f302cb315a607eaf461281ef65585489eb814b1db7c5e41e56aaa9193965a53e` |
| Stage 2 | seed 20260504 no-mixture-pool set reranker | `373ee6bdaf562f4ee70b06e515d5b84a18db8c6dbd2d4e2fd7dea864272465de` |

Reference metrics recorded by the source package are Stage-1 Top@20 95.78%,
Stage-2 Combo@1_full 71.81%, Combo@20_full 89.21%, and MRR_full 0.7748.
These are source-package evaluation figures, not metrics recomputed by the MCP
adapter.

One packaging-only change exists in this copy: `data.py` resolves its resource
directory relative to the copied Python package (`two_stage_retro/data/`). The
model architecture, checkpoint contents, scoring, candidate generation, and
source package on NAS are unchanged.
