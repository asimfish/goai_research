# GOAI 2026 · AI for Research（材料方向）复赛提交说明

项目：**SAGE-Mat / GoAI Research** —— 面向无机材料合成调研与合成规划的证据约束多智能体系统
方向：材料科学文献驱动的科学发现智能体（进阶路线 C：合成路线与工艺设计）
代码仓库：<https://github.com/asimfish/goai_research>（提交 tag：`goai-final-2026-09-03`；提交前固定 commit hash 写入 `submission/goai_final/MANIFEST.sha256` 同级的 `VERSION`）

本文件是评审入口：先说明六项交付物在仓库中的位置，再给出模型与 Harness 声明、全部运行记录与正式结果的筛选规则、数据与许可边界、指标复核方式、一条结论的完整追溯链，以及冒烟测试 / 核心复现命令。

---

## 1. 六项交付物与位置

| # | 官方交付物 | 本仓库位置 |
|---|---|---|
| 非代码 1 | 方案说明 PPT + 复赛报告 | `submission/goai_final/deck/`（PPTX + PDF）；`submission/goai_final/report_docx/复赛报告_SAGE-Mat.docx`（正文源 `docs/competition/FINAL_REPORT.md`） |
| 代码 1 | 系统复现包 | 全部源代码 `server/`（4 个 MCP server、25 个工具）、`skills/`（9 个 agent 的全部 Prompt）、`AGENTS.md`、`tools/`、`vendor/two_stage_retro/`（预测模型代码 + checkpoint）、`configs/*.example`、`.env.example`、`pyproject.toml` + `uv.lock`（依赖版本）、`docs/competition/TASK_PROMPT.md`；构筑阶段 Agent 轨迹 `submission/goai_final/traces/development/` |
| 代码 2 | 研究数据与证据包 | `submission/goai_final/evidence/`：`references.bib`（51 条）、`papers.jsonl`（63 条候选）、`claim_evidence.jsonl`（100 条结论 → 219 次引用）、`CITATION_AUDIT.json`（逐条核验）、`notes/condition_source_trace.md`（合成条件单元格 → 原文页/节）、`corpus_release/`（被引文献全文的精简 Parquet 知识库 + 构建脚本 `tools/build_cited_corpus.py`） |
| 代码 3 | 运行与评测包 | `submission/goai_final/run/`：输入 `inputs/topic.md`、子任务提示词 `tasks/*.tsv`、账本 `ledger.json`、MCP 审计日志 `tool_calls.jsonl`、审稿 trace、Codex 事件流 `traces/runtime/parallel/<batch>/<task>.jsonl`（40 个子任务）、`traces/runtime/orchestrator/`、`RUN_MANIFEST.json`；次要案例 `submission/goai_final/run_llzo/`；原生 Codex 会话 `submission/goai_final/traces/runtime_native_sessions/` |
| 代码 4 | 指标与分析代码 | `tools/eval_retro_benchmark.py`（前驱体预测基准复现）、`tools/build_claim_evidence.py`（引用—证据链与核验率）、`tools/analyze_agent_traces.py`（轨迹统计）、`tools/bib_guard.py` / `tools/tex_guard.py` / `tools/academic_language_guard.py`（稿件闸门）；结果 `submission/goai_final/metrics/` |
| 代码 5 | README + 一键命令 | `README.md` / `README_CN.md`、本文件、`scripts/smoke_test.sh`、`scripts/reproduce_core.sh`、`install.sh` |

`submission/goai_final/MANIFEST.sha256` 列出提交包内每个文件的 SHA-256。

---

## 2. 系统、模型与 Harness 声明

**智能体 Harness**：Codex CLI **0.146.1**（`@openai/codex`）。

- 运行阶段（生成正式结果）：`codex exec --json --ephemeral -a never -s danger-full-access`，宿主收到的唯一输入是一行主题文本；子任务由 `tools/parallel_run.sh` 以同一 CLI 扇出，每个子任务的完整事件流保存在 `run/traces/runtime/parallel/<batch>/<task>.jsonl`（含 `.exit` / `.status` / `.final.md` / `.stderr.log`）。
- 构筑阶段（编写本仓库）：同一 Codex 内核通过 whalent 网关以多轮对话方式使用（`session_meta.originator = "whalent"`），完整原生 rollout 见 `traces/development/rollout-2026-08-16T22-01-50-….jsonl.gz`（43 轮、2026-08-16 → 2026-09-02，`turn_context` 中逐轮记录 `model` 与 `effort`）；网关侧同一对话的消息级导出为 `traces/development/whalent_codex_conversation.jsonl.gz`（3399 条）。仓库另一部分由队友（GitHub `asimplefish`）以 Codex CLI 通过 PR #1–#20 提交，其会话轨迹以 PR 形式留存于 GitHub 历史。
- 两类轨迹分目录存放，`traces/codex_sessions_index.json` 给出每个 rollout 的 originator、cwd、模型、推理强度和轮数。

