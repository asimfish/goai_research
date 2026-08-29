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

## 阶段零：风格与语料装载（可与文献检索并行）

### 0a 领域风格卡（来自 goai-style-bank）

优先消费 `workspace/style_bank/writing_style_cards.md`（30 篇经典综述
归纳的结构骨架/句式模式/引用密度基准/对比表习惯）。风格库缺失或为
浅层（WARN）时降级：自行挑 2-3 篇公认高质量综述精读，产出
`workspace/notes/style_notes.md` 补位。阶段三的蓝图必须引用风格卡
（或 style_notes）的结论；与默认骨架冲突时，以领域归纳骨架为准并在
蓝图里说明理由。量化基准（篇均引用数/密度）直接决定 bank_check 与
bib_guard 的参数取值，在账本记 decision。

### 0b 专业语料库（super_library）

探测顺序：`$GOAI_SUPERLIB` 环境变量 → `~/Code/super_library` →
不存在则记账降级（跳过本节，不阻塞）。存在时**必须**使用：

- 每节动笔前拉一次有界语料包（从 super_library 仓库根执行）：

  ```
  python3 scripts/superlib.py bundle \
      --rhetoric-query "<本节的表达需求>" \
      --technical-query "<本节核心概念>" \
      --domain <domain> --section <section> --intent <intent> \
      --limit 4 --max-chars 24000 [--guide <guide-id>]
  ```

- section 协议与修辞句式卡是**领域无关**的，任何主题都用；术语卡只在
  主题落在其覆盖域（world models / RL / embodied AI / VLA）时用，
  域外主题（如材料化学）跳过术语卡并记账。
- 实验/对比表用其 `template --list` 的表格模板起手（替换全部 `SL_*`）。
- 语料是**语言与修辞的护栏**，不是证据来源：不得把语料库定义当引文，
  不得复制原句成文。
- 阶段五精修后跑其 wording lint：
  `python3 scripts/superlib.py lint --text-file <draft> --bib <refs.bib>`，
  lint 结果记入 revision_log。

## 阶段一：taxonomy（orchestrator 单独调用）

1. 通读 `workspace/library/papers.jsonl`（标题+摘要）与阅读卡片。
2. 产出 `workspace/notes/taxonomy.md`：树形分类法，每个叶节点 ≥3 篇支撑
   文献（key 列表）；孤儿论文单列「未归类」等待处理。
3. 同时产出 `workspace/notes/contribution.md`：本综述的贡献声明
   （新分类法？新对比框架?新 open problems？）+ motivation 一段。
   这两个文件是全文的宪法。
4. **呈报确认**：contribution.md 产出后，把贡献声明（给 2-3 个候选表述）
   与 motivation 摘要呈给用户确认或修改；确认前 `taxonomy_ready` 只能记
   PENDING，不得进入阶段二。用户明确不可达（全自动无人值守 run）时，
   账本记 `--detail "contribution 未经用户确认"`，并在最终汇报中如实声明。
   确认后 `loopctl gate --name taxonomy_ready --status PASS`。

## 阶段二：引用支持库（citation support bank）

产出 `workspace/notes/citation_bank.md`：按未来章节组织，每行 =
`- [key] 一句话可支撑的 claim (strong|weak)`。
规则：候选量 ≈ 目标引用数 × 1.5；近三年占比 ≥50%；
每条都必须真的读过摘要（不确定的标 weak）。
目标引用数与库规模联动：comprehensive 档（库 ≥100）的综述正文
目标引用数 ≥80（顶刊综述常态是引用数≈库规模），且库内条目最终
整合率仍须 ≥90%——不许「检索一大库、正文只用零头」。
产完跑确定性校验（不过线先补库或补读，再进阶段三）：

```
python3 tools/bank_check.py workspace/notes/citation_bank.md \
    workspace/library/references.bib --target-cites <目标引用数>
```

阈值适配：默认线（候选量 ×1.5、近三年 ≥50%）按满配综述设计；lite/mini 或
库规模受限的运行撞线时，先跑默认参数留下 FAIL 证据，再在账本记
`log --event decision` 说明理由（库上限/奠基文献偏旧等）后按比例调
`--min-recent`/`--min-ratio` 重跑——禁止不留痕直接降线；能补库时优先补库。

## 阶段三：章节蓝图

产出 `workspace/drafts/blueprint.md`，逐节写清：本节回答什么问题、
覆盖 taxonomy 哪个分支、**支撑 contribution.md 中的哪一条贡献**、
用哪些 bank 条目、配哪张图（figure_plan 里的名字）、预计字数、
**完稿检查项**（本节写完后按什么标准自查，如「对比表覆盖该分支全部
代表方法」）。任何一节「支撑贡献」或「完稿检查」为空即返工，不得进入
阶段四；找不到贡献落点的节要么删、要么回头修订贡献声明。
综述骨架默认（以 style_notes.md 归纳的范文骨架优先）：
Intro → Background/Preliminaries → Taxonomy 总览（配主图） →
per-branch 深入（每支一节，含对比表） → 讨论（趋势/矛盾/局限） →
Open Problems（含 idea-forge 产出） → Conclusion。

