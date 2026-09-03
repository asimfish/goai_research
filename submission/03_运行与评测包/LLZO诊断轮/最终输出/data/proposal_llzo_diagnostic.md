# LLZO 真实逆合成接入诊断提案

## 状态与适用边界

**BLOCKED：贡献确认与人工安全审批未完成。需材料化学负责人审核，NOT FOR LAB USE。**

本文件诊断本地两步无机逆合成模型能否为 Li7La3Zr2O12（LLZO）返回可审查的候选前驱体集合。模型路线是排序候选，不是实验真值；本次输出不得直接转化为实验操作。后端明确给出 `chemical_route_verified=false`。历史上的 Top-1 实验计划空步骤失败已由 `diagnostic_repair` 修复；当前计划恰有 1 个步骤。

## 动机与缺口证据

现有 taxonomy 将“固相反应与前驱体/化学计量控制”和“工艺复现性、均匀性与可比口径”分列，说明前驱体候选与可复现实验条件之间需要独立证据链。LLZO 合成与掺杂影响已有综述性证据 [@raju2021crystal]，而高置信度、相纯、低阻抗 LLZO 的固相路线也显示工艺路线需要专门验证 [@heywood2023tailoring]。coverage 报告对六个子主题均判定非缺口，因此本提案不声称发现无人研究方向；其动机是诊断“模型候选 → 可审查实验计划”的接入缺口。

## 方法草图

- 真实查询 provider 与无机模型状态，记录 checkpoint SHA-256 与哈希校验状态。
- 对目标式 Li7La3Zr2O12 运行两阶段 Top-5 排序，并完整保存原始响应。
- 仅对 Top-1（ZrO2、La2O3、Li2CO3）调用实验计划生成器。
- 将模型候选和文献事实分层：不把候选概率解释为反应成功率，不把模型路线当作实验真值。
- 不从摘要推断温度、时间或其他具体操作条件；当前 `conditions=null`。

## 验证计划

1. 机器侧：核对 provider、模型可用性、依赖、checkpoint hash、Top-5 数量及返回 schema。
2. 证据侧：由引用核查角色复核本提案全部 citation key，并由独立 reviewer 判断证据真实性、新颖性与可行性。
3. 人工侧：由材料化学负责人审批试剂、化学计量、热处理、环境控制、安全和废物处置后，才允许形成实验版方案。
4. 表征（待审建议）：相组成、微结构与离子输运表征方案须结合经核验全文文献，由材料化学负责人审定；此处不规定具体仪器参数或验收阈值。

## 风险与替代路线

- **适配修复后复测：**真实调用 `provider_status` 得到 `molecular_provider_trusted=false`、`local_inorganic_ready=true`，确认分子 provider 信任状态与本地无机模型就绪状态已经分离。Top-5 每条路线均携带 `provider=local_two_stage_inorganic`、`model_output_verified=true`、`chemical_route_verified=false`；Top-1 的 `make_experiment_plan` 返回恰好 1 个步骤，输入为 ZrO2、La2O3、Li2CO3，且 `provider_verified=true`。适配链路通过本次诊断，但化学路线仍未经验证。
- Top-5 含有规范化可疑的 `LiHO` 与 `La(HO)3` 表达，必须由材料化学负责人核查实体与化学式映射。
- 替代路线是先修复无机 route → plan 的 schema/步骤映射，再基于已核验全文逐项补条件；在此之前保持 `conditions=null`。
- 安全：需材料化学负责人审核，NOT FOR LAB USE。
