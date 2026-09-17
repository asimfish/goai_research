"""Deck figures · S0-PAPER-FOUNDATION + S1-FIGURE-STRATEGY (+ embedded S2 prompt packages).

Two slides for the 世界人工智能开源大赛 deck that explain the literature system's multi-agent parallel loop:
  deck_loop_parallel  — 账本驱动的状态机与并行分派（who runs in parallel, what the ledger does, where the gates sit）
  deck_loop_converge  — 四条互搏通道与机械闸门收敛（why the loop converges instead of stalling or lying）

The "paper" here is the system's own specification, so every module and edge is anchored to a file:
  docs/LOOP_PROTOCOL.md (LP), docs/ARCHITECTURE.md (AR), skills/goai-orchestrator/SKILL.md (OR),
  tools/parallel_run.sh (PR), docs/competition/FINAL_REPORT.md (FR), and the formal run's RUN_MANIFEST.json /
  ledger.json under submission/03_运行与评测包/正式案例_BYZSO冷启动 (RUN).

Surface style: the paper design system the author accepted in rounds 4–6 (four render tiers, one line-art glyph
family, four colour families), re-mapped for a software system: slate-blue = agents (认知层), teal = deterministic
tools and gates (控制层), amber = issues / adversarial findings, gray = human decision outside the automatic loop.

Writes per project: outputs/S0-paper-foundation/{paper-foundation-report.md, s0-semantic-precision-contract.json,
framework-figure-risk-register.md}, outputs/S1-figure-strategy/{style-combination-pool.json, figure-strategy.md,
core-detail-display-matrix.json, edge-seed-contract.json}, outputs/S2-sketch-explore/{prompts/C0x.md, prompt-index.json}.
"""
import json
from pathlib import Path

RUN = Path(__file__).resolve().parent / 'studio'
CANVAS = '1536x1024'   # the image route's fixed size; the native rebuild re-lays the winner into a 16:9 slide

# ---------------------------------------------------------------- shared surface
HARD = """HARD CONSTRAINTS (framework schematic for one 16:9 conference slide, Chinese labels):
Opaque pure-white page. No slide title, no caption, no legend paragraph, no logo, no photograph, no person, no 3D, no drop shadow, no gradient, no glow, no background texture, no watermark, no icons of robots or brains.
Visible text is Simplified Chinese exactly as listed in the whitelist below plus the listed code identifiers and numbers; write each label once, spelled exactly; no English sentences, no invented labels, no numbers that are not listed. Clean sans-serif (Source Han Sans / 思源黑体), horizontal; code identifiers in the same sans-serif, never in a monospace box.
Every arrow has exactly one arrowhead at its destination and connects exactly the two elements named in the routing list. Between two blocks draw one bundled connector, never several parallel lines with the same meaning. No decorative or unexplained connectors."""

TIERS = """RENDERING TIERS (obey strictly — this is the figure's information hierarchy):
- TIER 1 macro group: a large rounded region with a very light tint, a 1 px border in the group's hue and a small bold group label in one corner. Groups are containers only; they carry no content of their own.
- TIER 2 primary module: a white card with a 6 px accent bar in the group's hue, a bold dark title, and ONE small line-art glyph beside the title. Only true modules are cards. Cards within a group share one width and one height.
- TIER 3 internal mechanism: INSIDE a module card that the source describes as a sequence, draw its steps as a compact chain of small rounded tokens joined by short 1.5 px arrows. A card whose source gives no sequence carries recorded items as plain tokens with no arrows between them; a card that the source describes as a pair of opposed roles carries two tokens joined by one short double-headed arrow.
- TIER 4 labels: every gate name, criterion, count or caveat rides on a connector, a port or a small pill tag. None of them is ever its own box.
Nothing may appear at a tier above its role: a gate, a metric, a caveat or a file name is never a module card."""

MOTIF = """LINE-ART GLYPH FAMILY (one family for the whole figure, no exceptions):
Every glyph is monochrome dark slate (#1F2937), drawn with uniform thin strokes of equal weight, no fill, no shading, no colour, no perspective, geometric and flat, about 28 px on a 1536-wide canvas, beside its module title. Glyphs are schematic office and control objects (ledger book, padlock, checklist, document stack, magnifier, fork node, gate diamond, fingerprint, shield, pen, table grid, hourglass). All glyphs share the same stroke weight and the same optical size; none has a filled or tinted background."""

PALETTE = """COLOUR (four families, three tints each, nothing else):
- SLATE-BLUE = agent skills, the cognitive layer: tint #EEF2F7, accent #5B7592, text #2B3E57
- TEAL = deterministic tools, ledger and gates, the control layer: tint #E6F2F3, accent #1F7F8C, text #0F4F58
- AMBER = issues, adversarial findings, caveats: tint #FFF6E3, accent #C48A24, text #7A5410
- GRAY = human decision outside the automatic loop: tint #F5F6F7, accent #9AA3AB, text #5B6570
Connectors #4B5563, body text #3F4854, hairlines #DCE2E8, page white. Every element takes its colour from its group's family; a card never mixes two families. No gradients, no shadows, no glow, no second blue, no pure black."""

DOMINANCE = """WEIGHT AND SPACING:
- The main reading path occupies 55-70% of the canvas and sits on the optical centre line; supporting groups are visibly lighter and smaller; caveat material stays under 15%.
- Cards inside a group are equal in size and evenly spaced; gutters between groups are twice the gutters inside a group; margins are equal on all four sides.
- Composition fills about 92% of the width and 88% of the height. No empty quadrant, no giant arrows, no decoration.
- SLIDE LEGIBILITY: this figure is projected on a conference slide and read from the back of a room. The smallest visible label must stay at least 2.2% of the image height; if the content does not fit at that size, wrap the layout into more rows rather than shrinking the type."""

