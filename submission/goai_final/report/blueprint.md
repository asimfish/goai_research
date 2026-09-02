# Ba₅Y₁₂Zn[O(SiO₄)]₈ 合成条件综述：阶段三章节蓝图

> 状态：仅为 survey-writer 阶段三蓝图；本轮不创建任何 `.tex`、`sections/`或 `main.tex`，不设置 `draft_complete`。
> 证据边界：事实引用只能取自 `workspace/notes/citation_bank.md` 中的 bank key，并受已通过 ref gate 的 `workspace/library/references.bib` 约束。
> 读者与篇幅：面向中文无机固体化学读者；正文目标 8–12 页，约 8,550 汉字（不含参考文献、图注与表注），允许 8,000–9,300 汉字的编辑浮动。

## 蓝图决策

- **论证顺序**：身份核验 → 证据距离 → 路线/变量条件矩阵 → 近邻路线 → 表征终点 → 失败边界 → 可迁移性与结论。该顺序将“是什么”和“如何制得”隔开，先定义证据距离，再允许任何工艺比较。
- **风格依据**：采用 `workspace/notes/style_notes.md` §2–§6 的“比较问题/机制先行、同字段横向收束、判断句—证据比较—限定句—过渡句”结论，引用密度按每千词至少 8 次 citation calls 规划。风格库为 WARN，故不声称其为领域基准。
- **与默认骨架的差异**：不单设宽泛 Introduction/Background，而在第 1 节开头用“身份难题—证据缺口—比较框架”完成导入；不单设 Open Problems，因用户限定的主线以失败边界和可迁移性收束，且 `ideas_reviewed` 已记为 skipped/WARN。
- **标题词法**：7 个 section 标题均为 2–6 词的信息性名词短语，不用三连并列或 method/rules/aspects/considerations 类机关词。`GOAI_SUPERLIB` 未设置且 `~/Code/super_library` 不存在，故按 skill 降级跳过其标题 lint；该决策已记账。

## 篇幅与交付地图

| 顺序 | Section 标题 | 未来唯一文件 | 预计汉字 | 图表唯一归属 |
|---:|---|---|---:|---|
| 1 | 身份与结构核验 | `workspace/drafts/sections/01_phase_identity.tex` | 900 | 表 1：身份与出处核验表 |
| 2 | 证据距离分级 | `workspace/drafts/sections/02_evidence_distance.tex` | 900 | 图 1：`fig01_evidence_synthesis_map` |
| 3 | 路线变量矩阵 | `workspace/drafts/sections/03_condition_matrix.tex` | 2,100 | 图 2：`fig02_route_variable_matrix`；表 2：可追溯合成条件总表 |
| 4 | 近邻合成路线 | `workspace/drafts/sections/04_neighbor_routes.tex` | 1,400 | 只引用图 2/表 2，不新建数值表 |
| 5 | 表征验证终点 | `workspace/drafts/sections/05_validation_endpoints.tex` | 1,050 | 只引用图 2/表 2，表征判据用正文 run-in |
| 6 | 失败模式边界 | `workspace/drafts/sections/06_failure_boundaries.tex` | 1,200 | 只引用图 1/表 2，不独立绘图 |
| 7 | 配方迁移与结论 | `workspace/drafts/sections/07_transferability_conclusion.tex` | 1,000 | 综合图 1–2/表 2，不新建图表 |
| **合计** |  |  | **8,550** | **2 图 + 2 表** |

## 并行写作 ownership

