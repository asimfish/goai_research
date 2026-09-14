#!/bin/bash
# build main_typo3.pdf for both Chinese reports in the 5090 docker TeX Live (explicit passes; latexmk exit-12 false failure)
W=${W:-/data/liyufeng/goai_typeset_g76}
DIRS="$*"; timeout 900 docker run -e DIRS="$DIRS" --rm --user 1007:1007 -e HOME=/tmp -v $W:/work -v /data/liyufeng/goai_assets/fonts:/usr/share/fonts/noto-cjk:ro latex2pdf-latex-compile-server:latest bash -lc '
for d in ${DIRS:-/work/byzso/drafts /work/bzso/report}; do cd $d || continue
  for M in main_en main_en_iclr main_zh_iclr main_en_neurips main_en_orchestra main_en_arxiv main_en_springer main_en_journal main_zh_neurips main_zh_orchestra main_zh_arxiv main_zh_journal; do [ -f $M.tex ] || continue
    xelatex -interaction=nonstopmode $M.tex >/dev/null 2>&1; bibtex $M >/dev/null 2>&1; sed -i "s/\\\\penalty0 //g" $M.bbl
    xelatex -interaction=nonstopmode $M.tex >/dev/null 2>&1; xelatex -interaction=nonstopmode $M.tex >/dev/null 2>&1
    echo "$d/$M pdf=$(stat -c %s $M.pdf 2>/dev/null) pages=$(grep -o "Output written on $M.pdf ([0-9]* pages" $M.log | grep -o "[0-9]* pages") errors=$(grep -c "^!" $M.log) overfull=$(grep -c "^Overfull" $M.log)"
  done
  xelatex -interaction=nonstopmode main_typo3.tex >/dev/null 2>&1; bibtex main_typo3 >/dev/null 2>&1; sed -i "s/\\\\penalty0 //g" main_typo3.bbl
  xelatex -interaction=nonstopmode main_typo3.tex >/dev/null 2>&1; xelatex -interaction=nonstopmode main_typo3.tex >/dev/null 2>&1
  echo "$d pdf=$(stat -c %s main_typo3.pdf 2>/dev/null) pages=$(grep -o "Output written on main_typo3.pdf ([0-9]* pages" main_typo3.log | grep -o "[0-9]* pages") errors=$(grep -c "^!" main_typo3.log) toolarge=$(grep -c "too large" main_typo3.log) overfull=$(grep -c "^Overfull" main_typo3.log) undef=$(grep -c "undefined" main_typo3.log)"
  grep -A3 "^!" main_typo3.log | head -20; grep "too large\|Overfull .hbox.*[0-9][0-9]\.[0-9]*pt" main_typo3.log | head -12
done'
