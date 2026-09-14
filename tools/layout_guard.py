#!/usr/bin/env python3
r"""layout_guard —— 版面与格式门禁：把这一轮踩过的坑全部变成自动检查。

背景：2026-09-13/14 那一轮里，题注忽左忽中、图内文字被盖住、表格没浮到页底、标题多了记号、
`\sloppy` 把词距放松、图文用词不一致……全部是靠人一页页看出来的。这个脚本把每一类都写成
可执行的检查，接到构建脚本后面，编译完就跑，有 FAIL 就不该发布。

    layout_guard.py --pdf main.pdf --log main.log --src sections_zh3 --lang zh \
                    [--sty goai_zh_typo.sty] [--figdir figures/pdf] [--json] [--strict]

退出码：0 = 全通过（或只有 WARN）；1 = 有 FAIL；2 = 参数/文件问题。
`--strict` 时 WARN 也算失败。

检查分五层：
  A 编译层   读 .log：错误、Overfull、缺图、未定义引用
  B 版面层   读 PDF 几何：题注对齐、文字是否跑出版心、页眉页码
  C 结构层   读 .tex 源：图路径与语言、表格浮动位置、三线表、题注上下位置、列宽合计
  D 用词层   chemlib 措辞 lint，正文与**图件内文字**都要过
  E 样式层   读 .sty：默认模版、singlelinecheck、\sloppy 这些一改就出事的开关
"""
import argparse, collections, glob, json, os, re, subprocess, sys, xml.etree.ElementTree as ET

NS = '{http://www.w3.org/1999/xhtml}'
HERE = os.path.dirname(os.path.abspath(__file__))
findings = []


def add(level, cid, msg, where=''):
    findings.append({'level': level, 'check': cid, 'message': msg, 'where': where})


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=180).stdout
    except Exception:
        return ''


# ---------------------------------------------------------------- A 编译层
def check_log(path):
    if not path or not os.path.exists(path):
        add('WARN', 'A0', '没有 .log，跳过编译层检查', path or '-')
        return
    log = open(path, encoding='utf-8', errors='replace').read()

    errs = re.findall(r'^! .*$', log, re.M)
    if errs:
        add('FAIL', 'A1', '%d 处 LaTeX 错误，第一处：%s' % (len(errs), errs[0][:90]), path)

    over = [float(m) for m in re.findall(r'^Overfull \\hbox \(([\d.]+)pt too wide\)', log, re.M)]
    big = [x for x in over if x > 1.0]
    if big:
        add('FAIL', 'A2', '%d 处 Overfull \\hbox 超过 1pt，最大 %.2fpt' % (len(big), max(big)), path)
    elif over:
        add('WARN', 'A2', '%d 处 Overfull \\hbox 但都 ≤1pt（最大 %.2fpt，肉眼不可见）' % (len(over), max(over)), path)

    vbox = len(re.findall(r'^Overfull \\vbox', log, re.M))
    if vbox:
        add('FAIL', 'A3', '%d 处 Overfull \\vbox（内容溢出页面下边界）' % vbox, path)

    miss = re.findall(r'File `([^\']+)\' not found', log)
    if miss:
        add('FAIL', 'A4', '缺文件：%s' % ', '.join(sorted(set(miss))[:5]), path)

    if re.search(r'There were undefined references', log):
        und = sorted(set(re.findall(r"(?:Citation|Reference) `([^']+)' on page", log)))
        add('FAIL', 'A5', '未定义的引用/交叉引用：%s' % ', '.join(und[:8]), path)
    if re.search(r'multiply.defined', log, re.I):
        add('FAIL', 'A6', '存在重复定义的 \\label', path)

    bad = len(re.findall(r'Underfull \\hbox \(badness 10000\)', log))
    if bad > 8:
        add('WARN', 'A7', '%d 处 badness 10000 的 Underfull（行内空得厉害，通常是断行参数太松）' % bad, path)


# ---------------------------------------------------------------- B 版面层
def page_words(pdf):
    out = run(['pdftotext', '-bbox', pdf, '-'])
    if not out.strip():
        return []
    try:
        root = ET.fromstring(out)
    except ET.ParseError:
        return []
    pages = []
    for pg in root.iter(NS + 'page'):
        ws = [(w.text or '', float(w.get('xMin')), float(w.get('yMin')),
               float(w.get('xMax')), float(w.get('yMax'))) for w in pg.iter(NS + 'word')]
        pages.append((float(pg.get('width')), float(pg.get('height')), ws))
    return pages


