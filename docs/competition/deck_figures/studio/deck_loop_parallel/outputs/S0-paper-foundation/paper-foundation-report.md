# S0-PAPER-FOUNDATION — deck_loop_parallel

- 图：多智能体并行回环（一）· 账本驱动的状态机与并行分派
- 用途：关键技术实现 · 多智能体并行回环 1/2（世界人工智能开源大赛 · SAGE-Mat 答辩 PPT，16:9）
- contribution_type_visual_priority：system/process（多智能体流水线的控制结构），mainline 是阶段状态机；数据流不作主干
- primary_reader_question：一个研究主题进来后，七个专职智能体怎样被账本按阶段分派、并行干活而互不冲突？
- visual_mainline_decision：研究主题 → 范围界定 → [文献检索 ∥ 风格库] → 引用核查 → 分类法 → [图件 ∥ 写作 ∥ 实验构想] → 对抗审稿 → 终稿交付；回环账本是唯一状态源，每个阶段的出口闸门落在账本上

## S0-00 输入清点
本图的"论文"是系统自己的规范文档与正式运行记录（仓库 asimfish/goai_research）：
- **AR** = docs/ARCHITECTURE.md（一图总览、分层设计、账本结构、并行模型）
- **LP** = docs/LOOP_PROTOCOL.md（阶段与闸门表、流程机械约束、并行执行协议）
- **OR** = skills/goai-orchestrator/SKILL.md（"你只做四件事"、阶段状态机、并发是默认）
- **PR** = tools/parallel_run.sh（tasks.tsv 四列、分片产物、exit=3、BLOCKED_DEPENDENCY）
- **FR** = docs/competition/FINAL_REPORT.md §3（认知层 / 确定性工具层 / 控制层，九道闸门）
- **RUN** = 正式案例_BYZSO冷启动/RUN_MANIFEST.json（29 批 / 40 个子任务 / 单批最多 4 路 / 134 次 MCP 调用）

运行时 = 5090 Codex `image_gen`（route lock）；生图画布 1536x1024（图像通道固定尺寸）；原生重建目标 = 16:9 幻灯片内容区（1536×864 画布，标题栏之下）。

## S0-01 精读：实体与证据锚点
| 实体 | 证据 | 出图角色 |
|---|---|---|
| 编排器 goai-orchestrator | OR 开头："建账本 → 分派 → 验闸门 → 路由返工"，四件事 | 控制层卡，卡内四步机理链 |
| 回环账本 ledger.json | AR §3：gates / issues / log 三个字段；loopctl 原子写 + 排它文件锁；gate 带 sha256 产物指纹 | 控制层账本卡，卡内三行记录项 |
| 并行 runner parallel_run.sh | PR 头注释 + LP 并行执行协议：tasks.tsv 每行 任务名/提示词/产物/依赖 → 子进程各写自己的分片文件 → 汇合者等全部退出码 | 控制层卡，卡内四步机理链 |
| 范围界定 | LP 阶段 0：orchestrator + 人；gate scope_confirmed | 认知层阶段卡 |
| 文献检索 goai-lit-search | LP 阶段 1 + 并发证据：lit_coverage 需 ≥3 条 lit_search done 分片；OR："lit_search 按子主题切 ≥3 路并发" | 认知层阶段卡，卡内三个并行分片 token（无箭头） |
| 风格库 goai-style-bank | OR 状态机：与 lit_search 两路并行；gate style_bank_ready | 认知层阶段卡 |
| 引用核查 goai-ref-guard | LP 阶段 2：references.bib 零 UNVERIFIED/MISMATCH；gate ref_integrity | 认知层阶段卡 |
| 分类法 goai-survey-writer | LP 阶段 3：每叶 ≥3 篇支撑；gate taxonomy_ready | 认知层阶段卡 |
| 图件 goai-figure-studio | LP 阶段 4a；OR："figures 按图并发"；并发证据 ≥2 条 | 认知层阶段卡（三路并行之一） |
| 写作 goai-survey-writer | LP 阶段 4b；OR："writing 按章节并发"；并发证据 ≥2 条 | 认知层阶段卡（三路并行之一） |
| 实验构想 goai-idea-forge | LP 阶段 4c：每条 idea 过对抗审 + 引用二审，材料 idea 带前驱体预测 | 认知层阶段卡（三路并行之一） |
| 对抗审稿 goai-reviewer | LP 阶段 5：0 blocker 且 0 major，≥2 轮；issue 带 target 路由回源头阶段 | 认知层阶段卡 |
| 终稿交付 | OR 第 7 条：tex+pdf、references.bib、figures 三件套 + 重建脚本、审计记录、账本全文 | 主干终点，tier-4 交付标签 |
| 九道出口闸门 | LP 阶段表 + FR §3 "九道流程闸门"：scope_confirmed / lit_coverage / style_bank_ready / ref_integrity / taxonomy_ready / figures_ready / draft_complete / ideas_reviewed / review_pass | tier-4 药丸，落在账本带上，绝不是卡片 |

