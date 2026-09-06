#!/usr/bin/env python3
"""bib_enrich —— 用 Crossref 按 DOI 补齐参考文献的卷/期/页码并核对年份（只补缺、不改写已有值）。

审稿教训（2026-09-07 BYZSO round 5, I35）：80 篇期刊论文里 79 篇没有卷期页码——
检索工具导出的 BibTeX 只带 title/author/journal/year/doi，plainnat 打出来的参考文献
无法定位到具体一期。补齐是机械活，不该交给写作 agent 手工做。

用法：
  python3 tools/bib_enrich.py workspace/library/references.bib            # 只报告
  python3 tools/bib_enrich.py workspace/library/references.bib --write    # 补写（备份 .bak）
  python3 tools/bib_enrich.py references.bib --write --fix-year           # 年份与 Crossref 出版年不同则改为出版年
退出码：0 = 完成；1 = 有条目 Crossref 查不到（列出 key，需人工处理）。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server.core.bibtex import format_entry, parse_bibtex  # noqa: E402

UA = "goai-research/1.0 (mailto:" + os.environ.get("GOAI_EMAIL", "goai-research@example.com") + ")"


def crossref(doi: str) -> dict | None:
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)["message"]
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def issued_year(msg: dict) -> str:
    for k in ("published-print", "published-online", "issued", "created"):
        parts = (msg.get(k) or {}).get("date-parts") or []
        if parts and parts[0] and parts[0][0]:
            return str(parts[0][0])
    return ""


def enrich(text: str, fix_year: bool = False, sleep: float = 1.0) -> tuple[str, list[str], list[str]]:
    entries = parse_bibtex(text)
    changes: list[str] = []
    unresolved: list[str] = []
    out = []
    for e in entries:
        f = dict(e["fields"])
        doi = (f.get("doi") or "").strip()
        if e["entry_type"] == "article" and doi:
            msg = crossref(doi)
            time.sleep(sleep)
            if msg is None:
                unresolved.append(e["key"])
            else:
                filled = []
                if not f.get("volume") and msg.get("volume"):
                    f["volume"] = str(msg["volume"]); filled.append("volume")
                if not f.get("number") and msg.get("issue"):
                    f["number"] = str(msg["issue"]); filled.append("number")
                if not f.get("pages"):
                    page = msg.get("page") or msg.get("article-number")
                    if page:
                        f["pages"] = re.sub(r"\s*-\s*", "--", str(page)); filled.append("pages")
                if filled:
                    changes.append(f"{e['key']}: 补 {', '.join(filled)}")
                cy = issued_year(msg)
                if cy and f.get("year") and cy != f["year"].strip():
                    if fix_year:
                        changes.append(f"{e['key']}: year {f['year']} → {cy}（Crossref 出版年）")
                        f["year"] = cy
                    else:
                        changes.append(f"{e['key']}: 年份不一致 bib={f['year']} crossref={cy}（--fix-year 可改）")
        out.append(format_entry(e["key"], e["entry_type"], f))
    return "\n\n".join(out) + "\n", changes, unresolved


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bib")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--fix-year", action="store_true")
    ap.add_argument("--sleep", type=float, default=1.0, help="每次 Crossref 请求后的等待秒数")
    a = ap.parse_args()
    text = open(a.bib, encoding="utf-8").read()
    new, changes, unresolved = enrich(text, fix_year=a.fix_year, sleep=a.sleep)
    for c in changes:
        print("  -", c)
    if unresolved:
        print(f"Crossref 查不到 {len(unresolved)} 条: {', '.join(unresolved)}")
    if a.write and new != text:
        with open(a.bib + ".bak", "w", encoding="utf-8") as fh:
            fh.write(text)
        with open(a.bib, "w", encoding="utf-8") as fh:
            fh.write(new)
        print(f"已写入 {a.bib}（备份 .bak）")
    print(f"{len(changes)} 项变更{'' if a.write else '（dry run）'}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main())
