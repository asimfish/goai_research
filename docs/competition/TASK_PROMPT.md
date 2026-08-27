# 材料方向比赛任务 Prompt（GoAI Research 全流程）

> 用法：把本文件整体作为宿主 agent（Codex / Claude / Cursor）的任务指令，
> 替换 `{{...}}` 占位符后运行。系统会按回环协议产出全部比赛提交物。
> 评分口径：基本任务（文献调研）50% + 进阶路线 C（合成路线与工艺设计）50%。

---

## 任务指令（正文从此开始）

你是 GoAI Research 多智能体综述系统的宿主。仓库根目录 `{{REPO}}`，
Python 用 `{{REPO}}/.venv/bin/python`，工作区 `GOAI_WORKSPACE={{WORKSPACE}}`。
先读 `docs/LOOP_PROTOCOL.md` 与 `skills/goai-*/SKILL.md` 全部规程，然后以
orchestrator 身份按账本状态机推进，轮到哪个阶段就按对应 SKILL.md 执行。
**每个结论都要走真实工具调用**（检索/核查/渲染/闸门），禁止凭记忆编造。

### 研究主题

- **材料主题**：{{TOPIC}}
- **路线 C 目标物**：{{TARGET_MATERIAL}}（含代表性单体/前驱体的 SMILES，若适用）
- 目标读者：材料/化学方向研究生与评审专家；正文语言：英文；篇幅：{{PAGES}} 页级综述。

### 第一部分：基本任务 —— 文献调研报告（占比 50%）

按主回环完整执行 scoping → (lit_search ∥ style_bank) → ref_gate →
taxonomy → (figures ∥ writing) → review → final，硬性要求：

1. **文献覆盖针对性与规模**：把主题分解为 5±1 个 MECE 子主题；每个子主题经
   多源真实检索（arXiv + OpenAlex 必查，Crossref/S2/DBLP 择需），
   `coverage_report` 全子主题无缺口 + comprehensive 档配额（**库 ≥100 篇**、
   每子主题 ≥15、综述类 ≥8、近三年 ≥30%）才过 `lit_coverage` 闸门。
0. **领域风格库前置**：与 lit_search 并行跑 goai-style-bank——检索 30 篇
   本领域经典综述，产出写作/画图风格卡与范图库（`style_bank_ready` 闸门），
   写作与图纸阶段必须消费风格卡。
2. **知识抽取结构化**：每篇入库文献生成结构化阅读卡片（方法/材料体系/
   关键数值/局限），taxonomy 每叶 ≥3 篇支撑。
3. **Research Gap 识别质量**：产出 **≥5 条 Research Gap 清单**
   （`research_gaps.md`），每条必须：挂 ≥2 个库内真实引用 key 作证据链、
   注明证据来自哪个数据库（arXiv/OpenAlex/Crossref/...）、写明「为什么现有
   工作没有覆盖」的推理过程。Gap 清单同时进综述正文的 Open Challenges 节。
4. **证据链与引用完整性（红线）**：所有 `\cite` key 只能来自
   `references.bib`（由检索链路真实生成）；`ref_integrity` 闸门要求全库
   零 UNVERIFIED/MISMATCH；正文引用与参考文献一一对应由 `bib_guard`
   （整合率 ≥90%）+ `tex_guard` 双闸把守。**组委会会全文抽查引用真实性，
   虚假引用按违规处理**——这正是 refcheck 环节存在的意义，全部核查记录
   落 `CITATION_AUDIT.md` 作为可自证材料。
5. **交付格式**：报告以 LaTeX 撰写并**真实编译出 PDF**（本机有
   pdflatex/latexmk/bibtex），`.tex`、`.bib`、图与编译所需文件全部保留。
   主图走 goai-figure-studio 三段管线（策略合同 → AI 生图两轮候选 →
   可编辑化重建），辅助图走 figspec 直渲；一律交付 SVG（论文用）+
   .drawio（可编辑）双格式，主图另附两轮候选与审计 ledger。
   写作消费 super_library 语料（section 协议 + 句式卡 + 表格模板 +
   wording lint）与 style_bank 写作风格卡。

### 第二部分：进阶路线 C —— 合成路线与工艺设计（占比 50%）

基于第一部分识别的 Research Gap，以 idea-forge 规程产出：

