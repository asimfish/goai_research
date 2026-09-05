# 2026-09-05 运行可观测性与 Prompt / 工具面复审

> 范围：如何实时看到各角色（子 agent）的输出；正式运行轨迹复盘；skills / AGENTS.md /
> MCP 工具描述与返回格式、最终交付格式还有哪些可优化。证据全部来自
> `submission/03_运行与评测包/正式案例_BYZSO冷启动/` 的 40 个子任务事件流、账本与审计，
> 以及本次在 5090 上用 codex 0.153.4 做的两组实测。

## 0. 结论速览

| 结论 | 证据 | 处置 |
|---|---|---|
| 正式运行的子 agent **一次也没用 MCP**：40 个任务 0 次 `mcp_tool_call`，105 次 shell 直调 `from server.xxx_server import …`。原因不是配置——启动命令 `export RUNNER_ARGS='-p cold_full_byzso_m2gfJJ --ephemeral'` 已把 profile 传给子 agent——而是 **Codex 把 MCP 工具延迟加载**（`tool_search_always_defer_mcp_tools` 已固化为默认），子 agent 开场清单里看不到 goai-*，没有去 `tool_search` 就判定「未暴露」 | 子 agent 自述：`lit_identity_structure`「当前工具清单没有直接暴露检索函数」、`fig01_phase_c_retry`「当前会话没有暴露 goai-figure MCP 调用…走 server/figure_server.py 降级」；用原始 profile 在 codex 0.153.4 复现：工具清单只有 `tool_search.tool_search_tool`，「No MCP server tools are currently exposed directly」；而两次探针里 gpt-5.4-mini 先 tool_search 再调用，全部成功 | ✅ runner 在每个子任务提示词末尾附「MCP 工具延迟加载，先 tool_search」；AGENTS.md 铁律 16、五个 skill 的工具面同句；另保留 `GOAI_CODEX_PROFILE`→`-p` 透传与缺 profile 告警作为第二道防线 |
| MCP 服务端审计 **134 条全部无法归因**（`run_id: null`），且只覆盖 4/25 个工具 | `audit.record_tool_call` 读 `GOAI_RUN_ID`，runner 从未设置；codex 默认不向 MCP server 透传父进程 env（实测只带 9 个变量） | ✅ runner 导出 `GOAI_RUN_ID=<批次>/<任务>`；profile 加 `env_vars = ["GOAI_RUN_ID","GOAI_TASK_NAME"]`（实测透传成功）；`mcp_compat.FastMCP.tool()` 统一审计全部工具 |
| **40% 子任务撞超时墙**（16/40：FAIL_TIMEOUT 10、WARN_ARTIFACT_PASS_AFTER_TIMEOUT 6） | `.status` 统计；超时任务多为 40–60 条命令的长会话 | ✅ 投递协议附时间预算与 20 KB 输出上限；⏳ 建议在任务书模板固化「预算/步数」 |
| 输入 token 70.8 M 中 **95.8% 是缓存重发**；61 条命令输出 >20 KB，最大 950 KB（`rg`）与 933 KB（内嵌 `codex exec` 审稿） | 事件流 `turn.completed.usage` 汇总、`command_execution.aggregated_output` 长度 | ✅ AGENTS.md 铁律 16 + reviewer skill 要求内嵌 codex `-o` 落盘；⏳ 建议 `loopctl brief` 减少大文件重读（references.bib 被读 137 次、papers.jsonl 81 次） |
| 没有任何「看各角色在干什么」的工具，只能 `tail` 单个 jsonl | — | ✅ 新增 `tools/live_view.py`（快照 / `--follow` 终端流 / `--serve` 浏览器看板） |

## 1. 实时查看工具 `tools/live_view.py`

只读、纯标准库（Python ≥3.10），数据源即 runner 的落盘约定：

