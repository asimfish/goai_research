已按 `goai-ref-guard` 完成 I15/I17/I18：

- 第 6 节移除 `wang2025computational` 的 LLZO 输运误用；该键仍保留在库中，仅在第 2 节作为明确的 LLTO comparator。
- 第 7 节删除将 `anon2025decision` 编辑决定信称为 scalable-cathode report 的论据；该键仍保留在库中，当前正文引用次数为 0。
- `verify_entry`：`wang2025computational`、`anon2025decision`、`kulkarni2025machine` 均 PASS。
- 正文扫描：212 个 unique keys、378 次引用、0 个未定义 key、156 个孤儿条目。
- `tex_guard=PASS`，`academic_language_guard=PASS`。
- `bib_guard` 仍因既有 I14 背景库整合率 57.6% 而报告 `FAIL_ORPHAN_INTEGRATION`，但所有正文 key 均已解析。
- `references.bib` 未修改，哈希仍为 `6c182833bb513d245c1683d1e978ffd3aad1f085a5310cf0fccd5bd15281ec3c`。
- 已通过 `loopctl` 关闭 I15、I17、I18；未触碰仍独立存在的 I16、PDF 或图件。

产物：

- [06_transport_measurement.tex](<HOME>
- [07_interfaces_integration.tex](<HOME>
- [CITATION_AUDIT.json](<HOME>
- [CITATION_AUDIT.md](<HOME>