POOL = [
    ('SC1', '分层横带', 'banded tiers: two to four full-width horizontal group bands stacked top to bottom, one band per semantic group, cards in a row inside each band, vertical connectors between bands',
     'stage-by-stage narrative', 'high row alignment, easy scaling to a wide slide'),
    ('SC2', '单主干左右', 'left-to-right mainline: one horizontal spine of cards, forks and merges only where the source says so, feedback returned as a dashed line below the spine',
     'process narrative', 'strongest reading order, weakest for wide content'),
    ('SC3', '枢纽辐射', 'hub and branches: one anchor entity at the left or centre, branches fanning to grouped leaves, criteria on the branch labels',
     'taxonomy narrative', 'best for classification, no implied time order'),
    ('SC4', '账本为轴', 'ledger-centric: one wide record band as the pivot in the middle, producers above it, consumers below it',
     'comparison narrative', 'makes "everything is written to one ledger" literal'),
    ('SC5', '阶梯＋汇流', 'ladder and bus: an ordered column on one side with an axis, a bundled bus collecting the members into a single pivot, the excluded member bypassing the pivot',
     'ordering narrative', 'encodes an order without geometry that reads as a number'),
    ('SC6', '蛇形分段', 'serpentine steps: numbered cards wrapping across two or three rows, the wrap arrow carrying the hand-off label',
     'itinerary narrative', 'keeps type large on wide step sequences'),
    ('SC7', '双栏对照', 'two-column compare: two parallel lanes answering two different questions, a shared header of inputs and a shared footer of outcomes',
     'contrast narrative', 'best when exactly two mechanisms are compared'),
    ('SC8', '嵌套容器', 'nested containment: an outer context frame with inner groups, a small inset for what lies outside the automatic boundary',
     'scope narrative', 'shows what is inside vs outside the automatic loop'),
]
LABEL = {sc: lab for sc, lab, *_ in POOL}
LAYOUT = {sc: lay for sc, _l, lay, *_ in POOL}
NARRATIVE = {sc: nar for sc, _l, _lay, nar, _t in POOL}
TRADE = {sc: t for sc, _l, _lay, _n, t in POOL}

# ---------------------------------------------------------------- the two figures
FIGS = {}

