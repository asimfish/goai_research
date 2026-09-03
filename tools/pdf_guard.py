#!/usr/bin/env python3
"""pdf_guard —— 终稿 PDF 来源与形态闸门（确定性，依赖 poppler 的 pdfinfo/pdffonts/pdftotext）。

背景：实跑中测试机没有 TeX，agent 用 groff/Ghostscript 与 HTML→HeadlessChrome 渲染出
「PDF」，摘要/编号标题/公式/表格/蓝色引用全部走样，而账本仍记 PASS。tex_guard 只查
.tex 源码，没人查 main.pdf 是不是 TeX 从模板编译出来的——本工具补这一道。

检查项（阻塞）：
1. 文件存在、非空、pdfinfo 可解析、页数 ≥ 1
2. Producer/Creator 必须来自 TeX 引擎（xdvipdfmx / XeTeX / pdfTeX / LuaTeX / dvipdfmx）；
   出现 Skia、Chrome、Chromium、Ghostscript、groff、wkhtmltopdf、Word、LibreOffice、
   ReportLab、WeasyPrint、Prince、cairo 即 FAIL
3. 嵌入字体：须含模板字体族（TeX Gyre Termes / NewTX / TXTT / Fandol / CM）；
   出现 DejaVu / Arial / Liberation / Helvetica-as-body / Times New Roman(系统) 即 FAIL
4. main.pdf 不得早于 main.tex 与 references.bib（陈旧产物）
5. 首页文本含 Abstract 或 摘要；全文能匹配到编号一级标题（如 "1 Introduction"/"1 引言"）
告警：pdfinfo 缺 Title；页数与 --min-pages 不符。

用法：
  python3 tools/pdf_guard.py <main.pdf> [--tex main.tex] [--bib references.bib] [--min-pages 6]
退出码：0 = PASS；1 = FAIL；2 = 工具缺失（poppler 未安装）
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys

TEX_PRODUCERS = re.compile(r"xdvipdfmx|xetex|pdftex|luatex|luahbtex|dvipdfmx|dvips|tex live|miktex", re.I)
FAKE_PRODUCERS = re.compile(
    r"skia|chrome|chromium|ghostscript|groff|wkhtmltopdf|microsoft|word|libreoffice|openoffice|"
    r"reportlab|weasyprint|prince|cairo|pandoc|quartz|pdfkit|puppeteer|playwright", re.I)
TEMPLATE_FONTS = re.compile(r"TeXGyreTermes|NewTX|TXTT|txsy|txmia|Fandol|CMR|CMMI|CMSY|LMRoman|"
                            r"TeX-Gyre|Termes|NimbusRom|NimbusMon|ntx", re.I)
FAKE_FONTS = re.compile(r"DejaVu|ArialMT|Arial-|LiberationS|Calibri|Cambria|Verdana|Roboto|"
                        r"NotoSans|SegoeUI|Georgia|TimesNewRomanPS", re.I)
RE_NUMBERED_H1 = re.compile(r"^\s*1\.?\s+\S", re.M)   # 「1 Introduction」或「1. 引言」


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=120).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def check(pdf: str, tex: str | None, bib: str | None, min_pages: int) -> tuple[list[str], list[str], dict]:
    blocking: list[str] = []
    warnings: list[str] = []
    meta: dict = {}
    if not os.path.isfile(pdf) or os.path.getsize(pdf) == 0:
        return [f"PDF 不存在或为空: {pdf}"], warnings, meta
    info = _run(["pdfinfo", pdf])
    if not info.strip():
        return [f"pdfinfo 无法解析: {pdf}"], warnings, meta
    fields = {k.strip(): v.strip() for k, _, v in (ln.partition(":") for ln in info.splitlines()) if k}
    meta["producer"] = fields.get("Producer", "")
    meta["creator"] = fields.get("Creator", "")
    meta["pages"] = int(fields.get("Pages", "0") or 0)
    meta["title"] = fields.get("Title", "")
    if meta["pages"] < 1:
        blocking.append("页数为 0")
    elif meta["pages"] < min_pages:
        warnings.append(f"页数 {meta['pages']} 低于 --min-pages {min_pages}")
    if not meta["title"]:
        warnings.append("pdfinfo 缺 Title（hyperref 未写入 pdftitle）")

    prov = f"{meta['producer']} {meta['creator']}"
    if FAKE_PRODUCERS.search(prov) or not TEX_PRODUCERS.search(prov):
        blocking.append(
            f"PDF 不是 TeX 引擎产出: Producer=『{meta['producer']}』 Creator=『{meta['creator']}』"
            "——终稿只能由 xelatex/pdflatex 从 templates/survey_main*.tex 编译；"
            "缺 TeX 环境时 draft_complete 记 FAIL 并如实汇报『PDF 未编译』，禁止用回退渲染器冒充")

    fonts = _run(["pdffonts", pdf])
    font_names = [ln.split()[0] for ln in fonts.splitlines()[2:] if ln.strip()]
    meta["fonts"] = font_names[:12]
    if font_names:
        has_template = any(TEMPLATE_FONTS.search(f) for f in font_names)
        fakes = sorted({f for f in font_names if FAKE_FONTS.search(f)})
        if not has_template:
            blocking.append(f"未发现模板字体族（NewTX/TeX Gyre Termes/Fandol/CM）: {font_names[:6]}")
            if fakes:
                blocking.append(f"出现非模板正文字体 {fakes[:6]}（HTML/Office 渲染的典型痕迹）")
        elif fakes:
            # 真 TeX 产物里的 DejaVu/Arial 通常是 fontspec 对个别字形（下标数字、箭头）的
            # 回退，不是伪造信号；提醒补 \setmainfont 的 fallback 或改用模板字体覆盖的写法
            warnings.append(f"模板字体之外出现回退字体 {fakes[:4]}——个别字形（下标/箭头/CJK）落到系统字体，"
                            "建议在 figspec/正文里改用模板字体覆盖的记法或配置 fontspec 回退链")

    for src in (tex, bib):
        if src and os.path.isfile(src) and os.path.getmtime(src) > os.path.getmtime(pdf) + 1:
            blocking.append(f"{os.path.basename(src)} 比 PDF 新——PDF 是陈旧产物，需重新编译")

    first = _run(["pdftotext", "-f", "1", "-l", "1", "-layout", pdf, "-"])
    if not re.search(r"\bAbstract\b|摘\s*要", first):
        blocking.append("首页未见 Abstract/摘要——摘要块缺失或被排成正文")
    full = _run(["pdftotext", "-layout", pdf, "-"])
    if not RE_NUMBERED_H1.search(full):
        blocking.append("未匹配到编号一级标题（如『1 Introduction』/『1 引言』）——章节编号缺失")
    return blocking, warnings, meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--tex", default=None, help="main.tex（用于陈旧性比对）")
    ap.add_argument("--bib", default=None, help="references.bib（用于陈旧性比对）")
    ap.add_argument("--min-pages", type=int, default=6)
    args = ap.parse_args()
    for tool in ("pdfinfo", "pdffonts", "pdftotext"):
        if not shutil.which(tool):
            sys.exit(f"缺少 {tool}（poppler）：brew install poppler / apt install poppler-utils")
    blocking, warnings, meta = check(args.pdf, args.tex, args.bib, args.min_pages)
    print(f"PDF: {args.pdf}  pages={meta.get('pages')}  producer=『{meta.get('producer', '')}』  "
          f"creator=『{meta.get('creator', '')}』")
    if meta.get("fonts"):
        print(f"fonts: {', '.join(meta['fonts'][:8])}{' …' if len(meta['fonts']) > 8 else ''}")
    if blocking:
        print(f"\n[阻塞] {len(blocking)} 项:")
        for b in blocking:
            print(f"  - {b}")
    if warnings:
        print(f"\n[告警] {len(warnings)} 项:")
        for w in warnings:
            print(f"  - {w}")
    print("\n结论:", "FAIL" if blocking else "PASS")
    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
