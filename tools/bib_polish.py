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
5. 固溶体式整体保护：Ba1-xSrxZn2Si2O7 / BaZn2−xCoxSi2O7 这类以连字/减号串起的化学式先作为
   一个 token 加下标并加 {}（{Ba$_{1-x}$Sr$_x$Zn$_2$Si$_2$O$_7$}），再走元素前缀规则——
   出货稿里 Ba1- 被 plainnat 压成小写 ba1-。
6. author/title 先做 NFKC 归一（全角/合字/上标数字）；拉丁词里混入的西里尔/希腊同形字母
   （出货稿：「А. Yu. Tsivadze」的 А 是 U+0410，Times 字族排不出、印成缺字）记入 warnings，
   --strict 时非零退出。只报不改：改哪个字母要人看。

用法：
  python3 tools/bib_polish.py references.bib            # 只打印将做的修改（dry run）
  python3 tools/bib_polish.py references.bib --write    # 原地重写（先备份 .bak）
  python3 tools/bib_polish.py references.bib --strict   # 有同形字母告警即退出 1
退出码：0；--strict 且有告警 = 1。输出经 server.core.bibtex.format_entry 统一格式化。
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import unicodedata

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
# 前面是 $ 的字母段已在下标化学式（Zn$_2$SiGeO$_7$ 的 SiGeO）内，不再单独包裹
RE_PROTECT = re.compile(
    r"(?<![\w.{$])(?=[\w.]*[A-Z][\w.]*[A-Z])(?=[\w.]*\d)[\w()\[\]+.]*[A-Za-z0-9](?![\w])"
    r"|(?<![\w.{$])[A-Z]{2,}\d*(?![\w])"
    r"|(?<![\w.{$])(?:[A-Z][a-z]?){2,4}(?![\w])")
# 元素符号作连字前缀：Al-substituted / Ta-doped / Ga-doped
RE_ELEMENT_PREFIX = re.compile(rf"(?<![\w{{])({ELEMENTS})(?=[-\u2010\u2011\u2013]{{1,2}}[A-Za-z{{])")   # Al-substituted / Al-LLZO / Li-ion
# 连字/短横后的单元素符号：Y--Si--O oxides 的尾 O、Ba–Zn–Si 的 Si
RE_ELEMENT_SUFFIX = re.compile(rf"(?<=[-\u2010\u2011\u2013])({ELEMENTS})(?![\w}}$])")
RE_BRACED = re.compile(r"\{(?:[^{}]|\{[^{}]*\})*\}")   # 允许一层嵌套：{BaO-YO$_{1.5}$}
# 化学式内「元素/括号后紧跟的数字」→ 下标：SiO2 → SiO$_2$，YO1.5 → YO$_{1.5}$；
# 已含 $ 或 _ 的片段不再处理；单段数字 >3 位（H2020 之类）视为非化学式跳过
RE_FORMULA_TOKEN = re.compile(rf"(?<![\w.{{$_])(?=[\w.()\[\]]*(?:{ELEMENTS})\d)[A-Za-z0-9().\[\]]*[A-Za-z0-9)\]](?![\w$_])")
RE_SUBSCRIPT_DIGITS = re.compile(r"(?<=[A-Za-z)\]])(\d{1,3}(?:\.\d{1,2})?)(?![\d.])")
# 专有名词与大小写卫生
PROPER_NOUNS = ("Rietveld", "Raman", "Fourier", "Bragg", "Debye", "Scherrer", "Pauling", "Kelvin", "Ostwald",
                "Gibbs", "Arrhenius", "Curie", "Nernst", "Kröger", "Vink", "Le Bail", "Pawley")
RE_XRAY = re.compile(r"(?<![\w{])[xX]-ray(?![\w}])")
RE_ALLCAPS_LAST = re.compile(r"^[A-Z][A-Z' -]{1,}$")


def _subscript_formulas(title: str) -> str:
    def fix(m):
        tok = m.group(0)
        if re.search(r"\d{4,}", tok) or "$" in tok or "_" in tok:
            return tok
        # 至少一个「元素+数字」才算化学式（避免 3D、V2 之类）
        if not re.search(rf"(?:{ELEMENTS})\d", tok):
            return tok
        sub = RE_SUBSCRIPT_DIGITS.sub(lambda d: "$_{" + d.group(1) + "}$" if len(d.group(1)) > 1 else "$_" + d.group(1) + "$", tok)
        # 整个化学式加花括号：plainnat 会把未保护的 La/Zr 压成小写
        return "{" + sub + "}" if sub != tok else tok
    return RE_FORMULA_TOKEN.sub(fix, title)