FIGS['deck_loop_parallel'] = dict(
    title='多智能体并行回环（一）· 账本驱动的状态机与并行分派',
    slide='关键技术实现 · 多智能体并行回环 1/2',
    rq='一个研究主题进来后，七个专职智能体怎样被账本按阶段分派、并行干活而互不冲突？',
    ml='研究主题 → 范围界定 → [文献检索 ∥ 风格库] → 引用核查 → 分类法 → [图件 ∥ 写作 ∥ 实验构想] → 对抗审稿 → 终稿交付；回环账本是唯一状态源，每个阶段的出口闸门落在账本上',
    priority='system/process（多智能体流水线的控制结构），mainline 是阶段状态机；数据流不作主干',
    sources={
        'AR': 'docs/ARCHITECTURE.md（一图总览、分层设计、账本结构、并行模型）',
        'LP': 'docs/LOOP_PROTOCOL.md（阶段与闸门表、流程机械约束、并行执行协议）',
        'OR': 'skills/goai-orchestrator/SKILL.md（"你只做四件事"、阶段状态机、并发是默认）',
        'PR': 'tools/parallel_run.sh（tasks.tsv 四列、分片产物、exit=3、BLOCKED_DEPENDENCY）',
        'FR': 'docs/competition/FINAL_REPORT.md §3（认知层 / 确定性工具层 / 控制层，九道闸门）',
        'RUN': '正式案例_BYZSO冷启动/RUN_MANIFEST.json（29 批 / 40 个子任务 / 单批最多 4 路 / 134 次 MCP 调用）',
    },
    entities=[
        ('编排器 goai-orchestrator', 'OR 开头："建账本 → 分派 → 验闸门 → 路由返工"，四件事', '控制层卡，卡内四步机理链'),
        ('回环账本 ledger.json', 'AR §3：gates / issues / log 三个字段；loopctl 原子写 + 排它文件锁；gate 带 sha256 产物指纹', '控制层账本卡，卡内三行记录项'),
        ('并行 runner parallel_run.sh', 'PR 头注释 + LP 并行执行协议：tasks.tsv 每行 任务名/提示词/产物/依赖 → 子进程各写自己的分片文件 → 汇合者等全部退出码', '控制层卡，卡内四步机理链'),
        ('范围界定', 'LP 阶段 0：orchestrator + 人；gate scope_confirmed', '认知层阶段卡'),
        ('文献检索 goai-lit-search', 'LP 阶段 1 + 并发证据：lit_coverage 需 ≥3 条 lit_search done 分片；OR："lit_search 按子主题切 ≥3 路并发"', '认知层阶段卡，卡内三个并行分片 token（无箭头）'),
        ('风格库 goai-style-bank', 'OR 状态机：与 lit_search 两路并行；gate style_bank_ready', '认知层阶段卡'),
        ('引用核查 goai-ref-guard', 'LP 阶段 2：references.bib 零 UNVERIFIED/MISMATCH；gate ref_integrity', '认知层阶段卡'),
        ('分类法 goai-survey-writer', 'LP 阶段 3：每叶 ≥3 篇支撑；gate taxonomy_ready', '认知层阶段卡'),
        ('图件 goai-figure-studio', 'LP 阶段 4a；OR："figures 按图并发"；并发证据 ≥2 条', '认知层阶段卡（三路并行之一）'),
        ('写作 goai-survey-writer', 'LP 阶段 4b；OR："writing 按章节并发"；并发证据 ≥2 条', '认知层阶段卡（三路并行之一）'),
        ('实验构想 goai-idea-forge', 'LP 阶段 4c：每条 idea 过对抗审 + 引用二审，材料 idea 带前驱体预测', '认知层阶段卡（三路并行之一）'),
        ('对抗审稿 goai-reviewer', 'LP 阶段 5：0 blocker 且 0 major，≥2 轮；issue 带 target 路由回源头阶段', '认知层阶段卡'),
        ('终稿交付', 'OR 第 7 条：tex+pdf、references.bib、figures 三件套 + 重建脚本、审计记录、账本全文', '主干终点，tier-4 交付标签'),
        ('九道出口闸门', 'LP 阶段表 + FR §3 "九道流程闸门"：scope_confirmed / lit_coverage / style_bank_ready / ref_integrity / taxonomy_ready / figures_ready / draft_complete / ideas_reviewed / review_pass', 'tier-4 药丸，落在账本带上，绝不是卡片'),
    ],
    relations=[
        ('编排器 ⇄ 回环账本', 'AR "唯一可信状态源。所有 agent 只通过 loopctl 读写"；OR "所有状态只存在于回环账本…不允许口头交接"', '一条捆绑双向连线，标签 loopctl 读写 · 文件锁'),
        ('编排器 → 阶段主干', 'OR 第 3 条 "逐阶段分派——并发是默认，串行是降级"', '一条分派连线进入主干起点'),
        ('范围界定 → {文献检索, 风格库}', 'OR 状态机 "[lit_search ∥ style_bank] ← 两路并行"', '唯一的第一个分叉'),
        ('{文献检索, 风格库} → 引用核查 → 分类法', 'LP 阶段 1→2→3 前置顺序', '汇合后主干两段'),
        ('分类法 → {图件, 写作, 实验构想}', 'OR "[figures ∥ ideas ∥ writing] ← 三路并行"；LP "4a/4b/4c 无写冲突，可并行"', '唯一的第二个分叉'),
        ('{图件, 写作, 实验构想} → 对抗审稿 → 终稿交付', 'LP 阶段 5→6', '汇合后主干两段'),
        ('对抗审稿 ⇢ 责任阶段（虚线）', 'LP Issue 路由表 + 级联规则', '只画一条虚线回到主干，标签 issue 路由返工（细节见下一页）'),
        ('每个阶段 → 账本带上的闸门药丸', 'AGENTS.md 铁律 1 "收工必须 loopctl log --event done"；LP 并发证据', '阶段卡与账本带之间不逐一拉线：闸门药丸直接坐在账本带上、与阶段对齐，表示"落账"'),
        ('并行 runner → 两个分叉点', 'LP 并行执行协议：分片文件、文件锁串行化账本、汇合者等 exit 码', '两条短线从 runner 卡到两个分叉点，标签 各写自己的分片文件'),
    ],
    contract=dict(
        contribution_type_visual_priority='system/process',
        role_visual_realization_contract=[
            dict(role='七个专职智能体的并行', scientific_meaning='并行 = 各自只写自己的分片文件，收工在账本记一条 done；账本靠文件锁串行化；汇合者等全部退出码',
                 positive_visual_instruction='在两个分叉点把并行支线画成并排的等宽卡（2 路和 3 路），从同一个分叉点出发、在同一个汇合点并入一束',
                 negative_visual_instruction='禁止把七个智能体画成七条各自完整的流水线；禁止画智能体之间互相对话的连线'),
            dict(role='闸门', scientific_meaning='闸门是阶段的出口条件，记录在账本里，由 loopctl 机械核验',
                 positive_visual_instruction='闸门名做成 tier-4 药丸，坐在账本带上、与对应阶段对齐',
                 negative_visual_instruction='禁止把闸门画成卡片或菱形判定框；禁止把闸门名放进阶段卡标题'),
            dict(role='账本', scientific_meaning='唯一状态源：gates / issues / log 三个字段 + 产物指纹',
                 positive_visual_instruction='一张宽账本卡或一条横贯全幅的账本带，卡内三行记录项',
                 negative_visual_instruction='禁止画成数据库圆柱或云；禁止让阶段卡各拉一条线到账本（用对齐表示落账）'),
            dict(role='审稿返工', scientific_meaning='issue 带 target 路由回责任阶段；细节在下一页',
                 positive_visual_instruction='一条虚线从对抗审稿回到主干，标签 issue 路由返工',
                 negative_visual_instruction='禁止从审稿卡向每个阶段各画一条线'),
        ],
        forbidden_misimplementation_locks=[
            '不得把七个智能体画成七条完整流水线（并行 = 分片写 + 账本汇合，不是复制流程）',
            '不得画智能体之间互相对话的连线（口头交接无效，账本是唯一状态源）',
            '闸门不是模块：只能是账本带上的药丸，不得画成卡片或菱形',
            '不得从审稿卡向每个阶段各画一条返工线（只画一条虚线回主干）',
            '不得把 MCP 服务器画成独立模块（工具调用只出现在统计标签里）',
            '不得出现"大脑""机器人"类隐喻图元',
        ],
        process_instance_budget=dict(default_canonical_process_count=1, note='全图只有一条阶段主干；两个分叉各自并回主干'),
        downstream_s1_s4_carry_forward=[
            'S1/S4 的 forbidden-edge list 必须含"智能体 ↔ 智能体"与"阶段卡 → 账本逐一拉线"两条',
            'S4 的 dashed-line budget 只允许一条虚线语义：issue 路由返工',
            '并行支线必须是等宽并排卡 + 同源分叉 + 同点汇合；分叉点旁挂并发证据标签',
        ],
    ),
    scores={'SC4': 9, 'SC1': 8, 'SC2': 8, 'SC3': 7, 'SC8': 6, 'SC5': 6, 'SC6': 5, 'SC7': 4},
    picked=['SC4', 'SC1', 'SC2', 'SC3'],
    why={
        'SC4': '账本为轴把"一切写进同一个账本"画成字面意义：账本带横贯中间，阶段主干在上、编排器与 runner 在下，闸门药丸落在带上；最贴近 AR "唯一可信状态源"。',
        'SC1': '分层横带把控制层 / 认知层 / 闸门三段并列，直接对应 FR §3 的分层表述；与 SC4 的差异在叙事角色（分层 vs 以账本为轴）。',
        'SC2': '单主干最贴近 OR 状态机的线性陈述，两个分叉与一条虚线返工都能画在同一条主干上；账本退为主干下方的带。',
        'SC3': '枢纽辐射把编排器放在枢纽、七个智能体成扇形叶，正是 AR 一图总览的画法；并行在这里读成"同时被分派"，分叉语义弱但分派语义强。',
    },
    rejected_reason={'SC8': '内外框语义在本图不存在（人类旁路在下一页）', 'SC5': '阶段之间没有需要排序的同类项',
                     'SC6': '主干只有六段，不需要换行', 'SC7': '不是两个机制的对照'},
    nodes=['控制层组（teal）：编排器 goai-orchestrator（卡内四步机理链：建账本 → 分派 → 验闸门 → 路由返工）；回环账本 ledger.json（宽账本卡，卡内三行记录项：闸门 gates · 问题 issues · 日志 log，每行一个勾选标记）；并行 runner parallel_run.sh（卡内四步机理链：tasks.tsv → 子进程 → 各写自己的分片文件 → 汇合）',
           '认知层组（slate-blue）：阶段卡按主干顺序：范围界定 / 文献检索 goai-lit-search（卡内三个并排分片 token：子主题 1 · 子主题 2 · 子主题 3，无箭头）/ 风格库 goai-style-bank / 引用核查 goai-ref-guard / 分类法 goai-survey-writer / 图件 goai-figure-studio / 写作 goai-survey-writer / 实验构想 goai-idea-forge / 对抗审稿 goai-reviewer',
           '主干终点：终稿交付 tex · pdf · bib · 图源 · 账本（tier-4 交付标签，不是卡）',
           '账本带上的九个闸门药丸（teal）：scope_confirmed / lit_coverage / style_bank_ready / ref_integrity / taxonomy_ready / figures_ready / draft_complete / ideas_reviewed / review_pass，末端一个 check-done 退出码 0',
           '两个分叉点旁的并发证据标签（teal 药丸）：≥3 路分片 · 各记一条 done；按图 · 按章节 · 按目标 并发',
           '统计标签（gray 药丸，一次）：正式运行 29 批 · 40 个子任务 · 单批最多 4 路 · 134 次 MCP 工具调用'],
    edges=['编排器 ⇄ 回环账本（一条捆绑双向连线，标签 loopctl 读写 · 文件锁）',
           '编排器 → 范围界定（分派）',
           '范围界定 → 文献检索 与 风格库（唯一的第一个分叉，两路并排）',
           '文献检索 与 风格库 → 引用核查（并入一束）→ 分类法',
           '分类法 → 图件 · 写作 · 实验构想（唯一的第二个分叉，三路并排）',
           '图件 · 写作 · 实验构想 → 对抗审稿（并入一束）→ 终稿交付',
           '对抗审稿 ⇢ 主干（一条虚线回到第二个分叉点之前，标签 issue 路由返工）',
           '并行 runner → 两个分叉点（两条短线，标签 各写自己的分片文件）'],
    forbidden=['不得从任一阶段卡单独拉线到账本卡（闸门药丸与阶段对齐即表示落账）',
               '不得给分类法、引用核查等卡片编造内部步骤链（源文本只给出口条件）',
               '不得把九个闸门画成九个菱形或九张卡',
               '不得画 MCP 服务器、数据库、云'],
    wl=['研究主题', '范围界定', '文献检索', '风格库', '引用核查', '分类法', '图件', '写作', '实验构想', '对抗审稿', '终稿交付',
        '编排器', '回环账本', '并行 runner', '建账本', '分派', '验闸门', '路由返工', '闸门', '问题', '日志',
        '子进程', '各写自己的分片文件', '汇合', '子主题 1', '子主题 2', '子主题 3',
        '认知层', '控制层', 'loopctl 读写 · 文件锁', 'issue 路由返工', '≥3 路分片 · 各记一条 done', '按图 · 按章节 · 按目标 并发',
        'tex · pdf · bib · 图源 · 账本', '正式运行 29 批 · 40 个子任务 · 单批最多 4 路 · 134 次 MCP 工具调用',
        'goai-orchestrator', 'goai-lit-search', 'goai-style-bank', 'goai-ref-guard', 'goai-survey-writer', 'goai-figure-studio',
        'goai-idea-forge', 'goai-reviewer', 'ledger.json', 'parallel_run.sh', 'tasks.tsv', 'gates', 'issues', 'log',
        'scope_confirmed', 'lit_coverage', 'style_bank_ready', 'ref_integrity', 'taxonomy_ready', 'figures_ready',
        'draft_complete', 'ideas_reviewed', 'review_pass', 'check-done 退出码 0'],
    core_detail=[('编排器', '四步机理链 建账本 → 分派 → 验闸门 → 路由返工（tier 3）', 'OR 开头'),
                 ('回环账本', '三行记录项 + 勾选标记（tier 3，无箭头）', 'AR §3'),
                 ('并行 runner', '四步机理链 tasks.tsv → 子进程 → 各写自己的分片文件 → 汇合（tier 3）', 'PR 头注释、LP 并行执行协议'),
                 ('文献检索', '三个并排分片 token，无箭头（tier 3）', 'LP 并发证据 ≥3'),
                 ('其余阶段卡', '无内部机理链：源文本只给出口条件，只画标题 + 图元', 'LP 阶段表')],
    risks=[('九个闸门名在一条账本带上排不下（英文标识符较宽）', 'S1/S4：允许药丸两行排列或缩短为阶段对齐的短药丸；原生重建时按幻灯片字号实测', 'risk_locked'),
           ('生图模型会把并行画成七条流水线', '契约锁 1；S3 把"复制流水线"记 high', 'risk_locked'),
           ('生图模型会给阶段卡编造内部步骤', '禁止清单；S3 记 high', 'risk_locked')],
)

