# Sample Survey — COFs for Photocatalytic Hydrogen Evolution

**最新全流程实跑样例**（2026-08-28/29）：一条 prompt 进、26 页综述 PDF 出。
本目录是评审副本；工作区原件在 `workspace_live/full_run_20260828/`。
**注**：库内论文 PDF 原文因版权与体积不随附；两张图已按升级后的排版标准
（字号地板 4.5pt、主标默认加粗、组标签层级检查）重渲，工作区保留 run
当时的原件。

The latest end-to-end run of the GoAI pipeline: one prompt in, a 26-page
survey PDF out — with every citation verified and every figure still editable.

📄 **[paper/main.pdf](paper/main.pdf)** ← the deliverable

## Key numbers

| 指标 | 值 |
|------|-----|
| 文献库 | **143 篇**验证文献，五源检索 + snowballing，全部通过 ref_audit（零 UNVERIFIED/MISMATCH） |
| 综述正文 | **26 页** xelatex 编译 PDF，8 节 + 143 条参考文献（蓝色可点 DOI/URL） |
| 引用绑定 | bib 整合率 **100%**（零孤儿条目），密度 **51.2 次/千词**（闸门线 ≥8） |
| 图纸 | 2 张主图 × 四件套（figspec/SVG/drawio/PDF+PNG），全部通过排版 + 美学 lint（字号地板/溢出/遮挡 0 error；配色/对齐/尺寸/间距/连线 0 告警）。2026-09-02 按真实字宽折行重排：卡片加宽加高、列距与 waypoint 重算、边标签改窄，draw.io 导出与 SVG 逐行一致 |
| 风格库 | 30 篇经典综述蒸馏的写作与图纸风格卡（`style_bank`） |
| 预注册 idea | TpPa-1 mixed-linker D–A 掺杂路线：假设 → 匹配对照 → 量化闸门 G1–G4 → fallback（[idea_tppa1_route.md](idea_tppa1_route.md)） |
| 闸门 | 12 个全 PASS，账本带产物指纹（[ledger.json](ledger.json)）。注：该次运行早于「协议 gate 名 + 回执机械校验」上线，账本用的是当时 agent 自定的 gate 名（`ref_audit`/`review_round1` 等），review 回执为账本 detail 文字；现行 `loopctl check-done` 对这种账本会判缺必需 gate——这正是后来加严的原因 |

## What's here

| 文件 | 说明 |
|------|------|
| `paper/main.pdf` | 最终 26 页综述（Times 排版、蓝色引用、紧凑标题、运行页眉） |
| `paper/main.tex` + `sections/` + `references.bib` | LaTeX 源码，目录自含可复编译 |
| `paper/figures/*.pdf` `*.png` | 两张主图的排版件与预览件 |
| `paper/figures/src/` | 同一张图的 figspec（单一事实源）/ SVG / **.drawio**（draw.io 直接打开继续编辑） |
| `ledger.json` | 回环账本终态：12 闸门 PASS、issue 闭环、全过程 log |
| `ref_audit_corrections.md` + `ref_audit_per_entry.jsonl` | 143 条引用逐条核查记录（抽查对照用） |
| `idea_tppa1_route.md` | 预注册改进路线（假设/测量/闸门/fallback/safety 全结构） |
| `DELIVERABLES.md` | 交付物清单原件 |

## Figures stay editable

![fig1](paper/figures/fig1_factor_chain.png)

Open `paper/figures/src/fig1_factor_chain.drawio` in
[draw.io](https://app.diagrams.net) and keep editing — nodes drag, edges follow.
Typography is machine-checked: print-equivalent font floors (body ≥4.5pt),
bold-by-default node titles, shape-aware overflow, and occlusion checks all
pass with 0 errors before a figure is allowed to render.

## Rebuild the PDF

```bash
cd paper
xelatex -no-pdf main && bibtex main && xelatex -no-pdf main && xelatex main
```
