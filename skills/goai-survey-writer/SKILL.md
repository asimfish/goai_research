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

## 语言契约（scoping 定死，全程一致）

交付语言在 scope.md 里显式记录：用户指定为准；未指定时跟随主题语言。
语言决定模板与排版规范，**禁止中文正文套英文模板**（Abstract/Table 标签
混排是杂交文档，tex_guard 会告警）：
- 英文交付 → `templates/survey_main.tex`（article + newtx + pdflatex/xelatex）；
- 中文交付 → `templates/survey_main_zh.tex`（ctexart + fandol 字库，
  **必须 xelatex**），标签自动本地化（摘要/图/表/参考文献）。中文细则：
  正文标点全角；中西文间隙交给 xeCJK，禁手工空格；段首加粗小标签用
  「……：」或 `\paragraph{}`，禁英文式 run-in「标签。」；页眉短题用楷体。
- 两种语言的参考文献均保持 natbib 数字制；正文语言与文献条目语言允许
  不同（中文综述引英文文献是常态，不翻译条目）。

## 术语防火墙（内部词汇不入正文）

流水线内部词汇——gate/issue/ledger/loopctl、ref_gate、niche-balanced、
comprehensive 档、bank、WARN 等——**禁止出现在题目/摘要/正文/表格/图注**
里。读者面前只有学术语言：「检索截至 2026-08-31」而不是「ref_gate 后」。
证据分级代号（如 D0/D1/N1/P1、strong/weak）如果确要作为论文的记号体系，
必须在正文里正式定义（表格或术语节），排版用正体或小型大写，
**不用 `\texttt`**。`\texttt` 只留给真正的代码、命令、文件名；
缺失值/未报道一律用 —（em dash）或「未报道/not reported」，
禁止打字机体 `NA` 铺表——tex_guard 对 `\texttt` 密度有告警线。

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

**骨架强制项**（蓝图缺任何一项即返工）：
- **行文路线图（roadmap figure）**：Intro 末尾或 §2 开头必须配一张
  本文组织结构图——各节回答什么问题、按什么顺序推进、图表落在哪节。
  在 figure_plan.md 登记为标准图（顶会综述标配，读者导航用）。
- **近邻/同型体系小节**：材料与实验科学主题的 Intro 必须有独立小节
  （或 ≥2 段）专讲相似体系的已有发现——同型结构、同家族化学、可迁移
  工艺——逐条带引用；这是精确目标文献稀少时读者最需要的证据地图。
  写不出来 = lit_search 的近邻检索面没做够，开 issue 返工检索。
- **既有实验结论合集**：结果部分先给「前人实验结论的系统合集」
  （条件-结果对照表 + 逐条结论），再进入本文的分析与新贡献；
  结论不允许散落在叙述里让读者自己拼。
- **新方向 → 推荐实验**：Open Problems / Future Directions 不许停留在
  「值得进一步研究」——每个方向必须落到可执行建议：推荐做什么合成
  实验、采用什么工艺路线、用什么前驱体（消费 idea-forge 调用
  goai-retro MCP 预测工具的产物，标注「模型预测，待实验验证」）。
- **Conclusion 双段式**：(a) 主要结论按证据强度总结；(b) 「最有科学
  发现价值的下一步实验」优先级清单（哪个实验能最快裁决当前最大的
  不确定性），与 Open Problems 的方向一一呼应。

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
  **禁止引用倾倒**：单处 `\cite{}` 最多 5 个 key（natbib `sort&compress` 会压
  成区间）；不得为了拉高整合率写「本文文献库含 N 条，按角色分组如下……」
  然后把几十上百个 key 堆进一段——那不是引用，是给读者一墙数字。库大而
  正文用不完的条目，按阶段五孤儿规则处理：找到真正的落点、放进对比表/
  附录表（角色 → 代表性文献 ≤5 条）、或开 issue 交 lit_search 评估后移出库；
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
- **表格设计规范**（数据表是综述的门面，按数据形状设计而不是硬塞）：
  - 一张逻辑表**禁止拆成上下两半共享行号**让读者自己拼——列太多时按
    「主题分组拆成多张完整子表」（各自带表头与 caption）、转置、或
    `landscape` 横排；正文表列数指导线 ≤7，超线必须重新设计；
  - 单元格内容是**读者语言**：禁止出现裸 BibTeX key（tex_guard 直接
    阻塞），来源一律 `\cite{key}` 或「作者 (年份) \cite{key}」；
  - 缺失值统一 — 或「未报道」，禁止整表铺 `\texttt{NA}`；一行内
    多字段全缺时合并为一格说明，不逐格复读；
  - 长表（>1 页）用 `longtable` 并重复表头；窄列一律模板的 `P{}` 列型；
  - 每张表交稿前自查：拿掉正文，单看此表 + caption 能否自解释。
