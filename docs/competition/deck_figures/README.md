# 答辩 PPT · 「多智能体并行回环」两页图

世界人工智能开源大赛答辩模板（16:9）里讲文献系统多智能体并行回环的两页。**现行版本是第二轮**
（`deck_loop_parallel_r2/`、`deck_loop_converge_r2/`）；第一轮（`deck_loop_parallel/`、`deck_loop_converge/`、`studio/`）
被作者否掉（"质量太低，没有顶会的质感"），留作带完整路由表/闸门判据的备份页。

| 页 | 讲什么 | 目录 |
|---|---|---|
| 1/2 账本状态机与并行分派 | 论断"完成与否由程序判定，不由模型自报"；三相位（立项取证 / 并行生产 / 对抗审稿与交付）、两处分叉、编排器分派、九枚闸门的账本轨、KPI 条 | `deck_loop_parallel_r2/` |
| 2/2 互搏通道与机械闸门 | 论断"模型说了不算：检查不过即返工"；2×2 互搏卡、issue 路由 → 级联失效 → 橙色大回环、绿色机械放行、红色升级人类、四张轮次卡 4 → 7 → 0 → = 0 | `deck_loop_converge_r2/` |

每个目录：`*_editable.pptx`（整页 960×540 pt；文字/卡片/色带/箭头/轮次卡全是原生对象，角色与小插画是独立图片）、
`*.svg`、`*.pdf`、`*_render.png`、`slide_in_deck.png`（合入模板后的整页渲染）、`scene.json`、img2ppt 记录。
共用素材在 `art/`（24 个透明底 PNG）。

## 第二轮怎么做的（以及为什么）

参考 `wanshuiyin/auto-claude-code-research-in-sleep`（ARIS）的 `/method-figure`：

1. **brief，不是白名单**：每页 ≤14 个组件、每个"标题 + 一句话"，一个论断 + 一个数字；细节交给讲者。
2. **角色表**（`studio_r2/deck_cast`）：研究者 / 编排器 / 执行者 / 审稿人，两页共用；确定性工具（loopctl、守卫、check-done）画成图标，不画成角色。
3. **S2 八张候选**（Codex `image_gen`）：表面风格达标，但每张都有拓扑错误（并行画成串行、卡片换组、回环起止点错）——记在 `S3-direction-select/`。
4. **条件线框锁语义**：用 `figure_scenes/deckstyle.py` 的原生构件画出语义正确、文字到位的线框（`S4-candidate-brief/condition.jpg`），
   S5 让生图模型"照它出图，只提升质感"——四张 bake 全部忠实复现了版式。
5. **素材表**（`deck_assets_a/b`）：无文字的角色/小插画网格，`crop_assets.py` 按墨迹空白带切格、去掉与边相连的白底。
6. **可编辑页 = 线框 + 素材**：`scenes_deck_r2.py --art art/`，img2ppt 构建，`skills/goai-figure-studio/scripts/deck_merge.py` 1:1 合入模板（图片一并带入）。

证据锚点与第一轮相同：`docs/LOOP_PROTOCOL.md`、`docs/ARCHITECTURE.md`、`skills/goai-orchestrator/SKILL.md`、`tools/parallel_run.sh`、
`docs/competition/FINAL_REPORT.md §3`、正式运行的 `RUN_MANIFEST.json` / `ledger.json`
（29 批 · 40 个子任务 · 单批 ≤4 路 · 134 次工具调用；生产阶段闸门拦下 4 项、第 1 轮审稿 7 项、第 2 轮 0 项、check-done = 0）。

## 重生成

```bash
J=/tmp/deckjobs
GOAI_FIGSTUDIO_JOBS=$J python3 submission/03_运行与评测包/figure_scenes/scenes_deck_r2.py all --art docs/competition/deck_figures/art
for j in deck_loop_parallel_r2 deck_loop_converge_r2; do mkdir -p $J/$j/art && cp docs/competition/deck_figures/art/*.png $J/$j/art/; done
python3 skills/goai-figure-studio/scripts/precheck.py $J/*/scene.json            # 0 hard
img2ppt.sh build $J/deck_loop_parallel_r2/scene.json --out build1/               # 渲染主机
python3 skills/goai-figure-studio/scripts/deck_merge.py --deck 模板.pptx --out 带新页.pptx --font 微软雅黑 --after 9 \
    "build1/editable.pptx::多智能体并行回环 1/2：账本状态机与并行分派" "build2/editable.pptx::多智能体并行回环 2/2：互搏通道与机械闸门"
```

不带 `--art` 生成的就是条件线框（插画位是虚线圆）。`deck_r2.py` / `deck_r2_s345.py` 生成 brief、角色表与 S2/S5/素材表的提示词包。