**LLM 与采样参数**：

| 项 | 值 |
|---|---|
| 模型 | `gpt-5.6-sol`（OpenAI，经 Codex CLI 的默认 OpenAI 端点 `model_provider = "openai"`） |
| 推理强度 | `model_reasoning_effort = "xhigh"` |
| 温度 / top-p | Codex CLI 不暴露，采用服务端默认；LLM 输出**不可逐字复现**，复现目标是闸门级一致（见 §6） |
| 沙箱 / 审批 | `sandbox_mode = danger-full-access`，`approval_policy = never`，MCP `default_tools_approval_mode = "approve"` |
| 随机种子 | LLM 无可设种子；确定性组件有：两步前驱体预测模型 checkpoint（训练种子 20260504，SHA-256 见 `vendor/two_stage_retro/PROVENANCE.md`）、figspec 渲染器、bib/tex/术语闸门、引用核验（给定 API 返回时确定） |
| 外部 API（免密钥） | Crossref、OpenAlex、arXiv、Semantic Scholar、DBLP（文献检索与核验）；Codex 内置 `web_search` |
| 私有服务 | 无。不使用任何商业检索 API；不需要额外 API key |

**Prompt 全集**：`skills/goai-*/SKILL.md`（9 个角色的完整方法论提示词）、`AGENTS.md`（宿主路由表与铁律）、`docs/competition/TASK_PROMPT.md`（比赛任务模板）、`run/tasks/*.tsv`（正式运行中每个子任务收到的逐字提示词）、`run/inputs/topic.md`（唯一的人类输入）。

---

## 3. 全部运行记录与正式结果的筛选规则

复赛期间共进行 **7 组**运行，全部留痕；正式结果只取其中一组及其后续修订。

| # | 日期 | 运行 | 性质 | 留痕位置 |
|---|---|---|---|---|
| 1 | 08-27 | COF 光催化综述（框架样例） | 框架演示，非比赛结果 | `examples/competition_run/`、`examples/survey_cof_her/` |
| 2 | 08-29 | LLZO 烧结致密化诊断轮（初赛承诺主题） | 21 个 Agent 任务、49 次 MCP 调用；产出 10 页综述、46 篇核验文献、Top-5 前驱体路线 | `run_llzo/`、`submission/llzo_survey/`、`docs/competition/LLZO_AGENT_INTEGRATION_AUDIT.md` |
| 3 | 08-30 | LLZO 替代材料与路线分析 | 交互式补充分析 | `submission/llzo_survey/LLZO_ALTERNATIVES_AND_ROUTES.md` |
| 4 | 08-31 | Ba5Y12Zn[O(SiO4)]8（BYZSO）首轮 | 交互式编排 + 并行子任务；9 页报告 | `submission/byzso_synthesis_report/`、`traces/runtime_native_sessions/`（08-31 会话） |
| 5 | 08-31 | 冷启动 `cold_byzso_J4XmS8` | 仅给主题；停在文献阶段并交出 Markdown 笔记，暴露回环协议漏洞（`check-done` 只记一个 gate 即可宣告完成），已在 PR #17 机械化修复 | `traces/runtime/orchestrator/` 同名 `final.md`；修复见 `docs/audits/2026-09-02_spec_audit/` |
| 6 | 08-31 → 09-01 | **冷启动 `cold_full_byzso_m2gfJJ`（正式）** | 仅给主题；顶层编排器共调用 5 次（首轮 + 在 4 个人工停点处以同一主题续跑：范围确认、5 条作者名 MISMATCH 的处置、贡献结构确认、终审），29 批 / 40 个子任务；产出 20 页 PDF、51/51 核验文献、两轮对抗审稿 0 blocker / 0 major | `run/`（全部） |
| 7 | 09-02 | 对第 6 组产物的学术修订 | 依据材料专家 8 条意见：重写引言与同类体系、补前人实验结论汇总与相图讨论、四类研究方向 + MCP 前驱体预测、去除工程化术语（新增 `academic_language_guard.py`）、移除 Pt/Au 成对对照建议、三轮学术化重绘图 1–3；由并行子任务（`tasks_academic_repolish.tsv`、`tasks_academic_assemble.tsv`）与构筑阶段 Harness 直接编辑共同完成 | `run/tasks/`、`run/traces/runtime/parallel/20260902_*`、`traces/development/` |

