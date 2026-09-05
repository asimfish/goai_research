# 运行手册：怎么跑、怎么接真实 Parquet 语料、怎么看整个流程

> 面向在 5090（`/home/gaojing/goai_research`）或任何一台装好本仓库的机器上**再跑一次流水线**的人。
> 设计与规程见 [`LOOP_PROTOCOL.md`](LOOP_PROTOCOL.md) / [`../AGENTS.md`](../AGENTS.md)；本文只讲操作。
> 2026-09-05 复盘出的坑（MCP 工具延迟加载、子 agent 无 profile、输出灌满上下文）已在脚本里修掉，
> 细节见 [`audits/2026-09-05_live_view_and_prompt_review.md`](audits/2026-09-05_live_view_and_prompt_review.md)。

## 0. 一分钟版

```bash
cd /home/gaojing/goai_research
export CODEX_HOME=$HOME/.codex_rev          # 5090 上已登录的 Codex 目录（~/.codex 未登录）
bash install.sh --retro                     # 首次；已装过可跳过
bash scripts/smoke_test.sh --with-retro     # 无网络无 LLM，末行 SMOKE TEST PASSED
bash tools/check.sh --servers --corpus --retro --tex

# 一行主题 → 综述 PDF + 证据链（公开精简语料；私有全库见 §3）
screen -S goai_run
bash scripts/reproduce_core.sh --topic "Ba5Y12Zn[O(SiO4)]8及其结构相近化合物的合成条件"
# 另开一个终端看各角色在干什么
GOAI_WORKSPACE=$(ls -dt workspace_repro_* | head -1) python3 tools/live_view.py --serve 5051
```

## 1. 环境

| 项 | 5090 现状 | 说明 |
|---|---|---|
| 仓库 | `/home/gaojing/goai_research`（`origin/main`） | 以 gaojing 身份操作（`sudo su - gaojing`） |
| Python | `.venv/`（MCP server、工具）、`.venv-retro/`（torch + pymatgen，前驱体模型） | `install.sh --retro` 生成；所有验证都用 `.venv/bin/python` |
| Codex | `codex-cli 0.153.4`（`~/.nvm/versions/node/v24.19.0/bin/codex`） | **`~/.codex` 未登录，`~/.codex_rev` 已登录（ChatGPT）**，运行前 `export CODEX_HOME=$HOME/.codex_rev`；模型默认 `gpt-5.6-sol` / `xhigh` |
| MCP profile | `$CODEX_HOME/<name>.config.toml`（profile v2，`-p <name>` 叠加到基础配置上） | `reproduce_core.sh` 每次自动生成 `goai_repro_<时间戳>.config.toml`；手工跑参考 `configs/codex.config.toml.example` |
| 语料 | NAS 已挂载（CIFS `//truenas/nas` → `/mnt/nas/data`） | 私有全库路径见 §3 |
| TeX | `tools/check.sh --tex` 通过才允许进 writing | 缺 TeX 时流水线 fail-closed，不会用回退渲染器造假 PDF |

预检一次说清所有依赖：

```bash
bash tools/check.sh --servers --corpus --retro --tex     # 四个 server 可导入 / 语料可读 / 模型 checkpoint 哈希 / TeX 工具链
.venv/bin/python tools/preflight.py --servers            # 机器可读版
.venv/bin/python -m pytest tests/ -q                     # 离线测试；两条 local_corpus 用例需要 PATH 里有 rg
```

## 2. 运行方式

### 2.1 一行主题 → 全流程（正式案例的复现路径）

```bash
export CODEX_HOME=$HOME/.codex_rev
bash scripts/reproduce_core.sh                                   # 正式主题，公开精简语料，新建 workspace_repro_<stamp>/
bash scripts/reproduce_core.sh --topic "LLZO 石榴石固态电解质的烧结致密化"
GOAI_MODEL=gpt-5.6-sol GOAI_REASONING_EFFORT=xhigh bash scripts/reproduce_core.sh   # 默认值，可改
bash scripts/reproduce_core.sh --verify-only --workdir workspace_repro_20260906_010203  # 只跑终验闸门
```

脚本做的事：写 profile（4 个 MCP server + `env_vars` 透传 + 模型固定）→ 预检 → 以 `codex -a never -s danger-full-access -p <profile> --search exec --ephemeral --json`
启动编排器（事件流 `state/orchestrator/orchestrator.jsonl`）→ 账本没到 DONE 就用同一主题续跑（最多 5 次）→
`check-done` + bib/tex/academic_language/pdf 四道闸门 → 写 `state/REPRODUCTION_RECEIPT.json`。
编排器派出的子 agent经 `tools/parallel_run.sh` 启动，自动继承 `-p <profile> --ephemeral`（`RUNNER_ARGS` + `GOAI_CODEX_PROFILE` 双保险）。

建议在 `screen`/`tmux` 里跑（正式案例跑了约 9 小时、40 个子任务）；SSH 断开不影响。
成本参照：正式案例 70.8 M 输入 / 0.57 M 输出 token（95.8% 为缓存重发）。

