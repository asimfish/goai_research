# 回环协议（Loop Protocol）

多 agent 协作的核心不是「谁调用谁」，而是**账本驱动的状态机**：
每个 agent 干完活把状态写回账本，orchestrator 看账本决定下一步。
本文件是协议规范；orchestrator skill 是它的执行者。

## 阶段与闸门

| # | 阶段 | 执行者 | 出口闸门 | 闸门判据 |
|---|------|--------|---------|---------|
| 0 | scoping | orchestrator+人 | `scope_confirmed` | scope.md 有主题/边界/子主题清单/目标篇幅 |
| 1 | lit_search | goai-lit-search | `lit_coverage` | coverage_report 全子主题 ok；一轮新增去重后 <5 篇 |
| 2 | ref_gate | goai-ref-guard | `ref_integrity` | references.bib 零 UNVERIFIED/MISMATCH |
| 3 | taxonomy | goai-survey-writer | `taxonomy_ready` | 每叶 ≥3 篇支撑；孤儿论文有处置；贡献声明经用户确认 |
| 4a | figures | goai-figure-studio/-editable | `figures_ready` | 每图 svg+drawio 齐全且过自检 |
| 4b | writing | goai-survey-writer | `draft_complete` | bib_guard + tex_guard PASS；全节成文 |
| 4c | ideas | goai-idea-forge | `ideas_reviewed` | 每条 idea 过对抗审 + 引用二审（跳过时记 WARN） |
| 5 | review | goai-reviewer | `review_pass` | 0 blocker 且 0 major（PASS 须带审稿回执）；或连续两轮仅 minor |
| 6 | final | orchestrator | （无独立 gate） | `check-done` 通过：gate 全 PASS/WARN 且 0 open blocker/major（open minor 由 final 清理后 close） |

4a/4b/4c 无写冲突，**可并行**（见 parallel_run.sh）。

## Issue 路由表

review 产出的 issue 按 target 字段路由回源头阶段：

| target | 谁接活 | 典型内容 |
|--------|--------|---------|
| lit_search | goai-lit-search | 覆盖缺口、漏热点 → 增量补检（不重跑全量） |
| ref_gate | goai-ref-guard | 引用可疑、wrong-context |
| taxonomy | goai-survey-writer | 分类不 MECE、章节错位 |
| figures | goai-figure-studio | 图文不符、图不可读 |
| writing | goai-survey-writer | 无证据断言、术语漂移、AI 腔 |
| ideas | goai-idea-forge | 证据不实、安全缺失 |

**级联规则**：上游返工后，其下游闸门自动失效需复核——
lit_search 变 → ref_gate、taxonomy 需复核；taxonomy 变 → figures、writing 需复核。
orchestrator 负责按此把受影响闸门重置为 PENDING（`gate --status PENDING`）。
机器兜底：gate 记录时带 `--inputs <产物文件列表>` 存 sha256 指纹，
`check-done` 会重算指纹，发现上游产物已变更就自动把该 gate 置回 PENDING
并提示复审——级联失效不依赖编排者记性。

## 轮次与终止

- 一轮 = 阶段 1→5 走完一遍（返工只重跑受影响链路）。
- `next_round` 时机：review 未过且 issue 已路由完毕。
- **终止条件**（满足其一）：
  1. `check-done` 退出码 0（gate 全 PASS/WARN 且无 open blocker/major）
     → 交付；open minor 由 final 阶段清理完后逐条 close；
  2. 达 `--max-rounds`（默认 5）→ 强制收敛：带着未清 minor 交付 + 遗留清单；
  3. 同一 issue 三轮未收敛 → 升级人类决策，暂停该链路。
- **反空转**（阶梯执行，不允许原地换个说法重试）：任何 agent 连续两次
  运行账本无新增 log → orchestrator 判定卡死，记 `event=stall`。
  第一次 stall 换策略（缩小任务/换 agent）并记录所换策略；同一阶段
  第二次 stall 必须升级人类，不得再自选换策略。空转检测只负责报警与
  记录，不得代替审稿闸门改判任何结论。

