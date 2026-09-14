"""English variants of the five round-5 figures.

The scenes are geometry + strings, so the English set is produced by mapping every visible string and re-fitting
the type, not by re-authoring the layouts: same design system, same topology, same repairs.

Terminology comes from the papers' own English sections and from the English figures the typesetting lane
already produced (figures/pdf_tikz/*_en.pdf), so the figstudio figures and the English prose use one vocabulary.
Anything not in the table is reported as untranslated rather than shipped in Chinese.

Latin text is wider than the CJK it replaces, so every mapped string gets a shrink floor; the caller checks the
result with tools/precheck.py before the build.

usage: python3 tools/r5_en.py
"""
import json
import re
import sys
import pathlib
from pathlib import Path

# --- paths -------------------------------------------------------------------
# The design system lives in the repo; the job dir is where scene.json files are written and where
# super_img2ppt reads them from. Override with GOAI_FIGSTUDIO_JOBS when building somewhere else.
import os
_REPO = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / 'skills' / 'goai-figure-studio'))
JOBS_DIR = pathlib.Path(os.environ.get('GOAI_FIGSTUDIO_JOBS', _REPO.parent / 'final_round/figstudio/jobs'))

from lib import Scene, pack_pill_rows

JOBS = JOBS_DIR
PAIRS = [('fig01_r5', 'fig01_r5_en'), ('fig02_r5', 'fig02_r5_en'), ('fig03_r5', 'fig03_r5_en'),
         ('bzso_roadmap_r5', 'bzso_roadmap_r5_en'), ('bzso_taxonomy_r5', 'bzso_taxonomy_r5_en')]