**节标题词法**（顶刊综述口径，蓝图定标题时执行、final 复查）：
- 2–6 词名词短语，用领域标准术语点名对象；方法论细节留给正文。
- 禁三连并列标题（"A, B, and C" 式）；禁机关词堆叠——method /
  rules / aspects / considerations 这类只听着学术、不带信息的词
  不入标题。
- 层级分工：`\section` 定主题域，`\subsection` 定分支或机制，
  枚举性细项用 `\paragraph` 或正文 run-in，不提升为编号标题。
- 对照：✗ "Scope, evidence method, and comparison rules" →
  ✓ "Scope and Evidence Criteria"；✗ "Establish composition and
  provenance"（小节标题） → ✓ "Composition and Provenance"。
- super_library 装载成功时，标题词面过一遍它的 lint
  （`python3 scripts/superlib.py lint --text-file <标题清单>`），
  装饰性同义词与直译腔按报告修。

## 阶段四：逐节写作（可并行）

每节独立成文件 `workspace/drafts/sections/NN_<slug>.tex`。硬约束：
- **claim-cite 绑定**：每个事实性 claim 后必须跟 `\cite{key}`，key 来自
  bank；写不出支撑就删 claim 或降级为 "可能/或许" 并明说是推测；
- 缺证据槽位的另一种合法处理：保留结构并插入
  `% 待补证据: <需要什么数据/文献>` 注释（编译不可见、可 grep），同时在
  账本开 minor issue 移交 final 清理。严禁第三种：用编造内容填槽；
- 对比表的每个单元格可溯源到对应论文；
- 密度线：每千词 ≥8 次引用（综述标准）；
- 图文一致：引用图必须解释图中主线，与 caption 不重复；
- 语言风格：结论按证据强度陈述，不写忏悔式套话（"further research is
  needed" 只许出现在 Limitations）；
- **列表排版**（顶刊口径，TeX 与 HTML 交付一体适用）：≤4 个短项
  （每项 <15 词）一律段内 run-in 列举——"(i) …; (ii) …; (iii) …"，
  不开显示列表；显示列表（enumitem `nosep`）只给每项 ≥1 完整句的
  内容；禁止每项以同一动词开头的平行复读（"Establish… Establish…
  Establish…"），改名词短语引导或并成一句；真正的步骤/协议才用
  编号列表，平行要素用 run-in 或 itemize；
- 并行写作时只碰自己的节文件，公共文件（main.tex/bib）只由汇合者动。

## 阶段五：组装与精修

1. 用 `templates/survey_main.tex` 组装，`\input` 各节。模板内置排版
   规范不许降级：Times 字体系（newtx，加载顺序 amsmath→newtxtext→
   newtxmath，禁 amssymb）、引用/交叉引用/URL 统一学术蓝
   （`colorlinks` + `citecolor=blue`）、caption 小号加粗标签、
   `\arraystretch 1.18`、titlesec 紧凑节标题、fancyhdr 运行页眉、
   参考文献前 `\clearpage`。表格定宽列一律用模板的 `P{宽}`
   （raggedright）列型，禁用裸 `p{宽}`——窄列两端对齐会产生
   justify 空洞，是"表格乱"的头号来源；正文含 Unicode 组合符/希腊
   字母时用 xelatex 编译。组装时必须完成两处替换：页眉短题
   （`TODO: Short Running Title`→论文短题，斜体）；主标题超一行时
   **手工断行成 2–3 行且行长均衡**，禁止让 LaTeX 自动折出孤词行。
2. 一致性闸门（未定义 key＝阻塞；库内条目整合率 <90%＝阻塞——孤儿条目
   要么在正文找到落点，要么开 issue 交 lit_search 评估后移出库，
   不许留着充数）：

   ```
   python3 tools/bib_guard.py workspace/drafts/sections \
       workspace/library/references.bib --min-integration 0.9 --min-cites-per-1k 8
   ```

3. 自精修一轮（halt rules）：只修 clarity/流畅/重复，
   **不许**为讨好审稿删数据、删 limitation、改结论强度；每处改动在
   `workspace/drafts/revision_log.md` 留一行。拿不准是否更好的修改，
   在 revision_log 保留原文并标 `[REVERT-CANDIDATE]`，交 review 轮裁决；
   精修后必须复跑一致性闸门，引用密度或整合率较精修前下降即回滚该处修改。
4. 组稿完整性闸门：`python3 tools/tex_guard.py workspace/drafts` ——
   检查 TODO 占位残留（模板的标题/作者/摘要必须已替换）、`\input` 与
   图文件存在、`\ref` 无悬空、环境与花括号闭合。任一阻塞项不得记
   `draft_complete`。有 latex 环境则再编译验证，编译告警逐条处理或在
   revision_log 说明。
5. `loopctl gate --name draft_complete --status PASS
   --inputs workspace/drafts/main.tex,workspace/library/references.bib`
   并交 review。

## 返工协议

收到 reviewer 的 issue（账本里 target=writing）：逐条修，修完
`loopctl issue close --id <I?> --note "<改了什么>"`；不同意的意见要在
revision_log 里写反驳理由并保留原文，交由下轮 review 仲裁，不许静默忽略。
