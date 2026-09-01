# goai_research 需求验收审计报告

- 审计对象：`<repo>` @ `b675fc9`（main，与 origin 同步）
- 证据来源：第 1–8 项由独立审计 agent（9e04ff87）采集，原始输出见本目录 `01_*.txt`–`08b_*.txt`；
  该 agent 在第 8 项后静默退出未写报告，第 8d、9–13 项由主 agent 补做（`08c/08d/09/10/11/12/13_*.txt`）。
- 审计中发现的缺陷已在同一工作日修复并附测试（见 §4），修复后复验结果一并记录。

## 1. 总体结论

**基本达标，审计发现 4 项缺陷（1 项功能性 bug、2 项协议漏洞、1 项合规残留），已全部修复并复验。**
统计：PASS 14 / PARTIAL→已修复 2 / FAIL→已修复 2 / UNVERIFIED 0（共 16 条：R1–R12 + A1–A4）。

## 2. 逐条判定

| 需求 | 判定 | 关键证据 | 缺口 / 处置 |
|---|---|---|---|
| R1 画图模块 + draw.io | PASS | `04_mcp_tools.txt`：goai-figure 6 工具（figspec_schema/validate_figspec/render_figure/svg_file_to_drawio/drawio_export/list_figures）；`05_figure_pipeline.txt`：pipeline.figspec → SVG 10111 B，.drawio 根 `mxfile`→`mxGraphModel`，27 mxCell、14 顶点 11 边全部绑定 source&target；`05b_drawio_export.txt`：真机 CLI `/Applications/draw.io.app/.../draw.io` 导出 PNG 227 KB（magic ok）与 PDF 50 KB | — |
| R2 文献搜索 agent | PASS | goai-litsearch 11 工具（多源 search_papers / snowball / lookup / download_pdf / save_to_library / coverage_report / export_bibtex + 本地语料 4 工具）；`skills/goai-lit-search/SKILL.md:13-22` 规模档（comprehensive 100–150，不足不得 PASS） | — |
| R3 引用检查 agent | PASS | `07_author_compare.txt`：缺失→MISMATCH、伪造→MISMATCH、顺序调换→FIX；对抗样本（同姓不同名、错首字母）均检出，缩写/Last-First/变音符号不误报；goai-refcheck 3 工具 verify_entry/verify_bib_file/deep_audit_info | — |
| R4 idea → 逆合成 → 审核 → 二次查验 | **FAIL→已修复** | `08_retro.txt`：本地两阶段无机模型权重/数据齐全、SHA256 校验通过，但依赖未装；`08c` 安装后 `08d_retro_real.txt` 首次调用崩：`IndentationError: chemistry.py line 421`（`56832aa` 入库时缩进损坏，vendored 代码不可 import）。修复后：`BaZn2Si2O7` → Top-3 路线，前驱体 ZnO/SiO₂/BaCO₃，`model_output_verified=true / chemical_route_verified=false`，`make_experiment_plan` 返回含 TODO 条件槽、safety 强制项与 review_gates 的骨架，6.4 s | 修一行缩进；新增 `test_vendor_retro_modules_compile`（零依赖 py_compile 兜底） |
| R5 loop 机制 | **PARTIAL→已修复** | `09_loopctl.txt`：账本/gate/issue/指纹/回合上限均真实；**漏洞 1**：只记 `scope_confirmed` 一个 gate，`check-done` 即返回 DONE（放行条件仅 `not failing and gates`）；**漏洞 2**：`review_pass` 无 `--receipt` 记 PASS 被接受；样例账本 `examples/survey_cof_her/ledger.json` 使用自造 gate 名（ref_audit/review_round1…）也曾被放行 | 引入 9 个必需 gate 集合（缺一即阻塞，跳过须显式 WARN）、`review_pass` 回执机械校验（无回执/trace 不存在/占位 <512 B 直接拒绝，check-done 再核）、非协议 gate 名当场警告；+2 测试 |
| R6 接 Codex / 并行 | PASS | `configs/codex.config.toml(.example)`、`configs/claude.mcp.json(.example)`；`03_check_servers.txt` 四 server 预检 ok；`tools/parallel_run.sh` TSV 契约（产物列/依赖列/超时产物策略，LOOP_PROTOCOL §并行执行协议 1–8）；orchestrator SKILL 「并发是默认，串行是降级」 | — |
| R7 GitHub 仓库 | PASS | `01_git.txt`：origin asimfish/goai_research，main 与远端一致，213 tracked files；`02_pytest_offline.txt` 46 passed（修复后 48） | — |
| R8 排版/写作方法论 | PASS | `12_skill_evidence.txt` R8：writer SKILL 贡献先行(L9)、引用支持库 + bank_check(L94-106)、章节蓝图(L115)、整合率 ≥90% halt rule(L12,102)、语言契约与中文模板(L19-25)；模板 Times/学术蓝/P 列/紧凑标题；`11_templates.txt` 两模板真实编译 0 错误 | — |
| R9 画图方法论 | PASS | figure-studio SKILL：策略合同/源忠实表(L41)、edge-label-first(L47)、两轮候选 4+2(L22,79)、配色合同 ≤2 主题色(L59-62)、可编辑化重建(L14)；`05_figure_pipeline.txt` lint errors/warnings 均 0 | — |
| R10 图转可编辑 | PASS | figure-editable SKILL 路线 A 确定性逆向 / 路线 B 视觉重建回环(L17,45)；`server/core/svg2drawio.py:49 svg_to_figspec`；`06_roundtrip_tests.txt` `test_svg_roundtrip_to_figspec` 通过 | — |
| R11 接入 draw.io | PASS | 同 R1 证据 + `figure_server.py:29,45,211`（GOAI_DRAWIO_CLI / CLI 自动探测 / drawio_export）；README:163 官方 draw.io MCP 接入说明 | — |
| R12 ARIS 式对抗设计 | PASS | reviewer SKILL 跨模型首选、全新会话(L14-15)、留痕 review_traces(L27-28)、降级 provisional 不得单独放行(L20-25)、不改稿；idea-forge 不自审(L9)、graveyard(L22,74)；orchestrator 四条互搏通道(L85)；本次修复后回执改为机械强制 | — |
| A1 外部归功清零 | **FAIL→已修复** | `13_attribution.txt`：4 处命中——两模板注释「paper-orchestra 风格/硬规则」、figure-studio SKILL:8-9 的 c-narcissus URL；README Ecosystem 的 super_skill_team 为 owner 自有仓库（允许） | 改为中性措辞，复查 0 命中 |
| A2 裸主题全流程 + 分级 scope | PASS | AGENTS.md:23-27、orchestrator SKILL:3,12,60-67、LOOP_PROTOCOL:112 | — |
| A3 制作质量层 | PASS | `10_guards.txt`：tex_guard 对 `\texttt{lin1999phase}`、中文紧贴 `据zou2021crystal报道`、数字题词 `zhang20202d` 全部阻塞，`\cite/\citealp/\nocite/\pageref` 零误报；bib_guard 对 doi+url 冗余与未保护 `BaZn2Si2O7/LLZO` 告警且不误伤已保护条目；`templates/survey_main_zh.tex` ctexart 编译通过；reviewer 制作质量维度(L48,66-67) | — |
| A4 学术内容契约 | PASS | writer SKILL 骨架强制项(L129-145)、坩埚/相图(L191-197)；lit-search 两条强制检索面；idea-forge 前驱体预测非可选(L51,58-60,89)；reviewer 材料检查单(L51-55)；orchestrator 子主题强制(L54) | — |

