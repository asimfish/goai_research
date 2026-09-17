"""Deck figures · round 2 — the loop-engineering style (author feedback 2026-09-17).

Round 1 carried the *paper* surface style onto a talk slide: muted slate/teal, line-art glyphs only, ~55 locked
strings, thin grey connectors. The author's verdict on both the native slides and the Codex sketches from those
prompts: "质量太低，没有顶会的质感", with a pointer to wanshuiyin/auto-claude-code-research-in-sleep (ARIS) and its
/method-figure skill. What that style does, and what this round adopts:

  * a BRIEF, not a whitelist: <= 14 components, each "label + one line of <= 8 Chinese characters", one headline claim
    and one headline number; the rest of the detail lives in the talk, not on the slide;
  * three NUMBERED pastel phase panels with bold coloured titles; white cards with soft shadows; core cards carry a
    small meaningful illustration or a character, not an abstract glyph;
  * flow KINDS in colour and a LEGEND: thick navy main flow, the RETRY loop as the visual hero (bold orange arc with
    its bound written on it), blue dashed dispatch, thin grey ledger writes;
  * an EVIDENCE strip that tells the loop as rounds with shrinking issue counts (real ledger data);
  * a locked cast (identity sheet) so both slides show the same characters;
  * short, positive bake prompts (over-specified forbid-lists flatten the result).

S0 semantics are unchanged (same anchors: LOOP_PROTOCOL / ARCHITECTURE / orchestrator skill / parallel_run.sh /
FINAL_REPORT §3 / the formal run's ledger); this is an S1 rerun with an explicit first-round surface-style override,
which the super_teaser contract allows when the author asks for it.

Writes: figure-studio-runs/{deck_cast, deck_loop_parallel_r2, deck_loop_converge_r2}/outputs/…
"""
import json
import shutil
from pathlib import Path

RUN = Path('/root/lyf/goai/final_round/figstudio/figure-studio-runs')
NAS = '/mnt/nas/data/lyf/goai/deck_figstudio'          # where the Codex agent sees the packages
CAST_REL = 'deck_cast/outputs/CAST/generated/CAST.png'

STYLE = """STYLE: the visual language of a top ML-paper "Figure 1" / a polished README method figure (think PaperBanana, AutoFigure, the ARIS method figure): PURE WHITE background; three soft pastel NUMBERED phase panels (pale blue, pale green, pale lavender) with bold titles in the panel's own colour; rounded white node cards with subtle soft shadows; every card = a bold dark title + ONE short grey line + a small meaningful illustration (a tiny document page, a table grid with ticks, a stack of papers, a flask, a chart thumbnail, a shield) — never an empty box, never a wall of text. Arrows carry the story: thick dark-navy main-flow arrows with large arrowheads; the RETRY loop is the visual hero — one bold ORANGE curved arrow with its label sitting on the line; BLUE DASHED arrows = dispatch; THIN GREY arrows = writes to the ledger; GREEN = pass. A small LEGEND box explains the arrow kinds. Crisp, confident, generously sized sans-serif Chinese text (思源黑体 / Source Han Sans, bold titles); code identifiers in a clean monospace. It must look hand-designed by a researcher for a conference talk — not a corporate org chart, not a game screenshot."""

CAST_RULE = """CHARACTERS: use ONLY the cast on the reference sheet, same faces, hair, clothes and colours — 研究者 (white lab coat, glasses), 编排器 (navy vest, headset, clipboard), 执行者 (blue hoodie), 审稿人 (orange hoodie, round glasses, magnifier). Cute flat chibi, small, never covering a label or an arrow. Deterministic tools (loopctl, guards, check-done) are NOT characters: draw them as a shield / padlock / gate icon. No robots, no brains, no extra mascots."""

FIGS = {}

