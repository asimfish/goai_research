<div align="center">

# GoAI Research 📚⚔️

**Multi-agent pipeline that turns a research topic into a survey paper — with citations you can trust and figures you can still edit.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-48%20offline%20%2B%20100%20live-brightgreen.svg)](tests/)
[![MCP](https://img.shields.io/badge/MCP-4%20servers%20%C2%B7%2025%20tools-8A2BE2.svg)](server/)
[![Skills](https://img.shields.io/badge/skills-9%20agents-orange.svg)](skills/)

[中文版 README](README_CN.md) | English

</div>

> 🔍 **Search everything. Trust nothing unverified. Ship figures that stay editable.**
> Five-source literature search with snowballing, zero-trust citation verification,
> figures rendered simultaneously as paper-ready SVG **and** native draw.io files,
> idea generation with a pluggable retrosynthesis backend — all wired into a
> ledger-driven loop where an adversarial reviewer routes rework until every gate passes.

> 🪶 **Lightweight by design, zero lock-in.** The intelligence layer is 9 plain-Markdown
> skills readable by any LLM agent — Codex CLI, Claude Code, Cursor, or your own harness.
> The deterministic layer is 4 small MCP servers you can test offline. No framework,
> no database, no daemon. Fork it, rewrite it, adapt it to your stack.

## 📰 News

- **2026-09-02 — Independent audit closes two loop-protocol holes.** A
  read-only audit against the original spec found that `check-done` could
  declare DONE with a single recorded gate (the exact shape of a pipeline that
  stalled at literature search) and that `review_pass` accepted a PASS with no
  receipt. Now mechanical: nine required gates must all be recorded (skips as
  explicit WARN, home-made gate names warned), and a review PASS is refused
  unless its trace file exists and is not a stub. Also fixed a vendored-model
  indentation bug that made the inorganic precursor predictor unimportable —
  `BaZn2Si2O7 → ZnO / SiO₂ / BaCO₃` now runs end-to-end locally. 48 offline tests.
- **2026-08-31 — Scholarly content contract.** Domain-expert feedback on a
  materials survey became skill-level rules: every survey now ships a
  **paper roadmap figure**; materials topics get two mandatory search lanes
  (analogous/isostructural systems, phase diagrams) and a dedicated
  analogous-systems intro subsection; results open with a consolidated
  prior-findings table; every future direction must land on a concrete
  synthesis recommendation — named process + precursor candidates from the
  retro MCP tool, marked "model prediction, pending validation"; conclusions
  end with the highest-discovery-value next experiments. Figures: ≤2 theme
  colors, image-first reference generation for every delivered figure.
- **2026-08-31 — Production-quality layer.** A cold-start run in Chinese
  exposed a blind spot: correct content, degraded typesetting. Now shipped —
  a CJK language contract with a dedicated `ctexart` template (no more
  hybrid EN/CN documents; compile-verified with xelatex), table design rules
  (no split half-tables, no raw BibTeX keys in cells, no typewriter `NA`
  dumps), a pipeline-jargon firewall for reader-facing text, bib field
  hygiene (DOI/URL redundancy, brace protection for chemical formulas), and
  a "production quality" review dimension that requires page-by-page PDF
  inspection. `tex_guard` now **blocks** bare-bibkey leaks — CJK-adjacent
  and digit-leading keys included.
<details>
<summary>Earlier milestones</summary>

- **2026-08-30 — Typography hard gate v2.** Node titles render **bold by
  default**, font floors raised to 4.5 pt print-equivalent, and a new hierarchy
  lint flags group labels smaller than their member nodes. The writer skill
  gains section-heading lexicon rules (noun phrases, no "A, B, and C rules"
  titles) and top-venue run-in list conventions.
- **2026-08-29 — First public sample deliverable.** A 26-page survey on COF
  photocatalytic hydrogen evolution, produced end-to-end:
  [`examples/survey_cof_her`](examples/survey_cof_her) — 143 verified references
  (100 % integrated, 51.2 cites/1k words), lint-clean editable figures, a
  pre-registered improvement idea, and the full gate ledger.
- **2026-08-28 — Scale tiers + style bank.** Literature search gains
  standard / comprehensive / exhaustive tiers with layered quotas (100+ refs for
  a full survey); a style bank distilled from 30 classic surveys feeds writing
  and figure style; [super_library](https://github.com/asimfish/super_library)
  is wired in as the writing-language authority.
- **2026-08-28 — Typography lint v1.** Print-equivalent font floors, shape-aware
  text overflow, and occlusion checks; `render_figure` refuses to render while
  lint errors remain.
- **2026-08-27 — First full competition run.** 37-paper survey + synthesis-route
  design, 9 gates PASS, two review rounds with issue close-out
  ([`examples/competition_run`](examples/competition_run)).
- **2026-08-26 — The loop goes live.** Ledger-driven state machine (`loopctl`),
  adversarial reviewer with receipts, fingerprint-based stale-gate detection.

</details>

## 🖼 Gallery

![GoAI Research pipeline](examples/pipeline.png)

*This figure was drawn by the system itself: one [`figspec`](examples/pipeline.figspec.json) source file rendered into [`pipeline.svg`](examples/pipeline.svg) (for papers), [`pipeline.drawio`](examples/pipeline.drawio) (open it in draw.io and keep editing), and the PNG above (for self-check).*

**From a real run** — both figures below shipped inside the
[26-page sample survey](examples/survey_cof_her/paper/main.pdf); every one is
still editable (figspec → SVG → .drawio):

| [Design-lever factor chain](examples/survey_cof_her/paper/figures/fig1_factor_chain.png) | [Pre-registered improvement route](examples/survey_cof_her/paper/figures/fig2_tppa1_idea.png) |
| --- | --- |
| ![fig1](examples/survey_cof_her/paper/figures/fig1_factor_chain.png) | ![fig2](examples/survey_cof_her/paper/figures/fig2_tppa1_idea.png) |
| bold-by-default titles · lint-clean at 4.5 pt floors | gates, fallbacks and endpoints — one editable canvas |

## Contents

1. [More Than Just a Prompt](#1--more-than-just-a-prompt)
2. [Quick Start](#2--quick-start)
3. [What's Inside](#3--whats-inside)
4. [The Loop](#4--the-loop)
5. [Figures That Stay Editable](#5--figures-that-stay-editable)
6. [Citation Integrity](#6--citation-integrity)
7. [Idea Forge & Retrosynthesis](#7--idea-forge--retrosynthesis)
8. [Parallel Execution](#8--parallel-execution)
9. [Host Setup](#9--host-setup) · Codex / Claude Code / Cursor
10. [Configuration](#10--configuration)
11. [Testing](#11--testing)
12. [Design Notes](#12--design-notes) · why MCP + skills, why cross-model review
13. [FAQ](#13--faq)
14. [Ecosystem](#14--ecosystem) · sibling projects this pipeline builds on
15. [Citation](#15--citation)
16. [License & Contributing](#16--license--contributing)

---

## 1. 🎯 More Than Just a Prompt

**Full pipeline** — give it a topic, it runs the whole survey loop:

```
Use goai-orchestrator to run a survey on "diffusion models for molecule
generation", focus on 2022+, target 25 pages. Show me scope.md first.
```

**Each stage also works standalone:**

```
Use goai-lit-search to search "LLM agents for robotics" and give me a coverage report
Use goai-ref-guard to verify workspace/library/references.bib
Use goai-figure-studio to turn taxonomy.md into the main figure
Use goai-figure-editable to convert figures/old_diagram.png into an editable .drawio
Use goai-idea-forge to mine research gaps and draft experiment plans
```

The orchestrator reads the loop ledger, dispatches the right agent per stage,
enforces exit gates, and routes reviewer issues back to the stage that owns them —
until `check-done` returns green or the round budget runs out (it reports honestly
either way; it never claims an unfinished survey is done).

## 2. 🚀 Quick Start

```bash
git clone https://github.com/asimfish/goai_research && cd goai_research
bash install.sh     # creates .venv, installs deps, generates MCP configs with absolute paths
# With the vendored two-stage inorganic model: bash install.sh --retro

# Codex CLI
cat configs/codex.config.toml >> ~/.codex/config.toml
ln -s "$PWD/skills"/goai-* ~/.codex/skills/

# Claude Code
#   merge configs/claude.mcp.json into ~/.claude.json (mcpServers)
ln -s "$PWD/skills"/goai-* ~/.claude/skills/

# smoke check
tools/check.sh --servers
.venv/bin/python -m pytest tests/ -q     # offline tests, no network needed
```

Requirements: Python ≥ 3.10 (install.sh uses [uv](https://github.com/astral-sh/uv) if
available). Optional extras: `brew install --cask drawio` (export .drawio → png/pdf),
`.venv/bin/pip install -e '.[preview]'` (PNG previews for figure self-checks),
Node.js (official [draw.io MCP](https://github.com/jgraph/drawio-mcp) for live browser editing).
For the final PDF you need a TeX distribution: English surveys compile with
`pdflatex`/`xelatex` + `newtx`; **Chinese surveys require `xelatex` + `ctex` +
Fandol fonts** (bundled in TeX Live full; on a slim install run
`tlmgr install ctex fandol newtx`). Both templates load the `svg` package
only if present, so a missing `svg.sty`/Inkscape never breaks a build.

## 3. 🧩 What's Inside

**Start here** — use case → entry point:

| Use case | Start here |
|---|---|
| Topic → full survey, end to end | [goai-orchestrator](skills/goai-orchestrator/SKILL.md) |
| Find every relevant paper + PDFs + BibTeX | [goai-lit-search](skills/goai-lit-search/SKILL.md) |
| Learn writing & figure style from 30 classic surveys | [goai-style-bank](skills/goai-style-bank/SKILL.md) |
| Verify authors / order / year / venue of citations | [goai-ref-guard](skills/goai-ref-guard/SKILL.md) |
| Draw taxonomy / framework / timeline figures | [goai-figure-studio](skills/goai-figure-studio/SKILL.md) |
| Make an existing image editable in draw.io | [goai-figure-editable](skills/goai-figure-editable/SKILL.md) |
| Taxonomy → blueprint → sections → LaTeX | [goai-survey-writer](skills/goai-survey-writer/SKILL.md) |
| Mine gaps → proposals → experiment plans | [goai-idea-forge](skills/goai-idea-forge/SKILL.md) |
| Adversarial review with routed issues | [goai-reviewer](skills/goai-reviewer/SKILL.md) |

<details>
<summary><b>The three layers</b> — skills (cognition) · MCP servers (determinism) · loop tools (control)</summary>

| Layer | What | Why |
|---|---|---|
| `skills/` — 9 SKILL.md | Methodology the host LLM executes: taxonomy building, claim-bound writing, review judgment | Cognitive work stays with the strongest available model; skills carry no API keys and no LLM SDKs |
| `server/` — 4 MCP servers, 25 tools | Online search plus local full text, BibTeX parsing & author comparison, figspec validation & dual rendering, retrosynthesis adapters | Deterministic heavy lifting: testable offline, reusable across hosts |
| `tools/` | `loopctl.py` ledger CLI · `bib_guard.py` citation gate · `tex_guard.py` assembly gate · `bank_check.py` bank validator · `parallel_run.sh` | Loop control and hard gates: pure local, zero LLM |

| MCP server | Tools |
|---|---|
| `goai-litsearch` | `local_corpus_status` `grep_local_corpus` `read_local_document` `lookup_local_doi` `search_papers` `snowball` `lookup` `download_pdf` `save_to_library` `export_bibtex` `coverage_report` |
| `goai-refcheck` | `verify_entry` `verify_bib_file` `deep_audit_info` |
| `goai-figure` | `figspec_schema` `validate_figspec` `render_figure` `svg_file_to_drawio` `drawio_export` `list_figures` |
| `goai-retro` | `provider_status` `inorganic_model_status` `predict_precursor_routes` `predict_retro` `make_experiment_plan` |

</details>

<details>
<summary><b>Workspace layout</b> — everything lands on disk, auditable</summary>

```
workspace/
├── library/     papers.jsonl + references.bib + pdfs/
├── style_bank/  style cards + exemplar figures from 30 classic surveys
├── notes/       scope / taxonomy / citation_bank / figure_plan
├── figures/     svg/ + drawio/ + figspec/ + candidates/   ← same source, never drift
├── drafts/      blueprint + sections/*.tex + revision_log
├── ideas/       proposal_*.md + experiment_*.json + review_log
└── state/       ledger.json (the loop ledger) + audit reports
```

</details>

## 4. 🔄 The Loop

```
intake → scoping → [lit_search ∥ style_bank]    ← retrieval and style learning in parallel
      → ref_gate → taxonomy
      → [figures ∥ writing ∥ ideas]      ← three lanes in parallel
      → review → all gates PASS → final
               → issues → routed back to the owning stage → review again …
```

Every stage has an **exit gate** recorded in the ledger (`workspace/state/ledger.json`),
written only through `tools/loopctl.py`. The reviewer files structured issues with a
`target` stage; the orchestrator resets downstream gates when an upstream stage reruns
(cascade rule), bounds the loop with `--max-rounds`, and escalates to the human when
the same issue survives three rounds. Full protocol: [docs/LOOP_PROTOCOL.md](docs/LOOP_PROTOCOL.md).

| Stage | Agent | Exit gate |
|---|---|---|
| scoping | orchestrator + you | `scope_confirmed` |
| lit_search | goai-lit-search | `lit_coverage` — all subtopics covered + scale quota (≥100 papers for a full survey) |
| style_bank | goai-style-bank | `style_bank_ready` — style cards + exemplar figures from 30 classic surveys |
| ref_gate | goai-ref-guard | `ref_integrity` — zero UNVERIFIED / MISMATCH entries |
| taxonomy | goai-survey-writer | `taxonomy_ready` — every leaf backed by ≥ 3 papers |
| figures | goai-figure-studio / -editable | `figures_ready` — svg + drawio for every figure |
| writing | goai-survey-writer | `draft_complete` — bib_guard PASS, all sections done |
| ideas | goai-idea-forge | `ideas_reviewed` — adversarial review + second citation pass |
| review | goai-reviewer | `review_pass` — 0 blockers and 0 majors |

## 5. 🎨 Figures That Stay Editable

**Main figures run a three-phase pipeline**: strategy contract (source-fidelity
table + edge-label-first + palette/density budgets) → AI image generation with
two candidate rounds (4 exploratory sketches → issue-ledger audit picks a
direction → 2 formal candidates, prompts injected with style_bank domain cards
and exemplar references) → measurement-driven reconstruction into editable
vectors. Generated rasters are reference finals only — **deliverables always
come from reconstruction**, so venue-grade visuals and editability coexist.
Auxiliary figures (timelines, simple flows) render directly from figspec.

A figure here is never a dead bitmap. The single source of truth is a **figspec** —
a small JSON describing nodes, groups, edges, and texts. One render call emits:

- `figures/svg/<name>.svg` — for LaTeX (`\includesvg`, or export pdf via drawio CLI)
- `figures/drawio/<name>.drawio` — **native mxGraph XML**: open in
  [draw.io](https://app.diagrams.net) / draw.io Desktop, drag nodes, edges follow
  (source/target are bound, not painted)
- `figures/png/<name>.png` — for the agent's own render → self-check → fix loop (≤ 3 rounds)

**Typography is enforced, not hoped for.** A built-in lint guards every render:
print-equivalent font floors (`pt = px × 468 / canvas_width`, body text below
4.5 pt is rejected — tiny labels never survive to the PDF), shape-aware text
overflow (a diamond only holds ~55 % of its bounding width, a hexagon ~70 %),
occlusion checks (group labels vs. member nodes, edge labels vs. nodes), and a
hierarchy check that flags any group label smaller than its member nodes.
Node titles render **bold by default** (opt out per node with
`label_bold: false`). `render_figure` refuses to render while lint errors
remain, and the skill ships a font-size hierarchy table (title > lane label >
node title > sublabel) so generated figures come out with proportionate,
readable type by construction.

Already have a figure that isn't a figspec?

- **Structured SVG** → `svg_file_to_drawio` reverses it deterministically
  (recovers group containers, attaches edge labels, then re-renders)
- **Bitmap / PDF figure** → `goai-figure-editable` runs a visual-reconstruction loop:
  read the image → structured inventory → figspec → render → side-by-side compare → fix

Editability acceptance is explicit: text must be native text, shapes draggable,
edges bound to nodes — "looks similar" doesn't pass.

Private deployments point `GOAI_LOCAL_CORPUS_ROOTS` at the complete Parquet
archive (not the old 2015--2020 paragraph-extraction subset) and configure the
SQLite DOI index plus shard root as a pair. A submission exports only explicitly
redistributable text into a self-contained compact Parquet package; the same four
tools—status, search, bounded read, and DOI lookup—work without any private index:

```bash
cp configs/corpus-selection.example.json selection.private.json
.venv/bin/python tools/export_corpus_subset.py selection.private.json workspace/library/corpus-release --format compact-parquet
GOAI_LOCAL_CORPUS_ROOTS=$PWD/workspace/library/corpus-release tools/check.sh --corpus
```

`examples/demo_corpus/` is a three-record CC0 synthetic fixture for GitHub and
CI. Its manifest says `citable=false`; it tests the interface but is never
scientific evidence.

## 6. 🛡 Citation Integrity

The single most damaging failure of LLM-written surveys is fabricated or
mis-attributed citations. GoAI treats references as **zero-trust input**:

1. **Only one citation pool.** Writers may only cite keys from
   `workspace/library/references.bib`, which is built by `save_to_library` /
   `export_bibtex` — never typed by hand, never recalled from model memory.
2. **Fast tier** (`goai-refcheck`): every entry is re-looked-up against
   Crossref / OpenAlex / arXiv / DBLP; titles fuzzy-matched, authors compared for
   missing / fabricated / **reordered** names, year & venue cross-checked.
   Verdicts: `PASS` / `FIX` (auto-correctable) / `MISMATCH` / `UNVERIFIED` —
   the last two block the gate.
3. **Deep tier** (optional): local [super_ref](https://github.com/asimfish/super_ref)
   evidence-first audit — downloads PDFs and registry metadata, four isolated
   agents cross-check, author approval required for corrections.
4. **Draft-side gates**: `bib_guard.py` — undefined `\cite` keys block the build,
   bib integration rate < 90% blocks (orphan entries must earn a place in the text
   or leave the library), citation density < 8 / 1000 words warns, and field
   hygiene warns (DOI + URL redundancy; unprotected chemical formulas /
   acronyms in titles that bibliography styles would lowercase into fragments).
   `tex_guard.py` — leftover TODO placeholders, missing `\input`/figure files,
   dangling `\ref`, unclosed environments, and **bare BibTeX keys leaking into
   reader-visible text** all block assembly; typewriter-font (`\texttt`)
   overuse and a Chinese manuscript on the English template warn.
5. **Context check** (reviewer): samples claim–citation pairs and verifies the cited
   paper actually supports the claim — the most diagnostic and most-missed check.

## 7. 💡 Idea Forge & Retrosynthesis

`goai-idea-forge` mines three gap signals from the verified library — coverage gaps
(subtopics nobody addressed), contradiction signals (papers disagreeing), and
combination holes (two taxonomy branches never crossed) — and every proposal must
carry real citation keys as evidence.

For inorganic materials, call
`predict_precursor_routes(target_formula="Li7La3Zr2O12")`. Stage 1 retrieves
individual precursor Top-M candidates; after a chemistry filter, Stage 2 reranks
enumerated 2--5-component sets and returns Top-5 by default. The vendored model
and checkpoints live under `vendor/two_stage_retro/` and are hash-checked at
load time. Predictions still require literature evidence, condition completion,
and reviewer approval.

Molecular retrosynthesis can still use an HTTP backend:

```bash
export GOAI_RETRO_PROVIDER=http
export GOAI_RETRO_API_URL=https://your-askcos-instance/api/retro   # ASKCOS / IBM RXN / self-hosted
export GOAI_RETRO_API_KEY=...                                      # optional
```

The default provider is a **stub** that emits clearly-labeled demo routes so the
whole loop is testable without a chemistry backend — skills hard-forbid presenting
stub output as chemical conclusions. `make_experiment_plan` turns a route into a
plan skeleton whose `safety` field is mandatory; plans then pass **two gates**:
adversarial review (evidence / novelty / feasibility / safety) and a second
citation verification of every reference they cite.

## 8. ⚡ Parallel Execution

Figures, sections, and ideas have no shared writes — the orchestrator fans them out:

```bash
# tasks.tsv: <name>\t<prompt>\t<artifacts>\t<earlier dependencies> per line
bash tools/parallel_run.sh --backend codex --jobs 3 tasks.tsv   # or --backend claude
```

Rules that keep parallelism safe: Codex runs with a workspace-write sandbox;
stdout JSONL and stderr are stored separately; optional artifact declarations turn
missing, empty, or stale outputs into exit 3 (`=path` checks existence only). Each
fourth-column dependency is a real ready gate. A timed-out process whose declared
artifacts pass validation keeps `.process_exit=124` but receives a WARN effective
status instead of being mislabeled as failed content. Each task writes only its own shard files
(`sections/NN_*.tex`, `figures/<name>.*`); shared files (main.tex, references.bib)
are touched only by the merge step; ledger writes are serialized by loopctl's
file lock. Logs and exit codes land in `workspace/state/parallel/<run_id>/`.

## 9. 🖥 Host Setup

<details>
<summary><b>Codex CLI</b></summary>

```bash
cat configs/codex.config.toml >> ~/.codex/config.toml   # generated by install.sh
ln -s "$PWD/skills"/goai-* ~/.codex/skills/
```

`AGENTS.md` in the repo root gives Codex the routing table and iron rules when
working inside this repository.

</details>

<details>
<summary><b>Claude Code</b></summary>

Merge `configs/claude.mcp.json` into `~/.claude.json` → `mcpServers`, then:

```bash
ln -s "$PWD/skills"/goai-* ~/.claude/skills/
```

</details>

<details>
<summary><b>Cursor</b></summary>

Add the same four server entries to Cursor's `mcp.json`; reference the skills with
`@skills/goai-orchestrator/SKILL.md` or symlink them into your skills directory.
Use the Task tool for the parallel lanes instead of `parallel_run.sh` if you prefer
in-IDE subagents.

</details>

## 10. ⚙️ Configuration

| Env var | Default | What it does |
|---|---|---|
| `GOAI_EMAIL` | `goai-research@example.com` | Contact for Crossref/OpenAlex polite pools (better rate limits) |
| `GOAI_HTTP_MIN_INTERVAL` | `1.0` | Min seconds between requests to the same host |
| `GOAI_HTTP_MAX_RETRIES` | `2` | Bounded retries on 429/503 (honors Retry-After) |
| `GOAI_WORKSPACE` | `workspace` | Where all artifacts land |
| `GOAI_LOCAL_CORPUS_ROOTS` | `workspace/library/corpus` | Local Markdown roots, or a compact Parquet package root (`:` separated on Linux/macOS) |
| `GOAI_LOCAL_CORPUS_TIMEOUT` | `30` | Local full-text timeout in seconds |
| `GOAI_LOCAL_CORPUS_EXPECTED_INDEX` | — | Private SQLite UUID→archive index; must be configured with the shard root |
| `GOAI_LOCAL_CORPUS_SHARD_ROOT` | — | Private ingest-shard directory; compact public packages need neither variable |
| `GOAI_RETRO_DEVICE` | `cpu` | Inorganic two-stage model device, e.g. `cuda:0` |
| `GOAI_INORGANIC_RETRO_ROOT` | `vendor/two_stage_retro` | Vendored inorganic model root |
| `GOAI_RETRO_PROVIDER` | `stub` | `stub` (demo) or `http` (real predictor) |
| `GOAI_RETRO_API_URL` / `GOAI_RETRO_API_KEY` | — | Retrosynthesis backend endpoint / auth |
| `GOAI_DRAWIO_CLI` | auto-detect | Path to draw.io Desktop CLI for exports |
| `S2_API_KEY` | — | Optional Semantic Scholar key (higher rate limits) |

## 11. 🧪 Testing

```bash
.venv/bin/python -m pytest tests/ -q            # 48 offline tests — no network, no LLM
.venv/bin/python -m pytest -m live tests/live/  # live suite — real APIs, real draw.io CLI
```

Every pipeline stage has also been **live-tested end to end** (real 5-source
search, real citation verdicts on corrupted bibs, real draw.io PNG/PDF export,
mock-backend retro HTTP, 50-process ledger stress, and a full mini-survey run
whose `check-done` exits 0). Stage-by-stage reports: [docs/live-tests/](docs/live-tests/).

Covered: BibTeX parse/format round-trip, author comparison (abbreviations, order,
missing/fabricated), multi-source dedup, figspec validation (node-overlap and
synonymous parallel-edge detection) plus typography lint (print-equivalent font
floors, shape-aware text overflow, label occlusion), SVG and mxGraph rendering,
**SVG → figspec → drawio round-trip** (groups recovered as containers, edge labels reattached),
retro stub + plan skeleton, full loopctl ledger cycle plus concurrency (12
parallel writers, zero lost updates), check-done semantics (WARN pass-through,
minor deferral, stale-input fingerprint reset, review receipts), bib_guard
blocking (undefined keys + integration rate) and field-hygiene warnings,
tex_guard assembly gate (including bibkey-leak blocking, `\texttt` density and
CJK-template-mismatch warnings), and bank_check validation.

## 12. 📐 Design Notes

**Why MCP servers + Markdown skills, not a framework?**
Deterministic work (throttled search, metadata comparison, XML rendering) becomes
slow and flaky when an LLM improvises it — so it lives in small, offline-testable
MCP servers. Cognitive work (taxonomy, claims, review judgment) is where the host
model earns its keep — so it lives in plain-Markdown skills any agent can read.
The boundary is the design: *server when it must be right every time, skill when
it must think.*

**Why an adversarial reviewer instead of self-review?**
A model reviewing its own output falls into self-play blind spots. The reviewer
here is a separate agent (cross-model via Codex MCP when available), runs with a
fresh context per round, must verify before criticizing (run `verify_entry` before
calling a citation fake), and files structured issues instead of prose. Review and
execution never share a seat: the reviewer cannot edit, executors cannot acquit.
Every `review_pass` carries a receipt (reviewer model + trace archive) — a PASS
nobody can audit is treated as no PASS at all.

**Why two models and not more?**
Two is the smallest configuration that breaks self-review blind spots, and a
two-player game converges to a stable attack–defense equilibrium faster than a
committee. Adding reviewers grows token cost and coordination overhead linearly
while the marginal benefit decays — the big win is going from 1 to 2, not from
2 to 4.

**Why a ledger instead of agent-to-agent chat?**
Oral hand-offs don't survive parallel lanes, retries, or session restarts. The
ledger is the single state source: gates, issues, and logs are the only protocol
between agents, which makes every run resumable and every claim auditable.

## 13. ❓ FAQ

<details>
<summary><b>Do I need any LLM API keys?</b></summary>

No. The host agent (Codex CLI / Claude Code / Cursor) *is* the LLM — this repo
only adds skills and deterministic MCP tools on top of whatever subscription you
already have. The literature APIs (arXiv, OpenAlex, Crossref, DBLP) are free
without keys; a Semantic Scholar key is optional and only raises rate limits.
</details>

<details>
<summary><b>Can I use just one piece — say, only citation checking?</b></summary>

Yes. Each MCP server is independent: point your agent at `citation_server` and
call `verify_entry` / `audit_bibliography` on any `.bib` file — no loop, no
ledger required. Same for figures (`figure_server`) and search (`lit_server`).
The loop only enters when you want the full gated pipeline.
</details>

<details>
<summary><b>Why draw.io files instead of just SVG?</b></summary>

SVG is a rendering; `.drawio` (mxGraph XML) is a *model* — nodes keep their
identity, edges stay bound to endpoints, and your co-author can drag a box
without breaking arrows. Both are rendered from the same figspec source, so
they never drift apart.
</details>

<details>
<summary><b>How is citation trust actually enforced?</b></summary>

Zero-trust: every entry must be re-fetched from a primary source (DOI → Crossref,
arXiv ID → arXiv API) and field-compared — title, authors, year, venue. The
`citations_verified` gate blocks the writing stage until the audit passes, and
the adversarial reviewer must run `verify_entry` itself before calling any
citation fake.
</details>

<details>
<summary><b>My host isn't Codex / Claude Code / Cursor — can I still use this?</b></summary>

If your agent can read Markdown and speak MCP (stdio), yes. Skills are plain
Markdown with no host-specific syntax; servers are standard FastMCP processes.
Worst case, run the servers' Python APIs directly from your own harness.
</details>

<details>
<summary><b>How long does a full survey run take?</b></summary>

Depends on scale tier and host model speed: the 143-reference sample
(`examples/survey_cof_her`) took roughly one working session end-to-end,
including two adversarial review rounds and LaTeX compilation. Search and
verification are throttled to be polite to public APIs — that, not the LLM,
is usually the floor.
</details>

## 14. 🌐 Ecosystem

Sibling projects that this pipeline integrates with or grew out of:

| Project | What it is | How it plugs in |
| --- | --- | --- |
| [super_library](https://github.com/asimfish/super_library) | Academic writing corpus: phrase banks, section patterns, terminology lints | Writing-language authority for the survey-writer skill (style stage 0b) |
| [super_ref](https://github.com/asimfish/super_ref) | Reference verification toolkit | Shares the zero-trust citation philosophy behind `citation_server` |
| [super_skill_team](https://github.com/asimfish/super_skill_team) | A large team of agent skills for research workflows | The figure-studio lineage that informed our figspec pipeline |

## 15. 📖 Citation

```bibtex
@software{goai_research,
  title  = {GoAI Research: a multi-agent pipeline for literature surveys with
            verified citations and editable figures},
  author = {liyufeng},
  year   = {2026},
  url    = {https://github.com/asimfish/goai_research}
}
```

## 16. 🤝 License & Contributing

MIT License. Issues and PRs welcome — add a `skills/goai-*/SKILL.md`, wire it
into the loop protocol ([docs/LOOP_PROTOCOL.md](docs/LOOP_PROTOCOL.md)), and keep
the two iron rules: every claim carries a verifiable citation key, every figure
ships with its figspec source.

**A bad case is worth more than a star.** If a run produced an ugly figure, a
fake-looking citation, or a survey section that reads like a committee wrote it —
open an issue with the artifact attached. Real failure cases are what move the
lint rules and skill prompts forward.

<div align="center">

[![Star History Chart](https://api.star-history.com/svg?repos=asimfish/goai_research&type=Date)](https://star-history.com/#asimfish/goai_research&Date)

</div>
