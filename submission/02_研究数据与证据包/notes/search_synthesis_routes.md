# 子主题 4–5 检索日志：固相/陶瓷与单晶/助熔路线

## 任务边界与状态

- 日期：2026-08-31（Asia/Shanghai）
- 档位：`comprehensive`
- 主题：`Ba₅Y₁₂Zn[O(SiO₄)]₈` 及有明确晶体学结构近邻证据的化合物。
- 唯一负责范围：scope.md 子主题 4（固相与陶瓷路线）和 5（晶体生长及助熔路线）。
- 重点字段：原料与预处理、名义/实际配比、研磨/压片、温度—时间程序、气氛、坩埚、复烧、自熔/助熔剂及熔体组成、最高温度与保温、降温速率、籽晶/成核、洗涤/分离、冷却方式、产物形态及 PXRD/SCXRD/Rietveld/元素分析等表征。
- 纳入：原始论文、学位论文、专利、结构报告/权威晶体记录；二手来源只作滚雪球线索。
- 排除：无晶体学证据的仅元素组成相近体系；仅计算预测；不可追溯聚合摘要；与目标结构无关的玻璃/玻璃陶瓷/掺杂基质。
- 状态基线：`loopctl status` 显示 round 1/5、stage `lit_search`、`scope_confirmed=PASS`、open issue 0；开工时 `papers.jsonl` 不存在。
- 本地语料：`private-full-corpus`，DuckDB-Parquet，15 个 Parquet 文件，schema 完整；并非公开精简包。

## 记号变体策略

不把任一式子凭记忆改写成“规范式”。下列字符串仅作为并列检索入口；是否同一相必须由命中来源中的标题、结构式、组成、晶胞/空间群或 DOI 交叉核验：

1. `Ba5Y12Zn[O(SiO4)]8`
2. `Ba5Y12ZnO(SiO4)8`
3. `Ba5Y12Zn[SiO4]8O`
4. `Ba5Y12Zn(SiO4)8O`
5. `Ba5Y12ZnSi8O33`
6. `Ba5Y12ZnO33Si8`
7. `Ba₅Y₁₂Zn[O(SiO₄)]₈`
8. 文字变体：`barium yttrium zinc orthosilicate`、`barium yttrium zinc silicate`

## 预定关键词矩阵

### 子主题 4：固相/陶瓷

- S4-Q1：目标式各变体 + `synthesis` / `preparation`
- S4-Q2：目标式各变体 + `solid state` / `solid-state reaction`
- S4-Q3：文字名称 + `ceramic` / `sintering` / `calcination`
- S4-Q4：结构近邻/同型线索 + `powder X-ray` / `Rietveld` / `phase formation`
- S4-Q5：已确认种子的 DOI/题名 + 原料、温度、时间、气氛等全文字段词

### 子主题 5：单晶/助熔

- S5-Q1：目标式各变体 + `single crystal` / `crystal growth`
- S5-Q2：目标式/文字名称 + `flux` / `self-flux`
- S5-Q3：文字名称 + `melt` / `crucible` / `cooling rate`
- S5-Q4：结构报告/同型线索 + `single-crystal X-ray diffraction`
- S5-Q5：已确认种子的 DOI/题名 + `flux composition` / `decant` / `washed` / `furnace cooled`

## 轮次记录

### 预检

- `loopctl log` 首次漏传 `--stage` 与 `--agent`，CLI 拒绝写入；已按帮助信息补齐参数并成功记录 `scale=comprehensive` 决策。未影响检索或产物。

### 第 0 轮：本地全文语料

来源：私有全文语料 `private-full-corpus`（DuckDB-Parquet，15 shards）。均使用 `max_results=10`、`context_lines=1`、不区分大小写、literal 模式、30 s 超时。

| 查询式 | 返回 | 边际新增 | 直接证据 | 错误/解释 |
|---|---:|---:|---|---|
| `Ba5Y12Zn` | 0 | 0 | 0 | `timed_out=true`；扫描约 10% 即超时 |
| `Ba₅Y₁₂Zn` | 0 | 0 | 0 | `timed_out=true`；扫描约 10% 即超时 |
| `barium yttrium zinc silicate` | 0 | 0 | 0 | `timed_out=true`；扫描约 9% 即超时 |

