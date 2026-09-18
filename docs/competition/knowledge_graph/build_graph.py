#!/usr/bin/env python3
"""Build the SAGE-Mat knowledge forest (graph.json + single-file HTML) from the evidence package.

Every node and edge is derived from files that already ship with the submission, so the
graph is a *view* of the survey, not a new claim:

  inputs/scope.md                     -> 调研目标（5 个核心问题）与 8 个 MECE 子主题（原有的个人知识树）
  notes/taxonomy.md                   -> 文献树：8 个分支 → 35 个叶节点 → 支撑文献；§5 证据缺口
  references.bib + papers.jsonl       -> 51 篇通过 ref_gate 的文献（题名 / 年份 / DOI / 期刊 / 作者）
  claim_evidence.jsonl                -> 100 条正文主张及其引用证据（强/弱、全文是否在包内、条件溯源）
  sections/03_condition_matrix.tex    -> 29 条合成条件记录（A1、B1–B6、C1–C22）= 合成路线实体的实例
  ideas/precursor_predictions.md      -> RECIPE 两步逆合成前驱体预测（Zn / Mg / Co 目标，各 Top-5）
  ideas/experiment_directions.md      -> 四个优先实验方向
  补充案例 / LLZO 诊断轮 ledger.json    -> 从同一根长出的其他树
  站点 showcase.html                    -> 五条 OpenLab 自动化实验工作流（仿真）

Compounds / routes / precursors / characterization are curated lists (see CURATED_* below);
their links to papers, claims and condition records are computed by pattern matching on the
package text, and every link keeps the record it came from so it can be audited.

Usage:  python3 build_graph.py            # writes graph.json and knowledge_graph.html next to this file
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EVID = REPO / 'submission/02_研究数据与证据包'
CASE = REPO / 'submission/03_运行与评测包/正式案例_BYZSO冷启动'
SUPP = REPO / 'submission/03_运行与评测包/补充案例_20260903'
LLZO_DIAG = REPO / 'submission/03_运行与评测包/LLZO诊断轮'

LEVEL_RANK = {'D0': 0, 'D1': 1, 'N1': 2, 'P1': 3, 'H': 4, 'X': 5}
LEVEL_NAME = {'D0': '目标相直接证据', 'D1': '同一身份谱系', 'N1': '晶体化学近邻', 'P1': '工艺近邻', 'X': '边界 / 排除', 'H': '假设目标（未合成）'}


# ----------------------------------------------------------------------------- helpers
def read(p: Path) -> str:
    return p.read_text(encoding='utf-8')


def balanced(s: str, i: int) -> tuple[str, int]:
    """s[i] == '{' -> (inner text, index after the matching '}')."""
    assert s[i] == '{'
    d, j = 0, i
    while j < len(s):
        if s[j] == '{':
            d += 1
        elif s[j] == '}':
            d -= 1
            if d == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError('unbalanced brace')


GREEK = {'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ', 'approx': '≈', 'geq': '≥', 'leq': '≤', 'times': '×', 'circ': '°', 'pm': '±', 'rightarrow': '→', 'to': '→'}


def math2html(m: str) -> str:
    m = m.replace('\\mathrm', '').replace('\\,', '\u2009').replace('{:}', ':')
    for k, v in GREEK.items():
        m = m.replace('\\' + k, v)
    out, i = '', 0
    while i < len(m):
        c = m[i]
        if c in '_^':
            tag = 'sub' if c == '_' else 'sup'
            if i + 1 < len(m) and m[i + 1] == '{':
                inner, i = balanced(m, i + 1)
            else:
                inner, i = m[i + 1], i + 2
            inner = inner.replace('-', '−')
            out += f'<{tag}>{inner}</{tag}>'
            continue
        if c in '{}':
            i += 1
            continue
        out += c
        i += 1
    out = out.replace('--', '–')
    if re.fullmatch(r'[a-zA-Z]', out):
        out = f'<i>{out}</i>'
    return out


def tex2html(s: str) -> str:
    """LaTeX table cell / sentence -> compact HTML (only the constructs used in the package)."""
    s = re.sub(r'\\cite\{[^}]*\}', '', s)
    s = re.sub(r'\\label\{[^}]*\}', '', s)
    # \shortstack[l]{a\\b}
    while True:
        k = s.find('\\shortstack')
        if k < 0:
            break
        j = s.find('{', k)
        inner, e = balanced(s, j)
        s = s[:k] + inner.replace('\\\\', ' ') + s[e:]
    for cmd, wrap in (('texttt', ('<code>', '</code>')), ('textbf', ('<b>', '</b>')), ('emph', ('<i>', '</i>')), ('textit', ('<i>', '</i>'))):
        while True:
            k = s.find('\\' + cmd + '{')
            if k < 0:
                break
            inner, e = balanced(s, k + len(cmd) + 1)
            s = s[:k] + wrap[0] + inner + wrap[1] + s[e:]
    # $...$
    parts = s.split('$')
    for i in range(1, len(parts), 2):
        parts[i] = math2html(parts[i])
    s = ''.join(parts)
    s = (s.replace('\\,', '\u2009').replace('\\S', '§').replace('\\%', '%').replace('\\&', '&').replace('\\_', '_')
         .replace('\\slash', '/').replace('~', ' ').replace('{}', '').replace('\\\\', ' ').replace('--', '–').replace('\\ ', ' '))
    s = re.sub(r'\\[a-zA-Z]+', '', s)
    s = s.replace('{', '').replace('}', '')
    return re.sub(r'\s+', ' ', s).strip()


SUBS = str.maketrans('₀₁₂₃₄₅₆₇₈₉', '0123456789')


def norm(s: str) -> str:
    """Normalise a formula-bearing string for matching: strip TeX/HTML/spaces, unify dashes."""
    s = re.sub(r'<[^>]+>', '', s)
    s = s.translate(SUBS)
    s = s.replace('$', '').replace('{', '').replace('}', '').replace('_', '').replace('^', '').replace('\\', '')
    s = s.replace('−', '-').replace('–', '-').replace('\u2009', '').replace(' ', '')
    return s.lower()


def md_formula(s: str) -> str:
    """Markdown/plain formula (BaCO3, Y2O3, Ba5Y12ZnSi8O40, Mg5H2(C2O7)2) -> HTML with subscripts."""
    return re.sub(r'(?<=[A-Za-z\)\]])(\d+(?:\.\d+)?)', r'<sub>\1</sub>', s)


# ----------------------------------------------------------------------------- inputs
def parse_scope(text: str):
    qs, subs = [], []
    sec = None
    for line in text.splitlines():
        if line.startswith('## '):
            sec = line[3:].strip()
            continue
        m = re.match(r'^(\d+)\.\s+(.*)$', line.strip())
        if not m:
            continue
        if sec == '核心问题':
            qs.append(m.group(2).replace('`', ''))
        elif sec == 'MECE 子主题':
            mm = re.match(r'\*\*(.+?)\*\*：(.*)', m.group(2))
            subs.append((mm.group(1), mm.group(2)))
    return qs, subs


def parse_taxonomy(text: str):
    branches, leaves, gaps, unassigned = [], [], [], []
    cur_branch = cur_leaf = None
    sec = None
    for line in text.splitlines():
        if line.startswith('## '):
            sec = line[3:].strip()
            cur_branch = cur_leaf = None
            continue
        m = re.match(r'^### ([A-H])\. (.+)$', line)
        if m and sec.startswith('2.'):
            cur_branch = {'id': m.group(1), 'name': m.group(2).strip(), 'leaves': []}
            branches.append(cur_branch)
            cur_leaf = None
            continue
        m = re.match(r'^#### ([A-H]\d)\. (.+?)(（([^）]*)）)?\s*$', line)
        if m and cur_branch:
            cur_leaf = {'id': m.group(1), 'name': m.group(2).strip(), 'levels': (m.group(4) or '').split('/') if m.group(4) else [], 'keys': [], 'fields': {}}
            cur_leaf['levels'] = [x.strip() for x in cur_leaf['levels'] if x.strip()]
            cur_branch['leaves'].append(cur_leaf)
            leaves.append(cur_leaf)
            continue
        m = re.match(r'^- \*\*(.+?)\*\*：(.*)$', line)
        if m and cur_leaf:
            k, v = m.group(1), m.group(2).strip()
            if k.startswith('支撑 key'):
                cur_leaf['keys'] = re.findall(r'`([^`]+)`', v)
            else:
                cur_leaf['fields'][k] = v.replace('`', '')
            continue
        if sec and sec.startswith('5.'):
            m = re.match(r'^(\d+)\.\s+\*\*(.+?)\*\*：(.*)$', line.strip())
            if m:
                gaps.append({'id': f'GAP{int(m.group(1)):02d}', 'name': m.group(2), 'text': m.group(3).replace('`', '')})
        if sec and sec.startswith('4.'):
            m = re.match(r'^- `([^`]+)`：(.*)$', line.strip())
            if m:
                unassigned.append((m.group(1), m.group(2)))
    return branches, leaves, gaps, unassigned


def parse_bib(text: str):
    out = {}
    i = 0
    while True:
        k = text.find('@', i)
        if k < 0:
            break
        j = text.find('{', k)
        typ = text[k + 1:j].strip().lower()
        body, e = balanced(text, j)
        i = e
        if typ in ('comment', 'string', 'preamble'):
            continue
        key, _, rest = body.partition(',')
        key = key.strip()
        fields = {}
        p = 0
        while p < len(rest):
            m = re.compile(r'\s*(\w+)\s*=\s*').match(rest, p)
            if not m:
                p += 1
                continue
            name = m.group(1).lower()
            p = m.end()
            if p < len(rest) and rest[p] == '{':
                val, p = balanced(rest, p)
            elif p < len(rest) and rest[p] == '"':
                q = rest.find('"', p + 1)
                val, p = rest[p + 1:q], q + 1
            else:
                q = rest.find(',', p)
                q = len(rest) if q < 0 else q
                val, p = rest[p:q], q
            fields[name] = re.sub(r'\s+', ' ', val).strip()
            c = rest.find(',', p)
            p = len(rest) if c < 0 else c + 1
        out[key] = {'type': typ, **fields}
    return out


def bib_title_html(t: str) -> str:
    t = t.replace('{', '').replace('}', '')
    t = re.sub(r'(?<=[A-Za-z\)\]])(\d+(?:\.\d+)?)(?=[A-Za-z\(\[\)\]\s,:;\-–]|$)', r'<sub>\1</sub>', t)
    return html.escape(t, quote=False).replace('&lt;sub&gt;', '<sub>').replace('&lt;/sub&gt;', '</sub>')


def short_authors(a: str) -> str:
    a = a.replace('{', '').replace('}', '')
    first = a.split(' and ')[0].strip()
    if ',' in first:
        first = first.split(',')[0].strip()
    else:
        first = first.split()[-1]
    n = len(a.split(' and '))
    return first + (' et al.' if n > 2 else (' & ' + (a.split(' and ')[1].split(',')[0].strip() if ',' in a.split(' and ')[1] else a.split(' and ')[1].split()[-1]) if n == 2 else ''))


def parse_condition_matrix(text: str):
    rows = {}
    for line in text.splitlines():
        m = re.match(r'^([ABC]\d+) & (.*)\\\\\s*$', line.strip())
        if not m:
            continue
        rid = m.group(1)
        cells = [c.strip() for c in re.split(r'(?<!\\) & ', m.group(2))]
        cells = [tex2html(c) for c in cells]
        raw_cells = [c.strip() for c in re.split(r'(?<!\\) & ', m.group(2))]
        r = rows.setdefault(rid, {'id': rid})
        if len(cells) == 5:  # upper block: 来源与定位, 目标/产物式, 原料/配比/前处理, 合成方法, 关系
            r.update(source=cells[0], product=cells[1], inputs=cells[2], method=cells[3], relation=cells[4])
            km = re.search(r'\\texttt\{([^}]+)\}', raw_cells[0])
            r['key'] = km.group(1) if km else None
            r['product_norm'] = norm(raw_cells[1])
        elif len(cells) == 6:  # lower block
            r.update(temp_time=cells[0], atmosphere=cells[1], crucible_flux=cells[2], cooling=cells[3], product_char=cells[4], missing=cells[5])
    return [rows[k] for k in sorted(rows, key=lambda x: (x[0], int(x[1:])))]


def parse_recipe(text: str):
    targets, cur = [], None
    for line in text.splitlines():
        m = re.match(r'^## (.+?) (Ba5Y12\w+)\s*$', line)
        if m:
            cur = {'label': m.group(1), 'formula': m.group(2), 'rows': [], 'note': ''}
            targets.append(cur)
            continue
        m = re.match(r'^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*([\d.]+)\s*\|\s*$', line)
        if m and cur:
            cur['rows'].append({'rank': int(m.group(1)), 'combo': m.group(2), 'p': float(m.group(3))})
            continue
        if cur and cur['rows'] and line.strip() and not line.startswith('|') and not line.startswith('#') and not cur['note']:
            cur['note'] = line.strip()
    return targets


def parse_directions(text: str):
    out, cur = [], None
    for line in text.splitlines():
        m = re.match(r'^## (D\d)：(.+)$', line)
        if m:
            cur = {'id': m.group(1), 'name': m.group(2).strip(), 'text': ''}
            out.append(cur)
            continue
        if line.startswith('## '):
            cur = None
        if cur and line.strip():
            cur['text'] += line.strip() + ' '
    for d in out:
        d['text'] = d['text'].strip()
    return out


# ----------------------------------------------------------------------------- curated entity tables
# (formula_html, class, aliases used for matching on normalised text, note)
CURATED_COMPOUNDS = [
    ('cmp_target', 'Ba<sub>5</sub>Y<sub>12</sub>Zn[O(SiO<sub>4</sub>)]<sub>8</sub>', 'D0', ['ba5y12zn', 'byzso', 'ba5y12znsi8o40'], '目标相；I-42m 非中心对称硅酸盐，2024 年首次报道，开放体系高温溶液法 + SCXRD'),
    ('cmp_ba5y13', 'Ba<sub>5+x</sub>Y<sub>13</sub>Si<sub>8</sub>O<sub>41</sub>', 'D1', ['ba5+xy13si8o41', 'ba5.2y13si8o41', 'ba5+xy13'], '无 Zn 四方 Ba–Y 相的历史命名（助熔生长伴生相 / 151 组筛选）'),
    ('cmp_baxy26', 'Ba<sub>x</sub>Y<sub>26</sub>Si<sub>16</sub>O<sub>71+x</sub>', 'D1', ['baxy26si16o71+x', 'y26si16o71'], '2024 年单晶重审：非整比调制结构（x≈10.2），陶瓷系列 x=9–14'),
    ('cmp_ba5y13o85', 'Ba<sub>5</sub>Y<sub>13</sub>[SiO<sub>4</sub>]<sub>8</sub>O<sub>8.5</sub>', 'D1', ['ba5y13[sio4]8o8.5', 'ba5y13(sio4)8o8.5', 'ba5y13sio4', 'phasea'], '独立相场确认（EDS / CRED / 同步辐射 PXRD / 中子），I-42m；实验方向二的 x=0 参照相'),
    ('cmp_bay16', 'BaY<sub>16</sub>Si<sub>4</sub>O<sub>33</sub>', 'N1', ['bay16si4o33'], '含 Ba(SiO4)4 孤立单元的 Ba–Y 正硅酸盐端点'),
    ('cmp_bakysi2o7', 'BaKYSi<sub>2</sub>O<sub>7</sub>', 'N1', ['bakysi2o7'], '助熔批次主产物，与 Ba5+xY13Si8O41 伴生'),
    ('cmp_bazn2si2o7', 'BaZn<sub>2</sub>Si<sub>2</sub>O<sub>7</sub>', 'N1', ['bazn2si2o7'], '低温单斜 / 高温正交相变；负热膨胀固溶体母体；补充案例 02 与工作流 wf01 的对象'),
    ('cmp_ba2znsi2o7', 'Ba<sub>2</sub>ZnSi<sub>2</sub>O<sub>7</sub>', 'N1', ['ba2znsi2o7'], '焦硅酸根 Ba–Zn 相；多气氛烧结与抗还原证据'),
    ('cmp_baznsio4', 'BaMSiO<sub>4</sub>（M = Zn, Mg, Co）', 'N1', ['baznsio4', 'bamsio4', 'stuffedtridymite'], 'stuffed-tridymite 同结构族，Zn/Mg/Co 位替代的结构对照'),
    ('cmp_baznsi3o8', 'BaZnSi<sub>3</sub>O<sub>8</sub>', 'N1', ['baznsi3o8'], '低介电微波陶瓷；固相条件记录 C8 / C10'),
    ('cmp_ba3zn4si4o15', 'Ba<sub>3</sub>Zn<sub>4</sub>Si<sub>4</sub>O<sub>15</sub>', 'N1', ['ba3zn4si4o15'], '同一课题组 2024 年高温溶液法中心对称硅酸盐'),
    ('cmp_ba2mgsi2o7', 'Ba<sub>2</sub>MgSi<sub>2</sub>O<sub>7</sub>', 'N1', ['ba2mgsi2o7'], 'Mg 类比相（长余辉 / 微波介电）'),
    ('cmp_basrzn', 'Ba<sub>1−x</sub>Sr<sub>x</sub>Zn<sub>2</sub>Si<sub>2</sub>O<sub>7</sub>', 'P1', ['ba1-xsrxzn2si2o7', 'ba0.5sr0.5zn2sigeo7', 'basrzn'], 'Ba↔Sr 位替代系列（负 / 高热膨胀）'),
    ('cmp_bazn2mx', 'BaZn<sub>2−x</sub>M<sub>x</sub>Si<sub>2</sub>O<sub>7</sub>（M = Mg, Co）', 'P1', ['bazn2-xmgxsi2o7', 'bazn2-xcoxsi2o7', 'bazn2-xmgx', 'bazn2-xcox'], 'Zn 位固溶系列（高温封接）'),
    ('cmp_y2sio5', 'Y<sub>2</sub>SiO<sub>5</sub>', 'P1', ['y2sio5', 'y2o3sio2', 'yttriumoxyorthosilicate', 'yttriumorthosilicate'], 'Czochralski 提拉与熔体挥发控制的工艺参照'),
    ('cmp_y2si2o7', 'Y<sub>2</sub>Si<sub>2</sub>O<sub>7</sub>（α/β/γ/δ）', 'P1', ['y2si2o7'], '多型与热膨胀对照；β 型助熔生长记录 C2'),
    ('cmp_labsio5', 'LaBSiO<sub>5</sub>', 'P1', ['labsio5'], '与 Y2SiO5 / Y2Si2O7 同批高温结晶'),
    ('cmp_ln2sio5', 'Ln<sub>2</sub>SiO<sub>5</sub>（稀土正硅酸盐）', 'P1', ['ln2sio5', 'rare-earthorthosilicate', 'rare-earthsilicate', 'rareearthsilicate', '稀土正硅酸盐', '稀土硅酸盐', '稀土焦硅酸盐'], '稀土正硅酸盐族（Czochralski 路线研究）'),
    ('cmp_yoxyapatite', '钇氧磷灰石 Y<sub>4.67</sub>(SiO<sub>4</sub>)<sub>3</sub>O', 'P1', ['氧磷灰石', 'oxyapatite'], '机械化学预活化后的混相产物之一'),
    ('cmp_zn2sio4', 'Zn<sub>2</sub>SiO<sub>4</sub>', 'P1', ['zn2sio4'], 'Pb/F 助熔慢冷生长（1300→960 °C，1 °C h⁻¹）'),
    ('cmp_basi4o9', 'BaSi<sub>4</sub>O<sub>9</sub>', 'X', ['basi4o9'], 'benitoite / 高压 P3 型 Ba–Si–O 框架负对照'),
    ('cmp_ba2si4o10', 'Ba<sub>2</sub>[Si<sub>4</sub>O<sub>10</sub>]', 'X', ['ba2si4o10', 'ba2[si4o10]'], '高温层状 Ba 硅酸盐负对照'),
    ('cmp_ba3sio5', 'Ba<sub>3</sub>SiO<sub>5</sub>', 'X', ['ba3sio5', 'tribariumsilicate'], 'tribarium silicate 排除性案例'),
    ('cmp_ba5si8o21', 'Ba<sub>5</sub>Si<sub>8</sub>O<sub>21</sub>', 'X', ['ba5si8o21'], 'Ce³⁺ 光学语境，无 Y/Zn'),
    ('cmp_ba2sio4', 'Ba<sub>2</sub>SiO<sub>4</sub>（Ba/Zn 正硅酸盐）', 'X', ['ba2sio4', 'bariumandzincorthosilicate', 'ba/zn正硅酸盐'], '正硅酸钡；Eu³⁺ / Mn²⁺ 发光语境的固相前驱体'),
    ('cmp_liba2gasi2o8', 'LiBa<sub>2</sub>GaSi<sub>2</sub>O<sub>8</sub>', 'X', ['liba2gasi2o8'], '光学语境的前向引用，未纳入结构近邻'),
    ('cmp_mg_target', 'Ba<sub>5</sub>Y<sub>12</sub>MgSi<sub>8</sub>O<sub>40</sub>', 'H', ['ba5y12mgsi8o40', 'ba5y12mg'], 'Mg 类比假设目标（RECIPE 预测；未合成）'),
    ('cmp_co_target', 'Ba<sub>5</sub>Y<sub>12</sub>CoSi<sub>8</sub>O<sub>40</sub>', 'H', ['ba5y12cosi8o40', 'ba5y12co'], 'Co 类比假设目标（RECIPE 预测；未合成）'),
    ('cmp_series', 'Ba<sub>5</sub>Y<sub>13−x</sub>Zn<sub>x</sub>[SiO<sub>4</sub>]<sub>8</sub>O<sub>8.5−x/2</sub>', 'H', ['ba5y13-xznx'], '实验方向二的电荷平衡系列（0 ≤ x ≤ 1.25）；x=0 为无 Zn 参照相，x=1 对应目标组成'),
]

CURATED_ROUTES = [
    ('rt_flux', '外加助熔 · 高温溶液', 'D1', ['外加助熔', '高温溶液'], '相从外加助熔 / 矿化介质中结晶：MoO₃ 类助熔、含氟 / 含铅熔盐或论文明确称 high-temperature solution 的实验'),
    ('rt_melt', '自熔 · 熔体自发结晶', 'D2', ['自熔', '熔体', '无坩埚'], '不以外加助熔剂为主导介质，由反应物自熔、熔体自发成核或无坩埚熔制形成晶相'),
    ('rt_solid', '固相反应 · 陶瓷烧结', 'D3', ['固相', '固–液相烧结', '固-液相烧结'], '氧化物 / 碳酸盐粉体经混合、煅烧、压制、烧结或复烧形成块体 / 粉体'),
    ('rt_mech', '机械化学预活化', 'D4', ['机械化学'], '高能球磨或固液相辅助步骤实质改变反应性 / 成相温度'),
    ('rt_cz', 'Czochralski 提拉', 'D5', ['czochralski'], '射频加热、坩埚熔体、籽晶 / 提拉形成 Y₂SiO₅ 或稀土正硅酸盐晶体；仅作 P1 工艺对照'),
    ('rt_hydro', '水热 / 溶剂热（证据空白）', None, [], '当前通过 ref_gate 的引用池没有目标相或 N1 近邻的水热 / 溶剂热制备证据；列入缺口，不建伪叶'),
]

# (id, label_html, kind, aliases for matching in condition-record inputs/crucible fields and RECIPE combos)
CURATED_AGENTS = [
    ('ag_baco3', 'BaCO<sub>3</sub>', '前驱体', ['baco3']),
    ('ag_y2o3', 'Y<sub>2</sub>O<sub>3</sub>', '前驱体', ['y2o3', 'yo1.5']),
    ('ag_zno', 'ZnO', '前驱体', ['zno']),
    ('ag_sio2', 'SiO<sub>2</sub>', '前驱体', ['sio2']),
    ('ag_mgo', 'MgO', '前驱体', ['mgo']),
    ('ag_co3o4', 'Co<sub>3</sub>O<sub>4</sub>', '前驱体', ['co3o4']),
    ('ag_bao', 'BaO / Ba(NO<sub>3</sub>)<sub>2</sub>（冗余 Ba 源）', '前驱体', ['bao', 'ba(no3)2']),
    ('ag_baf2', 'BaF<sub>2</sub>（含氟，EHS 风险）', '前驱体', ['baf2']),
    ('ag_k2co3', 'K<sub>2</sub>CO<sub>3</sub>', '助熔剂', ['k2co3', 'k2o']),
    ('ag_moo3', 'MoO<sub>3</sub>', '助熔剂', ['moo3']),
    ('ag_na2moo4', 'Na<sub>2</sub>MoO<sub>4</sub> / Li,K 钼酸盐', '助熔剂', ['na2moo4', '钼酸盐']),
    ('ag_pbf', 'Pb<sub>2</sub>ZnSi<sub>2</sub>O<sub>7</sub> / 氟化物', '助熔剂', ['pb2znsi2o7', '氟化物']),
    ('ag_pt', 'Pt 坩埚', '坩埚', ['pt坩埚', 'pt–rh', 'pt-rh']),
    ('ag_al2o3', '氧化铝坩埚', '坩埚', ['氧化铝坩埚']),
    ('ag_ir', 'Ir 坩埚', '坩埚', ['ir坩埚']),
    ('ag_agate', '玛瑙研磨介质', '坩埚', ['玛瑙']),
    ('ag_zro2', 'ZrO<sub>2</sub> 球磨介质', '坩埚', ['zro2球']),
]

CURATED_CHAR = [
    ('ch_scxrd', 'SCXRD 单晶结构', ['scxrd', '单晶精修', '单晶x射线', '单晶结构']),
    ('ch_pxrd', 'PXRD / Rietveld', ['pxrd', 'rietveld', 'xrd']),
    ('ch_neutron', '中子衍射', ['中子']),
    ('ch_sync', 'CRED / 同步辐射', ['cred', '同步辐射']),
    ('ch_comp', 'EDS / EPMA / ICP 成分', ['eds', 'epma', 'icp', '电子探针', '化学分析']),
    ('ch_ht', 'HT-XRD / 热分析 / 膨胀', ['ht-xrd', '热分析', '膨胀', 'dta', 'tg']),
    ('ch_spec', '光学 / 发光光谱', ['光谱', '发光', 'ftir', 'uv', 'ir/']),
]

# 5 core questions -> claim sections (curated reading of the manuscript structure) and status
Q_MAP = [
    ('Q1', '身份与结构', ['问题与范围', '目标相出处', '四方谱系重审', '结构模型'], '已回答', '目标相只有一篇直接报道（2024，高温溶液 + SCXRD）；无 Zn 四方 Ba–Y 谱系已被 2024 年两项独立工作重审（非整比调制结构 / I-42m 相 A）。'),
    ('Q2', '结构近邻判据', ['同类体系已有发现', '分类依据', '结构相关性', '不适用资料的边界'], '已回答', '按 D0 / D1 / N1 / P1 / X 五级证据距离隔离"同一相"、"结构近邻"与"仅可借鉴工艺"；组成相近不等于结构近邻。'),
    ('Q3', '路线与条件', ['合成方法与实验条件比较', '前人实验结论概览', '合成条件的统一比较', '条件总表', '分区比较', '高温溶液路线', '固相成相路线', '活化与提拉'], '部分回答', '近邻体系的 29 条条件记录已按统一字段表格化；目标相本身除"开放体系高温溶液 + SCXRD"外，投料 / 温程 / 坩埚 / 助熔 / 冷却全部记 NA。'),
    ('Q4', '取代与成相控制', ['组成坐标比单一最高温度更能解释成相差异', '单晶存在不等于建立了批量相纯窗口', '相图是连接复现与发现的核心实验', '批量相组成', '实际组成与污染', '高温稳定性', '常见实验问题与适用范围'], '部分回答', 'Ba↔Sr、Zn↔Mg/Co、MoO₃ 用量、冷却路径与气氛的影响来自近邻体系；Zn 在四方 Ba–Y 谱系中的固溶范围与占位没有直接证据（缺口 4）。'),
    ('Q5', '原始实测 vs 推断', ['条件总表', '分类依据', '不适用资料的边界'], '已回答', '每条条件记录标注来源定位（实验部分 / 摘要 / 题名）；36 条主张带原始条件溯源，54 条主张的证据全文在包内；缺失字段记 NA，不得类比补值。'),
]

SUBTOPIC_TO_BRANCH = {'身份与记号核验': ['A'], '目标相结构基线': ['B'], '结构近邻判据与谱系': ['B', 'C'], '固相与陶瓷路线': ['D'], '晶体生长及助熔路线': ['D'], '替代与成相控制': ['C', 'G'], '产物与证据质量': ['F'], '条件对照与可复现建议': ['E', 'H']}

WORKFLOWS = [
    ('wf01', 'wf01 固相煅烧', 'BaZn₂Si₂O₇ 的碳酸盐 / 氧化物固相煅烧：A 站配料 → 研磨装坩埚 → B 站马弗炉', ['rt_solid', 'cmp_bazn2si2o7', 'ag_baco3', 'ag_zno', 'ag_sio2']),
    ('wf02', 'wf02 回收 + XRD', '粉体回收、装小瓶、C 站 XRD 相鉴定，把表征结果反馈给下一轮前驱体 / 温度', ['ch_pxrd', 'cmp_bazn2si2o7']),
    ('wf03', 'wf03 湿法前驱体', '溶液法前驱体制备：计量、搅拌、pH 调节、离心 / 干燥', ['ag_baco3', 'ag_y2o3']),
    ('wf04', 'wf04 Pt 坩埚助熔剂生长', '目标相 Ba₅Y₁₂Zn[O(SiO₄)]₈ 的铂坩埚高温溶液（助熔）生长', ['rt_flux', 'cmp_target', 'ag_pt', 'ag_moo3']),
    ('wf05', 'wf05 试剂后勤与安全处置', '试剂柜取还、瓶口分配、废坩埚 / 废物分流；贯穿全部工作流', ['ag_baf2', 'ag_pbf']),
]


# ----------------------------------------------------------------------------- build
def main():
    nodes, edges = [], []
    seen = set()

    def add(nid, **kw):
        assert nid not in seen, nid
        seen.add(nid)
        n = {'id': nid, **kw}
        nodes.append(n)
        return n

    def link(s, t, kind, **kw):
        if s == t:
            return
        edges.append({'s': s, 't': t, 'k': kind, **kw})

    # ---- stage 0: the researcher's original tree (topic -> questions -> subtopics)
    topic_md = read(CASE / 'inputs/topic.md')
    title = re.search(r'^## 题目\s*\n\s*\n(.+)$', topic_md, re.M).group(1).strip()
    qs, subs = parse_scope(read(CASE / 'inputs/scope.md'))
    add('root', type='root', stage=0, label='调研主题', title=title,
        text='Ba₅Y₁₂Zn[O(SiO₄)]₈ 及其结构相近化合物的合成条件。用户给出的结构式原样视为待核对记号；交付一份可追溯的合成条件表。',
        src='正式案例 inputs/topic.md')
    for i, (q, qm) in enumerate(zip(qs, Q_MAP), 1):
        add(f'Q{i}', type='question', stage=0, label=f'目标 {i} · {qm[1]}', text=q, status=qm[3], answer=qm[4], src='正式案例 inputs/scope.md · 核心问题')
        link('root', f'Q{i}', 'tree')
    for i, (name, desc) in enumerate(subs, 1):
        add(f'S{i}', type='subtopic', stage=0, label=f'S{i} {name}', text=desc, src='正式案例 inputs/scope.md · MECE 子主题')
        link('root', f'S{i}', 'tree')
    # question -> subtopic (which subtopics serve which question; from the scope's own ordering)
    q2s = {'Q1': [1, 2], 'Q2': [3], 'Q3': [4, 5], 'Q4': [6], 'Q5': [7, 8]}
    for q, ss in q2s.items():
        for s in ss:
            link(q, f'S{s}', 'serves')

    # ---- stage 1: literature tree (taxonomy branches -> leaves -> papers)
    branches, leaves, gaps, unassigned = parse_taxonomy(read(EVID / 'notes/taxonomy.md'))
    bib = parse_bib(read(EVID / 'references.bib'))
    papers_jsonl = [json.loads(l) for l in read(EVID / 'papers.jsonl').splitlines() if l.strip()]
    claims = [json.loads(l) for l in read(EVID / 'claim_evidence.jsonl').splitlines() if l.strip()]
    summary = json.loads(read(EVID / 'claim_evidence_summary.json'))
    fulltext_keys = set(summary['keys_with_full_text_in_package'])
    strength = {}
    for c in claims:
        for e in c['evidence']:
            strength.setdefault(e['citation_key'], e['support_strength'])

    for b in branches:
        add(f'B_{b["id"]}', type='branch', stage=1, label=f'{b["id"]} {b["name"]}', text=b['name'], src='证据包 notes/taxonomy.md §2')
        link('root', f'B_{b["id"]}', 'tree')
        for lf in b['leaves']:
            add(f'L_{lf["id"]}', type='leaf', stage=1, label=f'{lf["id"]} {lf["name"]}', levels=lf['levels'], fields=lf['fields'], keys=lf['keys'], src='证据包 notes/taxonomy.md §2')
            link(f'B_{b["id"]}', f'L_{lf["id"]}', 'tree')
    for name, bs in SUBTOPIC_TO_BRANCH.items():
        s = next(f'S{i}' for i, (n, _) in enumerate(subs, 1) if n == name)
        for b in bs:
            link(s, f'B_{b}', 'maps')

    # paper nodes: every ref_gate key in references.bib (51)
    def paper_meta(key):
        f = bib[key]
        doi = f.get('doi', '').strip()
        rec = None
        for p in papers_jsonl:
            if doi and (p.get('doi') or '').lower() == doi.lower():
                rec = p
                break
        if rec is None:
            t = norm(f.get('title', ''))[:40]
            for p in papers_jsonl:
                if t and norm(p.get('title') or '')[:40] == t:
                    rec = p
                    break
        return f, doi, rec

    leaf_keys = {}
    for lf in leaves:
        for k in lf['keys']:
            leaf_keys.setdefault(k, []).append(lf['id'])
    dup = {'liu1993structuresx': 'liu1993structures'}
    paper_ids = {}
    for key in bib:
        f, doi, rec = paper_meta(key)
        year = f.get('year', '') or (str(rec.get('year')) if rec and rec.get('year') else '')
        venue = f.get('journal') or f.get('booktitle') or f.get('publisher') or f.get('school') or (rec.get('venue') if rec else '') or ''
        venue = venue.replace('{', '').replace('}', '')
        authors = f.get('author', '')
        pid = 'P_' + key
        paper_ids[key] = pid
        add(pid, type='paper', stage=1, key=key, label=f'{short_authors(authors) if authors else key} {year}', title=bib_title_html(f.get('title', '')),
            year=year, venue=venue, doi=doi, url=(f'https://doi.org/{doi}' if doi else (f.get('url') or (rec.get('url') if rec else '') or '')),
            authors=authors.replace('{', '').replace('}', ''), abstract=(rec.get('abstract') if rec else '') or '',
            strength=strength.get(key, 'weak'), fulltext=key in fulltext_keys, leaves=leaf_keys.get(key, []), level='X',
            src='证据包 references.bib / papers.jsonl（ref_gate PASS）')
        for lid in leaf_keys.get(key, []):
            link(pid, f'L_{lid}', 'support')
        if key in dup:
            link(pid, paper_ids.get(dup[key], 'P_' + dup[key]), 'duplicate')
    # level of a paper = best level among its leaves' header tags; otherwise the best class of the
    # compounds its title reports; otherwise the level named in the leaf title (e.g. "H3. N1/P1 …")
    def level_of_paper(n):
        lv = [x for lid in n['leaves'] for x in next(l for l in leaves if l['id'] == lid)['levels'] if x in LEVEL_RANK]
        if lv:
            return min(lv, key=lambda x: LEVEL_RANK[x])
        t = norm(bib[n['key']].get('title', ''))
        cl = [c[2] for c in CURATED_COMPOUNDS if any(a in t for a in c[3]) and c[2] != 'H']
        if cl:
            return min(cl, key=lambda x: LEVEL_RANK[x])
        named = [x for lid in n['leaves'] for x in re.findall(r'\b(D0|D1|N1|P1)\b', next(l for l in leaves if l['id'] == lid)['name'])]
        return min(named, key=lambda x: LEVEL_RANK[x]) if named else 'X'
    for n in nodes:
        if n['type'] == 'paper':
            n['level'] = level_of_paper(n)

    # ---- stage 2: entity trunk (compounds, routes, agents, characterisation, condition records, failure modes)
    for cid, formula, cls, aliases, note in CURATED_COMPOUNDS:
        add(cid, type='compound', stage=2 if cls != 'H' else 4, label=formula, level=cls, aliases=aliases, note=note, src='人工整理，链接由证据包文本匹配生成')
    for rid, label, leaf, aliases, note in CURATED_ROUTES:
        add(rid, type='route', stage=2, label=label, leaf=leaf, aliases=aliases, note=note, src='证据包 notes/taxonomy.md §D（路线支）')
        if leaf:
            link(f'L_{leaf}', rid, 'defines')
    for aid, label, kind, aliases in CURATED_AGENTS:
        add(aid, type='agent', stage=2, label=label, kind=kind, aliases=aliases, src='条件总表原料 / 坩埚 / 助熔字段与 RECIPE 预测')
    for chid, label, aliases in CURATED_CHAR:
        add(chid, type='char', stage=2, label=label, aliases=aliases, src='条件总表「产物与表征」字段；taxonomy §F')
    # failure modes = taxonomy G leaves, mirrored as entities
    for lf in leaves:
        if lf['id'].startswith('G'):
            add('F_' + lf['id'], type='failure', stage=2, label=f'{lf["id"]} {lf["name"]}', text=lf['fields'].get('含义', ''), src='证据包 notes/taxonomy.md §G')
            link(f'L_{lf["id"]}', 'F_' + lf['id'], 'defines')
            for k in lf['keys']:
                link(paper_ids[k], 'F_' + lf['id'], 'evidence')

    # taxonomy leaves -> entities (C substitution leaves -> compounds / agents; E variables -> agents; F -> char)
    leaf_entity = {
        'C2': ['cmp_basrzn'], 'C3': ['cmp_bazn2mx', 'cmp_baznsio4', 'ag_mgo', 'ag_co3o4'], 'C1': ['cmp_baxy26', 'cmp_ba5y13o85'],
        'E4': ['ag_moo3', 'ag_pbf', 'ag_ir', 'ag_al2o3', 'ag_agate'], 'E1': ['ag_baco3', 'ag_zno', 'ag_sio2'],
        'F1': ['ch_scxrd', 'ch_sync', 'ch_neutron'], 'F2': ['ch_pxrd'], 'F3': ['ch_comp'], 'F4': ['ch_ht'],
        'A1': ['cmp_target'], 'A2': ['cmp_ba5y13', 'cmp_baxy26', 'cmp_ba5y13o85'], 'A3': ['cmp_bay16'], 'B1': ['cmp_target', 'cmp_ba5y13o85'],
        'B3': ['cmp_bazn2si2o7', 'cmp_ba2znsi2o7', 'cmp_baznsio4', 'cmp_baznsi3o8', 'cmp_ba3zn4si4o15'], 'B4': ['cmp_y2sio5', 'cmp_y2si2o7'],
        'B5': ['cmp_basi4o9', 'cmp_ba2si4o10', 'cmp_ba3sio5', 'cmp_ba5si8o21'], 'D5': ['ag_ir'], 'D1': ['ag_moo3', 'ag_k2co3'],
    }
    for lid, ents in leaf_entity.items():
        for e in ents:
            link(f'L_{lid}', e, 'defines')

    # papers -> compounds (title match)
    comp_nodes = [n for n in nodes if n['type'] == 'compound']
    for n in nodes:
        if n['type'] != 'paper':
            continue
        t = norm(bib[n['key']].get('title', ''))
        for c in comp_nodes:
            if any(a in t for a in c['aliases']):
                link(n['id'], c['id'], 'reports', via='title')

    # condition records (29) -> paper / compound / route / agents / characterisation
    records = parse_condition_matrix(read(CASE / '最终输出/sections/03_condition_matrix.tex'))
    route_nodes = [n for n in nodes if n['type'] == 'route']
    agent_nodes = [n for n in nodes if n['type'] == 'agent']
    char_nodes = [n for n in nodes if n['type'] == 'char']
    zone = {'A': 'A 区 · 目标化合物直接文献', 'B': 'B 区 · 无 Zn 同类 Ba–Y 四方硅酸盐', 'C': 'C 区 · 结构相关 / 工艺参照'}
    for r in records:
        rid = 'R_' + r['id']
        add(rid, type='record', stage=2, label=r['id'], zone=zone[r['id'][0]], key=r.get('key'), product=r.get('product', ''), inputs=r.get('inputs', ''), method=r.get('method', ''),
            relation=r.get('relation', ''), temp_time=r.get('temp_time', ''), atmosphere=r.get('atmosphere', ''), crucible_flux=r.get('crucible_flux', ''),
            cooling=r.get('cooling', ''), product_char=r.get('product_char', ''), missing=r.get('missing', ''), source=r.get('source', ''),
            src='正式案例 最终输出/sections/03_condition_matrix.tex 表「合成条件总表」')
        if r.get('key') and r['key'] in paper_ids:
            link(paper_ids[r['key']], rid, 'records')
        pn = r.get('product_norm', '')
        for c in comp_nodes:
            if any(a in pn for a in c['aliases']):
                link(rid, c['id'], 'produces')
        m = norm(r.get('method', '')).replace('非机械化学', '')
        for rt in route_nodes:
            if any(norm(a) in m for a in rt['aliases']):
                link(rid, rt['id'], 'route')
        blob = norm(r.get('inputs', '') + ' ' + r.get('crucible_flux', ''))
        for a in agent_nodes:
            if any(norm(x) in blob for x in a['aliases']):
                link(rid, a['id'], 'uses')
        pc = norm(r.get('product_char', ''))
        for ch in char_nodes:
            if any(norm(x) in pc for x in ch['aliases']):
                link(rid, ch['id'], 'characterised')

    # ---- stage 3: conclusion tree (claim sections -> claims -> papers / entities), question <- section
    sec_order, sec_of = [], {}
    for c in claims:
        k = (c['section_file'], c['section'])
        if k not in sec_of:
            sec_of[k] = f'SEC{len(sec_order) + 1:02d}'
            sec_order.append(k)
    file_label = {'00_introduction': '引言', '01_phase_identity': '相身份', '02_evidence_distance': '证据距离', '03_condition_matrix': '条件矩阵',
                  '04_prior_experimental_findings': '前人实验规律', '04_neighbor_routes': '近邻路线', '05_validation_endpoints': '验证终点',
                  '06_failure_boundaries': '失败边界', '07_transferability_conclusion': '结论', '08_future_directions': '优先方向'}
    for (sf, sname), sid in sec_of.items():
        chap = sf.replace('sections/', '').replace('.tex', '')
        conclusion = chap.startswith('07') or chap.startswith('08')
        add(sid, type='section', stage=4 if conclusion else 3, label=sname, chapter=file_label.get(chap, chap), file=sf, src='正式案例 最终输出/' + sf)
    for qid, _, secs, _, _ in Q_MAP:
        for s in secs:
            for (sf, sname), sid in sec_of.items():
                if sname == s:
                    link(sid, qid, 'answers')
    ent_nodes = comp_nodes + route_nodes + agent_nodes + char_nodes
    for c in claims:
        sid = sec_of[(c['section_file'], c['section'])]
        cid = 'C_' + c['claim_id']
        txt = c['claim_text']
        if txt.startswith('}'):  # C013 is a table fragment in the source; label it as such
            txt = '（表格片段：目标相化学式对照表）'
        conclusion = c['section_file'].startswith('sections/07') or c['section_file'].startswith('sections/08')
        add(cid, type='claim', stage=4 if conclusion else 3, label=c['claim_id'], text=txt, section=sid,
            evidence=[{'key': e['citation_key'], 'strength': e['support_strength'], 'fulltext': e['full_text_in_package'], 'note': e['support_note'],
                       'trace': [{k: v for k, v in t.items() if k in ('condition_cell', 'location', 'supportable_fields')} for t in (e['condition_source_trace'] or [])]} for e in c['evidence']],
            src='证据包 claim_evidence.jsonl')
        link(sid, cid, 'tree')
        for e in c['evidence']:
            if e['citation_key'] in paper_ids:
                link(cid, paper_ids[e['citation_key']], 'cites', strength=e['support_strength'])
            for t in (e['condition_source_trace'] or []):
                cell = t.get('condition_cell')
                if cell and ('R_' + cell) in seen:
                    link(cid, 'R_' + cell, 'traces')
        tn = norm(txt)
        for en in ent_nodes:
            if any(norm(a) in tn for a in en['aliases'] if len(norm(a)) >= 4 or not norm(a).isascii()):
                link(cid, en['id'], 'mentions')

    # ---- stage 4: grown trees (gaps, RECIPE, directions, workflows, supplementary cases)
    add('T_gaps', type='tree', stage=4, label='证据缺口（8）', text='taxonomy §5：现有证据边界内尚未闭合的问题；每条缺口都是下一轮检索或实验的入口。', src='证据包 notes/taxonomy.md §5')
    link('root', 'T_gaps', 'grows')
    gap_links = {'GAP01': ['cmp_target', 'L_A1'], 'GAP02': ['R_A1'], 'GAP03': ['B_B'], 'GAP04': ['L_C3', 'cmp_series'], 'GAP05': ['rt_hydro'], 'GAP06': ['ch_pxrd', 'L_F2'], 'GAP07': ['B_E'], 'GAP08': ['ag_pbf', 'F_G2']}
    for g in gaps:
        add(g['id'], type='gap', stage=4, label=g['name'], text=g['text'], src='证据包 notes/taxonomy.md §5')
        link('T_gaps', g['id'], 'tree')
        for t in gap_links.get(g['id'], []):
            if t in seen:
                link(g['id'], t, 'about')

    recipe = parse_recipe(read(CASE / 'ideas/precursor_predictions.md'))
    add('T_recipe', type='tree', stage=4, label='RECIPE 前驱体预测', text='两步无机逆合成 MCP（goai-retro）：Stage 1 单前驱体检索 → 化学硬过滤 → Stage 2 组合重排；每个目标取 Top-5，枚举 4928 个 2–5 元组合。所有路线 chemical_route_verified=false，是模型排序，不是实验验证。', src='正式案例 ideas/precursor_predictions.md；tool_calls.jsonl')
    link('root', 'T_recipe', 'grows')
    target_map = {'Ba5Y12ZnSi8O40': 'cmp_target', 'Ba5Y12MgSi8O40': 'cmp_mg_target', 'Ba5Y12CoSi8O40': 'cmp_co_target'}
    for t in recipe:
        tid = target_map[t['formula']]
        link('T_recipe', tid, 'predicts_for')
        for r in t['rows']:
            rid = f'RC_{t["formula"]}_{r["rank"]}'
            add(rid, type='recipe', stage=4, label=md_formula(r['combo']), rank=r['rank'], p=r['p'], target=tid, top=r['rank'] == 1, note=t['note'] if r['rank'] == 1 else '', src='正式案例 ideas/precursor_predictions.md')
            link(tid, rid, 'candidate')
            combo = norm(r['combo'])
            for a in agent_nodes:
                if any(re.search(r'(^|\+)' + re.escape(norm(x)) + r'($|\+)', combo) for x in a['aliases']):
                    link(rid, a['id'], 'uses')

    directions = parse_directions(read(CASE / 'ideas/experiment_directions.md'))
    add('T_dir', type='tree', stage=4, label='优先实验方向（4）', text='由既有证据和模型候选共同提出，均为实验假设；按"局部相图 → 占位 / 氧计量 → 晶体生长 → 类比替代"的顺序推进。', src='正式案例 ideas/experiment_directions.md；最终输出 §8')
    link('root', 'T_dir', 'grows')
    dir_links = {'D1': ['cmp_target', 'rt_solid', 'ag_baco3', 'ag_y2o3', 'ag_zno', 'ag_sio2', 'ch_pxrd', 'ch_comp'], 'D2': ['cmp_series', 'cmp_ba5y13o85', 'ch_neutron', 'ch_scxrd'],
                 'D3': ['rt_flux', 'rt_solid', 'ag_k2co3', 'ag_moo3', 'ag_pt', 'ch_scxrd'], 'D4': ['cmp_mg_target', 'cmp_co_target', 'ag_mgo', 'ag_co3o4', 'T_recipe']}
    for d in directions:
        add('DIR_' + d['id'], type='direction', stage=4, label=f'方向 {d["id"][1]} · {d["name"]}', text=d['text'], src='正式案例 ideas/experiment_directions.md')
        link('T_dir', 'DIR_' + d['id'], 'tree')
        for t in dir_links.get(d['id'], []):
            link('DIR_' + d['id'], t, 'about')

    add('T_wf', type='tree', stage=4, label='OpenLab 自动化工作流（仿真）', text='A-Lab 数字孪生（Isaac Sim）里的五条实验工作流：22 个任务、158 个机器人原语、28 项 SafeLab USD 资产、9 条文献依据。全部为仿真，不是实体实验。', src='站点 showcase.html 页首统计；final_round/05_alab_twin.md')
    link('root', 'T_wf', 'grows')
    for wid, label, text, targets in WORKFLOWS:
        add('WF_' + wid, type='workflow', stage=4, label=label, text=text, src='站点 showcase.html · 五条自动化实验工作流')
        link('T_wf', 'WF_' + wid, 'tree')
        for t in targets:
            link('WF_' + wid, t, 'about')

    add('T_cases', type='tree', stage=4, label='同根长出的其他调研树', text='同一流水线、同一九道闸门，对另外三个主题的运行结果；每棵树都有自己的 ledger / 引用审计。', src='submission/03_运行与评测包/补充案例_20260903；LLZO诊断轮')
    link('root', 'T_cases', 'grows')
    case_dirs = [(SUPP / '01_llzo/run', 'CASE_llzo', 'LLZO 石榴石固体电解质', ['root']),
                 (SUPP / '02_bazn2si2o7/run', 'CASE_bzso', 'BaZn₂Si₂O₇ 合成与相控制', ['cmp_bazn2si2o7', 'rt_solid']),
                 (SUPP / '03_bayznsi_o_phase_diagram/run', 'CASE_phase', 'Ba–Y–Zn–Si–O 相图导向合成', ['cmp_target', 'F_G1', 'DIR_D1']),
                 (LLZO_DIAG, 'CASE_llzo_diag', 'LLZO 诊断轮', ['CASE_llzo'])]
    for d, cid, label, targets in case_dirs:
        led = json.loads(read(d / 'ledger.json'))
        audit = read(d / 'CITATION_AUDIT.md')
        m = re.search(r'条目[:：]\s*(\d+)', audit) or re.search(r'Bib 整合：(\d+) 条目', audit)
        gates = led.get('gates') or {}
        gsum = {}
        for k, v in gates.items():
            st = v.get('status') if isinstance(v, dict) else v
            gsum[st] = gsum.get(st, 0) + 1
        add(cid, type='case', stage=4, label=label, topic=led.get('topic', ''), entries=int(m.group(1)) if m else None, gates=gsum, round=led.get('round'),
            src=str(d.relative_to(REPO)) + '/ledger.json, CITATION_AUDIT.md')
        link('T_cases', cid, 'tree')
        for t in targets:
            if t in seen:
                link(cid, t, 'about')

    # ---- meta
    n_papers = sum(1 for n in nodes if n['type'] == 'paper')
    meta = {
        'title': 'SAGE-Mat 知识森林',
        'subtitle': '一棵调研树如何长出文献树、实体主干、结论树与新的实验树',
        'built_from': ['submission/02_研究数据与证据包', 'submission/03_运行与评测包/正式案例_BYZSO冷启动', 'submission/03_运行与评测包/补充案例_20260903', 'final_round 站点 showcase.html'],
        'stats': {'papers': n_papers, 'citation_calls': summary['citation_calls'], 'claims': summary['claims'], 'claims_fulltext': summary['claims_with_any_full_text_evidence'],
                  'claims_trace': summary['claims_with_condition_source_trace'], 'refcheck_pass_rate': summary['refcheck_pass_rate'], 'leaves': len(leaves), 'branches': len(branches),
                  'records': len(records), 'compounds': len(CURATED_COMPOUNDS), 'gaps': len(gaps), 'nodes': len(nodes), 'edges': len(edges)},
        'stages': [
            {'i': 0, 'name': '个人知识树', 'desc': '调研主题、5 个预期目标与 8 个 MECE 子主题：调研开始前研究者自己的问题树。'},
            {'i': 1, 'name': '文献树', 'desc': '流水线检索、核验并分类：8 个分支、35 个叶节点、51 篇通过引用闸门的文献，按 D0/D1/N1/P1/X 证据距离着色。'},
            {'i': 2, 'name': '实体主干', 'desc': '把文献抽象成可复用的点：化合物 / 相、合成路线、前驱体与坩埚助熔、表征终点、失败模式，以及 29 条逐字段的合成条件记录。'},
            {'i': 3, 'name': '结论树', 'desc': '综述正文的 100 条主张，每条回连它引用的文献与实体；再回答最初的 5 个目标，标出已回答 / 部分回答。'},
            {'i': 4, 'name': '长出的新树', 'desc': '结论与缺口之上长出的四棵新树：RECIPE 前驱体预测、四个优先实验方向、OpenLab 自动化工作流（仿真）、同根的其他调研树。'},
        ],
        'levels': LEVEL_NAME,
        'unassigned_keys': unassigned,
    }
    graph = {'meta': meta, 'nodes': nodes, 'edges': edges}
    (HERE / 'graph.json').write_text(json.dumps(graph, ensure_ascii=False, indent=0), encoding='utf-8')

    tpl = read(HERE / 'template.html')
    out = tpl.replace('/*__GRAPH_JSON__*/null', json.dumps(graph, ensure_ascii=False, separators=(',', ':')))
    (HERE / 'knowledge_graph.html').write_text(out, encoding='utf-8')
    kinds = {}
    for e in edges:
        kinds[e['k']] = kinds.get(e['k'], 0) + 1
    types = {}
    for n in nodes:
        types[n['type']] = types.get(n['type'], 0) + 1
    print('nodes', len(nodes), types)
    print('edges', len(edges), kinds)
    print('stats', meta['stats'])


if __name__ == '__main__':
    main()
