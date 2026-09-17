# S1-FIGURE-STRATEGY — deck_loop_parallel

多智能体并行回环（一）· 账本驱动的状态机与并行分派

- primary_reader_question: 一个研究主题进来后，七个专职智能体怎样被账本按阶段分派、并行干活而互不冲突？
- visual_mainline_decision: 研究主题 → 范围界定 → [文献检索 ∥ 风格库] → 引用核查 → 分类法 → [图件 ∥ 写作 ∥ 实验构想] → 对抗审稿 → 终稿交付；回环账本是唯一状态源，每个阶段的出口闸门落在账本上
- contribution_type_visual_priority: system/process（多智能体流水线的控制结构），mainline 是阶段状态机；数据流不作主干
- data-flow mainline justified? 否 —— 本图讲的是控制结构 / 收敛机制，数据类标签只作支撑。
- complete-framework eligibility: 四个候选都是整页范围的完整框架图，非局部探针。
- surface style: formal_publication_schematic（作者已接受的设计系统），色族按软件系统重新映射。

## 八种风格组合的规划与打分（选四）
| SC | 名称 | 叙事角色 | 分数 | 选中 | 理由 |
|---|---|---|---|---|---|
| SC4 | 账本为轴 | comparison narrative | 9 | ✔ | 账本为轴把"一切写进同一个账本"画成字面意义：账本带横贯中间，阶段主干在上、编排器与 runner 在下，闸门药丸落在带上；最贴近 AR "唯一可信状态源"。 |
| SC1 | 分层横带 | stage-by-stage narrative | 8 | ✔ | 分层横带把控制层 / 认知层 / 闸门三段并列，直接对应 FR §3 的分层表述；与 SC4 的差异在叙事角色（分层 vs 以账本为轴）。 |
| SC2 | 单主干左右 | process narrative | 8 | ✔ | 单主干最贴近 OR 状态机的线性陈述，两个分叉与一条虚线返工都能画在同一条主干上；账本退为主干下方的带。 |
| SC3 | 枢纽辐射 | taxonomy narrative | 7 | ✔ | 枢纽辐射把编排器放在枢纽、七个智能体成扇形叶，正是 AR 一图总览的画法；并行在这里读成"同时被分派"，分叉语义弱但分派语义强。 |
| SC5 | 阶梯＋汇流 | ordering narrative | 6 |  | 阶段之间没有需要排序的同类项 |
| SC8 | 嵌套容器 | scope narrative | 6 |  | 内外框语义在本图不存在（人类旁路在下一页） |
| SC6 | 蛇形分段 | itinerary narrative | 5 |  | 主干只有六段，不需要换行 |
| SC7 | 双栏对照 | contrast narrative | 4 |  | 不是两个机制的对照 |

映射：C01=SC4、C02=SC1、C03=SC2、C04=SC3

四个选中组合的成分为什么互补而不冲突：它们共用同一层表面样式，只在 layout grammar 与 narrative role 上正交发散，
因此四张候选比较的是"同一套视觉语法下哪种版式最贴合系统语义"，而不是四种互相打架的画风。

## S0 语义精度契约的继承
- S1/S4 的 forbidden-edge list 必须含"智能体 ↔ 智能体"与"阶段卡 → 账本逐一拉线"两条
- S4 的 dashed-line budget 只允许一条虚线语义：issue 路由返工
- 并行支线必须是等宽并排卡 + 同源分叉 + 同点汇合；分叉点旁挂并发证据标签

## 禁止清单（写入四个候选的 negative constraints）
- 不得从任一阶段卡单独拉线到账本卡（闸门药丸与阶段对齐即表示落账）
- 不得给分类法、引用核查等卡片编造内部步骤链（源文本只给出口条件）
- 不得把九个闸门画成九个菱形或九张卡
- 不得画 MCP 服务器、数据库、云
- 不得把七个智能体画成七条完整流水线（并行 = 分片写 + 账本汇合，不是复制流程）
- 不得画智能体之间互相对话的连线（口头交接无效，账本是唯一状态源）
- 闸门不是模块：只能是账本带上的药丸，不得画成卡片或菱形
- 不得从审稿卡向每个阶段各画一条返工线（只画一条虚线回主干）
- 不得把 MCP 服务器画成独立模块（工具调用只出现在统计标签里）
- 不得出现"大脑""机器人"类隐喻图元

## 可见文字白名单
研究主题 | 范围界定 | 文献检索 | 风格库 | 引用核查 | 分类法 | 图件 | 写作 | 实验构想 | 对抗审稿 | 终稿交付 | 编排器 | 回环账本 | 并行 runner | 建账本 | 分派 | 验闸门 | 路由返工 | 闸门 | 问题 | 日志 | 子进程 | 各写自己的分片文件 | 汇合 | 子主题 1 | 子主题 2 | 子主题 3 | 认知层 | 控制层 | loopctl 读写 · 文件锁 | issue 路由返工 | ≥3 路分片 · 各记一条 done | 按图 · 按章节 · 按目标 并发 | tex · pdf · bib · 图源 · 账本 | 正式运行 29 批 · 40 个子任务 · 单批最多 4 路 · 134 次 MCP 工具调用 | goai-orchestrator | goai-lit-search | goai-style-bank | goai-ref-guard | goai-survey-writer | goai-figure-studio | goai-idea-forge | goai-reviewer | ledger.json | parallel_run.sh | tasks.tsv | gates | issues | log | scope_confirmed | lit_coverage | style_bank_ready | ref_integrity | taxonomy_ready | figures_ready | draft_complete | ideas_reviewed | review_pass | check-done 退出码 0
