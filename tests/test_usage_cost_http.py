"""HTTP acceptance for usage ingestion, tariff edits, and research launch wiring.

All providers/processes are isolated; these tests never start a paid model run.
"""
from copy import deepcopy
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from server.core.usage_cost import PriceBook
from server.core.usage_sources import BillingReader, atomic_json, initialize_billing, research_id
from tools import console_server


@pytest.fixture
def billing_http(tmp_path):
    prices = tmp_path / "prices.json"
    atomic_json(prices, PriceBook.load().config)
    spaces = [tmp_path / "research-1", tmp_path / "research-2"]
    for space in spaces:
        initialize_billing(space, prices, "round-http")
    by_id = {research_id(p): str(p) for p in spaces}
    ws = SimpleNamespace(billing=BillingReader(tmp_path / "cache.sqlite3", prices),
        candidate_paths=lambda: list(by_id.values()), find=by_id.get)
    server = ThreadingHTTPServer(("127.0.0.1", 0), console_server.make_handler(ws, {}, str(tmp_path), ""))
    worker = Thread(target=server.serve_forever, kwargs={"poll_interval": .02}, daemon=True)
    worker.start()

    def request(path, body=None):
        req = Request(f"http://127.0.0.1:{server.server_port}{path}",
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json"})
        try:
            response = urlopen(req, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)
    yield request, list(by_id)
    server.shutdown()
    worker.join(timeout=3)
    server.server_close()


def test_http_receipts_three_scopes_price_updates_and_conflicts(billing_http):
    request, ids = billing_http
    receipt = {"event_id": "provider-1", "model": "Luna", "session_id": "session-http",
        "format": "normalized", "usage": {"input": 100000, "output": 10000, "cache_read": 20000, "cache_write": 30000},
        "service_tier": "standard", "timestamp": "2026-09-16T00:30:00Z"}
    endpoint = f"/api/workspaces/{ids[0]}/usage"
    assert request(endpoint, receipt)[1]["recorded"] is True
    assert request(endpoint, receipt)[1]["duplicate"] is True
    assert request(endpoint, {**receipt, "usage": {**receipt["usage"], "output": 1}})[0] == 400
    assert request(endpoint, {**receipt, "usage_mode": "cumulative"})[0] == 400
    assert request(endpoint, [receipt])[0] == 400
    assert request("/api/workspaces/absent/usage", receipt)[0] == 404
    assert request(f"/api/workspaces/{ids[1]}/usage", {**receipt, "event_id": "provider-2", "session_id": "second-session"})[0] == 200
    status, report = request("/api/billing/summary?task_id=round-http")
    assert status == 200 and "records" not in report
    assert len(report["researches"]) == len(report["sessions"]) == 2
    assert len(report["tasks"]) == 1
    assert report["summary"]["currencies"]["USD"]["total"] == "0.0798"
    assert request("/api/billing/summary?session_id=session-http")[1]["summary"]["currencies"]["USD"]["total"] == "0.0399"
    status, current = request("/api/billing/prices")
    config = deepcopy(current["config"])
    config["models"]["gpt-5.6-luna"]["rates"]["input"] = "30"
    updated = {"config": config, "expected_revision": current["revision"]}
    assert request("/api/billing/prices", updated)[0] == 200
    assert request("/api/billing/prices", updated)[0] == 400
    assert request("/api/billing/prices", {**updated, "config": []})[0] == 400
    # Research price snapshots survive changes to the current table.
    assert request(f"/api/workspaces/{ids[0]}/costs")[1]["summary"]["currencies"]["USD"]["total"] == "0.0399"


def test_console_launch_freezes_tariff_and_propagates_task_id(tmp_path, monkeypatch):
    prices = tmp_path / "configs/model_prices.json"
    atomic_json(prices, PriceBook.load().config)
    monkeypatch.setenv("GOAI_PRICE_CONFIG", str(prices))
    monkeypatch.setattr(console_server, "resolve_codex_path", lambda: "/test/bin/codex")
    captured = {}

    class FakeProcess:
        pid = 987654
        def __init__(self, command, **kwargs):
            captured.update(command=command, **kwargs)
        def wait(self):
            return 0

    monkeypatch.setattr(console_server.subprocess, "Popen", FakeProcess)
    ws = console_server.Workspaces(str(tmp_path), str(tmp_path / "runs"), [])
    result = ws.launch("test research", "public", "gpt-5.6-luna", "high", "/test/codex", {}, billing_task_id="round-A")
    assert captured["env"]["GOAI_BILLING_TASK_ID"] == "round-A"
    assert captured["env"]["GOAI_MODEL"] == "gpt-5.6-luna"
    context = json.loads((Path(result["path"]) / "state/billing_context.json").read_text())
    assert context["task_id"] == "round-A"
    assert context["price_revision"] == PriceBook.load(prices).revision
    assert captured["command"][:2] == ["bash", "scripts/reproduce_core.sh"]
