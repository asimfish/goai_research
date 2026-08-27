<div align="center">

# GoAI Research 📚⚔️

**多智能体流水线：一个研究主题进去，一篇引用可信、图纸可编辑的综述论文出来。**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-25%20passing-brightgreen.svg)](tests/test_offline.py)
[![MCP](https://img.shields.io/badge/MCP-4%20servers%20%C2%B7%2019%20tools-8A2BE2.svg)](server/)
[![Skills](https://img.shields.io/badge/skills-8%20agents-orange.svg)](skills/)

中文版 README | [English](README.md)

</div>

> 🔍 **检索求全，引用零信任，图纸永远可编辑。**
> 五源文献检索 + 引文滚雪球；逐条核验的引用闸门；一份图纸源文件同时渲染出
> 论文 SVG 和 draw.io 原生可编辑文件；idea 生成可接逆合成预测器——全部接进一个
> 账本驱动的回环，由对抗审稿人把返工路由到对应阶段，直到所有闸门通过。

> 🪶 **轻量设计，零锁定。** 智能层是 8 个纯 Markdown skill，任何 LLM agent
> 都能读——Codex CLI、Claude Code、Cursor 或你自己的 harness；确定性层是 4 个
> 可离线测试的小 MCP server。没有框架、没有数据库、没有守护进程。随便 fork、改写、适配你的技术栈。

![GoAI Research pipeline](examples/pipeline.png)

*这张图就是系统自己画的：一份 [`figspec`](examples/pipeline.figspec.json) 源文件，
同时渲染出 [`pipeline.svg`](examples/pipeline.svg)（论文用）、
[`pipeline.drawio`](examples/pipeline.drawio)（draw.io 打开直接继续编辑）
和上面的 PNG（自检用）。*

## 目录

1. [不只是一段提示词](#1--不只是一段提示词)
2. [快速开始](#2--快速开始)
3. [内部构成](#3--内部构成)
4. [回环机制](#4--回环机制)
5. [永远可编辑的图纸](#5--永远可编辑的图纸)
6. [引用完整性](#6--引用完整性)
7. [Idea 锻造与逆合成](#7--idea-锻造与逆合成)
8. [并行执行](#8--并行执行)
9. [宿主接入](#9--宿主接入) · Codex / Claude Code / Cursor
10. [配置](#10--配置)
11. [测试](#11--测试)
12. [设计笔记](#12--设计笔记) · 为什么 MCP+skill、为什么跨模型审稿
13. [引用本项目](#13--引用本项目)
14. [License 与贡献](#14--license-与贡献)

---

## 1. 🎯 不只是一段提示词

**全流程模式** —— 给一个主题，跑完整条综述回环：

```
用 goai-orchestrator 跑一篇综述：主题「diffusion models for molecule
generation」，侧重 2022 年后，目标 25 页，先给我 scope.md 确认。
```

**每个环节也可以单独用：**

```
用 goai-lit-search 检索 "LLM agents for robotics"，给我覆盖率报告
用 goai-ref-guard 核查 workspace/library/references.bib
用 goai-figure-studio 把 taxonomy.md 画成主图
用 goai-figure-editable 把 figures/old_diagram.png 转成可编辑的 .drawio
用 goai-idea-forge 从文献缺口挖 idea 并生成实验方案
```

orchestrator 读回环账本、按阶段分派对应 agent、验收出口闸门、把审稿 issue
路由回属主阶段——直到 `check-done` 变绿或轮次预算用尽（两种情况都如实汇报，
绝不把没做完的综述谎报成完成）。

## 2. 🚀 快速开始

```bash
git clone https://github.com/asimfish/goai_research && cd goai_research
bash install.sh     # 建 .venv、装依赖、生成填好绝对路径的 MCP 配置

# Codex CLI
cat configs/codex.config.toml >> ~/.codex/config.toml
ln -s "$PWD/skills"/goai-* ~/.codex/skills/

# Claude Code
#   把 configs/claude.mcp.json 合并进 ~/.claude.json 的 mcpServers
ln -s "$PWD/skills"/goai-* ~/.claude/skills/

# 冒烟检查
.venv/bin/python -m pytest tests/ -q     # 25 个离线测试，不需要网络
```

要求：Python ≥ 3.10（install.sh 有 [uv](https://github.com/astral-sh/uv) 就用 uv）。
可选增强：`brew install --cask drawio`（.drawio 导出 png/pdf）、
`.venv/bin/pip install -e '.[preview]'`（图纸自检出 PNG 预览）、
Node.js（官方 [draw.io MCP](https://github.com/jgraph/drawio-mcp)，浏览器实时编辑）。

## 3. 🧩 内部构成

**从这里开始** —— 用例 → 入口：

| 用例 | 入口 |
|---|---|
| 主题 → 完整综述，端到端 | [goai-orchestrator](skills/goai-orchestrator/SKILL.md) |
| 检索全量相关文献 + PDF + BibTeX | [goai-lit-search](skills/goai-lit-search/SKILL.md) |
| 核查引用的作者/顺序/年份/venue | [goai-ref-guard](skills/goai-ref-guard/SKILL.md) |
| 画分类法 / 框架 / 时间线图 | [goai-figure-studio](skills/goai-figure-studio/SKILL.md) |
| 把现成图片变成 draw.io 可编辑 | [goai-figure-editable](skills/goai-figure-editable/SKILL.md) |
| taxonomy → 蓝图 → 逐节 → LaTeX | [goai-survey-writer](skills/goai-survey-writer/SKILL.md) |
| 挖缺口 → 提案 → 实验方案 | [goai-idea-forge](skills/goai-idea-forge/SKILL.md) |
| 对抗审稿 + issue 自动路由 | [goai-reviewer](skills/goai-reviewer/SKILL.md) |

<details>
<summary><b>三层架构</b> —— skill（认知）· MCP server（确定性）· 回环工具（控制）</summary>

| 层 | 内容 | 为什么 |
|---|---|---|
| `skills/` —— 8 个 SKILL.md | 宿主 LLM 执行的方法论：建分类法、claim 绑定写作、审稿判断 | 认知活交给最强的可用模型；skill 不带 API key、不内嵌 LLM SDK |
| `server/` —— 4 个 MCP server、19 个工具 | 检索聚合去重、BibTeX 解析与作者比对、figspec 校验与双渲染、逆合成适配 | 确定性重活：可离线测试、跨宿主复用 |
| `tools/` | `loopctl.py` 账本 CLI · `bib_guard.py` 引用闸门 · `tex_guard.py` 组稿闸门 · `bank_check.py` 支持库校验 · `parallel_run.sh` | 回环控制与硬闸门：纯本地、零 LLM |

| MCP server | 工具 |
|---|---|
| `goai-litsearch` | `search_papers` `snowball` `lookup` `download_pdf` `save_to_library` `export_bibtex` `coverage_report` |
| `goai-refcheck` | `verify_entry` `verify_bib_file` `deep_audit_info` |
| `goai-figure` | `figspec_schema` `validate_figspec` `render_figure` `svg_file_to_drawio` `drawio_export` `list_figures` |
| `goai-retro` | `provider_status` `predict_retro` `make_experiment_plan` |

</details>

<details>
<summary><b>工作区布局</b> —— 一切产物落盘，全程可审计</summary>

```
workspace/
├── library/     papers.jsonl + references.bib + pdfs/
├── notes/       scope / taxonomy / citation_bank / figure_plan
├── figures/     svg/ + drawio/ + figspec/ + png/   ← 同一份源，永不漂移
├── drafts/      blueprint + sections/*.tex + revision_log
├── ideas/       proposal_*.md + experiment_*.json + review_log
└── state/       ledger.json（回环账本）+ 审计报告
```

</details>

## 4. 🔄 回环机制

```
intake → scoping → lit_search → ref_gate → taxonomy
      → [figures ∥ writing ∥ ideas]      ← 三路并行
      → review → 全部闸门 PASS → final
               → 有 issue → 路由回属主阶段 → 再审 …
```

每个阶段有**出口闸门**，记录在账本 `workspace/state/ledger.json` 里，只能通过
`tools/loopctl.py` 读写。审稿人产出带 `target` 阶段的结构化 issue；上游返工时
orchestrator 按级联规则把下游闸门重置复核，`--max-rounds` 限定轮次，同一 issue
三轮未收敛就升级人类。完整协议见 [docs/LOOP_PROTOCOL.md](docs/LOOP_PROTOCOL.md)。

| 阶段 | Agent | 出口闸门 |
|---|---|---|
| scoping | orchestrator + 你 | `scope_confirmed` |
| lit_search | goai-lit-search | `lit_coverage` —— 全子主题覆盖，末轮新增去重后 < 5 篇 |
| ref_gate | goai-ref-guard | `ref_integrity` —— 零 UNVERIFIED / MISMATCH |
| taxonomy | goai-survey-writer | `taxonomy_ready` —— 每叶 ≥ 3 篇支撑 |
| figures | goai-figure-studio / -editable | `figures_ready` —— 每图 svg + drawio 齐全 |
| writing | goai-survey-writer | `draft_complete` —— bib_guard PASS，全节完成 |
| ideas | goai-idea-forge | `ideas_reviewed` —— 对抗审 + 引用二次核查 |
| review | goai-reviewer | `review_pass` —— 0 blocker 且 0 major |

## 5. 🎨 永远可编辑的图纸

这里的图从来不是一张死位图。单一事实源是 **figspec** —— 一个描述节点/分组/
边/文本的小 JSON。一次渲染同时产出：

- `figures/svg/<name>.svg` —— LaTeX 用（`\includesvg`，或经 drawio CLI 转 pdf）
- `figures/drawio/<name>.drawio` —— **原生 mxGraph XML**：
  [draw.io](https://app.diagrams.net) / draw.io Desktop 直接打开，拖动节点连线跟随
  （source/target 是绑定的，不是画上去的）
- `figures/png/<name>.png` —— 供 agent 自己走「渲染 → 自检 → 修正」回环（≤ 3 轮）

已有的图不是 figspec 怎么办？

- **结构化 SVG** → `svg_file_to_drawio` 确定性逆向
  （恢复分组容器、重挂边 label，再重渲染）
- **位图 / PDF 里的图** → `goai-figure-editable` 走视觉重建回环：
  读图 → 结构清单 → figspec → 渲染 → 并排对照 → 修正

可编辑性有明确验收标准：文字是原生文本、形状可拖拽、连线绑定节点——
「看起来像」不算过。

## 6. 🛡 引用完整性

LLM 写综述最致命的失败就是编造或张冠李戴的引用。GoAI 把引用当**零信任输入**：

1. **唯一引用池。** 写作者只能引用 `workspace/library/references.bib` 里的 key，
   这个文件由 `save_to_library` / `export_bibtex` 生成——禁止手写、禁止凭模型记忆。
2. **快速档**（`goai-refcheck`）：每条引用重新查 Crossref / OpenAlex / arXiv /
   DBLP；标题模糊匹配，作者比对遗漏/伪造/**顺序错误**，年份与 venue 交叉核对。
   判定：`PASS` / `FIX`（可自动修正）/ `MISMATCH` / `UNVERIFIED` —— 后两者堵闸门。
3. **深度档**（可选）：本地 [super_ref](https://github.com/asimfish/super_ref)
   证据先行审计——下载 PDF 与注册库元数据，四个隔离 agent 交叉核查，修正需作者批准。
4. **稿侧闸门**：`bib_guard.py` —— 未定义的 `\cite` key 阻塞构建；库内条目
   整合率 < 90% 阻塞（孤儿条目要么在正文找到落点，要么移出库）；引用密度
   < 8 条/千词警告。`tex_guard.py` —— TODO 占位残留、`\input`/图文件缺失、
   悬空 `\ref`、环境不闭合，全部阻塞组稿。
5. **语境核查**（reviewer）：抽查 claim–引用对，验证被引论文真的支撑该 claim ——
   最诊断性也最容易被漏掉的检查。

## 7. 💡 Idea 锻造与逆合成

`goai-idea-forge` 从已核验的文献库挖三类缺口信号——覆盖缺口（没人做的子主题）、
矛盾信号（论文结论互相打架）、组合空位（两个分类法分支从未交叉）——每条提案
必须挂真实引用 key 作证据。

化学 / 材料类 idea 调用 `goai-retro` MCP server：

```bash
export GOAI_RETRO_PROVIDER=http
export GOAI_RETRO_API_URL=https://your-askcos-instance/api/retro   # ASKCOS / IBM RXN / 自建
export GOAI_RETRO_API_KEY=...                                      # 可选
```

默认 provider 是 **stub**：输出带显式标注的演示路线，让整条回环无需化学后端也能
跑通——skill 层硬性禁止把 stub 输出当化学结论。`make_experiment_plan` 把路线转成
方案骨架，`safety` 字段强制填写；方案要过**双关**：对抗审核（证据/新颖性/可行性/
安全性）+ 所引文献的二次核查。

## 8. ⚡ 并行执行

图、章节、idea 之间没有共享写文件——orchestrator 直接扇出：

```bash
# tasks.tsv：每行 <任务名>\t<提示词>
bash tools/parallel_run.sh --backend codex --jobs 3 tasks.tsv   # 或 --backend claude
```

保证并行安全的规约：每个任务只写自己的分片文件（`sections/NN_*.tex`、
`figures/<name>.*`）；公共文件（main.tex、references.bib）只由汇合步骤动；
账本写入靠 loopctl 文件锁串行化。日志和退出码落在
`workspace/state/parallel/<run_id>/`。

## 9. 🖥 宿主接入

<details>
<summary><b>Codex CLI</b></summary>

```bash
cat configs/codex.config.toml >> ~/.codex/config.toml   # install.sh 已生成
ln -s "$PWD/skills"/goai-* ~/.codex/skills/
```

仓库根的 `AGENTS.md` 给 Codex 提供了在本仓库工作时的路由表与铁律。

</details>

<details>
<summary><b>Claude Code</b></summary>

把 `configs/claude.mcp.json` 合并进 `~/.claude.json` 的 `mcpServers`，然后：

```bash
ln -s "$PWD/skills"/goai-* ~/.claude/skills/
```

</details>

<details>
<summary><b>Cursor</b></summary>

把同样四个 server 条目加进 Cursor 的 `mcp.json`；skill 用
`@skills/goai-orchestrator/SKILL.md` 引用或软链到技能目录。并行支线可以用
IDE 内置的 Task 子代理代替 `parallel_run.sh`。

</details>

## 10. ⚙️ 配置

| 环境变量 | 默认 | 作用 |
|---|---|---|
| `GOAI_EMAIL` | `goai-research@example.com` | Crossref/OpenAlex polite pool 联系邮箱（更好的限流待遇） |
| `GOAI_HTTP_MIN_INTERVAL` | `1.0` | 同主机请求最小间隔（秒） |
| `GOAI_HTTP_MAX_RETRIES` | `2` | 429/503 有界重试（尊重 Retry-After） |
| `GOAI_WORKSPACE` | `workspace` | 所有产物的落盘位置 |
| `GOAI_RETRO_PROVIDER` | `stub` | `stub`（演示）或 `http`（真实预测器） |
| `GOAI_RETRO_API_URL` / `GOAI_RETRO_API_KEY` | — | 逆合成后端地址 / 鉴权 |
| `GOAI_DRAWIO_CLI` | 自动探测 | draw.io Desktop CLI 路径（导出用） |
| `S2_API_KEY` | — | 可选 Semantic Scholar key（更高限额） |

## 11. 🧪 测试

```bash
.venv/bin/python -m pytest tests/ -q    # 25 个离线测试 —— 无网络、无 LLM
```

覆盖：BibTeX 解析/生成往返、作者比对（缩写、顺序、遗漏/伪造）、多源去重、
figspec 校验（节点重叠与同义平行线检测）、SVG 与 mxGraph 渲染、**SVG →
figspec → drawio 往返**（分组恢复为容器、边 label 重挂）、retro stub 与方案
骨架、loopctl 账本全周期与并发安全（12 个并行写入者零丢失）、check-done
语义（WARN 放行、minor 移交、产物指纹变更重置闸门、审稿回执）、bib_guard
阻塞行为（未定义 key 与整合率）、tex_guard 组稿闸门、bank_check 支持库校验。

## 12. 📐 设计笔记

**为什么是 MCP server + Markdown skill，而不是一个框架？**
确定性工作（限流检索、元数据比对、XML 渲染）让 LLM 现场发挥又慢又不稳——
所以放进可离线测试的小 MCP server。认知工作（分类法、claim、审稿判断）才是
宿主模型的价值所在——所以放进任何 agent 都能读的纯 Markdown skill。
分界线本身就是设计：*必须每次都对的进 server，必须思考的进 skill。*

**为什么要对抗审稿而不是自审？**
模型审自己的产出会掉进自博弈盲区。这里的审稿人是独立 agent（有 Codex MCP 时
走跨模型），每轮全新上下文，先验证后批评（说引用是假的之前必须先跑
`verify_entry`），产出结构化 issue 而非评语散文。审与做永远分离：
审稿人不改稿，执行者不自判。每个 `review_pass` 都带回执（审稿模型 +
trace 存档）——没人能审计的 PASS 等于没有 PASS。

**为什么是两个模型而不是更多？**
两个是打破自审盲区的最小配置，双方博弈也比多方更容易收敛出稳定的攻防
均衡；再加审稿人，token 成本与协调开销线性涨，边际收益却递减——
最大的收益发生在从 1 到 2，而不是从 2 到 4。

**为什么用账本而不是 agent 之间对话交接？**
口头交接活不过并行支线、重试和会话重启。账本是唯一状态源：闸门、issue、日志
是 agent 之间唯一的协议——每次运行可续跑，每个结论可审计。

## 13. 📖 引用本项目

```bibtex
@software{goai_research,
  title  = {GoAI Research: a multi-agent pipeline for literature surveys with
            verified citations and editable figures},
  author = {liyufeng},
  year   = {2026},
  url    = {https://github.com/asimfish/goai_research}
}
```

## 14. 🤝 License 与贡献

MIT License。欢迎 issue 和 PR —— 加一个 `skills/goai-*/SKILL.md`，接进回环协议
（[docs/LOOP_PROTOCOL.md](docs/LOOP_PROTOCOL.md)），并守住两条铁律：每个 claim
挂可核验的引用 key，每张图交付时带 figspec 源文件。
