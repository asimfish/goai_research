已完成 `goai-survey-writer` 返工，且仅修改排版、渲染和文字间距；未修改科学结论、实验建议、引用事实或 `references.bib`。

主要修复：

- 标题改为三行平衡断行，确保 `Ba–Y–Zn–Si–O Silicates` 与 `Metastability Bottlenecks` 不粘连、不在化学式中间断开。
- Data Sources and Literature Coverage 独立起页，513 条记录按科学主题分组；引用采用带空格的压缩区间，如 `[25, 28–30, 52, 53, 65, 76, 81, 82, 94–107]`。
- fallback parser 支持星号章节标题、`\clearpage`、显式标题断行、Unicode 化学式下标、期刊/出版物/DOI 元数据和统一作者 — 题名 — venue — 年份 — DOI 格式；隐藏冗余 URL。
- 图 3 的相图标签同步为 Unicode 下标，保持 SVG、Draw.io 与 figspec 文本一致。
- `main.pdf` 与 `main_formatted.pdf` 字节一致，均为 35 页。

产物：

- [main.tex](<HOME>
- [main.pdf](<HOME>
- [main_formatted.pdf](<HOME>
- [revision_log.md](<HOME>

验收结果：

- `bib_guard`: PASS，513/513 条目整合
- `tex_guard`: PASS
- `academic_language_guard`: PASS
- `pdfinfo`、`pdftotext`、`pdffonts`、`pdfimages -list`: 已运行
- 标题页、引用密集页、Data Sources 页面、图表页和 References 页面已逐页目检
- TeX 编译器不可用，已在 revision log 记录，使用 Unicode-capable Chromium fallback
- 已通过 `loopctl` 关闭 I8；其他问题未擅自关闭，当前无开放 blocker/major issue。