本轮没有文献路径/行号可记录。三个结果都不是完成扫描后的零命中，故不能据此声称本地语料没有目标相；转入多源 API，并计划在获得 DOI/题名后用 `lookup_local_doi` 或更窄的题名片段回查直接证据。

### 第 1 轮：MCP 多源精确式检索

每式调用来源 `arxiv,openalex,semanticscholar,crossref,dblp`，`limit_per_source=15`，不限年份（目标相与奠基近邻不限年份）。

| 查询式 | 合并返回 | 入库新增 | 来源错误 |
|---|---:|---:|---|
| `Ba5Y12Zn` | 0 | 0 | arXiv、OpenAlex、Semantic Scholar、Crossref、DBLP 均为 `ConnectError: [Errno 1] Operation not permitted` |
| `Ba5Y12ZnSi8O33` | 0 | 0 | 同上 |
| `"barium yttrium zinc" silicate` | 0 | 0 | 同上 |

本轮 15 个单源请求全部因当前进程网络权限失败，不等价于各数据库零结果。按 skill 的“单源报错不终止、换源继续”规则，后续改走可用的网页检索通道，优先出版社、DOI 落地页、学位论文库、结构数据库与 Google Scholar 可索引片段；得到标识后再用精确元数据/本地 DOI 路由核验。此轮只有错误记录，无直接证据、无仅元数据记录。

### 第 2 轮：网页多源精确检索与记号变体

可用来源：RSC、Wiley、Elsevier/ScienceDirect、IUCr、ACS/DOI 落地页、IBM Research、HERO、大学机构库（Jena、Sakarya、Canterbury）、COD/结构记录、出版社可索引全文及原始论文 PDF。下表记录本轮**全部实际检索式**；同一检索式因搜索引擎分页/重试产生的重复请求不另计。

