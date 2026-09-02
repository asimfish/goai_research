# 文献检索日志：身份、结构基线与结构谱系（子主题 1–3）

## 任务边界与档位

- 主题：`Ba₅Y₁₂Zn[O(SiO₄)]₈` 及其结构相近化合物。
- 唯一职责：①身份与记号核验；②目标相结构基线；③结构近邻判据与谱系。
- 档位：`comprehensive`（正式综述档）。目标相与奠基性近邻不限年份；2020–2026 用于结构修订与新近相关体系。
- 纳入：有可追溯来源及明确晶体学证据的目标相、同构/同型/等结构/超结构/同拓扑/固溶体或明确结构派生物。
- 排除：仅元素或组成相似而无晶体学近邻证据者、纯计算预测且无实验结构者、不可追溯聚合摘要、无关玻璃/玻璃陶瓷或仅性能研究。
- 并行限制：只用检索工具并发安全地写 `workspace/library/papers.jsonl`；本切片不导出/手编 BibTeX，不运行 coverage 汇总，不写其他切片日志。

## Dispatch

- 状态：已派发并开始。
- 开始账本状态：`round=1/5`，`stage=lit_search`，`scope_confirmed=PASS`，开放 issue 为 0。
- 基线库规模：待检索工具初始化后记录。

## 检索阶段记录

### 阶段 0：本地语料优先

1. `local_corpus_status()`：`ok=true`；引擎 `duckdb-parquet`；模式 `private-full-corpus`；15 个 Parquet 分片；根目录 `/mnt/nas/data/gaojing/markdown_corpus_v1/packages/markdown-v1-final`；schema 完整；不是 synthetic/public compact 数据。
2. 精确式查询 `Ba5Y12Zn`：`max_results=10`、`context_lines=1`、literal、case-insensitive，120 秒超时。结果 `ok=false`、`total_returned=0`、`timed_out=true`、`truncated=false`，未取得路径/行号/DOI。
3. 错误与处置：第一次默认 30 秒调用在 DuckDB 扫描期间未产生最终结果；随后显式以 120 秒复核，仍在读取约 26% 分片时由工具超时并返回上述结构化错误。由于精确目标式尚且无法在预算内完成，未对近义词反复无差别扫描 NAS；转用 DOI/API 多源检索补全。此处“0 条”是超时后的返回数，不解释为本地库不存在相关文献。

### 阶段 1：多源关键词矩阵

#### 轮次 K1：目标式精确核验（不限年份）

- 项目多源工具调用：`Ba5Y12Zn SiO4 crystal structure`；sources=`arxiv,openalex,semanticscholar,crossref,dblp`；每源上限 15。五源均报 `ConnectError: [Errno 1] Operation not permitted`，返回 0；`save_to_library` 为 `before=0, added=0, total=0`。该错误表示本执行沙箱禁网，不表示来源无记录。
- 子主题 1 的 4 组检索式：`"Ba5Y12Zn" silicate crystal structure`；`"Ba5Y12ZnSi8O40" crystal`；`"BYZSO" silicate`；`"10.1039/D3NJ04480G"`（另用 `"Ba5 O40 Si8 Y12 Zn"` 交叉核对数据库展开式）。
- 子主题 2 的 4 组检索式：`"Ba5Y12Zn[O(SiO4)]8" space group lattice`；`"Ba5Y12Zn[O(SiO4)]8" CIF`；`"[ZnSi4O16]" silicate structure`；`"I-42m" "ZnSi4O16"`。
- 子主题 3 的 4 组检索式：`"Ba5Y12Zn[O(SiO4)]8" isostructural OR isotypic`；`"Ba5Ln12Zn" silicate`；`"Ba5RE12Zn" silicate`；`"Ba5Y12ZnSi8O40" related structure`。
- API 工具禁网后的替代来源：外部检索通道命中 RSC 出版者页、RSC ESI、Crystallography Open Database（COD）及二手聚合页；真实条目仅以出版者/COD/原始论文信息核验。目标论文为 Ababaikeri 等，2024，*New Journal of Chemistry* 48, 3594–3602，DOI `10.1039/D3NJ04480G`。该记录经 `save_to_library` 合并时为 `before=1, added=0, total=1`，说明并发 agent 已先写入同 DOI，幂等去重生效；本切片不重复计新增。
- 身份/结构命中路径：RSC 出版者页 → DOI；RSC ESI → 原子坐标、BVS、键长和 ICSD 比较表；COD → `COD 7063074`、展开式 `Ba5 O40 Si8 Y12 Zn`、空间群 `I -4 2 m`、晶胞 `18.7014, 18.7014, 5.364 Å`。出版者给出规范括号式 `Ba5Y12Zn[O(SiO4)]8`、别名 `BYZSO`、四方晶系、非中心对称空间群 `I-42m`（No. 121）、`a=18.7014(6) Å, c=5.3640(2) Å`，以及孤立 `[ZnSi4O16]` 与 `[SiO4]` 单元。
- 结构近邻精确式只返回目标论文/ESI/COD，未检出 `Ba5Ln12Zn...` 或 `Ba5RE12Zn...` 的已报道等结构替代物。暂不能据此断言不存在，下一阶段从目标论文的原始参考文献向后滚雪球。
- 弱相关排除：`BYZSO` 单独检索大量命中历史电子元件型号、影像链接及 OCR 噪声，均非化学文献；产品页/科研通/ResearchGate 仅作发现线索，不作为独立结构证据；COD 同页的其他 2024 晶体仅因分页或空间群邻近命中，不具谱系关系。

