# Pre-Registered Idea: Mixed-Linker D–A Doping of TpPa-1

Status: pre-registered (gates locked before synthesis). Paper Section 6; Figure 2
(`figures/pdf/fig2_tppa1_idea.pdf`, editable source `figures/drawio/fig2_tppa1_idea.drawio`).

## Hypothesis

Installing a fraction x of electron-accepting benzothiadiazole-diamine
BT(NH2)2 into the Pa-1 position of TpPa-1 creates local D–A dipoles that
lower exciton binding energy and raise charge-separation yield, while the
tautomer-locked Tp node preserves chemical stability.

Causal-chain position: acts on link 3–4 (band structure → exciton
dissociation) of the Fig. 1 factor chain.

## Design (Lane A)

- Series: x ∈ {0.05, 0.10, 0.25, 0.50}, statistical copolymerization.
- Fixed conditions: 120 °C, 3 d, dioxane/mesitylene, same batch of Tp.
- Matched controls (pre-committed): x = 0 baseline; physical blend
  (TpPa-1 + TpBT ground mix); amorphous analogue (same composition,
  fast-quench synthesis, identical activation).
- Precedent: benzothiadiazole-dianiline COFs are established HER platforms
  (chen2025modulating; liu2024dual); factor-isolation design follows
  ghosh2020identification / jiang2024significant / dong2025synergistic.

## Measurements (Lane B)

1. Structure and porosity QC: PXRD (line width vs baseline), BET, TGA.
2. Band and center mapping: Tauc, Mott–Schottky, UPS; CB edge vs NHE.
3. Exciton/charge: fs-TA (tau_CS), TRPL quenching, SPV, EIS.
4. HER assay (matched): 3 wt% Pt photodeposited, 10 vol% TEOA,
   >= 420 nm cutoff, stirred suspension, GC-TCD quantification;
   AQY at 420 nm.
5. Stability protocol: 5 x 4 h cycles (20 h), post-run PXRD/FTIR/XPS/ICP-MS.

## Gates (Lane C)

- G1 structure retained: PXRD width <= 1.3x baseline AND BET >= 0.7x baseline.
- G2 mechanism gain: tau_CS >= 2x baseline AND CB edge <= -0.3 V vs NHE.
- G3 activity gain: HER rate >= 2x baseline AND AQY(420) >= 5%,
  vs x = 0 and blend controls under the matched assay.
- G4 durable: >= 80% rate retention over 20 h with structural verification.

## Fallbacks (pre-committed)

- G1 fail → reduce x to {0.02, 0.05}, re-optimize solvent acidity.
- G2 fail → pivot lever to post-synthetic protonation
  (yang2021protonated; he2024double; duan2024protonated).
- G3 fail → single-atom cocatalyst at matched loading
  (dong2021platinum; chen2024low).
- G4 fail → substitute milder pyridine-diamine acceptor.

## Outcome rule

All gates pass → adopt best x* as new baseline. Fallback tree exhausted →
report bounded negative: "D–A dipole density insufficient at preserved
crystallinity for the beta-ketoenamine family" (publishable constraint).

## Safety (pre-registered)

Sealed-tube pressure rating and shielding; dioxane/mesitylene handling in
fume hood; Pt salt waste segregation; H2 venting and LEL monitoring on the
photoreactor line.
