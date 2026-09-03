#!/usr/bin/env bash
# Run three independent synthesis surveys sequentially.
#
# Each Codex invocation receives only one topic line.  The workspaces are kept
# separate so that papers, ledgers, MCP audit calls and sub-agent JSONL traces
# cannot be mixed across topics.  A failed topic is recorded and does not erase
# the other two runs.
set -uo pipefail

cd "$(dirname "$0")/.."
REPO="$PWD"
RUN_ROOT="${1:-/home/gaojing/goai_synthesis_runs/20260903_synthesis_topics}"
CORPUS_ROOT="${GOAI_LOCAL_CORPUS_ROOTS:-/mnt/nas/data/gaojing/markdown_corpus_v1/packages/markdown-v1-final}"

mkdir -p "$RUN_ROOT"
cp -f "$REPO/configs/three_synthesis_topics.tsv" "$RUN_ROOT/topic_manifest.tsv"

summary="$RUN_ROOT/run_summary.tsv"
printf 'slug\tstatus\texit_code\tworkspace\n' > "$summary"

run_one() {
  local slug="$1" topic="$2" workdir="$RUN_ROOT/$slug" rc
  # A completed topic is immutable for this sequence; allow safe re-entry
  # after an interrupted launcher without duplicating its audit trail.
  if [[ -f "$workdir/launcher.status" && "$(<"$workdir/launcher.status")" == "PASS" ]]; then
    printf '%s\tPASS\t%s\t%s\n' "$slug" "$(<"$workdir/launcher.exit")" "$workdir" >> "$summary"
    return 0
  fi
  mkdir -p "$workdir"
  printf '%s\n' "$topic" > "$workdir/topic_only.txt"
  printf 'START %s\t%s\n' "$slug" "$(date -Is)" | tee "$workdir/launcher.started"

  # Use the full local Parquet corpus.  The MCP server writes every call to
  # $workdir/state/tool_calls.jsonl; reproduce_core writes orchestrator and
  # parallel Codex JSONL streams below the same workspace.
  GOAI_CORPUS=private \
  GOAI_LOCAL_CORPUS_ROOTS="$CORPUS_ROOT" \
  GOAI_RETRO_DEVICE="${GOAI_RETRO_DEVICE:-cpu}" \
  bash "$REPO/scripts/reproduce_core.sh" --topic "$topic" --workdir "$workdir" \
    </dev/null >"$workdir/launcher.stdout.log" 2>"$workdir/launcher.stderr.log"
  rc=$?
  printf '%s\n' "$rc" > "$workdir/launcher.exit"
  printf '%s\n' "$(date -Is)" > "$workdir/launcher.finished"
  if [[ "$rc" == 0 ]]; then
    printf '%s\n' "PASS" > "$workdir/launcher.status"
    printf '%s\tPASS\t%s\t%s\n' "$slug" "$rc" "$workdir" >> "$summary"
  else
    printf '%s\n' "FAIL" > "$workdir/launcher.status"
    printf '%s\tFAIL\t%s\t%s\n' "$slug" "$rc" "$workdir" >> "$summary"
  fi
  # Do not abort the sequence: all three independent topics must get a run.
  return 0
}

while IFS=$'\t' read -r slug topic; do
  [[ -z "$slug" || "$slug" == \#* ]] && continue
  run_one "$slug" "$topic"
done < "$RUN_ROOT/topic_manifest.tsv"

echo "Three-topic sequence finished: $RUN_ROOT"
cat "$summary"
