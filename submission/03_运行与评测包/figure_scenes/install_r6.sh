#!/bin/bash
# 把第六轮十张图装进两篇报告（中英同名，英文加 _en；论文里的 \includegraphics 不用改）。
#   usage: install_r6.sh <img2ppt 构建树，含 jobs/<job>/build> [画廊目录]
# crop=render：重建自己决定画布用量；场景按「内容占画布宽 - 24 px」算的印刷字号，裁边必须同口径。
set -e
BUILDS=${1:?用法: install_r6.sh <构建树> [画廊目录]}
MEDIA=${2:-}
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
BY="$REPO/submission/03_运行与评测包/正式案例_BYZSO冷启动/最终输出/figures"
BZ="$REPO/submission/03_运行与评测包/补充案例_20260903/02_bazn2si2o7/figures"
I="$REPO/skills/goai-figure-studio/scripts/install_fig.py"

run () {  # job project name figdir
  python3 "$I" --build "$BUILDS/jobs/$1/build" --s5 "$BUILDS/jobs/$1/build/render/page_001.png" \
    --project "$2" --name "$3" --figdir "$4" --crop render --margin 14 ${MEDIA:+--media "$MEDIA"}
}

run fig01_r6            fig01_evidence_map  fig01_evidence_synthesis_map    "$BY"
run fig02_r6            fig02_route_matrix  fig02_route_variable_matrix     "$BY"
run fig03_r6            fig03_roadmap       fig03_research_roadmap          "$BY"
run bzso_roadmap_r6     bzso_roadmap        roadmap_bazn2si2o7              "$BZ"
run bzso_taxonomy_r6    bzso_taxonomy       taxonomy_phase_control          "$BZ"
run fig01_r6_en         fig01_evidence_map  fig01_evidence_synthesis_map_en "$BY"
run fig02_r6_en         fig02_route_matrix  fig02_route_variable_matrix_en  "$BY"
run fig03_r6_en         fig03_roadmap       fig03_research_roadmap_en       "$BY"
run bzso_roadmap_r6_en  bzso_roadmap        roadmap_bazn2si2o7_en           "$BZ"
run bzso_taxonomy_r6_en bzso_taxonomy       taxonomy_phase_control_en       "$BZ"
echo "INSTALL_R6_DONE"
