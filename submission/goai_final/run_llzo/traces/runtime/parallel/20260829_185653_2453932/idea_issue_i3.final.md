I3 状态一致性已修复并关闭。

- `experiment.provider_status` 已改为 `molecular_provider="stub"`，限定为分子逆合成。
- 本地无机 provider 保持 `local_two_stage_inorganic`，`ready=true`。
- proposal 已注明空步骤是历史失败，已由 `diagnostic_repair` 修复；当前恰 1 步。
- 本地断言全部通过：Top5=5、steps=1、inputs=3、模型已验证/化学未验证、conditions=null、包含 `NOT FOR LAB USE`。
- 已写入 `diagnostic_repair` 日志。
- I4 仍为 open；未设置 `ideas_reviewed`。