# 子主题 6–8 检索日志：位点替代、证据质量与可复现缺口

## 范围与定档

- 主题：`Ba5Y12Zn[O(SiO4)]8` 及具有明确晶体学关系的同构/同型、超结构或拓扑近邻。
- 切片：scope.md 子主题 6–8；不承担公共 coverage、BibTeX 导出或其他子主题。
- 档位：comprehensive；目标为每个切片子主题至少 15 篇强相关记录，但不以弱相关体系凑数。
- 纳入：原始合成/结构论文、可追溯的学位论文或专利、带可核验结构数据的权威记录；综述仅作谱系和滚雪球入口，合成事实回溯至原始来源。
- 排除：仅元素组成相近、无空间群/晶胞/SCXRD/PXRD-Rietveld/明确原型或拓扑关系证据的体系；纯计算预测；无法追溯来源的自动摘要。
- 年份：目标相和奠基近邻不限年份；2020–2026 用于结构修订、方法更新和独立复现。

## 执行记录

### 第 0 阶段：状态与边界

- `loopctl status`：round 1/5，stage `lit_search`，strict；`scope_confirmed=PASS`；open issue 0。
- 现有 `workspace/library/papers.jsonl`：0 条（开工统计）。
- 账本决策：`scale=comprehensive; slice=scope_subtopics_6_8`。
- 本日志是本切片唯一日志；将按本地语料、多源检索、滚雪球、边际收敛的顺序增量更新。

## 检索轮次

### 本地语料轮（private full-corpus）

| 查询式 | 返回/新增 | 来源与结果 | 说明 |
|---|---:|---|---|
| `Ba5Y12Zn` | 0/0 | local DuckDB-Parquet，15 分片 | 默认 30 s 超时；无命中不等于零结果。 |
| `Ba5Y12ZnSi8O40` | 0/0 | local DuckDB-Parquet，15 分片 | 延长至 90 s 仍超时。 |
| `Ba5Y12ZnO8(SiO4)8` | 0/0 | local DuckDB-Parquet，15 分片 | 延长至 90 s 仍超时。 |
| `Ba5Ln12Zn` | 0/0 | local DuckDB-Parquet，15 分片 | 延长至 90 s 仍超时。 |
| `O8(SiO4)8` | 0/0 | local DuckDB-Parquet，15 分片 | 延长至 90 s 仍超时。 |

本地轮边际新增为 0，但五次扫描均超时，故结论是“本地全文轮不完备”，不是“本地语料无相关文献”。后续以标识符/元数据多源检索补足，并在获得 DOI 后反向调用本地 DOI 索引读取正文证据。

### 多源检索轮 1

原生 `search_papers` 查询：`"Ba5Y12Zn" silicate crystal structure`，来源限定为
arXiv、OpenAlex、Semantic Scholar、Crossref、DBLP，`limit=15`。五个源均因沙箱
网络策略返回 `ConnectError: [Errno 1] Operation not permitted`，返回 0；该 0 不作
文献不存在的证据。随后按相同纳排标准切换至可访问的出版社/机构索引，并以 DOI、
题名、作者、年卷页交叉核验。

| 查询式（代表式；同义式仅作一次扩展） | 来源 | 本轮纳入 |
|---|---|---:|
| `"Ba5Y12Zn[O(SiO4)]8" crystal structure`、`D3NJ04480G` | RSC article/ESI、COD | 1 |
| `"Ba5.20Y13Si8O41" I-42m`、`"isotypic Ho analogue"` | DMG 2011 官方摘要册、维也纳大学活动页 | 2（会议原始报告、前序博士论文） |
| `"Ba5+xY13Si8O41" flux-grown` | Canadian Mineralogist/RRUFF 原文 | 1 |
| `"mixed-framework metal-Y silicates" flux 151` | ACS Cryst. Growth Des. | 1 |
| `BaxY26Si16O71+x 10.2 structure` | ACS Chemistry of Materials、Tohoku 机构页 | 1 |
| `BaxY26Si16O71+x planetary ball mill` | J. Ceram. Soc. Japan | 1 |
| `"Ba5Y13[SiO4]8O8.5" structure` | RSC Chemical Science 原文 | 1 |
| `BaY16Si4O33 Ba(SiO4)4 structure` | IUCr/Acta Cryst. E 原文 | 1 |