def text_block(pages):
    """版心边界。

    左边界用行首 x 的众数——正文顶左，这个众数很干净。
    右边界不能用众数：中文可在任意字处断行，行尾常差半个字没顶到版心，众数会偏小几十 pt，
    据此判越界会把正常的中文行全部误报。改用 xMax 的 99.5 百分位；真正的水平溢出由 A2
    从 .log 里的 Overfull \hbox 权威判定，这里只做兜底。"""
    lefts, rights = collections.Counter(), []
    for _, _, ws in pages:
        for _, x0, _, x1, _ in ws:
            lefts[round(x0 * 2) / 2] += 1
            rights.append(x1)
    if not lefts:
        return None, None
    rights.sort()
    return lefts.most_common(1)[0][0], rights[int(len(rights) * 0.995)]


CAPLABEL = {'zh': ('表', '图'), 'en': ('Table', 'Figure')}


def caption_labels(pages, lang):
    """题注标签的位置：标签词 + 紧随其后的「数字.」，且必须是所在行的第一个词。

    不加「行首」这个条件的话，正文里句末的 “…listed in Table 2.” 会被当成题注，
    而它出现在行中间，位置一比就被误判成「居中的题注」。"""
    out = []
    for pi, (_, _, ws) in enumerate(pages, 1):
        # 按基线分行，取每行最左的 x
        rows = collections.defaultdict(list)
        for w in ws:
            rows[round(w[2] / 3)].append(w)
        line_left = {r: min(w[1] for w in v) for r, v in rows.items()}
        for i, (t, x0, y0, x1, y1) in enumerate(ws):
            if x0 - line_left[round(y0 / 3)] > 1.0:      # 不是行首，跳过
                continue
            for k in CAPLABEL[lang]:
                if not t.startswith(k):
                    continue
                rest = t[len(k):].strip()
                nxt = ws[i + 1][0].strip() if i + 1 < len(ws) else ''
                cand = rest or nxt
                if re.match(r'^\d+[.．]$', cand):
                    out.append((pi, k + cand, x0, y0))
    return out


def check_pdf(pdf, lang, expect_head):
    if not os.path.exists(pdf):
        add('FAIL', 'B0', 'PDF 不存在', pdf)
        return
    pages = page_words(pdf)
    if not pages:
        add('WARN', 'B0', '读不出 PDF 文字（pdftotext -bbox 无输出），跳过版面检查', pdf)
        return
    left, right = text_block(pages)

    # B1 题注一律左对齐（singlelinecheck 开着时短题注会居中）
    bad = [(p, lab, x) for p, lab, x, _ in caption_labels(pages, lang) if x - left > 3.0]
    if bad:
        add('FAIL', 'B1', '%d 条题注没有顶左（singlelinecheck 没关？）：%s' % (
            len(bad), '; '.join('p%d %s x=%.0f' % (p, l, x) for p, l, x in bad[:4])), pdf)

    # B2 文字不得跑出版心。中文标点是悬挂的（句号逗号可以探出边界半个字），要排除，
    # 否则每份中文稿都会被误报；真正的水平溢出由 A2 从 .log 权威判定，这里只兜底。
    HANG = '。，、；：）」』】》？！%'
    total = sum(len(ws) for _, _, ws in pages) or 1
    out = []
    for pi, (_, _, ws) in enumerate(pages, 1):
        for t, x0, _, x1, _ in ws:
            if x0 < left - 3.0 or (x1 > right + 3.0 and not (t and t[-1] in HANG)):
                out.append((pi, t[:16], x0, x1))
    if len(out) > max(3, total * 0.002):
        add('FAIL', 'B2', '%d 处文字越出版心 [%.0f, %.0f]：%s' % (
            len(out), left, right, '; '.join('p%d «%s»' % (p, t) for p, t, _, _ in out[:4])), pdf)

    # B3 页眉 / 页码
    if expect_head and len(pages) > 2:
        nohead = [pi for pi, (_, h, ws) in enumerate(pages, 1)
                  if pi > 1 and not any(y1 < h * 0.11 for _, _, _, _, y1 in ws)]
        if len(nohead) > 1:
            add('WARN', 'B3', '%d 页没有页眉（首页除外）：%s' % (len(nohead), nohead[:6]), pdf)

    # B4 每页都要有页码（页眉右上或页脚居中）
    nonum = []
    for pi, (_, h, ws) in enumerate(pages, 1):
        if pi == 1:
            continue                       # 首页 \thispagestyle{empty}，本来就没有页码
        if not any(re.fullmatch(r'\d{1,3}', t) and (y0 < h * 0.11 or y1 > h * 0.90)
                   for t, _, y0, _, y1 in ws):
            nonum.append(pi)
    if nonum:
        add('WARN', 'B4', '%d 页找不到页码：%s' % (len(nonum), nonum[:6]), pdf)


