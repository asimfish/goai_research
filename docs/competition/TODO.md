# GOAI材料方向复赛TODO

更新时间：2026-08-29。优先级以“能否从原始输入复现主要科学结论”为准。

## P0：提交前必须完成

### A. 任务与证据（建议主责：高京）

- [ ] 固定正式主题为LLZO烧结与致密化，写入`competition/llzo/topic.md`和`scope.md`。
- [ ] 确认综述贡献组合（建议`A+B+C`），并将现有单树taxonomy改为“工艺链＋组成/环境修饰面＋结构性能证据面”的分面框架。
- [ ] 导入初赛已核验的LLZO文献清单、BibTeX、阅读卡片、Research Gap和Claim–Evidence映射。
- [ ] 每条主要Claim记录DOI、原文文件、页/行定位、证据摘录和文件SHA256。
- [ ] 生成公开子集：仅保留正式结果实际使用且允许分发的原始文献；其余文献不进入公开包。
- [ ] 对不能公开PDF的文献仅保留DOI、官方链接和版权说明。

### B. 离线文献工具（建议主责：吕丁阳；数据复核：高京）

- [x] 设计同一接口兼容私有NAS全库与公开裁剪子集。
- [x] 实现流式ripgrep全文检索，达到结果上限立即停止，返回路径、行号和上下文。
- [x] 实现命中文档受限读取，禁止读取配置语料根目录以外的文件。
- [x] 在LLZO全库上完成检索冒烟测试并保存工具JSONL日志。
- [x] 实现“选中文献→公开子集目录＋SHA256清单”的导出命令（`tools/export_corpus_subset.py`）。

### C. 无机逆合成（建议主责：李雨峰；模型/数据复核：高京）

- [x] 只读盘点`InorganicRetroSynthesis/two_stage_retro_package`最新两步模型。
- [x] 固定Stage-1 `seed20260504` checkpoint（SHA256 `f302cb...53e`）。
- [x] 固定Stage-2 Combo@1最佳`no_mixture_pool seed20260504` checkpoint（SHA256 `373ee6...5de`）。
- [x] 复制最小推理代码、词表、训练统计和checkpoint到本仓库；不修改原项目。
- [x] 实现“目标化学式→Stage-1 Top-M→硬过滤→组合枚举→Stage-2重排→Top-5路线”。
- [x] 用已知Retro测试样例和至少一个LLZO化学式完成真实checkpoint冒烟测试。
- [ ] 把输出路线交给文献证据补全与Reviewer，不把模型结果表述为实验真值。

### D. 条件预测器（建议主责：高京）

- [ ] 固定训练数据schema：目标物、前驱体、方法、温度、时间、气氛、操作步骤和来源DOI。
- [ ] 按来源文档/DOI划分train/validation/test，完成泄漏检查。
- [ ] 训练并冻结条件预测checkpoint，记录依赖、随机种子和SHA256。
- [ ] 暴露`predict_conditions(target_formula, precursors, method)`工具。
- [ ] 与Top-5前驱体路线组合，形成带条件的完整候选方案。

### E. 评测与输出（建议共同负责）

- [ ] 固定CEDER/Retro测试集和DOI隔离规则。
- [ ] 复现Stage-1 Top-K、Stage-2 Combo@K/MRR及必要基线。
- [ ] 条件预测报告温度误差、时间误差和类别字段F1/命中率。
- [ ] 输出人读`final_report.pdf`和机器读`final_result.json`。
- [ ] `final_result.json`中每条Claim、Gap和路线都绑定Evidence ID。
- [ ] 保存全部输入配置、中间候选、模型原始输出、重排结果、异常和最终输出。
- [ ] 将LLZO接口诊断升级为可证伪研究idea：补路线专属全文证据、对照、变量、量化阈值和失败判据；在化学负责人确认前保持`NOT FOR LAB USE`。

### F. 复现与合规（建议主责：吕丁阳）

- [x] Codex并行任务改为`--json`，每个实例保存JSONL轨迹和最终消息，并检查本轮产物非空及更新时间。
- [ ] 分开保存`traces/development/`与`traces/runtime/`。
- [x] 增加`.env.example`，不得提交API Key、Token或私有认证信息。
- [ ] 增加`scripts/smoke_test.sh`和`scripts/reproduce_core.sh`。
- [x] 修复干净环境安装：Python venv/uv兜底、测试依赖和retro可选依赖。
- [ ] 发布前确认vendored模型代码、checkpoint和Retro派生数据的开源许可与署名方式。
- [ ] 固定release/tag/commit hash，生成代码与模型文件SHA256清单。
- [ ] 确认GitHub公开可访问；否则提供评审可下载的release压缩包。

## P1：材料质量与答辩

- [ ] Proposal升级为复赛报告，补真实结果、基线、消融、限制和证据链。
- [ ] Agent系统说明并入报告方法部分及系统复现文档。
- [ ] AI文献调研改造成研究数据与证据包，不再作为独立报告提交。
- [ ] 制作PPT，前三页讲清科学问题、真实系统能力和关键量化结果。
- [ ] 按官方要求拆分代码/非代码压缩包，并在根目录各放一份`MANIFEST.json`。
- [ ] 在干净环境执行安装、冒烟、核心复现和随机Claim–Evidence抽查。

## 暂不扩展

- 不再新增同质化Agent角色；现有orchestrator、检索、写作、画图、idea和reviewer已经足够。
- 不以“顶会综述篇幅”作为目标；优先保证引用正确、科学结论可追溯、模型真实、结果可复现。
- 不把私有大语料整体上传；公开包只包含本次结论实际使用且许可允许的文献子集。
