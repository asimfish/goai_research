#!/bin/bash
# 把 PDF 渲染成审稿代理用的逐页 PNG：zh_render_pages.sh <pdf> <outdir> [dpi]
pdf=$1; out=$2; dpi=${3:-100}
mkdir -p "$out"; rm -f "$out"/page-*.png
pdftoppm -r "$dpi" -png "$pdf" "$out/page"
n=$(ls "$out"/page-*.png | wc -l); echo "$n pages -> $out"
