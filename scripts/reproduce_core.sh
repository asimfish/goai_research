#!/usr/bin/env bash
# Reproduce the core result: ONE research topic line in -> verified survey PDF + evidence out.
#
# This is the exact launch used for the formal case
# (submission/03_运行与评测包/正式案例_BYZSO冷启动):
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
#     40 sub-agent tasks plus the orchestrator
#     (see submission/04_指标与分析代码/agent_trace_stats_byzso.md);
#     the local two-stage precursor model runs on CPU in seconds per query.
#
# Usage
#   bash scripts/reproduce_core.sh                       # formal topic, fresh workspace
#   bash scripts/reproduce_core.sh --topic "LLZO 石榴石固态电解质的烧结致密化"
#   bash scripts/reproduce_core.sh --verify-only --workdir /path/to/completed/workspace
#   GOAI_CORPUS=private bash scripts/reproduce_core.sh   # use your own private corpus env
#
# Model pinning: model and reasoning effort are passed explicitly so the run matches the
# declared configuration (gpt-5.6-sol, reasoning effort xhigh). Override with
# GOAI_MODEL / GOAI_REASONING_EFFORT if your account exposes different model ids.
# Transient failures (model at capacity, network) do not abort the run: the orchestrator is
# re-invoked from the ledger with back-off (up to 6 attempts). Set GOAI_MODEL_FALLBACK=<model>
# to switch models after three capacity failures (opt-in; the switch is logged in the ledger).
set -euo pipefail
cd "$(dirname "$0")/.."
REPO="$PWD"

TOPIC='调研主题：Ba5Y12Zn[O(SiO4)]8及其结构相近化合物的合成条件'
WORKDIR=""
VERIFY_ONLY=0
while (( $# )); do
  case "$1" in
    --topic)   TOPIC="调研主题：${2:?}"; shift 2 ;;
    --workdir) WORKDIR="${2:?}"; shift 2 ;;
    --verify-only) VERIFY_ONLY=1; shift ;;
    -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