FIGS['deck_loop_converge'] = dict(
    title='多智能体并行回环（二）· 四条互搏通道与机械闸门收敛',
    slide='关键技术实现 · 多智能体并行回环 2/2',
    rq='这个回环为什么会收敛——谁在互相挑错，谁在机械把关，什么时候停？',
    ml='本轮产物 → 四条互搏通道挑错 → issue 带 target 经路由表回责任阶段 → 只重跑受影响链路、指纹变更把下游闸门置回 PENDING → 下一轮；无 issue 时 check-done 机械放行 → 交付；三条终止旁路通向人',
    priority='mechanism（收敛机制），mainline 是一轮回环的闭合路径；数据流不作主干',
    sources={
        'OR': 'skills/goai-orchestrator/SKILL.md 第 3 条"四条互搏通道"、第 4 条验收、第 6 条终止条件',
        'LP': 'docs/LOOP_PROTOCOL.md（Issue 路由表、级联规则、轮次与终止、反空转、流程机械约束）',
        'AR': 'docs/ARCHITECTURE.md §3（gate 带 receipt 与 inputs 指纹；check-done 重算指纹）',
        'FR': 'docs/competition/FINAL_REPORT.md §3（审稿人与执行者职责分离；三视角审稿；同一问题三轮未收敛转人工）',
        'RUN': '正式案例_BYZSO冷启动/ledger.json（2 轮；11 个 issue：4 blocker · 4 major · 3 minor 全部关闭；51/51 引用核对）+ FR §4（首轮 7 项 issue，第二轮 0）',
    },
    entities=[
        ('本轮产物', 'OR 第 7 条交付物：稿件 / 图件 / 实验方案 / 引用库', '主干起点卡（slate），卡内四个产物 token'),
        ('执行者 ⇄ 审稿人', 'OR 互搏通道 1；FR "独立上下文…领域、方法和编辑三个视角"；LP review_pass ≥2 轮', '通道卡，卡内一对角色 token + 双向短箭头 + 判据行'),
        ('提案者 ⇄ 攻击者', 'OR 互搏通道 2："idea-forge 内部提案-攻击双角色 + 引用二审"', '通道卡'),
        ('候选 ⇄ 审计', 'OR 互搏通道 3："figure-studio 两轮候选制的 issue-ledger 审计"', '通道卡'),
        ('稿件 ⇄ 机械守卫', 'OR 互搏通道 4："bib_guard/tex_guard/…/academic_language_guard 的机械互搏——检查不过即返工，模型说了不算"', '通道卡'),
        ('issue 路由表', 'LP Issue 路由表：target → 接活阶段（lit_search / ref_gate / taxonomy / figures / writing / ideas）', '控制层账本卡，卡内六行"问题 → 阶段"记录项'),
        ('级联失效', 'LP 级联规则 + AR：gate 带 --inputs 指纹，check-done 重算，上游变更自动把 gate 置回 PENDING', '控制层卡，卡内四步机理链'),
        ('loopctl 拒绝写入', 'LP 流程机械约束表：前置顺序 / 并发证据 / 审稿轮次 / 回执与 PDF / 完整性', '控制层卡，卡内五行勾选记录项'),
        ('check-done', 'LP 终止条件 1 的四个机械判据 (a)–(d)', '控制层卡，卡内四步机理链，出口 退出码 0'),
        ('终止旁路', 'LP 终止条件 2、3 + 反空转', 'gray 卡，卡内三个 token（无箭头）'),
        ('统计', 'RUN + FR §4', 'tier-4 gray 药丸'),
    ],
    relations=[
        ('本轮产物 → 四条通道', 'OR "四条互搏通道…验收时逐条核对"', '一条分叉进四张并排卡'),
        ('四条通道 → issue 路由表', 'LP "review 产出的 issue 按 target 字段路由回源头阶段"；amber 标签 issue 带 target · severity', '四路并入一束'),
        ('issue 路由表 → 级联失效 → 本轮产物（下一轮）', 'LP "上游返工后，其下游闸门自动失效需复核"、"一轮…返工只重跑受影响链路"', '一条虚线闭环，标签 只重跑责任阶段 · 下一轮'),
        ('issue 路由表 → check-done（无 issue 时）', 'LP 终止条件 1', '实线，标签 0 open blocker/major'),
        ('loopctl 拒绝写入 → 账本写入口', 'LP "loopctl gate 在写账本时拒绝一切绕过行为"', 'loopctl 卡挂在路由表与 check-done 之间，一条短线标签 写不进去'),
        ('check-done → 交付', 'LP 终止条件 1 "退出码 0 → 交付"', '主干终点'),
        ('回环 → 终止旁路', 'LP 终止条件 2（max-rounds）、3（三轮未收敛 → 升级人类）、反空转 stall', '一条实线从回环侧面出去到 gray 卡；不接回'),
    ],
    contract=dict(
        contribution_type_visual_priority='mechanism',
        role_visual_realization_contract=[
            dict(role='互搏通道', scientific_meaning='两个职责分离的角色互相挑错：审稿人独立上下文，守卫是确定性脚本',
                 positive_visual_instruction='一张卡内一对角色 token 用一个双向短箭头相连，下面一行判据',
                 negative_visual_instruction='禁止把一条通道画成两条流水线；禁止画成打架、盾牌对撞的隐喻'),
            dict(role='issue 路由', scientific_meaning='issue 带 target 与 severity，经路由表回到责任阶段，只重跑受影响链路',
                 positive_visual_instruction='四条通道并入一束进路由表；路由表是唯一的中继，一条虚线闭环回到本轮产物',
                 negative_visual_instruction='禁止从每条通道各拉线到各阶段（蛛网）'),
            dict(role='机械放行', scientific_meaning='check-done 只按四个机械判据返回 0；loopctl 在写入时拒绝绕过',
                 positive_visual_instruction='两张 teal 工具卡，判据做成勾选行 / 机理链，出口标签 退出码 0',
                 negative_visual_instruction='禁止把 check-done 画成智能体或人'),
            dict(role='终止旁路', scientific_meaning='轮次上限、三轮未收敛、空转三种情况把决定交给人',
                 positive_visual_instruction='一张 gray 卡在回环之外，一条实线从回环出去，不接回',
                 negative_visual_instruction='禁止把升级人类接回主环；禁止画人形'),
        ],
        forbidden_misimplementation_locks=[
            '互搏通道不是两条流水线：一张卡内一对角色 token + 一个双向短箭头',
            '不得从审稿直接向各阶段拉线；issue 只经路由表回流',
            '升级人类是灰族旁路，不接回主环',
            '只允许一种虚线语义：下一轮返工',
            'check-done 与 loopctl 不是智能体，是 teal 工具卡',
            '不得出现打架、拳击、盾牌、法官、天平等隐喻图元',
        ],
        process_instance_budget=dict(default_canonical_process_count=1, note='一条闭合回环 + 一个放行出口 + 一个旁路出口'),
        downstream_s1_s4_carry_forward=[
            'S1/S4 的 forbidden-edge list 必须含"通道 → 阶段（绕过路由表）"与"升级人类 → 主环"两条',
            'S4 的 dashed-line budget 只允许一条虚线语义：下一轮返工',
            '四条通道必须等宽并排，卡内机理是"一对 token + 双向短箭头 + 判据行"',
        ],
    ),
    scores={'SC2': 9, 'SC1': 8, 'SC8': 8, 'SC7': 7, 'SC4': 7, 'SC5': 5, 'SC6': 4, 'SC3': 3},
    picked=['SC2', 'SC1', 'SC8', 'SC7'],
    why={
        'SC2': '单主干把"产物 → 挑错 → 路由 → 返工 → 下一轮"画成一条闭合回环，放行出口在主干末端；最贴近 LP "一轮 = 阶段 1→5 走完一遍"。',
        'SC1': '分层横带把 互搏通道 / 路由与返工 / 机械放行 三段并列，读者一眼看到"谁挑错、谁路由、谁把关"；虚线返工走在带外。',
        'SC8': '嵌套容器用外框表示自动回环，升级人类落在框外的小插区，直接呈现 LP "人类介入点"的边界语义。',
        'SC7': '双栏对照把"互相挑错（认知层对抗）"与"机械把关（控制层拒绝）"分成两栏，共享上游产物与下游交付，突出"模型说了不算"。',
    },
    rejected_reason={'SC4': '路由表是中继而非比较轴', 'SC5': '通道之间没有序关系', 'SC6': '不是步骤序列', 'SC3': '主干是闭环不是分类'},
    nodes=['起点卡（slate-blue）：本轮产物（卡内四个 token：稿件 · 图件 · 实验方案 · 引用库，无箭头）',
           '互搏通道组（slate-blue，四张等宽卡，每张卡内一对角色 token 用一个双向短箭头相连，下面一行判据）：执行者 ⇄ 审稿人（独立上下文 · 三视角 · 两轮起）/ 提案者 ⇄ 攻击者（实验构想内部对抗 · 引用二审）/ 候选 ⇄ 审计（图件两轮候选制 · issue 台账）/ 稿件 ⇄ 机械守卫（bib_guard · tex_guard · pdf_guard · 语言守卫 —— 检查不过即返工）',
           '路由与返工组（teal）：issue 路由表（账本卡，卡内六行：覆盖缺口 → 文献检索 / 引用可疑 → 引用核查 / 分类不 MECE → 分类法 / 图文不符 → 图件 / 无证据断言 → 写作 / 未落到工艺与前驱体 → 实验构想）；级联失效（卡内四步机理链：上游产物变更 → 指纹重算 → 下游闸门置回 PENDING → 复核）',
           '机械放行组（teal）：loopctl 拒绝写入（卡内五行勾选：跳阶段 / 缺并发证据 / 单轮审稿 / 无回执 / 非 TeX 编译的 PDF）；check-done（卡内四步机理链：九个闸门全部落账 → 无未关闭的 blocker/major → 回执指向真实审稿记录 → 指纹未变，出口标签 退出码 0 → 交付）',
           '终止旁路卡（gray，回环之外）：三个 token：达到轮次上限 → 带遗留清单交付 / 同一问题三轮未收敛 → 升级人类 / 连续两次无新增日志 → 空转，换策略',
           'amber 标签（一次）：issue 带 target · severity',
           '统计标签（gray 药丸，一次）：正式运行 2 轮：首轮 7 项 issue 路由返工，第二轮 0 blocker · 0 major · 0 minor；11 个 issue 全部关闭'],
    edges=['本轮产物 → 四条通道（一条分叉进四张并排卡）',
           '四条通道 → issue 路由表（四路并入一束，束上挂 amber 标签 issue 带 target · severity）',
           'issue 路由表 → 级联失效 ⇢ 本轮产物（一条虚线闭环，标签 只重跑责任阶段 · 下一轮）',
           'issue 路由表 → check-done（实线，标签 0 open blocker/major）',
           'loopctl 拒绝写入 → issue 路由表与 check-done 之间的账本写入口（一条短线，标签 写不进去）',
           'check-done → 交付（主干终点，标签 退出码 0）',
           '回环 → 终止旁路（一条实线从回环侧面出去，不接回）'],
    forbidden=['不得从任一通道卡直接连到文献检索/写作等阶段（只经路由表）',
               '不得把四条通道画成四条流水线或四对打架的人',
               '不得把升级人类接回回环',
               '不得出现第二种虚线'],
    wl=['本轮产物', '稿件', '图件', '实验方案', '引用库', '互搏通道', '执行者', '审稿人', '提案者', '攻击者', '候选', '审计', '机械守卫',
        '独立上下文 · 三视角 · 两轮起', '实验构想内部对抗 · 引用二审', '图件两轮候选制 · issue 台账', '检查不过即返工',
        'issue 路由表', '覆盖缺口 → 文献检索', '引用可疑 → 引用核查', '分类不 MECE → 分类法', '图文不符 → 图件', '无证据断言 → 写作', '未落到工艺与前驱体 → 实验构想',
        '级联失效', '上游产物变更', '指纹重算', '下游闸门置回 PENDING', '复核', '只重跑责任阶段 · 下一轮',
        '机械放行', 'loopctl 拒绝写入', '跳阶段', '缺并发证据', '单轮审稿', '无回执', '非 TeX 编译的 PDF', '写不进去',
        'check-done', '九个闸门全部落账', '无未关闭的 blocker/major', '回执指向真实审稿记录', '指纹未变', '退出码 0', '交付', '0 open blocker/major',
        '终止旁路', '达到轮次上限 → 带遗留清单交付', '同一问题三轮未收敛 → 升级人类', '连续两次无新增日志 → 空转，换策略',
        'issue 带 target · severity', '路由与返工',
        '正式运行 2 轮：首轮 7 项 issue 路由返工，第二轮 0 blocker · 0 major · 0 minor；11 个 issue 全部关闭',
        'bib_guard · tex_guard · pdf_guard · 语言守卫'],
    core_detail=[('四条互搏通道', '一对角色 token + 一个双向短箭头 + 一行判据（tier 3）', 'OR 第 3 条四条通道'),
                 ('issue 路由表', '六行"问题 → 阶段"记录项，无箭头（tier 3）', 'LP Issue 路由表'),
                 ('级联失效', '四步机理链（tier 3）', 'LP 级联规则、AR 指纹'),
                 ('loopctl 拒绝写入', '五行勾选记录项（tier 3）', 'LP 流程机械约束表'),
                 ('check-done', '四步机理链 + 出口标签（tier 3）', 'LP 终止条件 1 (a)–(d)'),
                 ('终止旁路', '三个 token，无箭头（tier 3）', 'LP 终止条件 2、3、反空转')],
    risks=[('文字量大：路由表六行 + 拒绝清单五行 + 判据四行', 'S1/S4：允许把路由表与拒绝清单各压成一张卡，字号不低于 2.2% 画布高；原生重建按幻灯片字号实测', 'risk_locked'),
           ('生图模型会把互搏画成打架/对撞隐喻', '契约锁 6；S3 记 high', 'risk_locked'),
           ('生图模型会把升级人类接回主环', '契约锁 3；S3 记 high', 'risk_locked')],
)


