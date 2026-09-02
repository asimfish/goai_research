# goai_sagemat_defense - Design Spec

> Human-readable design narrative. Machine-readable execution contract: `spec_lock.md` (wins on divergence).

## I. Project Information

| Item | Value |
| ---- | ----- |
| **Project Name** | goai_sagemat_defense — SAGE-Mat / GoAI Research 复赛方案说明 |
| **Canvas Format** | PPT 16:9 (1280x720) |
| **Page Count** | 12 |
| **Design Style** | Mode `pyramid` + Visual style `swiss-minimal` |
| **Target Audience** | GOAI 2026 AI for Research（材料方向）复赛评审：材料科学与 AI4Science 专家，线上答辩 + 通读材料 |
| **Use Case** | 随作品提交的方案说明 PPT；官方要求前三页讲清科学问题、系统能力、关键结果；另需覆盖方法、结果、复现情况、开源情况 |
| **Delivery Purpose** | `balanced`（既被评审通读，也用于线上答辩）→ body 24px |
| **Content Strategy** | balanced default：以 FINAL_REPORT.md / SUBMISSION.md 为唯一事实源，按 pyramid 重组为"结论先行 + MECE 支撑"，所有数字来自提交包指标文件，不新增事实 |
| **Created Date** | 2026-09-02 |

---

## II. Canvas Specification

| Property | Value |
| -------- | ----- |
| **Format** | PPT 16:9 |
| **Dimensions** | 1280x720 |
| **viewBox** | `0 0 1280 720` |
| **Margins** | left/right 72px, top 56px, bottom 48px |
| **Content Area** | 1136x616（x 72–1208，y 56–672）；页眉标题区 y 56–130，页脚 y 680–700 |

---

## III. Visual Theme

### Theme Style

- **Mode**: pyramid —— 评审需要结论先行；每页标题即断言，数字必带对照（Retrieval-Retro 基线、论文均值、checkpoint 汇总）。
- **Visual style**: swiss-minimal —— 学术评审语境，网格、直角、留白、无装饰，与正式报告图的低饱和视觉一致；不使用渐变与阴影。
- **Theme**: Light theme
- **Tone**: 学术、克制、可核验

### Color Scheme

| Role | HEX | Purpose |
| ---- | --- | ------- |
| **Background** | `#FFFFFF` | 页面背景 |
| **Secondary bg** | `#F3F5F8` | 面板/表头/侧栏背景 |
| **Primary** | `#1F4D78` | 标题色块、主色条、图标、重点数字 |
| **Accent** | `#C48A2B` | 唯一强调色（关键结论、当前节点），每页不超过几处 |
| **Secondary accent** | `#4F8A9E` | 第二系列（图表中的 RECIPE 对照、次级节点） |
| **Body text** | `#1D1D1F` | 正文 |
| **Secondary text** | `#5A6573` | 说明、图注 |
| **Tertiary text** | `#8A94A0` | 页脚、来源 |
| **Border/divider** | `#D5DBE3` | 分隔线、表格线 |
| **Grid** | `#E6EAF0` | 图表网格线（比分隔线更浅） |
| **Surface** | `#EEF2F6` | 图表面板底 |
| **Success** | `#2E7D32` | 通过/PASS 语义 |
| **Warning** | `#C62828` | 失败/限制语义 |

（无 AI 生成图，不锁定 image rendering / palette。）

### Gradient Scheme

不使用渐变（swiss-minimal）。

---

## IV. Typography System

### Font Plan

**Typography direction**: 中性 CJK 无衬线，单一家族，用字重（700/400）与字号做层级（swiss-minimal 的 grotesque 性格）。

| Role | Chinese | English | Fallback tail |
| ---- | ------- | ------- | ------------- |
| **Title** | `"Microsoft YaHei"`, `"PingFang SC"` | `Arial` | `sans-serif` |
| **Body** | `"Microsoft YaHei"`, `"PingFang SC"` | `Arial` | `sans-serif` |
| **Emphasis** | same as Body（用 700 字重 + Primary 色） | same | same |
| **Code** | — | `Consolas`, `"Courier New"` | `monospace` |

**Per-role font stacks**:

- Title: `"Microsoft YaHei", "PingFang SC", Arial, sans-serif`
- Body: `"Microsoft YaHei", "PingFang SC", Arial, sans-serif`
- Emphasis: same as Body
- Code: `Consolas, "Courier New", monospace`