| 组 | 实际检索式（逐条以 `；` 分隔） | 去重后边际新增 | 证据层级 |
|---|---|---:|---|
| 目标式精确/变体 | `"Ba5Y12Zn"`；`"Ba5Y12ZnSi8O33" OR "Ba5Y12ZnO(SiO4)8"`；`"Ba₅Y₁₂Zn" silicate`；`"barium yttrium zinc" silicate crystal` | 1 | 目标原始论文；直接确认方法类别与 SCXRD，详细配方缺失 |
| 目标实验字段 | `"Ba5Y12Zn[O(SiO4)]8" synthesis platinum crucible temperature`；`"Ba5Y12Zn[O(SiO4)]8" "Pt crucible"`；`"D3NJ04480G" synthesis temperature flux`；`"D3NJ04480G" "BaCO3"`；`"Ba5Y12Zn[O(SiO4)]8" BaCO3 Y2O3 ZnO SiO2`；`"Ba5Y12Zn[O(SiO4)]8" 1000 1100 1200`；`"Ba5Y12Zn[O(SiO4)]8" cooled`；`"Ba5Y12Zn[O(SiO4)]8" molar ratio`；`site:pubs.rsc.org D3NJ04480G experimental crystal reagents`；`site:pubs.rsc.org D3NJ04480G articlepdf` | 0 | 只重复命中 RSC 摘要、作者页/聚合片段；未获得可核验的配比、温度或冷却程序 |
| 目标补充/结构库 | `"d3nj04480g1.pdf"`；`"D3NJ04480G" supplementary information`；`COD "Ba5Y12Zn"`；`"Ba5 O40 Si8 Y12 Zn"` | 2 个证据载体、0 篇新论文 | ESI 为直接结构/EDS/PXRD证据；COD 为结构元数据 |
| Ba–Zn–Si 结构近邻 | `"BaZnSiO4" Liu Barbier 1993 synthesis`；`"Structures of the stuffed tridymite derivatives" DOI`；`"BaZn2Si2O7" Lin 1999 synthesis`；`"Phase transition and crystal structures of BaZn2Si2O7"`；`"Ba2ZnSi2O7" Kaiser Jeitschko synthesis`；`"Crystal structure of the new barium zinc silicate Ba2ZnSi2O7"`；`"BaZnSi3O8" Zou experimental`；`"Crystal Structure and Ferroelectric Evidence of BaZnSi3O8" experimental`；`"Ba3Zn4Si4O15" synthesis`；`"Ba3Zn4Si4O15" supplementary` | 5 | 3 篇有直接程序字段，2 篇仅结构/方法元数据 |
| Ba–Zn–Si 固相扩展 | `"Ba2ZnSi2O7" solid-state temperature crucible`；`"BaZn2Si2O7" solid state BaCO3 ZnO SiO2`；`"BaZnSiO4" solid state synthesis`；`"Thermal expansion of Ba2ZnSi2O7, BaZnSiO4" DOI authors`；`"Anti-reductive characteristics and dielectric loss mechanisms" DOI`；`"10.1016/j.ceramint.2019.06.195" authors`；`"19415-19419" Ba2ZnSi2O7 authors`；`"Structural, thermal, and optical spectroscopic studies of Sm3+-doped Ba2ZnSi2O7"`；`"10.1039/d4ma00926f" authors synthesis`；`"Luminescence of Europium(III) and Manganese(II) in Barium and Zinc Orthosilicate"` | 5 | 4 篇直接实验字段，1 篇摘要级路线 |
| Ba–Zn–Si 助熔/晶体 | `"barium zinc silicate" single crystal flux`；`"Zn2SiO4 crystal growth from molten solutions" DOI`；`"Zn2SiO4 crystal growth" Pb2ZnSi2O7 flux cooling rate` | 1 | 原始论文机构页直接给熔体、温区、降温率及成分分析 |
| Y–Si–O 单晶/助熔 | `"Y2SiO5" single crystal growth flux crucible cooling rate`；`"Y2Si2O7" flux growth platinum crucible`；`"Study on the growth, etch morphology and spectra of Y2SiO5 crystal"`；`"High-temperature crystallization and X-ray characterization of Y2SiO5" DOI authors`；`"Crystal Growth and Structural Refinements of the Y2SiO5, Y2Si2O7"`；`"β-Y2Si2O7, a new thortveitite-type compound" DOI authors`；`"Czochralski growth of rare-earth orthosilicates-Y2SiO5"`；`"Shoudu" "Czochralski growth" Y2SiO5 1999 authors`；`"Czochralski growth of rare-earth orthosilicates (Ln2SiO5)"` | 7 | 6 篇直接或部分直接程序字段；1 篇重复版本只作独立结构报告元数据 |
| 学位论文/机械活化 | `site:ir.canterbury.ac.nz Yashar Alizadeh PhD thesis Y2SiO5 title`；`"Spectroscopy and crystal field analysis" "iridium crucible"`；`"Y2sio5 Tozu Üretimi Ve Plazma Sprey Tekniği İle Kaplanması"`；`"Effects of Mechanochemical Treatment on Yttrium Oxyapatite Formation"`；`"Kristallphasen mit hoher Wärmedehnung" Kerstan 2015`；`"Kristallphasen mit hoher Wärmedehnung" Ba2ZnSi2O7 1475` | 4 | 3 篇学位论文/机构全文、1 篇原始机械活化论文；均含路线字段或相纯度警示 |

本轮第一条目标论文经 `save_to_library` 入库：`before=0, added=1, total=1`。随后共享库有其他并行子任务的合法新增；本子任务再次调用检索入库工具时为 `before=50, added=13, total=63`。因此本子任务可归属的新增是 **14 条**，不能把共享库其余条目计入本轮边际新增。对 6 条已有 DOI 记录的路线证据补录为 `before=63, added=0, total=63`（去重后原位补空字段），不算新增。

### 第 3 轮：从目标 ESI 与种子题录做滚雪球

#### 3.1 自动 DOI 引文扩展

对下列种子分别调用 `snowball(direction=both, limit=30)`：

1. `10.1039/D3NJ04480G`（目标相）
2. `10.1016/S0022-3697(99)00004-9`（BaZn₂Si₂O₇）
3. `10.1002/chem.202005170`（BaZnSi₃O₈）
4. `10.1016/S0022-0248(99)00233-X`（Y₂SiO₅/Y₂Si₂O₇ 生长）

四个种子均因 Semantic Scholar 网络权限错误 `Errno 1 Operation not permitted` 返回空引用/被引；OpenAlex DOI 兜底未定位出记录，故自动滚雪球边际新增 0。此处空列表不解释为“无引用”。

#### 3.2 可核验的人工后向/前向滚雪球