## 3. 原始输出

见本目录各 `NN_*.txt`（agent 采集：01–08b；主 agent 补做：08c/08d/09/10/11/12/13）。

## 4. 修复清单（按严重度）

1. **[功能 bug] vendored 无机逆合成模型不可 import** — `vendor/two_stage_retro/chemistry.py:421` 缩进错误。已修；新增零依赖编译测试。
2. **[协议漏洞] check-done 不要求必需 gate 存在** — 账本停在半路可宣告 DONE（第一次 BYZSO 冷启动正是这种形态）。已修：9 个必需 gate 缺一即阻塞；`status` 列出缺席项；非协议名警告。
3. **[协议漏洞] review_pass 回执无机械校验** — 无回执/占位 trace 的 PASS 曾被接受。已修：`gate` 命令拒绝，`check-done` 再核。
4. **[合规残留] 外部项目归功语句 4 处** — 已清零。

## 5. 未覆盖项（如实声明）

- 真网络 live 测试（tests/live，100 项）本次未跑（审计约束：不打真实 API）；上次实测报告见 `docs/live-tests/`。
- 逆合成 http 后端（ASKCOS/RXN）未接真实服务，只验证了本地两阶段模型与 stub 路径。
- 端到端冷启动（裸主题 → PDF）未在本机重跑；远端上一轮 23 页学术修订版为最近一次全流程实证。
