"""离线单测：核心确定性逻辑全覆盖，不打网络。"""
import json
import hashlib
import os
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from server.core import (
    bibtex,
    corpus_export,
    figspec,
    inorganic_retro,
    local_corpus,
    render_drawio,
    render_svg,
    retro,
    sources,
    svg2drawio,
)


# ---------- bibtex ----------

SAMPLE_BIB = r"""
@article{vaswani2017attention,
  title   = {Attention Is All You Need},
  author  = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki},
  year    = {2017},
  journal = {NeurIPS}
}
@inproceedings{he2016deep,
  title  = {Deep Residual Learning for Image Recognition},
  author = {He, Kaiming and Zhang, Xiangyu},
  year   = {2016},
  booktitle = {CVPR},
}
"""


def test_bibtex_parse_roundtrip():
    entries = bibtex.parse_bibtex(SAMPLE_BIB)
    assert len(entries) == 2
    e = entries[0]
    assert e["key"] == "vaswani2017attention"
    assert e["entry_type"] == "article"
    assert e["fields"]["year"] == "2017"
    out = bibtex.format_entry(e["key"], e["entry_type"], e["fields"])
    reparsed = bibtex.parse_bibtex(out)[0]
    assert reparsed["fields"]["title"] == e["fields"]["title"]


def test_split_authors_normalizes_last_first():
    names = bibtex.split_authors("Vaswani, Ashish and Shazeer, Noam")
    assert names == ["Ashish Vaswani", "Noam Shazeer"]


