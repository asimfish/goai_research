---
name: goai-lit-search
description: Use when the task is comprehensive literature retrieval for a survey — 文献搜索 agent：多源检索（arXiv/OpenAlex/Semantic Scholar/Crossref/DBLP）+ 引文滚雪球 + 查全率闸门 + OA PDF 下载 + BibTeX 导出。触发词：「检索文献」「查全」「literature search」「下载论文」。
---

# GoAI Lit-Search —— 查全导向的文献检索 agent

目标不是「找到一些相关论文」，而是**尽可能全**：对给定子主题，检索到边际新增
趋近于零，并通过 coverage 闸门。工具来自 MCP server `goai-litsearch`。

## 规模档位（开工前先定档，记入账本）

| 档位 | 库规模 | 适用 | 分层配额 |
|---|---|---|---|
| standard | 30–50 | mini survey / 快速调研 | 每子主题 ≥6 |
| **comprehensive**（正式综述默认） | **100–150** | 投稿级综述 / 比赛 | 每子主题 ≥15；综述类 ≥8；近三年 ≥30%；奠基文献不限年份窗 |
| exhaustive | 200+ | 领域全景 / 系统性综述 | comprehensive 基础上滚雪球做满两跳 |

档位由 topic.md/任务书指定，缺省时正式综述取 comprehensive。定档后
`loopctl log --event decision --detail "scale=<档位>"`。**规模是硬指标**：
comprehensive 档不足 100 篇时 coverage gate 不得记 PASS（确属新兴小领域
文献总量不足时如实记 WARN + 检索式证据，不许凑弱相关充数）。

## 工具面

| 工具 | 用途 |
|---|---|
| `search_papers(query, sources, limit_per_source, year_from, year_to)` | 跨源检索+去重合并 |
| `snowball(seed, direction, limit)` | 引文滚雪球（references/citations/both） |
| `lookup(identifier)` | DOI/arXiv 精确查元数据 |
| `save_to_library(papers_json, library_path)` | 入库去重（papers.jsonl） |
| `coverage_report(subtopics, library_path)` | 查全率体检（gap 检测） |
| `download_pdf(url, filename, out_dir)` | OA PDF 下载（fail-closed，不绕付费墙） |
| `export_bibtex(library_path, out_path)` | 导出 references.bib |

## 检索规程（每个子主题跑完整四步）

1. **关键词矩阵**：为子主题写 3–5 组检索式（同义词 × 方法词 × 任务词；
   英文；含缩写变体，如 "world model" / "dynamics model"）。逐组
   `search_papers`，sources 至少 `arxiv,openalex,semanticscholar`；
   系统性综述再加 `crossref,dblp`。结果全部 `save_to_library`。
2. **滚雪球**：从库里挑该子主题 (a) 被引最高的 2 篇 (b) 最新的 2 篇
   (c) 已有综述 1 篇，对每篇 `snowball direction=both`；新命中入库。
   综述类种子的 references 是查全金矿，必须做。
3. **边际收敛判据**：重复 1–2 直到边际新增低于档位线（standard：一轮
   新增去重后 <5 篇；comprehensive/exhaustive：<10 篇且各分层配额已达标）
   或「连续两轮新增全是弱相关」。把每轮的检索式与新增数记入
   `workspace/notes/search_log.md`（可复现性要求）。
4. **闸门**：构造 subtopics JSON（name + keywords）跑 `coverage_report`，
   并核对档位配额（库规模、每子主题篇数、综述类篇数、近三年占比）。
   - `GAPS_FOUND` 或配额缺口：对 gap 子主题换关键词重搜 + 换种子滚雪球，
     最多 3 轮；仍有 gap → 如实上报「该子主题文献确实稀少」，附证据
     （检索式清单）。
   - `PASS`：`loopctl gate --name lit_coverage --status PASS
     --detail "<档位/N篇/M子主题/配额逐项达标情况>"`。

## 下载与导出

- 每篇有 `pdf_url` 或 arXiv id 的入库论文调 `download_pdf`，文件名用未来的
  citation key（一作姓+年+首词）。付费墙/反爬返回失败就记录跳过，
  **禁止**伪造 PDF 或用二手站点绕过。
- 全部子主题过闸后 `export_bibtex` 产出 `workspace/library/references.bib`，
  这是下游唯一允许引用的池子。
- **返工轮警示**：ref_gate 会直接修 references.bib（修复不回流 papers.jsonl），
  一旦 bib 经过引用核查修复，**禁止再全量 `export_bibtex` 重导**（会覆盖全部
  修复）。增量补检的新条目用 `server.core.bibtex.record_to_bibtex`（与
  export 同一代码路径）生成后追加进现有 bib，追加后按 key 查重，并把新条目
  交 ref-guard 逐条 `verify_entry`。
- 检索结果元数据可疑（标题与 id 对不上、作者异常）时，用 `lookup` 按
  DOI/arXiv id 走权威路由核实后再入库，不入库带病记录。

## 硬性规则

- 只入库真实检索结果；任何一条都必须能溯源到某次工具调用。
- 单源 API 报错不termination：换源继续，并把 errors 字段如实记进 search_log。
- 年份窗、语言、领域边界以 `workspace/inputs/scope.md` 为准，不自行扩界。
- 收工时 `loopctl log --stage lit_search --agent goai-lit-search --event done
  --detail "<库大小/新增/下载数>"`。

## 并行约定

被 orchestrator 按子主题切片时：只写自己切片的 search_log 小节；
`save_to_library` 是幂等去重的，多 agent 并发安全；coverage_report 与
export_bibtex 只由最后汇合的 agent（或 orchestrator）执行一次。
