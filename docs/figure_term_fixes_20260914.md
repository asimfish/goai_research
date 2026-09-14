# 图件用词返修清单（发给 goai_画图 那条线）

来源：`layout_guard.py` 的 D2 检查——把图件 PDF 里的文字抽出来，和正文用的术语表
（`templates/glossary_materials_zh.json` 的 `zh_normalize` + `chem_library` 的 anti-pattern）逐条比对。

第五轮交付的三张 BYZSO 图里有 13 处用词与正文不一致。正文早已按术语表统一过，
图件是另一条流水线做的，没走同一套词表，所以对不上。**要改图源，不要改正文。**

## fig01_evidence_synthesis_map
| 图里现在写的 | 应改为 |
|---|---|
| 热史 | 热历史 |
| 谱系 | 系列 |

## fig02_route_variable_matrix
| 图里现在写的 | 应改为 |
|---|---|
| 结构身份 | 结构归属 |
| 批量相纯 | 块体相纯 |
| 成相 | 相形成 |
| 处方 | 配方 |
| 慢冷 | 缓冷 |

## fig03_research_roadmap
| 图里现在写的 | 应改为 |
|---|---|
| 高温溶液长晶 | 高温溶液法晶体生长 |
| 谱系 | 系列 |
| 结构近邻 | 结构相关化合物 |
| 批量相区 | 块体相区 |
| 固相成相 | 固相反应 |
| 慢冷 | 缓冷 |

## 改完怎么验

图源改好、重新导出到各报告的 `figures/pdf/` 之后，在排版线上跑：

```bash
bash goai_research/tools/build_and_guard.sh
```

D2 应该清零，四份报告全部 PASS。英文图件同理，只是英文没有对应的中文词表，
D2 目前只拦中文写法。

## 建议：从源头堵

画图那条线在导出前也跑一次同样的检查即可（不需要整个 layout_guard）：

```bash
python3 goai_research/tools/layout_guard.py --figdir <导出目录> --src <正文目录> --lang zh
```
