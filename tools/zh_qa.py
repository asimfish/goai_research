r"""QA gate for the editorial pass: compares protected content between original and edited section dirs.
usage: python3 zh_qa.py <orig_dir> <edited_dir>  -> exit 1 on any mismatch (cite keys, math, ref/label, numbers, table cell counts)"""
import re, sys
from collections import Counter
from pathlib import Path
A, B = Path(sys.argv[1]), Path(sys.argv[2]); bad = 0
def feats(s):
    s = re.sub(r'%[^\n]*', '', s)
    return {
        'cite': Counter(k.strip() for m in re.findall(r'\\cite[pt]?\{([^}]*)\}', s) for k in m.split(',')),
        'math': Counter(re.findall(r'\$[^$]+\$', s)),
        'ref': Counter(re.sub(r'_(?:zh|en)\.pdf', '.pdf', x) for x in re.findall(r'\\(?:ref|label|eqref|includegraphics)(?:\[[^\]]*\])?\{[^}]*\}', s)),   # 图件的语言后缀不算差异（中英两条线各用各的图）
        'num': Counter(re.findall(r'\d+(?:\.\d+)?', s)),
        'amp': Counter({'&': s.count('&'), '\\\\': s.count('\\\\'), 'tabular': s.count('\\begin{tabular}') + s.count('\\begin{longtable}')}),
    }
for f in sorted(A.glob('*.tex')):
    g = B / f.name
    if not g.exists(): print('MISSING', g); bad += 1; continue
    fa, fb = feats(f.read_text(encoding='utf-8')), feats(g.read_text(encoding='utf-8'))
    for k in fa:
        if fa[k] != fb[k]:
            d1 = fa[k] - fb[k]; d2 = fb[k] - fa[k]
            print(f'{f.name} [{k}] lost={dict(d1)} added={dict(d2)}'); bad += 1
print('QA', 'FAIL' if bad else 'PASS', bad)
sys.exit(1 if bad else 0)
