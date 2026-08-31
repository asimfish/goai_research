#!/usr/bin/env python3
"""Validate taxonomy citation keys and the minimum evidence count per leaf."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ENTRY_RE = re.compile(r"(?m)^@\w+\s*\{\s*([^,]+),")
KEY_RE = re.compile(r"`([^`]+)`")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("taxonomy", type=Path)
    parser.add_argument("bib", type=Path)
    parser.add_argument("--min-per-leaf", type=int, default=3)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    bib_keys = set(ENTRY_RE.findall(args.bib.read_text(encoding="utf-8")))
    lines = args.taxonomy.read_text(encoding="utf-8").splitlines()
    leaves: list[tuple[str, list[str]]] = []
    all_taxonomy_keys: set[str] = set()
    current: str | None = None

    for line in lines:
        if line.startswith("### "):
            current = line[4:].strip()
        elif current and line.startswith("- 支撑文献："):
            keys = KEY_RE.findall(line)
            leaves.append((current, keys))
            all_taxonomy_keys.update(keys)
            current = None
        elif line.startswith("- 未归类 key："):
            all_taxonomy_keys.update(KEY_RE.findall(line))

    missing = sorted(all_taxonomy_keys - bib_keys)
    short = [(name, len(set(keys))) for name, keys in leaves if len(set(keys)) < args.min_per_leaf]
    duplicate_within = [name for name, keys in leaves if len(keys) != len(set(keys))]
    ok = bool(leaves) and not missing and not short and not duplicate_within

    report = [
        "# Taxonomy validation",
        "",
        f"- 结果：**{'PASS' if ok else 'FAIL'}**",
        f"- BibTeX 条目数：{len(bib_keys)}",
        f"- 已识别叶节点：{len(leaves)}",
        f"- taxonomy 中不同 citation key：{len(all_taxonomy_keys)}",
        f"- BibTeX 中不存在的 key：{', '.join(missing) if missing else '无'}",
        f"- 少于 {args.min_per_leaf} 篇支撑的叶节点："
        + (", ".join(f"{name} ({count})" for name, count in short) if short else "无"),
        "- 叶节点内重复 key：" + (", ".join(duplicate_within) if duplicate_within else "无"),
        "",
        "## 逐叶统计",
        "",
    ]
    report.extend(f"- {name}：{len(set(keys))} 个不同 key" for name, keys in leaves)
    report.extend(
        [
            "",
            "## 校验口径",
            "",
            "脚本只检查机械约束：引用 key 是否存在、每个叶节点是否至少包含指定数量的不同 key。"
            "它不把标题/摘要级归类提升为全文证据，也不验证具体事实性结论。",
        ]
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(report) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
