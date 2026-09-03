# 第13队 · 科学无极 · SAGE-Mat

**SAGE-Mat：面向无机材料发现与合成规划的证据约束自循环智能体**  
SAGE-Mat: Evidence-Constrained Self-Cyclic Agent for Inorganic Material Discovery & Synthesis Planning

方向：材料科学 / MaterialsScience（TeamNo.13）  
详细说明：`docs/competition/SUBMISSION.md`（代码包在 `01_系统复现包/goai_research/` 下）

本 README 只做索引。官方六项交付物对应目录如下。

---

## 非代码类（打开「非代码材料」包）

| # | 官方交付物 | 目录 |
|---|---|---|
| 1 | 方案说明 PPT | `方案说明PPT/`（PPTX + PDF） |
| 1 | 复赛报告 | `复赛报告/`（官方模板 DOCX + PDF；正式案例综述在 `复赛报告/正式综述/`） |
| — | 研究数据与证据包（官方后文亦列入非代码） | `研究数据与证据包/` |
| — | 运行与评测包（官方后文亦列入非代码） | `运行与评测包/` |

单独上传的 PPT 文件名：`AI4R_MAT_科学无极_SAGE-Mat_非代码材料_PPT.pptx`

---

## 代码类（打开「代码材料」包）

| # | 官方交付物 | 目录 |
|---|---|---|
| 1 | 系统复现包 | `01_系统复现包/`（源代码、全部 Prompt、配置、依赖、模型版本、构筑阶段轨迹） |
| 2 | 研究数据与证据包 | `02_研究数据与证据包/` |
| 3 | 运行与评测包 | `03_运行与评测包/` |
| 4 | 指标与分析代码 | `04_指标与分析代码/` |
| 5 | README + 一键命令 | `05_README与一键命令/`（与本文件） |

各包要点：

1. **系统复现包** — 可运行仓库在 `01_系统复现包/goai_research/`：`server/`（检索 / 核验 / 绘图 / 逆合成）、`skills/`（9 个 Agent 的全部 Prompt）、`AGENTS.md`、`configs/*.example`、`.env.example`、`pyproject.toml` + `uv.lock`、`vendor/two_stage_retro/`。构筑阶段 Codex 轨迹在 `01_系统复现包/构筑阶段轨迹/`。Harness：Codex CLI 0.146.1；模型 `gpt-5.6-sol`；推理强度 `xhigh`。
2. **研究数据与证据包** — 文献清单与 DOI、`claim_evidence.jsonl`、引用核验、精简知识库（被引全文 Parquet；版权限制见 SUBMISSION.md §4）。
3. **运行与评测包** — 正式冷启动输入、中间产物、JSONL 日志、异常留痕、最终 PDF；运行阶段轨迹与构筑阶段分目录。次要案例与 09-03 补充运行一并放入。
4. **指标与分析代码** — 引用—证据链、轨迹统计、稿件闸门、前驱体模型 dry run；checkpoint 评测汇总在仓库 `vendor/two_stage_retro/checkpoints/`。
5. **一键命令** — 在系统复现包仓库根目录执行：

```bash
cd 01_系统复现包/goai_research
bash install.sh --retro
bash scripts/smoke_test.sh --with-retro
# bash scripts/reproduce_core.sh    # 核心复现，需 Codex 登录、网络、TeX
```

---

包根还有 `VERSION`（git commit）与 `MANIFEST.sha256`。