def test_author_compare_order_missing_extra():
    canonical = ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"]

    ok = bibtex.compare_authors(
        ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"], canonical)
    assert ok["ok"] and not ok["issues"]

    # 真实调用链：bib 字段先经 split_authors 归一化（"Last, First"→"First Last"）
    ok_lf = bibtex.compare_authors(
        bibtex.split_authors("Vaswani, Ashish and Shazeer, Noam and Parmar, Niki"),
        canonical)
    assert ok_lf["ok"], ok_lf["issues"]

    # 缩写等价：A. Vaswani == Ashish Vaswani
    abbrev = bibtex.compare_authors(
        ["A. Vaswani", "N. Shazeer", "N. Parmar"], canonical)
    assert abbrev["ok"], abbrev["issues"]

    # 顺序错
    swapped = bibtex.compare_authors(
        ["Ashish Vaswani", "Niki Parmar", "Noam Shazeer"], canonical)
    assert not swapped["ok"]
    assert any(i["type"] == "order" for i in swapped["issues"])

    # 遗漏 + 伪造
    bad = bibtex.compare_authors(["Ashish Vaswani", "Fake Person"], canonical)
    types = {i["type"] for i in bad["issues"]}
    assert "missing" in types and "extra" in types


def test_title_similarity():
    assert bibtex.title_similarity(
        "Attention is all you need", "Attention Is All You Need!") > 0.95
    assert bibtex.title_similarity(
        "Attention is all you need", "Deep Residual Learning") < 0.5


def test_record_to_bibtex():
    rec = sources.record("arxiv", id="arxiv:2401.00001", title="Foo Bar Baz",
                         authors=["Alice One", "Bob Two"], year=2024,
                         venue="TestConf", doi="10.1/XYZ", arxiv_id="2401.00001",
                         publication_type="conference")
    s = bibtex.record_to_bibtex(rec)
    e = bibtex.parse_bibtex(s)[0]
    assert e["entry_type"] == "inproceedings"
    assert e["fields"]["doi"] == "10.1/xyz"          # record() 归一化小写
    assert e["fields"]["booktitle"] == "TestConf"
    assert "One" in e["fields"]["author"]
    assert e["key"] == "one2024foo"


def test_record_to_bibtex_defaults_nonconference_venue_to_article():
    rec = sources.record(
        "crossref", title="A Journal Paper", authors=["Alice One"], year=2024,
        venue="ACS Applied Materials & Interfaces", doi="10.1/example",
        publication_type="journal-article",
    )
    entry = bibtex.parse_bibtex(bibtex.record_to_bibtex(rec))[0]
    assert entry["entry_type"] == "article"
    assert entry["fields"]["journal"] == r"ACS Applied Materials \& Interfaces"


# ---------- sources（离线部分） ----------

def test_dedup_merge_fills_fields_and_tracks_sources():
    a = sources.record("arxiv", id="arxiv:1", title="A Survey: of LLMs!",
                       year=2024, doi="10.1/a", arxiv_id="2401.1")
    b = sources.record("s2", id="s2:9", title="A survey of llms",
                       doi="10.1/a", abstract="rich abstract")
    merged = sources.dedup_merge([a, b])
    assert len(merged) == 1
    m = merged[0]
    assert m["abstract"] == "rich abstract"          # 后见记录补空字段
    assert m["year"] == 2024
    assert m["sources"] == ["arxiv", "s2"]

    c = sources.record("dblp", id="dblp:7", title="Totally Different Paper")
    assert len(sources.dedup_merge([a, c])) == 2


def test_norm_title_and_arxiv_id():
    assert sources.norm_title("  A Survey: of LLMs!  ") == sources.norm_title(
        "a survey of llms")
    assert sources.norm_arxiv_id("arXiv:2401.00001v2") == "2401.00001"


def test_crossref_parser_cleans_html_and_keeps_publication_type():
    record = sources._parse_crossref({
        "DOI": "10.1/example",
        "title": ["Li<sub>7</sub> LLZO"],
        "container-title": ["ACS Applied Materials &amp; Interfaces"],
        "author": [{"given": "Alice", "family": "One"}],
        "issued": {"date-parts": [[2024]]},
        "type": "journal-article",
    })
    assert record["title"] == "Li 7 LLZO"
    assert record["venue"] == "ACS Applied Materials & Interfaces"
    assert record["publication_type"] == "journal-article"


# ---------- figspec / 渲染 ----------

SPEC = {
    "title": "demo",
    "canvas": {"width": 400, "height": 300},
    "groups": [{"id": "g1", "label": "Stage", "x": 20, "y": 20, "w": 360, "h": 120}],
    "nodes": [
        {"id": "a", "label": "Input", "x": 40, "y": 60, "w": 100, "h": 40,
         "shape": "rounded", "group": "g1"},
        {"id": "b", "label": "Model", "x": 220, "y": 60, "w": 100, "h": 40,
         "shape": "rect", "group": "g1"},
        {"id": "c", "label": "Out", "x": 150, "y": 200, "w": 90, "h": 40,
         "shape": "ellipse"},
    ],
    "edges": [
        {"from": "a", "to": "b", "label": "tokens"},
        {"from": "b", "to": "c", "dashed": True},
    ],
    "texts": [{"text": "fig demo", "x": 30, "y": 290}],
}


def test_figspec_validate_ok():
    assert figspec.validate(SPEC) == []


def test_figspec_validate_catches_errors():
    bad = json.loads(json.dumps(SPEC))
    bad["edges"].append({"from": "a", "to": "zzz"})
    bad["nodes"][0]["shape"] = "star"
    bad["nodes"][1]["group"] = "nope"
    errs = figspec.validate(bad)
    assert any("zzz" in e for e in errs)
    assert any("star" in e for e in errs)
    assert any("nope" in e for e in errs)


def test_figspec_validate_catches_overlap():
    bad = json.loads(json.dumps(SPEC))
    bad["nodes"][1]["x"] = bad["nodes"][0]["x"] + 10
    bad["nodes"][1]["y"] = bad["nodes"][0]["y"]
    errs = figspec.validate(bad)
    assert any("重叠" in e for e in errs)


def test_figspec_validate_catches_parallel_edges():
    bad = json.loads(json.dumps(SPEC))
    # 同起终点 + 相同 label（都空）→ 同义平行线
    bad["edges"].append({"from": "b", "to": "c", "dashed": False})
    errs = figspec.validate(bad)
    assert any("平行线" in e for e in errs)
    # 各自携带不同的量 → 合法
    ok = json.loads(json.dumps(SPEC))
    ok["edges"].append({"from": "a", "to": "b", "label": "gradients"})
    assert figspec.validate(ok) == []


def test_figspec_lint_font_floor():
    # 1500px 画布上 10px ≈ 3.1pt 印刷 → error;15.5px ≈ 4.8pt → 通过
    spec = {"canvas": {"width": 1500, "height": 400},
            "nodes": [{"id": "a", "label": "Small text", "x": 10, "y": 10,
                       "w": 200, "h": 60, "font_size": 10}]}
    r = figspec.lint(spec)
    assert any("印刷不可读" in e for e in r["errors"])
    spec["nodes"][0]["font_size"] = 15.5
    assert figspec.lint(spec)["errors"] == []


def test_figspec_lint_text_overflow():
    # 六边形有效文本区小,长文本 + 大字号 → 溢出 error
    spec = {"canvas": {"width": 800, "height": 400},
            "nodes": [{"id": "g", "shape": "hexagon", "font_size": 16,
                       "label": "a very long decision question that cannot fit",
                       "x": 10, "y": 10, "w": 150, "h": 50}]}
    r = figspec.lint(spec)
    assert any("溢出" in e for e in r["errors"])
    # 纯装饰节点(无文字)不检查
    deco = {"canvas": {"width": 800, "height": 400},
            "nodes": [{"id": "d", "label": "", "x": 0, "y": 0, "w": 4, "h": 8}]}
    assert figspec.lint(deco)["errors"] == []


def test_figspec_lint_group_label_occlusion():
    spec = {"canvas": {"width": 800, "height": 400},
            "groups": [{"id": "g1", "label": "Lane C - pre-registered gates",
                        "x": 0, "y": 0, "w": 700, "h": 200, "font_size": 15}],
            "nodes": [{"id": "n1", "label": "Node", "group": "g1",
                       "x": 20, "y": 8, "w": 150, "h": 50, "font_size": 15}]}
    r = figspec.lint(spec)
    assert any("遮挡" in e for e in r["errors"])
    spec["nodes"][0]["y"] = 40  # 移出标签带
    assert figspec.lint(spec)["errors"] == []


def test_figspec_lint_group_label_hierarchy():
    spec = {"canvas": {"width": 800, "height": 400},
            "groups": [{"id": "g1", "label": "Lane",
                        "x": 0, "y": 0, "w": 700, "h": 300, "font_size": 14}],
            "nodes": [{"id": "n1", "label": "Node", "group": "g1",
                       "x": 20, "y": 60, "w": 150, "h": 50, "font_size": 18}]}
    r = figspec.lint(spec)
    assert any("小于组内节点主标" in w for w in r["warnings"])
    spec["groups"][0]["font_size"] = 19  # 组标签 ≥ 主标 → 不再告警
    r2 = figspec.lint(spec)
    assert not any("小于组内节点主标" in w for w in r2["warnings"])


def test_render_svg_node_label_bold_default():
    spec = {"canvas": {"width": 800, "height": 300},
            "nodes": [{"id": "a", "label": "Bold by default",
                       "x": 40, "y": 60, "w": 220, "h": 60, "font_size": 18},
                      {"id": "b", "label": "Opt out",
                       "x": 320, "y": 60, "w": 180, "h": 60, "font_size": 18,
                       "label_bold": False}],
            "edges": []}
    svg = render_svg.render(spec)
    assert svg.count('font-weight="bold"') == 1


def test_render_svg_contains_elements():
    svg = render_svg.render(SPEC)
    for frag in ("Input", "Model", "tokens", "marker"):
        assert frag in svg
    ET.fromstring(svg)  # 必须是合法 XML


def test_render_drawio_valid_mxgraph():
    xml = render_drawio.render(SPEC)
    root = ET.fromstring(xml)
    assert root.tag == "mxfile"
    cells = root.findall(".//mxCell")
    ids = {c.get("id") for c in cells}
    assert {"a", "b", "c", "g1"} <= ids
    edges = [c for c in cells if c.get("edge") == "1"]
    assert len(edges) == 2
    # 可编辑性验收点：连线必须绑定 source/target，拖动节点线要跟随
    assert all(c.get("source") and c.get("target") for c in edges)
    # 分组成员 parent 指向组容器
    node_a = next(c for c in cells if c.get("id") == "a")
    assert node_a.get("parent") == "g1"


def test_render_label_style_and_edge_defaults():
    spec = json.loads(json.dumps(SPEC))
    # 深头带白字 + title_style + defaults.edge_color 键名（实测回归：三项此前均不生效）
    spec["title"] = "Styled Title"
    spec["title_style"] = {"font_size": 20, "y": 30, "bold": True}
    spec["nodes"][0].update(
        {"fill": "#1F5F5B", "label_color": "#FFFFFF", "label_bold": True})
    spec["defaults"] = {"edge_color": "#AA6600", "edge_width": 3}
    svg = render_svg.render(spec)
    assert 'fill="#FFFFFF" font-weight="bold">Input</text>' in svg
    assert 'font-size="20"' in svg
    assert 'stroke="#AA6600"' in svg and 'stroke-width="3"' in svg
    xml = render_drawio.render(spec)
    root = ET.fromstring(xml)
    node_a = next(c for c in root.findall(".//mxCell") if c.get("id") == "a")
    assert "fontColor=#FFFFFF" in node_a.get("style")
    assert "fontStyle=1" in node_a.get("style")
    edge = next(c for c in root.findall(".//mxCell") if c.get("edge") == "1")
    assert "strokeColor=#AA6600" in edge.get("style")
    title = next(c for c in root.findall(".//mxCell")
                 if c.get("id") == "goai-title")
    assert "fontSize=20" in title.get("style")


def test_render_publication_style_fields():
    spec = json.loads(json.dumps(SPEC))
    # 出版级样式字段：shadow / arc / stroke_width / texts.align 双渲染器生效
    spec["nodes"][0].update({"shadow": True, "arc": 12, "stroke_width": 2.5})
    spec["groups"][0].update({"shadow": True, "stroke_width": 1.8})
    spec["texts"] = [{"id": "t1", "text": "note", "x": 40, "y": 300,
                      "align": "left", "font_size": 12}]
    svg = render_svg.render(spec)
    assert "goai-shadow" in svg and 'filter="url(#goai-shadow)"' in svg
    assert 'rx="12"' in svg
    assert 'stroke-width="2.5"' in svg
    assert 'text-anchor="start"' in svg
    xml = render_drawio.render(spec)
    root = ET.fromstring(xml)
    node_a = next(c for c in root.findall(".//mxCell") if c.get("id") == "a")
    assert "shadow=1" in node_a.get("style")
    assert "arcSize=12" in node_a.get("style")
    assert "strokeWidth=2.5" in node_a.get("style")
    t1 = next(c for c in root.findall(".//mxCell") if c.get("id") == "t1")
    assert "align=left" in t1.get("style")


def test_svg_roundtrip_to_figspec():
    svg = render_svg.render(SPEC)
    rec = svg2drawio.svg_to_figspec(svg)
    assert figspec.validate(rec) == []
    assert len(rec["nodes"]) == 3
    labels = {n["label"] for n in rec["nodes"]}
    assert {"Input", "Model", "Out"} <= labels
    # 分组底板恢复为 group（而非与成员重叠的假节点）
    assert len(rec["groups"]) == 1
    assert "Stage" in rec["groups"][0]["label"]
    in_group = [n for n in rec["nodes"] if n.get("group") == rec["groups"][0]["id"]]
    assert {n["label"] for n in in_group} == {"Input", "Model"}
    assert len(rec["edges"]) >= 1  # 边靠启发式恢复，至少主边在
    # 边 label 恢复到边上（而非变成假节点或吞进 group label）
    assert any(e.get("label") == "tokens" for e in rec["edges"])
    # 逆向结果可再渲染为 drawio（编辑链路闭环）
    ET.fromstring(render_drawio.render(rec))


# ---------- retro stub ----------

def test_retro_stub_and_plan(monkeypatch):
    monkeypatch.delenv("GOAI_RETRO_PROVIDER", raising=False)
    route = retro.predict("CC(=O)Oc1ccccc1C(=O)O", max_depth=2)
    assert route["provider"] == "stub"
    assert route["verified"] is False and route["warning"]
    assert len(route["steps"]) == 2

    plan = retro.experiment_plan_skeleton(route, objective="demo synth")
    assert plan["objective"] == "demo synth"
    assert plan["provider_verified"] is False
    assert len(plan["steps"]) == len(route["steps"])
    assert all(s["safety"] for s in plan["steps"])
    assert plan["review_gates"]


def test_retro_http_requires_url(monkeypatch):
    monkeypatch.setenv("GOAI_RETRO_PROVIDER", "http")
    monkeypatch.delenv("GOAI_RETRO_API_URL", raising=False)
    r = retro.predict("CCO")
    assert r["ok"] is False and "GOAI_RETRO_API_URL" in r["error"]


def test_inorganic_route_maps_to_nonempty_plan_skeleton():
    route = {
        "provider": "local_two_stage_inorganic",
        "model_output_verified": True,
        "chemical_route_verified": False,
        "route_id": "two-stage-example",
        "target_formula": "Li7La3Zr2O12",
        "precursors": [
            {"formula": "ZrO2"}, {"formula": "La2O3"}, {"formula": "Li2CO3"},
        ],
    }
    plan = retro.experiment_plan_skeleton(route, "LLZO diagnostic")
    assert plan["provider"] == "local_two_stage_inorganic"
    assert plan["provider_verified"] is True
    assert plan["chemical_route_verified"] is False
    assert plan["steps"][0]["inputs"] == ["ZrO2", "La2O3", "Li2CO3"]
    assert "not predicted" in plan["steps"][0]["reaction"]


# ---------- local corpus / inorganic retro assets ----------

def test_local_corpus_search_read_and_audit(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    paper = corpus / "llzo-paper.md"
    paper.write_text(
        "# Example\nBefore context.\nLi7La3Zr2O12 was densified.\nAfter context.\n",
        encoding="utf-8",
    )
    workspace = tmp_path / "workspace"
    monkeypatch.setenv("GOAI_LOCAL_CORPUS_ROOTS", str(corpus))
    monkeypatch.setenv("GOAI_WORKSPACE", str(workspace))

    result = local_corpus.search_local_corpus(
        "Li7La3Zr2O12", max_results=2, context_lines=1, timeout_seconds=5
    )
    assert result["ok"] is True, result
    assert result["total_returned"] == 1
    assert result["matches"][0]["line"] == 3
    assert [row["line"] for row in result["matches"][0]["context"]] == [2, 3, 4]

    excerpt = local_corpus.read_local_document(str(paper), start_line=2, end_line=3)
    assert excerpt["ok"] is True
    assert excerpt["lines"][-1]["text"].startswith("Li7La3Zr2O12")
    outside = local_corpus.read_local_document(str(tmp_path / "outside.md"))
    assert outside["ok"] is False and "outside" in outside["error"]

    audit_path = workspace / "state" / "tool_calls.jsonl"
    events = [json.loads(line) for line in audit_path.read_text().splitlines()]
    assert [event["tool"] for event in events] == [
        "grep_local_corpus", "read_local_document", "read_local_document"
    ]


def test_local_corpus_search_clips_very_long_lines(tmp_path, monkeypatch):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    paper = corpus / "long.md"
    paper.write_text("LLZO " + "x" * 5000 + "\n", encoding="utf-8")
    monkeypatch.setenv("GOAI_LOCAL_CORPUS_ROOTS", str(corpus))
    monkeypatch.setenv("GOAI_WORKSPACE", str(tmp_path / "workspace"))
    monkeypatch.setenv("GOAI_LOCAL_MATCH_TEXT_CHARS", "300")

    result = local_corpus.search_local_corpus(
        "LLZO", max_results=1, context_lines=0, timeout_seconds=5
    )
    match = result["matches"][0]
    assert match["text_truncated"] is True
    assert len(match["text"]) < 330
    assert match["context"][0]["text_truncated"] is True


def test_parquet_corpus_search_read_and_doi_lookup(tmp_path, monkeypatch):
    duckdb = pytest.importorskip("duckdb")
    corpus = tmp_path / "parquet-corpus"
    corpus.mkdir()
    parquet = corpus / "part-00000.parquet"
    uuid = hashlib.md5(b"10.0000/byzso-test").hexdigest()
    connection = duckdb.connect(database=":memory:")
    connection.execute(
        "CREATE TABLE papers(uuid VARCHAR, doi_normalized VARCHAR, title VARCHAR, "
        "publisher_group VARCHAR, markdown VARCHAR)"
    )
    connection.execute(
        "INSERT INTO papers VALUES (?, ?, ?, ?, ?)",
        [uuid, "10.0000/byzso-test", "BYZSO analogue", "test-publisher",
         "# Example\nBefore.\nBa5Y12ZnSi8O40 candidate.\nAfter."],
    )
    connection.execute("COPY papers TO ? (FORMAT PARQUET)", [str(parquet)])
    connection.close()

    workspace = tmp_path / "workspace"
    monkeypatch.setenv("GOAI_LOCAL_CORPUS_ROOTS", str(corpus))
    monkeypatch.setenv("GOAI_WORKSPACE", str(workspace))
    result = local_corpus.search_local_corpus(
        "Ba5Y12ZnSi8O40", max_results=2, context_lines=1, timeout_seconds=5
    )
    assert result["ok"] is True, result
    assert result["engine"] == "duckdb-parquet"
    assert result["matches"][0]["doi"] == "10.0000/byzso-test"
    reference = result["matches"][0]["path"]
    excerpt = local_corpus.read_local_document(reference, start_line=2, end_line=4)
    assert excerpt["ok"] is True
    assert excerpt["lines"][1]["text"].startswith("Ba5Y12Zn")

    index = tmp_path / "expected.sqlite"
    sql = sqlite3.connect(index)
    sql.execute("CREATE TABLE expected_members(uuid TEXT PRIMARY KEY, archive_name TEXT NOT NULL)")
    sql.execute("INSERT INTO expected_members VALUES (?, ?)", (uuid, "archive-0001.7z"))
    sql.commit()
    sql.close()
    shards = tmp_path / "shards"
    shards.mkdir()
    parquet.rename(shards / "archive-0001.7z.parquet")
    monkeypatch.setenv("GOAI_LOCAL_CORPUS_EXPECTED_INDEX", str(index))
    monkeypatch.setenv("GOAI_LOCAL_CORPUS_SHARD_ROOT", str(shards))
    lookup = local_corpus.lookup_local_doi("https://doi.org/10.0000/BYZSO-TEST")
    assert lookup["found"] is True
    assert lookup["document_id"] == uuid


def test_repo_synthetic_compact_corpus_is_self_contained(tmp_path, monkeypatch):
    corpus = os.path.join(ROOT, "examples", "demo_corpus")
    monkeypatch.setenv("GOAI_LOCAL_CORPUS_ROOTS", corpus)
    monkeypatch.setenv("GOAI_WORKSPACE", str(tmp_path / "workspace"))
    monkeypatch.delenv("GOAI_LOCAL_CORPUS_EXPECTED_INDEX", raising=False)
    monkeypatch.delenv("GOAI_LOCAL_CORPUS_SHARD_ROOT", raising=False)

    status = local_corpus.corpus_status()
    assert status["ok"] is True, status
    assert status["mode"] == "synthetic-demo-parquet"
    assert status["package"]["citable"] is False
    assert status["schema"]["missing_columns"] == []

    result = local_corpus.search_local_corpus("Ba5Y12Zn[O(SiO4)]8")
    assert result["ok"] is True and result["total_returned"] == 1, result
    assert result["matches"][0]["synthetic"] is True
    assert result["matches"][0]["citable"] is False
    reference = result["matches"][0]["path"]
    excerpt = local_corpus.read_local_document(reference, start_line=1, end_line=4)
    assert excerpt["ok"] is True
    assert excerpt["synthetic"] is True and excerpt["citable"] is False
    assert any("fully synthetic" in row["text"] for row in excerpt["lines"])

    lookup = local_corpus.lookup_local_doi("10.0000/GOAI.DEMO.BYZSO")
    assert lookup["ok"] is True and lookup["found"] is True, lookup
    assert lookup["lookup_engine"] == "compact-parquet"
    assert lookup["synthetic"] is True and lookup["citable"] is False
    assert lookup["title"] == "Synthetic barium yttrium zinc silicate note"


def test_public_subset_export_is_allow_listed(tmp_path, monkeypatch):
    corpus = tmp_path / "private-corpus"
    corpus.mkdir()
    allowed = corpus / "used-paper.md"
    metadata_only = corpus / "copyrighted-paper.pdf"
    allowed.write_text("LLZO evidence", encoding="utf-8")
    metadata_only.write_bytes(b"not copied")
    manifest = tmp_path / "selection.json"
    manifest.write_text(json.dumps({"documents": [
        {
            "source_path": str(allowed),
            "document_id": "llzo-evidence",
            "doi": "10.0000/example",
            "license": "CC-BY-4.0",
            "redistributable": True,
        },
        {
            "source_path": str(metadata_only),
            "doi": "10.0000/copyrighted",
            "url": "https://doi.org/10.0000/copyrighted",
            "redistributable": False,
        },
    ]}), encoding="utf-8")

    result = corpus_export.export_public_subset(
        manifest, tmp_path / "public", roots=[corpus]
    )
    assert result["exported_count"] == 1
    assert result["metadata_only_count"] == 1
    copied = tmp_path / "public" / result["documents"][0]["path"]
    assert copied.read_text(encoding="utf-8") == "LLZO evidence"
    public_text = (tmp_path / "public" / "MANIFEST.json").read_text(encoding="utf-8")
    assert str(corpus) not in public_text
    assert metadata_only.name not in {path.name for path in (tmp_path / "public" / "documents").iterdir()}
    with pytest.raises(FileExistsError):
        corpus_export.export_public_subset(manifest, tmp_path / "public", roots=[corpus])

    compact_dir = tmp_path / "public-parquet"
    compact = corpus_export.export_public_subset(
        manifest,
        compact_dir,
        roots=[corpus],
        output_format="compact-parquet",
    )
    assert compact["corpus_format"] == "goai-compact-parquet-v1"
    assert compact["document_count"] == 1
    assert (compact_dir / "corpus.parquet").is_file()
    compact_text = (compact_dir / "corpus_manifest.json").read_text(encoding="utf-8")
    assert str(corpus) not in compact_text

    monkeypatch.delenv("GOAI_LOCAL_CORPUS_EXPECTED_INDEX", raising=False)
    monkeypatch.delenv("GOAI_LOCAL_CORPUS_SHARD_ROOT", raising=False)
    compact_status = local_corpus.corpus_status(roots=[compact_dir])
    assert compact_status["ok"] is True
    assert compact_status["mode"] == "public-compact-parquet"
    assert compact_status["package"]["citable"] is True
    hit = local_corpus.search_local_corpus("LLZO evidence", roots=[compact_dir])
    assert hit["total_returned"] == 1
    doi_hit = local_corpus.lookup_local_doi("10.0000/example", roots=[compact_dir])
    assert doi_hit["found"] is True
    assert doi_hit["lookup_engine"] == "compact-parquet"


def test_inorganic_retro_assets_and_checkpoint_hashes():
    result = inorganic_retro.status()
    assert all(result["assets"].values()), result
    assert all(result["checkpoint_hash_ok"].values()), result
    assert result["protocol"]["default_routes"] == 5


# ---------- loopctl 账本 ----------

def run_loopctl(tmpdir, *args):
    env = dict(os.environ, GOAI_WORKSPACE=str(tmpdir))
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "loopctl.py"), *args],
        capture_output=True, text=True, env=env)


