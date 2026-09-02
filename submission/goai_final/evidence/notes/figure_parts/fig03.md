# fig03_research_roadmap — 研究路线图合同与审计记录

## 2026-09-02 出版级返工审计

### Phase A 合同

- **Reader question**：如何把文献依据转成可检验的平行实验，并用结果反馈收敛结构假设？
- **Visual mainline**：文献依据 → 结构假设 → 前驱体 → 平行实验 → 结果反馈。
- **来源锚点**：taxonomy 的 A–H 节、scope 的实验边界、contribution 候选 1–3，以及
  `references.bib` 中已核验的 Ba–Y–Si–O、Ba–Zn–Si–O 和 Y–Si–O 体系。
- **可见语义**：保留局部组成网格、Zn–Y–氧计量耦合、模型前驱体、固相成相、高温溶液
  长晶、互补表征和三类科学问题；不使用 D0/D1、gate、ledger、字段、端点或工具箱。

### 参照测量与重建

`academic_style_reference.png` 的 25–30 px 白边、浅灰分区、灰色横条和深蓝灰细描边被
映射为 1500 × 900 画布的上下双区布局：上区单一研究路线容器（五阶段主线，平行实验
上下分叉），下区三张科学问题卡。赭色只用于高温溶液支线和结构假设卡，所有连线正交。

### 对照与交付

- 第 1 轮：确认五阶段顺序、上下分区和三类问题均在画布内。
- 第 2 轮：确认固相/长晶分叉不穿节点，反馈箭头仅回到结构假设，脚注与边缘留白充足。
- 第 3 轮：确认 figspec validate/lint 为 0 error/0 warning；SVG、Draw.io、PNG、单页
  PDF 均由同一事实源生成，XML 可编辑，所有可见字符串为材料学术语。
- 结果：未改正文或 `references.bib`，未设置 `figures_ready` gate。
