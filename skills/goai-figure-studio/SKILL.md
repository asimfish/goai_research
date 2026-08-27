---
name: goai-figure-studio
description: Use when the survey needs publication-quality figures — 画图 agent：顶会级主图走「策略合同 → AI 生图两轮候选 → 可编辑化重建」三段管线，辅助图走 figspec 直渲；产物恒为 svg+drawio 可编辑双格式。触发词：「画图」「框架图」「taxonomy 图」「figure」。
---

# GoAI Figure-Studio —— 论文图纸 agent

方法论四支柱：**源忠实、edge-label-first、模块化不碎片化、克制配色**。
执行形态是**自动化回环**：不等人逐步确认，候选生成与审计全自动收敛，
人只看最终产物。工具来自 MCP server `goai-figure`。

## 图纸分级（先分级再动手）

| 级别 | 适用 | 管线 |
|---|---|---|
| **主图** | taxonomy 总览、框架/机制图、领域地图（读者记住综述靠它） | 三段式：A 策略合同 → B AI 生图两轮候选 → C 可编辑化重建 |
| **辅助图** | 时间线、简单流程、统计示意 | A 策略合同 → figspec 直渲（跳过 B/C） |

对比矩阵优先建议用表格，不硬画。宿主无生图通道时主图降级走辅助图管线，
`loopctl log --event decision` 记录降级原因。

## Phase A：策略与合同（每图必做，写进 workspace/notes/figure_plan.md）

### A1 三问定生死

- **reader question**：读者看这张图要回答什么问题？
- **visual mainline**：视觉主线（方法流/分类层级/时间演进）？数据流当主线
  仅当综述对象本身是数据/检索/管线。
- **来源锚点**：图上每个模块/箭头对应库内哪些文献或 taxonomy 哪个节点？

### A2 图纸合同（prompt contract，违反即返工）

- **源忠实表**：逐行列出可见模块/边/符号/关键标签，每行标 `direct`（库内
  文献或 taxonomy 直接支撑）、`inferred`（严格推得，写明前提与推理链）、
  `remove`/`revise`；有未处理的 remove/revise 不得进入 B/C。
  「画起来顺」「常见画法」不算证据。
- **边证据账**：每条边能指出上下游端点含义的证据；不画装饰性箭头、
  不画假中继（A 产 x、C 用 x、B 不消费 x，则禁止 A→B 标 x）。
- **edge-label-first**：变量/指标/权重放边 label，不做同级盒子。
- **捆绑连线**：两模块间默认一条线；只有各自携带不同标注量时才许平行
  多线；每种线型在同图内只允许一个含义。
- **核心模块非空盒**：核心方法族模块要画出可见内部机制（步骤 token/
  判定门/fork-merge/轻量反馈环），保持「输入→操作→输出」最小链，
  不省掉操作、也不膨胀成第二张算法图。
- **符号一一对应**：同一符号/颜色不表示两个概念，反之亦然。
- **重复实体压缩**：重复家族默认压缩成标记（chips/branch），
  不复制整条流水线。
- **模糊指令规范化**：上游给的模糊视觉指令（「体现方法差异」）先翻译成
  具体含义/安全画法/禁止的误实现，翻译不出来退回提问。
- **可见文字白名单**：本图允许出现的全部文字，用词与 taxonomy/正文一致。
- **配色合同**：优先采用 `workspace/style_bank/figure_style_cards.md` 的
  领域配色基准；无风格库时一主一辅 + 灰阶可读。**禁**：AI 蓝紫渐变、
  霓虹饱和、玻璃球高光、bokeh、营销海报打光、装饰性色带。
- **密度预算**：主内容占画面中心，模块数落在风格卡舒适区间；
  大片空白、微块散射、头重脚轻的背景横幅都是阻塞项。

## Phase B：AI 生图两轮候选（仅主图）

生图路由：Codex 宿主用 `image_gen`；Cursor 宿主用 GenerateImage 工具；
均无 → 降级辅助图管线并记账。风格参照：prompt 附
`workspace/style_bank/exemplar_figures/` 的范图路径（支持 reference image
的通道传入；不支持则在 prompt 里文字化描述风格卡要点）。

### B1 第一轮：4 候选草图探索

- 基于 A2 合同写 4 份 prompt（同一语义骨架 × 不同叙事/布局组合：
  如横向流水线/纵向层级/中心辐射/分区地图），每份 prompt 内嵌
  合同硬约束块（源忠实清单、edge-label-first、配色合同、密度预算、
  文字白名单——生图模型渲染文字不可靠，白名单文字要求「位置留槽、
  拼写尽力」，最终以 Phase C 重建版为准）。
- 逐一生图得 `workspace/figures/candidates/<fig>/c01-c04.png`。

### B2 自动审计与方向选择（issue-ledger 式，不跳过）

- 用 Read 逐张审图，对照 A2 合同记 issue ledger（写入 figure_plan.md）：
  变量画成盒子？装饰箭头/假中继？同义平行线？核心模块空盒？主线偏心？
  密度失衡？AI 味配色？与源忠实表冲突的结构？
- 按「合同违反数 + 主线清晰度 + 风格卡贴合度」选出方向候选 1 张，
  并列出它要修的 issue 与要保留的视觉精华。

### B3 第二轮：2 正式候选

- 以胜出方向为主线重写 2 份 prompt（携带其视觉精华 + 逐条修复 B2 issue
  + 支持通道时附胜出草图为 reference image），生成
  `f01.png / f02.png`。生图模型对**箭头方向类指令不可靠**（实测明示
  方向仍被反转）：方向敏感边在两份 prompt 里用不同 routing 表述对冲，
  审计时把方向核对列为必查项。生图工具落盘在会话资产目录时，
  须 cp 归档进 `candidates/` 再审计。
