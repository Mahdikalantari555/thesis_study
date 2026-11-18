# 25 — Sentinel-2 MSI vs Landsat Thermal CWSI Comparison in Sugarcane (Zoratipour et al., 2025)

**Full Citation:** Zoratipour, E., Soltani Mohammadi, A., Veysi, Sh., Boroomand Nasab, S., & Naseri, A.A. (2025). Comparison Sentinel-2 with Landsat 8/9 to Detect Water Stress in Sugarcane Fields. *Iranian Journal of Soil and Water Research*, 56(5), 1219–1238.
**DOI:** [10.22059/ijswr.2025.389356.669872](https://doi.org/10.22059/ijswr.2025.389356.669872)
**Status:** ✅ Full read (2026-10-04)
**Themes:** #CWSI #Sentinel2 #Landsat #Comparison #MSI #Sugarcane

---

## What It Does

Compares Landsat 8/9 thermal bands (LST-based CWSI) against Sentinel-2 infrared bands (MSI-based dimensionless Moisture Stress Index) for detecting water stress in sugarcane, validated against ground-truth Idso CWSI.

## Study Area

- **Amirkabir Sugarcane Agro-Industry Unit**, Khuzestan, Iran (same site as papers #10 and #24). **Campaign year: 2024** (Jalali 1403; Table 1 Gregorian dates 2024; sampling Tir–Shahrivar 1403) — one year after #10/#24 (2023)
- Four fields, three proximal sensing points each
- Four cloudless image pairs (Landsat 8/9 + Sentinel-2) acquired simultaneously

## Methodology

### Landsat-Based CWSI (thermal)
- LST from single-channel algorithm (SC, Sobrino et al., 2004) using **TIR band 10** (corrected from "bands 10/11"; §LST, p.1226, Eqs 2–7)
- Hot/cold pixel approach (SEBAL): CWSI = (LST - LST_cold)/(LST_hot - LST_cold)

### Sentinel-2-Based DMSI (dimensionless MSI)
- MSI = R1600/R820 (SWIR/NIR reflectance from bands 11 and 8)
- Normalized to field-specific hot/cold pixel range:
  ```
  DMSI = (MSI - MSI_hot) / (MSI_bright - MSI_hot)
  ```
- Range 0–1, analogous to CWSI scale

### Validation
- Ground truth: Idso-method CWSI from proximal Tc/Ta/VPD measurements at satellite overpass time (10:30 AM)
- Metrics: R², RMSE, rMBE, Pearson r

## Results by Date

| Date | Landsat CWSI (R²/RMSE/rMBE/r) | Sentinel-2 DMSI (R²/RMSE/rMBE/r) |
|------|-------------------------------|----------------------------------|
| Jul 7/9* | 0.89 / 0.09 / 19.12 / 0.94 | 0.74 / 0.15 / 34.1 / 0.86 |
| Jul 24 | 0.92 / 0.08 / 14.20† / 0.96 | 0.89 / 0.14 / 6.38† / 0.94 |
| Aug 18 | 0.82 / 0.11 / 19.50 / 0.90 | 0.84 / 0.15 / 28.50 / 0.91 |
| Sep 2 | 0.78 / 0.08 / 14.54 / 0.88 | 0.77 / 0.14 / 30.80 / 0.88 |

\* First date: Results text & extended abstract say **7 July**; the Landsat CWSI map panel is labelled "CWSI- 9 JULY" (Fig. 6, p.1232) — paper-internal inconsistency.
\† Internal inconsistency: Results text (p.1228) & extended abstract give rMBE 14.20 (Landsat) / 6.38 (S2) for 24 July, but the Fig. 4 scatter panel (p.1228) plots **20.14 / 38.67** for the same date.

**Averaged across dates:**
- Landsat: R² = 0.78–0.92, RMSE = 0.08–0.11, rMBE = 14.2–19.5, r = 0.88–0.96
- Sentinel-2: R² = 0.74–0.89, RMSE = 0.14–0.15, rMBE = 28.5–38.6, r = 0.86–0.94

## Key Findings

| Finding | Detail |
|---------|--------|
| **Landsat thermal outperforms Sentinel-2 MSI** | Consistently higher R², lower RMSE and rMBE across all 4 dates |
| **Sentinel-2 is viable fallback** | When Landsat unavailable, Sentinel-2 provides acceptable estimates (R² > 0.74) |
| **Stress trend similarity** | Both satellites capture similar spatial stress patterns and temporal trends |
| **Peak stress ~0.65–0.69** | Detected by both sensors on Jul 24 |
| **Sentinel-2 advantages** | NOT verifiable in full text (2026-10-04): the "5-day revisit / 10 m resolution / free data" claims were not found in the paper (Persian body); the Discussion (p.1230) only cites S2's lack of a thermal band and pixel-size differences vs Landsat |
| **Landsat advantages** | Dedicated thermal bands, better accuracy for CWSI estimation |

## Spectral Indices Used
- **LST**: Land Surface Temperature from Landsat thermal bands (10.6–12.5 µm)
- **MSI**: Moisture Stress Index = R1600/R820 (Sentinel-2 SWIR/NIR)
- Both normalized to dimensionless 0–1 scale for comparison

## Relevance to Thesis

**Moderate-High.** Useful for sensor selection and multi-sensor fusion strategy:

1. **Confirms thermal > SWIR for CWSI** — thermal bands provide superior water stress detection vs. MSI, supporting prioritization of thermal data in the CNN-Mamba architecture
2. **Sentinel-2 as complementary source** — could be fused with Landsat for improved temporal coverage (addresses limitation in paper #24)
3. **MSI as alternative stress proxy** — useful when thermal data unavailable; DMSI normalization approach is transferable
4. **Same study area** — all three Zoratipour papers (#10, #24, #25) use identical field sites and ground measurements, enabling cross-validation of approaches
5. **No salinity disentanglement** — like paper #24, this compares pure water stress detection, not concurrent water-salinity stress separation

## Limitations
- Only 4 satellite overpass dates — limited statistical power
- No ML bias correction applied (unlike paper #24)
- MSI-based approach less sensitive to early-stage stress
- Assumes field-specific hot/cold pixel calibration

## Verified Full-Text Findings (2026-10-04)

Full read of `papers/25-Zoratipour-2025-Sentinel2-vs-Landsat-CWSI.pdf` (20 pp; IJSWR 56(5):1219–1238; body in Persian, English abstract + extended abstract on pp.1219–1220; printed page = PDF page + 1218). Every number below was checked against the PDF text.

### Study site & data (verified)
- **Site:** Amir Kabir Sugarcane Agro-Industry Unit, Khuzestan (English abstract p.1219; M&M p.1223; M&M reports the unit at ~31°N / ~48°E, elevation ~7 m). **Year: 2024** (Jalali 1403; Table 1 Gregorian dates 2024; sampling Tir–Shahrivar 1403, p.1223–1224) — one year after #10/#24 (2023).
- **Fields:** four fields of different ages — plant (کشت), ratoon 1/2/3 — with **3 measurement points each = 12 points** (M&M pp.1223–1224; Fig. 2 p.1224; Fig. 5 caption p.1231). Tc/Ta/RH measured continuously 06:00–18:00; canopy sensor ~30 cm into the canopy on a 3-m pole, with an air sensor on a 3-m pole ~100–200 m away (M&M p.1224).
- **Images:** four cloudless **simultaneous** Sentinel-2 + Landsat 8/9 pairs (abstract p.1219; Table 1 p.1226). Analysis dates in the Results text: **7 July, 24 July, 18 August, 2 September 2024** — but the Landsat map panel is labelled "CWSI- 9 JULY" (Fig. 6, p.1232): paper-internal date inconsistency.
- **Landsat side:** LST from single-channel (SC) algorithm (Sobrino et al., 2004) using TIR **band 10** (Eqs 2–7, p.1226); CWSI = (Ts − Tcold)/(Thot − Tcold) (Eq 8, p.1228); cold pixel = coolest well-vegetated, hot pixel = hottest stressed/bare; SEBAL-type hot/cold approach (Waters et al., 2002 cited pp.1227, 1229).
- **Sentinel-2 side:** MSI = R1600/R820 = **B11/B8** (Eq 9, p.1227); normalized dimensionless **DMSI = (MSI − MSI_hotpixel)/(MSI_brightpixel − MSI_hotpixel)** (Eq 10, p.1227) → 0–1 scale comparable to CWSI.
- **Ground truth:** Idso CWSI (Eq 1, p.1225) from Tc/Ta/VPD at the **10:30 am** satellite overpass (M&M pp.1225, 1227). Metrics: R², RMSE, rMBE, Pearson r (Eqs 11–14, p.1227).

### Results (verified)
Per-date (Results text p.1228; Fig. 4 scatter panels p.1228):

| Date | Landsat CWSI (R²/RMSE/rMBE/r) | Sentinel-2 DMSI (R²/RMSE/rMBE/r) |
|------|-------------------------------|----------------------------------|
| 7 (Fig. 6: 9) July | 0.89 / 0.09 / 19.12 / 0.94 | 0.74 / 0.15 / 34.1 / 0.86 |
| 24 July | 0.92 / 0.08 / 14.20† / 0.96 | 0.89 / 0.14 / 6.38† / 0.94 |
| 18 August | 0.82 / 0.11 / 19.5 / 0.90 | 0.84 / 0.15 / 28.5 / 0.91 |
| 2 September | 0.78 / 0.08 / 14.54 / 0.88 | 0.77 / 0.15 / 30.8 / 0.88 |

† Fig. 4 plots 20.14 / 38.67 for 24 July (conflicts with Results text; see table above in main note).

- **Ranges (abstracts, pp.1219, 1221):** Landsat thermal R² 0.78–0.92, RMSE 0.08–0.11, rMBE 14.20–19.5 (English abstract garbled as "14.54-14.20"; Persian abstract gives 19.5–14.20), r 0.88–0.96; Sentinel-2 R² 0.74–0.89, RMSE 0.14–0.15, rMBE 28.5–38.6 (per-date minimum 6.38 on 24 Jul), r 0.86–0.94.
- **Decision (abstract p.1219; نتیجه‌گیری p.1231):** Landsat thermal "showed a slightly better estimate of the actual stress data than the infrared bands of Sentinel-2"; both performed acceptably; "when Landsat 8-9 imagery is unavailable, the use of Sentinel-2 imagery is recommended for crop water stress estimation."
- **Peak stress:** highest mapped stress **0.65** (Landsat thermal, Fig. 6) and **0.69** (Sentinel-2 MSI, Fig. 7), both on 24 July (abstract p.1219; maps pp.1232–1233).
- Both sensors track similar spatial stress patterns and temporal trends vs actual values (abstract p.1219; Results pp.1228–1229; Figs 5–7).
- **Reasons for the Landsat advantage** (Discussion p.1230): Sentinel-2 has **no thermal band**; SWIR (MSI) vs thermal spectral ranges differ; pixel-size differences between the sensors.
- **NOT FOUND:** the "5-day revisit / 10 m resolution / free data" Sentinel-2 advantages are not stated in the full text. **Salinity is not mentioned anywhere** in the 20 pages (no شوری discussion, no EC data).

### Repo-claim verification

| # | Repo claim | Verdict | Evidence |
|---|------------|---------|----------|
| 3 | Landsat thermal outperforms S2 MSI: R² 0.78–0.92 (Landsat) vs 0.74–0.89 (S2) | VERIFIED | Abstract p.1219; Results p.1228; Fig. 4 |
| 3 | RMSE 0.08–0.11 vs 0.14–0.15; r 0.88–0.96 vs 0.86–0.94 | VERIFIED | Abstract p.1219 |
| 3 | What is compared: Landsat LST-CWSI (SC band 10, hot/cold) vs S2 SWIR MSI (B11/B8) normalized to DMSI, against Idso ground CWSI at the 10:30 overpass, 12 points × 4 dates | VERIFIED | M&M pp.1225–1228 |
| 3 | Practical sensor decision: prioritize thermal (Landsat 8/9); S2 recommended only when Landsat unavailable | VERIFIED | Abstract p.1219; Conclusion p.1231 |
| 5 | Site Amirkabir; four fields × 3 points; 4 simultaneous pairs; summer 2024 | VERIFIED | M&M pp.1223–1226; Table 1 p.1226 |
| 5 | Soil salinity involved | NOT FOUND — no salinity measurement or discussion anywhere | whole paper |
| — | First date "Jul 9" | PARTIAL — Results text says 7 July; Fig. 6 map says 9 JULY | p.1228 vs p.1232 |
| — | "bands 10/11" for LST | CORRECTED → band 10 only (single-channel) | p.1226 |
| — | S2 advantages: 5-day revisit, 10 m, free | NOT FOUND in full text | — |
| — | Peak stress 0.65–0.69 on Jul 24 | VERIFIED | Abstract p.1219; Figs 6–7 pp.1232–1233 |
| — | "Only 4 overpass dates" (note limitation) | VERIFIED | Table 1 p.1226; abstract |
| — | "No ML bias correction applied" (note limitation) | VERIFIED as description (paper contains no ML component) | whole paper |

---

*Linked from: [[Literature-Matrix]], [[00-Thesis-Overview]]*
