# 第13队 · 科学无极 · SAGE-Mat

**SAGE-Mat：面向无机材料发现与合成规划的证据约束自循环智能体**
SAGE-Mat: Evidence-Constrained Self-Cyclic Agent for Inorganic Material Discovery & Synthesis Planning

GOAI 2026 · AI for Research 算法赛 · 材料科学（MaterialsScience）· TeamNo.13 · 进阶路线 C（合成路线与工艺设计）
开源实现名 GoAI Research（MIT）。一行研究主题进去，可核验的综述、证据链与候选合成路线出来。

评审入口：[`docs/competition/SUBMISSION.md`](docs/competition/SUBMISSION.md)（模型与 Harness 声明、全部运行记录与筛选规则、数据许可边界、指标复核、追溯链、复现判据）。

---

## 六项交付物在哪里

仓库根目录就是**系统复现包**；其余交付物在 `submission/` 下按官方名称分文件夹。

| # | 官方交付物 | 位置 |
|---|---|---|
| 非代码 1 | 方案说明 PPT | [`submission/方案说明PPT/`](submission/方案说明PPT/)（PPTX + PDF；可编辑 SVG 源与讲稿在 `source/`） |
| 非代码 1 | 复赛报告 | [`submission/复赛报告/`](submission/复赛报告/)（官方模板 DOCX；正文源 [`docs/competition/FINAL_REPORT.md`](docs/competition/FINAL_REPORT.md)） |
| 代码 1 | 系统复现包 | 源代码 [`server/`](server/)（4 个 MCP server）· 全部 Prompt [`skills/`](skills/) + [`AGENTS.md`](AGENTS.md) + [`docs/competition/TASK_PROMPT.md`](docs/competition/TASK_PROMPT.md) · 配置 [`configs/`](configs/) · [`.env.example`](.env.example) · 依赖 [`pyproject.toml`](pyproject.toml) / [`uv.lock`](uv.lock) · 预测模型 [`vendor/two_stage_retro/`](vendor/two_stage_retro/) · 构筑阶段 Agent 轨迹 [`submission/01_系统复现包/`](submission/01_系统复现包/) |
| 代码 2 | 研究数据与证据包 | [`submission/02_研究数据与证据包/`](submission/02_研究数据与证据包/)：文献清单与 DOI、`claim_evidence.jsonl`（100 条结论 → 219 次引用 → 51 个核验键）、逐条引用核验、被引全文精简知识库 |
| 代码 3 | 运行与评测包 | [`submission/03_运行与评测包/`](submission/03_运行与评测包/)：正式案例（输入、提示词、账本、MCP 审计、JSONL 轨迹、最终 PDF）、LLZO 诊断轮、历史运行、09-03 补充案例、运行阶段原生 Codex 会话 |
| 代码 4 | 指标与分析代码 | 代码在 [`tools/`](tools/)（`build_claim_evidence.py`、`analyze_agent_traces.py`、`bib_guard.py`、`tex_guard.py`、`academic_language_guard.py`、`retro_dry_run.py`）；结果与说明在 [`submission/04_指标与分析代码/`](submission/04_指标与分析代码/) |
| 代码 5 | README + 一键命令 | 本文件、[`install.sh`](install.sh)、[`scripts/smoke_test.sh`](scripts/smoke_test.sh)、[`scripts/reproduce_core.sh`](scripts/reproduce_core.sh)、[`scripts/package_submission.sh`](scripts/package_submission.sh) |

正式报告（23 页，纯主题冷启动 + 有记录的专家反馈修订）：
[`submission/03_运行与评测包/正式案例_BYZSO冷启动/最终输出/Ba5Y12Zn_合成调研_学术润色版.pdf`](submission/03_运行与评测包/正式案例_BYZSO冷启动/最终输出/Ba5Y12Zn_合成调研_学术润色版.pdf)

## 一键命令

```bash
bash install.sh --retro                    # .venv + 依赖 + MCP 配置；--retro 另装 torch/pymatgen
bash scripts/smoke_test.sh --with-retro    # 无网络、无 LLM，1–2 分钟，末行 SMOKE TEST PASSED
.venv/bin/python tools/retro_dry_run.py    # 前驱体模型 dry run：校验 checkpoint 并在 CPU 上预测
bash scripts/reproduce_core.sh             # 核心复现：一行主题 → 综述 PDF（需 Codex 登录、网络、TeX）
bash scripts/package_submission.sh "科学无极"   # 生成官方命名的两个 zip 到 dist/
```

## 声明摘要

- Harness：Codex CLI 0.146.1；模型 `gpt-5.6-sol`；推理强度 `xhigh`；构筑阶段与运行阶段轨迹分目录提交。
- 私有全文库（约 3.76 千万篇）不公开；公开包只含正式报告被引 51 篇中的 21 篇全文，其余以 DOI 提供，对复现的影响见 SUBMISSION.md §4。
- 8 组运行全部留痕，正式结果取最后一个通过全部机械闸门的版本，未在多次运行间挑选（SUBMISSION.md §3）。

## 系统与框架文档

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) 三层架构 · [`docs/LOOP_PROTOCOL.md`](docs/LOOP_PROTOCOL.md) 账本驱动回环协议 · [`docs/FAILURE_MODE_FIXES.md`](docs/FAILURE_MODE_FIXES.md) 失效模式与守卫
- [`docs/FRAMEWORK_CN.md`](docs/FRAMEWORK_CN.md) / [`docs/FRAMEWORK.md`](docs/FRAMEWORK.md) 开源框架使用指南（宿主接入、配置、测试、FAQ）
- [`docs/live-tests/`](docs/live-tests/) 实测报告 · [`docs/audits/`](docs/audits/) 需求验收审计

团队：高京（上海交通大学）· 吕丁阳（中国科学院大学）· 李雨峰（上海交通大学）
