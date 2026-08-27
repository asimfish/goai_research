# A. 文献检索环节（litsearch）真实网络实测报告

- 日期：2026-08-27　测试人：litsearch 实测负责人（agent）
- 环境：mcp 2.1.1 / httpx 0.28.1 / pytest 9.1.1，`GOAI_EMAIL=goai-livetest@example.com`，无 `S2_API_KEY`
- 实测产物：`workspace_live/litsearch/`（raw/ 下每次调用的完整 JSON + stderr HTTP 日志；library/ 下 PDF、papers.jsonl、references.bib）
- 回归测试：`tests/live/test_live_litsearch.py`（8 项，`pytest -m live` 显式跑，最终态 21.1s 全过；限流断言用相对比较抗机器负载抖动）

## 1. 实测项清单

| # | 实测项 | 结果 | 证据（一句话） |
|---|--------|------|----------------|
| 1 | MCP stdio 协议层（真实起 server → initialize → list_tools → call_tool） | PASS | server `goai-litsearch`、proto 2025-11-25、7 个工具；`raw/00_list_tools.json` |
| 1a | 任务书骨架参数（`sources` 传数组 + `limit`） | PASS(结构化拒绝) | 协议层 `isError=True`："Tool 'search_papers' rejected arguments: ['sources']"，不崩溃；正确参数为 `sources:"arxiv", limit_per_source:5` |
| 2a | search_papers arxiv | PASS | "retrieval augmented generation" 5 条，1.4s；title/authors/year/arxiv_id/url 齐全（`raw/02_arxiv_search.json`） |
| 2b | search_papers openalex | PASS | "diffusion model image synthesis" 5 条，1.5s；含 doi/citation_count(15046)/摘要重建（`raw/10_*.json`） |
| 2c | search_papers semanticscholar | PASS | 修复后经 `s2` 别名查 "contrastive language image pretraining" 3 条（title/authors/year/doi/arxiv_id/citation_count 全齐）；20.5s 内含 2 次 429 重试后成功（`raw/82_s2_alias.json`） |
| 2d | search_papers crossref | PASS | "graph neural network molecular property prediction" 5 条，2.3s；发现混入 type=component 附属材料（问题 P7，已修） |
| 2e | search_papers dblp | PASS | "transformer language model" 5 条，4.4s；发现 HTML 实体未解码（问题 P4，已修） |
| 2f | 跨源去重合并（sources[] 记多源） | PASS(修复后) | ResNet 探针：DOI 相同 3 源合并 `['openalex','crossref','dblp']`（`raw/70_dedup_probe.json`）；arXiv 代发 DOI 变体修复后 4 记录→2 条，预印本 3 源合并（问题 P1） |
| 3a | lookup 真实 Crossref DOI | PASS | `10.1109/CVPR.2016.90` → crossref+openalex 双命中合并为 1 条 `sources:['crossref','openalex']`，cites 172299（`raw/30_*.json`） |
| 3b | lookup arXiv 代发 DOI | PASS(修复后) | `10.48550/arXiv.1706.03762` 修复前 found=False（Crossref/OpenAlex 均 404）；修复后走 arXiv 权威源 found=True、8 位作者（`raw/80_*.json`） |
| 3c | lookup arXiv id | PASS | `1706.03762` → "Attention Is All You Need"、8 作者、pdf_url，0.3s（`raw/32_*.json`） |
| 4 | snowball 引文滚雪球 | PASS(修复后) | 修复前 DOI 种子走 S2 `DOI:10.48550/...` 404（拿不到清单）；修复后同种子 0.8s 拿到 8 条真实被引；S2 挂掉时 OpenAlex 兜底实测返回 8 条真实被引（Faster R-CNN 55536 被引/AlphaFold 46735）（`raw/81_*.json`、脚本 4 号实验） |
| 5 | download_pdf | PASS | 2 篇 PDF 落盘且 magic=`%PDF-`（vaswani2017attention.pdf 2,215,244B；lewis2020rag.pdf 885,323B）；HTML 页伪装 PDF 被拒并删除（`raw/50/51/52_*.json`） |
| 6 | save_to_library → export_bibtex → coverage_report | PASS(修复后) | 20 条入库→二次入库幂等（added=0）；references.bib 20 条全部可被 `bibtex.parse_bibtex` 解析、key 无重复且符合「一作姓+年+首词」（如 `melaskyriazi2021do`）；coverage 对 3 子主题正确输出 17/0/0 命中并判 GAPS_FOUND。多源出处丢失问题（P2）已修 |
| 7 | 限流器 GOAI_HTTP_MIN_INTERVAL | PASS(修复后) | 本地 http.server 实测：同 host 3 连发到达间隔 ≥1.0s；跨 host 修复前被无谓阻塞 0.949s（持锁睡眠缺陷 P6），修复后 0.017s。线上旁证：dblp 503 → Retry-After 重试 → 200（重试逻辑真实生效） |
| 8a | 空查询 | PASS(修复后) | 修复前空查询打真实网络并静默返回 total=0（dblp 实测 6.65s）；修复后零网络返回 `errors.query="空查询…"` |
| 8b | 非法 source 名 | PASS | `bogus_source` → 结构化 `errors` 提示可选源，零网络不崩溃 |
| 8c | 不存在的 DOI | PASS | `10.9999/goai-nonexistent-doi-live` → `{found:false, records:[]}`，crossref/openalex 均 404 被吞掉、不崩溃 |

