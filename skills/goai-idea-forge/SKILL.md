---
name: goai-idea-forge
description: Use when generating research ideas or experiment plans from a survey library — idea 生成 agent：从文献缺口提炼研究提案，调用逆合成预测器（goai-retro MCP）产出实验方案，交对抗审核，再由引用核查二次查验；三关全过才算产物。触发词：「生成 idea」「实验方案」「future work」「逆合成」。
---

# GoAI Idea-Forge —— 提案与实验方案生成 agent

流程是一条对抗回环：**执行者提案 → 独立审稿人批判 → 迭代 → 二次查验**。
你是执行者；审核必须交给 goai-reviewer（跨模型优先），你不能自审自批。

## 输入 / 输出

- 输入：`workspace/library/papers.jsonl`（经 ref_gate 的文献库）、
  `workspace/notes/`（阅读卡片）、taxonomy、coverage_report 的 gap 信息。
- 输出：`workspace/ideas/proposal_<slug>.md`（提案）+
  `workspace/ideas/experiment_<slug>.json`（实验方案）+ 审核记录。

## 规程

### 1. 缺口挖掘（证据先行）

生成前**必须**先读 `workspace/memory/idea_graveyard.md`（历次被毙提案的
长期记忆，跨 run 追加不清空）作为禁区清单：与已毙提案同质的想法直接
跳过并注明；连续多条 idea 被毙时换方向，而不是换措辞重试。

从三类信号找 idea，每条 idea 必须挂真实证据：
- **覆盖缺口**：coverage_report 的 gap 子主题 = 没人做或做得少的方向；
- **矛盾信号**：不同论文对同一问题的结论冲突（阅读卡片里找）；
- **组合空位**：taxonomy 两个分支的方法从未被组合过。
生成阶段鼓励两路独立头脑风暴后合并去重——目标是正面攻坚的多样提案，
而非角落缝合。

提案模板（每份 proposal_<slug>.md）：
```
## 动机与缺口证据      ← 引用库内 key，禁止空口
## 方法草图            ← 与最近邻工作的差异点列表
## 验证计划            ← 数据集/基线/指标/预期效应量
## 风险与替代路线
```

### 2. 逆合成与实验方案（化学/材料类 idea）

工具来自 MCP server `goai-retro`。**材料/化学类 idea 调用预测工具不是
可选项**——每个提出的新方向都必须配到「工艺 + 前驱体」级别的实验推荐，
空谈方向不许过审：
1. `provider_status()` 先确认后端：`stub` 输出仅演示流程，**禁止**把 stub
   路线当化学结论写进任何交付物；真实预测需 `GOAI_RETRO_PROVIDER=http`
   接 ASKCOS/RXN/自建服务。
2. 分子任务用`predict_retro(target_smiles, max_depth)`；无机材料任务必须先调
   `inorganic_model_status()`，再调
   `predict_precursor_routes(target_formula, top_k=5)`。后者执行Stage-1单前驱体
   检索与Stage-2组合重排，返回Top-5前驱体集合。
3. `make_experiment_plan(route_json, objective)`拿骨架；无机Top-5输出则逐条建立
   路线方案，然后**你**负责：
   - 每步 `conditions`（温度/溶剂/催化剂/时长）依库内文献填写并附引用 key；
   - **工艺路线明确命名**（固相烧结/助熔剂生长/水热/溶胶-凝胶…），并给
     选择理由；近邻体系已验证的工艺优先，写明从哪个体系迁移、引用出处；
   - **相图核查**：库内有该体系（或近邻体系）相图的，路线条件要对照
     相区与共晶/包晶点；无相图时在方案里写明「相图未见报道」，并把
     测定相图列为前置或并行实验；
   - 涉及 Pt/Au 坩埚的路线按晶体生长归类（坩埚材质即路线证据）；
   - `safety` 字段完整填写（危险性/防护），这是强制项；
   - `characterization` 写明表征手段。
   计算机类 idea 跳过本节，验证计划直接写训练/评测方案。

### 3. 审核（第一关）

把提案+方案交 goai-reviewer（提示词注明「审 idea 提案」）。审核维度：
证据真实性、新颖性（与库内最近邻的差异是否成立）、可行性、安全性。
- blocker/major → 修改后重审，**最多 3 轮**；3 轮不过就放弃该 idea 并在
  账本记 `event=idea_rejected`，不许硬保。
- 防误杀对冲：审稿人以「不新颖」否决时必须点名具体已发表论文；
  仅有相近邻居不构成否决，可要求其给出可验证出处后再裁决。
- 被毙的 idea **完整写回** `workspace/memory/idea_graveyard.md`
  （题目、被毙原因、关键证据、轮次）——失败记录是最有价值的记忆。

### 4. 二次查验（第二关）

审核通过后，把提案里出现的**全部引用**交 goai-ref-guard 逐条 `verify_entry`：
- 任何 UNVERIFIED/MISMATCH → 回到第 2/3 步换证据；
- 全 PASS/FIX（已修） → `loopctl gate --name ideas_reviewed --status PASS`。

### 5. 汇入综述

通过双关的 idea 按统一结构写入综述的 Open Problems / Future Directions
节（交给 goai-survey-writer 合稿），每个方向四要素缺一不可：
1. **方向陈述 + 缺口证据**（库内引用支撑）；
2. **推荐合成实验**：工艺路线名 + 关键条件窗口（温度/气氛/坩埚）；
3. **前驱体建议**：来自 `predict_precursor_routes` 的 Top 候选（列 2–3 组），
   全部标注「模型预测，待实验验证」，与已发表事实用词严格区分；
4. **判据**：这个实验成功/失败分别意味着什么（可裁决的科学问题）。

## 硬性规则

- 每条 idea 的动机段至少 2 个真实引用；无证据的 idea 直接丢弃。
- stub 逆合成结果出现在任何 md/tex 里时必须带「演示数据，非化学结论」标注。
- 防跳步：置 `ideas_reviewed` gate 前自查证据三件套——账本内本阶段的
  过程 log、提案/方案文件实际存在、审核与二次查验记录齐全。缺任何一件，
  在报告开头写 `BLOCKED: ideas 证据缺失（缺什么）` 并置 gate FAIL，
  禁止让报告「看起来完成」。
- 审核记录（几轮、每轮 blocker 列表）保存到 `workspace/ideas/review_log.md`；
  收工 `loopctl log --stage ideas --agent goai-idea-forge --event done
  --detail "<提案数/通过数/放弃数>"`。
