# Format review trace — Ba–Y–Zn–Si–O phase-diagram survey

Review session initialized. The trace records commands, bounded outputs, and reviewer observations for the independent read-only format review. No manuscript, bibliography, or figure files are written by this review.

## Session

- Model: Codex (same-model cold-start unless a cross-model tool is available)
- Workspace: `<HOME>
- Scope: `main.pdf`, `main_formatted.pdf`, `main.tex`, all `drafts/sections/*.tex`, `revision_log.md`, I8 records, PDF/guard/raster evidence.

- Session label: `format_byzso` (platform did not expose an external session ID).
- Active-run restriction: the named active JSONL under `state/parallel/20260903_163239_625670` was not read.

## Source and I8 phase

Read `drafts/main.tex`, all eleven section files (including the complete 45-line `sections/11_corpus_coverage.tex`), `drafts/revision_log.md`, the closed I8 issue in `state/ledger.json`, and the prior writer record `state/parallel/20260903_160021_511265/byzso_format_writer.final.md`. The source title contains explicit balanced lines and normal source spaces (`Ba--Y--Zn--Si--O Silicates` and `Metastability Bottlenecks`). The writer record and revision log describe typography/rendering-only changes; no manuscript claims or bibliography entries were changed. Current hashes include `drafts/main.tex` = `99313cade85b834eb0aea7895f708ef9c94bc04a93cfc3d0bcf1e041356d14fa` and `library/references.bib` = `bdd1d98a39cfa5851320e146a094aa9317c0983ef7092325343ce27b915cfa1e`.

## Command evidence

Commands were run read-only from the requested workspace (the virtual-environment Python is located in the repository root):

```text
pdfinfo drafts/main.pdf; pdfinfo drafts/main_formatted.pdf
  both: 35 pages; A4 594.96 x 841.92 pt; unencrypted; PDF 1.4.
pdffonts drafts/main.pdf (and main_formatted.pdf)
  DejaVuSerif/Arial CID TrueType fonts and Type 3 math resources are embedded; all rows report Unicode mappings.
pdfimages -list drafts/main.pdf (and main_formatted.pdf)
  no raster image rows; figures are vector content.
sha256sum/cmp
  both PDFs = c54b7d75ce46833ae6915c62ac27b4c7139cdab9994b564f16af94d9926c24b3; `cmp` identical.

<HOME> <HOME> drafts
  PASS — 12 files; 8 labels; 7 references.
<HOME> <HOME> drafts/sections
  PASS.
<HOME> <HOME> drafts/sections library/references.bib
  PASS — 11 manuscript files; 757 citation calls; 513 unique keys; 513/513 integration; 702 field-hygiene warnings retained by the tool as non-blocking metadata warnings.
```

## Text, links, and geometry

`pdftotext -layout` reports 35 pages. Hazard scans for `■`, U+FFFD, `[t]`, `[Figure]`, `P0.`, unresolved `??`, `[Figure asset]`, `Columns:`, pipeline wording, naked BibTeX keys, and rendered URLs returned zero hits. The exact title phrases `Ba–Y–Zn–Si–O Silicates:` and `Metastability Bottlenecks` are present with ordinary spaces; the abstract and `513 distinct records` statement are intact. A bibliography parser found entries 1–513 in sequence; all 513 match `author — title — venue — year — DOI` (500 DOI values and 13 `DOI not reported`), and no `http(s)://` URL is rendered. PDF annotation counts are 975 `/Subtype /Link` objects, including 342 internal `/Dest /ref-...` links and 633 DOI URI links, consistent with blue clickable body citations and DOI links.

`pdftotext -bbox-layout` gives a global text box of x = 51.0–544.5 pt with no page outside the 35–560 pt margin screen. Source/PDF headings and captions agree: sections 1–10, unnumbered `Data Sources and Literature Coverage`, `References`, Figures 1–3, and Tables 1–3. The 513-record coverage is split into six named scientific groupings rather than a single number string.

## Raster inspection

`pdftoppm` rendered the full 35-page PDF to temporary PNGs and contact sheets; every page was checked for clipping, overflow, blank parser artifacts, and abnormal margins. High-resolution spot checks covered pages 1 (title/abstract), 2 (Figure 1), 4 (Figure 2), 5 (citation-dense Table 1), 7 (Figure 3), 10 (Table 3/conclusion transition), 12–13 (Data Sources), 14 (first References page), 18, 22, 24, 26, 29, 32, and 35 (formula- and DOI-dense References pages). The title, coverage prose, grouped citations, blue links, figures, tables, and reference layout are readable; no page margin anomaly or broken `scientific` word was observed.

The visual inspection did identify one non-blocking metadata typography residual: source titles on reference pages retain occasional mixed-case or baseline formula tokens (`Mn₃O4`, `Pbo-Sio2`, `Cao-Sio2`, `A1 2 O₃`, `BA2MGWO₆`, `Mg₀.2Co₀.8`, `Zno-Sio2`). They are legible and citation facts are unchanged, but they should be normalized in a future metadata-only pass. This is recorded as minor I9; no manuscript or bibliography file was modified.

## Citation spot-check

`mcp__goai_refcheck__verify_entry` was run on `kozhevnikova2024synthesis`, `kaur2011influence`, `sayyed2026physical`, `kolitsch2006bay2si3o10`, `kaiser2002crystal`, `ababaikeri2024ba`, `decterov2018thermodynamic`, `makrovets2023y2o3`, `jeon2025phase`, and `zeng2024selective`. All ten returned `verdict: PASS`, title similarity 1.0, and no issues. The sample supports that the format pass did not alter the cited author/year/venue/DOI facts or the bounded claims attached to them.

## Determination

No blocker or major issue was found. One minor residual metadata typography issue was routed to `writing` through loopctl as I9. The review remains provisional because no independent cross-model channel was available; it is a genuine same-model cold-start review rather than a reuse of the prior trace.

## Ledger commands and final receipt

```text
GOAI_WORKSPACE=<workspace> python3 tools/loopctl.py issue add --from-agent goai-reviewer --target writing --severity minor --text "...formula tokens..."
  新 issue I9 → writing
GOAI_WORKSPACE=<workspace> python3 tools/loopctl.py gate --name draft_complete --status PASS --detail "..." --inputs <workspace>/drafts/main.tex,<workspace>/drafts/main.pdf
  gate draft_complete = PASS
GOAI_WORKSPACE=<workspace> python3 tools/loopctl.py gate --name review_pass --status PASS --detail "..." \
  --receipt "model=Codex (same-model cold-start);trace=<workspace>/state/review_traces/format_byzso.md"
  gate review_pass = PASS
GOAI_WORKSPACE=<workspace> python3 tools/loopctl.py log --stage review --agent goai-reviewer --event done --detail "blocker 0/major 0/minor 1 (I9); PASS provisional same-model cold-start; format_byzso trace recorded"
  logged
GOAI_WORKSPACE=<workspace> python3 tools/loopctl.py check-done
  DONE: required gates recorded PASS/WARN; no open blocker/major (open minor ['I9'] handed to final cleanup).
```

Trace artifact size at completion: 6007 bytes (non-placeholder); report size: 2516 bytes.
