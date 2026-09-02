#!/usr/bin/env python3
"""Build the Claim -> Evidence mapping for a finished report.

Every sentence of the LaTeX manuscript that carries a ``\\cite`` becomes one
*claim* record.  Each cited key is resolved to its *evidence* record:

* bibliographic identity (title, year, DOI, official URL) from ``references.bib``
* the reference-check verdict from ``CITATION_AUDIT.json`` (existence / metadata /
  author-order axes, all re-fetched from Crossref / OpenAlex / arXiv at run time)
* the support note and strength (``strong`` / ``weak``) assigned in the citation
  bank before writing (``notes/citation_bank.md``)
* whether the full text is shipped in the public corpus package
  (``corpus_release/cited_references_index.json``) and its document id
* for synthesis-condition cells, the manually traced original-source location
  (``notes/condition_source_trace.md``: DOI, page / section, supportable and
  non-supportable fields)

Output: ``claim_evidence.jsonl`` (one claim per line) and
``claim_evidence_summary.json``.  Reviewers can pick any claim id, open the cited
DOI, and — when the text is in the package — read the passage through
``lookup_local_doi`` / ``read_local_document``.

Usage::

    python3 tools/build_claim_evidence.py --bundle submission/goai_final
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.core.bibtex import parse_bibtex  # noqa: E402

CITE_RE = re.compile(r"\\cite[tp]?\{([^}]+)\}")
SECTION_RE = re.compile(r"\\(section|subsection|subsubsection)\*?\{([^}]*)\}")
INPUT_RE = re.compile(r"\\input\{sections/([^}]+)\}")


def strip_latex(text: str) -> str:
    text = CITE_RE.sub("", text)
    text = re.sub(r"\\label\{[^}]*\}", "", text)
    text = re.sub(r"\\(?:ref|cref|Cref)\{[^}]*\}", "[ref]", text)
    text = re.sub(r"\\(?:emph|textbf|textit|texttt|mathrm|text)\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\,|~", " ", text)
    text = re.sub(r"\\(?:footnote|url)\{[^}]*\}", "", text)
    text = text.replace(r"\%", "%").replace(r"\&", "&").replace("--", "–")
    text = re.sub(r"\$\\circ\$|\^\\circ|\$\^\\circ\$", "°", text)
    text = re.sub(r"\$([^$]*)\$", lambda m: m.group(1).replace("_", "").replace("{", "").replace("}", "").replace("\\", ""), text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(paragraph: str) -> list[str]:
    # Chinese full stops, ASCII full stops followed by space, and semicolon-terminated clauses that end a citation group
    parts = re.split(r"(?<=[。！？])|(?<=[.!?])\s+(?=[A-Z\\$])", paragraph)
    return [p.strip() for p in parts if p and p.strip()]


def parse_bank(path: Path) -> dict[str, dict]:
    bank: dict[str, dict] = {}
    if not path.exists():
        return bank
    section = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
        m = re.match(r"- \[([^\]]+)\]\s*(.*?)\s*\((strong|weak)\)\s*$", line.strip())
        if m:
            bank[m.group(1)] = {"bank_section": section, "support_note": m.group(2), "support_strength": m.group(3)}
    return bank


def parse_condition_trace(path: Path) -> dict[str, list[dict]]:
    """Return {citation_key: [trace records]} from condition_source_trace.md."""
    out: dict[str, list[dict]] = {}
    if not path.exists():
        return out
    blocks = re.split(r"^## ", path.read_text(encoding="utf-8"), flags=re.M)
    for block in blocks[1:]:
        head, _, body = block.partition("\n")
        m = re.match(r"(\S+)\s*[—-]+\s*`([^`]+)`", head)
        if not m:
            continue
        cell, key = m.group(1), m.group(2)
        rec: dict = {"condition_cell": cell}
        for line in body.splitlines():
            line = line.strip().lstrip("- ").strip()
            for label, field in (("DOI", "doi"), ("原始来源", "source"), ("定位", "location"),
                                 ("可支持字段", "supportable_fields"), ("不可支持字段", "non_supportable_fields")):
                if line.startswith(label + "：") or line.startswith(label + ":"):
                    rec[field] = line.split("：", 1)[-1].split(":", 1)[-1].strip().strip("`")
        out.setdefault(key, []).append(rec)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bundle", default="submission/goai_final")
    args = ap.parse_args()
    bundle = Path(args.bundle).resolve()
    report = bundle / "report"
    evidence = bundle / "evidence"

    bib = {e["key"]: e["fields"] for e in parse_bibtex((report / "references.bib").read_text(encoding="utf-8"))}
    audit = {e["key"]: e for e in json.loads((evidence / "CITATION_AUDIT.json").read_text(encoding="utf-8"))["per_entry"]}
    bank = parse_bank(evidence / "notes" / "citation_bank.md")
    traces = parse_condition_trace(evidence / "notes" / "condition_source_trace.md")
    corpus_index = {}
    idx_path = evidence / "corpus_release" / "cited_references_index.json"
    if idx_path.exists():
        corpus_index = {d["citation_key"]: d for d in json.loads(idx_path.read_text(encoding="utf-8"))["documents"]}

    order = INPUT_RE.findall((report / "main.tex").read_text(encoding="utf-8"))
    claims = []
    cid = 0
    for stem in order:
        tex = (report / "sections" / f"{stem}.tex").read_text(encoding="utf-8")
        section_title = ""
        for para in re.split(r"\n\s*\n", tex):
            heads = SECTION_RE.findall(para)
            if heads:
                section_title = heads[-1][1]
            if "\\cite" not in para:
                continue
            para_clean = re.sub(r"%.*", "", para)
            for sentence in split_sentences(para_clean):
                keys = []
                for group in CITE_RE.findall(sentence):
                    keys.extend(k.strip() for k in group.split(",") if k.strip())
                if not keys:
                    continue
                cid += 1
                ev = []
                for key in keys:
                    fields = bib.get(key, {})
                    a = audit.get(key, {})
                    ci = corpus_index.get(key, {})
                    ev.append({
                        "citation_key": key,
                        "title": str(fields.get("title", "")).strip("{}"),
                        "year": fields.get("year"),
                        "doi": fields.get("doi"),
                        "url": fields.get("url") or (f"https://doi.org/{fields['doi']}" if fields.get("doi") else None),
                        "refcheck_verdict": a.get("verdict"),
                        "refcheck_axes": {k: v.get("status") for k, v in (a.get("axes") or {}).items()},
                        "support_strength": bank.get(key, {}).get("support_strength"),
                        "support_note": bank.get(key, {}).get("support_note"),
                        "full_text_in_package": bool(ci.get("full_text_in_package")),
                        "document_id": ci.get("document_id") or None,
                        "condition_source_trace": traces.get(key),
                    })
                claims.append({
                    "claim_id": f"C{cid:03d}",
                    "section_file": f"sections/{stem}.tex",
                    "section": section_title,
                    "claim_text": strip_latex(sentence),
                    "claim_latex": sentence.strip(),
                    "citation_keys": keys,
                    "evidence": ev,
                })

    out_path = evidence / "claim_evidence.jsonl"
    with out_path.open("w", encoding="utf-8") as fh:
        for c in claims:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")

    used = {k for c in claims for k in c["citation_keys"]}
    summary = {
        "claims": len(claims),
        "citation_calls": sum(len(c["citation_keys"]) for c in claims),
        "distinct_keys_cited": len(used),
        "bib_entries": len(bib),
        "bib_entries_uncited": sorted(set(bib) - used),
        "refcheck_pass_rate": round(100 * sum(1 for k in used if audit.get(k, {}).get("verdict") == "PASS") / max(len(used), 1), 2),
        "keys_with_full_text_in_package": sorted(k for k in used if corpus_index.get(k, {}).get("full_text_in_package")),
        "claims_with_any_full_text_evidence": sum(1 for c in claims if any(e["full_text_in_package"] for e in c["evidence"])),
        "claims_with_condition_source_trace": sum(1 for c in claims if any(e["condition_source_trace"] for e in c["evidence"])),
        "support_strength_of_cited_keys": {
            s: sorted(k for k in used if bank.get(k, {}).get("support_strength") == s) for s in ("strong", "weak")
        },
        "files": {"claims": out_path.name, "bib": "../report/references.bib", "audit": "CITATION_AUDIT.json",
                  "bank": "notes/citation_bank.md", "condition_trace": "notes/condition_source_trace.md",
                  "corpus_index": "corpus_release/cited_references_index.json"},
    }
    (evidence / "claim_evidence_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in {"keys_with_full_text_in_package", "support_strength_of_cited_keys"}}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
