# Ba₅Y₁₂Zn[O(SiO₄)]₈ 及结构相近化合物合成条件：阶段一 taxonomy

> 状态：阶段一产物。因本次输入为裸主题且流水线按非交互式自动推进规则运行，当前以候选 1 为主贡献、候选 2 为核心方法贡献、候选 3 为实践贡献；这是仅服务于本次交付的工作假设，未经用户逐项确认，也不表示投稿定位已获用户确认。最终响应必须显式告知用户可调整该组合。证据边界仅为 `workspace/inputs/topic.md`、`workspace/inputs/scope.md`、`workspace/library/papers.jsonl` 与已通过 ref_gate 的 `workspace/library/references.bib`。本文不是 citation bank、blueprint 或综述正文。

## 1. 分类对象、证据层级与 MECE 规则

### 1.1 分类对象

分类的基本单位是“用于回答合成条件的证据主张”，而不是整篇论文。一篇论文可以同时报告结构、路线和表征，因而可支撑不同顶层问题；但同一条主张在同一层级只归入一个叶节点。顶层七支分别回答：相是什么、为何可比、组成如何变化、如何制得、哪些工艺变量控制成相、怎样判断成功、哪些失败边界限制配方迁移。最后一支把这些证据转换成按迁移距离分级的配方篮子。

### 1.2 证据层级

- **D0（目标相直接证据）**：规范式与用户给定式一致，且原始工作直接报告合成与结构。当前仅 `ababaikeri2024ba5y12zn` 一篇，故“目标相直接证据稀缺”本身是分类结果；不得用 Ba–Y 无 Zn 相或 Ba–Zn 硅酸盐凑足三篇。
- **D1（同一身份谱系）**：围绕四方 Ba–Y 硅酸盐的早期 `Ba5+xY13Si8O41`、后续非整比/调制结构重审及独立相场确认；可用于辨析目标相附近竞争身份，但不自动等同于含 Zn 的目标相。
- **N1（晶体化学近邻）**：有 SCXRD、CRED、同步辐射、粉末/中子精修或明确同型关系支持的拓扑/位点近邻。
- **P1（工艺近邻）**：结构并非同型，但其固相、助熔、自熔、熔体生长等工艺变量可用作低权重对照。
- **X（边界/排除）**：仅组成相近、仅功能语境相近、玻璃陶瓷或一般理论背景，不能承担目标相结构或配方结论。

### 1.3 同层 MECE 判定

1. **身份支**按“精确含 Zn 目标式 → Ba–Y 同一结构谱系 → 同体系竞争相”依次判定，三类互斥。
2. **结构支**按证据距离依次判定为“同一 I-42m 谱系 → Ba–Y 多面体/硅酸根近邻 → Ba–Zn–Si 四面体网络 → Y–Si–O 多型对照 → Ba–Si–O 网络对照”；后两类只是负对照。
3. **组成支**按被扰动位点分为主相 Ba/Y/O 化学计量、Ba/Sr 位、Zn/Mg/Co 位、稀土/痕量激活离子位。
4. **路线支**按主导成相事件分为外加助熔高温溶液、自熔/熔体自发结晶、传统固相烧结、机械化学/固液辅助、Czochralski 提拉。若一篇论文含多组实验，每组实验按其主导事件单独分派。
5. **变量、表征与失败支**分别分类输入变量、验证终点和失败结果，不用其中一支替代另一支。
6. **迁移支**按与目标相的距离 D0 → D1 → N1/P1 单向降权，同一拟议配方只能取其最高、且证据充分的等级。

## 2. 树形分类

### A. 目标相身份与原始报道

#### A1. 精确含 Zn 目标相：直接证据稀缺（D0）

- **判定**：直接报告 `Ba5Y12Zn[O(SiO4)]8`、高温溶液法、开放体系和单晶 X 射线结构鉴定。
- **支撑 key（1）**：`ababaikeri2024ba5y12zn`。
- **解释**：这是唯一允许少于三篇的直接目标叶。该文自称 Ba–Y–Zn–Si–O 体系首个化合物；现有证据边界内没有第二篇精确同式的独立复现。原始式中的 O 计量、Zn 是否占据独立四面体以及与无 Zn 四方 Ba–Y 相的关系，必须保留为核验问题，不能先验合并。