# TeX engine discovery: services / cron / screen shells often lack ~/.local/bin, so a user-level
# tectonic (the engine build_tex.sh falls back to) would be invisible and the run would end without
# a PDF. Put the first directory that holds one on PATH before preflight and before the agents start.
if ! command -v xelatex >/dev/null 2>&1 && ! command -v tectonic >/dev/null 2>&1; then
  for d in "$HOME/.local/bin" "$HOME/.cargo/bin" /usr/local/texlive/*/bin/* "$HOME/miniforge3/bin" "$HOME/miniconda3/bin"; do
    if [[ -x "$d/tectonic" || -x "$d/xelatex" ]]; then export PATH="$d:$PATH"; echo "tex engine: $d"; break; fi
  done
fi

if [[ $VERIFY_ONLY == 0 ]]; then
command -v codex >/dev/null || { echo "codex CLI not found; install with: npm i -g @openai/codex" >&2; exit 2; }
[[ -x .venv/bin/python ]] || bash install.sh --retro
RETRO_PY=".venv-retro/bin/python"; [[ -x $RETRO_PY ]] || RETRO_PY=".venv/bin/python"

STAMP="$(date +%Y%m%d_%H%M%S)"
WORKDIR="${WORKDIR:-$REPO/workspace_repro_$STAMP}"
mkdir -p "$WORKDIR"/{library/pdfs,notes,memory,style_bank/{pdfs,exemplar_figures},figures/{svg,drawio,figspec,assets,candidates},drafts/sections,ideas,state/{parallel,review_traces},inputs}
LOGDIR="$WORKDIR/state/orchestrator"; mkdir -p "$LOGDIR"

# --- corpus: public package of the cited full texts by default -----------------------
if [[ "${GOAI_CORPUS:-public}" == "public" ]]; then
  export GOAI_LOCAL_CORPUS_ROOTS="$REPO/submission/02_研究数据与证据包/corpus_release"
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
# TOML 基本字符串：转义反斜杠与双引号（路径可含中文，UTF-8 直接合法）。
toml_str() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }
# 私有语料的索引 / 分片变量按需追加。不能写在 heredoc 里的 ${var:+...} 中——bash 会把展开体内的双引号
# 当引号处理并删掉，生成的 TOML 没有引号，codex 直接以 "string values must be quoted" 退出
# （2026-09-06 控制台以私有全库发起时实测触发）。
LIT_ENV="GOAI_EMAIL = \"$(toml_str "$GOAI_EMAIL")\", GOAI_WORKSPACE = \"$(toml_str "$WORKDIR")\", GOAI_LOCAL_CORPUS_ROOTS = \"$(toml_str "$GOAI_LOCAL_CORPUS_ROOTS")\""
if [[ -n "${GOAI_LOCAL_CORPUS_EXPECTED_INDEX:-}" ]]; then
  LIT_ENV+=", GOAI_LOCAL_CORPUS_EXPECTED_INDEX = \"$(toml_str "$GOAI_LOCAL_CORPUS_EXPECTED_INDEX")\""
fi
if [[ -n "${GOAI_LOCAL_CORPUS_SHARD_ROOT:-}" ]]; then
  LIT_ENV+=", GOAI_LOCAL_CORPUS_SHARD_ROOT = \"$(toml_str "$GOAI_LOCAL_CORPUS_SHARD_ROOT")\""
fi
WORKDIR_T="$(toml_str "$WORKDIR")"
cat > "$CODEX_HOME/$PROFILE.config.toml" <<TOML
model = "$MODEL"
model_reasoning_effort = "$EFFORT"

[mcp_servers.goai-litsearch]
command = "$REPO/.venv/bin/python"
args = ["$REPO/server/litsearch_server.py"]
default_tools_approval_mode = "approve"
env_vars = ["GOAI_RUN_ID", "GOAI_TASK_NAME"]  # parallel_run.sh 子任务归因 → tool_calls.jsonl.run_id
env = { $LIT_ENV }

[mcp_servers.goai-refcheck]
command = "$REPO/.venv/bin/python"
args = ["$REPO/server/refcheck_server.py"]
default_tools_approval_mode = "approve"
env_vars = ["GOAI_RUN_ID", "GOAI_TASK_NAME"]  # parallel_run.sh 子任务归因 → tool_calls.jsonl.run_id
env = { GOAI_EMAIL = "$(toml_str "$GOAI_EMAIL")", GOAI_WORKSPACE = "$WORKDIR_T" }

[mcp_servers.goai-figure]
command = "$REPO/.venv/bin/python"
args = ["$REPO/server/figure_server.py"]
default_tools_approval_mode = "approve"
env_vars = ["GOAI_RUN_ID", "GOAI_TASK_NAME"]  # parallel_run.sh 子任务归因 → tool_calls.jsonl.run_id
env = { GOAI_WORKSPACE = "$WORKDIR_T" }

[mcp_servers.goai-retro]
command = "$REPO/$RETRO_PY"
args = ["$REPO/server/retro_server.py"]
default_tools_approval_mode = "approve"
env_vars = ["GOAI_RUN_ID", "GOAI_TASK_NAME"]  # parallel_run.sh 子任务归因 → tool_calls.jsonl.run_id
env = { GOAI_WORKSPACE = "$WORKDIR_T", GOAI_INORGANIC_RETRO_ROOT = "$(toml_str "$GOAI_INORGANIC_RETRO_ROOT")", GOAI_RETRO_DEVICE = "$GOAI_RETRO_DEVICE" }
TOML
echo "codex profile written: $CODEX_HOME/$PROFILE.config.toml (model=$MODEL, effort=$EFFORT)"
# 有 tomllib（Python ≥3.11）就先解析一遍，别把坏配置交给 codex 才发现
if python3 -c 'import tomllib' 2>/dev/null; then
  python3 - "$CODEX_HOME/$PROFILE.config.toml" <<'PY' || { echo "生成的 codex profile 不是合法 TOML，见上方报错" >&2; exit 2; }
import sys, tomllib
with open(sys.argv[1], "rb") as fh:
    tomllib.load(fh)
PY
fi

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
export GOAI_CODEX_PROFILE="$PROFILE"   # parallel_run.sh 兜底：RUNNER_ARGS 丢失时仍给子 agent 挂上 MCP profile
echo "launching orchestrator; events -> $LOGDIR/orchestrator.jsonl"
echo "live view: GOAI_WORKSPACE=$WORKDIR python3 tools/live_view.py --follow   (or --serve 5051 for the browser dashboard)"
# GOAI_RUN_ID 让编排器自己的 MCP 调用也能在 state/tool_calls.jsonl 归因（key 与 live_view 的编排器任务一致）；
# parallel_run.sh 派出的子任务会在各自子进程里覆盖成 <run_id>/<task>。
# 一次编排器调用：捕获退出码而不是让 set -e 在管道失败时直接杀掉整个脚本
# （2026-09-06 实测：模型 "at capacity" 导致 codex 非零退出，脚本在续跑循环之前就死了）。
run_orchestrator() {   # $1 = 事件流/回执文件名后缀（"" 或 ".resumeN"）
  local suffix="$1" rc
  export GOAI_RUN_ID="orchestrator/orchestrator${suffix}" GOAI_TASK_NAME="orchestrator${suffix}"
  set +e
  codex -a never -s danger-full-access -p "$PROFILE" --search exec --ephemeral --json \
    -C "$REPO" -o "$LOGDIR/orchestrator${suffix}.final.md" "$TOPIC" </dev/null \
    | tee "$LOGDIR/orchestrator${suffix}.jsonl" >/dev/null
  rc=${PIPESTATUS[0]}
  set -e
  return "$rc"
}
# 事件流末尾的错误摘要（容量不足 / 网络 / 用量上限）
last_error() { grep -o '"message": *"[^"]*"' "$1" 2>/dev/null | tail -1 | sed 's/"message": *//'; }

