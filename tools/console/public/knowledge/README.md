# 知识图谱浏览（控制台 · 结果预览）

控制台「结果预览」页的预览区分为两个视图：**报告浏览**（综述 PDF）与**知识图谱浏览**（本目录的页面）。

| 文件 | 说明 |
|---|---|
| `knowledge_layers.html` | SAGE-Mat 知识森林「逐层展开」页，单文件、内嵌数据；由 `docs/competition/knowledge_graph/build_graph.py` 生成（`layers_template.html` 注入 `graph.json` 与图标）。控制台以 `?theme=console` 嵌入：字体与配色对应 `src/style.css` 的循证台系统（纸张白 / 深墨蓝 / 铜绿 / 琥珀 / 朱砂，Noto Sans SC） |
| `graph.json` | 图数据（`meta` 统计与阶段说明、`nodes`、`edges`），与页面内嵌的数据一致，供脚本或核对使用 |
| `results-tab.js` | 结果预览页的预览切换（运行时补丁）。当前 `dist/` 由带 `goai_final_lab` 同级仓库的机器构建，本地无法重建；源码版本在 `src/views/ResultsView.vue`（`.preview-switch`），重建 dist 后本脚本自动退出，可一并删除 |

页面参数：`?theme=console` 控制台主题；`?level=1..9` 停在某级（第 9 级为全貌）；`?select=<节点 id>` 打开某节点的详情；`?autoplay=1` 自动播放；`?movie=1` 隐藏控件。

数据来源：BYZSO 正式案例的证据包（`inputs/scope.md`、`notes/taxonomy.md`、`references.bib`、`papers.jsonl`、`claim_evidence.jsonl`、`03_condition_matrix.tex`、`ideas/*.md`、补充案例 `ledger.json`），全部数字与证据包一致；前驱体预测均为 `chemical_route_verified=false`，工作流均为仿真。

更新方式：在 `docs/competition/knowledge_graph/` 运行 `python3 build_graph.py`，再把生成的 `knowledge_layers.html` 与 `graph.json` 复制到本目录（以及 `dist/knowledge/`，直到 dist 重建）。
