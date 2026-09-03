诊断图视觉问题已修复，未改变 taxonomy 语义或 gate：

- `diag` 中心调整为 `x=268`；drawio 红字包围盒 `(0.25,733)–(535.75,757)`，未越出 `1500×820` 画布。
- 三条主链标签改为 `powder`、`phase state`、`ceramic`。
- 已同步边证据账、文字白名单和自检记录。
- 真实调用 `validate_figspec`：全部通过，无 warning。
- 真实调用 `render_figure`，覆盖同名 [SVG](<HOME> 和 [drawio](<HOME>
- 两种格式中三个标签均存在。
- 已在 [figure_plan.md](<HOME> 登记为 lint 漏检，未声称使用图像视觉工具。
- 已记录 `diagnostic_repair`；所有 gate 状态保持不变。