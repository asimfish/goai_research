# SAGE-Mat 宣传封面

两版只有笔记本屏幕里的孪生实验室视角不同，其余版面完全一致，作者选一版即可。每版都有 2×（`_2880x1620.png`，投放/印刷）与 1×（`_1440x810.png`）。

| 版本 | 源文件 | 屏幕 | 视角 |
|---|---|---|---|
| A | `cover_A.html` | `scene_A.jpg` | 配料站一角推近的全景：前景 FR3 与旋转托盘、天平、开门的干燥箱，后方四台马弗炉与导轨 UR5e，左侧 XRD 站 |
| B | `cover_B.html` | `scene_B.jpg` | XRD 站一角的反向全景：前景 UR5e 与工作站，右侧配料岛（托盘、FR3、干燥箱），远端马弗炉阵列与导轨 UR5e |

改字直接改 HTML 再重渲染（两版共用同一份文案，改动请同时改两份）。封面底部与浏览器地址栏不再放链接（作者要求）。

版式参照作者给的样例封面（左：中英文标题 + 深色主张条 + 事实行 + 流程条；右：三张特性卡 + 笔记本；底部公式与署名），
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

## 屏幕里的孪生实验室

屏幕是 A-Lab 数字孪生（布局 v4，与站点 `scenes.html` 同一场景与状态：六门全开、机械臂在初始位）在 Isaac Sim RTX 下的新渲染，
3000×2000 直出，比站点上 1280×800 的固定机位清晰得多。渲染脚本 `twin_hero_render.py` 放在 5090 的 `alab_twin/v4render/` 目录里用同目录的 `launch.sh`
运行（`bash launch.sh twin_hero_render.py`），只加相机、不改场景。两台相机（米，世界坐标；24 mm 水平底片，焦距 13 mm）：

| 版本 | 相机位置 | 视点 | 贴图裁切 |
|---|---|---|---|
| A | (3.5, 1.3, 2.3) | (−1.0, −2.0, 0.45) | 顶部去 80 px 天花板后按 3:2 居中裁切 |
| B | (3.9, −1.6, 2.7) | (−1.8, −0.2, 0.7) | 顶部去 160 px 后按 3:2 居中裁切 |

屏幕上的标注全部来自 `scenes.html` 与 `final_round/05_alab_twin.md`：A 站配料与干燥、B 站四台马弗炉 + 导轨 UR5e、C 站 XRD 与粉体回收；
「PhysX 接触审计 · 零穿模」= 布局 v4 的接触分离审计（67 对接触，器材间最小分离为正）。它是仿真渲染，不是实验室照片，屏幕左上角标了 ISAAC SIM · RTX RENDER。

## 重渲染

```bash
for v in A B; do
  google-chrome --headless=new --no-sandbox --hide-scrollbars --force-device-scale-factor=2 --window-size=1440,810 \
    --virtual-time-budget=12000 --screenshot=SAGE-Mat_cover_${v}_2880x1620.png file://$PWD/cover_$v.html
done
```

字体走 Google Fonts（Chakra Petch、IBM Plex Sans/Mono、Noto Sans SC 900）；离线环境需要先装这几套字体，否则标题会退回到常规字重。
