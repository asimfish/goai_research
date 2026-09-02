# 文献检索统一日志

## 汇合说明

- 主题：`Ba₅Y₁₂Zn[O(SiO₄)]₈` 及其结构相近化合物的合成条件。
- 正式档位：`niche-balanced`（2026-09-01 reviewer I6 复核后降级）；原
  `comprehensive` 的总库 100–150、八叶各至少 15、综述至少 8、近三年
  至少 30% 保留作未完成审计，不再声称已完成。降级阈值与依据见
  `coverage_report.md` 和 `scope.md`。
- 本文件是已关闭并发检索的串行降级汇合日志。它合并下列三个非空原始切片日志，
  原文件继续保留以便逐项复核：
  - `workspace/notes/search_identity_structure.md`（19,961 bytes；子主题 1–3）
  - `workspace/notes/search_synthesis_routes.md`（19,968 bytes；子主题 4–5）
  - `workspace/notes/search_substitution_evidence.md`（16,531 bytes；子主题 6–8）
- 用户指定的已关闭 run `20260831_193753_5998` 验收：
  - `lit_identity_structure`: `.status=WARN_ARTIFACT_PASS_AFTER_TIMEOUT`, `.exit=0`；
    stderr 明示 1800 s runner timeout；日志非空；无独立 `.validation.log`。
  - `lit_synthesis_routes`: `.status=WARN_ARTIFACT_PASS_AFTER_TIMEOUT`, `.exit=0`；
    stderr 明示 1800 s runner timeout；日志非空；无独立 `.validation.log`。
  - `lit_substitution_evidence`: `.status=PASS`, `.exit=0`；stderr 只有 runner 的
    stdin 提示；日志非空，且 final 明示未执行公共 coverage/BibTeX。
  - 原公共 `lit_merge_coverage` 为 `.status=BLOCKED_DEPENDENCY`, `.exit=4`；其
    validation 仅记录 `style_bank (exit=124)` 阻塞。当前 `style_bank_ready=WARN`
    已由账本按真实缺口登记，依用户指令不再等待。
- 本轮没有读取上述 run 的任何 JSONL，也没有读取活动 run
  `workspace/state/parallel/20260831_202519_280611` 下的日志。

## 范围与纳排

- 纳入目标相、具有 SCXRD/PXRD-Rietveld/中子衍射/明确空间群与拓扑证据的
  直接同型、近同晶胞、结构派生与受控固溶系列，以及能提供可复现实验条件的
  原始论文、学位论文和权威结构记录。
- 综述仅作谱系与滚雪球入口；具体合成条件回到原始来源。
- 排除只有元素或组成相近而无晶体学关系的材料、纯计算预测、不可追溯聚合摘要、
  无关玻璃/玻璃陶瓷和仅性质研究。`BYZSO` 的电子元件/OCR 噪声、COD 分页邻项、
  产品页及数据库自动“相似论文”均不进入核心池。
- 目标式同时检索 `Ba5Y12Zn[O(SiO4)]8`、`Ba5Y12ZnSi8O40`、
  `Ba5 O40 Si8 Y12 Zn`、`BYZSO` 及文字名称；记号是否等价只据论文/COD/电荷
  与晶体结构核验，不凭记忆更正。

## 第 0 轮：本地语料优先

- `local_corpus_status`: `ok=true`，`duckdb-parquet`，`private-full-corpus`，
  15 个分片，非 synthetic/public compact。
- 子主题 1–3 查询 `Ba5Y12Zn`（默认及 120 s 复核）；子主题 4–5 查询
  `Ba5Y12Zn`、`Ba₅Y₁₂Zn`、`barium yttrium zinc silicate`；子主题 6–8 查询
  `Ba5Y12Zn`、`Ba5Y12ZnSi8O40`、`Ba5Y12ZnO8(SiO4)8`、`Ba5Ln12Zn`、
  `O8(SiO4)8`。均使用 `max_results<=10`, `context_lines=1`。
- 所有扫描在 30–120 s 预算内超时，返回 0 条且 `timed_out=true`；因此只能写
  “本地轮不完备”，不能推断本地库无文献。获得 DOI 后的目标及若干 2024 DOI
  `lookup_local_doi` 亦为 `found=false`，只代表本地 DOI 索引缺口。

## 第 1 轮：原生多源关键词矩阵

