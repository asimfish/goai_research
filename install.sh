#!/usr/bin/env bash
# goai_research 安装：建 venv、装依赖、生成填好绝对路径的 MCP 配置。
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"

WITH_RETRO=0
if [ "${1:-}" = "--retro" ] || [ "${GOAI_INSTALL_RETRO:-0}" = "1" ]; then
  WITH_RETRO=1
fi
echo "==> goai_research install @ $ROOT"

# ---- 1. Python >=3.10 的 venv + uv.lock 锁定安装 -------------------------------
# retro 依赖里的 torch 默认从 CPU 轮子源安装（约 200 MB），避免默认 PyPI 拉取
# 2.5 GB 的 CUDA 轮子；需要 GPU 时设 GOAI_TORCH_INDEX（如
# https://download.pytorch.org/whl/cu128）或提前自行安装 torch。
TORCH_INDEX="${GOAI_TORCH_INDEX:-https://download.pytorch.org/whl/cpu}"

if command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
elif [[ -x "$ROOT/.cache/uv-bootstrap/bin/uv" ]]; then
  UV_BIN="$ROOT/.cache/uv-bootstrap/bin/uv"
else
  PY_BOOTSTRAP=python3
  echo "==> 在仓库 .cache 中引导 uv"
  UV_BOOTSTRAP_DIR="$ROOT/.cache/uv-bootstrap"
  mkdir -p "$UV_BOOTSTRAP_DIR"
  "$PY_BOOTSTRAP" -m pip install -q --upgrade --target "$UV_BOOTSTRAP_DIR" uv
  UV_BIN="$UV_BOOTSTRAP_DIR/bin/uv"
fi

# 选一个 >=3.10 的解释器；系统只有旧 python（如 macOS 自带 3.9）时让 uv 下载托管的 3.11，
# 不能把 3.9 拿来建 venv（pyproject 要求 >=3.10，后续步骤也会因缺模块中断）
PY=""
for cand in python3.11 python3.12 python3.10 python3; do
  if command -v "$cand" >/dev/null 2>&1 &&
     "$cand" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
    PY="$cand"
    break
  fi
done
if [[ -n "$PY" ]]; then
  echo "==> 用 $UV_BIN 建 .venv（$($PY -c 'import platform; print(platform.python_version())')）"
  "$UV_BIN" venv --allow-existing --python "$PY" .venv
else
  echo "==> 系统无 >=3.10 的 Python，用 uv 托管的 CPython 3.11 建 .venv"
  "$UV_BIN" venv --allow-existing --python 3.11 .venv
fi

if [ "$WITH_RETRO" = "0" ]; then
  "$UV_BIN" sync --frozen --extra dev --python .venv/bin/python
else
  # PyPI's Linux torch wheel pulls several GiB of CUDA libraries.  Install the
  # matching locked torch release from the selected CPU/GPU index, then apply
  # every remaining version from uv.lock as a constraints file.
  # 从 uv.lock 取锁定的 torch 版本：纯 awk，不依赖 tomllib（3.11+）也不依赖系统 python 版本
  TORCH_VERSION=$(awk '/^\[\[package\]\]/{p=0} /^name = "torch"$/{p=1} p && /^version = /{gsub(/"/,"",$3); print $3; exit}' uv.lock)
  if [[ -z "$TORCH_VERSION" ]]; then echo "无法从 uv.lock 读取 torch 版本" >&2; exit 1; fi
  echo "==> 安装锁定的 torch ${TORCH_VERSION}（${TORCH_INDEX}）"
  "$UV_BIN" pip install --python .venv/bin/python \
    "torch==$TORCH_VERSION" --index-url "$TORCH_INDEX"
  RETRO_REQUIREMENTS="$(mktemp)"
  RETRO_LOCKED_REQUIREMENTS="$(mktemp)"
  trap 'rm -f "$RETRO_REQUIREMENTS" "$RETRO_LOCKED_REQUIREMENTS"' EXIT
  "$UV_BIN" export --frozen --extra dev --extra retro --no-hashes \
    --no-emit-project --output-file "$RETRO_REQUIREMENTS" >/dev/null
  # The selected torch index owns torch and its platform dependencies.  Install
  # every other direct/transitive dependency exactly as pinned by uv.lock.
  grep -Ev '^(torch|triton|nvidia-[^=]+)==' "$RETRO_REQUIREMENTS" \
    > "$RETRO_LOCKED_REQUIREMENTS"
  "$UV_BIN" pip install --python .venv/bin/python \
    --requirement "$RETRO_LOCKED_REQUIREMENTS"
  "$UV_BIN" pip install --python .venv/bin/python --no-deps -e .
  "$UV_BIN" pip check --python .venv/bin/python
