#!/usr/bin/env bash
# Reproduce the core result: ONE research topic line in -> verified survey PDF + evidence out.
#
# This is the exact launch used for the formal case (submission/goai_final/run):
# a non-interactive Codex CLI run that receives only the topic string, reads the
# repository skills (goai-orchestrator etc.), and drives the ledger state machine
# (scoping -> lit_search/style_bank -> ref_gate -> taxonomy -> figures/writing/ideas
# -> review -> final). Sub-agents are fanned out with tools/parallel_run.sh and every
# Codex event stream is kept under <workspace>/state/parallel/.
#
# Requirements
#   * Codex CLI >= 0.146 (`npm i -g @openai/codex`) with a signed-in account
#   * this repository installed:  bash install.sh --retro   (creates .venv, MCP config)
#   * network access to Crossref / OpenAlex / arXiv / Semantic Scholar (free, no key)
#   * a TeX engine for the final PDF: xelatex+ctex (Chinese) or tectonic
#   * cost/compute: the formal run used ~70.8M input / 0.57M output tokens across
#     40 sub-agent tasks plus the orchestrator (see metrics/agent_trace_stats_byzso.md);
#     the local two-stage precursor model runs on CPU in seconds per query.
#
# Usage
#   bash scripts/reproduce_core.sh                       # formal topic, fresh workspace
#   bash scripts/reproduce_core.sh --topic "LLZO 石榴石固态电解质的烧结致密化"
#   GOAI_CORPUS=private bash scripts/reproduce_core.sh   # use your own private corpus env
#
# Model pinning: model and reasoning effort are passed explicitly so the run matches the
# declared configuration (gpt-5.6-sol, reasoning effort xhigh). Override with
# GOAI_MODEL / GOAI_REASONING_EFFORT if your account exposes different model ids.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="$PWD"

TOPIC='调研主题：Ba5Y12Zn[O(SiO4)]8及其结构相近化合物的合成条件'
WORKDIR=""
while (( $# )); do
  case "$1" in
    --topic)   TOPIC="调研主题：${2:?}"; shift 2 ;;
    --workdir) WORKDIR="${2:?}"; shift 2 ;;
    -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

command -v codex >/dev/null || { echo "codex CLI not found; install with: npm i -g @openai/codex" >&2; exit 2; }
[[ -x .venv/bin/python ]] || bash install.sh --retro
RETRO_PY=".venv-retro/bin/python"; [[ -x $RETRO_PY ]] || RETRO_PY=".venv/bin/python"

STAMP="$(date +%Y%m%d_%H%M%S)"
WORKDIR="${WORKDIR:-$REPO/workspace_repro_$STAMP}"
mkdir -p "$WORKDIR"/{library/pdfs,notes,memory,style_bank/{pdfs,exemplar_figures},figures/{svg,drawio,figspec,assets,candidates},drafts/sections,ideas,state/{parallel,review_traces},inputs}
LOGDIR="$WORKDIR/state/orchestrator"; mkdir -p "$LOGDIR"

# --- corpus: public package of the cited full texts by default -----------------------
if [[ "${GOAI_CORPUS:-public}" == "public" ]]; then
  export GOAI_LOCAL_CORPUS_ROOTS="$REPO/submission/goai_final/evidence/corpus_release"
  unset GOAI_LOCAL_CORPUS_EXPECTED_INDEX GOAI_LOCAL_CORPUS_SHARD_ROOT
  echo "corpus: public cited-paper package ($GOAI_LOCAL_CORPUS_ROOTS)"
else
  : "${GOAI_LOCAL_CORPUS_ROOTS:?set GOAI_LOCAL_CORPUS_ROOTS (and index/shard vars) for a private corpus}"
  echo "corpus: private ($GOAI_LOCAL_CORPUS_ROOTS)"
fi
export GOAI_WORKSPACE="$WORKDIR"
export GOAI_INORGANIC_RETRO_ROOT="$REPO/vendor/two_stage_retro"
export GOAI_RETRO_DEVICE="${GOAI_RETRO_DEVICE:-cpu}"
export GOAI_EMAIL="${GOAI_EMAIL:-goai-research@example.com}"

# --- Codex profile: four MCP servers of this checkout + pinned model ------------------
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
PROFILE="goai_repro_$STAMP"
MODEL="${GOAI_MODEL:-gpt-5.6-sol}"
EFFORT="${GOAI_REASONING_EFFORT:-xhigh}"
cat > "$CODEX_HOME/$PROFILE.config.toml" <<TOML
model = "$MODEL"
model_reasoning_effort = "$EFFORT"

