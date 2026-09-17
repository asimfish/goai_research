---
name: goai-figure-studio
description: Use when the survey needs publication-quality figures — 画图 agent：顶会级主图走「策略合同 → AI 生图两轮候选 → 可编辑化重建」三段管线，辅助图直接按合同用 lib/ 重建；产物恒为 pptx+svg+矢量 pdf 可编辑三件套（设计系统在 lib/，墨量见 references/ink-budget.md）。触发词：「画图」「框架图」「taxonomy 图」「figure」。
---

# GoAI Figure-Studio —— 论文图纸 agent

方法论四支柱（image-first 流程）：
**源忠实、edge-label-first、模块化不碎片化、克制配色**。
执行形态是**自动化回环**：不等人逐步确认，候选生成与审计全自动收敛，
人只看最终产物。工具来自 MCP server `goai-figure`（Codex 宿主把 MCP 工具**延迟加载**：开场工具清单里看不到 goai-* 不等于没挂，先 `tool_search` 搜 server 名或工具名再调用；只有搜也搜不到才按降级记账、走 `.venv/bin/python -c "from server.… import …"` 直调）。

**image-first 是默认路径**：凡进论文的图，一律先用 AI 生图拿视觉参照、
再按参照用 lib/ 的原生对象重建（scene.json → super_img2ppt）。生图可用于探索构图、
晶体/材料纹理和抽象结构意象；但生图模型生成的文字、化学式、数值和箭头
不具有证据效力，必须在重建阶段由 SVG/Draw.io 原生图元确定性补回。必要时，
可将经审查的生图作为 Draw.io 中的锁定底图或图像图层，再叠加原生文字、节点、
曲线和连接器。**生图本身永远不是论文交付物**。跳过生图直接重建只在无生图
通道时作为降级路径，且必须 `loopctl log --event decision` 记录降级原因。

## 图纸分级（先分级再动手）

| 级别 | 适用 | 管线 |
|---|---|---|
| **主图** | taxonomy 总览、框架/机制图、领域地图（读者记住综述靠它） | 三段式：A 策略合同 → B AI 生图两轮候选（4+2） → C 原生对象重建 |
| **标准图** | **行文路线图（每篇综述必配）**、时间线、多模块流程 | A 策略合同 → B 单轮 2 候选 → C 原生对象重建 |
| **辅助图** | 简单示意、统计小图 | A 策略合同 → 单轮 1 参照图 → lib/ 原生重建（无通道时直接按合同重建） |

对比矩阵优先建议用表格，不硬画。宿主无生图通道时直接按 A2 合同用 lib/ 重建，
记账说明。**行文路线图**（本文组织结构：各节回答什么问题、怎么推进）
是综述标配，writer 蓝图登记后由本 skill 按标准图管线出图。

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
- **学科用语约束**：图面、图例和图注使用材料学中的相组成、结构关系、
  合成条件和表征方法；不得把 agent 内部的“过闸、标签、字段、端点、
  工具箱、降权”等控制术语作为可见文字。优先写“目标化合物直接报道、
  相关结构体系、实验条件、互补表征和可外推范围”等学术表达。
- **配色合同（学术克制是硬约束，花哨即返工）**：优先采用
  `workspace/style_bank/figure_style_cards.md` 的领域配色基准；无风格库
  时一主一辅 + 灰阶可读。顶刊学术图的基线是：白/浅灰卡片底 + 中饱和
  描边 + **全图至多 2 个主题色**（其余信息用灰阶与线型区分）、强调色
  只给 1 个焦点元素；大面积彩色 lane 平铺、每个分组一种鲜艳底色的
  「彩虹泳道」都算花哨，改用浅灰分区 + 描边区分。**禁**：AI 蓝紫渐变、
  霓虹饱和、玻璃球高光、bokeh、营销海报打光、装饰性色带。自查基准：
  与 style_bank 范图并排对照，若明显比范图鲜艳/花哨即违反合同。
- **密度预算**：主内容占画面中心，模块数落在风格卡舒适区间；
  大片空白、微块散射、头重脚轻的背景横幅都是阻塞项。

## Phase B：AI 生图候选（主图两轮 4+2；标准图单轮 2；辅助图单轮 1）

