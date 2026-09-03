# fig02_route_variable_matrix — Phase A 合同与交付记录

## 角色、边界与管线

- 图级：辅助图。
- 管线：Phase A 策略合同 → figspec 直渲 → SVG/drawio 对照自检；跳过 AI 生图候选与主图重建。
- 证据边界：仅使用 `workspace/notes/taxonomy.md`、`workspace/library/references.bib`、`workspace/inputs/scope.md`。
- 文件边界：只写本文件与 `fig02_route_variable_matrix` 的 figspec/SVG/drawio；不改公共 `workspace/notes/figure_plan.md`、其他图、正文或 BibTeX。
- 语义边界：本图是已报道合成条件的**抽取与比较框架**，不是 `Ba₅Y₁₂Zn[O(SiO₄)]₈` 的实验处方，也不把 P1 工艺近邻条件迁移成目标相条件。

## A1. 三问定生死

1. **Reader question**：面对不同论文中的五类成相路线，读者应抽取哪些条件变量，并用哪些互补终点判断“结构身份、批量相纯度、组成可信度与高温稳定性”？
2. **Visual mainline**：从左到右的“路线族 → 字段抽取/标准化 → 验证终点”。路线节点展示最小工艺链；条件变量只放在边标签，验证方法也放在通向终点的边标签。
3. **来源锚点**：路线族对应 taxonomy D1–D5；变量字段对应 E1–E5 以及各 D 节的必录字段/边界；验证终点对应 F1–F4；“统一字段、区分直接证据与推断”的任务来自 scope 核心问题 5、MECE 子主题 7–8。所有列出的文献 key 均已在 `references.bib` 中核到存在。

## 模糊指令规范化

| 上游表述 | 具体含义 | 安全画法 | 禁止的误实现 |
|---|---|---|---|
| “路线—变量—验证示意” | 比较文献记录结构，而非声称变量必然导致某结果 | 五个路线节点汇入一个“统一路线记录”，再连接四类验证终点 | 画成实验优化闭环、因果图或推荐配方 |
| “机械化学预活化” | 高能研磨/固液辅助改变反应性，仍需记录后续成相步骤 | 节点内部写“高能研磨 → 活化 → 后续成相” | 把普通混匀等同机械化学，或暗示单靠球磨得到目标相 |
| “Czochralski” | 仅是 Y₂SiO₅/稀土正硅酸盐的 P1 工艺对照 | 保留独立路线节点，并在合同/caption 标明迁移边界 | 暗示目标相已有 Czochralski 制备证据 |
| “验证” | 不同尺度的证据闭环 | 四个并列终点，边标写实际表征读出 | 把“主相出现”等同相纯，或把室温回收相等同原位高温相 |

## A2. 源忠实表

状态只有 `direct` 或 `inferred`；本合同没有待处理的 `remove/revise` 项。

