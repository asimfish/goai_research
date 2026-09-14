"""工作流生成核心：仪器目录、工作流规范校验、场景导出。

设计依据（见 final_round/01_alab_instruments_workflow.md）：
- 仪器/任务/原语目录来自 A-Lab（Nature 2023）论文 Methods 与 alab_management /
  alab_control 代码，落在 configs/instruments_alab.json。
- 工作流规范 = AlabOS 风格任务链（samples × tasks，task 绑定 instrument 与机器人原语），
  每个原语带 SafeLab 式安全约束（ΔP / θ_dev / F_peak / tilt）。
- 导出两种下游格式：SafeLab 风格 YAML 任务配置（instruction / assets / scene /
  goals / safety_constraints）与 Isaac Sim 场景清单（USD 资产 + 位姿 + 机器人 + 相机），
  以及给重建 agent（codex cli）的任务简报。

引用零信任：spec.evidence[*].cite 必须存在于给定的 references.bib（AGENTS.md 铁律 2）。
本模块不做任何 LLM 调用；生成由调用方 agent 完成，这里只提供模板实例化与机械校验。
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / "configs" / "instruments_alab.json"
DEFAULT_TEMPLATES_DIR = ROOT / "configs" / "workflows"
DEFAULT_ASSET_REGISTRY = ROOT / "configs" / "safelab_asset_registry.json"

SPEC_VERSION = "1.0"
_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


# ---------------------------------------------------------------- catalog

def load_catalog(path: str | os.PathLike | None = None) -> dict:
    p = Path(path or os.environ.get("GOAI_INSTRUMENT_CATALOG", DEFAULT_CATALOG))
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def load_asset_registry(path: str | os.PathLike | None = None) -> dict | None:
    """SafeLab USD 资产登记表（由 5090 上 solid_assets_all 目录生成）；缺失返回 None。

    结构：{"assets": {"<asset_key>": {"usd": "<path>", "category": "...", "articulated": bool,
    "bbox_m": [x,y,z]}}, "root": "<dir>"}。
    """
    p = Path(path or os.environ.get("GOAI_ASSET_REGISTRY", DEFAULT_ASSET_REGISTRY))
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def list_instruments(catalog: dict | None = None) -> dict:
    cat = catalog or load_catalog()
    rows = []
    for key, inst in cat["instruments"].items():
        rows.append({
            "id": key,
            "name": inst["name"],
            "alab_ref": inst.get("alab_ref"),
            "driver": inst.get("driver"),
            "primitives": inst.get("primitives", []),
            "safelab_assets": inst.get("safelab_assets", []),
            "params": inst.get("params", {}),
        })
    return {
        "catalog_version": cat.get("catalog_version"),
        "source": cat.get("source"),
        "instruments": rows,
        "labware": cat.get("labware", {}),
        "primitives": cat.get("primitives", {}),
        "task_types": cat.get("task_types", {}),
        "embodiments": cat.get("embodiments", {}),
        "safety_defaults": cat.get("safety_defaults", {}),
    }


# ---------------------------------------------------------------- templates

def list_templates(templates_dir: str | os.PathLike | None = None) -> list[dict]:
    d = Path(templates_dir or os.environ.get("GOAI_WORKFLOW_TEMPLATES", DEFAULT_TEMPLATES_DIR))
    out = []
    if not d.exists():
        return out
    for p in sorted(d.glob("*.json")):
        try:
            with open(p, encoding="utf-8") as fh:
                spec = json.load(fh)
        except ValueError as exc:
            out.append({"id": p.stem, "path": str(p), "error": f"invalid JSON: {exc}"})
            continue
        out.append({
            "id": spec.get("id", p.stem),
            "title": spec.get("title"),
            "path": str(p),
            "n_tasks": len(spec.get("tasks", [])),
            "stations": [s.get("instrument") for s in spec.get("stations", [])],
            "goal": (spec.get("goal") or {}).get("objective"),
        })
    return out


def load_template(template_id: str, templates_dir: str | os.PathLike | None = None) -> dict:
    d = Path(templates_dir or os.environ.get("GOAI_WORKFLOW_TEMPLATES", DEFAULT_TEMPLATES_DIR))
    p = d / f"{template_id}.json"
    if not p.exists():
        raise FileNotFoundError(f"template not found: {template_id} (looked in {d})")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def instantiate_template(template_id: str, overrides: dict | None = None,
                         templates_dir: str | os.PathLike | None = None) -> dict:
    """按模板生成一份新 spec：允许覆盖 id/title/goal/samples/embodiment 与任务参数。

    overrides["task_params"] = {"<task_id>": {"heating_temperature": 950}} 只改参数不改结构。
    """
    spec = json.loads(json.dumps(load_template(template_id, templates_dir)))
    ov = overrides or {}
    for key in ("id", "title", "goal", "samples", "embodiment", "evidence"):
        if key in ov and ov[key] is not None:
            spec[key] = ov[key]
    task_params = ov.get("task_params") or {}
    for task in spec.get("tasks", []):
        if task["id"] in task_params:
            task.setdefault("params", {}).update(task_params[task["id"]])
    spec["template"] = template_id
    return spec


# ---------------------------------------------------------------- validation

def _bib_keys(bib_path: str | os.PathLike | None) -> set[str] | None:
    if not bib_path:
        return None
    p = Path(bib_path)
    if not p.exists():
        return set()
    text = p.read_text(encoding="utf-8", errors="replace")
    return set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", text))


def validate_spec(spec: dict, catalog: dict | None = None,
                  asset_registry: dict | None = None,
                  bib_path: str | os.PathLike | None = None) -> dict:
    """机械校验；返回 {"ok", "errors", "warnings", "stats"}。errors 非空即不可导出。"""
    cat = catalog or load_catalog()
    errors: list[str] = []
    warnings: list[str] = []

    if spec.get("spec_version") != SPEC_VERSION:
        warnings.append(f"spec_version {spec.get('spec_version')!r} != {SPEC_VERSION}")
    for key in ("id", "title", "goal", "embodiment", "samples", "stations", "tasks"):
        if key not in spec:
            errors.append(f"missing top-level field: {key}")
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings, "stats": {}}
    if not _ID_RE.match(str(spec["id"])):
        errors.append(f"id must match {_ID_RE.pattern}: {spec['id']!r}")

    emb = spec["embodiment"]
    if emb.get("robot") not in cat.get("embodiments", {}):
        errors.append(f"unknown embodiment robot {emb.get('robot')!r}; known: {sorted(cat.get('embodiments', {}))}")

    # samples / labware objects available for primitives
    sample_ids = [s.get("name") for s in spec["samples"]]
    if len(set(sample_ids)) != len(sample_ids) or any(not s for s in sample_ids):
        errors.append("sample names must be unique and non-empty")
    objects: set[str] = set()
    for s in spec["samples"]:
        for lw in s.get("labware", []):
            objects.add(lw)
    for obj in spec.get("objects", []):
        objects.add(obj.get("id"))

    # stations
    station_ids: set[str] = set()
    for st in spec["stations"]:
        sid = st.get("id")
        if not sid or sid in station_ids:
            errors.append(f"station id missing or duplicated: {sid!r}")
        station_ids.add(sid)
        inst = st.get("instrument")
        if inst not in cat["instruments"]:
            errors.append(f"station {sid}: unknown instrument {inst!r}")
        if asset_registry is not None:
            a = st.get("asset")
            if not a:
                warnings.append(f"station {sid}: no asset bound")
            elif a not in asset_registry.get("assets", {}):
                errors.append(f"station {sid}: asset {a!r} not in registry")
        elif not st.get("asset"):
            warnings.append(f"station {sid}: no asset bound (registry unavailable, not enforced)")
        pose = st.get("pose")
        if pose is not None and (not isinstance(pose, list) or len(pose) not in (3, 7)):
            errors.append(f"station {sid}: pose must be [x,y,z] or [x,y,z,qw,qx,qy,qz]")

    # tasks
    task_ids: set[str] = set()
    deps: dict[str, list[str]] = {}
    prims = cat.get("primitives", {})
    safety_defaults = cat.get("safety_defaults", {})
    n_prims = 0
    for t in spec["tasks"]:
        tid = t.get("id")
        if not tid or tid in task_ids:
            errors.append(f"task id missing or duplicated: {tid!r}")
            continue
        task_ids.add(tid)
        deps[tid] = list(t.get("depends_on", []))
        ttype = t.get("type")
        tdef = cat["task_types"].get(ttype)
        if tdef is None:
            errors.append(f"task {tid}: unknown type {ttype!r}")
            continue
        st_id = t.get("station")
        if st_id not in station_ids:
            errors.append(f"task {tid}: station {st_id!r} not declared")
        else:
            st = next(s for s in spec["stations"] if s.get("id") == st_id)
            if st.get("instrument") != tdef["instrument"]:
                errors.append(f"task {tid}: type {ttype} expects instrument {tdef['instrument']}, station {st_id} is {st.get('instrument')}")
        for s in t.get("samples", []):
            if s not in sample_ids:
                errors.append(f"task {tid}: unknown sample {s!r}")
        for p in tdef.get("params", []):
            if p not in (t.get("params") or {}):
                warnings.append(f"task {tid}: param {p!r} not set (catalog lists it for {ttype})")
        if not t.get("on_error"):
            warnings.append(f"task {tid}: no on_error policy (A-Lab default: retry 3 then request_user_input)")
        if tdef.get("robot") and not t.get("primitives"):
            errors.append(f"task {tid}: robot task has no primitives")
        for i, pr in enumerate(t.get("primitives", [])):
            n_prims += 1
            op = pr.get("op")
            pdef = prims.get(op)
            if pdef is None:
                errors.append(f"task {tid} primitive[{i}]: unknown op {op!r}")
                continue
            for arg in pdef.get("args", []):
                if arg not in pr:
                    errors.append(f"task {tid} primitive[{i}] {op}: missing arg {arg!r}")
            for ref_key in ("object", "to", "on", "tool"):
                ref = pr.get(ref_key)
                if ref and ref not in objects and ref not in station_ids and ref not in sample_ids:
                    errors.append(f"task {tid} primitive[{i}] {op}: {ref_key}={ref!r} is not a declared object/station/sample")
            if pr.get("station") and pr["station"] not in station_ids:
                errors.append(f"task {tid} primitive[{i}] {op}: station {pr['station']!r} not declared")
            need = pdef.get("safety", [])
            have = {**safety_defaults, **(spec.get("safety_constraints") or {}), **(t.get("safety") or {}), **(pr.get("safety") or {})}
            for k in need:
                if k not in have:
                    errors.append(f"task {tid} primitive[{i}] {op}: safety field {k!r} missing")
            if op in ("pour_powder", "pour_liquid"):
                tilt = have.get("tilt_limit_rad")
                if tilt is not None and tilt > 1.2:
                    errors.append(f"task {tid} primitive[{i}] {op}: tilt_limit_rad {tilt} exceeds 1.2 rad")

    for tid, ds in deps.items():
        for d in ds:
            if d not in task_ids:
                errors.append(f"task {tid}: depends_on unknown task {d!r}")
    if _has_cycle(deps):
        errors.append("task graph has a cycle")

    # evidence (citation zero-trust)
    keys = _bib_keys(bib_path)
    ev = spec.get("evidence", [])
    if not ev:
        warnings.append("no evidence entries; workflow steps should cite literature (goal.literature / evidence[])")
    for e in ev:
        cite = e.get("cite")
        if not cite:
            errors.append("evidence entry without cite key")
        elif keys is not None and cite not in keys:
            errors.append(f"evidence cite {cite!r} not found in references.bib (zero-trust)")

    stats = {
        "n_samples": len(sample_ids), "n_stations": len(station_ids),
        "n_tasks": len(task_ids), "n_primitives": n_prims, "n_evidence": len(ev),
        "safelab_categories": sorted({prims[p["op"]]["safelab_category"] for t in spec["tasks"]
                                      for p in t.get("primitives", []) if p.get("op") in prims}),
    }
    return {"ok": not errors, "errors": errors, "warnings": warnings, "stats": stats}


def _has_cycle(deps: dict[str, list[str]]) -> bool:
    state: dict[str, int] = {}

    def visit(n: str) -> bool:
        st = state.get(n, 0)
        if st == 1:
            return True
        if st == 2:
            return False
        state[n] = 1
        for m in deps.get(n, []):
            if m in deps and visit(m):
                return True
        state[n] = 2
        return False

    return any(visit(n) for n in deps)


def topological_order(spec: dict) -> list[str]:
    deps = {t["id"]: list(t.get("depends_on", [])) for t in spec["tasks"]}
    order: list[str] = []
    seen: set[str] = set()

    def visit(n: str) -> None:
        if n in seen:
            return
        seen.add(n)
        for m in deps.get(n, []):
            visit(m)
        order.append(n)

    for n in deps:
        visit(n)
    return order


# ---------------------------------------------------------------- export

def _yaml_scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return repr(v)
    s = str(v)
    if s == "" or re.search(r"[:#\[\]{}&*!|>'\"%@`,\n]|^\s|\s$", s) or s.lower() in ("yes", "no", "true", "false", "null"):
        return json.dumps(s, ensure_ascii=False)
    return s


def to_yaml(obj: Any, indent: int = 0) -> str:
    """最小 YAML 序列化（dict/list/标量），避免引入 pyyaml 依赖。"""
    pad = "  " * indent
    if isinstance(obj, dict):
        if not obj:
            return pad + "{}\n"
        out = []
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and v:
                out.append(f"{pad}{k}:\n{to_yaml(v, indent + 1)}")
            else:
                out.append(f"{pad}{k}: {_yaml_scalar(v) if not isinstance(v, (dict, list)) else ('{}' if isinstance(v, dict) else '[]')}\n")
        return "".join(out)
    if isinstance(obj, list):
        if not obj:
            return pad + "[]\n"
        out = []
        for v in obj:
            if isinstance(v, dict) and v:
                body = to_yaml(v, indent + 1)
                first, _, rest = body.partition("\n")
                out.append(f"{pad}- {first.strip()}\n" + (rest if rest.strip() == "" else rest))
            elif isinstance(v, list) and v:
                out.append(f"{pad}-\n{to_yaml(v, indent + 1)}")
            else:
                out.append(f"{pad}- {_yaml_scalar(v) if not isinstance(v, (dict, list)) else ('{}' if isinstance(v, dict) else '[]')}\n")
        return "".join(out)
    return pad + _yaml_scalar(obj) + "\n"


def _primitive_instruction(pr: dict) -> str:
    op = pr.get("op")
    o, to = pr.get("object"), pr.get("to")
    table = {
        "pick_place": f"Pick {o} and place it at {to}",
        "grasp": f"Grasp {o}",
        "release": f"Release {o}",
        "insert_rack": f"Insert {o} into {to}",
        "extract_rack": f"Take {o} out of {to}",
        "open_door": f"Open the door of {pr.get('station')}",
        "close_door": f"Close the door of {pr.get('station')}",
        "open_lid": f"Open the lid of {pr.get('station')}",
        "close_lid": f"Close the lid of {pr.get('station')}",
        "press_button": f"Press the {pr.get('button')} button on {pr.get('station')}",
        "clamp": f"Clamp {o} in {pr.get('station')}",
        "unclamp": f"Release {o} from {pr.get('station')}",
        "uncap": f"Unscrew the cap of {o}",
        "cap": f"Screw the cap onto {o}",
        "pour_powder": f"Pour the powder from {o} into {to} without spilling",
        "pour_liquid": f"Pour {pr.get('volume_ml')} mL from {o} into {to} without spilling",
        "flatten": f"Flatten the powder on {o} with {pr.get('tool')}",
        "weigh": f"Place {o} on {pr.get('station')} and read the mass",
        "handover": f"Hand {o} over to {to}",
        "stack": f"Stack {o} on {pr.get('on')}",
        "wait": f"Wait {pr.get('seconds')} s",
    }
    return table.get(op, f"{op} {pr}")


def export_safelab_tasks(spec: dict, catalog: dict | None = None) -> list[dict]:
    """每个机器人任务 → 一份 SafeLab 风格配置（instruction / assets / scene / goals / safety_constraints）。"""
    cat = catalog or load_catalog()
    prims = cat.get("primitives", {})
    defaults = {**cat.get("safety_defaults", {}), **(spec.get("safety_constraints") or {})}
    defaults.pop("note", None)
    station_by_id = {s["id"]: s for s in spec["stations"]}
    objects = {o["id"]: o for o in spec.get("objects", [])}
    out = []
    for tid in topological_order(spec):
        t = next(x for x in spec["tasks"] if x["id"] == tid)
        if not t.get("primitives"):
            continue
        used_assets: list[dict] = []
        seen: set[str] = set()
        for pr in t["primitives"]:
            for ref_key in ("object", "to", "on", "tool", "station"):
                ref = pr.get(ref_key)
                if not ref or ref in seen:
                    continue
                seen.add(ref)
                if ref in station_by_id:
                    st = station_by_id[ref]
                    used_assets.append({"id": ref, "role": "station", "instrument": st["instrument"], "asset": st.get("asset"), "pose": st.get("pose")})
                elif ref in objects:
                    ob = objects[ref]
                    used_assets.append({"id": ref, "role": "object", "labware": ob.get("labware"), "asset": ob.get("asset"), "pose": ob.get("pose")})
        goals = []
        for k, pr in enumerate(t["primitives"], 1):
            cat_name = prims.get(pr.get("op"), {}).get("safelab_category", "-")
            goals.append({"stage": k, "op": pr["op"], "category": cat_name, "instruction": _primitive_instruction(pr),
                          "safety": {**defaults, **(t.get("safety") or {}), **(pr.get("safety") or {})}})
        out.append({
            "task_id": f"{spec['id']}.{tid}",
            "instruction": t.get("instruction") or "; ".join(g["instruction"] for g in goals),
            "embodiment": spec["embodiment"],
            "assets": used_assets,
            "scene": {"workflow": spec["id"], "station": t.get("station"), "samples": t.get("samples", []),
                      "initial_state": t.get("initial_state", "sampled within reach; collision-free")},
            "goals": goals,
            "safety_constraints": {**defaults, **(t.get("safety") or {})},
            "process": {"type": t["type"], "params": t.get("params", {}), "on_error": t.get("on_error")},
        })
    return out


def export_isaac_manifest(spec: dict, asset_registry: dict | None = None) -> dict:
    """Isaac Sim 场景清单：机器人、仪器/器具 USD 与位姿、相机（SafeLab 三视角）、物理设置。"""
    reg = (asset_registry or {}).get("assets", {}) if asset_registry else {}
    root = (asset_registry or {}).get("root") if asset_registry else None
    prims = []
    for st in spec["stations"]:
        a = reg.get(st.get("asset") or "", {})
        prims.append({
            "prim_path": f"/World/Stations/{st['id']}",
            "kind": "station", "instrument": st["instrument"],
            "asset_key": st.get("asset"),
            "usd": a.get("usd"), "articulated": a.get("articulated"),
            "pose": st.get("pose") or [0, 0, 0, 1, 0, 0, 0],
            "semantic": st["instrument"],
        })
    for ob in spec.get("objects", []):
        a = reg.get(ob.get("asset") or "", {})
        prims.append({
            "prim_path": f"/World/Objects/{ob['id']}",
            "kind": "object", "labware": ob.get("labware"),
            "asset_key": ob.get("asset"), "usd": a.get("usd"),
            "pose": ob.get("pose") or [0, 0, 0, 1, 0, 0, 0],
            "semantic": ob.get("labware"),
            "sample": ob.get("sample"),
        })
    emb = spec["embodiment"]
    return {
        "workflow": spec["id"], "title": spec.get("title"),
        "asset_root": root,
        "robot": {"prim_path": "/World/Robot", "type": emb.get("robot"), "gripper": emb.get("gripper"),
                  "base_pose": emb.get("base_pose") or [0, 0, 0, 1, 0, 0, 0]},
        "cameras": [
            {"name": "head", "prim_path": "/World/Robot/head_cam", "resolution": [640, 480]},
            {"name": "wrist", "prim_path": "/World/Robot/panda_hand/wrist_cam", "resolution": [640, 480]},
            {"name": "third_person", "prim_path": "/World/Cameras/third_person", "resolution": [640, 480]},
        ],
        "physics": {"dt": 1 / 60, "gravity": -9.81, "fluid": "pbd" if any(p.get("op") == "pour_liquid" for t in spec["tasks"] for p in t.get("primitives", [])) else None},
        "recording": {"hz": 30, "streams": ["rgb", "depth", "seg", "joint_pos", "joint_vel", "ee_pose", "gripper", "contact_force", "safety_labels"]},
        "prims": prims,
        "task_order": topological_order(spec),
        "unresolved_assets": [p["asset_key"] for p in prims if p.get("asset_key") and not p.get("usd")],
        "unbound": [p["prim_path"] for p in prims if not p.get("asset_key")],
    }


def export_codex_brief(spec: dict, manifest: dict, safelab_tasks: list[dict]) -> str:
    """给 codex cli 重建/采集 agent 的任务简报（Markdown）。"""
    lines = [f"# Scene reconstruction + data collection brief: {spec['id']}", "",
             f"Title: {spec.get('title')}", f"Objective: {(spec.get('goal') or {}).get('objective')}", "",
             "## Robot", f"- {manifest['robot']['type']} with {manifest['robot']['gripper']}, base pose {manifest['robot']['base_pose']}", "",
             "## Stations and objects to place (USD under asset_root = %s)" % manifest.get("asset_root")]
    for p in manifest["prims"]:
        lines.append(f"- `{p['prim_path']}` ← {p.get('asset_key') or 'UNBOUND'} ({p.get('usd') or 'usd not resolved'}) pose={p['pose']}")
    lines += ["", "## Tasks (execute in this order; record every episode at 30 Hz with the streams in the manifest)"]
    for t in safelab_tasks:
        lines.append(f"### {t['task_id']}")
        lines.append(f"Instruction: {t['instruction']}")
        for g in t["goals"]:
            lines.append(f"  {g['stage']}. [{g['category']}] {g['instruction']}  (safety: ΔP≤{g['safety'].get('dp_max_mm')} mm, θ≤{g['safety'].get('theta_dev_max_rad')} rad, F≤{g['safety'].get('f_peak_max_n')} N)")
        lines.append(f"Process params: {json.dumps(t['process']['params'], ensure_ascii=False)}; on_error: {t['process']['on_error']}")
        lines.append("")
    if manifest["unresolved_assets"] or manifest["unbound"]:
        lines += ["## Open items", f"- unresolved asset keys: {manifest['unresolved_assets']}", f"- unbound prims: {manifest['unbound']}"]
    return "\n".join(lines) + "\n"


def export_all(spec: dict, out_dir: str | os.PathLike, catalog: dict | None = None,
               asset_registry: dict | None = None, bib_path: str | os.PathLike | None = None) -> dict:
    report = validate_spec(spec, catalog, asset_registry, bib_path)
    if not report["ok"]:
        return {"ok": False, "validation": report}
    out = Path(out_dir) / spec["id"]
    out.mkdir(parents=True, exist_ok=True)
    tasks = export_safelab_tasks(spec, catalog)
    manifest = export_isaac_manifest(spec, asset_registry)
    (out / "workflow.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "isaac_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    task_dir = out / "safelab_tasks"
    task_dir.mkdir(exist_ok=True)
    for t in tasks:
        (task_dir / (t["task_id"].split(".", 1)[1] + ".yaml")).write_text(to_yaml(t), encoding="utf-8")
    (out / "CODEX_BRIEF.md").write_text(export_codex_brief(spec, manifest, tasks), encoding="utf-8")
    return {"ok": True, "out_dir": str(out), "validation": report,
            "files": ["workflow.json", "isaac_manifest.json", "CODEX_BRIEF.md"] + [f"safelab_tasks/{t['task_id'].split('.', 1)[1]}.yaml" for t in tasks],
            "unresolved_assets": manifest["unresolved_assets"], "unbound": manifest["unbound"]}