- sources 均为 `arxiv,openalex,semanticscholar,crossref,dblp`，每源上限 15。
- 代表查询：
  - 身份/结构：`Ba5Y12Zn SiO4 crystal structure`、`Ba5Y12ZnSi8O40 crystal`、
    `Ba5Y12Zn[O(SiO4)]8 space group lattice`、`I-42m ZnSi4O16`、
    `Ba5Ln12Zn silicate`、`Ba5RE12Zn silicate`。
  - 合成：`Ba5Y12Zn`、`Ba5Y12ZnSi8O33`、
    `barium yttrium zinc silicate` 与 `synthesis/solid state/crystal growth/flux`。
  - 替代/证据：`Ba5Y12Zn silicate crystal structure`、
    `Ba5.20Y13Si8O41 I-42m`、`Ba5Y13[SiO4]8O8.5 structure`。
- 所有原生源均报 `ConnectError: [Errno 1] Operation not permitted`；自动
  snowball 的 Semantic Scholar/OpenAlex 路由也受同一网络策略限制。零返回不是
  阴性文献证据。切片随后使用可访问的出版者页、DOI 元数据、RSC ESI、COD、
  IUCr、机构库和原始论文索引交叉核验，并只把可追溯记录交给
  `save_to_library`。

## 第 2 轮：目标论文、结构表与实验字段检索

### 身份与结构基线

- 目标命中：Ababaikeri et al., 2024, *New Journal of Chemistry* 48,
  3594–3602, DOI `10.1039/D3NJ04480G`；RSC 出版者页/ESI/COD 7063074
  交叉核验。
- 核验字段：`Ba5Y12Zn[O(SiO4)]8 = Ba5Y12ZnSi8O40`；四方
  `I-42m` (No. 121)，`a=18.7014(6) Å`, `c=5.3640(2) Å`；BaO8、YO7、
  ZnO4、SiO4 配位及孤立 `[ZnSi4O16]`/`[SiO4]` 构件。
- 目标的精确原料比、峰温/保温/冷却仍未从可访问主文或 ESI 核得；只确认开放
  体系高温溶液法、单晶和 SCXRD/EDS/PXRD。第三方片段不升级为直接证据。

### 结构谱系后向滚雪球

- 目标 ESI 表 S4/参考文献 → 精确题名/作者/DOI → 出版者或期刊索引核验；
  共纳入 Y2SiO5/Y2Si2O7 多型、Ba–Si–O 拓扑、BaMSiO4、BaZn2Si2O7、
  Ba2ZnSi2O7、BaZnSi3O8、固溶/相变和综述入口等记录。
- 子主题 1–3 的分批 `save_to_library`：`before=9, added=11, total=20`；
  `20/11/31`；`31/11/42`。随后前向新增 Gu et al. 2025 一条（仅上下文，
  非直接结构近邻），`before=42, added=1, total=43`；五类种子/综述再新增 5，
  `43/5/48`。该切片工具物理新增 39，目标 DOI 因并发去重不重复计数。
- 结构直接/派生证据包括 Felsche 1973、Sun et al. 2014、Thieme & Rüssel 2022
  三个明确综述入口，以及一系列可核验 DOI/无 DOI 题录；无 DOI 条目保留“无 DOI”，
  未猜标识符。

### 固相、陶瓷、晶体生长和助熔

- 网页/出版者补偿矩阵覆盖目标式实验字段、Ba–Zn–Si 结构近邻与固相扩展、
  Ba–Zn–Si 助熔/晶体、Y–Si–O Czochralski/助熔、学位论文和机械活化。
- 代表直接路线：BaZnSi3O8 的水介质球磨、1000 °C/3 h 煅烧和
  1090–1120 °C/3 h 烧结；Ba2ZnSi2O7 的空气/氧/氮/还原气氛对照；
  β-Y2Si2O7 的 Na2MoO4–Pt 1473 K/24 h、2 K h−1 慢冷；Zn2SiO4 的
  Pb2ZnSi2O7 熔剂 1300→960 °C、1 °C h−1；Y2SiO5 的 Ir–N2 Czochralski。
- 本切片首先写入目标 1 条；后续共享库 `before=50, added=13, total=63`，
  因而可归属新增 14 条。对 6 条已有 DOI 的路线证据补录经去重为 added=0。

### 替代、证据质量与可复现缺口

- 第一轮发现目标、`Ba5+xY13Si8O41`/Ho 类比物、151 组 flux 实验、
  `BaxY26Si16O71+x` 重审/球磨复现、`Ba5Y13[SiO4]8O8.5`、BaY16Si4O33，
  共 9 条发现；首批工具从共享 1 条增至 9 条，物理新增 8。
