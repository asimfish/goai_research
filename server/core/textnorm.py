"""纯文本归一化（零第三方依赖）。

单独成模块的原因：bibtex 解析与 bib_guard 等离线闸门需要这两个函数，
不应因此拖上 sources → http → httpx 的网络依赖链。
"""
from __future__ import annotations

import re
import unicodedata


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def norm_title(s: str) -> str:
    s = strip_accents(s or "").lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()