def test_loopctl_full_cycle(tmp_path):
    r = run_loopctl(tmp_path, "init", "--topic", "test topic", "--max-rounds", "2")
    assert r.returncode == 0, r.stderr
    assert run_loopctl(tmp_path, "advance", "--to", "lit_search").returncode == 0
    assert run_loopctl(tmp_path, "advance", "--to", "bogus").returncode != 0
    assert run_loopctl(
        tmp_path, "gate", "--name", "lit_coverage", "--status", "PASS",
        "--detail", "48 papers").returncode == 0

    r = run_loopctl(tmp_path, "issue", "add", "--from-agent", "goai-reviewer",
                    "--target", "writing", "--severity", "major",
                    "--text", "S4 无证据断言")
    assert r.returncode == 0 and "I1" in r.stdout

    assert run_loopctl(tmp_path, "check-done").returncode != 0  # open issue → 未完成
    assert run_loopctl(tmp_path, "issue", "close", "--id", "I1",
                       "--note", "fixed").returncode == 0
    assert run_loopctl(tmp_path, "check-done").returncode == 0  # 全 PASS 无 open

    ledger = json.loads((tmp_path / "state" / "ledger.json").read_text())
    assert ledger["topic"] == "test topic"
    assert ledger["gates"]["lit_coverage"]["status"] == "PASS"
    assert ledger["issues"][0]["status"] == "closed"

    out = run_loopctl(tmp_path, "status").stdout
    assert "lit_search" in out

    # 回合上限强制收敛
    assert run_loopctl(tmp_path, "next-round").returncode == 0
    assert run_loopctl(tmp_path, "next-round").returncode != 0  # 达 max_rounds=2


