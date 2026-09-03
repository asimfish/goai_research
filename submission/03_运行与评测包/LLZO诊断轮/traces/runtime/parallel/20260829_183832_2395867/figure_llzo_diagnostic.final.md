已完成“LLZO synthesis-to-performance process map”诊断辅助图。

产物：

- [Phase A 合同与自检记录](<HOME>
- [figspec 单一事实源](<HOME>
- [SVG](<HOME>
- [可编辑 drawio](<HOME>

验证结果：

- 真实调用 `figspec_schema`、`validate_figspec` 和 `render_figure`
- 最终校验无 errors、typo errors 或 warnings
- 29 项白名单文字在 SVG/drawio 中齐全
- 5 条边的端点、方向和实虚线语义通过检查
- PNG 因环境缺少 draw.io Desktop CLI 未生成
- 已记录 `diagnostic_done`
- `taxonomy_ready` 仍为 `PENDING`，未设置 `figures_ready PASS`
- 已明确登记“跳过AI候选、降级figspec直渲、非正式交付”