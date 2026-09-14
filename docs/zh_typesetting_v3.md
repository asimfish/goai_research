# 中文综述排版与用语 v3（2026-09-13）

v2（`zh_typesetting_v2.md`）解决了字体、标点和标题层级；用户反馈 v2 仍然“表格丑、空白多、不紧凑、用词不专业”。v3 从三个层面处理：版式压缩、表格重构、术语与句法润色。super_translate 的可借鉴之处不是它的 ML/CS 语料，而是**术语表注入 + 全篇一致 + 保护区（公式/引用/结构）冻结 + 机器 QA** 这套流程；本轮把它移植为材料化学综述的工作流。

## 1. 版式（templates/goai_zh_typo.sty v3；v2 存档 goai_zh_typo_v2.sty）
| 项目 | v2 | v3 |
|---|---|---|
| 版心 | 左右 2.3 / 上下 2.6 cm | 左右 2.0 / 上下 2.3 cm |
| 行距 | 1.25 | 1.20（≈16.3 pt） |
| 节前/后空白 | 18/12/9 pt, 8/5/3 pt | 14/10/8 pt, 6/4/2 pt |
| 浮动体 | placeins[section] | 去掉按节 FloatBarrier（它让每个带图的节末留下半页空白）；textfloatsep 10 pt、floatsep/intextsep 8 pt；首页 `\suppressfloats[t]`，图不再排在标题之上 |
| 表格 | small、arraystretch 1.15、章节各自 tabcolsep | footnotesize、arraystretch 1.10、全局 tabcolsep 3 pt、colortbl 表头灰底（gray!12）+ 黑体 `\thead`、表内单倍行距、LTpre/LTpost 6 pt |
| 参考文献 | small、bibsep 3 pt、前置 `\clearpage` | footnotesize、bibsep 2 pt、紧接结论 |
| 标题块 | 18/26 pt | 17/24 pt，间距压缩 |

## 2. 条件总表（tools/zh_table_merge.py）
- v2 的六块 `table*`（每块上下两个 tabular，`\ContinuedFloat`）→ **一张横排 `longtable`**：`\newgeometry{1.5 cm}` + `landscape`，12 列 `P{}` 固定宽度（总宽 24.3 cm + 列距 = 26.4 cm < 26.7 cm），A/B/C 分区用整行黑体标题，`\endhead` 重复表头，“续下页”页脚。
- 单元格清理：`\texttt{NA}` → “—”，纯 NA 单元格整格记“—”，“均—”改“均未报道”；去掉 `\texttt{bibkey}`（保留 `\cite`）；`\shortstack` 展开；在数学模式之外的 `/`、`:` 后插入 `\allowbreak{}`，避免化学式串在窄列里溢出（v3 首次编译 12 处 Overfull 均来自这类串）。
- 其他小表：表头统一 `\rowcolor{gray!12}` + `\thead{}`；删除章节内的 `\arraystretch`、`\tabcolsep` 局部覆盖。
- `--splice <原 03.tex> <已润色 v3 03.tex>`：只重新生成 landscape 块并回填，不碰润色后的正文。

## 3. 术语与句法（templates/glossary_materials_zh.json，docs/zh_style_guide.md）
- 术语表分 crystal_growth / solid_state / phase_and_structure / characterization / review_method（英→中）和 `zh_normalize`（旧写法→规范写法）。`tools/zh_terms_apply.py` 以最长匹配在保护区（`$…$`、`\cite/\ref/\label/\includegraphics/\texttt/\url`、注释）之外替换：身份→归属、长晶→晶体生长、热史→热历史、谱系→系列、批量→块体、成相→相形成、温时→温度–时间、近邻→结构相关化合物/工艺参照体系、NA→未报道 等（BYZSO 正文 146 处 + 摘要 11 处）。
- 之后由三个并行编辑（按文件分工）做句法润色：陈述句、去翻译腔（把…作为…、所谓、回答了、拼接/拼出）、并列平行、缩写首次展开（HT-XRD、SCXRD、PXRD、CALPHAD）。硬约束：`\cite/\ref/\label`、数学、数字、单位、表格结构、事实与证据强度不得变动。
- 门禁 `tools/zh_qa.py <base> <edited>`：逐文件比较 cite 键多重集、数学片段、ref/label、数字、`&`/`\\` 计数，不一致即 FAIL。变更记录见各构建目录 `CHANGES*.md`。

