已按 `skills/goai-survey-writer/SKILL.md` 完成 I16 修复并关闭。

- [main.tex](<HOME> 10 个 section 的显式清单。
- [main.pdf](<HOME> groff/Ghostscript 生成 32 页 A4 内容完整 fallback PDF。已解析交叉引用、编号图表和公式，表格改为可换行语义行，化学式保持连续文本。三图位于第 3、6、16 页；无 fallback 语法泄漏。
- [revision_log.md](<HOME> reconciliation。

验证结果：

- `tex_guard`: PASS
- `academic_language_guard`: PASS
- `bib_guard`: 212 个唯一 key、378 次引用，212/368 = 57.6%；156 个孤儿条目导致 WARN，未修改 `references.bib`
- `draft_complete`: WARN，仅保留上述既有孤儿条目原因
- `loopctl`: I16 已关闭，当前 open issue 为 0

`review_pass` 保留原独立审稿状态，未进行自审或擅自修改。