def test_loopctl_check_done_semantics(tmp_path):
    run_loopctl(tmp_path, "init", "--topic", "t")
    run_loopctl(tmp_path, "gate", "--name", "lit_coverage", "--status", "PASS")
    # WARN = 合规跳过，不阻塞
    run_loopctl(tmp_path, "gate", "--name", "ideas_reviewed",
                "--status", "WARN", "--detail", "skipped")
    assert run_loopctl(tmp_path, "check-done").returncode == 0
    # PENDING 阻塞
    run_loopctl(tmp_path, "gate", "--name", "review_pass", "--status", "PENDING")
    assert run_loopctl(tmp_path, "check-done").returncode != 0
    run_loopctl(tmp_path, "gate", "--name", "review_pass", "--status", "PASS")
    # open minor 不阻塞（移交 final 清理），blocker/major 阻塞
    run_loopctl(tmp_path, "issue", "add", "--severity", "minor", "--text", "typo")
    r = run_loopctl(tmp_path, "check-done")
    assert r.returncode == 0 and "minor" in r.stdout
    run_loopctl(tmp_path, "issue", "add", "--severity", "major", "--text", "gap")
    assert run_loopctl(tmp_path, "check-done").returncode != 0


def test_loopctl_stale_inputs_reset_gate(tmp_path):
    artifact = tmp_path / "refs.bib"
    artifact.write_text("v1")
    run_loopctl(tmp_path, "init", "--topic", "t")
    run_loopctl(tmp_path, "gate", "--name", "ref_integrity", "--status", "PASS",
                "--inputs", str(artifact))
    assert run_loopctl(tmp_path, "check-done").returncode == 0
    artifact.write_text("v2 upstream changed")   # 上游产物变更
    r = run_loopctl(tmp_path, "check-done")
    assert r.returncode != 0 and "stale" in r.stdout
    ledger = json.loads((tmp_path / "state" / "ledger.json").read_text())
    assert ledger["gates"]["ref_integrity"]["status"] == "PENDING"


