# B — 引用核查环节真实网络实测报告（refcheck）

- 日期：2026-08-27　实测人：Cursor agent（引用核查环节负责人）
- 范围：`server/refcheck_server.py`（MCP stdio 全链路）、`server/core/bibtex.py`、
  `tools/bib_guard.py` / `tools/tex_guard.py` / `tools/bank_check.py`
- 回归测试落盘：`tests/live/test_live_refcheck.py`（`pytestmark = pytest.mark.live`）
  跑法：`.venv/bin/python -m pytest -m live tests/live/test_live_refcheck.py -v`
- 实测产物：`workspace_live/refcheck/`（矩阵逐轮结果在 `artifacts/matrix_results.jsonl`，
  整文件审计产物在 `state/CITATION_AUDIT.{json,md}`，稿件工程样例在 `gates/`）
- 环境：`.venv`（mcp 2.1.1 / httpx 0.28.1 / pytest 9.1.1），`GOAI_WORKSPACE=workspace_live/refcheck`

## 结论

判定矩阵 10 条最终全部符合期望（首轮 7/10，三处偏差全部定位到根因并修复后复验通过）。
共发现 9 个问题（2 个高危判定逻辑缺陷、1 个外部数据源噪声放大缺陷、6 个健壮性问题），
全部在授权文件内以最小改动修复；离线 25 项单测全程保持通过。
修复收官后已补做一次 live 全量单遍复验：**20 用例一次性全过（含矩阵 10/10）**，
离线 25 项同步复跑通过（见 §二 最终回归）。

## 一、verify_entry 判定矩阵（核心）

矩阵构造：真实论文 + 人为损坏混合（定义见 `tests/live/_fixtures.py::MATRIX`）。
「首轮」= 修复前行为；「最终」= 修复后复验（─ = 修复期间未单独定向重跑）。
收官全量复验已将 10 条整表重跑一遍，全部与「期望」列吻合
（逐条裁决见 `artifacts/matrix_results.jsonl` 末 10 行）。

| # | 构造 | 期望 | 首轮实际 | 最终实际 | 一致性 |
|---|------|------|----------|----------|--------|
| M1 | ResNet 全对 + DOI（DOI 路由） | PASS | PASS | ─ | ✅ 一致 |
| M2 | Attention 全对、无 DOI（标题路由） | PASS | **MISMATCH**（作者 extra+missing、YEAR 2017vs2025） | **PASS**（canonical=arXiv 1706.03762/2017） | ✅ 修复后一致（P7+P8） |
| M3 | Depth Anything 2024 全对（arXiv 路由） | PASS | PASS | ─ | ✅ 一致 |
| M4 | ResNet 作者顺序打乱（前两位互换） | FIX 或 MISMATCH，含 order | FIX + AUTHORS/order | ─ | ✅ 一致（实际行为=FIX，order 不升级 MISMATCH） |
| M5 | ResNet 第三作者换编造名 | MISMATCH | MISMATCH + extra/missing | ─ | ✅ 一致 |
| M6 | Adam 年份 2015（arXiv 口径 2014） | FIX + off_by_one | FIX + YEAR/off_by_one | ─ | ✅ 一致 |
| M7 | ResNet venue 写 "Proc. CVPR" | FIX + venue drift | FIX + VENUE/drift | ─ | ✅ 一致 |
| M8 | Attention 标题 + ResNet 的 DOI | 非 PASS 且明确指出 DOI 指向他篇 | **UNVERIFIED**，reason 称"未找到权威记录"，action 误导"提供 doi 重试" | **MISMATCH + ID/id_conflict**，明确给出标识符解析出的论文 | ✅ 修复后一致（P5） |
| M9 | 完全编造条目（假标题+假作者+假 venue） | UNVERIFIED | UNVERIFIED | ─ | ✅ 一致 |
| M10 | ResNet 全对 + 编造 DOI（10.1109/CVPR.2016.99999） | 应发现 DOI 不实（FIX 级） | **PASS**（幻觉 DOI 完全逃逸） | **FIX + ID/doi_mismatch**，suggested_bibtex 带正确 DOI | ✅ 修复后一致（P6） |

**矩阵符合率：首轮 7/10 → 最终 10/10。**

