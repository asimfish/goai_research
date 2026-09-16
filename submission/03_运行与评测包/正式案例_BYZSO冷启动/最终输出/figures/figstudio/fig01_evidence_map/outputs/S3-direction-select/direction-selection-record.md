# S3-DIRECTION-SELECT — fig01_evidence_map

## S2 outputs review (issue ledger)
| id | candidate | issue | severity | carry to S4 |
|---|---|---|---|---|
| I1 | C01 | canvas only ~65% filled vertically (empty top/bottom bands) | medium | fill 85% of height |
| I2 | C02 | ring labels stacked bottom-up reverse the reading order; large empty upper-right area | medium | not selected |
| I3 | C03 | ochre caveat tag overlaps the converging arrows; converging lines read as a junction | medium | not selected |
| I4 | C04 | hollow-square column in the ledger carries no paper meaning (decorative) | low | remove the column |
| I5 | all | text rendering correct (all whitelist labels spelled right); no unsupported edges; 非相关资料 correctly bypasses the ledger | pass | keep routing |

## exploration aggregate
- Semantic fidelity: all four are homomorphic to the S0 model (ladder → ledger → uses; dashed exclusion path). No false relay edges.
- Visual signals: C04 (document strips) gives the strongest "literature" identity and the cleanest table; C01 gives the fastest scan and encodes distance by outline strength; C02/C03 add little.

## direction selection
- selected_direction: document-strip lineage view (C04) refined with C01's graded-outline distance encoding.
- user_preferred_first_round_candidate_ids: none recorded (agent-run checkpoint); agent preference: C04 > C01 > C02 > C03.
- S4 must: absorb C04 layout + C01 gradient; avoid decorative marker columns; fill the canvas; keep the caveat tag off the arrow bodies.


## Round 2 (author request 2026-09-13: “图 1 按 C02 的方向重出正式版”)
- F03 同心圆环（正圆版）与 F04 半环版均按 C02 方向生成；两张的文字与连线均正确。
- 最终选 **F03**：正圆可用原生椭圆逐层重建（helper `i2p_scene_r2.bullseye`），半环无法用场景模式的原生形状表达（无半圆/圆弧，且圆心在画布外会被判越界）。
- 重建时的位置调整：环带标签沿用位图位置（外三层在 12 点方向、内两层在右下/正下），轴标签“与目标相的距离”改为水平置于斜轴中点旁（场景模式只支持 0/90/180/270 度旋转）。

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

- 本图版式：三个分组带（文献证据 / 实验方法 / 可回答的问题），左侧证据阶梯按“与目标相的距离”轴排序，四类可比证据经一条归并连线进入中间的比较账本（6 行记录格＋勾选标记），右侧三类可回答问题；“非相关资料 → 划定研究范围”走底部虚线，明确不经过账本。
- 警示标签“近邻条件 ≠ 已验证配方”移到实验方法带的标题行，不再压在卡片上。
