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


def parse_inline(text: str, hyperlinks: dict[str, str]) -> str:
    text = text.replace('`', '')
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


def para_body(text: str, hyperlinks: dict[str, str], indent: bool = True) -> str:
    ind = '<w:ind w:left="173" w:firstLine="0"/>' if indent else ''
    return (f'<w:p><w:pPr><w:spacing w:after="100" w:line="300" w:lineRule="auto"/>{ind}</w:pPr>'
            + parse_inline(text, hyperlinks) + '</w:p>')


def para_caption(text: str) -> str:
    return ('<w:p><w:pPr><w:spacing w:before="20" w:after="160"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:rPr>{FONT}<w:b w:val="0"/><w:i w:val="0"/><w:color w:val="5A6573"/><w:sz w:val="18"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')


def para_heading(text: str, style: str) -> str:
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r><w:t>{esc(text)}</w:t></w:r></w:p>'


def para_head_block(title: str, subtitle: str, note: str) -> str:
    t = ('<w:p><w:pPr><w:spacing w:after="60"/><w:jc w:val="center"/></w:pPr>'
         f'<w:r><w:rPr>{FONT}<w:b/><w:color w:val="0B2545"/><w:sz w:val="40"/></w:rPr><w:t>{esc(title)}</w:t></w:r></w:p>')
    s = ('<w:p><w:pPr><w:spacing w:after="200"/><w:jc w:val="center"/></w:pPr>'
         f'<w:r><w:rPr>{FONT}<w:b w:val="0"/><w:color w:val="5A6573"/><w:sz w:val="21"/></w:rPr><w:t>{esc(subtitle)}</w:t></w:r></w:p>')
    n = ('<w:p><w:pPr><w:shd w:val="clear" w:fill="F4F6F9"/><w:spacing w:before="40" w:after="120"/></w:pPr>'
         f'<w:r><w:rPr>{FONT}<w:b/><w:color w:val="1F4D78"/><w:sz w:val="19"/></w:rPr><w:t>说明：</w:t></w:r>'
         f'<w:r><w:rPr>{FONT}<w:b w:val="0"/><w:color w:val="0B2545"/><w:sz w:val="19"/></w:rPr><w:t xml:space="preserve">{esc(note)}</w:t></w:r></w:p>')
    return t + s + n


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
    return ('<w:p><w:pPr><w:spacing w:before="80" w:after="40"/><w:jc w:val="center"/></w:pPr>'
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


def build_table(rows: list[list[str]], hyperlinks: dict[str, str]) -> str:
    ncol = max(len(r) for r in rows)
    rows = [r + [''] * (ncol - len(r)) for r in rows]
    weights = [max(max(len(r[c]) for r in rows), 6) + 4 for c in range(ncol)]
    total = sum(weights)
    widths = [int(CONTENT_W_TWIP * w / total) for w in weights]
    widths[-1] = CONTENT_W_TWIP - sum(widths[:-1])
    grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    bd = '<w:tblBorders>' + ''.join(
        f'<w:{side} w:val="single" w:sz="4" w:color="A6A6A6"/>'
        for side in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV')) + '</w:tblBorders>'
    xml = [f'<w:tbl><w:tblPr><w:tblW w:w="{CONTENT_W_TWIP}" w:type="dxa"/>{bd}'
           '<w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid>' + grid + '</w:tblGrid>']
    for ri, row in enumerate(rows):
        xml.append('<w:tr>')
        for ci, cell in enumerate(row):
            shd = '<w:shd w:val="clear" w:fill="F4F6F9"/>' if ri == 0 else ''
            inline = parse_inline(('**' + cell + '**') if ri == 0 and '**' not in cell else cell, hyperlinks)
            inline = inline.replace('<w:sz w:val="21"/>', '<w:sz w:val="18"/>')
            xml.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[ci]}" w:type="dxa"/>{shd}<w:vAlign w:val="center"/></w:tcPr>'
                       '<w:p><w:pPr><w:spacing w:before="30" w:after="30"/></w:pPr>' + inline + '</w:p></w:tc>')
        xml.append('</w:tr>')
    xml.append('</w:tbl><w:p><w:pPr><w:spacing w:after="60"/></w:pPr></w:p>')
    return ''.join(xml)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--md', required=True)
    ap.add_argument('--template', default='templates/official_ai4r_report_template.docx')
    ap.add_argument('--out', required=True)
    ap.add_argument('--title', default='AI for Research赛道｜算法赛复赛报告')
    ap.add_argument('--subtitle', default='复赛提交：方案说明 PPT + 复赛报告（初赛问题定义文档加强版）')
    ap.add_argument('--note', default='本报告为初赛问题定义文档的加强版；其中每个主要结论、图与指标均可追溯到提交包中的代码版本、配置、数据、运行日志/Agent 轨迹与结果文件（见 docs/competition/SUBMISSION.md）。')
    ap.add_argument('--pagebreak-before', default='三、,五、', help='comma-separated heading-1 prefixes that start a new page')
    ap.add_argument('--footer', default='算法赛复赛报告 · SAGE-Mat', help='text replacing the template footer label')
    args = ap.parse_args()

    md_lines = Path(args.md).read_text(encoding='utf-8').split('\n')
    breaks = tuple(x for x in args.pagebreak_before.split(',') if x)
    hyperlinks: dict[str, str] = {}
    body: list[str] = [para_head_block(args.title, args.subtitle, args.note)]
    images: list[tuple[str, Path]] = []
    docpr = 100
    table_buf: list[str] = []

    def flush_table() -> None:
        nonlocal table_buf
        if table_buf:
            rows = [[c.strip() for c in ln.strip().strip('|').split('|')] for ln in table_buf]
            rows = [r for r in rows if not all(re.fullmatch(r':?-+:?', c) for c in r)]
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
        if s.startswith('- '):
            body.append(para_body('• ' + s[2:], hyperlinks))
            continue
        if re.match(r'^\d+\. ', s):
            body.append(para_body(s, hyperlinks))
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