```
<ws>/state/parallel/<run_id>/<task>.jsonl        Codex `exec --json` 事件流（每个角色一个）
<ws>/state/parallel/<run_id>/<task>.{status,exit,process_exit,final.md,stderr.log,validation.log,prompt.txt,meta.json}
<ws>/state/parallel/<run_id>/RUN_INFO.json      批次：backend / jobs / profile / model / sandbox / timeout / mcp_warning
<ws>/state/orchestrator/*.jsonl                 编排器事件流（reproduce_core.sh 的 tee）
<ws>/state/ledger.json                          阶段 / 闸门 / issue / 日志
<ws>/state/tool_calls.jsonl                     MCP 服务端审计（run_id 归因到任务）
```

三种形态（`GOAI_WORKSPACE` 或 `--workspace` 指工作区）：

```bash
python3 tools/live_view.py                 # 快照表：角色 | 任务 | 状态 | 耗时 | in/out token | cmd | mcp/审计 | web | file | 最近输出 + 账本闸门 + 审计汇总
python3 tools/live_view.py --follow        # 实时流：HH:MM:SS <角色图标> <任务> 💬消息 / $命令→exit / 🔧MCP调用 / ✎文件 / ☑todo / Σtoken / ✅PASS，账本与审计变化穿插；Ctrl-C 打印汇总
python3 tools/live_view.py --serve 5051    # 浏览器看板：按角色分组的卡片（点开看完整事件流、提示词、最终回复、stderr）+ 账本/闸门/issue + 审计 + 全局事件流
python3 tools/live_view.py --all           # 回放历史全部批次；--run-id <id> 只看一批
```

角色识别顺序：`.meta.json.skill`（runner 从提示词抓 `goai-*`）→ 提示词/消息里出现的 skill 名 → 任务名前缀兜底
（正式运行 40 个任务名全部可归类）。默认只显示「活动集合」（仍在跑的批次 + 最近一批 + 编排器）。

验证：① 用正式案例 29 批 47 条轨迹回放（`--all`），状态/耗时/token/验收失败原因全部还原；
② 用逐行回放脚本模拟正在写入的运行，`--follow` 增量 tail 正常；③ 真实 codex（gpt-5.4-mini）两路并行子任务
（`goai-litsearch` ×3 次、`goai-retro` ×2 次 MCP 调用）全程可见，审计 2 条全部归因到 `run_id=<批次>/<任务>`。

> 远程机器上看看板：`ssh -L 5051:127.0.0.1:5051 <host>` 后开 http://127.0.0.1:5051 。

## 2. 正式运行复盘（40 个子任务，2026-08-31 → 09-02）

- 状态：PASS 23 / WARN 6 / FAIL 10 / 未落盘 1。FAIL 全部是 `FAIL_TIMEOUT`（1800 s ×7、900 s ×4、1200 s ×2）或产物验收失败（figure_merge：产物「本轮未更新」）；BLOCKED_DEPENDENCY 3 个（style_bank 超时连带 lit_merge_coverage 两次未启动、figure_merge 失败连带 blueprint 未启动）。
- token：仅 24 个跑到 `turn.completed` 的任务就用了 70.8 M 输入（其中 67.9 M 缓存）/ 0.57 M 输出；最大单任务 `writing_repair` 11.5 M 输入、66 条命令。成本结构说明：**贵的不是规程文本，而是长会话每轮把巨大的命令输出反复带着**。
- 工具面：`mcp_tool_call` 0 次；`from server.` 直调 105 次；`references.bib` 被读 137 次、`papers.jsonl` 81 次、`SKILL.md` 47 次、`loopctl status/log` 67/69 次。
  启动命令（原对话 08-31 19:29）：`export RUNNER_ARGS='-p cold_full_byzso_m2gfJJ --ephemeral'` + `codex exec --ephemeral -p cold_full_byzso_m2gfJJ -s danger-full-access …`，
  profile 含 4 个 goai server 且冷启动目录的 `.venv`/`.venv-retro` 齐全——MCP 配置本身是启用的；子 agent 不用 MCP 的直接原因是 Codex 的延迟加载：
  goai 工具不在开场清单，需先 `tool_search`。`style_bank` 的自述「本地 MCP 组件通过预检，但执行环境禁止其直接联网…Operation not permitted」
  也印证它是在 `workspace-write` 沙箱的 shell 里直调 server 模块（MCP server 进程本身不受沙箱限制，走 MCP 就不会断网）。
