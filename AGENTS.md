# AGENTS.md —— 宿主 agent 工作守则

你在 goai_research 仓库里工作。这是一套「文献调研 → 综述论文」的
多 agent 流水线；你按下面的规则扮演其中的 agent。

## 快速路由

| 用户意图 | 读哪个 skill |
|---|---|
| 跑整条综述流水线 / 继续上次的活 / **只给了一个研究主题** | `skills/goai-orchestrator/SKILL.md` |
| 检索文献、下载 PDF、导 BibTeX | `skills/goai-lit-search/SKILL.md` |
| 核查引用真伪/作者/顺序 | `skills/goai-ref-guard/SKILL.md` |
| 画论文图 / taxonomy 图 | `skills/goai-figure-studio/SKILL.md` |
| 学经典综述风格建风格库 | `skills/goai-style-bank/SKILL.md` |
| 把现成图转 drawio 可编辑 | `skills/goai-figure-editable/SKILL.md` |
| 写综述 / 建 taxonomy / 组稿 | `skills/goai-survey-writer/SKILL.md` |
| 生成 idea / 实验方案 / 逆合成 | `skills/goai-idea-forge/SKILL.md` |
| 审稿 / 挑毛病 | `skills/goai-reviewer/SKILL.md` |

当用户只给出一个研究主题、没有显式限定为检索/引用/制图/写作等单阶段任务时，
默认视为“从零运行整条综述流水线”，读取 `skills/goai-orchestrator/SKILL.md`。
不要把裸主题降级成单独的文献检索任务；最终交付必须包含综述源码与 PDF。

**先读对应 SKILL.md 再动手**；被 parallel_run 以子任务派活时，提示词里
指明的那个 skill 就是你的全部职责边界，别越界碰公共文件。

**裸主题默认全流程**：用户输入只包含一个研究主题（如「调研主题：XXX」
「survey on XXX」），没有明确限定「只检索 / 只画图 / 只核引用」时，一律
按「跑整条综述流水线」处理，进入 goai-orchestrator 走完整个状态机；
最终交付硬性包含 `workspace/drafts/` 下的 tex+pdf。「没说只要检索」不等于
「只要检索」——禁止把裸主题降级成单纯文献检索或一份 Markdown 报告了事。

## 铁律（所有角色通用）

1. **账本是唯一状态源**：开工先 `python3 tools/loopctl.py status`，
   收工必须 `loopctl log --stage <阶段> --event done`（并行子任务每路一条——它就是
   并发证据，gate 记 PASS 时会数）；闸门/issue 只通过 loopctl 读写。loopctl 会拒绝
   跳阶段、缺并发证据、单轮审稿、无回执、非 TeX PDF 的 gate 写入，禁止绕过。
2. **引用零信任**：只引用 `workspace/library/references.bib` 里
   已过 ref_gate 的 key；任何场合禁止手编 BibTeX 条目、禁止凭记忆写引用。
3. **产物落盘**：一切结论写进 workspace/ 对应目录，不许只留在对话里。
4. **图必须双格式**：交付图 = svg + drawio 同源产出（figspec 渲染），
   位图不算交付物。
5. **stub 逆合成 ≠ 化学结论**：出现在任何文档里必须带演示标注。
6. **审稿独立**：执行者不自审；reviewer 不动稿。
7. 卡住三次就升级人类，不空转。例外：用户已经明确要求无人值守完成整条流水线时，
   对 ref_gate 中仅剩的非核心背景条目，若目标论文和支撑核心结论的条目均已 PASS，
   应保守删除仍为 MISMATCH/UNVERIFIED 的背景条目及其对应论述，再重跑闸门；
   只有核心条目仍不通过或删除会改变研究结论时才暂停请求人工决定。
8. **有界读取**：不得用 `cat`/`nl`/裸 `sed` 整体打印 `papers.jsonl`、
   Agent `*.jsonl` 轨迹或 PDF 转出的全文。先用 `wc`/结构化脚本统计，再只取
   所需字段、事件类型和小片段；单次命令输出应控制在 20 KB 内。
9. **检索预算**：`grep_local_corpus` 默认 `max_results<=10`、
   `context_lines<=1`；除非任务明确要求扩展，不得对近义词反复无差别检索。
10. **产物验收**：后端 `exit=0` 只代表会话结束。并行任务必须在 TSV
    第三列声明关键非空产物；默认还要求产物在本轮更新，由 runner 缺失、
    为空或沿用旧文件时改判失败（只查既有文件用 `=path`）。
11. **长任务增量落盘**：每完成一个可独立验收的阶段就更新第三列产物；不得
    等最终回复才首次写文件。不得读取当前 run_id 正在增长的 JSONL/stderr，
    只有提示词明确指定的已关闭历史 run_id 才可作为诊断输入。
12. **依赖显式化**：TSV 第四列声明前序任务名（逗号分隔），并按拓扑顺序
    排列。数据/证据生产者未通过时，消费者由 runner 记为 blocked 而不启动。
13. **交付物只说读者语言**：agent 可以在账本和日志中使用 gate、ledger、
    field、tag、endpoint、normalization 等便于程序协作的词，但这些词不得原样
    出现在论文正文、摘要、标题、表格、图中文字或图注中。交付稿统一改用
    “文献依据、实验项目、结构关系、合成条件、表征方法、可外推范围”等学科
    表达；组稿后必须运行 `tools/academic_language_guard.py`。裸 BibTeX key
    同样不得进入读者可见文本（`tex_guard` 直接阻塞）。交付语言以 scope.md
    为准，中文稿用 `templates/survey_main_zh.tex`，禁止套英文模板。