_ELEMENT_LIST = sorted(ELEMENTS.split("|"), key=len, reverse=True)


def _recase_formula(token: str) -> str:
    """全大写/全小写的化学式 token（须含数字）→ 元素符号规范大小写：SIO2 → SiO2，la9.33si6o26 → La9.33Si6O26。"""
    if not re.search(r"\d", token):
        return token
    out, i, s = [], 0, token
    while i < len(s):
        ch = s[i]
        if not ch.isalpha():
            out.append(ch); i += 1; continue
        hit = None
        for el in _ELEMENT_LIST:
            if s[i:i + len(el)].lower() == el.lower():
                hit = el; break
        if hit is None:
            return token          # 不是纯化学式，保持原样
        out.append(hit); i += len(hit)
    return "".join(out)


RE_MATH = re.compile(r"\$[^$]*\$")
RE_BRACED_WORD = re.compile(r"\{([A-Z][A-Z0-9-]*)\}")


def _title_case_hygiene(title: str) -> str:
    """全大写标题 → 句首大写（数学段不动，逐词花括号先拆掉）；x-ray → {X}-ray；专有名词保护。"""
    prose = RE_MATH.sub(" ", title)                      # 只用数学段以外的字母判断是否全大写
    letters = [c for c in prose if c.isalpha()]
    if len(letters) >= 12 and sum(c.isupper() for c in letters) / len(letters) > 0.7:
        holes: list[str] = []

        def stash(m):
            holes.append(m.group(0))
            return f"\x01{len(holes) - 1}\x01"

        work = RE_BRACED_WORD.sub(r"\1", title)         # {CRYSTAL} {CHEMISTRY} → CRYSTAL CHEMISTRY
        work = RE_MATH.sub(stash, work)                   # 先收数学段（内含花括号），再收其余保护片段
        work = RE_BRACED.sub(stash, work)
        low = work.lower()
        # 含数字的 token 按元素符号重新大小写（Y2O3-SIO2 → Y2O3-SiO2），其余小写
        low = re.sub(r"[A-Za-z0-9.()\[\]]+", lambda m: _recase_formula(m.group(0)), low)
        while re.search(r"\x01\d+\x01", low):
            low = re.sub(r"\x01(\d+)\x01", lambda m: holes[int(m.group(1))], low)
        title = low[0].upper() + low[1:]
    title = RE_XRAY.sub("{X}-ray", title)
    for noun in PROPER_NOUNS:
        title = re.sub(rf"(?<![\w{{])({re.escape(noun.lower())})(?![\w}}])", "{" + noun + "}", title)
        title = re.sub(rf"(?<![\w{{])({re.escape(noun)})(?![\w}}])", "{" + noun + "}", title)
    return title


def _author_case(author: str) -> str:
    """DOE, John → Doe, John（整段全大写的姓才动；带 {} 保护的不动）。"""
    parts = [a.strip() for a in re.split(r"\s+and\s+", author)]
    fixed = []
    for a in parts:
        if "," in a and "{" not in a:
            last, first = a.split(",", 1)
            if RE_ALLCAPS_LAST.match(last.strip()) and len(last.strip()) > 1:
                last = " ".join(w[:1] + w[1:].lower() if "-" not in w else "-".join(x[:1] + x[1:].lower() for x in w.split("-"))
                                for w in last.strip().split())
                a = f"{last}, {first.strip()}"
        fixed.append(a)
    return " and ".join(fixed)


def _protect_title(title: str) -> str:
    # 已保护片段先占位，避免重复包裹
    holes: list[str] = []

    def stash_text(s: str) -> str:
        holes.append(s)
        return f"\x00{len(holes) - 1}\x00"

    def stash(m):
        return stash_text(m.group(0))

    title = _title_case_hygiene(title)
    title = RE_MISSPLIT.sub(_merge_missplit, title)      # 先把拆错的化学式合回一个 token
    work = RE_BRACED.sub(stash, title)
    # 固溶体式整体转写并占位：否则元素前缀/下标规则会把 Ba1-xSr… 拆成 {Ba$_1$}-{xSr…}
    work = RE_SOLID_SOLUTION.sub(lambda m: stash_text(_chain_to_tex(m.group(0))), work)
    work = RE_SPACED_FORMULA.sub(lambda m: m.group(0).replace(" ", ""), work)
    work = _subscript_formulas(work)
    work = RE_ELEMENT_PREFIX.sub(lambda m: "{" + m.group(1) + "}", work)
    work = RE_ELEMENT_SUFFIX.sub(lambda m: "{" + m.group(1) + "}", work)
    work = RE_PROTECT.sub(lambda m: "{" + m.group(0) + "}", work)
    work = re.sub(r"\x00(\d+)\x00", lambda m: holes[int(m.group(1))], work)
    return RE_BRACED.sub(_subscript_inside_braces, work)


