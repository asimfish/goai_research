---
name: goai-figure-editable
description: Use when an existing figure image/SVG must become an editable drawio file — 图转可编辑 agent：结构化 SVG 走确定性逆向，位图/PDF 图走「视觉重建 figspec → 渲染 → 对照自检 → 修正」回环，输出 .drawio 原生可编辑文件并接入 draw.io 工具链。触发词：「转成可编辑」「图转 drawio」「editable figure」。
---

# GoAI Figure-Editable —— 图 → drawio 可编辑重建 agent

把「一张定死的图」变成「可继续编辑的图」。核心是重建循环
（重建 → 自我检查 → 页内修正）加分层策略：**可读文字恢复为原生文本、
简单几何恢复为原生形状、复杂视觉元素保留为独立资产并记录来源**。

## 路由：先判输入类型

| 输入 | 路线 |
|---|---|
| 结构化 SVG（矢量框图） | 路线 A：确定性逆向（一条工具调用） |
| 位图 PNG/JPG、PDF 里的图、复杂 SVG | 路线 B：视觉重建回环 |
| 本仓库 figspec 渲染出的图 | 不用转——figspec 就是源，直接改重渲染 |

**先想清楚是否值得转**：视觉重建回环需要多轮读图与渲染对照，token 成本
明显高于普通画图。若用户只想微调图里一两处内容，直接改源
（figspec/绘图代码）或让图像模型局部重绘往往更省；只有确有持续编辑
需求时才走本流程。弱视觉模型跑路线 B 效果不保证，读图没把握时应
提前告知用户预期折扣。

## 多图输入

多张图或一份 PDF 里多处图一起转时：先逐图拆成独立子任务（笔记按
`rebuild_<name>_p01.md` 起编号，跟随源顺序），每张图独立走下面的回环，
产物互不覆盖。宿主支持并行 subagent 时可按并发槽位分派，但每个子任务
只写自己的目录。全部完成后汇总一份总清单：每张图的路线、轮数、遗留差异。

## 路线 A：确定性逆向

```
svg_file_to_drawio(svg_path, out_path)
```
产物：`.drawio` + `.recovered.figspec.json`。随后**必须**做对照检查：
打开恢复出的 figspec 数一遍 nodes/edges/texts 与原图是否一致
（工具返回的 stats 计数做首轮对账）；
文本吸附错位、边吸附错节点是已知弱点，发现就手改 figspec 再
`render_figure` 重出。曲线路径与渐变会丢失——如实告知用户损失清单。
检查结论写入 `workspace/notes/rebuild_<name>.md`：发现了什么、改了什么。

## 路线 B：视觉重建回环（≤3 轮）

1. **读图列清单**：用视觉能力仔细看原图，产出结构清单：
   - 节点：文字、形状、相对位置（行列）、配色、分组归属
   - 边：起终点、方向、虚实、label
   - 独立文本与图例
   把清单写进 `workspace/notes/rebuild_<name>.md`（这是审计痕迹）。
   **文字测量（有条件必做）**：若本机有可用的 OCR 能力（PaddleOCR、
   macOS Vision、tesseract 均可），先对原图跑一遍文字检测，把每条文字的
   框坐标、实测字高和识别内容写进清单；重建时以测量值定 x/y/font_size，
   同一层级的文字统一取同组字号，不靠目测。无 OCR 可用时退化为目测，
   并在收工说明里注明「文字位置为目测，未经测量校正」。
2. **清单 → figspec**：按清单写 figspec（坐标自己排版：同层等距、
   分组包络成员留 16px 内边距）。颜色用取色近似即可，结构必须一致。
3. **渲染对照**：`render_figure` 出 svg/png，与原图并排对比：
   - 缺节点/缺边/文字错 = blocker，修 figspec 重来
   - 布局比例差异 = 可接受（可编辑性优先于像素还原）
   每轮对照后，把检查结论追加写入 `workspace/notes/rebuild_<name>.md`：
   轮次、发现的 blocker（缺节点/缺边/文字错/资产缺失，逐条列出）、
   本轮修正动作、是否收敛。末轮附终局对账：原图清单条目数 vs figspec
   条目数 vs 渲染结果三方一致才算过——这份记录就是本次重建的验收凭据。
4. **复杂元素分层**：照片/纹理/手绘装饰不要试图矢量化——在 figspec 里
   用占位节点标注 `label:"[asset: xxx]"`，同时把原图裁剪件存
   `workspace/figures/assets/`（命名 `<图名>_asset_<i>.png`），并在重建
   笔记里记一行来源：源文件、裁剪区域（x, y, w, h）、对应 figspec 占位
   节点 id——保证日后能追溯每个资产从哪来、贴回哪；
   drawio 里由用户拖入替换。
   3 轮后结构仍对不上 → 停，把差异清单交给用户决策。

## 接入 draw.io 工具链

- `.drawio` 文件：draw.io Desktop（`brew install --cask drawio`）或
  app.diagrams.net 直接打开。
- 官方 MCP：宿主配置 `npx @drawio/mcp` 后，可把 render 出的 XML 交
  `open_drawio_xml` 在浏览器即时打开（含避障重排 routing=libavoid）；
  Mermaid/CSV 输入也可走其 `open_drawio_mermaid` / `open_drawio_csv`。
- 回导出：`drawio_export(drawio_path, fmt=png|svg|pdf)`（需 Desktop CLI）。

## 硬性规则

- 视觉相似 ≠ 可编辑达标：验收看三样——文字是原生文本、形状可拖拽、
  连线跟随节点（.drawio 里 source/target 绑定）。
- 文字逐条对账：原图里每条可读文字都必须能在 figspec（节点 label /
  边 label / 独立 text）里找到归属，缺一条即 blocker；
  路线 A 用工具返回的 nodes/edges/texts 计数做首轮对账。
- 每次重建都保留 figspec——它是后续一切修改的单一事实源。
- 不虚构原图没有的内容；看不清的文字标 `[?]` 请用户确认。
- 收工 `loopctl log --stage figures --agent goai-figure-editable
  --event rebuilt --detail "<name> 路线A/B，N 轮收敛"`。
