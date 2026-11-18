# Study Note — Rodigheri et al. 2023

**Source PDF:** `D:\RS\Thesis\New_papers\remotesensing-15-05366-v2.pdf` (18 pp., open access CC BY 4.0)  
**Text extraction:** pypdf 6.19.0 (conda env `geo`, Python 3.12.14) — 74,886 characters extracted; extraction saved to `D:\RS\Thesis\thesis_implementation\.tmp\Rodigheri-2023-extracted.txt`  
**Status:** PDF available — verified against extracted full text.

---

## 1. Verified APA 7th citation

Rodigheri, G., Sanches, I. D., Richetti, J., Tsukahara, R. Y., Lawes, R., Bendini, H. d. N., & Adami, M. (2023). Estimating crop sowing and harvesting dates using satellite vegetation index: A comparative analysis. *Remote Sensing*, 15, 5366. https://doi.org/10.3390/rs15225366

**Verification (PDF available - verified):**
- Authors, year, title, journal (*Remote Sensing*), volume 15, article number 5366, and DOI `10.3390/rs15225366` all match the PDF header. **Verified.**
- Timeline: received 18 Sep 2023; revised 10 Nov 2023; accepted 13 Nov 2023; published 15 Nov 2023. **Verified.**
- Open access, CC BY 4.0, MDPI, Basel. **Verified.**
- Issue number: the user's citation lists `15(21)`; the extracted PDF header shows `Remote Sens. 2023, 15, 5366` without an explicit issue number, and the DOI string (`rs15225366`) is consistent with volume 15. The issue number `(21)` could not be independently confirmed from the extracted header — treat as **to confirm against the journal issue listing**.
- **Important discrepancy (verified from PDF):** despite the user-supplied title wording *"from Landsat"*, this paper does **NOT** use Landsat. It uses **MODIS** (MOD09Q1, MOD13Q1, MYD13Q1 → combined 8-day MCD13 at 250 m) and **Sentinel-2 MSI Level-2A** (5-day, 10 m), both accessed via Google Earth Engine. **Verified.**

---

## 2. Key findings relevant to harvest date detection

- **Harvest date (HD) is defined as the End of Season (EOS) date; sowing date (SD) is defined as SOS − 10 days** (to approximate the sowing–emergence lag; soybean emergence ≈ 10 days after sowing).
- **Best HD estimate:** phenex (PX) + Sentinel-2 + EVI → **RMSE 18 days, R 0.75, bias −0.2%**.
- **Best SD estimate:** TIMESAT/rTIMESAT (TM) + MCD13 + EVI → **RMSE 16 days, R 0.8, bias 10.4%**.
- **Threshold-method packages** (CropPhenology, phenex, TIMESAT) were more consistent than derivative-method packages (DEA tools, greenbrown, phenofit).
- **Worst performers:** DEA tools (DT) and greenbrown (GB) — most correlations below 0.5 and errors greater than 40 days; also the most sensitive to changes in data source.
- CropPhenology and phenofit showed low errors but lower correlation (R roughly 0.5–0.7).
- **EVI/EVI2 consistently outperformed NDVI** across all packages and data sources.
- **Double cropping is the major source of error** (lower R, more outliers): packages assume one crop per season and often select the wrong sowing/harvest cycle — particularly for harvest estimation. TIMESAT has cycle-selection features but often fails, especially for HD.
- Overall, **best performances have RMSE between 10 and 20 days**; the authors state even the best algorithms lack the precision to drive in-season decisions, though they are useful for regional trends and rapid large-area mapping.
- Validation used **>900 fields** (discussion) drawn from **1568 fields** across four Brazilian states (Paraná, São Paulo, Goiás, Minas Gerais), 2019–2020 soybean season, fields more than 2000 km apart.
- Region-dependent bias: estimates lower than observed in the northern region, higher in the southern region.

---

## 3. Methods used