## 4. 构建
同 v2：5090 docker `latex2pdf-latex-compile-server:latest`，`--user 1007:1007`，字体挂载到 `/usr/share/fonts/noto-cjk`，`xelatex → bibtex → xelatex → xelatex`（`build_v3.sh [dirs]`）。新增依赖：`xcolor[table]`（colortbl）、`pdflscape`、`longtable`、geometry `\newgeometry/\restoregeometry`。

## 5. 结果
| 报告 | v2 | v3 | 说明 |
|---|---|---|---|
| BYZSO 正式案例 | 24 页 | 19 页 | 0 错误、0 Overfull；表 2 横排 3 页；`pdf/byzso_cn_typo3_20260913.pdf` |
| BaZn2Si2O7 补充案例 | 8 页 | 6 页 | 0 错误、0 Overfull；`pdf/bazn2si2o7_cn_typo3_20260913.pdf` |

仓库内成品：`…/最终输出/main_zh3.tex + sections_zh3/ + main_zh3.pdf` 与 `…/02_bazn2si2o7/report/main_zh3.tex + sections_zh3/ + main_zh3.pdf`（`main_typo3.tex`/`sections_v3/` 是另一并行会话的在途文件，见 `OWNER_goai-76.md`）。5090 构建树：`/data/liyufeng/goai_typeset_g76/`。

## 6. 复现步骤
```
python3 tools/zh_table_merge.py <sections> <sections_v3>          # 表格重构 + NA/键清理 + 表头灰底
python3 tools/zh_terms_apply.py templates/glossary_materials_zh.json <sections_v3>   # 术语规范化
cp -r <sections_v3> <sections_v3_base>                            # 冻结基线
# 人工/编辑代理逐句润色 sections_v3（约束见 docs/zh_style_guide.md）
python3 tools/zh_qa.py <sections_v3_base> <sections_v3>           # 必须 QA PASS
python3 tools/zh_table_merge.py --splice <orig 03.tex> <sections_v3/03.tex>   # 表格参数调整后只回填长表
ssh 5090 'W=/data/liyufeng/goai_typeset_g76 bash /data/liyufeng/goai_typeset_g76/build_v3.sh'
```

## 7. v4：对齐 super_translate 的观感（2026-09-13）
用户看过 v3 后仍觉得 super_translate 的中文排版更好。读其引擎 `pdf_zh_translator/pdf_layout.py` 得到的可复用规则：
| super_translate | 值 | v4 对应 |
|---|---|---|
| 正文字体 | Songti SC Regular（Linux 回退 Noto Serif CJK SC） | Noto Serif CJK SC **Light**（字重对比页 fonttest.pdf：Light 的灰度最接近 Songti，ExtraLight 过淡，Regular 偏黑） |
| 粗体/标题 | Hiragino Sans GB W6（Linux 回退 Noto Sans CJK Bold） | Noto Sans CJK SC Bold |
| 行距 | `DEFAULT_LEADING = 1.5`（压缩回退 1.26 / 1.15；图注 1.18） | `\documentclass[zihao=5,linespread=1.5]{ctexart}`：10.5 pt / 15.75 pt |
| 两端对齐 | 单个间隙拉伸 ≤ 0.55 em 否则左齐 | xeCJK 有界 glue + `\emergencystretch` |
| 标点 | 全角，前后不加空；行首/行尾禁则表 | `PunctStyle=quanjiao`（禁则由 xeCJK 处理） |
| 中西文 | 一个 ASCII 空格（盘古之白） | `CJKecglue` 0.25 em |
| 拉丁字体 | 原文 Times | newtx（Times） |
| 段落 | 沿用原文（无缩进） | 保留中文期刊 2 字缩进 |
注意：`\ctexset{linespread=…}` 不是合法键（编译报错并忽略），行距必须作为文档类选项。表格内改回 Regular（`\tabCJK`），否则 7.5 pt 的 Light 太淡。结果：BYZSO 20 页、BaZn2Si2O7 6 页，0 错误 0 Overfull；部署 `pdf/byzso_cn_typo4_20260913.pdf`、`pdf/bazn2si2o7_cn_typo4_20260913.pdf`（v3 保留同名 typo3 文件）。sty v3 存档为 `goai_zh_typo_v3.sty`。

