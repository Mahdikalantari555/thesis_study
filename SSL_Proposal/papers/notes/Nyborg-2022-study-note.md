# Study Note — Nyborg et al. 2022

**Source:** Nyborg, J., Pelletier, C., & Assent, I. "Generalized Classification of Satellite Image Time Series with Thermal Positional Encoding." arXiv:2203.09175v2 [cs.CV], 14 Jun 2022.
**PDF:** `D:\RS\Thesis\New_papers\2203.09175v2.pdf` — available and text-extracted.
**Extracted text:** `D:\RS\Thesis\.tmp\nyborg_2022_extracted.txt` (11 pages, ~50.6k chars).
**Status:** PDF available — verified.

---

## 1. Verified APA 7th citation (arXiv:2203.09175)

Nyborg, J., Pelletier, C., & Assent, I. (2022, June 14). Generalized classification of satellite image time series with thermal positional encoding. arXiv. https://arxiv.org/abs/2203.09175

**In-text citation:** (Nyborg et al., 2022)

**Verified metadata (from PDF):**
- Title: Generalized Classification of Satellite Image Time Series with Thermal Positional Encoding
- Authors: Joachim Nyborg¹,³, Charlotte Pelletier², Ira Assent¹
- Affiliations: ¹ Dept. of Computer Science, Aarhus University, Denmark; ² IRISA UMR 6074, Univ. Bretagne Sud, France; ³ FieldSense A/S, Denmark
- arXiv ID: arXiv:2203.09175v2 [cs.CV], posted 14 Jun 2022
- Code: https://github.com/jnyborg/tpe
- Contact: jnyborg@cs.au.dk, charlotte.pelletier@univ-ubs.fr, ira@cs.au.dk

---

## 2. Key findings relevant to thermal time encoding in SITS

**Problem.** Self-attention–based SITS crop classifiers generalize poorly to regions not seen during training, mainly because calendar-time positional encoding (day-of-year) is not robust to temporal shifts of the growing season caused by climate variation (e.g., cooler regions reach growth stages later).

**Core idea.** Crop growth is directly related to thermal time (accumulated heat), not calendar time. Replacing calendar time with thermal time makes SITS from different regions invariant to temporal shifts while retaining class-wise timing differences within a region — i.e., shift-invariant between regions but shift-variant within a region.

**Key quantitative findings (leave-one-region-out, Table 1; macro F1 / overall accuracy, averaged across 4 held-out regions):**

| Model | Avg F1 | Avg OA | Notes |
|---|---:|---:|---|
| PSE+LTAE [41] (calendar time, baseline) | 68.0 | 82.9 | Worst generalization |
| w/o PE (no positional info) | 75.9 | 87.2 | Invariant to shifts but ambiguous order |
| w/ ShiftAug [33] (calendar + random shifts) | 79.9 | 88.8 | Calendar-time augmentation |
| TPE-Sinusoidal | 82.1 | 90.6 | Calendar→thermal in sinusoidal PE (+14.1% F1 vs baseline) |
| TPE-Concat | 82.7 | 90.2 | Jointly learned embedding + thermal time |
| TPE-Fourier | 80.3 | 90.3 | Learnable sinusoidal PE (not beneficial; −1.8% vs TPE-Sinusoidal) |
| TPE-Recurrent | 83.3 | 91.0 | Best; learns GDD development via GRU (+15.3% vs baseline, +3.4% vs ShiftAug) |
| Upper-bound (all 4 regions) | 91.8 | 95.4 | Fully supervised ceiling |

**Takeaways:**
- Simply removing positional encoding outperforms the calendar-time baseline (+7.9% F1), showing calendar time actively hurts cross-region generalization.
- TPE-Sinusoidal (replace calendar with thermal in sinusoidal PE) alone improves F1 by +14.1% — thermal time is the dominant driver.
- Learnable TPE-Recurrent is best but most compute-intensive (17.2 s/epoch vs ~15.5–16.4 s for others).
- TPE-Concat is computationally more efficient than TPE-Sinusoidal with comparable accuracy — recommended when compute is limited.
- Residual gap to upper-bound remains; TPE addresses temporal shift but not spectral-signature differences (topography, soil, varieties) — left to future work.

---

## 3. Methods used (positional encoding, thermal time)