#### A2. 四方 Ba–Y 硅酸盐身份谱系与重审（D1）

- **判定**：早期助熔生长的 `Ba5+xY13Si8O41` 谱系、系统助熔筛选、2024 年非整比/调制结构重审，以及 `Ba5Y13[SiO4]8O8.5` 的独立精修证据。
- **支撑 key（5）**：`kolitsch2009crystal`, `wierzbickawieczorek2017high`, `yamane2024synthesis`, `yamane2024microstructure`, `gulay2024navigation`。
- **用途**：建立“历史命名—规范化学计量—现代精修”对照，不把 D1 当成 D0。

#### A3. Ba–Y 体系中的竞争/伴生相身份（D1/N1）

- **判定**：同一成分空间内经结构或相场实验确认、会影响目标相归属或相纯度的 Ba–Y 正硅酸盐/焦硅酸盐及非整比陶瓷相。
- **支撑 key（4）**：`yamane2024synthesis`, `yamane2024microstructure`, `gulay2024navigation`, `motozawa2022bay16si4o33`。
- **用途**：回答“产物是否真为目标相”以及偏离配比时优先出现何种相，而不是扩张目标相定义。

### B. 结构拓扑与晶体化学近邻

#### B1. I-42m 四方 Ba–Y 主谱系（D1/N1）

- **判定**：空间群/结构精修或系统研究把相放入同一四方 Ba–Y 主谱系；含 Zn 目标只作为需要比较的 D0 端点。
- **支撑 key（5）**：`ababaikeri2024ba5y12zn`, `kolitsch2009crystal`, `wierzbickawieczorek2017high`, `yamane2024synthesis`, `gulay2024navigation`。
- **核心比较字段**：空间群、调制/超胞、Ba/Y 位点占据、孤立 `[SiO4]` 与复合四面体单元、氧盈亏。

#### B2. Ba–Y 正硅酸根/焦硅酸根多面体近邻（N1）

- **判定**：含 Ba 与 Y，且有明确结构数据展示孤立正硅酸根、焦硅酸根或 Ba–Y–O 多面体组织方式；不要求与 B1 同型。
- **支撑 key（4）**：`kolitsch2009crystal`, `gulay2024navigation`, `motozawa2022bay16si4o33`, `felsche1973the`。
- **用途**：比较配位与硅酸根聚合度对成相路线的影响，不用作精确目标配方复现证据。

#### B3. Ba–Zn–Si 四面体网络近邻（N1/P1）

- **判定**：ZnO4/SiO4 连接、stuffed-tridymite、焦硅酸根或相关 Ba–Zn–Si 网络有结构鉴定；元素集合相似但结构距离高于 B1/B2。
- **支撑 key（7）**：`liu1993structures`, `lin1999phase`, `kaiser2002crystal`, `zou2021crystal`, `ababaikeri2024ba3zn4si4o15`, `cai2024optimized`, `gorelova2016thermal`。
- **用途**：用于 Zn 挥发、ZnO4 网络形成、烧结和晶型转变的工艺类比；不能证明这些相与目标相同构。

#### B4. Y–Si–O 多型与高温结构对照（P1）

- **判定**：Y2SiO5/Y2Si2O7 或稀土硅酸盐的多型、熔体生成和结构修订证据。
- **支撑 key（7）**：`christensen1994investigation`, `dolan2008structures`, `redhammer2003beta`, `becerro2004revisiting`, `becerro2004revision`, `sun2014recent`, `felsche1973the`。
- **用途**：解释 Y–Si–O 竞争相与高温多型，不列为目标结构近邻。

#### B5. Ba–Si–O 框架负对照（P1/X）

- **判定**：Ba 硅酸盐中不同链、层、benitoite 或高压网络已有结构数据，但缺 Y/Zn 位点对应关系。
- **支撑 key（7）**：`finger1995refinement`, `hazen1999crystal`, `tillmanns1978refinement`, `katscher1973the`, `zhong2020combining`, `yusa2007rhombohedral`, `gorelova2016thermal`。
- **用途**：界定“组成相近不等于结构近邻”，并提示硅酸根聚合度和压力路径会改变结构终点。

### C. 组成替代关系

#### C1. Ba/Y/O 非整比与目标附近组成窗口（D1）

