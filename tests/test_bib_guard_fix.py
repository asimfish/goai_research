from tools.bib_guard import bib_hygiene, fix_bib_hygiene_text
from server.core.bibtex import parse_bibtex


def test_fix_bib_hygiene_is_idempotent_and_clears_warnings():
    raw = """@article{sample,
  author = {A. Author},
  title = {Properties of BaZnSi 3 O 8 measured by MAS-NMR},
  year = {2026},
  doi = {10.1000/example},
  url = {https://doi.org/10.1000/example},
}
"""

    fixed, changed = fix_bib_hygiene_text(raw)
    fixed_again, changed_again = fix_bib_hygiene_text(fixed)

    assert changed == 1
    assert changed_again == 0
    assert fixed_again == fixed
    assert "url =" not in fixed
    assert "{BaZnSi3O8}" in fixed
    assert "{MAS}-{NMR}" in fixed
    assert bib_hygiene(parse_bibtex(fixed)) == []


def test_fix_bib_hygiene_groups_complete_delimited_formulas():
    raw = """@article{sample,
  title = {BaY16Si4O33 containing Ba(SiO4)4, [ZnSi4O16], and [Si2O7]6-},
  year = {2026},
}
"""

    fixed, _ = fix_bib_hygiene_text(raw)

    assert "{Ba(SiO4)4}" in fixed
    assert "{[ZnSi4O16]}" in fixed
    assert "{[Si2O7]6-}" in fixed