### 3.1 Thermal time / GDD computation
Thermal time is measured in Growing Degree Days (GDD), computed by accumulating daily average temperatures above a baseline:

**GDD(t) = Σᵢ₌₁ᵗ max((Tᵢᵐⁱⁿ + Tᵢᵐᵃˣ)/2 − T_base, 0)**

- T_base = 0 °C, T_cap = 30 °C (standard values; growth stagnates below 0 °C, no faster above 30 °C)
- Temperatures clipped to [T_base, T_cap]
- Accumulated from the start of the input SITS (January 1); GDD is monotonically increasing, so it preserves time-series order and can directly replace day-of-year
- Weather from the E-OBS dataset (EU-wide, daily min/max temperature, 0.1° regular grid, 2017), geo-referenced by parcel centroid

### 3.2 Positional encoding background
- Self-attention is position-agnostic, so positional information must be added explicitly.
- Existing SITS methods use fixed sinusoidal positional encoding of calendar time (day of year).
- Fixed sinusoidal PE is well-defined for every position but not learnable; per-position learnable embeddings fail to generalize to unseen positions (ill-suited for irregularly sampled / cloud-filtered SITS).
- TPE focuses on **absolute** positional encoding (relative encoding is unsuitable because absolute phenological timing matters, e.g., winter vs spring images).

### 3.3 Four TPE strategies (input to PSE+LTAE [41])
The backbone is PSE+LTAE: Pixel-Set Encoder (spatial/spectral) + Lightweight Temporal Attention Encoder (a "master query" self-attention that outputs a single embedding).

1. **TPE-Sinusoidal** — Replace calendar time `t` with GDD(t) in the fixed sinusoidal PE (Eq. 1). Not learned; well-defined for any GDD value (inductive to unseen positions).
2. **TPE-Concat** — Concatenate GDD(t) to the intermediate PSE embedding before the final MLP: `e(t) = MLP2([ê(t) || GDD(t)])`. SITS and position learned jointly; computationally efficient (no separate PE function).
3. **TPE-Fourier** — Learnable Fourier-feature PE (Li et al. [20]): `r(t) = [cos(Wr t) || sin(Wr t)] / √D`, passed through an MLP. Generalizes sinusoidal PE; not beneficial here (−1.8% F1 vs TPE-Sinusoidal).
4. **TPE-Recurrent** — GRU learns a positional encoding capturing non-linear GDD development over the season (GDD rises faster in summer). Input = sinusoidal encoding of GDD(t); output projected to dimension D. Best accuracy but sequential/more compute.

**Requirements for successful SITS positional encoding:** (1) shift-invariant across regions; (2) shift-variant within a region (absolute in-season position); (3) inductive to unseen positions; (4) data-specific/learnable.

### 3.4 Experimental setup
- **Dataset:** TimeMatch [34], Sentinel-2 L1C SITS, 4 tiles — AT1 (33UVP, Austria), DK1 (32VNH, Denmark), FR1 (30TXT, mid-west France), FR2 (31TCJ, southern France)
- Period: Jan 1 – Dec 31, 2017; cloud cover ≤ 80%; coverage ≥ 50%; atmospheric bands (1, 9, 10) removed; 20 m bands bilinearly interpolated to 10 m
- 280K parcels, 15 crop classes; 9 crop types selected (≥200 samples in all tiles): corn, horsebeans, meadow, spring barley, winter barley, winter rapeseed, winter triticale, winter wheat, unknown
- Train/val/test = 70%/10%/20% per tile
- **Leave-one-region-out** spatial generalization: train on 3 tiles, test on the held-out 4th
- Training: 100 epochs, batch 128, single GTX 1080 Ti, Adam, lr 1e-3 with cosine annealing, weight decay 1e-4; pixels normalized to [0,1]

---

## 4. Findings-13 implications (relevant for GDD/thermal time R4; deferred until ERA5 wired)

**Status: DEFERRED — pending ERA5 weather-data integration.**

This paper's thermal-time/GDD findings are directly relevant to thesis research question/requirement **R4 (GDD/thermal time)**. However, Nyborg et al. computed GDD from the **E-OBS** reanalysis (0.1° grid, 2017), whereas the thesis pipeline plans to use **ERA5** weather data. Because GDD is sensitive to the underlying temperature product (spatial resolution, baseline/cap clipping, accumulation start date), the specific "findings-13" implication cannot be verified against this paper until ERA5 is wired into the GDD computation.