TR = {
    # ---- group bands
    '文献证据': 'Literature Evidence', '实验方法': 'Experimental Items', '可回答的问题': 'Answerable Questions',
    '产物表征': 'Characterization', '结果反馈': 'Result Feedback', '判断提醒': 'Open Questions',
    # ---- fig 1 · evidence classes and the shared ledger
    '目标化合物直接报道': 'Direct Reports on Target', '同类 Ba–Y 四方硅酸盐': 'Same Ba–Y Tetragonal Silicates',
    '结构相关化合物': 'Crystal-Chemical Neighbors', '工艺参照研究': 'Process Reference Studies',
    '非相关资料': 'Outside Study Scope', '相同实验项目下比较': 'Compared on Shared Items',
    '原料与配比': 'Ratio and raw materials', '热历史': 'Thermal history', '气氛': 'Atmosphere',
    '容器与助熔剂': 'Crucible and flux', '冷却与分离': 'Cooling and separation', '产物表征 ': 'Product characterization',
    '直接条件复现': 'Direct Reproduction', '系列内相图与结构比较': 'Family Phase Comparison',
    '方法与变量结构': 'Methods and Variables', '划定研究范围': 'Study Boundary Only',
    '与目标相的距离': 'Distance from target', '近': 'Near', '远': 'Far',
    '近邻条件 ≠ 已验证配方': 'Neighbor conditions ≠ proven recipe', '排除': 'Excluded',
    # ---- fig 2 · routes, record, characterization
    '外加助熔': 'External Flux', '自熔/熔体': 'Self-Flux / Melt', '固相陶瓷': 'Solid-State Ceramic',
    '机械化学预活化': 'Mechanochemical',
    '溶解': 'Dissolve', '保温': 'Dwell', '缓冷分离': 'Slow cool, separate',
    '均化': 'Homogenize', '自发成核': 'Nucleate', '受控冷却': 'Controlled cooling',
    '混合压片': 'Mix and press', '煅烧复磨': 'Calcine, regrind', '烧结': 'Sinter',
    '高能研磨': 'High-energy mill', '活化': 'Activate', '后续相形成': 'Phase formation',
    '预烧熔化': 'Pre-melt', '籽晶提拉': 'Seed pull', '退火': 'Anneal',
    '虚线＝工艺参照': 'Dashed = process reference', '统一实验记录': 'Unified Experiment Record',
    '配比与原料': 'Ratio and raw materials', '温度—时间与气氛': 'Temperature–time, atmosphere',
    '坩埚与助熔剂': 'Crucible, flux', '冷却、生长与分离': 'Cooling, growth, separation',
    '抽取框架 ≠ 实验配方': 'Framework ≠ recipe',
    '单晶结构': 'Single-Crystal Structure', '结构归属与位点占据': 'Structural identity and site occupancy',
    '块体相纯与杂相': 'Bulk phase purity and impurities', '成分与污染': 'Composition and Contamination',
    '名义—局域—体平均': 'Nominal–local–bulk mean', '高温稳定性': 'High-Temperature Stability',
    '原位高温 ≠ 冷却回收': 'In situ HT ≠ cooled product',
    '配比 · 温度': 'Ratio · temperature', '熔体 · 容器': 'Melt · crucible', '混合 · 煅烧': 'Mixing · calcination',
    '研磨 · 污染': 'Milling · contamination', '籽晶 · 退火': 'Seeding · annealing',
    '结构': 'Structure', '相组成': 'Phase composition', '成分': 'Composition', '高温': 'High temperature',
    # ---- fig 3 · research roadmap
    '文献依据': 'Literature Basis', 'Ba–Y–Si–O 系列': 'Ba–Y–Si–O family',
    'Ba–Zn–Si–O 结构相关化合物': 'Ba–Zn–Si–O structural neighbors', 'Y–Si–O 工艺参照': 'Y–Si–O process reference',
    '结构假设': 'Structural Hypothesis', '局部组成网格': 'Local composition grid',
    'Zn–Y–氧计量耦合': 'Zn–Y–O stoichiometric coupling', '竞争相与玻璃区': 'Competing phases, glass region',
    '前驱体筛选': 'Screened Precursors', '模型排序的候选': 'Model-ranked candidates',
    '模型排序 ≠ 验证': 'Ranking ≠ validation',
    '固相反应': 'Solid-State Route', '分段煅烧': 'Calcine', '复磨': 'Regrind',
    '块体相区与相纯度': 'Bulk phase purity',
    '高温溶液法晶体生长': 'Solution Growth', '助熔': 'Flux', '缓冷': 'Slow cool',
    '单晶结构与液相选择性': 'Single-crystal structure',
    '表征手段': 'Characterization', '高温相与冷却产物': 'HT vs cooled phases',
    '更新组成与工艺': 'Update composition and process',
    'Zn 是否进入并与氧计量耦合？': 'Does Zn enter and couple with oxygen stoichiometry?',
    '稳定相区还是液相选择性？': 'Stable phase field, or liquid selectivity?',
    '实际组成与结构信号如何对应？': 'How do actual composition and structural signals correspond?',
    # ---- BaZn2Si2O7 roadmap
    '结构基础': 'Structural Basis', '低温与高温多晶型': 'LT and HT polymorphs',
    '合成路线': 'Synthesis Routes', '固相 · 溶胶—凝胶': 'Solid-state · sol–gel',
    '相控制': 'Phase Control', '组成 · 热处理': 'Composition · annealing',
    '近邻体系': 'Neighbor Systems', '类似物判据': 'Analogue Criteria',
    '实验优先级': 'Test Priorities', '相图 · 结构 · 热力学': 'Phase diagram · structure · thermodynamics',
    '结构约束': 'Structural constraints', '条件窗口': 'Condition window', '可迁移变量': 'Transferable variables',
    '比较边界': 'Comparison boundary', '缺口驱动': 'Gap-driven',
    # ---- BaZn2Si2O7 taxonomy
    '目标相': 'Target phase', '结构与多晶型': 'Structure and Polymorphs', '相变 · 配位': 'Transition · sites',
    '组成与热处理': 'Composition and Annealing', 'Ba/Sr · Zn 位': 'Ba/Sr · Zn site',
    '玻璃析晶': 'Glass Crystallization', '成核 · 生长': 'Nucleation · growth',
    'Ba2ZnSi2O7 等': 'Ba2ZnSi2O7 family', '证据边界': 'Evidence Boundary',
    '直接 / 近邻 / 推断': 'Direct / near / implied', '未见直接报道': 'No direct report',
    '制备': 'Preparation', '变量': 'Variables', '晶化': 'Crystallization',
    '近邻': 'Neighbors', '判读': 'Interpretation', '类比': 'Analogy',
}

CJK = re.compile(r'[一-鿿　-〿＀-￯]')
NOTE_EN = {
    'fig01_r5_en': 'Figure 1 · Applicability of different literature classes to the target compound (round 5, F02).',
    'fig02_r5_en': 'Figure 2 · Condition comparison across synthesis routes and product characterization (round 5, F01).',
    'fig03_r5_en': 'Figure 3 · Research roadmap of this review (round 5, F02).',
    'bzso_roadmap_r5_en': 'BaZn2Si2O7 · Reading roadmap of this review (round 5, F02).',
    'bzso_taxonomy_r5_en': 'BaZn2Si2O7 · Taxonomy of synthesis and phase control (round 5, F02).',
}


# A pill or a zone label sizes itself from its own string, so the English one is simply re-measured around the
# same anchor. A card title or a token sits in a box the layout fixed, so it wraps to a second line or shrinks.
PILL_TEXT = re.compile(r'(.+_p)_t$')
FREE_PILLS = ('cav_t', 'leg_t')


def _relayout_label(el):
    """Zone label: grow the box to the right for the English string (rotated labels keep their frame)."""
    if el.get('rotation'):
        return
    el['box'][2] = int(Scene.measure(el['text'], el['font_size']) + 26)


