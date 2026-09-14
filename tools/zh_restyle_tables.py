"""Round 4: text-heavy tables and captions.
 - captions: hanging format, bold first sentence (title) + regular description
 - tables: justified p-columns, widths auto-balanced from cell text length, \\addlinespace between rows,
   fewer/wider columns (Table 1: 7 -> 5; condition matrix (一): 6 -> 5, (二): 7 -> 5)
"""
import re, glob, shutil, math

STY = '/root/lyf/goai/goai_research/templates/goai_zh_typo.sty'
GEN = '/root/lyf/goai/goai_research/tools/zh_table_merge.py'


def vis_len(cell):
    t = re.sub(r'\\cite\{[^}]*\}', '[00]', cell)
    t = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?', '', t)
    t = re.sub(r'[{}$_^~]', '', t)
    return sum(2 if ord(ch) > 0x2e80 else 1 for ch in t.strip())   # CJK ≈ 2 Latin units


def auto_widths(rows, n, floor=0.085, power=0.75):
    def tok(cell):   # longest unbreakable Latin/math token, in Latin char units
        t = re.sub(r'\\cite\{[^}]*\}', '[00]', cell); t = re.sub(r'\\(allowbreak|slash|newline)\s*\{?\}?', ' ', t)
        t = re.sub(r'\\[a-zA-Z]+\*?', '', t); t = re.sub(r'[{}$^~]', '', t); t = re.sub(r'_(\w)', r'\1', t)
        return max([len(x) for x in re.split(r'[\s\u2e80-\u9fff、，；：（）]+', t) if x] + [0])
    cols = [[vis_len(r[i]) for r in rows if i < len(r)] for i in range(n)]
    toks = [max([tok(r[i]) for r in rows if i < len(r)] + [0]) for i in range(n)]
    means = [max(1.0, (sum(c) / len(c)) if c else 1.0) for c in cols]
    w = [m ** power for m in means]; w = [x / sum(w) for x in w]
    fl = [max(floor, 0.0125 * t + 0.02) for t in toks]          # 1 Latin char ≈ 0.0125 textwidth at 8–9 pt, plus 2 colsep
    w = [max(f, x) for f, x in zip(fl, w)]; s = sum(w); return [round(x / s, 4) for x in w]


def spec(fr):
    return ''.join('P{\\dimexpr %.4f\\textwidth-2\\tabcolsep\\relax}' % f for f in fr)


# ---------------- sty
s = open(STY, encoding='utf-8').read()
rep = [
       ("labelsep=colon,skip=6pt,justification=justified,singlelinecheck=true]{caption}",
        "labelsep=colon,skip=6pt,justification=justified,singlelinecheck=true,format=hang]{caption}"),
       ("\\captionsetup[longtable]{font={small,stretch=1.15},labelfont={bf},skip=6pt,justification=justified,singlelinecheck=true}",
        "\\captionsetup[longtable]{font={small,stretch=1.15},labelfont={bf},skip=6pt,justification=justified,singlelinecheck=true,format=hang}")]
for a, b in rep:
    if a in s: s = s.replace(a, b)
open(STY, 'w', encoding='utf-8').write(s)
for d in ('byzso/drafts/', 'bzso/report/'): shutil.copyfile(STY, d + 'goai_zh_typo.sty')
print('sty: justified P, hanging captions')

# ---------------- generator: already patched in place (tools/zh_table_merge.py); no longer rewritten here

# ---------------- sections: Table 1 (7 -> 5 columns), captions bold title, addlinespace in small tables, auto widths
def restyle_tabular(block, merge=None):
    """block = full tabular environment text; returns restyled block"""
    m = re.match(r'(\s*\\begin\{tabular\}\{)([^\n]*)(\}\n)(.*)(\\end\{tabular\})', block, re.S)
    if not m: return block
    body = m.group(4)
    lines = [l for l in body.split('\n') if l.strip() != '\\addlinespace[3pt]']; out = []; rows = []; header = None
    for ln in lines:
        st = ln.strip()
        if '&' in st and st.endswith('\\\\'):
            cells = [c.strip() for c in st[:-2].split('&')]
            if merge: cells = merge(cells)
            if header is None and '\\thead' in st: header = cells; out.append('    ' + ' & '.join(cells) + '\\\\'); continue
            rows.append(cells); out.append('    ' + ' & '.join(cells) + '\\\\')
        else:
            out.append(ln)
    n = len(header) if header else (len(rows[0]) if rows else 0)
    fr = auto_widths(rows, n) if rows else None
    # add \addlinespace between data rows (not after the last one)
    res = []; data_idx = [i for i, l in enumerate(out) if l.strip().endswith('\\\\') and '&' in l and '\\thead' not in l]
    for i, l in enumerate(out):
        res.append(l)
        if i in data_idx[:-1]: res.append('    \\addlinespace[3pt]')
    newspec = spec(fr) if fr else m.group(2)
    return m.group(1) + newspec + m.group(3) + '\n'.join(res) + m.group(5)


def merge_identity(cells):
    if len(cells) != 7: return cells
    if '\\thead' in cells[0]:
        return ['\\thead{化学式（原文 → 本文写法）}', '\\thead{文献}', '\\thead{主要结构证据}', '\\thead{与目标相的关系}', '\\thead{结论与待研究问题}']
    a, b = cells[0], cells[1]
    formula = a if (b == a or b in ('同上',)) else a + '（本文：' + b + '）'
    return [formula, cells[2], cells[3], cells[4], '结论：' + cells[5] + '；待研究：' + cells[6]]


def bold_title(cap):
    # \caption{X。rest} -> \caption{\textbf{X。}rest}  (only when more than one sentence; skip if already bold)
    def rep(m):
        opt, txt = m.group(1) or '', m.group(2)
        if '\\textbf' in txt or '。' not in txt[:-1]: return m.group(0)
        i = txt.index('。') + 1
        return '\\caption' + opt + '{\\textbf{' + txt[:i] + '}' + txt[i:] + '}'
    return re.sub(r'\\caption(\[[^\]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}', rep, cap)


for d in ['byzso/drafts/sections_v3/', 'byzso/drafts/sections_v3_base/', 'bzso/report/sections_v3/', 'bzso/report/sections_v3_base/']:
    for f in sorted(glob.glob(d + '*.tex')):
        s = open(f, encoding='utf-8').read(); o = s
        merge = merge_identity if f.endswith('01_phase_identity.tex') else None
        s = re.sub(r'\s*\\begin\{tabular\}\{[^\n]*\}\n.*?\\end\{tabular\}', lambda m: restyle_tabular(m.group(0), merge), s, flags=re.S)
        s = bold_title(s)
        if s != o: open(f, 'w', encoding='utf-8').write(s)
print('sections restyled')
for p in ('byzso/drafts/main_typo3.tex', 'bzso/report/main_typo3.tex'):
    pass
