#!/usr/bin/env python3
"""Fill a Markdown report into the official AI4R competition DOCX template.

The official template (``templates/official_ai4r_report_template.docx``) supplies
page setup and heading styles; the Markdown supplies the body.  Supported Markdown:

* ``## 一、…`` -> heading 1, ``### 1.1 …`` -> heading 2 (page break before 三/五 chapters)
* paragraphs, ``- `` bullets, ``**bold**``, ``*italic*``, `` `code` `` (stripped), ``<https://…>`` links
* pipe tables (header row shaded)
* ``![alt](path/to/figure.png){0.9}`` images (path relative to the current directory,
  optional ``{ratio}`` = width as a fraction of the text column) followed by a
  ``图 N｜caption`` line rendered as a caption
* ``# `` top-level title and ``> `` blockquotes are ignored (the title block is rebuilt
  from ``--title/--subtitle/--note``)

Usage::

    python3 tools/build_report_docx.py --md docs/competition/FINAL_REPORT.md \
        --out submission/复赛报告/复赛报告_SAGE-Mat.docx \
        --title "AI for Research赛道｜算法赛复赛报告" \
        --subtitle "复赛提交：方案说明 PPT + 复赛报告（初赛问题定义文档加强版）" \
        --note "报告中的每个主要结论、图与指标均可追溯到提交包中的代码版本、配置、数据、运行日志与结果文件。"
"""
from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import tempfile
import zipfile
import struct
from pathlib import Path

EMU_PER_INCH = 914400
CONTENT_W_TWIP = 12240 - 1181 * 2
CONTENT_W_EMU = int(CONTENT_W_TWIP / 20 / 72 * EMU_PER_INCH)
FONT = '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="微软雅黑"/>'
RPR_BODY = '<w:rPr>' + FONT + '{b}{i}<w:color w:val="000000"/><w:sz w:val="21"/></w:rPr>'
PAGEBREAK = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def run(text: str, bold: bool = False, italic: bool = False) -> str:
    b = '<w:b/>' if bold else '<w:b w:val="0"/>'
    i = '<w:i/>' if italic else '<w:i w:val="0"/>'
    return f'<w:r>{RPR_BODY.format(b=b, i=i)}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


BREAKABLE_TOKEN = re.compile(r'(?<![\w/])[A-Za-z0-9][\w.-]*(?:[/_][\w.-]+)+')


def soften_long_tokens(text: str) -> str:
    """Insert zero-width break opportunities after '/' and '_' inside paths and
    identifiers so justified Chinese lines are not stretched around one long token."""
    return BREAKABLE_TOKEN.sub(lambda m: re.sub(r'([/_])', '\\1\u200b', m.group(0)), text)


def parse_inline(text: str, hyperlinks: dict[str, str]) -> str:
    text = soften_long_tokens(text.replace('`', ''))
    parts: list[str] = []
    for tok in re.split(r'(<https?://[^>]+>|https?://\S+)', text):
        m = re.fullmatch(r'<?(https?://[^>\s]+)>?', tok)
        if m and tok:
            url = m.group(1).rstrip('，。；、)')
            rid = hyperlinks.setdefault(url, f"rIdHl{len(hyperlinks) + 1}")
            parts.append(f'<w:hyperlink r:id="{rid}" w:history="1"><w:r><w:rPr>{FONT}'
                         '<w:color w:val="1F4D78"/><w:u w:val="single"/><w:sz w:val="21"/></w:rPr>'
                         f'<w:t xml:space="preserve">{esc(url)}</w:t></w:r></w:hyperlink>')
            continue
        for seg in re.split(r'(\*\*[^*]+\*\*|\*[^*]+\*)', tok):
            if not seg:
                continue
            if seg.startswith('**') and seg.endswith('**'):
                parts.append(run(seg[2:-2], bold=True))
            elif seg.startswith('*') and seg.endswith('*') and len(seg) > 2:
                parts.append(run(seg[1:-1], italic=True))
            else:
                parts.append(run(seg))
    return ''.join(parts)


BODY_SPACING = '<w:spacing w:after="80" w:line="330" w:lineRule="auto"/>'


def para_body(text: str, hyperlinks: dict[str, str], indent: bool = True) -> str:
    # Chinese body text: 2-character first-line indent (2 x 10.5pt = 420 twips), justified.
    ind = '<w:ind w:firstLine="420"/>' if indent else ''
    return (f'<w:p><w:pPr>{BODY_SPACING}{ind}<w:jc w:val="both"/></w:pPr>'
            + parse_inline(text, hyperlinks) + '</w:p>')


