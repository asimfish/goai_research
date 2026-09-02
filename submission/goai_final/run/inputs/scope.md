# 调研范围草案（待用户确认）

## 核心问题

1. `Ba₅Y₁₂Zn[O(SiO₄)]₈` 的规范化学式、晶体结构、空间群、结构原型与最初报道是什么？
2. 哪些化合物可由明确晶体学证据判定为结构相近，而不仅是元素组成相似？
3. 目标相及近邻相分别通过何种路线获得，其可复现实验条件是什么？
4. 阳离子取代、阴离子基团变化、助熔剂和热处理如何影响成相窗口、杂相与晶体尺寸？
5. 文献中哪些条件为原始实测，哪些仅由数据库、二手来源或结构类比推断？

## MECE 子主题

1. **身份与记号核验**：规范式、别名、数据库编号、氧计量、价态与电荷平衡。
2. **目标相结构基线**：晶系、空间群、晶胞、配位多面体、位点占据和结构原型。
3. **结构近邻判据与谱系**：同构/同型、等结构、超结构、同一拓扑、固溶体及明确结构派生物；给出纳入证据等级。
4. **固相与陶瓷路线**：原料、预处理、配比、研磨/压片、温度—时间程序、气氛、坩埚、复烧与冷却。
5. **晶体生长及助熔路线**：自熔/助熔、熔体组成、最高温度、保温、降温速率、籽晶/成核及洗涤分离。
6. **替代与成相控制**：Ba/Y/Zn 位替代、硅酸根相关替换、缺陷/非化学计量、相图或组成窗口。
7. **产物与证据质量**：粉末/单晶、产率、晶粒尺寸、PXRD/SCXRD/Rietveld/元素分析及是否有独立复现。
8. **条件对照与可复现建议**：将已报道条件标准化为统一字段，区分直接证据、二手转述和合理推断，识别信息缺口。

## Coverage 关键词 JSON

以下 JSON 是 `coverage_report` 的可复现输入。关键词只用于题名/摘要的初筛统计；
命中数不自动等于“直接结构近邻”或“独立实验论文”，最终仍按本文件的纳排标准
人工审计。

```json
[
  {
    "name": "身份与记号核验",
    "keywords": ["Ba5Y12Zn", "Ba5Y12ZnSi8O40", "barium yttrium zinc silicate", "BYZSO", "oxygen stoichiometry", "charge balance"]
  },
  {
    "name": "目标相结构基线",
    "keywords": ["crystal structure", "I-42m", "space group", "lattice parameters", "site occupancy", "coordination polyhedra"]
  },
  {
    "name": "结构近邻判据与谱系",
    "keywords": ["isotypic", "isostructural", "polymorph", "superstructure", "solid solution", "crystal chemistry", "structural relationship"]
  },
  {
    "name": "固相与陶瓷路线",
    "keywords": ["solid-state", "solid state reaction", "ceramic", "sintering", "calcination", "mechanochemical", "powder synthesis"]
  },
  {
    "name": "晶体生长及助熔路线",
    "keywords": ["crystal growth", "flux growth", "high-temperature solution", "Czochralski", "single crystal", "melt growth", "slow cooling"]
  },
  {
    "name": "替代与成相控制",
    "keywords": ["substitution", "solid solution", "phase formation", "phase transition", "nonstoichiometry", "defect", "composition range"]
  },
  {
    "name": "产物与证据质量",
    "keywords": ["single-crystal X-ray diffraction", "powder X-ray diffraction", "Rietveld", "neutron diffraction", "PXRD", "SCXRD", "EDS"]
  },
  {
    "name": "条件对照与可复现建议",
    "keywords": ["synthesis", "preparation", "experimental", "temperature", "cooling rate", "phase purity", "reproducibility"]
  }
]
```

## 覆盖档位（reviewer I6 正式降级）

- 自 2026-09-01 起，本窄主题采用 `niche-balanced`，不再采用
  `comprehensive`。原因是目标相 2024 年才首次报道，严格纳排下已有三轮和
  I6 复核轮边际新增均为 0；把一般组成相近相纳入只为达到 100 篇会违反本文件
  的晶体学证据边界。
- 重算阈值：相关文献总量≥50；身份与记号叶≥1 篇直接原始论文并完成精确式、
  DOI 和前后向引文链的收敛核验；目标结构基线/结构谱系各≥12；固相路线、
  晶体生长、替代控制、证据质量、条件对照各≥5；可确认综述入口≥3；
  2024–2026 占比≥10%。身份叶按“唯一直接报道 + 检索饱和”验收，不用一般
  性能材料人为凑成同叶多篇。
- 原 comprehensive 阈值（100–150、八叶各≥15、综述≥8、近三年≥30%）仅
  保留为未完成对照；任何产物不得声称 comprehensive 覆盖完成。残余缺口是
  目标相只有一篇直接主文、缺独立重复合成及若干完整实验字段。

## 纳入标准

- 直接报告目标相制备或晶体生长的原始论文、学位论文、专利或权威晶体数据库记录。
- 具有可核验结构数据、且满足上述结构关系之一的近邻化合物；优先收录含 Ba–稀土–Zn–硅酸盐骨架或同一结构原型的相。
- 综述可用于追溯文献谱系，但具体合成条件原则上回到原始来源核实。
- 目标相与奠基性近邻不限年份；2020–2026 年文献用于补充最新结构修订、合成方法和相关材料体系。

## 排除标准

- 仅元素组成相近、但无晶体学结构近邻证据的 Ba–Y–Zn–Si–O 化合物。
- 只有计算预测而无合成/结构实验证据的相（可在“候选与缺口”中另列，不混入已合成表）。
- 无法追溯到来源的供应商页面、聚合数据库自动摘要和未给实验细节的二手转述。
- 与目标结构无关的玻璃、玻璃陶瓷或掺杂基质性能研究，除非其中明确形成并鉴定了目标/近邻晶相。

## 安全边界（待用户确认）

- 本调研只汇总公开文献条件，不替代机构 EHS 审核和实验 SOP。
- 钡盐按具体形态评估毒性；优先避免可溶性钡盐暴露，粉体称量与研磨需工程控制和个体防护。
- 高温硅酸盐反应涉及炉体、热冲击、坩埚相容性和熔体飞溅风险；含 Zn 体系需评估高温挥发与通风。
- 若文献使用卤化物/含铅或其他有害助熔剂，将明确标注危害与废物分流，不把历史条件直接推荐为常规操作。
- 最终“建议条件”只给文献证据支持的研究起点，并标注风险审查项；不声称未经验证的相纯窗口。

## 拟议贡献声明

本综述拟首次将目标相的记号/结构身份核验、结构近邻的晶体学分级，以及逐字段的合成条件证据表合并呈现；贡献是否成立将在完成检索后据文献事实修订，并在 taxonomy 阶段再次请求用户确认。
