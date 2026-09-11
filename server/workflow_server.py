"""goai-workflow MCP server —— 实验工作流生成：仪器目录（A-Lab）、模板实例化、
机械校验（任务图 / 原语词表 / 安全约束 / 引用零信任）、场景导出（SafeLab YAML +
Isaac Sim 清单 + codex 重建简报）。

本 server 不调用 LLM：调用方 agent 负责按文献写出 spec，这里保证 spec 只用目录里
存在的仪器/原语、每个接触类原语都带安全阈值、每条依据都能在 references.bib 找到。
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.core.mcp_compat import FastMCP
from server.core import jsonout
from server.core import workflow as wf

mcp = FastMCP("goai-workflow")


def _dumps(obj) -> str:
    return jsonout.dumps(obj)


def _default_out_dir() -> str:
    return os.path.join(os.environ.get("GOAI_WORKSPACE", "workspace"), "workflows")


@mcp.tool()
def workflow_spec_schema() -> str:
    """返回工作流规范（spec v1.0）的字段说明与最小示例（写 spec 前先读这个）。"""
    example = {
        "spec_version": wf.SPEC_VERSION,
        "id": "wf_example", "title": "Calcine one crucible and run XRD",
        "goal": {"objective": "...", "target_phase": "BaZn2Si2O7", "literature": ["<bibkey>"]},
        "embodiment": {"robot": "franka_fr3", "gripper": "franka_hand", "base_pose": [0, 0, 0, 1, 0, 0, 0]},
        "samples": [{"name": "s1", "precursors": {"BaCO3": 1.0, "ZnO": 2.0, "SiO2": 2.0}, "labware": ["crucible_s1"]}],
        "stations": [{"id": "furnace_1", "instrument": "box_furnace", "asset": "art:Oven065", "pose": [1.0, 0.0, 0.0]}],
        "objects": [{"id": "crucible_s1", "labware": "crucible", "asset": "Crucible", "sample": "s1", "pose": [0.4, 0.2, 0.8]},
                    {"id": "tray_1", "labware": "crucible_tray", "asset": None}],
        "tasks": [{"id": "t_heat", "type": "Heating", "station": "furnace_1", "samples": ["s1"], "depends_on": [],
                   "params": {"heating_temperature": 950, "heating_time": 240},
                   "primitives": [{"op": "pick_place", "object": "crucible_s1", "to": "tray_1"},
                                  {"op": "open_door", "station": "furnace_1"},
                                  {"op": "insert_rack", "object": "tray_1", "to": "furnace_1"},
                                  {"op": "close_door", "station": "furnace_1"},
                                  {"op": "press_button", "station": "furnace_1", "button": "start"},
                                  {"op": "wait", "seconds": 60}],
                   "on_error": {"retry": 3, "then": "request_user_input"}}],
        "safety_constraints": {"dp_max_mm": 20, "theta_dev_max_rad": 0.25, "f_peak_max_n": 20, "tilt_limit_rad": 0.85},
        "evidence": [{"claim": "A-Lab heats in air with 2 C/min to 300 C then 15 C/min", "cite": "<bibkey>"}],
    }
    doc = {
        "spec_version": wf.SPEC_VERSION,
        "fields": {
            "goal": "objective / target_phase / literature[]（bib key）",
            "embodiment": "robot ∈ catalog.embodiments；gripper；base_pose [x,y,z,qw,qx,qy,qz]",
            "samples[]": "name（唯一）/ precursors{formula: g} / labware[]（本样品专属器具 id）",
            "stations[]": "id / instrument ∈ catalog.instruments / asset（资产登记表 key）/ pose",
            "objects[]": "id / labware ∈ catalog.labware / asset / sample / pose",
            "tasks[]": "id / type ∈ catalog.task_types / station / samples[] / depends_on[] / params / primitives[] / on_error / safety / instruction",
            "primitives[]": "op ∈ catalog.primitives，参数按 catalog.primitives[op].args；接触类原语必须能取到 safety 字段（spec→task→primitive 逐层覆盖）",
            "evidence[]": "claim + cite；cite 必须在 references.bib 中（零信任）",
        },
        "rules": [
            "任务 type 的 instrument 必须与 station.instrument 一致",
            "depends_on 构成 DAG",
            "pour_* 的 tilt_limit_rad ≤ 1.2",
            "机器人任务必须有 primitives",
        ],
        "example": example,
    }
    return _dumps(doc)


@mcp.tool()
def list_instruments() -> str:
    """列出仪器目录（A-Lab 三站 + 耗材 + 原语词表 + 任务类型 + 本体 + 安全默认值）。"""
    return _dumps(wf.list_instruments())


@mcp.tool()
def list_workflow_templates() -> str:
    """列出 configs/workflows/*.json 里的工作流模板（id/title/任务数/仪器）。"""
    return _dumps({"templates": wf.list_templates()})


@mcp.tool()
def instantiate_workflow(template_id: str, overrides_json: str = "{}") -> str:
    """按模板生成 spec 并立即校验。

    Args:
        template_id: list_workflow_templates 返回的 id
        overrides_json: 可覆盖 id/title/goal/samples/embodiment/evidence，以及
            task_params={"<task_id>": {...}} 只改参数
    Returns: {"spec": ..., "validation": {...}}
    """
    overrides = json.loads(overrides_json or "{}")
    spec = wf.instantiate_template(template_id, overrides)
    report = wf.validate_spec(spec, asset_registry=wf.load_asset_registry(),
                              bib_path=os.environ.get("GOAI_BIB_PATH"))
    return _dumps({"spec": spec, "validation": report})


@mcp.tool()
def validate_workflow(spec_json: str, bib_path: str = "", asset_registry_path: str = "") -> str:
    """机械校验一份 spec：仪器/原语/任务图/安全字段/引用零信任。

    Args:
        spec_json: 工作流 spec JSON
        bib_path: references.bib 路径（给了就核对 evidence[].cite；默认读 GOAI_BIB_PATH）
        asset_registry_path: SafeLab 资产登记表（默认 configs/safelab_asset_registry.json；缺失时资产绑定只告警）
    """
    spec = json.loads(spec_json)
    reg = wf.load_asset_registry(asset_registry_path or None)
    report = wf.validate_spec(spec, asset_registry=reg, bib_path=bib_path or os.environ.get("GOAI_BIB_PATH"))
    report["asset_registry_loaded"] = reg is not None
    return _dumps(report)


@mcp.tool()
def export_workflow(spec_json: str, out_dir: str = "", bib_path: str = "", asset_registry_path: str = "") -> str:
    """校验并导出：workflow.json、isaac_manifest.json、safelab_tasks/*.yaml、CODEX_BRIEF.md。

    Args:
        spec_json: 工作流 spec JSON
        out_dir: 输出根目录（默认 $GOAI_WORKSPACE/workflows）；实际写到 <out_dir>/<spec.id>/
    """
    spec = json.loads(spec_json)
    reg = wf.load_asset_registry(asset_registry_path or None)
    result = wf.export_all(spec, out_dir or _default_out_dir(), asset_registry=reg,
                           bib_path=bib_path or os.environ.get("GOAI_BIB_PATH"))
    return _dumps(result)


@mcp.tool()
def asset_registry_status(asset_registry_path: str = "") -> str:
    """资产登记表状态：是否存在、资产数、按类别计数、未绑定的目录仪器。"""
    reg = wf.load_asset_registry(asset_registry_path or None)
    if reg is None:
        return _dumps({"ok": False, "error": "asset registry not found; generate it from the 5090 solid_assets_all listing",
                       "expected_path": str(wf.DEFAULT_ASSET_REGISTRY)})
    cat = wf.load_catalog()
    assets = reg.get("assets", {})
    by_cat: dict[str, int] = {}
    for a in assets.values():
        by_cat[a.get("category", "?")] = by_cat.get(a.get("category", "?"), 0) + 1
    missing = {}
    for key, inst in cat["instruments"].items():
        cands = [c for c in inst.get("safelab_assets", []) if c in assets]
        if not cands:
            missing[key] = inst.get("safelab_assets", [])
    return _dumps({"ok": True, "root": reg.get("root"), "n_assets": len(assets), "by_category": by_cat,
                   "instruments_without_asset": missing})


if __name__ == "__main__":
    mcp.run()
