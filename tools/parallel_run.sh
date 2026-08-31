#!/usr/bin/env bash
# parallel_run.sh —— 多 agent 并行 runner（Codex CLI / Claude Code 通吃）
#
# 用法（两种等价写法）:
#   tools/parallel_run.sh tasks.tsv [max_parallel]
#   tools/parallel_run.sh --backend codex --jobs 3 tasks.tsv
#
# tasks.tsv 每行:  任务名<TAB>提示词<TAB>本轮预期更新的非空产物（可选，逗号分隔）
#                  <TAB>依赖的前序任务名（可选，逗号分隔）
# 第三列路径默认必须比任务启动标记新；前缀 = 表示只检查存在且非空。
#   lit_diffusion	使用 goai-lit-search skill 检索「diffusion policy」子主题并入库
#   lit_worldmodel	使用 goai-lit-search skill 检索「world model manipulation」子主题并入库
#
# 环境变量:
#   RUNNER=codex|claude   （默认 codex；--backend 优先）
#   GOAI_WORKSPACE        工作区目录（默认 workspace，作为 agent 的 cwd）
#   RUNNER_ARGS           追加给 runner 的参数
#   RUNNER_TIMEOUT        单任务超时秒数（默认 0=不限）；超时任务被强杀并记 exit=124
#   RUNNER_TIMEOUT_ARTIFACT_POLICY  accept|fail（默认 accept）。超时但声明产物全部
#                         本轮更新且非空时，accept 将有效退出码记 0、状态记 WARN；
#                         原始进程退出码仍保存在 .process_exit。
#   RUNNER_CWD            agent执行目录（默认启动脚本时的仓库根）；与GOAI_WORKSPACE分离
#   RUNNER_SANDBOX        Codex shell 沙箱（默认 workspace-write）
#
# 产物: <workspace>/state/parallel/<run_id>/<任务名>.jsonl + .stderr.log +
#       .final.md + .process_exit + .status + .exit
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
RUNNER_TIMEOUT_ARTIFACT_POLICY="${RUNNER_TIMEOUT_ARTIFACT_POLICY:-accept}"
case "$RUNNER_TIMEOUT_ARTIFACT_POLICY" in
  accept|fail) ;;
  *) echo "RUNNER_TIMEOUT_ARTIFACT_POLICY 需为 accept 或 fail，收到: ${RUNNER_TIMEOUT_ARTIFACT_POLICY}" >&2; exit 2 ;;
esac
RUNNER_SANDBOX="${RUNNER_SANDBOX:-workspace-write}"
case "$RUNNER_SANDBOX" in
  read-only|workspace-write|danger-full-access) ;;
  *) echo "RUNNER_SANDBOX 非法: ${RUNNER_SANDBOX}" >&2; exit 2 ;;
esac

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
# 第四列依赖必须指向同一 TSV 中已经出现的任务。要求按拓扑顺序书写，既能在
# bash 3.2 下避免复杂图算法，也能从源头阻止“消费者先于证据生产者启动”。
BAD_DEPENDENCY="$(awk -F'\t' '
  function trim(v) { gsub(/^[[:space:]]+|[[:space:]]+$/, "", v); return v }
  $1 != "" && $1 !~ /^#/ && $2 != "" {
    name=$1
    count=split($4, deps, ",")
    for (i=1; i<=count; i++) {
      dep=trim(deps[i])
      if (dep != "" && !seen[dep]) {
        print name " -> " dep
      }
    }
    seen[name]=1
  }
' "$TASKS_FILE")"
[[ -z "$BAD_DEPENDENCY" ]] || {
  echo "任务依赖必须引用已在前面声明的任务（TSV 需按拓扑顺序）:" >&2
  echo "$BAD_DEPENDENCY" >&2
  exit 2
}

WS="${GOAI_WORKSPACE:-workspace}"
RUNNER_CWD="${RUNNER_CWD:-$PWD}"
RUN_ID="$(date +%Y%m%d_%H%M%S)_$$"
LOG_DIR="$WS/state/parallel/$RUN_ID"
mkdir -p "$LOG_DIR"

