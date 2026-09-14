# 英文版是独立的一条线（2026-09-13）

用户要求：“不能直接翻译吧，我们的中英文应该是两条线，翻译的我理解表达不会那么 native，以及排版可能也有区别，比如这个英文版本的好多图都显示不全，以及图还是中文的。”

## 1. 两条线的边界
| 层 | 中文线 | 英文线 | 是否共用 |
|---|---|---|---|
| 事实/证据 | `sections_zh3/` | `sections_en/` | 共用同一批事实：`tools/zh_qa.py` 逐文件核对引用键、公式、交叉引用、数字、表格结构 |
| 文字 | 中文润色版 | **母语级改写**（不是逐句翻译）：句式重组、主动语态、去中文修辞脚手架、美式拼写、术语按英文惯用搭配 | 否 |
| 图件 | `figures/pdf_tikz/*_zh.pdf` | `figures/pdf_tikz/*_en.pdf` | 否（同一 figspec，两套标签） |
| 版式 | `goai_zh_typo.sty` | `goai_en_typo.sty` | 否（同为 NeurIPS 值；中文另加 xeCJK 字体、行距 1.5、全角标点） |
| 参考文献 | 同一 `references.bib` | 同一 | 是 |

英文正文由 4 个改写代理分节完成（00–02 / 03 表格 / 04–08 / BaZn2Si2O7），约束：`\cite`、公式、`\ref/\label`、表格结构不得变动；`zh_qa.py` 必须通过（唯一允许的差异是“方向一/二/三/四 → Direction 1/2/3/4”这类中文数词变数字，以及图件的语言后缀）。

## 2. 图件：从 drawio 导出改为 TikZ 直出
原来的图是 drawio 导出的 PDF：画布 1500×900 px 缩到 5.5 in 后图内文字只有 ≈4 pt，且导出框有大片空白（靠 `trim` 硬裁，裁多了就“显示不全”），标签还全是中文。

现在用 `tools/figspec2tikz.py` 从 `figures/figspec/*.json`（节点/连线/文本的绝对坐标）直接生成 TikZ：
- 画布按 5.5 in 版心换算（1500 px → 0.265 pt/px），**边界框由内容决定**，不需要 `trim`；
- 字号自动适配：按框宽估算行数，逐步缩到正好放下（下限 5.2 pt），题字 8 pt 左右、说明 6–7 pt；
- 化学式、元素链、缩写不断行：框宽不够时让框自己变宽（`widest_token`）；
- 连线标签放在两框之间的空隙里，带白色底衬；空隙放不下就省略该标签（内容在题注里）；
- `--lang zh|en --labels <labels_en.json>`：英文标签写在 `figures/figspec/<图>.labels_en.json`（与 spec 同名），由代理按每个框的字符预算撰写（预算 = 框宽/字号换算，见 `figs/labels_budget.json` 的生成方式）。

产物：`figures/pdf_tikz/<图>_{zh,en}.pdf`，源码 `figures/tikz/<图>_{zh,en}.tex`。章节里用 `\includegraphics[width=\textwidth]{../figures/pdf_tikz/<图>_<lang>.pdf}`，不再有 `trim/clip`。

## 3. 构建
`build_v3.sh` 在每个报告目录依次编译存在的目标：`main_typo3`（中文）、`main_zh_iclr`、`main_en`、`main_en_iclr`，各自 xelatex→bibtex→xelatex×2，并打印页数/错误/Overfull。

## 4. 结果（2026-09-13）
| 版本 | 页数 | 链接 |
|---|---|---|
| BYZSO 中文 | 25 | `pdf/byzso_cn_typo5_20260913.pdf` |
| BYZSO 英文 | 26 | `pdf/byzso_en_typo5_20260913.pdf` |
| BYZSO 英文 ICLR | 26 | `pdf/byzso_en_iclr_20260913.pdf` |
| BYZSO 中文 ICLR | 25 | `pdf/byzso_cn_iclr_20260913.pdf` |
| BaZn2Si2O7 中文 | 8 | `pdf/bazn2si2o7_cn_typo5_20260913.pdf` |
| BaZn2Si2O7 英文 | 7 | `pdf/bazn2si2o7_en_typo5_20260913.pdf` |
| BaZn2Si2O7 英文 ICLR | 8 | `pdf/bazn2si2o7_en_iclr_20260913.pdf` |
全部 0 编译错误、0 Overfull。

## 5. 待确认
- 英文图标签为放进原框宽做过压缩，个别说明只保留了一个概念（BaZn2Si2O7 路线图的 n2/n3/n6）。如果希望英文图重新排版（放大框、换行布局），需要给英文单独做一套 figspec。
- 改写代理标注的存疑术语见各代理报告：measured stoichiometry、analogs、Transferability Limits、phase assemblage、"not reported" 与摘要层面证据的措辞。