本轮发现并纳入 9 条。入库时共享库已有目标论文 1 条，本切片调用
`save_to_library` 去重后实际新增 8 条，库由 1 增至 9。核心标识符：
`10.1039/D3NJ04480G`、`10.3749/canmin.47.2.421`、
`10.1021/acs.cgd.6b01448`、`10.1021/acs.chemmater.4c00599`、
`10.2109/jcersj2.24080`、`10.1039/D4SC04440A`、
`10.1107/S2056989022011057`；2011 会议报告和 2007 博士论文无 DOI，保留其
官方来源信息，不虚构标识符。

### 滚雪球轮 2：从综述/目标 ESI 回到原始结构论文

种子按“高被引、最新、综述/汇总入口”分层：1999 年 BaZn2Si2O7 结构论文、
2017 年 151 组通量实验、2024 年目标论文与其 ESI、2024 年 Chemical Science
结构重定，以及 2021 年 framework-silicate 综述。综述只用于找谱系；结构和合成
结论均回到以下原始论文。原生 `snowball` 对
`10.1039/D3NJ04480G`、`10.1021/acs.cgd.6b01448`、
`10.1039/D4SC04440A` 三个种子均因 Semantic Scholar 网络受限返回空列表；改从
原文参考表、目标 ESI Table S4 和官方 forward-link/DOI 页面滚雪球。

| 查询/种子 | 原始来源 | 新纳入 | 结构纳入理由 |
|---|---|---:|---|
| 目标 ESI Table S4 → `BaMSiO4 stuffed tridymite` | JSSC 1993，`10.1006/jssc.1993.1013` | 1 | SCXRD/中子衍射证明 Co/Zn/Mg 同构系列及 kalsilite 超结构；仅作低阶超结构对照。 |
| 目标 ESI → `BaZn2Si2O7 phase transition` | JPCS 1999，`10.1016/S0022-3697(99)00004-9` | 1 | 中子+XRD/Rietveld 明确 LT `C2/c` 与 HT `Ccm2_1`。 |
| 目标 ESI → `Ba2ZnSi2O7 crystal structure` | Z. Krist. NCS 2002，`10.1524/ncrs.2002.217.1.25` | 1 | SCXRD、`C2/c`、低 R 值；不同拓扑，作相选择对照。 |
| 目标 ESI → `BaZnSi3O8 ZnSi4O16` | Chem. Eur. J. 2021，`10.1002/chem.202005170` | 1 | 同步辐射/实验室衍射；每个 ZnO4 角连四个 SiO4，直接对应目标的局部 `[ZnSi4O16]` 构筑单元。 |
| BaZn2Si2O7 refs → `BaZn2-xCoxSi2O7` | JSSC 2013，`10.1016/j.jssc.2013.09.003` | 1 | HT-XRD 跟踪 Zn/Co 位点替代与相变温度。 |
| BaZn2Si2O7 refs → `Ba1-xSrxZn2Si2O7` | Sci. Rep. 2015/2016，`10.1038/srep18040` | 1 | Ba0.6Sr0.4 晶体由 SCXRD+EDS 定量，直接比较 HT-BaZn2Si2O7。 |
| 上述论文 refs → `Ba0.5Sr0.5Zn2Si2-xGexO7` | Materials 2016，`10.3390/ma9080631` | 1 | HT-XRD 证明 Ge 替代保持 HT 结构至约 x=1，越界转为 LT 相。 |

本轮纳入 7 条。第二次工具入库发生时，共享库已被并行切片扩展至 48 条；本批
5 条已由 DOI 去重、2 条新增（JSSC 1993 的 DOI 完整记录及 Ge 替代论文），共享库
增至 50。这里的“新增”是本切片工具调用的物理新增数，不把其他切片的并发写入
算作本轮发现。

### 边际收敛轮 3

