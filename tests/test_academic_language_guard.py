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
