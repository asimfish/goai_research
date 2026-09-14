# 排版对照台（单文件 HTML）

用户要求：“不要用 claude 的链接，你弄成一个 html 本地查看就行。”
产物是 **一个自包含的 HTML**（77 张图以 data URI 内嵌，约 11.4 MB），双击即可离线打开，
只有 Google Fonts 的 IBM Plex 需要联网，缺网时回落到系统字体，排版不变。

- 部署副本：`final_round/pdf_gallery/typo_deck_20260913.html` → 站点根目录同名文件
- 来源 PDF：`final_round/pdf_gallery/byzso_{en,cn}_<模版>.pdf`（11 个版本）

## 三步生成

1. **渲染页面**（每个版本取 5 页：首页 / 图 1 页 / 表 1 页 / 条件矩阵页 / 参考文献页；
   页码见 `map.json`，springer 的表 1 在第 34 页）

   ```bash
   pdftocairo -jpeg -r 150 -f <n> -l <n> -singlefile <variant>.pdf p/<lang>_<tpl>_<kind>
   ```

2. **裁题注特写**（图注、表注各一条）——用 `pdftotext -bbox` 找到 “图 1 / 表 1 / Figure 1 / Table 1”
   这个词的 yMin，向上留 14 pt、向下取 95 pt（图注）或 175 pt（表注），左右取该页所有文字的
   最小/最大 x，再按 150 dpi 换算成像素交给 `convert -crop`。裁出的图放 `d/`。

3. **转 WebP 并打包**

   ```bash
   convert <src> -resize 1200x -quality 60 -define webp:method=6 -strip p/<name>.webp   # 整页
   convert <src> -resize 1000x -quality 72 -define webp:method=6 -strip d/<name>.webp   # 特写
   python3 build_local.py typo_deck_<date>.html
   ```

   WebP 在同等可读性下比 JPEG 小约 40%（整页 150 dpi JPEG 14 MB → 1200 px WebP 7.5 MB）。

## deck.html

11 张横向幻灯片，`←/→` 翻页，右上角切中英，点任意页面进原图查看（`1:1` 按钮切原始像素，Esc 关）。
图片路径写成 `p/...webp` 与 `d/...webp`；脚本里 `const IMG = window.__IMG || {}` 决定它是读同目录文件
还是读内嵌的 data URI，所以 `deck.html` 配上 `p/`、`d/` 两个目录也能直接打开，方便调样式。

数据（版心尺寸、字号、页数、Overfull、每个版本的页码）都写死在 `deck.html` 顶部的 `T` 数组里，
取自 `templates/goai_{zh,en}_typo.sty` 与 11 个 PDF 的实际编译结果；改模版后要同步更新。
对照结论见 `docs/typo_templates.md`。
