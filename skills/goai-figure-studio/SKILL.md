---
name: goai-figure-studio
description: Use when the survey needs publication-quality figures — 画图 agent：为综述设计并生成框架图/分类法树/时间线/对比图，figspec 单一事实源，一次渲染同时产出论文用 SVG 与 drawio 原生可编辑文件，带自检-修正回环。触发词：「画图」「框架图」「taxonomy 图」「figure」。
---

# GoAI Figure-Studio —— 论文图纸 agent

方法论四支柱：**源忠实、edge-label-first、模块化不碎片化、克制配色**。
执行形态是**自动化回环**：不等人逐步确认，用「渲染 → 自检 → 修正」
循环收敛，人只看最终候选。
工具来自 MCP server `goai-figure`；产物天然接 draw.io（原生 .drawio）。

## 综述常用图型

| 图型 | 用途 | figspec 要点 |
|---|---|---|
| 分类法树 | 综述主图 | groups 做层级底板，nodes 分层排布，每叶标代表文献 |
| 时间线 | 领域演进 | 横轴年份 texts + 里程碑 nodes，edges 用 arrow=none |
| 框架/流水线图 | 方法族抽象 | 主线居中，变量走边 label |
| 对比矩阵示意 | 方法族 × 能力 | 表格更合适时直接建议用表，不硬画 |

## 规程（每张图一个回环）

### 1. 图纸计划（写进 workspace/notes/figure_plan.md）

每图先回答三问，答不出就不画：
- **reader question**：读者看这张图要回答什么问题？
- **visual mainline**：视觉主线是什么（方法流/分类层级/时间演进）？
  数据流当主线仅当综述对象本身是数据/检索/管线。
- **来源锚点**：图上每个模块/箭头对应库内哪些文献或 taxonomy 哪个节点？

### 2. figspec 编写

先 `figspec_schema()` 拿 schema 与示例，再写 spec。强制约束
（prompt contract，违反即返工）：
- 每条边能指出证据锚点；不画装饰性箭头、不画假中继
  （A 产 x、C 用 x、B 不消费 x，则禁止 A→B 标 x）；
- 变量/指标/权重放**边 label**，不做同级盒子；
- 模块化不碎片化：主内容占画面中心，避免大片空白与微块散射；
- 同一符号/颜色不表示两个概念；
- 配色 human palette：一主一辅 + 灰阶可读，禁霓虹渐变、禁玻璃球高光；
- 重复实体家族默认压缩成标记（chips/branch），不复制整条流水线。

### 3. 渲染与自检回环（≤3 轮）

1. `validate_figspec` → 有错先修。
2. `render_figure(figspec_json, name, out_dir="workspace/figures")`
   → 同时得到 svg / drawio / figspec（+png 若装了 cairosvg）。
3. **自检**：用 Read 工具看渲染产物（png 优先，无 png 读 svg 源码核对坐标），
   对照检查单：文字溢出盒子？连线穿过节点？主线居中？分组框住了成员？
   label 与 taxonomy 用词一致？
4. 有问题改 figspec 重渲染。3 轮后仍有硬伤 → 记 issue 交人决策，不死磕。

### 4. 交付与登记

- 论文侧用 `workspace/figures/svg/<name>.svg`（LaTeX 走 includesvg 或
  `drawio_export` 转 pdf/png）。
- 可编辑侧交 `workspace/figures/drawio/<name>.drawio`——draw.io Desktop /
  app.diagrams.net 直接打开；装了官方 `@drawio/mcp` 的宿主可用其
  `open_drawio_xml` 在浏览器即时打开微调。
- 每图写 caption 草稿（图讲什么 + 符号约定）存 figure_plan.md，供 writer 引用。
- 全部图完成后 `loopctl gate --name figures_ready --status PASS
  --detail "<N 张图 svg+drawio 齐全>"`。

## 与生图模型的关系

本 skill 默认走**确定性 figspec 渲染**（可复现、可编辑、可进 drawio）。
如果宿主有 image-gen 且用户想要手绘感概念图：可先生成概念草图找方向，
但**最终交付物必须重建为 figspec**——位图不可编辑、不进论文图池；
重建流程走 goai-figure-editable。
