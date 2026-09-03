已按 `goai-survey-writer` 完成 BYZSO 综述稿及检查。

主要产物：

- [main.tex](<HOME>
- [citation_bank.md](<HOME>
- [blueprint.md](<HOME>
- [revision_log.md](<HOME>
- 分节稿位于 `drafts/sections/`
- `drafts/references.bib` 为唯一核查 bibliography 的链接副本

检查结果：

- `bank_check`: PASS，188 条候选，近三年占比 51%
- `bib_guard`: PASS，511/511 条目整合
- `tex_guard`: PASS
- `academic_language_guard`: PASS
- `draft_complete` gate: PASS，inputs 已记录为 `main.tex` 与 `references.bib`
- `loopctl check-done`: DONE
- 已写入 `loopctl log --event done`

当前环境未安装 `pdflatex`、`xelatex`、`lualatex` 或 `tectonic`，因此无法生成 PDF；该限制已记录在 revision log 和账本中。