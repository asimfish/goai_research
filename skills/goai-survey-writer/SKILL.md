---
name: goai-survey-writer
description: Use when drafting the survey manuscript — 综述写作 agent：贡献先行 + 五步流水线：taxonomy → 引用支持库 → 章节蓝图 → 逐节写作 → 精修，claim 级引用绑定，LaTeX 交付。触发词：「写综述」「survey draft」「组稿」「写 related work」。
---

# GoAI Survey-Writer —— 综述写作 agent

两条工作原则：
- **贡献先行**：没确认综述的贡献与 motivation 不动笔；
  引用支持库让每个候选引用先绑定到句子级 claim；产物链可审计。
- **分步流水线**：outline → literature review → section writing →
  refinement，配 halt rules（≥90% 引用整合率、防评审博弈）。

## 唯一引用池

只允许引用 `workspace/library/references.bib`（已过 ref_gate）里的 key。
写作中发现需要库外文献 → 开 issue 请 lit_search 补检，**不许手写 bib 条目**。

## 阶段一：taxonomy（orchestrator 单独调用）

1. 通读 `workspace/library/papers.jsonl`（标题+摘要）与阅读卡片。
2. 产出 `workspace/notes/taxonomy.md`：树形分类法，每个叶节点 ≥3 篇支撑
   文献（key 列表）；孤儿论文单列「未归类」等待处理。
3. 同时产出 `workspace/notes/contribution.md`：本综述的贡献声明
   （新分类法？新对比框架?新 open problems？）+ motivation 一段。
   这两个文件是全文的宪法；`loopctl gate --name taxonomy_ready --status PASS`。

## 阶段二：引用支持库（citation support bank）

产出 `workspace/notes/citation_bank.md`：按未来章节组织，每行 =
`[key] + 一句话可支撑的 claim + 强度(strong/weak)`。
规则：候选量 ≈ 目标引用数 × 1.5；近三年占比 ≥50%；
每条都必须真的读过摘要（不确定的标 weak）。

## 阶段三：章节蓝图

产出 `workspace/drafts/blueprint.md`，逐节写清：本节回答什么问题、
覆盖 taxonomy 哪个分支、用哪些 bank 条目、配哪张图（figure_plan 里的名字）、
预计字数。综述骨架默认：
Intro → Background/Preliminaries → Taxonomy 总览（配主图） →
per-branch 深入（每支一节，含对比表） → 讨论（趋势/矛盾/局限） →
Open Problems（含 idea-forge 产出） → Conclusion。

## 阶段四：逐节写作（可并行）

每节独立成文件 `workspace/drafts/sections/NN_<slug>.tex`。硬约束：
- **claim-cite 绑定**：每个事实性 claim 后必须跟 `\cite{key}`，key 来自
  bank；写不出支撑就删 claim 或降级为 "可能/或许" 并明说是推测；
- 对比表的每个单元格可溯源到对应论文；
- 密度线：每千词 ≥8 次引用（综述标准）；
- 图文一致：引用图必须解释图中主线，与 caption 不重复；
- 语言风格：结论按证据强度陈述，不写忏悔式套话（"further research is
  needed" 只许出现在 Limitations）；
- 并行写作时只碰自己的节文件，公共文件（main.tex/bib）只由汇合者动。

## 阶段五：组装与精修

1. 用 `templates/survey_main.tex` 组装，`\input` 各节。
2. 一致性闸门：`python3 tools/bib_guard.py workspace/drafts
   workspace/library/references.bib` 必须 PASS。
3. 自精修一轮（halt rules）：只修 clarity/流畅/重复，
   **不许**为讨好审稿删数据、删 limitation、改结论强度；每处改动在
   `workspace/drafts/revision_log.md` 留一行。
4. 有 latex 环境则编译验证；无则跑语法级检查（括号配对/环境闭合）。
5. `loopctl gate --name draft_complete --status PASS` 并交 review。

## 返工协议

收到 reviewer 的 issue（账本里 target=writing）：逐条修，修完
`loopctl issue close --id <I?> --note "<改了什么>"`；不同意的意见要在
revision_log 里写反驳理由并保留原文，交由下轮 review 仲裁，不许静默忽略。
