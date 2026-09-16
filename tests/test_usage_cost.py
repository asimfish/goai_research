from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

from server.core.usage_cost import BUCKETS, PriceBook, normalize_usage, summarize
from server.core.usage_sources import BillingReader, append_usage, atomic_json, initialize_billing


def event(**values):
    return {"kind": "usage", "event_id": "request-1", "research_id": "research-1", "task_id": "round-1",
            "session_id": "session-1", "model": "Luna", "format": "normalized", "service_tier": "standard",
            "timestamp": "2026-09-16T00:30:00+00:00",
            "usage": {"input": 100000, "output": 10000, "cache_read": 20000, "cache_write": 30000}, **values}


@pytest.mark.parametrize("model,expected", [("GPT 5.6", "0.758"), ("gpt-5.6", "0.758"),
    ("Luna", "0.0399"), ("Astra", "1.895"), ("DeepSeek", "0.02106")])
def test_four_buckets_known_prices(model, expected):
    priced = PriceBook.load().price(event(model=model))
    assert Decimal(priced["cost"]) == Decimal(expected)
    assert sum(Decimal(v) for v in priced["token_costs"].values()) == Decimal(expected)


def test_inclusive_cache_and_reasoning_are_not_double_billed():
    usage = {"input_tokens": 150000, "cached_input_tokens": 20000, "cache_write_input_tokens": 30000,
             "output_tokens": 10000, "reasoning_output_tokens": 7000}
    normalized = normalize_usage(usage)
    assert normalized["tokens"] == event()["usage"]
    assert PriceBook.load().price(event(usage=usage, format="auto"))["cost"] == "0.0399"


def test_responses_chat_and_anthropic_schemas():
    expected = {"input": 600, "output": 25, "cache_read": 300, "cache_write": 100}
    variants = [
        {"input_tokens": 1000, "output_tokens": 25, "input_tokens_details": {"cached_tokens": 300, "cache_write_tokens": 100}},
        {"prompt_tokens": 1000, "completion_tokens": 25, "prompt_tokens_details": {"cached_tokens": 300, "cache_write_tokens": 100}},
        {"input_tokens": 600, "output_tokens": 25, "cache_read_input_tokens": 300, "cache_creation_input_tokens": 100},
    ]
    assert all(normalize_usage(u)["tokens"] == expected for u in variants)


def test_deepseek_miss_is_input_not_a_second_write():
    usage = {"prompt_tokens": 1000, "completion_tokens": 20, "prompt_cache_hit_tokens": 800, "prompt_cache_miss_tokens": 200}
    assert normalize_usage(usage)["tokens"] == {"input": 200, "output": 20, "cache_read": 800, "cache_write": 0}
    assert normalize_usage(usage)["warnings"] == []
    with pytest.raises(ValueError):
        normalize_usage({**usage, "prompt_cache_miss_tokens": 1000})


@pytest.mark.parametrize("bad", [-1, True, False, 1.5, "10", None])
def test_bad_token_counts_are_rejected(bad):
    with pytest.raises(ValueError):
        normalize_usage({"input_tokens": 1000, "output_tokens": bad})


def test_bad_cache_is_not_clamped_or_made_free():
    with pytest.raises(ValueError):
        normalize_usage({"input_tokens": 10, "output_tokens": 1, "cached_input_tokens": 11})
    with pytest.raises(ValueError):
        normalize_usage({"input_tokens": 10, "output_tokens": 1, "cached_input_tokens": False})


def test_long_context_is_per_request_not_session_sum():
    book = PriceBook.load()
    usage = {"input_tokens": 1000000, "cached_input_tokens": 400000, "cache_write_input_tokens": 100000, "output_tokens": 10000}
    request = book.price(event(format="auto", usage=usage))
    session = book.price(event(format="auto", usage=usage, usage_scope="turn"))
    assert request["cost"] == "0.284"
    assert session["cost"] == "0.145"
    assert "aggregate_context_unknown_standard_context_rates" in session["warnings"]
    assert book.price(event(request_input_tokens=272000))["long_context"] is False
    assert book.price(event(request_input_tokens=272001))["long_context"] is True


@pytest.mark.parametrize("tier,factor", [("standard", 1), ("priority", 2), ("fast", 2), ("batch", .5), ("flex", .5)])
def test_service_tiers(tier, factor):
    assert Decimal(PriceBook.load().price(event(service_tier=tier))["cost"]) == Decimal("0.0399") * Decimal(str(factor))


@pytest.mark.parametrize("at,multiplier", [("2026-09-16T00:59:59Z", 1), ("2026-09-16T01:00:00Z", 2),
    ("2026-09-16T04:00:00Z", 1), ("2026-09-16T06:00:00Z", 2), ("2026-09-16T10:00:00Z", 1),
    ("2026-09-19T02:00:00Z", 1)])
def test_peak_offpeak_boundaries(at, multiplier):
    cost = PriceBook.load().price(event(model="DeepSeek", timestamp=at))["cost"]
    assert Decimal(cost) == Decimal("0.02106") * multiplier


