r"""Apply glossary zh_normalize (longest match first) to .tex prose outside protected spans
(math $...$, \cite{}, \ref{}, \label{}, \includegraphics{}, \input{}, \texttt{}, \url{}, comments).
usage: python3 zh_terms_apply.py <glossary.json> <dir> [<dir>...]   (in place; prints per-file replacement counts)"""
import json, re, sys
from pathlib import Path
g = json.load(open(sys.argv[1], encoding='utf-8'))['zh_normalize']
terms = sorted(g.items(), key=lambda kv: -len(kv[0]))
PROT = re.compile(r'(\$[^$]*\$|\\(?:cite|ref|label|includegraphics|input|texttt|url|nolinkurl|bibliography|hypersetup)\*?(?:\[[^\]]*\])?\{[^}]*\}|%[^\n]*)')
def fix(seg, log):
    for a, b in terms:
        n = seg.count(a)
        if n: seg = seg.replace(a, b); log[a] = log.get(a, 0) + n
    return seg
tot = {}
for d in sys.argv[2:]:
    for f in sorted(Path(d).glob('*.tex')):
        s = f.read_text(encoding='utf-8'); log = {}
        parts = PROT.split(s)
        s2 = ''.join(p if i % 2 else fix(p, log) for i, p in enumerate(parts))
        # 特殊后处理：连字修正
        s2 = s2.replace('未报道未报道', '未报道').replace('块体块体', '块体').replace('相形成相形成', '相形成')
        f.write_text(s2, encoding='utf-8')
        if log: print(f.name, sum(log.values()), dict(sorted(log.items(), key=lambda kv: -kv[1])))
        for k, v in log.items(): tot[k] = tot.get(k, 0) + v
print('TOTAL', sum(tot.values()), tot)