生图路由：Codex 宿主用 `image_gen`；Cursor 宿主用 GenerateImage 工具；
均无 → 跳过 B 段、直接按 A2 合同用 lib/ 重建并记账。风格参照：prompt 附
`workspace/style_bank/exemplar_figures/` 的范图路径（支持 reference image
的通道传入；不支持则在 prompt 里文字化描述风格卡要点）。
标准图/辅助图走本节的裁剪版：跳过 B1 的 4 候选探索，直接按 A2 合同写
prompt 生成 2/1 张参照，过一遍 B2 审计要点后进 Phase C。

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

## Phase A/B 的对接：super_teaser（paper-framework-figure-studio-pro）

主图的策略合同与生图候选按 `asimfish/super_teaser`（v3.2.21）的 S0–S5 契约执行，不另造一套：

- **S0 精读锁**：先写 `figure_plan.md` 的"实体—证据锚点"表（每个模块、连线、符号指向论文的节/图/句），
  再写 `role_visual_realization_contract`（重复角色是否合并、禁止的误画法）。没有证据锚点的箭头不画。
- **S1 策略**：八个"版式语法 × 表面处理"提案打分选四（C01–C04）；版式先于表面（读者问题 → 主线），
  表面只从 super_teaser `references/print-first-style-profiles.md` 的四个印刷优先档位里选（清洁模块 /
  技术线稿 / 编辑式机制 / 注释式机制），配色白底、炭黑线、≤1 强调色，灰度可辨。
- **Prompt 硬约束段**（每条生图 prompt 内必须含）：edge-label-first（变量/指标只在连线、端口、标签上，不作同级模块）；
  两模块之间只有一条捆绑连线；无伪中继；禁止渐变/霓虹/玻璃质感/装饰图标；说明有意抽象掉的细节。
- **S2/S5 只生图**：Codex 用内置 `image_gen`，其余宿主必须显式指定图像 API；**没有图像通道时不得用 SVG/截图冒充生图候选**，
  改走 Phase C 的原生重建（`lib/` + `references/ink-budget.md` 的印刷字号），
  并把 S0/S1 文档与 prompt package 留在 `workspace/figures/studio/` 等通道恢复后补生图。
- **S3 复审只看像素**：对照 S1 的 edge/port 合同逐条记 issue，转成 S4 的负约束；S5 终选后由人决定，agent 不再自动改图。
- 机器人/具身相关的图额外加载 `references/embodied-figure-guide.md`（先锁场景身份、接触、动作含义与时间，再谈风格）。

参考实现与证据：`refs/super_teaser/`（克隆），`final_round/figures/S0_paper_foundation.md`、`S1_figure_strategy.md`。

## Phase C：原生对象重建（交付物的唯一来源）

参照定稿只是视觉参照。**进论文的图是用本 skill 的设计系统重画的**，产出可编辑的
PPTX / SVG / 矢量 PDF。这一步决定质量：一致的墨、一致的图元、可编辑的输出，
以及在重建时修掉生图模型改不动的语义错误。

> 历史：C 段曾走 figspec → svg + drawio。经五轮作者返修后废弃 —— drawio 出的图
> 被明确否掉（「目前画的图还是很丑，不一定必须要 drawio」），且位图裁来的图标
> 导致图元风格不统一。现行路线是原生 scene 对象 + super_img2ppt。

### C1 用设计系统重画

```python
import sys; sys.path.insert(0, 'skills/goai-figure-studio')
from lib import Figure, FAM, TYPE_PT, TYPE_PT_EN

# print_width_pt：图在论文里的放置宽度（用 print_audit.py 从编好的 PDF 里读，不要估）。
# 传了它，所有构件的字号都按「印刷 pt × 角色」换算，正文自动用常规体；不传就是旧的写死 px。
f = Figure(1536, 1024, notes='图 2 …（F01 分层横带 → super_img2ppt 重建）',
           print_width_pt=435.2, type_scale=TYPE_PT)          # 英文：451.4 与 TYPE_PT_EN
z = f.zone('zT', [26, 28, 1484, 402], '实验方法', 'exp')        # 一级：分组带
f.card_stack('c1', [60, 100, 278, 300], '外加助熔',              # 二级：模块卡
             ['溶解', '保温', '缓冷分离'], fam='exp', glyph='beaker', container=z)
f.conn('d0', [(199, 404), (199, 448)], label='配比 · 温度')      # 四级：边标签
f.finish([z]); f.write('workspace/figures/scenes/fig02.json')
```

