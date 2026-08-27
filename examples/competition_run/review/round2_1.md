# Review Trace — Round 2, Seq 1（返工复审 + 终审三视角）

- 审稿模型：同模型冷启动降级（无跨模型 MCP 通道），**独立性受限**；
  本轮放行按规程记 `PASS`，detail 注明 `provisional（未经独立模型复核）`。
- 复审材料（按规程只含产物与上轮 issue 原文，不含执行者修复说明）：
  drafts/main.pdf（14 页 658844B 终版）、sections/01–07 现文、figures、
  notes/research_gaps.md、ideas/route_c_*、state/review_round1.md 的 issue 原文。

## 上轮 issue 逐条对照产物验证（审稿人自行核验，非对账）

| Issue | 验证方式 | 结果 |
|-------|----------|------|
| I1 "first systematic" | 正则扫 02 节现文 | 已改 "an early systematic"，原句 0 命中 → 修复成立 |
| I2 carbon nitrides 对位 | 正则扫 01 节现文 | "carbon nitrides" 0 命中，"designable photocatalyst class" 1 命中 → 修复成立 |
| I3 范围未限定 | 正则扫 03 节现文 | "the highest sacrificial rate in this survey's library" 1 命中 → 修复成立 |
| I4 无支撑断言 | 正则扫 06 节现文 | 改为 AQE/质量速率口径不一致表述并挂 li2022covalent+yang2021protonated → 修复成立 |
| I5 overfull | main.log 重扫 | 34 → 1（4.37pt，表格单元格级）；0 LaTeX Warning、0 undefined → 达到排版可接受线 |

占位标记 grep：`待补证据` 全稿 0 命中（终审前置检查项）。

## 终审三视角

**领域专家视角**（覆盖缺口与分类法合理性）：
factor-chain 五级分类与 scope.md 的 S1–S5 一一映射；13 叶各 ≥3 支撑（对照 taxonomy.md
与正文引用抽点 L1b/L2b/L4b/L5b 四叶确认）；奠基（2005/2012/2014）到 2026（flow 合成）
时间线连续；排除项（MOF/CO2RR/OER）未越界，OWS 仅作 outlook（G2），符合边界。
无新增覆盖异议。

**方法严谨派视角**（claim-cite 绑定与对比公平性）：
上轮抽查 10 条中 9 条 PASS、1 条超强度已修；本轮补抽 5 条：
(a) 3.8 nm mesopores [stegbauer2014a] — 卡片命中；
(b) TpPa-2 9N NaOH 归属（表 1 注明 TpPa-2 而非 TpPa-1）— 与摘要一致，无移花接木；
(c) "76 polymers/60 COFs/18 unreported" [zhao2022accelerated] — 摘要命中；
(d) 康采恩比较 O1 数字（725/152、1h/100°C）标注为 grenu2020microwave 汇编 wei2015the ——
两 key 并引，来源层级如实；
(e) G4 推理链「路线→结晶度→HER 中环节已被 ghosh2020identification 因果确立」——
表述准确（该文确立的是结晶度→HER，非路线→结晶度，正文用 'whose middle link' 精确指代）。
对比公平性：微波悖论（direct 优/transimination 劣）如实双向呈现，未选择性引用。无新增异议。

**期刊编辑视角**（venue 匹配）：
8–12 页目标 vs 实际 14 页（含图表参考文献）——正文 3764 词在 3500–5000 窗内，页数超出
来自 37 条参考文献与两张整宽图，可接受；图表规范（booktabs、编号、caption 不与正文重复）
达标；读者定位（材料/化学研究生）与语言风格（证据分级陈述）符合；与库内既有综述
（wang2020covalent/chen2024photocatalysis）差异化（factor-chain + Route C 桥）明确。
无阻塞异议；建议（非 issue）：投稿时按目标刊模板重排页数。

## 裁决

上轮 2 major 全部修复成立，无新增 blocker/major；残留 1 处 4.4pt 表格 overfull 属
排版噪声（minor 级以下，不开 issue）。
**放行：review_pass = PASS（provisional，同模型降级审稿，未经独立模型复核）。**
回执：model=claude-fable-5-cursor-host(same-model, cold-start, degraded);
trace=workspace_live/competition/state/review_traces/round2_1.md
