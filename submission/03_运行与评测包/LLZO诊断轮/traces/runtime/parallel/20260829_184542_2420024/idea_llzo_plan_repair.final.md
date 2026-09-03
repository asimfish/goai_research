复测完成，验收项全部通过：

- 真实 MCP stdio 调用确认：
  - `molecular_provider_trusted=false`
  - `local_inorganic_ready=true`
- Top-5 每条路线均包含 `provider`、`model_output_verified`、`chemical_route_verified`
- Top1 计划恰有 1 个 step，inputs 为 `ZrO2 / La2O3 / Li2CO3`
- `provider=local_two_stage_inorganic`
- `provider_verified=true`
- `chemical_route_verified=false`
- `conditions=null` 并标记 `TODO`
- 保留 `NOT FOR LAB USE`

已更新：

- [retro_llzo_top5.json](<HOME>
- [experiment_llzo_diagnostic.json](<HOME>
- [proposal_llzo_diagnostic.md](<HOME>

账本已记录 `event=diagnostic_repair`；`ideas_reviewed` 仍不存在，未设为 PASS。