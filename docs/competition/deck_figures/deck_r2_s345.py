"""Deck figures · round 2 — S3 (issue ledger + direction), S4 (formal briefs) and the S5 / asset-sheet prompt packages.

S5 in this round is a CONDITIONED bake (the ARIS /method-figure lesson): the semantically correct, labelled blueprint
render is the layout reference, the cast sheet is the identity reference, and the S2 pick is the style reference.
The editable deliverable is the blueprint itself (native text / cards / arrows) plus raster art; the art comes from
two ASSET SHEETS (text-free grids of characters and small illustrations) that are cropped cell by cell.

Inputs: the blueprint renders (copied to outputs/S4-candidate-brief/condition.png) and scene.json texts.
"""
import json
import shutil
from pathlib import Path

RUN = Path('/root/lyf/goai/final_round/figstudio/figure-studio-runs')
SP = Path('/tmp/claude-0/-root-lyf-goai/40c4734a-b33a-4ab2-9c07-33af650ee3f9/scratchpad')
NAS = '/mnt/nas/data/lyf/goai/deck_figstudio'
CAST = f'{NAS}/deck_cast/outputs/CAST/generated/CAST.png'

S3 = {
    'deck_loop_parallel_r2': dict(
        ledger={
            'C01': [('high', 'semantic', '立项取证带内 范围界定→文献检索→风格库→引用核查 被画成串行链；并行生产带内 分类法→图件→写作→实验构想 也被串成一条线——并行语义丢失'),
                    ('high', 'semantic', '返工弧从「终稿交付」出发（应从「裁决」）'),
                    ('medium', 'semantic', '研究者角色出现在 范围界定/风格库/引用核查/终稿交付 四张卡里，角色分工被冲淡'),
                    ('none', 'visual', '三条横向色带 + 左侧编排器分派 + 账本轨九枚闸门 + KPI 条，层次清楚')],
            'C02': [('high', 'semantic', '「引用核查」被挪进第 2 段，「实验构想」缺失'),
                    ('medium', 'semantic', '并行只靠卡片堆叠暗示，没有分叉/汇合'),
                    ('none', 'visual', '三相位并排 + 顶部编排器扇形分派 + 账本轨 + 四色 KPI，最克制、最像会议报告图')],
            'C03': [('high', 'semantic', '「引用核查」落在第 3 段，「风格库」缺失；PASS 弧终点指向「实验构想」，返工弧从账本出发'),
                    ('none', 'visual', '账本居中成环，橙色返工弧与绿色 PASS 弧围成回环——"回环"的视觉隐喻最强')],
            'C04': [('high', 'semantic', '相位成员被重排（风格库/引用核查/分类法/图件 在第 2 段，写作/实验构想 在第 3 段），且全部串行'),
                    ('none', 'visual', '顶部控制泳道把编排器四个动词做成 chip，账本轨编号 1–9')],
        },
        selected='C02 的构图（三相位并排 + 顶部编排器分派 + 底部账本轨 + KPI 条）为主方向；吸收 C01 的卡内角色与小插画、C04 的闸门轨节奏',
        avoid='任何把并行画成串行链的走线；返工弧起点不在「裁决」；相位成员漂移',
        transform='语义由条件线框锁死：P1 范围界定→[文献检索∥风格库]→引用核查；P2 分类法→[图件∥写作∥实验构想]；P3 对抗审稿→裁决→PASS→终稿交付；返工弧 裁决→并行生产',
    ),
    'deck_loop_converge_r2': dict(
        ledger={
            'C01': [('medium', 'semantic', '「写不进去」「不收敛」两条线从 loopctl 指向 升级人类（应分别指向账本写入口、出自回环）'),
                    ('none', 'visual', '大回环 + 2×2 互搏卡（角色成对）+ 四张轮次卡 4/7/0/=0，信息最完整')],
            'C02': [('high', 'semantic', '编排器角色出现在「路由返工」段；loopctl 被串进主流程；结尾的 Done! 庆祝偏娱乐'),
                    ('none', 'visual', '角色表现力强')],
            'C03': [('high', 'semantic', '气泡方向与发言人不符（"第 1 轮：7 项 issue" 应由审稿人发出）'),
                    ('none', 'visual', '对话式回环最像 ARIS 的 auto-review hero：轮次即叙事，机械闸门在右侧成列')],
            'C04': [('medium', 'visual', '收敛阶梯与下方轮次卡重复表达同一组数字'),
                    ('none', 'visual', '阶梯上的角色让"4→7→0"一眼可读')],
        },
        selected='C01 的构图（本轮产物 → 2×2 互搏卡 → 路由返工 → 大回环；机械放行在右；底部四张轮次卡）为主方向；C03 的对话式回环留作备选构图',
        avoid='loopctl 串进主流程；升级人类接回回环；庆祝式装饰',
        transform='语义由条件线框锁死：绿色 0 blocker/major 直通 check-done；橙色 U 形回环 级联失效→本轮产物；红色虚线 不收敛→升级人类',
    ),
}

