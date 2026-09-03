# 阶段五组装与精修日志

> 范围：只记录组装、清晰度、重复、表格排版与浮动体修改；不改变证据强度，不删除 limitation，不修改 `workspace/library/references.bib`。

## 首次组装

- 以 `templates/survey_main.tex` 为底稿创建 `workspace/drafts/main.tex`，保留 amsmath→newtxtext→newtxmath、学术蓝链接、caption、`P{}` 列型、`arraystretch=1.18`、titlesec、fancyhdr 与参考文献前 `\clearpage` 等模板规范。
- 为 XeTeX 增加 `fontspec`、`xeCJK` 与 Noto Serif/Sans/Mono CJK SC 字体配置；正文仍采用模板的 Times/newtx 拉丁与数学字体系。
- 替换标题、匿名作者、摘要和短页眉；主标题手工均衡断为两行，并按蓝图顺序 `\input` 7 节。
- 参考文献沿用只读 `workspace/library/references.bib`，主稿通过相对路径 `../library/references` 调用，未复制或改写 BibTeX 条目。

## 图形转换

- 使用 Chrome HTML wrapper 按 SVG 原始画布尺寸导出 PDF：图 1 为 1500×900 px（1125.12×675.12 pt），图 2 为 1500×835 px（1125.12×625.92 pt）；两者均为单页、无额外页边空白。
- 将两份 PDF 以 72 dpi 回栅格检查：图面覆盖完整页面，标题、节点、边标和底部边界徽章均可见，无裁字或外围纸张留白；源 SVG 与 drawio 未改动。
- 章节继续使用 `../figures/pdf/fig01_evidence_synthesis_map.pdf` 与 `../figures/pdf/fig02_route_variable_matrix.pdf`，确保从 `workspace/drafts/main.tex` 编译时路径可解析。

## 首轮闸门与编译

- 首次 `bib_guard`：7 个章节、195 次引用调用、52 个去重 key / 52 条 BibTeX，整合率 100%，引用密度 40.2 次/千词，PASS。
- 首次 `tex_guard`：8 个 TeX 文件、8 个标签、6 个交叉引用，无 TODO、缺失输入/图、悬空引用或环境闭合错误，PASS。
- Tectonic 首次联网拉取官方 bundle 后在 XeTeX 字体初始化阶段阻塞：fontconfig 可匹配的 `Noto Sans Mono CJK SC` 不是 fontspec 可直接定位的字族。已保留 `build/initial_main.log`。正文等宽环境只承载 `NA`、key 等拉丁字段标记，故删除不必要的 CJK mono 映射；中文正文继续由 Noto Serif CJK SC 承载。
- 正文只引入预转换 PDF，故移除未使用且会触发 shell-escape/transparent 告警的 `svg` 包；模板的图形能力由 `graphicx` 保持。该修改只清理编译依赖，不改变图面或内容。

## 清晰度与版式精修

- 将表 A 由独立浮动页 `[p]` 改为 `[!b]`，使其与前文共页；将仍需单独排版的长表浮动页改为顶端对齐，避免表格垂直居中造成的大片页首空白。
- 仅做排版性断行：对相鉴定表、A1、B1/B2 以及 C5/C6、C9、C17 的长化学式或方法字段增加可换行点；调整 C7--C11 表的首列列宽。未改动化学式、条件、引用或结论。
- 最终 `main.log` 中 `Overfull/Underfull box`、缺字、未定义交叉引用与未处理浮动体均为 0；所有 limitation 文字保留。

## 本次唯一重试：XDV→PDF 诊断与修复

