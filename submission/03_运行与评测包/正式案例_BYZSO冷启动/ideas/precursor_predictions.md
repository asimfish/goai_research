# 两步无机逆合成 MCP 预测记录

本记录来自 `goai-retro` 的真实 stdio MCP 调用。模型按“Stage 1 单前驱体检索—化学硬过滤—Stage 2 前驱体组合重排”运行，设备为 `cuda:0`。完整请求与返回保存在 `workspace/state/tool_calls.jsonl`（UTC 时间 2026-09-01 16:53:02、16:55:44 与 16:55:45）。

- Stage 1 checkpoint SHA-256：`f302cb315a607eaf461281ef65585489eb814b1db7c5e41e56aaa9193965a53e`
- Stage 2 checkpoint SHA-256：`373ee6bdaf562f4ee70b06e515d5b84a18db8c6dbd2d4e2fd7dea864272465de`
- 每个目标均取 Top-5；`top_m=30`，`pool_cap=15`，枚举 4928 个 2--5 元前驱体组合。
- `model_output_verified=true` 只表示模型完成了可复核推理；所有路线均为 `chemical_route_verified=false`，不得写成实验验证结论。

## 目标相 Ba5Y12ZnSi8O40

| 排名 | 前驱体组合 | 候选池内概率 |
|---:|---|---:|
| 1 | ZnO + Y2O3 + SiO2 + BaCO3 | 0.5941 |
| 2 | ZnO + Y2O3 + SiO2 + BaCO3 + BaO | 0.0302 |
| 3 | ZnO + Y2O3 + SiO2 + BaCO3 + BaF2 | 0.0211 |
| 4 | ZnO + Y2O3 + SiO2 + BaCO3 + SiH2O3 | 0.0151 |
| 5 | ZnO + Y2O3 + SiO2 + BaCO3 + Ba(NO3)2 | 0.0132 |

只有排名 1 同时具有较高组合概率和常规、可解释的氧化物/碳酸盐原料集合。排名 2--5 包含冗余 Ba 源、含氟盐、非常规数据库标签或低概率附加物，只保留为模型失效模式与候选池诊断；其中 BaF2 还会引入额外 EHS 与坩埚相容性问题。

## Mg 类比目标 Ba5Y12MgSi8O40

| 排名 | 前驱体组合 | 候选池内概率 |
|---:|---|---:|
| 1 | Y2O3 + BaCO3 + SiO2 + MgO | 0.5220 |
| 2 | Y2O3 + BaCO3 + SiO2 + Mg5H2(C2O7)2 | 0.0316 |
| 3 | Y2O3 + BaCO3 + SiO2 + MgCO3 | 0.0302 |
| 4 | Y2O3 + BaCO3 + SiO2 + MgO + BaO | 0.0279 |
| 5 | Y2O3 + BaCO3 + SiO2 + MgO + MgCO3 | 0.0269 |

排名 1 明显优于其余组合。Mg 类比实验若开展，应以 MgO 作为首选 Mg 源；MgCO3 只适合作为单独的前驱体形态对照，不与 MgO 同时加入。

## Co 类比目标 Ba5Y12CoSi8O40

| 排名 | 前驱体组合 | 候选池内概率 |
|---:|---|---:|
| 1 | Y2O3 + BaCO3 + SiO2 + Co3O4 | 0.2978 |
| 2 | Y2O3 + BaCO3 + SiO2 + CoO | 0.0953 |
| 3 | Y2O3 + BaCO3 + SiO2 + Co2O3 | 0.0890 |
| 4 | Y2O3 + BaCO3 + SiO2 + CoCO3 | 0.0375 |
| 5 | Y2O3 + BaCO3 + SiO2 + Co3O4 + BaO | 0.0167 |

Co 的前三条路线反映氧化态不确定性，而不是三条等价处方。若用 Co 作为位点/价态探针，必须把氧分压、烧前后 Co 价态与相组成联合测量；正文只把 Co3O4 作为空气条件下的首个模型候选，不把排序解释为热力学稳定性。

## 规范化显示问题

模型依赖的组成解析器把输入 `Ba5Y12MSi8O40` 显示为 `Ba5Y12M(SiO5)8`。这只是元素组成的约分/括号化显示，不是对 `[O(SiO4)]8` 结构基团的判断。论文正文一律保留用户指定的结构式与元素式，不采用该显示作为晶体化学描述。
