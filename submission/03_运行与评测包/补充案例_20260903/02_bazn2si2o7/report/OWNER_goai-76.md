# 排版/用语 v3 —— 由会话 goai-76 [c5cc50]（agent v1xcsr0…）负责，2026-09-12 19:3x

发现两个并行会话（同一对话的两次续接）都在做“中文排版 v3 + 用语润色”。为避免互相覆盖：

- goai-76 负责：goai_zh_typo.sty v3、tools/zh_table_merge.py（条件总表 → 一张横排 longtable）、tools/zh_terms_apply.py + templates/glossary_materials_zh.json（术语规范化）、tools/zh_qa.py（门禁）、两份报告的 sections_v3 润色（三个并行编辑，QA PASS）、docker 构建、部署为 pdf/*_cn_typo3_20260913.pdf、看板与文档更新。
- 工作目录：本机 /tmp/claude-0/-root-lyf-goai/fc788d38-0358-4f3a-839d-163ae1a21275/scratchpad/typeset/；5090 构建树改用 /data/liyufeng/goai_typeset_g76/（不再写 /data/liyufeng/goai_typeset/）。
- 进度：bzso v3 已构建（6 页，0 错误，0 Overfull）；byzso 00–03 节润色收尾中，随后 splice 长表、构建、审页、部署。
- 请另一会话不要再写 submission/…/最终输出/main_typo3.tex、sections_v3/ 与 …/02_bazn2si2o7/report/ 下的同名文件；图件工作（figure studio / S2 生成 / img2ppt）继续由该会话负责，排版这边完成后会在 progress.json 与 05_alab_twin.md 之外的 zh_typesetting_v3.md 记录结果。
- 如需协调，请在本文件追加一段并写明会话名。

## 更新 2026-09-13 03:40（goai-76）
- 为避免覆盖另一会话的 `main_typo3.tex` / `sections_v3/`，goai-76 的成品在仓库里改名为 `main_zh3.tex` + `sections_zh3/` + `main_zh3.pdf`（两份报告同名规则），部署为 `pdf/byzso_cn_typo3_20260913.pdf`、`pdf/bazn2si2o7_cn_typo3_20260913.pdf`，看板 progress.json 已加条目。
- 结果：BYZSO 19 页 / BaZn2Si2O7 6 页，0 错误 0 Overfull，zh_qa PASS。方法见 `goai_research/docs/zh_typesetting_v3.md`。
