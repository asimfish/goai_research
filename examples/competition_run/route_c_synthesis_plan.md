# Route C — Synthesis & Process Design Plan for TpPa-1

**Target**: β-ketoenamine COF **TpPa-1**
**Monomers**: 1,3,5-triformylphloroglucinol (**Tp**, SMILES `O=Cc1c(O)c(C=O)c(O)c(C=O)c1O`) +
p-phenylenediamine (**Pa-1**, SMILES `Nc1ccc(N)cc1`), stoichiometry **2 Tp : 3 Pa-1**
(3×CHO vs 2×NH2 functional balance) [kandambeth2012construction].
**Evidence base**: all cited keys live in `library/references.bib` (37/37 PASS in
`state/CITATION_AUDIT.md`, 2026-08-27). No key outside the audited pool is used.
**Retro backend status**: `provider=stub` — stub output is kept **only** as a systems-integration
demo in `state/retro_stub_demo.json` and §6; it is labeled 「演示数据，非化学结论」and
contributes nothing to the chemistry below, which is built from library literature + explicit
chemical reasoning.

---

## 1. Route selection — candidate comparison & decision record

Five synthesis routes for TpPa-1 (or its β-ketoenamine family) are documented in the library.
Decision criteria, in order: (i) photocatalysis-grade crystallinity/porosity — crystallinity is a
prime HER factor [ghosh2020identification]; (ii) reproducibility & literature depth for the exact
target; (iii) scalability/greenness as secondary optimization axes [xu2026structural].

| # | Route | Conditions (as reported) | Reported quality for TpPa family | Source (database) | Verdict |
|---|-------|--------------------------|----------------------------------|--------|---------|
| R1 | **Solvothermal (baseline)** | 1:1 mesitylene/dioxane, aqueous AcOH catalyst, 120 °C, 72 h, sealed tube | Canonical TpPa-1: crystalline, stable to 9 N HCl & boiling water | kandambeth2012construction (Crossref) | **SELECTED as baseline** — richest protocol record; the reference material for all later comparisons |
| R2 | Mechanochemical grinding | Room temperature, solvent-free | Moderate crystallinity vs solvothermal; exfoliated graphene-like layers; stability retained | biswal2013mechanochemical (OpenAlex) | **EXCLUDED for HER batches** — lower crystallinity/surface area directly penalizes the prime factor [ghosh2020identification]; retained as greenest option for sorbent-grade material |
| R3 | p-TsOH salt-mediated ("organic terracotta") | Seconds-scale crystallization; twin-screw extruder demonstrated for continuous processing | Highly crystalline, ultraporous (family surface areas up to 3000 m² g⁻¹) | karak2017constructing (Crossref) | **RESERVED for scale-up** — fastest route, but acid-salt work-up adds steps and the highest-SA values are for the wider family, not TpPa-1 specifically |
| R4 | Microwave-assisted solvothermal | 100 °C, 1 h (vs 120 °C, 3 d conventional) | TpPa-1-MW BET 725 m² g⁻¹ vs 152 m² g⁻¹ for the conventional control in the same comparison | wei2015the (OpenAlex); numbers compiled in grenu2020microwave (OpenAlex) | **SELECTED as Optimization O1** |
| R5 | RT batch / continuous flow | Room temperature batch (TpPa-1 demonstrated); flow with green-solvent selection (diacetin) | RT batch: crystallinity/porosity comparable to solvothermal; flow TpPa-1: BET 418 m² g⁻¹, 30× STY, −89 % specific energy vs batch | peng2016room (OpenAlex), xu2026structural (Crossref) | **SELECTED as Optimization O2** |

**Why not an alternative linkage/framework?** The survey's factor chain (taxonomy L1–L5) shows the
β-ketoenamine linkage uniquely combines synthesizability from cheap monomers with acid/base/water
stability via the irreversible keto lock [kandambeth2012construction; haase2020solving] — the
stability envelope needed for aqueous photocatalysis. Fully conjugated vinylene COFs offer better
in-plane conjugation but demand harsher, narrower-scope condensations [wang2022facile; li2023two],
so they are noted as future work, not Route C.

## 2. Step-by-step protocol (baseline R1, with per-step evidence)

### Step 0 — Monomer sourcing & preparation
| Item | Plan | Evidence / reasoning |
|------|------|----------------------|
| Tp (1,3,5-triformylphloroglucinol) | Purchase where available; otherwise prepare by Duff-type formylation of phloroglucinol (hexamethylenetetramine route) as in the TpPa-1 origin literature prep | kandambeth2012construction (monomer & literature prep; protocol level in paper body) |
| Pa-1 (p-phenylenediamine) | Commercial; purify (sublimation or recrystallization) immediately before use; store cold, dark, under N₂ | Chemical-practice inference (aromatic diamines air-oxidize, colored impurities disrupt stoichiometric balance); monomer purity/solubility is flagged as an enabler of mild-condition COF growth [peng2016room] |
| Stoichiometry | 2 Tp : 3 Pa-1, degassed solvent mixture | Functional-group balance 3×CHO / 2×NH₂ [kandambeth2012construction] |

