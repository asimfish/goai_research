# 修订记录

- 初稿：按 taxonomy.md 七节蓝图完成中文 LaTeX 章节，所有事实性陈述绑定核查后的文献键。
- 图纸：无生图通道，采用 figspec 直渲；消除边标签重叠和字号警告，保留两主题色加一强调色的配色提示并记录理由。
- 引用：删除未被正文使用的噪声条目，整合率提升至 100%；BibTeX DOI/化学式保护为非阻塞卫生告警，保留原始元数据以便审计。
- 语言：`academic_language_guard.py` PASS；将“结构类似物”表述限制为待验证候选，避免把近邻证据写成同构事实。
- 编译：本环境无 XeLaTeX/Draw.io CLI，使用同源 SVG 和 HTML→PDF 生成可视化 PDF；LaTeX 源码仍按中文模板交付。

## 2026-09-13 排版/用语 v3（main_zh3.tex + sections_zh3/，PDF main_zh3.pdf，6 页）
- 同 BYZSO v3 的 `goai_zh_typo.sty` v3；术语表注入 + 逐句润色（替位→取代、近邻/同型→结构相关化合物/同构、高温衍射→高温 X 射线衍射（HT-XRD）首次展开、膨胀测量→热膨胀测量、玻璃—陶瓷→微晶玻璃、粘度→黏度；记录见 `sections_zh3/CHANGES.md`），摘要同步润色；`zh_qa.py` PASS；8→6 页、0 Overfull；首页图不再排在标题之上。部署：`pdf/bazn2si2o7_cn_typo3_20260913.pdf`。

## 2026-09-13 排版 v4（main_zh3.tex 同源，仅换样式层 goai_zh_typo.sty v4）
- 对齐 super_translate 的中文观感：正文 Noto Serif CJK SC Light（≈Songti SC 灰度）、标题/粗体 Noto Sans CJK SC Bold（≈Hiragino Sans GB W6）、五号 10.5 pt、行距 1.5×字号（15.75 pt）、表内 Regular 字重；内容、术语与引用与 v3 完全相同。v3 的 PDF 保留为 `main_zh3_v3.pdf`。部署：`pdf/*_cn_typo4_20260913.pdf`。
- 2026-09-13 v4.1：所有竖排表改为严格等于版心宽（`tools/zh_table_width.py`，列宽为 `\textwidth` 的比例），去掉表头灰底，只留三线表与黑体表头；表 1 的 `\shortstack` 化学式改为自动换行。BYZSO 第 7.3 节标题由编辑改写的“机械化学活化与提拉法生长”改回准确表述“机械化学预活化与提拉法工艺参照”（该节只引用 Y2SiO5 的提拉法研究作工艺参照，目标相无提拉法生长证据）。

## 2026-09-13 排版 v5（NeurIPS 版式；main_zh3.tex 同源，样式层 goai_zh_typo.sty v5）
- 按 neurips_2023.sty 逐项移植：Letter 纸、版心 5.5 in × 9 in、上边距 1 in、页码居中页脚、首页无页码；正文 10 pt（Times + 思源宋 Light，行距 1.5 倍）、small/footnotesize 9 pt、large 12 pt、LARGE 17 pt；一级标题 12 pt 粗体左齐（前 2.0 ex 后 1.5 ex），二/三级 10 pt 粗体；无首行缩进、段间 5.5 pt；标题栏上下横线（4 pt / 1 pt）+ LARGE 粗体 + 粗体作者；摘要 12 pt 粗体居中 + quote 缩进；图注在下、表注在上，7 pt 间距，普通字号，冒号分隔；浮动比例 0.85/0.4/0.1/0.7；参考文献 \small、natbib 数字编号、`\section*`；超链接 hidelinks（不再有蓝色）；断行 \sloppy。
- 参考文献：修正 references.bib 中 `author = {None Available}`（Materials Project 数据条目）。v4 的 PDF 保留为 `main_zh3_v4.pdf`。部署：`pdf/*_cn_typo5_20260913.pdf`。

- 2026-09-13 v5.4：并行多代理版式审查环两轮（见 goai_research/docs/zh_review_loop.md）：表题注/表头/分区行/列宽、图件裁边、`\ref` 间距、run-in 标题、变量斜体、参考文献（bib_polish.py：括号保护大小写、Crossref 补卷期页、姓名/条目类型修正、去重）。PDF 同址更新。

- 2026-09-13 英文版：`main_en.tex + sections_en/`（由 sections_zh3 经并行翻译代理译出，zh_qa 门禁一致，美式拼写），样式 `goai_en_typo.sty`（NeurIPS 移植；`template=iclr` 为 ICLR 2025 变体 `main_en_iclr.tex`）；中文 ICLR 变体 `main_zh_iclr.tex`。部署 `pdf/*_en_typo5_20260913.pdf`、`pdf/*_en_iclr_20260913.pdf`。

- 2026-09-13 中英两条线：英文 `main_en.tex + sections_en/` 由母语级改写代理重写（非逐句翻译，zh_qa 门禁保证事实/引用/表格一致）；五张图改由 `tools/figspec2tikz.py` 从 figspec 直出 TikZ，中英各一版（`figures/pdf_tikz/*_{zh,en}.pdf`，源码 `figures/tikz/`，英文标签 `figures/figspec/*.labels_en.json`），图内文字 5.2–8 pt、无 trim、公式不断行。ICLR 变体 `main_en_iclr.tex` / `main_zh_iclr.tex`。方法见 `goai_research/docs/en_edition.md`。
