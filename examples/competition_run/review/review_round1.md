# Review Report — Round 1（综述稿）

审稿人：goai-reviewer（同模型冷启动降级，独立性受限已在 trace 声明）
对象：drafts/main.pdf（14 页）+ sections/01–07 + figures + research_gaps
完整过程与 claim-cite 抽查表：`state/review_traces/round1_1.md`

## 总评

稿件证据纪律和结构完成度高：165 次引用全部命中已审计库，量化数字逐条可回溯至摘要或
库内 PDF 原句；Route C 节与 ideas 产物、图 2、路线对比表交叉一致；Gap 注册表
（6 条，每条 ≥2 key + 数据库标注 + 推理）是实质贡献。主要问题集中在**结论强度管理**：
两处表述超出卡片证据强度（最高级/对位比较），属 must-fix；另有三处润色级。

## Issue 清单（已入账本）

| ID | 严重度 | 位置 | 问题 | 建议 |
|----|--------|------|------|------|
| I1 | major | 02 L1a | "first systematic structure–activity series" 无证据最高级 | 改 "an early systematic structure–activity series" |
| I2 | major | 01 Intro | "alternative to inorganic semiconductors and carbon nitrides" 超出 stegbauer2014a 证据 | 删对位或降级为 "designable photocatalyst class" |
| I3 | minor | 03 L3b | "among the highest reported" 范围未限定 | 限定为库内最高 |
| I4 | minor | 06 G1 | "no incentive exists…" 无支撑社会学断言 | 改为口径不一致的可验证表述 |
| I5 | minor | 全文 | 34 处 overfull hbox | 压表列宽或留痕接受 |

## 做得好的部分

抽查 10 条 claim-cite 有 9 条完全命中；微波 725/152 数字直接对上库内 PDF 原句；
stub 逆合成「演示数据非化学结论」标注完整；G4 与 Route C 形成可执行闭环。

## 裁决

0 blocker / 2 major / 3 minor → **不放行**，`review_pass = FAIL`，I1–I5 路由 target=writing，
等 orchestrator 组织返工后复审。
