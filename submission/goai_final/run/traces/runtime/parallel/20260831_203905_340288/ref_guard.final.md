核验未能收敛，`ref_integrity=FAIL`：

- 63 条均为 `UNVERIFIED`；FIX/MISMATCH 均为 0。
- 45 个 DOI `lookup` 全部受网络沙箱阻断；其余 18 条的四源标题检索同样返回 `Operation not permitted`。
- 三轴已逐条独立记录：存在性 UNVERIFIED；元数据及作者名单/顺序 BLOCKED。
- 未把网络不可达误判成权威查无记录，因此未批量删除或手工修改条目，也未重新 export。
- 已创建 writer blocker `I1`，并完成规定的 `loopctl done` 日志。

产物均已验证非空：

- [references.bib](/home/gaojing/goai_cold_full_byzso_m2gfJJ/workspace/library/references.bib)
- [CITATION_AUDIT.json](/home/gaojing/goai_cold_full_byzso_m2gfJJ/workspace/state/CITATION_AUDIT.json)
- [CITATION_AUDIT.md](/home/gaojing/goai_cold_full_byzso_m2gfJJ/workspace/state/CITATION_AUDIT.md)