### Font Size Hierarchy（px，body 24 为锚）

| Role | px | Note |
| ---- | -- | ---- |
| cover_title | 60 | 仅封面 |
| title | 40 | 页标题（断言句），每页一致 |
| subtitle | 30 | 章节副题 / 封面副题 |
| lead | 26 | 每页核心结论行（≥ body） |
| hero_number | 56 | KPI 大数字 |
| body | 24 | 正文 |
| annotation | 18 | 图注、说明、表格正文 |
| chart_annotation | 16 | 图表刻度、数据标签 |
| footnote | 16 | 页脚、来源、页码 |
| code | 18 | 命令行 |

Formula policy: `text-only`（无公式）。

---

## V. Layout Principles

- 页眉：左上 72px 起，标题 40px 700 字重；标题下 12px 处一条 4px 高、72px 宽的 Primary 色短横（唯一装饰性结构元素）。
- 页脚：y=690，左侧 `SAGE-Mat · GoAI Research` 16px 三级文字，右侧页码 16px；封面无页脚。
- 网格：12 列（列宽 78.67px，间距 16px）；卡片直角 `rx=0`，边线 1px `#D5DBE3` 或面板底 `#F3F5F8`，不加阴影。
- 布局模式：封面 = 版式化排字海报（左大字，右侧竖向关键数字栏）；图页 = 非对称 7:5（图 812px 宽 + 右侧要点）；指标页 = 图表占 2/3 + 右侧解读；链路页 = 水平 5 节点链 + 下方实例；结论页 = 单列居中留白。
- 密度按 `page_rhythm`：dense 页允许多列卡片；breathing 页不用多卡片网格。

---

## VI. Icon Usage Spec

- 库：`tabler-outline`，stroke_width 2，颜色 Primary `#1F4D78`（图标只用 `fill`）。
- 语法：`<use data-icon="tabler-outline/<name>" x y width height fill="#1F4D78" stroke-width="2"/>`
- 已同步到 `icons/tabler-outline/`：search, shield-check, chart-bar, flask, atom-2, git-branch, file-check, users, route, target, database, repeat, brand-github, microscope, report-analytics, list-check, hierarchy-2, alert-triangle, cpu, network

---

## VII. Visualization Reference List

Catalog read: 76 templates

| Page | Template | Path | Summary-quote (verbatim) | Usage |
| ---- | -------- | ---- | ------------------------ | ----- |
| P05 | pipeline_with_stages | templates/charts/pipeline_with_stages.svg | "Pick for 3-5 horizontal pipeline stages, each = title + 1-line description + output artifact, connected by arrows (data pipelines, ETL, build pipelines)." | RECIPE 三阶段（候选生成 → 过滤枚举 → 集合重排）+ MCP 输出产物 |
| P06 | kpi_cards | templates/charts/kpi_cards.svg | "Pick for 4-8 standalone numeric metrics shown as overview cards (2x2 or 1x4) — exec summary opener, dashboard headline, quarterly recap, results-at-a-glance." | 正式案例四个关键数字（51/51、100 条、219 次、23 页） |
| P09 | grouped_bar_chart | templates/charts/grouped_bar_chart.svg | "Pick for 2-4 series side-by-side across the same categories (e.g. YoY/QoQ)." | Retrieval-Retro vs RECIPE（checkpoint 评测汇总）在 Combo@1 / Combo@5 / Combo@20 / Combo MRR 四类指标上的对照 |

Runners-up considered:
- numbered_steps | rejected for P05: 每个阶段都有明确输出产物（候选池 / 4,928 个集合 / Top-K 排序），pipeline_with_stages 更贴合
- bullet_chart | rejected for P06: 这些指标没有 target/actual 结构，是结果一览
- dumbbell_chart | rejected for P09: 对照只有两个系列且要在四个指标上并列比较，分组柱状图更直观
- process_flow | rejected for P04: 闸门链需要"当前节点/状态"语义，用自绘节点链而非模板（no-template-match，P04 自绘）
- layered_architecture | rejected for P03: 三层架构由提交包中的系统流水线图（用户提供图）承载，不再重复画层

