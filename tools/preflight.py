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


# 模板 templates/survey_main*.tex 实际依赖的宏包；缺任一即不能按模板编译
TEX_REQUIRED_FILES = {
    "newtxtext.sty": "newtx", "newtxmath.sty": "newtx", "titlesec.sty": "titlesec",
    "enumitem.sty": "enumitem", "fancyhdr.sty": "fancyhdr", "booktabs.sty": "booktabs",
    "caption.sty": "caption", "natbib.sty": "natbib", "microtype.sty": "microtype",
    "hyperref.sty": "hyperref", "geometry.sty": "geometry", "textcomp.sty": "textcomp",
}
TEX_CJK_FILES = {"ctexart.cls": "ctex", "FandolSong-Regular.otf": "fandol"}


def _check_tex() -> dict[str, Any]:
    """TeX 工具链预检：交付 PDF 只能由 TeX 从模板编译，缺工具链必须 fail-closed，
    禁止用 groff/HTML→Chrome 等回退渲染器冒充（实跑中出现过，账本却记了 PASS）。"""
    import shutil
    import subprocess

    engines = {name: shutil.which(name) for name in ("xelatex", "pdflatex", "latexmk", "bibtex")}
    kpsewhich = shutil.which("kpsewhich")

    def found(fname: str) -> bool:
        if not kpsewhich:
            return False
        try:
            out = subprocess.run([kpsewhich, fname], capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return out.returncode == 0 and bool(out.stdout.strip())

    packages = {f: found(f) for f in TEX_REQUIRED_FILES}
    cjk = {f: found(f) for f in TEX_CJK_FILES}
    missing_pkgs = sorted({TEX_REQUIRED_FILES[f] for f, ok in packages.items() if not ok})
    missing_cjk = sorted({TEX_CJK_FILES[f] for f, ok in cjk.items() if not ok})
    ok_en = bool(engines["xelatex"] or engines["pdflatex"]) and bool(engines["bibtex"]) and not missing_pkgs
    ok_zh = bool(engines["xelatex"]) and ok_en and not missing_cjk
    hint = None
    if not ok_en:
        hint = ("TeX 工具链不完整：draft_complete 不得 PASS，交付 main.tex+bib+figures 并在终报"
                "写明『PDF 未编译』；禁止用 groff/HTML→Chrome 渲染 PDF 冒充。安装：TeX Live 完整版，"
                "或用户级 install-tl 后 `tlmgr install " + " ".join(missing_pkgs or ["newtx"]) +
                "`，或 tectonic（单二进制、自动拉包）。")
    elif not ok_zh:
        hint = ("英文模板可编译；中文模板还缺 " + ", ".join(missing_cjk) +
                "（`tlmgr install ctex fandol`），且必须用 xelatex。")
    return {"ok": ok_en, "english_template_ok": ok_en, "chinese_template_ok": ok_zh,
            "engines": engines, "kpsewhich": kpsewhich, "packages": packages,
            "cjk": cjk, "missing_packages": missing_pkgs, "missing_cjk": missing_cjk,
            "hint": hint}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--servers", action="store_true", help="import all MCP servers")
    parser.add_argument("--corpus", action="store_true", help="validate configured corpus package")
    parser.add_argument("--retro", action="store_true", help="validate two-stage model dependencies/assets")
    parser.add_argument("--tex", action="store_true",
                        help="validate the TeX toolchain the survey templates need (fail-closed for PDF delivery)")
    args = parser.parse_args()

    checks: dict[str, dict[str, Any]] = {"environment": _check_environment()}
    if args.servers or not (args.corpus or args.retro or args.tex):
        checks["servers"] = _check_servers()
    if args.corpus:
        checks["corpus"] = _check_corpus()
    if args.retro:
        checks["retro"] = _check_retro()
    if args.tex:
        checks["tex"] = _check_tex()
    result = {"ok": all(check.get("ok", False) for check in checks.values()),
              "checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