run_orchestrator "" && echo "orchestrator finished (attempt 1)" || echo "orchestrator exited rc=$? (attempt 1): $(last_error "$LOGDIR/orchestrator.jsonl")"

# --- the orchestrator may stop at a human gate (scope / citation mismatches / contribution),
# or die on a transient error (model at capacity, network). Re-invoke with the same topic to
# resume from the ledger until check-done exits 0. Capacity errors get a longer back-off; with
# GOAI_MODEL_FALLBACK set (opt-in), the third capacity failure switches the orchestrator and
# sub-agents to that model for the rest of the run (the change is logged in the ledger).
capacity_hits=0
for attempt in 2 3 4 5 6; do
  if .venv/bin/python tools/loopctl.py check-done >/dev/null 2>&1; then break; fi
  prev="$LOGDIR/orchestrator$([[ $attempt -eq 2 ]] && echo "" || echo ".resume$((attempt-1))").jsonl"
  err="$(last_error "$prev")"
  wait_s=30
  if [[ "$err" == *"at capacity"* || "$err" == *"usage limit"* || "$err" == *"rate limit"* ]]; then
    capacity_hits=$((capacity_hits+1)); wait_s=180
    if [[ -n "${GOAI_MODEL_FALLBACK:-}" && "$capacity_hits" -ge 3 && "$MODEL" != "$GOAI_MODEL_FALLBACK" ]]; then
      echo "model $MODEL at capacity ${capacity_hits}x; falling back to $GOAI_MODEL_FALLBACK for the rest of the run"
      MODEL="$GOAI_MODEL_FALLBACK"
      sed -i "s/^model = .*/model = \"$MODEL\"/" "$CODEX_HOME/$PROFILE.config.toml"
      export RUNNER_ARGS="-p $PROFILE --ephemeral -c model=\"$MODEL\" -c model_reasoning_effort=\"$EFFORT\""
      .venv/bin/python tools/loopctl.py log --stage "$(.venv/bin/python -c 'import json;print(json.load(open("'"$WORKDIR"'/state/ledger.json")).get("stage","intake"))' 2>/dev/null || echo intake)" \
        --agent orchestrator --event decision --detail "model fallback: $GOAI_MODEL_FALLBACK (previous model at capacity ${capacity_hits}x)" >/dev/null 2>&1 || true
    fi
  fi
  echo "ledger not DONE after run $((attempt-1))${err:+ (last error: $err)}; resuming in ${wait_s}s (attempt $attempt)"
  sleep "$wait_s"
  run_orchestrator ".resume$attempt" && echo "orchestrator finished (attempt $attempt)" || echo "orchestrator exited rc=$? (attempt $attempt): $(last_error "$LOGDIR/orchestrator.resume$attempt.jsonl")"
