# D. 逆合成 + 回环控制环节 实测报告

- 日期：2026-08-27（第一轮建链 + **第二轮独立复测与深挖**，见 §2.12 起）
- 范围：`server/core/retro.py`、`server/retro_server.py`、`tools/loopctl.py`、`tools/parallel_run.sh`
- 环境：macOS darwin 25.2.0 / arm64；Python `.venv/bin/python` 3.11.14；mcp SDK **2.1.1**；httpx 0.28.1；
  `/usr/bin/env bash` = **GNU bash 3.2.57**（macOS 自带）；codex-cli 0.149.1；claude 2.1.220
- 实测 workspace：`workspace_live/loop/`（`harness/` 探针脚本、`evidence/` 原始证据）
- 回归测试：`tests/live/test_live_loop.py`（**47 项**，`pytest -m live`）
- 结论：**46 PASS / 0 FAIL / 1 SKIP（真实 claude 未登录，如实跳过）；25/25 离线回归仍全过**。
  两轮共发现 **17 个真实缺陷**，修复 **15 个**，2 个列为遗留建议。
  第二轮新增 6 个缺陷（全部修复），其中 3 个是**汇总假绿**类：任务真实失败却被报成整批成功。

> 所有 http 测试打的是真实 socket 上的 mock ASKCOS 后端（真实 httpx 请求）；
> parallel_run.sh 的调度用「假 codex 二进制注入 PATH」测，真实后端（codex / claude）另有单独项。

### 第二轮（复测）摘要

| 新发现 | 严重度 | 现象 | 状态 |
|---|---|---|---|
| 末行无换行符 → 静默丢最后一个任务 | P0 | 3 任务只跑 2 个，汇总报 2 PASS、rc=0 | 已修 |
| 重名任务 → 失败被吞成假绿 | P0 | 真实 exit 9 的任务消失，整批 rc=0 | 已修 |
| 任务名含 `/` → 退出码丢失、任务消失 | P0 | 任务真实 exit 1，汇总只剩另一个 PASS、rc=0 | 已修 |
| 后端 steps 结构错位 → MCP 层抛裸异常 | P1 | 调用方只看到 `Error executing tool` | 已修 |
| loopctl 未 init / 账本损坏 → 12–24 行 traceback | P2 | 7 个子命令全部裸 traceback | 已修 |
| 无单任务超时 → 后端卡死拖挂整批 | P0 | 真实 codex 断网无限重连，实测挂 **8 分钟**不退出 | 已修（上一轮遗留项 #1） |

---

## 1. 实测项清单

### 1.1 retro server —— MCP stdio 协议层

| # | 实测项 | 结果 | 证据 |
|---|---|---|---|
| 1 | mcp SDK stdio client 拉起 `server/retro_server.py`，握手成功 | PASS | serverInfo.name=`goai-retro`；`harness/mcp_stdio_probe.py` |
| 2 | 工具清单完整 | PASS | `["make_experiment_plan","predict_retro","provider_status"]` |
| 3 | stub 全链路 provider_status → predict_retro → make_experiment_plan | PASS | 11/11 检查项；2 步路线 → 2 步方案，4 条 review_gates |
| 4 | stub 结果不冒充可信 | PASS | `status.trusted=false`、`route.verified=false`、`plan.provider_verified=false` |
| 5 | http provider 经协议层打真实后端 | PASS | 12/12 检查项；`route.engine="mock-askcos/1.0"`，`plan.provider_verified=true`；`harness/mcp_http_probe.py` |
| 6 | 后端 500 时协议层不抛裸异常 | PASS（修复后） | `route.ok=false` + error 含 500；`plan.provider_verified=false`、`steps=[]` |

附带发现（非缺陷，供客户端注意）：mcp SDK 2.1.1 的 `InitializeResult` 字段已改为 snake_case
（`server_info` / `protocol_version`），1.x 的 `serverInfo` 会 `AttributeError`。
server 端有 `server/core/mcp_compat.py` 兜住，客户端/测试代码需自行兼容。

### 1.2 retro server —— http provider 真实路径（离线测试完全未覆盖）

mock 后端按 `server/core/retro.py` 的约定实现：`POST {target_smiles, max_depth}` → ASKCOS 风格 JSON 路线。

| # | 实测项 | 结果 | 证据 |
|---|---|---|---|
| 7 | 真实 HTTP 往返、响应解析 | PASS | `route_id=mock-askcos-1`、`engine=mock-askcos/1.0`、steps 结构完整 |
| 8 | `max_depth` 透传并被后端遵守 | PASS | `max_depth=3` → 3 步；`max_depth=2` → 2 步 |
| 9 | 请求体符合文档约定 | PASS | `{"target_smiles":"CC(=O)Oc1ccccc1C(=O)O","max_depth":2}` |
| 10 | **API key 透传** | PASS | 8/8 请求带 `Authorization: Bearer live-test-key-abc123`；`evidence/mock_requests.jsonl` |
| 11 | 未设 key 时不发 Authorization 头 | PASS | mock 记录 `authorization: null`，后端 401 被结构化返回 |
| 12 | `Content-Type: application/json` | PASS | mock 记录全部为 `application/json` |
| 13 | 后端 `verified=true` 透传到实验方案 | PASS | `plan.provider_verified=true` |

第二轮补测（`harness/probe_retro.py`、`harness/measure_retro_http.py`）：

| # | 实测项 | 结果 | 证据 |
|---|---|---|---|
| 13a | 后端返回「JSON 合法但结构不合约定」共 6 形态 | PASS（修复后） | 6/6 收敛为可读方案，无一抛异常，无一自称 verified；见 §2.12 |
| 13b | `steps` 为 `{"1":..,"2":..}` 对象形态 | PASS（修复后） | 按 key 排序摊平为 first/second，并在 `route_problems` 如实记录 |
| 13c | MCP 协议层不再回不透明 `Error executing tool` | PASS（修复后） | 返回完整方案 JSON + `route_problems`；`harness/probe_mcp_crash.py` |
| 13d | 空路线（0 步）不得标记已验证 | PASS（修复后） | `steps=[]` → `provider_verified=false` |

### 1.3 loopctl 高并发

