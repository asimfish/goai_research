"""多源学术检索与元数据归一化。

数据源：arXiv（Atom API）、OpenAlex、Semantic Scholar Graph、Crossref、DBLP。
统一 paper record：
    {source, id, title, authors[], year, venue, doi, arxiv_id, url, pdf_url,
     abstract, citation_count}
"""
from __future__ import annotations

import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from typing import Any, Optional

from . import http

S2_BASE = "https://api.semanticscholar.org/graph/v1"
S2_FIELDS = "title,authors,year,venue,externalIds,openAccessPdf,abstract,citationCount,url"


# ---------- 归一化 ----------

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def norm_title(s: str) -> str:
    s = strip_accents(s or "").lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def norm_arxiv_id(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = s.strip()
    s = re.sub(r"^(arxiv:|https?://arxiv\.org/(abs|pdf)/)", "", s, flags=re.I)
    return re.sub(r"v\d+$", "", s).strip("/") or None


def record(source: str, **kw: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "source": source, "id": None, "title": None, "authors": [],
        "year": None, "venue": None, "doi": None, "arxiv_id": None,
        "url": None, "pdf_url": None, "abstract": None, "citation_count": None,
    }
    base.update({k: v for k, v in kw.items() if v is not None})
    if base.get("doi"):
        base["doi"] = str(base["doi"]).lower().replace("https://doi.org/", "").strip()
    base["arxiv_id"] = norm_arxiv_id(base.get("arxiv_id"))
    return base


# ---------- arXiv ----------

_ATOM = "{http://www.w3.org/2005/Atom}"
_ARXIV = "{http://arxiv.org/schemas/atom}"


def _parse_arxiv_feed(xml_text: str) -> list[dict[str, Any]]:
    out = []
    root = ET.fromstring(xml_text)
    for entry in root.findall(f"{_ATOM}entry"):
        eid = (entry.findtext(f"{_ATOM}id") or "").rsplit("/abs/", 1)[-1]
        title = re.sub(r"\s+", " ", entry.findtext(f"{_ATOM}title") or "").strip()
        authors = [a.findtext(f"{_ATOM}name") or ""
                   for a in entry.findall(f"{_ATOM}author")]
        published = entry.findtext(f"{_ATOM}published") or ""
        year = int(published[:4]) if published[:4].isdigit() else None
        doi = entry.findtext(f"{_ARXIV}doi")
        abstract = re.sub(r"\s+", " ", entry.findtext(f"{_ATOM}summary") or "").strip()
        aid = norm_arxiv_id(eid)
        out.append(record(
            "arxiv", id=aid, title=title, authors=[a for a in authors if a],
            year=year, venue="arXiv", doi=doi, arxiv_id=aid,
            url=f"https://arxiv.org/abs/{aid}",
            pdf_url=f"https://arxiv.org/pdf/{aid}", abstract=abstract))
    return out


def search_arxiv(query: str, limit: int = 20) -> list[dict[str, Any]]:
    resp = http.get("https://export.arxiv.org/api/query", params={
        "search_query": f"all:{query}", "start": 0, "max_results": limit,
        "sortBy": "relevance"})
    return _parse_arxiv_feed(resp.text)


def arxiv_by_id(arxiv_id: str) -> Optional[dict[str, Any]]:
    aid = norm_arxiv_id(arxiv_id)
    resp = http.get("https://export.arxiv.org/api/query",
                    params={"id_list": aid, "max_results": 1})
    hits = _parse_arxiv_feed(resp.text)
    return hits[0] if hits else None


# ---------- OpenAlex ----------

def _oa_abstract(inv: Optional[dict[str, list[int]]]) -> Optional[str]:
    if not inv:
        return None
    pos: dict[int, str] = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos)) or None