## 关系（每条连线的证据）
- **编排器 ⇄ 回环账本** — 证据：AR "唯一可信状态源。所有 agent 只通过 loopctl 读写"；OR "所有状态只存在于回环账本…不允许口头交接"；画法：一条捆绑双向连线，标签 loopctl 读写 · 文件锁
- **编排器 → 阶段主干** — 证据：OR 第 3 条 "逐阶段分派——并发是默认，串行是降级"；画法：一条分派连线进入主干起点
- **范围界定 → {文献检索, 风格库}** — 证据：OR 状态机 "[lit_search ∥ style_bank] ← 两路并行"；画法：唯一的第一个分叉
- **{文献检索, 风格库} → 引用核查 → 分类法** — 证据：LP 阶段 1→2→3 前置顺序；画法：汇合后主干两段
- **分类法 → {图件, 写作, 实验构想}** — 证据：OR "[figures ∥ ideas ∥ writing] ← 三路并行"；LP "4a/4b/4c 无写冲突，可并行"；画法：唯一的第二个分叉
- **{图件, 写作, 实验构想} → 对抗审稿 → 终稿交付** — 证据：LP 阶段 5→6；画法：汇合后主干两段
- **对抗审稿 ⇢ 责任阶段（虚线）** — 证据：LP Issue 路由表 + 级联规则；画法：只画一条虚线回到主干，标签 issue 路由返工（细节见下一页）
- **每个阶段 → 账本带上的闸门药丸** — 证据：AGENTS.md 铁律 1 "收工必须 loopctl log --event done"；LP 并发证据；画法：阶段卡与账本带之间不逐一拉线：闸门药丸直接坐在账本带上、与阶段对齐，表示"落账"
- **并行 runner → 两个分叉点** — 证据：LP 并行执行协议：分片文件、文件锁串行化账本、汇合者等 exit 码；画法：两条短线从 runner 卡到两个分叉点，标签 各写自己的分片文件

## S0-02 语义精度契约（摘要，完整版见 s0-semantic-precision-contract.json）
- 「七个专职智能体的并行」→ 并行 = 各自只写自己的分片文件，收工在账本记一条 done；账本靠文件锁串行化；汇合者等全部退出码
  - 安全画法：在两个分叉点把并行支线画成并排的等宽卡（2 路和 3 路），从同一个分叉点出发、在同一个汇合点并入一束
  - 禁止：禁止把七个智能体画成七条各自完整的流水线；禁止画智能体之间互相对话的连线
- 「闸门」→ 闸门是阶段的出口条件，记录在账本里，由 loopctl 机械核验
  - 安全画法：闸门名做成 tier-4 药丸，坐在账本带上、与对应阶段对齐
  - 禁止：禁止把闸门画成卡片或菱形判定框；禁止把闸门名放进阶段卡标题
- 「账本」→ 唯一状态源：gates / issues / log 三个字段 + 产物指纹
  - 安全画法：一张宽账本卡或一条横贯全幅的账本带，卡内三行记录项
  - 禁止：禁止画成数据库圆柱或云；禁止让阶段卡各拉一条线到账本（用对齐表示落账）
- 「审稿返工」→ issue 带 target 路由回责任阶段；细节在下一页
  - 安全画法：一条虚线从对抗审稿回到主干，标签 issue 路由返工
  - 禁止：禁止从审稿卡向每个阶段各画一条线

## S0-03/04 风险筛查与锁定
| 风险 | 处置 | 状态 |
|---|---|---|
| 九个闸门名在一条账本带上排不下（英文标识符较宽） | S1/S4：允许药丸两行排列或缩短为阶段对齐的短药丸；原生重建时按幻灯片字号实测 | risk_locked |
| 生图模型会把并行画成七条流水线 | 契约锁 1；S3 把"复制流水线"记 high | risk_locked |
| 生图模型会给阶段卡编造内部步骤 | 禁止清单；S3 记 high | risk_locked |

## S0-06 readiness
`S0_FOUNDATION_READY_WITH_RISK` — 缺口已在风险寄存器中锁定，且全部转成"不得画"的约束，不阻塞 S1。