- 目标 ESI 的结构对比表 S4 直接列出 BaZnSiO₄、BaZn₂Si₂O₇、Ba₂ZnSi₂O₇、BaZnSi₃O₈、Y₂SiO₅ 与 Y₂Si₂O₇ 多晶型，并给出相应文献 26–29；这些是纳入近邻的晶体学依据，不是凭元素相似度扩展。
- 由文献 26–29 得到 1993 BaMSiO₄、1999 BaZn₂Si₂O₇、2002 Ba₂ZnSi₂O₇、2021 BaZnSi₃O₈ 四个原始种子；继续由其题名/参考文献检索到 2012 三种 Ba–Zn 硅酸盐热膨胀/制备论文、2019 气氛对 Ba₂ZnSi₂O₇ 的研究以及 2024 Ba₃Zn₄Si₄O₁₅。
- Y₂SiO₅/Y₂Si₂O₇ 路线由 1999 高温结晶论文向后得到 1986/1999 Czochralski 生长与 2003 Na₂MoO₄ 助熔结构报告，向前找到 2005 无掺杂 Y₂SiO₅ 生长论文与 2021 学位论文。
- 前向检索还命中 2024 `Ba₃Zn₄Si₄O₁₅` 和 2024/2025 Ba₂ZnSi₂O₇ 固相表征论文；去重后人工滚雪球的**边际新增为 12 条**，其中 8 条可读实验程序、4 条仅题录/方法摘要。它们已包含在上节 14 条本子任务入库新增中，不重复计数。

滚雪球边际趋于饱和：目标结构表首轮带来 4 个 Ba–Zn–Si 原始种子，第二轮新增 5 条可用路线，第三轮 Y–Si–O 生长链新增 7 条；最后一轮用相同 DOI 加字段词主要返回重复记录，新增降为 0，故停止无差别扩展。

## 直接证据记录（可抽取路线字段）

下表只写来源原文可直接支持的内容；`未见` 表示当前可访问正文/补充材料没有给出，绝不补猜。

