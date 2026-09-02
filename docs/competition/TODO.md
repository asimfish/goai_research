# GOAI材料方向复赛TODO

更新时间：2026-09-03。提交截止 2026-09-03 18:00。评审入口见 `SUBMISSION.md`。

## 提交前最后步骤（人工）

- [ ] 确认队伍名，运行 `bash scripts/package_submission.sh "<队伍名>"` 生成两个 zip（`dist/`）。
- [ ] 打 tag `goai-final-2026-09-03` 并推送；`submission/goai_final/VERSION` 由打包脚本写入 commit。
- [ ] 将 GitHub 仓库设为公开（最后一步）；若不能公开，改为上传 `dist/` 中的 release 压缩包并在报告中说明。
- [ ] 官网上传两个 zip 与 PPT（`AI4R_MAT_<队伍名>_SAGE-Mat_非代码材料_PPT.pptx`），回下载校验 SHA-256。
- [ ] 在复赛群确认"研究数据与证据包 / 运行与评测包"归入非代码类的口径（官方总览表与正文不一致）。

## 已完成

### 任务与证据
- [x] 正式主题：Ba5Y12Zn[O(SiO4)]8 及其结构近邻的合成条件（纯主题冷启动）；LLZO 作为初赛承诺的诊断案例保留。
- [x] 51 篇文献三轴核验 PASS；`claim_evidence.jsonl` 100 条结论 → 219 次引用；36 条合成条件结论带原文页/节定位。
- [x] 公开知识库：被引 51 篇中 21 篇全文导出为 `goai-compact-parquet-v1`（`tools/build_cited_corpus.py`），其余以 DOI 提供。

### 离线文献工具
- [x] 私有 NAS 全库与公开精简包共用同一接口；流式检索、受限读取、DOI 查询、导出命令、`check.sh --corpus` 验证。

### 无机逆合成（RECIPE）
- [x] 两个 checkpoint 固定并校验 SHA-256；`predict_precursor_routes` 接入想法环节；正式报告 3 次调用留痕。
- [x] `tools/eval_retro_benchmark.py` 在 2,558 条留出反应上重算：Combo@1 71.81 / Combo@20 89.21 / MRR 77.48（与 checkpoint 汇总逐位一致）。
- [x] 模型输出一律标注 `chemical_route_verified=false`，经文献补全与审稿复核后才进入正文。

### 评测与输出
- [x] 人读 PDF（23 页）+ 机器读 `claim_evidence.jsonl` / `CITATION_AUDIT.json` / `retro_benchmark.json`。
- [x] 全部输入配置、子任务提示词、账本、MCP 审计日志、异常与超时任务均保留在 `submission/goai_final/run/`。

### 复现与合规
- [x] `scripts/smoke_test.sh`（干净环境 1–2 分钟）与 `scripts/reproduce_core.sh`（同一模型与推理强度重跑）。
- [x] 构筑阶段（Codex 原生 rollout + 网关导出）与运行阶段轨迹分目录；密钥模式脱敏；Harness / 模型 / 推理强度声明。
- [x] `.env.example`；包内无 API key / Token / 私有目录布局。
- [x] 复赛报告 DOCX（官方模板六章加强版）与方案说明 PPT（12 页，ppt-master 生成，PPTX + PDF + 可编辑 SVG 源）。

## 暂不扩展
- 不新增同质化 Agent 角色；不以"顶会综述篇幅"为目标；不上传私有大语料。
- 条件预测器（温度 / 气氛）与跨模型审稿列为下一步，不在本次提交范围。
