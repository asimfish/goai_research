from pathlib import Path

from tools.academic_language_guard import check


def test_reports_software_metaphor(tmp_path: Path):
    draft = tmp_path / "draft.tex"
    draft.write_text("\\section{字段归一化}\n正文使用相互独立的验证终点。\n", encoding="utf-8")
    findings = check([draft])
    assert {item[2] for item in findings} == {"字段归一化", "相互独立的验证终点"}


def test_ignores_tex_comments_and_accepts_academic_wording(tmp_path: Path):
    draft = tmp_path / "draft.tex"
    draft.write_text(
        "% 字段归一化仅供内部说明\n"
        "\\section{合成方法与产物表征}\n"
        "正文按相同实验项目比较。\n",
        encoding="utf-8",
    )
    assert check([draft]) == []


def test_reports_english_internal_terms_and_masks_tex_carriers(tmp_path: Path):
    """英文稿同样要拦内部术语/路径：gate、ledger、papers.jsonl…按整词匹配；
    \\ref{tab:identity-ledger} 之类标签参数不是读者可见文本，不报；器件物理的 gate voltage 不报。"""
    draft = tmp_path / "draft.tex"
    draft.write_text(
        "Each claim passed the ref_gate and the ledger records it (see papers.jsonl).\n"
        "Table~\\ref{tab:identity-ledger} lists the evidence package; the figspec is niche-balanced.\n"
        "The gate voltage dependence is a device property.\n"
        "Investigate the GATE of the reaction.\n"
        "Aggregated results were delegated to the compiler.\n",
        encoding="utf-8",
    )
    findings = check([draft])
    hits = {(item[1], item[2]) for item in findings}
    assert hits == {(1, "ref_gate"), (1, "ledger"), (1, "papers.jsonl"),
                    (2, "evidence package"), (2, "figspec"), (2, "niche-balanced"), (4, "gate")}, hits


def test_negative_existence_claims_need_search_receipt(tmp_path: Path):
    """出货补充稿摘要写「本次核查未发现 Ba5Y12Zn[O(SiO4)]8 …报道」，而主案例已核过其 DOI。
    摘要/结论里的否定性存在论断必须登记在 negative_claims.md 并带检索回执，否则 FAIL。"""
    main = tmp_path / "main.tex"
    main.write_text(
        "\\begin{abstract}\n本次核查未发现 Ba$_5$Y$_{12}$Zn[O(SiO$_4$)]$_8$ 的批量合成报道。\n\\end{abstract}\n"
        "\\section{引言}\n未见报道的说法在引言里不查。\n"
        "\\section{结论}\nThe Zn analogue has not been reported in the ICSD.\n",
        encoding="utf-8",
    )
    claims = tmp_path / "negative_claims.md"
    findings = check([main], negative_claims=claims)
    assert [(f[1], f[2]) for f in findings] == [(2, "negative-existence claim"), (7, "negative-existence claim")]
    assert "not listed" in findings[0][3]
    claims.write_text(
        "- claim: 本次核查未发现 Ba5Y12Zn[O(SiO4)]8 的批量合成报道\n"
        "  search: Crossref+OpenAlex \"Ba5Y12Zn\" 2026-09-08，0 条批量合成记录；DOI 10.1039/D3NJ04480G 为单晶生长\n"
        "- claim: The Zn analogue has not been reported in the ICSD\n",
        encoding="utf-8",
    )
    findings = check([main], negative_claims=claims)
    assert [(f[1], f[2]) for f in findings] == [(7, "negative-existence claim")]
    assert "without a 'search:" in findings[0][3]
    claims.write_text(claims.read_text(encoding="utf-8") + "  search: ICSD 2024.2 query Ba-Y-Zn-Si-O, 2026-09-08, 0 hits\n",
                      encoding="utf-8")
    assert check([main], negative_claims=claims) == []
