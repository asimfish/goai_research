# S0-PAPER-FOUNDATION — deck_loop_converge

- 图：多智能体并行回环（二）· 四条互搏通道与机械闸门收敛
- 用途：关键技术实现 · 多智能体并行回环 2/2（世界人工智能开源大赛 · SAGE-Mat 答辩 PPT，16:9）
- contribution_type_visual_priority：mechanism（收敛机制），mainline 是一轮回环的闭合路径；数据流不作主干
- primary_reader_question：这个回环为什么会收敛——谁在互相挑错，谁在机械把关，什么时候停？
- visual_mainline_decision：本轮产物 → 四条互搏通道挑错 → issue 带 target 经路由表回责任阶段 → 只重跑受影响链路、指纹变更把下游闸门置回 PENDING → 下一轮；无 issue 时 check-done 机械放行 → 交付；三条终止旁路通向人

## S0-00 输入清点
本图的"论文"是系统自己的规范文档与正式运行记录（仓库 asimfish/goai_research）：
- **OR** = skills/goai-orchestrator/SKILL.md 第 3 条"四条互搏通道"、第 4 条验收、第 6 条终止条件
- **LP** = docs/LOOP_PROTOCOL.md（Issue 路由表、级联规则、轮次与终止、反空转、流程机械约束）
- **AR** = docs/ARCHITECTURE.md §3（gate 带 receipt 与 inputs 指纹；check-done 重算指纹）
- **FR** = docs/competition/FINAL_REPORT.md §3（审稿人与执行者职责分离；三视角审稿；同一问题三轮未收敛转人工）
- **RUN** = 正式案例_BYZSO冷启动/ledger.json（2 轮；11 个 issue：4 blocker · 4 major · 3 minor 全部关闭；51/51 引用核对）+ FR §4（首轮 7 项 issue，第二轮 0）

运行时 = 5090 Codex `image_gen`（route lock）；生图画布 1536x1024（图像通道固定尺寸）；原生重建目标 = 16:9 幻灯片内容区（1536×864 画布，标题栏之下）。

## S0-01 精读：实体与证据锚点
| 实体 | 证据 | 出图角色 |
|---|---|---|
| 本轮产物 | OR 第 7 条交付物：稿件 / 图件 / 实验方案 / 引用库 | 主干起点卡（slate），卡内四个产物 token |
| 执行者 ⇄ 审稿人 | OR 互搏通道 1；FR "独立上下文…领域、方法和编辑三个视角"；LP review_pass ≥2 轮 | 通道卡，卡内一对角色 token + 双向短箭头 + 判据行 |
| 提案者 ⇄ 攻击者 | OR 互搏通道 2："idea-forge 内部提案-攻击双角色 + 引用二审" | 通道卡 |
| 候选 ⇄ 审计 | OR 互搏通道 3："figure-studio 两轮候选制的 issue-ledger 审计" | 通道卡 |
| 稿件 ⇄ 机械守卫 | OR 互搏通道 4："bib_guard/tex_guard/…/academic_language_guard 的机械互搏——检查不过即返工，模型说了不算" | 通道卡 |
| issue 路由表 | LP Issue 路由表：target → 接活阶段（lit_search / ref_gate / taxonomy / figures / writing / ideas） | 控制层账本卡，卡内六行"问题 → 阶段"记录项 |
| 级联失效 | LP 级联规则 + AR：gate 带 --inputs 指纹，check-done 重算，上游变更自动把 gate 置回 PENDING | 控制层卡，卡内四步机理链 |
| loopctl 拒绝写入 | LP 流程机械约束表：前置顺序 / 并发证据 / 审稿轮次 / 回执与 PDF / 完整性 | 控制层卡，卡内五行勾选记录项 |
| check-done | LP 终止条件 1 的四个机械判据 (a)–(d) | 控制层卡，卡内四步机理链，出口 退出码 0 |
| 终止旁路 | LP 终止条件 2、3 + 反空转 | gray 卡，卡内三个 token（无箭头） |
| 统计 | RUN + FR §4 | tier-4 gray 药丸 |

## 关系（每条连线的证据）
- **本轮产物 → 四条通道** — 证据：OR "四条互搏通道…验收时逐条核对"；画法：一条分叉进四张并排卡
- **四条通道 → issue 路由表** — 证据：LP "review 产出的 issue 按 target 字段路由回源头阶段"；amber 标签 issue 带 target · severity；画法：四路并入一束
- **issue 路由表 → 级联失效 → 本轮产物（下一轮）** — 证据：LP "上游返工后，其下游闸门自动失效需复核"、"一轮…返工只重跑受影响链路"；画法：一条虚线闭环，标签 只重跑责任阶段 · 下一轮
- **issue 路由表 → check-done（无 issue 时）** — 证据：LP 终止条件 1；画法：实线，标签 0 open blocker/major
- **loopctl 拒绝写入 → 账本写入口** — 证据：LP "loopctl gate 在写账本时拒绝一切绕过行为"；画法：loopctl 卡挂在路由表与 check-done 之间，一条短线标签 写不进去
- **check-done → 交付** — 证据：LP 终止条件 1 "退出码 0 → 交付"；画法：主干终点
- **回环 → 终止旁路** — 证据：LP 终止条件 2（max-rounds）、3（三轮未收敛 → 升级人类）、反空转 stall；画法：一条实线从回环侧面出去到 gray 卡；不接回

## S0-02 语义精度契约（摘要，完整版见 s0-semantic-precision-contract.json）
- 「互搏通道」→ 两个职责分离的角色互相挑错：审稿人独立上下文，守卫是确定性脚本
  - 安全画法：一张卡内一对角色 token 用一个双向短箭头相连，下面一行判据
  - 禁止：禁止把一条通道画成两条流水线；禁止画成打架、盾牌对撞的隐喻
- 「issue 路由」→ issue 带 target 与 severity，经路由表回到责任阶段，只重跑受影响链路
  - 安全画法：四条通道并入一束进路由表；路由表是唯一的中继，一条虚线闭环回到本轮产物
  - 禁止：禁止从每条通道各拉线到各阶段（蛛网）
- 「机械放行」→ check-done 只按四个机械判据返回 0；loopctl 在写入时拒绝绕过
  - 安全画法：两张 teal 工具卡，判据做成勾选行 / 机理链，出口标签 退出码 0
  - 禁止：禁止把 check-done 画成智能体或人
- 「终止旁路」→ 轮次上限、三轮未收敛、空转三种情况把决定交给人
  - 安全画法：一张 gray 卡在回环之外，一条实线从回环出去，不接回
  - 禁止：禁止把升级人类接回主环；禁止画人形

## S0-03/04 风险筛查与锁定
| 风险 | 处置 | 状态 |
|---|---|---|
| 文字量大：路由表六行 + 拒绝清单五行 + 判据四行 | S1/S4：允许把路由表与拒绝清单各压成一张卡，字号不低于 2.2% 画布高；原生重建按幻灯片字号实测 | risk_locked |
| 生图模型会把互搏画成打架/对撞隐喻 | 契约锁 6；S3 记 high | risk_locked |
| 生图模型会把升级人类接回主环 | 契约锁 3；S3 记 high | risk_locked |

## S0-06 readiness
`S0_FOUNDATION_READY_WITH_RISK` — 缺口已在风险寄存器中锁定，且全部转成"不得画"的约束，不阻塞 S1。
