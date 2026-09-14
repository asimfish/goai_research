r"""Normalise every tabular column spec so the table spans exactly the full text width (top-venue convention:
all tables the same width, centred, booktabs, no shading).  P{<len>} widths are rescaled proportionally to
fractions r_i of \textwidth (or \linewidth inside landscape/longtable) minus 2\tabcolsep per column.
usage: python3 zh_table_width.py <dir> [<dir>...]   (in place; also removes \rowcolor{gray!..} header shading)"""
import re, sys
from pathlib import Path
LEN = re.compile(r'P\{([0-9.]+)\s*(cm|mm|pt|\\linewidth|\\textwidth|\\columnwidth)\}')
def to_cm(v, u):
    v = float(v)
    return {'cm': v, 'mm': v / 10, 'pt': v / 28.4528}.get(u, v * 17.0)   # fractions of a ~17 cm text width: only ratios matter
def fix_spec(spec, base):
    cols = LEN.findall(spec)
    if len(cols) < 2: return spec
    ws = [to_cm(v, u) for v, u in cols]; tot = sum(ws)
    fr = [w / tot for w in ws]
    fr[-1] = round(1 - sum(round(f, 4) for f in fr[:-1]), 4)
    out = []; i = 0
    def rep(m):
        nonlocal i
        f = round(fr[i], 4) if i < len(fr) - 1 else fr[-1]; i += 1
        return 'P{\\dimexpr %.4f%s-2\\tabcolsep\\relax}' % (f, base)
    return LEN.sub(rep, spec)
for d in sys.argv[1:]:
    for f in sorted(Path(d).glob('*.tex')):
        s = f.read_text(encoding='utf-8'); o = s
        def fix_env(m):
            env, spec = m.group(1), m.group(2)
            base = '\\linewidth' if env == 'longtable' else '\\textwidth'
            return '\\begin{%s}{%s}' % (env, fix_spec(spec, base))
        s = re.sub(r'\\begin\{(tabular|longtable)\}\{([^\n]*?)\}(?=\s*\n)', fix_env, s)
        s = re.sub(r'\\rowcolor\{gray![0-9]+\}\s*', '', s)
        s = re.sub(r'\n\s*\\scriptsize\s*\n', '\n', s)     # table font size comes from the sty (footnotesize)
        if s != o: f.write_text(s, encoding='utf-8'); print('normalised', f.name)