def test_loopctl_gate_receipt_recorded(tmp_path):
    run_loopctl(tmp_path, "init", "--topic", "t")
    run_loopctl(tmp_path, "gate", "--name", "review_pass", "--status", "PASS",
                "--receipt", "model=x;trace=state/review_traces/r1.md")
    ledger = json.loads((tmp_path / "state" / "ledger.json").read_text())
    assert "trace" in ledger["gates"]["review_pass"]["receipt"]


def test_loopctl_concurrent_writes_no_loss(tmp_path):
    run_loopctl(tmp_path, "init", "--topic", "t")
    env = dict(os.environ, GOAI_WORKSPACE=str(tmp_path))
    procs = [subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "tools", "loopctl.py"),
         "log", "--stage", "writing", "--agent", f"w{i}", "--event", "done"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for i in range(12)]
    assert all(p.wait() == 0 for p in procs)
    ledger = json.loads((tmp_path / "state" / "ledger.json").read_text())
    done_events = [e for e in ledger["log"] if e.get("event") == "done"]
    assert len(done_events) == 12   # 文件锁保证读-改-写互斥，不丢更新


# ---------- bib_guard ----------

def run_bib_guard(drafts, bib):
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "bib_guard.py"),
         str(drafts), str(bib)],
        capture_output=True, text=True)


