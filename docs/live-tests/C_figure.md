# C. 图纸环节（goai-figure）真实外部 CLI 实测报告

- 日期：2026-08-27　执行人：figure 环节实测 agent（二轮：首轮建链，本轮全量真机复核并修正 CLI 事实）
- 范围：`server/figure_server.py` 全部 6 个 MCP tool，经真实 stdio 协议驱动；
  draw.io Desktop CLI 真实导出（本任务重头戏——参数插入 bug 修复后的真机验证）
- 环境：macOS (arm64)，Python 3.11.14（`REPO/.venv`），mcp SDK 2.1.1，
  draw.io Desktop **31.3.2**（`/Applications/draw.io.app/Contents/MacOS/draw.io`，
  `--version` 实测；首轮报告误记 26.0.9，已更正），cairosvg 2.9.0（venv 预装，
  本次未新装任何包），libcairo via Homebrew（需 `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`）
- 产物：`workspace_live/figure/`（本轮清空重跑生成：`raw/` 15 份逐调用记录、
  `figures/` 四套产物、逆向边界样例 `harder.*`）
- 回归测试：`tests/live/test_live_figure.py`（20 用例，`pytestmark = pytest.mark.live`，
  drawio CLI 不存在时相关用例自动 skip）
  跑法：`.venv/bin/python -m pytest -m live tests/live/test_live_figure.py -v`
  证据模式：前缀 `GOAI_FIGURE_LIVE_WS=$REPO/workspace_live/figure`

## 结论

**20/20 PASS，0 FAIL，0 SKIP**（本机 CLI 与 libcairo 均可用，无跳过项；
工作区清空后全量重跑，杜绝陈旧产物干扰）。
**draw.io 导出链路真实打通**：PNG（`-s 2` 缩放实测生效，放大比 1.998）、PDF、
SVG 均产出合法文件。本轮新发现并修复 1 个 Electron 会话级怪癖（F6，可杀死
终端前台启动的 server）。离线回归 `pytest tests/ -q` → **25 passed** 保持全绿。

## 1. 实测项清单

| # | 实测项 | 结果 | 证据 |
|---|--------|------|------|
| 1.1 | MCP stdio 握手 + tool 清单 | PASS | server=`goai-figure`，6 tools：drawio_export / figspec_schema / list_figures / render_figure / svg_file_to_drawio / validate_figspec |
| 1.2 | figspec_schema | PASS | 返回 shapes(10)/arrows(3)/rules/example，`raw/01_schema.json` |
| 1.3 | validate_figspec（合法 12 节点谱） | PASS | `{ok:true, errors:[]}` |
| 1.4 | validate_figspec（3 类错误谱） | PASS | 精确报 3 条：非法 shape『warp_core』、边端点『ghost』未知、节点 a/b 重叠（`raw/03_validate_bad.json`） |
| 1.5 | validate_figspec（非 JSON） | PASS | `{ok:false, errors:["JSON 解析失败: …"]}` |
| 2.1 | render_figure 全链路（12 节点/3 组/13 边/2 texts，8 种 shape） | PASS | figspec 5910B + svg 11719B + drawio 11522B，全部落在 `$GOAI_WORKSPACE/figures/` 下；耗时 0.39s |
| 2.2 | SVG 合法性与内容 | PASS | ElementTree 解析通过；12 节点 label、13 边 label、3 组 label 全部存在；`marker-end`×13（箭头齐全）；dashed 组/边有 `stroke-dasharray` |
| 2.3 | drawio mxGraph 结构 | PASS | `mxfile→diagram→mxGraphModel→root`；3 组均为 `container=1` vertex；12 节点 parent 正确（组内节点坐标=相对坐标，逐节点核对）；13 边 `edge=1` 且 source/target 与 spec 一一对应；dashed 边含 `dashed=1`；e9/e12 waypoints `<Array><mxPoint>`×2 |
| 2.4 | list_figures 对齐 | PASS | fig_pipeline 行 figspec/svg/drawio 三者 true |
| 3.1 | **drawio CLI 导出 PNG（-s 2）** | PASS | `figures/drawio/fig_pipeline.png` 357931B，magic `\x89PNG\r\n\x1a\n`，**2405×1398**（默认导出实测 1204×700，放大比 **1.998**，`-s 2` 真实生效）；MCP 端到端耗时 2.1–3.0s（两轮实测） |
| 3.2 | **drawio CLI 导出 PDF** | PASS | `fig_pipeline.pdf` 67373B，magic `%PDF-`；耗时 1.0–1.1s |
| 3.3 | CLI 能吃我们生成的 .drawio | PASS | PNG/PDF 两次导出零报错、rc=0——mxGraph 输出格式合法性的真机证明 |
| 3.4 | 导出超时路径 | PASS | `GOAI_DRAWIO_TIMEOUT=0.05` 触发 → `{ok:false, error:"drawio CLI 导出超时（0.05s）"}`；F6 修复后按进程组 SIGKILL（连 Electron GPU/utility 子进程），实测无残留进程、无半成品文件；随后重导成功（不破坏后续能力） |
| 3.5 | 陈旧产物防误判 | PASS | 旧 png 存在 + 本次导出失败（corrupt XML 真实过 CLI）→ 正确报 `ok:false` 且旧产物已被前置清除 |
| 4.1 | 正向 SVG → 逆向 figspec → drawio 往返 | PASS | 定量见 §2；逆向产物 drawio 结构合法（vertex/edge 计数核对） |
| 4.2 | 「更难」SVG 边界(嵌套 transform/polyline/tspan/scale/曲线 path) | PASS | 能力边界如实固化，见 §2.2 |
| 5.1 | preview png 自检（cairosvg） | PASS | `figures/png/fig_pipeline.png` 220997B，PNG magic，**2560×1440**（画布 1280×720 的精确 2×；与 drawio 导出口径不同，后者按内容包围盒 1204×700）；需 `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`（无此 env 时 import cairosvg 直接 OSError，server 已降级处理） |
| 6.1 | 非法 figspec 直接 render | PASS | 结构化 `{ok:false, error:"figspec 校验失败: …warp_core…"}`，校验详情完整透出（F5）；server 存活（后续调用正常） |
| 6.2 | svg_file_to_drawio 路径不存在 | PASS | `{ok:false, error:"文件不存在: …/nope.svg"}` |
| 6.3 | drawio_export 输入不存在 | PASS | `{ok:false, error:"文件不存在: …/ghost.drawio"}`，0.0s 返回（前置拦截；若真过 CLI，该路径实测要挂 19–48s，见 §3.4） |
| 6.4 | drawio_export 非法格式 | PASS | `{ok:false, error:"不支持的格式 bmp"}` |

