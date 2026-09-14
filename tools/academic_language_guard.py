#!/usr/bin/env python3
"""Check that manuscript prose uses disciplinary rather than software language.

The orchestration layer may retain its internal taxonomy (gates, ledgers, fields,
and endpoints).  Those terms must not leak into a manuscript, figure caption, or
table heading.  This small deterministic guard is intentionally conservative:
it reports the offending line and a materials-science alternative, and exits
non-zero so the writer/reviewer loop must address the wording before delivery.

Two extensions after the Chinese-PDF audit:

* English internal terms and file/tool names (``papers.jsonl``, ``bib_guard``,
  ``gate`` as a word, ``evidence package`` ...) are matched with word boundaries so
  English manuscripts are covered too; ``\\ref``/``\\label``/``\\cite`` arguments
  are not reader-visible and are masked first.
* Negative-existence claims in the abstract/conclusion ("未发现…报道", "has not
  been reported") must be listed with a search receipt in
  ``workspace/notes/negative_claims.md`` (``--negative-claims``).  A shipped
  supplement claimed no report exists for Ba5Y12Zn[O(SiO4)]8 while the main case
  had verified its DOI 10.1039/D3NJ04480G.
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
    # 英文内部术语 / 路径泄漏（按整词匹配，大小写不敏感）
    "tool_calls.jsonl": "remove the internal audit-file name; describe the literature check itself",
    "papers.jsonl": "remove the internal file name; say 'the literature records collected in this work'",
    "CITATION_AUDIT": "remove the internal report name; say 'the citation verification'",
    "niche-balanced": "balanced across sub-areas",
    "evidence package": "the literature material obtained in this work",
    "ref_gate": "the citation verification",
    "bib_guard": "the citation consistency check",
    "tex_guard": "the manuscript consistency check",
    "figspec": "figure",
    "ledger": "the study record",
    "gate": "verification step / literature check",
}

EXTENSIONS = {".tex", ".md", ".txt", ".json"}
_TEX_COMMENT = re.compile(r"(?<!\\)%.*$")
# \ref{tab:identity-ledger} / \label{...} / \cite{...} / \input{...} 的参数不是读者可见文本
_TEX_CARRIER = re.compile(
    r"\\(?:[A-Za-z]*[Cc]ite[A-Za-z]*\*?|[A-Za-z]*ref\*?|label|url|path|input|include[A-Za-z]*|"
    r"bibliography[A-Za-z]*)(?:\[[^\]]*\])?\{[^}]*\}")
# 器件物理里的 gate voltage / gate oxide 是学科用语，不算泄漏
_GATE_PHYSICS = r"(?!\s+(?:voltage|oxide|electrode|dielectric|insulator|stack|length|bias|tunable|all-around|tunnel))"


def _term_pattern(term: str) -> re.Pattern[str]:
    if re.fullmatch(r"[A-Za-z0-9_.\- ]+", term):
        body = re.escape(term).replace(r"\ ", r"\s+")
        if term == "gate":
            return re.compile(r"\bgates?\b" + _GATE_PHYSICS, re.I)
        return re.compile(r"(?<![A-Za-z0-9_])" + body + r"(?![A-Za-z0-9_])", re.I)
    return re.compile(re.escape(term))


_PATTERNS: dict[str, re.Pattern[str]] = {term: _term_pattern(term) for term in REPLACEMENTS}

# 否定性存在论断（摘要/结论里「未发现…报道」「has not been reported」）必须有检索回执
NEGATIVE_CLAIM = re.compile(
    r"未发现[^。！？.!?]*?(?:报道|文献)|未见(?:直接)?报道|"
    r"\bno (?:prior|published) reports?\b|\b(?:has|have) not been reported\b", re.I)
_SENTENCE_SPLIT = re.compile(r"(?<=[。！？.!?])\s*")
_CONCLUSION_HEADING = re.compile(r"结论|总结|展望|摘要|conclusion|summary|outlook|abstract", re.I)
_TEX_SECTION = re.compile(r"\\(?:section|subsection|chapter)\*?\{([^}]*)\}")
_MD_HEADING = re.compile(r"^#{1,6}\s*(.+)$")
_CLAIM_LINE = re.compile(r"^\s*[-*]?\s*claim\s*[:：]\s*(.+)$", re.I)
_RECEIPT_LINE = re.compile(r"^\s*[-*]?\s*(?:search|receipt|检索|查询)\s*[:：]\s*(\S.*)$", re.I)


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
        line = _TEX_CARRIER.sub(" ", line)
    return line


def _norm_claim(text: str) -> str:
    """比对用归一化：去 TeX 命令/花括号/数学符号/空白，保留字母数字与汉字。"""
    text = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?", " ", text)
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", text).lower()


def load_negative_claims(path: Path | None) -> dict[str, str]:
    """→ {归一化论断: 检索回执}；文件不存在或没有 claim 行时为空。

    格式（每条一块）::

        - claim: 本次核查未发现 Ba5Y12Zn[O(SiO4)]8 的批量合成报道
          search: Crossref+OpenAlex "Ba5Y12Zn" 2026-09-08，0 条批量合成记录；DOI 10.1039/D3NJ04480G 为单晶
    """
    out: dict[str, str] = {}
    if not path or not path.is_file():
        return out
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = _CLAIM_LINE.match(raw)
        if m:
            current = _norm_claim(m.group(1))
            out.setdefault(current, "")
            continue
        m = _RECEIPT_LINE.match(raw)
        if m and current is not None:
            out[current] = (out[current] + " " + m.group(1).strip()).strip()
    return out


def _in_claim_scope(path: Path) -> bool:
    return bool(_CONCLUSION_HEADING.search(path.stem))


def check_negative_claims(paths: list[Path], claims_file: Path | None) -> list[tuple[Path, int, str, str]]:
    """摘要/结论里的否定性存在论断必须在 negative_claims.md 里登记并带检索回执。"""
    listed = load_negative_claims(claims_file)
    findings: list[tuple[Path, int, str, str]] = []
    where = str(claims_file) if claims_file else "workspace/notes/negative_claims.md"
    for path in _files(paths):
        suffix = path.suffix.lower()
        in_scope = _in_claim_scope(path)
        in_abstract = False
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = _TEX_COMMENT.sub("", raw) if suffix == ".tex" else raw
            if suffix == ".tex":
                if r"\begin{abstract}" in line:
                    in_abstract = True
                m = _TEX_SECTION.search(line)
                if m:
                    in_scope = bool(_CONCLUSION_HEADING.search(m.group(1))) or _in_claim_scope(path)
            else:
                m = _MD_HEADING.match(line)
                if m:
                    in_scope = bool(_CONCLUSION_HEADING.search(m.group(1))) or _in_claim_scope(path)
            if in_scope or in_abstract:
                for sentence in _SENTENCE_SPLIT.split(line):
                    if not NEGATIVE_CLAIM.search(sentence):
                        continue
                    key = _norm_claim(sentence)
                    hit = next((r for c, r in listed.items() if c and (c in key or key in c)), None)
                    if hit is None:
                        findings.append((path, lineno, "negative-existence claim",
                                         f"not listed in {where}: add '- claim: …' with a 'search: …' "
                                         f"receipt (sources, query, date, result) or drop the claim"))
                    elif not hit:
                        findings.append((path, lineno, "negative-existence claim",
                                         f"listed in {where} without a 'search: …' receipt"))
            if suffix == ".tex" and r"\end{abstract}" in line:
                in_abstract = False
    return findings


def check(paths: list[Path], allow: set[str] | None = None,
          negative_claims: Path | None = None) -> list[tuple[Path, int, str, str]]:
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
                if _PATTERNS[term].search(line) and \
                        not any(term.lower() in previous.lower() for previous in reported_on_line):
                    findings.append((path, lineno, term, suggestion))
                    reported_on_line.append(term)
    findings.extend(check_negative_claims(paths, negative_claims))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="manuscript files or directories")
    parser.add_argument(
        "--allow", action="append", default=[],
        help="allow an explicitly necessary term (repeatable; record the reason in the review log)",
    )
    parser.add_argument(
        "--negative-claims", type=Path, default=Path("workspace/notes/negative_claims.md"),
        help="allowlist of negative-existence claims with search receipts (claim:/search: blocks)",
    )
    args = parser.parse_args()
    findings = check(args.paths, set(args.allow), args.negative_claims)
    if not findings:
        print("academic_language_guard: PASS")
        return 0
    for path, lineno, term, suggestion in findings:
        print(f"{path}:{lineno}: {term} -> {suggestion}")
    print(f"academic_language_guard: FAIL ({len(findings)} wording issue(s))", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