def test_missing_models_usage_and_mixed_currencies_are_visible():
    book = PriceBook.load()
    a = book.price(event())
    b = book.price(event(model="unknown-model", event_id="unknown"))
    c = book.price(event(kind="missing", event_id="missing", reason="usage_not_reported"))
    eur = deepcopy(book.config); eur["currency"] = "EUR"
    d = PriceBook(eur).price(event(event_id="eur"))
    result = summarize([a, b, c, d])
    assert result["summary"]["status"] == "partial"
    assert result["summary"]["unpriced_records"] == 2
    assert result["summary"]["currencies"]["USD"]["total"] == "0.0399"
    assert result["summary"]["currencies"]["EUR"]["total"] == "0.0399"


def test_three_dimensions_and_copied_trace_do_not_double_charge():
    book = PriceBook.load()
    a = book.price(event(source="original"))
    b = book.price(event(event_id="b", research_id="research-2", session_id="session-2"))
    report = summarize([a, {**a, "source": "copy"}, b])
    assert report["summary"]["currencies"]["USD"]["total"] == "0.0798"
    assert len(report["researches"]) == len(report["sessions"]) == 2
    assert len(report["tasks"]) == 1
    assert report["tasks"][0]["currencies"]["USD"]["total"] == "0.0798"


def test_replay_workspace_cannot_double_count_the_same_codex_turn():
    book = PriceBook.load()
    a = book.price(event(event_id="codex:thread-123:turn:1:usage-hash", source="original"))
    replay = {**a, "research_id": "replay", "task_id": "replay-round", "source": "replay"}
    report = summarize([replay, a])
    assert report["summary"]["currencies"]["USD"]["total"] == "0.0399"
    assert report["duplicates_ignored"] == 1
    assert report["records"][0]["also_in_researches"] == ["replay"]
    conflict = summarize([a, {**replay, "cost": "99"}])
    assert conflict["summary"]["unpriced_records"] == 1


def write_lines(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def test_real_trace_shape_failed_session_cache_refresh_and_audit_dedup(tmp_path):
    ws = tmp_path / "research"
    trace = ws / "state/orchestrator/orchestrator.jsonl"
    atomic_json(ws / "launcher.json", {"model": "gpt-5.6-luna"})
    frames = [{"type": "thread.started", "thread_id": "session-123"}, {"type": "turn.started"},
        {"type": "item.completed", "item": {"type": "mcp_tool_call", "id": "call1", "server": "goai_catalog", "tool": "lookup", "status": "completed"}}]
    write_lines(trace, frames)
    write_lines(ws / "state/tool_calls.jsonl", [{"run_id": "orchestrator/orchestrator", "tool": "lookup", "duration_ms": 125, "timestamp": "2026-09-16T01:00:00Z"}])
    reader = BillingReader(tmp_path / "cache.sqlite3")
    report = reader.report([ws])
    assert report["summary"]["missing_usage"] == 1
    assert report["summary"]["mcp_calls"] == 1
    assert report["summary"]["mcp_duration_ms"] == 125
    frames.append({"type": "turn.completed", "usage": {"input_tokens": 2276926, "cached_input_tokens": 2121216, "cache_write_input_tokens": 0, "output_tokens": 8744}})
    write_lines(trace, frames)
    report = reader.report([ws])
    assert report["summary"]["missing_usage"] == 0
    assert report["summary"]["tokens"] == {"input": 155710, "output": 8744, "cache_read": 2121216, "cache_write": 0}
    assert report["summary"]["currencies"]["USD"]["total"] == "0.08405912"
    assert reader.report([ws])["summary"] == report["summary"]


def test_request_receipts_idempotent_concurrent_and_price_snapshot(tmp_path):
    ws = tmp_path / "research"
    prices = tmp_path / "prices.json"
    atomic_json(prices, PriceBook.load().config)
    initialize_billing(ws, prices, "round-A")
    receipt = {k: v for k, v in event().items() if k not in ("kind", "research_id", "task_id")}
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: append_usage(ws, receipt), range(8)))
    assert sum(r["recorded"] for r in results) == 1
    with pytest.raises(ValueError):
        append_usage(ws, {**receipt, "usage": {**receipt["usage"], "input": 1}})
    reader = BillingReader(tmp_path / "cache.sqlite3", prices)
    config = deepcopy(PriceBook.load(prices).config); config["models"]["gpt-5.6-luna"]["rates"]["input"] = "20"
    before = PriceBook.load(prices).revision
    reader.update_prices(config, before)
    with pytest.raises(ValueError):
        reader.update_prices(config, before)
    report = reader.report([ws])
    assert report["tasks"][0]["id"] == "round-A"
    assert report["summary"]["currencies"]["USD"]["total"] == "0.0399"