def test_bib_guard(tmp_path):
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "s1.tex").write_text(
        r"Transformers \cite{vaswani2017attention} work. Bad \cite{ghost2020}.")
    bib = tmp_path / "refs.bib"
    bib.write_text(SAMPLE_BIB)

    r = run_bib_guard(drafts, bib)
    assert r.returncode != 0            # ghost2020 未定义 → 阻塞
    assert "ghost2020" in r.stdout
    assert "he2016deep" in r.stdout     # 孤儿条目 → 警告

    (drafts / "s1.tex").write_text(
        r"Transformers \cite{vaswani2017attention} and \cite{he2016deep}.")
    r2 = run_bib_guard(drafts, bib)
    assert r2.returncode == 0, r2.stdout


def test_bib_guard_integration_rate_blocks(tmp_path):
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    # 只引用 2 条中的 1 条 → 整合率 50% < 默认 90% → 阻塞
    (drafts / "s1.tex").write_text(r"Only \cite{vaswani2017attention} here.")
    bib = tmp_path / "refs.bib"
    bib.write_text(SAMPLE_BIB)
    r = run_bib_guard(drafts, bib)
    assert r.returncode != 0
    assert "整合率" in r.stdout


def test_bib_guard_bib_hygiene_warns(tmp_path):
    drafts = tmp_path / "drafts"
    drafts.mkdir()
    (drafts / "s1.tex").write_text(
        r"A \cite{chem2024tio} and B \cite{plain2020ok}.")
    bib = tmp_path / "refs.bib"
    bib.write_text("""
@article{chem2024tio,
  title  = {Growth of BaZn2Si2O7 single crystals},
  author = {Ann One},
  year   = {2024},
  doi    = {10.1000/x},
  url    = {https://example.org/x},
  journal = {J}
}
@article{plain2020ok,
  title  = {A survey of {LLZO} interfaces},
  author = {Bob Two},
  year   = {2020},
  doi    = {10.1000/y},
  journal = {J}
}
""")
    r = run_bib_guard(drafts, bib)
    assert r.returncode == 0, r.stdout        # 卫生问题只告警不阻塞
    assert "doi 与 url 同存" in r.stdout      # chem2024tio 冗余 url
    assert "BaZn2Si2O7" in r.stdout           # 未保护化学式
    hygiene = r.stdout.split("bib 字段卫生")[1]
    assert "plain2020ok" not in hygiene       # 已保护 + 无冗余 → 不告警


