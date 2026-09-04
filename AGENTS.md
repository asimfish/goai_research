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
- 并行派活：`bash tools/parallel_run.sh --backend codex --jobs 3 tasks.tsv`；
  TSV 第三列填预期产物，第四列填前序依赖。超时但产物验收通过时保留
  `.process_exit=124`，有效状态记 WARN，不再误判为内容失败。
- 回环协议细节（阶段/闸门/路由表/终止条件）：`docs/LOOP_PROTOCOL.md`。