1. 每个写作者只修改上表分配的一个 section 文件；不创建或修改 `main.tex`、BibTeX、图文件、其他 section 或本蓝图。
2. 第 1 节独占“规范式/别名/出处/结构身份”；第 2 节独占 D0/D1/N1/P1/X 的定义和纳排判据。其他节只回指，不重新定义。
3. 第 3 节独占所有文献配方数值、字段归一化和表 2；第 4–7 节只做路线逻辑、验证、边界或迁移综合，不复制数值段落。
4. 第 4 节独占 N1/P1 近邻路线的跨体系比较；第 5 节独占“什么才算产物已被验证”；第 6 节独占负结果、失败和不适用边界；第 7 节独占迁移规则与全文结论。
5. 交叉主题通过预留标签回指：`sec:identity`、`sec:evidence-distance`、`sec:condition-matrix`、`sec:neighbor-routes`、`sec:validation-endpoints`、`sec:failure-boundaries`、`sec:transferability`；图表标签由所属 section 唯一定义。

## 逐节蓝图

### 1. 身份与结构核验

- **未来文件/ownership**：`workspace/drafts/sections/01_phase_identity.tex`。唯一拥有全文的问题导入、范围边界、规范化学式、历史命名与相身份核验；不定义证据等级的完整规则，不写合成数值。
- **Reader question**：读者在比较合成条件前，如何确认 `Ba₅Y₁₂Zn[O(SiO₄)]₈` 的规范式、原始出处和结构身份，并把它与无 Zn 四方 Ba–Y 谱系和竞争相分开？
- **Taxonomy 分支**：主要 A1–A3、B1、C1；只为身份判定调用 F1、G4。
- **贡献落点**：候选 1 是主落点，把“规范式与结构身份核验”置于合成比较之前；候选 2 仅在表 1 的标准化字段中落地。
- **具体 bank keys**：核心 `ababaikeri2024ba5y12zn`；谱系与重审 `kolitsch2009crystal`, `wierzbickawieczorek2017high`, `yamane2024synthesis`, `yamane2024microstructure`, `gulay2024navigation`；竞争结构端点 `motozawa2022bay16si4o33`。本节不用 N1/P1 key 补足 D0 数量。
- **段落组织**：(i) `问题与范围`：用身份混淆、D0 稀缺和本综述的三层比较框架完成导入；(ii) `目标相出处`：只陈述原始工作能够直接支持的式、路线类型与结构验证层级；(iii) `四方谱系重审`：并列历史命名、非整比/调制结构重审和独立相场证据，结束时明示未解决的 Zn 占位/相关系问题。
- **图表**：表 1 `tab:identity-ledger`“身份与出处核验表”，列为原文化学式、规范化式、来源 key、结构/相场证据、拟定证据级、可支持身份主张、未决问题。表中不放工艺数值，避免与表 2 冲突。
- **预计字数**：900 汉字，其中导入 200、目标相 250、谱系重审 350、过渡 100。
- **完稿检查**：D0 始终只计 1 篇；D1 不写成含 Zn 目标相的独立复现；原文式与编者规范式分列；表 1 每行有 key 和证据类型；对证据包未暴露的占位/计量只写“未解决”，不作同相推断。

### 2. 证据距离分级