def test_mcp_model_usage_is_additional_but_local_service_is_free(tmp_path, monkeypatch):
    from server.core.audit import record_tool_call
    ws = tmp_path / "research"
    monkeypatch.setenv("GOAI_WORKSPACE", str(ws))
    monkeypatch.setenv("GOAI_RUN_ID", "round/worker")
    response = {"billing_usage": {"event_id": "provider-request", "model": "Luna", "usage": event()["usage"],
                                  "format": "normalized", "service_tier": "standard"}}
    record_tool_call("model_in_tool", {}, response, duration_ms=250)
    report = BillingReader(tmp_path / "cache.sqlite3").report([ws])
    assert report["summary"]["mcp_calls"] == 1
    assert report["summary"]["usage_records"] == 1
    assert report["summary"]["currencies"]["USD"]["total"] == "0.0399"


def test_paid_tool_tariff_and_missing_duration():
    config = deepcopy(PriceBook.load().config)
    config["tools"] = {"paid.search": {"per_call": "0.01", "per_second": "0.001"}}
    book = PriceBook(config)
    call = event(kind="tool", server="paid", tool="search", duration_ms=2500)
    assert book.price(call)["cost"] == "0.0125"
    call.pop("duration_ms")
    assert book.price(call)["cost"] is None


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-1", True])
def test_bad_price_config(bad):
    config = deepcopy(PriceBook.load().config)
    config["models"]["gpt-5.6-luna"]["rates"]["input"] = bad
    with pytest.raises(ValueError):
        PriceBook(config)


def test_internal_model_is_in_host_session_and_round(tmp_path, monkeypatch):
    from server.core.audit import record_tool_call
    ws = tmp_path / "research"
    monkeypatch.setenv("GOAI_WORKSPACE", str(ws))
    monkeypatch.setenv("GOAI_RUN_ID", "execution-1")
    monkeypatch.setenv("GOAI_BILLING_TASK_ID", "round-A")
    monkeypatch.delenv("GOAI_SESSION_ID", raising=False)
    atomic_json(ws / "model_runs/run/invocation.json", {"model": "Luna", "run_id": "execution-1", "billing_task_id": "round-A"})
    write_lines(ws / "model_runs/run/events.jsonl", [
        {"type": "thread.started", "thread_id": "host-session"}, {"type": "turn.started"},
        {"type": "turn.completed", "usage": {"input_tokens": 150000, "cached_input_tokens": 20000,
            "cache_write_input_tokens": 30000, "output_tokens": 10000}}])
    record_tool_call("nested_model", {}, {"billing_usage": {"event_id": "nested-request", "model": "Luna",
        "usage": event()["usage"], "format": "normalized", "service_tier": "standard"}}, duration_ms=25)
    report = BillingReader(tmp_path / "cache.sqlite3").report([ws])
    assert len(report["sessions"]) == len(report["tasks"]) == 1
    assert report["sessions"][0]["id"] == "host-session"
    assert report["tasks"][0]["id"] == "round-A"
    assert report["summary"]["currencies"]["USD"]["total"] == "0.0798"


def test_invalid_mcp_metering_remains_visible(tmp_path, monkeypatch):
    from server.core.audit import record_tool_call
    ws = tmp_path / "research"
    monkeypatch.setenv("GOAI_WORKSPACE", str(ws))
    monkeypatch.setenv("GOAI_RUN_ID", "worker-1")
    record_tool_call("nested_model", {}, {"billing_usage": {"model": "Luna", "usage": {"input_tokens": -1}}}, duration_ms=25)
    report = BillingReader(tmp_path / "cache.sqlite3").report([ws])
    assert report["summary"]["missing_usage"] == 1
    assert report["summary"]["status"] == "partial"
    assert report["summary"]["warnings"]["tool_usage_recording_failed"] == 1


def test_deepseek_import_without_request_time_does_not_guess_import_time(tmp_path):
    receipt = {k: v for k, v in event(model="DeepSeek").items() if k not in ("kind", "research_id", "timestamp")}
    append_usage(tmp_path / "research", receipt)
    report = BillingReader(tmp_path / "cache.sqlite3").report([tmp_path / "research"])
    assert report["summary"]["unpriced_records"] == 1
    assert report["summary"]["warnings"]["peak_time_unknown"] == 1


def test_standalone_parallel_run_keeps_explicit_round(tmp_path):
    ws = tmp_path / "research"
    atomic_json(ws / "state/parallel/batch/RUN_INFO.json", {"model": "Luna", "billing_task_id": "followup-round"})
    write_lines(ws / "state/parallel/batch/worker.jsonl", [{"type": "thread.started", "thread_id": "followup-session"},
        {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 25, "cached_input_tokens": 20, "cache_write_input_tokens": 0}}])
    report = BillingReader(tmp_path / "cache.sqlite3").report([ws], task_id="followup-round")
    assert report["summary"]["usage_records"] == 1
    assert report["tasks"][0]["id"] == "followup-round"


@pytest.mark.parametrize("usage,fmt", [({"input": 5}, "normalized"),
    ({"input_tokens": 1, "output_tokens": 1, "input_tokens_details": "bad"}, "auto"),
    ({"input_tokens": 1, "output_tokens": 1}, "unknown")])
def test_bad_usage_schema(usage, fmt):
    with pytest.raises(ValueError):
        normalize_usage(usage, fmt)
