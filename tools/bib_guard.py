#!/usr/bin/env python3
"""bib_guard —— 稿件引用一致性确定性闸门（离线，无网络）。

检查项：
1. 正文 \\cite{key} / [@key] 引用的 key 是否都在 .bib 中定义（未定义 = 阻塞）
2. .bib 中是否有从未被引用的孤儿条目（告警）
3. 每节引用密度（综述质检：正文章节引用过少给告警）

用法：
  python3 tools/bib_guard.py <draft_dir_or_file> <references.bib> [--min-cites-per-1k 3]
退出码：0 = PASS；1 = 存在未定义引用。
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server.core.bibtex import parse_bibtex  # noqa: E402

CITE_TEX = re.compile(r"\\cite[tp]?\*?(?:\[[^\]]*\])?\{([^}]+)\}")
CITE_MD = re.compile(r"\[@([A-Za-z0-9_:\-]+)(?:[;,\s]+@?[A-Za-z0-9_:\-]+)*\]")
CITE_MD_EACH = re.compile(r"@([A-Za-z0-9_:\-]+)")


def collect_cites(path: str) -> list[tuple[str, str, int]]:
    """→ [(key, file, line_no)]"""
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for ln, line in enumerate(f, 1):
            for m in CITE_TEX.finditer(line):
                for key in m.group(1).split(","):
                    out.append((key.strip(), path, ln))
            for m in CITE_MD.finditer(line):
                for km in CITE_MD_EACH.finditer(m.group(0)):
                    out.append((km.group(1), path, ln))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("draft", help="稿件目录或单个 .tex/.md 文件")
    ap.add_argument("bib", help="references.bib")
    ap.add_argument("--min-cites-per-1k", type=float, default=3.0,
                    help="每千词最低引用数（综述密度告警线）")
    args = ap.parse_args()

    files = ([args.draft] if os.path.isfile(args.draft) else
             sorted(glob.glob(os.path.join(args.draft, "**", "*.tex"),
                              recursive=True)
                    + glob.glob(os.path.join(args.draft, "**", "*.md"),
                                recursive=True)))
    if not files:
        sys.exit(f"未找到稿件文件: {args.draft}")

    with open(args.bib, encoding="utf-8") as f:
        bib_keys = {e["key"] for e in parse_bibtex(f.read())}

    cites: list[tuple[str, str, int]] = []
    word_count = 0
    for fp in files:
        cites.extend(collect_cites(fp))
        with open(fp, encoding="utf-8", errors="replace") as f:
            word_count += len(re.findall(r"[\w\u4e00-\u9fff]+", f.read()))

    used = {c[0] for c in cites}
    undefined = sorted(used - bib_keys)
    orphans = sorted(bib_keys - used)
    density = len(cites) / max(word_count / 1000, 1e-9)

    print(f"稿件文件: {len(files)}  引用调用: {len(cites)}  去重 key: {len(used)}")
    print(f"bib 条目: {len(bib_keys)}  引用密度: {density:.1f} 次/千词")
    if undefined:
        print(f"\n[阻塞] {len(undefined)} 个未定义引用 key:")
        for k in undefined:
            locs = [f"{os.path.basename(f)}:{ln}" for kk, f, ln in cites if kk == k][:3]
            print(f"  - {k}  ({', '.join(locs)})")
    if orphans:
        print(f"\n[告警] {len(orphans)} 个孤儿 bib 条目（未被引用）:")
        for k in orphans[:20]:
            print(f"  - {k}")
    if density < args.min_cites_per_1k:
        print(f"\n[告警] 引用密度 {density:.1f} 低于线 {args.min_cites_per_1k}"
              "（综述通常需要更密的证据支撑）")
    print("\n结论:", "FAIL（存在未定义引用）" if undefined else "PASS")
    sys.exit(1 if undefined else 0)


if __name__ == "__main__":
    main()
