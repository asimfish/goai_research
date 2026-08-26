"""goai-retro MCP server —— 逆合成预测器接入 + 实验方案骨架。

预测器可插拔（GOAI_RETRO_PROVIDER=stub|http）：
- stub：确定性模板，用于走通「idea → 逆合成 → 实验方案 → 审核 → 二次查验」回环
- http：POST 到 GOAI_RETRO_API_URL（自建 ASKCOS / IBM RXN 网关 / 本地模型均可）

安全边界：本 server 只做计算与格式化，不做任何实验执行；
实验方案必须经 goai-reviewer 审核 + goai-refcheck 文献二次查验后才算产物。
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.core.mcp_compat import FastMCP

from server.core import retro

mcp = FastMCP("goai-retro")


@mcp.tool()
def provider_status() -> str:
    """查询当前逆合成后端配置（provider / API 地址 / 是否可信）。"""
    provider = os.environ.get("GOAI_RETRO_PROVIDER", "stub")
    return retro.to_json({
        "provider": provider,
        "api_url": os.environ.get("GOAI_RETRO_API_URL") or None,
        "trusted": provider == "http" and bool(os.environ.get("GOAI_RETRO_API_URL")),
        "note": "stub 输出仅供流程演示，不可作为化学结论写入论文" if provider == "stub"
                else "http 后端结果的可信度由后端决定，仍需 reviewer 审核",
    })


@mcp.tool()
def predict_retro(target_smiles: str, max_depth: int = 3) -> str:
    """对目标分子做逆合成路线预测。

    Args:
        target_smiles: 目标分子 SMILES
        max_depth: 最大拆解深度
    Returns:
        JSON 路线 {provider, steps: [{reaction, precursors, confidence}], ...}
    """
    return retro.to_json(retro.predict(target_smiles, max_depth))


@mcp.tool()
def make_experiment_plan(route_json: str, objective: str = "") -> str:
    """把逆合成路线转为实验方案骨架（含审核闸门清单，供 idea-forge 填充）。

    Args:
        route_json: predict_retro 的输出 JSON
        objective: 实验目标一句话
    Returns:
        JSON 实验方案骨架；steps[*] 的 conditions/safety 为 TODO，
        由 idea-forge 依文献填写并附引用，交 reviewer 审核。
    """
    route = json.loads(route_json)
    return retro.to_json(retro.experiment_plan_skeleton(route, objective))


if __name__ == "__main__":
    mcp.run()
