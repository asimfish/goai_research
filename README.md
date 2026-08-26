# goai_research

多 agent 文献调研 → 综述论文流水线。检索、引用核查、画图（原生 draw.io
可编辑）、idea 生成（可接逆合成预测器）、写作、对抗审稿——全部接进一个
账本驱动的回环，支持并行执行与多轮迭代。宿主可以是 Codex CLI、
Claude Code 或 Cursor。

## 能干什么

给一个研究主题，系统走完整条链：

1. **goai-lit-search** 五源检索（arXiv/OpenAlex/Semantic Scholar/Crossref/DBLP）
   + 引文滚雪球，覆盖率闸门把关，下载 PDF、导出 BibTeX；
2. **goai-ref-guard** 逐条核对引用的标题/作者/顺序/年份/venue，
   快速档走注册库比对，深度档可接 [super_ref](https://github.com/asimfish/super_ref)
   证据审计；零虚假引用进稿；
3. **goai-survey-writer** 贡献先行（承 [PaperSpine](https://github.com/WUBING2023/PaperSpine)）
   + 五步流水线（承 [PaperOrchestra](https://github.com/Ar9av/PaperOrchestra)）：
   taxonomy → 引用支持库 → 蓝图 → 逐节写作 → 精修，claim 级引用绑定；
4. **goai-figure-studio / goai-figure-editable** figspec 单一事实源，
   一次渲染同时出论文 SVG 和 **draw.io 原生 .drawio 可编辑文件**；
   已有位图/SVG 也能重建成可编辑（承 [image-to-editable-ppt-skill](https://github.com/ningzimu/image-to-editable-ppt-skill)
   的重建-自检回环、[figure-studio-pro](https://github.com/asimfish/super_skill_team)
   的图纸方法论）；
5. **goai-idea-forge** 从文献缺口挖 idea，化学类可调逆合成预测器
   （ASKCOS/RXN 适配层）生成实验方案，对抗审核 + 引用二次查验双关；
6. **goai-reviewer** 跨模型对抗审稿（承 [ARIS](https://github.com/wanshuiyin/auto-claude-code-research-in-sleep)
   的执行者/审稿人分离），结构化 issue 写回账本自动路由返工；
7. **goai-orchestrator** 状态机总控：闸门、并行分派、轮次推进、终止判定。

![GoAI Research pipeline](examples/pipeline.png)

上图本身就是本系统画的：`examples/pipeline.figspec.json` 一份源文件，
同时渲染出 `pipeline.svg`（论文用）、`pipeline.drawio`（draw.io 直接编辑）
和 `pipeline.png`（自检预览）。

## 安装

```bash
git clone https://github.com/<you>/goai_research && cd goai_research
bash install.sh          # 建 .venv、装依赖、生成填好绝对路径的 MCP 配置
```

要求：Python ≥3.10（install.sh 会用 [uv](https://github.com/astral-sh/uv)
自动拉，没有 uv 则用系统 python3）。可选增强：
`brew install --cask drawio`（drawio CLI 导出 png/pdf）、
`pip install '.[preview]'`（cairosvg 出 png 供图纸自检）、Node.js（draw.io 官方 MCP）。

### 接入 Codex

```bash
cat configs/codex.config.toml >> ~/.codex/config.toml   # install.sh 生成的填好路径版
ln -s "$PWD/skills"/goai-* ~/.codex/skills/             # 技能桥接
```

### 接入 Claude Code / Cursor

MCP：把 `configs/claude.mcp.json` 内容合进 `~/.claude.json` 的 `mcpServers`
（或 Cursor 的 `mcp.json`）。技能：`ln -s "$PWD/skills"/goai-* ~/.claude/skills/`。

## 用法

对宿主 agent 说：

```
用 goai-orchestrator 跑一篇综述：主题「diffusion models for molecule
generation」，侧重 2022 年后，目标 25 页，先给我 scope.md 确认。
```

或手动分步调用单个环节：

```
用 goai-lit-search 检索 "LLM agents for robotics"，覆盖率报告给我
用 goai-ref-guard 核查 workspace/library/references.bib
用 goai-figure-studio 把 taxonomy.md 画成主图
把 figures/old_diagram.png 用 goai-figure-editable 转成 drawio
```

产物全部落在 `workspace/`：

```
workspace/
├── library/     papers.jsonl + references.bib + pdfs/
├── notes/       scope / taxonomy / citation_bank / figure_plan
├── figures/     svg/ + drawio/ + figspec/   ← 三格式同源
├── drafts/      blueprint + sections/*.tex + revision_log
├── ideas/       proposal_*.md + experiment_*.json + review_log
└── state/       ledger.json（回环账本）+ 审计报告
```

## 仓库结构

```
skills/     8 个 SKILL.md —— agent 的方法论（宿主模型执行认知活）
server/     4 个 FastMCP server —— 确定性能力（检索/核查/渲染/逆合成）
tools/      loopctl 账本 CLI · bib_guard 引用闸门 · parallel_run 并行 runner
configs/    Codex / Claude MCP 配置示例
templates/  综述 LaTeX 主模板
docs/       ARCHITECTURE.md · LOOP_PROTOCOL.md
```

设计详解见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)，
回环协议（闸门/issue 路由/终止条件/并行规约）见
[docs/LOOP_PROTOCOL.md](docs/LOOP_PROTOCOL.md)。

## 逆合成后端

默认 `stub`（演示流程用，输出带明确标注，禁止当化学结论）。接真实预测器：

```bash
export GOAI_RETRO_PROVIDER=http
export GOAI_RETRO_URL=https://your-askcos-instance/api/retro
export GOAI_RETRO_TOKEN=...   # 可选
```

适配层在 `server/core/retro.py`，改 `_predict_http` 的 payload 映射即可
对接 ASKCOS / IBM RXN / 自建服务。

## 测试

```bash
.venv/bin/python -m pytest tests/ -q     # 离线单测（渲染/解析/比对/账本）
```

## 致谢

设计参考：[super_ref](https://github.com/asimfish/super_ref)、
[ARIS](https://github.com/wanshuiyin/auto-claude-code-research-in-sleep)、
[PaperOrchestra](https://github.com/Ar9av/PaperOrchestra)、
[PaperSpine](https://github.com/WUBING2023/PaperSpine)、
[super_skill_team](https://github.com/asimfish/super_skill_team)、
[image-to-editable-ppt-skill](https://github.com/ningzimu/image-to-editable-ppt-skill)、
[drawio 官方 MCP](https://github.com/jgraph/drawio-mcp)。

MIT License.