**正式采用**：第 6 组冷启动结果经第 7 组修订后的最终稿 `report/Ba5Y12Zn_合成调研_学术润色版.pdf`（23 页）。
**筛选规则**：取最后一个同时通过全部机械闸门的版本 —— `bib_guard`（整合率 100%、无未定义键）、`tex_guard`（无占位/悬空引用）、`academic_language_guard`（无工程术语）、账本 `review_pass = PASS`。没有在多次运行间"挑最好的一次"：第 2–5 组各自完整留痕，其结论均以其自身产物为准，不混入正式报告。
**诚实边界**：终审 reviewer 为同家族 Codex 冷启动复审（`provisional = true`），不是跨模型独立认证；第 7 组修订包含人类专家意见驱动的编辑，因此正式 PDF 不是"零人工干预一次生成"，而是"一次冷启动 + 有记录的专家反馈修订"。

---

## 4. 数据、文献与许可边界

| 数据 | 来源 / 版本 | 许可与公开状态 | 对复现的影响 |
|---|---|---|---|
| 私有全文库 | 团队自建 Markdown 化全文库（约 3.76 千万篇，1990s–2021），DuckDB/Parquet 分片 + SQLite DOI 索引 | **不公开**（版权） | `grep_local_corpus` / `lookup_local_doi` 在公开环境只能命中下方精简包中的 21 篇；在线检索与核验（Crossref/OpenAlex/arXiv）不受影响 |
| 被引文献精简知识库 | `evidence/corpus_release/corpus.parquet`（`goai-compact-parquet-v1`）：正式报告 51 条参考文献中，私有库内有全文的 **21 篇** Markdown 全文；其余 30 篇（多为 2022–2026 年发表或不在库中）以 DOI + 官方链接形式列于 `cited_references_index.json` | 全文仅供评审复现使用，出版社版权保留，不得二次分发（`license` 字段已写明） | 构建脚本 `tools/build_cited_corpus.py`；`corpus_manifest.json` 含每篇 SHA-256；`tools/check.sh --corpus` 可验证 |
| 文献元数据与摘要 | `evidence/papers.jsonl`（63 条候选，来自 Crossref/OpenAlex/arXiv/S2） | 公开 API 元数据 | 完整提交 |
| 前驱体预测训练数据 | Retrieval-Retro 年份切分基准（源自 Ceder 文本挖掘合成数据集）：24,034 训练 / 1,842 验证 / 2,558 测试；`vendor/two_stage_retro/data/retro_split.csv` | 随源基准公开；本仓库只含推理所需最小数据与两份 checkpoint | 测试集与 checkpoint 完整提交，指标可独立重算（§5） |
| 风格库 | 30 篇经典综述的写作/画图风格卡（`style_bank`） | 风格卡为派生文本；原文 PDF 不分发 | 不影响闸门判定 |
| 模拟语料 | `examples/demo_corpus/`（3 条 CC0 合成文本，`citable=false`） | CC0 | 用于无私有数据时验证工具链 |

包内不含 API key、Token、密码或私有目录布局；导出脚本对轨迹做过密钥模式脱敏（`[REDACTED]`，共 4 处网关 Bearer/URL token）。

---

## 5. 指标与独立复核

### 5.1 无机前驱体预测（RECIPE 两步模型）的融入方式与复现

系统中"给定目标化合物 → 前驱体候选"由 `goai-retro` MCP server 的 `predict_precursor_routes(target_formula)` 提供，其内核是团队 NeurIPS 2026 投稿 **RECIPE（Reranking Exact Candidate Inorganic Precursor Entries）** 的两阶段模型：

1. **Precursor Candidate Generator**（Stage 1）：formula-token Transformer 对目标式与全部 798 个前驱体打分，取 Top-M（30）构成高召回候选池；
2. **化学硬过滤 + 变长集合枚举**：保留非挥发元素与目标元素兼容的前驱体（pool_cap 15），枚举 2–5 元组合（典型 4,928 个集合）；
3. **Complete-Set Reranker**（Stage 2）：以目标条件化的集合 token + 374 维集合描述子做 listwise 重排，直接对"完整前驱体集合"排序，返回 Top-K。

