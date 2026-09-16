# S3-DIRECTION-SELECT — fig03_roadmap
| id | candidate | issue | severity | carry |
|---|---|---|---|---|
| I1 | C01 | compact pipeline with feedback arc below and question tags; ~30% empty top band | low | second candidate; fill canvas |
| I2 | C02 | closed loop: fork region cramped on the right, question tags float in the middle without clear anchors | medium | not selected |
| I3 | C03 | two bands, feedback arc above the mainline; clean but questions detached from the flow | low | not selected |
| I4 | C04 | parallel lanes as the visual core (matches S0 process budget: one fork, two lanes, one merge); left column stacked; feedback along the bottom; slightly busy tags | low | lead; tidy tags, equalise lane heights |
| I5 | all | text/formulas correct; single feedback edge; no per-element lanes | pass | keep |
selected_direction: C04 (lanes as core) lead; C01 (compact pipeline) second. agent preference: C04 > C01 > C03 > C02.

## S5 outcome, corrections applied in the editable reconstruction (2026-09-13 04:10)
- Final: **F01** (parallel lanes). Two connector deviations from the paper were found in the S5 raster (visible-only in the raster, corrected in scene.json / PPTX / vector PDF):
  1. the fork bracket was also fed by a stub from 结构假设 — the paper's mainline is 结构假设 → 模型筛选的前驱体 → fork (§1.2, §8.3); the reconstruction feeds the fork from 模型筛选的前驱体 only;
  2. the dashed feedback 更新组成与工艺 returned to the bottom of 模型筛选的前驱体 — the paper says results update the hypotheses (§1.2 "根据…结果，逐轮调整组成和工艺"); the reconstruction routes it to 结构假设 (left edge).
- All other elements (three left modules with tokens, two lanes with 3 + 1 tokens, 结果反馈 with four items, three question tags with leaders) reconstructed as native objects.


## Round 2 (author: 配色太乱，没有层次感)
- Strict two-level palette (white modules with slate outline + bold titles; light-outlined regular tokens; teal only for mainline/feedback; ochre only for the three question tags; 模型排序 tag gray). F03 keeps the lanes layout, F04 the pipeline layout; both correct. Final **F03**, rebuilt with the same connector corrections as round 1.

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

- 本图版式：单条主干（文献依据 → 结构假设 → 前驱体筛选 → 两条实验通道 → 表征手段）＋底部判断提醒带；两条通道各自画出机理链与结论条（批量相区与相纯度 / 单晶结构与液相选择性）。
- 保留前几轮按论文修正的两条连线：分叉只由“前驱体筛选”驱动，反馈虚线回到“结构假设”。
- 候选里“模型排序的候选”一类的措辞按论文保留，编造的三步链未采用。