### 7.1 表格统一（用户反馈“宽度都不一致，要符合顶会要求”）
- 之前三张竖排表分别是固定厘米宽（14.9 / 13.9 cm）和 0.83–0.90 倍行宽，横排长表 27.4/27.7 cm；现在全部由 `tools/zh_table_width.py` 换算成 `P{\dimexpr r\textwidth-2\tabcolsep\relax}`（r 之和 = 1），每张表严格等于版心宽；横排长表用 `\linewidth`。
- 去掉表头灰底（`\rowcolor{gray!12}`），只保留三线表 + 黑体表头，与 NeurIPS/ICML 类模板一致；表 1 的 `\shortstack` 化学式改为自动换行（`\allowbreak`），行高不再忽高忽低；表内字号统一小五。
- 用词核对：编辑把原标题“活化与提拉”改成了“机械化学活化与提拉法生长”。“机械化学活化”（mechanochemical activation，Tzvetkov 2001 的球磨预活化）和“提拉法”（Czochralski 法的标准中文名）都是真实术语，但“提拉法生长”会让人以为目标相已被提拉法生长，而该节只是把 Y$_2$SiO$_5$ 的提拉法研究当作工艺参照；改为“机械化学预活化与提拉法工艺参照”，与表 2 的 C 区标题一致。

## 8. v5：NeurIPS 模版中文版（2026-09-13）
用户反馈“参考文献不符合顶会要求、中文里还是之前的蓝色，按 NeurIPS 模版来”。取 `neurips_2023.sty`（media.neurips.cc；2024/2025 路径 404）逐项移植到 `goai_zh_typo.sty` v5（v4 存档 `goai_zh_typo_v4.sty`）：
| 项目 | neurips_2023.sty | v5 |
|---|---|---|
| 纸张/版心 | letterpaper，textwidth 5.5 in，textheight 9 in，top 1 in，headsep 25 pt，footskip 30 pt | 同（作为 geometry 包选项，便于横排页 `\restoregeometry`） |
| 字体 | rmdefault ptm（Times），sfdefault phv | newtx Times + TeX Gyre Heros；中文思源宋 Light 正文、思源黑 Bold 粗体 |
| 字号 | 10/11，small 9/10，footnotesize 9/10，scriptsize 7/8，large 12/14，LARGE 17/20 | 同；正文行距由 `[10pt,linespread=1.5]` 给出（中文需要 1.5 倍） |
| 标题 | section `\large\bf\raggedright` −2.0ex/1.5ex；subsection/subsubsection `\normalsize\bf` −1.8ex/0.8ex、−1.5ex/0.5ex；paragraph run-in | `\ctexset` 同值（黑体由 BoldFont 映射） |
| 段落 | parindent 0，parskip 5.5 pt | 同（`autoindent=false`） |
| 标题栏 | 4 pt 横线 / LARGE bf 居中 / 1 pt 横线，作者粗体 tabular，首页 `\thispagestyle{empty}` | 同（去掉会议 notice 框） |
| 摘要 | `\large\bf Abstract` 居中 + quote | “摘要” + quote |
| 图表注 | 默认 `\@makecaption`：普通字号、冒号；图注下 7 pt、表注上 7 pt | caption 包 `labelsep=colon, font=normalsize, labelfont=normalfont`，表 `position=above` |
| 浮动 | 0.85 / 0.4 / 0.1 / 0.7 | 同 |
| 列表 | topsep 4 pt、itemsep 2 pt、leftmargin 3 pc | 同 |
| 脚注 | footnotesep 6.65 pt、脚注线 12 pc | 同 |
| 参考文献 | natbib，`\section*{References}`，`\small` | natbib numbers + sort&compress，`\bibfont` `\small`（行距 1.15），bibsep 3 pt |
| 链接 | 模版加载默认 hyperref（打印无色） | v5.2：按用户要求保留学术蓝（colorlinks，cite/link/url = RGB 0,84,159）；v5 首版误读为去蓝而用了 hidelinks |
| 断行 | `\sloppy`、flushbottom、widow/club 10000 | 同（不要再压低 tolerance：v5 首次编译因残留 `\tolerance=900` 出现 8.8 pt 溢出） |
| 页眉页脚 | 无页眉，页码居中 | 同（旧 `\runninghead` 变为空命令） |
结果：BYZSO 25 页（Letter）、BaZn2Si2O7 8 页，均 0 错误 0 Overfull；横排长表页边 0.8 cm、行高 1.0，仍为 3 页。`references.bib` 的 `author = {None Available}` 改为 `{{Materials Project}}`。部署 `pdf/*_cn_typo5_20260913.pdf`（v3/v4 文件保留）。

