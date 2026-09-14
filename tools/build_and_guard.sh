#!/usr/bin/env bash
# 编译 + 版面门禁：两份报告 × 中英四份，编完立刻跑 layout_guard，有 FAIL 就不往下发布。
#
#   tools/build_and_guard.sh [<本地构建树>]
#
# 构建树的结构（scratchpad 里那套）：
#   <tree>/byzso/drafts/{main_typo3,main_en}.tex + sections_v3/ + sections_en/ + goai_{zh,en}_typo.sty
#   <tree>/byzso/figures/pdf/                     图件（中文 <name>.pdf、英文 <name>_en.pdf）
#   <tree>/bzso/report/  同上
#
# 编译在 5090 的 docker TeX Live 里做（本机没有 TeX），门禁在本机跑（只要 pdftotext + python3）。
# 5090 的 sshd 并发下会随机断开，所以每一步都带重试。
set -uo pipefail
TREE="${1:-/tmp/claude-0/-root-lyf-goai/fc788d38-0358-4f3a-839d-163ae1a21275/scratchpad/typeset}"
TOOLS="$(cd "$(dirname "$0")" && pwd)"
SSH=(-i "$HOME/.ssh/id_ed_tianyiyun" -p 4009 -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 -o BatchMode=yes)
H=liyufeng@bj.wznln.com
R=/data/liyufeng/goai_typeset_g76
IMG=latex2pdf-latex-compile-server:latest

try() { local n=0; until "$@"; do n=$((n+1)); [ $n -ge 8 ] && { echo "GAVE UP: $*" >&2; return 1; }; sleep 12; done; }

echo "== 1/4 同步源码与图件到 5090"
for d in byzso/drafts/sections_v3 byzso/drafts/sections_en bzso/report/sections_v3 bzso/report/sections_en \
         byzso/figures/pdf bzso/figures/pdf; do
  [ -d "$TREE/$d" ] && try rsync -az -e "ssh ${SSH[*]}" "$TREE/$d/" "$H:$R/$d/"
done
for d in byzso/drafts bzso/report; do
  try rsync -az -e "ssh ${SSH[*]}" "$TREE/$d/"goai_zh_typo.sty "$TREE/$d/"goai_en_typo.sty "$H:$R/$d/"
done

echo "== 2/4 在 5090 编译四份"
try ssh "${SSH[@]}" $H "docker run --rm --user 1007:1007 -e HOME=/tmp -v $R:/work \
  -v /data/liyufeng/goai_assets/fonts:/usr/share/fonts/noto-cjk:ro $IMG bash -lc '
for d in /work/byzso/drafts /work/bzso/report; do cd \$d
  for M in main_typo3 main_en; do
    xelatex -interaction=nonstopmode \$M.tex >/dev/null 2>&1
    bibtex \$M >/dev/null 2>&1; sed -i \"s/\\\\\\\\penalty0 //g\" \$M.bbl
    xelatex -interaction=nonstopmode \$M.tex >/dev/null 2>&1
    xelatex -interaction=nonstopmode \$M.tex >/dev/null 2>&1
    echo \"\$d/\$M \$(grep -o \"([0-9]* pages\" \$M.log | tail -1)\"
  done
done'" 2>&1 | grep -E "main_(typo3|en) "

echo "== 3/4 取回 PDF 与 .log"
for d in byzso/drafts bzso/report; do
  try rsync -az -e "ssh ${SSH[*]}" --include='main_typo3.pdf' --include='main_en.pdf' \
      --include='main_typo3.log' --include='main_en.log' --exclude='*' "$H:$R/$d/" "$TREE/$d/"
done

echo "== 4/4 版面门禁"
rc=0
run_guard() {  # <pdf前缀> <源目录> <sty> <图目录> <lang>
  printf '\n──── %s [%s]\n' "$(basename "$1")" "$5"
  python3 "$TOOLS/layout_guard.py" --pdf "$TREE/$1.pdf" --log "$TREE/$1.log" \
      --src "$TREE/$2" --sty "$TREE/$3" --figdir "$TREE/$4" --lang "$5" || rc=1
}
run_guard byzso/drafts/main_typo3 byzso/drafts/sections_v3 byzso/drafts/goai_zh_typo.sty byzso/figures/pdf zh
run_guard byzso/drafts/main_en    byzso/drafts/sections_en byzso/drafts/goai_en_typo.sty byzso/figures/pdf en
run_guard bzso/report/main_typo3  bzso/report/sections_v3  bzso/report/goai_zh_typo.sty  bzso/figures/pdf  zh
run_guard bzso/report/main_en     bzso/report/sections_en  bzso/report/goai_en_typo.sty  bzso/figures/pdf  en

echo
if [ $rc -ne 0 ]; then
  echo "门禁未通过：上面每条 FAIL 都要改掉再发布。不要绕过。"
else
  echo "门禁通过：四份都可以发布。"
fi
exit $rc
