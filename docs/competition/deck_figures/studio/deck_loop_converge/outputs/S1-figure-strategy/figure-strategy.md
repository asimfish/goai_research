# S1-FIGURE-STRATEGY — deck_loop_converge

多智能体并行回环（二）· 四条互搏通道与机械闸门收敛

- primary_reader_question: 这个回环为什么会收敛——谁在互相挑错，谁在机械把关，什么时候停？
- visual_mainline_decision: 本轮产物 → 四条互搏通道挑错 → issue 带 target 经路由表回责任阶段 → 只重跑受影响链路、指纹变更把下游闸门置回 PENDING → 下一轮；无 issue 时 check-done 机械放行 → 交付；三条终止旁路通向人
- contribution_type_visual_priority: mechanism（收敛机制），mainline 是一轮回环的闭合路径；数据流不作主干
- data-flow mainline justified? 否 —— 本图讲的是控制结构 / 收敛机制，数据类标签只作支撑。
- complete-framework eligibility: 四个候选都是整页范围的完整框架图，非局部探针。
- surface style: formal_publication_schematic（作者已接受的设计系统），色族按软件系统重新映射。

## 八种风格组合的规划与打分（选四）
| SC | 名称 | 叙事角色 | 分数 | 选中 | 理由 |
|---|---|---|---|---|---|
| SC2 | 单主干左右 | process narrative | 9 | ✔ | 单主干把"产物 → 挑错 → 路由 → 返工 → 下一轮"画成一条闭合回环，放行出口在主干末端；最贴近 LP "一轮 = 阶段 1→5 走完一遍"。 |
| SC1 | 分层横带 | stage-by-stage narrative | 8 | ✔ | 分层横带把 互搏通道 / 路由与返工 / 机械放行 三段并列，读者一眼看到"谁挑错、谁路由、谁把关"；虚线返工走在带外。 |
| SC8 | 嵌套容器 | scope narrative | 8 | ✔ | 嵌套容器用外框表示自动回环，升级人类落在框外的小插区，直接呈现 LP "人类介入点"的边界语义。 |
| SC4 | 账本为轴 | comparison narrative | 7 |  | 路由表是中继而非比较轴 |
| SC7 | 双栏对照 | contrast narrative | 7 | ✔ | 双栏对照把"互相挑错（认知层对抗）"与"机械把关（控制层拒绝）"分成两栏，共享上游产物与下游交付，突出"模型说了不算"。 |
| SC5 | 阶梯＋汇流 | ordering narrative | 5 |  | 通道之间没有序关系 |
| SC6 | 蛇形分段 | itinerary narrative | 4 |  | 不是步骤序列 |
| SC3 | 枢纽辐射 | taxonomy narrative | 3 |  | 主干是闭环不是分类 |

映射：C01=SC2、C02=SC1、C03=SC8、C04=SC7

四个选中组合的成分为什么互补而不冲突：它们共用同一层表面样式，只在 layout grammar 与 narrative role 上正交发散，
因此四张候选比较的是"同一套视觉语法下哪种版式最贴合系统语义"，而不是四种互相打架的画风。

## S0 语义精度契约的继承
- S1/S4 的 forbidden-edge list 必须含"通道 → 阶段（绕过路由表）"与"升级人类 → 主环"两条
- S4 的 dashed-line budget 只允许一条虚线语义：下一轮返工
- 四条通道必须等宽并排，卡内机理是"一对 token + 双向短箭头 + 判据行"

## 禁止清单（写入四个候选的 negative constraints）
- 不得从任一通道卡直接连到文献检索/写作等阶段（只经路由表）
- 不得把四条通道画成四条流水线或四对打架的人
- 不得把升级人类接回回环
- 不得出现第二种虚线
- 互搏通道不是两条流水线：一张卡内一对角色 token + 一个双向短箭头
- 不得从审稿直接向各阶段拉线；issue 只经路由表回流
- 升级人类是灰族旁路，不接回主环
- 只允许一种虚线语义：下一轮返工
- check-done 与 loopctl 不是智能体，是 teal 工具卡
- 不得出现打架、拳击、盾牌、法官、天平等隐喻图元

## 可见文字白名单
本轮产物 | 稿件 | 图件 | 实验方案 | 引用库 | 互搏通道 | 执行者 | 审稿人 | 提案者 | 攻击者 | 候选 | 审计 | 机械守卫 | 独立上下文 · 三视角 · 两轮起 | 实验构想内部对抗 · 引用二审 | 图件两轮候选制 · issue 台账 | 检查不过即返工 | issue 路由表 | 覆盖缺口 → 文献检索 | 引用可疑 → 引用核查 | 分类不 MECE → 分类法 | 图文不符 → 图件 | 无证据断言 → 写作 | 未落到工艺与前驱体 → 实验构想 | 级联失效 | 上游产物变更 | 指纹重算 | 下游闸门置回 PENDING | 复核 | 只重跑责任阶段 · 下一轮 | 机械放行 | loopctl 拒绝写入 | 跳阶段 | 缺并发证据 | 单轮审稿 | 无回执 | 非 TeX 编译的 PDF | 写不进去 | check-done | 九个闸门全部落账 | 无未关闭的 blocker/major | 回执指向真实审稿记录 | 指纹未变 | 退出码 0 | 交付 | 0 open blocker/major | 终止旁路 | 达到轮次上限 → 带遗留清单交付 | 同一问题三轮未收敛 → 升级人类 | 连续两次无新增日志 → 空转，换策略 | issue 带 target · severity | 路由与返工 | 正式运行 2 轮：首轮 7 项 issue 路由返工，第二轮 0 blocker · 0 major · 0 minor；11 个 issue 全部关闭 | bib_guard · tex_guard · pdf_guard · 语言守卫