# ---------------------------------------------------------------- C 结构层
def check_sources(srcdir, lang, figdir):
    texs = sorted(glob.glob(os.path.join(srcdir, '*.tex')))
    if not texs:
        add('FAIL', 'C0', '源目录里没有 .tex', srcdir)
        return
    other = 'en' if lang == 'zh' else 'zh'
    for f in texs:
        s = open(f, encoding='utf-8').read()
        base = os.path.basename(f)

        # C1/C2 图件：路径要存在；语言要对
        for m in re.finditer(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', s):
            p = m.group(1)
            real = os.path.normpath(os.path.join(srcdir, p))
            if not os.path.exists(real) and not os.path.exists(real + '.pdf'):
                cand = os.path.join(figdir, os.path.basename(p)) if figdir else ''
                if not (cand and os.path.exists(cand)):
                    add('FAIL', 'C1', '图件不存在：%s' % p, base)
            if re.search(r'_%s\.(pdf|png|jpg)$' % other, p):
                add('FAIL', 'C2', '%s 版正文引用了 %s 版图件：%s' % (lang, other, p), base)

        # C3 表格浮动体要 [bp]（放页底），图 [t]
        for m in re.finditer(r'\\begin\{table\*?\}(\[[^\]]*\])?', s):
            spec = (m.group(1) or '')[1:-1]
            if spec != 'bp':
                add('FAIL', 'C3', 'table 浮动体应为 [bp]（浮到页底），实为 [%s]' % spec, base)

        # C4/C5 只用 booktabs 三线：不许竖线、不许 \hline
        for m in re.finditer(r'\\begin\{(?:tabular|longtable)\}(?:\[[^\]]*\])?\{([^}]*)\}', s):
            if '|' in m.group(1):
                add('FAIL', 'C4', '表格列格式里有竖线：%s' % m.group(1)[:50], base)
        if re.search(r'\\hline', s):
            add('FAIL', 'C5', '用了 \\hline（应只用 booktabs 的 \\toprule/\\midrule/\\bottomrule）', base)

        # C6 表注在表上、图注在图下
        for env, m in (('table', 'tabular'), ('figure', 'includegraphics')):
            for blk in re.findall(r'\\begin\{%s\*?\}.*?\\end\{%s\*?\}' % (env, env), s, re.S):
                ic, ib = blk.find('\\caption'), blk.find('\\' + m if env == 'figure' else '\\begin{' + m)
                if ic < 0 or ib < 0:
                    continue
                if env == 'table' and ic > ib:
                    add('FAIL', 'C6', 'table 的 \\caption 在表体之后（表注应在表上）', base)
                if env == 'figure' and ic < ib:
                    add('FAIL', 'C6', 'figure 的 \\caption 在图之前（图注应在图下）', base)

        # C7 分数列宽合计要等于 1（表格才会正好等于版心宽）
        for m in re.finditer(r'\\begin\{(?:tabular|longtable)\}(?:\[[^\]]*\])?\{((?:P\{[^{}]*\{[^{}]*\}[^{}]*\})+)\}', s):
            fr = [float(x) for x in re.findall(r'([\d.]+)\\textwidth', m.group(1))]
            if fr and abs(sum(fr) - 1.0) > 0.006:
                add('FAIL', 'C7', '表格列宽合计 %.4f ≠ 1，宽度会和正文不齐' % sum(fr), base)


# ---------------------------------------------------------------- D 用词层
def check_wording(srcdir, figdir):
    chem = os.path.join(HERE, 'chemlib.py')
    if not os.path.exists(chem):
        add('WARN', 'D0', '找不到 chemlib.py，跳过用词检查')
        return
    texs = sorted(glob.glob(os.path.join(srcdir, '*.tex')))
    out = run([sys.executable, chem, 'audit', '--json'] + texs)
    try:
        hits = json.loads(out) if out.strip().startswith('[') else []
    except json.JSONDecodeError:
        hits = []
    high = [h for h in hits if h.get('severity') == 'high']
    if high:
        add('FAIL', 'D1', '正文 %d 处 high 级用词问题：%s' % (
            len(high), '; '.join('%s:%d %s' % (h['file'], h['line'], h['match']) for h in high[:3])), srcdir)
    med = [h for h in hits if h.get('severity') == 'medium']
    if med:
        add('WARN', 'D1', '正文 %d 处 medium 级用词问题（chemlib audit 看详情）' % len(med), srcdir)

    # D2 图件里的文字也要守同一套术语——图文用词不一致是最容易漏的
    if not figdir or not os.path.isdir(figdir):
        return
    import tempfile
    terms = {}
    lib = os.path.join(HERE, '..', 'templates', 'chem_library', 'watchlist.json')
    anti = os.path.join(HERE, '..', 'templates', 'chem_library', 'entries', 'anti_patterns.jsonl')
    bad_terms = []
    if os.path.exists(anti):
        for line in open(anti, encoding='utf-8'):
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get('kind') == 'anti_pattern':
                for v in (e.get('variants') or [e.get('expression', '')]):
                    v = str(v).strip()
                    if 2 <= len(v) <= 8:
                        bad_terms.append((v, e.get('avoid') or ''))
    # 术语表里被规范化掉的旧写法
    gl = os.path.join(HERE, '..', 'templates', 'glossary_materials_zh.json')
    if os.path.exists(gl):
        g = json.load(open(gl, encoding='utf-8'))
        for old, new in (g.get('zh_normalize') or {}).items():
            if 2 <= len(old) <= 8:
                bad_terms.append((old, '正文已统一为「%s」' % new))
    for pdf in sorted(glob.glob(os.path.join(figdir, '*.pdf'))):
        txt = run(['pdftotext', '-layout', pdf, '-']).replace(' ', '').replace('\n', '')
        for v, why in bad_terms:
            if v in txt:
                add('FAIL', 'D2', '图件里用了非规范写法「%s」（%s），与正文不一致' % (v, why[:40]),
                    os.path.basename(pdf))


# ---------------------------------------------------------------- E 样式层
def check_sty(sty):
    if not sty or not os.path.exists(sty):
        add('WARN', 'E0', '没给 .sty，跳过样式层检查', sty or '-')
        return
    s = open(sty, encoding='utf-8').read()
    name = os.path.basename(sty)

    m = re.search(r'\\DeclareStringOption\[(\w+)\]\{template\}', s)
    if not m:
        add('FAIL', 'E1', '找不到 template 默认值声明', name)
    elif m.group(1) != 'manuscript':
        add('FAIL', 'E1', '默认模版是 %s，约定应为 manuscript' % m.group(1), name)

    if 'singlelinecheck=true' in s:
        add('FAIL', 'E2', 'singlelinecheck=true 还在（短题注会被居中，造成题注忽左忽中）', name)

    for m in re.finditer(r'^\s*\\sloppy\s*$', s, re.M):
        add('FAIL', 'E3', '有裸的 \\sloppy（tolerance 9999 会把词距放得很松），应放进 \\ifgoai@manu 的 else 分支', name)

    if 'microtype' not in s:
        add('WARN', 'E4', '没加载 microtype', name)
    if '\\raggedbottom' not in s:
        add('WARN', 'E5', '没有 \\raggedbottom（中文短页会被拉伸）', name)
    m = re.search(r'\\renewcommand\{\\bottomfraction\}\{([\d.]+)\}', s)
    if m and float(m.group(1)) < 0.7:
        add('FAIL', 'E6', 'bottomfraction=%s 太小，半页高的表格落不到页底会漂走' % m.group(1), name)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--pdf'); ap.add_argument('--log'); ap.add_argument('--src')
    ap.add_argument('--sty'); ap.add_argument('--figdir')
    ap.add_argument('--lang', default='zh', choices=['zh', 'en'])
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--strict', action='store_true', help='WARN 也算失败')
    a = ap.parse_args()

    if a.log or a.pdf:
        check_log(a.log or (os.path.splitext(a.pdf)[0] + '.log'))
    if a.pdf:
        check_pdf(a.pdf, a.lang, expect_head=True)
    if a.src:
        check_sources(a.src, a.lang, a.figdir)
        check_wording(a.src, a.figdir)
    check_sty(a.sty)

    if a.json:
        print(json.dumps(findings, ensure_ascii=False, indent=1))
    else:
        for f in sorted(findings, key=lambda x: {'FAIL': 0, 'WARN': 1}[x['level']]):
            print('%-4s %-3s %-28s %s' % (f['level'], f['check'], f['where'][:28], f['message']))
        nf = sum(1 for f in findings if f['level'] == 'FAIL')
        nw = len(findings) - nf
        print('\n%s  FAIL %d · WARN %d   (%s)' % ('PASS' if nf == 0 else 'BLOCKED', nf, nw,
                                                   os.path.basename(a.pdf or a.src or a.sty or '')))
    nf = sum(1 for f in findings if f['level'] == 'FAIL')
    sys.exit(1 if nf or (a.strict and findings) else 0)


if __name__ == '__main__':
    main()