| 可见模块/边/符号 | 状态 | 来源锚点与约束 |
|---|---|---|
| 路线族分区 | direct | taxonomy D：按主导成相事件分派路线；scope 子主题 4–5。 |
| 外加助熔 | direct | D1；`ababaikeri2024ba5y12zn`, `kolitsch2009crystal`, `wierzbickawieczorek2017high`, `ababaikeri2024ba3zn4si4o15`, `leonyuk1999high`, `giess1982zn2sio4`。 |
| 自熔/熔体 | direct | D2；`yamane2024synthesis`, `gulay2024navigation`, `christensen1994investigation`, `leonyuk1999high`, `leonyuk1999crystal`。 |
| 固相陶瓷 | direct | D3；`yamane2024synthesis`, `yamane2024microstructure`, `lin1999phase`, `zou2021crystal`, `kerstan2012thermal`, `cai2024optimized`, `zou2019anti`, `tejas2024structural`, `pires2001luminescence`, `zhao2026crystal`, `kerstan2015kristallphasen`。 |
| 机械化学预活化 | direct | D4；`yamane2024microstructure`, `yldrm2009y2sio5`, `tzvetkov2001effects`；必须记录研磨材质与污染，且不与普通玛瑙研钵混匀合并。 |
| Czochralski | direct | D5；`pang2005study`, `alizadeh2021spectroscopy`, `shoudu1999czochralski`, `brandle1986czochralski`；只作 P1 对照，当前没有目标相 Czochralski 证据。 |
| 五个路线节点内的操作 token | direct | 分别压缩 D1–D5 的路线判定/必录字段；只表示路线最小链，不添加未见于证据边界的工艺步骤。 |
| “统一路线记录：抽取 → 规范化 → 跨路线对照” | inferred | 前提：scope 子主题 8 要求把已报道条件标准化为统一字段；taxonomy 明确将路线、变量、验证分支分开。推理：需要一个真实消费路线字段、并向验证终点交接的记录层；它不是化学中间体。 |
| 五条“路线 → 统一路线记录”实线箭头 | inferred | D1–D5 给出路线字段，E1–E5给出跨路线变量；scope 子主题 8要求字段对齐。箭头仅表示“从论文抽取到记录”，不表示工艺因果。 |
| 单晶结构终点 | direct | F1；`ababaikeri2024ba5y12zn`, `kolitsch2009crystal`, `yamane2024synthesis`, `gulay2024navigation`, `motozawa2022bay16si4o33`, `zou2021crystal`。 |
| PXRD / Rietveld 终点 | direct | F2；`yamane2024microstructure`, `gulay2024navigation`, `lin1999phase`, `zou2021crystal`, `kerstan2012thermal`, `cai2024optimized`。 |
| 成分 / 污染终点 | direct | F3；`yamane2024microstructure`, `gulay2024navigation`, `thieme2015ba1`, `tejas2024structural`, `pang2005study`。 |
| 高温稳定性终点 | direct | F4；`lin1999phase`, `kerstan2012thermal`, `kerstan2013bazn2si2o7`, `thieme2016negative`, `zou2019anti`。 |
| 四条“统一路线记录 → 验证终点”实线箭头 | inferred | 前提：scope 子主题 7–8要求产物证据质量与标准化条件对照，F1–F4分别规定成功标准。推理：标准化路线记录必须由这些互补读出审计；箭头不声称所有论文都完成四项验证。 |
| 单一实线 + 实心箭头 | inferred | 全图唯一线型语义为“证据抽取/验证交接”。不使用虚线、不画装饰箭头、不编码证据强弱或因果。 |
| 底部处方边界徽章 | direct | scope 核心问题 5、排除标准与安全边界；taxonomy D5、E2、E5、H3–H5 的迁移限制。 |
| 蓝灰路线/验证、暖色记录层、灰阶文字 | inferred | 非事实编码；仅用于区分“来源记录”和“标准化操作”。颜色不表示路线优劣、证据强弱或相稳定性。 |

## 边证据账（edge-label-first）

| 边 | 边标签承载量 | 上游/下游为何真实相接 |
|---|---|---|
| 外加助熔 → 统一路线记录 | 配比、温度·时间、气氛、助熔/矿化剂、坩埚、冷却/分离 | D1 的必录字段被 E1–E5 归一化，记录层消费这些字段。 |
| 自熔/熔体 → 统一路线记录 | 熔体组成、最高 T/均化、气氛、容器接触、成核/冷却 | D2 的熔体字段进入同一记录；不借用外加助熔剂语义。 |
| 固相陶瓷 → 统一路线记录 | 配比、混合/压片、温度·时间、气氛、坩埚、复磨/复烧/冷却 | D3 与 scope 子主题 4逐项支撑。 |
| 机械化学预活化 → 统一路线记录 | 球磨能量/时长、液体辅助、研磨材质/污染、后续热处理 | D4明确预活化与污染审计必须成对记录。 |
| Czochralski → 统一路线记录 | 配比/预烧、熔化 T、气氛/坩埚、籽晶/提拉/旋转、冷却/退火 | D5与 H5 支撑工艺字段，但只作 P1 对照。 |
| 统一路线记录 → 单晶结构 | SCXRD/CRED、结构精修 | F1用这些读出确认规范式、空间群和位点占据。 |
| 统一路线记录 → PXRD/Rietveld | PXRD、相分数、未索引峰 | F2用批量衍射审计相纯度与杂相。 |
| 统一路线记录 → 成分/污染 | EDS/EDX/SEM、烧前后组成 | F3区分名义、局域与体平均，并追踪外来污染。 |
| 统一路线记录 → 高温稳定性 | HT-XRD、热分析、多气氛 | F4界定转变/分解边界，并区分原位高温相与冷却回收相。 |

两模块间均只有一条捆绑连线；没有平行同义线，也没有不消费边标签内容的假中继。

