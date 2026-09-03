# 第13队 · 科学无极 · SAGE-Mat

**SAGE-Mat：面向无机材料发现与合成规划的证据约束自循环智能体**
SAGE-Mat: Evidence-Constrained Self-Cyclic Agent for Inorganic Material Discovery & Synthesis Planning

方向：材料科学 / MaterialsScience（TeamNo.13）
仓库：<https://github.com/asimfish/goai_research>；详细说明 `docs/competition/SUBMISSION.md`（代码包内位于 `01_系统复现包/goai_research/docs/competition/SUBMISSION.md`）。

本 README 只做索引。官方六项交付物对应目录如下。

---

## 非代码类（「非代码材料」压缩包）

| # | 官方交付物 | 目录 |
|---|---|---|
| 1 | 方案说明 PPT | `方案说明PPT/`（PPTX + PDF；可编辑 SVG 源与讲稿在 `source/`） |
| 1 | 复赛报告 | `复赛报告/`（官方模板 DOCX） |
| — | 研究数据与证据包（官方说明亦归入非代码类） | `研究数据与证据包/` |
| — | 运行与评测包（官方说明亦归入非代码类） | `运行与评测包/`（正式报告 PDF 在 `正式案例_BYZSO冷启动/最终输出/`） |

单独上传的 PPT 文件名：`AI4R_MAT_科学无极_SAGE-Mat_非代码材料_PPT.pptx`（及同名 `.pdf`）

---

## 代码类（「代码材料」压缩包）

| # | 官方交付物 | 目录 |
|---|---|---|
| 1 | 系统复现包 | `01_系统复现包/goai_research/`（可运行仓库：源代码、全部 Prompt、配置、依赖、模型）+ `01_系统复现包/构筑阶段轨迹/`（Codex 构筑阶段会话） |
| 2 | 研究数据与证据包 | `02_研究数据与证据包/` |
| 3 | 运行与评测包 | `03_运行与评测包/`（正式案例、LLZO 诊断轮、历史运行、09-03 补充案例、运行阶段轨迹） |
| 4 | 指标与分析代码 | `04_指标与分析代码/`（结果 + 指标脚本副本；脚本主副本在仓库 `tools/`） |
| 5 | README + 一键命令 | `05_README与一键命令/`（本文件、SUBMISSION.md、install.sh、scripts/） |

要点：

1. **系统复现包** — `01_系统复现包/goai_research/` 下 `server/`（检索 / 核验 / 绘图 / 逆合成 4 个 MCP server）、`skills/`（9 个 Agent 的全部 Prompt）、`AGENTS.md`、`configs/*.example`、`.env.example`、`pyproject.toml` + `uv.lock`、`vendor/two_stage_retro/`（两阶段前驱体预测模型 checkpoint + 最小推理代码 + 原料库）。Harness：Codex CLI 0.146.1；模型 `gpt-5.6-sol`；推理强度 `xhigh`。
2. **研究数据与证据包** — `references.bib`（51 条）、`papers.jsonl`（63 条候选）、`claim_evidence.jsonl`（100 条结论 → 219 次引用）、`CITATION_AUDIT.json`、`notes/`（引用支持库、合成条件原文定位）、`corpus_release/`（被引全文精简 Parquet 知识库；版权限制见 SUBMISSION.md §4）。
3. **运行与评测包** — `正式案例_BYZSO冷启动/`：`inputs/`（唯一输入）、`tasks/`（逐字提示词）、`ledger.json`、`tool_calls.jsonl`、`review_*`、`traces/runtime/`（40 个子任务与编排器的 JSONL 事件流，含失败/超时留痕）、`最终输出/`（23 页 PDF + LaTeX + bib + 图源）。`LLZO诊断轮/`、`BYZSO首轮_20260831/`、`补充案例_20260903/`、`运行阶段轨迹/` 同理。
4. **指标与分析代码** — 引用—证据链、Agent 轨迹统计、稿件闸门、前驱体模型 dry run；模型基准指标随 checkpoint 的评测汇总在仓库 `vendor/two_stage_retro/checkpoints/*_summary.json`。
5. **一键命令** — 在 `01_系统复现包/goai_research/` 下执行：

```bash
bash install.sh --retro
bash scripts/smoke_test.sh --with-retro     # 无网络、无 LLM，末行 SMOKE TEST PASSED
# bash scripts/reproduce_core.sh            # 核心复现，需 Codex 登录、网络、TeX
```

---

包根另有 `VERSION`（生成本包的 git commit）与 `MANIFEST.sha256`（包内每个文件的 SHA-256）。
