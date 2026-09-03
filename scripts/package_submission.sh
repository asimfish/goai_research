#!/usr/bin/env bash
# Build the two official submission archives from submission/ (already laid out
# in the official deliverable folders) plus a snapshot of this repository.
#
#   bash scripts/package_submission.sh "科学无极" [作品名]
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
TEAM="${1:?usage: package_submission.sh <队伍名> [作品名]}"
WORK="${2:-SAGE-Mat}"
PREFIX="AI4R_MAT_${TEAM}_${WORK}"
SUB=submission
mkdir -p dist

COMMIT="$(git rev-parse HEAD)"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "WARNING: working tree has uncommitted changes; VERSION will record $COMMIT plus 'dirty'" >&2
  echo "$COMMIT dirty" > $SUB/VERSION
else
  echo "$COMMIT" > $SUB/VERSION
fi
git describe --tags --exact-match 2>/dev/null >> $SUB/VERSION || true

# Fail closed before packaging: scrub secrets/private paths, normalize every
# JSONL stream, validate all structured files, refresh MANIFEST.sha256.
.venv/bin/python tools/export_submission_bundle.py --sanitize-only --out "$SUB"

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
