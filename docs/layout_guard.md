# 版面与格式门禁 layout_guard（2026-09-14）

用户：“确保这些内容都完善到我们的机制里，不能再出现之前的版式不对，格式不对的问题了。”

2026-09-13/14 这一轮的每一个版面问题，都是我一页页翻 PDF 看出来的，没有任何一条是自动发现的。
所以把它们全部写成可执行的检查，接在编译后面：**编完就跑，有 FAIL 就不发布。**

## 一条命令

```bash
bash goai_research/tools/build_and_guard.sh [<构建树>]
```

同步 → 5090 编译四份 → 取回 PDF 与 `.log` → 对四份逐一跑 `layout_guard.py` → 有 FAIL 退出码非 0。

单独跑某一份：

```bash
python3 goai_research/tools/layout_guard.py \
  --pdf main_typo3.pdf --log main_typo3.log \
  --src sections_zh3 --sty goai_zh_typo.sty --figdir ../figures/pdf --lang zh
```

`--json` 出机读结果；`--strict` 让 WARN 也算失败。

## 检查清单：每条都对应一次真实返工

| 层 | 检查 | 对应踩过的坑 | 级别 |
|---|---|---|---|
| A1 | `^!` LaTeX 错误 | — | FAIL |
| A2 | Overfull `\hbox` > 1 pt | springer 窄栏；`\sloppy` 换掉后的回归 | FAIL（≤1 pt 记 WARN） |
| A3 | Overfull `\vbox` | 表格撑破页面下边界 | FAIL |
| A4 | `File ... not found` | 换图后路径没改全 | FAIL |
| A5 | 未定义引用 / 交叉引用 | bibtex 没跑够轮次 | FAIL |
| A6 | 重复 `\label` | — | FAIL |
| A7 | badness 10000 的 Underfull > 8 处 | `\sloppy` 把词距放松 | WARN |
| B1 | **题注一律顶左** | `singlelinecheck=true` 让短题注居中、长题注左对齐 | FAIL |
| B2 | 文字不得越出版心 | 表格/图件比正文宽 | FAIL |
| B3 | 除首页外每页有页眉 | manuscript 的 `\runninghead` 没生效 | WARN |
| B4 | 除首页外每页有页码 | — | WARN |
| C1 | `\includegraphics` 的文件存在 | 换图漏改 | FAIL |
| C2 | **中文稿不引用 `_en` 图、英文稿不引用 `_zh` 图** | 英文版曾用中文图 | FAIL |
| C3 | `table` 浮动体是 `[bp]` | 表格没浮到页底 | FAIL |
| C4 | 表格列格式无竖线 | — | FAIL |
| C5 | 没有 `\hline`（只用 booktabs） | — | FAIL |
| C6 | 表注在表上、图注在图下 | — | FAIL |
| C7 | 分数列宽合计 = 1 | 表格宽度与正文不齐 | FAIL |
| D1 | 正文过 chemlib（high 必须为 0） | 「生晶体生长体」这类语病 | FAIL |
| D2 | **图件里的文字也过同一套术语表** | 换图后图里写「谱系」「成相」，正文是「系列」「相形成」 | FAIL |
| E1 | 默认模版 = `manuscript` | 默认值被改回去 | FAIL |
| E2 | `singlelinecheck=false` | 题注忽左忽中的根因 | FAIL |
| E3 | 没有裸 `\sloppy` | 词距被放松、灰度不匀的根因 | FAIL |
| E4/E5 | 加载 microtype、`\raggedbottom` | — | WARN |
| E6 | `bottomfraction ≥ 0.7` | 不够大时半页高的表落不到页底，会漂到正文之后 | FAIL |

D2 是这次新加的一条，也是最容易漏的：**图件和正文是两条流水线，术语很容易各写各的**。
它把 `glossary_materials_zh.json` 的 `zh_normalize` 与 `chem_library` 的 anti-pattern 拿来，
`pdftotext` 抽出图里的文字逐条比对。

## 写检查时踩的坑（别再犯）

- **右版心边界不能取 xMax 的众数**。中文可在任意字处断行，行尾常差半个字没顶到边界，众数会偏小
  几十 pt，据此判越界会把每一行中文都误报。改用 99.5 百分位，真正的水平溢出交给 A2 从 `.log` 判。
- **中文标点是悬挂的**，句号逗号可以探出版心半个字，B2 要把行尾的 `。，、；：）` 排除。
- **题注标签必须限定在行首**。不加这个条件，正文里句末的 “…listed in Table 2.” 会被当成题注，
  而它在行中间，位置一比就误判成「居中的题注」。
- **首页没有页码也没有页眉**（`\thispagestyle{empty}`），B3/B4 要跳过第 1 页。

## 与其他门禁的关系

```
zh_table_merge / zh_terms_apply     生成与规范化
        ↓
chemlib audit                       措辞（正文）
        ↓
zh_qa.py sections_zh3 sections_en   中英一致（引用键/公式/交叉引用/数字/表格结构）
        ↓
build_and_guard.sh                  编译 + layout_guard（版面 + 格式 + 图文用词）
        ↓
deploy_pages.sh                     发布
```

`zh_qa` 管中英两条线的**内容**一致，`layout_guard` 管**版面与格式**。两个都过才发布。
唯一已知的、允许的 `zh_qa` 差异是 `08_future_directions.tex` 里「方向一/二/三/四 → Direction 1/2/3/4」。

## 当前状态（2026-09-14）

| 报告 | 结果 |
|---|---|
| BaZn₂Si₂O₇ 中文 | PASS |
| BaZn₂Si₂O₇ 英文 | PASS（1 处 0.23 pt Overfull，记 WARN） |
| BYZSO 中文 | **BLOCKED：18 条 D2** |
| BYZSO 英文 | **BLOCKED：18 条 D2** |

BYZSO 被拦下的全部是 D2——第五轮新图件里的用词与正文不一致，见下节。要改得回 `goai_画图`
那条线动图源，不在排版线上改别人的产物。