### Step 1 — Schiff-base polycondensation (solvothermal baseline)
- **Conditions**: Tp + Pa-1 (2:3) in 1:1 (v/v) mesitylene/1,4-dioxane with aqueous acetic acid
  catalyst, sealed tube, 120 °C, 72 h (protocol per origin paper; abstract confirms the solvent
  system and Schiff-base chemistry) [kandambeth2012construction].
- **Mechanistic rationale (why these conditions)**: acid-catalyzed imine formation is *reversible*
  at 120 °C, allowing error correction that produces a crystalline network under thermodynamic
  control; the solvent pair tunes monomer solubility/reversibility balance
  [kandambeth2012construction; haase2020solving]. Moderate-solvation media suppress *excessive*
  reversibility and promote crystallite growth — the quantitative solvent-selection logic (CHEM21
  greenness + Hansen parameters + ΔG_solv) is adopted from the TpPa-1 flow study
  [xu2026structural].
- **In-situ lock**: the initially formed enol-imine tautomerizes **irreversibly** to the
  β-ketoenamine; only the keto form is observed, removing hydrolyzable imine character
  [kandambeth2012construction].

### Step 2 — Work-up & activation
- Cool slowly; collect precipitate; wash with anhydrous acetone/DMAc-type solvents to remove
  oligomers and residual monomer; solvent-exchange to a low-boiling solvent; vacuum-dry
  (work-up level per origin & terracotta protocols) [kandambeth2012construction;
  karak2017constructing].
- For R3 variant: p-TsOH salt must be removed by thorough water washing before activation
  [karak2017constructing].

### Step 3 — Photocatalyst deployment (context for HER use)
- Load Pt cocatalyst by in-situ photodeposition and run sacrificial HER, following the TpPa-COF-X
  benchmark setup [sheng2019effect]; Pt speciation (nanoparticle → cluster → single-atom) is a
  separately tunable activity factor [dong2021platinum; li2022in].

## 3. Process optimizations (quantified, ≥2)

### O1 — Microwave-assisted synthesis: −98.6 % time, −20 °C, ~4.8× surface area
- Conventional: 120 °C, 3 days. Microwave: **100 °C, 1 h** — same enamine chemistry
  [wei2015the].
- Quantified outcome for TpPa-1 in the direct comparison compiled by the microwave review:
  **BET 725 m² g⁻¹ (MW) vs 152 m² g⁻¹ (conventional control)** — a ~4.8× porosity gain at
  lower temperature and 1/72 of the time [grenu2020microwave, compiling wei2015the].
- Trade-off recorded: for post-synthetic *transimination* quality boosts, solvothermal still
  outperformed microwave for β-ketoenamine COFs [grenu2020microwave] — so O1 is an optimization
  of the *direct* route, not a universal replacement.

### O2 — Green-solvent continuous flow: 30× STY, −89 % energy
- Solvent decision pathway (CHEM21 + Hansen + ΔG_solv) identifies **diacetin** as optimal for
  TpPa-1 flow synthesis; flow product reaches **BET 418 m² g⁻¹** with **30× space-time-yield**
  and **89 % lower specific energy consumption** vs batch in the same solvent, and +50 % CO₂
  uptake at 298 K [xu2026structural].
- Feasibility anchor: room-temperature batch TpPa-1 already matches solvothermal
  crystallinity/porosity, and COF flow production was demonstrated at **41 mg h⁻¹**
  (STY 703 kg m⁻³ day⁻¹, COF-LZU1) [peng2016room].

### O3 (reserve) — p-TsOH salt-mediated rapid crystallization
- Seconds-scale formation of highly crystalline, ultraporous frameworks (family record
  ~3000 m² g⁻¹); twin-screw extrusion demonstrates continuous, near-solvent-free processing
  [karak2017constructing]. Reserved because TpPa-1-specific quantitative data in-library are
  thinner than for O1/O2.

## 4. Thermodynamic feasibility audit

**Literature-supported statements** (no invented numbers):
1. **Two-stage thermodynamic design**: reversible imine equilibrium (error-correcting,
   crystallinity-enabling) followed by an **irreversible enol→keto tautomerization** — only the
   keto form is observed, i.e. the β-ketoenamine is the thermodynamic sink of the tautomer
   manifold [kandambeth2012construction].
2. **Product stability as thermodynamic evidence**: retained crystallinity in 9 N HCl and boiling
   water (both solvothermal and mechanochemical product) [kandambeth2012construction;
   biswal2013mechanochemical].
3. **Solvation thermodynamics**: ΔG_solv-guided solvent ranking shows moderate solvation
   (1,4-dioxane, propylene carbonate, diacetin) hinders excessive reversibility and promotes
   crystallite growth [xu2026structural].
