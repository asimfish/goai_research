# Review Trace — Round 1, Seq 1（综述稿全稿审）

- 审稿模型：同模型冷启动（Claude Fable 5 / Cursor 宿主）——**无跨模型 MCP 通道，
  独立性受限**，本轮结论按降级规程处理（可开 issue、可置 FAIL；终审放行仅记 provisional）。
- 审稿顺序（防执行者自评带偏）：先读产物（main.pdf 编译日志、drafts/sections/*.tex、
  figures、notes/research_gaps.md、ideas/route_c_*），后读账本 log。
- 审稿维度：覆盖 / 组织 / 引用（claim-cite 抽查 10 条）/ 图文 / 论证 / 写作。

## 提交给审稿视角的材料清单

- drafts/main.tex + sections/01–07（3764 词正文，165 次引用，37 key）
- library/references.bib（37 条，ref_integrity 37/37 PASS）
- notes/{taxonomy,reading_cards,research_gaps,contribution}.md
- figures/drawio/fig{1,2}*.pdf + figure_plan.md 白名单
- ideas/route_c_synthesis_plan.md（Route C 交叉引用一致性）

## claim-cite 抽查记录（10 条）

| # | 位置 | claim | 核对源 | 裁决 |
|---|------|-------|--------|------|
| 1 | 01 intro | 7–27 Å pores, 2005 boronate [cote2005porous] | 阅读卡片/摘要 | PASS |
| 2 | 01 intro | 20.7 mmol g-1 h-1 [yang2021protonated] | 卡片（摘要原句 as high as 20.7） | PASS |
| 3 | 02 L1b | 9 N HCl+沸水, 仅 keto 形式 [kandambeth2012construction] | 摘要 | PASS |
| 4 | 02 L1b | 二炔基>炔基 HER [pachfule2017diacetylene] | 卡片 | PASS |
| 5 | 03 L3b | 27.98 mmol h-1 g-1 [zhang2022reconstructed] | 摘要 | PASS |
| 6 | 03 L4b | 782 μmol h-1 g-1 / TON 54.4 [banerjee2017single] | 卡片 | PASS |
| 7 | 04 L5b | 725 vs 152 m2/g, 1h/100°C vs 3d/120°C [grenu2020microwave] | 库内 PDF 原句 | PASS |
| 8 | 04 L5b | 418 m2/g, 30× STY, −89% energy [xu2026structural] | 摘要 | PASS |
| 9 | 04 L5b | 41 mg/h, 703 kg m-3 day-1 [peng2016room] | 摘要 | PASS |
| 10 | 02 L1a | "first systematic structure–activity series" [vyas2015a] | 卡片 | **FAIL——超出证据**（卡片只支持 N 数单调序列，不支持 "first"） |

## 发现问题（结构化，已同步账本 issue）

1. [major][writing] 02_design_levers.tex L1a："Azine linkages then delivered the **first**
   systematic structure–activity series" —— "first" 为无证据最高级断言；vyas2015a 卡片只支持
   「N3>N2>N1>N0 单调」。建议改为 "an early systematic structure–activity series"。
2. [major][writing] 01_introduction.tex："establishing COFs as a designable alternative to
   inorganic semiconductors **and carbon nitrides**" —— stegbauer2014a 卡片仅支持「首个 COF HER
   演示」，与碳氮化物的对位比较超出库内证据（wrong-context 风险）。建议删去比较对象或降级为
   "a designable photocatalyst class"。
3. [minor][writing] 03_charge_interface.tex："27.98 … --- **among the highest reported**" ——
   评价性范围未限定；库内成立（>20.7）但"reported"含库外。建议限定为
   "the highest sacrificial rate in this survey's library"。
4. [minor][writing] 06_open_challenges.tex G1："no incentive exists to report unfavorable
   metrics" —— 社会学断言无引用支撑。建议改为可验证表述（口径不一致的事实已由
   li2022covalent vs yang2021protonated 支撑）。
5. [minor][writing] 排版：34 处 overfull hbox（revision_log 已自报）。建议压缩两张表列宽
   或改字号；不阻塞。

## 做得好的部分（反过度防御条款，如实记录）

- 引用纪律扎实：165 次引用全部落在 37 个已审计 key 内，抽查 9/10 语义命中；量化数字
  （725/152、418、30×、−89%、703、82.6%、20.7、27.98、3000、TON 54.4）全部能在库内
  摘要/PDF 原文找到原句。
- Route C 节与 ideas 产物、fig2、Table 2 四方一致；stub 逆合成标注到位。
- Gap 注册表证据链 + 数据库标注 + 推理三件套完整，G4 与 Route C 形成闭环是真贡献。
- 词数 3764 在窗内、密度 32/千词远超线、结构与 blueprint 一一对应。

## 结论

blocker 0 / major 2 / minor 3 → **本轮不放行**（review_pass FAIL），issue 已路由 target=writing。