FIGS['deck_loop_parallel_r2'] = dict(
    round1='deck_loop_parallel',
    title='多智能体并行回环 1/2 · 账本状态机与并行分派',
    brief=dict(
        figure_purpose='一行主题进，九道闸门出',
        headline_claim='完成与否由程序判定，不由模型自报',
        headline_number='9 道闸门 · 29 批 / 40 个子任务',
        caption_thesis='编排器只做四件事：建账本、分派、验闸门、路由返工；七个专职智能体各写自己的分片，闸门落在同一本账上。',
        phases=[dict(id='p1', label='1 · 立项取证', members=['scope', 'lit', 'style', 'ref']),
                dict(id='p2', label='2 · 并行生产', members=['tax', 'fig', 'write', 'idea']),
                dict(id='p3', label='3 · 对抗审稿与交付', members=['review', 'verdict', 'deliver'])],
        components=[
            dict(id='topic', label='研究主题', one_line='一行输入', role='input', character='研究者'),
            dict(id='orc', label='编排器', one_line='建账本 · 分派 · 验闸门 · 路由返工', role='control', character='编排器', priority='core'),
            dict(id='scope', label='范围界定', one_line='子主题与边界', phase='p1'),
            dict(id='lit', label='文献检索', one_line='≥3 路分片并发', phase='p1', character='执行者', priority='core'),
            dict(id='style', label='风格库', one_line='30 篇范文', phase='p1'),
            dict(id='ref', label='引用核查', one_line='51/51 逐条核对', phase='p1', icon='shield'),
            dict(id='tax', label='分类法', one_line='每叶 ≥3 篇', phase='p2'),
            dict(id='fig', label='图件', one_line='可编辑三件套', phase='p2', character='执行者'),
            dict(id='write', label='写作', one_line='按章节并发', phase='p2', character='执行者'),
            dict(id='idea', label='实验构想', one_line='前驱体预测', phase='p2', character='执行者'),
            dict(id='review', label='对抗审稿', one_line='独立上下文 · 三视角', phase='p3', character='审稿人', priority='core'),
            dict(id='verdict', label='裁决', one_line='0 blocker / major ?', phase='p3', shape='diamond'),
            dict(id='deliver', label='终稿交付', one_line='tex · pdf · bib · 账本', phase='p3'),
            dict(id='ledger', label='回环账本 ledger.json', one_line='九道闸门落账 · 文件锁 · 产物指纹', role='single source of truth', priority='core'),
        ],
        flows=[
            dict(frm='topic', to='scope', kind='flow'), dict(frm='scope', to='lit', kind='flow'), dict(frm='scope', to='style', kind='flow'),
            dict(frm='lit', to='ref', kind='flow'), dict(frm='style', to='ref', kind='flow'), dict(frm='ref', to='tax', kind='flow'),
            dict(frm='tax', to='fig', kind='flow'), dict(frm='tax', to='write', kind='flow'), dict(frm='tax', to='idea', kind='flow'),
            dict(frm='fig', to='review', kind='flow'), dict(frm='write', to='review', kind='flow'), dict(frm='idea', to='review', kind='flow'),
            dict(frm='review', to='verdict', kind='flow'), dict(frm='verdict', to='deliver', kind='keep', label='PASS'),
            dict(frm='verdict', to='tax', kind='retry', label='issue 路由返工 · 最多 5 轮'),
            dict(frm='orc', to='p1/p2/p3', kind='dispatch', label='分派'),
            dict(frm='each stage', to='ledger', kind='write', label='落账'),
        ],
        legend=['主流程', '并行分派', '返工回路', '落账'],
        gates=['scope_confirmed', 'lit_coverage', 'style_bank_ready', 'ref_integrity', 'taxonomy_ready', 'figures_ready',
               'draft_complete', 'ideas_reviewed', 'review_pass'],
        evidence=['29 批', '40 个子任务', '≤4 路并行', '134 次工具调用'],
    ),
    layouts={
        'C01': ('三条横向编号色带', 'THREE FULL-WIDTH HORIZONTAL PHASE PANELS stacked top to bottom (1 · 立项取证 / 2 · 并行生产 / 3 · 对抗审稿与交付), cards flowing left to right inside each panel; the 编排器 character stands at the left margin dispatching into all three panels with blue dashed arrows; the ledger is a long horizontal band at the very bottom carrying nine small green gate stamps; the orange RETRY arc sweeps up the right side from 裁决 back to 分类法.'),
        'C02': ('左→右三相位 + 底部账本轨', 'THREE PHASE PANELS SIDE BY SIDE, left to right (1 · 立项取证 | 2 · 并行生产 | 3 · 对抗审稿与交付); parallel cards are stacked vertically inside a panel so the fan-out is obvious; the 研究者 hands the one-line topic in at the far left, 编排器 stands above the panels with blue dashed dispatch arrows down into each; the ledger is a rail along the bottom with nine gate stamps; the orange RETRY arc runs under the panels from 裁决 back to 分类法; a row of four big KPI numbers sits under the rail.'),
        'C03': ('账本居中的环', 'A LITERAL LOOP: the ledger sits in the CENTRE as a large open ledger book with nine green gate stamps; the three phase panels are arranged clockwise around it (top-left 1, top-right 2, bottom 3), the main flow travelling clockwise; thin grey "落账" spokes run from each panel to the ledger; the orange RETRY arc closes the ring from 裁决 back to 分类法; 编排器 stands beside the ledger holding the clipboard.'),
        'C04': ('编排器泳道在上', 'A CONTROL LANE ON TOP: a slim navy-tinted lane with the 编排器 character and its four verbs as small chips (建账本 → 分派 → 验闸门 → 路由返工); below it the three numbered phase panels left to right; blue dashed dispatch arrows drop from the lane into each panel; the ledger lane at the bottom shows nine gate stamps aligned under their stages; the orange RETRY arc loops from 裁决 back to 分类法 between the panels and the ledger lane.'),
    },
)

