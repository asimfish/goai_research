#!/usr/bin/env python3
"""bib_guard —— 稿件引用一致性确定性闸门（离线，无网络）。

检查项：
1. 正文 \\cite{key} / [@key] 引用的 key 是否都在 .bib 中定义（未定义 = 阻塞）
2. 库内条目整合率：被正文引用的 bib 条目 / bib 总条目，低于线 = 阻塞
   （孤儿条目要么在正文找到落点，要么移出库，不许留着充数）
3. 引用密度（综述质检：正文引用过少给告警）
   密度统计只应覆盖正文章节文件（如 workspace/drafts/sections），
   蓝图、修订日志等过程文档不要计入词数分母。
4. bib 字段卫生（告警）：doi 与 url 同存（编译后 URL 断行难看且冗余，
   应删 url 留 doi）；title 中化学式/多大写缩写未加 {} 保护
   （plainnat 会把 BaZn2Si2O7 压成 bazn 2 si 2 o 7）。

用法：
  python3 tools/bib_guard.py <draft_dir_or_file> <references.bib> \
      [--min-cites-per-1k 8] [--min-integration 0.9]
退出码：0 = PASS；1 = 存在未定义引用或整合率不达标。
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server.core.bibtex import parse_bibtex  # noqa: E402

CITE_TEX = re.compile(r"\\cite[tp]?\*?(?:\[[^\]]*\])?\{([^}]+)\}")
CITE_MD = re.compile(r"\[@([A-Za-z0-9_:\-]+)(?:[;,\s]+@?[A-Za-z0-9_:\-]+)*\]")
CITE_MD_EACH = re.compile(r"@([A-Za-z0-9_:\-]+)")
# title 里需要 {} 保护的 token：≥2 个大写字母 + ≥1 个数字（化学式/缩写），
# 或全大写缩写词（≥3 字母）。plainnat 等样式会把未保护 token 压成小写。
RE_PROTECT_NEEDED = re.compile(
    r"\b(?=\w*[A-Z]\w*[A-Z])(?=\w*\d)[\w()\[\]+.\-]*[A-Za-z0-9]|\b[A-Z]{3,}\b")


def bib_hygiene(entries: list[dict]) -> list[str]:
    """bib 字段卫生检查 → 告警清单（不阻塞）。"""
    warns: list[str] = []
    for e in entries:
        fields = e.get("fields", {})
        key = e["key"]
        if fields.get("doi") and fields.get("url"):
            warns.append(f"{key}: doi 与 url 同存——删 url 留 doi"
                         "（正文已链接 DOI，长 URL 编译后断行难看）")
        title = fields.get("title", "")
        # 去掉已被 {} 保护的片段后再扫
        unprotected = re.sub(r"\{[^{}]*\}", " ", title)
        hits = sorted({m.group(0) for m in
                       RE_PROTECT_NEEDED.finditer(unprotected)})
        if hits:
            warns.append(f"{key}: title 含未保护 token {hits[:4]}——"
                         "加 {{}} 防止 bibliography 样式压成小写"
                         "（化学式会被拆成 bazn 2 si 2 o 7 这种碎片）")
    return warns


def collect_cites(path: str) -> list[tuple[str, str, int]]:
    """→ [(key, file, line_no)]。全文扫描：\cite{...} 参数允许跨行。"""
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    line_starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            line_starts.append(i + 1)

    def line_of(pos: int) -> int:
        import bisect
        return bisect.bisect_right(line_starts, pos)

    for m in CITE_TEX.finditer(text):
        ln = line_of(m.start())
        for key in m.group(1).split(","):
            key = key.strip()
            if key:
                out.append((key, path, ln))
    for m in CITE_MD.finditer(text):
        ln = line_of(m.start())
        for km in CITE_MD_EACH.finditer(m.group(0)):
            out.append((km.group(1), path, ln))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("draft", help="稿件目录或单个 .tex/.md 文件")
    ap.add_argument("bib", help="references.bib")
    ap.add_argument("--min-cites-per-1k", type=float, default=8.0,
                    help="每千词最低引用数（综述密度告警线）")
    ap.add_argument("--min-integration", type=float, default=0.9,
                    help="库内条目整合率下限（被引条目/bib 总条目，低于线阻塞）")
    args = ap.parse_args()

    files = ([args.draft] if os.path.isfile(args.draft) else
             sorted(glob.glob(os.path.join(args.draft, "**", "*.tex"),
                              recursive=True)
                    + glob.glob(os.path.join(args.draft, "**", "*.md"),
                                recursive=True)))
    if not files:
        sys.exit(f"未找到稿件文件: {args.draft}")
    if not os.path.isfile(args.bib):
        sys.exit(f"未找到 bib 文件: {args.bib}")

    with open(args.bib, encoding="utf-8") as f:
        bib_entries = parse_bibtex(f.read())
    bib_keys = {e["key"] for e in bib_entries}

    cites: list[tuple[str, str, int]] = []
    word_count = 0
    for fp in files:
        cites.extend(collect_cites(fp))
        with open(fp, encoding="utf-8", errors="replace") as f:
            word_count += len(re.findall(r"[\w\u4e00-\u9fff]+", f.read()))

    used = {c[0] for c in cites}
    undefined = sorted(used - bib_keys)
    orphans = sorted(bib_keys - used)
    density = len(cites) / max(word_count / 1000, 1e-9)
    integration = (len(bib_keys) - len(orphans)) / max(len(bib_keys), 1)

    print(f"稿件文件: {len(files)}  引用调用: {len(cites)}  去重 key: {len(used)}")
    print(f"bib 条目: {len(bib_keys)}  整合率: {integration:.0%}  "
          f"引用密度: {density:.1f} 次/千词")
    if undefined:
        print(f"\n[阻塞] {len(undefined)} 个未定义引用 key:")
        for k in undefined:
            locs = [f"{os.path.basename(f)}:{ln}" for kk, f, ln in cites if kk == k][:3]
            print(f"  - {k}  ({', '.join(locs)})")
    integration_fail = bib_keys and integration < args.min_integration
    if orphans:
        level = "阻塞" if integration_fail else "告警"
        print(f"\n[{level}] {len(orphans)} 个孤儿 bib 条目（未被引用），"
              f"整合率 {integration:.0%} vs 下限 {args.min_integration:.0%}:")
        for k in orphans[:20]:
            print(f"  - {k}")
    if density < args.min_cites_per_1k:
        print(f"\n[告警] 引用密度 {density:.1f} 低于线 {args.min_cites_per_1k}"
              "（综述通常需要更密的证据支撑）")
    hygiene = bib_hygiene(bib_entries)
    if hygiene:
        print(f"\n[告警] {len(hygiene)} 项 bib 字段卫生问题:")
        for h in hygiene[:30]:
            print(f"  - {h}")
    failed = bool(undefined) or bool(integration_fail)
    reasons = ([f"{len(undefined)} 个未定义引用"] if undefined else []) + \
              ([f"整合率 {integration:.0%} 低于 {args.min_integration:.0%}"]
               if integration_fail else [])
    print("\n结论:", f"FAIL（{'；'.join(reasons)}）" if failed else "PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
