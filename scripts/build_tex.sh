#!/usr/bin/env bash
# 一键编译终稿：xelatex → bibtex → xelatex ×2 → pdf_guard。只允许 TeX 路径；缺工具链即失败退出。
# 用法：bash scripts/build_tex.sh <draft_dir> [main]
set -uo pipefail
cd "$(dirname "$0")/.."
REPO="$(pwd)"
DIR="${1:?用法: scripts/build_tex.sh <draft_dir> [main]}"
JOB="${2:-main}"
PY=".venv/bin/python"; [[ -x "$PY" ]] || PY="python3"
if ! command -v xelatex >/dev/null 2>&1; then
  if command -v tectonic >/dev/null 2>&1; then
    echo "xelatex 不可用，使用 tectonic（同为 XeTeX 引擎）" >&2
    ( cd "$DIR" && tectonic -X compile "$JOB.tex" --keep-logs --keep-intermediates ) || { echo "tectonic 编译失败" >&2; exit 1; }
  else
    echo "FAIL-CLOSED: 没有 xelatex/tectonic。draft_complete 只能记 FAIL，交付 main.tex+bib+figures 并写明『PDF 未编译』；禁止用回退渲染器。" >&2
    exit 2
  fi
else
  rm -f "$DIR/$JOB.aux" "$DIR/$JOB.bbl" "$DIR/$JOB.blg" "$DIR/$JOB.out"   # 干净构建：旧 bbl 会让首遍编译在陈旧条目上中止
  ( cd "$DIR" \
    && xelatex -interaction=nonstopmode -halt-on-error "$JOB.tex" >/dev/null \
    && bibtex "$JOB" >/dev/null \
    && xelatex -interaction=nonstopmode -halt-on-error "$JOB.tex" >/dev/null \
    && xelatex -interaction=nonstopmode -halt-on-error "$JOB.tex" >/dev/null ) \
    || { echo "编译失败，见 $DIR/$JOB.log（rg '^!' 定位）" >&2; exit 1; }
fi
echo "编译完成: $DIR/$JOB.pdf  页数=$(pdfinfo "$DIR/$JOB.pdf" 2>/dev/null | awk '/Pages/{print $2}')  Overfull=$(rg -c Overfull "$DIR/$JOB.log" 2>/dev/null || echo 0)"
BIB="$DIR/references.bib"; [[ -f "$BIB" ]] || BIB=""
"$PY" tools/pdf_guard.py "$DIR/$JOB.pdf" --tex "$DIR/$JOB.tex" ${BIB:+--bib "$BIB"}
