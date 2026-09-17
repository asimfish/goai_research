# 算力与费用统计

控制台入口：[算力 / 费用统计](http://127.0.0.1:5051/#/costs)。也可以在研究运行页点击「算力 / 费用」。选择一个研究或全部研究后，可查看普通输入、输出、缓存读取、缓存写入的实际 token，以及按单次研究、单个会话、整轮任务汇总的金额。页面每 10 秒更新，支持导出 JSON。

计量来自 Codex / 模型服务返回的 usage，不从提示词长度推算。日志只有回合结束时才返回用量时，运行中的费用暂不完整；失败但没有返回 usage 的会话标记为缺失。**「已计金额」只包含可计算的部分，不能把未返回用量当作免费。**

## 对话与回复统计（2026-09-18）

页面默认选择最新研究，顶部新增活动指标，与当前选择的研究 / 会话 / 整轮任务范围一致：

| 字段 | 计数口径 |
| --- | --- |
| `conversation_count` / 对话次数 | 已保存 `thread.started` 的模型会话按 thread ID 去重；工具调用不增加对话次数 |
| `turn_count` / 交互轮数 | 已记录的 `turn.started`，含同一线程的后续调用 |
| `reply_count` / 回复条数 | `item.completed` 中的 `agent_message`，包含过程说明与最终答复；忽略 started/updated 流式片段、推理消息和工具输出 |

统计包含失败会话中已保存的回复。复制的工作区和重复完成事件不重复计数；同一线程后续调用复用局部消息 ID 时，按调用标识区分。只有 usage 收据而没有消息日志时，这三个字段返回 `null`，页面显示“—”；不以 token 数或收费记录数推测对话数量。指标只反映已保存日志，不代表日志以外的完整账户活动。

`summary`、`researches`、`sessions`、`tasks` 和 `models` 返回相同字段。活动标记与费用事件分开聚合，不参与定价、不产生缺价警告，也不保存消息正文。计量缓存解析版本升级后自动刷新，无需删除原始日志。

真实记录复核（5051）：

| 研究 | 对话次数 | 回复条数 | 已计金额 USD |
| --- | ---: | ---: | ---: |
| R-A1C302457C · 材料实验执行 | 1 | 7 | 0.02270264 |
| R-F7D0BA2E37 · LLZO 合成方法调研 | 40 | 509 | 7.37035912 |

两份报告新增计数前后的所有原费用汇总字段完全一致。计费回归共 50 项通过，覆盖重复记录、线程续用、失败回复、缓存更新、范围筛选与缺失日志。报告和界面验证保存在 `/home/gaojing/goai_final_lab/manifests/materials-workbench/panel-layout-20260918/`。

## 价格与计算

价格配置：[configs/model_prices.json](../configs/model_prices.json)。页面可以编辑四类单价、增加模型；高级 JSON 支持别名、币种、服务档位、峰谷价、长上下文倍率和工具服务费。价格按每百万 token 配置，金额用 Decimal 计算，不逐条取整。不同币种分别合计，不自动汇率换算。

2026-09-16 默认价格如下，币种为 USD。OpenAI 表格为 Standard、单请求输入不超过 272,000 token 的价格；DeepSeek 表格为谷时价格。

| 显示名称 / 模型 | Input | Output | Cache read | Cache write |
| --- | ---: | ---: | ---: | ---: |
| GPT 5.6 / gpt-5.6-sol | 4 | 20 | 0.4 | 5 |
| Luna / gpt-5.6-luna | 0.2 | 1.2 | 0.02 | 0.25 |
| Astra / gpt-6-astra | 10 | 50 | 1 | 12.5 |
| Terra / gpt-5.6-terra | 2 | 12 | 0.2 | 2.5 |
| DeepSeek / deepseek-flash | 0.15 | 0.6 | 0.003 | 0 |

来源：[OpenAI API 价格](https://developers.openai.com/api/docs/pricing)、[Astra](https://developers.openai.com/api/docs/models/gpt-6-astra)、[Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna)、[DeepSeek 官方价格](https://api-docs.deepseek.com/quick_start/pricing/)。GPT 5.6、Luna、Astra、DeepSeek 的别名均可直接使用；新增或第三方路由请配置对应的实际模型 ID 和费率。

OpenAI 长上下文输入及缓存价格乘 2、输出乘 1.5；Priority / Fast 乘 2，Batch / Flex 乘 0.5。配置支持 DeepSeek 工作日 UTC 01:00–04:00、06:00–10:00 的 2 倍峰价。DeepSeek 缓存未命中算普通输入，自动写缓存没有另收写入费；不能将 miss tokens 再计一次 cache write。[OpenAI 计价说明](https://developers.openai.com/api/docs/pricing)、[DeepSeek 缓存说明](https://api-docs.deepseek.com/guides/kv_cache/)。

计算公式：

```text
输入包含缓存子项的 usage：
  普通输入 = 总输入 − cache read − cache write

模型费用 = (普通输入 × input 单价 + 输出 × output 单价
            + cache read × 读取单价 + cache write × 写入单价) / 1,000,000
总费用 = 模型费用 + 已配置的 MCP 额外服务费
```

推理 token 是输出的子集，不再次收费。Anthropic 格式的普通 input 不包含缓存，适配器按它的口径处理。未知模型、未知服务档位、峰谷计费缺少请求时间、按时间计费的工具缺少时长，均显示「缺少计价」。

这些是可配置的 API 费率折算结果，**不等同于 Codex 订阅或转售商账户的实际扣款**。如果使用第三方平台，请将价格表改为平台费率。

## 自动归集与价格快照

- 单次研究：控制台工作区 ID；包含编排器、全部子任务、后续 MCP 用量。
- 单个会话：Codex thread ID 或上报的 session_id；能够确定所属线程的工具内部模型调用并入该线程。
- 整轮任务：billing_task_id；多个研究可以共享这个编号。发起研究的高级设置支持填写「整轮任务编号」，未填则默认一次研究为一轮。

研究启动时写入 `state/billing_context.json` 和 `state/billing_prices.json`，之后改变当前价格不会改写该研究的快照。价格编辑使用版本校验，防止多个浏览器互相覆盖；旧配置保存在 `workspace/.billing/price_history/`。

对于没有价格快照的历史研究，使用当前配置并标明「历史价格折算」。老 Codex CLI 日志往往只有整段会话累计输入，不能据此判断单请求是否超过长上下文阈值，也无法可靠恢复服务档位；统计会采用 Standard 基础费率并显示这些缺口，不会用累计百万 token 错套单请求长上下文加价。

自动读取的来源：

| 来源 | 用途 |
| --- | --- |
| `state/orchestrator/*.jsonl`、同名 `.billing.json` | 编排器真实用量、每次尝试的实际模型 |
| `state/parallel/*/*.jsonl`、`RUN_INFO.json` | 并行子任务的用量与模型 |
| `model_runs/*/events.jsonl`、`invocation.json` | 决赛方案提取、编排和实验执行的模型调用 |
| `state/tool_calls.jsonl` | MCP 审计、调用数、已有耗时；与客户端调用记录匹配去重 |
| `state/usage_events.jsonl` | API 或工具内部模型的用量回执 |
| `state/billing_errors.jsonl` | 工具内部用量保存失败的可见标记 |

回放目录中相同 Codex 线程 / 调用事件在全局汇总时只计一次；多份记录的计价信息冲突时标记为待核对。单独选择一个副本仍能查看其原有会话。缓存位于 `workspace/.billing/cache.sqlite3`，按文件指纹更新，只解析计量字段，不将整段提示词或工具返回内容复制到缓存。

本机 MCP 默认没有额外服务费。MCP 返回内容消耗的宿主模型 token 已计入宿主 usage。若 MCP 内部调用另一个收费模型，其回执单独计入。已有 audit 包装识别 `billing_usage`，或带 `model` 与 `usage` 的原始模型响应。工具需要返回这些回执才能计算内部模型费用；没有上报机制的外部付费服务需要补适配器。

如工具本身收费，可在价格表加入：

```json
"tools": {
  "paid.search": {"per_call": "0.01", "per_second": "0.001"}
}
```

`paid.search` 表示 server.tool，或使用仅含工具名的键。配置覆盖本机工具的默认零额外费用。

## API 与命令行

| 接口 | 功能 |
| --- | --- |
| `GET /api/billing/prices` | 当前配置与 revision |
| `POST /api/billing/prices` | 提交 `{config, expected_revision}` |
| `GET /api/billing/summary` | 全部研究汇总 |
| `GET /api/workspaces/{id}/costs` | 指定研究汇总 |
| `POST /api/workspaces/{id}/usage` | 上报模型实际用量 |

汇总接口支持 `?task_id=...` 或 `?session_id=...`。原始逐条计价依据通过 CLI 报告导出；页面接口只返回分组结果，减少刷新开销。

上报示例（测试数据，非实际账单）：

```json
{
  "event_id": "provider-request-123",
  "session_id": "host-thread-id",
  "task_id": "finals-round-1",
  "model": "Luna",
  "timestamp": "2026-09-16T00:30:00Z",
  "service_tier": "standard",
  "usage_scope": "request",
  "usage": {
    "input_tokens": 150000,
    "output_tokens": 10000,
    "cached_input_tokens": 20000,
    "cache_write_input_tokens": 30000
  }
}
```

普通输入为 100,000，四项费用为 0.02 + 0.012 + 0.0004 + 0.0075，合计 **USD 0.0399**。同一研究内相同 event_id 重传不重复计费；同一 ID 改内容返回 400。只接受单次增量计数，不接受重复累计计数。session_id 应使用宿主会话 ID，调用内部模型时可额外提供 agent_task_id、parent_tool_call_id。

```bash
# 不调用模型，也不运行实验；读取已有真实日志
.venv/bin/python tools/usage_cost.py report \
  --workspace workspace/finals_execution_20260915 \
  --output workspace/usage_cost_20260916/finals-round.json

# 多个研究归入同一轮：在启动前初始化新的工作区
.venv/bin/python tools/usage_cost.py init --workspace workspace_runs/new-study \
  --task-id finals-round-1

# 后续工具调用传递同一编号；只设置关联，不启动任何脚本
export GOAI_BILLING_TASK_ID=finals-round-1

# 提交真实模型回执；支持 --prices 指定配置文件
.venv/bin/python tools/usage_cost.py record --workspace workspace_runs/new-study \
  --receipt /path/to/provider-usage.json
```

`report` 支持重复 `--workspace`，以及 `--task-id` / `--session-id`。`GOAI_PRICE_CONFIG` 可指定控制台、CLI 和研究启动所使用的价格文件。`GOAI_SERVICE_TIER` 用于记录已知实际服务档位，本身不会改变模型服务的执行档位。

## 本机真实用量验证（2026-09-16）

以下金额使用真实历史 token、Luna 的当前 Standard 基础费率折算；不是重新启动实验，也不是构造 token 的演示账单。

| 范围 | 普通 Input | Output | Cache read | Cache write | 已计金额 USD | 缺失用量 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 一条实验执行会话 | 155,710 | 8,744 | 2,121,216 | 0 | 0.08405912 | 0 |
| 一次 BaZn2Si2O7 衍生物研究 | 6,604,599 | 1,144,969 | 219,501,184 | 0 | 7.08490628 | 4 |
| 决赛工作区整轮 | 2,819,511 | 243,582 | 48,472,064 | 0 | 1.82564188 | 1 |

会话 ID：`01a0a1c0-28bc-77e0-aa18-84cd294fac88`。普通输入从原始总输入 2,276,926 中扣除缓存读取得到；输入费 0.031142、输出费 0.0104928、缓存读取费 0.04242432。

研究工作区：`workspace_runs/console/20260906_065848_BaZn2Si2O7可能的衍生的新化合物合成调研`。决赛工作区：`workspace/finals_execution_20260915`，有 18 份完整用量和 1 条无完整 usage 的会话。上述研究与决赛金额都是已知部分，缺失会话未按零计算。

验收文件在 `workspace/usage_cost_20260916/`：Git 拉取记录、专项 / 全量测试、前端构建日志、浏览器桌面和移动截图、导出 JSON，以及 `research-example.json`、`session-example.json`、`finals-round.json` 的逐条计价依据。

验证：47 项计费专项测试；本功能发布范围在独立检出目录中得到 161 passed、1 skipped、100 deselected；TypeScript 检查与 Vite 构建通过。浏览器核对了三级汇总行数、模型价格输入、切换研究、金额一致性、导出 JSON 和页面错误。

重跑浏览器验收时，先安装 Playwright 及其 Chromium，然后指定运行中的控制台与真实研究工作区。Playwright 不在当前 Node 模块路径时，可用 `PLAYWRIGHT_MODULE` 指向已安装的模块；`CHROMIUM_PATH` 可覆盖浏览器路径：

```bash
CONSOLE_URL=http://127.0.0.1:5051 \
RESEARCH_WORKSPACE=/absolute/path/to/research-workspace \
node tools/usage_cost_ui_acceptance.cjs
```
