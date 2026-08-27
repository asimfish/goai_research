"""逆合成预测器可插拔适配层。

provider 通过环境变量选择：
  GOAI_RETRO_PROVIDER  = stub | http     （默认 stub）
  GOAI_RETRO_API_URL   = http 后端地址（如自建 ASKCOS / RXN 网关 / 本地模型服务）
  GOAI_RETRO_API_KEY   = 可选鉴权
  GOAI_RETRO_TIMEOUT   = http 超时秒数（默认 120）
  GOAI_RETRO_TRUST_ENV = 1/0 是否按环境代理设置走代理；默认对 localhost 后端不走代理

stub：确定性模板输出，用于走通「idea → 逆合成 → 实验方案 → 审核」回环；
      结果显式标记 provider=stub / verified=false，审核 agent 不得把它当真值。
http：POST {target_smiles, max_depth} 到 GOAI_RETRO_API_URL，透传 JSON 结果。
      对接真实预测器（ASKCOS、IBM RXN、本地 retro 模型）只需实现该接口。
      后端任何异常（超时/非 2xx/畸形 JSON/连不上）都收敛为
      {"ok": false, "error": ...}，不向 MCP 调用方抛裸异常。
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


def _http_error(msg: str) -> dict[str, Any]:
    return {"provider": "http", "ok": False, "verified": False, "error": msg}


def _timeout() -> float:
    try:
        return float(os.environ.get("GOAI_RETRO_TIMEOUT", "120"))
    except ValueError:
        return 120.0


def _trust_env(url: str) -> bool:
    """是否让 httpx 采用环境/系统代理设置。

    默认对 loopback 后端关闭：httpx 不像 urllib 那样自动 bypass localhost，
    自建 ASKCOS / 本地模型服务会被系统代理劫持，报出与后端无关的 502，
    并把 API key 送进代理进程。GOAI_RETRO_TRUST_ENV 可显式覆盖。
    """
    override = os.environ.get("GOAI_RETRO_TRUST_ENV")
    if override is not None:
        return override.strip().lower() not in ("0", "false", "no", "")
    try:
        host = (httpx.URL(url).host or "").lower()
    except Exception:  # noqa: BLE001  URL 畸形时交给请求阶段报错
        return True
    return not (host == "localhost" or host == "::1"
                or host.startswith("127.") or host.endswith(".localhost"))


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
    timeout = _timeout()
    try:
        with httpx.Client(timeout=timeout,
                          trust_env=_trust_env(url)) as client:
            resp = client.post(url, headers=headers,
                               json={"target_smiles": target_smiles,
                                     "max_depth": max_depth})
        if resp.status_code >= 400:
            return _http_error(
                f"后端返回 HTTP {resp.status_code}；响应片段: "
                f"{resp.text[:200]!r}")
        data = resp.json()
    except httpx.TimeoutException:
        return _http_error(
            f"后端 {timeout}s 内未响应（GOAI_RETRO_TIMEOUT 可调）；"
            "请检查后端负载或换用更小的 max_depth。")
    except httpx.HTTPError as e:
        return _http_error(
            f"连接逆合成后端失败: {type(e).__name__}: {e}；"
            "请检查 GOAI_RETRO_API_URL 与后端存活状态。")
    except ValueError as e:  # json.JSONDecodeError 是其子类
        return _http_error(f"后端响应不是合法 JSON: {e}")
    if not isinstance(data, dict):
        return _http_error(
            f"后端响应 JSON 顶层应为对象，实得 {type(data).__name__}；"
            "请按 {target_smiles, route_id, steps:[...]} 约定返回。")
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


def _normalize_steps(raw: Any) -> tuple[list[dict[str, Any]], list[str]]:
    """把后端返回的 steps 收敛成 list[dict]，并如实报告不合约定之处。

    真实后端（含版本漂移、网关改写）会把 steps 返回成 {"1": {...}} 形态、
    null、甚至元素是字符串。这些都能过 json.loads 与顶层 dict 校验，
    带着 ok=true 流到下游；直接迭代会在 MCP 工具层抛裸 AttributeError，
    调用方只看到 "Error executing tool make_experiment_plan"，
    分不清是后端违约还是本服务有 bug。
    """
    if raw is None:
        return [], []
    problems: list[str] = []
    if isinstance(raw, dict):
        # {"1": {...}, "2": {...}} 形态：按 key 排序摊平，不猜化学含义
        problems.append(f"steps 是对象而非数组（key: {sorted(map(str, raw))}）"
                        "，已按 key 排序摊平")
        raw = [raw[k] for k in sorted(raw, key=str)]
    if not isinstance(raw, list):
        return [], [f"steps 类型应为数组，实得 {type(raw).__name__}，已整体忽略"]
    steps: list[dict[str, Any]] = []
    for idx, item in enumerate(raw):
        if isinstance(item, dict):
            steps.append(item)
        else:
            problems.append(f"steps[{idx}] 应为对象，实得 "
                            f"{type(item).__name__}，已跳过")
    return steps, problems


def experiment_plan_skeleton(route: dict[str, Any],
                             objective: str = "") -> dict[str, Any]:
    """由逆合成路线生成实验方案骨架（供 idea-forge 填充、reviewer 审核）。"""
    raw_steps, route_problems = _normalize_steps(route.get("steps"))
    steps = []
    for s in raw_steps:
        steps.append({
            "step": s.get("step"),
            "reaction": s.get("reaction"),
            "inputs": s.get("precursors", []),
            "conditions": "TODO: 温度/溶剂/催化剂/时长（由 agent 依文献填写并给出引用）",
            "characterization": "TODO: NMR/MS/HPLC 等表征手段",
            "safety": "TODO: 危险性评估与防护（强制项，审核不过不得输出）",
            "citations_required": True,
        })
    # 失败的预测（ok=false）绝不能被当成「已验证」路线带进实验方案；
    # 结构读不全的路线同样不算已验证 —— 解析时丢过步骤就不能声称完整；
    # 一步都没有的空路线也不算（否则 0 步方案会空过审核闸门）。
    verified = bool(route.get("verified", route.get("provider") != "stub")) \
        and route.get("ok", True) is not False \
        and not route_problems \
        and bool(steps)
    plan = {
        "objective": objective,
        "route_id": route.get("route_id"),
        "provider": route.get("provider"),
        "provider_verified": verified,
        "steps": steps,
        "review_gates": [
            "文献支持：每步条件至少 1 条真实引用（经 goai-refcheck 核验）",
            "可行性：试剂可购/可制备，路线深度合理",
            "安全性：安全字段完整，无高危未标注操作",
            "新颖性：与检索到的已有工作明确区分",
        ],
    }
    if route_problems:
        plan["route_problems"] = route_problems
    return plan


def to_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)
