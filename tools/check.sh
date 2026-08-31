#!/usr/bin/env bash
# Always validate with the repository environment, never an ambient system Python.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then
  echo "仓库 .venv 不存在；请先运行 bash install.sh" >&2
  exit 2
fi
exec .venv/bin/python tools/preflight.py "$@"
