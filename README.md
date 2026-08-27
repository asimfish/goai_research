<div align="center">

# GoAI Research 📚⚔️

**Multi-agent pipeline that turns a research topic into a survey paper — with citations you can trust and figures you can still edit.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-17%20passing-brightgreen.svg)](tests/test_offline.py)
[![MCP](https://img.shields.io/badge/MCP-4%20servers%20%C2%B7%2019%20tools-8A2BE2.svg)](server/)
[![Skills](https://img.shields.io/badge/skills-8%20agents-orange.svg)](skills/)

[中文版 README](README_CN.md) | English

</div>

> 🔍 **Search everything. Trust nothing unverified. Ship figures that stay editable.**
> Five-source literature search with snowballing, zero-trust citation verification,
> figures rendered simultaneously as paper-ready SVG **and** native draw.io files,
> idea generation with a pluggable retrosynthesis backend — all wired into a
> ledger-driven loop where an adversarial reviewer routes rework until every gate passes.

> 🪶 **Lightweight by design, zero lock-in.** The intelligence layer is 8 plain-Markdown
> skills readable by any LLM agent — Codex CLI, Claude Code, Cursor, or your own harness.
> The deterministic layer is 4 small MCP servers you can test offline. No framework,
> no database, no daemon. Fork it, rewrite it, adapt it to your stack.

![GoAI Research pipeline](examples/pipeline.png)

*This figure was drawn by the system itself: one [`figspec`](examples/pipeline.figspec.json) source file rendered into [`pipeline.svg`](examples/pipeline.svg) (for papers), [`pipeline.drawio`](examples/pipeline.drawio) (open it in draw.io and keep editing), and the PNG above (for self-check).*

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
13. [Citation](#13--citation)
14. [License & Contributing](#14--license--contributing)

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

# Codex CLI
cat configs/codex.config.toml >> ~/.codex/config.toml
ln -s "$PWD/skills"/goai-* ~/.codex/skills/

# Claude Code
#   merge configs/claude.mcp.json into ~/.claude.json (mcpServers)
ln -s "$PWD/skills"/goai-* ~/.claude/skills/

# smoke check
.venv/bin/python -m pytest tests/ -q     # 17 offline tests, no network needed
```

Requirements: Python ≥ 3.10 (install.sh uses [uv](https://github.com/astral-sh/uv) if
available). Optional extras: `brew install --cask drawio` (export .drawio → png/pdf),
`.venv/bin/pip install -e '.[preview]'` (PNG previews for figure self-checks),
Node.js (official [draw.io MCP](https://github.com/jgraph/drawio-mcp) for live browser editing).

## 3. 🧩 What's Inside

**Start here** — use case → entry point:

| Use case | Start here |
|---|---|
| Topic → full survey, end to end | [goai-orchestrator](skills/goai-orchestrator/SKILL.md) |
| Find every relevant paper + PDFs + BibTeX | [goai-lit-search](skills/goai-lit-search/SKILL.md) |
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
| `skills/` — 8 SKILL.md | Methodology the host LLM executes: taxonomy building, claim-bound writing, review judgment | Cognitive work stays with the strongest available model; skills carry no API keys and no LLM SDKs |
| `server/` — 4 MCP servers, 19 tools | Search aggregation & dedup, BibTeX parsing & author comparison, figspec validation & dual rendering, retrosynthesis adapter | Deterministic heavy lifting: testable offline, reusable across hosts |
| `tools/` | `loopctl.py` ledger CLI · `bib_guard.py` citation gate · `parallel_run.sh` | Loop control and hard gates: pure local, zero LLM |

| MCP server | Tools |
|---|---|
| `goai-litsearch` | `search_papers` `snowball` `lookup` `download_pdf` `save_to_library` `export_bibtex` `coverage_report` |
| `goai-refcheck` | `verify_entry` `verify_bib_file` `deep_audit_info` |
| `goai-figure` | `figspec_schema` `validate_figspec` `render_figure` `svg_file_to_drawio` `drawio_export` `list_figures` |
| `goai-retro` | `provider_status` `predict_retro` `make_experiment_plan` |

</details>

<details>
<summary><b>Workspace layout</b> — everything lands on disk, auditable</summary>

```
workspace/
├── library/     papers.jsonl + references.bib + pdfs/
├── notes/       scope / taxonomy / citation_bank / figure_plan
├── figures/     svg/ + drawio/ + figspec/ + png/   ← same source, never drift
├── drafts/      blueprint + sections/*.tex + revision_log
├── ideas/       proposal_*.md + experiment_*.json + review_log
└── state/       ledger.json (the loop ledger) + audit reports
```

</details>

## 4. 🔄 The Loop

```
intake → scoping → lit_search → ref_gate → taxonomy
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
| lit_search | goai-lit-search | `lit_coverage` — all subtopics covered, marginal gain < 5% |
| ref_gate | goai-ref-guard | `ref_integrity` — zero UNVERIFIED / MISMATCH entries |
| taxonomy | goai-survey-writer | `taxonomy_ready` — every leaf backed by ≥ 3 papers |
| figures | goai-figure-studio / -editable | `figures_ready` — svg + drawio for every figure |
| writing | goai-survey-writer | `draft_complete` — bib_guard PASS, all sections done |
| ideas | goai-idea-forge | `ideas_reviewed` — adversarial review + second citation pass |
| review | goai-reviewer | `review_pass` — 0 blockers and 0 majors |

## 5. 🎨 Figures That Stay Editable

A figure here is never a dead bitmap. The single source of truth is a **figspec** —
a small JSON describing nodes, groups, edges, and texts. One render call emits:

- `figures/svg/<name>.svg` — for LaTeX (`\includesvg`, or export pdf via drawio CLI)
- `figures/drawio/<name>.drawio` — **native mxGraph XML**: open in
  [draw.io](https://app.diagrams.net) / draw.io Desktop, drag nodes, edges follow
  (source/target are bound, not painted)
- `figures/png/<name>.png` — for the agent's own render → self-check → fix loop (≤ 3 rounds)

Already have a figure that isn't a figspec?

- **Structured SVG** → `svg_file_to_drawio` reverses it deterministically
  (recovers group containers, attaches edge labels, then re-renders)
- **Bitmap / PDF figure** → `goai-figure-editable` runs a visual-reconstruction loop:
  read the image → structured inventory → figspec → render → side-by-side compare → fix

Editability acceptance is explicit: text must be native text, shapes draggable,
edges bound to nodes — "looks similar" doesn't pass.

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
4. **Draft-side gate** (`bib_guard.py`): undefined `\cite` keys block the build;
   orphan bib entries and low citation density (< 8 / 1000 words) warn.
5. **Context check** (reviewer): samples claim–citation pairs and verifies the cited
   paper actually supports the claim — the most diagnostic and most-missed check.

## 7. 💡 Idea Forge & Retrosynthesis

`goai-idea-forge` mines three gap signals from the verified library — coverage gaps
(subtopics nobody addressed), contradiction signals (papers disagreeing), and
combination holes (two taxonomy branches never crossed) — and every proposal must
carry real citation keys as evidence.

For chemistry / materials ideas it calls the `goai-retro` MCP server:

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
# tasks.tsv: <name>\t<prompt> per line
bash tools/parallel_run.sh --backend codex --jobs 3 tasks.tsv   # or --backend claude
```

Rules that keep parallelism safe: each task writes only its own shard files
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
| `GOAI_RETRO_PROVIDER` | `stub` | `stub` (demo) or `http` (real predictor) |
| `GOAI_RETRO_API_URL` / `GOAI_RETRO_API_KEY` | — | Retrosynthesis backend endpoint / auth |
| `GOAI_DRAWIO_CLI` | auto-detect | Path to draw.io Desktop CLI for exports |
| `S2_API_KEY` | — | Optional Semantic Scholar key (higher rate limits) |

## 11. 🧪 Testing

```bash
.venv/bin/python -m pytest tests/ -q    # 17 offline tests — no network, no LLM
```

Covered: BibTeX parse/format round-trip, author comparison (abbreviations, order,
missing/fabricated), multi-source dedup, figspec validation (including node-overlap
detection), SVG and mxGraph rendering, **SVG → figspec → drawio round-trip**
(groups recovered as containers, edge labels reattached), retro stub + plan
skeleton, full loopctl ledger cycle, and bib_guard blocking behavior.

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

**Why a ledger instead of agent-to-agent chat?**
Oral hand-offs don't survive parallel lanes, retries, or session restarts. The
ledger is the single state source: gates, issues, and logs are the only protocol
between agents, which makes every run resumable and every claim auditable.

## 13. 📖 Citation

```bibtex
@software{goai_research,
  title  = {GoAI Research: a multi-agent pipeline for literature surveys with
            verified citations and editable figures},
  author = {liyufeng},
  year   = {2026},
  url    = {https://github.com/asimfish/goai_research}
}
```

## 14. 🤝 License & Contributing

MIT License. Issues and PRs welcome — add a `skills/goai-*/SKILL.md`, wire it
into the loop protocol ([docs/LOOP_PROTOCOL.md](docs/LOOP_PROTOCOL.md)), and keep
the two iron rules: every claim carries a verifiable citation key, every figure
ships with its figspec source.
