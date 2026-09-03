已完成第一轮可写修复验收：

- 仅处理子主题 1/2。
- 真实执行 5 次 MCP 调用：1 次状态检查、2 次本地 grep、2 次 DOI lookup。
- 抽查 5 篇论文的 DOI 与主题相关性，未发现错配或明显离题。
- 文献库保持 46 条，本轮真实新增 0，未删除或重导。
- 已记录第一轮 Semantic Scholar HTTP 429 及检索限制。
- 验收笔记已写入 [search_precursor_powder.md](<HOME>
- 已真实执行 `loopctl log`，agent 为 `lit_precursor_repair`，返回 `logged`。