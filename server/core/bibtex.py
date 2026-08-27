"""容错 BibTeX 解析 / 生成 / 作者名单比对。

作者比对语义参考 super_ref：检测 遗漏(missing) / 多余或伪造(extra) /
顺序错误(order) / 缩写与全名等价(abbrev_ok)。
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Optional

from .textnorm import strip_accents, norm_title


# ---------- 解析 ----------

def parse_bibtex(text: str) -> list[dict[str, Any]]:
    """解析 BibTeX 字符串为 [{key, entry_type, fields{}}]，容忍 {} / "" / 裸值。"""
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{", text):
        etype = m.group(1).lower()
        if etype in ("comment", "preamble", "string"):
            continue
        start = m.end()
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        # depth>0 = 缺右括号扫到 EOF：此时 i 未消费闭括号，不能再减 1（否则丢尾字符）
        body = text[start:i - 1] if depth == 0 else text[start:i]
        key_m = re.match(r"\s*([^,\s]+)\s*,", body)
        if not key_m:
            continue
        key = key_m.group(1)
        fields = _parse_fields(body[key_m.end():])
        entries.append({"key": key, "entry_type": etype, "fields": fields})
    return entries


def _parse_fields(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    i = 0
    n = len(body)
    while i < n:
        m = re.match(r"\s*(\w[\w\-]*)\s*=\s*", body[i:])
        if not m:
            break
        name = m.group(1).lower()
        i += m.end()
        if i >= n:
            break
        c = body[i]
        if c == "{":
            depth = 1
            j = i + 1
            while j < n and depth > 0:
                if body[j] == "{":
                    depth += 1
                elif body[j] == "}":
                    depth -= 1
                j += 1
            value = body[i + 1:j - 1] if depth == 0 else body[i + 1:j]
            i = j
        elif c == '"':
            j = i + 1
            while j < n and body[j] != '"':
                j += 1
            value = body[i + 1:j]
            i = j + 1
        else:
            m2 = re.match(r"[^,\n]+", body[i:])
            value = m2.group(0).strip() if m2 else ""
            i += m2.end() if m2 else 1
        fields[name] = re.sub(r"\s+", " ", value).strip()
        m3 = re.match(r"\s*,", body[i:])
        if m3:
            i += m3.end()
    return fields


def split_authors(author_field: str) -> list[str]:
    """按 ' and ' 拆作者；'Last, First' 归一化为 'First Last'。"""
    out = []
    for raw in re.split(r"\s+and\s+", author_field or ""):
        raw = raw.strip().strip("{}")
        if not raw:
            continue
        if "," in raw:
            last, _, first = raw.partition(",")
            raw = f"{first.strip()} {last.strip()}".strip()
        out.append(re.sub(r"\s+", " ", raw))
    return out


# ---------- 生成 ----------

def format_entry(key: str, entry_type: str, fields: dict[str, str]) -> str:
    order = ["author", "title", "booktitle", "journal", "volume", "number",
             "pages", "year", "publisher", "doi", "eprint", "archiveprefix",
             "primaryclass", "url", "note"]
    lines = [f"@{entry_type}{{{key},"]
    done = set()
    for name in order:
        if name in fields and fields[name]:
            lines.append(f"  {name} = {{{fields[name]}}},")
            done.add(name)
    for name, v in fields.items():
        if name not in done and v:
            lines.append(f"  {name} = {{{v}}},")
    lines.append("}")
    return "\n".join(lines)


def record_to_bibtex(rec: dict[str, Any], key: Optional[str] = None) -> str:
    """统一 paper record → BibTeX。会议/期刊有则 inproceedings/article，否则 misc。"""
    authors = rec.get("authors") or []
    first_last = strip_accents((authors[0].split()[-1] if authors else "anon")).lower()
    first_word = (norm_title(rec.get("title") or "x").split() or ["x"])[0]
    key = key or f"{first_last}{rec.get('year') or ''}{first_word}"
    key = re.sub(r"[^A-Za-z0-9]", "", key)

    fields: dict[str, str] = {
        "author": " and ".join(authors),
        "title": rec.get("title") or "",
        "year": str(rec.get("year") or ""),
    }
    venue = rec.get("venue")
    if venue and venue.lower() != "arxiv":
        etype = "article" if re.search(
            r"journal|transactions|letters", venue, re.I) else "inproceedings"
        fields["journal" if etype == "article" else "booktitle"] = venue
    else:
        etype = "misc"
    if rec.get("doi"):
        fields["doi"] = rec["doi"]
    if rec.get("arxiv_id"):
        fields["eprint"] = rec["arxiv_id"]
        fields["archiveprefix"] = "arXiv"
        if etype == "misc":
            fields["note"] = f"arXiv:{rec['arxiv_id']}"
    if rec.get("url"):
        fields["url"] = rec["url"]
    return format_entry(key, etype, fields)


# ---------- 作者比对 ----------

# NFKD 分解对带笔画/合字的拉丁字母无效（Ł→Ł 而非 L），strip_accents 去不掉，
# 会把「Lukasz Kaiser」与「Łukasz Kaiser」误判为两个人。此处补一层折叠。
_LATIN_FOLD = str.maketrans({
    "ł": "l", "Ł": "L", "ø": "o", "Ø": "O", "đ": "d", "Đ": "D",
    "ð": "d", "Ð": "D", "þ": "th", "Þ": "Th", "ß": "ss", "ı": "i",
    "æ": "ae", "Æ": "Ae", "œ": "oe", "Œ": "Oe", "ħ": "h", "Ħ": "H",
})


def _fold_name(s: str) -> str:
    return strip_accents(s).translate(_LATIN_FOLD)


def _name_parts(name: str) -> tuple[str, list[str]]:
    """→ (family_lower, given_tokens_lower)。启发式：最后一个 token 为姓。"""
    toks = _fold_name(name).replace(".", ". ").split()
    toks = [t for t in toks if t]
    if not toks:
        return "", []
    return toks[-1].lower(), [t.lower().rstrip(".") for t in toks[:-1]]


def same_person(a: str, b: str) -> bool:
    """全名/缩写等价判断：姓必须一致；名逐位兼容（缩写=首字母匹配）。"""
    fa, ga = _name_parts(a)
    fb, gb = _name_parts(b)
    if not fa or fa != fb:
        return False
    if not ga or not gb:
        return True  # 只有姓，视为兼容
    for x, y in zip(ga, gb):
        if len(x) == 1 or len(y) == 1:
            if x[0] != y[0]:
                return False
        elif x != y:
            return False
    return True


def compare_authors(claimed: list[str], canonical: list[str]) -> dict[str, Any]:
    """声称作者 vs 权威作者。返回 {ok, issues[], aligned[]}。

    issues 元素：{type: missing|extra|order|name_mismatch, detail}
    """
    issues: list[dict[str, Any]] = []
    used_c: set[int] = set()
    mapping: list[Optional[int]] = []
    for cl in claimed:
        hit = None
        for j, ca in enumerate(canonical):
            if j in used_c:
                continue
            if same_person(cl, ca):
                hit = j
                break
        if hit is None:
            issues.append({"type": "extra", "detail": f"声称作者「{cl}」不在权威名单"})
            mapping.append(None)
        else:
            used_c.add(hit)
            mapping.append(hit)
    for j, ca in enumerate(canonical):
        if j not in used_c:
            issues.append({"type": "missing", "detail": f"权威作者「{ca}」未出现在声称名单"})
    matched = [m for m in mapping if m is not None]
    if matched != sorted(matched):
        issues.append({"type": "order", "detail": "作者顺序与权威来源不一致"})
    return {"ok": not issues, "issues": issues,
            "aligned": [{"claimed": cl, "canonical":
                         canonical[m] if m is not None else None}
                        for cl, m in zip(claimed, mapping)]}


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, norm_title(a), norm_title(b)).ratio()