| # | 实测项 | 结果 | 证据 |
|---|---|---|---|
| 14 | 50 进程混合 log/gate/issue add 并发 | PASS | **0.25s**（二轮复测，一轮 0.26s）；17 log + 17 gate + 16 issue，**零丢失** |
| 15 | 加压 150 进程 | PASS | **0.81s**；50/50/50 全中，零丢失 |
| 16 | 账本 JSON 始终合法（并发抽查） | PASS | 50 进程时抽查 52 次、150 进程时 142 次，**非法 0 次**（`save()` 的 `os.replace` 原子替换有效） |
| 17 | issue id 无重号、无空洞 | PASS | `I1..I16` 唯一且连续，`next_issue_id=17`（150 进程时 `I1..I50`，=51） |
| 18 | 无死锁（总超时 90s 兜底） | PASS | 全部进程 rc=0，0 次超时 |
| 19 | 锁竞争性能 | PASS | 50 并发 0.26s ≪ 30s 预算 |
| 20 | 持锁进程 `kill -9` 后锁不残留 | PASS | 持锁期间 loopctl 确认被阻塞（3s 观测）；kill -9 后 **0.031s** 恢复（`evidence/r2_kill9.json`） |
| 21 | 被阻塞的写入未污染账本 | PASS | 账本含 `AFTER-KILL-9`，不含 `SHOULD-BLOCK`；恢复后连续 5 次操作全成功 |
| 21a | 未 init / 账本损坏时的报错可读性 | **FAIL→PASS** | 二轮发现 7 个子命令全吐 12 行 traceback，见 §2.16 |

**并发正确性的直接证据**：16 个 issue add 并发做的是 `next_issue_id` 的读-改-写，
实测拿到 `I1..I16` 唯一且连续（`next_issue_id=17`）——这只有互斥真实生效才可能成立。
哨兵线程在压测全程读账本 59 次，**撕裂读 0 次**（`save()` 的 `os.replace` 原子替换有效）。

loopctl 的并发内核（flock 全命令周期持锁 + 临时文件原子替换）在真机高并发下完全站得住；
二轮唯一发现的问题在**报错可读性**，不涉及并发正确性。

### 1.4 parallel_run.sh 调度（假后端注入）

| # | 实测项 | 修复前 | 修复后 |
|---|---|---|---|
| 22 | `--jobs 2` 并发上限 | **FAIL** 峰值并发 **5** | **PASS** 峰值 **2** |
| 23 | 全部任务被执行 | PASS 5/5 | PASS 5/5 |
| 24 | 每任务 `.log` + `.exit` 落盘 | PASS 5+5 | PASS 5+5 |
| 25 | 失败任务退出码如实记录 | PASS `t3=3, t5=7` | PASS 同 |
| 26 | 汇总统计正确 | PASS 3 PASS / 2 FAIL，整批 rc=1 | PASS 同 |
| 27 | 子进程 stdin 与 tasks 文件隔离 | **FAIL** 见 §2.6 | **PASS** stdin=0 字节，5/5 执行 |

并发时间线（`evidence/trace_jobs2.log` → `trace_jobs2_fixed.log`）：

```
修复前 --jobs 2：+0.00s 五个任务同时 START，concurrent=5   ← 上限被静默忽略
修复后 --jobs 2：+0.00s t1,t2 (=2) → +2.52s t3 → +2.73s t4 → +4.40s t5，峰值=2
```

第二轮独立复测（5 任务 `--jobs 2`，`FAKE_CODEX_SLEEP=0.8`）：
**启动任务数=5，并发峰值=2，整批 2.98s，rc=1**（t3=3 / t5=7 如实记账），与一轮结论一致。

| # | 实测项（二轮新增） | 修复前 | 修复后 |
|---|---|---|---|
| 27a | tasks.tsv 末行无换行符 | **FAIL** 3 任务只跑 2 个，汇总 rc=0 | **PASS** 3/3 执行，`任务数: 3  失败: 0` |
| 27b | 重名任务名 | **FAIL** 真实 exit 9 被吞，整批 rc=0 | **PASS** 启动前 rc=2，0 任务被起 |
| 27c | 任务名含 `/` | **FAIL** 任务 exit 1 却消失，整批 rc=0 | **PASS** 启动前 rc=2 |
| 27d | 退出码未落盘（超长任务名 300 字符） | **FAIL** 任务从汇总消失，rc=0 | **PASS** 显式 `退出码未落盘` + rc=1 |
| 27e | 后端卡死（模拟断网无限重连） | **FAIL** 整批 `wait` 永不返回 | **PASS** `RUNNER_TIMEOUT=3` → 5s 收尾，`.exit=124`，无孤儿进程 |
| 27f | `RUNNER_TIMEOUT=3s`（非法值） | — | **PASS** rc=2 `需为非负整数秒` |

### 1.5 parallel_run.sh 报错路径

| # | 用例 | 修复前 | 修复后 |
|---|---|---|---|
| 28 | 空 tasks.tsv | PASS rc=2 | PASS rc=2 |
| 29 | 只有注释/空行 | PASS rc=2 | PASS rc=2 |
| 30 | tasks 文件不存在 | PASS rc=2 | PASS rc=2 |
| 31 | 无参数 | PASS rc=2 + 用法 | PASS 同 |
| 32 | 未知参数 `--wat` | PASS rc=2 | PASS 同 |
| 33 | **非法 backend 名** `--backend gpt5` | **FAIL rc=0 假 PASS** | PASS rc=2 `未知 backend: gpt5` |
| 34 | **缺提示词列（无 TAB）** | **FAIL** `set -u` 崩溃 rc=1 | PASS `[skip ]` 提示 + rc=2 |
| 35 | **`--jobs abc`** | **FAIL rc=0 假 PASS，只跑 1/5** | PASS rc=2 `需为正整数` |
| 36 | **后端二进制缺失** | 起 5 进程各 127、rc=1 | PASS rc=2 预检拦截，**0 个任务被起** |
| 37 | `--jobs` / `--backend` 缺值 | rc=1（bash `${2:?}`） | 未改，见 §4 遗留 |

### 1.6 真实后端