SHEETS = {
    'deck_assets_a': dict(grid=(4, 4), cells=[
        ('researcher', '研究者 (white lab coat, glasses) holding out ONE sheet of paper with a single line on it'),
        ('orchestrator', '编排器 (navy vest, headset) holding a clipboard with a checklist, one hand pointing forward'),
        ('scope', 'a document page with a dashed boundary frame and a small target mark on it'),
        ('search', '执行者 (blue hoodie) holding a magnifier over a tall stack of papers'),
        ('style', 'a neat stack of three journals with a ribbon bookmark'),
        ('refguard', 'a shield with a check mark in front of a short reference list'),
        ('taxonomy', 'a small tree diagram: one folder on top branching to three folders'),
        ('figure', '执行者 (blue hoodie) holding a brush beside a framed bar-chart thumbnail'),
        ('writer', '执行者 (blue hoodie) typing on a laptop, two finished pages beside it'),
        ('idea', '执行者 (blue hoodie) holding up a flask with a few bubbles'),
        ('reviewer', '审稿人 (orange hoodie, round glasses) with a magnifier in one hand and a red pen in the other'),
        ('deliver', 'a tidy bundle of three file icons (a page, a red-cornered document, a small book)'),
        ('ledger', 'an open ledger book with a bookmark ribbon, a few ruled lines with green ticks'),
        ('padlock', 'a closed padlock with a small red cross badge'),
        ('checkdone', 'a barrier gate with a green light on top and a small checklist'),
        ('pdf', 'a finished document page with a small chart on it and a green check badge'),
    ]),
    'deck_assets_b': dict(grid=(4, 2), cells=[
        ('products', 'a fanned bundle of work products: two draft pages, one chart page, one reference list'),
        ('duo_review', '执行者 (blue hoodie) and 审稿人 (orange hoodie, round glasses) side by side inspecting ONE draft page, the magnifier on the page'),
        ('duo_attack', '执行者 (blue hoodie) presenting a flask; 审稿人 (orange hoodie) pointing at it with a red pen, one small spark mark'),
        ('duo_audit', 'two framed chart candidates side by side, 审稿人 (orange hoodie) holding a magnifier over one of them'),
        ('guard', 'a large shield with a check mark standing in front of three small file icons'),
        ('route', 'a small routing table: four rows with coloured dots, a short arrow leaving each row to the right'),
        ('cascade', 'a fingerprint next to a circular refresh arrow and a small warning triangle'),
        ('human', '研究者 (white lab coat, glasses) raising one hand, friendly'),
    ]),
}


def sheet_prompt(sid, spec):
    cols, rows = spec['grid']
    lines = '\n'.join(f'  row {i // cols + 1}, column {i % cols + 1}: {desc}' for i, (_n, desc) in enumerate(spec['cells']))
    return f"""Use your IMAGE GENERATION tool to output ONE image. Image generation only.

Reference image (look at it first): {CAST} → the ONLY characters allowed; keep their faces, hair, clothes and colours exactly.

AN ASSET SHEET for conference-slide figures: a regular grid of {cols} columns × {rows} rows of SEPARATE small illustrations on a PURE WHITE background. Every illustration is centred in its own cell with generous white space around it (nothing touches a neighbour, nothing crosses a cell boundary). NO text, NO letters, NO numbers, NO labels, NO captions, NO borders, NO grid lines, NO background tint, NO ground shadows.

One consistent style for all cells, matching the reference cast: cute flat-vector chibi characters and flat icons, clean dark outlines, soft flat colours (navy, blue, orange, green accents), no gradients, no 3D, friendly and professional — suitable for an academic talk.

The cells, in reading order:
{lines}

Wide 16:9 landscape, white background, nothing else on the sheet."""


def scene_texts(pid):
    d = json.loads((SP / 'deckjobs' / pid / 'scene.json').read_text(encoding='utf-8'))
    seen, out = set(), []
    for e in d['slides'][0]['elements']:
        if e.get('kind') == 'text' and e['text'].strip() and e['text'] not in seen:
            seen.add(e['text'])
            out.append(e['text'])
    return out


