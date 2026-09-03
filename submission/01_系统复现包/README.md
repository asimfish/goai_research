# 01 系统复现包

系统复现包的主体就是本仓库（代码材料压缩包内为 `01_系统复现包/goai_research/`）：

| 内容 | 位置 |
|---|---|
| 全部功能模块源代码（检索、核验、绘图、逆合成 4 个 MCP server） | `server/` |
| 调用 LLM 的全部 Prompt | `skills/goai-*/SKILL.md`（9 个 Agent 角色）、`AGENTS.md`（宿主守则）、`docs/competition/TASK_PROMPT.md`；各次运行中子任务收到的逐字提示词在 `../03_运行与评测包/<运行>/tasks/*.tsv` |
| 配置、依赖版本 | `configs/*.example`、`pyproject.toml` + `uv.lock`、`install.sh` |
| 模型名称与版本、端点、采样参数、随机种子 | `docs/competition/SUBMISSION.md` §2（Codex CLI 0.146.1；`gpt-5.6-sol`；`model_reasoning_effort = xhigh`；OpenAI 默认端点；LLM 无可设种子，确定性组件种子与 checkpoint SHA-256 见 `vendor/two_stage_retro/PROVENANCE.md`） |
| 环境变量模板 | `.env.example` |
| 一键安装 / 运行 / 评测 | `install.sh`、`scripts/smoke_test.sh`、`scripts/reproduce_core.sh` |
| 预测模型（两阶段无机前驱体预测） | `vendor/two_stage_retro/`（checkpoint、最小推理代码、原料库） |

## 构筑阶段 Agent 会话轨迹（`构筑阶段轨迹/`）

Harness：Codex CLI 0.146.1（同一内核经 whalent 网关以多轮对话方式使用）。

| 文件 | 内容 |
|---|---|
| `rollout-2026-08-16T22-01-50-….jsonl.gz` | 构筑阶段的原生 Codex rollout（2026-08-16 → 2026-09-02），`turn_context` 逐轮记录 model 与 effort |
| `whalent_codex_conversation.jsonl.gz` | 同一对话在网关侧的消息级导出（3,539 条） |
| `codex_exec_deck_revision_2026-09-03.jsonl.gz` | 09-03 用 `codex exec --json` 按修订简报修改方案说明 PPT 的会话 |
| `trace_info.json` | 上述文件的计数与 SHA-256 |
| `codex_sessions_index.json` | 全部原生 rollout 的索引（originator、cwd、模型、推理强度、轮数）；运行阶段的 rollout 在 `../03_运行与评测包/运行阶段轨迹/` |

仓库另一部分由队友以 Codex CLI 通过 GitHub PR #1–#20 提交，其会话以 PR 形式留存于 GitHub 历史。