[mcp_servers.goai-litsearch]
command = "$REPO/.venv/bin/python"
args = ["$REPO/server/litsearch_server.py"]
default_tools_approval_mode = "approve"
env = { GOAI_EMAIL = "$GOAI_EMAIL", GOAI_WORKSPACE = "$WORKDIR", GOAI_LOCAL_CORPUS_ROOTS = "$GOAI_LOCAL_CORPUS_ROOTS"${GOAI_LOCAL_CORPUS_EXPECTED_INDEX:+, GOAI_LOCAL_CORPUS_EXPECTED_INDEX = "$GOAI_LOCAL_CORPUS_EXPECTED_INDEX", GOAI_LOCAL_CORPUS_SHARD_ROOT = "$GOAI_LOCAL_CORPUS_SHARD_ROOT"} }

[mcp_servers.goai-refcheck]
command = "$REPO/.venv/bin/python"
args = ["$REPO/server/refcheck_server.py"]
default_tools_approval_mode = "approve"
env = { GOAI_EMAIL = "$GOAI_EMAIL", GOAI_WORKSPACE = "$WORKDIR" }

[mcp_servers.goai-figure]
command = "$REPO/.venv/bin/python"
args = ["$REPO/server/figure_server.py"]
default_tools_approval_mode = "approve"
env = { GOAI_WORKSPACE = "$WORKDIR" }

[mcp_servers.goai-retro]
command = "$REPO/$RETRO_PY"
args = ["$REPO/server/retro_server.py"]
default_tools_approval_mode = "approve"
env = { GOAI_WORKSPACE = "$WORKDIR", GOAI_INORGANIC_RETRO_ROOT = "$GOAI_INORGANIC_RETRO_ROOT", GOAI_RETRO_DEVICE = "$GOAI_RETRO_DEVICE" }
TOML
echo "codex profile written: $CODEX_HOME/$PROFILE.config.toml (model=$MODEL, effort=$EFFORT)"

# --- preflight ------------------------------------------------------------------------
# The repository MCP servers run in .venv, while the vendored inorganic model
# intentionally runs in the separate .venv-retro environment.  Calling
# tools/check.sh --retro with .venv would therefore report a false failure when
# the model environment is healthy.  Validate the two environments explicitly
# and keep both receipts in the per-run audit directory.
tools/check.sh --servers --corpus > "$LOGDIR/preflight.json"
"$RETRO_PY" tools/retro_dry_run.py Li7La3Zr2O12 --device cpu > "$LOGDIR/retro_preflight.log"
echo "preflight: $(python3 -c 'import json,sys;print("OK" if json.load(open(sys.argv[1]))["ok"] else "FAILED")' "$LOGDIR/preflight.json")"
echo "retro preflight: PASS"
printf '%s\n' "$TOPIC" > "$WORKDIR/inputs/topic_input.txt"

# --- the run (identical flags to the formal case; sub-agents inherit RUNNER_* vars) ----
export RUNNER=codex RUNNER_CWD="$REPO" RUNNER_TIMEOUT=1800 RUNNER_TIMEOUT_ARTIFACT_POLICY=accept
export RUNNER_SANDBOX=danger-full-access RUNNER_ARGS="-p $PROFILE --ephemeral -c model=\"$MODEL\" -c model_reasoning_effort=\"$EFFORT\""
echo "launching orchestrator; events -> $LOGDIR/orchestrator.jsonl"
codex -a never -s danger-full-access -p "$PROFILE" --search exec --ephemeral --json \
  -C "$REPO" -o "$LOGDIR/orchestrator.final.md" "$TOPIC" | tee "$LOGDIR/orchestrator.jsonl" >/dev/null

# --- the orchestrator may stop at a human gate (scope / citation mismatches / contribution).
# Re-invoke with the same topic to resume from the ledger until check-done exits 0.
for attempt in 2 3 4 5; do
  if .venv/bin/python tools/loopctl.py check-done >/dev/null 2>&1; then break; fi
  echo "ledger not DONE after run $((attempt-1)); resuming (attempt $attempt)"
  codex -a never -s danger-full-access -p "$PROFILE" --search exec --ephemeral --json \
    -C "$REPO" -o "$LOGDIR/orchestrator.resume$attempt.final.md" "$TOPIC" | tee "$LOGDIR/orchestrator.resume$attempt.jsonl" >/dev/null
done

echo
echo "==> gates"; .venv/bin/python tools/loopctl.py status || true
echo "==> outputs"
ls -la "$WORKDIR/drafts/main.pdf" "$WORKDIR/library/references.bib" "$WORKDIR/state/CITATION_AUDIT.md" 2>/dev/null || true
echo "==> expected: main.pdf (8-25 pages), references.bib with all entries PASS in CITATION_AUDIT.md,"
echo "    figures/{svg,drawio}/fig0*.{svg,drawio}, state/ledger.json with review_pass PASS,"
echo "    state/parallel/<batch>/<task>.jsonl for every sub-agent, state/tool_calls.jsonl for MCP calls."