- **判定**：直接改变或重审 Ba/Y/O 化学计量、`x` 范围、位点占据或相场。
- **支撑 key（5）**：`kolitsch2009crystal`, `wierzbickawieczorek2017high`, `yamane2024synthesis`, `yamane2024microstructure`, `gulay2024navigation`。
- **迁移价值**：最高；用于设计目标式附近的小步长组成矩阵，但 Zn 维度仍无独立系列证据。

#### C2. Ba 位的 Ba↔Sr 替代（N1/P1）

- **判定**：Ba–Zn 硅酸盐固溶或玻璃陶瓷中以 Sr 系统替换 Ba，并有结构/热膨胀证据。
- **支撑 key（4）**：`thieme2015ba1`, `thieme2017variable`, `thieme2016negative`, `thieme2022solid`。
- **边界**：属于 BaZn2Si2O7 派生体系，不能直接推定 B1 主谱系的 Sr 容限。

#### C3. Zn 位的 Zn↔Mg/Co 替代（N1/P1）

- **判定**：Ba–M–Si–O 中 M = Zn/Mg/Co 的同型、固溶或结构/热稳定性比较。
- **支撑 key（6）**：`liu1993structures`, `kerstan2012thermal`, `aitasalo2006crystal`, `kerstan2013bazn2si2o7`, `zhao2026crystal`, `thieme2022solid`。
- **迁移价值**：用于选择 Zn 位扰动范围和监测晶型变化；因主结构不同，权重低于 C1。

#### C4. 稀土/痕量激活离子扰动（P1）

- **判定**：稀土正硅酸盐系列或 Ba/Zn/Y 硅酸盐中的 RE/过渡金属掺杂，且实验涉及晶体生长、固相反应或结构/成分表征。
- **支撑 key（6）**：`felsche1973the`, `tejas2024structural`, `pires2001luminescence`, `alizadeh2021spectroscopy`, `shoudu1999czochralski`, `brandle1986czochralski`。
- **边界**：只支持“掺杂会引入新的配比、分凝或价态控制问题”这一工艺框架，不支持目标相具体掺杂限度。

### D. 合成与晶体生长路线

#### D1. 外加助熔剂的高温溶液/助熔生长

- **判定**：相从外加助熔/矿化介质中结晶；包括 MoO3 类助熔体系、含氟/含铅熔盐或论文明确称 high-temperature solution 的实验。
- **支撑 key（6）**：`ababaikeri2024ba5y12zn`, `kolitsch2009crystal`, `wierzbickawieczorek2017high`, `ababaikeri2024ba3zn4si4o15`, `leonyuk1999high`, `giess1982zn2sio4`。
- **必录字段**：原料摩尔比、助熔剂/矿化剂及其比例、开放/封闭体系、坩埚、峰值温度、保温、降温速率、洗涤/分离和晶体尺寸。

#### D2. 自熔、熔体自发结晶与无坩埚熔制

- **判定**：不把外加助熔剂作为主导介质，由反应物自熔、熔体自发成核或无坩埚熔制形成晶相。
- **支撑 key（5）**：`yamane2024synthesis`, `gulay2024navigation`, `christensen1994investigation`, `leonyuk1999high`, `leonyuk1999crystal`。
- **必录字段**：液相组成、最高温度、熔体均化、成核方式、容器接触、冷却程序与玻璃/晶相竞争。

#### D3. 传统固相反应与陶瓷烧结

- **判定**：氧化物/碳酸盐等粉体经混合、煅烧、压制、烧结或复烧形成块体/粉体。
- **支撑 key（11）**：`yamane2024synthesis`, `yamane2024microstructure`, `lin1999phase`, `zou2021crystal`, `kerstan2012thermal`, `cai2024optimized`, `zou2019anti`, `tejas2024structural`, `pires2001luminescence`, `zhao2026crystal`, `kerstan2015kristallphasen`。
- **必录字段**：试剂与纯度、预处理、名义配比、湿/干混与介质、压片、温度—时间、复磨复烧、气氛、坩埚和冷却。

#### D4. 机械化学与固液辅助预活化

