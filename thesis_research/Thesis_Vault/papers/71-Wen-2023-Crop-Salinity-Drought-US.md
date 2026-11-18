# 71 — Crop-Specific Responses to Salinity and Drought from RS, USA (Wen et al., 2023)

**Full Citation:** Wen, W., Timmermans, J., Chen, Q., & van Bodegom, P.M. (2023). Evaluating crop-specific responses to salinity and drought stress from remote sensing. *International Journal of Applied Earth Observation and Geoinformation*, 122, 103438.
**DOI:** [10.1016/j.jag.2023.103438](https://doi.org/10.1016/j.jag.2023.103438) | Open Access (CC BY) | ~19 cites | Vol. 122 confirmed (do not "fix" to 123)
**Status:** ✅ Full read (2026-10-04)
**Themes:** #Concurrent-stress #Wen-trilogy #ANOVA #Trait-based

---

## What It Does

Third paper of the Wen trilogy: upscales the 2022 HESS design (five Sentinel-2 traits + two-way ANOVA) from 2 Dutch crops to **8 crops across the contiguous USA (2021 season)** using a new **pairwise matched-control design**. Traits: LAI, FVC, FAPAR, Cab (canopy chlorophyll), Cw (canopy water) from **S2GM-2 60 m monthly composites (10-day, 11th–20th)** via the SNAP biophysical processor; analysis units are **1-km fishnet cells** (zonal means of 30 m pixels); each stressed cell matched within a 30-km buffer to non-stressed cells on crop type, soil taxonomy, climate zone, and state; response = trait difference within pairs; statistics = ANOVA + Partial Eta Square (SPSS 27).

**Stress labels are proxies, not in-situ:** drought = cumulative **SPEI-3** (WestWide Drought Tracker); salinity = **static topsoil EC** from gNATSGO (0–4 / 4–8 / >8 dS/m per Richards 1954). Overlay → 9 stress-combination classes (sparse ones merged). **No machine learning anywhere** (ANOVA only); **no accuracy/R²/RMSE figures exist** — inferential effect sizes only; **single year (2021); no thermal data; no sugarcane.**

## Verified Findings

1. **Combined > individual stress impacts (structural traits):** "For all crops, the combination of salinity and drought stress commonly had the biggest impact on the performance of LAI, FAPAR, and FVC… salinity was more important in determining crop performance than drought" (§3.2, p.4). Same pattern for Cab and Cw (§3.3, p.6). Exceptions: **almond and sorghum** responded only to individual stresses (pp.6).
2. **Strongly time-dependent:** "The two-way ANOVAs of stress and time revealed a strongly time-dependent impact of stress on the five traits, as expressed by strong interactions effects" (§3.1, p.4); stress × time as important as the main effects; "even the dominant stress on crop traits varied throughout the growing season" (§4.1, p.7).
3. **Trait-response sequencing (novel, testable for our XAI):** "for all eight crops, **LAI was triggered first** by drought and salinity stress, followed by FVC and FAPAR, and **Cw and Cab were the last to respond**" (§4.2, p.8); stress onset concentrated in March–April.
4. **Literature tolerance classes failed:** "Importantly, none of these patterns seemed to relate to their perceived tolerance to salinity or drought (Table S2)" (§3.2, p.6) → cite "crop-specific **responses**", not "tolerance confirmed".
5. **Honest effect-size admission:** "Despite the strong significance of all patterns…, the effect sizes of the crop responses to salinity and drought stress were limited" (§4.3, p.9).

## ⚠️ Critical Implication for Our Gap Statements (G4 refinement)

The Wen trilogy now **partially closes the naive gap**: this paper claims (p.2) "This study addresses the challenge of **simultaneously evaluating** the response of diverse crops to the co-occurrence of drought and salinity stress in real-life settings at a large scale" and (Conclusions, p.9) "we established a quantitative foundation for **simultaneously assessing** the responses of various crops to the occurrence of stresses, alone and collectively."

Therefore our thesis must **not** quote Wen 2021's "remote sensing has not yet been used to monitor both… simultaneously" without the caveat that the same group partially addressed it in 2022/2023. The defensible refined gap: what Wen 2022/2023 do is **category-level comparison at 1-km national scale** with **proxy labels** (SPEI + static soil EC), **one year**, **no predictive model**, **no per-field unit**, **no uncertainty**, **no XAI** — and they never attempt **signal separation within a mixed observation** (mixed stress is only a class contrasted against matched controls). Our niche stays open: per-field (~490 sugarcane fields) 4-class *predictive* classification from a 2013–2025 Landsat time series with DL + SSL + temporal XAI.

## Design Cues We Can Reuse

- Their **pairwise matched-control logic** (stressed vs unstressed cells matched on covariates) is a citable statistical ancestor of contrastive SSL — motivates our Barlow Twins-style positive/negative construction across stress conditions.
- Their **trait sequencing** (LAI → FVC/FAPAR → Cw/Cab) generates a physiologically testable hypothesis for our temporal XAI: early-season structural-band saliency vs late-season chlorophyll/water saliency.
- Their static soil-EC proxy + single season is exactly the weakness our field-labeled multi-year design overcomes — use as differentiator, not as strawman.

## Quotable Verbatim (with pages)

1. "crops were more sensitive to combined salinity and drought than to individual stresses, although stress impacts significantly varied between time and species." — Abstract, p.1
2. "In general, for all eight crops, LAI was triggered first by drought and salinity stress, followed by FVC and FAPAR, and Cw and Cab were the last to respond (Fig. 7)." — §4.2, p.8
3. "Importantly, none of these patterns seemed to relate to their perceived tolerance to salinity or drought (Table S2)." — §3.2, p.6
4. "Despite the strong significance of all patterns described above, the effect sizes of the crop responses to salinity and drought stress were limited." — §4.3, p.9
5. "Most crops first reduced their primary production capacity through reducing LAI before reducing water or chlorophyll contents." — Conclusions, p.9

## Links

- Matrix row: #71 (verified 2026-10-04)
- Wen trilogy: #69 (2021 review, problem statement) → #70 (2022 HESS, statistical pipeline) → #71 (this, upscaling + matched controls)
- Feeds lit-review §3.1; gap **G4** (refined wording); XAI hypothesis list