P04（九个闸门链）、P10（追溯链五节点）为 `no-template-match`：结构性示意，自绘直角节点 + 单线连接。

---

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Acquire Via | Status | Reference | text_policy | page_role |
| -------- | --------- | ----- | ------- | ---- | -------------- | ----------- | ------ | --------- | ----------- | --------- |
| system_pipeline.png | 1846x1028 | 1.80 | P03 系统流水线（系统自绘 figspec 渲染） | Diagram | #3 right-third image + #21 rounded rectangle crop | user | Existing | 用户提供 | | |
| byzso_roadmap.png | 1600x900 | 1.78 | P06 正式报告研究路线图（第三轮学术化重绘） | Diagram | #5 top-bottom band | user | Existing | 用户提供 | | |
| byzso_evidence_map.png | 1500x900 | 1.67 | P07 证据来源—路线—用途图（备用，若版面允许） | Diagram | #2 left-third image | user | Existing | 用户提供 | | |
| byzso_route_matrix.png | 1500x860 | 1.74 | 备用（本次不放置） | Diagram | #2 left-third image | user | Existing | 用户提供 | | |

图均为示意图，`no-crop`（图中文字不可裁切）。无 AI 图，image-as-canvas 家族不适用（全部为需完整显示的示意图）。

---

## IX. Content Outline

### Part 1: 问题与系统（前三页讲清科学问题、系统能力、关键结果）

#### Slide 01 - 封面
- **Cover impact**: 钩子 = 一句核心主张"一行主题进去，可核验的综述与合成路线出来"；构图 = 版式化排字海报：左侧大字主标题 + 副题，右侧一条竖向 Primary 色栏承载四个关键数字（51/51、100、2,558、23），无背景装饰。
- **Layout**: 左 2/3 文字栏，右 1/3 竖色栏
- **Title**: SAGE-Mat：面向无机材料合成调研与合成规划的证据约束多智能体系统
- **Subtitle**: 一行主题进去，可核验的综述、证据链与候选合成路线出来
- **Info**: GOAI 2026 · AI for Research 材料方向 · 进阶路线 C ｜ 高京 · 吕丁阳 · 李雨峰（上海交通大学 / 中国科学院大学）｜ github.com/asimfish/goai_research

#### Slide 02 - 科学问题
- **Layout**: 上方核心结论行；下方左右两栏（两个案例）+ 底部三条难点
- **Title**: 新化合物的合成条件散落在文献里，"哪些能迁移"才是要回答的问题
- **Core message**: 对只有单篇报道的化合物，研究者需要知道文献能限定什么、哪些条件可从近邻体系迁移、哪些迁移不成立、下一步做什么实验最有发现价值。
- **Content**:
  - 案例 A · Ba5Y12Zn[O(SiO4)]8（BYZSO）：2024 年首次报道的非中心对称硅酸盐；公开文献仅 1 篇直接合成报道，未给出可复现的投料比、温程和冷却程序；近邻 Ba–Y–Si–O、Ba–Zn–Si–O、Y–Si–O 体系证据丰富——"文献稀缺、近邻丰富"。
  - 案例 B · LLZO 石榴石固态电解质：低温致密化、两步烧结、冷烧结、超快烧结各有先例，却缺少跨掺杂体系可比的工艺图景——"文献丰富、条件不可比"。
  - 难点：检索混入综述与参考文献 · "未检出"≠"未研究"（别名与语料覆盖制造假空白） · 温度/气氛/致密度只有在实验语境一致时才能比较

#### Slide 03 - 系统能力
- **Layout**: 左 812px 系统流水线图（no-crop），右侧三层要点
- **Title**: 系统把"生成像论文的结论"改为"保存证据与判定过程"
- **Core message**: 三层分离——认知层 9 个 Markdown 技能由 Codex 宿主执行，确定性层 4 个 MCP server/25 个工具可离线测试，控制层账本回环由代码判定"完成"。
- **Visualization**: 用户提供图 system_pipeline.png
- **Content**:
  - 认知层 · 9 个 agent 技能：编排 / 五源检索 / 风格库 / 引用核验 / 分类法与写作 / 图纸 ×2 / 想法与实验方案 / 对抗审稿
  - 确定性层 · 4 个 MCP server：litsearch（在线 + 本地全文库）· refcheck（存在性 / 元数据 / 作者顺序三轴）· figure（figspec → SVG + draw.io）· retro（两阶段前驱体预测）
  - 控制层 · 账本回环：9 个出口闸门、`check-done` 需全部落账且审稿 PASS 带回执；审稿人不改稿，执行者不自判

