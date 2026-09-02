#!/usr/bin/env bash
# goai_research 安装：建 venv、装依赖、生成填好绝对路径的 MCP 配置。
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"

WITH_RETRO=0
if [ "${1:-}" = "--retro" ] || [ "${GOAI_INSTALL_RETRO:-0}" = "1" ]; then
  WITH_RETRO=1
fi
INSTALL_SPEC=".[dev]"
if [ "$WITH_RETRO" = "1" ]; then
  INSTALL_SPEC=".[dev,retro]"
fi

echo "==> goai_research install @ $ROOT"

# ---- 1. Python >=3.10 的 venv（优先 uv，其次系统 python3；最后本地引导 uv）----
# retro 依赖里的 torch 默认从 CPU 轮子源安装（约 200 MB），避免默认 PyPI 拉取
# 2.5 GB 的 CUDA 轮子；需要 GPU 时设 GOAI_TORCH_INDEX（如
# https://download.pytorch.org/whl/cu128）或提前自行安装 torch。
TORCH_SPEC="torch>=2.2,<2.8"
TORCH_INDEX="${GOAI_TORCH_INDEX:-https://download.pytorch.org/whl/cpu}"

if command -v uv >/dev/null 2>&1; then
  echo "==> 用 uv 建 .venv（Python 3.11）"
  uv venv --python 3.11 .venv 2>/dev/null || uv venv .venv
  if [ "$WITH_RETRO" = "1" ]; then
    echo "==> 安装 torch（$TORCH_INDEX）"
    uv pip install --python .venv/bin/python "$TORCH_SPEC" --index-url "$TORCH_INDEX"
  fi
  uv pip install --python .venv/bin/python -e "$INSTALL_SPEC"
else
  PY=python3
  V=$($PY -c 'import sys;print(sys.version_info>=(3,10))')
  if [ "$V" != "True" ]; then
    for cand in python3.12 python3.11 python3.10; do
      command -v $cand >/dev/null 2>&1 && PY=$cand && break
    done
  fi
  echo "==> 用 $PY 建 .venv"
  if $PY -m venv .venv; then
    .venv/bin/pip install -q -U pip
    if [ "$WITH_RETRO" = "1" ]; then
      echo "==> 安装 torch（$TORCH_INDEX）"
      .venv/bin/pip install -q "$TORCH_SPEC" --index-url "$TORCH_INDEX"
    fi
    .venv/bin/pip install -q -e "$INSTALL_SPEC"
  else
    echo "==> 系统缺少venv/ensurepip；在仓库.cache中引导uv"
    UV_BOOTSTRAP="$ROOT/.cache/uv-bootstrap"
    mkdir -p "$UV_BOOTSTRAP"
    $PY -m pip install -q --upgrade --target "$UV_BOOTSTRAP" uv
    "$UV_BOOTSTRAP/bin/uv" venv --allow-existing --python "$PY" .venv
    if [ "$WITH_RETRO" = "1" ]; then
      "$UV_BOOTSTRAP/bin/uv" pip install --python .venv/bin/python "$TORCH_SPEC" --index-url "$TORCH_INDEX"
    fi
    "$UV_BOOTSTRAP/bin/uv" pip install --python .venv/bin/python -e "$INSTALL_SPEC"
  fi
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
