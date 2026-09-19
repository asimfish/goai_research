"""答辩 PPT · 「从研究方案到 OpenLab 工作流与仿真执行（整体方案）」页 · 可编辑重做（round 4，deck theme）。

作者给的是一页草稿（书 + 大脑、~20% 饼图、论文 → 笔记本 → 管式炉的三段、"Could AI Dream of Science"、等距实验室、
Experimental Guidance 引文段落 + 四色高亮）。本页把它做成原生可编辑对象 + 生图素材：
  * 左：文献数据库面板（88,343,822 篇文献 · 80.5 TB，取自 PPT 第 6 页；~20% 化学学科论文占比做成环形计量 + 大数字）；
  * 中：文献 → 结构化知识 → 合成方案与装置 的三段链，下面是口号；
  * 右：实验流程 Step 1 / 2 / 3（步骤直接从下面那段引文抽出来：称量研磨 → 装坩埚 → 分段热处理）；
  * 下：Experimental Guidance 引文（PPT 第 9 页原文，四类信息用彩色 run 而不是高亮块，仍是一个可编辑文本框）+ 四类信息图例。

usage: python3 scenes_deck_overview.py [--art <dir>]
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import deckstyle as DS  # noqa: E402

DS.use_theme('sagemat')
from deckstyle import Deck, TONE, SZ, KIND  # noqa: E402
from lib.scene import CJK, LATIN  # noqa: E402

INK, MUTED, NAVY = DS.INK, DS.MUTED, DS.NAVY
_REPO = pathlib.Path(__file__).resolve().parents[3]
JOBS_DIR = pathlib.Path(os.environ.get('GOAI_FIGSTUDIO_JOBS', _REPO.parent / 'final_round/figstudio/jobs'))
ART = None

# 引文（PPT 第 9 页原文，一字不改）；四类信息 → 颜色
QUOTE = [
    ('The phosphors of ', None),
    ('Sr4.75-5x-5yCa5xBa5y(PO4)2(SiO4):Eu0.252+ (0.01 ≤ x ≤ 1; 0.01 ≤ y ≤ 0.5)', 'comp'),
    (' were prepared: I) Sr4.75-5xCa5x((PO4)(SiO4)0.5)2:Eu0.252+ (0.01 ≤ x ≤ 0.95); and II) Sr4.75-5yBa5y(PO4) 2(SiO4):Eu0.252+ '
     '(y = 0.01, 0.05, 0.1, 0.2, 0.5). The starting materials were ', None),
    ('CaCO3 (99.99%), SrCO3 (99.99%), BaCO3 (99.99%), NH4H2PO4 (99.99%), SiO2 (99.99%), Eu2O3 (99.99%)', 'mat'),
    ('. The stoichiometric chemicals ', None),
    ('were weighed and thoroughly mixed in an agate mortar, then transferred to a corundum crucible', 'ops'),
    (' and ', None),
    ('heated at 350 (in air), 1000 (in air) and 1300 °C (in reducing (h2) atmosphere)', 'heat'),
    (' for 15 h, respectively. In the experiments no signals from Eu3+ were detected on the emission spectra, indicating the Eu3+ ions '
     'were successfully reduced to Eu2+ ions in the present experimental conditions.', None),
]
CAT = dict(comp=('组成与掺杂', 'amber', 'structure'), mat=('起始原料', 'peach', 'precursors'), ops=('操作：称量 · 研磨 · 装料', 'green', 'mortar'),
           heat=('热处理程序与气氛', 'blue', 'thermal'))


# 素材表 D 还没生成时（生图通道受限）用已有素材库里最接近的格子顶上；D 一到，同名文件优先
FALLBACK = dict(bookbrain='litdb', papers='products', notebook='condtable', furnacebench='furnace', isolab='robotlab', mortar='precursors',
                crucible='fluxgrowth', thermal='furnace', balance='precursors')


def A(name):
    if not ART:
        return None
    for n in (name, FALLBACK.get(name)):
        if n and (pathlib.Path(ART) / f'{n}.png').exists():
            return (f'art/{n}.png', f'cropped from the image-model asset sheet, cell "{n}" (Codex image_gen)')
    return None


def slot(d, cid, box, name, container=None, provenance=None):
    a = A(name)
    if a:
        d.art(cid, box, a[0], provenance or a[1], container=container)
    else:
        x, y, w, h = box
        d.sc.shape(cid, [x + w * 0.1, y + h * 0.1, w * 0.8, h * 0.8], shape='ellipse', fill='#F3F4F6', stroke='#D1D5DB', stroke_width=1.5,
                   dash=[6, 5], container=container)


def allow(d, ids, others, why):
    for e in d.sc.els:
        if e['id'] in ids:
            e['allow_overlap_with'] = sorted(set(e.get('allow_overlap_with', [])) | set(others))
            e.setdefault('overlap_reason', why)


def runs_text(d, tid, box, runs, size, container=None, color=None, align='left', line_height=1.35):
    """One editable paragraph whose spans carry their own colour/weight (img2ppt `runs`)."""
    el = {'id': tid, 'kind': 'text', 'z': d.sc._z(), 'box': [int(round(v)) for v in box], 'runs': runs, 'font_size': size,
          'font_family': LATIN, 'cjk_font_family': CJK, 'bold': False, 'color': color or INK, 'align': align, 'valign': 'top',
          'wrap': True, 'fit': 'shrink', 'min_font_size': max(9, size - 3), 'line_height': line_height}
    if container:
        el['container'] = container
    d.sc.els.append(el)
    return tid


def chip(d, cid, box, text, art, container, size=15):
    x, y, w, h = box
    d.sc.shape(cid, box, fill='#FFFFFF', stroke=DS.NODE_STROKE, stroke_width=1.5, radius=10, container=container)
    slot(d, cid + '_art', [x + 6, y + 4, h - 8, h - 8], art, container=cid)
    d.sc.text(cid + '_t', [x + h + 4, y, w - h - 12, h], text, size, color=INK, align='left', container=cid, fit='shrink', min_font_size=size - 3)


def write(d, job):
    p = JOBS_DIR / job / 'scene.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    d.write(p)


def overview():
    d = Deck('整体方案页：文献数据库 → 结构化知识 → 合成方案 → OpenLab 实验步骤；Experimental Guidance 引文四类信息着色（round 4, deck theme）')
    sc = d.sc
    TOP, PH = 118, 446

    # ---------------------------------------------------------------- 左：文献数据库
    P1 = [40, TOP, 352, PH]
    p1 = d.panel('p1', P1, '文献数据库', 'blue')
    slot(d, 'lit_art', [76, 176, 280, 148], 'bookbrain', p1)
    sc.text('lit_n', [52, 330, 328, 52], '88,343,822', 40, bold=True, color=TONE['teal']['accent'], container=p1)
    sc.text('lit_u', [52, 382, 328, 28], '篇文献 · 全文 80.5 TB', 18, bold=True, color=INK, container=p1)
    slot(d, 'donut', [60, 424, 120, 120], 'donut20', p1, provenance='ring meter rendered locally (PIL) from the value 20%, teal on a light track')
    sc.text('donut_t', [72, 460, 96, 48], '~20%', 26, bold=True, color=TONE['teal']['accent'], container=p1)
    allow(d, ('donut_t',), ['donut'], 'the value sits in the hole of its own ring meter')
    allow(d, ('donut',), ['donut_t'], 'the value sits in the hole of its own ring meter')
    sc.text('donut_c', [192, 446, 188, 30], '化学学科论文占比', 19, bold=True, color=INK, align='left', container=p1)
    sc.text('donut_s', [192, 478, 188, 24], '合成条件散落在正文段落中', 14, color=MUTED, align='left', container=p1)
    sc.text('donut_s2', [192, 502, 188, 24], '尚未结构化', 14, color=MUTED, align='left', container=p1)

    # ---------------------------------------------------------------- 中：三段链 + 口号
    CX0, CW = 416, 704
    cells = [('c_pap', 'papers', '文献中的合成描述'), ('c_nb', 'notebook', '结构化的合成知识'), ('c_fur', 'furnacebench', '合成方案与实验装置')]
    aw, gap = 196, 58
    x0 = CX0 + (CW - (3 * aw + 2 * gap)) / 2
    for k, (cid, art, cap) in enumerate(cells):
        x = x0 + k * (aw + gap)
        slot(d, cid, [x, 132, aw, 150], art)
        sc.text(cid + '_c', [x - 20, 288, aw + 40, 30], cap, 18, bold=True, color=INK)
        if k < 2:
            d.flow(f'f_c{k}', [(x + aw + 8, 207), (x + aw + gap - 8, 207)], 'main')
    # 口号（两行，可编辑文本；run 分色）
    runs_text(d, 'slogan1', [CX0, 344, CW, 90], [{'text': 'Could ', 'color': '#154A97'}, {'text': 'AI', 'color': '#E97132'}], 66, align='center',
              line_height=1.2)
    runs_text(d, 'slogan2', [CX0, 436, CW, 86], [{'text': 'Dream of ', 'color': '#154A97'}, {'text': 'Science', 'color': '#0E2841'}], 66,
              align='center', line_height=1.2)
    for e in sc.els:
        if e['id'] in ('slogan1', 'slogan2'):
            e['bold'], e['italic'], e['wrap'], e['fit'], e['valign'] = True, True, False, 'strict', 'middle'
            e.pop('min_font_size', None)
    sc.text('slogan_s', [CX0, 522, CW, 34], '大模型读懂文献里的合成经验，生成可执行的研究方案，交给自动化实验室执行与仿真', 17, color=MUTED,
            fit='shrink', min_font_size=14)

    # ---------------------------------------------------------------- 右：实验流程 Step 1 / 2 / 3
    P3 = [1144, TOP, 352, PH]
    p3 = d.panel('p3', P3, '实验流程 Step 1–3', 'green')
    slot(d, 'lab_art', [1156, 172, 328, 186], 'isolab', p3)
    sc.text('lab_c', [1156, 362, 328, 30], '繁琐细致的实验步骤', 20, bold=True, color=INK, container=p3)
    steps = [('s1', '① 称量后在玛瑙研钵中充分研磨混合', 'mortar'), ('s2', '② 转移至刚玉坩埚', 'crucible'),
             ('s3', '③ 分段热处理：350 / 1000 / 1300 °C', 'thermal')]
    for k, (cid, t, art) in enumerate(steps):
        chip(d, cid, [1156, 402 + k * 52, 328, 44], t, art, p3, size=14)

    # ---------------------------------------------------------------- 下：Experimental Guidance 引文
    QY, QH = 584, 270
    sc.shape('q', [40, QY, 1456, QH], fill='#FFFFFF', stroke=NAVY, stroke_width=2, radius=16)
    sc.shape('q_bar', [40, QY, 10, QH], shape='rect', fill=TONE['blue']['accent'], container='q')
    slot(d, 'q_art', [64, QY + 24, 150, 190], 'papers', 'q')
    sc.shape('q_pill', [236, QY + 16, 344, 34], fill=TONE['blue']['accent'], radius=17, container='q')
    sc.text('q_pill_t', [236, QY + 16, 344, 34], 'Experimental Guidance · 文献原文', 17, bold=True, color='#FFFFFF', container='q_pill')
    sc.text('q_open', [228, QY + 52, 36, 60], '“', 44, bold=True, color=TONE['blue']['accent'], container='q')
    runs = []
    for text, cat in QUOTE:
        r = {'text': text}
        if cat:
            r['color'], r['bold'] = TONE[CAT[cat][1]]['accent'], True
        runs.append(r)
    runs_text(d, 'quote', [262, QY + 58, 880, 166], runs, 14.5, container='q', line_height=1.45)
    sc.text('q_close', [1102, QY + 166, 36, 60], '”', 44, bold=True, color=TONE['blue']['accent'], container='q')
    allow(d, ('q_close',), ['quote'], 'closing quotation mark in the paragraph\'s last-line white space')
    allow(d, ('quote',), ['q_close'], 'closing quotation mark in the paragraph\'s last-line white space')
    sc.text('q_cap', [236, QY + 232, 900, 32], '简短且复杂的高密度知识信息 → 由大模型抽取为结构化合成方案（组成 · 原料 · 操作 · 条件）', 18, bold=True,
            color=NAVY, container='q', fit='shrink', min_font_size=15)
    # 图例：四类信息
    LX = 1160
    sc.text('lg_t', [LX, QY + 18, 320, 30], '一段话里的四类信息', 17, bold=True, color=INK, align='left', container='q')
    for k, key in enumerate(('comp', 'mat', 'ops', 'heat')):
        label, tone, art = CAT[key]
        y = QY + 56 + k * 50
        sc.shape(f'lg{k}', [LX, y, 320, 42], fill=TONE[tone]['fill'], stroke=TONE[tone]['stroke'], stroke_width=1.5, radius=10, container='q')
        slot(d, f'lg{k}_art', [LX + 6, y + 3, 36, 36], art, f'lg{k}')
        sc.text(f'lg{k}_t', [LX + 48, y, 266, 42], label, 15, bold=True, color=TONE[tone]['text'], align='left', container=f'lg{k}', fit='shrink',
                min_font_size=13)
    write(d, 'deck_overview_r4')


if __name__ == '__main__':
    args = sys.argv[1:]
    if '--art' in args:
        ART = args[args.index('--art') + 1]
    overview()