离线回归：`.venv/bin/python -m pytest tests/ -q` → **25 passed**（修复前后均全绿）。

## 2. 逆向往返保真度（定量，本轮清空重跑复核）

### 2.1 自产 SVG 往返（fig_pipeline，12 节点/3 组/13 边）

| 指标 | 保留率 | 丢失明细与根因 |
|------|--------|----------------|
| 分组 | **3/3** | 容器识别 + 成员归属全对 |
| 节点 | **11/12** | `document`（Survey Draft）由贝塞尔曲线 path 构成 → 逆向器按设计跳过曲线；`cylinder`（Paper Library）退化为顶盖 ellipse 小节点（主体是曲线 path） |
| 节点 label | **10/12** | 上述两个特殊形状的 label 变成独立 texts（未丢内容，丢归属）；缺 Paper Library / Survey Draft |
| 边 | **10/13** | e7/e8/e9 均连接未被恢复的 draft 节点，端点吸附（60px）失败 |
| 边 label | **10/13** | 随边丢失（sections / figures / cites） |
| dashed 边 | 2/3 | e8 随边丢失 |
| shape 还原 | diamond/parallelogram/stadium/rounded/ellipse 正确 | polygon 顶点数与圆角启发式有效 |

结论：**矩形系/多边形系图形往返保真度高（组 100%、节点 92%、边 77%）**；
损失全部可归因于曲线形状（document/cylinder），与 `svg2drawio.py` 文档声明的
适用范围一致。

### 2.2 「更难」SVG 能力边界（harder.svg）

- 嵌套 `translate` 双层累计：**正确**（A@(40,30)、B@(240,40) 精确命中）
- `polyline` → 边 + waypoints：**正确**（A→B，waypoints [[200,55],[200,65]] 保留）
- `tspan` 多行文本：内容保留（itertext 拼接），**换行符丢失**（"line one"+"line two" 连成一段）
- `scale(2)` 变换：**不支持**（仅累计 translate；rect 按未缩放坐标 (10,150) 恢复）
- 贝塞尔曲线 `path`：按设计跳过，不产生边

## 3. draw.io Desktop CLI 真实行为记录（31.3.2 / macOS arm64）

1. **版本与退出码（更正首轮报告）**：`--version` = **31.3.2**。本版本退出码
   **有语义**：成功 rc=0，失败 rc=1（「输入文件不存在」打
   `Error: input file/directory not found`、「XML 损坏」打
   `Error: Export failed: <file>`，均 rc=1）。首轮报告的「版本 26.0.9、退出码
   恒 0」与本机实测不符，已更正。鉴于 rc 语义随版本漂移，代码继续以
   **「产物文件存在」为唯一成功信号**（跨版本稳妥），rc 仅作诊断字段透出。
2. **失败路径会杀死 TTY 前台进程组（本轮新发现，3 次复现）**：当 CLI 的
   stdio 直连终端（前台执行）且走到失败路径时，其退出会连带杀掉整个前台
   进程组——实测两类失败路径（输入不存在/XML 损坏）各自把发起它的 shell
   一并带走（后续 `echo` 不执行、shell 以 rc=1 消失）。stdio 走管道时父进程
   可存活。对 MCP server 的含义：stdio 拉起的 server 无 TTY 天然安全，但
   **手动在终端前台起 server 时任意一次坏导出可能连 server 一起杀**。
   已修复（F6：`start_new_session=True` 把 Electron 隔离进无控制终端的独立
   会话，怪癖被彻底旁路）。