**What transfers from this paper (verified, product-agnostic):**
- Thermal time/GDD positional encoding improves cross-region SITS generalization vs calendar time.
- GDD formula with T_base = 0 °C, T_cap = 30 °C is a reasonable default when crop type is unknown.
- Accumulating GDD from SITS start date (Jan 1) preserves phenological order.
- Learnable thermal-time encodings (Recurrent > Concat ≈ Sinusoidal > Fourier) are worth evaluating.

**What remains deferred (findings-13):**
- Quantitative GDD values and cross-region generalization magnitudes under ERA5 (vs E-OBS here).
- Whether the +15.3% F1 gain of TPE-Recurrent over the calendar baseline holds with ERA5-derived GDD.
- Sensitivity of results to ERA5's spatial/temporal resolution vs E-OBS 0.1° daily.

**Action:** Revisit findings-13 once the ERA5 weather source is wired and GDD is recomputed; then compare against these E-OBS-based benchmarks.

---

## 5. TO VERIFY FROM PDF (mark as "PDF available - verified")

All items below were verified directly from the extracted PDF text (`2203.09175v2.pdf`, 11 pages):

| # | Item | Verified from PDF? | Evidence |
|---|---|---|---|
| 1 | Paper title & authors | PDF available - verified | Page 1: title, Nyborg/Pelletier/Assent, Aarhus/IRISA/FieldSense |
| 2 | arXiv ID & version | PDF available - verified | Page 1: "arXiv:2203.09175v2 [cs.CV] 14 Jun 2022" |
| 3 | TPE concept (thermal time replaces calendar time) | PDF available - verified | Abstract; §1, §4.1 |
| 4 | GDD formula with T_base=0, T_cap=30 | PDF available - verified | Page 4, Eq. (2); §4.1 "Thermal time" |
| 5 | Weather source = E-OBS (daily min/max, 0.1° grid) | PDF available - verified | Page 6, §5.1 Setup |
| 6 | Four TPE strategies (Sinusoidal/Concat/Fourier/Recurrent) | PDF available - verified | Pages 5–6, §4.2–4.5; Figure 2 |
| 7 | Dataset = TimeMatch, Sentinel-2 L1C, 4 tiles (AT1/DK1/FR1/FR2), 2017 | PDF available - verified | Page 6, §5.1; Figure 3 |
| 8 | 9 crop types (≥200 samples/tile), 280K parcels, 70/10/20 split | PDF available - verified | Page 6, §5.1 |
| 9 | Leave-one-region-out generalization setup | PDF available - verified | Pages 6–7, §5.2 |
| 10 | TPE-Recurrent best: F1 +15.3% vs PSE+LTAE, +3.4% vs ShiftAug | PDF available - verified | Pages 7–8, Table 1, §5.2 |
| 11 | TPE-Sinusoidal +14.1% F1 vs baseline; TPE-Fourier −1.8% vs TPE-Sinusoidal | PDF available - verified | Page 8, §5.2 Analysis |
| 12 | Code at github.com/jnyborg/tpe | PDF available - verified | Abstract; Page 7 |
| 13 | Residual gap to upper-bound; spectral-signature differences left to future work | PDF available - verified | Page 7, §5.2 |

**Overall verification status: PDF available - verified.** All substantive claims in this study note were cross-checked against the extracted PDF text. No claims were inferred beyond the document.

---

## Issues encountered

- **PDF text extraction:** `pypdf` (v6.19.0) successfully extracted all 11 pages (~50.6k characters). `PyPDF2` (v3.0.1) is also available but was not needed. No extraction errors occurred.
- **Python environment:** Ran under conda env `geo` (Python 3.12.14) at `D:\Dev\Miniforge3\envs\geo\python.exe`, per project convention (no system Python).
- **Console encoding:** Printing extracted text to the Windows console raised a `UnicodeEncodeError` (charmap/cp1252) on a ligature character (`\ufb01`); this affected only console display, not the file write. The extracted text file is valid UTF-8.
- **Deferred item:** "Findings-13" quantification under ERA5 is deferred (paper used E-OBS, not ERA5) — see Section 4.

---

**Deliverable written:** `D:\RS\Thesis\thesis_implementation\.tmp\study_notes\Nyborg-2022-study-note.md`
