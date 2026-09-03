I12 已处理完成，未修改正文。

- 将 Fig. 3 从 13 个节点压缩为 10 个节点，合并过密描述。
- 重排为清晰的“工艺/化学 → 微结构 → 离子电导率 → 测量可比性”主线。
- 为 tortuosity、conditions、thermal、interface、uncertainty 和 feedback 连线加入 waypoints，消除交叉与边标签重叠。
- 所有标题、节点、副文、边标签和注释均达到 lint 的 4.5 pt 下限。
- `validate_figspec`: `ok=true`，无 errors/typo_errors；仅保留已在审计中说明的三色系提示。
- `render_figure` 已同步更新 SVG 与 Draw.io；Draw.io XML 包含 11 条原生 source/target 连接器。
- `academic_language_guard`: PASS。
- I12 已关闭；`figures_ready`: PASS。Draw.io Desktop PNG 导出因主机未安装 CLI，已记录为非阻塞说明。

关键产物：

- [fig3_coupled_variables.svg](<HOME>
- [fig3_coupled_variables.drawio](<HOME>
- [fig3_coupled_variables.json](<HOME>
- [figure_plan.md](<HOME>