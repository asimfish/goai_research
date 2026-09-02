# LLZO 46 条 BibTeX 首次快速档诊断

## 诊断范围与方法

- 输入：`workspace/library/references.bib`
- 有界预检：46 条；仅读取条目数与 46 个 citation key，未整体打印 BibTeX。
- 快速档：已真实调用 `goai-refcheck.verify_bib_file`，生成 `CITATION_AUDIT.json` 和 `CITATION_AUDIT.md`。
- 抽查复核：仅对两个高风险非 PASS 条目 `huang2019searching`、`zhou2024li5alo4` 调用 `verify_entry`；两者仍为 MISMATCH。
- 深度档：已调用 `deep_audit_info`；返回 `available=false`，预期路径 `/home/gaojing/Code/super_ref` 未检测到。本次没有执行 super_ref 深度审计，不得把快速档结果表述为证据级深审。
- 本轮仅诊断，未修改或批量覆盖 `references.bib`。

## 总体裁决

| 裁决 | 数量 |
|---|---:|
| PASS | 43 |
| FIX | 1 |
| MISMATCH | 2 |
| UNVERIFIED | 0 |
| ERROR | 0 |
| 合计 | 46 |

快速档 gate 为 **FAIL**：存在 1 条 FIX 和 2 条 MISMATCH。

## 三轴统计

以下按“任一对应 issue 即该轴不通过”统计；无该轴 issue 记为通过。

| 核验轴 | 通过 | 不通过 | 说明 |
|---|---:|---:|---|
| 存在性 | 46 | 0 | 无 UNVERIFIED/ERROR，46 条均由快速档找到候选权威记录 |
| 元数据 | 44 | 2 | `shen2020a`、`zhou2024li5alo4` 出现 venue drift |
| 作者名单与顺序 | 44 | 2 | `huang2019searching`、`zhou2024li5alo4` 出现作者 extra/missing；未报告顺序错位 |

注意：存在性通过只代表快速档元数据路由找到了匹配记录，不等于 PDF 证据级深审通过。

## 非 PASS 条目与准确下一步

### `shen2020a` — FIX

- 存在性：通过；标题相似度 1.0。
- 元数据：venue 漂移。声称 `ACS Applied Materials and Interfaces`，权威记录为 `ACS Applied Materials & Interfaces`（审计输出中的 `&amp;` 是转义显示）。
- 作者：未报告问题。
- 下一步：以 DOI `10.1021/acsami.0c04850` 的出版方记录核对正式期刊名，再对该单条应用规范化修正并重跑 `verify_bib_file`；不要批量覆盖全库。

### `huang2019searching` — MISMATCH

- 存在性：通过；标题相似度 1.0；DOI `10.1016/j.jmat.2018.09.004`。
- 作者：声称 `Badding Michael Edward`，Crossref 权威名单为 `Michael E. Badding`；声称末位 `Z. Wen`，权威记录为 `Zhaoyin Wen`。工具将前一差异报告为一条 extra 和一条 missing。
- `verify_entry` 复核：仍为 MISMATCH，来源为 Crossref。
- 下一步：查 DOI 出版方页面/PDF 核定完整作者名单及顺序；确认后仅修正该条作者字段并重跑快速档。若权威来源冲突或快速档仍不收敛，待 super_ref 可用后进入深度审计。

### `zhou2024li5alo4` — MISMATCH

- 存在性：通过；标题相似度 0.959；DOI `10.1021/acsami.3c17606`。
- 作者：声称 `Yongjiang Zhou`，OpenAlex 权威名单为 `Yongjian Zhou`（拼写差异）。
- 元数据：venue 从 `ACS Applied Materials and Interfaces` 漂移为 `ACS Applied Materials & Interfaces`。
- `verify_entry` 复核：仍为 MISMATCH，来源为 OpenAlex。
- 下一步：优先查 DOI 出版方页面/PDF，核定 `Yongjian`/`Yongjiang`、完整作者顺序、正式文献类型及期刊名；不要直接照抄工具建议（其建议仍为 `@inproceedings`，需由出版方确认类型）。确认后仅修正该条并重跑。若不能取得证据或来源冲突，保持 FAIL，待 super_ref 可用后深审。

## 常见错误模式

- 作者规范化/展开差异：1 条（`Badding Michael Edward` vs `Michael E. Badding`，并伴 `Z. Wen` vs `Zhaoyin Wen`）。
- 作者名拼写差异：1 条（`Yongjiang` vs `Yongjian`）。
- venue 标点与实体转义差异：2 条（`and` vs `&`；审计 JSON 可能显示 `&amp;`）。
- 本批次未发现 UNVERIFIED、年份漂移或明确作者顺序错位。

## 闸门结论

`ref_integrity=FAIL`。解除条件：3 条非 PASS 均获得合适权威证据并完成单条修正，随后 `verify_bib_file` 全部 PASS；若快速档不收敛，保持阻塞并在 super_ref 深度档实际可用后进行证据级裁决。
