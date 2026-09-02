已完成 LLZO 风格库可写修复。

- [exemplar_surveys.jsonl](/home/gaojing/goai_research/workspace/style_bank/exemplar_surveys.jsonl)：15 篇真实综述，core 6 / adjacent 6 / method 3，DOI 与 id 均无重复。
- [writing_style_cards.md](/home/gaojing/goai_research/workspace/style_bank/writing_style_cards.md)：严格区分全文、摘要和纯元数据证据，每条结论均标来源 id。
- [figure_style_cards.md](/home/gaojing/goai_research/workspace/style_bank/figure_style_cards.md)：仅根据 Cao 2014 全文归纳视觉风格。
- [style_bank_log.md](/home/gaojing/goai_research/workspace/style_bank/style_bank_log.md)：记录三组检索、Semantic Scholar 429、Frontiers PDF 成功及两个 MDPI 403。
- [参照 PNG](/home/gaojing/goai_research/workspace/style_bank/exemplar_figures/cao2014_page4_reference.png)：来自 DOI `10.3389/fenrg.2014.00025`，已明确禁止在交付物中复用。

未新增 `search_papers` 调用，复用了第一轮候选。账本已执行：

- `style_bank_ready = WARN`
- 明确标注“诊断浅层风格库”
- 原因：15 < 25，全文仅 1 < 5
- 已完成 `loopctl log`，未虚报 PASS。