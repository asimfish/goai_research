已完成引用整合修复。

- 将 `main.tex` 中的 Corpus coverage 清单迁移至新的 [11_corpus_coverage.tex](<HOME> [main.tex](<HOME> 中通过 `\input` 引入。
- 未删除任何 `references.bib` 条目；sections-only 与整稿 `bib_guard` 均为 511/511、100% 覆盖，无未定义引用。
- `tex_guard`：PASS；`academic_language_guard`：PASS。
- 已更新 [revision_log.md](<HOME>
- 账本已设置 `draft_complete: PASS`（记录 `main.tex` 与 `references.bib` 输入指纹），并写入 `done` 日志；`check-done` 返回 DONE。

BibTeX 中原有的字段卫生告警仍为非阻塞项，未改动文献条目。