def _is_capsule(shape):
    """A pill is fully rounded; a record token has a small corner radius."""
    return shape.get('radius', 0) * 2 >= shape['box'][3] - 1


def _relayout_pill(slide, el, pill_id, page_w, padx=16):
    """Pill: re-measure shape and text together, keeping the pill's centre, height and page bounds."""
    shape = next((e for e in slide['elements'] if e['id'] == pill_id), None)
    if shape is None or not _is_capsule(shape):
        return
    cx = shape['box'][0] + shape['box'][2] / 2
    tw = Scene.measure(el['text'], el['font_size']) + 2 * padx
    left = min(max(6, cx - tw / 2), max(6, page_w - 6 - tw))   # a wider English pill must stay on the page
    shape['box'][0] = int(round(left))
    shape['box'][2] = int(round(tw))
    el['box'][0] = int(round(shape['box'][0] + padx - 6))
    el['box'][2] = int(round(tw - 2 * padx + 12))


def _bbox(el):
    if el['kind'] == 'line':
        xs = [q[0] for q in el['points']]; ys = [q[1] for q in el['points']]; w = el.get('stroke_width', 2)
        return [min(xs) - w, min(ys) - w, max(xs) + w, max(ys) + w]
    x, y, w, h = el['box']
    return [x, y, x + w, y + h]


def _reexempt_pills(slide):
    """A label pill masks whatever it sits on; after re-measuring, declare the overlaps its new width created."""
    els = slide['elements']
    caps = [e for e in els if e['kind'] == 'shape' and _is_capsule(e)]
    for cap in caps:
        family = {cap['id'], cap['id'] + '_t'}
        for el in [e for e in els if e['id'] in family]:
            eb = _bbox(el)
            for other in els:
                if other['id'] in family:
                    continue
                ob = _bbox(other)
                if eb[0] < ob[2] and eb[2] > ob[0] and eb[1] < ob[3] and eb[3] > ob[1]:
                    for a, b in ((el, other), (other, el)):
                        a['allow_overlap_with'] = sorted(set(a.get('allow_overlap_with', []) + [b['id']]))
                        a['overlap_reason'] = 'connector label sits on what it annotates, visible in source'


def translate(src: Path, dst: Path, job: str) -> list[str]:
    doc = json.loads(src.read_text(encoding='utf-8'))
    slide = doc['slides'][0]
    missing = []
    for el in slide['elements']:
        if el['kind'] != 'text':
            continue
        zh = el['text']
        if not CJK.search(zh):
            continue                      # already Latin (formulas, PXRD/Rietveld, step numbers)
        en = TR.get(zh)
        if en is None:
            missing.append(zh)
            continue
        el['text'] = en
        size = el['font_size']
        # Latin at the same point size runs wider than CJK: let it shrink, but not below readable print size
        el['fit'] = 'shrink'
        el['min_font_size'] = max(12, min(el.get('min_font_size', size), size - 8))
        # a font_group shrinks its members together, so the longest English string would hold the whole group at
        # the Chinese size; English boxes fit independently instead (the floor keeps the spread small)
        el.pop('font_group', None)
        m = PILL_TEXT.match(el['id'])
        if el['id'].endswith('_l'):
            _relayout_label(el)
        elif m:
            # a connector label lives in the gutter between two connectors; English runs wider, so drop it one
            # step before re-measuring or the pill reaches the next connector
            el['font_size'] = max(15, size - 2)
            el['min_font_size'] = min(el['min_font_size'], el['font_size'])
            _relayout_pill(slide, el, m.group(1), slide['width'])
        elif el['id'] in FREE_PILLS:
            _relayout_pill(slide, el, el['id'][:-2], slide['width'])
        elif el['box'][3] >= size * 2.1:
            el['wrap'] = True             # the box has room for a second line
    # the Chinese row fitted where it was authored; the wider English pills need the row packed again
    pack_pill_rows(slide['elements'], slide['width'])
    _reexempt_pills(slide)
    slide['notes'] = NOTE_EN.get(job, slide.get('notes', ''))
    doc['slides'][0] = slide
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')
    return missing


def main():
    total_missing = []
    for zh_job, en_job in PAIRS:
        miss = translate(JOBS / zh_job / 'scene.json', JOBS / en_job / 'scene.json', en_job)
        print(f'{en_job}: written' + (f', {len(miss)} untranslated' if miss else ''))
        for m in miss:
            print('    MISSING:', m)
        total_missing += miss
    if total_missing:
        print('\n!! untranslated strings remain — add them to TR before building')
        return 1
    print('\nall visible strings translated')
    return 0


if __name__ == '__main__':
    sys.exit(main())
