已完成 LLZO 制作质量返工，且仅修改排版/渲染：

- `main.tex`：明确 A4 版式，顶边距 22 mm。
- `render_groff_fallback.py`：移除 Ba–Y–Zn–Si–O 硬编码，改为通用 TeX 子集解析；支持源文件标题/摘要解析、规范编号、公式、网格表格、蓝色引用锚点和化学式清理。
- PDF：独立 Abstract 区块；章节显示 `1 Introduction`、`1.1 Scope...`；Equation 1/2 居中可读；Table 1/2 网格换行；References 编号和字体可读。
- TeX 编译器不可用，原因已写入 `revision_log.md`，使用可复现的 Chromium Unicode fallback。
- 已生成并同步：
  - [main.tex](<HOME>
  - [main.pdf](<HOME>
  - [main_formatted.pdf](<HOME>
  - [revision_log.md](<HOME>

验收结果：25 页 A4，顶端文本位置约 21.8 mm；逐页无空页；`pdfinfo`、`pdftotext`、`pdfimages`、`tex_guard`、`academic_language_guard` 通过；`bib_guard` 通过并保留原有 bibliography 警告；PDF 内含 378 个引用目的地。I21 已关闭，其他问题未关闭。