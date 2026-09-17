# SAGE-Mat 宣传封面

`SAGE-Mat_cover_2880x1620.png`（2×，投放/印刷用）与 `SAGE-Mat_cover_1440x810.png`（1×）。源文件是 `cover.html`，改字直接改 HTML 再重渲染。

版式参照作者给的样例封面（左：中英文标题 + 深色主张条 + 事实行 + 流程条；右：三张特性卡 + 笔记本里的真实页面；底部公式与署名），
视觉取自项目站点 goai-dashboard：浅灰蓝底 `#F1F4F7`、白卡、Chakra Petch / IBM Plex / Noto Sans SC、青 `#1E8FA8` 与橙 `#E06A1B` 强调色。
流程条用答辩 PPT 第 10、11 页同一套化学小插画（`docs/competition/deck_figures/art/`）。

## 封面上的每个数字的出处

| 封面文字 | 出处 |
|---|---|
| 51/51 篇参考文献逐条核验 · 219 次引用、整合率 100% | `docs/competition/FINAL_REPORT.md` §1.3；正式案例 `ledger.json` 的 `ref_integrity` |
| 9 道程序化闸门 | `docs/LOOP_PROTOCOL.md`；FINAL_REPORT §1.3「九道流程闸门」 |
| RECIPE Combo@1 71.81 | FINAL_REPORT §1.3（2,558 条留出测试反应；Combo@20 89.21，MRR 77.48） |
| 5 条实验工作流 · 158 个机器人原语（仿真） | 站点 `showcase.html` 页首统计（Isaac Sim 数字孪生，非实体实验） |
| 屏幕标注：三站内容、零穿模 | 站点 `scenes.html`（布局 v4 接触分离审计）、`final_round/05_alab_twin.md` |
| 5 SOURCES | arXiv / OpenAlex / Crossref / Semantic Scholar / DBLP 五源检索 |
| 案例 | BYZSO 正式案例、BaZn₂Si₂O₇ 补充案例、LLZO 诊断轮 |
| 署名 | FINAL_REPORT 题注：AI for Research 赛道 · 算法赛 · 材料科学 · 第 13 队 科学无极 |

笔记本屏幕是 A-Lab 数字孪生的 Isaac Sim RTX 全景渲染（`scene.jpg` = 站点 `scenes.html` 的「全景（六门全开）」，`final_round/showcase/media/alab_twin_v4/rtx/open_overview_1.png`），作者要求换成"最好看、最真实的场景"。屏幕上的标注全部来自 `scenes.html` 与 `final_round/05_alab_twin.md`：A 站配料与干燥、B 站四台马弗炉 + 导轨 UR5e、C 站 XRD 与粉体回收；「PhysX 接触审计 · 零穿模」= 布局 v4 的接触分离审计（67 对接触，器材间最小分离为正）。它是仿真渲染，不是实验室照片，屏幕左上角标了 ISAAC SIM · RTX RENDER。

## 重渲染

```bash
google-chrome --headless=new --no-sandbox --hide-scrollbars --force-device-scale-factor=2 --window-size=1440,810 \
  --virtual-time-budget=12000 --screenshot=SAGE-Mat_cover_2880x1620.png file://$PWD/cover.html
```

字体走 Google Fonts（Chakra Petch、IBM Plex Sans/Mono、Noto Sans SC 900）；离线环境需要先装这几套字体，否则标题会退回到常规字重。