- 对已关闭历史 run `20260901_005958_1409371` 作有界检查，并用正式命令 `/tmp/goai_tectonic_0_17_0/tectonic -X compile -C --keep-intermediates --keep-logs --print --outdir build_retry main.tex` 复现：XeTeX 和 BibTeX 已成功生成 20 页 XDV，但 `xdvipdfmx` 转换时以 `Segmentation fault (core dumped)` / exit 139 退出。复现记录为 `build_retry/tectonic_reproduce.console.log`。
- GDB 在最小化的 C 组矩阵上给出确切栈：`create_font_alias → pdf_dev_locate_font → dvi_locate_native_font → do_fnt → dvi_do_page → dvipdfmx_main`，见 `build_retry/gdb_matrix_c.log`。C 组四个分组各自单独编译均成功，排除某条表格数据或某个引用损坏；故障是长文档中 TTC 原生 CJK 字体别名的累积处理崩溃。
- 将 TTC `Noto Serif CJK SC` 主中文字体替换为单字面 TTF `Droid Sans Fallback`，并使用 DejaVu Serif/Sans TTF 作为 xeCJK 标点回退字体，从而绕过 `create_font_alias` 崩溃且完整显示中英文标点。
- 崩溃解除后，`xdvipdfmx` 暴露第二个独立错误：Tectonic 缓存 bundle 中 `ntxsy5` 没有可供 PDF 输出的 `.vf` 或物理字体。在保持 `amsmath → newtxtext → newtxmath` 加载顺序和 Times/newtx 体系的前提下，将数学包设为 `\usepackage[nonewtxmathopt]{newtxmath}`，选用 bundle 可输出的非光学尺寸符号字体。
- 最终字体警告仅为：为只含拉丁字段的 `\texttt` 未定义 CJK mono，以及 DejaVu 标点回退字体不声明 CJK script。两者均不产生缺字，也不影响 PDF 字体嵌入。
- 最终使用 `/tmp/goai_tectonic_0_17_0/tectonic -X compile -C --keep-intermediates --keep-logs --print --outdir . main.tex` 从 `main.tex` 真实生成 `main.pdf`；`xdvipdfmx` 完整输出 19 页并以 exit 0 结束。最终日志保存为 `main.log` 和 `build/final_compile.console.log`，未生成 HTML 镜像。

## 终检

- `pdfinfo` 确认最终 PDF 为 19 页、PDF 1.5、Letter 纸张；`pdftotext` 逐页字符数均大于 0（最少的第 19 页仍为 1573 字符），无空白页。抽取文本包含中文正文、图/表题和参考文献，无乱码或缺字。
- 将 19 页全部渲染为联络表 `build/qc/contact_19_pages.png`，并抽检第 3--4 页两张图、第 6--9 页代表性长表、第 15 页参考文献首页与第 19 页尾页：两图完整且标注可读，表格无裁切/重叠，参考文献从 [1] 连续到 [52]，限定性讨论和 limitation 在正文中保留。
- `pdfimages -list` 显示图页中的核心图面约为 721 dpi；`pdffonts` 确认文档字体嵌入。终检摘要保存为 `build/final_qc.log`，文本抽取保存为 `build/final_pdftotext.txt`。
- 终检前扫描 `TODO` 与“待补证据”均为 0。两道闸门的本次复跑结果在下一条追加。

## Reviewer I5/I7 定向返工

- 仅处理 reviewer I5（blocker）与 I7（major）；未修改 `references.bib`、taxonomy 或任何图源/图面，也未执行独立审稿。
- 新增 `workspace/notes/condition_source_trace.md`，逐字段回到 B1（原文 p. 422）、B5（p. 598, §2）、B6（主文 §2.1.1；SI §1.1/§1.3, pp. 2–3）、C17（p. 126, §2）实验段；C6 明确保留题名级证据边界。每条均记录 DOI/key、可支持字段和不可支持字段。
- 重建条件矩阵中 B1/B5/B6/C6/C17 两块联表及 `NA` 汇总：B6 改为固相陶瓷/粉体路线；B1 补整批投料克数、空气和关炉慢冷；B5 补 `Ba:Y:Si=x:26:16`、原料预处理、两次 400 rpm/1 h 玛瑙球磨、空气/容器/炉冷；C17 补 256 rpm、1–3 h、玛瑙罐/球与球粉比；C6 路线降为“未明”。同步修订条件矩阵、近邻路线和失败边界的比较措辞，禁止把题名补成路线或把“当前证据未暴露”写成“全文未报告”。
- D0 的路线、目标身份与直接复现起点仍只由 `ababaikeri2024ba5y12zn` 支撑；D1/N1/P1 只描述各自邻相或方法字段，不写成目标配方。
- 新增 `sections/00_review_method.tex` 并在 `main.tex` 摘要后引入：公开 2026-08-31 至 2026-09-01 的检索日期、本地语料与 OpenAlex/Crossref/Semantic Scholar/arXiv/DBLP 及出版社/DOI/IUCr/COD/RSC 路径、别名式、纳排/去重、前后向滚雪球和正式 `niche-balanced` 档位。
- 方法与局限同步披露 63 条候选、51 个经 ref_gate 核验的独立 works、2024–2026 为 9/63、D0 仅一篇且无独立复现、原 comprehensive 档位未完成；摘要与结论均删除任何可被理解为全面覆盖的口径并明确不声称 comprehensive。
- `GOAI_SUPERLIB` 与 `~/Code/super_library` 均不存在，按 survey-writer skill 记账降级：跳过 bundle 与 wording lint；本次方法/证据内容不以该语料库作来源。

