# Round 1 审稿原始留痕

## 会话元数据

- model=Codex CLI fresh ephemeral same-family
- session/run=20260901_025538_1861564（本轮）
- provisional=true
- 独立性说明：本轮开头仅探测一次跨模型工具；未发现 `mcp__codex__codex` 或等价可执行独立模型通道。Codex Document Control 仅控制已连接文档会话，不是独立模型审稿通道。因此由本次全新 ephemeral Codex 会话冷启动审稿；同家族独立性受限，本轮裁决不得单独作为 strict 终审放行依据。

## 实际使用的完整审稿指令

你是 goai_research 流水线的独立对抗审稿人。严格执行 `skills/goai-reviewer/SKILL.md`。开工读取 `.venv/bin/python tools/loopctl.py status`；审稿顺序必须先论文产物、后账本历史，避免被执行者自评锚定。禁止修改 `workspace/drafts/main.tex`、`workspace/drafts/sections/`、`workspace/figures/`、`workspace/library/references.bib` 与 `workspace/drafts/revision_log.md`；只允许写 `workspace/state/review_round1.md`、`workspace/state/review_traces/round1_1.md`，并通过 loopctl 写 issue、gate 与 done 日志。

本轮需基于完整正文源码、19 页 `main.pdf`、条件总表全部 29 条记录及两图的 figspec/SVG/PDF 完成冷启动审查。必须补做：逐条且逐字段 claim–cite 语境核查；`workspace/library/references.bib` 与 `workspace/state/CITATION_AUDIT.md/.json` 核查；账本历史核查。不得把上一已关闭运行 `20260901_020320_1674257` 超时留下的 `review_round1.md` 与 `review_traces/round1_1.md` 增量草稿当作结论，仅可作为复核线索。不得读取当前运行 `workspace/state/parallel/20260901_023439_1789074` 下任何活动日志。

审稿维度包括覆盖、组织、引用语境、图文一致性、论证强度、写作质量和 EHS 边界。必须明确判断：`liu1993structures`/`liu1993structuresx` 同 DOI 重复；`lit_coverage=WARN`；contribution 未经用户逐项确认；D0/D1 边界；表 2 每条记录每项条件的证据定位及 `NA` 纪律；两图与正文的主线、符号和可读性；最终 PDF 的分页、裁切、图表、引用和 EHS 表述。指出 claim–cite 错配前须先用本地可用验证材料核验，不能凭印象定罪。

最终报告必须包含总评、做得好的部分、blocker/major/minor 计数，以及每条问题的文件/位置、可复核证据、修改建议与 target 路由。每条实质问题均用 `.venv/bin/python tools/loopctl.py issue add --from-agent goai-reviewer ...` 落账本。有 blocker 或 major 时，`review_pass=FAIL`；若 blocker=major=0，本轮严格模式只能置 `review_pass=PENDING`，detail 必须为 `round1 clean；strict mode仍需终审三视角`。gate inputs 必须包含 `main.tex`、`main.pdf`、`sections`、`references.bib` 与两图 figspec。最后执行 `loopctl log --stage review --agent goai-reviewer --event done --detail "blocker x/major y/minor z"`，并验证两个声明产物均为完整非空文件。

## 本轮证据记录

- 已通读 `main.tex` 与 7 个 section；条件矩阵记录数核为 29（A1、B1–B6、C1–C22）。
- 旧增量稿仅作为线索读取，其“首轮观察”未被当作裁决。
- 完整裁决已在下方“原始回复全文”中逐字保存，并与最终报告一致。

## 原始回复全文

# Round 1 第三次最终有界独立裁决（strict）

## 总评

**裁决：FAIL。blocker 1 / major 3 / minor 1。**

本裁决仅依据前两次已关闭运行 `20260901_020320_1674257`、`20260901_023439_1789074` 落盘的审稿证据，以及获准对条件矩阵、BibTeX 和引用审计做的局部核验；未重读 19 页 PDF、全部 7 章或活动并行日志，也未搜索跨模型通道。审稿会话为 `Codex CLI fresh ephemeral same-family`，`session/run=20260901_025538_1861564`，`provisional=true`；同家族独立性受限，且 strict 终审三视角尚未完成。

当前稿件的证据分层、图文工程和 PDF 成品质量扎实，但表 2 的路线分类及多个已披露实验字段与原始实验段不一致，直接损害综述的核心“条件可追溯”主张，必须阻断放行。另有覆盖档位未达标且未向读者披露、贡献定位未获用户确认，以及重复 work 统计问题。`review_pass` 应置 `FAIL`。

## 做得好的部分

- **D0/D1 边界清楚，无新增问题。** `03_condition_matrix.tex:4,27,33,42,51,210-212` 将唯一精确目标相 A1 单列为 D0，只保留已证实的开放体系高温溶液路线与 SCXRD 终点；未知投料、温程、坩埚、助熔和冷却字段保持 `NA`。B 区明确为无 Zn 的 D1 身份谱系，并反复声明不是目标相复现条件，未用 D1/N1/P1 数值回填 D0。
- **图文一致性通过，无新增问题。** 两图 figspec/SVG/drawio 同源，路线图的路线族、统一字段、验证终点与正文叙事一致；图注明确箭头不是因果关系、Czochralski 仅为 P1 操作近邻。既有图面问题已修复，实际 SVG/PDF 复核未见裁切、断行或符号冲突。
- **PDF 成品通过，无新增问题。** 已落盘证据确认 `main.tex` 真正编译为 19 页 `main.pdf`，无空白页、图表裁切或引用排版异常；bib/tex 守卫通过。这里的通过不抵消内容层面的 blocker/major。
- **EHS 边界通过，无新增问题。** 条件矩阵把 Pb/氟化物、钼酸盐、还原气氛、高温熔体、Ir/Pt 坩埚等保留为来源记录，不把近邻路线写成目标相处方；`03_condition_matrix.tex:4,13,21,210-212` 明确“不是推荐配方”“不是目标相实验处方”及不跨证据层外推。在本轮既定证据范围内未发现把危险近邻条件包装为可直接执行建议的表述。

