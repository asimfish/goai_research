"""逆合成预测器可插拔适配层。

provider 通过环境变量选择：
  GOAI_RETRO_PROVIDER = stub | http     （默认 stub）
  GOAI_RETRO_API_URL  = http 后端地址（如自建 ASKCOS / RXN 网关 / 本地模型服务）
  GOAI_RETRO_API_KEY  = 可选鉴权

stub：确定性模板输出，用于走通「idea → 逆合成 → 实验方案 → 审核」回环；
      结果显式标记 provider=stub / verified=false，审核 agent 不得把它当真值。
http：POST {target_smiles, max_depth} 到 GOAI_RETRO_API_URL，透传 JSON 结果。
      对接真实预测器（ASKCOS、IBM RXN、本地 retro 模型）只需实现该接口。
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any

import httpx


def predict(target_smiles: str, max_depth: int = 3) -> dict[str, Any]:
    provider = os.environ.get("GOAI_RETRO_PROVIDER", "stub").lower()
    if provider == "http":
        return _predict_http(target_smiles, max_depth)
    return _predict_stub(target_smiles, max_depth)


def _predict_http(target_smiles: str, max_depth: int) -> dict[str, Any]:
    url = os.environ.get("GOAI_RETRO_API_URL")
    if not url:
        return {"provider": "http", "ok": False,
                "error": "未配置 GOAI_RETRO_API_URL；请设置逆合成后端地址，"
                         "或改用 GOAI_RETRO_PROVIDER=stub 走演示模板。"}
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("GOAI_RETRO_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    resp = httpx.post(url, headers=headers, timeout=120.0,
                      json={"target_smiles": target_smiles,
                            "max_depth": max_depth})
    resp.raise_for_status()
    data = resp.json()
    data.setdefault("provider", "http")
    data.setdefault("ok", True)
    return data


def _predict_stub(target_smiles: str, max_depth: int) -> dict[str, Any]:
    """确定性演示路线：按 SMILES 哈希生成稳定的假想两步拆解。"""
    h = hashlib.sha256(target_smiles.encode()).hexdigest()[:8]
    return {
        "provider": "stub",
        "ok": True,
        "verified": False,
        "warning": ("stub 路线仅用于流程演示，非真实化学预测；"
                    "接真实预测器请设 GOAI_RETRO_PROVIDER=http 与 GOAI_RETRO_API_URL。"),
        "target_smiles": target_smiles,
        "route_id": f"stub-{h}",
        "steps": [
            {"step": 1, "reaction": "disconnection A（模板占位）",
             "precursors": [f"PRECURSOR-A1-{h}", f"PRECURSOR-A2-{h}"],
             "confidence": 0.42},
            {"step": 2, "reaction": "disconnection B（模板占位）",
             "precursors": [f"COMMERCIAL-B1-{h}"],
             "confidence": 0.37},
        ][:max_depth],
    }


def experiment_plan_skeleton(route: dict[str, Any],
                             objective: str = "") -> dict[str, Any]:
    """由逆合成路线生成实验方案骨架（供 idea-forge 填充、reviewer 审核）。"""
    steps = []
    for s in route.get("steps", []):
        steps.append({
            "step": s.get("step"),
            "reaction": s.get("reaction"),
            "inputs": s.get("precursors", []),
            "conditions": "TODO: 温度/溶剂/催化剂/时长（由 agent 依文献填写并给出引用）",
            "characterization": "TODO: NMR/MS/HPLC 等表征手段",
            "safety": "TODO: 危险性评估与防护（强制项，审核不过不得输出）",
            "citations_required": True,
        })
    return {
        "objective": objective,
        "route_id": route.get("route_id"),
        "provider": route.get("provider"),
        "provider_verified": bool(route.get("verified", route.get("provider") != "stub")),
        "steps": steps,
        "review_gates": [
            "文献支持：每步条件至少 1 条真实引用（经 goai-refcheck 核验）",
            "可行性：试剂可购/可制备，路线深度合理",
            "安全性：安全字段完整，无高危未标注操作",
            "新颖性：与检索到的已有工作明确区分",
        ],
    }


def to_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)