末轮用 `Ba3Zn4Si4O15 topology`、`BaZnSi3O8 based ceramics structure`、
`Ba1-xSrxZn2Si2O7 solid solution single crystal`、`BaZn2-xMxSi2O7 HT-XRD`、
`Ba Y Zn silicate superstructure` 做定向补漏，并核对 2011→2007、2021 综述→
1993/1999/2002 原始来源链。新增强相关记录为 0；命中均为已去重、性质导向后续
论文，或仅同元素而结构不同的体系。连续轮次新增为 9、7、0，已满足连续两轮
小于 10 的边际收敛条件；严格纳排下停止扩展，不用弱相关结果填充篇数。

comprehensive 数量目标在本窄题上未达到“每个子主题 15 篇独立强相关论文”：
经核验的核心/直接谱系 8 条、带明确衍射关系的局部拓扑或受控替代对照 8 条，
共 16 条证据记录（学位论文与会议原始报告分别计一条）。这是证据稀疏 WARN，
不改写公共 coverage gate；子主题 7–8 的质量/可复现判断复用同一批原始实验文献，
不把同一论文按三个子主题重复计数。

## 结构关系证据与纳排审计

### A 级：目标本身与近同晶胞 `I-42m` 家族

| 记录 | 晶体学/成相关系证据 | 合成与证据质量 | 缺口或限定 |
|---|---|---|---|
| Ababaikeri et al., NJC 2024, `D3NJ04480G` | SCXRD：四方 `I-42m` (No. 121)，a=18.7014(6), c=5.3640(2) Å；Zn 在 2b，局部 `[ZnSi4O16]`；ESI 有原子坐标、键长/BVS、EDS、实验 PXRD、CIF/COD 7063074。 | 高温溶液法、Pt 坩埚、开放体系；结构为多证据支持。 | 主文抓取返回 403，ESI 未给完整投料摩尔比、峰温保温/冷却曲线和产率；本轮不能可靠复述这些参数。 |
| Wierzbicka-Wieczorek et al., DMG 2011 | Ba5.20Y13Si8O41 与 Ho 类比物明确称 `isotypic`；二者均 `I-42m`，a≈18.93, c≈5.358 Å；SCXRD R(F)=2.49/1.76%，报告孪晶和占位。 | MoO3 flux，Pt/空气，1150 °C，2 K h−1 冷至 900 °C；小型无色棱柱。 | 会议摘要而非完整数据论文；相纯度、收率、完整原子表不足。 |
| Wierzbicka-Wieczorek 2007 博士论文 | 2011 报告及后续原始论文指向的前序合成/结构来源。 | 维也纳大学博士论文，186 页。 | 本轮未定位可直接读取的论文全文/馆藏记录；仅将其作为来源谱系节点，不从二手摘要增造参数。 |
| Kolitsch et al., Canadian Mineralogist 2009 | 在 BaKYSi2O7 合成中，SCXRD 识别伴生 Ba5+xY13Si8O41 无色棱柱。 | 给出完整批次：BaCO3/K2CO3/MoO3/Y2O3/SiO2，盖 Pt 坩埚，1150 °C 保温 3 h、2 K h−1 冷至 900 °C，水溶去 flux。 | 伴生相而非目标产物；不能据此假定对 Zn 目标同样最优。 |
| Wierzbicka-Wieczorek et al., CGD 2017 | 151 次 BaO-K2O-Y2O3-SiO2-MoO3 flux 实验，SCXRD/PXRD/Rietveld/SEM；相表含 Ba5+xY13Si8O41。 | 系统改变峰温、保温、冷却、MoO3、Y2O3/SiO2、坩埚/装填；Y2O3/SiO2 与 MoO3 是主要结构控制变量，慢冷改善晶体/产率。 | 完整“哪一批生成多少目标近邻”在 SI；本轮未直接取得 SI 表，具体批号不外推。 |
| Yamane et al., Chem. Mater. 2024 | 重审 2011 相：基本晶胞 a=18.9229(3), c=5.34880(10) Å；弱卫星峰揭示非公度复合结构，平均 `I-42m`、Ba/Y 分裂位点，精修 Ba10.22Y26Si16O81.22。 | 1600 °C 自助熔剂单晶；SCXRD 与陶瓷组分窗。 | “同一平均结构”不等于目标 Zn 相严格同型；卫星反射提示简单平均模型不足。 |
| Yamane et al., JCSJ 2024 | 同一 BaxY26Si16O71+x 相的行星球磨复现；PXRD 识别主/副相。 | x=9–14；BaCO3/Y2O3/SiO2，1300 °C×12 h 预烧、1600 °C×2 h 烧结。 | 行星球磨没有得到单相；与玛瑙研钵结果不同，作者指向玛瑙球/罐 SiO2 混入，是关键过程敏感性。 |
| Gulay et al., Chem. Sci. 2024 | Ba5Y13[SiO4]8O8.5：`I-42m`，a=18.92732(1), c=5.357307(6) Å；CRED、同步辐射 PXRD、中子 TOF、EDS 独立支持，CCDC 2352740。 | 1273–1573 K 探索，1573 K 隔离主相；报告玻璃/竞争相区。 | 论文未讨论 Zn 目标。下述关系是本轮跨文献推断而非原文主张。 |