done
else
  [[ -n "$WORKDIR" ]] || { echo "--verify-only requires --workdir" >&2; exit 2; }
  [[ -d "$WORKDIR" ]] || { echo "workspace not found: $WORKDIR" >&2; exit 2; }
  WORKDIR="$(realpath "$WORKDIR")"
  LOGDIR="$WORKDIR/state/orchestrator"
  mkdir -p "$LOGDIR"
  export GOAI_WORKSPACE="$WORKDIR"
  MODEL="${GOAI_MODEL:-gpt-5.6-sol}"
  EFFORT="${GOAI_REASONING_EFFORT:-xhigh}"
  echo "verify-only: $WORKDIR"
fi

# --- fail-closed final verification --------------------------------------------------
fail() { echo "CORE REPRODUCTION FAILED: $*" >&2; exit 1; }
require_nonempty() { [[ -s "$1" ]] || fail "missing or empty artifact: $1"; }

echo
echo "==> final ledger gate"
if ! .venv/bin/python tools/loopctl.py check-done; then
  .venv/bin/python tools/loopctl.py status >&2 || true
  fail "ledger did not reach DONE after 6 orchestrator attempts"
fi

require_nonempty "$WORKDIR/drafts/main.pdf"
require_nonempty "$WORKDIR/library/references.bib"
require_nonempty "$WORKDIR/state/CITATION_AUDIT.md"
require_nonempty "$WORKDIR/state/CITATION_AUDIT.json"
require_nonempty "$WORKDIR/state/ledger.json"
require_nonempty "$WORKDIR/state/tool_calls.jsonl"

