# S3-DIRECTION-SELECT — fig02_route_matrix

## S2 outputs review (issue ledger)
| id | candidate | issue | severity | carry to S4 |
|---|---|---|---|---|
| I1 | C01 | empty top/bottom bands (content ~62% of height) | medium | fill 85% |
| I2 | C02 | step tokens placed under specific record columns imply cell-level data the paper does not state (fidelity risk) | high | not selected as lead; matrix framing may not be reused |
| I3 | C03 | curved spokes cross each other; ledger→check arrows fan from one point (reads as a junction) | medium | not selected |
| I4 | C04 | 工艺参照 tag overlaps the Czochralski column corner; otherwise cleanest and fills the canvas | low | move the tag inside the column under its title |
| I5 | all | all whitelist labels rendered correctly; check-card motifs (polyhedron, peak trace, dots, temperature curve) are simple and reviewer-recognisable; no route→check edges | pass | keep |

## exploration aggregate
- Semantic fidelity: C01/C03/C04 are homomorphic to the S0 model; C02 adds an unsupported step-to-column mapping.
- Visual signals: C04 (three tiers) uses the 3:2 canvas best and gives an immediate top-down reading; C01 is the fastest left-to-right scan with edge labels on the arrows.

## direction selection
- selected_direction: top-down three-tier schematic (C04) as lead; left-to-right three-band (C01) as the second formal candidate.
- user_preferred_first_round_candidate_ids: none recorded; agent preference: C04 > C01 > C03 > C02.

## S5 outcome (2026-09-13 04:00)
- Final: **F01** (three tiers). Reconstruction: 123 native objects; the four check-card motifs (polyhedron, diffraction trace, temperature curve) are exact crops of the source registered as image assets; the three dots are native ellipses.

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

- 本图版式：上带五条合成路线（每张卡内是纵向机理链：溶解→保温→慢冷分离 等，均出自论文的条件描述），中带是统一实验记录（四列记录格），下带是四项互补表征；Czochralski 卡为虚线＋灰族，并在分组带右上给出“虚线＝工艺参照”的图例。
- “抽取框架 ≠ 实验处方”改为记录卡标题行上的标签（`tag_at='title'`），不再与记录格重叠。