| # | 实测项 | 结果 | 证据 |
|---|---|---|---|
| 38 | **真实 codex CLI 端到端**（一轮） | **PASS** | codex-cli 0.149.1、model `gpt-5.6-sol`、session `01a042d5-…`；回复 `LIVE_TEST_OK`；tokens 28,313；`.exit=0`；16.1s |
| 38a | **真实 codex CLI 端到端**（二轮独立复跑） | **PASS** | session `01a042f2-50df-7611-8146-693bf1a13a11`；日志含真实 banner `OpenAI Codex v0.149.1` + `LIVE_TEST_OK`；tokens 28,319；`.exit=0`；**14s**；`evidence/ws_codex2/state/parallel/*/live_ok.log` |
| 39 | 真实 codex（网络故障期，18:26 与 19:06 两次） | 当时不可用 | `tls handshake eof` → `Reconnecting... 5/5` → `Reconnecting... waiting for network` 无限循环，实测 **491s（8 分钟）不退出、不写 `.exit`**；催生 §2.17 超时看护修复。事后补充证据：手动 SIGTERM 该卡死进程后，**codex 捕获信号并以 0 退出**，旧脚本把这个从未产出结果的任务记成 `.exit=0` 即 PASS —— 这就是 §2.17 修复必须无视 `wait` 返回值、强制把超时任务记 **124** 的原因（终端存档 `evidence/ws_codex/.../live_ok.exit`） |
| 40 | **claude 后端命令可见性**（本机正常 PATH） | **PASS（能找到）** | `command -v claude` → `~/.nvm/versions/node/v24.14.0/bin/claude`；预检通过并真实起了任务 |
| 40a | claude 后端在净 PATH（launchd/cron 口径） | PASS | `env -i PATH=/usr/bin:/bin` → rc=2 `找不到 claude` + alias 提示，0 任务被起；`evidence/claude_cleanpath.txt` |
| 40b | **claude 后端端到端** | **SKIP（CLI 未登录）** | 每任务 `Not logged in · Please run /login` → exit 1；脚本如实报 `FAIL live_ok` 且整批 rc=1，**没有假绿**；`evidence/claude_precheck.txt` |

关于 claude 后端，任务书的前提在本机**不成立，需要更正**：

- **`claude` 不是「只有 alias 没有二进制」**。本机 `which -a claude` 显示 3 条：
  交互式 zsh 的 alias（`claude --effort max --model "fable"`）、
  `~/.nvm/versions/node/v24.14.0/bin/claude`、`/opt/homebrew/bin/claude`。
  后两条是**真实二进制**，非交互 bash/zsh 都能 `command -v` 到（实测 rc=0）。
  所以「文档宣称支持但非交互 shell 找不到命令」这一缺陷**不复现**。
- **真正的阻塞是 CLI 未登录**：`claude -p "..."` 直接返回 `Not logged in · Please run /login`（rc=1）。
  这属于环境未配置，而非脚本缺陷；且脚本的记账是诚实的（任务 FAIL、整批 rc=1）。
- **`command -v` 预检仍有价值**：它拦住的是二进制真的缺失的场景 —— 净 PATH
  （launchd / cron / systemd 风格环境）下 codex 与 claude 都找不到，实测 rc=2 且 0 任务被起（#36、#40a）。
- **副作用提示**：脚本调用 PATH 上的二进制，交互式 alias 的 `--effort max --model fable`
  **不会生效**。要复现同款配置需 `RUNNER_ARGS="--effort max --model fable"`。
  这条属于文档口径问题，`README`/`docs` 不在本次可改范围，记为遗留 §5.3。

---

## 2. 发现的问题与修复

### 2.1 [P0] http provider 任何后端异常都向 MCP 调用方抛裸异常

`_predict_http` 用 `resp.raise_for_status()` + `resp.json()` + `data.setdefault(...)` 直通，
四类后端故障全部变成穿透 MCP 工具的 Python 异常。故障注入实测（修复前）：

| 注入 | 修复前系统行为 | 耗时 |
|---|---|---|
| HTTP 500 | 抛 `httpx.HTTPStatusError` | 0.03s |
| HTTP 401（缺 key） | 抛 `httpx.HTTPStatusError` | 0.03s |
| 畸形 JSON（截断 body） | 抛 `json.decoder.JSONDecodeError` | 0.02s |
| JSON 顶层是 list | 抛 `AttributeError: 'list' object has no attribute 'setdefault'` | 0.01s |
| 连接被拒 | 抛 `httpx.HTTPStatusError`（被代理伪装成 502，见 §2.3） | 3.91s |

对一个「回环里被 agent 调用」的工具，这意味着后端一抖动就是不可读的 traceback，
且 `AttributeError` 完全指不出问题在后端契约。

**修复**：全部收敛为 `{"provider":"http","ok":false,"verified":false,"error":...}`，
与既有「未配置 API_URL」分支的返回形状一致。修复后：

| 注入 | 修复后系统行为 | 耗时 |
|---|---|---|
| HTTP 500 | `ok=false`，error 含 `后端返回 HTTP 500；响应片段: '{"error":"internal predictor failure"}'` | 0.01s |
| HTTP 401 | `ok=false`，error 含 `HTTP 401` + 响应片段 | 0.00s |
| 畸形 JSON | `ok=false`，`后端响应不是合法 JSON: Expecting property name...` | 0.00s |
| JSON 非 dict | `ok=false`，`顶层应为对象，实得 list；请按 {target_smiles, route_id, steps:[...]} 约定返回` | 0.00s |
| 连接被拒 | `ok=false`，`连接逆合成后端失败: ConnectError: [Errno 61] Connection refused` | 0.00s |
| 超时 | `ok=false`，`后端 1.0s 内未响应（GOAI_RETRO_TIMEOUT 可调）` | 1.01s |

### 2.2 [P1] 超时硬编码 120s、不可配置，实测无法生效

修复前 `timeout=120.0` 写死。故障注入「后端 sleep 6s」时，系统**等满 6.02s 并返回成功**——
超时行为既不可测也不可调，真实后端挂住会把一个 agent 卡满 2 分钟。

**修复**：新增 `GOAI_RETRO_TIMEOUT`（默认 120，保持原行为）。实测 `GOAI_RETRO_TIMEOUT=1`
对 sleep 3s 的后端在 **1.01s** 返回结构化超时错误。

### 2.3 [P1] httpx 不 bypass localhost，自建后端被 macOS 系统代理劫持

本机 `_scproxy` 报系统代理 `http://127.0.0.1:7890`，而**没有任何 `*_PROXY` 环境变量**
（`env | grep -i proxy` 为空，所以肉眼排查不到）。三方对比：

```
raw socket  → ConnectionRefusedError（直连，真话）
urllib      → ConnectionRefusedError（urllib.request.proxy_bypass('127.0.0.1') == True，自动绕过）
httpx 默认  → HTTP 502（空 body）      ← 被代理接管，且把真实错误吞掉
httpx trust_env=False → ConnectError  （直连）
```