- **判定**：高能球磨或固液相辅助步骤实质改变反应性/成相温度，而非普通混匀。
- **支撑 key（3）**：`yamane2024microstructure`, `yldrm2009y2sio5`, `tzvetkov2001effects`。
- **边界**：需要同时记录研磨材质与污染；行星球磨的结果不能与普通玛瑙研钵处理合并比较。

#### D5. Czochralski 熔体提拉

- **判定**：射频加热、坩埚熔体、籽晶/提拉形成 Y2SiO5 或稀土正硅酸盐晶体。
- **支撑 key（4）**：`pang2005study`, `alizadeh2021spectroscopy`, `shoudu1999czochralski`, `brandle1986czochralski`。
- **迁移边界**：仅作为高温熔体稳定性、SiO2 挥发、Ir 坩埚与气氛控制的 P1 对照；当前没有目标相 Czochralski 证据。

> **水热/溶剂热路线不建伪叶**：当前 52 个通过 ref_gate 的 key 中没有足够证据支持目标相或 N1 近邻的水热/溶剂热制备。该路线列入证据缺口，不能用三篇无关水热硅酸盐凑数。

### E. 温度、时间、气氛、坩埚与矿化剂变量

#### E1. 起始配比、试剂形态与挥发补偿

- **判定**：主张针对名义组成、试剂形态/纯度、过量补偿或组成扫描。
- **支撑 key（6）**：`wierzbickawieczorek2017high`, `yamane2024synthesis`, `yamane2024microstructure`, `lin1999phase`, `zou2021crystal`, `shoudu1999czochralski`。
- **对照重点**：BaCO3/氧化物来源、Zn/Si 挥发、`x` 步长、称量后与烧后组成差异。

#### E2. 温度—时间、复磨复烧与升降温程序

- **判定**：主张针对峰值温度、保温时长、升降温速率、中间研磨或重复热处理。
- **支撑 key（7）**：`wierzbickawieczorek2017high`, `yamane2024microstructure`, `lin1999phase`, `zou2021crystal`, `kerstan2012thermal`, `tejas2024structural`, `kerstan2015kristallphasen`。
- **现有可抽取锚点**：近邻固相工作覆盖约 1000–1475 °C、数小时及中间复磨；这些数值是路线对照，不是目标相窗口。

#### E3. 开放体系、氧化/还原气氛与气流

- **判定**：主张针对 open system、空气、O2、N2 或还原性混合气氛。
- **支撑 key（5）**：`ababaikeri2024ba5y12zn`, `ababaikeri2024ba3zn4si4o15`, `zou2019anti`, `tejas2024structural`, `pang2005study`。
- **对照重点**：Zn 挥发/价态、坩埚氧化、相稳定性及开放体系的物质损失。

#### E4. 坩埚、助熔剂/矿化剂与研磨介质

- **判定**：主张针对 MoO3/钼酸盐、含氟/含铅助熔剂、Ir/Al2O3 等坩埚或研磨介质。
- **支撑 key（6）**：`kolitsch2009crystal`, `wierzbickawieczorek2017high`, `pang2005study`, `shoudu1999czochralski`, `giess1982zn2sio4`, `tejas2024structural`。
- **对照重点**：容器相容性、助熔剂残留、Pb/F 危害与废物分流、玛瑙/球磨介质带入 SiO2。

#### E5. 冷却、成核、提拉与晶体分离

- **判定**：主张针对慢冷、分段炉冷、自发成核、籽晶提拉、晶体洗涤或机械分离。
- **支撑 key（6）**：`ababaikeri2024ba5y12zn`, `zou2021crystal`, `pang2005study`, `leonyuk1999high`, `shoudu1999czochralski`, `giess1982zn2sio4`。
- **对照重点**：晶体尺寸与降温速率的对应关系；当前证据内 `giess1982zn2sio4` 给出 1300→960 °C、1 °C h−1 的明确类比，但它使用含铅/含氟体系，迁移等级低。

### F. 相纯度、结构与产物表征

#### F1. 单晶/先进衍射的身份确认

- **判定**：SCXRD、CRED、同步辐射 PXRD 或中子精修承担规范式、空间群、位点占据或调制结构确认。
- **支撑 key（6）**：`ababaikeri2024ba5y12zn`, `kolitsch2009crystal`, `yamane2024synthesis`, `gulay2024navigation`, `motozawa2022bay16si4o33`, `zou2021crystal`。
- **成功标准**：不能只凭峰位相似或功能性能认相；应报告结构模型、拟合质量和组成约束。

