#!/usr/bin/env bash
# Build the two official submission archives from submission/ (already laid out
# in the official deliverable folders) plus a snapshot of this repository.
#
#   bash scripts/package_submission.sh "科学无极" [作品名] [--allow-incomplete]
#
# Packaging refuses unless every run ledger under 03_运行与评测包 passes
# `loopctl check-done` (all required gates recorded PASS/WARN, no open blocker/major,
# receipts and PDF still valid). `--allow-incomplete` packages anyway and records a
# WARN line naming the failing workspaces in MANIFEST.sha256.
#
# Produces in dist/:
#   AI4R_MAT_<队伍名>_<作品名>_非代码材料.zip
#       README.md · 方案说明PPT/ · 复赛报告/ · 研究数据与证据包/ · 运行与评测包/ · VERSION · MANIFEST.sha256
#   AI4R_MAT_<队伍名>_<作品名>_代码材料.zip
#       README.md · 01_系统复现包/{goai_research/ (repo snapshot), 构筑阶段轨迹/, codex_sessions_index.json}
#       · 02_研究数据与证据包/ · 03_运行与评测包/ · 04_指标与分析代码/ · 05_README与一键命令/ · VERSION · MANIFEST.sha256
#   AI4R_MAT_<队伍名>_<作品名>_非代码材料_PPT.{pptx,pdf}
set -euo pipefail
cd "$(dirname "$0")/.."
ALLOW_INCOMPLETE=0
POS=()
for arg in "$@"; do
  case "$arg" in
    --allow-incomplete) ALLOW_INCOMPLETE=1 ;;
    *) POS+=("$arg") ;;
  esac
done
set -- ${POS[@]+"${POS[@]}"}
TEAM="${1:?usage: package_submission.sh <队伍名> [作品名] [--allow-incomplete]}"
WORK="${2:-SAGE-Mat}"
PREFIX="AI4R_MAT_${TEAM}_${WORK}"
SUB=submission
PY="${PY:-.venv/bin/python}"
mkdir -p dist

# Run `loopctl check-done` against a copy of every ledger under <dir> (check-done rewrites
# stale gates, so the shipped ledger itself is never touched). Prints one line per failing
# workspace; returns 1 when any fails or when no ledger exists at all.
check_ledgers_done() {
  local root="$1" fails=0 found=0 ledger ws tmp
  while IFS= read -r -d '' ledger; do
    found=$((found + 1))
    ws="$(dirname "$ledger")"; [[ "$(basename "$ws")" == "state" ]] && ws="$(dirname "$ws")"
    tmp="$(mktemp -d)"; mkdir -p "$tmp/state"; cp "$ledger" "$tmp/state/ledger.json"
    if ! GOAI_WORKSPACE="$tmp" "$PY" tools/loopctl.py check-done > "$tmp/check_done.log" 2>&1; then
      echo "check-done FAIL: $ws"; tail -3 "$tmp/check_done.log" | cut -c1-400; fails=$((fails + 1))
    fi
    rm -rf "$tmp"
  done < <(find "$root" -type f -name ledger.json -print0 | sort -z)
  if [[ "$found" -eq 0 ]]; then echo "check-done FAIL: no ledger.json under $root"; return 1; fi
  [[ "$fails" -eq 0 ]]
}

COMMIT="$(git rev-parse HEAD)"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "WARNING: working tree has uncommitted changes; VERSION will record $COMMIT plus 'dirty'" >&2
  echo "$COMMIT dirty" > $SUB/VERSION
else
  echo "$COMMIT" > $SUB/VERSION
fi
git describe --tags --exact-match 2>/dev/null >> $SUB/VERSION || true