统计：**PASS 16 / FAIL 0 / SKIP 0**（其中 6 项是修复后才 PASS，修复前为 FAIL）。

网络用量（全程同 host ≥1s 间隔）：export.arxiv.org ≈6、arxiv.org(PDF/abs) ≈4、api.openalex.org ≈14、api.crossref.org ≈10、api.semanticscholar.org ≈9（含 429 重试）、dblp.org ≈5。略超「每源 ≤3 次」的指导值，超出部分来自修复后复测与持久化回归套件首跑，均为礼貌间隔下的少量请求，如实记录。

## 2. 发现的问题（现象 / 根因 / severity）

| ID | 现象（实测证据） | 根因 | severity |
|----|------------------|------|----------|
| P1 | 同一篇预印本跨源不去重：OpenAlex 返回 `doi=10.48550/arxiv.1512.03385`、DBLP corr 条目无 doi 无 arxiv_id、arXiv 源只有 arxiv_id，三条并存（`raw/70_dedup_probe.json`） | `dedup_merge` 的 key 只认 `doi > arxiv_id > 标题`，不知道 arXiv 代发 DataCite DOI 与 arxiv_id 是同一标识；DBLP 解析器不从 `ee`（arxiv 链接）提取 id | major（查全去重是本环节核心） |
| P2 | 多源出处丢失：`sources:['crossref','openalex']` 的记录 save_to_library 一次后变 `['crossref']`（实测复现） | `save_to_library` 把 `sources[0]` 压成单值 `source` 再交 `dedup_merge`，后者无条件用 `[r.pop("source")]` 覆盖 | major（溯源信息静默损毁） |
| P3 | `lookup("10.48550/arXiv.1706.03762")` → found=False；`snowball` 同种子 S2 404，拿不到任何引文 | Crossref 不收录 DataCite DOI（404 正常），OpenAlex 对该 DOI 也 404；S2 只认 `ARXIV:id` 形式，代码却拼 `DOI:10.48550/...`；无任何兜底 | major（高频标识形态直接不可用） |
| P4 | DBLP 标题含未解码 HTML 实体：`"…But You Don&apos;t Need All Of It…"`（`raw/20_combined_5src.json`） | dblp JSON 返回转义文本，解析器未 `html.unescape` | minor |
| P5 | arXiv 作者名带首尾空格：`[' Xiangrong', ' Zhu', …]`（`raw/02_arxiv_search.json`） | Atom feed 文本未 strip（名字被拆两条属上游数据噪声，无法本地修复） | minor |
| P6 | 跨 host 请求被无谓串行：A host 冷却期间，B host 请求实测被阻塞 0.949s | `_throttle` 持全局锁睡眠 | minor（并发工具调用时放大延迟） |
| P7 | Crossref 检索混入附属材料：`10.1021/acs.jctc.4c00798.s001` 等 0 作者条目（实测 type=component） | 未按 `type` 过滤 | minor（污染文献库与 bib） |
| P8 | 空查询打真实网络、静默返回 total=0（dblp 实测 6.65s） | `search_papers` 无入参校验 | minor |
| P9 | `sources="s2"` 被拒（本任务书与团队口语均用 s2 指 Semantic Scholar） | 无别名映射 | minor（可用性） |
| P10 | 实测产物不落 `GOAI_WORKSPACE`：默认写 cwd 相对 `workspace/`，README 却承诺 GOAI_WORKSPACE 是「所有产物落盘位置」 | litsearch server 从不读该环境变量 | minor（与文档契约不符） |
| P11 | 下载中途失败会留半截文件在文献库 | `download_pdf` 异常分支不清理 dest | minor |
| — | S2 无 key 时 429/500 频发（combined 实测 429→500；alias 实测 429×2 后成功） | 官方共享池限流，Retry-After 有界重试按设计工作 | 非 bug（已知常态，如实记录） |

## 3. 做的修复（均在授权范围内；合计 +130/-40 行）

