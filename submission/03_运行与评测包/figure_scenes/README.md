# 图件重建源（第五轮，两篇报告共用）

**这里是十张图的唯一事实源。** 导出的 `figures/pdf/*.pdf`、`*.pptx`、`*.svg` 都是产物，
改图请改这里重生成，**不要直接改导出件**。

| 文件 | 作用 |
|---|---|
| `scenes_r5.py` | 五张中文图的重建（BYZSO 图 1/2/3、BaZn2Si2O7 路线图/分类框架） |
| `r5_en.py` | 英文版：把中文场景的字串整体映射为英文并重排字号，几何与层级不变 |

设计系统在 `skills/goai-figure-studio/`（`lib/` 四级层次与 36 个原生图元、
`references/ink-budget.md` 墨量表、`references/pitfalls.md` 已知误报）。

## 重生成

```bash
export GOAI_FIGSTUDIO_JOBS=<写 scene.json 的目录>      # 不设则用默认工作树
python3 scenes_r5.py                                   # 五张中文
python3 r5_en.py                                       # 五张英文（缺译会退出 1）

python3 ../../../skills/goai-figure-studio/scripts/precheck.py "$GOAI_FIGSTUDIO_JOBS"/*/scene.json
img2ppt.sh build <scene.json> --out build/
python3 ../../../skills/goai-figure-studio/scripts/install_fig.py --crop render --margin 14 …
```

## 改中文标签之后必须做的事

英文表是按**中文原文**做键的，改了中文标签而不同步它，英文版就再也生成不出来
（2026-09-14 实际发生过：排版线按术语表改了 15 处，英文表没跟上，13 条字串缺译，
数天后审计别的东西时才偶然发现）。所以改完跑：

```bash
python3 ../../../skills/goai-figure-studio/scripts/check_i18n.py \
    --tr r5_en.py "$GOAI_FIGSTUDIO_JOBS"/{fig01_r5,fig02_r5,fig03_r5,bzso_roadmap_r5,bzso_taxonomy_r5}/scene.json
```

覆盖不全会逐条列出并退出 1。

## 图内用词

必须与正文术语表一致（`templates/glossary_materials_zh.json`）。排版线的
`tools/layout_guard.py` D2 会把图件 PDF 的文字抽出来逐条比对 —— **对不上是改这里，不是改正文。**