### 阶段 2：引文滚雪球

#### S1：目标论文向后滚雪球（原始参考文献表）

- 机器接口调用：`snowball(seed=10.1039/D3NJ04480G, direction=both, limit=30)` 返回 references=0、citations=0；Semantic Scholar 错误为 `[Errno 1] Operation not permitted`，OpenAlex 兜底也未形成结果。随后从 RSC ESI 的比较表与参考文献表抽取题名/作者/年卷页，以精确题名或 DOI 重新检索出版者、DOI 元数据、期刊索引和 COD；只把能回溯到原始论文/出版者的记录交给 `save_to_library`。
- 去重后新增 33 条；分三批保存，工具结果依次为 `before=9, added=11, total=20`、`before=20, added=11, total=31`、`before=31, added=11, total=42`。`before` 是并行共享库的即时值，并非本切片独占基线。
- 命中路径统一为“RSC ESI 表 S4/参考文献 → 精确题名/作者检索 → DOI/出版者或期刊索引核验 → `save_to_library`”。逐条 DOI/无 DOI 状态如下（“无 DOI”表示本轮未取得可核验 DOI，未据记忆补写）：

| # | 年份 | 核验后的文献/体系 | DOI 或命中路径 | 谱系用途 |
|---:|---:|---|---|---|
| 1 | 1967 | Michel, Buisson & Bertaut, *Structure de Y2SiO5* | 无 DOI；*C. R. Acad. Sci. B* 264, 397–399 | `Y2SiO5` 基础结构 |
| 2 | 1970 | Maksimov et al., `Y2SiO5` 晶体结构 | 无 DOI；*Kristallografiya* 15, 926–933 | `Y2SiO5` 基础结构 |
| 3 | 1972 | Batalieva & Pyatenko, artificial yttrialite (`y-Y2SiO5`) | 无 DOI；*Sov. Phys. Crystallogr.* 16, 786–789 | `Y2SiO5` 多型 |
| 4 | 1990 | Dias et al., delta-`Y2Si2O7` | 无 DOI；*Z. Kristallogr.* 191, 117–123 | 稀土焦硅酸盐多型 |
| 5 | 1994 | Christensen, high-temperature rare-earth disilicates by neutron powder diffraction | 无 DOI；*Z. Kristallogr.* 209, 7–13 | 稀土焦硅酸盐结构族 |
| 6 | 2008 | Dolan et al., structures and thermal expansion of `Y2Si2O7` polymorphs | `10.1154/1.2825308` | 多型/结构比较 |
| 7 | 2003 | Redhammer & Roth, beta-`Y2Si2O7` thortveitite type | `10.1107/S0108270103018869` | 同型标杆 |
| 8 | 2004 | Becerro et al., revisiting `Y2Si2O7/Y2SiO5` by `89Y` NMR | `10.1016/j.jssc.2004.03.047` | 结构修订/相鉴别 |
| 9 | 2004 | Becerro & Escudero, revision of crystallographic data | `10.1080/01411590412331282814` | 结构数据修订 |
| 10 | 2014 | Sun, Li & Zhou, rare-earth silicate review | `10.1179/1743280414Y.0000000033` | 综述入口 |
| 11 | 1973 | Felsche, *The crystal chemistry of rare-earth silicates* | `10.1007/3-540-06125-8_3` | 奠基综述/谱系入口 |
| 12 | 1974 | Grosse & Tillmanns, `Ba2SiO4` structure | 无 DOI；题名/卷页索引核验 | Ba–Si–O 比较相 |
| 13 | 1995 | Finger, Hazen & Fursenko, `BaSi4O9` benitoite | `10.1016/0022-3697(95)00075-5` | Ba–Si–O 结构比较 |
| 14 | 1999 | Hazen et al., `BaSi4O9` (`P3`) | 无 DOI；题名/作者索引核验 | 同组成结构变体 |
| 15 | 1978 | Tillmanns & Grosse, tribarium silicate | `10.1107/S0567740878003696` | Ba–Si–O 比较相 |
| 16 | 1973 | Katscher, Bissert & Liebau, high-T `Ba2[Si4O10]` | `10.1524/zkri.1973.137.2-3.146` | 链/层拓扑比较 |
| 17 | 1980 | Hesse & Liebau, barium silicate chains, part I | 无 DOI；*Z. Kristallogr.* 153, 3–17 | 链硅酸盐谱系 |
| 18 | 1980 | Hesse & Liebau, barium layer silicates, part III | 无 DOI；*Z. Kristallogr.* 153, 33–41 | 层硅酸盐谱系 |
| 19 | 1974 | Goreaud et al., sanbornite `Ba(Si,Ge)2O5` | 无 DOI；题名/作者索引核验 | Ba 硅酸盐比较相 |
| 20 | 1971 | Filipenko et al., ribbon `Ba4Si6O16` | 无 DOI；题名/作者索引核验 | 带状拓扑比较 |
| 21 | 2020 | Zhong et al., `Ba5Si8O21` | `10.1039/C9CP05576B`；OpenAlex `W2998599066` | 新近 Ba–Si–O 结构基线 |
| 22 | 2007 | Yusa et al., high-pressure `BaSiO3` | `10.2138/am.2007.2314` | 压致多型/结构演化 |
| 23 | 1993 | Liu & Barbier, stuffed-tridymite `BaMSiO4` (`M=Co,Zn,Mg`) | DOI `10.1006/jssc.1993.1013`；题名/作者顺序/期刊索引核验 | `Ba–Zn–Si–O` 同型族 |
| 24 | 1999 | Lin et al., `BaZn2Si2O7` phase transition | `10.1016/S0022-3697(99)00004-9` | 核心 Ba–Zn 硅酸盐结构族 |
| 25 | 2002 | Kaiser & Jeitschko, `Ba2ZnSi2O7` | `10.1524/ncrs.2002.217.1.25` | Ba–Zn 硅酸盐结构比较 |
| 26 | 2021 | Zou et al., `BaZnSi3O8` | `10.1002/chem.202005170` | Ba–Zn 硅酸盐新相 |
| 27 | 2012 | Kerstan, Müller & Rüssel, `BaZn2-xMgxSi2O7` | `10.1016/j.jssc.2012.01.055` | 固溶/等结构判据样本 |
| 28 | 2022 | Thieme & Rüssel, solid solutions review | `10.1039/D2CE00667G` | 综述入口/取代谱系 |
| 29 | 2024 | Ababaikeri et al., `Ba3Zn4Si4O15` | `10.1002/zaac.202400026` | 新近 Ba–Zn 硅酸盐结构 |
| 30 | 2024 | Cai et al., `BaZnSi3O8`-based ceramics | `10.1111/jace.19513` | 新近结构/性能交叉核验 |
| 31 | 2016 | Gorelova et al., Ba silicates: thermal expansion and structural complexity | `10.1016/j.jssc.2015.12.012` | Ba 硅酸盐结构复杂度 |
| 32 | 2006 | Aitasalo et al., monoclinic `Ba2MgSi2O7` | 无 DOI；题名/作者索引核验 | `Ba2MSi2O7` 近邻族 |
| 33 | 1954 | Buerger, *The stuffed derivatives of the silica structures* | 无 DOI；题名/期刊索引核验 | stuffed-silica 奠基框架 |