A2 合同的四级层次在库里各有对应，别压扁成两级：

| 层 | 方法 | 长相 |
|---|---|---|
| 1 宏观分组 | `zone()` | 淡底色带 + 细边 + 小标题 |
| 2 主模块 | `card()` / `card_stack()` / `card_step()` | 白卡 + 左色条 + 一个线描图元 + 粗标题 |
| 3 内部机制 | `chain()` / `vchain()` / `ledger()` / `row()` | 小 token 用短箭头串起来、或带勾选的记录网格 —— **不能是一串句子** |
| 4 标签 | `conn(label=…)` / `pill()` | 变量、记录项、警示，挂在连线和端口上 |

- **色族只有四个**（`FAM`）：`lit` 证据（石板蓝）、`exp` 方法（teal）、`note` 警示（琥珀）、
  `mute` 范围外（灰）。这就是 A2 配色合同的机器化形式：**琥珀只给警示**，不做第五个色族。
- **图元用 `lib/motifs.py` 的 36 个原生线描图元**，一种墨、一种线宽。
  `python3 skills/goai-figure-studio/scripts/glyphs.py` 列清单，
  `… glyphs.py sheet out.json` 出对照表。缺图元就往 `motifs.py` 里加，
  **绝不从生图里裁图标** —— 那正是前三轮图元风格不统一的根因。
- **字号按印刷 pt 定、按角色取**：中文 分组 9.5 / 标题 9 / 步骤号 12 / 正文 8 / 标签 7.5 pt，英文各降一档，
  下限 7 pt。**只有分组名、卡片标题、步骤号加粗**，其余常规体——全加粗等于没有层次。
  **卡片尺寸由内容算出**（先量字再定框，放不下就折行），不要先定整齐的框再往里塞小字。
  实例：`submission/03_运行与评测包/figure_scenes/scenes_r6.py`。
- **墨量、字号、CJK 行高**一律照 `references/ink-budget.md`，改任何线宽/颜色前先看那份。
  数字不是口味，每一条都是作者否掉上一版定出来的；要改就改 `lib/framework.py`，
  让所有图一起动。
- **箭头**由 `conn()` / `chain()` 生成，端点与线段同源计算，不存在「独立摆放的箭头头部」
  这种画法；箭头头长自动小于线段长度。
- **连线标签成行时不要逐个摆**：`finish()` 会调 `pack_pill_rows()` 把同族标签归到本行主 y、
  按序去重叠、整行夹在页内。字串一长（换语言、换术语）逐个摆必然互撞。

### C2 保真修正（重建时必做）

生图模型会编造论文里没有的内容，也会画错方向。实测到过：编造的中文子步骤、
分类图的分支箭头指向枢纽、分叉只喂了两条通道中的一条、非警示的带子用了琥珀。
**逐条对照论文原文核字串**，不成立的删掉，把审计写进 S3 记录 / figure_plan.md。
重建是矢量级控制，正是修这些的地方。详见 `references/pitfalls.md` 的 Fidelity 一节。

### C3 本地预检（0 hard 才许发出去）

```bash
python3 skills/goai-figure-studio/scripts/precheck.py workspace/figures/scenes/*.json
```

用的宽度模型和 `lib.Scene.measure` 同源，提前挡掉 `text_overflow` /
`text_shrunk` / `outside_container` / `unintended_overlap`，省一次远端往返。

### C4 构建与装回

```bash
img2ppt.sh check scene.json --out check/ && img2ppt.sh build scene.json --out build/
python3 skills/goai-figure-studio/scripts/install_fig.py \
    --build build/ --s5 build/render/page_001.png --crop render --margin 14 \
    --project <项目> --name <图名> --figdir <论文>/figures [--media <画廊目录>]
```

- `--crop render`：按重建自己的 bbox 裁，不按生图位图裁（按位图裁会切掉重建
  路由到位图范围外的连线）。
- 英文版 `--name` 以 `_en` 结尾，同一 `--project` 下的记录自动带后缀
  （`validation_en.json`、画廊 `render_en.png`），中英两版不会互相覆盖。
