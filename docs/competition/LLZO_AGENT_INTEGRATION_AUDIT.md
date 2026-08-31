# LLZO Agent 集成实测与失效模式审计

日期：2026-08-29。范围：将仓库的通用化学合成调研切换为
`Li7La3Zr2O12`（LLZO）合成、相稳定与致密化诊断调研，并真实运行各角色。

## 1. 运行口径

- 宿主：本机默认 Codex 账户、默认模型 `gpt-5.6-sol`、默认 `xhigh` 推理；
  runner 未显式覆写模型。
- 真实角色：三路 lit-search、style-bank、汇合者、ref-guard、survey-writer
  taxonomy、figure-studio、idea-forge/retro、两轮 reviewer。
- MCP：`goai-litsearch`、`goai-refcheck`、`goai-figure`、`goai-retro`。
- 轨迹：21 个 JSONL 任务；当前可解析轨迹记录 49 次完成的 MCP 调用。
  总 input tokens 约 7.49M，其中 cached 约 6.68M。第一轮三条检索轨迹因
  运行中热修改 runner 被重复启动覆盖，故实际调用与 token 高于此数。
- 自动分析：`tools/analyze_agent_traces.py`；报告在
  `workspace/state/AGENT_TRACE_AUDIT.{json,md}`。

## 2. 当前可用结果

| 环节 | 实测结果 | 当前状态 |
|---|---|---|
| 本地全文 + 多源检索 | 46 篇 LLZO 论文，DOI/年份/作者齐，规范化后零重复 | PASS（standard 诊断档） |
| 六主题覆盖 | 命中 14/9/44/28/13/23 | PASS，但非 comprehensive |
| 风格库 | 15 篇综述、1 篇全文、写作卡/图卡/参照图 | WARN（浅层） |
| 引用核查 | 首轮 43 PASS/1 FIX/2 MISMATCH；修复后 46/46 PASS | PASS |
| Taxonomy | 14 叶、46 key 全存在、每叶 4–7 篇 | 机械校验 PASS；语义待确认 |
| 图 | figspec + SVG + drawio + PNG；I2 修复后复审通过 | 诊断产物，非正式图 |
| 无机逆合成 | 真实 checkpoint，LLZO Top-5；Top-1 为 ZrO2/La2O3/Li2CO3 | 模型输出已验证，化学未验证 |
| route → plan | Top-1 已映射为 1 步非空骨架，conditions=null | 接口 PASS；NOT FOR LAB USE |
| Reviewer | 首审 4 major；I2/I3 修复复审通过 | I1/I4 仍 open；同模型 provisional |

## 3. 失效模式、证据和处置

### F01 — MCP 工具全部显示“user cancelled”

- 现象：server 可被直接 MCP client 调用，但 Codex Agent 的每个 MCP 调用均取消。
- 根因：`approval_policy=never` 只控制 shell/审批流程，不会自动批准 MCP tool；
  server 缺少 `default_tools_approval_mode="approve"`。
- 处置：四个 server 均显式配置该字段；`mcp_probe4` 后真实调用成功。

### F02 — Agent cwd 错位

- 现象：Agent 从 `workspace/` 起步后查找 `workspace/inputs`，形成
  `workspace/workspace/...`，并看不到仓库根的 skills/tools。
- 处置：runner 分离 `GOAI_WORKSPACE`（产物根）与 `RUNNER_CWD`（仓库根）。

### F03 — 只读 Agent + 可写 MCP 的“半成功”

- 现象：文献通过 MCP 成功入库，但 Agent 自己写笔记与 ledger 失败；后端仍 exit=0。
- 根因：Codex shell 默认 read-only，MCP server 是独立进程且仍可写。
- 处置：runner 显式 `-s workspace-write`；stdout JSONL 与 stderr 分流。

### F04 — 并行入库并非真正并发安全

- 现象：`save_to_library` 原实现为无锁 read–merge–overwrite，多 Agent 可丢记录。
- 处置：为完整 read-modify-write 周期加 `fcntl` 文件锁，并使用
  `fsync + os.replace`；20 进程并发测试保留 20/20 条。

### F05 — 检索输出与上下文膨胀

