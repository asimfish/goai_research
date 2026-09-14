#!/usr/bin/env python3
r"""chemlib —— 固态化学中文写作词库的检索与 lint。

对标 github.com/asimfish/super_library（那是英文 AI 论文语料，没有化学内容；这里照搬它的
schema 与方法：term / definition / phrase / sentence_pattern / usage_note / anti_pattern
六种词条 + 按 domain/section/intent 检索 + 写作协议 + 措辞 lint）。

词库在 `goai_research/templates/chem_library/`：
    taxonomy.json           分类词表
    entries/*.jsonl         词条，一行一条
    writing_guides.json     各章节写作协议
    watchlist.json          lint 正则规则

用法：
    chemlib.py audit  <file.tex ...> [--severity high|medium|low] [--json]
    chemlib.py route  --section condition_matrix [--intent caution] [--domain crystal_growth]
    chemlib.py show   <entry-id>
    chemlib.py terms  [--domain D] [--grep 词]
    chemlib.py guide  [--list | <guide-id>]
    chemlib.py stats
"""
import argparse, json, os, re, sys

LIB = os.environ.get('CHEMLIB_DIR') or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'templates', 'chem_library')
LIB = os.path.abspath(LIB)


def _load_json(name, default=None):
    p = os.path.join(LIB, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def load_entries():
    out, bad = [], 0
    d = os.path.join(LIB, 'entries')
    if not os.path.isdir(d):
        return out, bad
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.jsonl'):
            continue
        with open(os.path.join(d, fn), encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    bad += 1
                    continue
                e.setdefault('_file', fn)
                e.setdefault('_line', i)
                out.append(e)
    return out, bad


# ---------------------------------------------------------------- 正文清洗
PROTECT = [
    (r'\\cite\w*\{[^}]*\}', ' '),          # 引用
    (r'\\(?:ref|eqref|label)\{[^}]*\}', ' '),
    (r'\$[^$]*\$', ' '),                   # 行内公式：化学式在这里，别 lint 它
    (r'%.*', ' '),                         # 注释
]


def strip_tex(text):
    """把 \\cite/公式/注释换成等长空白，行号与列号保持不变"""
    out = text
    for pat, _ in PROTECT:
        out = re.sub(pat, lambda m: ' ' * len(m.group(0)), out)
    return out


def line_of(text, pos):
    return text.count('\n', 0, pos) + 1


# ---------------------------------------------------------------- audit
def cmd_audit(a):
    rules = _load_json('watchlist.json', []) or []
    entries, bad = load_entries()
    anti = [e for e in entries if e.get('kind') == 'anti_pattern']
    order = {'high': 0, 'medium': 1, 'low': 2}
    findings = []
    for path in a.files:
        try:
            raw = open(path, encoding='utf-8').read()
        except OSError as exc:
            print('ERROR: %s' % exc, file=sys.stderr)
            return 1
        text = strip_tex(raw)
        for r in rules:
            sev = r.get('severity', 'medium')
            if a.severity and order.get(sev, 1) > order.get(a.severity, 2):
                continue
            try:
                rx = re.compile(r['pattern'])
            except re.error as exc:
                print('WARN: bad pattern %s: %s' % (r.get('id'), exc), file=sys.stderr)
                continue
            for m in rx.finditer(text):
                findings.append({'file': os.path.basename(path), 'line': line_of(text, m.start()),
                                 'rule': r.get('id', '?'), 'severity': sev,
                                 'match': m.group(0).strip(), 'message': r.get('message', '')})
        for e in anti:
            # super_library splits `expression` on '/' because its anti-patterns are English
            # alternatives ("utilize/leverage"). Chinese expressions use '/' inside the phrase
            # itself ("开放/封闭性—"), so only split on an explicit `variants` list or a spaced slash.
            variants = e.get('variants') or ([p for p in str(e.get('expression', '')).split(' / ')]
                                             if ' / ' in str(e.get('expression', ''))
                                             else [e.get('expression', '')])
            for variant in variants:
                v = str(variant).strip()
                if len(v) < 2:
                    continue
                for m in re.finditer(re.escape(v), text):
                    findings.append({'file': os.path.basename(path), 'line': line_of(text, m.start()),
                                     'rule': e.get('id', '?'), 'severity': 'medium',
                                     'match': v, 'message': e.get('avoid') or e.get('guidance', '')})
    findings.sort(key=lambda f: (order.get(f['severity'], 1), f['file'], f['line']))
    if a.json:
        print(json.dumps(findings, ensure_ascii=False, indent=1))
    else:
        for f in findings:
            print('%-28s %4d  [%-6s] %-22s %s' % (f['file'], f['line'], f['severity'],
                                                  f['match'][:22], f['message'][:90]))
        print('\n%d findings (%d rules, %d anti-patterns%s)' % (
            len(findings), len(rules), len(anti), ', %d unparsable entry lines' % bad if bad else ''))
    return 1 if any(f['severity'] == 'high' for f in findings) else 0


# ---------------------------------------------------------------- route / show / terms
def _match(e, a):
    if a.domain and a.domain not in e.get('domains', []):
        return False
    if a.section and a.section not in e.get('sections', []):
        return False
    if a.intent and a.intent not in e.get('intents', []):
        return False
    if a.kind and e.get('kind') != a.kind:
        return False
    return True


def _brief(e):
    return '%-34s %-16s %s' % (e.get('id', '?'), e.get('kind', '?'),
                               str(e.get('expression', ''))[:60])


def cmd_route(a):
    entries, _ = load_entries()
    hits = [e for e in entries if _match(e, a)]
    guides = (_load_json('writing_guides.json', {}) or {}).get('guides', [])
    gh = [g for g in guides if (not a.section) or g.get('section') == a.section]
    print('# guides')
    for g in gh[:3]:
        print('  %-26s %s' % (g.get('id', '?'), g.get('label') or g.get('purpose', '')[:70]))
    print('# entries (%d matched, showing %d)' % (len(hits), min(len(hits), a.limit)))
    for e in hits[:a.limit]:
        print('  ' + _brief(e))
    return 0


def cmd_show(a):
    entries, _ = load_entries()
    for e in entries:
        if e.get('id') == a.entry_id:
            print(json.dumps(e, ensure_ascii=False, indent=1))
            return 0
    print('not found: %s' % a.entry_id, file=sys.stderr)
    return 1


def cmd_terms(a):
    entries, _ = load_entries()
    for e in entries:
        if e.get('kind') not in ('term', 'definition'):
            continue
        if a.domain and a.domain not in e.get('domains', []):
            continue
        blob = json.dumps(e, ensure_ascii=False)
        if a.grep and a.grep not in blob:
            continue
        print('%-22s %-34s %s' % (str(e.get('expression', ''))[:22], str(e.get('en', ''))[:34],
                                  str(e.get('meaning', ''))[:60]))
    return 0


def cmd_guide(a):
    guides = (_load_json('writing_guides.json', {}) or {}).get('guides', [])
    if a.guide_id:
        for g in guides:
            if g.get('id') == a.guide_id:
                print(json.dumps(g, ensure_ascii=False, indent=1))
                return 0
        print('not found: %s' % a.guide_id, file=sys.stderr)
        return 1
    for g in guides:
        print('%-26s %-20s %s' % (g.get('id', '?'), g.get('section', '?'),
                                  (g.get('label') or g.get('purpose', ''))[:60]))
    return 0


def cmd_stats(a):
    entries, bad = load_entries()
    kinds, domains = {}, {}
    for e in entries:
        kinds[e.get('kind', '?')] = kinds.get(e.get('kind', '?'), 0) + 1
        for d in e.get('domains', []):
            domains[d] = domains.get(d, 0) + 1
    guides = (_load_json('writing_guides.json', {}) or {}).get('guides', [])
    print('library : %s' % LIB)
    print('entries : %d  (%d unparsable lines)' % (len(entries), bad))
    print('kinds   : %s' % ', '.join('%s=%d' % kv for kv in sorted(kinds.items())))
    print('domains : %s' % ', '.join('%s=%d' % kv for kv in sorted(domains.items())))
    print('guides  : %d' % len(guides))
    print('watchlist rules: %d' % len(_load_json('watchlist.json', []) or []))
    return 0


def main():
    ap = argparse.ArgumentParser(prog='chemlib', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('audit', help='措辞 lint：watchlist 正则 + anti_pattern 词条')
    p.add_argument('files', nargs='+')
    p.add_argument('--severity', choices=['high', 'medium', 'low'])
    p.add_argument('--json', action='store_true')
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser('route', help='按 section/intent/domain 取一小批词条与写作协议')
    for k in ('domain', 'section', 'intent', 'kind'):
        p.add_argument('--' + k)
    p.add_argument('--limit', type=int, default=12)
    p.set_defaults(func=cmd_route)

    p = sub.add_parser('show', help='按 id 看一条词条')
    p.add_argument('entry_id')
    p.set_defaults(func=cmd_show)

    p = sub.add_parser('terms', help='列术语表')
    p.add_argument('--domain')
    p.add_argument('--grep')
    p.set_defaults(func=cmd_terms)

    p = sub.add_parser('guide', help='列/看章节写作协议')
    p.add_argument('guide_id', nargs='?')
    p.set_defaults(func=cmd_guide)

    p = sub.add_parser('stats', help='词库规模')
    p.set_defaults(func=cmd_stats)

    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == '__main__':
    main()
