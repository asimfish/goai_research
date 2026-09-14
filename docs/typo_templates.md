# 排版模版对照（2026-09-13）

> **已定版（2026-09-14 更新）：默认 = `manuscript`。**
> 用户：“感觉现在的排版没有之前的这个好看呢：`pdf/bayznsio_phase_en_20260904.pdf`”。
> 把那份 2026-09-04 相图报告的排版逐条对照复刻成 `template=manuscript`，并设为两套 sty 的默认值。
>
> | 特征 | 那一版（参考） | 之前的 journal | 现在的 manuscript |
> |---|---|---|---|
> | 正文 | 11 pt / 13.6 pt | 10 pt / 12.5 pt | 11 pt / 13.6 pt |
> | 版心 | Letter margin 1 in = 6.5×9 in | 6.5×9 in | 同（中文 A4 margin 2.54 cm） |
> | 节标题 | 衬线粗体（Times） | 无衬线粗体 | 衬线粗体（中文仍用黑体） |
> | 标题栏 | 居中、不加粗、无横线 | 左对齐 + 1.2 pt 粗横线 | 居中、不加粗、无横线 |
> | 摘要 | 居中粗体 Abstract + 两侧缩进 small 块 | NeurIPS 式 | 同参考版 |
> | 段落 | 首行缩进、段间 0 | 缩进 1.0 em、段间 2 pt | 缩进 1.5 em（中文 2 字）、段间 0 |
> | 断行 | `emergencystretch`，**不开 `\sloppy`** | `\sloppy` | `emergencystretch=2em`、`tolerance=2000` |
> | 页眉 | 斜体短题 + 页码 + 0.3 pt 细线 | 无 | 同参考版 |
>
> **观感变差的主因是 `\sloppy`**：它把 tolerance 放到 9999、emergencystretch 给到 3em，词距被拉得很开，
> 整段的灰度不匀。microtype 其实一直开着，但被 `\sloppy` 抵消了。
>
> 用户此前明确要求的这些**保留不变**：表格浮到页底、PaperOrchestra 题注（标签后句点、首句不加粗）、
> 图宽 0.95 行宽、参考文献前 `\clearpage`、run-in 小标题的蓝色方块、编号标题只用数字。

> **（历史，2026-09-13）曾定为：journal 版心 + PaperOrchestra 题注/浮动体约定。**
> 用户：“那默认还是用 journal 的模版吧，先用 orchestra 的模式然后套 journal 的模型。”
> 两套样式文件的 `template` 默认值都改成了 `journal`，并且 `journal` 分支现在同时启用
> orchestra 的约定层：题注 `labelsep=period`、首句不加粗、图宽 `0.95\linewidth`、
> `\bibliography` 前 `\clearpage`。`\usepackage{goai_zh_typo}` 不带参数即为此版。
> 四份正式版重编结果：BYZSO 中 22 页 / 英 24 页，BaZn₂Si₂O₇ 中 7 页 / 英 7 页，全部 0 错误 0 Overfull。

用户要求“多试几种排版”，并点名 PaperOrchestra、NeurIPS、ICLR。现在两套样式文件都带模版开关：

```latex
\usepackage[template=neurips|iclr|orchestra|arxiv|springer|journal]{goai_en_typo}   % 英文
\usepackage[template=neurips|iclr|orchestra|arxiv|journal]{goai_zh_typo}            % 中文（无 springer）
```

## 六套模版的来源与特征
| 模版 | 来源 | 版心 | 标题/节标题 | 段落 | 题注 |
|---|---|---|---|---|---|
| `neurips` | `neurips_2023.sty` 官方值 | Letter 5.5×9 in | 上下横线 + 17 pt 粗体居中；节 12 pt 粗体 | 无缩进，段间 5.5 pt | 小号、粗体标签、首句加粗、悬挂 |
| `iclr` | `iclr2025_conference.sty`（ICLR/Master-Template） | 同上 | 标题/节标题/Abstract 小型大写 | 段间 0.5 pc | 同上 |
| `orchestra` | PaperOrchestra（Ar9av/PaperOrchestra，`skills/section-writing-agent/references/{latex-table-patterns,figure-integration}.md`） | 同 NeurIPS | 同 NeurIPS | 同 NeurIPS | **题注不加粗首句**、标签后用句点；图宽 0.95 行宽；参考文献前 `\clearpage`（防浮动体漂到 References 之后）；表注在上、图注在下；只用 booktabs 三线 |
| `arxiv` | arxiv.sty（G. Kour）的观感 | Letter 6.0×8.8 in | 左对齐标题 + 细横线；节标题黑体无衬线 | 首行缩进（中文 2 字） | 同 NeurIPS |
| `springer` | LNCS 类 | A4 12.2×19.3 cm | 居中标题；节标题粗体 | 首行缩进 | 小号、标签后句点 |
| `journal` | 单栏期刊（ACS/RSC 类） | Letter 6.5×9 in / 中文 A4 16 cm | 左对齐标题 + 粗横线；节标题黑体无衬线 | 首行缩进、行距 12.5 pt | 小号 |