| 相/文献 | 原料与配比/前处理 | 温度—时间、气氛、容器、冷却 | 产物与表征 | 证据来源 |
|---|---|---|---|---|
| `Ba5Y12Zn[O(SiO4)]8`, DOI `10.1039/D3NJ04480G` | 目标原始论文可访问摘要未见原料/配比 | 高温溶液法、开放体系；温度、时间、坩埚、助熔剂、冷却未见 | 单晶；SCXRD；ESI 有 EDS、实验 PXRD、结构表 | RSC 原始论文落地页 + ESI；部分直接 |
| `BaZn2Si2O7`, DOI `10.1016/S0022-3697(99)00004-9` | BaCO₃、ZnO、SiO₂ 按化学计量比，充分混合；需中间研磨 | 1280 °C；时间、气氛、坩埚、冷却未见 | 白色多晶粉；PXRD、中子衍射、GSAS/Rietveld；相变约 250–305 °C | Elsevier 原始论文实验段 |
| `BaZnSi3O8`, DOI `10.1002/chem.202005170` | BaCO₃ 99.8%、ZnO/SiO₂ 99.5%；聚乙烯罐、ZrO₂ 球、去离子水球磨 5 h；85 °C 干燥；150 MPa 压片 | 空气中 1000 °C/3 h 煅烧，5 °C min⁻¹；1090–1120 °C/3 h 烧结；2 °C min⁻¹ 冷至 1000 °C 后随炉冷却 | 陶瓷；实验室 XRD、同步辐射 XRD/Rietveld、介电/铁电 | 原始论文 PDF |
| `Ba2ZnSi2O7`, DOI `10.1016/j.jssc.2012.01.055` | SiO₂ 石英粉、BaCO₃、ZnO；球磨；同文另用镁碳酸盐氢氧化物水合物 | Ba–Zn 相 1250–1475 °C/2–8 h；固溶体 1200–1360 °C/5–8 h；冷后再球磨；气氛/坩埚/冷速未见 | 多晶；HT-XRD、膨胀仪 | 原始论文 PDF |
| `Ba2ZnSi2O7`, DOI `10.1016/j.ceramint.2019.06.195` | BaCO₃ 99.8%、ZnO/SiO₂ 99.5%；聚乙烯罐、ZrO₂ 球、去离子水球磨 5 h | 空气中 1100 °C/3 h 煅烧；随后分别在 air/O₂/N₂（1200 °C）和 N₂–1 vol% H₂（1125 °C）烧结；后者出现 BaSiO₃，归因于 Zn 损失 | 陶瓷；XRD、XPS、微波介电/电化学 | Elsevier 原始论文实验段 |
| `Ba2ZnSi2O7:Sm3+`, DOI `10.1039/D4MA00926F` | BaCO₃ 99%、ZnO/SiO₂ 99%、Sm₂O₃ 99.9%；乙醇中玛瑙研钵研磨 1 h | 氧气、氧化铝坩埚、1200 °C/6 h、5 °C min⁻¹；自然冷却至室温后研磨 | 粉体；XRD、FTIR、SEM/EDS、热/光谱 | RSC 开放原始全文 |
| `BaZnSiO4:Eu,Mn`, DOI `10.1021/cm000063g` | 氧化物/碳酸盐，或 Ba₂SiO₄:Eu 与 Zn₂SiO₄:Mn 前驱体 | 固相反应；可访问摘要未给温度、时间、容器、冷却 | 粉体；PXRD、IR、UV–vis/发光 | ACS 题录/原始摘要；仅部分直接 |
| `Zn2SiO4`, DOI `10.1016/0022-0248(82)90092-6` | 熔体 `5 Zn2SiO4 + 3 Pb2ZnSi2O7`；以氟化物供 Zn 可改善晶体 | 1300→960 °C，1 °C h⁻¹；坩埚/保温/分离未见 | 数毫米六方柱；化学分析和浮力密度给出来源所报 `Zn1.96Si1.04O4.04`，不改写 | IBM 原始论文记录 |
| `β-Y2Si2O7`, DOI `10.1107/S0108270103018869` | Na₂CO₃/Y₂O₃/SiO₂ 按 NaYSi₂O₆ 配比；与 Na₂MoO₄ 助熔剂按营养物:助熔剂=1:10 | 有盖 Pt 坩埚；缓慢升至 1473 K、保温 24 h；2 K h⁻¹ 冷至 673 K；沸水溶去助熔剂 | 无色立方状 β-Y₂Si₂O₇，伴 Na₂Si₂O₅ 片晶和 Y 硅酸盐氧磷灰石；SCXRD 100/280 K | IUCr 原始结构报告全文 |
| `Y2SiO5`, DOI `10.1016/j.matlet.2005.06.036` | Y₂O₃ 99.999%、SiO₂ 99.99%，约 980 g、化学计量比；刚玉研钵混磨、液压压块；1200 °C/24 h 得单相炉料 | RF 加热 Czochralski；Ir 坩埚 80×60 mm；高纯 N₂；可访问段未完整显示拉速/转速/冷却 | 单晶；取向/抛光、光学显微、SEM、吸收光谱 | Elsevier 原始论文全文段 |
| `Y2SiO5/Y2Si2O7`, DOI `10.1016/S0022-0248(99)00233-X` | Czochralski 炉料为高纯 Y₂O₃/SiO₂（Cr 掺杂系列）；助熔路线使用 Li/K 二、三钼酸盐 | HF 加热 Ir 坩埚约 80×90 mm；Czochralski 推荐拉速 2.0–2.5 mm h⁻¹；助熔条件的精确批料/冷程当前只见方法摘要 | YSO 大晶体及自发成核的 YSO/Y₂Si₂O₇；电子探针、XRD/结构精修 | 原始论文可索引实验段 + 权威题录 |
| `Y2SiO5`, DOI `10.1016/S0022-0248(98)00553-3` | ≥99.99% 原料；因 SiO₂ 挥发使用富 SiO₂ 熔体或相对化学计量组成最多 0.2% 的偏移（按原文表述，不自行改正方向） | RF 加热 Ir 坩埚、Czochralski；可访问段未完整显示拉速/转速/气氛/冷却；生长后退火 20 h | 约 35 mm×130 mm、460–486 g YSO/Eu:YSO；显微观察 Ir 夹杂 | Elsevier 原始论文全文段 |
| Y–Si–O 机械活化，DOI `10.1023/A:1013293329770` | Y₂O₃/SiO₂=7/9，空气中细磨；另比较含水氧化钇 | 加热 `T>1000 °C`；具体时间/容器/冷却未见 | 固相反应总得到 Y₂SiO₅、Y₂Si₂O₇、氧磷灰石混相；XRD/IR/热分析 | 原始论文题录与摘要 |
| Y₂SiO₅ 硕士论文（Yıldırım, 2009） | LiYO₂ 添加剂，固–液相烧结 | 仓储页未给完整温程；全文为后续精读入口 | Y₂SiO₅ 粉体；光学显微、XRD、SEM-EDS；随后等离子喷涂 | Sakarya 机构论文库；摘要直接、细节待全文定位 |

