r"""Polish a references.bib for plainnat (top-venue look):
 - brace title tokens that must keep their case (formulas, element symbols, acronyms, Greek letters, digits)
 - normalise ' - ' / ' – ' in titles/journals to '--'
 - apply a JSON patch {key: {field: value, '@type': 'phdthesis', '__drop__': [fields]}}
 - optionally enrich volume/number/pages from Crossref by DOI (--crossref)
usage: python3 bib_polish.py <in.bib> <out.bib> [--patch patch.json] [--crossref]"""
import re, sys, json, urllib.request, urllib.parse, time
src, dst = sys.argv[1], sys.argv[2]
patch = {}; crossref = '--crossref' in sys.argv
if '--patch' in sys.argv: patch = json.load(open(sys.argv[sys.argv.index('--patch') + 1], encoding='utf-8'))
txt = open(src, encoding='utf-8').read()
ELEM = set('H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi'.split())
KEEP = {'II', 'III', 'IV', 'X-ray', 'X-Ray', 'XRD', 'NMR', 'MAS-NMR', 'HT-XRD', 'DFT', 'CALPHAD', 'SOFC', 'SEM', 'TEM', 'EDS', 'PXRD', 'SCXRD', 'LED', 'NTE', 'ZTE', 'CTE', 'DSC', 'TG', 'IR', 'UV', 'RF', 'ChemInform', 'CIF', 'ICSD', 'DOI'}
GREEK = {'α': r'$\alpha$', 'β': r'$\beta$', 'γ': r'$\gamma$', 'δ': r'$\delta$', 'ε': r'$\epsilon$', 'μ': r'$\mu$'}


def brace_title(t):
    t = t.strip()
    if t.startswith('{') and t.endswith('}') and t.count('{') == 1: return t   # fully braced already
    toks = t.split(' '); out = []
    for i, tok in enumerate(toks):
        core = tok.replace('{', '').replace('}', '')
        for g, r in GREEK.items():
            if g in core: core = core.replace(g, '{' + r + '}')
        word = re.sub(r'^[\(\[“"\']+|[\)\]”"\'.,;:?!]+$', '', core)
        need = False
        if re.search(r'\d', word): need = True
        elif re.search(r'[a-z][A-Z]|^[A-Z]{2,}', word): need = True          # inner capital / all-caps acronym
        elif word in ELEM or word in KEEP: need = True
        elif re.match(r'^[A-Z][a-z]?[-–][A-Z]', word): need = True           # Y-Si-O, Ba–Y
        if need and '{$' not in core:
            m = re.match(r'^([\(\[“"\']*)(.*?)([\)\]”"\'.,;:?!]*)$', core)
            if m and m.group(2): core = m.group(1) + '{' + m.group(2) + '}' + m.group(3)
        out.append(core)
    return ' '.join(out)


def fix_field(field, val):
    if field in ('title', 'journal', 'booktitle'):
        val = re.sub(r'\s+[-–—]\s+', ' -- ', val)
    if field == 'title': val = brace_title(val)
    return val


entries = re.split(r'(?=^@)', txt, flags=re.M)
out = []; stats = {'braced': 0, 'crossref': 0, 'patched': 0}
for e in entries:
    if not e.strip().startswith('@'): out.append(e); continue
    m = re.match(r'@(\w+)\{([^,]+),', e); typ, key = m.group(1), m.group(2).strip()
    fields = dict(re.findall(r'^\s*(\w+)\s*=\s*\{(.*)\},?\s*$', e, flags=re.M))
    p = patch.get(key, {})
    if p: stats['patched'] += 1
    typ = p.get('@type', typ)
    for k, v in p.items():
        if k not in ('@type', '__drop__'): fields[k] = v
    for k in p.get('__drop__', []): fields.pop(k, None)
    if crossref and fields.get('doi') and not (fields.get('volume') and fields.get('pages')):
        try:
            req = urllib.request.Request('https://api.crossref.org/works/' + urllib.parse.quote(fields['doi']), headers={'User-Agent': 'goai-bib-polish/1.0'})
            d = json.load(urllib.request.urlopen(req, timeout=20))['message']
            for a, b in (('volume', 'volume'), ('number', 'issue'), ('pages', 'page')):
                if not fields.get(a) and d.get(b): fields[a] = str(d[b]).replace('-', '--'); stats['crossref'] += 1
            time.sleep(0.3)
        except Exception as ex: print('crossref miss', key, str(ex)[:60])
    new = fields.copy()
    for k in ('title', 'journal', 'booktitle'):
        if k in new: new[k] = fix_field(k, new[k])
    if new.get('title') != fields.get('title'): stats['braced'] += 1
    order = ['author', 'title', 'journal', 'booktitle', 'school', 'type', 'howpublished', 'publisher', 'volume', 'number', 'pages', 'year', 'doi', 'url', 'note']
    keys = [k for k in order if k in new] + [k for k in new if k not in order]
    out.append('@%s{%s,\n' % (typ, key) + ''.join('  %s = {%s},\n' % (k, new[k]) for k in keys) + '}\n\n')
open(dst, 'w', encoding='utf-8').write(''.join(out)); print(stats)