- **中文图的 `validation.json` 会是 `status: fail`** —— 那是 LibreOffice 把 Noto CJK
  嵌成 `…-VKana` 造成的字体命名假阳性，`rendered_ink_width_drift` 则是中西文混排
  自动补空。两者都在 `references/pitfalls.md` 里有条目，**不要因此说图失败了**，
  也不要去追。

### C4b 幻灯片图（答辩 PPT）

同一套设计系统，画布 1536×864 = 一整页 16:9（img2ppt 把 1536 px 映射到 960 pt 页宽），
字号按幻灯片 pt 取（分组 16 / 标题 14 / 步骤号 18 / 正文 12 / 标签 11，`print_width_pt=960, crop_px=0`），
内容避开模板标题栏（y < 122 px）。构建后用 `scripts/deck_merge.py` 把整页形状 1:1 复制进模板的新页
（沿用模板标题占位符与蓝色标题条，可 `--font 微软雅黑` 换成作者机器上的字体）。
实例：`submission/03_运行与评测包/figure_scenes/scenes_deck.py`、`docs/competition/deck_figures/`。
生图通道在 Codex 宿主上是 `scripts/image_gen_codex.py`（标准库实现；登录过期先 `scripts/codex_refresh.py`）。

### C4c 幻灯片图的表面风格：别把论文图的克制搬上讲台

论文图的契约（克制四色、纯线稿图元、几十条锁定字串）用在答辩幻灯片上会显得平——作者原话"没有顶会的质感"。
幻灯片走 **loop-engineering 风格**（参考 ARIS `/method-figure`），构件在 `figure_scenes/deckstyle.py`：

- **brief 化**：≤14 个组件，每个"标题 + 一句话"，一个论断 + 一个数字；其余留给讲者。
- 三条**编号淡彩色带**（实色标题条）、带投影的白卡、核心卡配角色或小插画；确定性工具画成图标而不是角色。
- **连线按含义上色并配图例**：深蓝粗线主流程、橙色回环弧是视觉主角（写明上限）、蓝虚线分派、细灰线落账、绿色放行、红虚线升级人类。
- **证据条**用真实轮次数据讲回环（issue 数逐轮下降），而不是角落里一行统计。
- **条件线框锁语义**：生图模型画风可以很好，但不守拓扑（并行画成串行、卡片换组、弧线起止点错）。先用原生构件画出语义正确、
  文字到位的线框，S5 让模型"照它出图，只提升质感"；可编辑交付件 = 线框 + 从**无文字素材表**裁出的插画
  （`scripts/crop_assets.py`，按墨迹空白带切格、只去掉与边相连的白底）。
- 提示词写**正面描述**、3–4K 字符即可；堆禁令和长白名单会把结果压平。尺寸只要求"16:9 横版"，按工具原生像素登记。
- 生图可以委托给有内置 `image_gen` 的 Codex agent：提示词包 + `register_image.py`（逐字节登记 + 来源记录）放进它的工作区，
  任务书写明"只用 image_gen、提示词原样、不审计"。

实例与全流程记录：`docs/competition/deck_figures/`（README、`studio_r2/`）。

### C4d 放进别人的 PPT：先读它的色板和叙事

第三轮，作者原话："和我们的风格统一下，包括我们的化学流程，注意用词要专业"。

- 先从目标 PPT 里取色（theme1.xml 的 accent/dk，和内容页真正用到的 srgbClr），写成 `deckstyle.THEMES` 的一项，用
  `use_theme()` 整体换色；数字卡、标题条照它已有页面的样式画（`tile()` / `headline_bar()`），图例用一行的 `hlegend()`。
- 卡片内容用项目**自己的领域环节**命名并配领域小插画（再开一张无文字素材表即可），不要只讲通用的"检索/写作/审稿"。
- 每个数字回到账本核对一次再上页（`ledger.json` 的 issues 有 `round_opened`，别凭记忆写"7 → 0"）；闸门的 WARN 如实画。
- 作者点了多个候选构图时，同一份内容各出一页（`parallel_bands()` / `parallel_ring()`），合进同一份 PPT 供挑选。
- 构件：`band()`（横向相位带，左侧页签）、`rflow()`（圆角折线回路，末段保留整只箭头）、`curve()`（三次曲线，环的四分之一圈）、
  `pgroup`（蓝虚线框 +「并行 ×N」= 并发语义，一进一出，不画分叉总线）。