#### S2：目标论文向前滚雪球

- 查询式：`"10.1039/D3NJ04480G" 2025`、`"10.1039/D3NJ04480G" 2026`、`"Ba5Y12Zn[O(SiO4)]8" 2025 OR 2026`、目标 DOI 的 OpenAlex/citing 检索。
- 去重后新增 1 条：Gu et al. (2025), `LiBa2GaSi2O8: A Noncentrosymmetric Silicate ...`, DOI `10.1021/acs.inorgchem.5c05174`，ACS *Inorganic Chemistry* 64(50), 25007–25014；命中路径为 DOI/题名检索 → ACS 出版者记录 → PubMed `41379479` 与 OpenAlex `W4417274802` 交叉核验 → `save_to_library`（`before=42, added=1, total=43`）。
- 该文属于目标论文的光学材料语境前向关联，但本轮未核得它与目标相同型/同拓扑；因此只保留为“前引上下文”，在目标相结构近邻谱系中标为弱相关，不把它计作直接近邻。

#### S3：五类种子复核与综述参考文献跟进

- 按 skill 要求选择 5 个种子：高被引/奠基入口 `10.1007/3-540-06125-8_3`、核心结构论文 `10.1016/S0022-3697(99)00004-9`、两篇新近论文 `10.1002/zaac.202400026` 与 `10.1111/jace.19513`、综述 `10.1039/D2CE00667G`。对每个均调用 `snowball(direction=both, limit=30)`；五次都返回 refs=0/cites=0，且 Semantic Scholar 报 `[Errno 1] Operation not permitted`，故用出版者综述正文的参考文献和精确 DOI/题名检索补偿。
- 从 2022 CrystEngComm 综述核得：`BaZn2Si2O7` 低温 `C2/c`、高温 `Ccm2₁`，约 280 °C 相变；Mg/Co 可形成保持结构族的广泛取代，Ni/Cu 为部分取代，Ba→Sr 与 Si→Ge 改变相变/膨胀行为。这里的“同族”仅描述 `BaZn2Si2O7` 固溶系列，不能外推成与目标 `Ba5Y12ZnSi8O40` 等结构。
- 本轮去重后新增 5 条，保存结果 `before=43, added=5, total=48`：

