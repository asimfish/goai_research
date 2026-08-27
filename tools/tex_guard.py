#!/usr/bin/env python3
"""tex_guard —— 组稿完整性确定性闸门（离线，零依赖）。

检查项（均忽略 % 注释掉的内容）：
1. TODO/FIXME 占位残留（模板里的 TODO 标题/作者/摘要必须已替换）＝阻塞
2. \\input 目标文件存在 ＝阻塞
3. \\includegraphics / \\includesvg 目标文件存在（自动尝试常见扩展名）＝阻塞
4. \\ref / \\autoref / \\cref 无悬空（有对应 \\label）＝阻塞
5. \\begin/\\end 环境闭合 ＝阻塞
6. 花括号平衡 ＝告警（verbatim 等场景可能误报）

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
