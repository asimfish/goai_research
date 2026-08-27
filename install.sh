#!/usr/bin/env bash
# goai_research 安装：建 venv、装依赖、生成填好绝对路径的 MCP 配置。
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"

echo "==> goai_research install @ $ROOT"

# ---- 1. Python >=3.10 的 venv（优先 uv，其次系统 python3）----
if command -v uv >/dev/null 2>&1; then
  echo "==> 用 uv 建 .venv（Python 3.11）"
  uv venv --python 3.11 .venv 2>/dev/null || uv venv .venv
  uv pip install --python .venv/bin/python -e .
else
  PY=python3
  V=$($PY -c 'import sys;print(sys.version_info>=(3,10))')
  if [ "$V" != "True" ]; then
    for cand in python3.12 python3.11 python3.10; do
      command -v $cand >/dev/null 2>&1 && PY=$cand && break
    done
  fi
  echo "==> 用 $PY 建 .venv"
  $PY -m venv .venv
  .venv/bin/pip install -q -U pip
  .venv/bin/pip install -q -e .
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
mkdir -p workspace/{library/pdfs,notes,memory,figures/{svg,drawio,figspec,assets},drafts/sections,ideas,state/{parallel,review_traces}}

# ---- 4. 冒烟：四个 server 能 import ----
for s in litsearch refcheck figure retro; do
  .venv/bin/python -c "import importlib.util,sys; \
spec=importlib.util.spec_from_file_location('m','server/${s}_server.py'); \
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print('  server/${s}_server.py OK')" \
  || { echo "  server/${s}_server.py FAILED"; exit 1; }
done

cat <<EOF

安装完成。接下来：
  Codex : cat configs/codex.config.toml >> ~/.codex/config.toml
          ln -s "$ROOT/skills"/goai-* ~/.codex/skills/
  Claude: 把 configs/claude.mcp.json 合进 ~/.claude.json 的 mcpServers
          ln -s "$ROOT/skills"/goai-* ~/.claude/skills/
  测试  : .venv/bin/python -m pytest tests/ -q
可选增强：brew install --cask drawio（图导出 png/pdf）；
          .venv/bin/pip install -e '.[preview]'（图纸自检出 png）
EOF