run_one() {
  local name="$1" prompt="$2" expected="${3:-}" dependencies="${4:-}"
  local log="$LOG_DIR/$name.jsonl"
  local stderr_log="$LOG_DIR/$name.stderr.log"
  local final="$LOG_DIR/$name.final.md"
  local marker="$LOG_DIR/$name.started"
  local rc process_rc pid t0 timed_out=0 artifact artifact_path freshness dep dep_rc
  local status="PASS" expected_checked=0 expected_ok=1 missing=()
  echo "[start] ${name} → ${log}"
  : >"$marker"
  if [[ -n "$dependencies" ]]; then
    IFS=',' read -r -a dependency_items <<<"$dependencies"
    for dep in "${dependency_items[@]}"; do
      dep="${dep#${dep%%[![:space:]]*}}"
      dep="${dep%${dep##*[![:space:]]}}"
      [[ -z "$dep" ]] && continue
      while [[ ! -f "$LOG_DIR/$dep.exit" ]]; do sleep 0.2; done
      dep_rc="$(cat "$LOG_DIR/$dep.exit")"
      if [[ "$dep_rc" != "0" ]]; then
        printf '依赖任务失败，当前任务未启动: %s (exit=%s)\n' "$dep" "$dep_rc" \
          >"$LOG_DIR/$name.validation.log"
        echo "not-started" >"$LOG_DIR/$name.process_exit"
        echo "BLOCKED_DEPENDENCY" >"$LOG_DIR/$name.status"
        echo "4" >"$LOG_DIR/$name.exit"
        echo "[block] ${name} (dependency=${dep}, exit=${dep_rc})"
        return 4
      fi
    done
  fi
  if [[ -n "$expected" ]]; then
    prompt="${prompt}

[parallel runner delivery protocol]
- Write the declared artifacts early, then update them incrementally after each completed phase; do not wait for the final chat response.
- Do not read any active log under ${LOG_DIR}. Only inspect a prior run log when the prompt names that closed run_id explicitly.
- Before finishing, verify every declared artifact is non-empty and saved inside the requested path.
Declared artifacts: ${expected}"
  fi
  # exec 让子 shell 被后端进程本体替换，$! 就是后端自己的 pid，
  # 超时看护才能真正杀到它（实测杀掉 codex 的 node 入口会连带回收原生子进程）。
  case "$RUNNER" in
    codex)
      # shellcheck disable=SC2086
      ( exec codex exec --skip-git-repo-check --json -s "$RUNNER_SANDBOX" \
          -c 'approval_policy="never"' -o "$final" \
          -C "$RUNNER_CWD" ${RUNNER_ARGS:-} \
          "$prompt" ) >"$log" 2>"$stderr_log" &
      ;;
    claude)
      # shellcheck disable=SC2086
      ( cd "$RUNNER_CWD" && exec claude -p ${RUNNER_ARGS:-} "$prompt" ) >"$log" 2>"$stderr_log" &
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
          >>"$stderr_log"
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
  process_rc=$?
  (( timed_out )) && process_rc=124 # 与 GNU timeout 一致，便于与后端自身退出码区分
  rc=$process_rc
  # 产物验收独立于进程退出。尤其是 timeout 后，先判断交付是否真的完成，再决定
  # 是 WARN 放行还是失败；原始退出码永远保存在 .process_exit，不会被抹掉。
  if [[ -n "$expected" ]]; then
    expected_checked=1
    IFS=',' read -r -a expected_items <<<"$expected"
    for artifact in "${expected_items[@]}"; do
      artifact="${artifact#${artifact%%[![:space:]]*}}"
      artifact="${artifact%${artifact##*[![:space:]]}}"
      [[ -z "$artifact" ]] && continue
      freshness=1
      if [[ "$artifact" == =* ]]; then
        freshness=0
        artifact="${artifact#=}"
      fi
      if [[ "$artifact" = /* ]]; then artifact_path="$artifact"; else artifact_path="$RUNNER_CWD/$artifact"; fi
      if [[ ! -s "$artifact_path" ]]; then
        missing+=("$artifact (缺失或为空)")
      elif (( freshness )) && [[ ! "$artifact_path" -nt "$marker" ]]; then
        missing+=("$artifact (本轮未更新)")
      fi
    done
    if (( ${#missing[@]} > 0 )); then
      printf '预期产物验收失败: %s\n' "${missing[*]}" >"$LOG_DIR/$name.validation.log"
      expected_ok=0
      (( process_rc == 0 )) && rc=3
    fi
  fi
  if (( process_rc == 124 )); then
    if (( expected_checked && expected_ok )) \
        && [[ "$RUNNER_TIMEOUT_ARTIFACT_POLICY" == "accept" ]]; then
      rc=0
      status="WARN_ARTIFACT_PASS_AFTER_TIMEOUT"
    else
      rc=124
      status="FAIL_TIMEOUT"
    fi
  elif (( rc != 0 )); then
    status="FAIL"
  fi
  echo "$process_rc" >"$LOG_DIR/$name.process_exit"
  echo "$status" >"$LOG_DIR/$name.status"
  echo "$rc" >"$LOG_DIR/$name.exit"
  echo "[done ] ${name} (exit=${rc}, process_exit=${process_rc}, status=${status})"
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
# `|| [[ -n "${task_line:-}" ]]`：最后一行没有换行符时 read 返回非零，
# 但变量已赋值；缺了这个兜底，手工编辑的 tasks.tsv（多数编辑器不补末尾换行）
# 会被静默丢掉最后一个任务，汇总还报全部成功。
while IFS= read -r task_line || [[ -n "${task_line:-}" ]]; do
  # TAB 属于 shell 的空白 IFS 字符，`read name prompt expected dependencies` 会把
  # 连续 TAB 合并，导致空第三列时第四列依赖错位。逐列切割以保留空字段。
  name="${task_line%%$'\t'*}"
  if [[ "$task_line" == *$'\t'* ]]; then task_rest="${task_line#*$'\t'}"; else task_rest=""; fi
  prompt="${task_rest%%$'\t'*}"
  if [[ "$task_rest" == *$'\t'* ]]; then task_rest="${task_rest#*$'\t'}"; else task_rest=""; fi
  expected="${task_rest%%$'\t'*}"
  if [[ "$task_rest" == *$'\t'* ]]; then dependencies="${task_rest#*$'\t'}"; else dependencies=""; fi
  [[ -z "${name// /}" || "$name" == \#* ]] && continue
  if [[ -z "${prompt:-}" ]]; then
    echo "[skip ] ${name}：缺少提示词列（需 TAB 分隔）" >&2
    continue
  fi
  wait_slot
  # </dev/null 必需：codex exec 会读 stdin（"Reading additional input from
  # stdin..."），子进程继承本循环的 tasks 文件 fd 会把后续任务行吞掉。
  run_one "$name" "$prompt" "${expected:-}" "${dependencies:-}" </dev/null &
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
  status="$(cat "$LOG_DIR/$name.status" 2>/dev/null || echo UNKNOWN)"
  if [[ "$status" == WARN_* ]]; then
    process_rc="$(cat "$LOG_DIR/$name.process_exit" 2>/dev/null || echo unknown)"
    echo "WARN  $name ($status; process_exit=$process_rc; artifacts accepted)"
  elif [[ "$rc" == "0" ]]; then
    echo "PASS  $name"
  else
    echo "FAIL  $name (exit=$rc)  日志: $LOG_DIR/$name.jsonl"
    fail=$((fail + 1))
  fi
done
echo "任务数: ${total}  失败: ${fail}"
echo "日志目录: $LOG_DIR"
exit $(( fail > 0 ? 1 : 0 ))