后果：`retro.py` 文档明确支持的「自建 ASKCOS / 本地模型服务」场景，
在任何装了 Clash/Surge 类代理的开发机上都会得到与后端无关的 502；
连接失败要 3.91s 才报出来；并且 `Authorization: Bearer <key>` 会经过代理进程。

**修复**：目标主机是 loopback（`127.*` / `localhost` / `::1` / `*.localhost`）时默认
`trust_env=False`，与 urllib/requests 的既有行为对齐；`GOAI_RETRO_TRUST_ENV=1` 可显式覆盖
（内网/企业代理场景）。回归测试 `test_http_loopback_ignores_system_proxy` 会在
`HTTP_PROXY` 指向死端口时要求 localhost 后端仍然连通。

### 2.4 [P1] 失败的预测会被实验方案标记为「已验证」

`experiment_plan_skeleton` 的 `provider_verified` 取
`route.get("verified", route.get("provider") != "stub")`。
一旦把 `ok=false` 的错误字典喂进 `make_experiment_plan`（回环里 agent 完全可能这么干），
provider 是 `http` 且没有 `verified` 键 → **`provider_verified: true`**，
即「后端刚报 500，方案却宣称路线已验证」。这直接违反该模块的安全契约
（stub/未验证结果不得当真值）。

**修复**：`ok=false` 的路线一律 `provider_verified=false`。
实测：后端 500 → `provider_verified=false`、`steps=[]`。

### 2.5 [P0] `--jobs` 并发上限在 macOS 自带 bash 下完全失效

根因：`wait_slot()` 只把 `rc == 127` 当作「bash 不支持 `wait -n`」，
但 bash 3.2 对 `wait -n` 报的是 **`rc=2`**（`wait: -n: invalid option`）：

```
$ /usr/bin/env bash -c 'sleep 0.1 & wait -n; echo rc=$?'
bash: line 0: wait: -n: invalid option
rc=2
```

于是 `wait_slot` 既不等待、又把 `active` 减 1 —— 闸门变成空操作。
实测 `--jobs 2` 跑 5 个任务：**峰值并发 5**，全部在 +0.00s 同时启动。
对真实 codex/claude 后端，这意味着说好并发 2、实际起 N 个计费 agent 会话。

**修复**：改用 `jobs -pr` 计数轮询（已实测在 bash 3.2 的命令替换里能正确看到父 shell 作业表），
在 bash 3.2/4/5 下都真实生效，不依赖 `wait -n` 的返回码语义。
实测修复后峰值 = 2，5/5 任务完成，退出码与汇总不变。

### 2.6 [P0] 子进程继承 tasks 文件 fd，`codex exec` 会吞掉后续任务行

真实 codex 日志第一行就是 `Reading additional input from stdin...`——
`codex exec` 会读 stdin。而 `while read ... done < "$TASKS_FILE"` 让后台子进程
继承了同一个 tasks 文件描述符，父子共享文件偏移。

修复前这个缺陷被 §2.5 掩盖了（闸门失效 → 父进程瞬间读到 EOF → 子进程读到 0 字节），
**一旦并发上限修好就会立刻暴露**。A/B 最小复现（`harness/stdin_steal_repro.sh`）：

```
A) 旧结构（闸门生效 + 无 </dev/null）：
   [t1] 从 stdin 吞掉 69 字节
   [t2] 从 stdin 吞掉 0 字节
   A 实际执行任务数 = 2   ← tasks 文件 5 行，静默丢 3 个，汇总还报两个 PASS

B) 修复后（</dev/null）：
   5 个任务各吞掉 0 字节，B 实际执行任务数 = 5
```

**修复**：`run_one "$name" "$prompt" </dev/null &`。
两处修复必须同时落地，否则修好闸门就等于引入静默丢任务。
回归测试 `test_parallel_run_child_stdin_isolated_from_tasks_file` 用「主动读 stdin 的假后端」守住。

### 2.7 [P1] 非法 backend 名 → 整批假 PASS、退出码 0

`run_one` 的 `*)` 分支 `return 2` 在写 `.exit` 之前返回，于是没有任何 `.exit` 文件；
末尾汇总循环 `for f in "$LOG_DIR"/*.exit` 一个都没匹配到 → `fail=0` → **`exit 0`**。
实测 `--backend gpt5`：日志目录空、5 个任务一个没跑成、汇总区一片空白、**rc=0**。
在无人值守回环里这是最危险的一类缺陷：拼错后端名 = 静默跳过整批工作并上报成功。

**修复**：启动前校验 backend 名，非 `codex|claude` 直接 `exit 2`；
`run_one` 里那个不可达的 `*)` 分支随之删除。实测 rc=2 + 明确报错。

### 2.8 [P1] bash 3.2 把 CJK 全角标点当作变量名的一部分 → `set -u` 崩溃

`echo "[skip ] $name：缺少提示词列..."` 与 `echo "未知 RUNNER=$RUNNER（支持...）"`
里，变量名紧贴全角 `：`/`（`。bash 3.2 把 ≥0x80 的字节当作合法标识符字符，
变量名被解析成 `name：` / `RUNNER（` → 未定义 → 在 `set -u` 下是致命错误：

```
tools/parallel_run.sh: line 83: name：: unbound variable
tools/parallel_run.sh: line 55: RUNNER（: unbound variable
```

后果：缺提示词列的行本该被友好跳过，实际让整个脚本 rc=1 退出；
非法 backend 连错误信息都打不出来。

**修复**：改用 `${name}` / `${RUNNER}` 显式花括号定界。

### 2.9 [P2] `--jobs abc` → 崩在循环里、只跑 1 个任务、仍然 rc=0

`(( active >= MAX_PAR ))` 里 `MAX_PAR=abc` 被当变量名解析 → `set -u` 报
`line 89: abc: unbound variable`，循环在第一个任务后中断，
而先跑完的那个任务成功 → 汇总 1 PASS、**rc=0**。又一个假 PASS。

**修复**：`[[ "$MAX_PAR" =~ ^[1-9][0-9]*$ ]]` 校验，不合法 `exit 2`。

### 2.10 [P2] 后端二进制缺失时先起一批任务再失败

