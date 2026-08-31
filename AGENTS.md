# AGENTS.md —— 宿主 agent 工作守则

你在 goai_research 仓库里工作。这是一套「文献调研 → 综述论文」的
多 agent 流水线；你按下面的规则扮演其中的 agent。

## 快速路由

| 用户意图 | 读哪个 skill |
|---|---|
| 跑整条综述流水线 / 继续上次的活 | `skills/goai-orchestrator/SKILL.md` |
| 检索文献、下载 PDF、导 BibTeX | `skills/goai-lit-search/SKILL.md` |
| 核查引用真伪/作者/顺序 | `skills/goai-ref-guard/SKILL.md` |
| 画论文图 / taxonomy 图 | `skills/goai-figure-studio/SKILL.md` |
| 学经典综述风格建风格库 | `skills/goai-style-bank/SKILL.md` |
| 把现成图转 drawio 可编辑 | `skills/goai-figure-editable/SKILL.md` |
| 写综述 / 建 taxonomy / 组稿 | `skills/goai-survey-writer/SKILL.md` |
| 生成 idea / 实验方案 / 逆合成 | `skills/goai-idea-forge/SKILL.md` |
| 审稿 / 挑毛病 | `skills/goai-reviewer/SKILL.md` |

**先读对应 SKILL.md 再动手**；被 parallel_run 以子任务派活时，提示词里
指明的那个 skill 就是你的全部职责边界，别越界碰公共文件。

## 铁律（所有角色通用）

1. **账本是唯一状态源**：开工先 `python3 tools/loopctl.py status`，
   收工必须 `loopctl log`；闸门/issue 只通过 loopctl 读写。
2. **引用零信任**：只引用 `workspace/library/references.bib` 里
   已过 ref_gate 的 key；任何场合禁止手编 BibTeX 条目、禁止凭记忆写引用。
3. **产物落盘**：一切结论写进 workspace/ 对应目录，不许只留在对话里。
4. **图必须双格式**：交付图 = svg + drawio 同源产出（figspec 渲染），
   位图不算交付物。
5. **stub 逆合成 ≠ 化学结论**：出现在任何文档里必须带演示标注。
6. **审稿独立**：执行者不自审；reviewer 不动稿。
7. 卡住三次就升级人类，不空转。
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

## 环境速查

- venv：`.venv/bin/python`（install.sh 建）；所有验证均使用它，不用系统
  `python3`。统一预检：`tools/check.sh --servers`，另可加 `--corpus`/`--retro`。
- 离线测试：`.venv/bin/python -m pytest tests/ -q`。
- 引用一致性闸门：`python3 tools/bib_guard.py workspace/drafts/sections workspace/library/references.bib`；
  组稿完整性闸门：`python3 tools/tex_guard.py workspace/drafts`。
- 并行派活：`bash tools/parallel_run.sh --backend codex --jobs 3 tasks.tsv`；
  TSV 第三列填预期产物，第四列填前序依赖。超时但产物验收通过时保留
  `.process_exit=124`，有效状态记 WARN，不再误判为内容失败。
- 回环协议细节（阶段/闸门/路由表/终止条件）：`docs/LOOP_PROTOCOL.md`。
