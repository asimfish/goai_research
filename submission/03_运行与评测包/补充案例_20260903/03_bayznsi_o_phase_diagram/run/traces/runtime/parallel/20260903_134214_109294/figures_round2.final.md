已完成 I2 与 I6 修复。

- 更新 [figure_plan.md](<HOME>
  - `taxonomy_overview` 修正为 9 个内容节点、11 条边。
  - 解释了 3 条重复 `structure motif` 标签：端点节点分别限定为 Ba–Y、Ba–Zn 结构及其向处理控制的转移关系。
  - 补充 SVG/XML 实际计数、白名单与连接器审计。
  - 写入三图的 TeX 路径、caption、label 契约及 writer 嵌入位置。
  - 记录三图 `validate_figspec` 均为 `ok=true`，`errors=[]`、`typo_errors=[]`、`typo_warnings=[]`。

- 修正文稿源码：
  - [01_introduction.tex](<HOME> 嵌入 `roadmap.svg`。
  - [03_taxonomy.tex](<HOME> 嵌入 `taxonomy_overview.svg`。
  - [07_metastability.tex](<HOME> 嵌入 `phase_bottlenecks.svg`。
  - 移除旧 boxed 占位图，统一为编号 caption 和稳定 label。
  - 重新生成 [main.pdf](<HOME> 中已出现 Figure 1–3 新 caption。

- `tex_guard` 与 `academic_language_guard` 均 PASS。
- `figures_ready` 已用 `figure_plan.md` 和三份 figspec 作为 inputs 记录为 PASS。
- I2、I6 已通过 `loopctl` 关闭，并已记录 `done` 日志。

SVG 与 Draw.io 源文件未改动、未重渲染。其它未涉及本任务的 I1/I3/I4 仍保持开放。