# ---------------------------------------------------------------- S0
def write_s0(pid, f):
    s0 = RUN / pid / 'outputs' / 'S0-paper-foundation'
    s0.mkdir(parents=True, exist_ok=True)
    src = '\n'.join(f'- **{k}** = {v}' for k, v in f['sources'].items())
    ents = '\n'.join(f'| {a} | {b} | {c} |' for a, b, c in f['entities'])
    rels = '\n'.join(f'- **{a}** — 证据：{b}；画法：{c}' for a, b, c in f['relations'])
    c = f['contract']
    roles = '\n'.join(f"- 「{r['role']}」→ {r['scientific_meaning']}\n  - 安全画法：{r['positive_visual_instruction']}\n  - 禁止：{r['negative_visual_instruction']}"
                      for r in c['role_visual_realization_contract'])
    risks = '\n'.join(f'| {a} | {b} | {c_} |' for a, b, c_ in f['risks'])
    (s0 / 'paper-foundation-report.md').write_text(f"""# S0-PAPER-FOUNDATION — {pid}

- 图：{f['title']}
- 用途：{f['slide']}（世界人工智能开源大赛 · SAGE-Mat 答辩 PPT，16:9）
- contribution_type_visual_priority：{f['priority']}
- primary_reader_question：{f['rq']}
- visual_mainline_decision：{f['ml']}

## S0-00 输入清点
本图的"论文"是系统自己的规范文档与正式运行记录（仓库 asimfish/goai_research）：
{src}

运行时 = 5090 Codex `image_gen`（route lock）；生图画布 {CANVAS}（图像通道固定尺寸）；原生重建目标 = 16:9 幻灯片内容区（1536×864 画布，标题栏之下）。

## S0-01 精读：实体与证据锚点
| 实体 | 证据 | 出图角色 |
|---|---|---|
{ents}

## 关系（每条连线的证据）
{rels}

## S0-02 语义精度契约（摘要，完整版见 s0-semantic-precision-contract.json）
{roles}

## S0-03/04 风险筛查与锁定
| 风险 | 处置 | 状态 |
|---|---|---|
{risks}

## S0-06 readiness
`S0_FOUNDATION_READY_WITH_RISK` — 缺口已在风险寄存器中锁定，且全部转成"不得画"的约束，不阻塞 S1。
""", encoding='utf-8')
    (s0 / 's0-semantic-precision-contract.json').write_text(json.dumps(dict(
        project_id=pid, figure=f['title'], primary_reader_question=f['rq'], visual_mainline_decision=f['ml'], **c),
        ensure_ascii=False, indent=1), encoding='utf-8')
    (s0 / 'framework-figure-risk-register.md').write_text(
        f'# framework-figure-risk-register — {pid}\n\n| 风险 | 处置 | 状态 |\n|---|---|---|\n{risks}\n\nreadiness: S0_FOUNDATION_READY_WITH_RISK\n', encoding='utf-8')


