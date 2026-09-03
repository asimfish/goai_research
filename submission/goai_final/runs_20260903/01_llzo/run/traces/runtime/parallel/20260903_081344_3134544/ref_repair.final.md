已按 `skills/goai-ref-guard/SKILL.md` 完成定向处理：

- I10：对 `wang2025computational` 执行 `verify_entry`，元数据为 PASS，但论文明确研究 LLTO，不适用于 LLZO 正文。已在 `06_transport_measurement.tex` 两处、`08_discussion.tex` 一处改为 `kulkarni2025machine`（LLZO，`verify_entry=PASS`）。该 LLTO 条目仍保留在文献库，但不再被正文引用。
- lit_supplement 新增 11 条条目已批量核验，11/11 PASS；无可疑项需要删除。
- `references.bib`：368 个唯一条目、343 个 DOI、无重复 DOI/键。
- `tex_guard`：PASS；正文 89 个引用键均可解析。既有 I14 的 279 个孤儿条目整合率问题仍保留，未扩大本次任务范围。
- `loopctl`：I10 已关闭；`ref_integrity=PASS`；已记录 `ref_gate / goai-ref-guard / done`。

关键产物：

- [CITATION_AUDIT.md](<HOME>
- [CITATION_AUDIT.json](<HOME>
- [references.bib](<HOME>