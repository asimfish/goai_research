#!/usr/bin/env bash
# Build the two official submission archives, with official-category folders
# at the zip root and a short index README.
#
#   bash scripts/package_submission.sh "科学无极" [作品名]
#
# Produces in dist/:
#   AI4R_MAT_<队伍名>_<作品名>_非代码材料.zip
#   AI4R_MAT_<队伍名>_<作品名>_代码材料.zip
#   AI4R_MAT_<队伍名>_<作品名>_非代码材料_PPT.{pptx,pdf}
set -euo pipefail
cd "$(dirname "$0")/.."
TEAM="${1:?usage: package_submission.sh <队伍名> [作品名]}"
WORK="${2:-SAGE-Mat}"
PREFIX="AI4R_MAT_${TEAM}_${WORK}"
FINAL=submission/goai_final
mkdir -p dist

COMMIT="$(git rev-parse HEAD)"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "WARNING: working tree has uncommitted changes; VERSION will record $COMMIT plus 'dirty'" >&2
  echo "$COMMIT dirty" > $FINAL/VERSION
else
  echo "$COMMIT" > $FINAL/VERSION
fi
git describe --tags --exact-match 2>/dev/null >> $FINAL/VERSION || true

.venv/bin/python tools/export_submission_bundle.py --sanitize-only --out "$FINAL"

NONCODE="dist/${PREFIX}_非代码材料.zip"
CODE="dist/${PREFIX}_代码材料.zip"
rm -f "$NONCODE" "$CODE"

STAGE="$(mktemp -d)"
cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT

README="$FINAL/README.md"
cp "$README" "$STAGE/README.md"
cp "$FINAL/VERSION" "$STAGE/VERSION"
cp "$FINAL/MANIFEST.sha256" "$STAGE/MANIFEST.sha256"

# ---- non-code: official folders at zip root --------------------------------
NC="$STAGE/noncode"
mkdir -p "$NC/方案说明PPT" "$NC/复赛报告/正式综述" "$NC/研究数据与证据包" "$NC/运行与评测包"
cp "$STAGE/README.md" "$NC/README.md"
cp "$STAGE/VERSION" "$NC/VERSION"
cp "$STAGE/MANIFEST.sha256" "$NC/MANIFEST.sha256"
cp "$FINAL"/deck/*.pptx "$FINAL"/deck/*.pdf "$NC/方案说明PPT/" 2>/dev/null || true
cp "$FINAL"/report_docx/* "$NC/复赛报告/"
cp -a "$FINAL/report/." "$NC/复赛报告/正式综述/"
cp -a "$FINAL/evidence/." "$NC/研究数据与证据包/"
cp -a "$FINAL/run" "$NC/运行与评测包/正式案例"
cp -a "$FINAL/run_llzo" "$NC/运行与评测包/LLZO诊断轮"
if [[ -d "$FINAL/runs_20260903" ]]; then
  cp -a "$FINAL/runs_20260903" "$NC/运行与评测包/补充案例_20260903"
fi
( cd "$NC" && zip -q -r "$OLDPWD/$NONCODE" . -x '*.pyc' -x '*/__pycache__/*' )

for f in "$FINAL"/deck/*.pptx "$FINAL"/deck/*.pdf; do
  [[ -f "$f" ]] || continue
  ext="${f##*.}"
  cp "$f" "dist/${PREFIX}_非代码材料_PPT.${ext}"
done

# ---- code: official numbered folders at zip root ---------------------------
CD="$STAGE/code"
mkdir -p \
  "$CD/01_系统复现包/goai_research/submission/goai_final" \
  "$CD/01_系统复现包/构筑阶段轨迹" \
  "$CD/02_研究数据与证据包" \
  "$CD/03_运行与评测包/运行阶段轨迹" \
  "$CD/04_指标与分析代码" \
  "$CD/05_README与一键命令"
cp "$STAGE/README.md" "$CD/README.md"
cp "$STAGE/VERSION" "$CD/VERSION"
cp "$STAGE/MANIFEST.sha256" "$CD/MANIFEST.sha256"

REPO="$CD/01_系统复现包/goai_research"
# Working-tree snapshot so uncommitted title/README updates are in the package.
rsync -a \
  --exclude '.git/' --exclude 'dist/' --exclude '.venv/' --exclude '.venv-retro/' \
  --exclude 'workspace/' --exclude '__pycache__/' --exclude '*.pyc' \
  --exclude '.pytest_cache/' --exclude '.cache/' \
  --exclude 'submission/goai_final/run/' \
  --exclude 'submission/goai_final/run_llzo/' \
  --exclude 'submission/goai_final/runs_20260903/' \
  --exclude 'submission/goai_final/traces/' \
  --exclude 'submission/goai_final/deck/' \
  --exclude 'submission/goai_final/report/' \
  --exclude 'submission/goai_final/report_docx/' \
  ./ "$REPO/"

if [[ -d "$FINAL/traces/development" ]]; then
  cp -a "$FINAL/traces/development/." "$CD/01_系统复现包/构筑阶段轨迹/"
fi
[[ -f "$FINAL/traces/codex_sessions_index.json" ]] && \
  cp "$FINAL/traces/codex_sessions_index.json" "$CD/01_系统复现包/"

cp -a "$FINAL/evidence/." "$CD/02_研究数据与证据包/"
cp -a "$FINAL/run" "$CD/03_运行与评测包/正式案例"
cp -a "$FINAL/run_llzo" "$CD/03_运行与评测包/LLZO诊断轮"
if [[ -d "$FINAL/runs_20260903" ]]; then
  cp -a "$FINAL/runs_20260903" "$CD/03_运行与评测包/补充案例_20260903"
fi
if [[ -d "$FINAL/traces/runtime_native_sessions" ]]; then
  cp -a "$FINAL/traces/runtime_native_sessions" "$CD/03_运行与评测包/运行阶段轨迹/"
fi
cp -a "$FINAL/report" "$CD/03_运行与评测包/最终输出"
cp -a "$FINAL/metrics/." "$CD/04_指标与分析代码/"
mkdir -p "$CD/04_指标与分析代码/tools" "$CD/04_指标与分析代码/checkpoint_summaries"
for t in build_claim_evidence.py analyze_agent_traces.py bib_guard.py tex_guard.py academic_language_guard.py retro_dry_run.py; do
  [[ -f tools/$t ]] && cp "tools/$t" "$CD/04_指标与分析代码/tools/"
done
cp vendor/two_stage_retro/checkpoints/*_summary.json "$CD/04_指标与分析代码/checkpoint_summaries/" 2>/dev/null || true

cp "$README" "$CD/05_README与一键命令/README.md"
cp docs/competition/SUBMISSION.md "$CD/05_README与一键命令/"
cp install.sh "$CD/05_README与一键命令/"
mkdir -p "$CD/05_README与一键命令/scripts"
cp scripts/smoke_test.sh scripts/reproduce_core.sh "$CD/05_README与一键命令/scripts/"

( cd "$CD" && zip -q -r "$OLDPWD/$CODE" . -x '*.pyc' -x '*/__pycache__/*' )

echo "built:"; ls -la dist/
echo "commit: $(cat $FINAL/VERSION)"
echo "---- zip roots ----"
unzip -l "$NONCODE" | awk '{print $4}' | awk -F/ 'NF<=2 && $0!=""' | head -30
echo "..."
unzip -l "$CODE" | awk '{print $4}' | awk -F/ 'NF<=2 && $0!=""' | head -40
sha256sum dist/*.zip dist/*_PPT.pptx dist/*_PPT.pdf 2>/dev/null || sha256sum dist/*.zip