**Study area & reference data**
- 1568 soybean fields in Paraná (PR), São Paulo (SP), Goiás (GO), Minas Gerais (MG), Brazil; observed sowing/harvest dates reported by landowners to the ABC Foundation; growing season 2019–2020; study window end of August 2019 to beginning of May 2020; soybean cycle length 120–160 days.

**Remote sensing data (4 sources × 2 indices)**
- MODIS MOD13Q1/MYD13Q1 (16-day MVC NDVI & EVI2, 250 m) and MOD09Q1 (8-day MVC red/NIR, 250 m); MOD13Q1+MYD13Q1 combined into an 8-day **MCD13** product.
- Sentinel-2 MSI Level-2A (5-day revisit, 10 m).
- Vegetation indices: **NDVI** and **two-band EVI2**.
- Total: **48 experiments** (6 packages × 4 data sources × 2 indices).

**Pre-processing (Google Earth Engine)**
- Field-border pixels excluded with a 125 m negative buffer.
- Cloud/shadow masking: MODIS QA (QA = 0 or 1; blue reflectance <10%; view zenith <30°), MOD09Q1 State band (cloud/cloud-shadow/cirrus bits), Sentinel-2 SCL band (remove saturated/dark/shadow/cloud/snow classes) + QA60 cloud mask.
- Gap filling and daily interpolation; Savitzky–Golay smoothing (window 5, polynomial degree 2) on all datasets; Best Index Slope Extraction (BISE) for Sentinel-2 outlier removal.

**Phenology extraction algorithms**
- CropPhenology (CP), DEA tools `xr_phenology` (DT), greenbrown (GB), phenofit (PF), phenex (PX), rTIMESAT / TIMESAT (TM).
- Two methodological families: **threshold method** (CP, PX, TM) and **derivative method** (DT, GB, PF).
- Parameter calibration on **200 randomly sampled fields**; best-correlating parameters selected (Table 1).

**Performance evaluation**
- Metrics: Shapiro–Wilk normality test, Spearman's rank correlation (R), RMSE, bias (%), linear regression vs field data, Wilcoxon signed-rank test.
- Processing time recorded per package.
- SD = SOS − 10 days; HD = EOS.
- Spatialization: sowing/harvest/length maps produced for the 2020–2021 season (example using CP and PF with MCD13).
- Reproducible code: GitHub `grazirodigheri/get-phenometrics`; field data remain private.

---

## 4. Findings-13 implications (RMSE 16–18 days; supports D2 30-day threshold)

**Implication statement (interpretation for the sugarcane water–salinity stress thesis):**
Rodigheri et al. report that satellite vegetation-index-derived phenology dates carry a date-estimation error of **RMSE 16 days (sowing, TIMESAT)** to **RMSE 18 days (harvest, phenex)**, with all best-performing configurations falling in an overall **RMSE 10–20 day** range against ground-referenced sowing/harvest dates. Because this 16–18 day RMSE is **smaller than a 30-day (D2) tolerance window**, phenology-date uncertainty from VI-based estimation alone would **not** by itself push a field across a D2 30-day stress-classification boundary. In other words, the reported date errors support the operational use of a **D2 30-day threshold** for phenology/stress timing decisions at regional scale.