- 铁律 8（单条输出 ≤20 KB）被违反 61 次；最大的两条来自 `rg` 全库检索（950 KB）与内嵌 `codex exec` 审稿把整段 stdout 打回上下文（933 KB）；tectonic 编译日志 120–300 KB 出现 5 次。
- 审计：`tool_calls.jsonl` 134 条（lookup_local_doi 111 / grep_local_corpus 19 / predict_precursor_routes 4），`run_id` 全为 null；`search_papers`（web 检索 205 次）、`verify_*`、`render_figure` 等 21 个工具没有任何服务端审计。

## 3. 本次已落地的改动

| 文件 | 改动 |
|---|---|
| `tools/live_view.py` `tools/live_view_ui.html` | 新增实时查看工具（§1） |
| `tools/parallel_run.sh` | 每个子任务提示词末尾附运行协议：**goai MCP 工具延迟加载、先 tool_search**、禁读活动日志、20 KB 输出上限、时间预算、声明产物增量落盘；`GOAI_CODEX_PROFILE`→`-p` 自动透传 + 缺 MCP 告警；`RUN_INFO.json`；`<task>.prompt.txt` / `.meta.json`；子进程导出 `GOAI_RUN_ID`/`GOAI_TASK_NAME`；启动/收尾打印 live_view 用法。21 项 live 调度测试全过 |
| `scripts/reproduce_core.sh` | 四个 server 加 `env_vars = ["GOAI_RUN_ID","GOAI_TASK_NAME"]`；`export GOAI_CODEX_PROFILE`；打印 live_view 用法 |
| `configs/codex.config.toml.example` | 同上 `env_vars` + profile 用法说明 |
| `server/core/mcp_compat.py` | `FastMCP.tool()` 统一审计（跳过核心层已记的 4 个），请求截断 2000 字、响应只存摘要；MCP 协议路径与直调路径都留痕 |
| `server/core/jsonout.py` + 4 个 server | `GOAI_MCP_COMPACT_JSON=1` 时紧凑 JSON（省 20–30% 输出 token），默认不变 |
| `server/litsearch_server.py` | `grep_local_corpus` 默认 `max_results` 20→10（对齐铁律 9）；`search_papers` / `snowball` 加 `compact` 参数（体量约 1/4）；`coverage_report` 加 `min_hits` 参数并返回 `recent_3y_share`；`lookup` / `local_corpus_status` / `read_local_document` / `lookup_local_doi` 补 Args/Returns |
| `server/figure_server.py` `server/retro_server.py` | `drawio_export` / `provider_status` / `inorganic_model_status` 补 Args/Returns 与「结果怎么用」 |
| `AGENTS.md` | 铁律 16（MCP 优先、直调兜底须留痕、输出 ≤20 KB 的具体做法）；环境速查加派活 profile 与 live_view |
| `skills/goai-orchestrator/SKILL.md` | 终端派活命令带 `GOAI_CODEX_PROFILE`，看进度用 live_view 而不是读活动 jsonl |
| `skills/goai-lit-search|ref-guard|figure-studio|idea-forge|style-bank` | 工具面各加一句「Codex 延迟加载 MCP 工具，先 tool_search 再调用；搜不到才降级直调并记账」 |
| `skills/goai-reviewer/SKILL.md` | 跨模型审稿用 `codex exec -o <trace>` 直接落盘，禁止整段 stdout 回灌 |
| `docs/LOOP_PROTOCOL.md` `README.md` | 并行协议规约 9–11（MCP 透传 / 归因 / 提示词落盘）；一键命令加 live_view |

