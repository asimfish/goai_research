已按 `skills/goai-survey-writer/SKILL.md` 完成 I9/I11/I14 处理，未联网，也未修改 `references.bib` 元数据。

完成内容：

- 在 Introduction 增加 BaZn₂Si₂O₇ 与 Ba–Y–Zn–Si–O 的“方法学类比、非 LLZO 证据”段落，明确说明未找到完整 Ba–Y–Zn–Si–O 四元相图，补入 9 个已核查硅酸盐类比 key。
- 修复近邻 garnet 论述，并将 Fig. 3 集成到 Discussion，删除“future expansion”残留表述。
- 正文现使用 213 个不同 key、380 次引用；citation bank 162/162 全部落到正文，`bank_check` PASS。
- 严格 `bib_guard` 结果：整合率 58%（213/368），155 条孤立记录，仍为 WARN/FAIL。由于用户要求不得修改 `references.bib`，该限制已记录。
- 在无 `pdflatex/xelatex` 环境下，用 groff + Ghostscript 生成 32 页 A4 内容完整 fallback PDF，并嵌入现有三张 SVG 图的转换版本。
- `tex_guard` PASS（19 labels、10 refs）。
- `academic_language_guard` PASS。
- `draft_complete` 已通过 `loopctl` 设置为 WARN；I9、I11、I14 已关闭，当前 open issue 为 0。旧的 `review_pass=FAIL` 尚未重新进行独立审稿。

关键产物：

- [main.tex](<HOME>
- [main.pdf](<HOME>
- [revision_log.md](<HOME>