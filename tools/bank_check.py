#!/usr/bin/env python3
"""bank_check —— 引用支持库（citation bank）确定性校验（离线）。

校验 workspace/notes/citation_bank.md：
1. 行格式：`- [key] <一句话可支撑的 claim> (strong|weak)`，格式坏 = 阻塞
2. key 全部在 references.bib 中 = 阻塞
3. 候选量 ≥ 目标引用数 × --min-ratio（传了 --target-cites 才检查）= 阻塞
4. 近三年条目占比 ≥ --min-recent（年份取自 bib 条目）= 阻塞

用法：
  python3 tools/bank_check.py workspace/notes/citation_bank.md \
      workspace/library/references.bib \
      [--target-cites 120] [--min-ratio 1.5] [--min-recent 0.5]
退出码：0 = PASS；1 = 存在阻塞问题。
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server.core.bibtex import parse_bibtex  # noqa: E402

RE_ENTRY = re.compile(r"^\s*[-*]\s*\[([^\]\s]+)\]\s*(.*)$")
RE_STRENGTH = re.compile(r"\((strong|weak)\)\s*$", re.I)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bank", help="citation_bank.md")
    ap.add_argument("bib", help="references.bib")
    ap.add_argument("--target-cites", type=int, default=0,
                    help="目标引用数（>0 时检查候选量 ≥ 目标 × min-ratio）")
    ap.add_argument("--min-ratio", type=float, default=1.5)
    ap.add_argument("--min-recent", type=float, default=0.5,
                    help="近三年条目最低占比")
    args = ap.parse_args()

    if not os.path.isfile(args.bank):
        sys.exit(f"未找到 citation bank: {args.bank}")
    if not os.path.isfile(args.bib):
        sys.exit(f"未找到 bib 文件: {args.bib}")

    with open(args.bib, encoding="utf-8") as f:
        bib = {e["key"]: e for e in parse_bibtex(f.read())}

    entries: list[tuple[int, str, str]] = []   # (line_no, key, body)
    bad_format: list[str] = []
    with open(args.bank, encoding="utf-8") as f:
        for ln, raw in enumerate(f, 1):
            line = raw.rstrip()
            if not line or line.lstrip().startswith(("#", "<!--")):
                continue
            m = RE_ENTRY.match(line)
            if not m:
                if line.lstrip().startswith(("-", "*")):
                    bad_format.append(f"L{ln} 缺 [key] 前缀: {line.strip()[:60]}")
                continue
            key, body = m.group(1), m.group(2).strip()
            if not RE_STRENGTH.search(body):
                bad_format.append(f"L{ln} [{key}] 缺 (strong|weak) 强度标注")
            claim = RE_STRENGTH.sub("", body).strip()
            if len(claim) < 8:
                bad_format.append(f"L{ln} [{key}] claim 过短/为空，"
                                  "每行须写一句可支撑的具体 claim")
            entries.append((ln, key, body))

    unknown = [(ln, k) for ln, k, _ in entries if k not in bib]
    keys = [k for _, k, _ in entries]

    this_year = date.today().year
    recent_cut = this_year - 2
    known = [k for k in keys if k in bib]
    years = []
    for k in known:
        y = str(bib[k]["fields"].get("year", ""))
        m = re.search(r"\d{4}", y)
        years.append(int(m.group()) if m else 0)
    recent_ratio = (sum(1 for y in years if y >= recent_cut) / len(years)
                    if years else 0.0)

    blocking: list[str] = []
    blocking += bad_format
    for ln, k in unknown:
        blocking.append(f"L{ln} key 不在 references.bib: {k}"
                        "（不许手写库外 key，先交 lit_search 补检）")
    if args.target_cites > 0:
        need = int(args.target_cites * args.min_ratio)
        if len(entries) < need:
            blocking.append(f"候选量 {len(entries)} < 目标 {args.target_cites} × "
                            f"{args.min_ratio} = {need}，先补库再进蓝图")
    if years and recent_ratio < args.min_recent:
        blocking.append(f"近三年（≥{recent_cut}）占比 {recent_ratio:.0%} "
                        f"< 下限 {args.min_recent:.0%}")

    print(f"bank 条目: {len(entries)}  唯一 key: {len(set(keys))}  "
          f"近三年占比: {recent_ratio:.0%}")
    if blocking:
        print(f"\n[阻塞] {len(blocking)} 项:")
        for b in blocking:
            print(f"  - {b}")
    print("\n结论:", "FAIL" if blocking else "PASS")
    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