FIGS['deck_loop_converge_r2'] = dict(
    round1='deck_loop_converge',
    title='多智能体并行回环 2/2 · 互搏通道与机械闸门',
    brief=dict(
        figure_purpose='回环为什么收敛',
        headline_claim='模型说了不算：检查不过即返工',
        headline_number='7 → 0 项 issue（两轮）',
        caption_thesis='四条互搏通道负责挑错，issue 带 target 回到责任阶段，只重跑受影响链路；放行由 loopctl 与 check-done 机械判定。',
        phases=[dict(id='p1', label='1 · 互搏挑错', members=['c1', 'c2', 'c3', 'c4']),
                dict(id='p2', label='2 · 路由返工', members=['route', 'cascade']),
                dict(id='p3', label='3 · 机械放行', members=['loopctl', 'checkdone', 'deliver'])],
        components=[
            dict(id='prod', label='本轮产物', one_line='稿件 · 图件 · 方案 · 引用库', role='input'),
            dict(id='c1', label='执行者 ⇄ 审稿人', one_line='独立上下文 · 三视角', phase='p1', character='执行者 + 审稿人', priority='core'),
            dict(id='c2', label='提案者 ⇄ 攻击者', one_line='实验构想内部对抗', phase='p1'),
            dict(id='c3', label='候选 ⇄ 审计', one_line='图件两轮候选制', phase='p1'),
            dict(id='c4', label='稿件 ⇄ 机械守卫', one_line='bib · tex · pdf · 语言守卫', phase='p1', icon='shield'),
            dict(id='route', label='issue 路由表', one_line='target → 责任阶段', phase='p2', priority='core'),
            dict(id='cascade', label='级联失效', one_line='指纹变更 → 闸门回 PENDING', phase='p2'),
            dict(id='loopctl', label='loopctl 拒绝写入', one_line='跳阶段 · 单轮审稿 · 无回执', phase='p3', icon='padlock'),
            dict(id='checkdone', label='check-done', one_line='九道闸门全过 · 退出码 0', phase='p3', icon='gate', priority='core'),
            dict(id='deliver', label='交付', one_line='23 页 PDF · 51/51 引用', phase='p3'),
            dict(id='human', label='升级人类', one_line='三轮未收敛 / 轮次用尽', role='outside the loop'),
        ],
        flows=[
            dict(frm='prod', to='p1', kind='flow'), dict(frm='p1', to='route', kind='flow', label='issue 带 target · severity'),
            dict(frm='route', to='cascade', kind='flow'),
            dict(frm='cascade', to='prod', kind='retry', label='只重跑责任阶段 · 最多 5 轮'),
            dict(frm='p1', to='checkdone', kind='keep', label='0 blocker / major'),
            dict(frm='checkdone', to='deliver', kind='keep', label='退出码 0'),
            dict(frm='loopctl', to='ledger writes', kind='write', label='写不进去'),
            dict(frm='loop', to='human', kind='escalate', label='不收敛'),
        ],
        legend=['主流程', '返工回路', '机械放行', '升级人类'],
        evidence=['生产阶段 · 闸门拦下 4 项', '第 1 轮审稿 · 7 项 → 路由返工', '第 2 轮审稿 · 0 项 → PASS', 'check-done = 0'],
    ),
    layouts={
        'C01': ('中央大回环', 'ONE BIG LOOP in the middle of the slide: 本轮产物 (left) → the phase-1 panel with the four adversarial pairs → issue 路由表 → 级联失效, and the bold ORANGE RETRY arc sweeping back under everything to 本轮产物; from the phase-1 panel a GREEN arrow leaves upward-right to check-done and 交付 (phase 3, right); 升级人类 sits outside the loop at the bottom right behind a thin red dashed arrow. The executor and reviewer characters sit together inside the first pair card, inspecting a draft page with a magnifier. A strip of four round cards runs along the bottom.'),
        'C02': ('左→右三相位 + 轮次条', 'THREE PHASE PANELS SIDE BY SIDE (1 · 互搏挑错 | 2 · 路由返工 | 3 · 机械放行); the four adversarial pairs are stacked in panel 1, each as two small role chips joined by a double-headed arrow; the ORANGE RETRY arc runs under the panels from 级联失效 back to 本轮产物 at the far left; phase 3 shows a padlock (loopctl) and a gate with a green light (check-done) leading to 交付; the bottom strip tells the run as four round cards whose colour goes red → amber → green.'),
        'C03': ('对话式回环', 'A DIALOGUE LOOP in the manner of an auto-review hero figure: the 执行者 character on the left, the 审稿人 character on the right, and between them alternating message bubbles travelling left→right (blue) and right→left (orange): "第 1 轮：7 项 issue" / "已按 target 返工" / "第 2 轮：0 · 0 · 0" / a final green "PASS"; to the right of the dialogue a slim column of the mechanical gates (loopctl padlock → check-done gate → 交付); under the dialogue the issue 路由表 and 级联失效 as two cards feeding the orange RETRY arrow.'),
        'C04': ('收敛阶梯', 'A CONVERGENCE STAIRCASE: the rounds descend left to right as four steps whose height is the open-issue count (4 → 7 → 0 → check-done = 0), coloured red → amber → green; above the staircase the loop itself as a compact ring (本轮产物 → 四条互搏通道 → issue 路由表 → 级联失效 → back, the return drawn as the bold ORANGE arc); the mechanical exit (loopctl padlock, check-done gate, 交付) sits at the foot of the last step; 升级人类 is a small grey card off to the side.'),
    },
)

