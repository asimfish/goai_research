#!/usr/bin/env python3
"""tex_guard —— 组稿完整性确定性闸门（离线，零依赖）。

检查项（均忽略 % 注释掉的内容）：
1. TODO/FIXME 占位残留（模板里的 TODO 标题/作者/摘要必须已替换）＝阻塞
2. \\input 目标文件存在 ＝阻塞
3. \\includegraphics / \\includesvg 目标文件存在（自动尝试常见扩展名）＝阻塞
4. \\ref / \\autoref / \\cref 无悬空（有对应 \\label）＝阻塞
5. \\begin/\\end 环境闭合 ＝阻塞
6. 花括号平衡 ＝告警（verbatim 等场景可能误报）
7. BibTeX key 泄漏到正文（形如 lin1999phase 的裸 key 出现在读者可见文本，
   引用必须走 \\cite）＝阻塞
8. \\texttt 密度过高（正文大量打字机体是内部术语泄漏的信号）＝告警
9. 中文稿套英文模板（CJK 占比高但 documentclass 非 ctex 系，Abstract/
   Table 等标签会是英文）＝告警
10. 竖版密表：≥6 列且有长单元格（CJK 计 2 单位，> 40 单位）或 ≥8 列的竖版
    tabular/longtable ＝阻塞（转横版 landscape/sidewaystable、拆表或合并列；
    实跑中 7 列 P{0.12\textwidth} 的中文条件表把每行挤成 4–5 个字）

用法：
  python3 tools/tex_guard.py <draft_dir_or_main.tex>
退出码：0 = PASS；1 = 存在阻塞问题。
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

RE_TODO = re.compile(r"\b(TODO|FIXME)\b")
RE_INPUT = re.compile(r"\\(?:input|include)\{([^}]+)\}")
RE_GRAPHIC = re.compile(r"\\(?:includegraphics|includesvg)(?:\[[^\]]*\])?\{([^}]+)\}")
RE_LABEL = re.compile(r"\\label\{([^}]+)\}")
RE_REF = re.compile(r"\\(?:ref|autoref|cref|Cref|eqref)\{([^}]+)\}")
RE_ENV = re.compile(r"\\(begin|end)\{([^}]+)\}")

GRAPHIC_EXTS = ["", ".pdf", ".png", ".svg", ".jpg", ".jpeg", ".eps"]

# --- 排版/泄漏检查 ---
# 剥掉合法携带 key/路径的命令参数后，正文残留的 `名字+年份+词` 裸 token
# 即为 BibTeX key 泄漏（写作规范：引用一律 \cite，表格单元格不得出现裸 key）。
# 载体覆盖 natbib/biblatex 全部 cite 变体（citet/citep/citealp/nocite/
# autocite/textcite…）、全部 ref 变体（ref/autoref/cref/pageref/nameref/
# hyperref/href…）、label、url/path、bib 相关、input/include 家族。
RE_KEY_CARRIER = re.compile(
    r"\\(?:[A-Za-z]*[Cc]ite[A-Za-z]*\*?|[A-Za-z]*ref\*?|label|url|path|"
    r"bibliography[A-Za-z]*|bibitem|input|include[A-Za-z]*)"
    r"(?:\[[^\]]*\])?\{[^}]*\}")
# key 形态与 server.core.bibtex.record_to_bibtex 一致：字母 ≥2 + 年份 +
# 题首词（可以数字开头，如 zhang20202d）。边界用 lookaround 而非 \b：
# 中文正文里 key 与汉字紧贴时 \b 不成立（汉字属 \w）。
RE_BARE_BIBKEY = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z]{2,}(?:19|20)\d{2}[A-Za-z0-9]+(?![A-Za-z0-9])")
# 行内豁免标记（写在该行注释里）：% tex-guard: allow-key
RE_ALLOW_KEY = re.compile(r"tex-guard:\s*allow-key", re.I)
RE_TEXTTT = re.compile(r"\\texttt\{")
RE_CJK = re.compile(r"[\u4e00-\u9fff]")
RE_DOCCLASS = re.compile(r"\\documentclass(?:\[[^\]]*\])?\{([^}]+)\}")
# 中文支持既可来自 ctex 文档类，也可来自 \usepackage{ctex}/xeCJK 等
RE_TABLE_BEGIN = re.compile(
    r"\\begin\{(tabular\*?|tabularx|longtable|tabulary)\}"
    r"(?:\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})?"      # tabularx/tabular* 的宽度参数
    r"\s*(?:\[[^\]]*\])?\s*\{")               # 到列格式的左花括号
RE_COLSPEC_TOKEN = re.compile(
    r"\*\{(\d+)\}\{([^{}]*)\}"                   # *{n}{spec}
    r"|[>@!<]\{(?:[^{}]|\{[^{}]*\})*\}"           # 装饰项，不计列
    r"|[pmbPLCRS]\s*(?:\[[^\]]*\])?\{[^{}]*\}"  # 定宽列
    r"|[lcrXY]"                                  # 单字母列
    r"|\|")
LANDSCAPE_ENVS = {"landscape", "sidewaystable", "sidewaystable*", "sidewaysfigure"}
DENSE_MIN_COLS = 6          # 竖版 ≥6 列才检查单元格长度
DENSE_MAX_COLS = 8          # 竖版 ≥8 列一律阻塞
DENSE_MAX_UNITS = 40        # 最长单元格：CJK 字符计 2、其他计 1，> 40 即"读不下去"
RE_CJK_PKG = re.compile(
    r"\\usepackage(?:\[[^\]]*\])?\{[^}]*(?:ctex|xeCJK|luatexja|CJKutf8|CJK)[^}]*\}")
TEXTTT_WARN_MIN_COUNT = 8       # 少量合法用法（命令/代码名）不告警
TEXTTT_WARN_PER_1K = 2.0        # 每千字符超过该密度则告警
CJK_RATIO_ZH_DOC = 0.05         # CJK 字符占比超过 5% 视为中文稿


def strip_comment(line: str) -> str:
    """去掉 % 注释（保留 \\% 转义）。"""
    out = []
    prev = ""
    for ch in line:
        if ch == "%" and prev != "\\":
            break
        out.append(ch)
        prev = ch
    return "".join(out)


def check_file(path: str, roots: list[str]) -> tuple[list[str], list[str],
                                                     set[str], set[str]]:
    """→ (blocking, warnings, labels, refs)"""
    blocking: list[str] = []
    warnings: list[str] = []
    labels: set[str] = set()
    refs: set[str] = set()
    env_stack: list[tuple[str, int]] = []
    brace_balance = 0
    base = os.path.basename(path)

    with open(path, encoding="utf-8", errors="replace") as f:
        for ln, raw in enumerate(f, 1):
            line = strip_comment(raw)
            if RE_TODO.search(line):
                blocking.append(f"{base}:{ln} 占位残留: {line.strip()[:60]}")
            for m in RE_INPUT.finditer(line):
                target = m.group(1)
                cands = [os.path.join(r, target + ext)
                         for r in roots for ext in ("", ".tex")]
                if not any(os.path.isfile(c) for c in cands):
                    blocking.append(f"{base}:{ln} \\input 目标不存在: {target}")
            for m in RE_GRAPHIC.finditer(line):
                target = m.group(1)
                cands = [os.path.join(r, target + ext)
                         for r in roots for ext in GRAPHIC_EXTS]
                if not any(os.path.isfile(c) for c in cands):
                    blocking.append(f"{base}:{ln} 图文件不存在: {target}")
            labels.update(RE_LABEL.findall(line))
            refs.update(RE_REF.findall(line))
            for m in RE_ENV.finditer(line):
                kind, env = m.group(1), m.group(2)
                if kind == "begin":
                    env_stack.append((env, ln))
                elif not env_stack:
                    blocking.append(f"{base}:{ln} \\end{{{env}}} 没有对应 \\begin")
                else:
                    top, top_ln = env_stack.pop()
                    if top != env:
                        blocking.append(
                            f"{base}:{ln} 环境错配: \\begin{{{top}}}(L{top_ln}) "
                            f"被 \\end{{{env}}} 闭合")
            brace_balance += line.count("{") - line.count("}")

    for env, ln in env_stack:
        blocking.append(f"{base}:{ln} \\begin{{{env}}} 未闭合")
    if brace_balance != 0:
        warnings.append(f"{base} 花括号不平衡（差 {brace_balance:+d}），"
                        "请检查是否漏写 }")
    return blocking, warnings, labels, refs


def check_bibkey_leak(path: str) -> list[str]:
    """BibTeX key 泄漏检查（全文级：\\cite 参数允许跨行，逐行剥会误伤）。

    行尾注释写 `% tex-guard: allow-key` 可豁免该行（真有同形词时的安全阀）。
    """
    base = os.path.basename(path)
    with open(path, encoding="utf-8", errors="replace") as f:
        raw_lines = f.read().splitlines()
    text = "\n".join(strip_comment(l) for l in raw_lines)
    visible = RE_KEY_CARRIER.sub(
        lambda m: "".join(c if c == "\n" else " " for c in m.group(0)), text)
    line_starts = [0] + [i + 1 for i, ch in enumerate(visible) if ch == "\n"]

    def line_of(pos: int) -> int:
        import bisect
        return bisect.bisect_right(line_starts, pos)

    out = []
    for km in RE_BARE_BIBKEY.finditer(visible):
        ln = line_of(km.start())
        if ln <= len(raw_lines) and RE_ALLOW_KEY.search(raw_lines[ln - 1]):
            continue
        out.append(
            f"{base}:{ln} 疑似 BibTeX key 泄漏到正文: {km.group(0)}"
            "（引用一律 \\cite，表格单元格不得出现裸 key；确属同形词可在行尾"
            "注释 % tex-guard: allow-key 豁免）")
    return out


def check_typography(files: list[str]) -> list[str]:
    """跨文件排版体检：\\texttt 密度 + 中文稿模板匹配。→ warnings"""
    warnings: list[str] = []
    total_chars = 0
    total_texttt = 0
    total_cjk = 0
    doc_classes: list[str] = []
    has_cjk_pkg = False
    for fp in files:
        with open(fp, encoding="utf-8", errors="replace") as f:
            text = "\n".join(strip_comment(l) for l in f)
        total_chars += len(text)
        total_texttt += len(RE_TEXTTT.findall(text))
        total_cjk += len(RE_CJK.findall(text))
        doc_classes += RE_DOCCLASS.findall(text)
        has_cjk_pkg = has_cjk_pkg or bool(RE_CJK_PKG.search(text))

    density = total_texttt / max(total_chars / 1000, 1e-9)
    if total_texttt >= TEXTTT_WARN_MIN_COUNT and density > TEXTTT_WARN_PER_1K:
        warnings.append(
            f"\\texttt 使用 {total_texttt} 次（{density:.1f} 次/千字符）——"
            "打字机体只该给真正的代码/命令；正文术语、缺失值（NA）、"
            "证据代号应改正体或数学记号，检查是否有内部术语泄漏")
    cjk_ratio = total_cjk / max(total_chars, 1)
    has_cjk_class = any("ctex" in c for c in doc_classes)
    if cjk_ratio > CJK_RATIO_ZH_DOC and doc_classes and \
            not (has_cjk_class or has_cjk_pkg):
        warnings.append(
            f"中文稿（CJK 占比 {cjk_ratio:.0%}）使用非 ctex 文档类 "
            f"{doc_classes} 且未加载 ctex/xeCJK：Abstract/Table/Figure 标签"
            "将是英文，请改用 templates/survey_main_zh.tex（ctexart + 本地化标签）")
    return warnings


def _count_columns(spec: str) -> int:
    n = 0
    for m in RE_COLSPEC_TOKEN.finditer(spec):
        if m.group(1) is not None:
            n += int(m.group(1)) * _count_columns(m.group(2))
        elif m.group(0) in ("|",) or m.group(0)[0] in ">@!<":
            continue
        else:
            n += 1
    return n


def _cell_units(cell: str) -> int:
    """单元格的印刷长度估计：去掉 \cite/\ref 与命令名，CJK 计 2、其余计 1。"""
    s = re.sub(r"\\(?:cite[pt]?\*?|ref|autoref|cref|label)(?:\[[^\]]*\])?\{[^}]*\}", "", cell)
    s = re.sub(r"\\[A-Za-z]+\*?", "", s)
    s = re.sub(r"[{}$^_~\\]", "", s)
    s = " ".join(s.split())
    return sum(2 if RE_CJK.match(ch) else 1 for ch in s)


def check_table_density(path: str) -> list[str]:
    """竖版密表阻塞：≥6 列且最长单元格 > 40 单位，或 ≥8 列。横排环境内的表不计。"""
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = [strip_comment(l) for l in fh]
    text = "\n".join(lines)
    problems: list[str] = []
    for m in RE_TABLE_BEGIN.finditer(text):
        env = m.group(1)
        # 列格式：从 m.end() 起到配对的右花括号
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        spec = text[m.end():i - 1]
        cols = _count_columns(spec)
        if cols < DENSE_MIN_COLS:
            continue
        # 是否在横排环境内
        before = text[:m.start()]
        landscape = any(
            before.count(f"\\begin{{{e}}}") > before.count(f"\\end{{{e}}}")
            for e in LANDSCAPE_ENVS)
        if landscape:
            continue
        end_tag = f"\\end{{{env}}}"
        j = text.find(end_tag, i)
        body = text[i:j if j != -1 else len(text)]
        cells = [c for row in re.split(r"\\\\", body) for c in re.split(r"(?<!\\)&", row)]
        longest = max((_cell_units(c) for c in cells), default=0)
        line_no = text.count("\n", 0, m.start()) + 1
        if cols >= DENSE_MAX_COLS or longest > DENSE_MAX_UNITS:
            problems.append(
                f"竖版密表: {path}:{line_no} {env} {cols} 列，最长单元格 ≈{longest} 单位"
                f"（CJK 计 2）——顶刊做法：≤5 列，或转横版（pdflscape 的 landscape / "
                f"rotating 的 sidewaystable），或拆表、合并列、把长说明挪到表注")
    return problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("draft", help="稿件目录或 main.tex")
    args = ap.parse_args()

    if os.path.isfile(args.draft):
        files = [args.draft]
        root = os.path.dirname(os.path.abspath(args.draft))
    else:
        files = sorted(glob.glob(os.path.join(args.draft, "**", "*.tex"),
                                 recursive=True))
        root = os.path.abspath(args.draft)
    if not files:
        sys.exit(f"未找到 .tex 文件: {args.draft}")
    roots = [root] + sorted({os.path.dirname(os.path.abspath(f)) for f in files})

    blocking: list[str] = []
    warnings: list[str] = []
    all_labels: set[str] = set()
    all_refs: set[str] = set()
    for fp in files:
        b, w, ls, rs = check_file(fp, roots)
        blocking += b
        warnings += w
        all_labels |= ls
        all_refs |= rs
        blocking += check_bibkey_leak(fp)
        blocking += check_table_density(fp)
    warnings += check_typography(files)

    dangling = sorted(all_refs - all_labels)
    for r in dangling:
        blocking.append(f"悬空引用: \\ref{{{r}}} 无对应 \\label")

    print(f"检查文件: {len(files)}  labels: {len(all_labels)}  refs: {len(all_refs)}")
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
