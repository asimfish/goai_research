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
