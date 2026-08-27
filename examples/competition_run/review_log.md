# Ideas 对抗审记录 — route_c_tppa1

审稿通道：无跨模型 MCP 可用 → 同模型冷启动降级（先读产物再读账本历史），
独立性受限，最终 `ideas_reviewed` 以 PASS(provisional 语义由 review 阶段回执统一声明) 记录。
四维：证据真实性 / 新颖性 / 可行性 / 安全性。graveyard 为空（首个 run），无禁区冲突。

## Round 1（2026-08-27，冷启动）

逐条核对文件：`route_c_synthesis_plan.md`、`proposal_route_c_tppa1.md`、
`experiment_route_c_tppa1.json`，对照 `library/papers.jsonl` 摘要与
`library/pdfs/Microwave‐Assisted_2020.pdf` 原文。

**数值抽查（全部命中原文）**：725/152 m² g⁻¹ 与 100 °C/1 h vs 120 °C/3 d
（grenu2020microwave PDF 原句）；418 m² g⁻¹ / 30× STY / −89% energy
（xu2026structural 摘要）；703 kg m⁻³ day⁻¹ / 41 mg h⁻¹（peng2016room 摘要）；
3000 m² g⁻¹（karak2017constructing 摘要，且方案已标注为 family 值非 TpPa-1）；
9 N HCl/沸水（kandambeth2012construction 摘要）。未发现编造数值。

**发现的问题**：

| # | 严重度 | 维度 | 位置 | 问题 | 处置 |
|---|--------|------|------|------|------|
| R1-1 | major | 证据 | experiment JSON `optimizations.O2.quantified_gain` | "+50% CO2 uptake at 298 K" 缺比较基线，可能被误读为相对溶剂热基线；摘要原文是 vs 同溶剂(diacetin)批次 | 修：补 "vs batch (diacetin)" |
| R1-2 | minor | 安全 | plan §5 / JSON step 0 | 自制 Tp 路线（Duff 甲酰化）无安全条目：强酸操作与 HMTA 分解风险未列 | 修：safety 表补一行（不虚构具体 protocol） |
| R1-3 | minor | 证据 | plan §7 PXRD 条目 | 引 zhou2021peg 支撑 "eclipsed-stacking family behavior" 属 wrong-context 边缘：该文是光催化循环中 PEG 锁定堆叠，非粉末 PXRD 对照 | 修：改述为堆叠无序风险提示，引用语境对齐 |
| R1-4 | minor | 新颖性 | proposal 方法草图 | 应显式声明新颖性在于 decision-workflow 打包而非新化学，防止 overselling | 修：加一句限定 |

判定：1 major + 3 minor → 修改后复审（未过）。

## Round 2（2026-08-27，修复后复审）

- R1-1 ✔ JSON 已改为 "+50% CO2 uptake at 298 K vs batch (diacetin)"；与摘要一致。
- R1-2 ✔ plan §5 新增 in-house Tp prep 行（浓酸/HMTA 热分解风险 + 手套/面屏/通风橱）；
  JSON step 0 safety 同步。
- R1-3 ✔ plan §7 PXRD 条目改为「crystallinity vs simulated pattern
  [kandambeth2012construction]; stacking-disorder risk during photocatalytic cycling noted
  [zhou2021peg]」——引用语境对齐。
- R1-4 ✔ proposal 方法草图末尾加限定句。

复查四维：
- 证据真实性：数值抽查全过；19 个引用 key 全部 ⊆ 已审计 bib（37/37 PASS，见
  `state/CITATION_AUDIT.md`），无库外 key、无手写条目。
- 新颖性：定位为 survey-to-synthesis decision workflow（组合空位），与最近邻
  xu2026structural / li2020new / grenu2020microwave 差异成立且已显式限定边界。
- 可行性：单体可购/可制备，五路线均有文献先例；风险与替代路线齐备。
- 安全性：safety 字段覆盖全步骤 + 两条优化 + H2 测试，无空字段。

**判定：0 blocker / 0 major → 通过第一关（对抗审）。**

## 引用二审（第二关）

提案+方案全部 19 key 与 `references.bib` 逐一比对：无 UNVERIFIED/MISMATCH 可能性
（均为当日 `ref_integrity` 闸门 37/37 PASS 的已核条目，未引入任何新文献；
核查记录：`state/CITATION_AUDIT.{json,md}`）。按任务规程不重核已 PASS 条目。

**判定：第二关通过 → 置 `ideas_reviewed` PASS。**