- **未来文件/ownership**：`workspace/drafts/sections/02_evidence_distance.tex`。唯一拥有 D0/D1/N1/P1/X 的定义、纳排规则、降权方向和图 1；不重复表 1 的出处史，不列任何合成数值。
- **Reader question**：“同一相”、“同一身份谱系”、“结构近邻”、“工艺近邻”和“应排除记录”分别要求什么证据，证据距离如何约束条件的可迁移性？
- **Taxonomy 分支**：§1.1–1.3、B1–B5、§4 未归类与 §5.3 结构可比性缺口；迁移方向回指 H1–H5。
- **贡献落点**：候选 1 的 D0/D1/N1/P1/X 证据梯度是本节主体；候选 3 的“逐级降权、只迁移变量结构”作为输出规则。
- **具体 bank keys**：层级锚点 `ababaikeri2024ba5y12zn`, `kolitsch2009crystal`, `yamane2024synthesis`, `gulay2024navigation`；N1 对照 `liu1993structures`, `lin1999phase`, `kaiser2002crystal`, `zou2021crystal`, `gorelova2016thermal`；P1 与多型边界 `dolan2008structures`, `becerro2004revision`；Ba–Si–O/X 边界 `finger1995refinement`, `hazen1999crystal`, `tillmanns1978refinement`, `katscher1973the`, `zhong2020combining`, `yusa2007rhombohedral`, `buerger1954the`, `gu2025liba2gasi2o8`, `erlebach2020thermomechanical`。
- **段落组织**：(i) `分级判据`：以主张而非整篇论文为分类单位；(ii) `结构距离`：从 I-42m 主谱系到 Ba–Y、Ba–Zn–Si、Y–Si–O 与 Ba–Si–O 对照，只比较存在明确结构读出的层级；(iii) `排除边界`：说明组成相近、功能相近或一般理论背景为何不能承担目标相配方主张。
- **图表**：插入图 1 `fig:evidence-map`，使用 `workspace/figures/svg/fig01_evidence_synthesis_map.svg`；caption 以 `figure_plan.md` 的定稿为起点，正文解释“允许进入框架”不等于“数值可直接迁移”。
- **预计字数**：900 汉字，分级判据 300、结构距离 350、排除/过渡 250。
- **完稿检查**：每个材料级别都给出可接受的主张类型和禁止的主张类型；实线/虚线的文字解释与图 1 一致；不用“相似”跳过结构证据；X 类不进入合成条件表；强/弱 claim 不超过 bank 原定强度。

### 3. 路线变量矩阵

- **未来文件/ownership**：`workspace/drafts/sections/03_condition_matrix.tex`。唯一拥有五类路线的字段归一化、文献中任何配方数值、图 2 和表 2；其他 section 只能引用本节的表格/结论。
- **Reader question**：如何把外加助熔、自熔/熔体、固相陶瓷、机械化学预活化与 Czochralski 记录转换为同一组可追溯字段，同时不把近邻数值写成目标相条件？
- **Taxonomy 分支**：D1–D5、E1–E5，并以 F1–F4 作产物终点字段；分区规则调用 H1–H5。
- **贡献落点**：候选 2 的“路线—变量—结果”可追溯对照是本节核心交付；候选 1 通过证据等级列落地；候选 3 通过 D0 与近邻数值分区落地。
- **具体 bank keys**：D0/D1 核心 `ababaikeri2024ba5y12zn`, `kolitsch2009crystal`, `wierzbickawieczorek2017high`, `yamane2024synthesis`, `yamane2024microstructure`, `gulay2024navigation`；外加助熔/熔体 `ababaikeri2024ba3zn4si4o15`, `christensen1994investigation`, `leonyuk1999high`, `leonyuk1999crystal`, `giess1982zn2sio4`；固相/陶瓷 `lin1999phase`, `zou2021crystal`, `kerstan2012thermal`, `cai2024optimized`, `zou2019anti`, `tejas2024structural`, `pires2001luminescence`, `zhao2026crystal`, `kerstan2015kristallphasen`；机械化学 `yldrm2009y2sio5`, `tzvetkov2001effects`；提拉/生长 `pang2005study`, `alizadeh2021spectroscopy`, `shoudu1999czochralski`, `brandle1986czochralski`。
- **段落组织**：(i) `路线字段`：先解释五类主导成相事件和共享/特有字段；(ii) `条件总表`：先呈现 D0 独立分区，再呈现 D1 和 N1/P1 分区；(iii) `变量比较`：比较配比、温度—时间、气氛、坩埚/助熔与冷却的报告完整度，只在同一证据分区内归纳。
- **图表**：图 2 `fig:route-matrix`使用 `workspace/figures/svg/fig02_route_variable_matrix.svg`，说明字段抽取与验证交接，不画成因果或优化图；表 2 `tab:synthesis-conditions`是全文唯一的可追溯合成条件总表，详细合同见下文。
- **预计字数**：2,100 汉字，路线与字段 500、读表指南 350、跨路线比较 850、证据完整度/过渡 400；表内文字不计入正文字数。
- **完稿检查**：表 2 包含全部强 D0/D1 路线记录和有可用工艺字段的代表 N1/P1 记录；每行有 key、证据级和来源定位；每个数值单元格能回到同一 key 的原始实验段/表图；缺值一律 `NA`，不留空白、不写“应为”；D0 数值与近邻数值在版面上完全分区；不由多篇拼接出一个未报道配方。