M2 偏差深挖结论（判定逻辑 bug 与外部噪声兼有，见 P7/P8）：
- 外部实况：`Attention Is All You Need` 裸标题检索，Crossref/DBLP/OpenAlex 三源 top5
  **均无 2017 正版**（NeurIPS 不注册 Crossref；DBLP/OpenAlex 相关性被同名蹭热点文淹没）；
  OpenAlex 反而返回 sim=1.0 的 **2025 盗版重印记录**（doi `10.65215/2q58a426`，无 venue）；
  期间还实测到 Crossref 同名书章《Is Attention All You Need?》(sim 0.88) 与 DBLP 503 限流。
- 判定层放大：旧逻辑对同分候选盲选检索顺序第一名，且 `strip_accents` 折不掉 Ł
  （NFKD 不可分解），把「Lukasz Kaiser」vs「Łukasz Kaiser」判成两个人。

## 二、实测项清单

| 必测项 | 结果 | 证据 |
|--------|------|------|
| 1. MCP stdio 协议层（SDK stdio client 真实起 server、initialize、list_tools、call_tool） | PASS | `test_stdio_handshake_and_tool_surface`：server_info.name=goai-refcheck，工具面恰为 {verify_entry, verify_bib_file, deep_audit_info}，schema 含 bibtex_entry。注意 mcp 2.x API 差异（见 O3） |
| 2. verify_entry 判定矩阵 10 条 | PASS（修复后） | 上表；逐轮原始 JSON 在 `artifacts/matrix_results.jsonl`（M2×4 轮、M8/M10×2 轮） |
| 3. verify_bib_file 整文件核查（3 条混合：PASS+MISMATCH+UNVERIFIED） | PASS | `test_verify_bib_file_mixed_summary_and_artifacts`：total=3，counts={PASS:1,MISMATCH:1,UNVERIFIED:1}，gate=FAIL，JSON/MD 落盘于 `$GOAI_WORKSPACE/state/`（默认路径不再依赖 server CWD），MD 只列问题条目 |
| 4. deep_audit_info | PASS | `test_deep_audit_info_structure`：available 布尔、path、usage（不可用时给 clone 指引）、when_to_use 齐全，说明合理 |
| 5a. bib_guard 真实规模（2 节 tex、24 次引用、12 keys、≥600 词） | PASS | `test_bib_guard_realistic_numbers`：引用调用 24、去重 12、整合率 100%、密度约 35/千词（合理带内）；混入幻觉 key → 阻塞并点名；库塞 3 孤儿 → 整合率 80%<90% 阻塞 |
| 5b. tex_guard 真实多文件工程（main + \input×2 + 图引用） | PASS | `test_tex_guard_realistic`：好工程 labels:3/refs:3 → PASS；注入版五类问题（TODO 残留/`\input` 缺失/图缺失/悬空 ref/环境未闭合+错配）全部拦截 |
| 5c. bank_check 配套 citation_bank（7 条、近三年 86%） | PASS | `test_bank_check_realistic`：好库 → PASS；坏库三类违规（库外 key/缺强度标注/claim 过短+近三年占比不足）全部拦截；`--target-cites 10` 候选量闸门生效 |
| 6. 错误路径 | PASS（修复后） | `test_error_*`、`test_cli_missing_paths_structured`：verify_entry 空串/垃圾 → ERROR；bib 路径不存在 → ok:false；空 bib → ok:false（修复前 gate=PASS，见 P1）；缺右括号 bib → 结构化处理不崩溃且不丢字符（P3）；CLI 三工具坏路径 → 清晰报错无 traceback（P4） |

最终回归（2026-08-27 收官全量复验）：`tests/` 离线 **25 passed**；
live 全量单遍 **20 passed（86.95s）** —— stdio 握手、矩阵 10/10、整文件核查、
三闸门、错误路径一次性全过。证据：矩阵逐条裁决追加在
`artifacts/matrix_results.jsonl` 末 10 行（M1–M3 PASS；M4 FIX+order；
M5 MISMATCH+extra/missing；M6 FIX+off_by_one；M7 FIX+venue drift；
M8 MISMATCH+id_conflict；M9 UNVERIFIED；M10 FIX+doi_mismatch），
审计产物 `state/CITATION_AUDIT.{json,md}` 同轮刷新
（total=3，counts PASS/MISMATCH/UNVERIFIED=1/1/1，gate=FAIL 符合预期）。

