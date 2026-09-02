# submission/goai_final — 复赛正式提交包

评审入口文档：[`docs/competition/SUBMISSION.md`](../../docs/competition/SUBMISSION.md)（交付物位置、模型与 Harness 声明、全部运行记录与筛选规则、数据许可边界、指标复核、追溯链、复现命令）。

```
report/            正式报告 PDF（Ba5Y12Zn_合成调研_学术润色版.pdf，23 页）+ LaTeX 源 + BibTeX + 图源（figspec/svg/drawio/png/pdf）
report_docx/       复赛报告（官方模板六章加强版）DOCX
deck/              方案说明 PPT（PPTX + PDF）
evidence/          研究数据与证据包：references.bib、papers.jsonl、claim_evidence.jsonl、CITATION_AUDIT.json、
                   notes/（citation_bank、condition_source_trace、检索日志）、corpus_release/（被引文献全文精简 Parquet 知识库）
run/               运行与评测包（正式案例，冷启动 cold_full_byzso_m2gfJJ）：inputs/、tasks/、ledger.json、tool_calls.jsonl、
                   review_traces/、ideas/、traces/runtime/parallel/<batch>/<task>.jsonl、traces/runtime/orchestrator/、RUN_MANIFEST.json
run_llzo/          次要案例（LLZO 诊断轮）：账本、MCP 日志、子任务轨迹、审计报告
traces/            development/  构筑阶段 Agent 轨迹（Codex 原生 rollout + 网关消息导出）
                   runtime_native_sessions/  codex exec 子任务的原生 rollout（08-29 LLZO、08-31 BYZSO 首轮）
                   codex_sessions_index.json
metrics/           agent_trace_stats_*.md/json（前驱体模型指标见 vendor/two_stage_retro/checkpoints/*_summary.json）
MANIFEST.sha256    包内每个文件的 SHA-256
VERSION            生成本包的 git commit
```

重建本目录（需要私有工作区与私有语料，仅团队内部）：

```bash
.venv/bin/python tools/export_submission_bundle.py --cold-workspace <clone-of-cold-run> \
    --llzo-workspace workspace --dev-trace-dir <gateway-export> --codex-sessions-dir $CODEX_HOME/sessions
.venv/bin/python tools/build_cited_corpus.py --bib submission/goai_final/report/references.bib \
    --out submission/goai_final/evidence/corpus_release       # 需要 GOAI_LOCAL_CORPUS_* 指向私有库
.venv/bin/python tools/build_claim_evidence.py --bundle submission/goai_final
.venv/bin/python tools/retro_dry_run.py Li7La3Zr2O12      # 前驱体模型 dry run（CPU）
```