# ---------------------------------------------------------------- S1 + S2 packages
def prompt_text(f, sc, c0):
    locks = '\n'.join('- ' + x for x in c0['forbidden_misimplementation_locks'])
    roles = '\n'.join(f"- {r['role']}: {r['positive_visual_instruction']} 禁止：{r['negative_visual_instruction']}"
                      for r in c0['role_visual_realization_contract'])
    return f"""Draw one flat framework schematic for a 16:9 conference slide explaining a multi-agent research pipeline (Chinese labels). Canvas {CANVAS}; compose the content as a wide band so it re-lays cleanly into a 16:9 slide.

{HARD}

LAYOUT GRAMMAR FOR THIS CANDIDATE ({sc} · {LABEL[sc]}, narrative role: {NARRATIVE[sc]}):
{LAYOUT[sc]}

{TIERS}

{MOTIF}

{PALETTE}

{DOMINANCE}

MODULES TO DRAW:
{chr(10).join('- ' + n for n in f['nodes'])}

CONNECTIONS (draw exactly these, nothing else):
{chr(10).join('- ' + e for e in f['edges'])}

ROLE REALIZATION (from the S0 precision contract — obey literally):
{roles}

FORBIDDEN (any of these makes the candidate unusable):
{chr(10).join('- ' + x for x in f['forbidden'])}
{locks}

VISIBLE TEXT WHITELIST (write each exactly once, nothing else):
{' | '.join(f['wl'])}"""