## I5/I7 编译与终检

- 使用指定二进制 `/tmp/goai_tectonic_0_17_0/tectonic -X compile -C --keep-intermediates --keep-logs --print --outdir . main.tex` 从 `workspace/drafts/main.tex` 真编译；最终 exit 0，`xdvipdfmx` 写出 20 页 `main.pdf`。
- 首轮因 B 区新增字段出现 `Float too large by 18.7 pt`；只在该浮动表局部将 `arraystretch` 调至 1.05，四轮编译后超页告警归零。最终 `main.log` 无 Float-too-large、Overfull/Underfull、未定义引用、缺字或未处理浮动体告警；既有可复现性/字体回退提示不影响输出。
- 最终 `bib_guard`：8 个章节文件、196 次引用调用、51 个去重 key/51 条 BibTeX，整合率 100%，引用密度 36.8 次/千词，PASS。最终 `tex_guard`：21 个 TeX 文件、12 labels、6 refs，PASS。
- `pdfinfo`：20 页、Letter、PDF 1.5、1,860,699 bytes。逐页 `pdftotext` 均非空（最少第 15 页 259 个非空白字符）；抽检方法页、两图附近、B/C 条件表、结论尾页和参考文献尾页，无裁切、重叠或空白页。第 15 页的下部留白来自参考文献前模板强制 `clearpage`，页面含结论正文。

## Reviewer I10 定向返工

- 仅处理终审 minor I10；未修改 `references.bib`、figure、taxonomy 或 `CITATION_AUDIT`，也未处理仍属 ref_gate 的 I11。
- 在“证据距离分级”中补充 strong/weak 的独立判据：该后缀只表示允许证据包对记录在本综述中所承担主张的直接支撑强度，与 D0/D1/N1/P1 的迁移距离正交；它不表示全文可得性、实验字段完整度或字段真伪。
- 以 B2 和 C2/C17 明示判据边界：摘要或系统研究可以直接支撑 D1 身份谱系角色而记 strong；可靠、详细的原始实验数值若只承担间接 P1/N1 路线或方法对照，仍记 weak。表中既有等级与数值均未改动。
- I10 修改后 `bib_guard`：8 个章节文件、196 次引用调用、51 个去重 key/51 条 BibTeX，整合率 100%，引用密度 36.5 次/千词，PASS；`tex_guard`：21 个 TeX 文件、12 labels、6 refs，PASS。
- 使用 `/tmp/goai_tectonic_0_17_0/tectonic -X compile -C --keep-intermediates --keep-logs --print --outdir . main.tex` 从 `workspace/drafts/main.tex` 真编译，exit 0；`xdvipdfmx` 写出 20 页、1,863,919 bytes 的 `main.pdf`。编译后的 PDF 可检出新增 strong/weak 定义与 B2、C2/C17 解释，20 页逐页非空（最少第 15 页 755 个非空白字符）。
- `main.log` 中 Float-too-large、Overfull/Underfull、未定义引用、缺字、未处理浮动体及 LaTeX error 均为 0；仍只有既有字体回退/绝对字体路径可复现性提示，未修改排版模板或字体配置。

## 2026-09-02 学术结构、实验方向与图稿重写

