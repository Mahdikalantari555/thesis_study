# 69 — RS Challenges for Food Security wrt Salinity and Drought Threats (Wen et al., 2021)

**Full Citation:** Wen, W., Timmermans, J., Chen, Q., & van Bodegom, P.M. (2021). A Review of Remote Sensing Challenges for Food Security with Respect to Salinity and Drought Threats. *Remote Sensing*, 13(1), 6.
**DOI:** [10.3390/rs13010006](https://doi.org/10.3390/rs13010006) | Open Access | ~77 cites (external; 75 refs in-paper) | Published online 22 Dec 2020, issue 2021 — cite as **Wen et al. 2021**
**Status:** ✅ Full read (2026-10-04)
**Themes:** #Concurrent-stress #Problem-statement #VI-limits #RTM

---

## What It Does

Systematic review / meta-analysis (Web of Science + Google Scholar, **2005–2020**) of RS for crop drought **and/or** salinity stress: **1,184 records → 115 publications → 348 extracted correlations** (102 trait–wavelength, 171 VI–wavelength, 75 trait–VI), pooled as R² per trait/VI cluster. Organized by response-variable class (biomass / photosynthesis / water / osmosis traits; xanthophyll / water / carotenoid / greenness VIs), not by stress type.

## Why This Is Our Problem-Statement Anchor (verified)

The three load-bearing quotes all check out **verbatim**:

1. **Joint monitoring never done (abstract, p.1):** "However, remote sensing has not yet been used to monitor both drought and salinity stresses simultaneously."
2. **Spectral overlap (abstract, p.1):** "Moreover, the response signals for joint drought and salinity stresses overlapped spectrally, thereby **significantly limiting** the application of remote sensing to monitor these separately." — ⚠️ this wording is **abstract-only**; the Discussion version is weaker: "crop (biomass and water) responses to salinity are to some extent similar to those to drought. This confounding factor … hitherto not been accounted for in previous studies" (p.10). Cite as "Wen et al. 2021, abstract".
3. **VI insufficiency (abstract, p.1):** "We found that VIs are insufficiently accurate (**0.02 ≤ R² ≤ 0.80**) to characterize the crop health under drought and salinity stress."

## Stronger Ammunition the Repo Wasn't Using

- **Zero VI–salinity spectral evidence in the whole corpus** (p.4): "All 171 VIs–wavelength correlations that were found focused on drought, and **no reviewed study provided correlations for salinity stress**." The salinity side of our problem is even more under-evidenced than the drought side.
- **Co-occurrence + causal coupling (p.2):** "Drought and salinity cannot be seen independently of each other… hydrological drought significantly increases the salinity in rivers… there are already numerous areas in the world where both drought and salinity stress co-occur" — exactly the Khuzestan irrigation setting.
- **Early-stage symptom identity (p.10):** "The responses of plants to drought and salinity are **identical at the early stage**." → per-field temporal disentanglement (our design) is precisely what this implies is needed.
- **No ML at all:** the 2005–2020 corpus contains no machine/deep learning synthesis — the entire corpus is correlation-based; our CNN-Mamba + SSL + XAI approach is post-review frontier.
- **No sugarcane, no Iran, no arid-irrigated field-scale study** in the reviewed set (crops: wheat, cotton, grass, paddy, potato).
- FAO framing numbers (p.2): 11% of global irrigated area (34 Mha) salinized; salinity projected to affect 50% of cultivated land by 2050.

## Claim Nuances (corrections to our matrix row)

- **"Plant traits are the better target" — overstated.** The paper says traits "have a big potential … more in line with the vegetation processes" (abstract) **but** correlations "were not necessarily stronger" than VIs (p.7) and are inconsistent within/between crops (p.10). The actual hierarchy: **osmotic/ionic traits are the standout** (all R² > 0.50 across 500–2300 nm vs salinity, p.7) — but they are In-RS only: "Dissolved salts such as Na⁺, Cl⁻, K⁺ and Ca²⁺ are not directly tractable [by RTM]" (p.12). Correct framing: *traits are the mechanistically aligned target, osmotic traits the promising exception, but the evidence base is thin and inconsistent.*
- **RTM recommendation verified** (abstract + p.11–12): multi-trait simultaneous retrieval via RTM inversion + multi-sensor frameworks; two explicit future directions (p.12): "(1) advancing our capability to simultaneously monitor (through multi-sensor frameworks) the suite of crop traits… and (2) expanding our characterization of the spectral properties of osmotic traits (through optimized RTMs)." Our learned latent representations partially address this; we do NOT do physical RTM retrieval — state as honest limitation.
- **NDVI was deliberately excluded** from their VI analysis (Table 2 notes, p.5 — "greenness index… not found to respond to rainfall… during the crop growth period"). Do not extend "VIs insufficient" to NDVI-specific claims.
- Review window ends 2020 → position as the authoritative synthesis of the **pre-deep-learning era**, not current SOTA.

## Key Numbers (page-ref'd)

| Statistic | Value | Page |
|-----------|-------|------|
| Publications included | 115 (from 1,184 records; +49 snowball −12 dupes) | pp.3–4 |
| Correlations extracted | 348 (102 trait–λ, 171 VI–λ, 75 trait–VI) | p.4 |
| VI–λ correlations for salinity | **0** | p.4 |
| VI accuracy range (abstract) | R² 0.02–0.80 | p.1 |
| Water traits vs stress | R² 0.02–0.78 (peak 600–800 nm) | p.7 |
| Osmosis traits vs salinity | all R² > 0.50 (500–2300 nm) — In-RS only | p.7, 12 |
| CWSI correlations (Table 3) | LWP 0.78, Gs 0.77 | p.9 |
| Trait–VI range | R² 0.02–0.80 | p.8 |

## Quotable Set (for lit review §3.1)

Quotes 1–3 above + p.2 ("drought and salinity should not be viewed independently…") + p.10 ("responses… identical at the early stage") + p.12 (two future directions). Full verbatim list with pages in the agent report of 2026-10-04; the six above are the citable core.

## Links

- Matrix row: #69 (verified 2026-10-04)
- Feeds lit-review §3.1 and gap **G4** (joint monitoring unsolved); complements #70 (2022 HESS empirical) and #71 (2023 multi-crop)
- Wen trilogy positioning: 2021 = problem statement → 2022 = statistical pipeline we supersede → 2023 = multi-crop upscaling