def _parse_oa_work(w: dict[str, Any]) -> dict[str, Any]:
    ids = w.get("ids") or {}
    loc = w.get("best_oa_location") or {}
    src = ((w.get("primary_location") or {}).get("source") or {})
    return record(
        "openalex",
        id=(w.get("id") or "").rsplit("/", 1)[-1],
        title=w.get("display_name"),
        authors=[(a.get("author") or {}).get("display_name") or ""
                 for a in (w.get("authorships") or [])],
        year=w.get("publication_year"),
        venue=src.get("display_name"),
        doi=ids.get("doi"),
        arxiv_id=norm_arxiv_id((loc.get("landing_page_url") or "")
                               if "arxiv.org" in (loc.get("landing_page_url") or "") else None),
        url=ids.get("doi") or w.get("id"),
        pdf_url=loc.get("pdf_url"),
        abstract=_oa_abstract(w.get("abstract_inverted_index")),
        citation_count=w.get("cited_by_count"))


def search_openalex(query: str, limit: int = 20,
                    year_from: Optional[int] = None,
                    year_to: Optional[int] = None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"search": query, "per-page": min(limit, 50),
                              "mailto": http.CONTACT}
    filters = []
    if year_from:
        filters.append(f"from_publication_date:{year_from}-01-01")
    if year_to:
        filters.append(f"to_publication_date:{year_to}-12-31")
    if filters:
        params["filter"] = ",".join(filters)
    data = http.get_json("https://api.openalex.org/works", params=params)
    return [_parse_oa_work(w) for w in data.get("results", [])]


def openalex_by_doi(doi: str) -> Optional[dict[str, Any]]:
    doi = doi.lower().replace("https://doi.org/", "")
    try:
        w = http.get_json(f"https://api.openalex.org/works/doi:{doi}",
                          params={"mailto": http.CONTACT})
    except Exception:
        return None
    return _parse_oa_work(w)