- **材料领域判读规则**（条件表与路线分类时执行，来源：领域专家意见）：
  - 记录中出现 **Pt 坩埚 / Au 坩埚**（及 Ir/刚玉坩埚 + 高温慢冷组合）
    基本可判定为熔体/助熔剂晶体生长路线，归类时不得混入普通固相烧结；
    坩埚材质本身就是路线证据，条件表应保留该字段；
  - 讨论合成窗口、相稳定性或新配方时必须核查**相图**：库内有相图
    文献就引用并对照（组分点落在哪个相区、有无共晶/包晶陷阱）；
    检索不到目标体系相图时明确写「该体系相图未见报道」，并把
    「测定相图」列入实验建议——不许对相关系保持沉默。
- 并行写作时只碰自己的节文件，公共文件（main.tex/bib）只由汇合者动。

### 学术语言与内部术语隔离

正文、摘要、标题、表头、图中文字和图注必须使用本学科的研究对象、实验
条件、结构关系与表征方法来表述；账本、提示词和程序日志中的内部术语不得
直接进入论文。写作时将内部表达转换为下列学术表达：

| 内部表达（仅限 agent 状态） | 论文表达 |
|---|---|
| 证据级、比较标签 | 与目标相的关系、分类依据 |
| 过闸、证据包、引用池 | 已通过文献核查、本文获得的文献材料、本文核查的文献 |
| 字段、字段归一化 | 实验项目、合成条件的统一比较 |
| 验证终点、端点 | 表征方法、参照相 |
| 降权、迁移权限、工具箱 | 限制其适用范围、可外推范围、方法参照 |
| 身份锚点、谱系核验、验证闭环 | 直接结构依据、结构关系复核、可迭代的实验依据 |

不要在论文中使用“过闸”“标签”“字段”“端点”“证据包”“工具箱”等
软件流程隐喻。完成组稿后运行：

```bash
.venv/bin/python tools/academic_language_guard.py workspace/drafts/sections workspace/drafts/main.tex
```

该检查出现任何未解释的术语均视为写作阻塞项；若某术语确为研究对象本身，
必须在 `revision_log.md` 说明理由后以 `--allow` 明确放行。

## 阶段五：组装与精修

1. 按语言契约选模板组装（英文 `templates/survey_main.tex`、中文
   `templates/survey_main_zh.tex`），`\input` 各节。模板内置排版
   规范不许降级：Times 字体系（newtx，加载顺序 amsmath→newtxtext→
   newtxmath，禁 amssymb）、引用/交叉引用/URL 统一学术蓝
   （`colorlinks` + `citecolor=blue`）、caption 小号加粗标签、
   `\arraystretch 1.18`、紧凑节标题、fancyhdr 运行页眉、
   参考文献前 `\clearpage`。表格定宽列一律用模板的 `P{宽}`
   （raggedright）列型，禁用裸 `p{宽}`——窄列两端对齐会产生
   justify 空洞，是"表格乱"的头号来源；正文含 Unicode 组合符/希腊
   字母时用 xelatex 编译（中文模板必须 xelatex）。组装时必须完成
   两处替换：页眉短题（`TODO` 短题→论文短题）；主标题超一行时
   **手工断行成 2–3 行且行长均衡**，禁止让 LaTeX 自动折出孤词行。
   组装同时做 **bib 字段卫生**：直接跑 `python3 tools/bib_polish.py
   workspace/library/references.bib --write`（确定性修复：doi 在则删 url、
   化学式/缩写/元素前缀加 `{}` 保护、拆散的「Li 7 La 3」合并、裸 `&` 转义），
   再跑 bib_guard 确认卫生告警清零；然后 `python3 tools/tex_polish.py
   workspace/drafts --write`（正文斜杠改可断 `\slash`——「phase/density/transport」
   这类连词是 Overfull 头号来源；`\bibliography` 路径归一；直接引用 SVG 会被点名）。
   编译统一用 `bash scripts/build_tex.sh workspace/drafts`（干净构建 xelatex→bibtex→
   xelatex×2 并自动跑 pdf_guard；无 TeX 时直接 fail-closed 退出）。
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
   **语言自然度专项**（拗口是最常见的失败模式，两种语言都查）：
   - 逐段做朗读测试：一口气读不顺、定语连环套、一句超过 40 词/60 字
     的拆句重写；
   - 英文稿禁中式英语（逐字直译的搭配、"research(es)" 滥用、名词化
     堆叠 the utilization of…），动词优先、主语就近；
   - 中文稿禁翻译腔（"被"字滥用、"进行了…的研究"、"对于…而言"空转、
     欧化长定语），改短句与主动语态；
   - 每节抽 2 段与 style_bank 写作卡的句式模式对照，偏离领域惯用
     表达的改写；super_library lint 报告里的 wording 项逐条处理。
