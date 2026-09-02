#!/usr/bin/env bash
# Build the two official submission archives.
#
#   bash scripts/package_submission.sh "<队伍名>" [作品名]
#
# Produces in dist/:
#   AI4R_MAT_<队伍名>_<作品名>_非代码材料.zip   deck + report docx + evidence + run + run_llzo (+ SUBMISSION.md)
#   AI4R_MAT_<队伍名>_<作品名>_代码材料.zip     git snapshot of the repository (tracked files) + traces + metrics
# and writes submission/goai_final/VERSION with the exact commit hash first.
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

# refresh the SHA manifest so it covers deck/, report_docx/ and VERSION
.venv/bin/python - <<'PY'
import hashlib, pathlib
root = pathlib.Path("submission/goai_final")
lines = []
for p in sorted(root.rglob("*")):
    if p.is_file() and p.name != "MANIFEST.sha256":
        lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}")
(root / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("manifest entries:", len(lines))
PY

NONCODE="dist/${PREFIX}_非代码材料.zip"
CODE="dist/${PREFIX}_代码材料.zip"
rm -f "$NONCODE" "$CODE"

# ---- non-code archive ----------------------------------------------------------------
zip -q -r "$NONCODE" \
  $FINAL/deck $FINAL/report_docx $FINAL/report $FINAL/evidence $FINAL/run $FINAL/run_llzo \
  $FINAL/README.md $FINAL/MANIFEST.sha256 $FINAL/VERSION docs/competition/SUBMISSION.md \
  -x '*.pyc' -x '*/__pycache__/*'
# PPT must also be discoverable by its own prefixed name
for f in $FINAL/deck/*.pptx $FINAL/deck/*.pdf; do
  [[ -f "$f" ]] || continue
  ext="${f##*.}"; cp "$f" "dist/${PREFIX}_非代码材料_PPT.${ext}"
done

# ---- code archive: exactly the tracked tree at $COMMIT plus the trace/metric folders ---
TMP="$(mktemp -d)"
git archive --format=tar --prefix=goai_research/ "$COMMIT" | tar -x -C "$TMP"
mkdir -p "$TMP/goai_research/$FINAL"
cp -r $FINAL/traces $FINAL/metrics $FINAL/MANIFEST.sha256 $FINAL/VERSION $FINAL/README.md "$TMP/goai_research/$FINAL/"
cp -r $FINAL/evidence "$TMP/goai_research/$FINAL/"   # knowledge base is needed by smoke_test.sh
( cd "$TMP" && zip -q -r "$OLDPWD/$CODE" goai_research -x '*.pyc' -x '*/__pycache__/*' )
rm -rf "$TMP"

echo "built:"; ls -la dist/
echo "commit: $(cat $FINAL/VERSION)"
sha256sum dist/*.zip