**受限推断，不作为已证实同型声明：** Zn 目标与 Ba5Y13 家族同为空间群
`I-42m`、a≈18.7–18.93 Å、c≈5.35 Å。电荷/化学计量上，从
Ba5Y13Si8O40.5 到 Ba5Y12ZnSi8O40 可形式化为一个 Y3+→Zn2+ 并少 0.5 O/式量；
但现有论文未给二者的逐位点群-子群映射，也没有原位替代实验，故只能标为
“近同晶胞、可能的异价替代衍生关系”，不能写成已证明 isotypic。

### B 级：有直接衍射的局部拓扑/受控位点替代对照

| 记录 | 可用关系 | 不得外推的边界 |
|---|---|---|
| Liu & Barbier 1993, BaMSiO4 | Zn/Co/Mg 系列经 SCXRD/中子衍射证实同构并为 kalsilite 超结构，说明四面体位点同价替代可保持母拓扑。 | 该 stuffed-tridymite 三维骨架不是目标的 0D 混合构筑，不能称目标同型。 |
| Lin et al. 1999, BaZn2Si2O7 | LT `C2/c`↔HT `Ccm2_1` 的温变结构由中子/XRD 精修；给出热史控制相型的直接范例。 | 晶胞、维度和 Zn/Si 连通均与目标不同。 |
| Kaiser & Jeitschko 2002, Ba2ZnSi2O7 | SCXRD 确认 `C2/c` 新相，适合做 Ba/Zn/Si 竞争相识别。 | 只因同含 Ba/Zn/Si 不足以列为拓扑近邻，故仅保留为结构化相选择对照。 |
| Zou et al. 2021, BaZnSi3O8 | 同步辐射/实验室精修；一个 ZnO4 角连四个 SiO4，与目标 `[ZnSi4O16]` 局部单元直接相同。 | 整体是 feldspar-related `P21/a` 框架，局部基元相同不等于全局拓扑相同。 |
| Kerstan et al. 2013 | BaZn2−xCoxSi2O7 的 HT-XRD 显示 Zn/Co 替代维持系列且移动相变温度。 | 同价替代规律不能直接量化预测目标 Y/Zn 异价替代。 |
| Thieme et al. 2015/2016 | Ba1−xSrxZn2Si2O7 的 SCXRD+EDS 确证 A 位替代；Ba/Sr 与 Si/Ge 系列的 HT-XRD 给出结构保持区和相界。 | 是方法学/控制变量近邻，不是目标结构同型。 |
| Motozawa et al. 2022, BaY16Si4O33 | SCXRD；Ba(SiO4)4 孤立簇嵌于 Y–O 骨架，且被 2024 Chem. Sci. 用作混合框架端元比较。 | 无 Zn，且全局结构不同；只作构筑单元/拓扑端元。 |

### 条件对照与可复现缺口汇总（子主题 7–8）

1. **结构身份最强：** 目标有 SCXRD+CIF、PXRD、EDS、BVS；Ba5Y13 重审有
   CRED/同步辐射/中子/EDS。仅凭常规粉末峰位将两者并为同型不充分，尤其非公度
   卫星峰可能被实验室 PXRD 漏掉。
2. **相纯度/产率：** 目标 ESI 展示实验 PXRD 和 EDS，但未找到定量 Rietveld 相
   分数、产率、晶体挑选比例；2009 近邻是伴生相；2011 仅“小棱柱”描述。这些都
   不支持“高产、单相、可规模复现”的结论。