fi
echo "==> 依赖就绪：$(.venv/bin/python -c 'import mcp,httpx;print("mcp",mcp.__file__.split("/")[-2],"ok")' 2>&1)"

# ---- 2. 生成填好绝对路径的 MCP 配置 ----
EMAIL="${GOAI_EMAIL:-goai-research@example.com}"
sed -e "s|/ABSOLUTE/PATH/TO/goai_research|$ROOT|g" \
    -e "s|you@example.com|$EMAIL|g" \
    configs/codex.config.toml.example > configs/codex.config.toml
sed -e "s|/ABSOLUTE/PATH/TO/goai_research|$ROOT|g" \
    -e "s|you@example.com|$EMAIL|g" \
    configs/claude.mcp.json.example > configs/claude.mcp.json
echo "==> 已生成 configs/codex.config.toml 与 configs/claude.mcp.json"

# ---- 3. workspace 骨架 ----
mkdir -p workspace/{library/pdfs,notes,memory,style_bank/{pdfs,exemplar_figures},figures/{svg,drawio,figspec,assets,candidates},drafts/sections,ideas,state/{parallel,review_traces}}

# ---- 4. 统一冒烟：绑定仓库 .venv，避免系统 Python 依赖误报 ----
PREFLIGHT_ARGS=(--servers)
if [ "$WITH_RETRO" = "1" ]; then
  PREFLIGHT_ARGS+=(--retro)
fi
.venv/bin/python tools/preflight.py "${PREFLIGHT_ARGS[@]}"

# ---- 5. 安装收据：机器、解释器和关键依赖版本 -------------------------------
mkdir -p "$ROOT/.cache"
.venv/bin/python - "$ROOT/.cache/install-receipt.json" "$UV_BIN" "$WITH_RETRO" <<'PY'
import datetime as dt
import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

out, uv_bin, with_retro = Path(sys.argv[1]), sys.argv[2], sys.argv[3] == "1"
packages = ["goai-research", "duckdb", "httpx", "mcp", "pytest"]
if with_retro:
    packages += ["numpy", "pandas", "pymatgen", "torch"]
versions = {}
for package in packages:
    try:
        versions[package] = importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        versions[package] = None

def command_version(command):
    if not shutil.which(command[0]):
        return None
    return subprocess.run(command, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, check=False).stdout.strip()

receipt = {
    "installed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "python": platform.python_version(),
    "platform": platform.platform(),
    "uv": command_version([uv_bin, "--version"]),
    "codex": command_version(["codex", "--version"]),
    "with_retro": with_retro,
    "packages": versions,
    "uv_lock_sha256": hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest(),
}
out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
               encoding="utf-8")
print(f"==> 安装收据：{out}")
PY

cat <<EOF

安装完成。接下来：
  Codex : cat configs/codex.config.toml >> ~/.codex/config.toml
          ln -s "$ROOT/skills"/goai-* ~/.codex/skills/
  Claude: 把 configs/claude.mcp.json 合进 ~/.claude.json 的 mcpServers
          ln -s "$ROOT/skills"/goai-* ~/.claude/skills/
  测试  : .venv/bin/python -m pytest tests/ -q
可选增强：brew install --cask drawio（图导出 png/pdf）；
          .venv/bin/pip install -e '.[preview]'（图纸自检出 png）；
          bash install.sh --retro（安装本地无机两步模型所需依赖；torch 默认 CPU 轮子，
          GPU 请设 GOAI_TORCH_INDEX）
  Dry run: .venv/bin/python tools/retro_dry_run.py   （加载 checkpoint 并预测一个目标）
EOF