修复前 PATH 无 codex：起 5 个进程各自 `command not found` → 127，rc=1。
虽然结论正确，但对真实后端等于先创建 N 个日志/进程再失败，
且错误信息埋在每个任务日志里而非顶层。

**修复**：启动前 `command -v "$RUNNER"` 预检，缺失则 `exit 2`，
并提示「若该命令只是交互式 shell 的 alias/函数，非交互 shell 看不到它」。
实测 rc=2，且 `state/parallel/` 下**没有任何任务被起**。

### 2.11 [P1，测试自身缺陷] real-codex 测试会被 PATH 上的假 codex 骗出假 PASS

我的第一版 `test_real_codex_backend_end_to_end` 只断言日志里出现 `LIVE_TEST_OK`。
由于提示词本身就是 `Reply with exactly: LIVE_TEST_OK`，任何回显提示词的假后端都能命中。
实测中我的 shell 会话 PATH 残留了假 codex，该测试在 **2.17s** 内「通过」——
是假 PASS（假后端只是把提示词打进日志）。

**修复**：测试先用 `codex --version` 认身份（要求含 `codex-cli`），
再要求日志出现真实 CLI banner `OpenAI Codex`，否则宁可 SKIP。
清理 PATH 后复测，真实后端 20.41s 通过（真实模型往返）。
这条记在这里是因为它同样是「只有实测才暴露」的问题：**验证代码本身也会说谎。**

二轮复现了这条防伪断言的价值：我的探测 shell 里残留了假 codex，该测试直接
SKIP 并给出理由 `PATH 上的 codex 不是真实 CLI: /var/.../fakebin/codex`，
而不是给假 PASS。清理 PATH 后同一测试 36.8s 真实通过。

---

## 2bis. 第二轮新发现的缺陷与修复

三个 P0 属于同一根因族：**汇总是靠 glob `.exit` 文件拼出来的，从不与「真正启动了哪些任务」对账。**
任何让 `.exit` 写不进去的原因，都会让该任务从汇总里凭空消失，整批还报成功。

### 2.12 [P1] 后端 steps 结构错位 → MCP 调用方只看到 `Error executing tool`

`retro.py` 的模块文档承诺「后端任何异常都收敛为 `{ok:false, error}`，不向 MCP 调用方抛裸异常」。
但这个承诺只覆盖了传输层。**JSON 合法、顶层是 dict、`steps` 结构不对**的响应
（后端版本漂移、网关改写、字段名变更都会产生）能过全部现有校验，
带着 `ok=true` 流进 `experiment_plan_skeleton`，然后在迭代 `steps` 时炸掉。

6 形态实测（`harness/probe_retro.py`，修复前）：

| 后端响应 | `predict` | `experiment_plan_skeleton` |
|---|---|---|
| `steps: "oops"`（字符串） | ok=True | **RAISED** `AttributeError: 'str' object has no attribute 'get'` |
| `steps: {"1": {...}}`（对象） | ok=True | **RAISED** `AttributeError: 'str' ...`（迭代 dict 得到 key 字符串） |
| `steps: null` | ok=True | **RAISED** `TypeError: 'NoneType' object is not iterable` |
| `steps: ["one","two"]`（元素是字符串） | ok=True | **RAISED** `AttributeError: 'str' ...` |
| `steps: [1,2,3]`（元素是数字） | ok=True | **RAISED** `AttributeError: 'int' ...` |
| 完全没有 `steps` | ok=True | steps=0，但 **verified=True**（空路线冒充已验证） |

经真实 MCP stdio 协议层看到的是（`harness/probe_mcp_crash.py`）：

```
payload = Error executing tool make_experiment_plan
```

调用方（agent）拿不到任何可判断的信息 —— 分不清是后端违约、路线 JSON 不对，还是本服务有 bug。

**修复**：新增 `_normalize_steps()`，在边界把 steps 收敛成 `list[dict]` 并如实报告问题：
对象形态按 key 排序摊平、非列表整体忽略、非对象元素跳过，全部记入返回值的 `route_problems`；
同时 `provider_verified` 增加两个必要条件 —— **解析时丢过东西不算已验证、0 步空路线不算已验证**。
不猜化学含义，只保证「读不全就不许声称完整」。

修复后 6/6 形态均返回可读方案、无一抛异常、无一自称 verified；
MCP 层返回完整 JSON（含 `route_problems`），`Error executing tool` 不再出现。

### 2.13 [P0] tasks.tsv 末行无换行符 → 静默丢掉最后一个任务

`while IFS=$'\t' read -r name prompt` 在末行没有换行符时返回非零，循环体不执行 —— 
这是 shell 的经典陷阱，而**多数编辑器默认不补末尾换行**。实测 3 行任务文件（末行无 `\n`）：

```
[start] a → .../a.log        [start] b → .../b.log
[done ] a (exit=0)           [done ] b (exit=0)
===== 并行批次汇总 =====
PASS  a
PASS  b                      ← 任务 c 从未执行，也没有任何警告
（脚本 rc=0）
```

无人值守回环里，这就是「少跑一个子主题检索，流程报告全部成功」。

**修复**：`while ... read -r name prompt || [[ -n "${name:-}" ]]`，末行未终止时仍处理一次。
实测 3/3 执行，汇总 `任务数: 3  失败: 0`。

### 2.14 [P0] 重名任务 → 真实失败被吞成假绿

日志与退出码按任务名落盘（`$LOG_DIR/$name.log` / `.exit`）。重名任务并发写同一份文件，
后完成的覆盖先完成的。实测两行同名 `dup`（一个 exit 9、一个 exit 0）：

```
[done ] dup (exit=9)          ← 真实失败
[done ] dup (exit=0)          ← 覆盖了上面那份 .exit
===== 并行批次汇总 =====
PASS  dup                     ← 只剩一行，失败彻底消失
（脚本 rc=0）
```

**修复**：启动前用 awk 抽任务名列做 `sort | uniq -d` 检测，重名直接 `exit 2` 并列出冲突名。
实测 rc=2、`state/parallel/` 下 0 个任务被起。

### 2.15 [P0] 任务名含 `/` → 退出码丢失、任务从汇总消失

任务名形如 `lit/diffusion`（对「按子主题命名」是很自然的写法）时，
`$LOG_DIR/lit/diffusion.log` 的父目录不存在，重定向失败：