## 可见文字白名单

以下逐项为允许出现在 SVG/drawio 中的完整文字；换行符只控制排版，不改变文字。

- `路线—变量—验证：合成条件证据的统一抽取框架`
- `路线族（主导成相事件）`
- `字段标准化`
- `验证终点（证据闭环）`
- `外加助熔`
- `溶解/保温 → 慢冷/分离`
- `自熔/熔体`
- `均化 → 自发成核 → 受控冷却`
- `固相陶瓷`
- `混合/压片 → 煅烧/复磨 → 烧结`
- `机械化学预活化`
- `高能研磨 → 活化 → 后续成相`
- `Czochralski`
- `预烧/熔化 → 籽晶提拉 → 退火`
- `统一路线记录`
- `抽取 → 规范化 → 跨路线对照`
- `单晶结构`
- `结构身份 / 位点占据`
- `PXRD / Rietveld`
- `批量相纯 / 杂相`
- `成分 / 污染`
- `名义—局域—体平均`
- `高温稳定性`
- `原位高温 ≠ 冷却回收`
- `配比｜温度·时间｜气氛` + `助熔/矿化剂·坩埚｜冷却/分离`
- `熔体组成｜最高温/均化｜气氛` + `容器接触｜成核·冷却`
- `配比｜混合/压片｜温度·时间` + `气氛·坩埚｜复磨/复烧·冷却`
- `球磨能量·时长｜液体辅助` + `研磨材质·污染｜后续热处理`
- `配比/预烧｜熔化温度｜气氛·坩埚` + `籽晶·提拉/旋转｜冷却/退火`
- `SCXRD / CRED` + `结构精修`
- `PXRD / 相分数` + `未索引峰`
- `EDS / EDX / SEM` + `烧前后组成`
- `HT-XRD / 热分析` + `多气氛`
- `抽取框架 ≠ Ba₅Y₁₂Zn[O(SiO₄)]₈ 实验处方`

## 配色、符号与密度合同

- 配色：风格卡仍在构建中，故采用一主一辅 + 灰阶。主色为克制蓝灰（路线与验证），辅色为低饱和暖赭（字段标准化与边界提醒），背景近白；无渐变、霓虹、高光或装饰性色带。
- 符号：圆角卡片只表示实体模块；浅色 group 表示阅读分区；实线实心箭头只表示证据交接；边标签白底只为提升可读性，不另编码含义。
- 密度：1500 × 835 px；3 个分区、10 个有文字节点、9 条带标签边、1 个底部边界徽章。节点主标 20 px、边标 17 px、组标 21 px、标题 28 px、边界徽章 17 px；节点副文自动为 17 px。按 468 pt 栏宽换算，正文层级均达到约 5.3 pt 或更大。
- 布局：左侧五路线纵排，中部单一记录层，右侧四终点纵排；标签走廊保留至少约 150 px，卡片纵向间隙不低于正文字号的 0.9 倍，底部边界徽章紧贴主体。
- 禁止项：变量不得升级成同级盒子；不得把路线颜色解释为优劣；不得出现处方数值；不得出现未在白名单的装饰文字。

## 来源锚点汇总

- `scope.md`：核心问题 3–5；MECE 子主题 4–5、7–8；纳入/排除标准；安全边界。
- `taxonomy.md`：D1–D5（路线）、E1–E5（变量）、F1–F4（验证）、H3–H5（迁移边界）。
- `references.bib`：本合同源忠实表中列出的 key；开工核验结果为全部存在，且账本 `ref_integrity` 为 PASS（52/52）。

## Caption 草稿

**图 2｜路线—变量—验证的合成条件抽取框架。** 左侧按主导成相事件区分外加助熔、自熔/熔体、固相陶瓷、机械化学预活化与 Czochralski 五类路线；连线标签给出应从每项实验抽取的配比、温度—时间、气氛、坩埚/矿化剂、冷却及路线特有字段。统一记录随后由单晶结构、PXRD/Rietveld、成分/污染和高温稳定性四类终点交叉审计。实线箭头表示证据字段的抽取与验证交接，不表示变量—结果因果。Czochralski 仅作为 P1 工艺近邻对照；本图不是目标相实验处方。

## 渲染与自检记录