验证：离线测试 71 通过 / 1 跳过（另 2 个 `local_corpus` 测试在改动前后同样失败，原因是该 shell PATH 无 ripgrep，与本次无关）；
`tools/preflight.py --servers` 通过；MCP 客户端 `list_tools` 核对 `search_papers` 参数与描述完整；两组真实 codex 实测见 §1。

## 4. Prompt（skills / AGENTS.md / 任务书）优化建议

按「收益 / 风险」排序，✅ 已做、⏳ 建议。

1. ⏳ **任务书模板化（最大收益）**。正式运行 28 份 TSV 的提示词由编排器临场手写，长度 300–900 字、结构不一。建议
   `docs/TASK_CARD_TEMPLATE.md`：`角色 skill 路径 | 本切片 | 只读输入 | 声明产物（第三列） | 验收判据 | 禁止事项 |
   时间/步数预算 | 收工动作（loopctl log）`，编排器按模板填空。可读性与可审计性都提升，也便于 live_view 展示。
2. ✅/⏳ **把预算写进提示词**。runner 现已附「wall-clock budget + 用到一半先落盘」；建议 skills 通用段再加
   「步数预算：一个子任务 ≤25 条命令，超出先写产物再继续」——超时任务的命令数（40–60）是成功任务（13–30）的两倍。
3. ✅ **输出有界的具体做法**而不是只写原则：铁律 16 与投递协议已给出「重定向到文件再 tail」；建议 `tools/check.sh`
   增加 `--bounded <cmd>` 包装（`head -c 20000` + 落盘全量日志）供 skills 直接引用。
4. ⏳ **skill 顶部加 10 行「本阶段清单」**。survey-writer 307 行、figure-studio 237 行，子 agent 每次通读
   （SKILL.md 被读 47 次）；把「做什么 / 产物 / 闸门 / 禁止 / 收工」压成开头一屏，细则作为附录。不改语义，只改结构。
5. ⏳ **`loopctl brief --for <stage>`**：输出该阶段需要的摘要（库规模、近三年占比、可用 key 列表、open issue、
   上游 gate detail），替代各角色反复 `cat`/`rg` 大文件（references.bib 137 次、papers.jsonl 81 次）。
6. ⏳ **对抗审稿的独立通道要机器可验**：正式运行 `review_round1` 在子 agent 内再起 `codex exec --ephemeral --sandbox
   read-only` 调 gpt-5.6-terra，符合 skill 的跨模型要求，但「用了哪个模型」只存在于 agent 的自述与回执文本里。
   建议 `loopctl gate review_pass` 校验 `--receipt` 的 `model=` 与执行者模型（RUN_INFO.json / profile）不同，
   否则自动降为 provisional；内嵌 codex 的事件流用 `--json > trace.jsonl` 落盘作为凭证（其中 `turn.completed`
   可证明确有独立会话），而不是把 stdout 回灌上下文。
7. ⏳ **TASK_PROMPT.md 与 skills 的数字对齐**：任务书说「5±1 个子主题」，orchestrator skill 说 balanced 6–12；
   任务书 comprehensive「库 ≥100」，而正式案例最终 63 篇记 WARN——建议任务书直接引用 skill 的档位表，不再各写一份。

## 5. MCP 工具描述与返回格式

1. ✅ **审计覆盖全部工具**（原 4/25），且能按任务归因。竞赛口径「工具输入/中间输出可追溯」现在对 MCP 协议路径与直调路径同时成立。
2. ✅ **`coverage_report` 的 verdict 与 skill 配额不一致**：工具硬编码「<5 为缺口」，skill 要求 comprehensive 每子主题 ≥15、
   近三年 ≥30%。现加 `min_hits` 参数、返回 `recent_3y_share`，描述明说「verdict 只判 min_hits 缺口，档位配额自查」。
