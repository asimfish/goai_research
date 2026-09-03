#!/usr/bin/env python3
"""tex_polish —— 稿件源码的确定性排版修补（tex_guard 之外的「难看但不报错」项）。

1. 正文里字母之间的斜杠 → 可断斜杠 `\\slash `。TeX 不在 "/" 处断行，
   "phase/density/transport" 这类连词是 Overfull \\hbox 的头号来源（实测一处 37pt）。
   携带路径/URL/key 的命令参数（includegraphics/includesvg/url/href/input/path/
   texttt/bibliography/cite*/ref*/label 的花括号内容）与注释行不动。
2. `\\bibliography{<任意路径>/references}` 在 references.bib 与 main.tex 同目录时
   归一为 `\\bibliography{references}`（提交包/工作区常把 bib 搬到稿件旁）。
3. `\\usepackage{svg}` → `\\IfFileExists{svg.sty}{\\usepackage{svg}}{}`；
   `\\includegraphics{...svg}` 报告出来——graphicx 不能直接吃 SVG，须先转 PDF。

用法：
  python3 tools/tex_polish.py <draft_dir>            # dry run，打印将做的修改
  python3 tools/tex_polish.py <draft_dir> --write    # 原地修改
退出码：0。
"""
from __future__ import annotations

import argparse
import glob
import os
import re

RE_SLASH = re.compile(r"(?<=[A-Za-z\)])/(?=[A-Za-z\(])")
# 只遮罩携带路径/URL/key 的命令参数（整行跳过会漏掉同一行里的正文斜杠）
RE_MASK = re.compile(
    r"\\(?:includegraphics|includesvg|url|href|input|include|path|texttt|bibliography|"
    r"bibliographystyle|[A-Za-z]*cite[A-Za-z]*|[A-Za-z]*ref|label)\*?(?:\[[^\]]*\])?\{[^}]*\}")
RE_BIBLIO = re.compile(r"\\bibliography\{([^}]*)\}")
RE_SVG_INC = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{[^}]*\.svg\}")


def polish_dir(root: str, write: bool) -> list[str]:
    changes: list[str] = []
    files = sorted(glob.glob(os.path.join(root, "**", "*.tex"), recursive=True))
    for fp in files:
        rel = os.path.relpath(fp, root)
        text = open(fp, encoding="utf-8").read()
        out_lines = []
        n_slash = 0
        for line in text.splitlines(keepends=True):
            if line.lstrip().startswith("%"):
                out_lines.append(line)
                continue
            holes: list[str] = []
            masked = RE_MASK.sub(lambda m: (holes.append(m.group(0)) or f"\x00{len(holes) - 1}\x00"), line)
            new, k = RE_SLASH.subn(r"\\slash ", masked)
            new = re.sub(r"\x00(\d+)\x00", lambda m: holes[int(m.group(1))], new)
            n_slash += k
            out_lines.append(new)
        new_text = "".join(out_lines)
        if n_slash:
            changes.append(f"{rel}: {n_slash} 处正文斜杠 → \\slash")
        if os.path.basename(fp) == "main.tex":
            m = RE_BIBLIO.search(new_text)
            if m and "/" in m.group(1) and os.path.isfile(os.path.join(os.path.dirname(fp), "references.bib")):
                new_text = new_text.replace(m.group(0), r"\bibliography{references}")
                changes.append(f"{rel}: \\bibliography{{{m.group(1)}}} → \\bibliography{{references}}（bib 与 main.tex 同目录）")
            if "\\usepackage{svg}" in new_text:
                new_text = new_text.replace("\\usepackage{svg}", "\\IfFileExists{svg.sty}{\\usepackage{svg}}{}")
                changes.append(f"{rel}: \\usepackage{{svg}} 改为存在才加载")
        for m in RE_SVG_INC.finditer(new_text):
            changes.append(f"{rel}: 直接引用 SVG 无法被 graphicx 处理，须先转 PDF 再引用: {m.group(0)[:70]}")
        if write and new_text != text:
            with open(fp, "w", encoding="utf-8") as fh:
                fh.write(new_text)
    return changes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("draft_dir")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    changes = polish_dir(args.draft_dir, args.write)
    print(f"{args.draft_dir}: {len(changes)} 项{'（已写入）' if args.write else '（dry run）'}")
    for c in changes:
        print("  -", c)


if __name__ == "__main__":
    main()
