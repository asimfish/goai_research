已完成串行降级，但按 fail-closed 裁决为 `ref_integrity=FAIL`：

- 全库核验：52 条，47 PASS、0 FIX、5 MISMATCH、0 UNVERIFIED/ERROR。
- 仅处理了指定 5 条；此前移除的 11 条均未恢复。
- 未采纳删空作者、希腊 `Μ`、导师/院系冒充作者及 `Last, First` 死循环等不安全建议。
- 权威证据来自 Crossref/DOI、INIST-CNRS、[MSA 原文](https://msaweb.org/AmMin/AM39/AM39_600.pdf)、[Sakarya 机构库](https://acikerisim.sakarya.edu.tr/handle/20.500.12619/81021?show=full)及 [DataCite DOI](https://doi.org/10.26021/12446)。
- 新增 blocker I3；I1/I2 保持开放。已执行规定的 `loopctl log`。
- 未进入 taxonomy、writing 或 figures。

产物：

- [references.bib](/home/gaojing/goai_cold_full_byzso_m2gfJJ/workspace/library/references.bib)
- [CITATION_AUDIT.json](/home/gaojing/goai_cold_full_byzso_m2gfJJ/workspace/state/CITATION_AUDIT.json)
- [CITATION_AUDIT.md](/home/gaojing/goai_cold_full_byzso_m2gfJJ/workspace/state/CITATION_AUDIT.md)

给 orchestrator 的建议：先修复 refcheck 的空作者处理、双侧姓名规范化、Unicode 同形字符和机构库作者角色映射，再重跑全库；否则转交 super_ref 深审。修复前不得放行 writing。