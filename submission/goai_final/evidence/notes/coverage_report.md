# 文献覆盖审计

## 审计口径

- 正式档位：`niche-balanced`（2026-09-01 针对 reviewer issue I6 降级）。
  目标相在 2024 年才首次报道，严格晶体学边界内经既有三轮和 I6 复核轮均无
  新增；继续维持 `comprehensive` 会迫使一般组成相近材料进入库，故不再把
  comprehensive 当作已承诺交付档位。
- `niche-balanced` 配额：总量至少 50；“身份与记号”要求至少 1 篇直接原始
  论文并完成精确式/DOI/双向引文链收敛核验；两个结构核心叶各至少 12；五个
  路线/控制/证据叶各至少 5；确认综述入口至少 3；2024–2026 至少 10%。该档
  只表示窄主题的 balanced 覆盖，不等于 comprehensive。
- 原 `comprehensive` 配额（总量 100–150、八叶各至少 15、综述至少 8、
  2024–2026 至少 30%）保留作未完成的反事实审计。当前日期为 2026-09-01，
  近三年仍按完整自然年 2024–2026 统计。
- 输入：`workspace/library/papers.jsonl` 与 `workspace/inputs/scope.md` 中
  “Coverage 关键词 JSON”。`coverage_report` 只在题名与摘要做关键词 OR 匹配；
  因 63 条中只有 16 条有摘要，且宽词可能命中比较相，命中数是初筛上限，不自动
  证明直接晶体学关系。
- 完整检索式、错误、滚雪球和三轮补检证据见
  `workspace/notes/search_log.md`。四次补检后没有新增，所以下列是最终结果。

## `coverage_report` 原始结果

```json
{
  "library_size": 63,
  "subtopics": [
    {
      "subtopic": "身份与记号核验",
      "hits": 1,
      "year_span": [2024, 2024],
      "gap": true,
      "sample": [
        "Ba5Y12Zn[O(SiO4)]8: a novel non-centrosymmetric silicate with a short ultraviolet cut-off edge featuring [ZnSi4O16] and [SiO4] units"
      ]
    },
    {
      "subtopic": "目标相结构基线",
      "hits": 16,
      "year_span": [1970, 2026],
      "gap": false,
      "sample": [
        "A novel crystal structure type shown by a flux-grown tetragonal Ba-Y-silicate and its isotypic Ho-analogue",
        "Syntheses, crystal structures and crystal chemistry of new mixed-framework silicates and a new molybdate structure type",
        "Synthesis, Crystal Structure, and Dielectric Properties of BaxY26Si16O71+x (x ≈ 10.2)"
      ]
    },
    {
      "subtopic": "结构近邻判据与谱系",
      "hits": 15,
      "year_span": [1973, 2022],
      "gap": false,
      "sample": [
        "Crystal chemistry and topology of two flux-grown yttrium silicates, BaKYSi2O7 and Cs3YSi8O19",
        "A novel crystal structure type shown by a flux-grown tetragonal Ba-Y-silicate and its isotypic Ho-analogue",
        "Syntheses, crystal structures and crystal chemistry of new mixed-framework silicates and a new molybdate structure type"
      ]
    },
    {
      "subtopic": "固相与陶瓷路线",
      "hits": 8,
      "year_span": [2001, 2026],
      "gap": false,
      "sample": [
        "Synthesis, Crystal Structure, and Dielectric Properties of BaxY26Si16O71+x (x ≈ 10.2)",
        "Microstructure and dielectric properties of BaxY26Si16O71+x (x ≈ 10.2) ceramics prepared using a planetary ball mill",
        "Crystal Structure and Ferroelectric Evidence of BaZnSi3O8, a Low-Permittivity Microwave Dielectric Ceramic"
      ]
    },
    {
      "subtopic": "晶体生长及助熔路线",
      "hits": 6,
      "year_span": [1982, 2024],
      "gap": false,
      "sample": [
        "Ba5Y12Zn[O(SiO4)]8: a novel non-centrosymmetric silicate with a short ultraviolet cut-off edge featuring [ZnSi4O16] and [SiO4] units",
        "High-Temperature Flux Growth as a Tool for the Preparation of Mixed-Framework Metal-Y Silicates: A Systematic Evaluation of the Influence of Experimental Parameters",
        "Crystal Growth and Structural Refinements of the Y2SiO5, Y2Si2O7 and LaBSiO5 Single Crystals"
      ]
    },
    {
      "subtopic": "替代与成相控制",
      "hits": 5,
      "year_span": [1999, 2022],
      "gap": false,
      "sample": [
        "Phase transition and crystal structures of BaZn2Si2O7",
        "Thermal expansion of Ba2ZnSi2O7, BaZnSiO4 and the solid solution series BaZn2-xMgxSi2O7 studied by high-temperature X-ray diffraction and dilatometry",
        "Solid solutions based on BaZn2Si2O7 with thermal expansions from negative to highly positive - a review"
      ]
    },
    {
      "subtopic": "产物与证据质量",
      "hits": 7,
      "year_span": [1993, 2024],
      "gap": false,
      "sample": [
        "Ba5Y12Zn[O(SiO4)]8: a novel non-centrosymmetric silicate with a short ultraviolet cut-off edge featuring [ZnSi4O16] and [SiO4] units",
        "A novel crystal structure type shown by a flux-grown tetragonal Ba-Y-silicate and its isotypic Ho-analogue",
        "Synthesis, Crystal Structure, and Dielectric Properties of BaxY26Si16O71+x (x ≈ 10.2)"
      ]
    },
    {
      "subtopic": "条件对照与可复现建议",
      "hits": 14,
      "year_span": [1973, 2024],
      "gap": false,
      "sample": [
        "Ba5Y12Zn[O(SiO4)]8: a novel non-centrosymmetric silicate with a short ultraviolet cut-off edge featuring [ZnSi4O16] and [SiO4] units",
        "Syntheses, crystal structures and crystal chemistry of new mixed-framework silicates and a new molybdate structure type",
        "High-Temperature Flux Growth as a Tool for the Preparation of Mixed-Framework Metal-Y Silicates: A Systematic Evaluation of the Influence of Experimental Parameters"
      ]
    }
  ],
  "gaps": ["身份与记号核验"],
  "verdict": "GAPS_FOUND",
  "advice": "对 gaps 子主题换关键词重搜 + 对已命中论文 snowball"
}
```