#### F2. PXRD/Rietveld 的批量相纯度与杂相审计

- **判定**：粉末衍射或 Rietveld 用于批量相含量、晶型或次生相判断。
- **支撑 key（6）**：`yamane2024microstructure`, `gulay2024navigation`, `lin1999phase`, `zou2021crystal`, `kerstan2012thermal`, `cai2024optimized`。
- **成功标准**：报告未索引峰、相分数/检出限和热处理历史；“主相出现”不等于“相纯”。

#### F3. 元素组成、显微结构与污染追踪

- **判定**：EDS/EDX、元素分析、SEM/显微镜或烧前后组成用于验证位点化学、晶粒与外来污染。
- **支撑 key（5）**：`yamane2024microstructure`, `gulay2024navigation`, `thieme2015ba1`, `tejas2024structural`, `pang2005study`。
- **成功标准**：把名义配比、局域点分析和体平均分开；尤其审计玛瑙研磨导致的 SiO2 污染。

#### F4. 高温相稳定性、热分析与气氛耐受

- **判定**：HT-XRD、热分析、膨胀测量或多气氛烧结用于界定转变/分解边界。
- **支撑 key（5）**：`lin1999phase`, `kerstan2012thermal`, `kerstan2013bazn2si2o7`, `thieme2016negative`, `zou2019anti`。
- **成功标准**：区分室温回收相与原位高温相，不能把可逆高温结构直接当成冷却后产品。

### G. 失败模式与适用边界

#### G1. 配比偏离导致竞争相、玻璃或宽相场

- **判定**：系统组成扫描或重复实验直接显示杂相、玻璃区、非整比宽度或相竞争。
- **支撑 key（5）**：`wierzbickawieczorek2017high`, `yamane2024synthesis`, `yamane2024microstructure`, `gulay2024navigation`, `tzvetkov2001effects`。
- **含义**：不存在一个可脱离组成坐标的“单点万能温度”；配方必须和相场/相纯度结果绑定。

#### G2. 研磨污染、挥发与助熔剂副作用

- **判定**：原料/介质损失、研磨介质带入、SiO2 挥发或助熔剂改变晶体形貌/纯度。
- **支撑 key（4）**：`yamane2024microstructure`, `shoudu1999czochralski`, `tzvetkov2001effects`, `giess1982zn2sio4`。
- **含义**：配比偏差应先排除工艺污染和挥发，不应一律解释成真实固溶。

#### G3. 气氛诱导变化与热致晶型边界

- **判定**：气氛、温度或取代使晶型、相稳定性或还原耐受发生变化。
- **支撑 key（5）**：`lin1999phase`, `kerstan2012thermal`, `kerstan2013bazn2si2o7`, `thieme2016negative`, `zou2019anti`。
- **含义**：空气中成功的 Ba–Zn 对照配方不能无条件迁移至还原气氛；高温原位相也不能等同于室温相。

#### G4. 当前证据边界内实验字段不完整

- **判定**：`papers.jsonl` 的摘要/检索证据只确认路线或结构，未同时暴露配比、温度、时间、气氛、坩埚和冷却全字段。
- **支撑 key（5）**：`ababaikeri2024ba5y12zn`, `ababaikeri2024ba3zn4si4o15`, `kaiser2002crystal`, `cai2024optimized`, `zhao2026crystal`。
- **含义**：这是“当前证据包不完整”，不是断言原论文没有细节。进入后续阶段前需回到原始实验部分补齐；本阶段不得猜值。

### H. 可迁移配方篮子（比较框架，不是实验建议）

#### H1. D0 目标相复现起点：直接证据稀缺

- **纳入**：只收精确含 Zn 目标相的原始高温溶液路线。
- **支撑 key（1）**：`ababaikeri2024ba5y12zn`。
- **用法**：作为唯一直接起点；在实验段完整字段未抽取前，不输出具体推荐配方。

#### H2. D1 同一 Ba–Y 身份谱系的组成—路线矩阵