### 4. 近邻合成路线

- **未来文件/ownership**：`workspace/drafts/sections/04_neighbor_routes.tex`。唯一拥有 N1/P1 路线的跨体系综合；只引用表 2 中已归一化的数值，正文不再复制数值、不将近邻排成“候选配方”。
- **Reader question**：在结构与工艺距离已明确的前提下，Ba–Y、Ba–Zn–Si、Y–Si–O 与 Ba–Si–O 近邻的助熔/熔体、固相、机械活化和提拉路线各能提供哪些可用方法信息？
- **Taxonomy 分支**：B2–B5、C2–C4、D1–D5，以 H3–H5 为迁移上限。
- **贡献落点**：候选 2 通过“按主导成相事件，而不是按化合物逐篇罗列”落地；候选 3 通过“只迁移变量结构和验证清单”落地。
- **具体 bank keys**：稀土硅酸盐结构/多型 `redhammer2003beta`, `becerro2004revisiting`, `sun2014recent`, `felsche1973the`；Ba–Zn/Mg–Si–O 结构与替代 `liu1993structures`, `kaiser2002crystal`, `thieme2022solid`, `aitasalo2006crystal`, `thieme2015ba1`, `kerstan2013bazn2si2o7`, `thieme2017variable`, `thieme2016negative`, `zou2019anti`；路线对照 `christensen1994investigation`, `ababaikeri2024ba3zn4si4o15`, `pang2005study`, `leonyuk1999high`, `leonyuk1999crystal`, `giess1982zn2sio4`, `yldrm2009y2sio5`, `tzvetkov2001effects`, `shoudu1999czochralski`, `brandle1986czochralski`。
- **段落组织**：(i) `高温溶液路线`：比较外加助熔、自熔与慢冷/分离变量，对 Pb/F 历史条件同时给出 EHS 边界；(ii) `固相成相路线`：以组成系列、复磨复烧、气氛与 PXRD/成分审计为同字段比较；(iii) `活化与提拉`：机械化学只支持预活化/污染审计框架，Czochralski 只支持熔体、坩埚、气氛与挥发控制清单。
- **图表**：正文回指图 2 `fig:route-matrix` 与表 2 `tab:synthesis-conditions`；不新建“近邻数值摘要表”，避免与总表重复且模糊证据距离。
- **预计字数**：1,400 汉字，高温溶液 500、固相成相 500、活化/提拉及过渡 400。
- **完稿检查**：每个近邻实例首次出现都标 D1/N1/P1 用途；每个小节都用相同的“可迁移变量—所需验证—禁止外推”三拍收束；不将多型/功能性能证据写成 D0 成相证据；不转写表 2 的任何近邻数值为目标相建议。

### 5. 表征验证终点

