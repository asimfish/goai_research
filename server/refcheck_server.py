"""goai-refcheck MCP server —— 引用真实性快速核查（存在性 / 元数据 / 作者名单+顺序）。

两档核查体系中的「快速档」：回环内高频调用，权威源为
Crossref（DOI）/ arXiv / OpenAlex / DBLP。
「深度档」为 super_ref 四隔离 agent 审计（若本机可用），用 deep_audit_info 查询。

裁决口径（参考 citation-audit / super_ref）：
  PASS        三轴干净
  FIX         元数据漂移（作者缩写/年份±1/venue 记法），给出修正后 BibTeX
  MISMATCH    标题能对上但作者名单严重不符（遗漏/伪造/乱序）——高危
  UNVERIFIED  找不到权威记录（可能是幻觉引用）——fail-closed，不猜测
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.core.mcp_compat import FastMCP

from server.core import bibtex as bib
from server.core import sources as src

mcp = FastMCP("goai-refcheck")

TITLE_MATCH = 0.92
TITLE_SUSPECT = 0.75


def _dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _author_overlap(claimed: list[str], candidate: dict[str, Any]) -> float:
    """声称作者与候选记录作者的重合率（0-1），用于同分候选决胜。"""
    cand = candidate.get("authors") or []
    if not claimed or not cand:
        return 0.0
    used: set[int] = set()
    hit = 0
    for cl in claimed:
        for j, ca in enumerate(cand):
            if j not in used and bib.same_person(cl, ca):
                used.add(j)
                hit += 1
                break
    return hit / len(claimed)


def _year_distance(fields: dict[str, str], candidate: dict[str, Any]) -> int:
    try:
        return abs(int(fields.get("year", "")) - int(candidate.get("year")))
    except (TypeError, ValueError):
        return 99  # 任一侧无年份 → 劣后于年份贴近的候选


def _authoritative_lookup(
        fields: dict[str, str]) -> tuple[Optional[dict], list[dict], Optional[dict]]:
    """按权威路由取规范记录：DOI > arXiv > 标题检索(crossref+dblp+openalex)。

    Returns:
        (canonical, near_misses, id_conflict)
        id_conflict: DOI/arXiv 可解析、但解析结果与声称标题不符时的权威记录
        （典型场景：条目挂了另一篇真实论文的 DOI）。
    """
    id_hits: list[dict[str, Any]] = []
    doi = fields.get("doi")
    if doi:
        for fn in (src.crossref_by_doi, src.openalex_by_doi):
            try:
                r = fn(doi)
                if r:
                    id_hits.append(r)
            except Exception:
                pass
    aid = fields.get("eprint") or fields.get("arxiv")
    if not id_hits and aid:
        try:
            r = src.arxiv_by_id(aid)
            if r:
                id_hits.append(r)
        except Exception:
            pass
    candidates = list(id_hits)
    title = fields.get("title", "")
    if not candidates and title:
        # 核查是「核对已知标题」而非发现式检索：crossref/openalex/arxiv 用
        # 引号短语查询，防止高频词标题被同名蹭热点文淹没（实测「Attention Is
        # All You Need」裸查询三源 top5 均无 2017 正版，OpenAlex 反而返回
        # sim=1.0 的 2025 盗版重印记录）。DBLP 语法不吃引号，保持裸标题。
        # arXiv 必须在列：NeurIPS/ICLR/ICML 等会议不注册 Crossref。
        phrase = '"' + title.replace('"', " ").strip() + '"'
        for fn in (lambda: src.search_crossref(phrase, 5),
                   lambda: src.search_dblp(title, 5),
                   lambda: src.search_openalex(phrase, 5),
                   lambda: src.search_arxiv(phrase, 5)):
            try:
                candidates.extend(fn())
            except Exception:
                pass
    if not candidates:
        return None, [], None
    # 标题相似度为主；同名多记录（重印/盗版/编辑评论）按作者重合度、
    # 年份贴近度决胜，避免盲选检索顺序靠前的野记录。
    claimed_authors = bib.split_authors(fields.get("author", ""))
    scored = sorted(
        ((bib.title_similarity(title, c.get("title") or ""),
          _author_overlap(claimed_authors, c),
          -_year_distance(fields, c),
          c)
         for c in candidates if c.get("title")),
        key=lambda x: (-x[0], -x[1], -x[2]))
    near = [c for *_, c in scored[:5]]
    # 接受为 canonical 的门槛：标题基本一致（≥MATCH，视为同一篇）；或标题
    # 疑似（≥SUSPECT）且作者有重合（同篇的版本漂移）。疑似区间内作者零重合
    # 的记录不是「作者不符的同一篇」而是「另一篇」，不配当权威基准 ——
    # 否则一条正确引用会被陌生记录数落成 MISMATCH（fail-closed 归 UNVERIFIED）。
    if scored:
        sim, overlap = scored[0][0], scored[0][1]
        if sim >= TITLE_MATCH or (sim >= TITLE_SUSPECT
                                  and (overlap > 0 or not claimed_authors)):
            return {"score": round(sim, 3), **scored[0][3]}, near, None
    # 走到这里：或一无所获，或 id 路由解析成功但指向别的论文
    id_conflict = None
    if id_hits:
        id_conflict = max(
            id_hits, key=lambda c: bib.title_similarity(title, c.get("title") or ""))
    return None, near, id_conflict


def _verify_fields(fields: dict[str, str]) -> dict[str, Any]:
    claimed_title = fields.get("title", "")
    claimed_authors = bib.split_authors(fields.get("author", ""))
    claimed_year = fields.get("year", "")

    canonical, near, id_conflict = _authoritative_lookup(fields)
    if canonical is None:
        if id_conflict is not None:
            # DOI/arXiv 能解析，但指向另一篇论文 —— 高危：标识符与标题张冠李戴
            return {
                "verdict": "MISMATCH",
                "reason": "doi/arxiv 标识符可解析，但指向另一篇论文，与声称标题不符；"
                          "不给自动修正（无法判断该留标题还是留标识符），须人工裁决",
                "issues": [{
                    "axis": "ID", "type": "id_conflict",
                    "detail": f"声称标题「{claimed_title}」 vs 标识符解析出"
                              f"「{id_conflict.get('title')}」"
                              f"(doi={id_conflict.get('doi')}, "
                              f"year={id_conflict.get('year')})"}],
                "id_resolved": {k: id_conflict.get(k) for k in
                                ("title", "authors", "year", "venue", "doi",
                                 "arxiv_id", "url")},
                "action": "核对 DOI/arXiv 号属于哪篇论文；改标识符或改条目元数据后重试",
            }
        return {
            "verdict": "UNVERIFIED",
            "reason": "在 Crossref/arXiv/OpenAlex/DBLP 均未找到可信匹配；"
                      "可能为幻觉引用或元数据严重失真",
            "near_misses": [{"title": c.get("title"), "year": c.get("year"),
                             "doi": c.get("doi")} for c in near[:3]],
            "action": "提供 doi/arxiv_id 重试，或人工确认后删除该引用",
        }

    issues: list[dict[str, Any]] = []
    title_sim = canonical.pop("score")
    if title_sim < TITLE_MATCH:
        issues.append({"axis": "TITLE", "type": "drift",
                       "detail": f"标题相似度 {title_sim}，可能存在版本漂移",
                       "canonical": canonical.get("title")})

    author_cmp = bib.compare_authors(claimed_authors, canonical.get("authors") or [])
    hard_author = [i for i in author_cmp["issues"]
                   if i["type"] in ("missing", "extra", "order")]
    for i in author_cmp["issues"]:
        issues.append({"axis": "AUTHORS", **i})

    canon_year = canonical.get("year")
    if claimed_year and canon_year:
        try:
            dy = abs(int(claimed_year) - int(canon_year))
            if dy >= 2:
                issues.append({"axis": "YEAR", "type": "mismatch",
                               "detail": f"声称 {claimed_year} vs 权威 {canon_year}"})
            elif dy == 1:
                issues.append({"axis": "YEAR", "type": "off_by_one",
                               "detail": f"声称 {claimed_year} vs 权威 {canon_year}"
                                         "（常见于 arXiv 年份 vs 会议年份，需选定口径）"})
        except ValueError:
            pass

    # 单源记录只有 source（str），dedup_merge 后才有 sources（list）——两者都认
    canon_sources = (canonical.get("sources")
                     or ([canonical["source"]] if canonical.get("source") else []))
    claimed_venue = (fields.get("booktitle") or fields.get("journal") or "").lower()
    canon_venue = (canonical.get("venue") or "").lower()
    if claimed_venue and canon_venue and canon_sources != ["arxiv"]:
        if (src.norm_title(claimed_venue) != src.norm_title(canon_venue)
                and src.norm_title(canon_venue) not in src.norm_title(claimed_venue)
                and src.norm_title(claimed_venue) not in src.norm_title(canon_venue)):
            issues.append({"axis": "VENUE", "type": "drift",
                           "detail": f"声称「{claimed_venue}」vs 权威「{canon_venue}」；"
                                     "注意 arXiv 路由通常不能证实 venue，会议口径以出版方为准"})

    # 标识符一致性：声称的 doi/arxiv 与权威记录不符 = 幻觉标识符（可自动修正）
    claimed_doi = (fields.get("doi") or "").lower().replace(
        "https://doi.org/", "").strip()
    canon_doi = (canonical.get("doi") or "").lower()
    if claimed_doi and canon_doi and claimed_doi != canon_doi:
        issues.append({"axis": "ID", "type": "doi_mismatch",
                       "detail": f"声称 doi {claimed_doi} vs 权威 {canon_doi}"
                                 "（声称 DOI 解析不出或不属于该文）"})
    claimed_aid = src.norm_arxiv_id(fields.get("eprint") or fields.get("arxiv"))
    canon_aid = canonical.get("arxiv_id")
    if claimed_aid and canon_aid and claimed_aid != canon_aid:
        issues.append({"axis": "ID", "type": "arxiv_mismatch",
                       "detail": f"声称 arXiv {claimed_aid} vs 权威 {canon_aid}"})

    if any(i["type"] in ("missing", "extra") for i in hard_author):
        verdict = "MISMATCH"
    elif issues:
        verdict = "FIX"
    else:
        verdict = "PASS"

    fixed = None
    if verdict in ("FIX", "MISMATCH"):
        fixed = bib.record_to_bibtex(canonical)
    return {"verdict": verdict, "title_similarity": title_sim,
            "canonical": {**{k: canonical.get(k) for k in
                             ("title", "authors", "year", "venue", "doi",
                              "arxiv_id", "url")},
                          "sources": canon_sources},
            "issues": issues, "suggested_bibtex": fixed}


@mcp.tool()
def verify_entry(bibtex_entry: str) -> str:
    """核查单条 BibTeX 引用的真实性（存在性/标题/作者名单与顺序/年份/venue）。

    Args:
        bibtex_entry: 完整 @xxx{key, ...} 条目文本
    Returns:
        JSON {key, verdict: PASS|FIX|MISMATCH|UNVERIFIED, issues, canonical,
              suggested_bibtex}
    """
    entries = bib.parse_bibtex(bibtex_entry)
    if not entries:
        return _dumps({"verdict": "ERROR", "error": "无法解析 BibTeX 条目"})
    e = entries[0]
    result = _verify_fields(e["fields"])
    return _dumps({"key": e["key"], **result})


@mcp.tool()
def verify_bib_file(bib_path: str, out_dir: str = "workspace/state") -> str:
    """批量核查 .bib 文件，产出 CITATION_AUDIT.json 与人读报告 CITATION_AUDIT.md。

    Args:
        bib_path: references.bib 路径
        out_dir: 审计产物目录（默认值在设置了 GOAI_WORKSPACE 时锚定为
            $GOAI_WORKSPACE/state，避免依赖 MCP server 进程的 CWD）
    Returns:
        JSON 汇总 {total, counts, gate: PASS|FAIL, report_md, report_json}
    """
    if out_dir == "workspace/state" and os.environ.get("GOAI_WORKSPACE"):
        out_dir = os.path.join(os.environ["GOAI_WORKSPACE"], "state")
    if not os.path.exists(bib_path):
        return _dumps({"ok": False, "error": f"文件不存在: {bib_path}"})
    with open(bib_path, encoding="utf-8") as f:
        entries = bib.parse_bibtex(f.read())
    if not entries:
        return _dumps({"ok": False, "total": 0,
                       "error": "bib 文件为空或未解析出任何条目；"
                                "fail-closed：空引用库不发 PASS 闸门"})
    per_entry = []
    counts = {"PASS": 0, "FIX": 0, "MISMATCH": 0, "UNVERIFIED": 0, "ERROR": 0}
    for e in entries:
        try:
            r = _verify_fields(e["fields"])
        except Exception as exc:
            r = {"verdict": "ERROR", "reason": f"{type(exc).__name__}: {exc}"}
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        per_entry.append({"key": e["key"], **r})

    gate = "PASS" if (counts["MISMATCH"] == 0 and counts["UNVERIFIED"] == 0
                      and counts["ERROR"] == 0) else "FAIL"
    audit = {"audit_skill": "goai-refcheck", "bib_file": bib_path,
             "total": len(entries), "counts": counts, "gate": gate,
             "per_entry": per_entry}
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "CITATION_AUDIT.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)

    lines = [f"# 引用核查报告\n\n- bib: `{bib_path}`\n- 条目: {len(entries)}",
             f"- 裁决分布: {counts}\n- 闸门: **{gate}**\n"]
    for r in per_entry:
        if r["verdict"] == "PASS":
            continue
        lines.append(f"## {r['verdict']}: `{r['key']}`")
        for i in r.get("issues", []):
            lines.append(f"- [{i.get('axis', '?')}] {i.get('detail', i.get('type'))}")
        if r.get("reason"):
            lines.append(f"- {r['reason']}")
        if r.get("suggested_bibtex"):
            lines.append("\n```bibtex\n" + r["suggested_bibtex"] + "\n```")
        lines.append("")
    md_path = os.path.join(out_dir, "CITATION_AUDIT.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return _dumps({"total": len(entries), "counts": counts, "gate": gate,
                   "report_json": json_path, "report_md": md_path,
                   "next": "MISMATCH/UNVERIFIED 条目必须人工处理或走 super_ref 深度审计；"
                           "FIX 条目可用 suggested_bibtex 替换后复跑"})


@mcp.tool()
def deep_audit_info() -> str:
    """查询本机 super_ref 深度审计（四隔离 agent、证据优先、fail-closed）是否可用。"""
    path = os.environ.get("GOAI_SUPER_REF",
                          os.path.expanduser("~/Code/super_ref"))
    available = os.path.exists(os.path.join(path, "scripts", "citationctl"))
    return _dumps({
        "available": available, "path": path,
        "usage": [
            f"mkdir -p {path}/workspaces/<name> 并写入 REFERENCES.json",
            f"python3 {path}/scripts/citationctl init workspaces/<name>",
            "依次 collect / packetize / run-agents / consensus / propose",
            "apply 需作者本人过目 CITATION_CORRECTIONS.json 后绑定提案 SHA-256 执行",
        ] if available else
        ["未检测到 super_ref；设置 GOAI_SUPER_REF 指向仓库路径，"
         "或 git clone github.com/asimfish/super_ref"],
        "when_to_use": "投稿前终审、或快速档出现 MISMATCH/UNVERIFIED 需要证据级裁决时",
    })


if __name__ == "__main__":
    mcp.run()