4. 组稿完整性闸门：`python3 tools/tex_guard.py workspace/drafts` ——
   阻塞项：TODO 占位残留（模板的标题/作者/摘要必须已替换）、`\input` 与
   图文件存在、`\ref` 无悬空、环境与花括号闭合、**裸 BibTeX key 泄漏到
   正文**（含与汉字紧贴的 key；确属同形词可在行尾注释
   `% tex-guard: allow-key` 豁免）；告警项：`\texttt` 密度过高、中文稿
   套英文模板。任一阻塞项不得记 `draft_complete`，告警项逐条处理或在
   revision_log 说明原因。**编译是硬性步骤，且只能用 TeX**：先
   `tools/check.sh --tex` 确认 xelatex/pdflatex 与模板宏包齐全；齐全则
   xelatex→bibtex→xelatex×2（中文稿必须 xelatex；图一律先 `drawio_export`
   出 pdf 再 `\includegraphics`，不依赖 `\includesvg`），编译告警逐条处理。
   **环境缺 TeX 时 fail-closed**：`draft_complete` 记 FAIL + issue「环境缺
   TeX」，交付 main.tex + references.bib + figures，终报明写「PDF 未编译」；
   **禁止**用 groff/Ghostscript、HTML→Chrome、pandoc、Word 等任何回退渲染器
   生成 PDF 冒充终稿——那样产出的文件没有摘要块、编号标题、公式排版、
   booktabs 表格和蓝色引用，账本却会显得「完成」。编译后必跑
   `python3 tools/pdf_guard.py workspace/drafts/main.pdf --tex workspace/drafts/main.tex --bib workspace/library/references.bib`
   （Producer 须为 TeX 引擎、字体须为模板字体族、PDF 不早于源文件、首页有
   Abstract/摘要、有编号一级标题），FAIL 不得置 `draft_complete`。最后
   `pdftoppm` 抽首页、一张表所在页、参考文献页各看一眼——标签语言、表格
   完整性、文献条目有无被压小写的化学式，这三处是制作质量事故的高发区。
   另外，`academic_language_guard.py` 必须通过，确保内部控制语言没有泄漏
   到正文、表格和图注。
5. `loopctl gate --name draft_complete --status PASS
   --inputs workspace/drafts/main.tex,workspace/library/references.bib,workspace/drafts/main.pdf
   --detail "bib_guard/tex_guard/academic_language_guard/pdf_guard 全 PASS；<引擎> 编译 <N> 页"`
   并交 review。PDF 也进指纹：源文件改了而 PDF 没重编，check-done 会把 gate
   置回 PENDING。

## 返工协议

收到 reviewer 的 issue（账本里 target=writing）：逐条修，修完
`loopctl issue close --id <I?> --note "<改了什么>"`；不同意的意见要在
revision_log 里写反驳理由并保留原文，交由下轮 review 仲裁，不许静默忽略。