## 同一份 BYZSO 内容的结果
| 模版 | 英文页数 | 中文页数 | 备注 |
|---|---|---|---|
| neurips | 26 | 25 | 0 错误 0 Overfull |
| iclr | 26 | 25 | 0 错误 0 Overfull |
| orchestra | 26 | 25 | 0 错误 0 Overfull |
| arxiv | 24 | 22 | 0 错误 0 Overfull；版心宽 0.5 in，表格列更松 |
| springer | 35 | —（未做） | 4 处 Overfull；12.2 cm 窄栏放不下宽表，表 1 被推到第 34 页 → **不建议** |
| journal | 23 | 21 | 0 错误 0 Overfull；最紧凑，宽版心让长表的列最舒展 |

对照册：`pdf/gallery/typo_gallery_20260913.pdf`（34 页，每套模版给出首页、图 1 页、表 1 页），单个版本在 `pdf/gallery/byzso_{en,cn}_<模版>.pdf`。



## 约定层怎么实现的
`template=` 只管版心 / 字号 / 标题，题注与浮动体规则拆成两个独立开关：

```latex
\newif\ifgoai@plaincap   % orchestra 的题注写法（标签后句点、整段同字重）
\newif\ifgoai@orchfloat  % 图宽 0.95 行宽 + 参考文献前 \clearpage
\ifgoai@orch    \goai@plaincaptrue \goai@orchfloattrue \fi
\ifgoai@journal \goai@plaincaptrue \goai@orchfloattrue \fi
```

章节源里的 `\caption{\textbf{首句。}其余}` **不动**（`neurips` 等版式仍要加粗首句），
改由 caption 的 format 在排版时把 `\textbf` 变成透明宏：

```latex
\DeclareCaptionFormat{goaiplain}{\begingroup\let\textbf\@firstofone#1#2#3\endgroup}
\captionsetup{format=goaiplain}
```

`\pretocmd{\bibliography}{\clearpage}` 必须放进 `\AtBeginDocument`：natbib 在导言区后半段会重定义
`\bibliography`，在它之前打的补丁会被覆盖（orchestra 之前那一版就是无效的）。

## 对照台（推荐用这个比）
`typo_deck_20260913.html` —— 单文件 HTML，11 张横向幻灯片，六套模版逐页并排：
总览 / 版心尺寸（纸张与文本块按同一比例）/ 首页 / 图页 / **图注特写** / **表格页** / **表头特写** /
条件矩阵 / 参考文献 / springer 的问题 / 建议。`←/→` 翻页，右上角切中英，点任意页面看整页原图。
图注与表头那两张是按 `pdftotext -bbox` 找到题注坐标后裁出的特写，能直接看清“加粗首句 + 冒号”与“整段同字重 + 句点”的差别。

77 张图已内嵌为 data URI（11.4 MB），下载后可离线打开；生成方式见 `tools/typo_deck/README.md`。

## 建议
- 这份报告的瓶颈是两张宽长表：版心越宽越好看。**journal（英 6.5 in / 中 A4 16 cm）或 arxiv（6.0 in）** 的表格观感最好，页数也最少。
- 若要投顶会或对齐会议观感，用 `neurips`；要小型大写的会议风用 `iclr`。
- `orchestra` 与 `neurips` 版心相同，差别在题注（不加粗首句、句点分隔）和图宽 0.95；若不喜欢加粗首句题注，选它。
- `springer` 不适合本报告（窄栏 + 宽表）。

## 构建
`build_v3.sh` 会编译每个目录下存在的目标：`main_typo3`（中文默认）、`main_zh_<模版>`、`main_en`、`main_en_<模版>`，各自 xelatex→bibtex→xelatex×2 并打印页数/错误/Overfull。