### C5 中英两版

同一套几何换字符串，不重画：

```python
from scripts.relayout import retype
missing = retype(slide, TR, free_pills=('cav_t', 'leg_t'))
if missing: ...        # 报出来，绝不把没译的字串直接发出去
```

术语取论文自己的英文章节和已有英文图，保持全文一套词汇。拉丁文比中文宽约 1.6 倍，
`retype` 负责收字号、放宽盒子、重排标签行，并丢掉 `font_group`（否则最长的字串会把
整组按原字号卡住）。

**改过中文标签就必须查覆盖**：翻译表按中文原文做键，改了中文不同步它，英文版就再也
生不出来。2026-09-14 实际发生过——排版线按术语表改了 15 处标签，翻译表没跟上，13 条
字串缺译，数天后审计别的东西时才偶然发现。

```bash
python3 skills/goai-figure-studio/scripts/check_i18n.py --tr <r5_en.py 或 tr.json> <中文 scene.json …>
```

覆盖不全会逐条列出并退出 1。

### C6 印刷尺度终检

```bash
python3 skills/goai-figure-studio/scripts/print_audit.py --paper <编好的论文.pdf> <图.pdf>=<scene.json> …
```

它从编好的 PDF 里找到每张图的实际放置宽度，报出每类文字印出来多少 pt，低于 7 pt 就失败。
然后**在编译好的论文页上看**（`pdftoppm` 出页），不是只看单张图 PDF —— 单张图永远好看。
`\linewidth` 下 1536px 画布的 19px 字接近 6pt；低于这个就重新构图（一行宽排改 3+3），
**宁缩画布、勿缩字号**。同时核对 `\includegraphics` 没有残留为旧图调的 `trim=…,clip`。

### 改了 lib 之后

```bash
python3 skills/goai-figure-studio/scripts/selftest.py
```

36 个图元全画一遍、四级层次搭一个、标签行打包断言、precheck 必须 0 hard。
它挡的是只有跑完一次远端构建才会发现的问题。

## 交付与登记

- 每图四件套：`<论文>/figures/pdf/<name>.pdf`（矢量，LaTeX 直接 `\includegraphics`）、
  `figures/svg/<name>.svg`、`<name>_editable.pptx`（PowerPoint / WPS 直接可编辑）、
  `figures/png/<name>.png`；主图另附候选目录（S2/S5 两轮候选与参照定稿，审计可溯源）。
  中英两版同名，英文加 `_en`。
- 单一事实源是**重建脚本**（`scenes_*.py`）＋ 它生成的 `scene.json`，不是导出的 PDF/SVG。
  别人要改图内用词，改脚本重生成，**不要直接改导出件**。
- 每图写 caption 草稿（图讲什么 + 符号约定）存 figure_plan.md 供 writer。
- 全部图完成后 `loopctl gate --name figures_ready --status PASS
  --detail "<N 图 pptx+svg+pdf 齐；precheck 0 hard；print_audit 最小 ≥7pt 且同角色跨图同字号；img2ppt findings 仅剩 pitfalls
  列出的已知误报；中英两版齐全且 check_i18n 覆盖完整>"`。独立图纸任务（无 loop 会话）不必强行
  gate —— 交付登记写进 figure_plan.md 即可。

## 硬性规则

- **交付物必须可编辑**（pptx + svg + 矢量 pdf）；位图永不直接进论文图池。
- **图元全部原生**，没有一处位图裁切。
- 候选生图、ledger issue、保真审计、重建对照都要在 figure_plan.md 留痕 —— 审计链完整才许过闸。
- 风格库缺失不阻塞：按 `FAM` 与 `references/ink-budget.md` 的默认执行并记账。
- 交付前对包含图注或图中文字的稿件运行
  `.venv/bin/python tools/academic_language_guard.py workspace/drafts/sections
  workspace/drafts/main.tex`；命中内部控制术语时先修图稿和 caption，再登记。
- 图内用词必须与正文术语表一致。排版线的 `tools/layout_guard.py` D2 检查会把图件
  PDF 的文字抽出来和 `templates/glossary_materials_zh.json` 逐条比对 —— **对不上要改图源、
  不要改正文**（实抓 15 处：热史→热历史、慢冷→缓冷、批量相纯→块体相纯…）。
