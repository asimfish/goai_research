# Research Gap Register — COFs for Photocatalytic HER

每条 gap：证据链（≥2 库内 key + 检索数据库标注）→ 为什么现有工作没有覆盖（推理）→
缺的是什么。与综述 Open Challenges 节（`drafts/sections/06_open_challenges.tex`）同步；
key 数据库出处与 `notes/search_log.md` 检索记录一致。

## G1 — 跨家族标准化 HER 基准协议缺失

- **证据链**: `ghosh2020identification` (OpenAlex) 的因子解耦协议只在 S-COF/FS-COF 单一家族内
  完成；`li2022covalent` (OpenAlex) 用 AQE@450nm 报告性能而 `yang2021protonated` (OpenAlex)
  用质量比速率 (mmol g⁻¹ h⁻¹)，两种口径无法互换；`zhao2022accelerated` (OpenAlex) 的高通量
  筛选面向 H₂O₂ 光合成而非 HER。
- **为什么现有工作没覆盖**: 因子解耦实验成本高（同族多变量对照样品），各组倾向报告对自家
  材料有利的指标（AQE vs 速率 vs TON），且照明/牺牲剂/助催化剂载量无统一规范——没有任何
  一篇库内工作跨 ≥2 个 linkage 家族做过同协议对照。
- **缺什么**: 跨 linkage 家族的固定协议基准（统一光源/牺牲剂/Pt 载量 + 报告 AQE 与质量速率
  双口径），类似 ghosh2020identification 协议的多家族扩展。

## G2 — 非牺牲全水分解仍是孤例

- **证据链**: `shen2023in` (OpenAlex) 是库内唯一直指 overall water splitting 的 COF 体系
  （2D/2D Z-scheme，速率远低于牺牲体系）；`wang2020covalent` (OpenAlex/Crossref) 综述确认
  截至 2020 COF 光催化以牺牲 HER 为主；`banerjee2017single` (OpenAlex) 等分子助催化体系
  仍依赖 TEOA 牺牲给体。
- **为什么现有工作没覆盖**: 牺牲给体掩蔽了水氧化半反应的动力学瓶颈——四电子 OER 对有机
  骨架的氧化损伤与电荷提取要求远超牺牲 HER，多数 COF 的价带位置与抗氧化性未按 OER 设计。
- **缺什么**: 面向 OER 半反应稳定的 COF/助催化剂界面设计与 Z-scheme 电荷路由的定量研究。

## G3 — 光催化循环中的结构耐久性未被量化

- **证据链**: `zhou2021peg` (OpenAlex) 证明光催化循环中会发生共轴堆叠失序并导致活性衰减
  （需 PEG 锁定）；`kandambeth2012construction` (Crossref) 的 9 N HCl/沸水化学稳定性
  与光照工况稳定性是两类不同指标；`haase2020solving` (OpenAlex) 的 trilemma 框架未含
  operando 维度。
- **为什么现有工作没覆盖**: 领域默认「化学稳定 ≈ 光催化稳定」，但堆叠失序、激发态氧化、
  助催化剂脱附都只在工况下发生；表征习惯是反应前后 PXRD 对照，缺 operando 时间分辨结构数据。
- **缺什么**: operando/时间分辨的结构-活性关联（循环数 vs 结晶度/堆叠序/速率），
  及统一的「光催化寿命」报告规范。

## G4 — 绿色可放大路线与 HER 性能脱节

- **证据链**: `xu2026structural` (Crossref) 流动合成 TpPa-1 报告 BET 418 m² g⁻¹、30× STY、
  −89% 能耗，但**未报告 HER 数据**；`grenu2020microwave` (OpenAlex) 汇编的微波 TpPa-1
  BET 725 m² g⁻¹ 同样止于孔隙度/CO₂ 表征（原始工作 `wei2015the`, OpenAlex）；
  `peng2016room` (OpenAlex) 室温/流动路线以结晶度与孔隙度收尾。
- **为什么现有工作没覆盖**: 合成方法学与光催化两个社区的评价体系割裂——方法学论文用
  BET/PXRD 收尾即可发表，光催化论文默认溶剂热标准品；无人把「路线 → 结晶度/缺陷 → HER」
  链条在同一材料上补全（而 `ghosh2020identification`, OpenAlex 已证明结晶度是主因子，
  该链条理应成立）。
- **缺什么**: 同一 COF（如 TpPa-1）跨路线（溶剂热/微波/流动/机械化学）的同协议 HER 对照
  ——这正是本综述 Route C 设计（§Route C）要奠基的实验。

## G5 — 激子结合能设计规则缺实验闭环

- **证据链**: `qian2023computation` (OpenAlex) 用 DFT 系统筛选 D–A 对的激子结合能，但实验
  验证仅覆盖子集；`chen2023tuning` (OpenAlex) 的激发态电子分布解析限于酰肼单家族；
  `blatte2024photons` (OpenAlex) 明确指出 photon→exciton→electron 链条各环节的表征
  方法学仍未统一。
- **为什么现有工作没覆盖**: E_b 的实验测定（温变 PL/TA 光谱）在多晶粉末 COF 上噪声大、
  与计算模型（单层/理想堆叠）失配；计算组与光谱组的样品集不重叠，导致「计算预测 →
  合成 → 实测 E_b → HER」闭环从未在同一材料系列上走通。
- **缺什么**: 计算-合成-光谱闭环的 E_b 基准数据集（同一 isoreticular 系列 ≥5 个成员）。

## G6 — 地球丰产助催化剂与 Pt 的性能差距未被系统攻关

- **证据链**: `banerjee2017single` (OpenAlex) 钴肟/N₂-COF 体系 TON 54.4、782 μmol h⁻¹ g⁻¹，
  与 Pt 基体系（如 `yang2021protonated`, OpenAlex, 20.7 mmol g⁻¹ h⁻¹ 量级）相差显著；
  `gottschling2020rational` (OpenAlex) 共价锚定改善但未解决钴肟降解；`dong2021platinum` /
  `li2022in` (OpenAlex) 表明领域主力仍在 Pt 物种工程内卷。
- **为什么现有工作没覆盖**: 分子助催化剂的失活机理（配体解离、Co 还原态副反应）需要
  operando 光谱+电化学联用，超出多数 COF 课题组的表征栈；Pt photodeposition 太方便，
  降低了替代路线的投入动机。
- **缺什么**: 共价锚定 + 自修复配体设计的稳定性攻关，及 TON 口径的 Pt/非 Pt 全生命周期
  成本对比。

---
统计：6 条 gap；每条 ≥2 库内 key；数据库标注 OpenAlex/Crossref（与 search_log 一致，
stegbauer2014a 的 arXiv 佐证线未用于 gap 主证据）；全部 key 已过 ref_integrity（37/37）。
