import gzip
import json

from tools.export_submission_bundle import (
    normalize_jsonl,
    refresh_export_metadata,
    sanitize_export_tree,
    scrub_text,
    validate_export_tree,
)


def test_scrub_text_covers_bare_gateway_token_and_private_paths():
    token = "tk-" + "a" * 26 + "-" + "1" * 8
    text = f"daemon --token {token} /home/alice/project /mnt/nas/private/data"

    scrubbed, hits = scrub_text(text)

    assert hits == 3
    assert token not in scrubbed
    assert "/home/alice" not in scrubbed
    assert "/mnt/nas" not in scrubbed
    assert scrubbed == "daemon --token [REDACTED] <HOME> <PRIVATE_MOUNT_PATH>"


def test_normalize_jsonl_preserves_malformed_lines_as_json_records():
    normalized, wrapped, blank = normalize_jsonl(
        '{"type":"ok"}\nplain diagnostic\n\n{"partial":\n'
    )

    records = [json.loads(line) for line in normalized.splitlines()]
    assert wrapped == 2
    assert blank == 1
    assert records[0] == {"type": "ok"}
    assert records[1]["type"] == "unparsed_raw"
    assert records[1]["raw"] == "plain diagnostic"
    assert records[2]["raw"] == '{"partial":'


def test_sanitize_and_validate_tree_including_gzip_jsonl(tmp_path):
    plain = tmp_path / "events.jsonl"
    plain.write_text('{"ok":true}\nnot json\n', encoding="utf-8")
    compressed = tmp_path / "rollout.jsonl.gz"
    token = "tk-" + "a" * 26 + "-" + "1" * 8
    with gzip.open(compressed, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps({"command": f"--token {token}",
                             "cwd": "/home/alice/project"}) + "\n")

    log = []
    stats = sanitize_export_tree(tmp_path, log)
    validation = validate_export_tree(tmp_path)

    assert stats["redactions"] == 2
    assert stats["jsonl_wrapped"] == 1
    assert validation["jsonl_files"] == 2
    assert validation["jsonl_records"] == 3
    with gzip.open(compressed, "rt", encoding="utf-8") as fh:
        record = json.loads(fh.readline())
    assert record["command"] == "--token [REDACTED]"
    assert record["cwd"] == "<HOME>"


def test_refresh_export_metadata_updates_development_trace_hash(tmp_path):
    trace_dir = tmp_path / "traces" / "development"
    trace_dir.mkdir(parents=True)
    trace = trace_dir / "conversation.jsonl.gz"
    with gzip.open(trace, "wt", encoding="utf-8") as fh:
        fh.write('{"ok":true}\n')
    info = trace_dir / "trace_info.json"
    info.write_text(json.dumps({"file": trace.name, "sha256": "stale"}),
                    encoding="utf-8")

    stats = refresh_export_metadata(tmp_path)
    refreshed = json.loads(info.read_text(encoding="utf-8"))

    assert stats["development_trace_hashes"] == 1
    assert refreshed["sha256"] != "stale"
    assert refreshed["post_export_sanitized"] is True


def test_refresh_export_metadata_repairs_trace_paths_and_sizes(tmp_path):
    run = tmp_path / "run"
    trace = run / "traces" / "runtime" / "parallel" / "batch" / "task.jsonl"
    trace.parent.mkdir(parents=True)
    trace.write_text('{"ok":true}\n', encoding="utf-8")
    manifest = run / "RUN_MANIFEST.json"
    manifest.write_text(json.dumps({
        "parallel_batches": [{"tasks": [{
            "trace": "state/parallel/batch/task.jsonl", "bytes": 1,
        }]}],
    }), encoding="utf-8")

    stats = refresh_export_metadata(tmp_path)
    task = json.loads(manifest.read_text(encoding="utf-8"))["parallel_batches"][0]["tasks"][0]

    assert stats["run_trace_sizes"] == 1
    assert task["trace"] == "traces/runtime/parallel/batch/task.jsonl"
    assert task["bytes"] == trace.stat().st_size