## 三、发现的问题与修复

| # | 现象 | 根因 | severity | 状态 |
|---|------|------|----------|------|
| P1 | 空 bib / 解析不出条目的 bib → `gate: PASS`（fail-open：把引用删光即可过闸） | `verify_bib_file` 对 entries=[] 无守卫 | high | ✅ 已修：返回 `ok:false` 结构化错误，不发 PASS |
| P2 | 默认审计产物写到 server 进程 CWD 下的 `workspace/state`（MCP 宿主拉起时 CWD 不确定，产物写飞/写不进） | 相对路径默认值 | medium | ✅ 已修：默认值在设置 `GOAI_WORKSPACE` 时锚定 `$GOAI_WORKSPACE/state`；显式传参不受影响 |
| P3 | 缺右括号的条目被解析但**静默丢尾字符**（`Half open sentence`→`Half open senten`） | `parse_bibtex`/`_parse_fields` 扫描到 EOF 未闭合时仍按"已消费闭括号"减 1 | low | ✅ 已修：按 depth 判断是否减 1 |
| P4 | `bib_guard`（bib 缺失）、`bank_check`（两入参缺失）裸 traceback | 文件存在性未守卫（`tex_guard` 本就有守卫） | low | ✅ 已修：`sys.exit` 清晰消息 |
| P5 | 真标题挂他篇真论文的 DOI → 误判 UNVERIFIED（"未找到权威记录"），action 还引导"提供 doi 重试"（DOI 本身就是病灶） | DOI 解析成功但标题不符时，lookup 只返回 None，判定层无从区分"没找到"与"找到了但不是这篇" | **high** | ✅ 已修：新增 `id_conflict` 通道 → MISMATCH + `ID/id_conflict`，输出标识符实际解析出的论文，不给自动修正（须人工裁决） |
| P6 | 编造 DOI + 正确元数据 → PASS，**幻觉 DOI 完全逃逸**（防幻觉卖点的正面漏洞） | 声称 doi/eprint 与权威记录的一致性从未检查 | **high** | ✅ 已修：ID 轴新增 `doi_mismatch`/`arxiv_mismatch`（FIX 级，suggested_bibtex 带权威标识符） |
| P7 | 「Lukasz Kaiser」vs「Łukasz Kaiser」判为两个人 → 正确条目报 extra+missing | `strip_accents`（NFKD）对 Ł/ø/ß/đ 等**不可分解**拉丁字母无效；姓名比对直接用它 | medium | ✅ 已修：`bibtex.py` 增 `_LATIN_FOLD` 折叠层（textnorm.py 属禁改区，未动） |
| P8 | 标题路由：候选池被同名蹭热点文/盗版重印记录占据时，盲选检索顺序第一名 → 正确条目被判 FIX/MISMATCH，且 suggested_bibtex 会把正确引用"修"成盗版重印 | ① 排序仅看标题相似度，平分不看作者/年份佐证；② 裸查询在高频词标题下召回不了正版；③ 疑似区间 [0.75,0.92) 的零作者重合记录也能当 canonical | **high** | ✅ 已修：① 排序按（标题相似度, 作者重合率, 年份贴近度）决胜；② crossref/openalex/arxiv 改引号短语查询 + 标题路由补 arXiv 源（NeurIPS/ICLR/ICML 不在 Crossref）；③ 疑似区间须作者重合>0 才接受，否则 fail-closed 落 UNVERIFIED |
| P9 | 输出的 `canonical.sources` 恒为 null；venue 检查的 arXiv 豁免（`sources != ["arxiv"]`）是死代码 | 单源记录键名是 `source`（str），dedup_merge 后才有 `sources`（list），代码只认后者 | low | ✅ 已修：两者归一；M2 复验中豁免真实生效（canonical 为 arXiv 记录时不误报 booktitle） |

### 观察（不属于本环节修复范围 / 无需修复）

- **O1 外部数据源噪声实录**：OpenAlex 收录盗版重印记录（`10.65215/2q58a426`，
  Attention Is All You Need"2025 版"）；Crossref 有同名书章；DBLP 对连续查询返回
  503（http.py 有界重试后单源缺席，lookup 静默降级）。建议网络层考虑把"哪些源
  不可达"上抛（见遗留建议），本报告已转交网络层负责人参考。