# ---------- tex_guard ----------

def run_tex_guard(target):
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "tex_guard.py"), str(target)],
        capture_output=True, text=True)


def test_tex_guard_blocks_and_passes(tmp_path):
    d = tmp_path / "drafts"
    (d / "sections").mkdir(parents=True)
    (d / "figures").mkdir()
    (d / "main.tex").write_text("\n".join([
        r"\title{TODO: Survey Title}",                 # 占位残留
        r"\begin{document}",
        r"\input{sections/01_intro}",                  # 存在
        r"\input{sections/99_missing}",                # 缺失
        r"\includegraphics{figures/ghost}",            # 缺失
        r"See \ref{sec:nowhere}.",                     # 悬空 ref
        r"\begin{itemize}",                            # 不闭合
        r"\end{document}",
    ]))
    (d / "sections" / "01_intro.tex").write_text(
        "\\section{Intro}\\label{sec:intro}\nOK \\ref{sec:intro}.")
    r = run_tex_guard(d)
    assert r.returncode != 0
    for frag in ("占位残留", "99_missing", "ghost", "sec:nowhere", "未闭合"):
        assert frag in r.stdout, f"missing {frag}\n{r.stdout}"

    good = tmp_path / "good"
    (good / "sections").mkdir(parents=True)
    (good / "main.tex").write_text("\n".join([
        r"\title{Real Title}",
        r"\begin{document}",
        r"\input{sections/01_intro}",
        r"\end{document}",
    ]))
    (good / "sections" / "01_intro.tex").write_text(
        "\\section{Intro}\\label{sec:intro}\nSee \\ref{sec:intro}.")
    r2 = run_tex_guard(good)
    assert r2.returncode == 0, r2.stdout


def test_tex_guard_bibkey_leak_blocks(tmp_path):
    d = tmp_path / "drafts"
    d.mkdir()
    # 裸 key 出现在正文（含 \texttt 包裹）→ 阻塞；跨行 \cite 参数不误伤
    (d / "main.tex").write_text("\n".join([
        r"\begin{document}",
        r"来源见 \texttt{lin1999phase} 的实验部分。",
        r"合法引用 \cite{vaswani2017attention,",
        r"  he2016deep} 不应误报。",
        r"中文紧贴无空格：据zou2021crystal报道。",     # CJK 邻接，\b 抓不到
        r"题首词数字开头：见 zhang20202d 的结果。",     # 年份后接数字
        r"\end{document}",
    ]))
    r = run_tex_guard(d)
    assert r.returncode != 0
    for leaked in ("lin1999phase", "zou2021crystal", "zhang20202d"):
        assert leaked in r.stdout, f"missed {leaked}\n{r.stdout}"
    assert "he2016deep" not in r.stdout      # 跨行 cite 参数不是泄漏

    # 全部 cite/ref 变体都是合法载体；行尾豁免标记生效
    (d / "main.tex").write_text("\n".join([
        r"\begin{document}",
        r"合法引用 \cite{lin1999phase} 与 \citep{zou2021crystal}，",
        r"\citealp{ab2020cd} \citet*{ef2021gh} \nocite{ij2022kl} \textcite{mn2023op}",
        r"\pageref{sec:qr2024st} \hyperref[fig:uv2025wx]{图} \label{tab:yz2026ab}",
        r"同形词豁免 model2020x 见注释。  % tex-guard: allow-key",
        r"\end{document}",
    ]))
    r2 = run_tex_guard(d)
    assert r2.returncode == 0, r2.stdout