在综述流水线中，`goai-idea-forge` 对每个研究方向调用一次该工具，结果只能以"模型候选、待实验验证"（`chemical_route_verified=false`）写入正文，并保留 `stage1_probability`、`stage2_score` 与候选池内概率供审稿人核对；正式报告中对 Zn / Mg / Co 三个目标各调用一次（`run/ideas/precursor_predictions.md`，原始请求与返回在 `run/tool_calls.jsonl`）。

指标复核脚本 `tools/eval_retro_benchmark.py` 用**与 MCP 工具完全相同的推理代码**在 2,558 条留出测试反应上重算：

| 指标（Retro 测试集，全分母） | 本仓库重算 | checkpoint 自带汇总 | 论文 3 种子均值 | Retrieval-Retro 基线 |
|---|---:|---:|---:|---:|
| Stage 1 Top-20 前驱体覆盖 | 95.78 | 95.78 | 95.93 ± 0.18 | 92.96 |
| Combo@1（精确集合命中） | 71.81 | 71.81 | 71.70 ± 0.10 | 60.40 |
| Combo@20 | 89.21 | 89.21 | 89.82 ± 1.74 | 69.00 |
| Combo MRR | 77.48 | 77.48 | 77.43 ± 0.69 | 63.29 |
| 同枚举 product 对照 Combo@1 / MRR | 11.65 / 23.24 | 11.65 / 23.24 | 11.65 / 23.24 | — |

重算与 checkpoint 自带汇总逐位一致（单种子 20260504），并落在论文报告的三种子区间内；逐目标结果（真值集合在重排列表中的名次）在 `metrics/retro_benchmark.per_target.jsonl`。

### 5.2 文献与引用完整性

`tools/build_claim_evidence.py` 产出 `evidence/claim_evidence_summary.json`：正文 100 条含引用的结论、219 次引用、51 个独立键全部被使用（整合率 100%），`goai-refcheck` 对 51 条的存在性 / 元数据 / 作者顺序三轴核验全部 PASS；54 条结论有包内全文可直接回读，36 条合成条件结论带原文页/节定位。

### 5.3 Agent 运行统计

`tools/analyze_agent_traces.py` 对正式运行 40 个子任务的事件流统计（`metrics/agent_trace_stats_byzso.md`）：约 7,084 万输入 token / 56.7 万输出 token；224 次工具函数调用（`lookup` 25、`coverage_report` 25、`search_papers` 24、`save_to_library` 24、`render_figure` 17、`grep_local_corpus` 16、`verify_bib_file` 16 …）、205 次内置 web_search；任务状态 PASS 23、超时后产物完整放行（WARN）6、超时失败 9、失败 1、无终态 1。失败与超时任务均保留在轨迹中并由后续批次重跑，未被删除。子任务通过 Python 直接调用 MCP server 的同一函数，故事件流中 `mcp_tool_call` 计数为 0，工具调用以 `command_execution` 与服务端审计日志 `run/tool_calls.jsonl`（134 条）为准。

---

## 6. 一条结论的完整追溯链（示例）

结论 C012（`evidence/claim_evidence.jsonl`）："该文采用开放体系高温溶液法，并以单晶 X 射线衍射鉴定晶体。"

1. **代码版本**：tag `goai-final-2026-09-03`（`VERSION`）；生成该句的 skill 为 `skills/goai-survey-writer/SKILL.md`，写作子任务提示词 `run/tasks/tasks_write_sections.tsv`（任务 `write_identity_evidence`）。
2. **配置**：`run/inputs/topic.md`（唯一输入）、`run/inputs/scope.md`（自动确认的范围）、Codex 配置 §2。
3. **数据**：引用键 `ababaikeri2024ba5y12zn` → DOI `10.1039/D3NJ04480G`（`report/references.bib`）；核验记录 `evidence/CITATION_AUDIT.json`（三轴 PASS）；全文不在私有库（`cited_references_index.json: full_text_in_package=false`），证据来自出版社页面与 ESI（`evidence/notes/search_identity_structure.md`）。
4. **运行日志 / 轨迹**：子任务事件流 `run/traces/runtime/parallel/20260901_003133_1289042/write_identity_evidence.jsonl`；账本 `run/ledger.json` 中 `draft_complete` 与 `review_pass` 的记录及回执；审稿 `run/review_round2.md`。
5. **结果文件**：`report/sections/01_phase_identity.tex` 第 12 行附近 → `report/Ba5Y12Zn_合成调研_学术润色版.pdf` 第 1 章"目标相出处"。