- **O2 并行改动声明**：实测期间仓库存在网络层等并行未提交改动（`http.py`、
  `sources.py`、`litsearch_server.py`、`figure_server.py`、`retro.py`、
  `parallel_run.sh`、`pyproject.toml`）。本环节最终复验（矩阵定向重跑 + 离线 25 项 +
  live 零网络 9 项）均在当前工作区状态下通过；本人改动仅限授权四文件 + `tests/live/`。
- **O3 mcp 2.x SDK API 差异**（写测试时踩到，供后续实测人参考）：`CallToolResult.is_error`
  / `InitializeResult.server_info` / `Tool.input_schema`（snake_case），
  `call_tool(read_timeout_seconds=)` 接受**秒数 float**（1.x 是 `timedelta`）。
  server 侧 `mcp_compat` 无问题。
- **O4 verify_bib_file 空文件曾写出 total=0 的审计报告**：P1 修复后不再落盘空报告。

## 四、修复清单（最小改动，均在授权文件内）

| 文件 | 改动 |
|------|------|
| `server/refcheck_server.py` | P1 空 bib fail-closed；P2 out_dir 锚定 GOAI_WORKSPACE；P5 id_conflict 通道与 MISMATCH 裁决；P6 ID 轴 doi/arxiv 一致性检查；P8 短语查询、arXiv 源、（标题,作者,年份）决胜排序、疑似区间收紧；P9 source/sources 归一 |
| `server/core/bibtex.py` | P3 未闭合扫描不丢尾字符（两处）；P7 `_LATIN_FOLD` 姓名折叠 |
| `tools/bib_guard.py` | P4 bib 缺失守卫 |
| `tools/bank_check.py` | P4 bank/bib 缺失守卫 |
| `tests/live/test_live_refcheck.py` + `tests/live/_fixtures.py` | 新增：可持久化 live 回归（20 用例：stdio 握手/判定矩阵×10/整文件/deep_audit_info/错误路径×3/三闸门×3/CLI 坏路径） |

禁改区（textnorm/http/sources）与共享文件（pyproject/test_offline/README）均未改动。

## 五、网络请求记账

预算：≤15 次条目核查/轮。实测轮消耗 **22 次条目核查当量**：首轮全量 13（矩阵 10+
整文件 3）、修复复验 8（M2×3 轮迭代、M8/M10 各 1、整文件重跑 3）、根因定位重放 1。
超出部分全部用于修复验证闭环，已尽量定向重跑（`-k`）而非全量。收官复验轮另消耗
**13 次**（一次全量，预算 ≤15 内，全程无 429/503）。每次核查 2–4 个 HTTP GET，经
`http.py` 同主机 1s 节流；实测轮仅 DBLP 一次 503（有界重试语义正常）。今后每次全量
live 运行固定消耗 13 次核查（已写入测试文件头部说明）。

## 六、遗留建议（只报告不改）

1. **共享/禁改区**（转交对应负责人）：
   - `http.py`/`sources.py`：单源限流失败目前被 lookup 静默吞掉，建议把"源不可达"
     信息上抛，refcheck 可在 UNVERIFIED 时提示"部分权威源本轮未参与"（降低误杀）；
   - DBLP 503 的 Retry-After 偶尔较长，`RETRY_BUDGET=45s` 下单条核查可能明显变慢，
     批量核查（verify_bib_file）建议考虑跨条目的源级熔断。
2. `verify_bib_file` 对大 bib 是逐条串行网络核查，100 条约需数分钟；建议按
   DOI/归一化标题做进程内缓存与去重（重复条目/重跑场景显著省流量）。
3. `suggested_bibtex` 的 key 由权威记录重新生成（如 `he2016deep_fakeauthor`→
   `he2016deep`），直接替换会破坏正文 `\cite`；建议 `record_to_bibtex` 透传原 key。
4. `README` 可补一节 live 实测跑法（`-m live`）与网络预算说明（共享文件，未动）。
5. M4（作者顺序打乱）实际行为为 FIX 级并给出修正 bibtex，order 不升级 MISMATCH；
   语义上可辩护（顺序可自动修正），但若产品口径认为乱序=高危（署名顺序纠纷），
   可把 `order` 加入硬性作者问题集合，一行改动。
