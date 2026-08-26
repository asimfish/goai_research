#!/usr/bin/env bash
# parallel_run.sh —— 多 agent 并行 runner（Codex CLI / Claude Code 通吃）
#
# 用法:
#   tools/parallel_run.sh tasks.tsv [max_parallel]
#
# tasks.tsv 每行:  任务名<TAB>提示词
#   lit_diffusion	使用 goai-lit-search skill 检索「diffusion policy」子主题并入库
#   lit_worldmodel	使用 goai-lit-search skill 检索「world model manipulation」子主题并入库
#
# 环境变量:
#   RUNNER=codex|claude   （默认 codex）
#   GOAI_WORKSPACE        工作区目录（默认 workspace，作为 agent 的 cwd）
#   RUNNER_ARGS           追加给 runner 的参数
#
# 产物: <workspace>/state/parallel_logs/<时间戳>/<任务名>.log
set -uo pipefail

TASKS_FILE="${1:?用法: parallel_run.sh tasks.tsv [max_parallel]}"
MAX_PAR="${2:-4}"
RUNNER="${RUNNER:-codex}"
WS="${GOAI_WORKSPACE:-workspace}"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="$WS/state/parallel_logs/$STAMP"
mkdir -p "$LOG_DIR"

run_one() {
  local name="$1" prompt="$2"
  local log="$LOG_DIR/$name.log"
  echo "[start] $name → $log"
  case "$RUNNER" in
    codex)
      # shellcheck disable=SC2086
      codex exec --skip-git-repo-check -C "$WS" ${RUNNER_ARGS:-} \
        "$prompt" >"$log" 2>&1
      ;;
    claude)
      # shellcheck disable=SC2086
      (cd "$WS" && claude -p ${RUNNER_ARGS:-} "$prompt") >"$log" 2>&1
      ;;
    *)
      echo "未知 RUNNER=$RUNNER（支持 codex / claude）" >"$log"
      return 2
      ;;
  esac
  local rc=$?
  echo "$rc" >"$LOG_DIR/$name.exit"
  echo "[done ] $name (exit=$rc)"
  return $rc
}

active=0
while IFS=$'\t' read -r name prompt; do
  [[ -z "${name// /}" || "$name" == \#* ]] && continue
  if [[ -z "${prompt:-}" ]]; then
    echo "[skip ] $name：缺少提示词列（需 TAB 分隔）" >&2
    continue
  fi
  run_one "$name" "$prompt" &
  active=$((active + 1))
  if (( active >= MAX_PAR )); then
    wait -n 2>/dev/null || wait
    active=$((active - 1))
  fi
done < "$TASKS_FILE"
wait

echo
echo "===== 并行批次汇总 ====="
fail=0
for f in "$LOG_DIR"/*.exit; do
  [[ -e "$f" ]] || continue
  name="$(basename "${f%.exit}")"
  rc="$(cat "$f")"
  if [[ "$rc" == "0" ]]; then
    echo "PASS  $name"
  else
    echo "FAIL  $name (exit=$rc)  日志: $LOG_DIR/$name.log"
    fail=$((fail + 1))
  fi
done
echo "日志目录: $LOG_DIR"
exit $(( fail > 0 ? 1 : 0 ))