## 账本操作速查

```bash
T=tools/loopctl.py
python3 $T init --topic "LLM agents for chemistry" --max-rounds 5 \
        --effort balanced --strictness normal --auto-proceed true
python3 $T status                          # 全景：阶段/闸门/开放 issue
python3 $T advance --to lit_search         # 进入阶段
python3 $T gate --name lit_coverage --status PASS --detail "48 篇, 新增 3" \
        --inputs workspace/library/papers.jsonl        # 产物指纹，防 stale
python3 $T gate --name review_pass --status PASS \
        --receipt "model=<审稿模型>;trace=workspace/state/review_traces/round2_1.md"
python3 $T issue add --from-agent goai-reviewer --target writing \
        --severity major --text "S4.2 无证据断言"
python3 $T issue close --id I1 --note "已补 \cite{...}"
python3 $T log --stage writing --agent goai-survey-writer --event done
python3 $T next-round                      # round+1
python3 $T check-done                      # 退出码 0=可交付（重算指纹）
```

## 并行执行协议

```bash
# tasks.tsv：每行 "任务名<TAB>提示词<TAB>本轮产物<TAB>前序依赖（均可选、逗号分隔）"
bash tools/parallel_run.sh --backend codex --jobs 3 tasks.tsv
# 产物：workspace/state/parallel/<run_id>/<任务名>.{jsonl,stderr.log,final.md,process_exit,status,exit}
```
规约：
1. 并行任务**只写自己的分片文件**（sections/NN_*.tex、figures/<name>.*）；
2. 账本写入靠 loopctl 的文件锁串行化，安全；
3. 汇合者（orchestrator）等全部 exit 码，失败任务单独重跑，不阻塞成功者；
4. 建议并行度 ≤4（受 API 限流与本机内存约束）。
5. Codex 默认以 `workspace-write` 运行；stderr 与 JSONL 分流，保证轨迹可解析。
6. 后端退出码为 0 但第三列产物缺失、为空或本轮未更新时，runner 改记
   exit=3，防止沿用旧文件造成假绿；路径前加 `=` 可只检查既有非空文件。
7. 第四列依赖必须引用本文件中已经出现的任务。依赖失败时消费者不启动并记
   `BLOCKED_DEPENDENCY`，消除证据文件尚未生成就开始写作的竞态。
8. 声明产物的任务会收到增量落盘与禁止自读当前活动日志的协议。若进程超时但
   全部声明产物已在本轮写出且非空，`.process_exit`保留124，`.status`记
   `WARN_ARTIFACT_PASS_AFTER_TIMEOUT`，有效`.exit`为0；设
   `RUNNER_TIMEOUT_ARTIFACT_POLICY=fail`可恢复严格失败策略。

## 人类介入点

默认全自动，四处建议人工过目——但每处都定义了**用户不可达时的降级路径**，
非交互客户端（只发一行主题、不会回复确认的场景）不允许卡死在停点上：

- **scope.md 定稿**（方向错了后面全白干）：裸主题且无实质歧义时按已写明的
  默认值自动确认并记 decision；只有歧义会改变研究对象时才真正停下来问。
- **taxonomy 阶段的贡献声明与 motivation**（全文的宪法）：用户不可达时按
  writer skill 的降级规则记录后继续。
- **max-rounds 用尽仍有 blocker**（质量与截稿的取舍）：用户不可达时停止
  并如实汇报未收敛项，绝不谎报完成。
- **idea-forge 的化学实验方案**（安全责任必须人担）：**永不自动确认**；
  用户不可达时该支线记 WARN skipped，终报如实说明，不输出可执行危险协议。

另有全局开关 `init --auto-proceed false`：每轮 review 结束后暂停，
等人类读完审稿报告再继续。该开关只控制轮间暂停，不改变上面四处的分级规则。
