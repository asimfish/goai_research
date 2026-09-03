已完成 I1/I4 修复并配合 I2：

- 将三张 approved SVG 作为稳定的编号 `figure` 环境直接写入 [main.tex](<HOME>
  - `fig:roadmap`
  - `fig:taxonomy-overview`
  - `fig:phase-bottlenecks`
- 使用 DejaVu 字体注册的 Unicode Chromium fallback 重新生成 [main.pdf](<HOME>
- PDF：22 页、513 条引用、3 张图、3 张网格表；字体已嵌入。
- `pdftotext` 全文扫描结果：`■`、U+FFFD、`[t]`、`[Figure]`、`P0.`、伪影文本、`??`、裸 BibTeX key 均为 0。
- `bib_guard`、`tex_guard`、`academic_language_guard` 均通过；`references.bib` 未修改。
- 检查记录已写入 [revision_log.md](<HOME>
- 账本已记录 `draft_complete=PASS`，I1/I4 已关闭，`log done` 已完成；LaTeX 编译器不可用已在账本和 revision log 中注明。独立 `review_pass` 仍保留原有待复核状态，未进行自审。