### 2.2 只跑一批子任务（调试某个角色）

```bash
export CODEX_HOME=$HOME/.codex_rev
# profile：拿 reproduce_core.sh 生成过的任何一份，或按 configs/codex.config.toml.example 另存为 $CODEX_HOME/goai_dev.config.toml
printf '%s\t%s\t%s\n' lit_neighbors \
  '使用 skills/goai-lit-search/SKILL.md，只做「近邻/同型体系」检索面，结果 save_to_library，search_log 写入 workspace/notes/search_log.md' \
  'workspace/notes/search_log.md' > tasks_dev.tsv
GOAI_WORKSPACE=$PWD/workspace GOAI_CODEX_PROFILE=goai_dev RUNNER_TIMEOUT=1800 \
  bash tools/parallel_run.sh --backend codex --jobs 2 tasks_dev.tsv
```

TSV 四列：任务名 / 提示词 / 本轮必须更新的非空产物（逗号分隔，`=路径` 只查存在）/ 前序任务名。
runner 会在每个提示词末尾附运行协议（MCP 工具延迟加载先 `tool_search`、禁读活动日志、20 KB 输出上限、时间预算、产物增量落盘），
产物落在 `$GOAI_WORKSPACE/state/parallel/<run_id>/`：`<task>.jsonl`（事件流）、`.final.md`、`.status`、`.exit`、`.prompt.txt`、`.meta.json`，批次级 `RUN_INFO.json`。

### 2.3 不用 LLM 的验证

```bash
bash scripts/smoke_test.sh --with-retro              # 安装 + 服务导入 + 离线测试 + 前驱体 dry run
.venv-retro/bin/python tools/retro_dry_run.py Li7La3Zr2O12 --device cpu
.venv/bin/python tools/bib_guard.py workspace/drafts/sections workspace/library/references.bib
.venv/bin/python tools/tex_guard.py workspace/drafts
.venv/bin/python tools/pdf_guard.py workspace/drafts/main.pdf --tex workspace/drafts/main.tex --bib workspace/library/references.bib
```

## 3. 连接真实 Parquet 语料

同一套 `goai-litsearch` 工具（`local_corpus_status` / `grep_local_corpus` / `read_local_document` / `lookup_local_doi`）
靠三个环境变量在「公开精简包」和「私有全库」之间切换，代码与输出 schema 不变：

| 变量 | 公开精简包（默认，随仓库提交） | 私有全库（5090 NAS） |
|---|---|---|
| `GOAI_LOCAL_CORPUS_ROOTS` | `submission/02_研究数据与证据包/corpus_release`（21 篇被引全文，`goai-compact-parquet-v1`） | `/mnt/nas/data/gaojing/markdown_corpus_v1/packages/markdown-v1-final`（336 GB，按 `publisher_group=*` 分区，15 个 parquet） |
| `GOAI_LOCAL_CORPUS_EXPECTED_INDEX` | 不设 | `/home/gaojing/讨论/08-05_材料文献智能提取系统/任务/01_文献识别/data/index/markdown_expected.sqlite`（4.7 GB，DOI → UUID） |
| `GOAI_LOCAL_CORPUS_SHARD_ROOT` | 不设 | `/mnt/nas/data/gaojing/markdown_corpus_v1/ingest/markdown-v1/shards`（2702 个分片，`lookup_local_doi` 直接取正文） |
| `GOAI_LOCAL_CORPUS_TIMEOUT` | 30 | NAS 慢时可放到 60–90（正式运行首批 `grep_local_corpus` 就是 33 s 超时返回空） |

```bash
# 3.1 先验证语料可读（mode 应为 private-full-corpus，ok=true）
export GOAI_LOCAL_CORPUS_ROOTS=/mnt/nas/data/gaojing/markdown_corpus_v1/packages/markdown-v1-final
export GOAI_LOCAL_CORPUS_EXPECTED_INDEX="/home/gaojing/讨论/08-05_材料文献智能提取系统/任务/01_文献识别/data/index/markdown_expected.sqlite"
export GOAI_LOCAL_CORPUS_SHARD_ROOT=/mnt/nas/data/gaojing/markdown_corpus_v1/ingest/markdown-v1/shards
bash tools/check.sh --corpus
.venv/bin/python -c 'from server.core import local_corpus; import json; print(json.dumps(local_corpus.corpus_status(), ensure_ascii=False)[:600])'

# 3.2 全流程用私有全库：加 GOAI_CORPUS=private，三个变量会原样写进 profile 的 env
GOAI_CORPUS=private CODEX_HOME=$HOME/.codex_rev bash scripts/reproduce_core.sh --topic "..."

# 3.3 单批子任务用私有全库：把三个变量写进 profile 的 [mcp_servers.goai-litsearch].env（见 configs/codex.config.toml.example 注释）
```