| 年份 | 文献/体系 | DOI/命中路径 | 用途 |
|---:|---|---|---|
| 2015 | Thieme, Görls & Rüssel, `Ba1-xSrxZn2Si2O7` | `10.1038/srep18040`；RSC 综述参考文献 → Scientific Reports | A 级：该固溶系列内部的结构取代证据 |
| 2013 | Kerstan et al., `BaZn2-xCoxSi2O7` | `10.1016/j.jssc.2013.09.003` | A 级：该固溶系列内部的结构取代证据 |
| 2017 | Thieme et al., variable-thermal-expansion glass-ceramics | `10.1038/s41598-017-03132-x` | B/C 级：结构—相变关联；非目标直接同型 |
| 2020 | Erlebach et al., zero-expansion thermomechanical properties | `10.1039/D0CP02975K`；另命中 arXiv `2405.19378` | B/C 级：结构族性质佐证；非目标直接同型 |
| 2026 | Zhao et al., monoclinic `Ba2MgSi2O7` ceramics | `10.1016/j.ceramint.2026.07.034` | 新近近邻族结构/性能交叉记录 |

#### 滚雪球检索的可复现错误

- RSC 目标落地页的一次直接打开返回 403，但检索结果、DOI 落地元数据和可打开的 ESI 相互一致；未把 403 页面当作证据。
- OpenAlex API 的一次直接打开被环境判为不安全/内部错误；仅保留能由出版者或第二索引交叉确认的字段。
- RSC 综述参考文献中的 3 个内部点击返回工具内部错误，随后用精确题名/DOI 独立检索恢复；无法恢复 DOI 的条目明确保留“无 DOI”，未手编。
- 所有项目 `search_papers`/`snowball` 联网错误及本地超时均在本日志保留；没有把错误返回误记为“文献不存在”。