### Part 2: 方法

#### Slide 04 - 方法路线与闸门
- **Layout**: 上方 9 节点水平闸门链（自绘直角节点 + 单线），下方两栏：人工停点 / 对抗审稿
- **Title**: 九个出口闸门由代码判定完成，审与做分离
- **Core message**: 完成不是模型自报——`check-done` 只在九个闸门全部落账、无 FAIL、无 open blocker/major、且 review_pass 指向真实 trace 时退出 0。
- **Content**:
  - 闸门链：范围确认 → 文献覆盖 → 风格库 → 引用完整性 → 分类法 → 图纸 → 稿件 → 想法审稿 → 终审
  - 人工停点（正式运行触发 4 次）：范围确认 · 5 条作者名 MISMATCH 三轮未收敛升级 · 贡献结构确认 · 终审
  - 对抗审稿：全新上下文、三视角（领域专家 / 方法严谨派 / 期刊编辑）、结构化 issue 路由回属主阶段；同一 issue 三轮未收敛升级人工

#### Slide 05 - RECIPE 融入
- **Layout**: 上方三阶段流水线（pipeline_with_stages 结构），下方左右：融入规则 / 输出字段
- **Title**: 前驱体预测来自团队 NeurIPS 2026 投稿 RECIPE：把逆合成改为变长集合排序
- **Core message**: Generator 高召回 → 化学过滤与 2–5 元集合枚举 → Complete-Set Reranker 对完整前驱体集合排序；以 MCP 工具 `predict_precursor_routes` 进入想法环节，输出只能标注为"模型候选、待实验验证"。
- **Visualization**: pipeline_with_stages
- **Content**:
  - 阶段 1 · Precursor Candidate Generator：formula-token Transformer 对目标式与 798 个前驱体打分 → 输出 Top-30 候选池
  - 阶段 2 · 化学硬过滤 + 变长枚举：非挥发元素须为目标元素子集，pool ≤ 15 → 2–5 元组合，典型 4,928 个集合
  - 阶段 3 · Complete-Set Reranker：目标条件化集合 token + 374 维集合描述子，listwise 重排 + 最强负样本间隔 + 元素覆盖辅助损失 → Top-K 完整集合
  - 融入规则：skill 层硬性规定 `chemical_route_verified=false`；每条路线带 Stage-1 概率、Stage-2 分数、候选池内概率、checkpoint SHA-256；须经文献证据补全与审稿人复核
  - 正式报告调用 3 次：Zn 目标 Top-1 `ZnO + Y2O3 + SiO2 + BaCO3`（0.594）· Mg 类比 `MgO + …`（0.522）· Co 类比 `Co3O4 + …`（0.298）

### Part 3: 结果

#### Slide 06 - 正式案例结果
- **Layout**: 上方 1x4 KPI 卡（kpi_cards 结构，直角无阴影），下方研究路线图（no-crop，居中）
- **Title**: 纯主题冷启动：51 篇文献全部核验、100 条结论全部可追溯、23 页正式报告
- **Core message**: 唯一输入是一行主题；系统在 4 个人工停点续跑后交出 20 页综述，再经专家反馈修订为 23 页正式稿。
- **Visualization**: kpi_cards + 用户提供图 byzso_roadmap.png
- **Content**:
  - 51 / 51 文献三轴核验 PASS（63 条候选入库 51 条）
  - 100 条含引用结论 · 219 次引用 · 整合率 100% · 41.3 次/千词
  - 3 张图 figspec → SVG + draw.io 同源，通过排版 lint
  - 两轮对抗审稿：0 blocker / 0 major / 0 minor
  - 图注：正式报告研究路线图——从 Ba–Y–Si–O 组成空间，经候选晶相与两条合成路径，到互补表征反馈

