已仅修复 ledger I2，未读取或修改 taxonomy 内容。

- 主链改为四个 group 的不可见边缘锚点，不再连接具体路线 chip。
- 新增 `env1 → densification group` 虚线；D1–D3 均落到对应 group 锚点，并用 waypoint 避免交叉。
- 更新了白名单、边证据账、caption、PNG/CLI 状态及自检记录。
- `validate_figspec` 通过，无错误或告警。
- `render_figure` 成功，同源更新 SVG 与 drawio。
- drawio XML 端点、锚点颜色、虚线及 waypoint 检查通过。
- I2 已关闭并完成 `loopctl log`。
- `figures_ready` 未设置，仍保持原状态。

相关文件：[figspec](/home/gaojing/goai_research/workspace/figures/figspec/llzo_process_map.json)、[figure_plan.md](/home/gaojing/goai_research/workspace/notes/figure_plan.md)、[SVG](/home/gaojing/goai_research/workspace/figures/svg/llzo_process_map.svg)、[drawio](/home/gaojing/goai_research/workspace/figures/drawio/llzo_process_map.drawio)。

PNG 已记录为由宿主 Chrome 从 SVG 生成；drawio CLI 仍缺失。本容器内 Chrome 因 crashpad 沙箱限制未能覆盖现有 PNG。