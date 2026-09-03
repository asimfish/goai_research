#!/usr/bin/env python3
"""Unicode-safe manuscript fallback used when no TeX engine is installed.

The TeX sources remain authoritative.  This renderer expands the same
``main.tex`` input order into a self-contained HTML document and asks
headless Chromium to print it to PDF.  Chromium gives us a Unicode-capable
font stack (DejaVu first, Libertinus when present), native SVG image support,
CSS grid tables, and selectable text without the parser artefacts that the old
groff fallback could introduce.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


SUBSCRIPT = str.maketrans("0123456789+-=()aeijhklmnoprstuvxy", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑᵢⱼₕₖₗₘₙₒₚᵣₛₜᵤᵥₓᵧ")
SUPERSCRIPT = str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")

# Element symbols used to restore readable subscripts in bibliography
# metadata that was stored as plain text (for example ``Ba2ZnSi2O7``).
# Matching is intentionally limited to symbols followed by digits so ordinary
# prose and years remain unchanged.
ELEMENT_SYMBOLS = """
Ac Ag Al Am Sb Ar As At Au B Ba Bk Be Bi Bh Br C Ca Cd Ce Cf Cl Cm Cn Co Cr Cs Cu Db
Dy Ds Er Es Eu F Fe Fl Fm Fr Ga Gd Ge H He Hf Hg Ho In Ir K Kr La Li Lr Lu Lv Mc Md
I In Ir Mg Mn Mo Mt N Na Nb Nd Ne Nh Ni No Np O Os P Pa Pb Pd Pm Po Pr Pt Pu Ra Rb Re Rf Rg
Rh Rn Ru S Sc Se Sg Si Sm Sn Sr Ta Tb Tc Te Th Ti Tl Tm Ts U V W Xe Y Yb Zn Zr
""".split()
ELEMENT_ALT = "|".join(sorted(set(ELEMENT_SYMBOLS), key=len, reverse=True))
# Match an element followed by an integer or decimal stoichiometric value.
# Four-digit values are deliberately excluded: this prevents prose such as
# ``In 2024`` from being interpreted as indium with a 2024 atom count.
ELEMENT_RE = re.compile(r"(" + ELEMENT_ALT + r")(\d{1,3}(?:\d+)?)(?!\d)")
SPACED_STOICH_RE = re.compile(
    r"(?<![A-Za-z])(" + ELEMENT_ALT + r")\s+(\d{1,3}(?:\.\d+)?|[xXyY])(?!\d)"
)


def balanced_field(entry: str, field: str) -> str:
    m = re.search(r"\n\s*" + re.escape(field) + r"\s*=\s*\{", entry)
    if m:
        start, depth, i = m.end(), 1, m.end()
        while i < len(entry) and depth:
            if entry[i] == "{":
                depth += 1
            elif entry[i] == "}":
                depth -= 1
            i += 1
        return entry[start : i - 1]
    m = re.search(r"\n\s*" + re.escape(field) + r"\s*=\s*\"", entry)
    if m:
        start = m.end()
        end = entry.find('"', start)
        return entry[start:end] if end >= 0 else entry[start:]
    return ""


def _subscript(value: str) -> str:
    return value.translate(SUBSCRIPT)


def _superscript(value: str) -> str:
    return value.translate(SUPERSCRIPT)


def _replace_frac_commands(source: str) -> str:
    """Replace balanced ``\\frac{numerator}{denominator}`` commands."""
    while True:
        pos = source.find(r"\frac")
        if pos < 0:
            return source
        i = pos + len(r"\frac")
        while i < len(source) and source[i].isspace():
            i += 1
        if i >= len(source) or source[i] != "{":
            source = source[:pos] + source[i:]
            continue

        def read_group(start: int) -> tuple[str, int] | None:
            depth, j = 1, start + 1
            while j < len(source) and depth:
                if source[j] == "{":
                    depth += 1
                elif source[j] == "}":
                    depth -= 1
                j += 1
            return (source[start + 1 : j - 1], j) if depth == 0 else None

        numerator = read_group(i)
        if numerator is None:
            return source
        j = numerator[1]
        while j < len(source) and source[j].isspace():
            j += 1
        if j >= len(source) or source[j] != "{":
            source = source[:pos] + source[i:]
            continue
        denominator = read_group(j)
        if denominator is None:
            return source
        replacement = f"({denominator[0]})"  # initialized below for clarity
        replacement = f"({numerator[0]})/({denominator[0]})"
        source = source[:pos] + replacement + source[denominator[1] :]


def _subscript_stoich(value: str) -> str:
    """Render a stoichiometric number/variable as Unicode subscripts.

    Decimal points have no dedicated subscript code point in the Unicode
    block, so the period is retained between subscript digits (``6.25`` →
    ``₆.₂₅``).  This keeps the number searchable while avoiding a visual
    fallback such as ``Li 6.25``.
    """
    return _subscript(value)


def _normalize_chemical_spacing(source: str) -> str:
    """Join common chemical-formula tokens without topic-specific strings.

    Bibliography metadata is a mixture of plain text and TeX-like notation.
    Some records put spaces between every element/count token (``Li 7 La 3``)
    or around a variable and a parenthesized group.  The passes below only
    touch short element/count tokens and formula-like uppercase runs; four
    digit prose values (for example ``In 2024``) and en dashes in composition
    ranges (``Ba–Y–Zn–Si–O``) remain untouched.
    """
    # Ionic charges occasionally arrive as plain ``Fe 3+`` or ``Li +``. Do
    # this before the stoichiometric pass so the number is not mistaken for a
    # subscript; the look-ahead keeps ordinary arithmetic/prose untouched.
    raw_charge = re.compile(
        r"(?<![A-Za-z])(" + ELEMENT_ALT + r")\s+(?:(\d{1,2})([+\-−])|([+\-−]))(?=\s|[,.;:)]|$)"
    )
    s = raw_charge.sub(
        lambda m: m.group(1) + _superscript(
            (m.group(2) + m.group(3)) if m.group(2) else m.group(4)
        ),
        source,
    )

    # Element/formula-word + integer/decimal/variable, including records with
    # a space between the symbol and count.  The count bound avoids year-like
    # prose.  A formula word such as ``PO`` or ``LiFePO`` is accepted only if
    # it can be fully tokenized as element symbols (plus a site variable M).
    def formula_word(word: str) -> bool:
        i = 0
        while i < len(word):
            match = re.match(r"(?:" + ELEMENT_ALT + r")", word[i:])
            if match:
                i += len(match.group(0))
            elif word[i] in "M":
                i += 1
            else:
                return False
        return i > 0

    formula_word_re = re.compile(
        r"(?<![A-Za-z])([A-Z][A-Za-z]{0,11})\s+(\d{1,3}(?:\.\d+)?|[xXyY])(?!\d)"
    )
    s = formula_word_re.sub(
        lambda m: m.group(1) + _subscript_stoich(m.group(2))
        if formula_word(m.group(1)) else m.group(0),
        s,
    )

    # Element + integer/decimal/variable, including records with a space
    # between the symbol and count.  The count bound avoids year-like prose.
    s = SPACED_STOICH_RE.sub(
        lambda m: m.group(1) + _subscript_stoich(m.group(2)), s
    )

    # A site variable commonly appears as ``LiM x`` or ``H x`` in imported
    # titles.  Restrict conversion to a single uppercase letter immediately
    # before the variable; ordinary lowercase prose is not affected.
    s = re.sub(r"(?<=[A-Z])\s+([xXyY])\b", lambda m: _subscript_stoich(m.group(1).lower()), s)

    # Parenthesis typography and a count written after a closing group, e.g.
    # ``( PO 4 ) 3`` → ``(PO₄)₃``.
    s = re.sub(r"\(\s+(?=[A-Z])", "(", s)
    s = re.sub(r"(?<=[₀-₉ₓᵧ])\s+\(", "(", s)
    s = re.sub(r"(?<=[A-Za-z₀-₉])\s+\)", ")", s)
    s = re.sub(r"(?<=\))\s+(\d{1,3}(?:\.\d+)?)\b", lambda m: _subscript_stoich(m.group(1)), s)

    # Join a subscript-bearing formula component to an adjacent formula word.
    # The second token may omit its own count (``Li₂ O`` → ``Li₂O``), but it
    # must itself be tokenizable as element symbols so sentence words are not
    # concatenated.
    component = r"(?:[A-Z][a-z]?|[A-Z][a-z]?[_₀-₉]+|[A-Z][a-z]?₍[^₎]+₎)"
    join_re = re.compile(
        r"(?P<first>(?:" + component + r"[₀-₉]+(?:\.[₀-₉]+)?|[A-Z][A-Za-z]*[₀-₉₊₋ₓᵧ]+))"
        r"\s+(?P<second>[A-Z][A-Za-z]*(?:[₀-₉]+(?:\.[₀-₉]+)?)?)"
    )
    def join_formula(match: re.Match[str]) -> str:
        first, second = match.group("first"), match.group("second")
        letters = re.sub(r"[₀-₉₊₋ₓᵧ.]+$", "", second)
        return first + second if formula_word(letters) else match.group(0)

    for _ in range(6):
        old = s
        s = join_re.sub(join_formula, s)
        s = re.sub(
            r"(?P<first>\)[₀-₉]+(?:\.[₀-₉]+)?)\s+(?P<second>[A-Z][A-Za-z]*(?:[₀-₉]+(?:\.[₀-₉]+)?)?)",
            join_formula,
            s,
        )
        if s == old:
            break

    # Remove spaces around the mathematical minus/plus used within a formula,
    # but deliberately leave the en dash used for composition ranges intact.
    charge_element = re.compile(r"(?<![A-Za-z])(" + ELEMENT_ALT + r")\s+(\d{1,2})([+-])(?=\s|[,.;:)]|$)")
    s = charge_element.sub(
        lambda m: m.group(1) + _superscript(m.group(2) + m.group(3)), s
    )
    charge_sign = re.compile(r"(?<![A-Za-z])(" + ELEMENT_ALT + r")\s*([+-])(?=\s|[,.;:)]|$)")
    s = charge_sign.sub(
        lambda m: m.group(1) + _superscript(m.group(2)), s
    )
    s = re.sub(r"(?<=[A-Za-z₀-₉ₓᵧ\)])\s*−\s*(?=[A-Za-z0-9₀-₉ₓᵧ(])", "−", s)
    s = re.sub(r"(?<=[A-Za-z₀-₉ₓᵧ\)])\s*\+\s*(?=[A-Za-z0-9₀-₉ₓᵧ(])", "+", s)
    s = re.sub(r"(?<=−x)\s+\((?=[A-Z])", "(", s)

    # Formula components may have been separated by a slash in an alloy or
    # composite title.  Keep a readable single space on either side, while
    # ensuring the formula itself remains contiguous.
    s = re.sub(r"\s*/\s*", " / ", s)
    return s


def clean_tex(value: str) -> str:
    """Convert the small TeX subset used by this manuscript to plain Unicode."""
    s = re.sub(r"(?<!\\)%.*", "", value).strip()
    # TeX line breaks are visual separators.  Replace optional spacing
    # arguments as well, otherwise a break such as ``\\\\[2pt]`` can glue the
    # adjacent words in extracted HTML/PDF text.
    s = re.sub(r"\\\\(?:\s*\[[^\]]*\])?", " ", s)
    s = s.replace("~", " ")
    # TeX accents and common text escapes found in bibliography metadata.
    s = re.sub(r"\\['`\"^~=.uvH]\s*\{?([A-Za-z])\}?", r"\1", s)
    for old, new in {
        r"\mu": "μ", r"\sigma": "σ", r"\eta": "η", r"\kappa": "κ",
        r"\Delta": "Δ", r"\Gamma": "Γ", r"\Omega": "Ω", r"\sum": "Σ",
        r"\cdot": "·", r"\times": "×", r"\rightarrow": "→", r"\pm": "±",
        r"\leq": "≤", r"\geq": "≥", r"\degree": "°", r"\circ": "°", r"\exp": "exp",
        r"\rm": "", r"\bf": "", r"\it": "", r"\,": " ",
        r"\;": " ", r"\!": "", r"\%": "%", r"\&": "&", r"\_": "_",
        r"\#": "#", r"\$": "$",
    }.items():
        s = s.replace(old, new)
    # Keep the semantic content of formatting commands; do not silently drop
    # ``\text{...}`` as the former fallback did.
    s = re.sub(r"\\(?:textsubscript|subscript)\{([^{}]*)\}", lambda m: _subscript(m.group(1)), s)
    s = re.sub(r"\\(?:textsuperscript|superscript)\{([^{}]*)\}", lambda m: _superscript(m.group(1)), s)
    for _ in range(4):
        s = re.sub(r"\\(?:text|textrm|textit|textbf|texttt|mathrm|mathbf|mathit|emph)\{([^{}]*)\}", r"\1", s)
    # Fractions are deliberately rendered as readable inline equations.  A
    # balanced parser is needed for common nested forms such as
    # ``\\frac{E_{a}}}{k_{B}T}``.
    s = _replace_frac_commands(s)
    s = re.sub(r"\\left|\\right", "", s)
    # ``^{\circ}`` is a degree symbol, not a literal caret followed by a
    # superscript.  Normalize this before stripping grouping syntax so
    # ``900~$^{\circ}$C`` becomes the searchable text ``900 °C``.
    s = re.sub(r"\^\s*\{?\s*°\s*\}?", "°", s)
    # Explicit grouped subscripts/superscripts must be handled before braces
    # are discarded.  This supports multi-character counts, variables,
    # parentheses and ionic charges (for example ``PO_{4}^{3-}``).
    s = re.sub(r"_\s*\{([^{}]*)\}", lambda m: _subscript(m.group(1)), s)
    s = re.sub(r"\^\s*\{([^{}]*)\}", lambda m: _superscript(m.group(1)), s)
    # Math delimiters are syntax, not visible separators; remove them after
    # the grouped pass so ``Y$_2$O$_3$`` becomes ``Y₂O₃``.
    s = s.replace("$", "")
    # Grouping braces that are not part of a command are presentation syntax;
    # discard them before applying the single-token conversion pass.
    s = s.replace("{", "").replace("}", "")
    # Explicit math commands and generic subscripts/superscripts.  The
    # Unicode forms avoid strings such as ``G=_i n_i_i`` in extracted text.
    s = re.sub(r"Σ\s*_\s*([A-Za-z0-9]+)", lambda m: "Σ" + _subscript(m.group(1)), s)
    s = re.sub(r"([A-Za-zΓΔΩμσ)])\s*_\s*([0-9]+(?:\.[0-9]+)?|[A-Za-z])", lambda m: m.group(1) + _subscript(m.group(2)), s)
    s = re.sub(r"(?<![A-Za-z0-9])\^\s*([0-9]+(?:[+\-])?)(?![A-Za-z0-9])", lambda m: _superscript(m.group(1)), s)
    s = re.sub(r"(?<=[A-Za-z0-9)])\^\s*([0-9]+(?:[+\-])?)(?![A-Za-z0-9])", lambda m: _superscript(m.group(1)), s)
    # A degree command may have become ``^°`` after command expansion (for
    # example when braces were absent); remove only that semantic caret.
    s = re.sub(r"\^\s*°", "°", s)
    # Bibliography titles frequently contain unwrapped chemical formulas.
    # Convert only element-symbol + digit tokens; this is topic-independent
    # and leaves normal words and citation numbers untouched.
    s = ELEMENT_RE.sub(lambda m: m.group(1) + _subscript(m.group(2)), s)
    # Some imported records place spaces between element/count tokens or use
    # site variables and parenthesized groups.  Normalize the complete run
    # with the generic, topic-independent chemistry pass above.
    s = _normalize_chemical_spacing(s)
    # Remaining command names are not reader-facing content.
    s = re.sub(r"\\[A-Za-z]+(?:\[[^]]*\])?", "", s)
    # Keep an element symbol adjacent to its subscripted oxygen (e.g.,
    # ``Li₂ O`` → ``Li₂O``) so chemical formulas remain searchable.
    next_formula = r"(?:" + "|".join(sorted(set(ELEMENT_SYMBOLS), key=len, reverse=True)) + r")[₀-₉]"
    for _ in range(3):
        s = re.sub(r"([A-Z][a-z]?[_₀-₉]+)\s+(?=" + next_formula + r")", r"\1", s)
    s = s.replace("---", "—").replace("--", "–")
    s = s.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    # A few records contain a Cyrillic O in a chemical formula.  Normalizing
    # this look-alike prevents font fallback and keeps formulas searchable.
    s = s.replace("О", "O").replace("о", "o")
    # A few bibliography records contain both a plain formula and a second
    # TeX-styled copy (for example ``Li2O${\\rm Li}_2{\\rm O}$``).  Collapse
    # only adjacent digit-bearing tokens with the same normalized formula;
    # ordinary repeated words are left untouched.
    sub_to_digit = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
    def dedupe_formula(match: re.Match[str]) -> str:
        left, right = match.group(1), match.group(2)
        if any(ch.isdigit() or ch in "₀₁₂₃₄₅₆₇₈₉" for ch in left + right):
            if left.translate(sub_to_digit) == right.translate(sub_to_digit):
                return left
            # Some records place a plain oxide token next to a TeX-styled
            # copy with reordered subscripts (e.g., ``ZrO2 Zr₂O₂``).  Treat a
            # subscript-bearing copy sharing the same leading element as the
            # duplicate, while leaving unrelated plain formulas intact.
            leading_left = re.match(r"[A-Z][a-z]?", left)
            leading_right = re.match(r"[A-Z][a-z]?", right)
            if any(ch in right for ch in "₀₁₂₃₄₅₆₇₈₉") and leading_left and leading_right and leading_left.group() == leading_right.group():
                return left
        return match.group(0)
    s = re.sub(
        r"(?<![A-Za-z])([A-Z][A-Za-z0-9₀-₉]*[0-9₀-₉][A-Za-z0-9₀-₉]*)\s+([A-Z][A-Za-z0-9₀-₉]*)",
        dedupe_formula,
        s,
    )
    s = re.sub(r"\s*=\s*", " = ", s)
    # Imported metadata occasionally leaves a blank before punctuation such
    # as "Scientific ," or "title :"; remove only that typographic artefact.
    s = re.sub(r"\s+([,.;:])", r"\1", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def parse_bib(path: Path) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    entries: dict[str, dict[str, str]] = {}
    for m in re.finditer(r"@\w+\{([^,]+),", text):
        end = text.find("\n}\n", m.end())
        if end < 0:
            end = len(text)
        entry = text[m.start() : end + 3]
        key = m.group(1).strip()
        entries[key] = {
            "author": clean_tex(balanced_field(entry, "author")),
            "year": clean_tex(balanced_field(entry, "year")),
            "title": clean_tex(balanced_field(entry, "title")),
            "venue": clean_tex(
                balanced_field(entry, "journal")
                or balanced_field(entry, "booktitle")
                or balanced_field(entry, "publisher")
            ),
            "doi": clean_tex(balanced_field(entry, "doi")),
        }
    return entries


def expand_sources(base: Path) -> list[str]:
    """Expand main.tex inputs in their actual assembly order."""
    drafts = base / "drafts"
    main = drafts / "main.tex"
    out: list[str] = []
    for raw in main.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"\s*\\input\{([^}]+)\}\s*$", raw)
        if m:
            target = drafts / m.group(1)
            if target.suffix != ".tex":
                target = target.with_suffix(".tex")
            if target.exists():
                out.extend(target.read_text(encoding="utf-8", errors="replace").splitlines())
            continue
        out.append(raw)
    return out


def command_arg(line: str, command: str) -> str:
    match = re.search(r"\\" + re.escape(command) + r"\*?\s*\{", line)
    if not match:
        return ""
    start = match.start()
    i, depth = match.end(), 1
    while i < len(line) and depth:
        if line[i] == "{":
            depth += 1
        elif line[i] == "}":
            depth -= 1
        i += 1
    return line[i - (i - match.end()) : i - 1] if depth == 0 else line[match.end() :]


def extract_command(lines: list[str], command: str) -> str:
    """Extract a possibly multi-line braced command from the TeX source."""
    source = "\n".join(lines)
    match = re.search(r"\\" + re.escape(command) + r"\s*\{", source)
    if not match:
        return ""
    start = match.end()
    depth, i = 1, start
    while i < len(source) and depth:
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
        i += 1
    return source[start : i - 1] if depth == 0 else source[start:]


def strip_line_comment(line: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", line).strip()


def inline_text(line: str, cited: dict[str, int], labels: dict[str, str]) -> str:
    """Render inline TeX and turn numeric citations into bibliography links."""
    s = strip_line_comment(line)
    citation_markup: list[str] = []

    s = re.sub(
        r"\\cite[tp]?\*?(?:\[[^\]]*\])?\{([^}]+)\}",
        lambda m: _citation_marker(m.group(1), cited, citation_markup),
        s,
    )
    s = re.sub(r"\\(?:ref|pageref)\{([^}]+)\}", lambda m: labels.get(m.group(1), "??"), s)
    escaped = html.escape(clean_tex(s), quote=False)
    for i, markup in enumerate(citation_markup):
        escaped = escaped.replace(f"@@CITE{i}@@", markup)
    return escaped


def _citation_marker(group: str, cited: dict[str, int], markup: list[str]) -> str:
    numbers: list[int] = []
    for key in group.split(","):
        key = key.strip()
        if key not in cited:
            continue
        number = cited[key]
        if number not in numbers:
            numbers.append(number)
    if not numbers:
        return ""
    numbers.sort()

    def linked(number: int) -> str:
        key = next(k for k, n in cited.items() if n == number)
        anchor = html.escape(f"ref-{key}", quote=True)
        return f'<a class="citation" href="#{anchor}">{number}</a>'

    # Match natbib's sort&compress convention: runs of three or more numbers
    # become an en-dash range, while singleton and two-item runs stay explicit.
    chunks: list[str] = []
    start = prev = numbers[0]
    for number in numbers[1:] + [None]:
        if number is not None and number == prev + 1:
            prev = number
            continue
        if prev - start >= 2:
            chunks.append(f"{linked(start)}–{linked(prev)}")
        else:
            chunks.extend(linked(n) for n in range(start, prev + 1))
        if number is not None:
            start = prev = number
    links = ", ".join(chunks)
    marker = f"@@CITE{len(markup)}@@"
    markup.append(f"[{links}]")
    return marker


def equation_text(raw: str) -> str:
    """Make display equations legible in a Unicode-capable browser."""
    text = clean_tex(raw)
    # Collapse TeX's parenthesized fraction form while retaining a clear
    # denominator; this applies to arbitrary fractions, not a topic string.
    text = re.sub(r"\(([^()]+)\)/\(([^()]+)\)", r"\1/(\2)", text)
    text = text.replace("exp(-", "exp(−")
    text = text.replace("kBT", "k_B T")
    return text


def scan_labels(lines: list[str]) -> tuple[dict[str, str], dict[str, int]]:
    labels: dict[str, str] = {}
    sec_no = sub_no = fig_no = tab_no = eq_no = 0
    context: str | None = None
    for raw in lines:
        line = strip_line_comment(raw)
        m = re.search(r"\\section(\*)?\{([^{}]*)\}", line)
        if m and not m.group(1):
            sec_no += 1
            sub_no = 0
            context = "section"
        elif m:
            context = "section-star"
        m = re.search(r"\\subsection(\*)?\{([^{}]*)\}", line)
        if m and not m.group(1):
            sub_no += 1
            context = "subsection"
        elif m:
            context = "subsection-star"
        if re.search(r"\\begin\{figure", line):
            fig_no += 1
            context = "figure"
        if re.search(r"\\begin\{table", line):
            tab_no += 1
            context = "table"
        if re.search(r"\\begin\{equation", line):
            eq_no += 1
            context = "equation"
        for key in re.findall(r"\\label\{([^}]+)\}", line):
            if context == "figure":
                labels[key] = str(fig_no)
            elif context == "table":
                labels[key] = str(tab_no)
            elif context == "equation":
                labels[key] = str(eq_no)
            elif context == "subsection":
                labels[key] = f"{sec_no}.{sub_no}"
            elif context == "section":
                labels[key] = str(sec_no)
        if re.search(r"\\end\{(?:figure|table|equation)\}", line):
            context = None
    return labels, {"figures": fig_no, "tables": tab_no, "equations": eq_no}


def citation_order(lines: list[str]) -> list[str]:
    order: list[str] = []
    for line in lines:
        for group in re.findall(r"\\cite[tp]?\*?(?:\[[^\]]*\])?\{([^}]+)\}", line):
            for key in group.split(","):
                key = key.strip()
                if key and key not in order:
                    order.append(key)
    return order


def render_html(base: Path, lines: list[str], cited: dict[str, int], labels: dict[str, str], bib: dict[str, dict[str, str]]) -> str:
    body: list[str] = []
    para: list[str] = []
    in_env: str | None = None
    figure_asset = figure_caption = ""
    table_caption = ""
    table_rows: list[list[str]] = []
    equation_lines: list[str] = []
    abstract_lines: list[str] = []
    sec_no = sub_no = fig_no = tab_no = eq_no = 0

    raw_title = extract_command(lines, "title")
    document_title = clean_tex(raw_title) or "Untitled manuscript"
    author = clean_tex(extract_command(lines, "author"))
    date = clean_tex(extract_command(lines, "date"))
    # Preserve explicit TeX line breaks in the source.  Inserting a visible
    # space at each break keeps searchable text from gluing the final word of
    # one line to the first word of the next; the break itself is source-
    # derived and therefore remains generic across topics.
    title_parts = [clean_tex(part) for part in re.split(r"\\\\(?:\s*\[[^\]]*\])?", raw_title) if clean_tex(part)]
    if len(title_parts) > 1:
        title_markup = "<br>".join(
            f'<span class="title-line">{html.escape(part, quote=False)}</span>' for part in title_parts
        )
    # A colon is a safe, source-derived title break for long titles that do not
    # contain an explicit break, and keeps the first page balanced.
    elif ": " in document_title:
        first, second = document_title.split(": ", 1)
        title_markup = (
            f'<span class="title-line">{html.escape(first, quote=False)}:</span><br>'
            f'<span class="title-line">{html.escape(second, quote=False)}</span>'
        )
    else:
        title_markup = html.escape(document_title, quote=False)
    body.append(
        '<header class="title-block">'
        f'<h1>{title_markup}</h1>'
        f'<div class="author">{html.escape(author, quote=False)}</div>'
        f'<div class="date">{html.escape(date, quote=False)}</div>'
        "</header>"
    )

    def flush_para() -> None:
        if para:
            text = " ".join(x.strip() for x in para if x.strip())
            if text:
                body.append(f"<p>{inline_text(text, cited, labels)}</p>")
            para.clear()

    def flush_table() -> None:
        nonlocal table_rows, table_caption
        if not table_rows:
            table_rows, table_caption = [], ""
            return
        cap = inline_text(table_caption, cited, labels) if table_caption else ""
        caption = f"<caption>Table {tab_no}. {cap}</caption>" if cap else f"<caption>Table {tab_no}</caption>"
        rows = []
        for i, row in enumerate(table_rows):
            cells = []
            tag = "th" if i == 0 else "td"
            for cell in row:
                # Pipe delimiters are a Markdown artefact, not a table design;
                # keep any accidental source pipe readable as a slash.
                cell = cell.replace("|", " / ")
                scope = ' scope="col"' if tag == "th" else ""
                cells.append(f"<{tag}{scope}>{inline_text(cell, cited, labels)}</{tag}>")
            rows.append("<tr>" + "".join(cells) + "</tr>")
        body.append("<table class=\"data-table\">" + caption + "<thead>" + rows[0] + "</thead><tbody>" + "".join(rows[1:]) + "</tbody></table>")
        table_rows, table_caption = [], ""

    document_started = False
    for raw in lines:
        line = strip_line_comment(raw)
        if not line:
            if in_env is None:
                flush_para()
            continue
        if line == "\\begin{document}":
            document_started = True
            continue
        if line == "\\end{document}":
            flush_para()
            break
        if not document_started:
            continue
        if line == "\\maketitle":
            flush_para()
            continue
        if line == "\\clearpage":
            flush_para()
            body.append('<div class="page-break"></div>')
            continue
        if line.startswith("\\begin{abstract}"):
            flush_para()
            in_env = "abstract"
            abstract_lines = []
            continue
        if line.startswith("\\end{abstract}"):
            abstract = " ".join(x.strip() for x in abstract_lines if x.strip())
            if abstract:
                body.append(
                    '<section class="abstract-block"><h2>Abstract</h2>'
                    f'<p>{inline_text(abstract, cited, labels)}</p></section>'
                )
            in_env = None
            continue
        if in_env == "abstract":
            abstract_lines.append(line)
            continue
        if line.startswith("\\begin{figure"):
            flush_para(); in_env = "figure"; fig_no += 1; figure_asset = figure_caption = ""; continue
        if line.startswith("\\end{figure"):
            in_env = None
            asset = (base / "drafts" / figure_asset).resolve()
            if figure_asset and asset.exists():
                src = html.escape(asset.as_uri(), quote=True)
                image = f'<img src="{src}" alt="{html.escape(clean_tex(figure_caption), quote=True)}">'
            else:
                image = '<div class="missing-asset">Vector figure asset unavailable</div>'
            cap = inline_text(figure_caption, cited, labels)
            body.append(f'<figure>{image}<figcaption>Figure {fig_no}. {cap}</figcaption></figure>')
            continue
        if line.startswith("\\begin{table"):
            flush_para(); in_env = "table"; tab_no += 1; table_rows = []; table_caption = ""; continue
        if line.startswith("\\end{table"):
            flush_table(); in_env = None; continue
        if line.startswith("\\begin{equation"):
            flush_para(); in_env = "equation"; eq_no += 1; equation_lines = []; continue
        if line.startswith("\\end{equation"):
            in_env = None
            equation = html.escape(equation_text(" ".join(equation_lines)), quote=False)
            body.append(
                f'<div class="equation"><span class="equation-label">Equation {eq_no}</span>'
                f'<span class="equation-formula">{equation}</span></div>'
            )
            continue
        if in_env == "figure":
            m = re.search(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", line)
            if m: figure_asset = m.group(1)
            if "\\caption{" in line: figure_caption = command_arg(line, "caption")
            continue
        if in_env == "table":
            if "\\caption{" in line: table_caption = command_arg(line, "caption"); continue
            if "\\label{" in line or line.startswith(("\\centering", "\\small", "\\begin{tabular", "\\end{tabular", "\\toprule", "\\midrule", "\\bottomrule")): continue
            if "&" in line:
                row = re.sub(r"\\\\\s*$", "", line).strip()
                table_rows.append([x.strip() for x in row.split("&")])
            continue
        if in_env == "equation":
            if "\\label{" not in line: equation_lines.append(line)
            continue
        if line.startswith(r"\section"):
            flush_para()
            star = line.startswith(r"\section*")
            heading_title = command_arg(line, "section")
            if not star:
                sec_no += 1; sub_no = 0; heading = f"{sec_no} {inline_text(heading_title, cited, labels)}"
            else:
                heading = inline_text(heading_title, cited, labels)
            body.append(f"<h2>{heading}</h2>")
            continue
        if line.startswith(r"\subsection"):
            flush_para(); star = line.startswith(r"\subsection*"); heading_title = command_arg(line, "subsection")
            if not star:
                sub_no += 1; heading = f"{sec_no}.{sub_no} {inline_text(heading_title, cited, labels)}"
            else: heading = inline_text(heading_title, cited, labels)
            body.append(f"<h3>{heading}</h3>"); continue
        if line.startswith(r"\paragraph"):
            flush_para(); body.append(f"<h4>{inline_text(command_arg(line, 'paragraph'), cited, labels)}</h4>"); continue
        if line.startswith(("\\label", "\\addcontentsline", "\\centering", "\\small", "\\bibliographystyle", "\\bibliography", "\\input")):
            continue
        # Coverage sections keep long, complete citation inventories on their
        # own source lines.  Render each inventory as a separate paragraph so
        # grouped records remain legible instead of forming one justified
        # block of adjacent numbers.
        if re.fullmatch(r"\\cite[tp]?\*?(?:\[[^\]]*\])?\{[^}]+\}", line):
            flush_para()
            body.append(f'<p class="citation-block">{inline_text(line, cited, labels)}</p>')
            continue
        para.append(line)
    flush_para()

    refs: list[str] = []
    for key, number in cited.items():
        item = bib.get(key, {})
        author = item.get("author", "") or "Anonymous"
        title = item.get("title", "") or "Untitled record"
        venue = item.get("venue", "") or "Venue not reported"
        year = item.get("year", "")
        doi = item.get("doi", "").strip()
        doi = re.sub(r"^(?:https?://)?(?:dx\.)?doi\.org/", "", doi, flags=re.I)
        doi = re.sub(r"^doi:\s*", "", doi, flags=re.I)
        anchor = html.escape(f"ref-{key}", quote=True)
        parts = [html.escape(author, quote=False), html.escape(title, quote=False),
                 f'<span class="venue">{html.escape(venue, quote=False)}</span>',
                 html.escape(year or "Year not reported", quote=False)]
        if doi:
            doi_text = html.escape(doi, quote=False)
            doi_href = html.escape("https://doi.org/" + doi, quote=True)
            parts.append(f'<a class="doi" href="{doi_href}">DOI: {doi_text}</a>')
        else:
            parts.append('<span class="doi-missing">DOI not reported</span>')
        ref = " — ".join(parts)
        refs.append(f'<li id="{anchor}" value="{number}">{ref}</li>')
    body.append('<h2 class="references-heading">References</h2><ol class="references">' + "".join(refs) + "</ol>")
    body_html = "".join(body)
    return """<!doctype html><html><head><meta charset="utf-8"><title>""" + html.escape(document_title, quote=False) + """</title><style>
