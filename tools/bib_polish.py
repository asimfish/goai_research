#!/usr/bin/env python3
"""bib_polish —— 参考文献库确定性清理（bib_guard 卫生告警的修复器）。

四件事，全部可逆、不碰语义：
1. doi 与 url 同存 → 删 url（doi.org 链接是重复，Semantic Scholar 等落地页只是 DOI
   的二级入口）。正文已通过 hyperref 链接 DOI，重复的长 URL 是参考文献区最难看的伤。
2. title 里被元数据源拆散的化学式「Li 7 La 3 Zr 2 O 12」→「Li7La3Zr2O12」
   （仅匹配「元素符号 空格 数字」连续 ≥2 段的序列，不碰年份与普通数字）。
3. title 里需要大小写保护的 token 加 {}：含 ≥2 大写字母且含数字的化学式
   （Li7La3Zr2O12、BaZn2Si2O7）、≥2 字母全大写缩写（LLZO、XRD、COF）、
   元素符号作前缀的连字词（Al-substituted → {Al}-substituted、c-LLZO → c-{LLZO}）。
   已在 {} 内的内容不重复处理。plainnat 等样式会把未保护 token 压成小写甚至
   拆成「li 7 la 3 zr 2 o 12」。
4. title/journal/booktitle 等文本字段里的裸 & → \\&（否则 LaTeX 报 Misplaced alignment tab）。

用法：
  python3 tools/bib_polish.py references.bib            # 只打印将做的修改（dry run）
  python3 tools/bib_polish.py references.bib --write    # 原地重写（先备份 .bak）
退出码：0。输出经 server.core.bibtex.format_entry 统一格式化（与 export_bibtex 同路径）。
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server.core.bibtex import format_entry, parse_bibtex  # noqa: E402

ELEMENTS = ("He|Li|Be|Ne|Na|Mg|Al|Si|Cl|Ar|Ca|Sc|Ti|Cr|Mn|Fe|Co|Ni|Cu|Zn|Ga|Ge|As|Se|Br|Kr|"
            "Rb|Sr|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Sb|Te|Xe|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|"
            "Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|At|Rn|Fr|Ra|Ac|Th|Pa|"
            "Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr|H|B|C|N|O|F|P|S|K|V|Y|I|W|U")
# 「Li 7 La 3 Zr 2 O 12」：元素 + 空格 + 数字，连续 ≥2 段
RE_SPACED_FORMULA = re.compile(
    rf"\b(?:{ELEMENTS}) \d+(?:\.\d+)?(?: (?:{ELEMENTS}) \d+(?:\.\d+)?)+\b")   # 段间单空格，不吞尾部空格
# 需保护的 token（token 可含小数点，如 Li6.25La3Zr2Al0.25O12，故边界用 lookaround 而非 \b）：
#  a) ≥2 大写且含数字的化学式；b) ≥2 字母全大写缩写（可带数字尾）；
#  c) 2–4 个元素符号拼成的无数字化合物（AlN、NaCl、GaAs）
RE_PROTECT = re.compile(
    r"(?<![\w.{])(?=[\w.]*[A-Z][\w.]*[A-Z])(?=[\w.]*\d)[\w()\[\]+.]*[A-Za-z0-9](?![\w])"
    r"|(?<![\w.{])[A-Z]{2,}\d*(?![\w])"
    r"|(?<![\w.{])(?:[A-Z][a-z]?){2,4}(?![\w])")
# 元素符号作连字前缀：Al-substituted / Ta-doped / Ga-doped
RE_ELEMENT_PREFIX = re.compile(rf"(?<![\w{{])({ELEMENTS})(?=[-\u2010\u2011\u2013][A-Za-z])")   # Al-substituted / Al-LLZO / Li-ion
RE_BRACED = re.compile(r"\{[^{}]*\}")


def _protect_title(title: str) -> str:
    # 已保护片段先占位，避免重复包裹
    holes: list[str] = []

    def stash(m):
        holes.append(m.group(0))
        return f"\x00{len(holes) - 1}\x00"

    work = RE_BRACED.sub(stash, title)
    work = RE_SPACED_FORMULA.sub(lambda m: m.group(0).replace(" ", ""), work)
    work = RE_ELEMENT_PREFIX.sub(lambda m: "{" + m.group(1) + "}", work)
    work = RE_PROTECT.sub(lambda m: "{" + m.group(0) + "}", work)
    return re.sub(r"\x00(\d+)\x00", lambda m: holes[int(m.group(1))], work)


def polish(text: str) -> tuple[str, list[str]]:
    entries = parse_bibtex(text)
    changes: list[str] = []
    out = []
    for e in entries:
        f = dict(e["fields"])
        doi, url = f.get("doi", ""), f.get("url", "")
        if doi and url:
            # 有 DOI 就不再需要 url：doi.org 链接是重复，Semantic Scholar/出版社落地页
            # 也只是 DOI 的二级入口；正文已通过 hyperref 链接 DOI
            f.pop("url")
            changes.append(f"{e['key']}: 删除 url（已有 doi）")
        # 4. 文本字段里的裸 & → \&（BibTeX 原样输出，LaTeX 会报 Misplaced alignment tab）
        for fld in ("title", "journal", "booktitle", "publisher", "note"):
            v = f.get(fld, "")
            if v and re.search(r"(?<!\\)&", v):
                f[fld] = re.sub(r"(?<!\\)&", r"\\&", v)
                changes.append(f"{e['key']}: {fld} 裸 & → \\&")
        title = f.get("title", "")
        if title:
            new_title = _protect_title(title)
            if new_title != title:
                f["title"] = new_title
                changes.append(f"{e['key']}: title → {new_title[:90]}")
        out.append(format_entry(e["key"], e["entry_type"], f))
    return "\n\n".join(out) + "\n", changes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bib")
    ap.add_argument("--write", action="store_true", help="原地重写（先备份为 .bak）")
    args = ap.parse_args()
    text = open(args.bib, encoding="utf-8").read()
    new_text, changes = polish(text)
    print(f"{args.bib}: {len(changes)} 处修改")
    for c in changes[:40]:
        print("  -", c)
    if len(changes) > 40:
        print(f"  … 另 {len(changes) - 40} 处")
    if args.write and changes:
        shutil.copyfile(args.bib, args.bib + ".bak")
        with open(args.bib, "w", encoding="utf-8") as fh:
            fh.write(new_text)
        print(f"已写回 {args.bib}（备份 {args.bib}.bak）")


if __name__ == "__main__":
    main()
