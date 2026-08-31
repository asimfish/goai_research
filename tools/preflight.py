#!/usr/bin/env python3
"""Fail-closed environment, corpus, and local-model preflight checks."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _check_environment() -> dict[str, Any]:
    expected = (ROOT / ".venv").resolve()
    actual = Path(sys.prefix).resolve()
    dependencies = {
        name: importlib.util.find_spec(name) is not None
        for name in ("mcp", "httpx", "duckdb")
    }
    return {
        "ok": actual == expected and all(dependencies.values()),
        # Keep the invoked venv path visible; resolving its symlink would display
        # the base interpreter and make a healthy venv look like system Python.
        "python": str(Path(sys.executable).absolute()),
        "prefix": str(actual),
        "expected_prefix": str(expected),
        "using_repository_venv": actual == expected,
        "dependencies": dependencies,
        "hint": None if actual == expected else (
            "Run this check with .venv/bin/python or tools/check.sh; do not use "
            "the system Python for repository validation."
        ),
    }


def _check_servers() -> dict[str, Any]:
    modules: dict[str, dict[str, Any]] = {}
    for name in ("litsearch", "refcheck", "figure", "retro"):
        path = ROOT / "server" / f"{name}_server.py"
        try:
            spec = importlib.util.spec_from_file_location(f"goai_preflight_{name}", path)
            if spec is None or spec.loader is None:
                raise RuntimeError("cannot construct import spec")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001 - boundary must return diagnostics
            modules[name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        else:
            modules[name] = {"ok": True, "path": str(path)}
    return {"ok": all(item["ok"] for item in modules.values()), "modules": modules}


def _check_corpus() -> dict[str, Any]:
    from server.core.local_corpus import corpus_status

    return corpus_status()


def _check_retro() -> dict[str, Any]:
    from server.core.inorganic_retro import status

    result = status()
    return {"ok": bool(result.get("available")), **result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--servers", action="store_true", help="import all MCP servers")
    parser.add_argument("--corpus", action="store_true", help="validate configured corpus package")
    parser.add_argument("--retro", action="store_true", help="validate two-stage model dependencies/assets")
    args = parser.parse_args()

    checks: dict[str, dict[str, Any]] = {"environment": _check_environment()}
    if args.servers or not (args.corpus or args.retro):
        checks["servers"] = _check_servers()
    if args.corpus:
        checks["corpus"] = _check_corpus()
    if args.retro:
        checks["retro"] = _check_retro()
    result = {"ok": all(check.get("ok", False) for check in checks.values()),
              "checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
