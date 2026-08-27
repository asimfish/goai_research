---
name: goai-style-bank
description: Use when building the domain style bank before figures/writing — 风格库 agent：检索本领域 30 篇经典综述，学习其写作风格与画图风格，沉淀成可消费的风格卡（结构骨架/句式卡/图型语法/配色基准）+ 范图库。触发词：「风格库」「学习经典综述」「style bank」。
---

# GoAI Style-Bank —— 领域风格库 agent

综述的「专业感」来自领域惯例，不来自通用模板。本 skill 在动笔/动图之前
把领域惯例学出来：**检索 30 篇经典综述 → 提取写作与画图风格 → 沉淀风格卡**。
产物被 goai-survey-writer（阶段零）与 goai-figure-studio（生图 prompt）消费。
只学结构、句式模式与视觉语法，**不抄内容**；范图仅作风格参照，不进交付物。

## 产物清单（全部在 workspace/style_bank/）

| 文件 | 内容 |
|---|---|
| `exemplar_surveys.jsonl` | 30 篇经典综述元数据 + 入选理由（被引/venue/相关度） |
| `writing_style_cards.md` | 写作风格卡（见下） |
| `figure_style_cards.md` | 画图风格卡（见下） |
| `exemplar_figures/` | 3-5 张代表性主图 PNG（版权参照用，禁止进交付物） |
| `style_bank_log.md` | 检索式、全文获取成败、提取方法记录（可复现） |

## 规程

### 1. 经典综述检索（目标 30 篇，25 篇为下限）

- 检索式：`<主题词> + (survey | review | progress | advances)` 的 3-4 组变体，
  `search_papers` sources 至少 `openalex,semanticscholar,crossref`（综述的
  被引数据在这些源最全），年份窗放宽到近 15 年。
- 排序与筛选：按被引降序 + venue 加权（Chem Rev / Chem Soc Rev / TPAMI /
  ACM CSUR / Nature Reviews 系 / IJCV 等顶刊综述优先），人工核对标题确为
  综述体裁（排除 perspective/editorial）。相关度分三档记入 jsonl：
  `core`（同主题）、`adjacent`（同大领域）、`method`（跨领域但体裁典范）。
  core 不足 15 篇时如实记录并放宽到 adjacent 补齐。
- 入档 `exemplar_surveys.jsonl`（独立于主库 papers.jsonl——风格库不是引用池；
  其中与主题直接相关的 core 篇目**同时** `save_to_library` 进主库供正文引用）。

### 2. 全文获取（尽力而为，目标 ≥10 篇全文）

- 有 OA 渠道的调 `download_pdf` 存 `workspace/style_bank/pdfs/`；
  付费墙照 lit-search 规矩：跳过并记录，不绕。
- 拿不到全文的篇目：用 OpenAlex 的结构化字段（abstract、referenced_works
  数、biblio 页码）+ Semantic Scholar tldr 做浅层提取。
- 全文 <5 篇时 gate 只能记 WARN 并注明「浅层风格库」。

### 3. 写作风格提取 → writing_style_cards.md

对每篇全文提取，再跨篇归纳出**领域基准**（每项给出现频次）：

- **结构骨架**：节标题序列（照录）→ 归纳众数骨架（如
  Intro → Fundamentals → Taxonomy → per-branch → Applications →
  Challenges → Outlook）；taxonomy 主图出现在第几节。
- **开题模式**：Intro 首段句式模式 2-3 个（照录原句 + 标注出处，写作时
  只允许模仿句式结构，禁止照抄原句——writer 侧有 lint）。
- **branch 节写法**：topic sentence 模式、每小节引用密度、
  对比表的列设计习惯（性能列用什么指标口径）。
- **Open Problems 写法**：逐条式还是叙事式、每条是否配文献锚点。
- **量化基准**：篇均引用数、页数、引用密度（次/页）、图表数——
  这些数字直接喂给 writer 的 bank_check/bib_guard 参数决策。

### 4. 画图风格提取 → figure_style_cards.md

- 全文 PDF 用 `pdftoppm`/`pdfimages` 抽页面图，定位每篇的**主图**
  （taxonomy 总览/框架图，通常在前 3 节）；无全文的按图注文本统计。
- 每篇主图记：图型（树/流水线/矩阵/时间线）、布局方向、配色系
  （从图中采样 2-3 个主色 hex）、标注密度（模块数/边数/图例项数）、
  是否双栏通栏。
- 跨篇归纳**领域图型语法卡**：本领域主图的众数图型、典型配色
  （学术克制系的具体色值）、模块数量的舒适区间、图例惯例。
- 挑 3-5 张最能代表领域水准的主图存 `exemplar_figures/`（记录出处 DOI），
  作为 figure-studio 生图时的风格参照图（reference image）。

### 5. 收工

- `style_bank_log.md` 记全程；
- `loopctl gate --name style_bank_ready --status PASS
  --detail "<N 篇入档/M 篇全文/写作卡+图卡齐/范图 K 张>"
  --inputs workspace/style_bank/writing_style_cards.md,workspace/style_bank/figure_style_cards.md`；
- 全文 <5 篇或 core <15 篇时记 WARN 而非 PASS，detail 写明缺口——
  下游按浅层风格库降级消费，不阻塞流水线。

## 并行约定

本 skill 与 lit_search 并行执行（orchestrator 在 scoping 后同时派发）：
两者都写主库但 `save_to_library` 幂等去重，安全；style_bank/ 目录只归本
skill 写。检索预算：礼貌限速下 30 篇元数据 + 10 篇 PDF 约 15 分钟。

## 硬性规则

- 每张风格卡的每个结论都要标注来源篇目（jsonl 里的 id），不许「凭印象」。
- 原句照录仅限句式参照区并逐句标出处；范图仅限风格参照，**禁止**
  出现在综述交付物或 examples 中（版权）。
- 领域无经典综述（新兴主题）时如实上报，用 `method` 档跨领域典范补齐，
  并在卡片头部声明「跨领域基准」。
