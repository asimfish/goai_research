LLZO 真实逆合成接入诊断已完成并落盘。

- 模型：`local_two_stage_inorganic`，CUDA `cuda:0`
- Stage-1 checkpoint：`f302cb315a607eaf461281ef65585489eb814b1db7c5e41e56aaa9193965a53e`，hash OK
- Stage-2 checkpoint：`373ee6bdaf562f4ee70b06e515d5b84a18db8c6dbd2d4e2fd7dea864272465de`，hash OK
- 模型输出已验证，但化学路线未验证
- 后端调用总耗时：5319 ms

Top-5：

1. `ZrO2 + La2O3 + Li2CO3`
2. `ZrO2 + La2O3 + LiHO`
3. `ZrO2 + Li2CO3 + La(HO)3`
4. `ZrO2 + La2O3 + Li2CO3 + LiHO`
5. `ZrO2 + LiHO + La(HO)3`

主要诊断问题：

- 总 provider 报告 `stub`、`trusted=false`，但本地无机模型可用，信任语义不一致。
- Top-1 的 `make_experiment_plan` 返回 `steps=[]`、`provider=null`、`provider_verified=false`。
- `LiHO`、`La(HO)3` 的规范化表达需要人工核查。
- 未从摘要推断温度或时间；`conditions=null`。
- safety 已写入“需材料化学负责人审核，NOT FOR LAB USE”。
- characterization 仅作为待审建议。
- 动机绑定已验证 key：`raju2021crystal`、`heywood2023tailoring`。

产物：

- [retro_llzo_top5.json](/home/gaojing/goai_research/workspace/ideas/retro_llzo_top5.json)
- [experiment_llzo_diagnostic.json](/home/gaojing/goai_research/workspace/ideas/experiment_llzo_diagnostic.json)
- [proposal_llzo_diagnostic.md](/home/gaojing/goai_research/workspace/ideas/proposal_llzo_diagnostic.md)
- [idea_graveyard.md](/home/gaojing/goai_research/workspace/memory/idea_graveyard.md)

已执行 `loopctl log`。因贡献确认和人工安全审批尚未完成，未设置 `ideas_reviewed` PASS。