```
tools/parallel_run.sh: line 63: .../lit/diffusion.log: No such file or directory
tools/parallel_run.sh: line 72: .../lit/diffusion.exit: No such file or directory
[done ] lit/diffusion (exit=1)   ← 任务真实失败
===== 并行批次汇总 =====
PASS  ok_task                    ← 失败任务不在汇总里
（脚本 rc=0）
```

**修复（两层）**：

1. 启动前拒绝含 `/` 的任务名（`exit 2` + 明确原因）；
2. **汇总改为与「已启动任务列表」逐个对账**，不再 glob `.exit`：
   退出码没落盘的任务显式报 `FAIL <name> (退出码未落盘: ... 缺失，任务未正常收尾)`，
   并新增一行 `任务数: N  失败: M` 便于核对。

第 2 层是对整个缺陷族的兜底。取证用超长任务名（300 字符 → 文件名过长，`.exit` 写失败）
验证：修复前该任务消失且 rc=0，修复后显式 FAIL、`任务数: 2  失败: 1`、rc=1。

### 2.16 [P2] loopctl 未 init / 账本损坏 → 12–24 行裸 traceback

`load()` 直接 `open()` + `json.load()`。实测 7 个子命令（status / log / gate / issue add /
check-done / advance / next-round）在未 init 的 workspace 下**全部**吐 12 行 traceback，
末行 `FileNotFoundError: [Errno 2] ...`；账本被损坏时是 24 行，末行 `json.decoder.JSONDecodeError`。

loopctl 是「多 agent 唯一状态源」，调用方（含 LLM agent）通常只读 stderr 尾行，
而裸 `FileNotFoundError` 分不清两种完全不同的处置：忘了 `init`，还是 `GOAI_WORKSPACE` 指错了。

**修复**：`load()` 捕获两类异常并给可执行提示（含当前 workspace 回显）：

```
账本不存在: <path>
请先初始化: loopctl.py init --topic "<研究主题>"；若已初始化过，检查 GOAI_WORKSPACE 是否指向正确工作区（当前 = <ws>）
```

```
账本 JSON 已损坏: <path>（Expecting property name enclosed in double quotes: line 1 column 16）
请人工修复该文件，或用 init --force 重建（会丢失回环历史）
```

实测 7 个子命令 stderr 均 ≤3 行、无 `Traceback`。

### 2.17 [P0] 无单任务超时 → 后端卡死拖挂整批（上一轮遗留项 #1，本轮修复）

一轮把它列为遗留是因为「会改变语义」。二轮实测中网络真的断了，拿到了硬证据：
真实 codex 在断网时**不会自行退出**，只无限打印

```
warning: Falling back from WebSockets to HTTPS transport. stream disconnected before completion: tls handshake eof
ERROR: Reconnecting... waiting for network        （持续重复）
```

实测挂了 **491 秒（8 分钟）**仍在跑，`.exit` 从未写出，脚本末尾 `wait` 永不返回。
对「晚上挂 5 个并行 agent」这个核心场景，等于整批无限期卡死且无任何诊断。

**修复（默认行为不变）**：新增 `RUNNER_TIMEOUT`（默认 0 = 不限，保持原语义）。
设为正整数时，`run_one` 用 `SECONDS` 计时看护，超时先 SIGTERM 再 SIGKILL，
退出码**强制**记 **124**（与 GNU timeout 一致），并在任务日志追加一行说明。
「强制」是实测逼出来的：codex 会捕获 SIGTERM 并以 **0** 退出（卡死 8 分钟的那次
被手动 SIGTERM 后，旧脚本把它记成 `.exit=0` 即 PASS）——若只信 `wait` 的返回值，
超时杀掉的任务会变成假 PASS。
实现要点：后端用 `( exec <backend> ... ) &` 启动，使 `$!` 就是后端进程本体，
否则杀到的只是包装子 shell。杀进程语义已实测确认：SIGTERM 掉 codex 的 node 入口会**连带回收原生子进程**
（`codex` = node 包装 + `codex-darwin-arm64` 原生二进制两个进程），因此无需进程组处理。

实测（1 个卡死任务 + 1 个正常任务，`RUNNER_TIMEOUT=3`，`--jobs 2`）：
整批 **5s** 收尾（原为永久挂死），`hang.exit=124`、`normal.exit=0`、rc=1，
任务日志末尾 `[parallel_run] 任务超过 RUNNER_TIMEOUT=3s 未返回，已强杀`，
`ps` 复查**无孤儿进程残留**。真实 codex 复跑时也带 `RUNNER_TIMEOUT=150` 兜底，14s 正常通过。

---

## 3. 故障注入结果总表

| 注入项 | 修复前系统行为 | 修复后系统行为 |
|---|---|---|
| 后端 HTTP 500 | 抛 `httpx.HTTPStatusError` 穿透 MCP 工具 | `ok=false` + `HTTP 500` + 响应片段（0.01s） |
| 后端 HTTP 401（缺 key） | 抛 `httpx.HTTPStatusError` | `ok=false` + `HTTP 401` |
| 畸形 JSON（截断 body） | 抛 `json.decoder.JSONDecodeError` | `ok=false` + `不是合法 JSON` + 解析位置 |
| JSON 顶层非 dict（list） | 抛 `AttributeError: 'list' ... setdefault` | `ok=false` + 契约提示 `{target_smiles, route_id, steps}` |
| 后端超时（sleep 6s） | **超时不生效**，等满 6.02s 后返回成功 | `GOAI_RETRO_TIMEOUT=1` → 1.01s 结构化超时 |
| 后端连接被拒（死端口） | 系统代理伪装成 `HTTP 502`，3.91s | 真实 `ConnectError`，0.00s |
| 失败路线喂进 make_experiment_plan | `provider_verified=true`（谎称已验证） | `provider_verified=false`，`steps=[]` |
| 持锁进程 `kill -9` | —（本来就正确） | 0.04s 恢复，无锁残留，账本未污染 |
| 假后端随机退出码 3 / 7 | 如实记录（本来就正确） | 同 |
| 后端二进制缺失 | 5 个任务各 127，rc=1 | 预检 `exit 2`，0 任务被起 |
| 非法 backend 名 | **rc=0 假 PASS**，无任何产物 | `exit 2` + 明确报错 |
| `--jobs abc` | **rc=0 假 PASS**，只跑 1/5 | `exit 2` + 明确报错 |
| tasks 行缺 TAB | `set -u` 崩溃 rc=1 | `[skip ]` 跳过该行 |
| 后端主动读 stdin | 闸门修好后**静默丢 3/5 任务** | 5/5 执行，子进程 stdin 恒为空 |

