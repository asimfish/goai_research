完成独立只读复核。

结论：`review_pass = PASS`（provisional，同模型冷启动），0 blocker、0 major、1 minor（I9）。

- `main.pdf` 与 `main_formatted.pdf` 均为 35 页且字节一致；标题空格/断行、513 条文献分组、蓝色可点击引用、图表、页边距和 PDF 清洁扫描均通过。
- `tex_guard`、`academic_language_guard`、`bib_guard` 均 PASS；513/513 引用整合，10 条引用事实抽查均 `verify_entry PASS`。
- 已使用 `pdfinfo`、`pdftotext`、`pdffonts`、`pdfimages`、`pdftoppm`，并检查标题页、图页、引用密集页、Data Sources 页及多页 References。
- 未修改正文、`references.bib` 或图件；现有 I8 及其他历史 issue 未关闭或改动。
- 新增 minor I9：少数参考文献元数据仍有化学式大小写/下标不统一（不影响可读性、引用事实或科学结论）。

产物：

- [review_round_format.md](<HOME>
- [format_byzso.md](<HOME>

账本已刷新：`draft_complete PASS`（inputs 为当前 `main.tex`、`main.pdf`），`review_pass PASS`（含 `model=` 与真实 `trace=` 回执），`loopctl check-done` 返回 DONE。