### 阶段 3：边际新增与收敛

#### C1：稀土位替换的直接等结构物窄化检索

- 查询式：`"Ba5Gd12Zn" silicate crystal`、`"Ba5Lu12Zn" silicate crystal`、`"Ba5Yb12Zn" silicate crystal`、`"Ba5Sc12Zn" silicate crystal`。
- 来源：外部多源网页/出版者索引检索；均返回空结果。本轮去重后新增 0。
- 解释边界：只说明在本轮来源与查询式下没有发现直接 `Ba5Ln12Zn` 同型报道；不能据此作全局不存在断言。

#### C2：目标式的结构关系术语收敛检索

- 查询式：精确 `"Ba5Y12Zn[O(SiO4)]8"` 分别与 `"solid solution"`、`superstructure`、`isotypic`、`derivative` 联合；并复核展开式 `"Ba5Y12ZnSi8O40"`。
- 命中仍为目标 RSC 论文、ESI、COD 及无关聚合/前引页面，无新的可核验结构论文。本轮去重后新增 0。
- 连续两轮边际新增为 `0, 0`；此前综述跟进轮新增 5（小于 10）。就本切片的限定问题，新增已经收敛，因此停止扩展近义词，避免以组成相似文献填充正式综述配额。

#### 每轮边际汇总

| 轮次 | 检索动作 | 去重新增 | 共享库即时总量 | 备注 |
|---|---|---:|---:|---|
| K1 | 目标 DOI/式精确核验 | 0 | 1 | 目标 DOI 已被并发 agent 先写入，幂等去重 |
| S1 | RSC ESI 向后滚雪球 | 33 | 42 | 三批各 11；总量夹有其他切片并发写入 |
| S2 | 目标 DOI 向前滚雪球 | 1 | 43 | 前引上下文，非直接结构近邻 |
| S3 | 5 种子复核 + 综述参考文献 | 5 | 48 | 一批保存 |
| C1 | `Ba5Ln12Zn` 直接替换系列 | 0 | 48 | 空结果，不作不存在断言 |
| C2 | solid-solution/superstructure/isotypic/derivative | 0 | 48 | 收敛 |

本切片经检索工具实际新增 39 条；目标 DOI 因并发去重不计入本切片新增。共享库总量是逐次保存时的快照，最终汇合以账本/库文件为准。

### 阶段 4：身份、基线和谱系判据结论（只据上述检索证据）

#### 1. 目标式身份与记号

- 规范括号式：`Ba5Y12Zn[O(SiO4)]8`；数据库展开式：`Ba5Y12ZnSi8O40` / `Ba5 O40 Si8 Y12 Zn`；简称：`BYZSO`。括号展开为 8 个 Si 和 40 个 O，与 COD 7063074 一致。
- 形式电荷校验（记号算术，不是独立的价态测定）：`5×Ba2+ + 12×Y3+ + Zn2+ + 8×Si4+ = +80`，`40×O2− = −80`，式量电中性。目标论文 ESI 的 Zn BVS 约 1.954，与 Zn(II) 记号相容。
- 唯一核验到的目标结构主论文：Ababaikeri et al. (2024), DOI `10.1039/D3NJ04480G`；首发 2024-01-23，稿件提交 2023-09-25。目标论文称其为 Ba–Y–Zn–Si–O 体系首例；本切片只把此表述归因于该论文，不升级为数据库穷尽性结论。

#### 2. 目标相结构基线

- 四方、非中心对称 `I-42m`（No. 121）；`a=18.7014(6) Å`、`c=5.3640(2) Å`，COD 给出体积约 `1876.02 Å³`。
- ESI 核验的基本配位/构件：`BaO8`、`YO7`、`ZnO4`、`SiO4`；含孤立 `[ZnSi4O16]` 与孤立 `[SiO4]`，按论文表 S4 归为 0D 构件，`nM/nSi=2.3:1`。
- ESI 原子位点提供了可复核锚点：Ba(1) `8f`、Ba(2) `4d`（占位 0.5）、Y(1) `8i`、Y(2) `16j`、Zn `2b`、Si(1) `8i`、Si(2) `8f`。这些字段优先于仅凭化学式猜测拓扑。

