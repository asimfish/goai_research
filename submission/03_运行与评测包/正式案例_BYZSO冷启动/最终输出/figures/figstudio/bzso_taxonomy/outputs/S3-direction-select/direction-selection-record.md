# S3-DIRECTION-SELECT — bzso_taxonomy
| id | candidate | issue | severity | carry |
|---|---|---|---|---|
| I1 | C01 | radial hub: correct, but the 7 cards leave uneven gaps; dashed 类比 node at far left reads as a lower-priority afterthought | low | not selected |
| I2 | C02 | left-rooted tree: cleanest, fills the canvas, dashed 类比 branch at the bottom; spoke labels on pills | none | selected as lead |
| I3 | C03 | arrows point INTO the hub (direction reversed) and a decorative outer circle appears | high (semantic) | rejected |
| I4 | C04 | grouped columns: clean; group panels have no titles (as required) | low | selected as second |
| I5 | all | text and formulas rendered correctly | pass | keep |
selected_direction: C02 tree (lead), C04 grouped columns (second). agent preference: C02 > C04 > C01 > C03.

## S5 outcome (2026-09-13 04:05)
- Final: **F01** (left-rooted tree); 54 native objects (hub, trunk, six teal branches + one dashed ochre branch with pills, seven cards). Branch lines are split around the pills so the labels are true editable text.

## Round 4（作者：顶会配图的模块化、层次感、配色一致性明显更好 / “你有好好参考我们的 super_teaser 吗”）
本轮先补读了前三轮**跳过**的三份参考策略，并按它们重做，而不是继续在第三轮的版式上调色：
- `academic-framework-hierarchy-and-asset-mirroring-policy-v3210`：四级渲染层级 —— ①分组底色带（tier 1）②模块卡＋6 px 主色条＋线稿图标（tier 2）③卡内机理链 / 记录格（tier 3）④连线标签、端口与警示标签（tier 4）；连线按束归并，禁止把成品图当作一个色块贴上去。
- `core-submodule-detail-policy-v313`：核心模块必须画出可见的内部机理（输入→操作→输出），主干流程占版面 55–70%。
- `edge-label-first-and-internal-motif-policy-v3211`：先定连线标签与内部母题，再定框。
- `scripts/figure_studio_select_composition.py` 对这五张图返回 `no_structural_match`（内置 7 套配方都是 ML 结构图），按参考允许的做法改为自撰针对性版式，并在此记录。
- 图标不再用 S5 位图裁剪（第三轮的笔触粗细与底色不一致就是从这里来的），改为 `figstudio/motifs.py` 的 27 个原生线稿图元，统一 `#1F2937` 墨色与统一笔宽，随卡片缩放。
- 配色收敛为四个族：lit（蓝灰，文献证据）、exp（青，实验方法）、note（琥珀，判断提醒）、mute（灰，排除/参照），底色—描边—文字三档同族取值。

### 保真审核（本轮必须记录）
第四轮生成候选在三张图里**编造了论文中没有的子步骤文字**：图 1 的证据类目里写了“文献检索 / 信息提取 / 关键数据”，BaZn2Si2O7 路线图写了“原始结构 / 结构分析 / 多晶型”，分类框架写了“已知结构 / 位点替换 / 相关化合物”。重建**不采用**这些文字：只有论文本身给出顺序的模块保留机理链（图 2 的五条合成路线、图 3 的两条实验通道），其余模块回到“标题＋图标＋可追溯条目”。

### 交付
- img2ppt `check` 五张全部 pass；`build` 的 preflight 全部 pass（余下为 `text_shrunk` 与 LibreOffice 的字体替换提示）。
- 第三轮交付件保留在 `deliverables_round3/`，本轮写入 `deliverables/` 并同名替换 `figures/{pdf,png,svg}`。

- 本图版式：左侧目标相枢纽 → 实验方法四支（结构与多晶型 / 合成路线 / 组成与热处理 / 玻璃析晶），另一条从枢纽底部绕到右侧的文献证据三支（近邻体系 / 证据边界 / 类似物）；`Ba5Y12Zn[O(SiO4)]8` 仍为虚线 note 卡，标注“未见直接报道”。
- 连线标签抬到连线上方，保证箭头与线段可见。