3. **热史对照：** 2009/2011 的 MoO3 flux、1150 °C、2 K h−1 是可复现基线；
   2017 系统实验表明 MoO3 与 Y2O3/SiO2 比的窗口效应和慢冷收益，且过多 MoO3
   反而抑制结晶。目标 Zn 相缺少公开的成分/热史参数矩阵。
4. **工艺敏感性：** 2024 球磨/玛瑙研钵对照显示微量 SiO2 污染即可改变
   BaxY26Si16O71+x 的单相窗口；因此研磨介质、坩埚材质/盖合、挥发损失与实际
   批后组成均应记录，不能只给名义配方。
5. **位点替代证据缺口：** 现有 Zn 目标是一个终点结构，没有 Y/Zn 梯度、原位
   PXRD/DSC、占位随 x 的精修或相图；“Y→Zn+氧空位”目前是计量推断，不是已
   测得的固溶机制。
6. **独立复现：** 2024 Chem. Sci. 对无 Zn 的 Ba5Y13 相提供独立多探针重定，
   但没有发现独立团队重复合成并结构精修 `Ba5Y12Zn[O(SiO4)]8`。这是目标相最
   重要的外部可复现空白。

## 明确排除

- 目标 ESI Table S4 中仅为元素/维度比较的 ZnSiO3 多型、普通 Y2SiO5/Y2Si2O7、
  Ba2SiO4 等，若无逐位点、原型或局部构筑单元对应，不纳入本切片核心集合。
- `Ba3Zn4Si4O15`（`10.1002/zaac.202400026`）：虽同作者且同为 Ba–Zn–Si，
  但为 `C2/c`、含独立 SiO4/Si2O7 和 ZnO4；未见目标拓扑映射，按“仅元素相近”
  排出核心/替代集合。
- Chem. Sci. 同文的 `Ba3Y2[Si2O7]2`：原文归为另一已知磷酸盐原型的超结构，
  不是 Ba5Y13/目标家族；只作为竞争相背景，不计近邻。
- 仅报告介电/发光/NLO 性能而无新结构精修或位点占据证据的掺杂陶瓷、玻璃、
  供应商页面、数据库自动“相似论文”均排除。
- ResearchGate、题录聚合和搜索摘要仅作发现入口；有原始出版社/机构源时不作为
  结构或合成事实的最终证据。

## 错误与降级路径

- 本地 DuckDB-Parquet 对所有五个精确/家族式查询均在 30–90 s 截止；保留 `timed_out=true`，降级为多源元数据发现 + DOI 反查本地全文。
- 本地 `lookup_local_doi` 对目标、Chem. Sci. 2024、Chem. Mater. 2024、JCSJ 2024
  均 `found=false`；这是本地 DOI 索引缺口，不代表文献不存在。
- 原生 arXiv/OpenAlex/Semantic Scholar/Crossref/DBLP 多源检索均被沙箱网络策略
  拒绝；保留逐源错误，不将 0 返回写成检索阴性。
- 三个滚雪球种子的 Semantic Scholar 调用均被同一网络策略拒绝；使用原文参考表、
  ESI、出版社 forward links 和 DOI 官方落地页替代。
- RSC 目标主文 HTML/PDF 抓取返回 403，但官方 ESI 可读；因此仅记录 ESI/官方
  摘要明确支持的参数，未凭相似论文补写目标具体投料和热程。
- 共享 `papers.jsonl` 有并行写入：开工为 0，本切片首批保存前已出现目标 1 条，
  首批工具新增 8；第二批保存前共享库为 48，新增 2，完成时共享总量 50。所有
  本切片新增均经 `save_to_library` 写入；未直接编辑 JSONL。

## 完成状态

- 已完成：本地语料、多源检索、综述/目标 ESI 到原始来源滚雪球、两轮边际收敛、
  结构关系分级、排除审计和可复现缺口归纳。
- 未执行（按任务边界）：`export_bibtex`、`references.bib` 写入、公共 coverage。
- 本日志是本切片唯一日志；papers 仅通过检索工具去重入库。