- **未来文件/ownership**：`workspace/drafts/sections/05_validation_endpoints.tex`。唯一拥有结构身份、批量相纯度、组成/污染和高温稳定性的成功判据；不承担路线数值或失败机理的全面讨论。
- **Reader question**：一个“得到主相/晶体”的报道要满足哪些互补表征终点，才足以支持结构身份、相纯度、组成可信度和冷却后稳定性？
- **Taxonomy 分支**：F1–F4，并回指 A1–A3 的身份问题、E1–E5 的输入字段和 G2–G3 的风险。
- **贡献落点**：候选 2 的“输入变量与验证终点分开”是主落点；候选 1 通过高等级结构读出支持身份核验。
- **具体 bank keys**：单晶/先进衍射 `ababaikeri2024ba5y12zn`, `kolitsch2009crystal`, `yamane2024synthesis`, `gulay2024navigation`, `motozawa2022bay16si4o33`, `zou2021crystal`；局域结构补充 `becerro2004revisiting`；PXRD/Rietveld `yamane2024microstructure`, `lin1999phase`, `kerstan2012thermal`, `cai2024optimized`；成分/显微 `thieme2015ba1`, `tejas2024structural`, `pang2005study`；高温/气氛 `kerstan2013bazn2si2o7`, `thieme2016negative`, `zou2019anti`。
- **段落组织**：(i) `结构身份终点`：区分 SCXRD/CRED/同步辐射/中子精修所支持的主张；(ii) `批量相纯终点`：要求未索引峰、相分数/检出限与热史；(iii) `组成污染终点`：分开名义配比、局域点分析和体平均；(iv) `高温稳定终点`：分开原位高温相和室温回收相。
- **图表**：解读图 2 右侧四类验证终点，并解释表 2 的“产物/验证”列如何决定该行能支持的结论强度；不新建图表。
- **预计字数**：1,050 汉字，四类终点约 220–250 字/类，结尾 100 字。
- **完稿检查**：“峰位相似”或“主相出现”不被写成相纯/身份已定；每类终点都列出可支持主张和不能支持主张；原位高温相不等同冷却产物；表 2 中只要没有对应验证，正文结论即同步降级。

### 6. 失败模式边界

- **未来文件/ownership**：`workspace/drafts/sections/06_failure_boundaries.tex`。唯一拥有竞争相/玻璃、污染/挥发/助熔副作用、气氛/热致晶型边界、字段不完整与安全边界；不改写成功路线或提出新实验方案。
- **Reader question**：哪些负结果和缺字段记录真正限制了配方的可复现性，何时必须停止将“工艺异常”解释为“真实固溶/相窗”？
- **Taxonomy 分支**：G1–G4，回指 E1–E5、F2–F4与 scope 的安全边界。
- **贡献落点**：候选 3 的“失败边界与分级配方迁移”是本节主落点；候选 2 通过输入字段与失败终点的对照落地。
- **具体 bank keys**：组成/相竞争 `wierzbickawieczorek2017high`, `yamane2024synthesis`, `yamane2024microstructure`, `gulay2024navigation`, `tzvetkov2001effects`；污染/挥发/助熔 `yamane2024microstructure`, `shoudu1999czochralski`, `giess1982zn2sio4`；热致/气氛 `lin1999phase`, `kerstan2012thermal`, `kerstan2013bazn2si2o7`, `thieme2016negative`, `zou2019anti`；字段不完整 `ababaikeri2024ba5y12zn`, `ababaikeri2024ba3zn4si4o15`, `kaiser2002crystal`, `cai2024optimized`, `zhao2026crystal`；排除性功能/理论语境 `thieme2017variable`, `erlebach2020thermomechanical`, `gu2025liba2gasi2o8`。
- **段落组织**：(i) `相场与竞争`：把组成偏离、竞争相、玻璃和宽相场与同一行条件绑定；(ii) `污染与挥发`：区分研磨介质带入、Si/Zn 损失和助熔副作用；(iii) `气氛与晶型`：说明原位高温相、还原耐受与冷却回收相不能混同；(iv) `缺失与安全`：将当前证据包未暴露字段写为 `NA`，并对钡盐粉体、高温挥发、Pb/F 助熔、坩埚相容性给出 EHS 审核边界。
- **图表**：回指图 1 的降权/排除路径与表 2 的产物、验证、NA 列；不新建失败模式表，防止在 8–12 页内重复表 2。
- **预计字数**：1,200 汉字，相场/竞争 300、污染/挥发 300、气氛/晶型 250、缺失/安全 250、过渡 100。
- **完稿检查**：至少覆盖 G1–G4 四类边界；负结果与成功数值指向表 2 同一来源行；“证据包未报告”不写成“原论文没有”；危害条件仅作历史对照并显示废物/相容性审核；不用未验证机制语气解释失败。

