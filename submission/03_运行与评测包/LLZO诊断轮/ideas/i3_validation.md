# I3 修复验证

验证范围：仅验证 ledger I3 的状态一致性修复；未修改 `retro_llzo_top5.json`、`experiment_llzo_diagnostic.json` 或 `proposal_llzo_diagnostic.md`，未处理 I4，未设置任何 gate。

## 历史与账本状态

- I3 原问题：`provider=stub` 与本地无机路线/计划状态混用，同时 proposal 对当前计划存在“空步骤”和“修复后 1 步”的矛盾描述。
- 账本已有 `diagnostic_repair` 记录：无机 route-to-plan 复测得到 Top-1 单步计划，随后完成 I3 跨文件状态一致性修复。
- 当前 issue 状态：I3 = `closed`；I4 = `open`。

## 确定性断言结果

以下断言均以解析 JSON 和精确字符串/字段比较执行；任一不满足即由 Python `assert` 失败退出。

| 断言 | 观测值 | 结果 |
|---|---|---|
| Top5 = 5 | `top_k=5`，`len(routes)=5` | PASS |
| `provider_status` 仅以 `molecular_provider` 表示 stub | 无笼统 `provider` 字段；`molecular_provider="stub"`；scope 为 `molecular retrosynthesis only` | PASS |
| 本地无机 provider / ready 正确 | `local_inorganic_provider="local_two_stage_inorganic"`；`local_inorganic_ready=true` | PASS |
| plan 恰 1 步且 inputs 精确匹配 | `len(steps)=1`；`["ZrO2", "La2O3", "Li2CO3"]` | PASS |
| 模型输出已验证、化学路线未验证 | retro 顶层、全部 5 条 route 及 plan 均为 `model_output_verified=true`、`chemical_route_verified=false` | PASS |
| conditions 为空 | experiment 顶层及唯一 step 的 `conditions=null` | PASS |
| proposal 不再把当前 plan 写成空步骤 | 存在“当前计划恰有 1 个步骤”；不存在“当前计划空步骤”或“当前计划为空步骤” | PASS |
| `NOT FOR LAB USE` 存在 | proposal 与 experiment 均存在 | PASS |
| issue 状态符合要求 | I3 = `closed`；I4 = `open` | PASS |

## 结论

I3 修复验证通过。当前产物一致地表达：分子 provider 为 stub，但本地两阶段无机 provider 已就绪；当前 Top-1 plan 为单步骨架；模型输出已验证而化学路线、条件与实验安全性均未验证。该结果仅是适配器/状态一致性验证，**NOT FOR LAB USE**。I4 保持 open。