## `niche-balanced` 重算结果

| 项目 | 实际 | 重算阈值 | 判定 |
|---|---:|---:|---|
| 总库规模 | 63 | ≥50 | **PASS** |
| 身份与记号核验 | 1 篇直接原始论文；精确式/DOI/双向引文链末轮新增 0 | ≥1 且检索收敛 | **PASS（档位）/残余单源风险** |
| 目标相结构基线 | 16 | ≥12 | **PASS** |
| 结构近邻判据与谱系 | 15 | ≥12 | **PASS** |
| 固相与陶瓷路线 | 8 | ≥5 | **PASS** |
| 晶体生长及助熔路线 | 6 | ≥5 | **PASS** |
| 替代与成相控制 | 5 | ≥5 | **PASS** |
| 产物与证据质量 | 7 | ≥5 | **PASS** |
| 条件对照与可复现建议 | 14 | ≥5 | **PASS** |
| 可确认综述类 | 3 | ≥3 | **PASS** |
| 2024–2026 | 9/63 = 14.29% | ≥10% | **PASS** |

阈值按证据角色分层：结构核心保留双位数要求；路线/控制/证据叶采用工具的
`<5` gap 边界；首次报道相的身份叶不制造 15 篇配额，而以“直接原始论文存在 +
精确检索和双向滚雪球收敛”验收。该重算在现有 63 条上全部达到，但不能消除只有
1 篇目标主文、没有独立重复合成的证据缺口。

## 原 Comprehensive 配额逐项审计（未完成）