1. **合成路线生成**：给定目标物 {{TARGET_MATERIAL}}，生成可行合成路线
   （前驱体选择、反应条件、步骤顺序），**每一步**标注：文献依据
   （库内真实引用 key）或化学原理推理；不能凭空生成。有真实逆合成后端
   （`GOAI_RETRO_PROVIDER=http`）时调用 `predict_retro` 并交叉验证；
   只有 stub 时，路线以文献追溯 + LLM 化学推理为主构建，stub 输出仅可
   作为系统集成演示并显式标注「演示数据，非化学结论」。
2. **工艺优化**：对该目标物的现行主流合成工艺提出 ≥2 条改进方案
   （产率提升/条件简化/成本降低），每条给出**量化依据**（文献报道的
   对比数值：温度、时长、产率、比表面积等），标明出处。
3. **合成验证与热力学可行性检验**：对路线中的中间体/前驱体做热力学
   稳定性论证——优先引用文献已报道的形成能/键能/可逆反应热力学数据；
   文献没有数值的项，如实列入「待计算清单」（注明建议的 DFT 泛函与
   软件设置），**禁止编造数值**。实验验证为可选项，列为后续工作。
4. **推理过程展示（核心要求）**：方案文档必须含「为什么选这条路线/
   这个条件」的决策记录（候选路线对比表 + 排除理由），这与账本审计
   天然一致：审稿轮次、issue、返工全程留在 ledger 里。
5. **对抗审核**：方案过 goai-reviewer 四维审（证据真实性/新颖性/
   可行性/安全性，safety 字段强制），再过引用二次核查，双关后
   `ideas_reviewed` 闸门才 PASS。

### 提交物清单（final 阶段逐项自查落盘）

| # | 提交物 | 路径 |
|---|--------|------|
| 1 | 文献调研报告 PDF（编译产物） | `{{WORKSPACE}}/drafts/main.pdf` |
| 2 | LaTeX 源码（.tex/.bib/图/编译文件） | `{{WORKSPACE}}/drafts/` + `library/references.bib` |
| 3 | Research Gap 清单（证据链+数据库标注） | `{{WORKSPACE}}/notes/research_gaps.md` |
| 4 | 引用真实性自证 | `{{WORKSPACE}}/state/CITATION_AUDIT.md` |
| 5 | 路线 C 合成/优化方案 + 验证证据 | `{{WORKSPACE}}/ideas/route_c_*.md` |
| 6 | 图（SVG + 可编辑 drawio + PNG） | `{{WORKSPACE}}/figures/` |
| 7 | 系统说明（架构+方法论，供评审复现） | `{{WORKSPACE}}/SYSTEM_NOTE.md` |
| 8 | 回环账本全文（过程可审计） | `{{WORKSPACE}}/state/ledger.json` |
| 9 | 审稿记录与回执 | `{{WORKSPACE}}/state/review_*` |

### 运行参数与纪律

- `loopctl init --topic "{{TOPIC}}" --max-rounds 4 --effort balanced --strictness normal --auto-proceed true`
- 人类确认点（scope 定稿、贡献声明、化学安全）在无人值守运行时由你代行
  并在账本 log 注明「代行」；正式参赛时这三处必须停下来等人。
- 检索预算：comprehensive 档——总库 100–150 篇、每子主题 ≥15 篇；
  核查预算：正文实际引用条目 100% 核查 + 其余库内条目全量核查
  （时间受限时正文引用优先，剩余抽样 ≥30% 并记账）；
  429 限流重试 ≤2 次后如实记录。
- 审稿至少 2 轮（第 1 轮必须产出真实 issue，禁止一轮全绿）；无跨模型
  通道时按降级规程记 provisional 并附回执。
- 终点判据：`loopctl check-done` 退出码 0 + 提交物清单 9 项全部存在。

---

## 本仓库实测实例化（2026-08-27）

| 占位符 | 实例值 |
|--------|--------|
| `{{REPO}}` | `/Users/liyufeng/Code/goai_research` |
| `{{WORKSPACE}}` | `{{REPO}}/workspace_live/competition` |
| `{{TOPIC}}` | Covalent organic frameworks (COFs) for photocatalytic hydrogen evolution |
| `{{TARGET_MATERIAL}}` | β-ketoenamine COF **TpPa-1**（单体：1,3,5-triformylphloroglucinol，SMILES `O=Cc1c(O)c(C=O)c(O)c(C=O)c1O`；p-phenylenediamine，SMILES `Nc1ccc(N)cc1`） |
| `{{PAGES}}` | 8–12 |