# bash 3.2 (macOS /bin/bash) has no globstar; collect recursive traces with find.
shopt -s nullglob
SVG_FILES=("$WORKDIR"/figures/svg/*.svg)
DRAWIO_FILES=("$WORKDIR"/figures/drawio/*.drawio)
TRACE_FILES=()
while IFS= read -r -d '' trace; do TRACE_FILES+=("$trace"); done \
  < <(find "$WORKDIR/state/parallel" -type f -name '*.jsonl' -print0 2>/dev/null)
(( ${#SVG_FILES[@]} > 0 )) || fail "no SVG figure artifacts found"
(( ${#DRAWIO_FILES[@]} > 0 )) || fail "no draw.io figure artifacts found"
(( ${#TRACE_FILES[@]} > 0 )) || fail "no per-task JSONL traces found"
for path in "${SVG_FILES[@]}" "${DRAWIO_FILES[@]}" "${TRACE_FILES[@]}"; do
  require_nonempty "$path"
done

echo "==> deterministic manuscript gates"
run_guard() {
  local name="$1"; shift
  local guard_log="$LOGDIR/${name}.log"
  if ! "$@" > "$guard_log" 2>&1; then
    tail -40 "$guard_log" >&2 || true
    fail "$name did not pass (full log: $guard_log)"
  fi
}
run_guard bib_guard .venv/bin/python tools/bib_guard.py \
  "$WORKDIR/drafts/sections" "$WORKDIR/library/references.bib"
run_guard tex_guard .venv/bin/python tools/tex_guard.py "$WORKDIR/drafts"
# 与 goai-survey-writer / goai-orchestrator 约定的范围一致：只查正文源文件，
# 不查 blueprint.md / revision_log.md 等内部规划笔记。
run_guard academic_language_guard .venv/bin/python tools/academic_language_guard.py \
  "$WORKDIR/drafts/sections" "$WORKDIR/drafts/main.tex"
# 终稿 PDF 必须是 TeX 从模板编译的产物（Producer/字体/时效/摘要块/编号标题）
run_guard pdf_guard .venv/bin/python tools/pdf_guard.py "$WORKDIR/drafts/main.pdf" \
  --tex "$WORKDIR/drafts/main.tex" --bib "$WORKDIR/library/references.bib"

.venv/bin/python - "$WORKDIR" "$TOPIC" "$MODEL" "$EFFORT" <<'PY'
from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
topic, model, effort = sys.argv[2:]
audit_path = workspace / "state" / "CITATION_AUDIT.json"
audit = json.loads(audit_path.read_text(encoding="utf-8"))
counts = audit.get("counts", {})
# 与 goai-refcheck 服务端闸门同口径：MISMATCH / UNVERIFIED / ERROR 必须为 0；
# FIX 是带 suggested_bibtex 的元数据漂移提示（作者缩写、年份口径、题名排版），允许存在。
blocking = {k: counts.get(k, 0) for k in ("MISMATCH", "UNVERIFIED", "ERROR") if counts.get(k, 0)}
if blocking or audit.get("gate") != "PASS" or not audit.get("total"):
    raise SystemExit(f"citation audit gate is not PASS: gate={audit.get('gate')!r} counts={counts!r}")

required = [
    workspace / "drafts" / "main.pdf",
    workspace / "library" / "references.bib",
    workspace / "state" / "CITATION_AUDIT.json",
    workspace / "state" / "ledger.json",
    workspace / "state" / "tool_calls.jsonl",
]

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

# 子 agent 实际使用的模型：来自各并行批次的 RUN_INFO.json（parallel_run.sh 记录）。
# 运行中模型可能因供给侧变化被替换（实跑：gpt-5.6-sol 中途对账户不可用 → 子任务改 gpt-5.5），
# 回执必须写实际值而不是钉死的期望值。
import collections
import re as _re
sub_models: collections.Counter[str] = collections.Counter()
for info_path in sorted((workspace / "state" / "parallel").glob("*/RUN_INFO.json")):
    try:
        info = json.loads(info_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        continue
    name = info.get("model") or ""
    if not name:
        m = _re.search(r'(?:^|\s)(?:-m|--model)[\s=]+"?([^\s"]+)"?', info.get("runner_args") or "") \
            or _re.search(r'\smodel=("?)([^\s"]+)', info.get("runner_args") or "")
        name = (m.group(m.lastindex) if m else "") or "unknown"
    sub_models[name] += 1

receipt = {
    "status": "PASS",
    "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "workspace": str(workspace),
    "topic": topic,
    "model": model,
    "reasoning_effort": effort,
    "sub_agent_models": dict(sub_models),          # {模型: 批次数}；与 model 不一致时说明中途替换
    "git_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip(),
    "gates": {
        "loopctl_check_done": "PASS",
        "citation_audit": f"PASS (PASS={counts.get('PASS', 0)}, FIX={counts.get('FIX', 0)})",
        "bib_guard": "PASS",
        "tex_guard": "PASS",
        "academic_language_guard": "PASS",
    },
    "artifacts": {str(path.relative_to(workspace)): sha256(path) for path in required},
    "svg_files": len(list((workspace / "figures" / "svg").glob("*.svg"))),
    "drawio_files": len(list((workspace / "figures" / "drawio").glob("*.drawio"))),
    "task_trace_files": len(list((workspace / "state" / "parallel").glob("**/*.jsonl"))),
}
receipt_path = workspace / "state" / "REPRODUCTION_RECEIPT.json"
receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
print(f"reproduction receipt: {receipt_path}")
PY

echo "==> verified outputs"
ls -la "$WORKDIR/drafts/main.pdf" "$WORKDIR/library/references.bib" \
  "$WORKDIR/state/CITATION_AUDIT.md" "$WORKDIR/state/REPRODUCTION_RECEIPT.json"
echo "CORE REPRODUCTION PASSED: $WORKDIR"
