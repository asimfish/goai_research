#!/usr/bin/env bash
# parallel_run.sh —— 多 agent 并行 runner（Codex CLI / Claude Code 通吃）
#
# 用法（两种等价写法）:
#   tools/parallel_run.sh tasks.tsv [max_parallel]
#   tools/parallel_run.sh --backend codex --jobs 3 tasks.tsv
#
# tasks.tsv 每行:  任务名<TAB>提示词
#   lit_diffusion	使用 goai-lit-search skill 检索「diffusion policy」子主题并入库
#   lit_worldmodel	使用 goai-lit-search skill 检索「world model manipulation」子主题并入库
#
# 环境变量:
#   RUNNER=codex|claude   （默认 codex；--backend 优先）
#   GOAI_WORKSPACE        工作区目录（默认 workspace，作为 agent 的 cwd）
#   RUNNER_ARGS           追加给 runner 的参数
#
# 产物: <workspace>/state/parallel/<run_id>/<任务名>.log + .exit
set -uo pipefail

RUNNER="${RUNNER:-codex}"
TASKS_FILE=""
MAX_PAR=4
while (( $# )); do
  case "$1" in
    --backend) RUNNER="${2:?--backend 需要值}"; shift 2 ;;
    --jobs)    MAX_PAR="${2:?--jobs 需要值}"; shift 2 ;;
    -*)        echo "未知参数: $1（支持 --backend、--jobs）" >&2; exit 2 ;;
    *) if [[ -z "$TASKS_FILE" ]]; then TASKS_FILE="$1"; else MAX_PAR="$1"; fi
       shift ;;
  esac
done
[[ -n "$TASKS_FILE" ]] || { echo "用法: parallel_run.sh [--backend codex|claude] [--jobs N] tasks.tsv" >&2; exit 2; }
[[ -f "$TASKS_FILE" ]] || { echo "tasks 文件不存在: $TASKS_FILE" >&2; exit 2; }

WS="${GOAI_WORKSPACE:-workspace}"
RUN_ID="$(date +%Y%m%d_%H%M%S)_$$"
LOG_DIR="$WS/state/parallel/$RUN_ID"
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

# 等一个槽位：wait -n 的非零返回是「已结束任务的退出码」，不代表 wait 失败；
# 只有 127（bash < 4.3 不支持 -n）才退化为全量 wait
wait_slot() {
  wait -n 2>/dev/null
  local rc=$?
  if (( rc == 127 )); then
    wait
    active=0
    return
  fi
  active=$((active - 1))
}

active=0
total=0
while IFS=$'\t' read -r name prompt; do
  [[ -z "${name// /}" || "$name" == \#* ]] && continue
  if [[ -z "${prompt:-}" ]]; then
    echo "[skip ] $name：缺少提示词列（需 TAB 分隔）" >&2
    continue
  fi
  run_one "$name" "$prompt" &
  active=$((active + 1))
  total=$((total + 1))
  if (( active >= MAX_PAR )); then
    wait_slot
  fi
done < "$TASKS_FILE"
wait

if (( total == 0 )); then
  echo "tasks 文件里没有可执行任务（每行需: 任务名<TAB>提示词）: $TASKS_FILE" >&2
  exit 2
fi

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
