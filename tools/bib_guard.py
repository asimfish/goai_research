#!/usr/bin/env python3
"""bib_guard —— 稿件引用一致性确定性闸门（离线，无网络）。

检查项：
1. 正文 \\cite{key} / [@key] 引用的 key 是否都在 .bib 中定义（未定义 = 阻塞）
2. 库内条目整合率：被正文引用的 bib 条目 / bib 总条目，低于线 = 阻塞
   （孤儿条目要么在正文找到落点，要么移出库，不许留着充数）
3. 引用密度（综述质检：正文引用过少给告警）
   密度统计只应覆盖正文章节文件（如 workspace/drafts/sections），
   蓝图、修订日志等过程文档不要计入词数分母。

用法：
  python3 tools/bib_guard.py <draft_dir_or_file> <references.bib> \
      [--min-cites-per-1k 8] [--min-integration 0.9]
退出码：0 = PASS；1 = 存在未定义引用或整合率不达标。
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
    ap.add_argument("--min-cites-per-1k", type=float, default=8.0,
                    help="每千词最低引用数（综述密度告警线）")
    ap.add_argument("--min-integration", type=float, default=0.9,
                    help="库内条目整合率下限（被引条目/bib 总条目，低于线阻塞）")
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
    integration = (len(bib_keys) - len(orphans)) / max(len(bib_keys), 1)

    print(f"稿件文件: {len(files)}  引用调用: {len(cites)}  去重 key: {len(used)}")
    print(f"bib 条目: {len(bib_keys)}  整合率: {integration:.0%}  "
          f"引用密度: {density:.1f} 次/千词")
    if undefined:
        print(f"\n[阻塞] {len(undefined)} 个未定义引用 key:")
        for k in undefined:
            locs = [f"{os.path.basename(f)}:{ln}" for kk, f, ln in cites if kk == k][:3]
            print(f"  - {k}  ({', '.join(locs)})")
    integration_fail = bib_keys and integration < args.min_integration
    if orphans:
        level = "阻塞" if integration_fail else "告警"
        print(f"\n[{level}] {len(orphans)} 个孤儿 bib 条目（未被引用），"
              f"整合率 {integration:.0%} vs 下限 {args.min_integration:.0%}:")
        for k in orphans[:20]:
            print(f"  - {k}")
    if density < args.min_cites_per_1k:
        print(f"\n[告警] 引用密度 {density:.1f} 低于线 {args.min_cites_per_1k}"
              "（综述通常需要更密的证据支撑）")
    failed = bool(undefined) or bool(integration_fail)
    reasons = ([f"{len(undefined)} 个未定义引用"] if undefined else []) + \
              ([f"整合率 {integration:.0%} 低于 {args.min_integration:.0%}"]
               if integration_fail else [])
    print("\n结论:", f"FAIL（{'；'.join(reasons)}）" if failed else "PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
