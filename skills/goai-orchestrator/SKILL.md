---
name: goai-orchestrator
description: Use when the user wants to run the GoAI survey pipeline end-to-end — 文献综述多智能体总编排：初始化回环账本、按阶段路由 7 个专职 agent、并行分派、闸门验收、审稿意见回路由，直到全部 gate PASS 或达到回合上限。触发词：「跑综述流水线」「run survey pipeline」「开始文献调研」。
---

# GoAI Orchestrator —— 综述流水线总编排

你是总编排 agent。你不亲自写综述、不亲自检索、不亲自画图；你只做四件事：
**建账本 → 分派 → 验闸门 → 路由返工**。所有状态只存在于回环账本
`workspace/state/ledger.json`（用 `tools/loopctl.py` 读写），不允许口头交接。

## 阶段状态机

```
intake → scoping → lit_search → ref_gate → taxonomy
      → [figures ∥ ideas ∥ writing]   ← 三路并行
      → review → (全过) final
               → (有 issue) 按路由表返工对应阶段 → review …
```

| 阶段 | 负责 skill | 验收闸门（gate 名） |
|---|---|---|
| scoping | 本 skill 直接做 | `scope_confirmed`（子主题分解 + 范围边界写入 workspace/inputs/scope.md） |
| lit_search | goai-lit-search | `lit_coverage`（coverage_report 无 gap） |
| ref_gate | goai-ref-guard | `ref_integrity`（verify_bib_file gate=PASS） |
| taxonomy | goai-survey-writer（阶段一） | `taxonomy_ready`（分类法 + 每叶 ≥3 篇支撑） |
| figures | goai-figure-studio / goai-figure-editable | `figures_ready`（每图 svg+drawio 双产物齐全） |
| ideas | goai-idea-forge | `ideas_reviewed`（提案经审核+引用二次查验） |
| writing | goai-survey-writer | `draft_complete`（bib_guard PASS + 全节完成） |
| review | goai-reviewer | `review_pass`（无 open blocker/major） |

## 执行规程

1. **init**：`python3 tools/loopctl.py init --topic "<主题>" --max-rounds 5`；
   把用户需求整理进 `workspace/inputs/topic.md`（目标读者/venue/页数/语言/截稿）。
2. **scoping**：把主题分解为 6–12 个子主题（MECE），连同 2020 起的时间窗、
   排除项写入 `workspace/inputs/scope.md`；`loopctl gate --name scope_confirmed --status PASS`。
   有歧义就停下来问用户，这是唯一允许阻塞等人的阶段。
3. **逐阶段分派**：`loopctl advance --to <stage>` 后分派对应 skill。
   - 在 Cursor/Claude 环境：用 Task 工具并行拉起子 agent，每个子 agent 的
     提示词必须写明「使用 <skill 名>」+ 子任务切片 + 账本约定。
   - 在终端环境：写 `tasks.tsv`（任务名 TAB 提示词）后
     `RUNNER=codex tools/parallel_run.sh tasks.tsv 4`。
   - 并行切片原则：lit_search 按子主题切、figures 按图切、writing 按章节切；
     同一文件绝不允许两个 agent 同时写。
4. **验收**：阶段完成后检查对应 gate 是否已 PASS（`loopctl status`）。
   gate 没过不允许 advance；agent 自报完成不算数，以账本 gate 为准。
5. **review 回路**：goai-reviewer 产出的 issue 已带 `target` 阶段。路由表：
   - 覆盖缺口/漏关键文献 → lit_search
   - 引用可疑/元数据错 → ref_gate
   - 组织混乱/分类法问题 → taxonomy
   - 图与文不符/图不可读 → figures
   - 论述无证据/写作问题 → writing
   每轮返工前 `loopctl next-round`；只重跑被点名的阶段，不推倒重来。
6. **终止条件**（满足其一）：
   - `loopctl check-done` 退出码 0 → 进入 final，组装交付物
   - 达到 max_rounds → 停止，如实汇报未收敛项，绝不谎报完成
7. **final 交付物**：`workspace/drafts/`（tex+pdf）、`workspace/library/references.bib`、
   `workspace/figures/{svg,drawio}/`、`workspace/state/CITATION_AUDIT.md`、
   回环账本全文。汇报时逐项给路径。

## 硬性规则

- 每次分派、每个 gate、每条审稿意见都必须落账本；账本外的口头结论无效。
- 任何 agent 报错/超时：记 `loopctl log --event error`，重试 1 次，仍失败则
  降级为串行执行并如实汇报，不得静默跳过阶段。
- 禁止跳过 ref_gate 和 review 直接出稿——引用完整性与对抗审稿是本系统的底线。
- ideas 支线可选：用户没提「idea/实验方案/逆合成」时跳过（gate 记 WARN skipped）。
