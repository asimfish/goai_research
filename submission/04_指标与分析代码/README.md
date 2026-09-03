# 04 指标与分析代码

指标脚本在仓库 `tools/`，本目录存放它们对提交包内数据重算得到的结果。

| 指标 / 分析 | 代码 | 输入 | 结果 |
|---|---|---|---|
| 结论—证据链（100 条结论、219 次引用、51 键核验率） | `tools/build_claim_evidence.py` | `../03_运行与评测包/正式案例_BYZSO冷启动/最终输出/{main.tex,sections,references.bib}`、`../02_研究数据与证据包/{CITATION_AUDIT.json,notes,corpus_release}` | `../02_研究数据与证据包/claim_evidence.jsonl`、`claim_evidence_summary.json` |
| Agent 运行统计（工具调用、web_search、token、失败/超时标记） | `tools/analyze_agent_traces.py` | `../03_运行与评测包/正式案例_BYZSO冷启动/traces/runtime/parallel`、`../03_运行与评测包/LLZO诊断轮/traces/runtime/parallel` | `agent_trace_stats_byzso.{md,json}`、`agent_trace_stats_llzo.{md,json}` |
| 引用一致性闸门（整合率、未定义键、引用密度） | `tools/bib_guard.py` | 稿件 `sections/` + `references.bib` | 运行时写入账本；正式稿 51/51 整合率 100% |
| 组稿完整性闸门（占位、悬空引用、裸 BibTeX key） | `tools/tex_guard.py` | 稿件目录 | 同上 |
| 学术语言闸门（禁止工程术语进入正文） | `tools/academic_language_guard.py` | 稿件目录 | 同上 |
| 前驱体预测模型可用性（加载两个 checkpoint、CPU 预测） | `tools/retro_dry_run.py` | `vendor/two_stage_retro/` | 终端输出；`scripts/smoke_test.sh --with-retro` 自动执行 |
| 前驱体预测基准（Combo@1 71.81 / Combo@20 89.21 / MRR 77.48） | 随 checkpoint 提交的源包评测汇总 | Retro 测试集 2,558 条 | `vendor/two_stage_retro/checkpoints/stage1_summary.json`、`stage2_summary.json` |

重算命令（仓库根目录）：

```bash
.venv/bin/python tools/build_claim_evidence.py
.venv/bin/python tools/analyze_agent_traces.py "submission/03_运行与评测包/正式案例_BYZSO冷启动/traces/runtime/parallel" \
    --md submission/04_指标与分析代码/agent_trace_stats_byzso.md --json submission/04_指标与分析代码/agent_trace_stats_byzso.json
.venv/bin/python tools/analyze_agent_traces.py "submission/03_运行与评测包/LLZO诊断轮/traces/runtime/parallel" \
    --md submission/04_指标与分析代码/agent_trace_stats_llzo.md --json submission/04_指标与分析代码/agent_trace_stats_llzo.json
```