| 项目 | 实际 | 配额 | 审计 |
|---|---:|---:|---|
| 总库规模 | 63 | 100–150 | **WARN**：距下限少 37；严格范围内检索已收敛，禁止用弱相关补齐 |
| 身份与记号核验 | 1 | ≥15 | **WARN**；同时是工具默认 `<5` gap |
| 目标相结构基线 | 16 | ≥15 | 数值达标；但含结构比较相，不能把 16 条都解释为目标直接论文 |
| 结构近邻判据与谱系 | 15 | ≥15 | 数值恰达标；关系等级仍须逐篇按 A/B/C 审计 |
| 固相与陶瓷路线 | 8 | ≥15 | **WARN**，少 7 |
| 晶体生长及助熔路线 | 6 | ≥15 | **WARN**，少 9 |
| 替代与成相控制 | 5 | ≥15 | **WARN**，少 10；工具默认阈值为 `<5`，故未自动列 gap |
| 产物与证据质量 | 7 | ≥15 | **WARN**，少 8 |
| 条件对照与可复现建议 | 14 | ≥15 | **WARN**，少 1 |
| 可确认综述类 | 3 | ≥8 | **WARN**，少 5 |
| 2024–2026 | 9/63 = 14.29% | ≥30% | **WARN**；在当前 N 下需至少 19 条，少 10 |

### 综述类人工复核

确认的 3 个综述/综述性入口为：Felsche (1973), *The crystal chemistry of the
rare-earth silicates*；Sun et al. (2014), *Recent progress on synthesis,
multi-scale structure, and properties of Y-Si-O oxides*；Thieme & Rüssel
(2022), *Solid solutions based on BaZn2Si2O7 ... - a review*。题名中仅出现
“crystal chemistry”的原始结构精修论文不因关键词而误计为综述。

### 近三年原始计数

- 2024：7 条；2025：1 条；2026：1 条；合计 9 条。
- 其中 2025 的 `LiBa2GaSi2O8` 在切片日志中只标为目标论文前引语境，尚无
  目标同型/同拓扑证据。因此 14.29% 已是按整库计算的宽口径上限，而不是 9 条
  全部强相关的声明。

## 补检与最终判定

- 对明确 gap 既有三轮定向补检为：身份别名、目标合成字段、近同晶胞家族/
  综述/2024–2026；当时原生五源受网络权限限制，网页复核只恢复已入库目标论文
  或无结构关系结果，逐轮新增为 `0, 0, 0`。
- I6 于 2026-09-01 追加一次有界且不重复近义词的结构家族补检。三式为
  `"flux-grown tetragonal Ba-Y-silicate" Ho isotypic`、
  `"Ba5+xY13Si8O41" "I-42m" synthesis`、
  `"Ba5Y13[SiO4]8O8.5" flux crystal structure`；原生检索请求
  arXiv/OpenAlex/Semantic Scholar/Crossref/DBLP（每源 10），并在
  Semantic Scholar 限流后用 OpenAlex/Crossref 定向恢复。唯一相关命中是已
  入库的 DOI `10.1039/D4SC04440A`，新增 0。
- 同轮对目标主文 `10.1039/D3NJ04480G`、2024 近同晶胞论文
  `10.1039/D4SC04440A`、2017 助熔系统研究 `10.1021/acs.cgd.6b01448`
  和 2022 综述 `10.1039/D2CE00667G` 各做 `both`、每方向最多 12 条的滚雪球。
  新题名均为不同拓扑稀土硅酸盐、通用助熔方法或仅光学前引；出版者结构信息
  复核后无一满足 scope，滚雪球新增 0。完整计数、错误和排除依据见 search_log。
- 三切片此前也记录了结构式、目标 DOI/ESI、综述参考文献、前后向滚雪球与
  `Ba5Ln12Zn`/关系术语等收敛查询。可复现查询与 errors 全部保存在统一日志。
- 真实相关文献不足 comprehensive 的 100 条及多个分层配额。将一般
  Ba–Y–Zn–Si–O 性能材料、供应商页、光学 forward-link 或仅组成相近相加入库
  会违反 scope 的晶体学证据边界。
- 正式降级依据：四个定向补检轮的边际新增序列为 `0, 0, 0, 0`；I6 轮公共
  学术接口已恢复可用，仍无严格相关新增，说明主要限制是窄主题证据体量，而不再
  只归因于旧轮 API 网络限制。
- 最终判定：`niche-balanced` 重算配额达到；`lit_coverage` 仍记 **WARN**，
  因通用 coverage 工具对身份叶仍返回 `GAPS_FOUND`，且目标相只有 1 篇直接论文、
  无独立重复合成。**没有完成 comprehensive，也不作 comprehensive 声称。**
