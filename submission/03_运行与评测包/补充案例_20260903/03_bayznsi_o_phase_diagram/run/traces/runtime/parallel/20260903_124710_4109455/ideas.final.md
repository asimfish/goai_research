已使用 `goai-idea-forge` 完成并落盘：

- [proposal_phase_purity.md](<HOME>
- [proposal_metastability.md](<HOME>
- [proposal_closed_loop.md](<HOME>
- [experiment_phase_purity.json](<HOME>
- [experiment_metastability.json](<HOME>
- [experiment_closed_loop.json](<HOME>
- [review_log.md](<HOME>
- [review_round1.md](<HOME>

关键结果：

- 已按顺序调用 `provider_status`、`inorganic_model_status` 和 `predict_precursor_routes("Ba2Y2ZnSi2O8")`。
- provider 为 `stub`、`trusted=false`；本地两阶段无机模型可用，但 `chemical_route_verified=false`。
- 每条预测路线均标注“模型预测，待实验验证；演示数据，非化学结论”，且包含完整条件、安全、废弃物和表征字段。
- 19 个引用完成二次 `verify_entry`：PASS 19，FIX/MISMATCH/UNVERIFIED 均为 0。
- `ideas_reviewed` 已置为 PASS；账本已记录 `goai-idea-forge ... event=done`，开放 issue 为 0。
- 独立 `goai-reviewer` 两次 handoff 均超时，因此审稿报告按技能降级规则标记为 provisional；`review_pass` 保持 WARN，未虚构独立审稿结论。