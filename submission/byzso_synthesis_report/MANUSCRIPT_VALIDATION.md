# BYZSO 文稿验收记录

**状态：PASS**<br>
**验收日期：** 2026-08-31<br>
**交付 PDF SHA-256：** `1a6c1dca11f423a3cefaa4e74c27186f56a497aa5b465ff5c75b81f2f161e108`

## 1. 引用与参考文献

- `tools/bib_guard.py report.md references.bib`：PASS。
- 文稿引用调用 30 次，去重引用键 10 个；BibTeX 共 10 条，整合率 100%。
- 引用密度 15.0 次/千词。
- HTML 中有 30 个正文内部引用、10 个参考文献锚点、10 个 DOI 外链和 1 个明确标注为低置信度的 ResearchGate 二次索引链接。
- PDF 中有 43 个链接注释：30 个命名内部跳转和 13 个 URI 注释，对应 11 个唯一外部 URL。
- `references.bib` SHA-256：`ecb76a8192d58494ce7daca146e498f6337759078381ab98075b04b6bfd91ece`。

## 2. 版式与 PDF

- Google Chrome 142 宿主层无页眉页脚渲染。
- 9 页，A4（594.96 × 841.92 pt）；Tagged PDF；`Suspects: no`。
- `pdffonts` 检查 297 个字体子集/资源，未嵌入数为 0。Chrome 将 CJK 字形子集化为 Type 3 资源，DejaVu Sans 也已嵌入。
- CSS 显式设置正文为 `#111111`，所有章节标题为 `#000000`；仅链接使用深蓝色。
- 表格行使用 `break-inside: avoid`，视觉抽检页 1、2、3、9 无裁切、方框字形、Markdown 符号泄漏或参考文献超链接错位。

## 3. 文本与证据边界

- `pdftotext -layout` 成功抽取 284 行、27,207 字节；9 页均有非空文本。
- 未发现未渲染的 `**`、`[@citekey]`、过期 `MISSING_AFTER_ONE_WAIT_AND_RECHECK` 或“等待并重查后仍不存在”。
- 所有 1280/1300/1500/1800 °C 数字均与具体近邻相、引用和不可迁移说明绑定，未组合成 BYZSO 配方。
- 精确 BYZSO 公开证据仍仅支持“开放体系中的高温溶液法”；精确前驱体、flux 与温程保持 UNKNOWN。
- 模型 Rank 1 仅保留候选，Rank 2–5 淘汰仅归档；所有路线仍为 `chemical_route_verified=false / NOT FOR LAB USE`。

## 4. 文件指纹

- `report.md`：`cd1b0bc2d33e901ca4e2a85ea09e918b4652ac52a7c79d0a367faddcee288261`
- `report.html`：`048adae9b536ce1df8d3d91eb2a483628a69bf04d59cd3fe3ca17d58c187ad17`
- `references.bib`：`ecb76a8192d58494ce7daca146e498f6337759078381ab98075b04b6bfd91ece`
- `BYZSO_Synthesis_Research_Report.pdf`：`1a6c1dca11f423a3cefaa4e74c27186f56a497aa5b465ff5c75b81f2f161e108`