def para_list_item(marker: str, text: str, hyperlinks: dict[str, str]) -> str:
    # Hanging indent so wrapped lines align under the text, not under the marker.
    return (f'<w:p><w:pPr>{BODY_SPACING}<w:ind w:left="480" w:hanging="480"/><w:jc w:val="both"/></w:pPr>'
            + run(marker + '\u2002') + parse_inline(text, hyperlinks) + '</w:p>')


def caption_text(text: str) -> str:
    # "图 1｜xxx" / "表 2｜xxx" -> "图 1　xxx" (full-width space instead of a bar)
    return re.sub(r'^(图|表) ?(\d+)\s*[｜|]\s*', lambda m: f'{m.group(1)} {m.group(2)}\u3000', text)


def para_caption(text: str, above: bool = False) -> str:
    spacing = ('<w:spacing w:before="120" w:after="60"/><w:keepNext/>' if above
               else '<w:spacing w:before="40" w:after="200"/>')
    return (f'<w:p><w:pPr>{spacing}<w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:rPr>{FONT}<w:b w:val="0"/><w:i w:val="0"/><w:color w:val="404040"/><w:sz w:val="18"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(caption_text(text))}</w:t></w:r></w:p>')


def para_heading(text: str, style: str) -> str:
    return (f'<w:p><w:pPr><w:pStyle w:val="{style}"/><w:keepNext/><w:keepLines/></w:pPr>'
            f'<w:r><w:t>{esc(text)}</w:t></w:r></w:p>')


def para_head_block(title: str, subtitle: str, note: str) -> str:
    t = ('<w:p><w:pPr><w:spacing w:before="120" w:after="80" w:line="300" w:lineRule="auto"/><w:jc w:val="center"/></w:pPr>'
         f'<w:r><w:rPr>{FONT}<w:b/><w:color w:val="0B2545"/><w:sz w:val="36"/></w:rPr><w:t>{esc(title)}</w:t></w:r></w:p>')
    s = ''
    if subtitle:
        s = ('<w:p><w:pPr><w:spacing w:after="60"/><w:jc w:val="center"/></w:pPr>'
             f'<w:r><w:rPr>{FONT}<w:b w:val="0"/><w:color w:val="5A6573"/><w:sz w:val="20"/></w:rPr><w:t>{esc(subtitle)}</w:t></w:r></w:p>')
    n = ''
    if note:
        n = ('<w:p><w:pPr><w:spacing w:before="40" w:after="120"/><w:jc w:val="center"/></w:pPr>'
             f'<w:r><w:rPr>{FONT}<w:b w:val="0"/><w:color w:val="5A6573"/><w:sz w:val="18"/></w:rPr><w:t xml:space="preserve">{esc(note)}</w:t></w:r></w:p>')
    # a thin rule under the title block
    rule = ('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="1F4D78"/></w:pBdr>'
            '<w:spacing w:before="0" w:after="200"/></w:pPr></w:p>')
    return t + s + n + rule