### 7. 配方迁移与结论

- **未来文件/ownership**：`workspace/drafts/sections/07_transferability_conclusion.tex`。唯一拥有 D0 复现起点、D1 同谱系筛选、N1/P1 工具箱、X 不迁移的综合规则以及全文结论；不引入新证据、新数值或实验方案。
- **Reader question**：在只有一条 D0 直接证据、且多数条件来自 D1/N1/P1 的情况下，读者可以带走哪些可审计的复现起点、筛选框架和不可越过的结论边界？
- **Taxonomy 分支**：H1–H5，并综合 §5 证据缺口与 §6 阶段一结论。
- **贡献落点**：同时收束候选 1（身份与证据分级）、候选 2（可追溯条件矩阵）与候选 3（失败边界与降权迁移）；结论按三项贡献的已完成程度逐项回答。
- **具体 bank keys**：D0 `ababaikeri2024ba5y12zn`；D1 `kolitsch2009crystal`, `wierzbickawieczorek2017high`, `yamane2024synthesis`, `yamane2024microstructure`, `gulay2024navigation`；N1/P1 工具箱代表 `motozawa2022bay16si4o33`, `liu1993structures`, `lin1999phase`, `zou2021crystal`, `kerstan2012thermal`, `thieme2015ba1`, `kerstan2013bazn2si2o7`, `thieme2016negative`, `pang2005study`, `giess1982zn2sio4`, `tzvetkov2001effects`, `shoudu1999czochralski`；X 边界 `buerger1954the`, `erlebach2020thermomechanical`, `gu2025liba2gasi2o8`。
- **段落组织**：(i) `分级迁移策略`：按 D0 直接起点、D1 组成/相场筛选、N1/P1 变量/验证工具箱、X 排除顺序陈述；(ii) `证据缺口`：将 D0 独立复现、Zn 占位/固溶系列、相纯窗口和关键工艺字段作为限制，不生成 idea-forge 式新方案；(iii) `综述结论`：用三句对应三项贡献，最后一句明确“可迁移的首先是变量结构和验证纪律，而非近邻数值”。
- **图表**：一次回指图 1 的降权逻辑、图 2 的抽取/验证框架和表 2 的数值分区；不新建图表。
- **预计字数**：1,000 汉字，分级迁移 450、证据缺口 250、结论 300。
- **完稿检查**：结论每一点都能回指前文图/表/证据；不出现本节首次引入的事实数值；D0 只称“唯一直接起点”，不称“已确立相纯窗口”；D1/N1/P1 输出均带用途限定；对未解问题只作证据缺口总结，不把推测写成化学结论。

## 可追溯合成条件总表合同

### 表格身份与行粒度

- 名称：表 2“可追溯合成条件总表”，标签 `tab:synthesis-conditions`，唯一所有者为 `03_condition_matrix.tex`。
- 一行对应一篇来源中的一个明确实验/组成点；同文献若有不同配比、路线、气氛或热程序，必须拆行，不以范围号合并成一个“代表配方”。
- 证据只到摘要/题名层且无数值的 key 仍可作“路线已确认、条件字段 NA”行，但必须标 `weak` 和来源定位，不得用同类文献补值。

### 强制分区

1. **A 区：D0 精确目标相**。只允许 `ababaikeri2024ba5y12zn` 中对精确目标相直接报道的记录。即使多个数值字段都是 `NA`，也必须保持独立板块，不向 D1/N1/P1 借值。
2. **B 区：D1 同一身份谱系**。收录四方 Ba–Y 谱系的助熔、自熔/陶瓷与组成扫描记录；标题和每行均写明“无 Zn D1，不是目标相复现”。
3. **C 区：N1/P1 近邻路线**。先按证据级 N1/P1，再按五类主导成相事件分组。近邻数值只用于显示工艺变量结构和报告范围，不与 A 区计算平均值、包线、“常用条件”或“建议窗口”。
4. **X 类排除**。X 记录不进入数值总表；如需说明排除理由，只在表注指向第 2/6 节。