- 后向滚雪球纳入 BaMSiO4、BaZn2Si2O7、Ba2ZnSi2O7、BaZnSi3O8、
  BaZn2-xCoxSi2O7、Ba1-xSrxZn2Si2O7、Ba/Sr/Zn/Si/Ge 固溶体 7 条；共享库
  已有去重记录，仅物理新增 2，不能把其他切片的并发写入计作本切片新增。
- 强证据结论：Zn 目标与 Ba5Y13 家族均为 `I-42m` 且晶胞接近，但把
  `Y3+→Zn2+` 与氧量变化解释成实际位点替代仍只是跨文献计量推断；没有梯度固溶、
  原位表征或逐位点映射，禁止写成已证实同型/替代机制。
- 目标相尚未找到独立团队的重复合成与结构精修；投料摩尔比、完整热史、产率和
  相纯量化是直接缺口。

## 第 3 轮：定向收敛与明确阴性证据

- 结构切片 C1：`Ba5Gd12Zn`、`Ba5Lu12Zn`、`Ba5Yb12Zn`、
  `Ba5Sc12Zn` + silicate/crystal，新增 0。
- 结构切片 C2：目标精确式分别联用 `solid solution`、`superstructure`、
  `isotypic`、`derivative`，以及展开式复核，新增 0。最后边际序列为
  S3=5、C1=0、C2=0。
- 合成切片：相同 DOI + 原料/温度/坩埚/冷却字段词的末轮主要返回重复，新增 0；
  自动引用源被网络权限阻断后停止无差别扩展。
- 替代切片末轮：`Ba3Zn4Si4O15 topology`、`BaZnSi3O8 based ceramics
  structure`、`Ba1-xSrxZn2Si2O7 solid solution single crystal`、
  `BaZn2-xMxSi2O7 HT-XRD`、`Ba Y Zn silicate superstructure`，新增 0；
  边际序列 9→7→0，且最后命中均为已去重、性质导向或仅同元素而结构不同。
- 对目标相/直接近邻问题，连续低于 10 且最后轮新增为 0；继续扩词只会引入
  组成相近的弱相关材料，故按 strict 纳排停止。

## 合并后的数量与真实性边界

- 三切片结束时共享 `papers.jsonl` 为 63 条，逐行解析无错误；物理新增数不能
  跨切片相加成独立总数，因为共享库并发去重且各次 `before` 是即时快照。
- 直接目标结构主论文目前只有 1 篇。明确综述入口至少 3 篇；切片没有声称达到
  comprehensive 的综述 ≥8。
- 子主题 1–2、6–8 的直接强相关证据明显不足每题 15；质量/复现主题复用同一批
  原始实验记录，不把同一篇论文拆成多篇计数。
- 本轮不会为达到 100 条总量而加入只有 Ba/Y/Zn/Si/O 元素相近、却没有晶体学
  或实验路线关系的记录。最终是否补检以及 gate 状态以统一 coverage 审计为准。

## 串行汇合补检（最多三轮）

统一 `coverage_report` 首次运行得到 `library_size=63`、
`verdict=GAPS_FOUND`，明确 gap 为“身份与记号核验”（1 条）。comprehensive
人工配额还显示多个子主题不足 15、综述不足 8、近三年占比不足 30%。据此只做
以下三轮定向补检；每轮原生 sources 均为
`arxiv,openalex,semanticscholar,crossref,dblp`、`limit_per_source=15`：

1. 身份别名轮：`"Ba5Y12Zn[O(SiO4)]8" OR "Ba5Y12ZnSi8O40"
   crystal structure identity`，不限年份。五源均返回
   `ConnectError: [Errno 1] Operation not permitted`，0 条。
2. 目标合成字段轮：`"D3NJ04480G" synthesis flux temperature cooling
   Ba5Y12Zn`，不限年份。五源同样因网络权限返回 0 条。
3. 近同晶胞/综述/新近轮：`"Ba5Y13[SiO4]8O8.5" OR
   "Ba5+xY13Si8O41" review synthesis`，年份 2024–2026。五源同样因网络
   权限返回 0 条。

