# Proposal — Route C: Survey-to-Synthesis Bridge for TpPa-1

Slug: `route_c_tppa1` · Stage: ideas · Companion files:
`route_c_synthesis_plan.md` (full protocol), `experiment_route_c_tppa1.json` (machine-readable plan),
`state/retro_stub_demo.json` (stub integration demo, 演示数据非化学结论).

## 动机与缺口证据

1. **Gap (coverage/organization)**: TpPa-1 — the field's workhorse β-ketoenamine COF — has at
   least five distinct synthesis routes in the literature (solvothermal
   [kandambeth2012construction], mechanochemical [biswal2013mechanochemical], p-TsOH terracotta
   [karak2017constructing], microwave [wei2015the; grenu2020microwave], RT/flow [peng2016room;
   xu2026structural]), yet no side-by-side, decision-oriented tabulation for *process selection*
   exists in the library's reviews [wang2020covalent; chen2024photocatalysis; li2020new].
   Reviews organize by material family, not by process trade-off.
2. **Contradiction signal**: microwave heating gives TpPa-1 a ~4.8× BET gain over the
   conventional control in the direct comparison [grenu2020microwave, compiling wei2015the], yet
   for transimination-based quality upgrading, solvothermal *beats* microwave for β-ketoenamine
   COFs [grenu2020microwave]. The "best route" is therefore context-dependent — exactly what a
   decision-recorded plan must capture.
3. **Combination空位**: the ΔG_solv/Hansen/CHEM21 solvent-decision framework was published for
   TpPa-1 flow synthesis [xu2026structural] but has never been combined with the
   crystallinity-as-prime-factor evidence chain from HER benchmarking [ghosh2020identification]
   into one synthesis-design workflow targeting photocatalysis-grade material.

## 方法草图（与最近邻工作的差异）

- Build a five-route decision table with explicit selection/exclusion rationale anchored to
  quantified library data (§1 of the plan), then a per-step protocol whose every condition carries
  a library key or an explicitly labeled chemical-practice inference (§2).
- Nearest neighbors & differences:
  - vs [xu2026structural] (solvent framework only): we add route-level comparison + HER-facing
    quality criteria + thermodynamic audit.
  - vs [li2020new] / [grenu2020microwave] (method reviews): we target one material and produce an
    executable, safety-annotated protocol with a to-be-computed DFT list instead of a narrative.
  - vs [kandambeth2012construction] (origin protocol): we layer two quantified process
    optimizations (O1 microwave: 72 h→1 h, BET 152→725 m² g⁻¹; O2 flow/diacetin: 30× STY,
    −89 % energy, BET 418 m² g⁻¹) and a documented decision record.
- **Novelty boundary (explicit)**: no new chemistry is claimed — every reaction and number is
  literature-reported; the contribution is the *decision-recorded workflow* that converts survey
  evidence into a process selection, which none of the in-library reviews provides.

## 验证计划

- **Paper-internal validation** (this run): all cited keys ⊆ audited references.bib (37/37 PASS,
  `state/CITATION_AUDIT.md`); adversarial 4-dim review (evidence/novelty/feasibility/safety) +
  citation re-check before `ideas_reviewed`.
- **Computational validation** (listed, not fabricated): T1–T4 DFT items in plan §4 with
  recommended functionals/software; success criterion = keto sink confirmed (T1 < 0), per-bond
  condensation ΔG consistent with observed reversibility window (T2), AA stacking preferred (T3).
- **Experimental validation** (optional follow-up): three-batch comparison R1 vs O1 vs O2 on
  PXRD/BET/HER under the [sheng2019effect] deployment protocol; effect size expectation is set by
  the literature deltas above, not by new claims.

## 风险与替代路线

- **Risk: monomer quality drift** (Pa-1 oxidation) → sublimation before use; solubility-driven
  mild-condition growth degrades with impure feed [peng2016room].
- **Risk: O1 scale ceiling** (microwave penetration) → fall back to O2 flow, which is the
  scalability-optimized branch [xu2026structural; peng2016room].
- **Risk: crystallinity shortfall vs HER requirement** [ghosh2020identification] → R3 terracotta
  route as crystallinity rescue [karak2017constructing]; amorphous→crystalline reconstruction as
  a further fallback paradigm [zhang2022reconstructed].
- **Rejected alternative**: vinylene/sp²-carbon frameworks (better conjugation, harsher narrower
  chemistry [wang2022facile; li2023two]) — out of Route C scope, noted for future work.