### 8.1 横排表与版心一致（用户：“表格怎么还是和其他部分宽度不一样”）
v5 首版的横排条件总表用 `\newgeometry{0.8 cm}` 自成版心，表宽 25.9 cm，与 5.5 in 的正文版心不是同一矩形。改为不改页边：`\begin{landscape}` 直接旋转 NeurIPS 版心（9 in × 5.5 in），表宽 = 版心高，页边与正文页相同（旋转后左右 1 in、上下 1.5 in），列宽按 `\linewidth` 比例缩放，化学式列由 2.4 加宽到 2.75（份额）以免 A1/B6 溢出。代价：每个横排页只能放 5.5 in 高的行，表 2 由 3 页变 4 页；BYZSO 共 26 页。`zh_table_merge.py` 不再输出 `\newgeometry/\restoregeometry`。

### 8.2 条件总表改竖排（用户：“第 11 页的表格还是横表，超出宽度了”）
旋转页在用户的阅读器里仍显示为横向、超出正文宽度，因此彻底放弃横排：`zh_table_merge.py` 现在生成两张竖排 `longtable`，均为 5.5 in 版心宽的比例列宽（`P{\dimexpr r\textwidth-2\tabcolsep\relax}`）：表 2（一）编号 / 来源与出处 / 目标产物式 / 原料配比前处理 / 合成方法 / 与目标相的关系（r = .06/.18/.18/.28/.14/.16），表 3（二）编号 / 温度–时间 / 气氛体系 / 坩埚与助熔剂 / 冷却生长 / 产物与表征 / 未记载项（r = .06/.16/.13/.16/.14/.18/.17），7.5/8.8 pt、列距 2.5 pt、行高 1.0，A/B/C 分区整行标题，续页重复表头。生成块用 `% >>> condition-matrix` … `% <<< condition-matrix` 标记，`--splice` 按标记回填；正文句子补上“表~\ref{tab:synthesis-conditions-b} 以相同编号承接…”。结果：BYZSO 24 页，表 2/3 共 4 个竖排页，0 Overfull。不再使用 pdflscape。

## 9. 并行多代理审查环（用户：“格式不对吧，表格的标题的提行、加粗等等，你好好调整下我们的并行多 agent loop 系统”）
流程见 `docs/zh_review_loop.md`，清单 `templates/zh_layout_checklist.md`，渲染 `tools/zh_render_pages.sh`。两轮结果：
- 第一轮 3 名审稿（64 条：P0 7 / P1 34 / P2 23）→ 修法归类：sty（raggedbottom、标题 boldmath、run-in 间距、arraystretch 1.3、题注 stretch 1.15、url[hyphens]+`\doi` 蓝链只在 / - 断行、bibsep 弹性、en dash 字符类）、生成脚本（分区行 `\\*`、8pt/3pt、needspace）、章节（`\ref` 后 `\CJKecglue{}`、`\paragraph` 统一、`\slash`、`\nobreakdash`、`\mathit{x}`、表头换行与列宽、图件按墨迹 bbox `trim`、bzso 表加 label+引用）、参考文献（`tools/bib_polish.py`：题名整词加括号、姓名/学位论文/数据集修正、Crossref 补卷期页 200 项、删除 ChemInform 重复条目）。
- 第二轮 3 名复审：BYZSO 1–13 页 7/10 已修，14–25 页 16/20 已修，BaZn2Si2O7 9/11 已修；余下项（table* 未挂钩→改 table、`$M$~=~Co`、`(M = Co)`/β/III 括号、Yıldırım 排序、表 4 列宽、术语脚本伪影“保温度–时间间/组相形成关”）在第三批修完；0 Overfull。
- 留给图件流程：三张 drawio 图内文字缩放后仅 ≈4 pt、图内标题与题注重复、Type 3 字体；参考文献个别条目仍缺卷页（Crossref 无记录）与在线/印刷年份差异。
- 教训：`\newgeometry` 与 `\restoregeometry`、`\flushbottom`、hyperref 链接末尾阻断 xeCJK 间距、glossary 最长匹配会命中词内子串（“保温时间”含“温时”）——术语表应加词边界或例外表。