def package(pid, f, cid, sc, c0):
    cd = '\n'.join(f'| {a} | {b} | {c} |' for a, b, c in f['core_detail'])
    return f"""# {pid} · {cid} · {LABEL[sc]}

- source_style_combination_id: {sc}
- first_round_default_style_id: formal_publication_schematic
- surface_style_decision: 沿用作者在第四至六轮视觉认可的设计系统（四级层级 + 单一线稿图元族 + 四族配色），色族按软件系统重新映射（slate=智能体、teal=确定性工具与闸门、amber=issue、gray=人）；本轮的发散轴是 layout grammar 与 narrative role。
- figure_intent: complete framework figure（整页幻灯片范围）
- primary_reader_question: {f['rq']}
- visual_mainline_decision: {f['ml']}
- narrative_role: {NARRATIVE[sc]}
- layout_grammar: {LAYOUT[sc]}
- selection_rationale: {f['why'][sc]}

## core_detail_display_matrix
| 模块 | 内部机理的画法 | 证据锚点 |
|---|---|---|
{cd}

## s0_precision_carry_forward
{chr(10).join('- ' + x for x in c0['downstream_s1_s4_carry_forward'])}

## strict prompt audit
contribution-type visual priority: {c0['contribution_type_visual_priority']}；data-flow 不作为主干。
edge-support ledger: 上面每条连线都在 S0 报告里有文件锚点。
connector multiplicity: 每对模块之间只有一条捆绑连线。
false relay: 没有模块转发它不消费也不改变的东西（路由表消费 issue.target 并改写为阶段）。
variable placement: 所有闸门名/判据/计数/警示只出现在连线标签、端口或药丸标签上。
modularity-not-fragmentation: 模块数 {len(f['nodes'])} 组，未碎片化。
simple internal motif: 只有源文本给出顺序的模块才画机理链。
workflow redundancy: 全图只有 {c0['process_instance_budget']['default_canonical_process_count']} 条完整流程。
background/context budget: <= 10%。
verdict: pass（repair cycles used: 1）

## IMAGE PROMPT
{prompt_text(f, sc, c0)}
"""


