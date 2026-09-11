"""goai-workflow：仪器目录 / 模板校验 / 导出 的离线测试。"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.core import workflow as wf  # noqa: E402

BIB = ROOT / "tests" / "fixtures" / "workflow_refs.bib"


@pytest.fixture(scope="module")
def bib(tmp_path_factory):
    p = tmp_path_factory.mktemp("bib") / "refs.bib"
    keys = ["szymanski2023alab", "szymanski2023arrows", "fei2024alabos", "bai2026safelab",
            "ababaikeri2024ba5y12zn", "wierzbickawieczorek2017high", "gulay2024navigation",
            "lin1999phase", "thieme2022solid", "kerstan2013bazn2si2o7"]
    p.write_text("\n".join(f"@article{{{k},\n  title = {{x}},\n  year = {{2024}}\n}}\n" for k in keys), encoding="utf-8")
    return p


@pytest.fixture(scope="module")
def registry():
    reg = wf.load_asset_registry()
    assert reg is not None, "configs/safelab_asset_registry.json missing"
    return reg


def test_catalog_consistency():
    cat = wf.load_catalog()
    for name, t in cat["task_types"].items():
        assert t["instrument"] in cat["instruments"], f"task type {name} points to unknown instrument"
    for name, inst in cat["instruments"].items():
        for p in inst["primitives"]:
            assert p in cat["primitives"], f"instrument {name} lists unknown primitive {p}"
    for name, p in cat["primitives"].items():
        for s in p.get("safety", []):
            assert s in cat["safety_defaults"], f"primitive {name} needs safety key {s} without default"
    assert "franka_fr3" in cat["embodiments"]


def test_catalog_assets_exist_in_registry(registry):
    cat = wf.load_catalog()
    keys = registry["assets"]
    for name, inst in cat["instruments"].items():
        assert inst["safelab_assets"], f"instrument {name} has no asset binding"
        missing = [a for a in inst["safelab_assets"] if a not in keys]
        assert not missing, f"instrument {name}: assets not in registry {missing}"


def test_generator_reproduces_committed_templates(tmp_path):
    subprocess.run([sys.executable, str(ROOT / "tools" / "gen_workflow_templates.py"), "--out", str(tmp_path)], check=True, capture_output=True)
    committed = ROOT / "configs" / "workflows"
    gen = sorted(p.name for p in tmp_path.glob("*.json"))
    assert gen == sorted(p.name for p in committed.glob("*.json"))
    for name in gen:
        assert json.loads((tmp_path / name).read_text()) == json.loads((committed / name).read_text()), f"{name} drifted from generator"


@pytest.mark.parametrize("tid", [t["id"] for t in wf.list_templates()])
def test_templates_validate_and_export(tid, registry, bib, tmp_path):
    spec = wf.load_template(tid)
    r = wf.validate_spec(spec, asset_registry=registry, bib_path=bib)
    assert r["ok"], r["errors"]
    assert r["warnings"] == [], r["warnings"]
    assert r["stats"]["n_evidence"] >= 2
    res = wf.export_all(spec, tmp_path, asset_registry=registry, bib_path=bib)
    assert res["ok"] and res["unresolved_assets"] == []
    out = Path(res["out_dir"])
    assert (out / "isaac_manifest.json").exists() and (out / "CODEX_BRIEF.md").exists()
    manifest = json.loads((out / "isaac_manifest.json").read_text())
    assert manifest["robot"]["type"] == "franka_fr3"
    assert all(p["usd"] for p in manifest["prims"] if p.get("asset_key"))
    yamls = list((out / "safelab_tasks").glob("*.yaml"))
    assert len(yamls) == sum(1 for t in spec["tasks"] if t.get("primitives"))
    text = yamls[0].read_text(encoding="utf-8")
    assert "safety_constraints:" in text and "goals:" in text


def test_five_workflows_cover_safelab_categories():
    cats = set()
    for t in wf.list_templates():
        spec = wf.load_template(t["id"])
        cats |= set(wf.validate_spec(spec)["stats"]["safelab_categories"])
    for c in ("pick-and-place", "pour liquid", "press switch", "open cabinet", "close cabinet", "grasp vessel"):
        assert c in cats, f"no workflow exercises SafeLab category {c}"


def _base():
    return wf.load_template("wf05_reagent_logistics_safety")


def test_validation_rejects_unknown_instrument_and_primitive():
    spec = _base()
    spec["stations"][0]["instrument"] = "teleporter"
    spec["tasks"][0]["primitives"].append({"op": "levitate", "object": "bottle_acid"})
    r = wf.validate_spec(spec)
    assert not r["ok"]
    assert any("unknown instrument" in e for e in r["errors"])
    assert any("unknown op" in e for e in r["errors"])


def test_validation_rejects_cycle_and_bad_reference():
    spec = _base()
    spec["tasks"][0]["depends_on"] = ["t_dispose"]  # t_dispose already depends (transitively) on t_get
    spec["tasks"][1]["primitives"][0]["to"] = "nowhere"
    r = wf.validate_spec(spec)
    assert not r["ok"]
    assert any("cycle" in e for e in r["errors"])
    assert any("not a declared object/station/sample" in e for e in r["errors"])


def test_validation_requires_safety_fields_and_tilt_limit():
    spec = _base()
    spec["safety_constraints"] = {}
    cat = copy.deepcopy(wf.load_catalog())
    cat["safety_defaults"] = {}
    r = wf.validate_spec(spec, catalog=cat)
    assert not r["ok"] and any("safety field" in e for e in r["errors"])
    spec2 = wf.load_template("wf03_wet_chemical_precursor")
    spec2["safety_constraints"]["tilt_limit_rad"] = 1.5
    r2 = wf.validate_spec(spec2)
    assert any("tilt_limit_rad" in e for e in r2["errors"])


def test_validation_zero_trust_citations(tmp_path):
    spec = _base()
    p = tmp_path / "refs.bib"
    p.write_text("@article{other2020,\n title={x}\n}\n", encoding="utf-8")
    r = wf.validate_spec(spec, bib_path=p)
    assert not r["ok"] and any("zero-trust" in e for e in r["errors"])


def test_asset_registry_enforced_when_present(registry):
    spec = _base()
    spec["stations"][0]["asset"] = "not_an_asset"
    r = wf.validate_spec(spec, asset_registry=registry)
    assert any("not in registry" in e for e in r["errors"])
    r2 = wf.validate_spec(spec, asset_registry=None)
    assert r2["ok"], r2["errors"]


def test_instantiate_template_overrides_params():
    spec = wf.instantiate_template("wf01_solid_state_calcination", {"id": "wf01_run7", "task_params": {"t_heat": {"heating_temperature": 950}}})
    assert spec["id"] == "wf01_run7" and spec["template"] == "wf01_solid_state_calcination"
    heat = next(t for t in spec["tasks"] if t["id"] == "t_heat")
    assert heat["params"]["heating_temperature"] == 950
    assert wf.validate_spec(spec)["ok"]


def test_yaml_roundtrip_scalars():
    text = wf.to_yaml({"a": "x: y", "b": [1, {"c": None, "d": True}], "e": "plain"})
    assert '"x: y"' in text and "null" in text and "true" in text and "- 1" in text


def test_server_tools_return_json():
    from server import workflow_server as ws
    d = json.loads(ws.list_instruments())
    assert len(d["instruments"]) >= 15
    t = json.loads(ws.list_workflow_templates())["templates"]
    assert len(t) == 5
    r = json.loads(ws.validate_workflow(json.dumps(wf.load_template(t[0]["id"]))))
    assert r["ok"] and r["asset_registry_loaded"] is True
    s = json.loads(ws.workflow_spec_schema())
    assert s["spec_version"] == wf.SPEC_VERSION and json.loads(ws.validate_workflow(json.dumps(s["example"])))["ok"]
