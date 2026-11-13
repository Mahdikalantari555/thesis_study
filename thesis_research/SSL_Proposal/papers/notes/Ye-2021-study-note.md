# Study Note: Ye et al. 2021 — Stochastic Continuous Change Detection (S-CCD)

**Source PDF:** `D:\RS\Thesis\New_papers\1-s2.0-S003442572030540X-main.pdf`  
**PDF available - verified** (17 pages, text extracted with `pypdf` 6.19.0)

---

## Verified APA 7th Citation

Ye, S., Rogan, J., Zhu, Z., & Eastman, J. R. (2021). A near-real-time approach for monitoring forest disturbance using Landsat time series: Stochastic continuous change detection. *Remote Sensing of Environment*, 252, 112167. https://doi.org/10.1016/j.rse.2020.112167

**Verification details (from PDF, all confirmed):**
- **Authors:** Su Ye (corresponding author, sye@clarku.edu), John Rogan, Zhe Zhu, J. Ronald Eastman
- **Affiliations:** Graduate School of Geography, Clark University (Worcester, MA); Department of Natural Resources and the Environment, University of Connecticut (Storrs, CT); Clark Labs, Clark University
- **Journal:** Remote Sensing of Environment, Volume 252, Article 112167
- **Published:** Available online 5 November 2020; print issue 2021
- **Received:** 22 March 2020; **Revised:** 14 September 2020; **Accepted:** 26 October 2020
- **License:** Open access, CC BY-NC-ND (https://creativecommons.org/licenses/by-nc-nd/4.0/)
- **Keywords:** Time series analysis; Forest disturbance; State space model; Kalman filter; Landsat; Near real-time

---

## Key Findings Relevant to Disturbance Detection (CCD Algorithm, Stochastic Change Detection)

### Overall accuracy
- S-CCD achieves a best **F1 score of 0.793** (at 0.95 probability threshold), with **20.1% omission error** and **21.4% commission error**.
- This is slightly higher than COLD's best F1 of 0.789 (at 0.975 threshold, 24.6% omission, 17.2% commission).
- The difference in best overall accuracy is only 0.4% — largely because 63% of reference disturbances are harvest activities (strong spectral signals), on which both algorithms perform similarly (omission errors 16% vs 16.2%).

### Superiority for subtle/gradual disturbances
- S-CCD achieves **noticeably fewer omission errors than COLD for lower-magnitude disturbances** such as drought stress and low-severity fire.
- Qualitative gypsy moth case study: S-CCD identified disturbance regions that COLD missed; these were confirmed as genuine forest damage (not commission errors) via NIR time-series inspection and ADS reference data.
- Reason: S-CCD's state space model allows trend and seasonality to evolve stochastically over time, achieving better model fitting than COLD's rigid "linear trend + harmonic cycles" assumption. Lower RMSE → greater sensitivity to low-magnitude spectral changes.

### Timeliness (near real-time monitoring)
- S-CCD requires **126 days** to confirm 50% of disturbances, vs. **166 days** for COLD (alert-lag relationship curve, 500 date-level reference plots).
- Disturbance probability output enables earlier, flexible decision-making before statistical confirmation (e.g., homogeneous pixels reaching ~0.5 probability within 30 days of initial infestation signal).

### Computational efficiency
- S-CCD is **up to ~4.4× faster than C-based COLD** for 34-year time series records (~3.5× at 20 years, ~1.8× at 10 years).
- For a standard 20-year Landsat ARD time series, S-CCD processes a 5000-pixel scanline in ~6 minutes (~500 computing hours per Landsat ARD scene).
- Efficiency gains come from the recursive Kalman filter update (no need to reload all historical images per new observation; ~95% reduction in data inputs per monitoring step).

### Validation dataset
- **3,782 Landsat-based disturbance reference plots (30 m)** from probability sampling across the Conterminous United States.
- 2,704 undisturbed plots; 1,078 disturbed plots; 1,413 disturbance occurrences total.
- Disturbance causal agents: harvest (n=903, 63.9%), mechanical (n=149, 10.5%), stress (n=141, 9.9%), fire (n=127), others/hydrology/wind/debris/land use change (n=83).
- 50% of samples used for algorithm development/parameter calibration; 50% (n=1,891) held out for validation.

---

## Methods Used (CCD, Landsat Time Series)

### Data preparation
- **Input data:** Landsat ARD (Analysis Ready Data) — Landsat-4/5 TM, Landsat-7 ETM+, Landsat-8 OLI/TIRS, gridded to Albers Equal Area Conic projection, consistently geo-registered and atmospherically corrected.
- **Spectral bands used:** green, red, NIR, SWIR1, SWIR2 (five bands). Zhu et al. (2020) reported these five bands alone achieve best performance vs. combining with vegetation indices.
- **Cloud/snow masking:** Fmask (Zhu and Woodcock, 2012) and Tmask (Zhu and Woodcock, 2014a) applied to screen clouds, cloud shadows, and snow.
- Thermal band not used for change magnitude computation in either S-CCD or COLD.

### CCD (Continuous Change Detection) lineage
- CCDC (Continuous Change Detection and Classification; Zhu and Woodcock, 2014b): multivariate time-series model using harmonic regression per spectral band; breakpoints identified when minimum discrepancy between actual and predicted reflectance exceeds a threshold.
- COLD (COntinuous monitoring of Land Disturbance; Zhu et al., 2020): improved CCDC with per-observation model updates (vs. per time span), temporally-adjusted RMSE, and change angles for disturbance confirmation.
- S-CCD (Stochastic Continuous Change Detection; this paper): builds on COLD by incorporating a **state space model (SSM)** and **Kalman filter**.

### State space model (SSM)
- Two stochastic assumptions: (1) observations = stochastic observational noise (εt) + latent states (αt); (2) states evolve over time as a stochastic process with process noise (ηt).
- **Observation equation:** yt = Z·αt + εt, εt ~ N(0, H)
- **State equation:** αt+1 = T·αt + ηt, ηt ~ N(0, Q)
- Trend modeled as random walk; cycle (annual + semi-annual) modeled with two state variables each (ct and ct*).
- Unlike classical harmonic regression (rigid, deterministic coefficients), SSM allows trend and cycle components to evolve randomly over time — better for complex nonlinear vegetation dynamics and missing data.

### Kalman filter
- Recursive estimation: when a new observation arrives, the "innovation" (difference between predicted and actual) is computed; the Kalman gain weights the model update; observational noise is filtered out; filtered states predict the next observation.
- Enables **completely recursive / online processing** — new measurements processed immediately as they arrive; no need to rebuild models from scratch.
- Missing data handled simply: no innovation computed; state and covariance propagate forward (at+1,i = T·αt|t,i; Pt+1,i = T·Pt,i·TT + Qi).

### S-CCD algorithm steps
1. **Build initial model:** Stability test + "looking back" procedure to find a stable initialization window. Minimum **18 clear observations** required (vs. 12 in COLD), because the fixed 'trend + annual + semi-annual' structure equals a 6-coefficient harmonic model (minimum window = coefficients × 3).
2. **SSM initialization:** Estimate observational noise (H), process noise (Q), initial states (a0), initial covariance (P0) via a fast method based on initial LASSO regression (detailed in supplementary Section S1).
3. **Temporally-adjusted peek window:** Completely online adjustment of consecutive observation count (consecutef = 6 default) and minimum temporal span (min_peek_days = 80 days default). Defined by calendar days, not fixed observation count — accounts for variability in Landsat revisit frequency across space and time.
4. **Recursive temporally-adjusted RMSE:** Two histograms (clear observation counts and squared RMSE by Day of Year, 6-day bin width, 61 bins) updated recursively; eliminates need to process all images per new observation. Dynamic minimum RMSE (temporal lag-1 madogram) updated yearly.
5. **Standardized Change Vector (SCVn):** Difference between multispectral reference and one-step-ahead predictions, normalized by RMSE across 5 bands.
6. **Change magnitude (CM):** Minimum L2 norm of SCVn within peek window; follows Chi-squared distribution with k=5 degrees of freedom. Breakpoint candidate if CM > χ² threshold(5).
7. **Confirm change using angular spread:** Mean Angular Spread = average angle between each SCVn and the median SCV (MedSCV); threshold < 30°. More robust to outliers than COLD's mean included angle (45°).
8. **Update model using Kalman filter:** Non-consecutive outlier removal (change probability 0.99999); unchanged observations update the model via Kalman filter.
9. **Disturbance identification:** Disturbance evidence = MedSCV_RED − MedSCV_NIR + MedSCV_SWIR1 > 0. A typical forest disturbance causes lower NIR, higher Red, higher SWIR.
10. **Disturbance probability:** Ratio of "anomaly days" to required confirmation days (min_peek_days); provides fuzzy membership for near real-time decision-making prior to confirmation.

---

## Findings-13 Implications (Relevant for P7 Transient Dip Detection; CCD Change Detection Logic)

### CCD change detection logic (directly applicable)
The paper's CCD-family change detection logic provides a concrete, validated template:

| CCD Step | S-CCD Implementation | Relevance to P7 / transient dip detection |
|---|---|---|
| Prediction vs. observation | One-step-ahead prediction from Kalman-filtered state; innovation = actual − predicted | Baseline for detecting deviation from expected trajectory (dip detection) |
| Change magnitude | Min L2 norm of Standardized Change Vector across 5 bands; χ²(5) test | Multispectral change indicator; avoids single-band false alarms |
| Change confirmation | Mean Angular Spread < 30° vs. median change vector | Ensures consistent change direction across bands — filters ephemeral noise |
| Disturbance evidence | MedSCV_RED − MedSCV_NIR + MedSCV_SWIR1 > 0 | Band-combination rule to single out health-decline breaks from recovery |
| Recursive update | Kalman filter updates states/covariance only (~95% less data I/O) | Enables continuous monitoring without reprocessing history |
| Near real-time output | Disturbance probability = anomaly days / min_peek_days | Early warning before statistical confirmation; tunable alert thresholds |

### Relevance for P7 transient dip detection
The term "P7 transient dip" and "Findings-13" do **not** appear verbatim in this paper — they belong to the user's own thesis framework. However, the paper's findings have direct implications:

1. **Sensitivity to subtle/gradual spectral change:** S-CCD's key advantage over COLD is detecting disturbances with small spectral change magnitudes (lower omission for stress, low-severity fire). This is directly relevant to transient dip detection, where the signal may be a short-lived, low-magnitude depression in a vegetation index.

2. **Sharper detection lag:** 126 days (S-CCD) vs. 166 days (COLD) to confirm 50% of disturbances. Shorter lag matters for catching transient events before they are masked by recovery or seasonal phenology.

3. **Disturbance probability for early alerting:** The fuzzy probability output (e.g., ~0.5 within 30 days of initial signal) supports threshold-flexible early detection — useful for transient dip events where waiting for full confirmation may miss the window.

4. **Multi-band change vector approach:** Using 5 bands (green, red, NIR, SWIR1, SWIR2) rather than a single index reduces false positives from ephemeral changes (e.g., soil moisture) — relevant for distinguishing true transient dips from noise.

### Limitations noted by authors (relevant to P7 scope)
- S-CCD assumes a fixed 'trend + annual + semi-annual' structure (6-coefficient model); adding a trimodal cycle **decreased F1 from 0.795 to 0.706**. Trimodal components are more useful for cropland than forest.
- S-CCD is more prone to over-detection in highly-fluctuated environments (ephemeral moisture change in grassland/bare land, agricultural rotation). A user-specified mask is recommended to exclude non-target land change.
- Both S-CCD and COLD have relatively high omission errors for fire (some low-severity/underground fires cause only subtle spectral change).

---

## TO VERIFY FROM PDF (mark as "PDF available - verified")

| Item | Status | Evidence from PDF |
|---|---|---|
| Citation (authors, year, title, journal, volume, article number, DOI) | **PDF available - verified** | Page 1: Remote Sensing of Environment 252 (2021) 112167; DOI 10.1016/j.rse.2020.112167; authors Su Ye, John Rogan, Zhe Zhu, J. Ronald Eastman |
| Open access license (CC BY-NC-ND) | **PDF available - verified** | Page 1: "This is an open access article under the CC BY-NC-ND license" |
| Best F1 score (0.793, 20% omission, 21% commission) | **PDF available - verified** | Page 1 (Abstract) and Page 9 (Section 5.1): F1 = 0.793 at 0.95 threshold, 20.1% omission, 21.4% commission |
| COLD comparison (F1 = 0.789) | **PDF available - verified** | Page 9: COLD best F1 = 0.789 at 0.975 threshold |
| 126 vs. 166 days lag for 50% detection | **PDF available - verified** | Page 10 (Section 5.3): S-CCD 126 days vs. COLD 166 days |
| ~4.4× speedup vs. COLD | **PDF available - verified** | Page 1 (Abstract) and Page 13 (Section 5.4): up to ~4.4 times faster for 34-year records |
| 3,782 reference plots; 2,704 undisturbed; 1,078 disturbed; 1,413 occurrences | **PDF available - verified** | Page 9 (Section 4) |
| Disturbance categories: harvest (903), mechanical (149), stress (141), fire (127), others (83) | **PDF available - verified** | Page 9 (Section 4) |
| Five spectral bands (green, red, NIR, SWIR1, SWIR2) | **PDF available - verified** | Page 4 (Section 3) |
| State space model + Kalman filter as core innovation | **PDF available - verified** | Pages 3–4 (Section 2), Pages 4–6 (Section 3) |
| Disturbance evidence index (MedSCV_RED − MedSCV_NIR + MedSCV_SWIR1 > 0) | **PDF available - verified** | Page 6 (Section 3.7) |
| Mean Angular Spread < 30° for change confirmation | **PDF available - verified** | Page 6 (Section 3.5) |
| min_peek_days = 80 days default | **PDF available - verified** | Page 5 (Section 3.3) |
| Software available at github.com/SuYe99/s-ccd (C implementation) | **PDF available - verified** | Page 12 (Section 5.4) |
| "Findings-13" / "P7 transient dip" terminology | **Not in paper** | These terms do not appear in the PDF; they belong to the user's thesis framework. The paper's CCD change detection logic and sensitivity to subtle spectral change are relevant by implication. |

---

## Summary

Ye et al. (2021) present **S-CCD (Stochastic Continuous Change Detection)**, an advancement over the COLD algorithm for near real-time forest disturbance monitoring using dense Landsat time series. The core innovation is the integration of a **state space model** with a **Kalman filter**, treating trend and seasonality as stochastic (evolving) processes rather than fixed harmonic coefficients. This yields: (1) slightly better overall accuracy (F1 0.793 vs. 0.789), (2) meaningfully better detection of subtle/gradual disturbances (lower omission for stress and low-severity fire), (3) shorter detection lag (126 vs. 166 days for 50% detection), and (4) up to ~4.4× computational speedup via recursive updating. The validated CCD change detection logic — standardized change vectors, χ² thresholding, angular-spread confirmation, disturbance evidence band combination, Kalman-filter recursion, and disturbance probability output — provides a directly transferable template for transient dip detection (P7) in the user's thesis context, particularly for catching low-magnitude, short-lived spectral deviations with multispectral consistency checks and early probabilistic alerting.

**Note on title discrepancy:** The user-requested title ("Forest disturbance detection using Landsat and stochastic CCD") differs slightly from the actual PDF title ("A near-real-time approach for monitoring forest disturbance using Landsat time series: stochastic continuous change detection"). The citation above uses the verified actual title.

---
*Study note generated from PDF text extraction using pypdf 6.19.0. All "PDF available - verified" items were confirmed against the extracted text of the source PDF.*
