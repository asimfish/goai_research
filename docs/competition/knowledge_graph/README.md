# SAGE-Mat 知识森林（知识图谱展示）

把一次调研画成一片森林：最左是研究者开始前自己的问题树（个人知识树），流水线从中长出文献树，
再把文献抽象成可复用的实体主干（化合物 / 相、合成路线、前驱体、条件记录、表征、失败模式），
据此写成结论树并回答最初的目标，最后在结论和缺口上长出新树（前驱体预测、实验方向、自动化工作流、
同根的其他调研）。页面是单文件 HTML，数据全部从提交包里已有的文件确定性生成，不新增任何主张。

| 文件 | 说明 |
|---|---|
| `knowledge_graph.html` | 交互页面（单文件，内嵌 `graph.json`；D3 v7 走 cdnjs）。`?stage=0..4` 指定生长阶段，`?select=<节点 id>` 打开某节点，`?poster=1` 为无界面海报模式（截图用） |
| `graph.json` | 图数据：`meta`（统计、阶段说明、证据等级）、`nodes`、`edges` |
| `build_graph.py` | 生成脚本：`python3 build_graph.py` 重新生成上面两个文件 |
| `template.html` | 页面模板（`build_graph.py` 把 JSON 注入 `/*__GRAPH_JSON__*/null`） |

线上：<https://asimfish.github.io/goai-dashboard/knowledge_graph.html>；
五张阶段海报（3072×1728）在看板 `pdf/gallery/sagemat_knowledge_forest_20260918_stage{0..4}_3072x1728.png`。

## 五层怎么长

| 层 | 节点 | 来源文件 |
|---|---|---|
| 0 个人知识树 | 调研主题 → 5 个预期目标（核心问题）→ 8 个 MECE 子主题 | 正式案例 `inputs/topic.md`、`inputs/scope.md` |
| 1 文献树 | 8 个分支 → 35 个叶节点 → 51 篇通过 ref_gate 的文献；按 D0 / D1 / N1 / P1 / X 证据距离着色，外圈加深 = 全文在证据包内 | 证据包 `notes/taxonomy.md`、`references.bib`、`papers.jsonl`、`claim_evidence_summary.json` |
| 2 实体主干 | 29 个化合物 / 相、6 条合成路线（含水热空白）、17 种前驱体 / 助熔剂 / 坩埚、7 类表征终点、4 类失败模式、29 条逐字段的合成条件记录（A1、B1–B6、C1–C22） | 正式案例 `最终输出/sections/03_condition_matrix.tex` 条件总表；`taxonomy.md` §C–§G；化合物与试剂为人工整理表（脚本内 `CURATED_*`） |
| 3 结论树 | 27 个章节 → 100 条主张；每条主张回连引用文献（强 / 弱、全文、条件溯源）与提到的实体；章节回答第 0 层的目标（已回答 / 部分回答） | 证据包 `claim_evidence.jsonl`；目标 ↔ 章节的对应是人工读稿给出的（脚本内 `Q_MAP`） |
| 4 长出的新树 | 结论 4 条 + 方向 2 条主张；8 条证据缺口；RECIPE 前驱体预测（Zn / Mg / Co 三个目标各 Top-5）；4 个优先实验方向；5 条 OpenLab 自动化工作流（仿真）；3 个补充案例 + LLZO 诊断轮 | `taxonomy.md` §5；`ideas/precursor_predictions.md`；`ideas/experiment_directions.md`；站点 `showcase.html`；各案例 `ledger.json` / `CITATION_AUDIT.md` |

## 连线是怎么算出来的

- 结构线（默认显示）：树的父子、文献 → 叶节点（taxonomy 的支撑 key）、文献 → 条件记录（表格里的 `\texttt{key}`）、条件记录 → 产物 / 路线、章节 → 目标、根 → 新树、新树 → 相关实体。
- 引用线：主张 → 文献来自 `claim_evidence.jsonl` 的 `citation_keys`；主张 → 条件记录来自 `condition_source_trace`。
- 文本匹配线（勾选「全部连线」或悬停时显示）：文献题名 / 条件记录产物字段 / 主张文本里出现化合物别名 → 化合物；条件记录原料与坩埚字段 → 前驱体 / 坩埚；产物与表征字段 → 表征终点。别名表在脚本里，逐条可审。
- 文献的证据等级 = 它支撑的叶节点标题里的等级（如 A2（D1））；叶节点没标等级时取题名里报道的化合物等级；再没有取叶名里写明的等级；否则记 X。

## 边界

- 图里所有数字（51 / 219 / 100 / 54 / 36 / 29）与证据包一致；RECIPE 预测全部为 `chemical_route_verified=false`，工作流全部为仿真，页面上都有标注。
- 目标 3、4 标为「部分回答」，理由写在节点详情里（目标相本身条件字段全为 NA；Zn 固溶范围没有直接证据）。
- 与文献的连线只在页面里展示，不回写任何提交材料。