## 仅元数据/结构关系记录

这些记录可证明文献存在、方法类别或近邻关系，但当前没有足够直接实验文本，不与上表混写：

- `BaZnSiO4`：Liu & Barbier, 1993, *Structures of the Stuffed Tridymite Derivatives, BaMSiO4 (M = Co, Zn, Mg)*。SCXRD/粉末中子结构种子；未取得合成温程。
- `Ba2ZnSi2O7`：Kaiser & Jeitschko, 2002, DOI `10.1524/ncrs.2002.217.1.25`。结构报告；未取得坩埚/温程。
- `Ba3Zn4Si4O15`：DOI `10.1002/zaac.202400026`。开放空气高温溶液法与 SCXRD 可确认；补充 PDF 被 Wiley 拒绝访问，批料/最高温度/冷程未知。
- `Y2SiO5/Y2Si2O7/LaBSiO5` 的 *Crystal Growth and Structural Refinements...*，DOI `10.1002/(SICI)1521-4079(199911)34:9<1175::AID-CRAT1175>3.0.CO;2-2`：独立题名/DOI 的结构精修记录，疑与同年 JCG 数据链高度重合，写作时需防重复计数。
- Kerstan 2015 博士论文：确认覆盖 Ba₂ZnSi₂O₇/BaZnSiO₄ 制备、相稳定和 HT-XRD；可从全文读到相稳定温区，但未把论文中玻璃陶瓷的一般内容扩入本任务。
- Alizadeh 2021 博士论文，DOI `10.26021/12446`：机构库确认 Y₂SiO₅ 稀土掺杂晶体及生长章节；作为 Czochralski 操作的补充记录，不替代原始生长论文。
- COD 搜索结果将目标结构记录显示为 `Ba5 O40 Si8 Y12 Zn`（COD 7063074）。该字符串与论文题名的目标式并列保留为数据库原样元数据，未凭记忆将其“更正”或据此另立化学相。

## 错误、访问限制与缺失字段

1. 本地三次宽字符串扫描均在约 9–10% 处超时；因此没有本地全文命中，不能下零命中结论。目标 DOI 的 `lookup_local_doi('10.1039/D3NJ04480G')` 明确返回 `found=false`。
2. MCP 五源检索的 15 个请求以及四个自动 snowball 种子均受当前网络权限限制；已原样记录，未伪装成数据库零结果。
3. RSC 目标主文实验段在当前通道未被索引；ESI 只有结构、EDS、PXRD等，不含可见的合成批料与炉程。第三方作者页虽出现“Pt crucible”片段，但因不能回到实验原文，未作为直接字段采信。
4. Wiley 的 `zaac202400026` 补充文件地址可定位但返回访问拒绝；只保留出版社摘要确认的“open-air high-temperature solution”，不补配方。
5. 部分 ScienceDirect 页面只暴露章节片段；表中凡片段截断之字段一律标 `未见`，不利用同课题组常见做法外推。
6. 没有导出 `references.bib`，没有生成或修改公共 coverage；所有 `papers.jsonl` 写入均由 `save_to_library` 检索入库工具完成。

## 本子任务结论与停止条件

- 目标相本身：只确认开放体系高温溶液法与 SCXRD；精确配方、坩埚、最高温度、保温和降温仍是明确证据缺口。
- 固相/陶瓷：对 BaZn₂Si₂O₇、BaZnSi₃O₈、Ba₂ZnSi₂O₇、BaZnSiO₄ 及 Y–Si–O 近邻获得从原料到烧结/冷却和 PXRD/Rietveld 的多条直接路线；气氛对 Zn 挥发/副相的对照是可复现实验的重要边界。
- 单晶/助熔：获得 Na₂MoO₄–Pt 的 Y₂Si₂O₇ 全程序、Zn₂SiO₄–Pb₂ZnSi₂O₇ 的完整冷却窗口，以及 Y₂SiO₅ 的 Ir–N₂ Czochralski 炉料与生长参数。
- 最后一轮精确 DOI + 字段词只返回重复项，自动引文源又受权限阻断；在综合档的本地、多源、后向/前向滚雪球均已执行且边际新增降为 0 后停止。
