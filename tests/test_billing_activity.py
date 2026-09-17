import json
import shutil

from server.core.usage_sources import BillingReader, append_usage, atomic_json


def trace(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))


USAGE = {"type": "turn.completed", "usage": {"input_tokens": 1000,
    "cached_input_tokens": 200, "cache_write_input_tokens": 0, "output_tokens": 50}}


def test_activity_counts_completed_replies_and_deduplicates_copies(tmp_path):
    ws = tmp_path / "a-original"
    atomic_json(ws / "launcher.json", {"model": "gpt-5.6-luna"})
    reply = {"type": "item.completed", "item": {"type": "agent_message", "id": "item_1", "text": "PRIVATE_REPLY_SENTINEL"}}
    rows = [{"type": "thread.started", "thread_id": "thread-1"}, {"type": "turn.started"},
        {"type": "item.started", "item": {"type": "agent_message", "id": "item_1"}},
        {"type": "item.updated", "item": {"type": "agent_message", "id": "item_1"}},
        {"type": "item.completed", "item": {"type": "reasoning", "id": "reasoning-1"}},
        reply, reply, USAGE]
    trace(ws / "state/orchestrator/first.jsonl", rows)
    # A resumed invocation can reuse the item ID; it is still a separate reply.
    trace(ws / "state/orchestrator/resumed.jsonl", [rows[0], rows[1], reply, {**USAGE, "usage": {**USAGE["usage"], "output_tokens": 51}}])
    reader = BillingReader(tmp_path / "cache.sqlite3")
    original = reader.report([ws])
    assert original["summary"]["conversation_count"] == 1
    assert original["summary"]["reply_count"] == 2
    assert original["summary"]["turn_count"] == 2
    assert original["summary"]["usage_records"] == 2
    copy = tmp_path / "z-copy"
    shutil.copytree(ws, copy)
    copied = reader.report([ws, copy], session_id="thread-1")
    assert copied["summary"] == original["summary"]
    for section in ("researches", "sessions", "tasks", "models"):
        assert copied[section][0]["reply_count"] == 2
    assert reader.report([ws], session_id="missing")["summary"]["reply_count"] is None
    import sqlite3
    with sqlite3.connect(reader.cache) as con:
        assert all("PRIVATE_REPLY_SENTINEL" not in payload for (payload,) in con.execute("SELECT payload FROM traces"))


def test_failed_conversation_activity_and_cache_growth(tmp_path):
    ws = tmp_path / "research"
    atomic_json(ws / "launcher.json", {"model": "gpt-5.6-luna"})
    path = ws / "state/orchestrator/run.jsonl"
    rows = [{"type": "thread.started", "thread_id": "failed-thread"}, {"type": "turn.started"},
        {"type": "item.completed", "item": {"type": "agent_message", "id": "item_1"}}]
    trace(path, rows)
    reader = BillingReader(tmp_path / "cache.sqlite3")
    first = reader.report([ws])["summary"]
    assert (first["conversation_count"], first["reply_count"], first["missing_usage"]) == (1, 1, 1)
    trace(path, rows + [{"type": "item.completed", "item": {"type": "agent_message", "id": "item_2"}}, USAGE])
    second = reader.report([ws])["summary"]
    assert (second["conversation_count"], second["reply_count"], second["missing_usage"]) == (1, 2, 0)
    assert second["usage_records"] == 1
    assert second["tokens"]["output"] == 50


def test_usage_only_receipt_does_not_invent_conversation_or_replies(tmp_path):
    ws = tmp_path / "research"
    append_usage(ws, {"event_id": "provider-1", "session_id": "receipt-only", "model": "Luna",
        "format": "normalized", "usage": {"input": 1000, "output": 100, "cache_read": 0, "cache_write": 0}})
    summary = BillingReader(tmp_path / "cache.sqlite3").report([ws])["summary"]
    assert summary["usage_records"] == 1
    assert summary["conversation_count"] is None
    assert summary["reply_count"] is None