- 新增正式引言 `00_introduction.tex`：从目标相的科学问题起笔，单列 Ba--Y--Si--O、Ba--Zn--Si--O 和 Y--Si--O 三类相关体系及其已发表发现；检索截止日期只保留在方法节，不进入引言或摘要。
- 将方法节改写为常规的检索范围、纳排/去重、证据评价与条件抽取，不在正文使用 `niche-balanced`、`ref_gate`、`works` 等内部工作流术语。
- 新增 `04_prior_experimental_findings.tex`，综合既有实验的三项结论：组成坐标优先于孤立最高温度；单晶身份不等于批量相纯；局部相图是连接复现与发现的核心实验。Pt/Au 容器、研磨介质和氧分压的成对对照仅保留在内部材料知识库，不写入正文结论。
- 新增 `08_future_directions.tex`，提出局部相图、`Ba5Y13-xZnx[SiO4]8O8.5-x/2` 系列、固相/高温溶液并行和 Mg/Co 类比四项方向；每项均给出前驱体、工艺筛查起点、验证终点和可区分的科学结论。
- 通过真实 stdio MCP 调用本地两步无机逆合成模型。Zn、Mg、Co 三个目标的首选前驱体分别为共同的 BaCO3/Y2O3/SiO2 加 ZnO/MgO/Co3O4；候选池概率为 0.594/0.522/0.298。完整调用保存在 `state/tool_calls.jsonl`，整理与失效模式在 `ideas/precursor_predictions.md`。模型规范化的括号显示不进入论文结构式。
- 首次 MCP 调用暴露 vendored `chemistry.py` 第 421 行缩进错误；主仓库已做单行修复，`py_compile` 及离线相关测试通过。该修复不改变模型权重或 NAS 源代码。
- 按“先图像生成参照、再 Draw.io 矢量重建”的要求重绘图 1、图 2，并新增图 3 研究路线。三图均使用白底、深蓝灰和单一赭色强调，无渐变、无阴影；figspec、SVG、Draw.io、PDF 同源。图 3 初版验证框过窄，第二轮加宽后通过排版 lint 和实际预览。
- `main.tex` 改为中文“图/表”标签并使用空格分隔 caption 标签；摘要和结论重写为研究问题、既有结论、优先实验和科学发现价值。
- 最终 `bib_guard`：11 个章节、206 次引用调用、51/51 条文献整合、引用密度 32.8 次/千词，PASS；`tex_guard`：24 个 TeX 文件、17 labels、8 refs，PASS。
- 使用 Tectonic 0.17.0 从 `main.tex` 真编译得到 23 页 `main.pdf`（1,257,520 bytes，PDF 1.5）。`main.log` 中 Overfull/Underfull、Float-too-large、未定义引用、缺字、LaTeX error 和未处理浮动体均为 0；抽检标题/引言、三张图、实验方向/模型表和结论页，无裁切、重叠或空白页。

## 2026-09-02 学术措辞专项修订

- 将“身份与出处核验表、证据级、比较标签、已过闸、字段归一化、相互独立的验证终点、四方端点”等内部流程用语改为“目标化合物及相关体系的组成与结构依据、与目标相的关系、分类依据、已通过文献核查、合成条件的统一比较、互补的表征方法、四方参照相”等材料学表达。
- 重写第 2--6 节中残留的 D0/D1/N1/P1、strong/weak、证据包、引用池、工具箱、降权和迁移权限等软件化表述；保留文献相关程度、合成条件、结构关系和表征方法的学术逻辑。
- 同步修订三张图的标题、节点和图注，使图面文字与正文使用同一套材料学术语；重新导出 PDF 图并检查图中文字、连线和裁切。
- 在 `AGENTS.md`、`goai-survey-writer`、`goai-reviewer`、`goai-orchestrator` 和 `goai-figure-studio` 中加入“内部控制语汇与论文语言分离”规则，并新增 `tools/academic_language_guard.py` 及离线测试。该检查对正文、表格、图注和图中文字阻止软件流程隐喻泄漏。
- 修订后 `academic_language_guard`、`bib_guard` 和 `tex_guard` 均 PASS；引用调用 215 次、51/51 条文献整合、引用密度 35.8 次/千词；离线测试 43 项通过。Tectonic 0.17.0 编译得到 23 页 PDF，未见 Overfull/Underfull、Float-too-large、未定义引用、缺字或 LaTeX error。

## 2026-09-02 中文学术语言独立返工