- 再审一轮：两张都过合同审计 → 选综合最优 1 张为**参照定稿**；
  都有硬伤 → 取伤少者，硬伤记入 ledger 交 Phase C 重建时修正
  （重建是矢量级控制，能修生图模型改不动的毛病）。两轮共 6 次生图为
  预算上限，不许无限重试。

## Phase C：可编辑化重建（测量驱动，仅主图）

把参照定稿重建为 figspec，产出可编辑矢量——这是交付物的唯一来源，
AI 栅格只是参照。方法论吸收测量驱动重建：**先测量、再重建、后对照**。

1. **测量**：Read 参照图，逐区域记录版式测量表（模块相对位置/尺寸、
   连线拓扑、颜色采样 hex、文字内容与层级）——写进 figure_plan.md
   的重建测量节。
2. **重建**：`figspec_schema()` 拿 schema → 按测量表写 figspec（文字用
   白名单矫正生图拼写错误；结构以 A2 合同为准，参照图与合同冲突时
   **合同赢**）→ `validate_figspec` → `render_figure`。
   figspec 实战要点：深色头带白字用 node 的 `label_color`/`label_bold`；
   标题样式用顶层 `title_style`；边默认色在 defaults 里键名是
   `edge_color`/`edge_width`；自动折行按宽度硬切会切词——多词 label
   一律手工 `\n` 控行；边只能连 node 不能连 group——「连到分组带」的
   合同边用组边缘的隐形锚点小节点（`label:"", fill/stroke 同组底色`）
   落点；超长 edge label 改用 texts 独立摆放。
   **出版级版式硬规范**（实测迭代出的顶会观感底线，重建时按此自查）：
   - 密度是**双向约束**：画布宽 ≤ 正文字号×122（防稀疏），同时留足
     呼吸空间（防拥挤，见下）。稀疏时首选**全局坐标等比缩小而字号
     不变**；缩后必须复查下面的拥挤下限，压过头比稀疏更难看。
   - 拥挤下限（任何一条不满足就放宽画布，勿缩字号）：
     列间若放注释文字，走廊宽 ≥ 注释最宽行宽×1.15（三行窄注释优于
     两行宽注释）；同列卡片纵向间隙 ≥ 字号×0.9；注释/独立文字距
     画布边缘 ≥ 字号×0.8，禁止顶边。
   - 层次四件套：标题带/头带 `shadow:true` + 深底白粗字；卡片白底 +
     中饱和度描边 `stroke_width≥1.6`；容器淡色底（非纯白）+ 浅描边；
     主链边 `width≥3`（箭头随线宽自动放大）。
   - 强调元素（如 Route-C 归属叶）用辅色描边 + 加粗 `stroke_width:2`
     单独高亮；徽章用 stadium 小节点直接携带 `label_color` 文字，
     不要 texts 绕行。徽章**不许骑跨带文字卡片的边缘**（会遮字）——
     外置到母卡正下方、间隙 ≈4px 表从属。
   - 边的出点要避让徽章等贴附元素：必要时加一个与源卡片中心同高的
     waypoint，强制从卡片左/右缘干净出线，禁止斜穿贴附徽章。
   - 各区纵向空隙 ≤ 正文字号×4；图例/脚注紧贴主体（空隙 ≤ 字号×5），
     禁止大片下部留白；图例各组文字间距按实测文字宽排布，禁止重叠。
3. **对照自检（≤3 轮）**：对照 png 以 `drawio_export` 导出为准
   （render_figure 的 cairosvg 光栅无字体 fallback，`→/ν/≥` 等字符
   可能画成豆腐块，勿据此误判；SVG/drawio 源码文字以逐字符核对为准）。
   Read 导出 png 与参照图并排对照——
   布局拓扑一致？模块/边无缺漏？文字 ⊆ 白名单（逐字）？配色贴合？
   渲染级检查：文字溢出？连线穿节点？分组框住成员？
   语义级：B2/B3 遗留 issue 是否已在重建中修复？
   注意 drawio 导出按内容裁边、坐标系与画布不同：waypoint/几何对账
   以 .drawio XML 为准，不做导出图的像素级坐标对账。
   有问题改 figspec 重渲染；3 轮后仍有硬伤记 issue 交人决策。
4. 辅助图跳过 1-2，直接按 A2 合同写 figspec 走 3 的检查单。

## 交付与登记

- 每图四件套：`workspace/figures/svg/<name>.svg`（论文侧，LaTeX 用
  `drawio_export` 转 pdf/png 嵌入）、`drawio/<name>.drawio`（draw.io
  Desktop / app.diagrams.net 直接可编辑）、`figspec/<name>.json`
  （单一事实源）、主图另附 `candidates/<fig>/`（两轮候选与参照定稿，
  审计可溯源）。
- 每图写 caption 草稿（图讲什么 + 符号约定）存 figure_plan.md 供 writer。
- 全部图完成后 `loopctl gate --name figures_ready --status PASS
  --detail "<N 图 svg+drawio 齐；主图 M 张走两轮候选制（6 生图/图上限），
  审计 ledger 在 figure_plan.md>"`。独立图纸任务（无 loop 会话、
  `state/ledger.json` 未 init）不必强行 gate——交付登记写进
  figure_plan.md 即可。

## 硬性规则

- 交付物必须可编辑（svg+drawio）；位图永不直接进论文图池。
- 两轮候选的每张生图、每条 ledger issue、每次重建对照都要在
  figure_plan.md 留痕——审计链完整才许过闸。
- 风格库缺失不阻塞：按合同默认配色执行并记账。