- **Phase A**：合同、来源锚点、边证据账、文字白名单、配色/密度预算与 caption 草稿已在本文件落盘；无待处理的 `remove/revise` 项。
- **Schema/初检**：已先读取 `figspec_schema()`；初版结构校验通过，但 lint 提示副文与边标约 4.6–4.8 pt，仅略高于硬下限。随后将组标/节点/边标分别提高到 21/20/17 px，节点副文随主标达到 17 px。
- **第 1 轮直渲**：`validate_figspec` 返回 `ok=true`，`errors=[]`、`typo_errors=[]`、`typo_warnings=[]`；同一 figspec 成功生成 SVG 与 drawio。视觉检查确认五路线汇入真实记录层、四终点互不混淆、连线不穿节点、group 完整框住成员、配色克制。发现边标 `T·t` 虽可理解但不够直白，改为“温度·时间/最高温/熔化温度”。
- **第 2 轮直渲**：再次得到零错误、零警告；SVG 视觉检查确认所有变量标签完整、处方边界徽章可见，未发现文字溢出、标签遮挡、主线偏心、大片无效空白或颜色语义冲突。
- **drawio 对账**：环境未安装 draw.io Desktop CLI，`drawio_export` 明确返回“未找到 draw.io Desktop CLI”；因此不能取得 drawio CLI 导出 PNG。按工具给出的 fallback，视觉检查使用同源 SVG 的无头浏览器光栅化结果，几何/可编辑性则直接核对 drawio XML。XML 可正常解析，包含 15 个 vertex（标题、3 个 group、11 个节点）与 9 条 edge；figspec 要求的 group/node/edge ID 无缺漏，五个路线节点及记录节点的 parent 均正确。
- **结构计数**：figspec = 3 groups、11 nodes（含处方边界徽章）、9 edges、0 free texts；SVG = 24 rect、11 path、43 text；所有可见字符串逐项核对后均属于白名单。

## 最终自检清单

- [x] 来源忠实：五路线绑定 D1–D5，变量绑定 E1–E5，验证绑定 F1–F4；文献 key 均存在于已核验 BibTeX。
- [x] Edge-label-first：配比、温度·时间、气氛、坩埚/矿化剂、冷却及路线特有量全部位于边标签，没有变量同级盒子。
- [x] 边语义：每条边均有真实上下游；全图只用一种实线箭头语义，无装饰边、假中继或同义平行线。
- [x] 核心机制非空：五个路线节点展示最小工艺 token 链；记录层展示“抽取 → 规范化 → 跨路线对照”。
- [x] 验证终点：单晶结构、PXRD/Rietveld、成分/污染、高温稳定性在图面和读出标签上均明确区分。
- [x] 迁移边界：Czochralski 在 caption 中限定为 P1 对照；图面醒目标出“抽取框架 ≠ 目标相实验处方”。
- [x] 排版：lint 零错误零警告；字号、卡片间距、标签走廊、分组与页边距满足合同。
- [x] 双格式同源：figspec、SVG、drawio 均由 `render_figure` 同次直渲；drawio 为原生 mxGraph 可编辑结构。

Caption 草稿经第二轮自检后定稿，无需修改。

## 2026-09-02 出版级返工审计

- **Phase A 参照**：采用 `workspace/figures/candidates/academic_style_reference.png`
  的三栏浅灰容器、灰色横条、深蓝灰描边和低饱和赭色记录层；版式参照与科学事实分离。
- **主线**：路线族 → 实验项目 → 验证终点；可见文字全部改为材料学表达，删去
  “字段”等内部控制术语，底部明确“抽取框架 ≠ Ba₅Y₁₂Zn[O(SiO₄)]₈ 实验处方”。
- **几何修正**：统一实验记录卡移至 x=600；五条路线边各走独立水平走廊，标签压缩为
  配比/温度、熔体/容器、混合/煅烧、研磨/污染、籽晶/退火；四类验证终点右侧纵排。
- **对照迭代**：第 1 轮发现旧版中央汇流标签拥挤；第 2 轮完成右移和标签重排；第 3 轮
  检查边界卡与路线标签间距、XML 可编辑性及同源导出。当前 figspec lint 为 0 error/0 warning。
- **交付**：figspec、SVG、Draw.io、PNG、单页 PDF 均已更新；无 Draw.io Desktop CLI 时
  采用仓库本地 SVG 等价渲染与 XML 对账，不改正文或 references.bib。
