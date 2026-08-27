# 架构

## 一图总览

```
                         ┌──────────────────────────────┐
                         │      goai-orchestrator        │
                         │  状态机 + 闸门 + issue 路由    │
                         └──────┬───────────────────────┘
                                │ loopctl 账本 (workspace/state/ledger.json)
        ┌───────────┬───────────┼────────────┬─────────────┬──────────┐
        ▼           ▼           ▼            ▼             ▼          ▼
  goai-lit-search goai-ref-guard goai-survey-writer goai-figure-* goai-idea-forge goai-reviewer
   （检索/滚雪球）  （引用核查）    （taxonomy/写作）   （画图/转可编辑） （提案/实验方案）  （对抗审稿）
        │           │                │             │             │
        ▼           ▼                ▼             ▼             ▼
  goai-litsearch  goai-refcheck   bib_guard     goai-figure   goai-retro     ← MCP servers / 确定性工具
   (MCP)           (MCP)          (本地脚本)      (MCP)         (MCP)
        │           │                              │             │
   arXiv/OpenAlex  Crossref/DBLP              figspec 渲染    stub / HTTP
   S2/Crossref/DBLP + super_ref(深度档)       SVG + .drawio   (ASKCOS/RXN)
```

## 分层设计

| 层 | 内容 | 原则 |
|---|---|---|
| **技能层** `skills/` | 9 个 SKILL.md，宿主 agent（Codex/Claude/Cursor）读入后按规程行动 | 方法论放这层：LLM 推理、判断、写作全由宿主模型完成，skill 不带 API key、不内嵌 LLM SDK |
| **服务层** `server/` | 4 个 FastMCP stdio server | 确定性能力放这层：检索聚合、元数据比对、figspec 渲染、逆合成适配。全部可独立测试 |
| **工具层** `tools/` | loopctl / bib_guard / tex_guard / bank_check / parallel_run.sh | 回环控制与硬闸门：纯本地、零 LLM、可离线跑 |
| **运行层** `workspace/` | library / notes / drafts / figures / ideas / state | 一切产物落盘、可审计；gitignore 不入库 |

## 关键数据结构

### 1. 文献记录（papers.jsonl 每行）
`sources.py` 把 5 个源归一化成统一 record：
`{id, title, authors[], year, venue, doi, arxiv_id, abstract, url, pdf_url, citation_count, source}`
（去重合并后 `source` 变为 `sources[]` 记录多源出处）。
去重键：DOI > arXiv ID > 规范化标题。

### 2. figspec（图的单一事实源）
JSON：`{title, canvas, defaults, groups[], nodes[], edges[], texts[]}`，schema 见
`figure_server.figspec_schema()`。一份 spec 同时渲染：
- `render_svg.py` → 论文用 SVG（LaTeX includesvg）
- `render_drawio.py` → mxGraph XML（draw.io 原生打开，连线绑定 source/target）

改图只改 spec 重渲染，SVG 与 drawio 永不漂移。位图重建（figure-editable
路线 B）也是先重建 spec 再渲染，保证一切图可编辑。

### 3. 回环账本（ledger.json）
```json
{
  "topic": "...", "round": 2, "stage": "writing",
  "effort": "balanced", "strictness": "normal", "auto_proceed": true,
  "gates":  {"review_pass": {"status": "PASS", "detail": "...", "round": 2,
              "at": "...", "receipt": "model=...;trace=...",
              "inputs": [{"path": "...", "sha256": "..."}]}},
  "issues": [{"id":"I3","from":"goai-reviewer","target":"writing",
               "severity":"major","text":"...","status":"open"}],
  "log":    [{"ts":"...","stage":"...","agent":"...","event":"...","detail":"..."}]
}
```
唯一可信状态源。所有 agent 只通过 `tools/loopctl.py` 读写（原子写 + 排它
文件锁，读-改-写全周期互斥）。gate 可选带审稿回执（`receipt`）与产物
指纹（`inputs`）：check-done 会重算指纹，上游产物变更自动把 gate 置回
PENDING——旧审计不得当新审计用。

## 回环机制（详见 LOOP_PROTOCOL.md）

主回环：`scope → (lit_search ∥ style_bank) → ref_gate → taxonomy → (figures ∥ writing ∥ ideas) → review → 返工/放行 → final`。
三处内嵌子回环：
- 检索子回环：搜索→滚雪球→coverage_report，一轮新增去重后 <5 篇才过闸；
- 图纸子回环：渲染→自检→修 figspec，≤3 轮；
- idea 子回环：提案→对抗审→引用二次核查，双关全过才进稿。

## 并行模型

- **节内并行**：writer 的各 section、figure-studio 的各图、ref-guard 的
  分片核查天然无共享写文件，可用 `tools/parallel_run.sh`（codex exec /
  claude -p 后端）同时跑。
- **写冲突规避**：公共文件（main.tex、references.bib、账本）只允许
  orchestrator/汇合步骤写；并行任务各写各的分片文件。

## 为什么 MCP 而不是全 skill

检索限流、BibTeX 比对、SVG/XML 渲染是**确定性重活**：放 skill 里让 LLM
现写现跑既慢又不稳；做成 MCP server 后，宿主一次工具调用拿结果，
可单测、可复用（Codex/Claude/Cursor 三宿主同一份 server）。
反之 taxonomy 构建、claim 写作、审稿判断是**认知活**，留在 skill 层
由宿主模型完成——这就是「该 server 就 server、该 skill 就 skill」的分界线。
