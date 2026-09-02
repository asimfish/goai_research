# Ref-gate resolution

## 完成状态

- 范围仅限 `ref_gate` 串行收尾；未探索或推进其他阶段。
- `workspace/state/CITATION_AUDIT.json` 的结构化验证通过：`total=52`，计数恰为 `PASS=52 / FIX=0 / MISMATCH=0 / UNVERIFIED=0 / ERROR=0`，`gate=PASS`。
- 全部 52 条记录的 `verdict=PASS`，且存在性、元数据、作者名单与顺序三轴均为 PASS（52/52）。
- `.venv/bin/python -m pytest tests/test_refcheck_authors.py -q` 通过：`6 passed`。

## 问题解决

先前的 `47 PASS / 5 MISMATCH` 已由以下通用机制闭合：双侧姓名归一化、initial-confusable folding、权威作者缺失状态区分，以及带来源的 closed author adjudication。实现修改位于 `server/core/bibtex.py` 和 `server/refcheck_server.py`；没有针对 citation key 的硬编码，审计中的既有 provenance 全部保留。

## 执行轨迹

- 第一轮关闭的 run `20260831_215020_649130` 虽为 `process_exit=124`，但审计产物已经验收。
- 第二轮关闭的 run `20260831_220642_719260` timeout 后，不再访问外部源或重跑全库网络核查，改由本轮仅消费现有 `workspace/state/CITATION_AUDIT.json` 的串行收尾完成裁决。
- I1：网络通道已在 `danger-full-access` 环境重跑。
- I2：11 条 UNVERIFIED 已按规则移除，且不在当前 52 条过闸库中。
- I3：5 条 MISMATCH 已由通用归一化与闭合权威证据解决。

## 最终决定

`ref_integrity=PASS`：52/52 PASS；存在性、元数据、作者名单与顺序三轴全 PASS；通用归一化回归测试 6/6 通过。