### 强制列与填写语义

| 列 | 强制内容 | 填写规则 |
|---|---|---|
| 来源 | BibTeX bank key + 实验定位 | 定位写页码/实验节/表图；若当前只有摘要，明写“摘要证据” |
| 目标/产物式 | 该行实验声称的化学式 | 保留原文式；编者规范式放表注，不静默改式 |
| 原料 | 试剂化学式/形态/纯度 | 未报告任一子项即在该子项写 `NA` |
| 配比 | 称量比/摩尔比/名义组成 | 标明比值基准；称量与烧后组成不混合 |
| 路线 | 外加助熔、自熔/熔体、固相陶瓷、机械化学、Czochralski | 按主导成相事件择一；普通混匀不标机械化学 |
| 前处理 | 干燥/预烧/混合/球磨/压片 | 保留顺序与介质；无报告即 `NA` |
| 温度—时间 | 升温、峰值、保温、复烧 | 统一显示 °C、h/min，但保留原始程序顺序；不用近邻范围补 D0 |
| 气氛/体系 | 空气/O₂/N₂/还原气/气流、开放/封闭 | “开放体系”与气体组成分开记；一项未报告就写 `NA` |
| 坩埚 | 材质、加盖/密封、容器接触 | 与助熔副作用、挥发和污染评价连接；未报告即 `NA` |
| 助熔剂/矿化剂 | 种类、用量/比例、洗涤/分离 | 无外加助熔时写“无外加助熔”；信息不足写 `NA`，不得猜测 |
| 冷却/生长 | 冷却区间、速率、炉冷/淬冷、籽晶/提拉/退火 | 每个数值保留单位；只报“慢冷”时不换算速率 |
| 产物 | 粉体/陶瓷/单晶、产率/尺寸、主/杂相 | 产物形态、产率、纯度分子项；未报告子项写 `NA` |
| 验证 | SCXRD/CRED/PXRD/Rietveld/EDS/EDX/SEM/HT-XRD/热分析 | 写实际方法和它验证的对象；不从性能测量反推相纯 |
| 证据等级 | D0/D1/N1/P1 + strong/weak | 两轴并列，例如 `D1·strong`；不用“高/中/低”替代既定分级 |
| 缺失值 | `NA` 字段清单 | 单元格不留空白或破折号；末列汇总该行的 `NA` 字段，便于完整度审计 |

### 数值与溯源禁则

- 只转写对应 key 的原始实验段、表或图明示的数值；综述/二手摘要中的数值必须标二手层级，不可伪装成原始条件。
- 不做单位不明的换算，不由图形目测伪造精确值，不由总组成反解未报告的起始比，不由路线名称推测坩埚、气氛或冷却速率。
- D0 和近邻都允许出现 `NA`；`NA` 代表“当前允许证据包未暴露”，不代表“实验没有该步骤”。
- 表注必须完整写出：“D0 数值与 D1/N1/P1 数值分区；近邻数值不是 `Ba₅Y₁₂Zn[O(SiO₄)]₈` 已验证配方，不得类比补值。”

## Bank key 主引入 ownership

> 下表为了避免并行写作时遗漏 key，将 52 个 bank key 各指定一个“首次完整介绍”的主责 section。其他 section 仍须对自己的事实 claim 重复绑定相应 key，不得以“前文已引”代替 claim-cite 绑定。

