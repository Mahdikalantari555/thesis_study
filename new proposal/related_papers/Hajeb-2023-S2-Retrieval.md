# 11 — Simultaneous Sugarcane Retrieval from Sentinel-2 via BRANN (Hajeb et al., 2023)

**Full Citation:** Hajeb, M., Hamzeh, S., Alavipanah, S.K., Neissi, L., & Verrelst, J. (2023). Simultaneous retrieval of sugarcane variables from Sentinel-2 data using Bayesian regularized neural network. *International Journal of Applied Earth Observation and Geoinformation*, 116, 103168.
**DOI:** [10.1016/j.jag.2022.103168](https://doi.org/10.1016/j.jag.2022.103168) | Open Access (CC BY-NC-ND) | ~16 cites (external)
**Status:** ✅ Full read (2026-10-04)
**Themes:** #Study-area #Ground-protocols #Multi-output-retrieval #Label-proxies

---

## What It Does

Simultaneous multi-variable retrieval of four sugarcane traits — **LAI, leaf sheath moisture (LSM), leaf chlorophyll content (LCC), leaf nitrogen concentration (LNC)** — from 10 Sentinel-2 bands using a Bayesian-regularized ANN (BRANN), with the conventional LM-ANN as the only comparator. **Same study area as this thesis** (Amir Kabir Sugarcane Agro-Industrial zone, Khuzestan). Co-author Neissi is at the Sugarcane Research and Training Institute of Khuzestan, which supplied the ground data.

## Verified Study Design

| Element | Value | Source |
|---------|-------|--------|
| Site | Amir Kabir zone (48°12′–48°21′E, 30°58′–31°05′N); 14,000 ha, ~10,000 ha cultivated (2020); fields ~25 ha (1000 m × 250 m); semi-arid, 266 mm rain, ~2,780 mm/yr pan evaporation | §2.1, p.2 |
| Sampling | **136 ESUs** (3 m × 3 m elementary sampling units — *not* 136 fields), 5 varieties, 7 ratoon ages (PC + R1–R8); 8 campaign dates 15 May–23 Aug 2020 concurrent with S2A | §2.2.1, p.3 |
| Ground protocols | LAI destructive (3 plants/ESU); LSM oven method (FW/DW, 80 °C, 24 h); LCC SPAD-502 → Markwell eq.; LNC Kjeldahl (leaves 3–6, midrib removed) | §2.2.1, p.3 |
| S2 data | 10 bands B2–B8, B8a, B11–B12, all at 20 m; 25 S2A/S2B dates (5 May–27 Oct 2020) for mapping | §2.2.2, p.3 |
| Model | BRANN 10→4(hidden)→4(outputs); only 38 effective parameters of 64 weights; LM-ANN best = 2 neurons; 64 architectures searched | §3.1, p.5 |
| Validation | 70/30 split, **201 bootstrap replicates**; median RMSE = accuracy, Std = precision; Shapiro-Wilk + paired t/Wilcoxon | §2.3.3, p.5 |

## Key Results (verified, Table 1/Fig. 7, p.9; Tables 2–3, p.10)

| Variable | Simultaneous RMSE (median, test) | RRMSE % | Pooled R² (Fig. 7) | Individual RMSE (median) |
|----------|-------------------------------|---------|--------------------|--------------------------|
| LAI | **0.48 m²/m²** | 37.8% | 0.70 | 0.51 |
| LSM | 2.37 %wb | **2.91%** | 0.40 | 2.38 |
| LCC | 5.85 μg/cm² | 16.4% | 0.34 | 6.03 |
| LNC | 0.232 % | 15.5% | 0.17 | 0.247 |

- **Simultaneous > individual:** statistically significant for BRANN on all four traits (p ≤ 0.0004), **but the authors themselves call it a "marginal gain"** (p.14); for LM-ANN it fails on LSM (2.66 vs 2.60, ns). Cite as "modest but significant gain", never "≫".
- Runtime: sequential 1,766 s → simultaneous 403 s (BRANN) — 4.4× faster.
- **Retrievability tracks trait variability** (CV): per-replicate CV–RMSE correlation r = 0.73 (LAI), 0.37 (LSM)… (Fig. 9, p.11).
- **Single-trait LNC test R² ≈ 0 at n = 136** — their own failure mode; argument for richer representations (ours: SSL + temporal deep model) over shallow single-trait regressors.

## Salinity & Water Stress Coverage — NONE (verified)

No salinity, water-stress, irrigation, or soil measurement anywhere: salinity appears only as one introductory citation (Hamzeh et al. salinity hyperspectral work in the same cane zone); water appears only as "water requirement of sugarcane is supplied sufficiently by performing regular irrigation" (p.11) — which explains LSM's low CV. No stress classes, no disentanglement. **The "Kcb values for sugarcane" claim our matrix once carried here is confirmed absent from the entire paper** (it belonged to #12 Malee).

## Implications for the Thesis

1. **Site-specific grounding citable:** printed site descriptors (25-ha fields, semi-arid, evaporation regime) match our setting; ~10,000 ha / 25 ha ≈ 400 fields, compatible with our ~490-field frame (but don't cite the paper for a field count — it never states one).
2. **Ground-protocol template** for our own campaign: ESU design, destructive LAI, SPAD+Markwell, Kjeldahl LNC, sheath FW/DW — supplied by the same institute we would work with.
3. **Plant-water proxy is learnable here:** LSM (CV 3.6%) retrieved to ~2.9% RRMSE from multispectral bands in this exact landscape — supports the Water_Only signal being recoverable at Landsat scale.
4. **Multi-output precedent** for multi-task heads; correlated traits (LCC–LNC r=0.35, LSM–LAI r=0.49) benefit from joint retrieval.
5. **BRANN small-n regularization** (38/64 effective params) = classical counterpoint to our SSL design under label scarcity.
6. **Label proxies:** their four traits map onto our classes (low LSM → water-side evidence; LCC/LNC/LAI depression → general stress), but the paper supplies **zero salinity labels** — Salinity_Only/Mixed grounding must come from ECe surveys (Motlagh #09 protocol).

## Quotable Verbatim (with pages)

1. "The study has been conducted in Amir Kabir Sugarcane Agro-Industrial zone, one of the seven units in Khuzestan province of Iran…" — §2.1, p.2
2. "RMSE values of 0.48 (m²/m²) for LAI, 2.36 (% wb) for LSM, 5.85 (μg/cm²) for LCC, and 0.22 (%) for LNC, applying simultaneous retrieval." — Abstract, p.1
3. "A total of 136 ESUs were taken in the field campaign… distributed in fields with 5 different sugarcane varieties… and 7 different ratoons." — §2.2.1, p.3
4. "Statistical comparison between simultaneous and individual retrievals showed a marginal gain in accuracy and precision." — Conclusion, p.14
5. "Our predictions of the sugarcane variables, especially the LSM and LNC predictions, are being used practically for irrigation and fertilizer management in the Amir Kabir Sugarcane Agro-Industrial zone." — Conclusion, p.14

## Cautions

- Per-pixel 20 m product, not per-field; qualitative field-pattern interpretation only.
- S2 2020 only — no Landsat, no multi-year archive.
- Paper typos (don't propagate): abstract "(LNG)" for LNC; "annual compaction" → evaporation; "5.49 m²" ESU area vs 3 m × 3 m; both lon/lat labeled "latitude".

## Links

- Matrix row: #11 (verified 2026-10-04; journal IJAEOG — the old "ISPRS" entry is fixed)
- Feeds lit-review §3.7 (Khuzestan baselines); label-proxy discussion in 04-Thesis-Design