RE_HYPHEN_FORMULA_CHAIN = re.compile(rf"^(?:(?:{ELEMENTS})\d*(?:\.\d+)?)+(?:[-\u2010\u2011\u2013]+(?:(?:{ELEMENTS})\d*(?:\.\d+)?)+)*$")
# 固溶体式：元素 + 计量数，计量数可带「-x」「+δ」尾巴，或元素直接跟 x/y/z/δ；整体须含
# 「数字-x」签名（Ba1-x、Zn2−x），避免吞掉年份区间与普通连字词
_SUB_DASH = r"[-\u2212\u2010\u2011\u2013+]"
_VAR = r"[xyz\u03b4]"
RE_SOLID_SOLUTION = re.compile(
    rf"(?<![\w.{{$_])(?=[A-Za-z0-9.]*\d{_SUB_DASH}{_VAR})"
    rf"(?:(?:{ELEMENTS})(?:\d+(?:\.\d+)?(?:{_SUB_DASH}{_VAR})?|{_VAR})?)+(?![\w$_])")
RE_CHAIN_PART = re.compile(rf"({ELEMENTS})(\d+(?:\.\d+)?(?:{_SUB_DASH}{_VAR})?|{_VAR})?")
# 早期 hygiene（bib_guard --fix-hygiene）把化学式拆错的形态：Ba1−{xSrxZn2Si2O7}、Ba0.5Sr0.{5Zn2SiGeO7}
# ——花括号外的 Ba1− 被 plainnat 压成 ba1−。合并条件：拼回去后整段是纯化学式语法
RE_MISSPLIT = re.compile(
    rf"(?<![\w{{$_])([A-Za-z][A-Za-z0-9.]*(?:[0-9.]|{_SUB_DASH}))\{{([A-Za-z0-9.]+(?:{_SUB_DASH}[A-Za-z0-9.]+)*)\}}(?![\w$_])"
    rf"|(?<![\w{{$_])\{{([A-Za-z][A-Za-z0-9.]*)\}}({_SUB_DASH})\{{([A-Za-z0-9.]+(?:{_SUB_DASH}[A-Za-z0-9.]+)*)\}}(?![\w$_])")
RE_FORMULA_GRAMMAR = re.compile(
    rf"^(?:(?:{ELEMENTS})(?:\d+(?:\.\d+)?(?:{_SUB_DASH}{_VAR})?|{_VAR})?|{_SUB_DASH})+$")


def _merge_missplit(m: "re.Match[str]") -> str:
    merged = (m.group(1) + m.group(2)) if m.group(1) is not None else (m.group(3) + m.group(4) + m.group(5))
    if RE_FORMULA_GRAMMAR.match(merged) and re.search(rf"(?:{ELEMENTS})\d", merged) \
            and not re.search(r"\d{4,}", merged):
        return merged
    return m.group(0)


def _chain_to_tex(tok: str) -> str:
    """Ba1-xSrxZn2Si2O7 → {Ba$_{1-x}$Sr$_x$Zn$_2$Si$_2$O$_7$}（减号统一为 ASCII，避免缺字）。"""
    out = []
    for m in RE_CHAIN_PART.finditer(tok):
        el, sub = m.group(1), m.group(2) or ""
        sub = re.sub(_SUB_DASH.replace("+", ""), "-", sub)
        if not sub:
            out.append(el)
        elif len(sub) == 1:
            out.append(f"{el}$_{sub}$")
        else:
            out.append(f"{el}$_{{{sub}}}$")
    return "{" + "".join(out) + "}"