3. **「输入文件不存在」路径极慢**：错误信息立刻打到 stderr，但进程滞留
   **19–48s** 才真正退出（两次实测 19.4s / 48.2s）。`drawio_export` 的前置
   存在性检查（F1 轮次的 F3 修复）因此不只是省 2s 冷启动，而是避开一次
   20–50s 的挂起。XML 损坏路径则 ~3.2s 正常退出。
4. `-s 2` 放在 `-f png` 与 `-o` 之间被正确接受（当初验收修的参数插入 bug
   真机确认已解决）：默认导出 1204×700，`-s 2` 得 2405×1398（×**1.998**）。
5. **导出尺寸按内容包围盒而非画布**（画布 1280×720 → scale1 导出 1204×700）。
   与 cairosvg preview（按画布，2560×1440）口径不同，对比图像时须注意。
6. 无需 `--no-sandbox`/`--disable-gpu`/虚拟显示器；Electron 每次调用冷启动，
   单次成功导出 1.8–3.0s（直调 CLI 1.8–1.9s；经 MCP 全链路 png 2.1–3.0s、
   pdf 1.0–1.1s）。
7. 超时（F6 后）：对新会话进程组 SIGKILL，实测无残留进程（`pgrep -fl draw.io`
   为空）、无半成品文件，随后导出能力不受影响。
8. CLI 会静默覆盖已存在的输出文件（代码另做前置删除，防失败时误判成功）。

## 4. 发现的问题与修复（均限 `server/figure_server.py`，最小改动）

| # | 问题 | 修复 |
|---|------|------|
| F1 | `GOAI_WORKSPACE` 完全未被 figure server 读取，而 README 承诺它是"所有产物的落盘位置"；stdio 拉起的 server CWD 不可控，默认 `workspace/figures` 落点随机 | 新增 `_default_out_dir()`；`render_figure`/`list_figures` 的 `out_dir` 缺省改为 `$GOAI_WORKSPACE/figures`（未设 env 时仍是 `workspace/figures`，向后兼容）。stdio 实测验证落点 |
| F2 | `drawio_export` 曾以 `returncode==0` 作为成功条件之一；rc 语义随 CLI 版本漂移，且旧产物残留时失败导出会**误报成功**并指向陈旧文件 | 导出前先删除已存在的 out_path；成功判定改为「导出后文件存在」；响应保留 `returncode` 字段供诊断 |
| F3 | 输入 .drawio 不存在时白白拉起 Electron，该路径实测挂 19–48s 才退出 | 前置存在性检查，0.0s 结构化返回 `文件不存在` |
| F4 | 超时硬编码 120s，超时路径无法被测试触发 | 改为 `GOAI_DRAWIO_TIMEOUT` env（默认 120s）；用 0.05s 真机触发验证结构化超时返回 |
| F5 | `render_figure` 收到非法 figspec 时裸抛 ValueError，mcp SDK 2.x 把详情吞成 `Error executing tool render_figure`，调用方看不到哪里错 | 捕获后结构化返回 `{ok:false, error:"figspec 校验失败: …"}`，校验详情完整透出 |
| F6（本轮新增） | CLI 失败路径退出时会杀死 TTY 前台进程组（§3.2，3 次复现）：终端前台手动起的 server 一次坏导出即可被连带杀死；且原 `subprocess.run` 超时只杀 Electron 主进程，GPU/utility 子进程不在清理范围 | `drawio_export` 改用 `Popen(..., start_new_session=True)`：Electron 进独立会话（无控制终端，怪癖旁路）；超时改为 `os.killpg(SIGKILL)` 整组清理后再结构化返回。真机复测：20/20 live 全绿，超时/损坏/成功三路径行为不变，无残留进程 |

未发现需要修改 `figspec.py` / `render_svg.py` / `render_drawio.py` /
`svg2drawio.py` 的缺陷（渲染两端结构实测全对；逆向器损失均在声明的能力边界内）。

## 5. 遗留建议（共享文件，只报告不改）

1. **README 环境变量表**：补 `GOAI_DRAWIO_TIMEOUT`（默认 120s）一行。
2. **README/文档**：注明 drawio CLI 行为随版本漂移（本机 31.3.2 失败 rc=1，
   旧版有失败 rc=0 报告），下游不要依赖 returncode 判成败；导出尺寸=内容
   包围盒（非画布）口径也值得注明。
3. **svg2drawio 后续增强（可选）**：识别 `render_svg` 自产的 cylinder/document
   路径签名，可把自产 SVG 往返保真度提到 12/12、13/13；`scale()` 变换与 tspan
   换行保留也是已知边界。
4. pyproject 的 `live` marker 已由并行实测工作流加入，无需重复处理；
   cairosvg（preview extra）在 venv 中已预装，本次未安装任何新包。
5. 首轮报告的「GUI 同开不影响 CLI 导出」结论本轮未复测（避免打扰桌面环境），
   如需背书请单独验证。