# Fail closed before packaging: every manuscript PDF that ships in 运行与评测包 must be a
# TeX build of its sources (tools/pdf_guard.py). A non-TeX render (browser/office
# printing), a stale PDF, or a PDF without an abstract block / numbered headings fails
# packaging here rather than reaching the judges. Figure PDFs and slide decks are not
# manuscripts and are skipped.
PDF_FAIL=0
while IFS= read -r -d '' pdf; do
  case "$pdf" in */figures/*|*/figspec/*|*PPT*|*方案说明*) continue ;; esac
  dir="$(dirname "$pdf")"; base="$(basename "$pdf" .pdf)"
  tex=""; [[ -f "$dir/$base.tex" ]] && tex="$dir/$base.tex"
  bib=""; [[ -f "$dir/references.bib" ]] && bib="$dir/references.bib"
  if ! .venv/bin/python tools/pdf_guard.py "$pdf" ${tex:+--tex "$tex"} ${bib:+--bib "$bib"} >/tmp/pdf_guard_pkg.log 2>&1; then
    echo "PDF 未通过 pdf_guard，拒绝打包: $pdf" >&2; tail -8 /tmp/pdf_guard_pkg.log >&2; PDF_FAIL=1
  fi
done < <(find "$SUB/03_运行与评测包" -type f -name '*.pdf' -print0)
[[ "$PDF_FAIL" -eq 0 ]] || { echo "存在非 TeX/陈旧/缺摘要的稿件 PDF，先按 scripts/build_tex.sh 重编再打包。" >&2; exit 3; }

# Fail closed before packaging: every packaged run must be complete by the ledger's own
# rules (loopctl check-done). --allow-incomplete records the debt in the manifest instead.
LEDGER_WARN=""
if ! LEDGER_REPORT="$(check_ledgers_done "$SUB/03_运行与评测包")"; then
  echo "$LEDGER_REPORT" >&2
  if [[ "$ALLOW_INCOMPLETE" -eq 1 ]]; then
    LEDGER_WARN="# WARN: packaged with --allow-incomplete; loopctl check-done failed for: $(printf '%s\n' "$LEDGER_REPORT" | grep '^check-done FAIL' | sed 's/^check-done FAIL: //' | tr '\n' ';')"
    echo "$LEDGER_WARN" >&2
  else
    echo "存在未通过 loopctl check-done 的运行账本，拒绝打包（确需打包用 --allow-incomplete，会在 MANIFEST 记 WARN）。" >&2
    exit 4
  fi
fi

# Fail closed before packaging: scrub secrets/private paths, normalize every
# JSONL stream, validate all structured files, refresh MANIFEST.sha256.
.venv/bin/python tools/export_submission_bundle.py --sanitize-only --out "$SUB"
[[ -z "$LEDGER_WARN" ]] || echo "$LEDGER_WARN" >> "$SUB/MANIFEST.sha256"

NONCODE="dist/${PREFIX}_非代码材料.zip"
CODE="dist/${PREFIX}_代码材料.zip"
rm -f "$NONCODE" "$CODE"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

# ---- non-code archive --------------------------------------------------------
NC="$STAGE/noncode"
mkdir -p "$NC"
cp "$SUB/README.md" "$SUB/VERSION" "$SUB/MANIFEST.sha256" "$NC/"
cp -a "$SUB/方案说明PPT"          "$NC/方案说明PPT"
cp -a "$SUB/复赛报告"             "$NC/复赛报告"
cp -a "$SUB/02_研究数据与证据包"   "$NC/研究数据与证据包"
cp -a "$SUB/03_运行与评测包"       "$NC/运行与评测包"
( cd "$NC" && zip -q -r "$OLDPWD/$NONCODE" . -x '*.pyc' -x '*/__pycache__/*' )

for f in "$SUB"/方案说明PPT/*.pptx "$SUB"/方案说明PPT/*.pdf; do
  [[ -f "$f" ]] || continue
  cp "$f" "dist/${PREFIX}_非代码材料_PPT.${f##*.}"
done

# ---- code archive ------------------------------------------------------------
CD="$STAGE/code"
mkdir -p "$CD/01_系统复现包" "$CD/05_README与一键命令/scripts"
cp "$SUB/README.md" "$SUB/VERSION" "$SUB/MANIFEST.sha256" "$CD/"

# Repository snapshot (working tree, so an uncommitted packaging fix is included);
# the large run/trace/deck folders live in their own numbered folders instead.
rsync -a \
  --exclude '.git/' --exclude 'dist/' --exclude '.venv/' --exclude '.venv-retro/' \
  --exclude 'workspace/' --exclude 'workspace_live/' --exclude 'workspace_repro_*/' --exclude 'workspace_runs/' \
  --exclude '__pycache__/' --exclude '*.pyc' --exclude '.pytest_cache/' --exclude '.cache/' \
  --exclude '*.egg-info/' --exclude '*.jsonl.lock' \
  --exclude 'submission/03_运行与评测包/' --exclude 'submission/方案说明PPT/' --exclude 'submission/复赛报告/' \
  --exclude 'submission/01_系统复现包/构筑阶段轨迹/' \
  ./ "$CD/01_系统复现包/goai_research/"
cat > "$CD/01_系统复现包/goai_research/submission/PACKAGE_NOTE.md" <<'NOTE'
# 归档说明

本目录是代码材料压缩包内的仓库快照。为避免重复打包，以下内容没有放在这里，
而是位于压缩包根目录（与 `goai_research/` 平级）：

- `submission/01_系统复现包/构筑阶段轨迹/` → 压缩包根 `01_系统复现包/构筑阶段轨迹/`
- `submission/03_运行与评测包/` → 压缩包根 `03_运行与评测包/`
- `submission/方案说明PPT/`、`submission/复赛报告/` → 非代码材料压缩包

GitHub 仓库 <https://github.com/asimfish/goai_research> 中这些目录均在原位；
`docs/competition/SUBMISSION.md` 里的路径以仓库布局为准。
NOTE
cp -a "$SUB/01_系统复现包/构筑阶段轨迹"        "$CD/01_系统复现包/构筑阶段轨迹"
cp    "$SUB/01_系统复现包/codex_sessions_index.json" "$SUB/01_系统复现包/README.md" "$CD/01_系统复现包/"
cp -a "$SUB/02_研究数据与证据包"  "$CD/02_研究数据与证据包"
cp -a "$SUB/03_运行与评测包"      "$CD/03_运行与评测包"
cp -a "$SUB/04_指标与分析代码"    "$CD/04_指标与分析代码"
mkdir -p "$CD/04_指标与分析代码/tools"
for t in build_claim_evidence.py analyze_agent_traces.py bib_guard.py tex_guard.py academic_language_guard.py retro_dry_run.py; do
  cp "tools/$t" "$CD/04_指标与分析代码/tools/"
done
cp "$SUB/README.md" docs/competition/SUBMISSION.md install.sh "$CD/05_README与一键命令/"
cp scripts/smoke_test.sh scripts/reproduce_core.sh "$CD/05_README与一键命令/scripts/"
( cd "$CD" && zip -q -r "$OLDPWD/$CODE" . -x '*.pyc' -x '*/__pycache__/*' )

echo "built:"; ls -la dist/
echo "commit: $(cat $SUB/VERSION)"
echo "---- zip roots ----"
unzip -Z1 "$NONCODE" | awk -F/ '{print $1}' | sort -u
echo "..."
unzip -Z1 "$CODE" | awk -F/ '{print $1}' | sort -u
sha256sum dist/*.zip dist/*_PPT.*
