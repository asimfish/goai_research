# 答辩 PPT · 「多智能体并行回环」两页图

世界人工智能开源大赛答辩模板（16:9）里讲文献系统多智能体并行回环的两页，按 `skills/goai-figure-studio`
的流程做：策略合同（S0/S1）→ 设计系统原生重建（scene.json）→ super_img2ppt 出可编辑件 → 1:1 合入模板。

| 页 | 讲什么 | S1 选定版式 | 目录 |
|---|---|---|---|
| 1/2 账本状态机与并行分派 | 七个专职 agent 怎样被账本按阶段分派、两处分叉并行、闸门落账 | SC4 账本为轴 | `deck_loop_parallel/` |
| 2/2 互搏通道与机械闸门 | 四条互搏通道挑错、issue 经路由表回责任阶段、级联失效、check-done 机械放行、三条终止旁路 | SC2 单主干闭环 | `deck_loop_converge/` |

每个目录：`*_editable.pptx`（整页 960×540 pt，PowerPoint/WPS 直接改）、`*.svg`、`*.pdf`（矢量）、
`*_render.png`（LibreOffice 渲染）、`slide_in_deck.png`（合入模板后的整页渲染）、`scene.json`（单一事实源）、
`validation.json` / `fonts.json`（img2ppt 记录）。

## 证据锚点

图上每个模块和连线都对应系统自己的规范：`docs/LOOP_PROTOCOL.md`、`docs/ARCHITECTURE.md`、
`skills/goai-orchestrator/SKILL.md`、`tools/parallel_run.sh`、`docs/competition/FINAL_REPORT.md §3`，
以及正式运行记录 `submission/03_运行与评测包/正式案例_BYZSO冷启动/{RUN_MANIFEST.json,ledger.json}`
（29 批 / 40 个子任务 / 单批最多 4 路 / 134 次 MCP 调用；2 轮收敛、11 个 issue 全部关闭）。
逐条对照见 `studio/<project>/outputs/S0-paper-foundation/paper-foundation-report.md`。

## 重生成

```bash
# 场景（字号按幻灯片 pt：分组 16 / 标题 14 / 正文 12 / 标签 11）
GOAI_FIGSTUDIO_JOBS=/tmp/deckjobs python3 submission/03_运行与评测包/figure_scenes/scenes_deck.py all
python3 skills/goai-figure-studio/scripts/precheck.py /tmp/deckjobs/*/scene.json          # 0 hard
img2ppt.sh build /tmp/deckjobs/deck_loop_parallel/scene.json --out build/                 # 渲染主机
# 合入模板：1536×864 画布 = 960×540 pt 整页，形状 1:1 复制到「比较」版式的新页上，标题栏沿用模板
python3 skills/goai-figure-studio/scripts/deck_merge.py --deck 模板.pptx --out 带新页.pptx --font 微软雅黑 --after 9 \
    "build/editable.pptx::多智能体并行回环 1/2：账本状态机与并行分派" ...
```

`deck_s01.py` 重写 S0/S1 记录与 S2 提示词包（`studio/`）。

## 生图候选（S2–S5）的状态

2026-09-17 两条生图通道都不可用：5090 的 Codex 登录被服务端作废（`token_revoked` /
`refresh_token_invalidated`，需重新 `codex login`），工作站的 Codex 身份有效但 Pro 用量额度耗尽
（`usage_limit_reached`，2026-09-19 06:50Z 恢复）。按 SKILL.md 的降级路径：S0/S1 与 S2 提示词包已就绪
（`studio/<project>/outputs/S2-sketch-explore/`），先按 S1 最高分版式做原生重建交付；通道恢复后
`final_round/figstudio/tools/run_deck_s2_local.sh` 补跑 S2，再走 S3–S5，若选出的方向不同则重排。
