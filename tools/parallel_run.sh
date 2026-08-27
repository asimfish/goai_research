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
#   RUNNER_TIMEOUT        单任务超时秒数（默认 0=不限）；超时任务被强杀并记 exit=124
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
[[ "$MAX_PAR" =~ ^[1-9][0-9]*$ ]] || { echo "--jobs / max_parallel 需为正整数，收到: ${MAX_PAR}" >&2; exit 2; }
RUNNER_TIMEOUT="${RUNNER_TIMEOUT:-0}"
[[ "$RUNNER_TIMEOUT" =~ ^[0-9]+$ ]] || { echo "RUNNER_TIMEOUT 需为非负整数秒（0=不限），收到: ${RUNNER_TIMEOUT}" >&2; exit 2; }

# 启动前预检：backend 名合法 + 命令真实可用。
# 缺后端时必须 exit 2 直接退出 —— 否则会空跑一批任务、汇总里还报 0 失败。
case "$RUNNER" in
  codex|claude) ;;
  *) echo "未知 backend: ${RUNNER}（支持 codex / claude）" >&2; exit 2 ;;
esac
command -v "$RUNNER" >/dev/null 2>&1 || {
  echo "后端命令不可用: PATH 中找不到 ${RUNNER}" >&2
  echo "提示: 若 ${RUNNER} 只是交互式 shell 的 alias/函数（如 zsh alias），" >&2
  echo "      本脚本的非交互 shell 看不到它；请安装为 PATH 可见的可执行文件，" >&2
  echo "      或用 RUNNER_ARGS/--backend 指定可用后端。" >&2
  exit 2
}

# 任务名预检：日志/退出码按任务名落盘，名字冲突或带路径分隔符会让任务
# 在汇总里凭空消失（实测：重名任务真实 exit 9 却被报成整批 PASS 且脚本退出 0）。
_task_names() {
  awk -F'\t' '$1 != "" && $1 !~ /^#/ && $2 != "" {print $1}' "$TASKS_FILE"
}
BAD_NAMES="$(_task_names | grep '/' | sort -u | tr '\n' ' ')"
[[ -z "${BAD_NAMES// /}" ]] || {
  echo "任务名不能包含 /（日志路径会落到不存在的子目录，退出码丢失）: ${BAD_NAMES}" >&2
  exit 2
}
DUP_NAMES="$(_task_names | sort | uniq -d | tr '\n' ' ')"
[[ -z "${DUP_NAMES// /}" ]] || {
  echo "任务名重复（多个任务会并发覆盖同一份 .log/.exit，失败会被吞）: ${DUP_NAMES}" >&2
  exit 2
}

WS="${GOAI_WORKSPACE:-workspace}"
RUN_ID="$(date +%Y%m%d_%H%M%S)_$$"
LOG_DIR="$WS/state/parallel/$RUN_ID"
mkdir -p "$LOG_DIR"

run_one() {
  local name="$1" prompt="$2"
  local log="$LOG_DIR/$name.log"
  local rc pid t0 timed_out=0
  echo "[start] ${name} → ${log}"
  # exec 让子 shell 被后端进程本体替换，$! 就是后端自己的 pid，
  # 超时看护才能真正杀到它（实测杀掉 codex 的 node 入口会连带回收原生子进程）。
  case "$RUNNER" in
    codex)
      # shellcheck disable=SC2086
      ( exec codex exec --skip-git-repo-check -C "$WS" ${RUNNER_ARGS:-} \
          "$prompt" ) >"$log" 2>&1 &
      ;;
    claude)
      # shellcheck disable=SC2086
      ( cd "$WS" && exec claude -p ${RUNNER_ARGS:-} "$prompt" ) >"$log" 2>&1 &
      ;;
  esac
  pid=$!
  # 超时看护：后端卡死时整批 wait 会永久挂住。实测 codex 断网后只会无限打印
  # "Reconnecting... waiting for network"，7 分钟不自行退出，也不吐任何结论。
  if (( RUNNER_TIMEOUT > 0 )); then
    t0=$SECONDS
    while kill -0 "$pid" 2>/dev/null; do
      if (( SECONDS - t0 >= RUNNER_TIMEOUT )); then
        echo "[parallel_run] 任务超过 RUNNER_TIMEOUT=${RUNNER_TIMEOUT}s 未返回，已强杀" \
          >>"$log"
        kill -TERM "$pid" 2>/dev/null
        sleep 2
        kill -KILL "$pid" 2>/dev/null
        timed_out=1
        break
      fi
      sleep 1
    done
  fi
  wait "$pid"
  rc=$?
  (( timed_out )) && rc=124        # 与 GNU timeout 一致，便于与后端自身退出码区分
  echo "$rc" >"$LOG_DIR/$name.exit"
  echo "[done ] ${name} (exit=${rc})"
  return $rc
}

# 并发闸门：macOS 自带 bash 3.2 不支持 `wait -n`（返回 rc=2 而非 127），
# 旧实现只认 127，于是 --jobs 上限被静默忽略、任务全量并发。
# 统一改用 `jobs -pr` 计数轮询，在 bash 3.2 / 4 / 5 下都真实生效。
wait_slot() {
  while (( $(jobs -pr | wc -l) >= MAX_PAR )); do
    sleep 0.2
  done
}

total=0
launched=()
# `|| [[ -n "${name:-}" ]]`：最后一行没有换行符时 read 返回非零，
# 但变量已赋值；缺了这个兜底，手工编辑的 tasks.tsv（多数编辑器不补末尾换行）
# 会被静默丢掉最后一个任务，汇总还报全部成功。
while IFS=$'\t' read -r name prompt || [[ -n "${name:-}" ]]; do
  [[ -z "${name// /}" || "$name" == \#* ]] && continue
  if [[ -z "${prompt:-}" ]]; then
    echo "[skip ] ${name}：缺少提示词列（需 TAB 分隔）" >&2
    continue
  fi
  wait_slot
  # </dev/null 必需：codex exec 会读 stdin（"Reading additional input from
  # stdin..."），子进程继承本循环的 tasks 文件 fd 会把后续任务行吞掉。
  run_one "$name" "$prompt" </dev/null &
  total=$((total + 1))
  launched+=("$name")
done < "$TASKS_FILE"
wait

if (( total == 0 )); then
  echo "tasks 文件里没有可执行任务（每行需: 任务名<TAB>提示词）: $TASKS_FILE" >&2
  exit 2
fi

echo
echo "===== 并行批次汇总 ====="
# 按「真正启动过的任务」逐个对账，而不是 glob .exit 文件：
# 退出码没落盘的任务必须显式报失败，否则它会从汇总里消失、整批假绿。
fail=0
for name in "${launched[@]}"; do
  f="$LOG_DIR/$name.exit"
  if [[ ! -f "$f" ]]; then
    echo "FAIL  $name (退出码未落盘: $f 缺失，任务未正常收尾)"
    fail=$((fail + 1))
    continue
  fi
  rc="$(cat "$f")"
  if [[ "$rc" == "0" ]]; then
    echo "PASS  $name"
  else
    echo "FAIL  $name (exit=$rc)  日志: $LOG_DIR/$name.log"
    fail=$((fail + 1))
  fi
done
echo "任务数: ${total}  失败: ${fail}"
echo "日志目录: $LOG_DIR"
exit $(( fail > 0 ? 1 : 0 ))