4. **General trade-off**: framework-forming reversibility correlates with crystallinity but
   anti-correlates with chemical robustness — the trilemma the keto lock circumvents
   [haase2020solving; zhang2022reconstructed].

**To-be-computed list** (values absent from the library; DFT recommendations, *no numbers
fabricated here*):
| # | Quantity | Model | Recommended setup |
|---|----------|-------|-------------------|
| T1 | ΔE(keto − enol) of the tautomer pair | Trianil model of Tp + 3 aniline | ωB97X-D/def2-TZVP (or B3LYP-D3(BJ)/6-311+G(d,p)), SMD(dioxane) and SMD(water), Gaussian16/ORCA |
| T2 | Per-bond imine condensation ΔG (298 K, 393 K) | Tp + Pa-1 monomer model, explicit H₂O release | Same level as T1; thermal corrections at both temperatures |
| T3 | Periodic formation energy & AA vs AB stacking energy of TpPa-1 | Periodic slab/bulk | PBE-D3(BJ) plane-wave (VASP/CP2K), standard 500–550 eV cutoff class settings, Γ-centered k-mesh (settings = recommendation, to be converged) |
| T4 | ΔG_solv of Tp/Pa-1 in candidate solvents | COSMO-RS | Extends the solvent framework of [xu2026structural] to monomer speciation |

Experimental validation (PXRD/BET/HER of O1 vs O2 vs R1 batches) is **optional follow-up work**,
not claimed here.

## 5. Safety assessment (mandatory)

| Hazard | Applies to | Controls |
|--------|-----------|----------|
| p-Phenylenediamine: toxic, potent skin sensitizer, suspected mutagen | Step 0/1 | Nitrile gloves, goggles, fume hood, no dust exposure; sealed storage under N₂ |
| In-house Tp preparation (Duff-type formylation): concentrated-acid handling; hexamethylenetetramine thermal decomposition | Step 0 (only if Tp made in-house) | Face shield, fume hood, controlled quench of acidic mixture; prefer commercial Tp when available |
| 1,4-Dioxane: suspected carcinogen, peroxide former | Step 1 (R1) | Fume hood; peroxide test before use; never evaporate to dryness; substitute per CHEM21 ranking where possible [xu2026structural] |
| Mesitylene: flammable irritant | Step 1 | Fume hood, ignition control |
| Acetic acid (aqueous catalyst): corrosive | Step 1 | Acid-resistant gloves/face protection |
| Sealed-tube 120 °C: autogenous pressure | Step 1 (R1) | Pressure-rated ampoule/autoclave, blast shield, slow cooling before opening |
| Microwave heating of sealed vessels | O1 | Only microwave-rated reactors with T/p monitoring and pressure relief [grenu2020microwave] |
| p-TsOH: corrosive solid | O3 | Gloves/goggles; complete aqueous removal before activation [karak2017constructing] |
| H₂ evolution testing: flammable/explosive gas mixtures | Step 3 | Gas-tight degassed reactor, inert headspace, H₂ kept below explosive accumulation, ventilated GC sampling [sheng2019effect setup context] |
| H₂PtCl₆ for photodeposition: corrosive, sensitizer | Step 3 | Gloves, fume hood |
| Waste | All | Amine and halogen-free organic waste segregated as hazardous |

## 6. Retro-stub integration demo (演示数据，非化学结论)

`predict_retro` / `make_experiment_plan` were invoked against the stub backend
(`provider=stub`, `verified=false`) to demonstrate the idea-forge ↔ retro MCP integration;
raw output: `state/retro_stub_demo.json`. The stub's placeholder disconnections
(`PRECURSOR-A1-*` etc.) are **demo data only, not chemical conclusions**, and are excluded from
every chemical statement in this plan. A production run would set `GOAI_RETRO_PROVIDER=http`
(ASKCOS/RXN) and cross-validate the literature route above.

## 7. Characterization plan

- **PXRD** — crystallinity vs simulated pattern [kandambeth2012construction]; stacking-disorder
  risk during photocatalytic cycling is a separate known failure mode to monitor post-run
  [zhou2021peg].
- **FT-IR / ¹³C CP-MAS NMR** — keto-form signature confirming complete tautomerization
  [kandambeth2012construction].
- **N₂ sorption (BET)** — benchmark against 725 m² g⁻¹ (O1) / 418 m² g⁻¹ (O2 flow) references
  [grenu2020microwave; xu2026structural].
- **TGA, SEM/TEM** — thermal stability, morphology (exfoliation check per mechanochemical
  contrast) [biswal2013mechanochemical].
- **UV-vis DRS + Tauc, PL** — optical gap and recombination diagnostics for HER deployment
  [sheng2019effect].
- **Chemical stability** — 9 N HCl / boiling-water soak with PXRD/BET retention
  [kandambeth2012construction].
