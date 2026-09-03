#!/usr/bin/env bash
# One-command smoke test for reviewers (no LLM, no network, no private data needed).
#
#   bash scripts/smoke_test.sh            # installs .venv if missing, then runs all checks
#   bash scripts/smoke_test.sh --with-retro   # additionally loads the two-stage precursor
#                                             # model and predicts one reference target (CPU)
#
# Expected result: every step prints OK and the script exits 0. Details of what a
# healthy run looks like are listed in docs/competition/SUBMISSION.md §7.
set -euo pipefail
cd "$(dirname "$0")/.."
WITH_RETRO=0
[[ "${1:-}" == "--with-retro" ]] && WITH_RETRO=1

step() { printf '\n==> %s\n' "$*"; }
ok()   { printf 'OK  %s\n' "$*"; }

step "1/6 environment (.venv)"
if [[ ! -x .venv/bin/python ]]; then
  if [[ $WITH_RETRO == 1 ]]; then bash install.sh --retro; else bash install.sh; fi
fi
.venv/bin/python -c 'import sys; assert sys.version_info >= (3,10), sys.version' && ok "python $(.venv/bin/python -c 'import platform;print(platform.python_version())')"

step "2/6 MCP servers import (litsearch / refcheck / figure / retro)"
tools/check.sh --servers >/dev/null && ok "4 MCP servers importable"

step "3/6 offline unit tests (no network)"
.venv/bin/python -m pytest tests/ -q -x --no-header -p no:cacheprovider 2>&1 | tail -3
ok "offline tests"

step "4/6 public corpus package (cited full texts) served through the MCP corpus tools"
export GOAI_LOCAL_CORPUS_ROOTS="$PWD/submission/02_研究数据与证据包/corpus_release"
unset GOAI_LOCAL_CORPUS_EXPECTED_INDEX GOAI_LOCAL_CORPUS_SHARD_ROOT
tools/check.sh --corpus >/dev/null && ok "corpus package validates"
.venv/bin/python - <<'PY'
from server.core import parquet_corpus as pc
from server.core.local_corpus import configured_roots
roots = configured_roots(None); files = pc.discover_files(roots)
r = pc.lookup_doi("10.1021/acs.cgd.6b01448", roots=roots, files=files, start_line=1, end_line=2)
assert r.get("found"), r
print("OK  lookup_local_doi ->", r["title"][:70])
PY

step "5/6 claim -> evidence chain is complete for the formal report"
.venv/bin/python - <<'PY'
import json
s = json.load(open("submission/02_研究数据与证据包/claim_evidence_summary.json"))
assert s["bib_entries_uncited"] == [], s["bib_entries_uncited"]
assert s["refcheck_pass_rate"] == 100.0, s["refcheck_pass_rate"]
print(f"OK  {s['claims']} claims / {s['citation_calls']} citation calls / {s['distinct_keys_cited']} verified keys")
PY

step "6/6 figure pipeline: figspec -> svg + drawio (deterministic renderer)"
.venv/bin/python - <<'PY'
import json
from server.core import figspec, render_svg, render_drawio
spec = figspec.loads(open("examples/pipeline.figspec.json", encoding="utf-8").read())
errors = figspec.validate(spec)
assert not errors, errors
svg = render_svg.render(spec)
drawio = render_drawio.render(spec)
assert svg.lstrip().startswith("<svg") and "<mxGraphModel" in drawio
print(f"OK  figspec -> svg ({len(svg)} bytes) + drawio ({len(drawio)} bytes)")
PY

if [[ $WITH_RETRO == 1 ]]; then
  step "optional: two-stage precursor model dry run (load both checkpoints, predict Li7La3Zr2O12 on CPU)"
  PY=.venv-retro/bin/python; [[ -x $PY ]] || PY=.venv/bin/python
  $PY tools/retro_dry_run.py Li7La3Zr2O12 --device cpu | tail -9
  ok "retro model loads and predicts (reference metrics: vendor/two_stage_retro/checkpoints/*_summary.json)"
fi

printf '\nSMOKE TEST PASSED\n'