第二轮补充的注入项：

| 注入项 | 修复前系统行为 | 修复后系统行为 |
|---|---|---|
| 后端返回 `steps: "字符串"` | 抛 `AttributeError: 'str' object has no attribute 'get'` | 方案 steps=0、`provider_verified=false` + `route_problems` |
| 后端返回 `steps: {"1":{...}}` | 抛 `AttributeError`（迭代 dict 得到 key） | 按 key 排序摊平，`route_problems` 记录，不标 verified |
| 后端返回 `steps: null` | 抛 `TypeError: 'NoneType' object is not iterable` | 方案 steps=0，`provider_verified=false` |
| 后端返回 `steps: [1,2,3]` / `["a","b"]` | 抛 `AttributeError: 'int'/'str' ...` | 逐元素跳过并记账，不标 verified |
| 后端 200 但完全没有 `steps` | `provider_verified=true`（0 步空路线冒充已验证） | `provider_verified=false` |
| 上述任一经 MCP 协议层 | `Error executing tool make_experiment_plan`（无诊断信息） | 完整方案 JSON + `route_problems` |
| tasks.tsv 末行无换行符 | **静默丢末行任务，rc=0 报全成功** | 全部执行，`任务数: N  失败: 0` |
| 重名任务（exit 9 + exit 0） | **只剩 1 行 PASS，rc=0**（失败被吞） | 启动前 rc=2，0 任务被起 |
| 任务名含 `/`（真实 exit 1） | **任务从汇总消失，rc=0** | 启动前 rc=2 |
| `.exit` 未落盘（超长任务名） | **任务从汇总消失，rc=0** | `FAIL ... 退出码未落盘`，rc=1 |
| 后端卡死（断网无限重连） | **整批 `wait` 永不返回**（实测 491s 未退出） | `RUNNER_TIMEOUT=3` → 5s 收尾，`.exit=124`，无孤儿 |
| loopctl 未 init（7 个子命令） | 12 行 Python traceback | ≤3 行可执行提示（含 workspace 回显） |
| loopctl 账本 JSON 损坏 | 24 行 traceback | ≤3 行提示，指向 `init --force` |

---

## 4. 修复清单

`server/core/retro.py`（4 项）

1. `_predict_http` 全异常收敛为结构化 `ok=false`（500/4xx、超时、连接失败、畸形 JSON、非 dict JSON），新增 `_http_error` 辅助函数。
2. 新增 `GOAI_RETRO_TIMEOUT`（默认 120.0，保持原行为），超时可测可调。
3. 新增 `_trust_env()`：loopback 后端默认不走环境/系统代理，`GOAI_RETRO_TRUST_ENV` 可覆盖。
4. `experiment_plan_skeleton`：`ok=false` 的路线一律 `provider_verified=false`。

`tools/parallel_run.sh`（5 项）

5. `wait_slot` 改为 `jobs -pr` 计数轮询，替换只认 `rc==127` 的 `wait -n` 判断（bash 3.2 实为 rc=2）。
6. 子进程 `</dev/null`，隔离 tasks 文件 fd（与 5 必须同时生效）。
7. 启动前 backend 名白名单校验 + `command -v` 可用性预检，失败 `exit 2`；删除 `run_one` 里不可达的 `*)` 分支。
8. `--jobs` / `max_parallel` 正整数校验，非法 `exit 2`。
9. `${name}` / `${RUNNER}` 花括号定界，修 bash 3.2 下 CJK 标点导致的 `set -u` 崩溃。

**第二轮新增修复（6 项）**

`server/core/retro.py`（1 项，含 2 处语义收紧）

10. 新增 `_normalize_steps()`：后端 `steps` 为对象/null/非列表/元素非对象时收敛为 `list[dict]`，
    问题记入返回值 `route_problems`；`provider_verified` 追加两个条件 ——
    解析时丢过内容不算已验证、0 步空路线不算已验证。

`tools/parallel_run.sh`（4 项）

11. 主循环 `|| [[ -n "${name:-}" ]]`：末行无换行符时不再丢任务。
12. 启动前任务名预检：重名（`sort | uniq -d`）与含 `/` 一律 `exit 2`。
13. 汇总改为与 `launched[]` 逐个对账，`.exit` 缺失显式报 FAIL，并输出 `任务数: N  失败: M`。
14. 新增 `RUNNER_TIMEOUT`（默认 0=不限）单任务超时看护：SIGTERM→SIGKILL，退出码记 124；
    后端改用 `( exec ... ) &` 启动以便杀到进程本体；含非负整数校验。

`tools/loopctl.py`（1 项）

15. `load()` 捕获 `FileNotFoundError` / `json.JSONDecodeError`，改为可执行提示（含当前 workspace 回显），
    替代 12–24 行裸 traceback。

未改动共享文件：`pyproject.toml`、`tests/test_offline.py`、`README*`、其它 `docs/`。
`pyproject.toml` 已有 `live` marker 与默认 `-m 'not live'`，无需改动即可跑本轮测试。

验证（第二轮收工态）：

- `.venv/bin/python -m pytest tests/ -q` → **25 passed**（离线基线未动）
- `.venv/bin/python -m pytest -m live tests/live/test_live_loop.py -q` →
  **46 passed, 1 skipped**（43.0s；唯一 skip 是真实 claude 未登录，且已断言失败被如实记账）
- `bash -n tools/parallel_run.sh` 通过（本机未装 shellcheck，已跳过）
- 新增 live 用例 24 项：结构错位 6 参数化 + 摊平 1 + MCP 不透明错误 1 +
  loopctl 未 init 7 参数化 + 账本损坏 1 + parallel_run 末行/重名/斜杠/退出码缺失/超时/非法超时 6 +
  claude 净 PATH 预检 1 + 真实 claude 端到端 1

---

## 5. 遗留建议（两轮收工后仍未改）

> 一轮遗留 #1（无单任务超时）已在二轮修复，见 §2.17。

1. **[中] `loopctl` 的 flock 是无限期阻塞、无锁超时。** `kill -9` 的进程内核会自动放锁
   （二轮复测 0.031s 恢复），但**挂而不死**的持锁进程会无限阻塞所有 agent。
   建议 `LOCK_NB` + 有限重试 + 超时报错，把「账本被谁占着」变成可诊断故障。
   本轮未做：会改变所有子命令的阻塞语义，且需要设计「等多久算异常」的默认值。