def _png_size(path: Path) -> tuple[int, int]:
    with path.open('rb') as fh:
        head = fh.read(24)
    if head[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError(f'only PNG figures are supported: {path}')
    w, h = struct.unpack('>II', head[16:24])
    return w, h


def para_image(rid: str, png_path: Path, width_ratio: float, docpr_id: int) -> str:
    w_px, h_px = _png_size(png_path)
    cx = int(CONTENT_W_EMU * width_ratio)
    cy = int(cx * h_px / w_px)
    return ('<w:p><w:pPr><w:spacing w:before="120" w:after="40"/><w:keepNext/><w:jc w:val="center"/></w:pPr>'
            '<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{docpr_id}" name="Figure{docpr_id}"/>'
            '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:nvPicPr><pic:cNvPr id="{docpr_id}" name="Figure{docpr_id}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')


NUMERIC_CELL = re.compile(r'^[\d.,%±/\s—–\-]+$')


def _cjk_width(s: str) -> float:
    return sum(1.0 if ord(ch) > 0x2E7F else 0.55 for ch in s)


CHAR_TWIP = 190          # one CJK character at 9pt plus a little tracking
CELL_PAD_TWIP = 170      # left + right cell margins


def _column_widths(rows: list[list[str]]) -> list[int]:
    """Fixed-layout widths. Short columns (labels, numbers) get their natural width so
    they never wrap; only long-text columns are squeezed to fit the text block."""
    ncol = len(rows[0])
    longest = [max(_cjk_width(r[c]) for r in rows) for c in range(ncol)]
    natural = [int(min(L, 18) * CHAR_TWIP + CELL_PAD_TWIP) for L in longest]
    flexible = [L > 18 for L in longest]
    if not any(flexible):
        flexible = [L == max(longest) for L in longest]
    fixed_total = sum(w for w, f in zip(natural, flexible) if not f)
    remaining = max(CONTENT_W_TWIP - fixed_total, 1200 * sum(flexible))
    flex_weights = [min(L, 60) for L, f in zip(longest, flexible) if f]
    flex_total = sum(flex_weights) or 1
    widths, fi = [], 0
    for w, f in zip(natural, flexible):
        if f:
            widths.append(int(remaining * flex_weights[fi] / flex_total))
            fi += 1
        else:
            widths.append(w)
    widths[-1] = CONTENT_W_TWIP - sum(widths[:-1])
    return widths


def build_table(rows: list[list[str]], hyperlinks: dict[str, str]) -> str:
    ncol = max(len(r) for r in rows)
    rows = [r + [''] * (ncol - len(r)) for r in rows]
    widths = _column_widths(rows)
    grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    # Three-line (booktabs-style) table: heavier top/bottom rules, a rule under the
    # header, light inner horizontal rules, no vertical rules.
    bd = ('<w:tblBorders>'
          '<w:top w:val="single" w:sz="12" w:color="1F1F1F"/>'
          '<w:left w:val="nil"/><w:right w:val="nil"/>'
          '<w:bottom w:val="single" w:sz="12" w:color="1F1F1F"/>'
          '<w:insideH w:val="single" w:sz="2" w:color="D0D0D0"/>'
          '<w:insideV w:val="nil"/>'
          '</w:tblBorders>')
    mar = ('<w:tblCellMar><w:top w:w="50" w:type="dxa"/><w:left w:w="80" w:type="dxa"/>'
           '<w:bottom w:w="50" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar>')
    xml = [f'<w:tbl><w:tblPr><w:tblW w:w="{CONTENT_W_TWIP}" w:type="dxa"/><w:jc w:val="center"/>{bd}'
           f'<w:tblLayout w:type="fixed"/>{mar}</w:tblPr><w:tblGrid>' + grid + '</w:tblGrid>']
    for ri, row in enumerate(rows):
        trpr = '<w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' if ri == 0 else '<w:trPr><w:cantSplit/></w:trPr>'
        xml.append('<w:tr>' + trpr)
        for ci, cell in enumerate(row):
            header = ri == 0
            numeric = (not header) and ci > 0 and bool(NUMERIC_CELL.match(cell.strip() or 'x'))
            jc = 'center' if (header and ci > 0 and all(NUMERIC_CELL.match(r[ci].strip() or 'x') for r in rows[1:])) or numeric else 'left'
            tcpr = f'<w:tcW w:w="{widths[ci]}" w:type="dxa"/>'
            if header:
                tcpr += '<w:shd w:val="clear" w:fill="F2F2F2"/><w:tcBorders><w:bottom w:val="single" w:sz="6" w:color="1F1F1F"/></w:tcBorders>'
            tcpr += '<w:vAlign w:val="center"/>'
            inline = parse_inline(('**' + cell + '**') if header and '**' not in cell else cell, hyperlinks)
            inline = inline.replace('<w:sz w:val="21"/>', '<w:sz w:val="18"/>')
            xml.append(f'<w:tc><w:tcPr>{tcpr}</w:tcPr>'
                       f'<w:p><w:pPr><w:spacing w:before="20" w:after="20" w:line="260" w:lineRule="auto"/><w:jc w:val="{jc}"/></w:pPr>'
                       + inline + '</w:p></w:tc>')
        xml.append('</w:tr>')
    xml.append('</w:tbl><w:p><w:pPr><w:spacing w:before="0" w:after="120"/></w:pPr></w:p>')
    return ''.join(xml)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--md', required=True)
    ap.add_argument('--template', default='templates/official_ai4r_report_template.docx')
    ap.add_argument('--out', required=True)
    ap.add_argument('--title', default='AI for Research赛道｜算法赛复赛报告')
    ap.add_argument('--subtitle', default='复赛提交：方案说明 PPT + 复赛报告（初赛问题定义文档加强版）')
    ap.add_argument('--note', default='本报告为初赛问题定义文档的加强版；其中每个主要结论、图与指标均可追溯到提交包中的代码版本、配置、数据、运行日志/Agent 轨迹与结果文件（见 docs/competition/SUBMISSION.md）。')
    ap.add_argument('--pagebreak-before', default='', help='comma-separated heading-1 prefixes that start a new page (default: none)')
    ap.add_argument('--footer', default='算法赛复赛报告 · SAGE-Mat', help='text replacing the template footer label')
    args = ap.parse_args()

    md_lines = Path(args.md).read_text(encoding='utf-8').split('\n')
    breaks = tuple(x for x in args.pagebreak_before.split(',') if x)
    hyperlinks: dict[str, str] = {}
    body: list[str] = [para_head_block(args.title, args.subtitle, args.note)]
    images: list[tuple[str, Path]] = []
    docpr = 100
    table_buf: list[str] = []
    pending_table_caption: str | None = None

    def flush_table() -> None:
        nonlocal table_buf, pending_table_caption
        if table_buf:
            rows = [[c.strip() for c in ln.strip().strip('|').split('|')] for ln in table_buf]
            rows = [r for r in rows if not all(re.fullmatch(r':?-+:?', c) for c in r)]
            if pending_table_caption:
                body.append(para_caption(pending_table_caption, above=True))
                pending_table_caption = None
            body.append(build_table(rows, hyperlinks))
            table_buf = []

    for raw in md_lines:
        s = raw.rstrip().strip()
        if s.startswith('|'):
            table_buf.append(s)
            continue
        flush_table()
        if not s or s.startswith('# ') or s.startswith('> '):
            continue
        if s.startswith('## '):
            title = s[3:]
            if title.startswith(breaks):
                body.append(PAGEBREAK)
            body.append(para_heading(title, '3'))
            continue
        if s.startswith('### '):
            body.append(para_heading(s[4:], '4'))
            continue
        m = re.match(r'!\[[^\]]*\]\(([^)]+)\)(?:\{([0-9.]+)\})?', s)
        if m:
            png = Path(m.group(1))
            if not png.exists():
                raise FileNotFoundError(png)
            ratio = float(m.group(2) or 1.0)
            rid = f'rIdImg{len(images) + 1}'
            images.append((rid, png))
            docpr += 1
            body.append(para_image(rid, png, ratio, docpr))
            continue
        if re.match(r'^图 ?\d+[｜|]', s):
            body.append(para_caption(s))
            continue
        if re.match(r'^表 ?\d+[｜|]', s):
            pending_table_caption = s      # rendered when the table that follows is flushed
            continue
        if s.startswith('- '):
            body.append(para_list_item('•', s[2:], hyperlinks))
            continue
        m = re.match(r'^(\d+)\. (.*)', s)
        if m:
            body.append(para_list_item(m.group(1) + '.', m.group(2), hyperlinks))
            continue
        body.append(para_body(s, hyperlinks))
    flush_table()

    tmp = tempfile.mkdtemp()
    with zipfile.ZipFile(args.template) as z:
        z.extractall(tmp)
    doc_path = os.path.join(tmp, 'word/document.xml')
    doc = open(doc_path, encoding='utf-8').read()
    m_body = re.search(r'(<w:body>)(.*)(<w:sectPr>.*</w:sectPr>)</w:body>', doc, flags=re.S)
    new_doc = doc[:m_body.start(2)] + ''.join(body) + m_body.group(3) + '</w:body></w:document>'
    open(doc_path, 'w', encoding='utf-8').write(new_doc)

    os.makedirs(os.path.join(tmp, 'word/media'), exist_ok=True)
    media_entries = []
    for i, (rid, png) in enumerate(images, 1):
        name = f'image{i}.png'
        shutil.copy(png, os.path.join(tmp, 'word/media', name))
        media_entries.append((rid, name))
    rels_path = os.path.join(tmp, 'word/_rels/document.xml.rels')
    rels = open(rels_path, encoding='utf-8').read()
    add = ''.join(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{name}"/>'
                  for rid, name in media_entries)
    add += ''.join(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="{html.escape(url)}" TargetMode="External"/>'
                   for url, rid in hyperlinks.items())
    open(rels_path, 'w', encoding='utf-8').write(rels.replace('</Relationships>', add + '</Relationships>'))
    ct_path = os.path.join(tmp, '[Content_Types].xml')
    ct = open(ct_path, encoding='utf-8').read()
    if 'Extension="png"' not in ct:
        ct = ct.replace('<Default Extension="xml"', '<Default Extension="png" ContentType="image/png"/><Default Extension="xml"')
    open(ct_path, 'w', encoding='utf-8').write(ct)
    # footer of the official template says "初赛大纲模板"; relabel for the final-round report
    for footer in Path(tmp, 'word').glob('footer*.xml'):
        f = footer.read_text(encoding='utf-8')
        f = f.replace('算法赛初赛大纲模板', esc(args.footer))
        footer.write_text(f, encoding='utf-8')
    # refresh core properties title/creator when present
    core = os.path.join(tmp, 'docProps/core.xml')
    if os.path.exists(core):
        c = open(core, encoding='utf-8').read()
        c = re.sub(r'<dc:title>.*?</dc:title>', f'<dc:title>{esc(args.title)}</dc:title>', c, flags=re.S)
        open(core, 'w', encoding='utf-8').write(c)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(tmp):
            for fn in files:
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, tmp))
    shutil.rmtree(tmp)
    print('wrote', out, out.stat().st_size, 'bytes;', len(media_entries), 'images;', len(hyperlinks), 'hyperlinks')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