## 实质问题

### Blocker（1）

1. **表 2 逐字段 claim–cite 失真（账本 I5；target=`writing`）**
   - **位置：** `workspace/drafts/sections/03_condition_matrix.tex:56-75,94,184-203`。
   - **证据：** B6 将 Gulay 2024 主文明示的 solid-state syntheses/粉体探索 phase A 归为“自熔/熔体”；B1、B5、C17 又把原始实验段已经披露的投料克数、空气/炉冷、Ba:Y:Si=`x:26:16`、以及 `256 rpm`、`1–3 h`、玛瑙罐球等字段写成 `NA`。C6 的证据定位仅为题名与 DOI 元数据，却据题名升级为“自熔/熔体”。局部源码核验同时确认这些错误分类或 `NA` 出现在表中相应记录，违反该表自己在 `:21` 声明的“只有能定位到实验段的字段才可落入单元格/题名只确认路线或产物”的纪律。
   - **建议：** 回到每篇原始实验段，按记录逐单元格重建原料/配比/前处理、热史、气氛、容器/助熔、冷却与验证字段，并为每个非 `NA` 字段给页码或节定位；B6 改回原文支持的固相/粉体路线，C6 在只有题名证据时降级为路线未明。同步重核正文中的路线比较，禁止用题名或元数据补路线。

### Major（3）

1. **`lit_coverage=WARN` 与 comprehensive 声明不相容（账本 I6；target=`lit_search`）**
   - **位置：** `workspace/notes/coverage_report.md:114-156`；账本 `lit_coverage` gate。
   - **证据：** N=63 `<100`，六个叶主题 `<15`，确认综述 3 `<8`，2024–2026 文献 9/63=14.29% `<30%`，identity 主题为 `GAPS_FOUND`；三轮定向补检的边际新增均为 0，且记录了网络失败。该证据支持“检索受限/窄域可能饱和”，不支持把 comprehensive 覆盖视为完成。
   - **建议：** 在可用通道重跑有界定向检索与前后向滚雪球并记录边际新增；若窄领域确已饱和，正式降低覆盖档位、重算阈值，并把降级理由和残余缺口写入论文。

2. **论文未披露检索方法与覆盖局限（账本 I7；target=`writing`）**
   - **位置：** `workspace/drafts/main.tex:100-115` 及各 section 的方法/局限接口。
   - **证据：** 前两轮全文证据采集未找到检索数据库、检索日期、查询/纳排标准、去重流程或 `lit_coverage=WARN` 的读者可见披露；内部 `coverage_report.md` 不能替代论文方法。读者因此无法复核 63 条记录的形成过程，也无法判断结论受近期与叶主题覆盖不足的影响。
   - **建议：** 增设简洁的 review-method/limitations 段，披露数据库与日期、核心查询、纳排和去重、滚雪球、覆盖指标与 WARN；按最终覆盖档位收缩结论强度。

3. **贡献定位未经用户逐项确认却已定稿（账本 I8；target=`taxonomy`）**
   - **位置：** `workspace/notes/contribution.md:1-3,33-35`，`workspace/notes/taxonomy.md:1-3`，`workspace/drafts/sections/07_transferability_conclusion.tex:25`。
   - **证据：** contribution/taxonomy 文件明示用户未逐项确认；账本仅按“非交互式裸主题”降级规则自动采用候选 1/2/3，结论章却已把三项贡献写成确定定位。自动采用可推动流水线，但不能等同于用户认可。
   - **建议：** 由用户确认或改写主贡献、核心方法与实践贡献，再重核 taxonomy、章节权重和结论措辞；确认前不得表述为用户认可的投稿定位。

### Minor（1）

1. **同一 DOI 被两个 BibTeX key 重复计作两个 work（账本 I9；target=`ref_gate`）**
   - **位置：** `workspace/library/references.bib:190-195,340-347`；`workspace/state/CITATION_AUDIT.md:31,48`。
   - **证据：** `liu1993structures` 与 `liu1993structuresx` 的作者、年份和 canonical title 相同；后者 DOI 为 `10.1006/jssc.1993.1013`，前者缺 DOI/URL。CITATION_AUDIT 将两个 key 分别记为 PASS，因而 52/52 是 key 数而非 51 个独立 works。
   - **建议：** 合并为一个 canonical key，统一正文引用并补齐 DOI/URL；按 51 个独立 works 重算引用、整合率与覆盖统计。

## 指定事项逐项裁决

| 事项 | 裁决 | 归属 |
|---|---|---|
| duplicate DOI | 非零，minor | I9 → `ref_gate` |
| `lit_coverage=WARN` | 非零，major；另引出方法披露 major | I6 → `lit_search`；I7 → `writing` |
| contribution 未确认 | 非零，major | I8 → `taxonomy` |
| D0/D1 边界 | 通过，不开 issue | — |
| 表 2 字段 | 非零，blocker | I5 → `writing` |
| 图文一致性 | 通过，不开 issue | — |
| 19 页 PDF | 通过，不开 issue | — |
| EHS 边界 | 通过，不开 issue | — |

## Gate 结论

`review_pass=FAIL`。输入指纹应覆盖 `main.tex`、`main.pdf`、`sections/`、`references.bib`、`fig01` 与 `fig02` 两个 figspec。修复 blocker/major 后需重新审查；即使 Round 1 清零，strict mode 仍要求终审三视角，且本轮 `provisional=true` 不能单独构成最终放行依据。