ART_NOTES = {
    'deck_loop_parallel_r2': """ART SLOTS (each dashed grey circle in the layout reference is a slot — replace it with the illustration, same place, same size):
编排器 card → the 编排器 character with the clipboard; 研究主题 card → the 研究者 holding out one sheet; 范围界定 → a page with a dashed boundary and a target mark; 文献检索 → the 执行者 with a magnifier over a paper stack; 风格库 → a stack of journals; 引用核查 → a shield with a check over a reference list; 分类法 → a small folder tree; 图件 → the 执行者 with a brush beside a chart thumbnail; 写作 → the 执行者 typing, pages beside; 实验构想 → the 执行者 holding a flask; 对抗审稿 → the 审稿人 with magnifier and red pen; 终稿交付 → a bundle of file icons; 回环账本 → an open ledger book.""",
    'deck_loop_converge_r2': """ART SLOTS (each dashed grey circle/ellipse in the layout reference is a slot — replace it with the illustration, same place, same size):
本轮产物 → a fanned bundle of draft pages and a chart; 执行者 ⇄ 审稿人 → the 执行者 and the 审稿人 inspecting one draft page with the magnifier; 提案者 ⇄ 攻击者 → the 执行者 presenting a flask while the 审稿人 points a red pen at it; 候选 ⇄ 审计 → two chart candidates under the 审稿人's magnifier; 稿件 ⇄ 机械守卫 → a shield with a check in front of three file icons; issue 路由表 → a small routing table with coloured dots and arrows; 级联失效 → a fingerprint with a refresh arrow and a warning triangle; check-done → a barrier gate with a green light; 交付 → a finished PDF page with a green check; loopctl 拒绝写入 → a closed padlock with a red cross; 升级人类 → the 研究者 raising a hand.""",
}


def s5_prompt(pid, fid, variant, refs):
    texts = '\n'.join(f'  "{t}"' for t in scene_texts(pid))
    return f"""Use your IMAGE GENERATION tool to output ONE image. Image generation only — do not write or edit code, SVG or files for the picture itself.

References (look at all of them first):
- {refs['condition']}  → the EXACT LAYOUT to reproduce: every panel, card, arrow, label pill, legend, evidence tile and number is already in its final place with its final text. Reproduce this layout faithfully — same positions, same arrow routes, same reading order. Do not add, remove, rename or move a box or an arrow.
- {CAST}  → the ONLY characters allowed; keep faces, hair, clothes and colours exactly.
- {refs['style']}  → the visual finish to reach (soft pastel panels, white cards with subtle soft shadows, thick confident arrows, friendly illustrations).

TASK: render the layout reference as a finished, publication-quality conference-slide figure (Chinese). Keep the geometry; upgrade the finish.

STYLE: top ML-paper "Figure 1" / polished README method figure: PURE WHITE background; soft pastel numbered phase panels with bold titles in the panel's colour; rounded white cards with subtle soft shadows; thick dark-navy main-flow arrows with large arrowheads; the ORANGE return loop is the visual hero; green = pass; blue dashed = dispatch; thin grey = ledger writes; red dashed = escalate. Crisp, bold, generously sized sans-serif Chinese text (思源黑体); code identifiers in a clean monospace.

{ART_NOTES[pid]}
{variant}

TEXT IS LOCKED — every string below appears in the layout reference; render each verbatim and crisp, exactly once, where the reference puts it (no renaming, no extra captions, no invented boxes):
{texts}

Output the single finished figure: wide 16:9 landscape, white background, no slide title bar, no logo, no watermark."""


VARIANTS = {
    'F01': ('restrained', 'ART DIRECTION — restrained: characters appear only where the slot list names one; every other slot is a small flat icon-illustration. Calm, editorial, lots of white.'),
    'F02': ('rich', 'ART DIRECTION — rich: make the illustrations a little larger and more expressive (still inside their slots), add tiny supporting details inside cards (a second page behind a document, small check marks), keep every label and arrow fully visible.'),
}
STYLE_REF = {'deck_loop_parallel_r2': 'C02', 'deck_loop_converge_r2': 'C01'}


