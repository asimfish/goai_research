#!/usr/bin/env bash
# 一键编译终稿：bib_enrich（可选，需网络）→ bib_polish → xelatex → bibtex → xelatex ×2 → pdf_guard。
# 只允许 TeX 路径；缺工具链即失败退出。编译日志里出现 Missing character（字族排不出的字形，
# 出货稿里是 U+0410 西里尔 А 与 U+2212 减号印成缺字）同样失败。
# 用法：bash scripts/build_tex.sh <draft_dir> [main]
#   GOAI_OFFLINE=1 跳过 bib_enrich（Crossref 补卷期页码）；bib_enrich 失败只记录、不阻塞。
set -uo pipefail
cd "$(dirname "$0")/.."
REPO="$(pwd)"
DIR="${1:?用法: scripts/build_tex.sh <draft_dir> [main]}"
JOB="${2:-main}"
PY=".venv/bin/python"; [[ -x "$PY" ]] || PY="python3"
BIB="$DIR/references.bib"; [[ -f "$BIB" ]] || BIB=""

# 参考文献先补齐再清理：bib_enrich 只补缺（卷/期/页码、年份统一为出版年），要走 Crossref；
# bib_polish 是离线确定性卫生（删冗余 url、化学式下标与大小写保护、同形字母告警）
if [[ -n "$BIB" ]]; then
  if [[ "${GOAI_OFFLINE:-0}" == "1" ]]; then
    echo "bib_enrich 跳过（GOAI_OFFLINE=1，离线不查 Crossref）" >&2
  elif ! "$PY" tools/bib_enrich.py "$BIB" --write --fix-year > "$DIR/bib_enrich.log" 2>&1; then
    echo "bib_enrich 未完成（网络不可用或部分 DOI 查不到，见 $DIR/bib_enrich.log）——继续编译" >&2
  fi
  "$PY" tools/bib_polish.py "$BIB" --write | tail -3
fi

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
MISSING="$(grep -c 'Missing character' "$DIR/$JOB.log" 2>/dev/null || true)"; MISSING="${MISSING:-0}"
echo "编译完成: $DIR/$JOB.pdf  页数=$(pdfinfo "$DIR/$JOB.pdf" 2>/dev/null | awk '/Pages/{print $2}')  Overfull=$(grep -c Overfull "$DIR/$JOB.log" 2>/dev/null || echo 0)  MissingChar=$MISSING"
if [[ "$MISSING" -gt 0 ]]; then
  echo "FAIL: 编译日志有 $MISSING 处 Missing character（字族排不出的字形会印成空白/缺字）：" >&2
  grep 'Missing character' "$DIR/$JOB.log" | sort | uniq -c | sort -rn | head -8 >&2
  echo "定位：bib_polish --strict 查同形字母；正文的 −/≤/→ 等符号改用数学模式或模板字体覆盖的写法" >&2
  exit 1
fi
"$PY" tools/pdf_guard.py "$DIR/$JOB.pdf" --tex "$DIR/$JOB.tex" ${BIB:+--bib "$BIB"}
