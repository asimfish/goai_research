已按 `skills/goai-survey-writer/SKILL.md` 完成 I22 修复，仅改动：

- [tools/render_groff_fallback.py](<HOME>
- [drafts/revision_log.md](<HOME>
- 重新生成两个 PDF

解析层现已通用支持：

- `~$^{\circ}$C` → `900 °C`
- 元素与数字/小数下标
- `LiM_x`、`LiFePO_4`
- 括号计量数与电荷，如 `PO₄³⁻`
- 保持 `Ba–Y–Zn–Si–O` 不变
- 未写 LLZO 专用字符串规则

产物：

- [main.pdf](<HOME>
- [main_formatted.pdf](<HOME>

两份 PDF 均为 16 页 A4、Tagged，且 SHA-256 完全一致：

`1ccf68be6e4779a944d77d5b6537a760340819ad0c6b5d0b65f385103f9608ec`

Token 检查：

| 项目 | 修复前 | 修复后 |
|---|---:|---:|
| `900 ^` | 1 | 0 |
| `900 °C` | 0 | 1 |
| `Li 7` | 7 | 0 |
| `Li 6.25` | 1 | 0 |
| `Li 2 CO 3` | 1 | 0 |
| `LiM x` | 1 | 0 |
| `Li 9 Al 4` | 1 | 0 |
| `LiFePO 4` | 1 | 0 |
| `[sub]` | 0 | 0 |

检查结果：

- `pdfinfo`：PASS，16 页，A4
- `pdffonts`：PASS，DejaVu Unicode 字体嵌入
- `pdfimages`：PASS，图像对象位于第 2、4、8 页
- `tex_guard`：PASS
- `academic_language_guard`：PASS
- `bib_guard --min-integration 0`：exit 0；保留既有 156 条孤儿记录和 497 条字段卫生告警，未改 `references.bib`
- 解析器 smoke test：7/7 PASS
- 栅格检查：正文 `900 °C` 所在第 9 页、指定第 14 页、最终参考文献第 16 页均可读

账本已记录；I22 已关闭，未关闭或改写其他 issue。`draft_complete` 已置 PASS，`review_pass` 保持 PENDING，等待独立格式复核。