- 本轮只修改 `workspace/drafts/sections/*.tex` 与本日志；未修改 `references.bib`、figspec、SVG/PDF/Draw.io 图文件、taxonomy 或证据审计。所有原有 `\cite{}`、数值、化学式、实验限制和 `\texttt{NA}` 信息均保留在原论断范围内。
- `00_introduction.tex`：把开头改为“研究目标—材料体系—证据边界”，将Ba--Y--Si--O、Ba--Zn--Si--O和Y--Si--O的已有发现另列小节；代表性改写为“先确定研究对象，再区分单晶生长、固相反应和相图筛查各自回答的问题”。未把近邻条件写成目标相配方。
- `00_review_method.tex`：将检索、纳排、去重和条件抽取改为短句主动语态；保留63条候选、51篇独立文献、截至2026-09-01及“不命中不等于不存在”的限制。
- `01_phase_identity.tex`：把“获得了什么相”和“采用了什么条件”分开叙述，明确目标相只有一篇直接报道；表格仍保留原始化学式、非整比式、结构方法和待研究问题，未将变量式改成定组成式。
- `02_evidence_distance.tex`：将分类依据改写为“研究对象与目标相的关系”，删除以单一等级评价整篇论文的表述；保留直接报道、同类Ba--Y、结构相关、工艺参照和非相关资料的适用边界。
- `03_condition_matrix.tex`：在条件总表前新增“前人实验结论概览”，先总结组成、批量相纯、坩埚判据和局部相图四项认识，再进入路线比较；表格中的原料、温度--时间、气氛、容器、冷却、产物和`NA`未改动其证据边界。
- `04_prior_experimental_findings.tex`：按组成坐标、单晶与批量相纯、局部相图三个主题朗读式重写；1150\,$^\circ$C、2\,K\,h$^{-1}$、151组实验、$x=9$--14等数值和对应引用均保留。
- `04_neighbor_routes.tex`：改用材料化学常用的主动句，明确高温溶液、固相成相、机械活化和Czochralski只能提供方法参照；Pb/F助熔风险、题名级记录和目标相不可直接外推的限制均保留。
- `05_validation_endpoints.tex`：将四类“端点”统一改为结构模型、批量相组成、实际组成与污染、高温稳定性四类表征问题；保留SCXRD、PXRD/Rietveld、EDS/EPMA/ICP、HT-XRD及各自不能替代的范围。
- `06_failure_boundaries.tex`：用短句重写相竞争、污染/挥发、气氛/晶型和资料缺失/EHS四段；保留Pb/F路线审核、研磨污染、观察温度与冷却状态等限制，不补写未报道的失败机理。
- `07_transferability_conclusion.tex`：结论明确最值得优先开展的实验是目标组成附近的小步长局部相图，并落到BaCO$_3$、Y$_2$O$_3$、ZnO、SiO$_2$前驱体、分段煅烧/退火和PXRD/Rietveld及SCXRD复核；未把近邻数值外推为目标相条件。
- `08_future_directions.tex`：四个方向逐一写明前驱体与工艺，并加入“模型预测，待实验验证”；方向二保留$0\leq x\leq1.25$及六个离散点，方向三保留1100--1200\,$^\circ$C、约3\,h、1--2\,K\,h$^{-1}$和约900\,$^\circ$C，方向四保留0.594、0.522、0.298概率及Mg/Co对照限制。
- 对全部章节做了一轮朗读式检查，删除中英文和数字周围的手工空格，让XeLaTeX/xeCJK处理间距；未改变数学环境中的`\,`单位间距、引用、表格列结构和图路径。
- 本轮复跑结果：`academic_language_guard` PASS；`bib_guard`检查11个章节、223次引用调用、51/51条目整合率100%、引用密度41.3次/千词，PASS；`tex_guard`检查24个TeX文件、17个标签、8个交叉引用，PASS。所有声明产物均已写入并保持非空。
- 终检后仅修正`08_future_directions.tex`中电荷平衡式的数学标点空格（`1.25 ,`改为`1.25,`），不涉及化学计量、引用或结论；三项检查随后复跑仍为PASS。

## 阶段五组装与最终版面精修（2026-09-02）

- 使用指定 `/tmp/goai_tectonic_0_17_0/tectonic` 从当前 `main.tex` 真实编译，并抽查首页、三张图页、条件表页、研究方向页和参考文献页。三张最新 PDF 均已由正文路径嵌入；图面无裁切、重叠或不可读文字。
- 编译日志仅发现第 1 节一处约 3.5 pt 的窄栏溢出；将 `01_phase_identity.tex` 的断行点移至结构式引用之后，避免短行并仅改善断行，不改变事实、数值、引用或证据强度。
- 输入图 PDF 自带 1.7 版本而主稿输出设为 1.5，Tectonic 对三次嵌图各给出版本提示；未改动图件内容，记录该兼容性提示并以 `pdfinfo` 核对嵌图完整性。
- 条件总表的来源定位单元原先以等宽字体显示 BibTeX key；在主模板的 `\\texttt` 显示层将含年份的内部 key 统一呈现为“来源”，保留同一单元中的 `\\cite{}` 文献标记，不改引用对象、数值或证据边界。
- 最终 QC：`pdfinfo` 确认 23 页 Letter、PDF 1.5；`pdftotext` 逐页非空且裸 BibTeX key/内部控制术语扫描为 0；`pdftoppm` 抽查首页、含表格页、三张图页、研究方向页及参考文献首尾页，确认无裁切、重叠、空白页，图注与正文编号一致。最终 PDF 已复制至仓库根目录 `Ba5Y12Zn_合成调研_学术润色版.pdf`。
