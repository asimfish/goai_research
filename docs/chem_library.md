# 化学写作词库 chem_library（2026-09-13）

用户问：“用词感觉有的不够专业，不是那么符合化学规范，你的并行 agent loop 系统里是否有
https://github.com/asimfish/super_library 这样的化学词汇库让文献的用词用句专业？”

## 先把事实说清楚：super_library 不是化学词库

克隆下来读过（`/data/liyufeng/super_library`，9.2 MB）：

| 项目 | 实际情况 |
|---|---|
| 定位 | `AGENTS.md` 第一句：“whenever the task involves **English AI-paper writing**, rewriting, translation, rebuttal, terminology, definitions, or related work” |
| 领域 | `general` / `world_models` / `reinforcement_learning` / `embodied_ai` / `robot_learning` / `vision_language_action` |
| 规模 | 274 条词条：definition 93、sentence_pattern 78、term 57、usage_note 29、phrase 14、anti_pattern 3；17 条 writing guide |
| 语言 | 英文 |
| 化学内容 | **没有** |

所以它不能直接用。**能用的是它的 schema 与方法**，这套是领域无关的：

1. **六种词条类型**：`term` / `definition` / `phrase` / `sentence_pattern` / `usage_note` / `anti_pattern`。
   关键在后三种——真正让文字变专业的不是术语表，是「在某个交际意图下本领域惯用怎么说」
   （sentence_pattern）与「本领域不这么说」（anti_pattern）。
2. **按 `domain × section × intent` 三维检索**，写之前只取一小批（`bundle --limit 4 --max-chars 24000`），
   不把整个词库塞进上下文。
3. **writing_guides**：每个章节一份写作协议，字段是 `purpose / use_when / inputs / moves /
   templates / verification / avoid`——把「这一节该怎么写」写成可执行的动作序列。
4. **audit 措辞 lint**：watchlist 正则 + 语料里的 anti_pattern，自动扫草稿。
   它自己也声明 lint 不能验证科学论断、引用覆盖、术语一致性，那些仍要人看。

## 我们的化学版

目录 `goai_research/templates/chem_library/`，CLI `goai_research/tools/chemlib.py`：

```
taxonomy.json              domains(7) / sections(9) / intents(10) / kinds(6)
entries/terms.jsonl        规范术语（中文 + en + 释义 + 用法边界 + 文献佐证）
entries/anti_patterns.jsonl  从我们自己正文里揪出来的不规范写法 + 改法
entries/sentence_patterns.jsonl  中文化学句式（证据 / 限定 / 缺口 / 比较 / 量值 / 定名 / 范围 / 衔接）
writing_guides.json        9 条章节写作协议
watchlist.json             lint 正则规则
```

`domains`：`solid_state_synthesis`（固相反应/煅烧/烧结）、`crystal_growth`（高温溶液法/助熔剂/提拉法/自熔）、
`phase_equilibria`（相图/相区/固溶度/共存相）、`crystallography`（结构精修/空间群/位点占据/调制结构）、
`characterization`（XRD/Rietveld/EDS/EPMA/ICP/HT-XRD/热分析）、`glass_ceramics`（玻璃析晶/成核—长大）、
`evidence_method`（检索、证据分级、可迁移性边界）。

### 与已有 glossary 的关系

`templates/glossary_materials_zh.json`（6 个领域分区 + `zh_normalize` 56 条替换规则）是 v3 那轮做的，
只解决「把非标准词换成标准词」。chem_library 是它的超集：把已有条目搬进新 schema 并补上英文对应、
释义、用法边界与文献佐证，再加上 glossary 没有的 sentence_pattern / anti_pattern / writing_guide 三层。
`zh_terms_apply.py` 的替换流程保留不变（它跑在编辑之前，做机械替换）。

## 用法

```bash
T=goai_research/tools/chemlib.py

python3 $T stats                                   # 词库规模
python3 $T audit sections_zh3/*.tex                # 措辞 lint（正则 + anti_pattern）
python3 $T audit sections_zh3/*.tex --severity high --json
python3 $T route --section condition_matrix --intent caution   # 写之前取一小批
python3 $T terms --domain crystal_growth           # 术语表
python3 $T guide                                   # 列章节协议
python3 $T guide <guide-id>                        # 看一条协议
python3 $T show <entry-id>
```

`audit` 会把 `\cite{}`、行内公式 `$...$`、`\ref/\label`、注释替换成等长空白再匹配，
所以化学式和引用键不会被误报，行号也保持不变。命中 high 级规则时退出码为 1，可以当门禁用。

## 在并行 agent loop 里的位置

```
零. chemlib audit sections_zh3/*.tex        → 措辞问题清单（按严重度排序）
一. 并行编辑代理（按文件分片）              → 每个代理先 chemlib route 取本节协议与句式，
                                              再逐条改 audit 报出来的问题
二. zh_qa.py sections_base sections_zh3     → 引用键/公式/交叉引用/数字/表格结构必须完全一致
三. chemlib audit 复扫                      → high 级必须清零
四. 5090 重编 → 版面复核（zh_layout_checklist.md）
```

编辑代理的硬约束与 v3 一致：只动措辞，不动 `\cite`、公式、`\ref/\label`、数值、表格结构；
拿不准的标 `uncertain` 交回来，不要自行改写科学论断。