为区分“API 被拒绝”与“检索阴性”，同一三轮检索式又通过可用网页检索通道复核：
第一轮只恢复 RSC 的已入库目标论文 `10.1039/D3NJ04480G` 及其二手重复页；
第二轮仍只返回同一 RSC 主文/ESI线索，未出现可核验的新增实验论文；第三轮没有
发现新的原始综述或目标家族论文。RSC forward-link 中出现的光学晶体、硼酸盐、
氟化物及供应商页面没有目标晶体学关系，全部排除。三轮去重新增均为 0，未调用
`save_to_library`，共享库仍为 63 条。

停止理由：身份 gap 针对的是 2024 年首次报道的单一目标相；精确式、展开式、
DOI、近同晶胞式、结构术语与引文链均已覆盖，继续扩大到一般钡/钇/锌硅酸盐会把
只有元素或性质语境相近的结果纳入。严格范围内的真实文献总量不足 100，保留
可复现的查询式、逐源错误和 0 新增证据，并按 skill 将 `lit_coverage` 记 WARN。

## Reviewer I6 定向复核（2026-09-01）

### 复核前统计与有界设计

- 起始库：63 条；八叶命中 `1,16,15,8,6,5,7,14`；确认综述 3；
  2024–2026 为 `9/63=14.29%`；既有补检边际新增 `0,0,0`。
- 本轮只补检“目标/近同晶胞结构家族 + 合成关系”，不再重复一般
  Ba/Y/Zn/Si/O 近义词。原生检索请求 sources=
  `arxiv,openalex,semanticscholar,crossref,dblp`、`limit_per_source=10`：
  1. `"flux-grown tetragonal Ba-Y-silicate" Ho isotypic`
  2. `"Ba5+xY13Si8O41" "I-42m" synthesis`
  3. `"Ba5Y13[SiO4]8O8.5" flux crystal structure`
- 首次五源调用中 arXiv/OpenAlex/Crossref/DBLP 可连接；Semantic Scholar 出现
  HTTP 429，前两式重试成功，第三式未在限流通道继续空转。随后仅以
  OpenAlex/Crossref 对三式做同式恢复（不是扩词重搜）：每式合并返回 10 条。
  第一式唯一严格相关结果是已入库 `10.1039/D4SC04440A`；其余为公式解析噪声、
  无关 tetragonal/flux 材料或无结构关系硅酸盐。关键词矩阵新增 0。

### 前后向滚雪球与候选审计

- 统一参数：`direction=both`、每个方向 `limit=12`。种子覆盖直接目标、最新
  近同晶胞、系统助熔实验和既有综述：
  - `10.1039/D3NJ04480G`：references=12、citations=3；Semantic Scholar
    返回空列表异常，工具自动回退 OpenAlex `W4391116450`。新候选
    NdBSiO5 与 2026 `BaScSi2O6F` 均非同型/同拓扑；后者为 `P4/mbm`、
    `a=8.8965 Å, c=8.0336 Å` 的含氟独立结构，仅在光学语境引用目标，排除。
  - `10.1039/D4SC04440A`：references=12、citations=0；无未入库的范围内候选。
  - `10.1021/acs.cgd.6b01448`：references=12、citations=3；Semantic Scholar
    异常后回退 OpenAlex `W2552059179`。`K3RESi2O7`、`BaREE2Si3O10`、
    `Ba2Gd2(Si4O13)` 等为不同组成/不同硅酸根拓扑，通用 flux 生长论文不提供
    目标或已纳入近邻的直接条件，均按 scope 排除。
  - `10.1039/D2CE00667G`：references=0、citations=1；无未入库的范围内候选。
- 本轮滚雪球新增 0；定向补检总新增 0。候选只经题名、DOI 与出版者结构摘要
  核验，没有把网页结果直接写入库，也没有手编 BibTeX。

### 正式降档与停止理由

- 四轮定向边际新增为 `0,0,0,0`。I6 轮在公共接口恢复后仍为 0，窄主题文献量
  不足是主要约束；继续扩到一般稀土硅酸盐会破坏晶体学关系边界。
- 正式由 `comprehensive` 降为 `niche-balanced`。重算阈值：总量≥50；身份叶
  ≥1 篇直接主文且精确检索/双向滚雪球收敛；两个结构核心叶各≥12；五个路线/
  控制/证据叶各≥5；确认综述≥3；2024–2026≥10%。当前 63 条全部达到这些档位
  配额，但目标单一主文、无独立重复合成仍是残余 gap；因此 gate 保持 WARN，
  且明确不声称 comprehensive 完成。
