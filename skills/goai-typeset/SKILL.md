---
name: goai-typeset
description: Use when a manuscript must be typeset, re-typeset, or checked for layout before shipping — 排版 agent：manuscript 版式模板 + 化学写作词库 + 版面门禁 layout_guard，一条命令编四份（中英 × 两报告）并逐条判 FAIL/WARN。触发词：「排版」「版式」「题注」「版面」「overfull」「编译论文」「layout」「typeset」。
---

# GoAI Typeset —— 版面 agent

**这条线的教训是：版面问题过去全靠人一页页翻 PDF 看出来，没有一条是自动发现的。**
所以现在每一条返工都变成一次检查，人只看门禁报告。写排版代码前先读
`docs/layout_guard.md`（检查清单逐条对应一次真实返工）与 `docs/typo_templates.md`。

## 一条命令

```bash
tools/build_and_guard.sh [<本地构建树>]
```

编译在 5090 的 docker TeX Live 里做（本机没有 TeX），门禁在本机跑（只要 pdftotext + python3）。
两份报告 × 中英四份，编完立刻跑 `tools/layout_guard.py`，**有 FAIL 就不往下发布**。
5090 的 sshd 并发下会随机断开，脚本每一步都带重试 —— 别拆开手工跑。

## 门禁分层（完整清单在 docs/layout_guard.md）

| 层 | 管什么 |
|---|---|
| **A** | 编译健康：`^!` 错误、Overfull `\hbox` > 1pt、Overfull `\vbox`、缺文件、未定义引用、重复 label |
| **B** | 版心与页眉：题注一律顶左、文字不越出版心、每页有页眉页码 |
| **C** | 图表：`\includegraphics` 文件存在、**中文稿不引 `_en` 图 / 英文稿不引 `_zh` 图**、表浮到 `[bp]`、booktabs 无竖线无 `\hline`、表注在上图注在下、分数列宽合计为 1 |
| **D** | 用词：正文过 `tools/chemlib.py`（high 必须为 0）、**图件里的文字过同一套术语表** |
| **E** | 模板不被改回去：默认 `manuscript`、`singlelinecheck=false`、无裸 `\sloppy`、microtype、`\raggedbottom`、`bottomfraction ≥ 0.7` |

## 几个不要再翻案的决定

- **`\sloppy` 是观感变差的主因**，不是 microtype 没开。tolerance 9999 + emergencystretch 3em
  把词距放得很松，microtype 一直开着但被它抵消。改用 `emergencystretch=2em` + `tolerance=2000`。
  E3 就是防它被加回来的。
- **`singlelinecheck=false`**：开着时短题注居中、长题注左对齐，同一篇像两套规矩。题注一律顶左。
- **表格 `[t]` → `[bp]`，`bottomfraction` 0.4 → 0.78**：不够大时半页高的表落不到页底，会漂到正文之后。
- **编号标题回到纯数字**，只在加粗的 run-in 小标题前留一个 `\rule` 画的蓝色方块。
- 版式基准是用户指定的参照版 `pdf/bayznsio_phase_en_20260904.pdf`：11/13.6 pt 衬线正文、
  衬线粗体节标题、居中不加粗标题栏、article 式摘要、首行缩进段间 0、fancyhdr 页眉。

## 化学写作词库

`templates/chem_library/`（219 条词条、9 条章节写作协议、11 条 lint 规则），按 super_library 的
schema 建 —— 那是英文 AI 论文语料，没有化学内容，**只借方法不借内容**。

```bash
python3 tools/chemlib.py <正文目录或 tex>
```

首扫就抓到正文两处「生晶体生长体」语病和 16 处术语不统一。D1 要求 high 级为 0。

## D2：图件用词对不上时，改图源不要改正文

`layout_guard` 的 D2 把图件 PDF 里的文字抽出来，和 `templates/glossary_materials_zh.json`
的 `zh_normalize` + chem_library 的 anti-pattern 逐条比对。正文早已统一过，图件是另一条
流水线做的，对不上是常态。

**修法是改图源重新导出，不是改正文，也不是改导出的 PDF/SVG。** 找画图线
（`skills/goai-figure-studio/`）改重建脚本里的标签、重生成 `scene.json`、走 img2ppt 重出。
实抓 15 处：热史→热历史、谱系→系列、结构身份→结构归属、批量相纯→块体相纯、
成相→相形成、处方→配方、慢冷→缓冷、高温溶液长晶→高温溶液法晶体生长、
结构近邻→结构相关化合物、批量相区→块体相区、固相成相→固相反应。

踩过的坑：试过用 headless Chrome 从改过的 SVG 重出，Chrome 替换了拉丁字体，把
`PXRD / Rietveld`、`EDS / EPMA / ICP` 这类字符串裁掉了。**走画图线自己的工具链，别绕。**

## 参考文献侧

编译链里 `bib_enrich`（需网络，失败只记录不阻塞）→ `bib_polish --write` → xelatex →
bibtex → xelatex ×2 → `pdf_guard`。引用核查与 bib 卫生归 `skills/goai-ref-guard/`，
这里只负责把它接进 `scripts/build_tex.sh` 并保证不被绕过。

> 注意 `tools/bib_polish.py` 是 bib_guard 的卫生修复器（`polish()` / `_protect_title()`，
> 接口是 `bib_polish.py <bib> --write`）。**别往这个文件名上放别的脚本** —— 曾经发生过一次
> 同名覆盖，导致它在 import 时就崩、测试挂掉、build_tex 里这一步消失。另一个加花括号/
> 补 Crossref 的脚本现在叫 `tools/bib_plainnat_brace.py`。

## 交付与登记

- 四份 PDF（BYZSO 中英、BaZn2Si2O7 中英）全部 layout_guard PASS 才算完成；
  WARN 逐条在报告里写处置或保留理由。
- `loopctl gate --name typeset_ready --status PASS --detail "<四份 PASS；FAIL 0；WARN N 条已处置>"`。
- 换图、换模板、改 sty 之后**必须重跑整条**：这些改动的回归全部落在 A/B/E 层。
