"""Four disjoint token buckets, Decimal pricing, and attributable cost totals.

No text is tokenized here: only provider/CLI usage counters are accepted.
Missing usage or an unknown tariff stays visible instead of becoming free.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any

BUCKETS = ("input", "output", "cache_read", "cache_write")
DEFAULT_PRICES = Path(__file__).resolve().parents[2] / "configs/model_prices.json"


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def money(value: Any) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("价格不能为布尔值")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("价格必须是非负有限数") from None
    if not result.is_finite() or result < 0:
        raise ValueError("价格必须是非负有限数")
    return result


def number(value: Decimal) -> str:
    return format(value, "f")


def tokens(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("token 用量必须是非负整数")
    return value


def normalize_usage(usage: dict, fmt: str = "auto") -> dict:
    """OpenAI/Codex totals include cache buckets; Anthropic input excludes them."""
    if not isinstance(usage, dict) or not usage:
        raise ValueError("未返回 usage")
    if fmt not in ("auto", "openai", "codex", "deepseek", "anthropic", "normalized"):
        raise ValueError("未知用量格式")
    warnings = []
    if fmt == "normalized":
        if any(k not in usage for k in BUCKETS):
            raise ValueError("标准用量必须包含全部四类 token")
        normalized = {k: tokens(usage[k]) for k in BUCKETS}
        return {"tokens": normalized, "input_total": sum(normalized[k] for k in ("input", "cache_read", "cache_write")), "warnings": []}
    anthropic = fmt == "anthropic" or (fmt == "auto" and any(k in usage for k in ("cache_creation_input_tokens", "cache_read_input_tokens")))
    details = usage.get("input_tokens_details") or usage.get("prompt_tokens_details") or {}
    if not isinstance(details, dict):
        raise ValueError("缓存用量详情必须为对象")
    raw_input = usage.get("input_tokens", usage.get("prompt_tokens"))
    raw_output = usage.get("output_tokens", usage.get("completion_tokens"))
    if raw_input is None or raw_output is None:
        raise ValueError("usage 缺少 input/output 计数")
    total, output = tokens(raw_input), tokens(raw_output)
    if anthropic:
        read = tokens(usage.get("cache_read_input_tokens", 0))
        write = tokens(usage.get("cache_creation_input_tokens", 0))
        plain = total
        total += read + write
    else:
        read_value = usage.get("cached_input_tokens", usage.get("prompt_cache_hit_tokens", details.get("cached_tokens")))
        write_value = usage.get("cache_write_input_tokens", details.get("cache_write_tokens"))
        if read_value is None:
            warnings.append("cache_read_not_reported")
        if write_value is None and "prompt_cache_hit_tokens" not in usage:
            warnings.append("cache_write_not_reported")
        read, write = tokens(0 if read_value is None else read_value), tokens(0 if write_value is None else write_value)
        plain = total - read - write
        if plain < 0:
            raise ValueError("缓存 token 超过总输入；拒绝重复或负数计费")
        if "prompt_cache_miss_tokens" in usage and tokens(usage["prompt_cache_miss_tokens"]) != total - read:
            raise ValueError("DeepSeek hit/miss 与总输入不一致")
    # Reasoning is a subset of output, never an additional charge.
    return {"tokens": dict(zip(BUCKETS, (plain, output, read, write))), "input_total": total, "warnings": warnings}


class PriceBook:
    def __init__(self, config: dict):
        if not isinstance(config, dict):
            raise ValueError("价格表必须为 JSON 对象")
        if config.get("schema") != "goai-pricing/1" or config.get("unit_tokens") != 1_000_000:
            raise ValueError("价格表必须使用 goai-pricing/1 和每百万 token 单位")
        currency = config.get("currency", "")
        if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha() or currency != currency.upper():
            raise ValueError("currency 必须是三位大写币种")
        if not isinstance(config.get("version"), str) or not config["version"].strip():
            raise ValueError("价格版本不能为空")
        if not isinstance(config.get("models"), dict) or not config["models"]:
            raise ValueError("价格表至少需要一个模型")
        self.aliases = {}
        for model, data in config["models"].items():
            if not isinstance(model, str) or not model.strip():
                raise ValueError("模型名不能为空")
            if not isinstance(data, dict) or not isinstance(data.get("rates"), dict) or any(k not in data["rates"] for k in BUCKETS):
                raise ValueError("每个模型需要四类价格")
            if not isinstance(data.get("aliases", []), list):
                raise ValueError("模型别名必须为数组")
            for key in BUCKETS:
                money(data["rates"][key])
            for group in ("long_context_multipliers", "service_tiers"):
                for value in data.get(group, {}).values():
                    money(value)
            if "long_context_threshold" in data:
                tokens(data["long_context_threshold"])
            if data.get("peak_utc"):
                peak = data["peak_utc"]
                money(peak["multiplier"])
                if any(type(d) is not int or not 0 <= d <= 6 for d in peak["weekdays"]):
                    raise ValueError("峰时星期必须为 0–6")
                if any(len(h) != 2 or not all(type(x) is int for x in h) or not 0 <= h[0] < h[1] <= 24 for h in peak["hours"]):
                    raise ValueError("峰时时间段不合法")
            for name in [model, *data.get("aliases", [])]:
                if not isinstance(name, str) or not name.strip() or name.casefold() in self.aliases:
                    raise ValueError("模型别名重复或无效: " + str(name))
                self.aliases[name.casefold()] = model
        for tariff in config.get("tools", {}).values():
            money(tariff["per_call"])
            money(tariff.get("per_second", "0"))
        self.config = config
        self.revision = digest(config)
        self.currency = currency

    @classmethod
    def load(cls, path: str | Path = DEFAULT_PRICES):
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def price(self, record: dict) -> dict:
        out = {**record, "currency": self.currency, "price_version": self.config["version"],
               "price_revision": self.revision, "cost": None, "warnings": list(record.get("warnings", []))}
        if record["kind"] == "missing":
            out["warnings"].append(record.get("reason", "usage_missing"))
            return out
        if record["kind"] == "tool":
            key = record["server"] + "." + record["tool"]
            tariff = self.config.get("tools", {}).get(key, self.config.get("tools", {}).get(record["tool"]))
            if tariff is None:
                local = record["server"] in self.config.get("local_mcp_servers", []) or record.get("local_tool") is True
                if not local:
                    out["warnings"].append("tool_price_missing")
                    return out
                tariff = {"per_call": "0", "per_second": "0"}
            fee = money(tariff["per_call"])
            per_second = money(tariff.get("per_second", "0"))
            if per_second and record.get("duration_ms") is None:
                out["warnings"].append("tool_duration_missing")
                return out
            fee += per_second * money(record.get("duration_ms") or 0) / 1000
            out.update(cost=number(fee), tool_cost=number(fee), tariff=tariff)
            return out
        normalized = normalize_usage(record["usage"], record.get("format", "auto"))
        out.update(tokens=normalized["tokens"], input_total=normalized["input_total"])
        out["warnings"] += normalized["warnings"]
        model = self.aliases.get(str(record.get("model", "")).casefold())
        if model is None:
            out["warnings"].append("model_price_missing")
            return out
        out["canonical_model"] = model
        entry = self.config["models"][model]
        tier = record.get("service_tier") or "standard"
        if not record.get("service_tier"):
            out["warnings"].append("service_tier_assumed_standard")
        tiers = entry.get("service_tiers", {"standard": "1", "default": "1"})
        if tier not in tiers:
            out["warnings"].append("service_tier_price_missing")
            return out
        multiplier = money(tiers[tier])
        if entry.get("peak_utc"):
            try:
                instant = datetime.fromisoformat(str(record.get("timestamp", "")).replace("Z", "+00:00"))
                if instant.tzinfo is None:
                    raise ValueError("缺少时区")
                instant = instant.astimezone(timezone.utc)
            except ValueError:
                out["warnings"].append("peak_time_unknown")
                return out
            peak = entry["peak_utc"]
            if record.get("usage_scope", "request") != "request":
                out["warnings"].append("aggregate_peak_time_assumed")
            if instant.weekday() in peak["weekdays"] and any(a <= instant.hour < b for a, b in peak["hours"]):
                multiplier *= money(peak["multiplier"])
                out["peak"] = True
        long = False
        if entry.get("long_context_threshold"):
            context = record.get("request_input_tokens")
            if context is None and record.get("usage_scope", "request") == "request":
                context = normalized["input_total"]
            if context is None:
                out["warnings"].append("aggregate_context_unknown_standard_context_rates")
            else:
                long = tokens(context) > entry["long_context_threshold"]
        rates = {k: money(entry["rates"][k]) * multiplier * (money(entry.get("long_context_multipliers", {}).get(k, "1")) if long else 1) for k in BUCKETS}
        costs = {k: rates[k] * normalized["tokens"][k] / 1_000_000 for k in BUCKETS}
        out.update(cost=number(sum(costs.values())), token_costs={k: number(v) for k, v in costs.items()},
                   rates={k: number(v) for k, v in rates.items()}, long_context=long, applied_service_tier=tier)
        return out


def total(records: list[dict]) -> dict:
    counts = Counter(r["kind"] for r in records)
    currencies = {}
    for r in records:
        cur = currencies.setdefault(r["currency"], {"total": Decimal(0), "model": Decimal(0), "tools": Decimal(0),
            "token_costs": {k: Decimal(0) for k in BUCKETS}})
        if r.get("cost") is not None:
            cost = money(r["cost"])
            cur["total"] += cost
            cur["tools" if r["kind"] == "tool" else "model"] += cost
            for k, value in r.get("token_costs", {}).items():
                cur["token_costs"][k] += money(value)
    warnings = Counter(w for r in records for w in r.get("warnings", []))
    unpriced = sum(r.get("cost") is None for r in records)
    return {"tokens": {k: sum(r.get("tokens", {}).get(k, 0) for r in records) for k in BUCKETS},
        "currencies": {c: {**{k: number(v) for k, v in d.items() if k != "token_costs"},
            "token_costs": {k: number(v) for k, v in d["token_costs"].items()}} for c, d in currencies.items()},
        "records": len(records), "usage_records": counts["usage"], "mcp_calls": counts["tool"],
        "missing_usage": counts["missing"], "unpriced_records": unpriced,
        "mcp_duration_ms": sum(float(r.get("duration_ms") or 0) for r in records if r["kind"] == "tool"),
        "warnings": dict(warnings), "status": "partial" if unpriced else "estimated" if warnings else "complete"}


def summarize(records: list[dict]) -> dict:
    # The same provider event in a copied trace must not be billed twice.
    unique = {}
    duplicates = 0
    for original in sorted(records, key=lambda r: str(r.get("source", ""))):
        r = dict(original)
        event_id = r["event_id"]
        # Codex thread/call IDs and hashed legacy audit events retain their
        # identity in replay workspaces. Arbitrary receipt IDs remain scoped to
        # their research so two providers may both use e.g. "request-1".
        shared = event_id.startswith(("codex:", "mcp:", "missing:", "audit:")) and "unreported:" not in event_id
        key = ("trace" if shared else r["research_id"], event_id)
        if key in unique:
            old = unique[key]
            duplicates += 1
            if shared and old["research_id"] != r["research_id"]:
                fields = ("kind", "tokens", "cost", "currency", "canonical_model", "server", "tool")
                if any(old.get(k) != r.get(k) for k in fields):
                    old.update(cost=None, token_costs={}, warnings=[*old.get("warnings", []), "duplicate_event_conflict"])
                old["also_in_researches"] = sorted(set(old.get("also_in_researches", [])) | {r["research_id"]})
                continue
            left = {k: v for k, v in old.items() if k not in ("source", "line")}
            right = {k: v for k, v in r.items() if k not in ("source", "line")}
            if left != right:
                raise ValueError("同一用量事件内容冲突: " + r["event_id"])
        unique[key] = r
    rows = list(unique.values())
    result = {"summary": total(rows), "duplicates_ignored": duplicates}
    for name, key in (("researches", "research_id"), ("sessions", "session_id"), ("tasks", "task_id"), ("models", "model")):
        groups = defaultdict(list)
        for r in rows:
            groups[r.get(key) or "(unknown)"].append(r)
        result[name] = [{"id": group, **total(items)} for group, items in sorted(groups.items())]
    return {**result, "records": rows}
