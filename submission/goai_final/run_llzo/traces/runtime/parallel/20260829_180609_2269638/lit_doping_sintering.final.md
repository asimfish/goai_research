已完成子主题 3/4 的真实检索切片：

- 已调用私有全文库，检索 LLZO/LLZTO 与掺杂、立方相、煅烧、烧结、SPS、热压、致密化及晶界等组合。
- 已调用 OpenAlex、Crossref、Semantic Scholar 补充元数据。
- 筛选并通过 `save_to_library` 入库 16 篇真实强相关论文。
- 入库结果：`before=0, added=16, total=16`，已确认 [papers.jsonl](/home/gaojing/goai_research/workspace/library/papers.jsonl) 共 16 行。
- Semantic Scholar 多数请求返回 HTTP 429；OpenAlex/Crossref 检索继续成功。
- 未导出 BibTeX、未运行 coverage、未设置 gate。

两个要求因当前只读 sandbox 未能完成：

- [search_doping_sintering.md](/home/gaojing/goai_research/workspace/notes/search_doping_sintering.md) 写入被只读权限拒绝。
- 已真实执行 `loopctl log --agent lit_doping_sintering`，但创建 `workspace/state/ledger.json.lock` 时同样因只读文件系统失败。

因此，文献入库成功；检索笔记和账本日志未落盘，不能声称完整交付。