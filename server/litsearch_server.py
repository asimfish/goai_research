"""goai-litsearch MCP server —— 本地全文 + 多源检索 / PDF / BibTeX。

启动：python server/litsearch_server.py（stdio）
环境：GOAI_EMAIL（polite pool 联系邮箱）、S2_API_KEY（可选，提额）
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.core.mcp_compat import FastMCP

from server.core import bibtex as bib
from server.core import http as ghttp
from server.core import local_corpus
from server.core import sources as src

mcp = FastMCP("goai-litsearch")

ALL_SOURCES = ("arxiv", "openalex", "semanticscholar", "crossref", "dblp")
SOURCE_ALIASES = {"s2": "semanticscholar"}
_ARXIV_DOI = re.compile(r"^10\.48550/arxiv\.(.+)$", re.I)
DEFAULT_SEARCH_ABSTRACT_CHARS = 1200


def _ws(*parts: str) -> str:
    """默认产物路径落到 GOAI_WORKSPACE（README 约定）下；显式传参不受影响。"""
    return os.path.join(os.environ.get("GOAI_WORKSPACE", "workspace"), *parts)


def _dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _compact_search_records(records: list[dict]) -> list[dict]:
    """Limit verbose abstracts in MCP search responses.

    Search is a discovery primitive, not a full-text transport.  Returning an
    unbounded abstract for every source/result made a single agent turn exceed
    hundreds of thousands of input tokens.  Exact DOI lookup remains available
    when a selected record needs richer metadata.
    """
    limit = max(200, int(os.environ.get(
        "GOAI_SEARCH_ABSTRACT_CHARS", str(DEFAULT_SEARCH_ABSTRACT_CHARS)
    )))
    out = []
    for record in records:
        row = dict(record)
        abstract = row.get("abstract")
        if isinstance(abstract, str) and len(abstract) > limit:
            row["abstract"] = abstract[:limit].rstrip() + " …[truncated]"
            row["abstract_truncated"] = True
        out.append(row)
    return out


@mcp.tool()
def local_corpus_status() -> str:
    """检查离线全文语料及 DuckDB-Parquet / ripgrep 后端是否可用。"""
    return _dumps(local_corpus.corpus_status())


@mcp.tool()
def grep_local_corpus(query: str, max_results: int = 20,
                      context_lines: int = 1, case_sensitive: bool = False,
                      regex: bool = False, file_glob: str = "*.md") -> str:
    """在私有 NAS 语料或公开裁剪语料中做流式全文检索。

    Args:
        query: 文本或正则表达式。
        max_results: 全局返回上限（1--100）；达到后立即停止扫描。
        context_lines: 每个命中前后附带的行数（0--10）。
        case_sensitive: 是否区分大小写。
        regex: false 时按字面量检索；true 时使用正则。
        file_glob: Markdown 后端的文件过滤；Parquet 后端忽略此项。
    Returns:
        JSON，含文档路径、行号、命中文本、上下文和超时/截断状态。
    """
    return _dumps(local_corpus.search_local_corpus(
        query,
        max_results=max_results,
        context_lines=context_lines,
        case_sensitive=case_sensitive,
        regex=regex,
        file_glob=file_glob,
    ))


@mcp.tool()
def read_local_document(path: str, start_line: int = 1,
                        end_line: int = 200) -> str:
    """读取全文检索命中的本地文献片段；路径必须位于配置的语料根目录内。"""
    return _dumps(local_corpus.read_local_document(
        path,
        start_line=start_line,
        end_line=end_line,
    ))


@mcp.tool()
def lookup_local_doi(doi: str, start_line: int = 1,
                     end_line: int = 200) -> str:
    """用私有 DOI→UUID→Parquet 分片索引直接读取一篇本地全文；未命中时如实返回。"""
    return _dumps(local_corpus.lookup_local_doi(
        doi,
        start_line=start_line,
        end_line=end_line,
    ))


@mcp.tool()
def search_papers(query: str, sources: str = "arxiv,openalex,semanticscholar",
                  limit_per_source: int = 15,
                  year_from: Optional[int] = None,
                  year_to: Optional[int] = None) -> str:
    """跨源检索文献并合并去重。

    Args:
        query: 检索式（英文关键词效果最好；一次一个主题面）
        sources: 逗号分隔，可选 arxiv/openalex/semanticscholar(别名 s2)/crossref/dblp
        limit_per_source: 每源条数上限
        year_from / year_to: 年份过滤（arxiv/crossref/dblp 不支持时忽略）
    Returns:
        JSON {query, total, papers: [统一 record，含 sources 命中列表]}
    """
    query = (query or "").strip()
    if not query:
        return _dumps({"query": query, "total": 0,
                       "errors": {"query": "空查询：请提供非空检索式"}, "papers": []})
    wanted = [SOURCE_ALIASES.get(n, n)
              for n in (s.strip().lower() for s in sources.split(",")) if n]
    records, errors = [], {}
    dispatch = {
        "arxiv": lambda: src.search_arxiv(query, limit_per_source),
        "openalex": lambda: src.search_openalex(query, limit_per_source,
                                                year_from, year_to),
        "semanticscholar": lambda: src.search_s2(query, limit_per_source,
                                                 year_from, year_to),
        "crossref": lambda: src.search_crossref(query, limit_per_source),
        "dblp": lambda: src.search_dblp(query, limit_per_source),
    }
    for name in wanted:
        if name not in dispatch:
            errors[name] = f"未知源，可选 {ALL_SOURCES}"
            continue
        try:
            records.extend(dispatch[name]())
        except Exception as exc:  # 单源失败不拖垮整体，但必须如实上报
            errors[name] = f"{type(exc).__name__}: {exc}"
    merged = src.dedup_merge(records)
    if year_from or year_to:
        merged = [r for r in merged
                  if r.get("year") is None
                  or ((not year_from or r["year"] >= year_from)
                      and (not year_to or r["year"] <= year_to))]
    return _dumps({"query": query, "total": len(merged),
                   "errors": errors, "papers": _compact_search_records(merged)})


@mcp.tool()
def snowball(seed: str, direction: str = "both", limit: int = 30) -> str:
    """从种子论文做引文滚雪球扩展（查全的关键手段）。

    Args:
        seed: DOI（10.xxxx/...）/ arXiv id（2402.xxxxx）/ OpenAlex id（Wxxxx）
        direction: references（它引用谁）| citations（谁引用它）| both
        limit: 每个方向的条数上限
    Returns:
        JSON {seed, references: [...], citations: [...]}
    """
    seed = seed.strip()
    out = {"seed": seed, "references": [], "citations": [], "errors": {}}

    def _via_openalex(wid: str) -> None:
        if direction in ("references", "both"):
            out["references"] = src.openalex_references(wid, limit)
        if direction in ("citations", "both"):
            out["citations"] = src.openalex_citers(wid, limit)

    if re.match(r"^W\d+$", seed):  # OpenAlex
        try:
            _via_openalex(seed)
        except Exception as exc:
            out["errors"]["openalex"] = str(exc)
        return _dumps(out)
    m = _ARXIV_DOI.match(seed)
    if m:  # arXiv 代发 DOI：S2 只认 ARXIV:id，DOI:10.48550/... 会 404
        ref = f"ARXIV:{src.norm_arxiv_id(m.group(1))}"
    elif re.match(r"^10\.", seed):
        ref = f"DOI:{seed}"
    elif re.match(r"^\d{4}\.\d{4,5}", seed):
        ref = f"ARXIV:{src.norm_arxiv_id(seed)}"
    else:
        ref = seed  # 视为 S2 paperId
    try:
        if direction in ("references", "both"):
            out["references"] = src.s2_neighbors(ref, "references", limit)
        if direction in ("citations", "both"):
            out["citations"] = src.s2_neighbors(ref, "citations", limit)
    except Exception as exc:
        out["errors"]["semanticscholar"] = str(exc)
        # S2 无 key 时限流常态化：能定位 DOI 的种子改走 OpenAlex 兜底
        doi = (f"10.48550/arxiv.{src.norm_arxiv_id(seed)}"
               if ref.startswith("ARXIV:") else seed if ref.startswith("DOI:") else None)
        if doi:
            try:
                w = src.openalex_by_doi(doi)
                wid = (w or {}).get("id") or ""
                if str(wid).startswith("W"):
                    _via_openalex(str(wid))
                    out["fallback"] = f"semanticscholar 不可用，已用 openalex:{wid} 兜底"
            except Exception as exc2:
                out["errors"]["openalex"] = str(exc2)
    out["references"] = _compact_search_records(out["references"])
    out["citations"] = _compact_search_records(out["citations"])
    return _dumps(out)


@mcp.tool()
def lookup(identifier: str) -> str:
    """按权威标识精确查元数据。identifier 支持 DOI 或 arXiv id。"""
    ident = identifier.strip()
    hits = []
    arxiv_doi = _ARXIV_DOI.match(ident)
    if arxiv_doi:  # arXiv 代发 DOI：权威源是 arXiv 本身（Crossref 不收录 DataCite DOI）
        try:
            r = src.arxiv_by_id(arxiv_doi.group(1))
            if r:
                hits.append(r)
        except Exception:
            pass
    if re.match(r"^10\.", ident):
        for fn in (src.crossref_by_doi, src.openalex_by_doi):
            try:
                r = fn(ident)
                if r:
                    hits.append(r)
            except Exception:
                pass
    elif not arxiv_doi:
        try:
            r = src.arxiv_by_id(ident)
            if r:
                hits.append(r)
        except Exception:
            pass
    return _dumps({"identifier": ident, "found": bool(hits),
                   "records": src.dedup_merge(hits)})


@mcp.tool()
def download_pdf(url: str, filename: str,
                 out_dir: Optional[str] = None) -> str:
    """下载开放获取 PDF 到文献库。

    Args:
        url: pdf_url（来自 search/snowball 结果；arXiv id 也可直接给）
        filename: 保存名（建议 citation key，如 vaswani2017attention.pdf）
        out_dir: 保存目录（默认 $GOAI_WORKSPACE/library/pdfs）
    """
    out_dir = out_dir or _ws("library", "pdfs")
    if re.match(r"^\d{4}\.\d{4,5}", url):
        url = f"https://arxiv.org/pdf/{src.norm_arxiv_id(url)}"
    if not filename.endswith(".pdf"):
        filename += ".pdf"
    dest = os.path.join(out_dir, filename)
    try:
        info = ghttp.download(url, dest)
    except Exception as exc:
        if os.path.exists(dest):
            os.remove(dest)  # 半截文件不留在文献库
        return _dumps({"ok": False, "url": url,
                       "error": f"{type(exc).__name__}: {exc}",
                       "hint": "付费墙/反爬按 fail-closed 处理：如实报告，勿绕过；"
                               "改用 arXiv/OA 副本或让作者提供来源。"})
    is_pdf = "pdf" in info["content_type"].lower() or info["bytes"] > 10_000
    with open(dest, "rb") as f:
        magic_ok = f.read(5) == b"%PDF-"
    if not magic_ok:
        os.remove(dest)
        return _dumps({"ok": False, "url": url,
                       "error": "响应不是 PDF（可能是登录页/challenge 页），已丢弃",
                       "content_type": info["content_type"]})
    return _dumps({"ok": True, **info, "looks_like_pdf": is_pdf})


@mcp.tool()
def save_to_library(papers_json: str,
                    library_path: Optional[str] = None) -> str:
    """把检索结果并入文献库 papers.jsonl（按 doi/arxiv/标题去重）。

    Args:
        papers_json: JSON 数组或 {papers: [...]} 
        library_path: 文献库 jsonl 路径（默认 $GOAI_WORKSPACE/library/papers.jsonl）
    """
    library_path = library_path or _ws("library", "papers.jsonl")
    data = json.loads(papers_json)
    incoming = data["papers"] if isinstance(data, dict) else data
    os.makedirs(os.path.dirname(library_path) or ".", exist_ok=True)
    lock_path = library_path + ".lock"
    with open(lock_path, "a+", encoding="utf-8") as lock_handle:
        try:
            import fcntl

            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass
        existing = []
        if os.path.exists(library_path):
            with open(library_path, encoding="utf-8") as f:
                existing = [json.loads(line) for line in f if line.strip()]
        # 锁覆盖完整的read-modify-write周期；临时文件+replace避免半截JSONL。
        merged = src.dedup_merge(existing + incoming)
        tmp_path = f"{library_path}.tmp.{os.getpid()}"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                for record in merged:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, library_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        try:
            import fcntl

            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        except (ImportError, OSError):
            pass
    return _dumps({"ok": True, "library": library_path,
                   "before": len(existing), "added": len(merged) - len(existing),
                   "total": len(merged)})


@mcp.tool()
def export_bibtex(library_path: Optional[str] = None,
                  out_path: Optional[str] = None,
                  overrides_path: Optional[str] = None) -> str:
    """把文献库导出为 references.bib（key = 一作姓+年份+标题首词）。

    路径默认取 $GOAI_WORKSPACE/library/ 下的 papers.jsonl / references.bib。
    """
    library_path = library_path or _ws("library", "papers.jsonl")
    out_path = out_path or _ws("library", "references.bib")
    if not os.path.exists(library_path):
        return _dumps({"ok": False, "error": f"文献库不存在: {library_path}"})
    with open(library_path, encoding="utf-8") as f:
        papers = [json.loads(line) for line in f if line.strip()]
    overrides_path = overrides_path or os.path.join(
        os.path.dirname(library_path), "metadata_overrides.json"
    )
    overrides = {}
    if os.path.exists(overrides_path):
        with open(overrides_path, encoding="utf-8") as f:
            raw_overrides = json.load(f)
        overrides = {
            str(doi).lower().replace("https://doi.org/", ""): values
            for doi, values in raw_overrides.items()
        }
    papers = [
        {**paper, **overrides.get(str(paper.get("doi") or "").lower(), {})}
        for paper in papers
    ]
    entries, seen = [], set()
    for r in papers:
        entry = bib.record_to_bibtex(r)
        key = entry.split("{", 1)[1].split(",", 1)[0]
        if key in seen:
            key2 = key + (r.get("arxiv_id") or "x").replace(".", "")[-4:]
            entry = entry.replace("{" + key + ",", "{" + key2 + ",", 1)
            key = key2
        seen.add(key)
        entries.append(entry)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(entries) + "\n")
    return _dumps({"ok": True, "bib": out_path, "entries": len(entries),
                   "metadata_overrides": len(overrides)})


@mcp.tool()
def coverage_report(subtopics: str,
                    library_path: Optional[str] = None) -> str:
    """查全率体检：逐子主题统计文献库命中量，暴露覆盖缺口。

    Args:
        subtopics: JSON 数组，每项 {name, keywords: [...]}（keywords 用于标题/摘要匹配）
        library_path: 文献库 jsonl（默认 $GOAI_WORKSPACE/library/papers.jsonl）
    Returns:
        JSON 每个子主题的命中数 / 年份分布 / 缺口告警（<5 视为缺口）
    """
    topics = json.loads(subtopics)
    library_path = library_path or _ws("library", "papers.jsonl")
    papers = []
    if os.path.exists(library_path):
        with open(library_path, encoding="utf-8") as f:
            papers = [json.loads(line) for line in f if line.strip()]
    report = []
    for t in topics:
        kws = [k.lower() for k in t.get("keywords", [])]
        hits = [p for p in papers
                if any(k in ((p.get("title") or "") + " "
                             + (p.get("abstract") or "")).lower() for k in kws)]
        years = sorted({p.get("year") for p in hits if p.get("year")})
        report.append({"subtopic": t.get("name"), "hits": len(hits),
                       "year_span": [years[0], years[-1]] if years else None,
                       "gap": len(hits) < 5,
                       "sample": [p.get("title") for p in hits[:3]]})
    gaps = [r["subtopic"] for r in report if r["gap"]]
    return _dumps({"library_size": len(papers), "subtopics": report,
                   "gaps": gaps,
                   "verdict": "PASS" if not gaps else "GAPS_FOUND",
                   "advice": "对 gaps 子主题换关键词重搜 + 对已命中论文 snowball" if gaps else "覆盖达标"})


if __name__ == "__main__":
    mcp.run()