- 现象：单个 grep MCP 返回最高约 266 KB；style Agent 一次 shell 事件超过
  1.07 MB；11 个任务 input tokens 超过 300k。一次 lit Agent 累计约 888k。
- 原因：Markdown 单行超长、摘要无界、重复近义词检索、整体打印 JSONL/PDF、
  默认 xhigh 对低风险整理任务也很重。
- 处置：全文命中行和 search 摘要截断并标 `*_truncated`；AGENTS 增加有界读取
  与检索预算；新增轨迹分析器。仍建议把整理/格式角色降到 medium/high。

### F06 — exit=0 假绿与旧产物假绿

- 现象：第一轮 Agent 明确缺笔记仍被 runner 报 PASS；重跑时旧文件存在也可能
  让“产物存在”检查误过。
- 处置：TSV 第三列声明产物；缺失/为空/未在本轮更新均改判 exit=3；
  `=path` 只检查既有非空依赖。I3 返工中真实触发过一次 exit=3，证明闸门有效。

### F07 — 运行中热修改 shell 脚本

- 现象：修改正在被 Bash 解释的 runner 后，旧进程按变化后的行偏移继续读取，
  汇总后意外再次启动任务并覆盖前三条 JSONL。
- 处置：立即终止重复进程并补跑低调用验收。操作规则：运行中的调度脚本只读，
  修复必须等当前批次退出或复制为新版本后再启。

### F08 — 上游 API/下载常态失败

- 现象：Semantic Scholar 多次 HTTP 429；两个 MDPI PDF 为 403；部分 NAS grep
  超时；draw.io Desktop CLI 缺失。
- 处置：OpenAlex/Crossref 兜底，付费墙/403 fail-closed；本地超时如实记录；
  SVG/drawio 正常交付，PNG 用宿主 Chrome 从 SVG 生成。未伪造成功。

### F09 — 引用元数据噪声与 BibTeX 类型误判

- 现象：首轮发现 `Badding Michael Edward`、`Yongjiang Zhou` 两处作者问题，
  ACS venue 规范化问题；旧导出器把不含 Journal/Transactions/Letters 的期刊
  默认写成 `@inproceedings`。
- 处置：按 DOI 权威记录建立 `metadata_overrides.json`；Crossref HTML 清洗；
  保存 `publication_type`；默认期刊/会议判断修复。复核 46/46 PASS。

### F10 — Ref-Guard 批处理无进度、串行耗时

- 现象：46 条全库核查单次 MCP 调用约 2 分钟，期间 Agent 看不到逐条进度，
  难以区分“慢”与“挂”。
- 状态：功能正确、性能未优化。建议增加分片/并发上限、进度事件和断点续查。

### F11 — 确定性图 lint 全绿但视觉仍坏

- 现象：首次 validate/render 声称无错误；真实 PNG 显示红色限定语被左裁切、
  长边标签遮挡。XML/字号/端点校验没有覆盖文本锚点和最终视觉拥挤。
- 处置：真实截图 → 修复中心锚定坐标/缩短标签 → 再截图；Reviewer 又发现
  中间 chip 被误当整组主线，随后改用 group 边缘隐形锚点并补 D1 虚线。
- 结论：图的完成条件必须包含真实渲染视觉检查，不能只信 schema/lint。

### F12 — Retro provider 语义与 route-to-plan 不兼容

- 现象：`provider_status` 显示分子 provider=stub/trusted=false，但本地无机模型
  实际可用；无机 route 使用 `precursors` 而通用 plan 只识别 `steps`，返回空计划。
- 处置：拆出 `molecular_provider_trusted` / `local_inorganic_ready`；每条无机
  route 带 provider/模型验证/化学验证字段；无机前驱体集合映射为单步骨架。
- 复测：Top-1 plan=1 步、三输入、provider_verified=true、
  chemical_route_verified=false、conditions=null。

### F13 — Python 环境分裂

- 现象：基础 `.venv` 不含 torch/pymatgen，直接调用无机模型失败；
  `.venv-retro` 可用且 MCP 配置正确。
- 处置：本机使用独立 retro venv；公开安装必须用 `bash install.sh --retro`，
  并把“用错解释器”作为 preflight 错误显式报告。