14. **图纸美学是闸门**：`render_figure` 对配色 ≥4 色系、彩虹泳道、越界直接
    拒绝；其余美学告警（近失对齐、尺寸漂移、间距、连线穿节点、描边档数…）
    要么改 figspec 消掉，要么在 figure_plan.md 逐条写明保留理由，否则不得置
    `figures_ready`。
15. **PDF 只能由 TeX 从模板编译，缺环境就 fail-closed**：开工先
    `tools/check.sh --tex`；没有 xelatex/pdflatex 或模板宏包时，`draft_complete`
    记 FAIL + issue「环境缺 TeX」，交付 main.tex + references.bib + figures 并在
    终报明写「PDF 未编译」。**禁止**用 groff/Ghostscript、HTML→Chrome、Word、
    pandoc 等回退渲染器生成 PDF 冒充终稿（实跑中发生过：摘要/编号/公式/表格/
    蓝色引用全部走样而账本记 PASS）。编译后必须过 `tools/pdf_guard.py`
    （Producer/字体/时效/摘要/编号五项）——`loopctl gate draft_complete PASS` 会自动
    调用它，不带 PDF 或不过闸直接拒绝；`check-done` 再核一遍。
16. **goai 工具走 MCP，先 `tool_search` 再说「没有」**：Codex 宿主把 MCP 工具
    **延迟加载**（`tool_search_always_defer_mcp_tools` 已固化为默认，不可关闭）——
    开场工具清单里看不到 goai-* 不等于没挂。先 `tool_search` 搜 `goai-litsearch` /
    `goai-refcheck` / `goai-figure` / `goai-retro`（或具体工具名），拿到后经 MCP
    调用：事件流留 `mcp_tool_call`，服务端审计 `state/tool_calls.jsonl` 自动带
    `run_id=<批次>/<任务>`，网络请求由 server 进程发出、不受 shell 沙箱限制。
    `tool_search` 一次只返回与查询匹配的若干工具——搜到 `search_papers` 不代表
    `save_to_library` / `export_bibtex` 也在手边，需要哪个就按工具名再搜一次，
    不要因为「清单里没看到」就退回 shell 直调（09-06 实测：编排器搜到检索工具后
    误以为「没有入库接口」）。
    正式运行实测：子 agent 拿到了 profile 却没有搜索，判定「工具未暴露」后改用
    `.venv/bin/python -c "from server.xxx_server import 工具"` 直调 105 次、MCP 0 次，
    134 条审计无法归因，`workspace-write` 沙箱下直调还全部断网。只有 tool_search
    也搜不到（派活方没传 profile，RUN_INFO.json 会记 `mcp_warning`）才允许直调兜底，
    并 `loopctl log --event decision` 记录降级；同一份审计包装仍会留痕。
    单条命令输出仍受铁律 8 的 20 KB 上限：编译/大检索/内嵌 `codex exec` 一律
    重定向到文件后只 `tail`，不要把整段日志灌进上下文（实测 61 条命令输出超限，
    最大 950 KB，是 40% 子任务撞 RUNNER_TIMEOUT 的主因之一）。

## 环境速查

- venv：`.venv/bin/python`（install.sh 建）；所有验证均使用它，不用系统
  `python3`。统一预检：`tools/check.sh --servers`，另可加 `--corpus`/`--retro`/
  `--tex`（TeX 工具链与模板宏包，进入 writing 前必跑）。
- 离线测试：`.venv/bin/python -m pytest tests/ -q`。
- 引用一致性闸门：`python3 tools/bib_guard.py workspace/drafts/sections workspace/library/references.bib`；
  组稿完整性闸门：`python3 tools/tex_guard.py workspace/drafts`；
  终稿 PDF 来源闸门：`python3 tools/pdf_guard.py workspace/drafts/main.pdf --tex workspace/drafts/main.tex --bib workspace/library/references.bib`；
  排版修补：`tools/bib_polish.py <bib> --write`（bib 卫生）、`tools/tex_polish.py <drafts> --write`（可断斜杠/路径归一）；
  一键编译 + 闸门：`bash scripts/build_tex.sh workspace/drafts`（无 TeX 即 fail-closed 退出）。
- 并行派活：`GOAI_CODEX_PROFILE=<profile> bash tools/parallel_run.sh --backend codex --jobs 3 tasks.tsv`
  （profile = `$CODEX_HOME/<profile>.config.toml`，含四个 goai MCP server 与
  `env_vars = ["GOAI_RUN_ID", "GOAI_TASK_NAME"]`，样例 `configs/codex.config.toml.example`；
  reproduce_core.sh 已自动设置）。TSV 第三列填预期产物，第四列填前序依赖。超时但产物
  验收通过时保留 `.process_exit=124`，有效状态记 WARN，不再误判为内容失败。
- **控制台（推荐）**：`python3 tools/console_server.py --port 5051 --codex-home ~/.codex_rev`
  → http://127.0.0.1:5051 ：角色说明（点开看完整 skill）、发起新研究主题 / 终止运行、历史工作区
  浏览与回放、按角色的实时观察（流程条 / 批次时间线 / 角色卡 / 闸门 / 审计归因）。前端在
  `tools/console/`（Vite + Vue 3 + Naive UI，构建产物已提交，服务端纯标准库），历史目录用
  `--workspace-glob` 挂入，私有语料用 `--private-corpus-env <KEY=VALUE 文件>`。
- **终端版**：`python3 tools/live_view.py --follow`（按角色着色的实时流）/ 不带参数快照 /
  `--serve 5051` 无需构建的单页看板；`--all` 回放历史批次，`GOAI_WORKSPACE` 或 `--workspace`
  指定工作区。两者都只读，不影响运行。
- 回环协议细节（阶段/闸门/路由表/终止条件）：`docs/LOOP_PROTOCOL.md`。
