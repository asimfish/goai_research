# F. 本地全文语料与无机两步逆合成实测

日期：2026-08-29。测试均使用仓库副本；NAS源代码未修改。

## 1. 离线全文检索

- 语料：`InorganicSys/2015-2017`、`2018`、`2019`、`2020`四个私有根目录。
- 查询：字面量`Li7La3Zr2O12`，全局最多返回1条，前后各1行。
- 结果：`ok=true`、命中1条、`timed_out=false`，工具用时7956.735 ms。
- 命中文献：2018年目录下 *A novel synthetic route of garnet-type...*，第15行。
- 受限读取：同一文献第14--16行读取成功；根目录外路径由单测验证会拒绝。
- 审计：请求、命中、耗时及读取结果均追加到`$GOAI_WORKSPACE/state/tool_calls.jsonl`。

实现采用每个语料根一个`rg --json --line-buffered`进程并发扫描，只把match事件
送回主线程；达到结果上限后终止其余进程。这样适配NAS的年份分片，也避免把整库
索引加载进内存。

## 2. 两阶段无机逆合成

运行环境：Python 3.11，PyTorch 2.7.0+cu128，CUDA可用，设备`cuda:0`。

固定模型：

- Stage 1：formula-token precursor retriever，seed 20260504，SHA256
  `f302cb315a607eaf461281ef65585489eb814b1db7c5e41e56aaa9193965a53e`。
- Stage 2：no-mixture-pool set reranker，seed 20260504，SHA256
  `373ee6bdaf562f4ee70b06e515d5b84a18db8c6dbd2d4e2fd7dea864272465de`。

实测结果：

| 输入 | Top-1前驱体组合 | 结果 |
|---|---|---|
| `Ca9Zn4.2Sb9`（Retro测试集，标注ID为591/108/342） | `Sb + Zn + Ca` | 与标注集合一致，排名第1 |
| `BaTiO3` | `BaCO3 + TiO2` | 返回Top-5成功 |
| `Li7La3Zr2O12` | `ZrO2 + La2O3 + Li2CO3` | 返回Top-5成功 |

LLZO在模型已加载后的推理用时437.192 ms；默认枚举2--5元组合，共4928条候选，
再由Stage 2重排。输出明确区分`model_output_verified=true`与
`chemical_route_verified=false`，不能把预测路线当作实验事实。

## 3. 离线回归

`tests/test_offline.py`共33项通过，覆盖本地检索/受限读取/审计日志、公开文献子集
allow-list与私有路径脱敏、模型资产和checkpoint哈希，以及原有确定性模块。