ROUND_CARDS = """EVIDENCE STRIP (bottom, four cards in a row, colour progression red → amber → green → green, big numbers):
- "生产阶段" — big "4" — "闸门拦下 · 3 blocker · 1 major"
- "第 1 轮审稿" — big "7" — "1 blocker · 3 major · 3 minor → 路由返工"
- "第 2 轮审稿" — big "0" — "0 · 0 · 0 → review_pass"
- "check-done" — big "= 0" — "23 页 PDF · 51/51 引用" """

KPI_CARDS = """KPI STRIP (bottom, four tiles with big bold numbers and a small grey caption each):
- "29" 批 · 并行批次     - "40" 个子任务     - "≤4" 路并行     - "134" 次工具调用"""


def locked_text(f):
    b = f['brief']
    out = [f'"{p["label"]}"' for p in b['phases']]
    out += [f'"{c["label"]}" — "{c["one_line"]}"' for c in b['components']]
    out += [f'arrow label "{fl["label"]}"' for fl in b['flows'] if fl.get('label')]
    out += ['legend: ' + ' / '.join(f'"{x}"' for x in b['legend'])]
    if b.get('gates'):
        out += ['nine gate stamps on the ledger (small monospace): ' + ' · '.join(b['gates'])]
    out += [f'headline (top-left, bold): "{b["headline_claim"]}"', f'headline number (accent colour): "{b["headline_number"]}"']
    return '\n'.join('  ' + x for x in out)


