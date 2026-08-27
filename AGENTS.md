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

## 环境速查

- venv：`.venv/bin/python`（install.sh 建）；MCP server 配置见 `configs/`。
- 离线测试：`.venv/bin/python -m pytest tests/ -q`。
- 引用一致性闸门：`python3 tools/bib_guard.py workspace/drafts/sections workspace/library/references.bib`；
  组稿完整性闸门：`python3 tools/tex_guard.py workspace/drafts`。
- 并行派活：`bash tools/parallel_run.sh --backend codex --jobs 3 tasks.tsv`。
- 回环协议细节（阶段/闸门/路由表/终止条件）：`docs/LOOP_PROTOCOL.md`。
