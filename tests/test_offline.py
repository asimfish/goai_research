"""离线单测：核心确定性逻辑全覆盖，不打网络。"""
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from server.core import bibtex, figspec, render_drawio, render_svg, retro, sources, svg2drawio


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
        ["Vaswani, Ashish", "Shazeer, Noam", "Parmar, Niki"]
        and ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"], canonical)
    assert ok["ok"] and not ok["issues"]

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
                         venue="TestConf", doi="10.1/XYZ", arxiv_id="2401.00001")
    s = bibtex.record_to_bibtex(rec)
    e = bibtex.parse_bibtex(s)[0]
    assert e["entry_type"] == "inproceedings"
    assert e["fields"]["doi"] == "10.1/xyz"          # record() 归一化小写
    assert e["fields"]["booktitle"] == "TestConf"
    assert "One" in e["fields"]["author"]
    assert e["key"] == "one2024foo"


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


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