- **纳入**：MoO3 助熔、系统 151-run 参数筛选、非整比组成扫描、陶瓷复现和独立相场确认。
- **支撑 key（5）**：`kolitsch2009crystal`, `wierzbickawieczorek2017high`, `yamane2024synthesis`, `yamane2024microstructure`, `gulay2024navigation`。
- **可迁移内容**：组成步长、相场设计、杂相审计和结构核验流程；不能把无 Zn 配比直接改名为目标配方。

#### H3. N1/P1 高温溶液与助熔生长工具箱

- **纳入**：Ba–Y、Ba–Zn 或 Y–Si–O 结构/工艺近邻的外加助熔和慢冷条件。
- **支撑 key（6）**：`kolitsch2009crystal`, `wierzbickawieczorek2017high`, `ababaikeri2024ba3zn4si4o15`, `leonyuk1999high`, `leonyuk1999crystal`, `giess1982zn2sio4`。
- **可迁移内容**：变量表结构、慢冷/分离策略和助熔剂筛选方法；具体温度与 Pb/F 助熔剂不直接迁移。

#### H4. N1/P1 固相成相与相纯度筛选工具箱

- **纳入**：组成系列、复磨复烧、温度窗口、多气氛烧结及 PXRD/EDS 审计。
- **支撑 key（8）**：`yamane2024synthesis`, `yamane2024microstructure`, `lin1999phase`, `zou2021crystal`, `kerstan2012thermal`, `cai2024optimized`, `zou2019anti`, `tejas2024structural`。
- **可迁移内容**：小步长配比 × 温度 × 气氛的筛选设计，以及主相/杂相判据；近邻的数值窗口只能作为下限/上限探索的参考。

#### H5. P1 熔体提拉与挥发控制工具箱

- **纳入**：Y2SiO5/稀土正硅酸盐的 Czochralski 原料预烧、Ir 坩埚、保护气氛、提拉和后退火。
- **支撑 key（4）**：`pang2005study`, `alizadeh2021spectroscopy`, `shoudu1999czochralski`, `brandle1986czochralski`。
- **可迁移内容**：高温熔体稳定性和挥发/坩埚控制清单；当前不支持把目标相改走 Czochralski 路线。

## 3. 叶节点支撑计数审计

| 叶节点 | 支撑 key 数 | ≥3 篇规则 | 备注 |
|---|---:|---|---|
| A1 | 1 | 例外 | D0 直接证据稀缺，不以近邻凑数 |
| A2 | 5 | PASS | D1 身份谱系 |
| A3 | 4 | PASS | 竞争/伴生相 |
| B1 | 5 | PASS | 主谱系 |
| B2 | 4 | PASS | Ba–Y 多面体近邻 |
| B3 | 7 | PASS | Ba–Zn–Si 网络对照 |
| B4 | 7 | PASS | Y–Si–O 多型对照 |
| B5 | 7 | PASS | Ba–Si–O 负对照 |
| C1 | 5 | PASS | 主相非整比 |
| C2 | 4 | PASS | Ba↔Sr |
| C3 | 6 | PASS | Zn↔Mg/Co |
| C4 | 6 | PASS | 稀土/激活离子，低迁移权重 |
| D1 | 6 | PASS | 外加助熔 |
| D2 | 5 | PASS | 自熔/自发/无坩埚 |
| D3 | 11 | PASS | 固相/陶瓷 |
| D4 | 3 | PASS | 机械化学/固液辅助 |
| D5 | 4 | PASS | Czochralski |
| E1 | 6 | PASS | 配比/试剂/挥发 |
| E2 | 7 | PASS | 温度—时间/复烧 |
| E3 | 5 | PASS | 气氛/开放体系 |
| E4 | 6 | PASS | 坩埚/助熔/研磨介质 |
| E5 | 6 | PASS | 冷却/成核/分离 |
| F1 | 6 | PASS | 结构身份 |
| F2 | 6 | PASS | 批量相纯度 |
| F3 | 5 | PASS | 成分/显微/污染 |
| F4 | 5 | PASS | 高温/气氛稳定性 |
| G1 | 5 | PASS | 相竞争/玻璃/相场 |
| G2 | 4 | PASS | 污染/挥发/助熔副作用 |
| G3 | 5 | PASS | 气氛/热致边界 |
| G4 | 5 | PASS | 当前证据字段不完整 |
| H1 | 1 | 例外 | D0 直接复现起点稀缺 |
| H2 | 5 | PASS | D1 配方矩阵 |
| H3 | 6 | PASS | 助熔工具箱 |
| H4 | 8 | PASS | 固相筛选工具箱 |
| H5 | 4 | PASS | 熔体提拉工具箱 |

