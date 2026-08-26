# 回环协议（Loop Protocol）

多 agent 协作的核心不是「谁调用谁」，而是**账本驱动的状态机**：
每个 agent 干完活把状态写回账本，orchestrator 看账本决定下一步。
本文件是协议规范；orchestrator skill 是它的执行者。

## 阶段与闸门

| # | 阶段 | 执行者 | 出口闸门 | 闸门判据 |
|---|------|--------|---------|---------|
| 0 | scoping | orchestrator+人 | `scope_confirmed` | scope.md 有主题/边界/子主题清单/目标篇幅 |
| 1 | lit_search | goai-lit-search | `lit_coverage` | coverage_report 全子主题 ok；末轮新增去重后 <5% |
| 2 | ref_gate | goai-ref-guard | `ref_integrity` | references.bib 零 UNVERIFIED/MISMATCH |
| 3 | taxonomy | goai-survey-writer | `taxonomy_ready` | 每叶 ≥3 篇支撑；孤儿论文有处置 |
| 4a | figures | goai-figure-studio/-editable | `figures_ready` | 每图 svg+drawio 齐全且过自检 |
| 4b | writing | goai-survey-writer | `draft_complete` | bib_guard PASS；全节成文 |
| 4c | ideas | goai-idea-forge | `ideas_reviewed` | 每条 idea 过对抗审 + 引用二审 |
| 5 | review | goai-reviewer | `review_pass` | 0 blocker 且 0 major；或连续两轮仅 minor |
| 6 | final | orchestrator | （无独立 gate） | `check-done` 通过：全 gate PASS 且 0 open issue |

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
orchestrator 负责按此把受影响闸门重置为 PENDING。

## 轮次与终止

- 一轮 = 阶段 1→5 走完一遍（返工只重跑受影响链路）。
- `next_round` 时机：review 未过且 issue 已路由完毕。
- **终止条件**（满足其一）：
  1. `check-done` 退出码 0（全 gate PASS 且无 open issue）→ 交付；
  2. 达 `--max-rounds`（默认 3）→ 强制收敛：带着未清 minor 交付 + 遗留清单；
  3. 同一 issue 三轮未收敛 → 升级人类决策，暂停该链路。
- **反空转**：任何 agent 连续两次运行账本无新增 log → orchestrator 判定
  卡死，记 `event=stall` 并换策略（缩小任务/换 agent/升级人类）。

## 账本操作速查

```bash
T=tools/loopctl.py
python3 $T init --topic "LLM agents for chemistry" --max-rounds 3
python3 $T status                          # 全景：阶段/闸门/开放 issue
python3 $T advance --to lit_search         # 进入阶段
python3 $T gate --name lit_coverage --status PASS --detail "48 篇, 增益 3%"
python3 $T issue add --from-agent goai-reviewer --target writing \
        --severity major --text "S4.2 无证据断言"
python3 $T issue close --id I1 --note "已补 \cite{...}"
python3 $T log --stage writing --agent goai-survey-writer --event done
python3 $T next-round                      # round+1
python3 $T check-done                      # 退出码 0=可交付
```

## 并行执行协议

```bash
# tasks.tsv：每行 "任务名<TAB>提示词"
bash tools/parallel_run.sh --backend codex --jobs 3 tasks.tsv
# 产物：workspace/state/parallel/<run_id>/<任务名>.{log,exit}
```
规约：
1. 并行任务**只写自己的分片文件**（sections/NN_*.tex、figures/<name>.*）；
2. 账本写入靠 loopctl 的文件锁串行化，安全；
3. 汇合者（orchestrator）等全部 exit 码，失败任务单独重跑，不阻塞成功者；
4. 建议并行度 ≤4（受 API 限流与本机内存约束）。

## 人类介入点

默认全自动，但三处建议人工过目（orchestrator 会停下来问）：
- scope.md 定稿（方向错了后面全白干）；
- max-rounds 用尽仍有 blocker（质量与截稿的取舍）;
- idea-forge 的化学实验方案（安全责任必须人担）。