**Caveats & conditions for transfer to this thesis (sugarcane, water–salinity stress, Landsat):**
- This paper is **soybean in Brazil**, not sugarcane; and uses **MODIS + Sentinel-2**, not Landsat. Landsat's 16-day revisit and 30 m resolution differ from the sources tested, so the 16–18 day RMSE should be treated as an indicative upper bound, not a verified Landsat error.
- The **SOS − 10 days** emergence-lag correction is crop- and region-specific; sugarcane (a perennial, multi-cut crop) has a different emergence/growth physiology, so a fixed 10-day offset may not apply.
- **Double cropping** was the dominant error source here; sugarcane ratoon cycles / multiple cuts present an analogous multi-cycle confounding risk for harvest-date detection.
- Even the best algorithms "lack the precision to drive in-season decisions" (authors' conclusion) — suitable for **regional/trend assessment**, less so for precise field-level or in-season management.
- "D2" and "30-day threshold" are **not terms used in this paper**; they are the user's thesis framing. The paper does not validate any D2 threshold. The link (RMSE 16–18 days < 30 days) is an inference to be tested against Landsat/sugarcane data, not a claim made by Rodigheri et al.

---

## 5. TO VERIFY FROM PDF (mark as "PDF available - verified")

| # | Item | Evidence in PDF | Status |
|---|------|-----------------|--------|
| 1 | Authors & author order | G. Rodigheri, I. D. Sanches, J. Richetti, R. Y. Tsukahara, R. Lawes, H. d. N. Bendini, M. Adami | PDF available - verified |
| 2 | Year / journal / volume / article | 2023; *Remote Sensing*; 15; 5366 | PDF available - verified |
| 3 | DOI | `10.3390/rs15225366` | PDF available - verified |
| 4 | Timeline (received/revised/accepted/published) | 18 Sep 2023 / 10 Nov 2023 / 13 Nov 2023 / 15 Nov 2023 | PDF available - verified |
| 5 | Open access / license | CC BY 4.0, MDPI | PDF available - verified |
| 6 | Issue number `(21)` vs DOI `rs15225366` | Header shows `Remote Sens. 2023, 15, 5366`; issue not explicitly printed | To confirm against journal issue listing (PDF available - verified for vol./article/DOI only) |
| 7 | Data sources: MODIS (MOD09Q1/MOD13Q1/MYD13Q1/MCD13) + Sentinel-2 MSI L2A; NOT Landsat | §2.2, §2.3 | PDF available - verified |
| 8 | Indices: NDVI + EVI2; EVI2 better than NDVI | §2.2, Results | PDF available - verified |
| 9 | Six algorithms: CropPhenology, DEA, greenbrown, phenex, phenofit, TIMESAT (rTIMESAT) | §2.4.2 | PDF available - verified |
| 10 | 48 experiments (6 × 4 × 2) | §2.2 | PDF available - verified |
| 11 | Calibration 200 fields; validation >900 fields (of 1568 total) | §2.1, §2.5, Discussion | PDF available - verified |
| 12 | Study area: PR, SP, GO, MG (Brazil); 2019–2020 season | §2.1 | PDF available - verified |
| 13 | SD = SOS − 10 days; HD = EOS | §2.4, §2.6 | PDF available - verified |
| 14 | Best SD: TIMESAT + MCD13 + EVI, RMSE 16 days, R 0.8 | Results (§3) | PDF available - verified |
| 15 | Best HD: phenex + Sentinel-2 + EVI, RMSE 18 days, R 0.75, bias −0.2% | Results (§3) | PDF available - verified |
| 16 | Overall best RMSE 10–20 days; DT/GB worst (R < 0.5, errors > 40 days) | Results (§3), Discussion (§4) | PDF available - verified |
| 17 | Double cropping = major error source, esp. for harvest | Results (§3), Discussion (§4) | PDF available - verified |
| 18 | Authors state best algorithms lack precision for in-season decisions | Discussion (§4), Conclusions (§5) | PDF available - verified |
| 19 | Paper does NOT use "D2" or "30-day threshold" (user's thesis terms) | Absent from full text | PDF available - verified (term absent); linkage is user inference |
| 20 | Code: github.com/grazirodigheri/get-phenometrics; field data private | Data Availability | PDF available - verified |

---

**Bottom line for the thesis:** Rodigheri et al. (2023) provide the closest published benchmark for satellite-based sowing/harvest date estimation: RMSE ≈ 16–18 days (best SD/HD), within a 30-day D2 window, but derived from MODIS/Sentinel-2 soybean data in Brazil — not Landsat sugarcane. Treat the 16–18 day RMSE as indicative, and re-validate emergence-lag correction and multi-cycle (ratoon) confounders before applying a D2 30-day threshold to the sugarcane water–salinity stress work.

---
*Study note prepared from extracted PDF text (pypdf). All factual claims above are traceable to `D:\RS\Thesis\New_papers\remotesensing-15-05366-v2.pdf`.*