# 与拉丁字母同形的西里尔/希腊字母（U+0410 А 与 A 肉眼无别，但 Times 字族没有该字形）
CONFUSABLES = {
    "\u0410": "A", "\u0412": "B", "\u0421": "C", "\u0415": "E", "\u041d": "H", "\u041a": "K",
    "\u041c": "M", "\u041e": "O", "\u0420": "P", "\u0422": "T", "\u0425": "X", "\u0430": "a",
    "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0441": "c", "\u0443": "y", "\u0445": "x",
    "\u0456": "i", "\u0458": "j", "\u0455": "s",
    "\u0391": "A", "\u0392": "B", "\u0395": "E", "\u0396": "Z", "\u0397": "H", "\u0399": "I",
    "\u039a": "K", "\u039c": "M", "\u039d": "N", "\u039f": "O", "\u03a1": "P", "\u03a4": "T",
    "\u03a5": "Y", "\u03a7": "X", "\u03bf": "o",
}
RE_LETTER_WORD = re.compile(r"[^\W\d_]+")


def _is_cyr_greek(ch: str) -> bool:
    name = unicodedata.name(ch, "")
    return name.startswith(("CYRILLIC", "GREEK"))


def confusable_warnings(key: str, fld: str, value: str) -> list[str]:
    """拉丁文本里混入的同形西里尔/希腊字母 → 告警。

    按段判断（author 按 and 拆成单个人名，title 整段）：段内除同形字母外没有别的西里尔/
    希腊字母，或同形字母与拉丁字母同在一个词里，才算混入；整段西里尔的真俄文名、α-相不报。
    """
    if not any(ch in CONFUSABLES for ch in value):
        return []
    segments = re.split(r"\s+and\s+", value) if fld == "author" else [value]
    out = []
    for seg in segments:
        seg_otherwise_latin = not any(_is_cyr_greek(ch) and ch not in CONFUSABLES for ch in seg)
        for word in RE_LETTER_WORD.findall(seg):
            bad = [ch for ch in word if ch in CONFUSABLES]
            if not bad:
                continue
            has_latin = any("a" <= ch.lower() <= "z" for ch in word)
            if has_latin or seg_otherwise_latin:
                ch = bad[0]
                out.append(f"{key}: {fld} 的『{word}』含同形异码字母 {ch!r} (U+{ord(ch):04X} "
                           f"{unicodedata.name(ch, '?')})——应为拉丁字母 {CONFUSABLES[ch]!r}；"
                           "Times 字族排不出该字形，PDF 里是缺字")
    return out


def _subscript_inside_braces(m: "re.Match[str]") -> str:
    """已加保护的 {ZnO-MgO-SiO2} / {BaO-YO1.5} 这类系统名，下标同样要补（无 $ 才处理）。"""
    inner = m.group(0)[1:-1]
    if "$" in inner or "_" in inner or "{" in inner or not re.search(r"\d", inner):
        return m.group(0)
    if not RE_HYPHEN_FORMULA_CHAIN.match(inner) or re.search(r"\d{4,}", inner):
        return m.group(0)
    return "{" + RE_SUBSCRIPT_DIGITS.sub(lambda d: "$_{" + d.group(1) + "}$" if len(d.group(1)) > 1 else "$_" + d.group(1) + "$", inner) + "}"


def polish(text: str, warnings: list[str] | None = None) -> tuple[str, list[str]]:
    """→ (新文本, 修改清单)；传入 warnings 列表可收集只报不改的问题（同形字母）。"""
    entries = parse_bibtex(text)
    changes: list[str] = []
    out = []
    for e in entries:
        f = dict(e["fields"])
        # 6. NFKC：全角括号/合字/上标数字/不换行空格归一；同形字母只报不改
        for fld in ("author", "title"):
            v = f.get(fld, "")
            if v:
                nv = unicodedata.normalize("NFKC", v)
                if nv != v:
                    f[fld] = nv
                    changes.append(f"{e['key']}: {fld} NFKC 归一")
                if warnings is not None:
                    warnings.extend(confusable_warnings(e["key"], fld, f[fld]))
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
        author = f.get("author", "")
        if author:
            new_author = _author_case(author)
            if new_author != author:
                f["author"] = new_author
                changes.append(f"{e['key']}: author 全大写姓 → {new_author[:60]}")
        out.append(format_entry(e["key"], e["entry_type"], f))
    return "\n\n".join(out) + "\n", changes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bib")
    ap.add_argument("--write", action="store_true", help="原地重写（先备份为 .bak）")
    ap.add_argument("--strict", action="store_true", help="有同形字母等告警时退出 1")
    args = ap.parse_args()
    text = open(args.bib, encoding="utf-8").read()
    warnings: list[str] = []
    new_text, changes = polish(text, warnings)
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
    if warnings:
        print(f"\n[告警] {len(warnings)} 项（只报不改）:")
        for w in warnings[:40]:
            print("  -", w)
        if args.strict:
            sys.exit(1)


if __name__ == "__main__":
    main()