## 10. v5.5：题注与字多的表（用户：“图注部分还是有点丑，表格也是，尤其 BYZSO 表格里字多的时候排版好丑”）
- 题注：caption 包 `format=hang`（说明文字悬挂在标签之后对齐），题注首句（到第一个句号）加粗作为标题，其余为说明；表题注在上、图题注在下不变。脚本 `restyle_tables.py` 的 `bold_title()` 自动加粗，续表题注不动。
- 表格：单元格一律左齐（`P` 列 `\raggedright`；试过两端对齐，窄列会把汉字撑开，更丑）；行间 `\addlinespace[3pt]`；列宽按各列单元格平均文字量（汉字计 2）的 0.75 次幂分配，并以最长不可断西文串（化学式、引用）给每列设下限，避免公式溢出；列数减少：表 1 由 7 列合并为 5 列（原文/本文化学式合并，结论与待研究合并为“结论：…；待研究：…”），条件总表（一）5 列（合成方法；关系：…），（二）5 列（温度--时间；冷却/生长：…｜气氛/体系；坩埚/助熔剂：…｜产物与表征｜未记载项）；长表前 `\Needspace{8\baselineskip}`（14 行会把整表推到下页留半页空白；`needspace` 小写版与 longtable 冲突会把续表头排在首题注之前）。
- 结果：BYZSO 25 页、BaZn2Si2O7 8 页，0 错误 0 Overfull；生成脚本 `tools/zh_table_merge.py` 与 `restyle_tables.py`（scratch，已随构建树保存）。

## 11. 模版与语言（用户：“中英文都提供一版吧，以及模版是不是只有 nips 的模版”）
- 现在有两套样式文件：`templates/goai_zh_typo.sty`（中文，ctexart）与 `templates/goai_en_typo.sty`（英文，article），共用同一套章节/表格/参考文献源（英文由 `sections_en/` 提供，翻译由 4 个并行代理完成并经 `zh_qa.py` 门禁：引用键、公式、交叉引用、表格结构与中文版逐一一致）。
- 模版选项 `\usepackage[template=neurips|iclr]{goai_*_typo}`：
  - `neurips`（默认）：neurips_2023.sty 的版心 5.5 in × 9 in、Times 10/11、粗体标题、4 pt/1 pt 标题横线、quote 摘要、段间 5.5 pt。
  - `iclr`：iclr2025_conference.sty（GitHub ICLR/Master-Template）——版心相同，标题/节标题/“Abstract” 小型大写，段间 0.5 pc，无页眉（会议模版的 “Published as a conference paper at ICLR 2025” 页眉不适用于报告）。中文版无小型大写，节标题仍为黑体，只改段间距。
  - 未做：ICML（双栏；本报告的两张长表与 longtable 在双栏下不可用，需改用 `\onecolumn` 附录）、ACS/RSC/Elsevier 期刊模版（achemso/elsarticle 需各自的 cls 与参考文献样式）。需要时再加。
- 英文版构建：`build_v3.sh` 对每个目录额外编译 `main_en.tex`、`main_en_iclr.tex`、`main_zh_iclr.tex`（存在即编译）。
