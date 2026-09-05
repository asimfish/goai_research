"""纯文本归一化（零第三方依赖）。

单独成模块的原因：bibtex 解析与 bib_guard 等离线闸门需要这两个函数，
不应因此拖上 sources → http → httpx 的网络依赖链。
"""
from __future__ import annotations

import re
import unicodedata

# 题名里的排版标记不属于题名内容：bib_polish 会给化学式加 {Ba}$_5$Y$_{12}$ 一类保护，
# 出版方元数据则可能带 <sub>5</sub>。比对前统一剥掉，否则 "ba 5 y 12" 对 "ba5y12"
# 会把同一篇文章误判成题名漂移（FIX）。
_HTML_TAG = re.compile(r"<[^>]+>")
_TEX_COMMAND = re.compile(r"\\[A-Za-z]+\*?")       # \ce \emph \textsubscript \alpha …
_TEX_ESCAPED = re.compile(r"\\([^A-Za-z])")          # \& \% \_ → 保留被转义的符号本身
_TEX_MARKUP = re.compile(r"[{}$^_~]")


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def strip_markup(s: str) -> str:
    """去掉 HTML 标签与 TeX 命令/数学模式/分组符号，只留题名文字。"""
    s = _HTML_TAG.sub("", s or "")
    s = _TEX_ESCAPED.sub(r"\1", s)
    s = _TEX_COMMAND.sub("", s)
    return _TEX_MARKUP.sub("", s)


def norm_title(s: str) -> str:
    s = strip_accents(strip_markup(s)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()