2. **[中] claude 后端需要登录，文档未提。** 真机 `claude -p` 直接
   `Not logged in · Please run /login`（rc=1）。建议 README/文档写明
   「claude 后端需先交互登录」，并考虑预检加一次轻量鉴权探测。
   注意：**不要**把「未登录」也做成 `exit 2` 预检 —— 每次批次前额外打一次 API
   既慢又计费，当前「任务级失败 + 如实记账」的行为是可接受的。

3. **[中] `parallel_run.sh` 走 PATH 二进制，交互式 alias 的参数不生效。**
   本机 `alias claude='claude --effort max --model "fable"'` 在脚本里完全不起作用，
   用户会以为跑的是 fable/max 配置，实际是 CLI 默认配置。
   建议文档写明用 `RUNNER_ARGS` 显式传参（`docs/` 不在本次可改范围）。

4. **[低] 非 loopback 后端的 API key 仍会过系统代理。** 若对接内网 ASKCOS，
   建议显式设 `NO_PROXY` 或 `GOAI_RETRO_TRUST_ENV=0`，避免 key 经第三方代理进程。

5. **[低] `--jobs` / `--backend` 缺值时 rc=1**（bash `${2:?}` 的默认行为），
   与其它用法错误统一的 rc=2 不一致，报错文本也偏底层（`line 26: 2: --jobs 需要值`）。

6. **[低] mcp SDK 2.x 字段改名。** 客户端侧 `serverInfo`→`server_info`、
   `protocolVersion`→`protocol_version`；写实测/集成代码时建议 `getattr` 双写兼容。

7. **[低] 任务名未做字符白名单。** 已拒绝 `/` 与重名，但含空格、`..`、
   前导 `-` 的名字仍会进日志文件名（实测不会丢退出码，故未拦）。
   若要更严，建议限定 `[A-Za-z0-9_.-]+`。

8. **[低] `RUNNER_TIMEOUT` 的超时精度是 1 秒轮询**（`sleep 1` + `SECONDS` 计时），
   对分钟级的 agent 任务足够；若要秒级精度需改用更细的轮询间隔。

---

## 6. 证据文件索引

实测探针与原始输出均保留在 `workspace_live/loop/`：

| 路径 | 内容 |
|---|---|
| `harness/mock_askcos.py` | mock ASKCOS 风格后端（含 500/slow/badjson/notdict/needkey 注入端点） |
| `harness/mcp_stdio_probe.py` | MCP stdio stub 全链路探针（11 检查项） |
| `harness/mcp_http_probe.py` | MCP stdio + http provider 全链路探针（12 检查项） |
| `harness/http_provider_probe.py` | http provider 故障注入探针 |
| `harness/loopctl_stress.py` | loopctl N 进程混合并发压测 |
| `harness/loopctl_kill9.py` | 持锁 `kill -9` 锁释放实测 |
| `harness/fakebin/codex`、`fakebin_stdin/codex` | 假 codex 后端（并发轨迹版 / 读 stdin 版） |
| `harness/stdin_steal_repro.sh` | stdin 吞任务 A/B 最小复现 |
| `harness/throttle_probe.sh` | bash 3.2 下 `jobs -pr` 闸门可行性验证 |
| `harness/pr_errorpaths.sh`、`pr_edge.sh`、`pr_missing_backend.sh` | parallel_run.sh 报错路径矩阵 |
| `harness/net_probe.py` | socket/urllib/httpx 三方对比，定位系统代理劫持 |
| `evidence/mock_requests.jsonl` | mock 后端逐条请求日志（API key 透传证据） |
| `evidence/http_probe_A_proxy.json`、`http_probe_fixed.json` | 故障注入修复前/后原始结果 |
| `evidence/trace_jobs2.log`、`trace_jobs2_fixed.log` | 并发时间线（峰值 5 → 2） |
| `evidence/trace_stdin_steal.log`、`trace_stdin_fixed.log` | 子进程 stdin 读取字节数 |
| `pr_ws_real2/state/parallel/*/live_ok.log` | 真实 codex 端到端日志（banner + `LIVE_TEST_OK` + tokens） |

第二轮新增（`harness/` 探针 + `evidence/r2_*.json` 固化输出）：

| 路径 | 内容 |
|---|---|
| `harness/probe_retro.py` | 6 形态结构错位后端响应探针（起真实 HTTP server） |
| `harness/probe_mcp_crash.py` | 结构错位路线经真实 MCP stdio 层的调用方视角取证 |
| `harness/probe_loopctl.py` | loopctl 未 init / 账本损坏的 8 用例报错矩阵 |
| `harness/measure_retro_http.py` | http provider 全量取证：key 透传 + 5 类故障注入 + MCP 三链路 |
| `harness/measure_loopctl.py` | 50 进程混合并发压测（含撕裂读哨兵线程） |
| `harness/measure_kill9.py` | 持锁 `kill -9` 锁释放取证 |
| `evidence/r2_retro_http.json` | mock 后端逐条请求 + 故障注入结果 + MCP 链路结论 |
| `evidence/r2_loopctl_50proc.json` | 50 并发：0.25s、零丢失、撕裂读 0 次、`I1..I16` 连续 |
| `evidence/r2_kill9.json` | 阻塞确认 + SIGKILL 后 0.031s 恢复 |
| `evidence/r2_malformed_steps.json` | 6 形态修复后结论（全部 `verified=False`，无异常） |
| `evidence/r2_loopctl_errorpaths.json` | 8 用例 stderr 行数 / 是否含 Traceback |
| `evidence/claude_precheck.txt`、`claude_cleanpath.txt` | claude 后端正常 PATH 与净 PATH 两种口径 |
| `evidence/ws_codex2/state/parallel/*/live_ok.log` | 二轮真实 codex 日志（session `01a042f2-…`，tokens 28,319） |

可持久化回归：`tests/live/test_live_loop.py`（**47 项**，`pytestmark = pytest.mark.live`）。
跑法：`.venv/bin/python -m pytest -m live tests/live/test_live_loop.py -v`
（自带 mock 后端与假后端；只有真实 codex / 真实 claude 两项依赖外部网络与登录态，
不可用时按防伪规则 SKIP 而非假 PASS）。
