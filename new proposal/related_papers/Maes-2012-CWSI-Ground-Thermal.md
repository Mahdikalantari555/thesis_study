# 39 — Ground-Based Thermal Remote Sensing for ET and Drought Stress: A Review (Maes & Steppe, 2012)

**Full Citation:** Maes, W. H., & Steppe, K. (2012). Estimating evapotranspiration and drought stress with ground-based thermal remote sensing in agriculture: a review. *Journal of Experimental Botany*, *63*(13), 4671–4712. https://doi.org/10.1093/jxb/ers165
**DOI:** [10.1093/jxb/ers165](https://doi.org/10.1093/jxb/ers165) | Open Access (OUP JXB) | JXB "Darwin review" | 42 pp.
**Status:** ✅ Full read (2026-10-20) — body read (abstract, §1, §3 theory/modelling, §4.2–4.5 index family, §5); §2 and the reference list skimmed
**Themes:** #CWSI #Thermal #Stress-physiology #Review

---

## Corpus & Scope

- Narrative "Darwin review" (JXB's review category), 5 sections: thermal-RS basics → T_s↔sensible/latent heat relations → application methods → future challenges. **Page convention:** the extract's 42 PDF pages = printed pp. 4671–4712 (offset +4670); printed pages cited below.
- **Explicitly ground-based** (IR thermometers, thermal cameras); satellite and high-altitude airborne techniques are excluded and delegated to other reviews (p. 4672) — the transferable content is the *physics*, not the hardware.
- Inventories: Table 1 (abbreviations), Table 2 (CWSI per crop), Table S1 (non-water-stressed baselines for **39 different crops**, p. 4688), Supplementary Data S1–S6 (Ts–flux derivations, resistances, CWSI derivation, Rni).

## What It Does

Canonical review of canopy/leaf temperature as an indicator of evapotranspiration and drought stress. It derives the leaf- and canopy-scale energy balance linking transpiration to surface temperature, uses the authors' own model to test how T_s responds to weather and canopy structure, and organises the ground-thermal index family — stress time, stress degree day, CTD, **CWSI** (analytical / empirical / direct), WDI, the stomatal conductance index I_g and the **3T model** — with a sensitivity and discriminative-power analysis of each. Its CWSI/CTD formulations are the reference framework for *any* thermal stress index, including spaceborne ones.

## Key Methodology

- One-source leaf energy balance + canopy aerodynamics, simulated at reference conditions: T_a = 25 °C, K_in = 700 W m⁻², z_u = 3 m, u = 2 m s⁻¹, δe = 1590 Pa (Hr = 50 %); canopy α = 0.20, h_c = 1 m, LAI = 2 m² m⁻², ε = 0.98, z0M = 0.13 h_c, d = 0.64 h_c (p. 4683).
- Monte-Carlo error propagation: **5000** samples per configuration; temperature-measurement SD **0.18 °C** (CWSI_d), 0.1 °C (T_a, 3T model); 95 % CI as ±2σ; reference-vs-measured mismatch simulated at ±10 % for u, K_in, δe, leaf angle/size/shape/albedo and ±0.2 °C for T_a (pp. 4689–4690, 4694, 4699). g_s levels tested: **20, 200, 600 mmol m⁻² s⁻¹**; "discriminative power" = the range of g_s statistically distinguishable from a given index value (p. 4690).

## Key Findings

- **CWSI (eq. 41):** CWSI = (T_pot − T_c)/(T_pot − T_dry) = 1 − λE/λE_pot, with ΔT_pot = T_pot − T_a, ΔT_dry = T_dry − T_a, ΔT_a = T_c − T_a (p. 4687). Assumptions: one-source, r_aH = r_aV = r_aM (Reynolds analogy), R_n equal for wet/dry/actual crop, S = 0, G_i = 0, **T_s = T_c** — "in partially vegetated fields, this assumption is problematic" (p. 4688), where CWSI is *overestimated* (p. 4691).
- **CWSI_a (analytical, Jackson et al. 1981):** needs r_aH, r_c,pot and r_c/r_aH (eq. 42); most studies compute ΔT_pot (eq. 43) and ΔT_dry (eq. 44) directly. "The large input requirements have hampered a routine use"; main error sources u, R_n, T_a, T_c (p. 4688).
- **CWSI_e (empirical, Idso et al. 1981a):** ΔT_pot = a_pot + b_pot·δe (eq. 45); ΔT_dry = a_pot + b_pot[e*(T_a) − e*(T_a + a_pot)] (eq. 46); became "the most commonly used thermal drought stress index" (p. 4689). **Key weakness:** a_pot and b_pot are "not entirely crop specific or weather independent" — they change with T_a, u and K_in, so CWSI_e "requires stable weather conditions (preferably hot and dry, with open skies)" and measurements only around solar noon; the baseline drifts within and between seasons with crop height and leaf area (p. 4689).
- **CWSI_d (direct, eq. 49):** (T_l − T_wet)/(T_dry − T_wet) from petroleum-jelly-coated (dry) and water-sprayed (wet) reference leaves; with a thermal camera the references can be embedded in the scene, so "no additional meteorological measurements are required" and emissivity/geometry errors cancel (p. 4690). But CWSI_d "does not tend to zero" even at very high g_s (T_wet ≪ T_pot) and its lower bound depends on T_a, u, A_l and leaf shape, "which complicates the interpretation"; at canopy scale ΔT_dry "is usually set arbitrarily at 5 °C" (p. 4692). Field use relies on wet artificial reference surfaces (WARS: water tray + foam + absorbent cloth), which correlated better with leaf water potential than CWSI_a (p. 4692).
- **WDI (Moran et al. 1994)** repairs T_s ≠ T_c by relating ΔT to fractional cover or a VI (eq. 52); the analytical form needs R_n, δe, u, T_a, LAI, h_c, r_aH, SAVI → "applied in a very limited number of studies"; the empirical form (Clarke 1997) is an airborne method (pp. 4691–4694).
- **I_g (eqs. 57–58)** is *linear* in g_s (unlike CWSI_d) and insensitive in expectation to K_in, δe, leaf angle and albedo. Worked example (Jatropha): T_dry = 27.3 °C for both plants, T_wet 19.4 (drought) vs 18.4 °C (control); control T_l = 24.8 °C → I_g = 0.39, CWSI_d = 0.72; 2-month droughted T_l = 26.7 °C → I_g = 0.09, CWSI_d = 0.92 (p. 4695).
- **3T model (Qiu et al. 2000–2009)** needs T_l, T_a, T_dry + R_n and R_n,dry (eqs. 61–62); the ratio "hat" was highly correlated with CWSI_e of sorghum (**R² = 0.97**) and separated drought/temperature treatments of melon and tomato. The authors' own modelling shows hat responds to *every* weather variable and breaks down at low irradiance (negative hat; confirmed in re-analysis of Jatropha data at max 130 W m⁻², p. 4702).
- **Sensitivity laws:** T_s rises with T_a and K_in, falls with wind speed and RH; at leaf level leaf angle and dimension dominate, at canopy level the roughness length (canopy height/structure) dominates (abstract, p. 4671). T_s exceeds aerodynamic T_0 by 2–3 °C for uniform canopies, up to 10–15 °C for incomplete covers (p. 4684); T_s = T_0 at a viewing angle of typically 50–70° from nadir (p. 4684); (T_c − T_a) decreases linearly with λE, K_in shifting the intercept and u the slope (p. 4684).
- **Practical ceiling:** the few indices in practice (stress time, CWSI_e) work "only in regions with very constant (semi-)arid weather conditions during the growth season" and are "largely limited to low, homogeneous crops" (p. 4703); UAV thermal mapping reaches 5–25 cm resolution (p. 4703).
- ⚠️ **Discrepancy with intake note A1:** the note claims the review "notes that osmotic (salinity-induced) stomatal effects can mimic drought T_s responses". The PDF contains no such statement — osmotic/salinity do not enter its treatment, which runs purely through g_s, λE and the energy balance. The limitation below is a **derivation from the framework, not a quotation**.
- ⚠️ **The thesis-critical limitation (derived from eq. 41):** CWSI and CTD are *functional* indices of stomatal closure, not of the **cause** of closure. Because T_pot and T_dry are defined by the energy balance of a maximally transpiring and a non-transpiring canopy of the *same* structure, every driver that reduces g_s — hydraulic (soil-water deficit), osmotic (salinity), or a waxy cuticle — moves T_c along the same one-dimensional axis, while heat-driven stomatal *opening* moves it the other way. The thermal signal is **equifinal with respect to the driver**, and the review offers no term that separates them: its only discriminants are the *weather context* (T_a, u, K_in, δe) and the *reference construction* (wet/dry surfaces) — never the plant's water status (Ψ, Ψ_s, turgor) or solute status. Separating osmotic from hydraulic stress therefore requires evidence outside the thermal channel.

## Relevance to Thesis

**High** — canonical CWSI/CTD physics: it supplies the equations, assumptions and documented failure modes of every thermal index in the thesis's water branch, and its equifinality structure *is* the thesis's problem statement.
- ✅ Gives the exact formulations (eqs. 41–52, 57–62) behind the thesis's CWSI/LST features and the ground↔spaceborne transfer of the thermal index.
- ✅ Quantifies the meteorological dependence of the baselines (a_pot/b_pot drift with T_a, u, K_in, crop height/LAI, p. 4689) → argues for conditioning thermal features on meteorological co-drivers rather than a fixed threshold.
- ✅ Provides the formal argument that thermal proxies measure g_s/λE, not the driver of stomatal closure, so salinity-driven and drought-driven closure are indistinguishable in the thermal channel.
- ⚠️ Ground-based and hardware-centred; satellite/airborne is explicitly out of scope, so the transfer to Landsat TIRS is an inference — our corpus already contains the spaceborne version (#24, #25).
- ❌ No salinity/osmotic-stress treatment, no machine learning, no multi-temporal or sequence modelling, no operational label design: physics, not a protocol.

## Key Takeaway

The review is the thesis's physics anchor: CWSI/CTD are one-dimensional functionals of stomatal conductance, which is why salinity-induced (osmotic) and drought-induced (hydraulic) closure give numerically identical canopy-temperature signatures, and why a heat wave can push the same index in opposite directions. Caveat: this equifinality is a rigorous inference from the review's equations, not a sentence the authors write — cite this paper for the formulations and baseline drift, and #41 (Tardieu) for the hydraulics that can break the equifinality.

## Links

- Matrix row: #39
- Related: #42 (same physics at sensor level + multi-sensor argument), #10 (Khuzestan CWSI trigger), #24 (ML bias-correction of satellite CWSI), #25 (S2 MSI vs Landsat thermal CWSI), #09 (Khuzestan CWSI→yield with a salinity covariate), #07 (Angon: combined drought+salinity physiology — the other half of the equifinality argument), #41 (Tardieu: hydraulics that can break the equifinality), #69 (Wen 2021: RS cannot yet monitor drought and salinity simultaneously)

---

*Linked from: [[Literature-Matrix]]*
