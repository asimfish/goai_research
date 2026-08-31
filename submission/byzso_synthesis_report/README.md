# BYZSO synthesis research report

本目录是 Ba₅Y₁₂Zn[O(SiO₄)]₈（BYZSO）合成条件、近邻相证据与两阶段前驱体诊断的交付包。

## 文件

- `report.md`：中文学术型聚焦调研的可编辑源稿。
- `report.html`：自包含 CSS 的 A4 排版稿，章节标题和正文为黑色，链接为深蓝色。
- `BYZSO_Synthesis_Research_Report.pdf`：由 Google Chrome 以 A4、无页眉页脚方式渲染。
- `references.bib`：从工作区已通过 `ref_integrity` 的唯一引用池复制的 10 条 BibTeX。
- `MANUSCRIPT_VALIDATION.md`：引用键、链接、PDF 页数、字体嵌入和文本抽取验收记录。

## 结论边界

官方公开原文只证实 BYZSO 由开放体系中的高温溶液法获得。精确前驱体、实际投料比、flux、具体气氛和温程仍未知；铂坩埚仅为低置信度二次索引。报告不是实验 SOP，所有研究设计矩阵均为 `NOT FOR LAB USE`，须经人工材料化学与机构安全审批。

## 重新渲染

在仓库根目录执行：

```bash
google-chrome --headless --disable-gpu --no-sandbox \
  --disable-dev-shm-usage --disable-crash-reporter --disable-breakpad \
  --user-data-dir=/tmp/byzso_chrome_profile \
  --no-pdf-header-footer \
  --print-to-pdf="$PWD/submission/byzso_synthesis_report/BYZSO_Synthesis_Research_Report.pdf" \
  "file://$PWD/submission/byzso_synthesis_report/report.html"
```

验收命令及当前结果见 `MANUSCRIPT_VALIDATION.md`。
