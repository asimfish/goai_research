"""Rebuild the two-block condition matrix (03_condition_matrix.tex) as ONE landscape longtable with 12 columns,
one row per record (A1, B1..B6, C1..C22), zone headers as full-width rows, "—" for not-reported cells, bib keys dropped
(the citation stays), and shaded bold headers.  Also shades headers of the other tables and normalises NA.

usage: python3 zh_table_merge.py <sections_dir> <out_dir>   (writes every .tex; only the table structure/wording of
cells is changed — prose is left for the editorial pass)
"""
import re, sys, shutil
from pathlib import Path

src, out = (Path(sys.argv[1]), Path(sys.argv[2])) if sys.argv[1] != "--splice" else (None, None)
if out: out.mkdir(parents=True, exist_ok=True)
NA = re.compile(r'\\texttt\{NA\}')
KEY = re.compile(r'\\texttt\{[a-z0-9_]+\}[；;，,]?\s*')


def clean_cell(c):
    c = c.strip()
    c = KEY.sub('', c)                                    # drop bib keys rendered as \texttt
    parts = [p.strip() for p in re.split('；', c) if p.strip()]
    if parts and all(NA.search(p) and not re.search(r'\d|\\cite', NA.sub('', p)) for p in parts): return '—'
    c = NA.sub('—', c)
    c = re.sub(r'(均)—', r'\1未报道', c)                  # "温度、时间均—" → "温度、时间均未报道"
    # 化学式串 (A/B/C, A:B:C) 在窄列里不可断行 → 在数学模式之外的 / 和 : 之后允许断行
    parts = re.split(r'(\$[^$]*\$)', c)
    c = ''.join(p if i % 2 else re.sub(r'([/:])(?=\S)', r'\1\\allowbreak{}', p) for i, p in enumerate(parts))
    return c


def unstack(body):
    """\\shortstack[l]{A\\\\{}B\\\\C} -> ABC (balanced braces); P columns wrap by themselves"""
    out = ''; i = 0; tag = '\\shortstack'
    while True:
        j = body.find(tag, i)
        if j < 0: out += body[i:]; return out
        out += body[i:j]; k = body.find('{', j); depth = 0; m = k
        while True:
            if body[m] == '{': depth += 1
            elif body[m] == '}':
                depth -= 1
                if depth == 0: break
            m += 1
        inner = body[k + 1:m].replace('\\\\{}', '').replace('\\\\', '')
        out += inner; i = m + 1


def split_rows(body):
    rows = []
    body = unstack(body)
    body = re.sub(r'\\(top|mid|bottom)rule', '', body)
    for line in body.split('\\\\'):
        line = line.strip()
        cells = [x for x in line.split('&')]
        if len(cells) < 4: continue
        rows.append([clean_cell(x) for x in cells])
    return rows