def write_s1_s2(pid, f):
    c0 = f['contract']
    s1 = RUN / pid / 'outputs' / 'S1-figure-strategy'
    s2 = RUN / pid / 'outputs' / 'S2-sketch-explore'
    (s2 / 'prompts').mkdir(parents=True, exist_ok=True)
    (s2 / 'generated').mkdir(exist_ok=True)
    s1.mkdir(parents=True, exist_ok=True)
    pool = [dict(style_combination_id=sc, label=LABEL[sc], layout_grammar=LAYOUT[sc], narrative_role=NARRATIVE[sc],
                 trade_off=TRADE[sc], score=f['scores'][sc], selected=sc in f['picked'],
                 rationale=f['why'].get(sc) or f['rejected_reason'].get(sc, '')) for sc in sorted(LABEL, key=lambda s: -f['scores'][s])]
    mapping = {f'C0{i + 1}': sc for i, sc in enumerate(f['picked'])}
    (s1 / 'style-combination-pool.json').write_text(json.dumps(dict(
        planned_combinations=8, selected_combinations=4,
        selection_rule='top four by score, with the constraint that the four differ in layout grammar and narrative role',
        mapping=mapping, pool=pool), ensure_ascii=False, indent=1), encoding='utf-8')
    rows = '\n'.join(f"| {p['style_combination_id']} | {p['label']} | {p['narrative_role']} | {p['score']} | {'✔' if p['selected'] else ''} | {p['rationale']} |" for p in pool)
    (s1 / 'figure-strategy.md').write_text(f"""# S1-FIGURE-STRATEGY — {pid}

{f['title']}

- primary_reader_question: {f['rq']}
- visual_mainline_decision: {f['ml']}
- contribution_type_visual_priority: {f['priority']}
- data-flow mainline justified? 否 —— 本图讲的是控制结构 / 收敛机制，数据类标签只作支撑。
- complete-framework eligibility: 四个候选都是整页范围的完整框架图，非局部探针。
- surface style: formal_publication_schematic（作者已接受的设计系统），色族按软件系统重新映射。

## 八种风格组合的规划与打分（选四）
| SC | 名称 | 叙事角色 | 分数 | 选中 | 理由 |
|---|---|---|---|---|---|
{rows}

映射：{'、'.join(f'{k}={v}' for k, v in mapping.items())}

四个选中组合的成分为什么互补而不冲突：它们共用同一层表面样式，只在 layout grammar 与 narrative role 上正交发散，
因此四张候选比较的是"同一套视觉语法下哪种版式最贴合系统语义"，而不是四种互相打架的画风。

## S0 语义精度契约的继承
{chr(10).join('- ' + x for x in c0['downstream_s1_s4_carry_forward'])}

## 禁止清单（写入四个候选的 negative constraints）
{chr(10).join('- ' + x for x in f['forbidden'])}
{chr(10).join('- ' + x for x in c0['forbidden_misimplementation_locks'])}

## 可见文字白名单
{' | '.join(f['wl'])}
""", encoding='utf-8')
    (s1 / 'core-detail-display-matrix.json').write_text(json.dumps(
        [dict(module=a, internal_mechanism=b, evidence=c) for a, b, c in f['core_detail']], ensure_ascii=False, indent=1), encoding='utf-8')
    (s1 / 'edge-seed-contract.json').write_text(json.dumps(dict(
        edges=f['edges'], forbidden_edges=f['forbidden'], dashed_semantics=[c0['downstream_s1_s4_carry_forward'][1]]),
        ensure_ascii=False, indent=1), encoding='utf-8')
    cands = []
    for cid, sc in mapping.items():
        (s2 / 'prompts' / f'{cid}.md').write_text(package(pid, f, cid, sc, c0), encoding='utf-8')
        cands.append(dict(candidate_id=cid, style_combination_id=sc, prompt_path=f'outputs/S2-sketch-explore/prompts/{cid}.md',
                          target_image_path=f'outputs/S2-sketch-explore/generated/{cid}.png', skip=False, size=CANVAS))
    (s2 / 'prompt-index.json').write_text(json.dumps(dict(
        stage='S2-SKETCH-EXPLORE', project_id=pid, first_round_default_style_id='formal_publication_schematic',
        candidates=cands, rows=cands), ensure_ascii=False, indent=1), encoding='utf-8')
    return mapping


def main():
    for pid, f in FIGS.items():
        write_s0(pid, f)
        mapping = write_s1_s2(pid, f)
        (RUN / pid / 'state').mkdir(exist_ok=True)
        (RUN / pid / 'state' / 'project-state.json').write_text(json.dumps(dict(
            project_id=pid, stage_completed=['S0-PAPER-FOUNDATION', 'S1-FIGURE-STRATEGY'], next='S2-SKETCH-EXPLORE',
            canvas=CANVAS, mapping=mapping), ensure_ascii=False, indent=1), encoding='utf-8')
        n = sum(len(f['wl'][i]) for i in range(len(f['wl'])))
        print(pid, '→', mapping, '| whitelist', len(f['wl']), 'strings,', n, 'chars')


if __name__ == '__main__':
    main()
