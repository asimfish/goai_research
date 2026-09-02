已完成真实检索与入库，但宿主只读限制阻止了笔记和账本写入。

- 真实调用了 `goai-litsearch` 本地全文检索及 OpenAlex、Crossref、Semantic Scholar。
- 筛选 18 篇强相关真实论文并调用 `save_to_library`。
- MCP 返回：`before=16`、`added=15`、`total=31`；随后文件因并行任务已增长至 46 行：[papers.jsonl](/home/gaojing/goai_research/workspace/library/papers.jsonl)。
- 未导出 BibTeX、未跑 coverage、未设置 gate。
- API 元数据检索均为 `errors={}`；记录到本地正则扫描超时及 `Li volatilization` 的 `timed_out=true`。
- [search_additive_property.md](/home/gaojing/goai_research/workspace/notes/search_additive_property.md) 写入被只读沙箱拒绝。
- 已执行要求的 `loopctl log --agent lit_additive_property`，但创建 `ledger.json.lock` 时因 `Errno 30: Read-only file system` 失败。

需要在可写环境中补写检索笔记并重放最后的 `loopctl log`；当前不能诚实宣称这两项已落盘。