### F14 — 返工只追加新状态，不清理旧状态

- 现象：route-to-plan 修复后 proposal 后段说“当前 1 步”，首段仍说“空步骤”。
- 处置：Reviewer 抓到 I3；idea Agent 统一当前状态并写确定性断言；冷启动复审
  判 I3 verified。说明返工后必须做跨文件 current-state consistency 检查。

### F15 — 机械 taxonomy 校验冒充语义 MECE

- 现象：key 存在/每叶≥3 可以机械 PASS，但工艺阶段、跨切环境和结果证据层
  混在一棵树里，不能由唯一主归属证明 MECE。
- 状态：I1 major 仍 open。建议改称“分面框架”：主工艺链 + 组成/环境修饰面 +
  结构性能证据面，并把 validator 明示为 mechanical-only。

### F16 — 接口诊断不等于研究 idea

- 现象：Top-1 路线可用，但尚无可证伪假设、对照、条件、量化阈值、路线专属
  全文证据；`LiHO`/`La(HO)3` 还需实体规范化。
- 状态：I4 major 仍 open。当前文件必须保持 infrastructure diagnostic 与
  `NOT FOR LAB USE`，不能包装成科学创新。

### F17 — 审稿独立性有限

- 现象：执行和审查都使用本地默认同一模型，虽为全新冷启动会话，仍非跨模型。
- 处置：两轮报告均明确 provisional；可以开 issue/拒绝，但不能作为终审放行。

### F18 — Live test 与 `--json` 输出契约漂移

- 现象：真实 Codex 已成功完成任务，但旧测试仍要求交互模式的
  `OpenAI Codex` banner，因此把可用后端错误标成 SKIP。
- 根因：runner 已切换为 `codex exec --json`；此模式的健康证据是结构化
  `thread.started` / `turn.completed` 事件和独立 final 文件，而非交互横幅。
- 处置：测试先用 `codex --version` 防伪，再解析 JSONL 事件，并在 final 文件
  校验答案。真实本地 Codex 最小端到端复测通过。

### F19 — 本地跑出了产物，但 Git 提交中会消失

- 现象：`.gitignore` 按模板仓库口径忽略 `workspace/library`、图、idea、draft
  等运行产物；本机文件完整存在，但直接 `git add` 不会进入公开仓库。
- 风险：GitHub 看起来只剩 Agent 框架，评审无法取得本次 LLZO 结果与证据包。
- 处置建议：正式定稿后把允许公开的文献子集、survey、figure、引用审计、
  retro 原始输出与必要 runtime traces 导出到受版本控制的 release 目录，生成
  `MANIFEST.json` 和 SHA256；不要简单取消忽略后把私有全文或全部开发轨迹提交。

## 4. 仍需人类确认/外部条件

1. 贡献选择：`A`（工艺链）、`A+B`（加可比性）、`A+C`（加复现问题图谱）
   或 `A+B+C`。推荐 `A+B+C`，但把 taxonomy 改为三分面而非声称单树 MECE。
2. 是否把 standard 诊断档升级为 comprehensive：当前 46 篇；正式综述规则是
   100–150 篇、每子主题≥15、综述≥8、近三年≥30%。
3. 材料化学负责人核对 `LiHO`/`La(HO)3`，审批试剂、化学计量、热处理、
   安全与废弃物处理后，才可补实验条件。
4. 安装 draw.io Desktop CLI 以完成 drawio 官方 PNG/PDF 导出。
5. 终审换独立模型；当前 reviewer 结论只能作为开发诊断。
6. 正式发布前执行受控导出；当前 `workspace/` 诊断产物默认不进入 Git。

## 5. 验证

- 离线测试：37 passed。
- runner 实调度子集：18 passed。
- retro/MCP 关键 live 子集：11 passed。
- loop live 全量：48 passed / 1 skipped；跳过项仅为本机未安装 Claude CLI，
  真实 Codex 端到端用例通过。
- Ref-Guard：46/46 PASS。
- Taxonomy mechanical validation：14 叶、46 key、每叶 4–7，PASS。
- I2/I3 冷启动复审：0 blocker/0 major/0 minor，verified；I1/I4 未复审且保持 open。
