三张图已按 `goai-figure-studio` 完成出版级返工，使用指定的 `academic_style_reference.png` 作为唯一版式参照；科学内容仍来自既有 taxonomy、scope 与核验文献。所有可见文字已移除 D0/D1、gate、ledger、字段、端点、工具箱等内部标记。

产物：

- 图 1：[figspec](<<HOME>>) · [SVG](<<HOME>>) · [Draw.io](<<HOME>>) · [PDF](<<HOME>>) · [PNG](<<HOME>>)
- 图 2：[figspec](<<HOME>>) · [SVG](<<HOME>>) · [Draw.io](<<HOME>>) · [PDF](<<HOME>>) · [PNG](<<HOME>>)
- 图 3：[figspec](<<HOME>>) · [SVG](<<HOME>>) · [Draw.io](<<HOME>>) · [PDF](<<HOME>>) · [PNG](<<HOME>>)

计划与审计记录已更新：[figure_plan.md](<<HOME>>)、[fig01 audit](<<HOME>>)、[fig02 audit](<<HOME>>)、[fig03 audit](<<HOME>>)。

最终检查：三份 figspec 均 `validate/lint = 0 error, 0 warning`；SVG 与 Draw.io 同源复算一致；PNG 有效；PDF 均为单页且方向正常；`academic_language_guard` 通过。Draw.io Desktop CLI 不可用，因此采用仓库本地等价渲染并直接核对 XML 可编辑结构；未修改正文、`references.bib`，也未设置新的 `figures_ready` gate。