def merge_condition_matrix(tex):
    blocks = re.findall(r'\\begin\{table\*\}.*?\\end\{table\*\}', tex, re.S)
    if not blocks: return tex
    zones = []            # (zone title, rows dict key -> 12 cells)
    for b in blocks:
        cap = re.search(r'\\caption\{(.*?)\}\s*(?:\\label|\n)', b, re.S)
        cap = cap.group(1) if cap else ''
        zone = re.search(r'([ABC]区[：:][^）)。]*)', cap)
        zone = zone.group(1) if zone else cap[:40]
        tabs = [t.split('\\toprule', 1)[1] for t in re.findall(r'\\begin\{tabular\}(.*?)\\end\{tabular\}', b, re.S)]
        if len(tabs) != 2: continue
        top, bot = split_rows(tabs[0]), split_rows(tabs[1])
        top = [r for r in top if not r[0].startswith('编号')]; bot = [r for r in bot if not r[0].startswith('编号')]
        botd = {r[0]: r[1:] for r in bot}
        merged = []
        for r in top:
            k = r[0]; merged.append([k] + r[1:] + botd.get(k, ['—'] * 6))
        zones.append((zone, merged))
    # 竖排两张长表：各 5 列（合并短列），列宽按单元格文字量自动分配，行间 \addlinespace
    def vis_len(cell):
        t = re.sub(r'\\cite\{[^}]*\}', '[00]', cell); t = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?', '', t); t = re.sub(r'[{}$_^~]', '', t)
        return sum(2 if ord(ch) > 0x2e80 else 1 for ch in t.strip())
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
    def join(a, b, label):
        a, b = a.strip(), b.strip()
        if b in ('', '—'): return a
        if a in ('', '—'): return label + b
        return a + '；' + label + b
    pick_a = lambda r: [r[0], r[1], r[2], r[3], join(r[4], r[5], '关系：')]
    pick_b = lambda r: [r[0], join(r[6], r[9], '冷却/生长：'), join(r[7], r[8], '坩埚/助熔剂：'), r[10], r[11]]
    ha = ['\\thead{编号}', '\\thead{来源与出处}', '\\thead{目标/产物式}', '\\thead{原料、配比与前处理}', '\\thead{合成方法；与目标相的关系}']
    hb = ['\\thead{编号}', '\\thead{温度--时间；冷却/生长}', '\\thead{气氛/体系；坩埚/助熔剂}', '\\thead{产物与表征}', '\\thead{未记载项}']
    all_rows = [r for _, rows in zones for r in rows]
    fa = auto_widths([pick_a(r) for r in all_rows], 5); fb = auto_widths([pick_b(r) for r in all_rows], 5)
    def spec(fr): return ''.join('P{\\dimexpr %.4f\\textwidth-2\\tabcolsep\\relax}' % f for f in fr)
    def table(fr, header, cap, contcap, label, pick):
        n = len(fr); h = ' & '.join(header)
        lt = ['{\\fontsize{8}{9.8}\\selectfont\\setlength{\\tabcolsep}{3pt}\\renewcommand{\\arraystretch}{1.05}',
              '\\begin{longtable}{' + spec(fr) + '}',
              '\\caption{' + cap + '}\\label{' + label + '}\\\\', '\\toprule', h + '\\\\', '\\midrule', '\\endfirsthead',
              '\\caption[]{' + contcap + '}\\\\', '\\toprule', h + '\\\\', '\\midrule', '\\endhead',
              '\\midrule', '\\multicolumn{%d}{r}{续下页}\\\\' % n, '\\endfoot', '\\bottomrule', '\\endlastfoot']
        for i, (zone, rows) in enumerate(zones):
            if i: lt.append('\\midrule')
            lt.append('\\multicolumn{%d}{l}{\\textbf{%s}}\\\\*[2pt]' % (n, zone))
            for j, r in enumerate(rows):
                lt.append(' & '.join(pick(r)) + ('\\\\' if j == len(rows) - 1 else '\\\\ \\addlinespace[3pt]'))
        lt += ['\\end{longtable}}']
        return lt
    lt = ['% >>> condition-matrix (generated by tools/zh_table_merge.py)', '\\Needspace{8\\baselineskip}']
    lt += table(fa, ha,
                '\\textbf{目标化合物及相关体系的合成条件总表（一）：文献出处、化学输入、合成方法与目标相的关系。}每条记录一行；A 区为目标化合物的直接文献，B 区为无 Zn 的同类 Ba--Y 四方硅酸盐（不是目标相的复现），C 区为结构相关与工艺参照研究。“—”表示本次核查未取得明确记载，不表示原实验没有该步骤；相关体系的数值不是目标相的已验证配方。',
                '合成条件总表（一）续表', 'tab:synthesis-conditions', pick_a)
    lt += ['\\Needspace{8\\baselineskip}']
    lt += table(fb, hb,
                '\\textbf{合成条件总表（二）：热历史、气氛与体系、坩埚与助熔剂、产物表征和未记载项。}编号与表~\\ref{tab:synthesis-conditions} 对应；单元格内以“；”分隔并标注的子项（冷却/生长、坩埚/助熔剂）承接原表的对应栏。',
                '合成条件总表（二）续表', 'tab:synthesis-conditions-b', pick_b)
    lt += ['% <<< condition-matrix']
    first = tex.index(blocks[0]); last = tex.index(blocks[-1]) + len(blocks[-1])
    tex = tex[:first] + '\n'.join(lt) + tex[last:]
    tex = tex.replace('采用两块联表。上块记录文献出处、化学输入、合成方法和与目标相的关系；下块以相同编号承接热史、体系、容器与助熔、冷却或生长、产物表征及资料缺失。',
                      '按记录逐行列出文献出处、化学输入、合成方法和与目标相的关系；表~\\ref{tab:synthesis-conditions-b}以相同编号承接热历史、体系、坩埚与助熔剂、冷却或生长程序、产物表征和未记载项。')
    return tex


def shade_headers(tex):
    # add a light header shade after \toprule inside tabular/longtable (first row only) and make header cells sans bold
    def fix(m):
        head = m.group(2)
        if head.lstrip().startswith('\\rowcolor'): return m.group(0)
        cells = [c.strip() for c in head.split('&')]
        cells = [('\\thead{' + c + '}') if c and not c.startswith('\\thead') and not c.startswith('\\multicolumn') else c for c in cells]
        return m.group(1) + ' & '.join(cells) + '\\\\'
    return re.sub(r'(\\toprule\s*\n\s*)([^\n\\]*(?:\\[a-zA-Z]+\{[^\n]*?\})?[^\n]*?)\\\\', fix, tex)


if sys.argv[1] == '--splice':                       # zh_table_merge.py --splice <orig 03.tex> <edited v3 03.tex>
    orig, v3 = Path(sys.argv[2]), Path(sys.argv[3])
    block = merge_condition_matrix(orig.read_text(encoding='utf-8'))
    M1, M2 = '% >>> condition-matrix', '% <<< condition-matrix'
    block = block[block.index(M1):block.index(M2) + len(M2)]
    cur = v3.read_text(encoding='utf-8')
    if M1 in cur: a = cur.index(M1); b = cur.index(M2) + len(M2)
    else:
        a = cur.index('\\newgeometry') if '\\newgeometry' in cur else cur.index('\\begin{landscape}')
        b = cur.index('\\restoregeometry') + len('\\restoregeometry') if '\\restoregeometry' in cur else cur.index('\\end{landscape}') + len('\\end{landscape}')
    v3.write_text(cur[:a] + block + cur[b:], encoding='utf-8'); print('spliced', v3, len(block)); sys.exit(0)

for f in sorted(src.glob('*.tex')):
    tex = f.read_text(encoding='utf-8')
    if 'tab:synthesis-conditions' in tex and 'ContinuedFloat' in tex: tex = merge_condition_matrix(tex)
    tex = tex.replace('记为\\texttt{NA}', '记为未报道').replace('\\texttt{NA}表示', '“—”表示')
    tex = NA.sub('—', tex)
    tex = shade_headers(tex)
    tex = re.sub(r'\\renewcommand\{\\arraystretch\}\{[0-9.]+\}\s*', '', tex)          # table-local stretch → global
    tex = re.sub(r'\\setlength\{\\tabcolsep\}\{[0-9.]+pt\}\s*', '', tex)             # → global 3pt
    (out / f.name).write_text(tex, encoding='utf-8'); print('wrote', f.name, len(tex))