#### 3. 结构近邻纳入层级与所得谱系

- A（直接）：有 SCXRD/Rietveld/中子衍射等结构证据，且明确同型/等结构/相同空间群与拓扑或为经结构精修的连续固溶系列。
- B（派生）：有结构证据且论文明确给出多型、超结构、相变或拓扑派生关系。
- C（比较）：只共享 Ba–Si–O、Y–Si–O、Ba–Zn–Si–O 子体系、局部构件或维度；可作化学/拓扑基线，但不得称为目标相直接近邻。
- D（排除）：只有元素/组成相似、性能或计算结果，无实验晶体学关系；不进入结构谱系。
- 对目标相本身，本轮未发现 A 级 `Ba5Ln12ZnSi8O40` 直接等结构替换物。`BaZn2Si2O7` 及 Mg/Co/Sr/Ge 取代文献可在它们自己的固溶族内判为 A/B 级，却因化学计量、空间群和构件与目标不同，只能作为目标综述的 C 级旁系比较。`Y2SiO5/Y2Si2O7` 多型、Ba 硅酸盐链/层/带结构、`BaMSiO4` stuffed-tridymite、`Ba2MSi2O7` 与其他 Ba–Zn 硅酸盐共同构成“稀土硅酸盐基线 → Ba 硅酸盐拓扑 → Ba–Zn 硅酸盐旁系 → 目标五元相”的证据谱系，而非一条未经证明的同构演化链。

#### 弱相关与排除清单

- `BYZSO` 电子元件/图像/OCR 噪声；产品页、ResearchGate、科研通/摘要镜像仅作发现线索。
- COD 分页中因年份、空间群或列表位置相邻而命中的无关晶体；只共享元素但没有结构关系的材料。
- `LiBa2GaSi2O8` 仅保留为目标论文前引语境，未作为结构近邻。
- 只报告介电/光学/热膨胀而未给出可追溯结构证据的掺杂、玻璃及玻璃陶瓷条目；综述中提及但无法恢复题名/作者/卷页的碎片。
- 供应商、数据库自动页和二手聚合页不得替代原始结构论文；无法核验 DOI 时保留无 DOI，而不是推测。

#### Comprehensive 档切片观察

- 子主题 3 的结构谱系已取得超过 15 条原始/综述入口，但子主题 1–2 针对这个 2024 新五元相只有 1 篇直接结构主论文；用旁系组成文献凑足每子题 15 条会破坏纳入标准。
- 本切片可核验的明确综述入口为 Felsche (1973)、Sun et al. (2014)、Thieme & Rüssel (2022)，未在本切片人为补足“综述 ≥8”；正式 comprehensive 总量、近三年比例和跨切片配额应由汇合 agent 在所有切片完成后评估。本切片按要求没有运行 coverage 汇总或设置 coverage gate。

## Done

- 检索完成：本地语料优先、多源关键词矩阵、目标向后/向前滚雪球、5 类种子复核、两轮收敛检索均已记录。
- 写库方式：所有新增仅经检索工具的 `save_to_library` 写入并发共享 `workspace/library/papers.jsonl`；未直接编辑该 JSONL。
- 数量：本切片去重新增 39；目标记录并发去重 1；本切片最后一次保存快照为共享库 48 条；结束校验时因其他切片继续并发写入，共享库已为 63 条；末两轮新增 `0,0`。
- 未执行：未手编/导出 `references.bib`，未运行 coverage 汇总，未写其他切片日志。
- 有界验收：本日志经 `test -s`/`wc` 检查为非空；共享 JSONL 63 条均可逐行解析、0 个 JSON 错误。核对清单中的 26 个 DOI（含并发去重的目标 DOI）全部命中，14 条明确“无 DOI”的题名也全部命中，即目标记录与本切片 39 条新增均已落盘。未输出整库内容，未读取活动 parallel 日志。
- 账本：上述验收通过后登记本切片 `done`；本文件不代替汇合 agent 的 coverage/配额判断。