同样的链对报告中的每张图（`report/figures/figspec/*.json` → `svg/` + `drawio/` → PDF）和每条前驱体预测（`run/tool_calls.jsonl` → `run/ideas/precursor_predictions.md` → 第 8 章）成立。

---

## 7. 一键安装 / 冒烟测试 / 核心复现

```bash
git clone https://github.com/asimfish/goai_research && cd goai_research
git checkout goai-final-2026-09-03
bash install.sh --retro                 # .venv + 依赖 + MCP 配置；--retro 装 torch/pymatgen
bash scripts/smoke_test.sh --with-retro # 无网络、无 LLM：约 1–2 分钟
```

冒烟测试通过时依次打印 `OK`：Python ≥ 3.10；4 个 MCP server 可导入；56 项离线测试通过；公开知识库可被 `lookup_local_doi` 命中；结论—证据链 100 条 / 51 键全部核验；figspec 渲染出 SVG 与 draw.io；（`--with-retro`）两步模型在 20 条留出目标上完成预测。最后一行 `SMOKE TEST PASSED`。

干净环境实测（2026-09-03，本地克隆）：`bash install.sh` 13 秒，`bash scripts/smoke_test.sh` 5 秒全部通过。`--retro` 额外安装 `torch<2.8`（默认拉取 CUDA 12 wheel，约 2.5 GB），下载时长取决于网络；只做 CPU 复核时可先 `pip install torch --index-url https://download.pytorch.org/whl/cpu` 再运行 `install.sh --retro`。

```bash
# 完整指标复算（GPU 约 20 分钟 / CPU 约 2 小时）
.venv-retro/bin/python tools/eval_retro_benchmark.py --device cuda:0 --out /tmp/retro_check
diff <(python3 -c 'import json;print(json.load(open("/tmp/retro_check.json"))["stage2_reranker"])') \
     <(python3 -c 'import json;print(json.load(open("submission/goai_final/metrics/retro_benchmark.json"))["stage2_reranker"])')

# 核心流程复现：一行主题 → 综述 PDF（需 Codex CLI 登录、网络、TeX；数小时，token 量见 §5.3）
bash scripts/reproduce_core.sh                      # 默认正式主题，使用公开精简知识库
bash scripts/reproduce_core.sh --topic "LLZO 石榴石固态电解质的烧结致密化"
```

核心复现的判定标准不是逐字相同的 PDF（LLM 不可逐字复现），而是：`loopctl check-done` 退出 0；`CITATION_AUDIT.md` 中全部条目 PASS；`bib_guard` 整合率 ≥ 90%；产出 `main.pdf`、`references.bib`、`figures/{svg,drawio}`、逐子任务 JSONL 轨迹与 `tool_calls.jsonl`。

算力与成本：确定性组件仅需 CPU（前驱体预测单次查询秒级；全测试集 GPU 19 分钟）；LLM 调用量以正式运行为参考（§5.3）。

---

## 8. 已知限制

- 目标相 Ba5Y12Zn[O(SiO4)]8 公开文献仅 1 篇直接报道且无独立复现，报告如实以"近邻体系条件 + 模型候选前驱体 + 建议实验"呈现，未给出"已验证配方"。
- 公开知识库只覆盖 51 篇被引文献中的 21 篇全文；其余以 DOI 提供。
- 终审为同家族模型的冷启动复审；跨模型（如 Claude Code）审稿在本仓库支持但本次未启用。
- LLM 步骤不可逐字复现；复现以闸门与证据链一致为准。
- 正式 PDF 含专家反馈驱动的修订（§3 第 7 组），全部有轨迹留痕。

---

## 9. 打包与命名

```bash
bash scripts/package_submission.sh "<队伍名>"     # 生成两个 zip 到 dist/
# AI4R_MAT_<队伍名>_SAGE-Mat_非代码材料.zip : deck/ + report_docx/ + evidence/ + run/ + run_llzo/
# AI4R_MAT_<队伍名>_SAGE-Mat_代码材料.zip   : 仓库源码快照 + traces/ + metrics/ + scripts/
```

官方总览表将"研究数据与证据包 / 运行与评测包"同时列在两类下；本包按正文说明放入非代码材料，并在代码材料的 README 中给出相对路径与 SHA-256，评审可按任一口径检查。