def prompt(pid, f, cid):
    b = f['brief']
    name, layout = f['layouts'][cid]
    strip = KPI_CARDS if 'parallel' in pid else ROUND_CARDS
    return f"""Use your IMAGE GENERATION tool to output ONE image. Image generation only — do not write or edit code, SVG or files for the picture itself.

Reference image (look at it first): {NAS}/{CAST_REL} → the ONLY characters allowed.

WHAT THIS IS: the figure for one 16:9 conference slide (Chinese) about a multi-agent literature-review system — "{b['figure_purpose']}". Thesis: {b['caption_thesis']}

{STYLE}

LAYOUT — candidate {cid} · {name}:
{layout}

{CAST_RULE}

{strip}

TEXT IS LOCKED — render these strings verbatim and crisp (no renaming, no invented boxes, no extra captions):
{locked_text(f)}

Output the single finished figure: wide 16:9 landscape, white background, no slide title bar, no logo, no watermark."""


def package(pid, f, cid):
    name, layout = f['layouts'][cid]
    return f"""# {pid} · {cid} · {name}

- round: 2 (first-round surface-style override requested by the author on 2026-09-17: loop-engineering method-figure style)
- first_round_surface_style: loop_engineering_method_figure (replaces formal_publication_schematic)
- semantics: unchanged from {f['round1']} S0 (same evidence anchors); content compressed to a brief
- layout_grammar: {layout}

## strict prompt audit
source faithfulness: every component and flow is a subset of the round-1 S0 entity/relation tables; numbers come from the formal run's ledger / RUN_MANIFEST.
connector kinds: main flow / dispatch / retry / ledger write (+ escalate on slide 2) — each kind has one colour and appears in the legend.
repeated roles: the producing agents share ONE executor character with different props, not four different characters.
deterministic tools are icons (shield / padlock / gate), not characters — "模型说了不算".
verdict: pass

## IMAGE PROMPT
{prompt(pid, f, cid)}
"""


CAST_PROMPT = """Use your IMAGE GENERATION tool to output ONE image. Image generation only.

A CHARACTER IDENTITY SHEET for a set of conference-slide figures about a multi-agent research system. Pure white background, four characters standing in a row with generous spacing, full body, front view, all in ONE consistent style: cute flat-vector chibi (big head, small body), clean dark outlines, soft flat colours, no gradients, no shadows on the ground except a tiny soft ellipse, friendly and professional — suitable for an academic talk, not a game.

Left to right, each with its name printed underneath in bold Chinese sans-serif:
1. "研究者" — a materials scientist: short dark hair, rectangular glasses, white lab coat over a dark tee, holding one sheet of paper.
2. "编排器" — the orchestrator agent: navy vest over a light shirt, a small headset, holding a clipboard with a checklist.
3. "执行者" — the executor agent: brown hair, BLUE hoodie, holding a pen; this same character will later appear with different props (magnifier and paper stack, brush, flask).
4. "审稿人" — the reviewer agent: black hair, round glasses, ORANGE hoodie, holding a magnifying glass and a red pen, a slightly stern but kind expression.

Under the row, small and grey: "cast · identity sheet". Wide landscape, white background, nothing else."""


