#!/usr/bin/env python3
"""Check that manuscript prose uses disciplinary rather than software language.

The orchestration layer may retain its internal taxonomy (gates, ledgers, fields,
and endpoints).  Those terms must not leak into a manuscript, figure caption, or
table heading.  This small deterministic guard is intentionally conservative:
it reports the offending line and a materials-science alternative, and exits
non-zero so the writer/reviewer loop must address the wording before delivery.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REPLACEMENTS: dict[str, str] = {
    "身份与出处核验表": "目标化合物及相关体系的组成与结构依据",
    "证据级": "与目标相的关系",
    "比较标签": "分类依据",
    "已过闸": "已通过文献核查",
    "过闸": "通过文献核查",
    "字段归一化": "合成条件的统一比较",
    "固定字段": "固定实验项目",
    "字段": "实验项目",
    "相互独立的验证终点": "互补的表征方法",
    "验证终点": "表征方法",
    "四方端点": "四方参照相",
    "端点": "参照相",
    "证据包": "本文获得的文献材料",
    "引用池": "本文核查的文献",
    "变量与表征工具箱": "实验变量与表征方法",
    "工具箱": "方法参照",
    "降权": "限制其适用范围",
    "迁移权限": "可外推范围",
    "身份锚点": "直接结构依据",
    "谱系核验": "结构关系复核",
    "路线归一化": "合成方法的统一比较",
    "验证闭环": "可迭代的实验依据",
    "同字段比较": "按相同实验项目比较",
    "统一字段": "统一实验项目",
    "工作流": "研究流程",
    "流水线": "研究流程",
}

EXTENSIONS = {".tex", ".md", ".txt", ".json"}
_TEX_COMMENT = re.compile(r"(?<!\\)%.*$")


def _files(paths: list[Path]) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        if path.is_file():
            if path.suffix.lower() in EXTENSIONS:
                found.append(path)
        elif path.is_dir():
            found.extend(
                p for p in path.rglob("*")
                if p.is_file() and p.suffix.lower() in EXTENSIONS
            )
    return sorted(set(found))


def _visible(line: str, suffix: str) -> str:
    # Comments and orchestration-only notes are not manuscript prose.  A JSON
    # figure spec has no comments, so all of its labels remain visible here.
    if suffix == ".tex":
        line = _TEX_COMMENT.sub("", line)
    return line


def check(paths: list[Path], allow: set[str] | None = None) -> list[tuple[Path, int, str, str]]:
    allow = allow or set()
    findings: list[tuple[Path, int, str, str]] = []
    for path in _files(paths):
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = _visible(raw, path.suffix.lower())
            reported_on_line: list[str] = []
            # Report the most specific phrase only; e.g. “字段归一化” should
            # not generate a second, less useful hit for the nested word “字段”.
            for term in sorted(REPLACEMENTS, key=len, reverse=True):
                suggestion = REPLACEMENTS[term]
                if term in allow:
                    continue
                if term in line and not any(term in previous for previous in reported_on_line):
                    findings.append((path, lineno, term, suggestion))
                    reported_on_line.append(term)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="manuscript files or directories")
    parser.add_argument(
        "--allow", action="append", default=[],
        help="allow an explicitly necessary term (repeatable; record the reason in the review log)",
    )
    args = parser.parse_args()
    findings = check(args.paths, set(args.allow))
    if not findings:
        print("academic_language_guard: PASS")
        return 0
    for path, lineno, term, suggestion in findings:
        print(f"{path}:{lineno}: {term} -> {suggestion}")
    print(f"academic_language_guard: FAIL ({len(findings)} wording issue(s))", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