#### Slide 07 - 科学结论与实验方向
- **Layout**: 左栏三条结论（编号），右栏四个方向 + 模型 Top-1 前驱体
- **Title**: 目标相只有一篇直接报道；组成坐标比单一温度更能解释成相差异
- **Core message**: 系统给出的不是配方，而是文献证据限定的可迁移范围与四类可检验实验方向。
- **Content**:
  - 结论 1：公开证据只能确认"开放体系高温溶液法 + 单晶 X 射线衍射鉴定"，不足以给出经验证的复现配方
  - 结论 2：无 Zn 四方谱系提供三类可比路线——MoO3 助熔（Pt 坩埚、1150 °C、2 K/h）、`x:26:16` 固相陶瓷（1300 / 1600 °C）、`5:13:8` 粉体相场筛查（1273 / 1573 K）——数值不得无条件迁移
  - 结论 3："获得单晶"不等于"建立批量相纯窗口"；局部相图是连接复现与发现的核心实验
  - 方向 1 目标组成附近的局部相图 · 方向 2 Zn–Y–氧计量耦合 · 方向 3 固相成相与高温溶液长晶并行 · 方向 4 Mg/Co 类比
  - 模型候选（待实验验证）：Zn `ZnO+Y2O3+SiO2+BaCO3` · Mg `MgO+Y2O3+BaCO3+SiO2` · Co `Co3O4+Y2O3+BaCO3+SiO2`

#### Slide 08 - LLZO 案例
- **Layout**: 左侧三个数字（竖排）+ Top-1 路线；右侧失效模式列表（两列）
- **Title**: 初赛承诺的 LLZO 诊断轮跑通端到端，并暴露、修复了 11 类集成失效模式
- **Core message**: 46 篇文献六个子主题覆盖、46/46 核验通过、10 页综述、模型 Top-1 与文献一致；Top-2 起出现可疑命名，因而保留"模型生成—规范化—文献复核—审稿"闸门。
- **Content**:
  - 46 篇 · 21 个 Agent 任务 · 49 次 MCP 调用 · 10 页 A4
  - 模型 Top-1 `ZrO2 + La2O3 + Li2CO3` 与文献一致；Top-2–5 出现 `LiHO` / `La(HO)3` → 标记"化学路线未验证"
  - 失效模式（已修复）：MCP 审批配置 · Agent 工作目录 · 并行写库竞争 · exit=0 假成功 · 旧产物假成功 · 上下文膨胀 · 上游限流 · 图片 lint 假绿 · retro 字段不兼容 · 测试契约漂移 · 同模型审稿独立性
  - 后续替代材料分析：Li6PS5Cl / Li3YCl6 / LATP 的模型 Top-1 路线均通过文献复核

#### Slide 09 - 基准指标
- **Layout**: 左 2/3 分组柱状图，右 1/3 解读 + 一致性说明
- **Title**: 留出测试集 Combo@1 71.81，比 Retrieval-Retro 高 11.4 点
- **Core message**: 指标来自随 checkpoint 提交的源包评测汇总，落在论文三种子区间内；逆合成部分只交 checkpoint、最小加载/预测代码与原料库，CPU dry run 保证可加载可预测。
- **Visualization**: grouped_bar_chart（两系列：Retrieval-Retro / RECIPE checkpoint 评测汇总；类别：Combo@1、Combo@5、Combo@20、Combo MRR；值 60.40/66.22/69.00/63.29 vs 71.81/84.71/89.21/77.48）
- **Content**:
  - Stage 1 Top-20 覆盖 95.78（基线 92.96）
  - 论文三种子均值：71.70 ± 0.10 / 84.52 ± 1.48 / 89.82 ± 1.74 / 77.43 ± 0.69
  - 同枚举 product 对照仅 Combo@1 11.65 / MRR 23.24 → 增益来自学习到的集合级排序，而非枚举或过滤
  - 来源：vendor/two_stage_retro/checkpoints/stage1_summary.json、stage2_summary.json；dry run：tools/retro_dry_run.py

### Part 4: 复现与开源