def main():
    # cast
    cast = RUN / 'deck_cast' / 'outputs' / 'CAST'
    (cast / 'prompts').mkdir(parents=True, exist_ok=True)
    (cast / 'generated').mkdir(exist_ok=True)
    (cast / 'prompts' / 'CAST.md').write_text('# deck_cast · identity sheet\n\n## IMAGE PROMPT\n' + CAST_PROMPT + '\n', encoding='utf-8')
    row = dict(candidate_id='CAST', prompt_path='outputs/CAST/prompts/CAST.md', target_image_path='outputs/CAST/generated/CAST.png', skip=False)
    (cast / 'prompt-index.json').write_text(json.dumps(dict(stage='CAST', project_id='deck_cast', candidates=[row], rows=[row]),
                                                       ensure_ascii=False, indent=1), encoding='utf-8')
    for pid, f in FIGS.items():
        out = RUN / pid / 'outputs'
        s0 = out / 'S0-paper-foundation'
        if not s0.exists():
            shutil.copytree(RUN / f['round1'] / 'outputs' / 'S0-paper-foundation', s0)
        (s0 / 'round2-addendum.md').write_text(f"""# S0 addendum — round 2 ({pid})

Semantics, evidence anchors and relations are those of `{f['round1']}` (copied here unchanged). Round 2 changes only the
rendering contract, at the author's request (2026-09-17, reference: wanshuiyin/auto-claude-code-research-in-sleep):
- characters ARE allowed, but only the locked cast (研究者 / 编排器 / 执行者 / 审稿人); the round-1 lock "禁止画人形" is lifted
  for these four; deterministic tools stay icons (shield / padlock / gate) so the slide still says "模型说了不算";
- content is compressed to a brief (label + one line); the full routing table, gate criteria and refusal list move to the
  speaker notes — the round-1 slide stays available as the detailed backup;
- flow kinds get colours and a legend; the retry loop is the visual hero.
Still forbidden: one full pipeline per agent; agent-to-agent chat lines as data flow on slide 1; escalation wired back into the loop.
""", encoding='utf-8')
        s1 = out / 'S1-figure-strategy'
        s2 = out / 'S2-sketch-explore'
        (s2 / 'prompts').mkdir(parents=True, exist_ok=True)
        (s2 / 'generated').mkdir(exist_ok=True)
        s1.mkdir(parents=True, exist_ok=True)
        (s1 / 'figure-brief.json').write_text(json.dumps(dict(schema='goai-deck/brief/v1', figure_id=pid, **f['brief']),
                                                         ensure_ascii=False, indent=1), encoding='utf-8')
        rows_md = '\n'.join(f'| {cid} | {name} | {layout[:90]}… |' for cid, (name, layout) in f['layouts'].items())
        (s1 / 'figure-strategy.md').write_text(f"""# S1-FIGURE-STRATEGY (round 2) — {pid}

{f['title']}

- headline_claim: {f['brief']['headline_claim']}
- headline_number: {f['brief']['headline_number']}
- first_round_surface_style: loop_engineering_method_figure（作者指定参考 ARIS /method-figure；取代 formal_publication_schematic）
- 为什么换：第一轮把论文图的表面风格（克制四色、纯线稿图元、约 55 条锁定字串、细灰连线）搬到了答辩幻灯片上，
  作者对原生重建和 Codex 草图的评价一致——"质量太低，没有顶会的质感"。媒介不同：幻灯片要一眼看懂回环，细节由讲者补。

## 四个候选（同一表面风格，版式正交）
| 候选 | 版式 | 要点 |
|---|---|---|
{rows_md}

## 组件（brief）
{chr(10).join(f"- {c['label']} — {c['one_line']}" for c in f['brief']['components'])}

## 连线种类
主流程（深蓝粗线）/ 并行分派（蓝虚线）/ 返工回路（橙色弧线，写明上限）/ 落账（细灰线）；图例必须出现。
""", encoding='utf-8')
        cands = []
        for cid in f['layouts']:
            (s2 / 'prompts' / f'{cid}.md').write_text(package(pid, f, cid), encoding='utf-8')
            cands.append(dict(candidate_id=cid, prompt_path=f'outputs/S2-sketch-explore/prompts/{cid}.md',
                              target_image_path=f'outputs/S2-sketch-explore/generated/{cid}.png',
                              reference_image_paths=[f'../{CAST_REL}'], skip=False, size='16:9'))
        (s2 / 'prompt-index.json').write_text(json.dumps(dict(stage='S2-SKETCH-EXPLORE', project_id=pid,
                                                              first_round_surface_style='loop_engineering_method_figure',
                                                              candidates=cands, rows=cands), ensure_ascii=False, indent=1), encoding='utf-8')
        n = len(prompt(pid, f, 'C01'))
        print(pid, '→ 4 candidates, prompt', n, 'chars,', len(f['brief']['components']), 'components')
    print('cast prompt', len(CAST_PROMPT), 'chars')


if __name__ == '__main__':
    main()
