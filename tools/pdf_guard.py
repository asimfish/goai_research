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
6. 交付语言形态（--lang zh|en，或 --scope scope.md 自动读声明；都没给则沿用第 5 项的宽松口径）：
   zh 稿首页标签必须是「摘要」（出现英文 Abstract 即中文稿套了英文模板）、全文须有「参考文献」
   标签，且须嵌入真正的中文字族（Fandol / Noto CJK / Source Han / 思源 / 宋黑楷仿等），只靠
   Droid Sans Fallback / DejaVu 回退承载汉字 = FAIL（实跑：正式中文稿的 Abstract 标签、
   DroidSansFallback 正文全部放行）；en 稿首页须有 Abstract、全文须有 References/Bibliography。
告警：pdfinfo 缺 Title；页数与 --min-pages 不符。

用法：
  python3 tools/pdf_guard.py <main.pdf> [--tex main.tex] [--bib references.bib] [--min-pages 6]
                             [--lang zh|en] [--scope workspace/inputs/scope.md]
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
                        r"NotoSans(?!CJK|SC|TC|JP|KR|HK)|SegoeUI|Georgia|TimesNewRomanPS", re.I)
RE_NUMBERED_H1 = re.compile(r"^\s*1\.?\s+\S", re.M)   # 「1 Introduction」或「1. 引言」
# 中文稿必须嵌入的中文字族（ctex fontset=fandol / 思源 / 系统宋黑楷仿）；Droid Sans Fallback 与
# DejaVu 只是 fontspec 的回退字体，中文稿全文汉字落在回退字体上就是没配中文字族
CJK_FONTS = re.compile(r"Fandol|Noto(?:Sans|Serif)CJK|Noto(?:Sans|Serif)(?:SC|TC|JP|KR|HK)|SourceHan|"
                       r"SimSun|SimHei|SimKai|SimFang|STSong|STHeiti|STKaiti|STFangsong|PingFang|Hiragino|"
                       r"WenQuanYi|ARPL|AR PL|KaiTi|FangSong|Songti|Heiti|Adobe(?:Song|Heiti|Kaiti|Fangsong)|"
                       r"BabelStone|HanaMin|MicrosoftYaHei|YaHei|DengXian|LXGW|Sarasa", re.I)
CJK_FALLBACK_FONTS = re.compile(r"DroidSansFallback|DejaVu", re.I)
RE_LANG_SCOPE = re.compile(r"交付语言|delivery language", re.I)
RE_LANG_ZH = re.compile(r"中文|Chinese", re.I)


def scope_language(path: str | None) -> str | None:
    """从 scope.md 的「交付语言」声明读 zh/en（与 loopctl._scope_language 同口径）；无声明返回 None。"""
    if not path or not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if RE_LANG_SCOPE.search(line):
                return "zh" if RE_LANG_ZH.search(line) else "en"
    return None


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=120).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def check(pdf: str, tex: str | None, bib: str | None, min_pages: int,
          lang: str | None = None) -> tuple[list[str], list[str], dict]:
    blocking: list[str] = []
    warnings: list[str] = []
    meta: dict = {"lang": lang or "auto"}
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
    full = _run(["pdftotext", "-layout", pdf, "-"])
    has_abstract_en = bool(re.search(r"\bAbstract\b", first))
    has_abstract_zh = bool(re.search(r"摘\s*要", first))
    if lang == "zh":
        # 中文稿：标签必须本地化（ctexart 自动给 摘要/参考文献），英文 Abstract/References 就是套了英文模板
        if not has_abstract_zh:
            blocking.append("中文稿首页未见「摘要」标签" + ("（首页是英文 Abstract：中文稿套了英文模板，"
                            "改用 templates/survey_main_zh.tex 或 \\renewcommand{\\abstractname}{摘要}）"
                            if has_abstract_en else "——摘要块缺失或被排成正文"))
        if not re.search(r"^\s*参\s*考\s*文\s*献\s*$", full, re.M):
            blocking.append("中文稿全文未见「参考文献」标签" + ("（出现英文 References：须 "
                            "\\renewcommand{\\refname}{参考文献} 或改用 ctexart）"
                            if re.search(r"^\s*References\s*$", full, re.M) else "——参考文献区缺失"))
        if font_names and not any(CJK_FONTS.search(f) for f in font_names):
            fallback = sorted({f.split("+")[-1] for f in font_names if CJK_FALLBACK_FONTS.search(f)})
            blocking.append("中文稿未嵌入中文字族（Fandol/Noto CJK/Source Han/宋黑楷仿）"
                            + (f"，汉字全部落在回退字体 {fallback[:3]} 上" if fallback else "")
                            + "——用 ctexart fontset=fandol 或 \\setCJKmainfont 指定真正的中文字体")
    elif lang == "en":
        if not has_abstract_en:
            blocking.append("英文稿首页未见 Abstract 标签" + ("（首页是中文「摘要」：交付语言与 scope 声明不符）"
                            if has_abstract_zh else "——摘要块缺失或被排成正文"))
        if not re.search(r"^\s*(?:References|Bibliography)\s*$", full, re.M):
            blocking.append("英文稿全文未见 References/Bibliography 标签——参考文献区缺失")
    elif not (has_abstract_en or has_abstract_zh):
        blocking.append("首页未见 Abstract/摘要——摘要块缺失或被排成正文")
    if not RE_NUMBERED_H1.search(full):
        blocking.append("未匹配到编号一级标题（如『1 Introduction』/『1 引言』）——章节编号缺失")
    return blocking, warnings, meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--tex", default=None, help="main.tex（用于陈旧性比对）")
    ap.add_argument("--bib", default=None, help="references.bib（用于陈旧性比对）")
    ap.add_argument("--min-pages", type=int, default=6)
    ap.add_argument("--lang", choices=["auto", "zh", "en"], default="auto",
                    help="交付语言形态检查：zh 要求 摘要/参考文献 标签与中文字族，en 要求 Abstract/References；"
                         "auto = 从 --scope 读声明，无声明则只查 Abstract 或 摘要 任一")
    ap.add_argument("--scope", default=None, help="scope.md（auto 模式下读其「交付语言」声明）")
    args = ap.parse_args()
    for tool in ("pdfinfo", "pdffonts", "pdftotext"):
        if not shutil.which(tool):
            sys.exit(f"缺少 {tool}（poppler）：brew install poppler / apt install poppler-utils")
    lang = args.lang if args.lang != "auto" else scope_language(args.scope)
    blocking, warnings, meta = check(args.pdf, args.tex, args.bib, args.min_pages, lang)
    print(f"PDF: {args.pdf}  pages={meta.get('pages')}  lang={meta.get('lang')}  "
          f"producer=『{meta.get('producer', '')}』  creator=『{meta.get('creator', '')}』")
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