@font-face{font-family:'DejaVu Serif';src:url('file:///usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf') format('truetype');font-weight:400}
@font-face{font-family:'DejaVu Serif';src:url('file:///usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf') format('truetype');font-weight:700}
@font-face{font-family:'DejaVu Serif';src:url('file:///usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf') format('truetype');font-style:italic}
@font-face{font-family:'DejaVu Sans';src:url('file:///usr/share/fonts/truetype/dejavu/DejaVuSans.ttf') format('truetype')}
@font-face{font-family:'DejaVu Math';src:url('file:///usr/share/fonts/truetype/dejavu/DejaVuMathTeXGyre.ttf') format('truetype')}
@font-face{font-family:'Libertinus Serif';src:url('file:///usr/share/fonts/truetype/libertinus/LibertinusSerif-Regular.ttf') format('truetype')}
@page{size:A4;margin:22mm 18mm 20mm 18mm}
*{box-sizing:border-box} body{font-family:'DejaVu Serif','Libertinus Serif',serif;color:#202124;font-size:10.2pt;line-height:1.35;margin:0}
.title-block{text-align:center;margin:0 0 16pt}.title-block h1{font-size:16.5pt;line-height:1.18;margin:0 0 8pt;font-weight:700}.title-line{display:inline-block;white-space:nowrap}.author{font-size:11.5pt;margin:0 0 3pt}.date{font-size:10pt;font-style:italic}.abstract-block{font-size:9.7pt;margin:0 8mm 16pt;text-align:justify;border-top:0.7pt solid #777;border-bottom:0.7pt solid #777;padding:7pt 0 5pt}.abstract-block h2{font-size:11pt;text-align:center;border:0;margin:0 0 5pt;padding:0;letter-spacing:.02em}.abstract-block p{margin:0}.page-break{break-before:page;page-break-before:always}
h2{font-size:14pt;line-height:1.15;margin:16pt 0 6pt;border-bottom:0.5pt solid #777;padding-bottom:3pt}h3{font-size:11.5pt;line-height:1.2;margin:10pt 0 4pt;padding-left:0.2em}h4{font-size:10.5pt;margin:7pt 0 2pt}p{margin:0 0 7pt;text-align:justify;orphans:2;widows:2}.citation-block{margin:2pt 0 5pt 8pt;text-align:left;line-height:1.28}.citation{color:#1f5aa6;text-decoration:none}.citation:hover{text-decoration:underline}
figure{margin:10pt 0 13pt;text-align:center;break-inside:avoid;page-break-inside:avoid}figure img{display:block;width:100%;max-height:245mm;object-fit:contain;margin:auto}figcaption{font-size:9pt;line-height:1.25;margin-top:4pt;text-align:left}table{border-collapse:collapse;table-layout:fixed;width:100%;margin:9pt 0 12pt;font-size:8.4pt;line-height:1.22;break-inside:auto;overflow-wrap:anywhere;word-break:normal}caption{text-align:left;font-weight:700;font-size:9.2pt;line-height:1.2;margin-bottom:4pt}th,td{border:0.6pt solid #666;padding:4pt 4.5pt;vertical-align:top;text-align:left;overflow-wrap:anywhere}th{background:#eef3f8;font-weight:700}thead{display:table-header-group}tr{break-inside:avoid;page-break-inside:avoid}.equation{display:flex;align-items:center;justify-content:center;gap:13pt;font-family:'DejaVu Math','DejaVu Sans',sans-serif;text-align:center;margin:9pt 0;padding:7pt 22pt;border-top:0.5pt solid #aaa;border-bottom:0.5pt solid #aaa;font-size:13pt;line-height:1.25}.equation-label{font-family:'DejaVu Serif',serif;font-size:9pt;font-weight:700;color:#444;white-space:nowrap}.equation-formula{min-width:12em}.references-heading{page-break-before:always}.references{font-size:8.2pt;line-height:1.28;padding-left:28pt}.references li{padding-left:4pt;margin:0 0 4pt;break-inside:avoid}.references .venue{font-style:italic}.references .doi,.references .doi-missing{color:#1f5aa6}.citation{white-space:nowrap}.missing-asset{border:0.5pt solid #b44;padding:18pt;color:#933}
 .references-heading{page-break-before:auto}
 </style></head><body>""" + body_html + "</body></html>"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("base", type=Path, help="run directory containing drafts/, library/ and figures/")
    args = ap.parse_args()
    base = args.base.resolve()
    drafts = base / "drafts"
    lines = expand_sources(base)
    labels, counts = scan_labels(lines)
    order = citation_order(lines)
    bib = parse_bib(base / "library" / "references.bib")
    missing = [k for k in order if k not in bib]
    if missing:
        raise SystemExit("undefined bibliography keys: " + ", ".join(missing[:10]))
    cited = {key: i + 1 for i, key in enumerate(order)}
    document = render_html(base, lines, cited, labels, bib)
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        raise SystemExit("no Unicode-capable browser fallback (google-chrome/chromium) is installed")
    with tempfile.TemporaryDirectory(prefix="goai_unicode_fallback_") as td:
        source = Path(td) / "main.html"
        source.write_text(document, encoding="utf-8")
        output = drafts / "main.pdf"
        cmd = [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--allow-file-access-from-files", "--no-pdf-header-footer", f"--print-to-pdf={output}", source.as_uri()]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode:
            print(proc.stdout, proc.stderr)
            return proc.returncode
    print(f"wrote {drafts / 'main.pdf'} with {len(order)} cited references; figures={counts['figures']}, tables={counts['tables']}, equations={counts['equations']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