注意：① MCP server 进程**不继承** shell 的环境变量，语料路径必须写在 profile 的 `env = {...}` 里
（`reproduce_core.sh` 已处理；只有 `GOAI_RUN_ID`/`GOAI_TASK_NAME` 通过 `env_vars` 透传）；
② `lookup_local_doi` 只在配了 `EXPECTED_INDEX` + `SHARD_ROOT` 时走私有索引，精简包直接查自身 parquet；
③ 私有路径不进提交物：`tools/export_submission_bundle.py --sanitize-only` 会把它们脱敏为 `<PRIVATE_MOUNT_PATH>`；
④ 公开包里 `corpus_manifest.json` 标 `citable=true` 才能进引用池，`synthetic=true` 的演示包只能做接口测试。

## 4. 可视化整个流程

### 4.1 运行中：`tools/live_view.py`（只读，纯标准库）

```bash
WS=$(ls -dt workspace_repro_* | head -1)       # 或 workspace / 任何 GOAI_WORKSPACE
GOAI_WORKSPACE=$WS python3 tools/live_view.py                 # 快照：每个角色的状态/耗时/token/cmd/mcp/审计 + 账本闸门
GOAI_WORKSPACE=$WS python3 tools/live_view.py --follow        # 终端实时流（按角色着色），Ctrl-C 打印汇总
GOAI_WORKSPACE=$WS python3 tools/live_view.py --serve 5051    # 浏览器看板
```

看板顶部是**流程条**：账本的 11 个阶段按顺序排开（`lit_search ∥ style_bank`、`figures ∥ writing ∥ ideas` 标为并行段），
每格显示对应闸门状态（PASS/WARN/FAIL/PENDING 色条）、当前阶段（◀）和该阶段正在跑的角色数；下面是**批次时间线**
（每个子任务一根按状态着色的时间条）、按角色分组的任务卡（消息 / 命令+exit / MCP 调用 / 文件改动 / todo / token，点开看完整事件流、
提示词、最终回复、stderr）、左栏账本闸门与 open issue、MCP 审计（按 `run_id=<批次>/<任务>` 归因）、底部全局事件流。

远程看：`ssh -L 5051:127.0.0.1:5051 -p 4009 ubuntu@nas.zgca.com` 后开 http://127.0.0.1:5051 。

### 4.2 事后：回放与统计

```bash
GOAI_WORKSPACE=$WS python3 tools/live_view.py --all --serve 5051      # 回放整场（所有批次），可用批次下拉切换
GOAI_WORKSPACE=$WS python3 tools/live_view.py --run-id 20260901_003133_1289042   # 只看一批
.venv/bin/python tools/analyze_agent_traces.py --help                 # 轨迹统计：命令数 / web_search / token / MCP 调用
.venv/bin/python tools/loopctl.py status                              # 账本全景（阶段 / 闸门 / open issue）
```

正式案例的轨迹已随提交包归档在 `submission/03_运行与评测包/正式案例_BYZSO冷启动/traces/runtime/`，把 `parallel/` 复制到
任意 `<ws>/state/parallel/`、`ledger.json`/`tool_calls.jsonl` 放到 `<ws>/state/` 即可用 `--all` 回放（回放时耗时以文件 mtime 近似）。

### 4.3 静态流程图

阶段状态机与路由表在 [`LOOP_PROTOCOL.md`](LOOP_PROTOCOL.md)；三层架构在 [`ARCHITECTURE.md`](ARCHITECTURE.md)；
方案说明 PPT 第 4–6 页（`submission/方案说明PPT/source/svg_output/`）有带动画的 agent 交互与数据流图。

## 5. 常见问题

| 现象 | 原因 | 处置 |
|---|---|---|
| 子 agent 说「工具清单里没有 goai-*」然后 shell 直调 server 模块 | Codex 把 MCP 工具延迟加载，必须先 `tool_search` | runner 已在提示词末尾说明；AGENTS.md 铁律 16；若 `RUN_INFO.json` 有 `mcp_warning`，说明派活时没传 profile |
| `codex login status` 显示 Not logged in | 用了 `~/.codex` | `export CODEX_HOME=$HOME/.codex_rev` |
| `error: unexpected argument '-a' found` | `-a/--ask-for-approval` 是根级参数，不能放在 `exec` 之后 | 用 `codex -a never ... exec ...`（脚本已如此） |
| 直调工具时网络 `Operation not permitted` | `workspace-write` 沙箱禁网；MCP server 进程不受限 | 走 MCP；确需直调时 `RUNNER_SANDBOX=danger-full-access` |
| `grep_local_corpus` 超时返回空 | NAS 首次扫描慢 | 调大 `GOAI_LOCAL_CORPUS_TIMEOUT`；优先 `lookup_local_doi` 精确取正文 |
| 离线测试两条 `local_corpus` 失败 | PATH 无 ripgrep | `apt install ripgrep` 或忽略（Parquet 路径用 DuckDB，不需要 rg） |
| 子任务 `FAIL_TIMEOUT` | 单会话命令过多 / 输出过大 | 看 live_view 卡片里 `$` 数与 `↳` 输出体量；拆任务、遵守 20 KB 上限 |