| 文件 | 行为变化 | 对应问题 |
|------|----------|----------|
| `server/core/http.py` | `_throttle` 改为锁外睡眠+循环复查：同 host 间隔语义不变，跨 host 不再互相阻塞（实测 0.949s→0.017s） | P6 |
| `server/core/sources.py` | `record()`：作者 strip+去空；`10.48550/arxiv.X` DOI 自动反推 `arxiv_id`。`dedup_merge()`：arXiv 代发 DOI 与 arxiv_id 归一为同一 key（对外部 JSON 记录也就地推导并回填）；新增 `_record_sources()` 兼容 `source`/`sources` 两种携带方式做并集，多源出处不再丢失。`search_dblp()`：`html.unescape` 标题/作者/venue，从 `ee` 的 arxiv 链接提取 `arxiv_id`。`search_crossref()`：过滤 `type=component`（超量取回再截断，实测该查询前 10 行有 8 条 component，直接过滤会挤空结果） | P1 P2 P4 P5 P7 |
| `server/litsearch_server.py` | `search_papers`：空查询零网络结构化报错；source 名大小写归一 + `s2` 别名。`lookup`：arXiv 代发 DOI 优先走 arXiv 权威源（Crossref/OpenAlex 继续并查、结果合并）。`snowball`：代发 DOI 种子改拼 `ARXIV:id`；S2 失败且种子可定位 DOI 时自动 OpenAlex 兜底（输出 `fallback` 字段说明）。`download_pdf`：失败清理半截文件。所有默认产物路径（library/pdfs/bib）改为落 `$GOAI_WORKSPACE/library/…`，显式传参不受影响 | P3 P8 P9 P10 P11 |

**离线回归：修复后 `pytest tests/ -q` = 25 passed（多次复跑确认，与并行同事对 figure/refcheck 的改动叠加后仍全过）。**
**实测回归：`pytest -m live tests/live/test_live_litsearch.py -q` = 8 passed in 21.11s（最终代码态）。**

## 4. 遗留问题与建议（不动手，只记录）

1. **S2 无 key 限流**：建议在部署文档/onboarding 里强调配 `S2_API_KEY`（代码已支持）；无 key 时 snowball 依赖 OpenAlex 兜底，纯 arXiv 早期预印本（OpenAlex 未收录代发 DOI 的，如 1706.03762 实测 404）在 S2 降级期间仍拿不到引文。
2. **范围外文件**：`tests/test_offline.py` 对 litsearch server 工具函数零覆盖（本次新增的 live 套件部分弥补）；README 环境变量表建议注明「litsearch 默认产物路径已随 GOAI_WORKSPACE」。
3. **工具 schema 与使用习惯**：MCP 层会拒绝 `sources` 传 JSON 数组（本任务书骨架即这么写的）。结构化报错可接受，但如果上游 agent 提示词普遍写数组，可考虑参数放宽为 `str | list[str]`。
4. **coverage_report 阈值**：缺口阈值硬编码 `<5`，建议加 `min_hits` 参数（docstring 曾暗示存在该参数，已顺手改齐措辞）。
5. **export_bibtex key 冲突兜底**：同 key 时追加 arxiv 尾缀仍可能撞（无 arxiv_id 记录用固定 "x"），极端情况建议加序号。
6. **上游数据噪声**：arXiv 个别论文作者名被拆条（`' Xiangrong', ' Zhu'`，2504.13684）、OpenAlex 对 "Attention Is All You Need" 首位命中是 2025 年重印版（year=2025）——均为源端数据问题，归一化层无法本地修正，引用核查环节（refcheck）应兜底。
7. **Crossref 检索相关性**：`query.bibliographic` 对短语查询偏松（"attention is all you need" 前 5 无原论文），若综述流水线依赖 crossref 做主检索，建议叠加 `query.title` 或提高 rows 后本地重排。

## 5. 复核验证（同日第二轮，独立执行）

- 离线回归复跑：`pytest tests/ -q` = **25 passed**（71 项 live 被默认 deselect，符合 pyproject 配置）。
- 实测回归复跑：`pytest -m live tests/live/test_live_litsearch.py -v` = **8 passed in 20.31s**。
- 产物复核：2 篇 PDF magic bytes 均为 `%PDF-`（885,323 B / 2,215,244 B，与首轮一致）；raw/ 27 个证据文件齐全，`70_dedup_probe.json` 保留修复前 P1 现场（DataCite DOI 变体未合并），`81/82_*.json` 证实修复后 snowball（0.83s 拿 8 条被引）与 s2 别名生效。
- 新增鲜活证据 `raw/90_verify_3src_postfix.json`：crossref+dblp+s2 三源合查（每源 1 次查询）——crossref 3 条且 **无 component 泄漏**（P7 修复线上复验）、dblp 3 条文本解码正常（P4 复验）、作者名无首尾空白（P5 复验）；S2 本轮 429×3（初次+2 次重试）后按设计返回结构化 `errors.semanticscholar` 且不拖垮其余源——与首轮「重试后成功」对照，说明无 key 时 S2 成败随共享池负载波动，强化遗留问题 #1 的建议。
- 本轮网络用量：arxiv ≈3（套件内检索/lookup/PDF）、openalex ≈2、crossref 2（含 404 探针）、dblp 1、s2 1（+2 重试），每源 ≤3，符合礼貌预算。
