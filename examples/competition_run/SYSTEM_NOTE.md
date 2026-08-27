# SYSTEM NOTE — GoAI Research 多智能体综述系统（比赛实跑说明）

主题：Covalent organic frameworks (COFs) for photocatalytic hydrogen evolution
路线 C 目标物：β-ketoenamine COF TpPa-1 · 实跑日期：2026-08-27 · 轮次：1/4 一轮收敛

## 1. 架构总览

系统 = **账本驱动的状态机** + 七个专职 agent + 四个确定性闸门工具 + 四个 MCP server。
没有"谁调用谁"的硬编排：每个 agent 干完活把状态写回账本（`state/ledger.json`），
orchestrator 看账本决定下一步。所有闸门带产物 sha256 指纹，`check-done` 重算指纹，
上游产物变更会自动把下游闸门打回 PENDING（本次实跑真实触发过一次，见 §4）。

```
scoping → lit_search → ref_gate → taxonomy → (figures ∥ writing ∥ ideas) → review×2 → final
   │          │            │          │            │                          │
scope_confirmed lit_coverage ref_integrity taxonomy_ready figures_ready/draft_complete/ideas_reviewed review_pass
```

组件：
- **agent 规程**（skills/goai-*/SKILL.md）：orchestrator / lit-search / ref-guard /
  survey-writer / figure-studio+figure-editable / idea-forge / reviewer，每个 SKILL 定义
  输入输出、硬性规则与防跳步自查。
- **MCP servers**（server/*.py）：litsearch（arXiv/OpenAlex/Crossref/S2 多源检索）、
  refcheck（DOI/arXiv 权威核查）、figure（figspec→SVG/drawio 渲染）、retro（逆合成，
  本次为 stub 仅演示）。
- **确定性闸门**（tools/）：bank_check（引用支持库格式/候选量/时效）、bib_guard
  （引用整合率/密度/未定义 key）、tex_guard（TODO 残留/悬空 ref/环境闭合）、
  loopctl（账本 CRUD + 指纹 + check-done）。

## 2. 各环节方法论（本次实跑实际执行）

| 环节 | 方法论 | 本次证据 |
|------|--------|---------|
| scoping | 主题 MECE 分解 5 子主题 + 时间窗 + 排除项；无人值守代行确认并留痕 | inputs/scope.md；账本 decision |
| lit_search | 16 查询 × arXiv+OpenAlex 首轮 → snowball 失败如实记录 → 6 gap-fill 查询补 Crossref → 人工相关性筛 37 篇 | notes/search_log.md（429/失败全记录）|
| ref_gate | 全库逐条 verify（DOI→Crossref、arXiv→API 权威比对）零容忍 | state/CITATION_AUDIT.{json,md} 37/37 PASS |
| taxonomy | 5 级 13 叶因子链分类，每叶 ≥3 支撑，零孤儿；贡献声明先行 | notes/taxonomy.md、contribution.md |
| figures | figspec JSON → 渲染 → 源忠实表（每个视觉元素挂 anchor key）→ 白名单文字 → 自检 2 轮 | notes/figure_plan.md、figures/ 四格式 |
| ideas (Route C) | graveyard 禁区检查 → 证据先行提案 → stub 逆合成仅演示并标注 → 对抗审四维（1 major+3 minor 返工）→ 引用二审 | ideas/route_c_*、ideas/review_log.md |
| writing | 范文学习 → 引用支持库（bank_check，默认线 FAIL 留痕后调参）→ 蓝图（节-贡献-完稿检查绑定）→ 逐节 claim-cite 绑定写作 → bib_guard+tex_guard → pdflatex+bibtex 真实编译 | drafts/ 全链、revision_log.md |
| review | R1 同模型冷启动降级（独立性受限声明）：claim-cite 抽查 10 条，0 blocker/2 major/3 minor 路由返工；R2 产物级复验 + 终审三视角，provisional 放行带回执 | state/review_round{1,2}.md、review_traces/ |
| final | check-done 指纹重算（真实抓到 1 个 stale 闸门并复审重记）→ 9 项提交物自查 → 交付 | state/ledger.json 终态 |

## 3. 关键设计原则

1. **每个结论走真实工具调用**：所有量化数字可回溯到库内摘要或库内 PDF 原句
   （微波 725/152 m²/g 来自库内综述 PDF 原文抽取）；文献没有的数值进「待计算清单」
   而非编造（Route C 热力学 T1–T4）。
2. **引用红线双保险**：唯一引用池 references.bib（37 条全过权威核查）+ bib_guard
   闸门（未定义 key = 阻塞，整合率 <90% = 阻塞）。正文 167 次引用 100% 落库。
3. **审稿独立性按可用性降级**：无跨模型通道时冷启动自审 + 显式 provisional 标记 +
   回执 + trace 存档，不冒充独立审稿。
4. **失败留痕**：S2 429 限流、snowball 全 0 命中、bank_check 默认线 FAIL、
   lit_coverage stale——全部如实入账本后再处置，不静默重试。

## 4. 复现步骤

```bash
cd <REPO>
export GOAI_WORKSPACE=<REPO>/workspace_live/competition   # 或新工作区
T=".venv/bin/python tools/loopctl.py"

# 0. 初始化（新跑）
$T init --topic "<主题>" --max-rounds 4 --effort balanced --strictness normal --auto-proceed true

# 1. 按账本状态机推进；每阶段读对应 skills/goai-*/SKILL.md 执行
$T status                      # 看当前阶段与闸门
$T advance --to <stage>        # 阶段推进
$T gate --name <gate> --status PASS --detail "..." --inputs <产物文件>   # 带指纹记闸门

# 2. 确定性闸门（writing 阶段）
.venv/bin/python tools/bank_check.py $GOAI_WORKSPACE/notes/citation_bank.md \
    $GOAI_WORKSPACE/library/references.bib --target-cites 32 [--min-recent 按库时效留痕调参]
.venv/bin/python tools/bib_guard.py $GOAI_WORKSPACE/drafts/sections \
    $GOAI_WORKSPACE/library/references.bib --min-integration 0.9 --min-cites-per-1k 8
.venv/bin/python tools/tex_guard.py $GOAI_WORKSPACE/drafts

# 3. 编译（drafts/ 内，figures pdf 与 references.bib 构建副本已就位）
pdflatex main && bibtex main && pdflatex main && pdflatex main

# 4. 终点判据
$T check-done   # 退出码 0 = 可交付（自动重算指纹抓 stale）
```

MCP 工具在宿主内直接 import 调用（无需起 stdio）：
`from server import litsearch_server; litsearch_server.search_papers(...)`。
逆合成接真实后端需 `GOAI_RETRO_PROVIDER=http GOAI_RETRO_API_URL=<ASKCOS/RXN>`；
stub 输出一律标注「演示数据，非化学结论」。

## 5. 诚实声明（无人值守 run）

- scope 定稿、贡献声明、化学安全三处人类确认点由宿主**代行**并在账本注明；
  正式参赛需人工确认。
- 审稿为同模型降级（provisional），跨模型通道恢复后应补一轮独立复审。
- 逆合成后端为 stub，路线 C 化学内容全部来自文献追溯 + 显式标注的化学推理，
  stub 输出仅作集成演示。