def test_tex_guard_texttt_density_warns(tmp_path):
    d = tmp_path / "drafts"
    d.mkdir()
    body = " ".join(r"\texttt{NA}" for _ in range(12))
    (d / "main.tex").write_text(
        "\\begin{document}\n" + body + "\n\\end{document}\n")
    r = run_tex_guard(d)
    assert r.returncode == 0, r.stdout       # 密度问题只告警不阻塞
    assert "texttt" in r.stdout


def test_tex_guard_cjk_english_template_warns(tmp_path):
    d = tmp_path / "drafts"
    d.mkdir()
    zh_body = "本综述覆盖高温溶液法与固相路线的全部公开条件记录。" * 3
    (d / "main.tex").write_text("\n".join([
        r"\documentclass[11pt]{article}",
        r"\begin{document}", zh_body, r"\end{document}",
    ]))
    r = run_tex_guard(d)
    assert r.returncode == 0, r.stdout       # 告警不阻塞
    assert "survey_main_zh" in r.stdout      # 建议改用中文模板

    (d / "main.tex").write_text("\n".join([
        r"\documentclass[11pt,fontset=fandol]{ctexart}",
        r"\begin{document}", zh_body, r"\end{document}",
    ]))
    r2 = run_tex_guard(d)
    assert "survey_main_zh" not in r2.stdout

    # article + \usepackage{ctex} 同样是合法中文支持，不告警
    (d / "main.tex").write_text("\n".join([
        r"\documentclass[11pt]{article}",
        r"\usepackage[fontset=fandol]{ctex}",
        r"\begin{document}", zh_body, r"\end{document}",
    ]))
    r3 = run_tex_guard(d)
    assert "survey_main_zh" not in r3.stdout


# ---------- templates ----------

def test_survey_templates_contract():
    """两份主模板的排版契约：语言分工、健壮性、可被 tex_guard 拦住未替换占位。"""
    en = open(os.path.join(ROOT, "templates", "survey_main.tex"), encoding="utf-8").read()
    zh = open(os.path.join(ROOT, "templates", "survey_main_zh.tex"), encoding="utf-8").read()
    # 语言分工：英文 article，中文 ctexart（标签本地化）
    assert r"\documentclass[11pt]{article}" in en
    assert "{ctexart}" in zh and "fontset=fandol" in zh
    for tpl in (en, zh):
        # svg 包只在存在时加载——缺包/缺 inkscape 不得拖垮编译
        assert r"\IfFileExists{svg.sty}{\usepackage{svg}}{}" in tpl
        assert r"\usepackage{svg}" + "\n" not in tpl.replace(
            r"\IfFileExists{svg.sty}{\usepackage{svg}}{}", "")
        # 共同排版契约：学术蓝引用、P 列型、Times 字体链、参考文献前 clearpage
        assert "citecolor=blue" in tpl
        assert r"\newcolumntype{P}" in tpl
        assert r"\usepackage{newtxtext}" in tpl and r"\usepackage{newtxmath}" in tpl
        assert r"\usepackage{amssymb}" not in tpl
        assert r"\clearpage" in tpl
        # 占位符必须在（writer 替换）且能被 tex_guard 拦住
        assert "TODO" in tpl
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "tex_guard.py"),
         os.path.join(ROOT, "templates", "survey_main_zh.tex")],
        capture_output=True, text=True)
    assert r.returncode != 0 and "占位残留" in r.stdout


# ---------- bank_check ----------

RECENT_BIB = SAMPLE_BIB + r"""
@article{fresh2025loop,
  title  = {Loop Agents Survey},
  author = {Carol Three},
  year   = {2025},
  journal = {TestJournal}
}
@article{fresh2026gate,
  title  = {Gated Pipelines},
  author = {Dan Four},
  year   = {2026},
  journal = {TestJournal}
}
"""


def run_bank_check(bank, bib, *extra):
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, "tools", "bank_check.py"),
         str(bank), str(bib), *extra],
        capture_output=True, text=True)


def test_bank_check_passes_and_blocks(tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text(RECENT_BIB)

    good = tmp_path / "bank.md"
    good.write_text("\n".join([
        "# Section 1",
        "- [fresh2025loop] 回环式 agent 是近年综述的主流组织方式 (strong)",
        "- [fresh2026gate] 闸门机制能显著降低幻觉引用率 (strong)",
        "- [vaswani2017attention] 自注意力是这些系统的共同底座 (weak)",
    ]))
    r = run_bank_check(good, bib)
    assert r.returncode == 0, r.stdout

    bad = tmp_path / "bad.md"
    bad.write_text("\n".join([
        "- [ghost2030] 不存在的 key (strong)",       # 库外 key
        "- [fresh2025loop] 缺强度标注的行",           # 缺 (strong|weak)
        "- [he2016deep] 旧文献 (weak)",              # 拉低近三年占比
        "- [vaswani2017attention] 旧文献 (weak)",
    ]))
    r2 = run_bank_check(bad, bib)
    assert r2.returncode != 0
    for frag in ("ghost2030", "强度", "近三年"):
        assert frag in r2.stdout, f"missing {frag}\n{r2.stdout}"

    # 候选量闸门：3 条 < 目标 10 × 1.5
    r3 = run_bank_check(good, bib, "--target-cites", "10")
    assert r3.returncode != 0 and "候选量" in r3.stdout


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