3. ✅ **默认值对齐铁律**：`grep_local_corpus` 默认 20 → 10。
4. ✅ **检索返回体量**：`search_papers` 一次 3 源 ×15 条 ≈ 60–70 KB；新增 `compact=true`（识别/入库字段 + 240 字摘要，约 1/4）。
   建议 lit-search skill 的「关键词矩阵」步骤默认 `compact=true`，只对候选记录 `lookup`。
5. ✅ **描述模板**：补齐 7 个原本一句话/无 Args 的工具（`lookup`、`local_corpus_status`、`read_local_document`、`lookup_local_doi`、
   `drawio_export`、`provider_status`、`inorganic_model_status`），统一为「用途 → Args → Returns（判定字段怎么读）→ 失败语义」。
   ⏳ 其余工具（`verify_entry` 等）已有 Args/Returns，建议逐个补「失败/空结果时下一步做什么」一句。
6. ✅ **JSON 缩进**：所有工具 `indent=2` 返回，`GOAI_MCP_COMPACT_JSON=1` 可切紧凑；⏳ 建议在 reproduce_core.sh 的 profile
   `env` 中默认打开（本次未改默认，避免影响对照实验）。
7. ⏳ **`save_to_library` 返回 `added` 但不返回新增了哪些**：lit-search 的边际收敛判据需要「本轮新增去重后 <10 篇」，
   建议返回 `added_ids` 前 20 条，省一次重读 papers.jsonl。
8. ⏳ **`verify_bib_file` 一次核验全库**（52–63 条外网请求，正式运行多次撞超时）：建议加 `keys`/`only_unverified`
   增量参数，返工轮只复核上次非 PASS 的条目。

## 6. 最终交付格式复审（正式案例 23 页中文综述）

- 结构：11 节（引言 / 检索方法 / 目标相 / 相关程度 / 条件比较（6 表）/ 近邻路线 / 既有结论 / 表征 / 常见问题 / 方向 / 结论），
  与 writer skill 的「骨架强制项」一一对应，`pdf_guard` 五项通过（Producer xdvipdfmx）。
- 仍可改：① `\title` 与 PDF 元数据标题保留「证据分级、路线矩阵与迁移边界」——上一轮已指出是流程口吻，
  但 `academic_language_guard` 只扫正文/表/图注，未扫 `\title`，建议把标题与 `\hypersetup{pdftitle}` 纳入扫描；
  ② 引用密度极不均衡：`03_condition_matrix` 34 次 `\cite`，引言 5、结论 2、`08_future_directions` 2——
  建议 `bib_guard` 增加「按节最低引用密度」告警；③ `sections/` 编号有两个 `00_`、两个 `04_`，顺序只由 `main.tex`
  决定，建议 blueprint 阶段固化编号并让 `tex_guard` 检查文件名与 `\input` 顺序一致。
- 事件流格式：Codex `exec --json` **不带时间戳、不带模型名**（`--ephemeral` 下原生 rollout 也不落盘），live_view 只能用
  观测时间近似。建议 runner 在 `.meta.json` 里记 `model/effort`（已记 backend/profile），并在需要精确时间线时去掉
  `--ephemeral`、把 `CODEX_HOME/sessions` 一并归档。

## 7. 未做 / 需要人决定

- skills 的结构性重写（§4 第 1、4 条）与 `loopctl brief`（第 5 条）涉及 9 个 skill 与账本接口，建议在下一轮实跑前统一改。
- `GOAI_MCP_COMPACT_JSON` 与 `search_papers(compact=true)` 是否作为默认——会改变与 08-31 正式运行的可比性。
- 5090 上 `~/.codex_rev` 才是已登录的 CODEX_HOME（`~/.codex` 未登录），reproduce_core.sh 若在该机重跑需
  `CODEX_HOME=$HOME/.codex_rev`。
