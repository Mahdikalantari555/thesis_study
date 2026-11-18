# 07 — Combined Drought and Salinity Stress (Angon et al., 2022)

**Full Citation:** Angon, P.B., et al. (2022). How Do Plants Respond to Combined Drought and Salinity Stress?—A Systematic Review. *Plants*, 11(21), 2884.  
**DOI:** [10.3390/plants11212884](https://doi.org/10.3390/plants11212884) | **Open Access**  
**Status:** ✅ Full read (2026-10-04)  
**Themes:** #Physiology #Salinity #Stress

---

## Core Finding

Combined drought + salinity stress produces **non-additive, interactive effects** — the joint impact is neither simply additive nor fully predictable from single-stress responses.

## Physiological Mechanisms

| Mechanism | Effect | Implication for Thesis |
|-----------|--------|----------------------|
| **Osmotic adjustment** | Salinity induces osmotic stress → reduces water uptake even if soil moisture present | Water stress signals persist under salinity |
| **Synergistic oxidative damage** | ROS accumulation under combined stress exceeds either stress alone | Mixed stress has unique spectral signature |
| **Antagonistic compensation** | Salinity can partially mitigate certain drought effects via osmotic adjustment | Complex, non-linear interactions |
| **Distinct gene expression** | Combined stress triggers unique transcriptional profiles vs. single stresses | Mixed class is qualitatively different |
| **Stomatal closure patterns** | Different kinetics under combined vs. individual stress | Temporal dynamics differ by stress type |

## Critical Implication for Thesis

> **"Mixed Stress" MUST be an explicit prediction class.** You cannot infer it from independent water-stress and salinity-stress predictions.

Model output must be: `[Healthy, Water_Only, Salinity_Only, Mixed_Stress]`

## Validation Requirement

Ground-truth labels must include mixed-stress fields with clear criteria:
- ECe > threshold AND CWSI > threshold simultaneously
- Distinct from pure classes in feature space

---

## Verified Full-Text Findings (2026-10-04)

Full read of all 15 pages (Secs. 1–5, Figs. 1–5, references). Meta-analysis of 30 original studies (536 records → 43 retrieved → 30 included, PRISMA Fig. 1, p.3); Welch's t-test on %-of-control values digitized from figures (Methods, p.3–4). Included experiments ran ≥7 days of stress: "Experiments conducted for a short period (<7 days) under stress conditions were omitted" (Methods, p.2). S = salinity, D = drought, S+D = combined.

### Response table (as the paper states it; all values % of control)

| Parameter | D vs control | S vs control | S+D vs control | Key between-stress contrasts | Source |
|---|---|---|---|---|---|
| Shoot dry weight | ↓ (small) | ≈ control | ↓↓ (lowest) | S+D −14% vs S (p=0.003); −16% vs D (p=0.021) | Fig. 2A; Sec. 3.1, p.4 |
| Root dry weight | ↑ (root proliferation) | ≈ control | ↓ | S+D −39% vs D (p=0.016); S+D vs S ns (p=0.167) | Fig. 2B; Sec. 3.1, p.4 |
| Plant height | ↓ | ↓ | ↓↓ | S+D −22% vs S (p<0.001); D vs S+D ns (p=0.077) | Fig. 2C; Sec. 3.1, p.4 |
| Relative growth rate | ↓ | ↓ | ↓ | S+D vs S p=0.046; S vs D ns (p=0.638) | Fig. 2D; Sec. 3.1, p.4 |
| Chl a | ↓ | ↓ | ↓↓ | S+D −25% vs D (p=0.031); S vs S+D ns (p=0.067) | Fig. 3A; Sec. 3.2, p.5 |
| Chl b, Chl a+b | ↓ (ns) | ↓ (ns) | ↓ (ns) | all ns; text: "statistically non-significant" | Fig. 3B,C; Sec. 3.2, p.5 |
| Net CO₂ assimilation (A) | ↓↓ (−30% vs S) | ↓ | ↓ | S+D vs S p<0.001; S+D vs D ns (p=0.541) | Fig. 3D; Sec. 3.2, p.5–6 |
| Transpiration (E) | ↓↓ (−27% vs S) | ↓ | ↓ | S+D vs S p=0.008; S+D vs D ns (p=0.576) | Fig. 3E; Sec. 3.2, p.6 |
| Stomatal conductance (gs) | ↓ (−17% vs S) | ↓ | ↓↓ (−25% vs S) | S+D vs S p<0.001; S+D vs D ns (p=0.238) | Fig. 3F; Sec. 3.2, p.6 |
| Na⁺ | ≈ control (lowest) | ↑↑ | ↑↑ | S+D vs D p<0.001; S+D vs S ns (p=0.801) | Fig. 4A; Sec. 3.3, p.6 |
| Cl⁻ | ≈ control (lowest) | ↑ | ↑ | S+D vs D p<0.001; S+D vs S ns (p=0.082) | Fig. 4C; Sec. 3.3, p.6 |
| K⁺ | ns | ns | ns | "no significant changes in K⁺ content" in any treatment | Fig. 4B; Sec. 3.3, p.6 |
| H₂O₂ | ↑ | ↑ | ↑↑ | S+D +52% vs D (p=0.022); S vs S+D ns (p=0.152) | Fig. 5A; Sec. 3.4, p.7 |
| MDA | ↑ | ↑ | ↑↑ | S+D vs S p=0.031; S+D vs D p=0.006; S vs D ns (p=0.645) | Fig. 5B; Sec. 3.4, p.7 |
| SOD, CAT, APX, POX | ↑ vs control | ↑ vs control | ↑ vs control | ns among S, D, S+D (all p>0.05) | Fig. 5C–F; Sec. 3.4, p.7–8 |
| Canopy/leaf temperature (Ts) | NOT MEASURED in this paper | — | — | — | parameter list, Methods p.3 |
| Proline, ABA, osmolytes | NOT MEASURED | — | — | "osmolytes play a crucial role... their roles under combined salinity and drought stress has not been reported... we were unable to include these in this meta-analysis" | Research gaps, p.10 |

Paper-internal wording error: Sec. 3.3 (p.6) says Na⁺/Cl⁻ "decreased by 347% and 115% in the S+D treatment compared to the drought treatment" — direction is wrong as written; Fig. 4 and Discussion (p.9: "Na⁺ and Cl⁻ contents were much higher in salinity and combined salinity-drought stress than in individual drought stress") show S+D ≫ D. Correct reading: S+D ≈ S (ns), both ≫ D.

### Interactivity evidence (non-additive)

- **Drought does not add to Na⁺/Cl⁻ load:** S+D ≈ S for Na⁺ (p=0.801) and Cl⁻ (p=0.082) — "water constraint in saline soils does not increase Na⁺ and Cl⁻ accumulation in plants" (Discussion, p.9). Additive expectation (S+D > S) is violated.
- **Stomatal/gas-exchange response saturates at the drought level:** S+D ≈ D for A (p=0.541), E (p=0.576), gs (p=0.238); the osmotic component dominates closure and salinity adds no further reduction (Discussion, p.9).
- **Synergistic damage where it counts:** S+D below BOTH single stresses for shoot biomass (−14%/−16%, p=0.003/0.021, Fig. 2A); H₂O₂ (+52% vs D) and MDA (p=0.031 vs S, p=0.006 vs D) highest under S+D while antioxidant enzymes stay flat → "the antioxidant enzyme system reaches a steady-state point or becomes exhausted" (p.10).
- **Antagonism on roots:** drought ↑ RDW, S+D pulls it 39% below drought (p=0.016) — salinity reverses drought's root-proliferation response (Fig. 2B).
- **The paper is explicit that responses are not uniformly non-additive:** intro cites an "additive adverse effect on photosynthesis" [22] (p.2) and Discussion notes salinity+drought "had an additive effect on dry-matter accumulation" [54–56] (p.8); overall effect "cannot be predicted based on plant responses to individual stresses" [21] (p.2). Conclusions: combined stress is worse overall, but which single stress dominates is parameter-specific — drought dominates photosynthesis, salinity dominates ionic imbalance (Conclusions, p.10–11).
- **Severity:** only qualitative — under SEVERE combined stress antioxidant enzymes (CAT, POX, SOD, glutathione reductase) show reduced activity [109–111], incl. halophyte *Halogeton glomeratus* [108] (p.10). No mild-vs-severe subgroup analysis; stress level is listed as a future sub-group analysis research gap (p.10).

### Repo-claim verification

- **Claim "Combined stress is interactive, not additive"** — ✅ VERIFIED with nuance (Abstract p.1; Sec. 3.1–3.4; Discussion p.8–10; Conclusions p.10–11): combined stress is worse than either single stress overall, but interactions are mixed — additive for dry matter/photosynthesis [22,54–56], non-additive for Na⁺/Cl⁻ (S+D≈S), gas exchange (S+D≈D), shoot biomass (S+D < both), oxidative damage. The strong version "neither simply additive nor fully predictable" (our Core Finding above) is consistent with the paper's "cannot be predicted based on plant responses to individual stresses" [21] (p.2).
- **Claim "physiological response table (gs↓, Ts↑, Na⁺↑, ROS, chlorophyll↓)"** — PARTIALLY VERIFIED: gs↓ ✅ (S+D −25% vs S, Fig. 3F); Na⁺↑ ✅ but only vs drought — S+D ≈ salinity alone (Fig. 4A); chlorophyll↓ ✅ for Chl a only (Fig. 3A; Chl b ns); ROS ✅ via proxies H₂O₂/MDA (Fig. 5A,B) — ROS itself never measured. **Ts↑ NOT FOUND** — canopy/leaf temperature is not among the paper's parameters (Methods p.3); ↑Ts is only inferable from transpiration ↓ (Fig. 3E).

### Labeling + XAI checklist implications

- **Operational labeling criteria: NOT FOUND.** The paper gives physiology only — no ECe, CWSI, or soil/plant thresholds for labeling fields Mixed_Stress; all included studies were ≥7-day controlled-condition experiments with %-of-control endpoints, not field diagnostics. The "ECe > threshold AND CWSI > threshold" rule in our Validation Requirement section is OUR proposal, not Angon et al.'s — do not cite it to this paper.
- XAI explanations for Mixed_Stress should attribute gas-exchange/canopy-temperature features (gs, CWSI proxies) at drought-like levels, NOT additive extremes — S+D ≈ D for gs/A/E (p=0.238/0.541/0.576).
- Salt-indicator features (chlorosis/Chl a decline) should appear at salinity-like magnitude in Mixed predictions — Chl a: S+D ≈ S (p=0.067), and K⁺ unchanged — explanations must not require Na⁺/Cl⁻ amplification beyond Salinity_Only (p=0.801/0.082).
- Vigor/biomass-related spectral features should show the amplified drop (SDW −14%/−16% below both singles, PH −22% vs S) — this is where Mixed_Stress should separate most cleanly from pure classes in feature space.
- Damage/necrosis features may be disproportionately strong (H₂O₂ +52% vs D, MDA p=0.031/0.006) with flat antioxidant response — consistent with a unique Mixed_Stress spectral signature, but this is oxidative-damage physiology, not a directly imageable marker.
- Proline, ABA, and canopy temperature are NOT covered by this paper — validate any checklist items on those markers against other sources (e.g., the osmolyte research gap the authors flag, p.10).

### Corrections to pre-existing note content

- "Antagonistic compensation: salinity mitigates drought via osmotic adjustment" — NOT FOUND as stated (osmolytes/osmotic adjustment not analyzed; closest real antagonism is on root biomass, Fig. 2B).
- "Distinct gene expression... unique transcriptional profiles" — NOT FOUND (transcriptomics is only recommended as future work, p.10).
- "Stomatal closure patterns: different kinetics" — NOT FOUND (paper reports magnitudes, no kinetics; finding is S+D ≈ D).
- Sugarcane/Saccharum: NOT FOUND anywhere in the paper (checked full text; ref 69 is sugar *beet*). Evidence base = herbaceous annual crops (wheat, barley, cotton, maize, tomato, potato, rice, sunflower, quinoa, cabbage; named in Discussion p.8 and reference titles); the full 30-paper species list is in Supplementary Table S1 (not in this PDF).

---

*Linked from: [[Literature-Matrix]]*