审计口径：同一篇论文的重复 BibTeX key 不重复计数；`liu1993structuresx` 与 `liu1993structures` 是同题同 DOI 的重复记录，本表只使用后者。除 A1/H1 对“同一个 D0 事实”的不同视图外，所有叶节点均达到至少 3 篇的规则。

## 4. 未归类

### 4.1 已过 ref_gate、但暂不进入树叶的 key

- `buerger1954the`：一般 stuffed-silica 结构概念，当前证据没有目标/近邻合成条件字段。
- `erlebach2020thermomechanical`：零热膨胀材料的一般理论—实验综述，未形成目标相结构或路线证据。
- `gu2025liba2gasi2o8`：检索记录已标为光学语境的前向引用，当前没有足够证据把 Li–Ba–Ga 硅酸盐纳入目标结构近邻。
- `thieme2017variable`：只在 C2 作为 Ba↔Sr 组成关系背景计数；按 scope，玻璃陶瓷本身不进入目标合成路线叶。
- `liu1993structuresx`：与 `liu1993structures` 同题同 DOI 的重复 BibTeX 记录，不作为第二篇支撑文献。

### 4.2 `papers.jsonl` 中无可用 ref_gate key 的孤儿记录

以下 11 条记录在 `papers.jsonl` 中存在，但没有对应的 `references.bib` key，故不能支撑叶节点或在后续正文中引用：2011 年四方 Ba–Y/Ho 同型会议摘要、2007 年相关博士论文、1967/1970 年 Y2SiO5 结构记录、1972/1990 年 Y2Si2O7 结构记录、1974 年 Ba2SiO4、两条 1980 年富硅 Ba 硅酸盐结构记录、1974 年 Ba(Si,Ge)2O5、1971 年 Ba4Si6O16。它们应由 lit-search/ref-guard 补 key 后再分派；本阶段不手编 BibTeX。

## 5. 证据缺口

1. **D0 独立复现缺口**：精确 `Ba5Y12Zn[O(SiO4)]8` 只有一个通过闸门的直接 key；尚不能判断报道式与 Ba–Y 四方谱系是取代、共生、误指认还是不同相。
2. **完整配方字段缺口**：目标相 D0 的当前摘要只确认开放体系高温溶液法与 SCXRD，未在允许证据包中同时给出原料比、助熔剂、峰值温度、保温、坩埚和冷却程序。
3. **结构可比性缺口**：Ba–Zn–Si、Y–Si–O 与 Ba–Si–O 多数只是 N1/P1 对照；缺少统一拓扑描述符、位点映射或定量结构距离，不能笼统称“同构”。
4. **Zn 取代系列缺口**：D1 文献系统扫描 Ba/Y/O 非整比，但没有至少三篇直接建立 Zn 在四方 Ba–Y 主谱系中固溶范围与占位的证据。
5. **水热/溶剂热空白**：当前通过闸门的引用池没有目标或 N1 近邻的水热/溶剂热制备证据。
6. **相纯窗口与重复性缺口**：虽有 Ba–Y 组成扫描、独立结构精修和陶瓷过程比较，但精确 D0 尚无跨实验室、同配方的相纯复现。
7. **关键工艺字段缺口**：气氛、坩埚、冷却速率和产率在多条记录中缺失；缺失应记 NA/未报告，不能从相似路线推测。
8. **安全迁移缺口**：含 Pb/F 助熔条件只能作为历史工艺对照；在 EHS、坩埚相容性和废物分流未审核前，不应转写成推荐方案。

## 6. 阶段一结论

回答合成条件时，应以唯一 D0 工作为目标锚点，以 D1 四方 Ba–Y 身份谱系处理规范式和竞争相，以 N1/P1 文献构建变量与失败模式清单。最值得迁移的不是近邻论文中的单个温度，而是“组成小步长 × 路线 × 温度—时间 × 气氛/坩埚 × 冷却 × 多模态认相”的比较框架。任何具体目标相配方仍须在后续阶段读取 D0 原始实验段后才能提出。