#### Slide 10 - 证据链与可追溯
- **Layout**: 上方五节点水平链（自绘），中部一条真实结论示例，底部运行统计三段
- **Title**: 每条结论可追溯：代码版本 → 配置 → 数据 → 日志/轨迹 → 结果文件
- **Core message**: 报告中 100 条结论、3 张图、每条前驱体预测都能沿同一条链回到提交包中的具体文件。
- **Content**:
  - 链：tag goai-final-2026-09-03 → topic.md / scope.md / Codex 配置 → references.bib + CITATION_AUDIT.json + corpus_release → parallel/<batch>/<task>.jsonl + ledger.json + tool_calls.jsonl → sections/*.tex → PDF
  - 示例 C012："该文采用开放体系高温溶液法，并以单晶 X 射线衍射鉴定晶体。" → `ababaikeri2024ba5y12zn` · DOI 10.1039/D3NJ04480G · 三轴 PASS · 子任务 `write_identity_evidence.jsonl`
  - 运行统计：40 个子任务 / 29 批 · 7,084 万输入 token · 224 次工具函数调用 · 205 次网页搜索 · 134 条服务端审计调用
  - 数据边界：私有全文库不公开；公开包含被引 51 篇中 21 篇全文（review-only），其余 30 篇 DOI + 官方链接

#### Slide 11 - 复现情况与限制
- **Layout**: 左栏命令与预期输出（等宽字体），右栏已知限制四条
- **Title**: 干净环境一键冒烟 1–2 分钟；核心流程以闸门一致为复现判据
- **Core message**: 确定性部分（模型 dry run、渲染、闸门）在干净环境稳定通过；LLM 部分不可逐字复现，以 check-done 退出 0、CITATION_AUDIT 全 PASS、整合率 ≥ 90% 为判据。
- **Content**:
  - `bash install.sh --retro` → `bash scripts/smoke_test.sh --with-retro` → `SMOKE TEST PASSED`（56 项离线测试、4 个 MCP server、公开知识库、结论—证据链、figspec 渲染）
  - `tools/retro_dry_run.py Li7La3Zr2O12` → 校验 checkpoint、CPU 预测 Top-5，RETRO DRY RUN PASSED
  - `bash scripts/reproduce_core.sh --topic "…"` → Codex CLI 0.146.1 · gpt-5.6-sol · reasoning xhigh，同一主题重跑整条流水线
  - 限制：目标相仅 1 篇直接报道，无"已验证配方" · 公开知识库覆盖 21/51 全文 · 终审为同家族模型冷启动复审 · 正式 PDF 含有记录的专家反馈修订

#### Slide 12 - 开源与结论（Closing）
- **Closing impact**: 带走的一句话——"把'该不该相信这条结论'变成可以点开 DOI 与原文段落回答的问题"；构图 = 单列居中大字结论 + 下方三栏（开源 / 可复用 / 下一步）+ 仓库地址。
- **Layout**: 上半居中 lead 大字，下半三栏
- **Title**: MIT 开源、tag 固定；下一步是跨模型审稿与实验验证
- **Content**:
  - 开源：github.com/asimfish/goai_research · MIT · tag goai-final-2026-09-03 · 全部 Prompt / 配置 / 模型 checkpoint / 轨迹 / 证据包
  - 可复用：任意主题的综述回环 · 引用零信任核验 · figspec 可编辑图纸 · 无机前驱体预测 MCP 工具
  - 下一步：接入跨模型审稿（Claude Code）· 对四个方向开展合成实验并回写证据 · 扩展条件预测器（温度 / 气氛）
  - 团队：高京（SJTU）· 吕丁阳（UCAS）· 李雨峰（SJTU）

---

## X. Speaker Notes Requirements

- 文件名与 SVG 一致（`01_封面.svg` → `notes/01_封面.md`）
- 总时长约 8 分钟；风格正式、结论先行；目的 inform + persuade
- `notes/total.md` 使用 `#` 标题分页，分页文件不含 `#`

---

## XI. Technical Constraints Reminder

1. viewBox `0 0 1280 720`；背景用 `<rect>`
2. 换行用 `<tspan x dy>`；禁 `<foreignObject>`、`<style>`、`class`、`mask`、`textPath`、`animate*`、`script`、`<g opacity>`、`rgba()`、HTML 命名实体
3. 图片 `<image href="../images/…" preserveAspectRatio="xMidYMid meet"/>`（均 no-crop）
4. 图标 `<use data-icon="tabler-outline/…" fill="#1F4D78" stroke-width="2"/>`
5. 颜色仅取自 spec_lock colors；字号仅取自 spec_lock typography；顶层语义 `<g id>` 3–8 个
6. 图表页含 `<!-- chart-plot-area -->` 与 `data-pptx-native="chart"` 元数据
