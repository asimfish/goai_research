# S3-DIRECTION-SELECT — bzso_roadmap
| id | candidate | issue | severity | carry |
|---|---|---|---|---|
| I1 | C01 | single row: tall empty modules, ~40% of canvas is white above/below | medium | not selected |
| I2 | C02 | serpentine fills the canvas; the right-side turn is a thick pipe that reads heavier than the labelled arrows | low | selected as second; thin the turn |
| I3 | C03 | staircase is quirky; small modules, diagonal whitespace | medium | not selected |
| I4 | C04 | chevron band is the most journal-like and compact; labels sit above joints via leader ticks (fine); band only ~30% of height | low | selected as lead; make the band taller and add breathing room |
| I5 | all | text and formula (Ba5Y12Zn[O(SiO4)]8 with subscripts) rendered correctly | pass | keep |
selected_direction: C04 chevron band (lead), C02 serpentine (second). agent preference: C04 > C02 > C01 > C03.

## S5 outcome and final choice (agent checkpoint, 2026-09-13 04:10)
- F01 (chevron band) and F02 (serpentine) both rendered all whitelist text and the formula subscripts correctly.
- Final for the paper and the editable reconstruction: **F02 (serpentine)**. Reason: super_img2ppt's scene schema has no chevron point-depth adjustment (OOXML default 50% would change the interlocking geometry), so the chevron band cannot be reconstructed faithfully as native shapes; the serpentine uses plain rounded rectangles and thick labelled arrows and reconstructs 1:1. F01 stays registered as a candidate for the author.


## Round 2 (author: 没有质感且有点乱)
- F03: single row of six numbered cards (01–06), bold title + subtitle, one monochrome line motif per step, thin teal arrows with small labels above, a light baseline; 2172×724 canvas. F04 (serpentine + icons) initially failed on a proxy SSL error and was re-run. Final **F03**; icons reconstructed as exact source crops, everything else native.

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

- 本图版式：单行六卡（编号＋标题＋线稿图元＋要点条），按文献证据 / 实验方法分成两个分组带；五个连线标签（结构约束 / 条件窗口 / 可迁移变量 / 比较边界 / 缺口驱动）放在顶部标签带，分组标题移到分组带底部，避免标签与分组标题相撞、也避免标签把箭头整段盖住。
- “类似物判据”卡用 note 族（琥珀）标出这是待验证的比较对象。