def openalex_references(openalex_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """该工作引用的文献（向后滚雪球）。"""
    w = http.get_json(f"https://api.openalex.org/works/{openalex_id}",
                      params={"mailto": http.CONTACT})
    ref_ids = [r.rsplit("/", 1)[-1] for r in (w.get("referenced_works") or [])][:limit]
    out = []
    for chunk_start in range(0, len(ref_ids), 25):
        chunk = ref_ids[chunk_start:chunk_start + 25]
        data = http.get_json("https://api.openalex.org/works", params={
            "filter": "openalex_id:" + "|".join(chunk),
            "per-page": 25, "mailto": http.CONTACT})
        out.extend(_parse_oa_work(x) for x in data.get("results", []))
    return out


def openalex_citers(openalex_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """引用了该工作的文献（向前滚雪球）。"""
    data = http.get_json("https://api.openalex.org/works", params={
        "filter": f"cites:{openalex_id}", "per-page": min(limit, 50),
        "sort": "cited_by_count:desc", "mailto": http.CONTACT})
    return [_parse_oa_work(w) for w in data.get("results", [])]


# ---------- Semantic Scholar ----------

def _s2_headers() -> dict[str, str]:
    key = os.environ.get("S2_API_KEY") or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    return {"x-api-key": key} if key else {}


def _parse_s2(p: dict[str, Any]) -> dict[str, Any]:
    ext = p.get("externalIds") or {}
    return record(
        "semanticscholar", id=p.get("paperId"), title=p.get("title"),
        authors=[a.get("name") or "" for a in (p.get("authors") or [])],
        year=p.get("year"), venue=p.get("venue") or None,
        doi=ext.get("DOI"), arxiv_id=ext.get("ArXiv"),
        url=p.get("url"),
        pdf_url=(p.get("openAccessPdf") or {}).get("url"),
        abstract=p.get("abstract"), citation_count=p.get("citationCount"))


def search_s2(query: str, limit: int = 20,
              year_from: Optional[int] = None,
              year_to: Optional[int] = None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"query": query, "limit": min(limit, 100),
                              "fields": S2_FIELDS}
    if year_from or year_to:
        params["year"] = f"{year_from or ''}-{year_to or ''}"
    data = http.get_json(f"{S2_BASE}/paper/search", params=params,
                         headers=_s2_headers())
    return [_parse_s2(p) for p in data.get("data", [])]


def s2_neighbors(paper_ref: str, direction: str = "references",
                 limit: int = 50) -> list[dict[str, Any]]:
    """direction: references（被它引用）| citations（引用它）。paper_ref 可为
    S2 id / DOI:xx / ARXIV:xx。"""
    assert direction in ("references", "citations")
    data = http.get_json(
        f"{S2_BASE}/paper/{paper_ref}/{direction}",
        params={"fields": S2_FIELDS, "limit": min(limit, 100)},
        headers=_s2_headers())
    key = "citedPaper" if direction == "references" else "citingPaper"
    return [_parse_s2(row[key]) for row in data.get("data", []) if row.get(key)]


# ---------- Crossref ----------

def _parse_crossref(it: dict[str, Any]) -> dict[str, Any]:
    year = None
    for k in ("published-print", "published-online", "issued", "created"):
        parts = ((it.get(k) or {}).get("date-parts") or [[None]])[0]
        if parts and parts[0]:
            year = parts[0]
            break
    authors = []
    for a in it.get("author") or []:
        name = " ".join(x for x in (a.get("given"), a.get("family")) if x)
        if name:
            authors.append(name)
    return record(
        "crossref", id=it.get("DOI"),
        title=(it.get("title") or [None])[0],
        authors=authors, year=year,
        venue=(it.get("container-title") or [None])[0] or it.get("event", {}).get("name")
        if isinstance(it.get("event"), dict) else (it.get("container-title") or [None])[0],
        doi=it.get("DOI"), url=it.get("URL"),
        citation_count=it.get("is-referenced-by-count"))


def search_crossref(query: str, limit: int = 20) -> list[dict[str, Any]]:
    data = http.get_json("https://api.crossref.org/works", params={
        "query.bibliographic": query, "rows": min(limit, 50),
        "mailto": http.CONTACT})
    return [_parse_crossref(it) for it in data.get("message", {}).get("items", [])]


def crossref_by_doi(doi: str) -> Optional[dict[str, Any]]:
    doi = doi.lower().replace("https://doi.org/", "")
    try:
        data = http.get_json(f"https://api.crossref.org/works/{doi}",
                             params={"mailto": http.CONTACT})
    except Exception:
        return None
    return _parse_crossref(data.get("message", {}))


# ---------- DBLP ----------

def search_dblp(query: str, limit: int = 20) -> list[dict[str, Any]]:
    data = http.get_json("https://dblp.org/search/publ/api",
                         params={"q": query, "format": "json", "h": min(limit, 50)})
    hits = (((data.get("result") or {}).get("hits") or {}).get("hit") or [])
    out = []
    for h in hits:
        info = h.get("info") or {}
        raw_authors = ((info.get("authors") or {}).get("author") or [])
        if isinstance(raw_authors, dict):
            raw_authors = [raw_authors]
        authors = [re.sub(r"\s+\d{4}$", "", a.get("text", "")) for a in raw_authors]
        out.append(record(
            "dblp", id=info.get("key"), title=(info.get("title") or "").rstrip("."),
            authors=[a for a in authors if a],
            year=int(info["year"]) if str(info.get("year", "")).isdigit() else None,
            venue=info.get("venue"), doi=info.get("doi"),
            url=info.get("ee") or info.get("url")))
    return out


# ---------- 合并去重 ----------

def dedup_merge(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按 doi > arxiv_id > 归一化标题 去重；后见记录只补空字段，来源累加。"""
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for r in records:
        key = (r.get("doi") or r.get("arxiv_id")
               or norm_title(r.get("title") or "") or f"anon:{id(r)}")
        if key not in merged:
            r = dict(r)
            r["sources"] = [r.pop("source")]
            merged[key] = r
            order.append(key)
        else:
            base = merged[key]
            src = r.get("source")
            if src and src not in base["sources"]:
                base["sources"].append(src)
            for f, v in r.items():
                if f in ("source", "sources"):
                    continue
                if base.get(f) in (None, [], "") and v not in (None, [], ""):
                    base[f] = v
    return [merged[k] for k in order]
