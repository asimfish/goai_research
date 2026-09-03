# 引用核查报告（定向语境修复 + 正文同步）

- 目标 bib：`/home/gaojing/goai_synthesis_runs/20260903_synthesis_topics/01_llzo/library/references.bib`
- 生成时间：`2026-09-03T09:08:23+08:00`
- 审计范围：保留既有 BibTeX 三轴核验结果；本轮只重扫正文引用并记录 I15/I17/I18 语境修复，未修改 `references.bib` 元数据。
- 机械正文扫描：10 个 section 文件，109 个 `\cite`/Markdown 引用命令，378 次引用，212 个正文唯一 key；未定义 key：0。
- Bib 整合：368 条目中 212 条被正文引用，整合率 57.6%；孤儿条目 **156**（严格 90% 下限下 `bib_guard` 为 `FAIL_ORPHAN_INTEGRATION`，这是既有 I14 范围，本轮不删库内背景条目）。
- 引用密度：55.47 次/千词（正文词数 6814）。

## 终审问题处理

- **I15**：`wang2025computational` 的 `verify_entry` 为 PASS，但权威标题明确是 LLTO。该键仍保留在 `references.bib`，且仅在 `02_background.tex:20` 作为“LLTO comparator, not LLZO evidence”；已从 `06_transport_measurement.tex` 的 LLZO 输运证据链移除。
- **I17**：`anon2025decision` 的 `verify_entry` 为 PASS，但条目是编辑决定信而非实验报告。该键仍保留在 `references.bib`，当前正文引用次数为 0；已删除 `07_interfaces_integration.tex` 中将其称为 scalable-cathode report 的论据，并改为不依赖该来源的测量规范表述。
- **I18**：本报告与当前正文同步：212 个唯一 key、378 次引用、156 个孤儿；`wang2025computational` 未被错误地声称为“全稿已移除”，`anon2025decision` 也未被声称为删除出库。

## 当前正文引用摘要

- 前 12 个按字典序的正文 key：`abakumov2020solid, ahmad2015concentration, ahmad2025reducing, ali2021spray, alizadeh2023synthesis, aman2026susceptor, anderson2024comprehensive, aono1993the, aote2023enhancement, aote2024effect, aote2024investigation, aote2025impact`
- 孤儿示例（完整列表见 JSON `manuscript_check.orphan_keys`）：`2013sb, abdalla2020communications, abrahams1971rutile, ahmad2016lithium, angelis2022chc, anon1969structure, anon2024industrial, anon2024review, anon2024reviewx, anon2024reviewx_review1, anon2025decision, anon2026test, asta1993theoretical, bachmann2022ecg, balaish2021processing, baumgartner2026unlocking, bell2021monoclinic, bernstein2012origin, besiii2026measurement, besiii2026precise`
- 所有正文 key 均存在于 `references.bib`；不存在未定义引用。

## 定向核验

| key | verify_entry | 正文处置 |
|---|---|---|
| `wang2025computational` | PASS；LLTO | 保留库内；仅作 LLTO comparator，移除第 6 节 LLZO 证据用法 |
| `anon2025decision` | PASS；editorial decision letter | 保留库内；删除第 7 节证据论断，正文当前不引用 |
| `kulkarni2025machine` | PASS；cubic LLZO transport | 保留为 LLZO 输运证据 |

`CITATION_AUDIT.json` 中的 `per_entry` 逐条保留既有核验裁决，并新增 `manuscript_citation_count` 与 `cited_in_current_manuscript` 字段以便复核。