| 主责 section | 主引入 bank keys |
|---|---|
| 01 身份与结构核验 | `ababaikeri2024ba5y12zn`, `kolitsch2009crystal`, `wierzbickawieczorek2017high`, `yamane2024synthesis`, `yamane2024microstructure`, `gulay2024navigation`, `motozawa2022bay16si4o33` |
| 02 证据距离分级 | `dolan2008structures`, `becerro2004revision`, `finger1995refinement`, `hazen1999crystal`, `tillmanns1978refinement`, `katscher1973the`, `zhong2020combining`, `yusa2007rhombohedral`, `buerger1954the`, `gorelova2016thermal`, `gu2025liba2gasi2o8`, `erlebach2020thermomechanical` |
| 03 路线变量矩阵 | `christensen1994investigation`, `lin1999phase`, `zou2021crystal`, `kerstan2012thermal`, `ababaikeri2024ba3zn4si4o15`, `cai2024optimized`, `zhao2026crystal`, `tejas2024structural`, `pires2001luminescence`, `pang2005study`, `leonyuk1999high`, `leonyuk1999crystal`, `giess1982zn2sio4`, `yldrm2009y2sio5`, `tzvetkov2001effects`, `alizadeh2021spectroscopy`, `shoudu1999czochralski`, `brandle1986czochralski`, `kerstan2015kristallphasen` |
| 04 近邻合成路线 | `redhammer2003beta`, `becerro2004revisiting`, `sun2014recent`, `felsche1973the`, `liu1993structures`, `kaiser2002crystal`, `thieme2022solid`, `aitasalo2006crystal`, `thieme2015ba1`, `kerstan2013bazn2si2o7`, `thieme2017variable`, `thieme2016negative`, `zou2019anti` |

Ownership 审计口径：4 组合计 51 个彼此独立的 key，无遗漏、无跨组重复。

## 全文汇合验收

1. **结构完整性**：7 个 section 顺序严格为“身份核验 → 证据距离 → 路线/变量条件矩阵 → 近邻路线 → 表征终点 → 失败边界 → 可迁移性与结论”；不加与主线竞争的宽泛背景节。
2. **标题完整性**：section/subsection 标题均为 2–6 词名词短语；枚举性细项降为 run-in paragraph，不出现三连并列标题或机关词堆叠。
3. **贡献完整性**：每节开头都明示与 contribution 候选 1/2/3 的对应；结论按相同次序回收；找不到贡献落点的段落直接删除。
4. **引用完整性**：只使用 citation bank/已过 ref gate 的 key；每个可查事实紧跟引用；目标每千词至少 8 次 citation calls，全文至少整合 46/51 个 key（≥90%）。
5. **证据强度**：D0 直接主张只由 `ababaikeri2024ba5y12zn` 承担；D1/N1/P1 只承担对应层级主张；weak bank 条目不升级为因果或目标相窗口结论；找不到支持时删除 claim 或明示降级，不手编 BibTeX。
6. **图文一致性**：图 1 只由第 2 节定义并解释证据距离/降权；图 2 只由第 3 节定义并解释路线—变量—验证；其他节只回指。caption 从 `figure_plan.md` 定稿起步，正文解释主线而不重述 caption。
7. **条件表一致性**：表 2 强制含原料、配比、路线、温度—时间、气氛、坩埚、助熔剂/矿化剂、冷却/生长、产物、验证、证据等级与缺失值 `NA`；D0、D1、N1/P1 三区视觉隔离；不作类比补值或跨文献拼配方。
8. **中文专业表达**：首次出现定义 D0/D1/N1/P1/X、SCXRD、CRED、PXRD、Rietveld 和 HT-XRD；化学式、价态、温度、时间与降温速率单位统一；避免“最佳/优化/成功”而无比较基准或相纯终点。
9. **篇幅与排版**：正文 8,000–9,300 汉字，预期 8–12 页；小于等于 4 个且每项很短的枚举改为段内 `(i)…; (ii)…`；只有每项为完整判断时才用显示列表。
10. **并行汇合**：每个 writer 只交付自己的 section 文件并声明非空产物；第 3 节为数值/表 2 唯一主责人，第 2/3 节分别为图 1/2 唯一主责人；公共 `main.tex`、BibTeX 和汇合修改留给后续单一汇合者。