def main():
    for pid, rec in S3.items():
        out = RUN / pid / 'outputs'
        s3 = out / 'S3-direction-select'
        s3.mkdir(parents=True, exist_ok=True)
        md = [f'# S3-DIRECTION-SELECT (round 2) — {pid}\n', '## issue ledger（逐候选，语义与视觉分开记）']
        for cid, items in rec['ledger'].items():
            md.append(f'### {cid}')
            md += [f'- [{sev}] ({kind}) {txt}' for sev, kind, txt in items]
        high = sum(1 for items in rec['ledger'].values() for sev, *_ in items if sev == 'high')
        md += ['', '## S2 exploration aggregate', f'- high 级问题共 {high} 条，全部是语义类（并行画成串行、成员漂移、弧线起止点错）——表面风格已达标，问题出在生图模型不守拓扑。',
               '', '## direction selection', f"- selected_direction: {rec['selected']}", '- user_preferred_first_round_candidate_ids: 无（作者尚未点名）',
               f"- S5 避免: {rec['avoid']}", f"- S5 转化: {rec['transform']}", '- 方法变更：S5 改为「条件线框锁语义」的 bake；可编辑交付件 = 线框（原生对象）+ 素材表裁出的插画。']
        (s3 / 'direction-selection-record.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
        (s3 / 'direction-selection-record.json').write_text(json.dumps(dict(
            project_id=pid, issue_ledger={c: [dict(severity=a, kind=b, finding=t) for a, b, t in items] for c, items in rec['ledger'].items()},
            selected_direction=rec['selected'], user_preferred_first_round_candidate_ids=[], avoid=rec['avoid'], transform=rec['transform']),
            ensure_ascii=False, indent=1), encoding='utf-8')

        s4 = out / 'S4-candidate-brief'
        s5 = out / 'S5-candidate-image'
        (s5 / 'prompts').mkdir(parents=True, exist_ok=True)
        (s5 / 'generated').mkdir(exist_ok=True)
        s4.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SP / 'deckb' / 'jobs' / pid / 'build' / 'render' / 'page_001.png', s4 / 'condition.png')
        shutil.copyfile(SP / 'deckjobs' / pid / 'scene.json', s4 / 'blueprint.scene.json')
        refs = dict(condition=f'{NAS}/{pid}/outputs/S4-candidate-brief/condition.png',
                    style=f'{NAS}/{pid}/outputs/S2-sketch-explore/generated/{STYLE_REF[pid]}.png')
        rows, matrix = [], []
        for fid, (name, variant) in VARIANTS.items():
            (s5 / 'prompts' / f'{fid}.md').write_text(
                f'# {pid} · {fid} · 条件线框 bake（{name}）\n\n- lineage: blueprint (S4 condition.png) + cast + S2 {STYLE_REF[pid]}\n'
                f'- semantics: locked by the blueprint; the bake may not move or rename anything\n\n## IMAGE PROMPT\n' + s5_prompt(pid, fid, variant, refs) + '\n',
                encoding='utf-8')
            row = dict(candidate_id=fid, prompt_path=f'outputs/S5-candidate-image/prompts/{fid}.md',
                       target_image_path=f'outputs/S5-candidate-image/generated/{fid}.png',
                       reference_image_paths=['outputs/S4-candidate-brief/condition.png', '../deck_cast/outputs/CAST/generated/CAST.png',
                                              f'outputs/S2-sketch-explore/generated/{STYLE_REF[pid]}.png'],
                       refined_from_first_round_candidate_ids=[STYLE_REF[pid]], lineage_role='blueprint_conditioned_bake', skip=False, size='16:9')
            rows.append(row)
            matrix.append(dict(candidate_id=fid, direction=name, refined_from_first_round_candidate_ids=[STYLE_REF[pid]],
                               must_fix=[t for items in rec['ledger'].values() for sev, _k, t in items if sev == 'high']))
        (s4 / 'candidate-matrix.json').write_text(json.dumps(matrix, ensure_ascii=False, indent=1), encoding='utf-8')
        (s5 / 'prompt-index.json').write_text(json.dumps(dict(stage='S5-CANDIDATE-IMAGE', project_id=pid, candidates=rows, rows=rows),
                                                         ensure_ascii=False, indent=1), encoding='utf-8')
        print(pid, 'S3/S4/S5 written; locked strings:', len(scene_texts(pid)), '| F01 prompt', len(s5_prompt(pid, 'F01', VARIANTS['F01'][1], refs)), 'chars')

    for sid, spec in SHEETS.items():
        d = RUN / sid / 'outputs' / 'ASSETS'
        (d / 'prompts').mkdir(parents=True, exist_ok=True)
        (d / 'generated').mkdir(exist_ok=True)
        (d / 'prompts' / 'SHEET.md').write_text(f'# {sid} · asset sheet\n\n## IMAGE PROMPT\n' + sheet_prompt(sid, spec) + '\n', encoding='utf-8')
        row = dict(candidate_id='SHEET', prompt_path='outputs/ASSETS/prompts/SHEET.md', target_image_path='outputs/ASSETS/generated/SHEET.png',
                   reference_image_paths=['../deck_cast/outputs/CAST/generated/CAST.png'], skip=False, size='16:9')
        (d / 'prompt-index.json').write_text(json.dumps(dict(stage='ASSETS', project_id=sid, grid=list(spec['grid']),
                                                             cells=[n for n, _ in spec['cells']], candidates=[row], rows=[row]),
                                                        ensure_ascii=False, indent=1), encoding='utf-8')
        print(sid, 'asset sheet:', spec['grid'], len(spec['cells']), 'cells')


if __name__ == '__main__':
    main()
