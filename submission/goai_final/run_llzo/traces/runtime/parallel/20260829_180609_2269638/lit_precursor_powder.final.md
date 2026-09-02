检索与入库已真实执行：

- 筛选候选：16 篇强相关真实论文
- 主库入库前：31 篇
- 实际新增：15 篇
- 去重：1 篇
- 入库后：46 篇
- Semantic Scholar 多次 HTTP 429；OpenAlex/Crossref 正常补充，部分查询三源均成功
- 本地全文发现 PVP 溶液法论文 `10.3938/jkps.74.187`，定位到前驱体、10% Li 过量及煅烧条件等行号
- 未导出 BibTeX、未运行 `coverage_report`、未设置 `lit_coverage` gate

受当前只读沙箱限制，以下两项未能完成：

- `workspace/notes/search_precursor_powder.md` 写入被拒绝
- `loopctl log` 因无法创建 `workspace/state/ledger.json.lock` 失败

因此真实结果是：文献库新增成功，但审计笔记和最终账本日志写入失败。