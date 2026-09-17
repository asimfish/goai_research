# 答辩 PPT · 「多智能体并行闭环」两页图

世界人工智能开源大赛答辩模板（16:9）里讲文献系统多智能体并行闭环的两页。**现行版本是第三轮**
（`deck_loop_parallel_r3a/`、`deck_loop_parallel_r3b/`、`deck_loop_converge_r3/`）：图一有 A / B 两种构图待作者二选一。
第二轮（`*_r2/`，ARIS 粉彩配色）因"与整套 PPT 的风格、化学流程、用词不统一"被取代；第一轮（`deck_loop_parallel/`、
`deck_loop_converge/`、`studio/`）因"没有顶会的质感"被否，留作带完整路由表/闸门判据的备份页。

## 第三轮（现行）

| 页 | 讲什么 | 目录 |
|---|---|---|
| 1/2 · 构图 A | S2 候选 C01：三条横向相位带（文献取证 / 并行生产 / 评审放行），编排器在左侧分派，运行账本九道闸门 + KPI 在下；橙色返修回路从「裁决」绕过右侧回到并行生产带 | `deck_loop_parallel_r3a/` |
| 1/2 · 构图 B | S2 候选 C03：编排器 + 运行账本居中，三个相位顺时针成环（上：1→2，右下弧：2→3，左下橙色弧：定向返修），轮辐 = 任务分派（出）/ 记录入账（入） | `deck_loop_parallel_r3b/` |
| 2/2 | 交叉核验（四条通道）→ 问题路由与返修（意见路由 → 级联失效 → 橙色大回路）→ 程序化放行；一条真实问题 I5 + 四张轮次卡 | `deck_loop_converge_r3/` |

本轮改了三件事：

1. **与 PPT 统一**：`deckstyle.use_theme('sagemat')` 把色板换成模板自己的颜色（标题条 #154A97、数字 #156082、橙 #E97132、
   状态色 #DC3C3C / #F59E0B / #10B981、面板底 #E6ECF5），KPI / 轮次卡照第 12 页的数字卡样式（浅色卡 + 顶部色条 + 大数字），
   页首论断放进模板的深蓝条，图例改成一行；合入模板时字体统一为微软雅黑。
2. **落到化学流程上**：卡片内容换成正式案例（Ba₅Y₁₂Zn[O(SiO₄)]₈ 冷启动）的真实环节——体系界定（目标相与近邻 · 相图与热力学）→
   五源 + 本地全文库检索 → 引用核验 51/51 → 证据分类（路线 × 条件 × 表征，合成条件表）→ 图表 ∥ 撰写 ∥ 合成方案构想
   （RECIPE 前驱体预测：BaCO₃ · Y₂O₃ · ZnO · SiO₂）→ 三视角评审 → 交付（综述 PDF + 合成方案 → OpenLab 工作流）。
   新增 12 个化学小插画（`studio_r3/deck_assets_c`：文献库、晶体结构、相图、条件表、前驱体、RECIPE 排序、箱式炉、助熔剂生长、XRD、工作流、机械臂工作站、合成方案）。
3. **用词**：互搏挑错 → 交叉核验；路由返工 → 问题路由与（定向）返修；机械放行 → 程序化放行；升级人类 → 转人工裁决；
   落账 → 记录入账；分派 → 任务分派；风格库 → 综述范式库；分类法 → 证据分类；图件 → 图表制作；"模型说了不算" → "完成判定由程序执行，而非模型自述"。

**数字逐项对过 `正式案例_BYZSO冷启动/ledger.json`**：问题共 11 项 = 生产阶段 4（I1–I4：3 blocker + 1 major）+ 第 1 轮评审 5
（I5–I9：1 blocker + 3 major + 1 minor）+ 第 2 轮终审 2（I10–I11：minor，当轮关闭）；终判 0 / 0 / 0。第二轮页面写的"第 1 轮 7 项 → 第 2 轮 0 项"
把 I10、I11 误算进了第 1 轮，本轮已更正。九道闸门的真实状态是 PASS 6 · WARN 3（文献覆盖、范式库、方案评审为显式入账的降级），页面如实画出。
实例 I5：合成条件表把原文的固相合成误标为熔体法 → 路由到写作阶段 → 逐字段回核实验段后重建条件表，第 2 轮关闭。

```bash
J=/tmp/deckjobs
GOAI_FIGSTUDIO_JOBS=$J python3 submission/03_运行与评测包/figure_scenes/scenes_deck_r3.py all --art docs/competition/deck_figures/art   # bands | ring | converge
python3 skills/goai-figure-studio/scripts/deck_merge.py --deck 模板.pptx --out 带新页.pptx --font 微软雅黑 --after 9 \
    "A/editable.pptx::多智能体并行闭环 1/2：运行账本与任务分派" "C/editable.pptx::多智能体并行闭环 2/2：交叉核验与程序化放行"
```

## 第二轮（已被取代）

| 页 | 讲什么 | 目录 |
|---|---|---|
| 1/2 账本状态机与并行分派 | 论断"完成与否由程序判定，不由模型自报"；三相位（立项取证 / 并行生产 / 对抗审稿与交付）、两处分叉、编排器分派、九枚闸门的账本轨、KPI 条 | `deck_loop_parallel_r2/` |
| 2/2 互搏通道与机械闸门 | 论断"模型说了不算：检查不过即返工"；2×2 互搏卡、issue 路由 → 级联失效 → 橙色大回环、绿色机械放行、红色升级人类、四张轮次卡 4 → 7 → 0 → = 0 | `deck_loop_converge_r2/` |

每个目录：`*_editable.pptx`（整页 960×540 pt；文字/卡片/色带/箭头/轮次卡全是原生对象，角色与小插画是独立图片）、
`*.svg`、`*.pdf`、`*_render.png`、`slide_in_deck.png`（合入模板后的整页渲染）、`scene.json`、img2ppt 记录。
共用素材在 `art/`（24 个透明底 PNG）。

### 第二轮怎么做的（以及为什么）

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

### 重生成（第二轮）

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
