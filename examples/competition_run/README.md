# Competition Run — 产物索引（COFs for Photocatalytic HER / Route C: TpPa-1）

GoAI Research 多智能体系统全流程实跑交付物（2026-08-27，round 1/4 一轮收敛，
`check-done` 退出码 0）。工作区原件在 `workspace_live/competition/`；本目录为评审副本。
**注**：库内论文 PDF 原文（`library/pdfs/`）因版权与体积不随附。

## 关键数字一览

| 指标 | 值 |
|------|-----|
| 文献库 | 37 篇，多源检索（arXiv+OpenAlex 必查 + Crossref 补检），DOI 零重复 |
| 引用核查 | 37/37 PASS，零 UNVERIFIED/MISMATCH（组委会抽查口径的自证材料） |
| 综述正文 | 3764 词（表/图外），14 页编译 PDF，7 节 |
| 引用绑定 | 167 次 `\cite`，37 key 整合率 100%，密度 32.2 次/千词（线 ≥8） |
| Research Gap | 6 条（要求 ≥5），每条 ≥2 key + 数据库标注 + 未覆盖推理 |
| Route C | 5 路线决策表 + 2 条量化优化 + 热力学审计 + T1–T4 待算清单 + 全步骤 safety |
| 审稿 | 2 轮：R1 开出 5 issue（2 major/3 minor）全部返工闭环；R2 三视角复验放行（provisional）|
| 闸门 | 9 个全 PASS（含 1 次指纹 stale 被 check-done 抓到后复审重记） |

## 文件 → 评分项映射

### 基本任务：文献调研报告（50%）

| 文件 | 对应评分项 | 要点 |
|------|-----------|------|
| `paper/main.pdf` | 交付格式（LaTeX 真实编译 PDF） | 14 页，0 编译警告/0 未解析引用 |
| `paper/main.tex` + `paper/sections/` + `paper/references.bib` + `paper/figures/` | 交付格式（源码齐全可复编译） | 目录自含：`pdflatex → bibtex → pdflatex ×2` 即可复现 |
| `paper/sections/02–04_*.tex` | 文献覆盖针对性 + 知识抽取结构化 | 按 5 级因子链分类组织，每叶 ≥3 支撑；两张可溯源对比表 |
| `research_gaps.md` + `paper/sections/06_open_challenges.tex` | Research Gap 识别质量 | 6 条 gap：证据链（≥2 key）+ 数据库（OpenAlex/Crossref）+ 「为什么没覆盖」推理；正文同步 |
| `CITATION_AUDIT.md` / `.json` | 证据链与引用完整性（红线） | 全库 37 条权威核查记录，供组委会抽查对照 |
| `paper/figures/` | 图纸双格式 | fig1 因子链主图 + fig2 TpPa-1 路线图；工作区另有 SVG/.drawio 可编辑源 |

### 进阶路线 C：合成路线与工艺设计（50%）

| 文件 | 对应评分项 | 要点 |
|------|-----------|------|
| `route_c_synthesis_plan.md` | 合成路线生成 | 单体制备/来源 → 缩合 → 后处理，每步条件挂库内 key；retro stub 仅集成演示且显式标注 |
| `route_c_synthesis_plan.md` §3 | 工艺优化（≥2 条量化） | O1 微波：72h→1h、120→100 °C、BET 152→725 m²/g（~4.8×）；O2 绿溶剂流动：30× STY、−89% 比能耗、BET 418 m²/g |
| `route_c_synthesis_plan.md` §4 | 热力学可行性检验 | 文献支持 4 条（可逆亚胺+不可逆酮式锁等）+ T1–T4 待计算清单（DFT 泛函/软件建议），零编造数值 |
| `route_c_synthesis_plan.md` §1 | 推理过程展示 | 5 路线候选对比表 + 选择/排除理由（决策记录） |
| `route_c_synthesis_plan.md` §5 + `experiment_route_c_tppa1.json` | 对抗审核（safety 强制） | 全步骤+优化+H₂ 测试 hazard 表；机器可读实验方案含逐步 safety 字段 |
| `proposal_route_c_tppa1.md` | 缺口→提案链路 | 动机挂 G4 缺口证据；新颖性边界显式声明 |
| `review_log.md` | 对抗审核留痕 | ideas 四维审 2 轮（R1 抓到 1 major CO₂ 基线缺失）+ 引用二审记录 |

### 过程可审计（两部分共用）

| 文件 | 说明 |
|------|------|
| `ledger.json` | 回环账本终态：9 闸门（带产物 sha256 指纹与审稿回执）、5+4 条 issue 全闭环、34 条过程 log（含失败留痕：S2 429、snowball 全空、bank_check 默认线 FAIL、lit_coverage stale） |
| `review/review_round1.md` | R1 审稿报告：0 blocker/2 major/3 minor，claim-cite 抽查 10 条表 |
| `review/review_round2.md` | R2 审稿报告：返工产物级复验 + 终审三视角，provisional 放行 |
| `review/round1_1.md`, `review/round2_1.md` | 审稿原始 trace（独立性声明 + 抽查记录 + 回执） |
| `SYSTEM_NOTE.md` | 系统架构 + 各环节方法论 + 复现步骤 + 诚实声明（代行确认/降级审稿/stub 演示） |

## 复编译

```bash
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```
