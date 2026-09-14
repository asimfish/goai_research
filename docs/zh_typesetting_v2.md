# 中文综述排版规范 v2（2026-09-13）

参考 [super_translate](https://github.com/asimfish/super_translate) 的中文排版原则（宋体正文 + 黑体加粗/标题、行距约 1.5 倍、有界两端对齐、中文禁则、中西文自动加隙、全角标点、Noto/思源 CJK 字体链）与中文期刊综述惯例，落地为 `templates/goai_zh_typo.sty` + `templates/survey_main_zh.tex`。

| 项目 | v1（旧） | v2（新） |
|---|---|---|
| 中文字体 | Droid Sans Fallback（伪粗）/ Fandol | Noto Serif CJK SC 正文，Noto Sans CJK SC 标题与粗体，FandolKai 页眉/强调；macOS 回退 Songti/PingFang，最后 Fandol |
| 拉丁/数学 | Times（newtx） | 不变；无衬线 TeX Gyre Heros、等宽 Cursor 与黑体搭配 |
| 字号/行距 | 11pt，默认 1.2 行距 | 11pt，行距 17pt（≈1.5 倍字号） |
| 版心 | 1 in 四周 | A4，左右 2.3 cm、上下 2.6 cm |
| 节标题 | 居中或 Times 粗体 | 黑体左齐：一级 14pt、二级 12pt、三级 11pt，节前空白递减 |
| 段落 | 首段不缩进 | 所有段落缩进 2 字（ctex autoindent） |
| 标点 | 混用 | 全角式（xeCJK quanjiao），行末压缩；中西文/数字间自动四分之一空 |
| 强调 | 伪斜体 | 楷体 |
| 图表注 | 小号 Times | 黑体粗标签 + 小五宋体说明；表内 9.5pt、行高 1.3 |
| 断行 | — | 禁孤行寡行，两端对齐弹性受限（emergencystretch 1em） |
| 页眉 | 斜体短题 | 楷体短题 + 页码，0.3pt 眉线 |

## 已知坑
- 拉丁无衬线/等宽必须用 fontspec 按文件名选字（`\setsansfont{texgyreheros}[Extension=.otf,UprightFont=*-regular,...]`，kpathsea 能找到 TeX Live 自带 OTF）；按家族名 `TeX Gyre Heros` 在没有 fontconfig 索引的编译机（docker）上找不到，会让节号与等宽文本整体消失；legacy 的 `tgheros`/`tgcursor` 在 TU 编码下则静默回退到 Latin Modern。
- 在 docker 里 `xelatex` 即使写出完整 PDF 也可能返回 1（xdvipdfmx 对 `pdftitle` 中的中文给出警告），`latexmk` 会据此报 exit 12 并删掉 PDF；用三遍 `xelatex` + `bibtex` 的显式序列，并以 PDF 存在与日志无 `^!` 为准。
- docker 以 root 运行过一次后，工作目录里的 aux/pdf 归 root，之后以普通用户运行会因权限失败；统一以同一身份运行或事后 `chown`。
- 标点用 `PunctStyle=quanjiao`（全角式，期刊惯例）；`kaiming` 会把逗号/顿号压成半宽，观感像半角。

- 表格必须恢复单倍行距并用较小的 arraystretch（1.15）：正文 1.25 倍行距 + 1.3 行高会让原本贴着页高设计的大表（条件总表 A/B/C 区）超出页面 40–200 pt，底部被裁掉；同时浮动体用 `placeins[section]` 在节末强制排出，否则大表会漂到十页之后。

## 编译
- 本地/服务器：`xelatex`（TeX Live ≥ 2023）+ ctex/xeCJK/newtx；Noto CJK SC 单字面 OTF 放在 `/usr/share/fonts/noto-cjk/`（或 `\newcommand{\goainotopath}{...}` 指向目录）。
- 5090 上现成环境：docker 镜像 `latex2pdf-latex-compile-server:latest`（TeX Live 2023），字体在 `/data/liyufeng/goai_assets/fonts/`：
  `docker run --rm --user $(id -u):$(id -g) -e HOME=/tmp -v <build>:/work -v /data/liyufeng/goai_assets/fonts:/usr/share/fonts/noto-cjk:ro latex2pdf-latex-compile-server:latest bash -lc "cd /work/drafts && latexmk -xelatex -interaction=nonstopmode main.tex"`
- macOS：直接 xelatex，字体自动回退到 Songti SC / PingFang SC。

## 已用 v2 重排的稿件（内容层未动，只换排版层）
- `submission/03_运行与评测包/正式案例_BYZSO冷启动/最终输出/main_typo2.tex` → `main_typo2.pdf`
- `submission/03_运行与评测包/补充案例_20260903/02_bazn2si2o7/report/main_typo2.tex` → `main_typo2.pdf`
