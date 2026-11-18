# Study Note: T³S — Thermal Time for Crop Mapping

**Source paper**: Turkoglu, M. O., Ledain, S., Lauber, T., Zweidler, J., & Aasen, H. (2025). T³S: Think in Thermal Time for Generalizable Crop Mapping from Satellite Image Time Series. arXiv:2506.12885 [cs.CV]. https://arxiv.org/abs/2506.12885

**PDF available**: `D:\RS\Thesis\New_papers\2506.12885v5.pdf` — text extracted with `pypdf` v6.19.0 (26 pages, 65,880 chars). All claims below verified against the extracted PDF text.

---

## Verified APA 7th Citation

Turkoglu, M. O., Ledain, S., Lauber, T., Zweidler, J., & Aasen, H. (2025). T³S: Think in thermal time for generalizable crop mapping from satellite image time series. arXiv preprint arXiv:2506.12885. https://arxiv.org/abs/2506.12885

**Authors (verified from PDF page 1)**:
1. Mehmet Ozgur Turkoglu — Earth Observation of Agroecosystems Team, Agroscope, Switzerland
2. Selene Ledain — Earth Observation of Agroecosystems Team, Agroscope, Switzerland
3. Thomas Lauber — Earth Observation of Agroecosystems Team, Agroscope, Switzerland
4. Jeffrey Zweidler — ETH Zurich, Switzerland
5. Helge Aasen — Earth Observation of Agroecosystems Team, Agroscope, Switzerland

**Version**: arXiv:2506.12885v5, [cs.CV], 9 Aug 2026

**Code & dataset**: https://github.com/moturkoglu/T3S ; SwissCrop on HuggingFace: https://huggingface.co/datasets/EOA-team/SwissCrop25

---

## Key Findings Relevant to Thermal Time / GDD for Crop Mapping

### 1. Core claim: thermal-time re-indexing aligns phenology across years

- Crop development is driven by thermal conditions; temperature determines growth and phenological development (citing [20, 46]).
- Inter-annual temperature variability means the same crop reaches key growth stages weeks earlier or later depending on the season (Figure 1 in PDF: cGDD across Switzerland over 30 years).
- A model trained on calendar-indexed time series encounters a shifting input distribution across years because phenologically equivalent growth stages appear at different positions in the sequence.
- Re-indexing observations by thermal time (cGDD) warps the time axis so equivalent phenological stages align irrespective of inter-annual temperature variability (Figure 2 in PDF: NDVI aligned by calendar date vs. cGDD).

### 2. Cross-year generalization: consistent improvement over baselines

Evaluated on SwissCrop (leave-one-year-out, train on one season, test on remaining two, six folds total). T³S with U-TAE backbone:

| Metric | U-TAE | MC-Dropout | TPE (Sinusoidal) | Deformable Sampling | T³S (U-TAE) |
|--------|-------|------------|------------------|---------------------|-------------|
| Accuracy (%) | 71.2 ± 0.6 | 71.9 ± 0.6 | 71.3 ± 3.5 | 75.4 ± 1.0 | **77.0 ± 0.5** |
| IoU (%) | 55.3 ± 0.8 | 56.1 ± 0.7 | 55.5 ± 4.1 | 60.5 ± 1.2 | **62.6 ± 0.7** |
| mIoU (%) | 17.3 ± 0.7 | 17.3 ± 0.7 | 17.1 ± 1.9 | 20.5 ± 0.9 | **21.5 ± 1.0** |
| ECE (%) | 5.1 ± 1.2 | 3.4 ± 0.7 | 7.7 ± 2.9 | 6.3 ± 2.5 | **1.1 ± 0.6** |
| NLL | 0.929 | 0.902 | 1.015 | 0.868 | **0.698** |
| Brier | 0.403 | 0.395 | 0.416 | 0.361 | **0.314** |

- T³S improves overall accuracy by ~6% over vanilla U-TAE.
- ECE reduced roughly fourfold (5.1% → 1.1%), approaching perfect calibration.
- Lower NLL and Brier score indicate sharper, more reliable uncertainty estimates.

### 3. Uncertainty calibration is a standout strength

- T³S achieves ECE ≈ 1.1%, compared to 5.1% for U-TAE and 7.7% for TPE.
- Qualitative analysis (Figure 5): T³S elevates uncertainty around its own errors and flags annotation mistakes; U-TAE remains overconfident and produces diffuse, misaligned uncertainty maps.
- MC-Dropout achieves second-best ECE (3.4%) but is specifically designed for calibration and gives only modest accuracy gains.

### 4. Robustness under label scarcity (10% training data)

- T³S trained on just 10% of labels still **outperforms U-TAE trained on the full dataset**.
- T³S calibration remains substantially more reliable under low-data conditions.
- Reducing temporal sequence length from 24 to 12 timestamps causes only a minor drop for T³S; U-TAE degrades more substantially (Appendix C).

### 5. Early-season prediction

- At 75th-percentile cutoff (end of September), T³S remains virtually unchanged while U-TAE drops sharply.
- At 50th-percentile cutoff (end of June), T³S still achieves similar accuracy and better calibration than U-TAE at the 75th-percentile cutoff.
- Practically suitable for operational in-season crop monitoring where timeliness and reliable uncertainty estimates are critical.

### 6. Cross-region generalization (TimeMatch: Denmark → South of France; South of France → Denmark)

Using PSE+LTAE backbone:

| Direction | Method | Accuracy (%) | F1 (%) | ECE (%) |
|-----------|--------|--------------|--------|---------|
| SoF → Denmark | PSE+LTAE | 31.6 ± 3.3 | 31.8 ± 3.6 | 37.9 ± 3.3 |
| SoF → Denmark | TPE (RNN) | 27.3 ± 4.5 | 26.4 ± 5.4 | 44.0 ± 5.2 |
| SoF → Denmark | T³S | **38.6 ± 2.1** | **36.4 ± 2.7** | **31.0 ± 2.8** |
| Denmark → SoF | PSE+LTAE | 36.5 ± 2.2 | 36.3 ± 3.1 | 37.3 ± 2.1 |
| Denmark → SoF | TPE (RNN) | 47.4 ± 5.9 | 49.7 ± 6.6 | 26.3 ± 7.4 |
| Denmark → SoF | T³S | **57.7 ± 6.8** | **59.2 ± 4.8** | **7.2 ± 3.1** |

### 7. Model-agnostic — works across architectures

- Evaluated on three backbones: U-TAE (CNN + temporal attention), PSE+LTAE (pixel-set encoder + lightweight attention), Galileo (pretrained EO foundation model).
- T³S + Galileo closes most of the gap to T³S + U-TAE despite Galileo's scale (74.7% vs 77.0% accuracy).
- Operating at the input level (preprocessing), T³S applies where thermal-time positional encoding (TPE) cannot:
  1. Architectures without a positional-encoding module (RNN/CNN backbones).
  2. Models with coarse temporal granularity (e.g., monthly timesteps).
  3. Frozen pretrained foundation models (e.g., Tessera, AlphaEarth) where PE cannot be altered.

### 8. SwissCrop dataset (first of its kind)

- Three-year (2021–2023), country-scale (Switzerland), Sentinel-2 Level-2A SITS.
- ~110 timestamps per season, ~20K analysis-ready cubes per year, 128×128 px (1280×1280 m at 10 m resolution).
- 50 crop types, long-tail class distribution.
- Paired with daily temperature data from MeteoSwiss (1 km grid, resampled to 10 m via nearest-neighbor).
- First dataset simultaneously country-scale, multi-year, and paired with temperature data.

### 9. Climatic range of SwissCrop

- 2021: cool and wet.
- 2022 and 2023: two warmest years on record (+1.6°C and +1.4°C above 1991–2020 norm).
- The 2021→2022 transition induced phenological shifts beyond typical inter-annual variability.

---

## Methods Used (Thermal Time Encoding)

### GDD computation (Section 3.3, Equation 1)

For a given day i:

```
GDDᵢ = max(0, (Tmaxᵢ + Tminᵢ)/2 − Tbase)
```

- Tmaxᵢ, Tminᵢ: daily maximum and minimum temperatures.
- Tbase = 0°C (common value for temperate-climate crops; same as TPE [26]).
- Crop type unknown at sampling time → single crop-agnostic threshold.

### Cumulative GDD (Equation 2)

```
cGDD_d = Σᵢ₌₁ᵈ GDDᵢ
```

### T³S Algorithm (Algorithm 1)

```
function T³S(X, cGDD, cloudMask, T):
    t_min ← min(cGDD)
    t_max ← max(cGDD)
    Δ ← (t_max − t_min) / T          # T = target temporal length (fixed at 24)
    selected ← []
    current ← t_min
    while |selected| < T and current < t_max:
        next ← current + Δ
        window ← {i | current ≤ cGDD[i] < next}
        if window ≠ ∅:
            best ← arg maxᵢ∈window X (cloudMask[i] = 0)   # least-cloudy observation
            append best to selected
        current ← next
    sort(selected)
    return X[selected, ...]   # shape [T, H, W, B]
```

- Partition the cGDD range [cGDD_min, cGDD_max] into T equal intervals.
- Within each interval, select the least-cloudy satellite observation using the Sentinel-2 Scene Classification Layer (SCL) cloud mask.
- T = 24 uniformly sampled observations per season (roughly one image every 15 days); justified by PASTIS analysis showing only 0.2% accuracy drop while halving compute.
- Purely input-level preprocessing — no architectural modification required.
- Cloud-aware selection is intrinsic to the method (retains least-cloudy acquisition in each thermal-time bin).

### Temperature data source

- MeteoSwiss near-surface temperature fields (minimum, maximum, average) on 1 km, 2 km, and 5 km grids.
- Study uses 1 km daily minimum (TminD) and maximum (TmaxD) temperature series.

### Training details (Appendix G)

- 100 epochs, batch size 8, T = 24, image size 128×128 px.
- Adam optimizer, initial LR 0.001, OneCycleLR with max LR 0.01, 30% warm-up.
- U-TAE: encoder widths [128,128,128,256], decoder widths [32,64,128,256], stride conv k=4 s=2 p=1, nhead=16, d_model=256.
- Features standardized per-channel to zero mean/unit variance.
- Trained on single NVIDIA RTX 4090, ~3 days.

### Key design insight

- Thermal-time sampling vs. encoding: T³S couples thermal-time sampling with cloud-aware selection. Even against a strengthened baseline (DS+TPE: TPE + same cloud-aware selection), T³S outperforms on accuracy (77.0 vs 76.4) and calibration (1.1% vs 6.3% ECE, ~6× lower). The gains stem from thermal-time alignment via sampling, not cloud filtering alone.

---

## Findings-13 Implications (Relevant for GDD/Thermal Time R4)

**Status: DEFERRED — pending ERA5 wiring.**

This section addresses implications relevant to findings-13 for GDD/thermal time R4 in the thesis context. Per project notes, these implications are deferred until ERA5 data is wired into the pipeline. No findings-13 claims can be verified against this paper until ERA5 integration is complete.

**Items to revisit once ERA5 is wired:**
- Cross-year GDD/thermal-time re-indexing using ERA5 temperature instead of MeteoSwiss.
- Early-season prediction performance with ERA5-derived cGDD.
- Uncertainty calibration (ECE) behavior with ERA5 temperature inputs.
- Label-scarcity robustness (10% training regime) under ERA5 thermal time.
- Model-agnostic applicability of T³S to thesis backbones (CNN-Mamba, SSL encoders).

---

## TO VERIFY FROM PDF

All items below marked **"PDF available — verified"** (text extracted from `D:\RS\Thesis\New_papers\2506.12885v5.pdf` using pypdf v6.19.0, 26 pages):

| # | Item | Verified from PDF? | Notes |
|---|------|-------------------|-------|
| 1 | Full author list (5 authors) | ✅ PDF available — verified | Page 1 |
| 2 | Affiliations (Agroscope + ETH Zurich) | ✅ PDF available — verified | Page 1 |
| 3 | arXiv ID and version (2506.12885v5) | ✅ PDF available — verified | Page 1 header |
| 4 | Title | ✅ PDF available — verified | Page 1 |
| 5 | T³S = Thermal Time-based Temporal Sampling | ✅ PDF available — verified | Abstract, Section 3.3 |
| 6 | GDD formula with Tbase = 0°C | ✅ PDF available — verified | Page 7, Equation 1 |
| 7 | cGDD accumulation formula | ✅ PDF available — verified | Page 7, Equation 2 |
| 8 | Algorithm 1 (T³S sampling procedure) | ✅ PDF available — verified | Page 7 |
| 9 | T = 24 temporal length | ✅ PDF available — verified | Pages 5-6, Appendix A |
| 10 | Three backbones: U-TAE, PSE+LTAE, Galileo | ✅ PDF available — verified | Pages 4, 9-10 |
| 11 | SwissCrop: 3 years (2021–2023), Switzerland | ✅ PDF available — verified | Section 4, Appendix F |
| 12 | SwissCrop: 50 crop types, long-tail distribution | ✅ PDF available — verified | Section 4, Appendix F |
| 13 | SwissCrop: paired MeteoSwiss temperature data | ✅ PDF available — verified | Section 4, Appendix F |
| 14 | Cross-year accuracy ~77.0% (T³S+U-TAE) | ✅ PDF available — verified | Table 1 |
| 15 | ECE ~1.1% (T³S+U-TAE) | ✅ PDF available — verified | Table 1 |
| 16 | Low-data robustness (10% labels) | ✅ PDF available — verified | Section 5.5, Figure 6 |
| 17 | Early-season prediction (50th/75th percentile) | ✅ PDF available — verified | Section 5.5, Figure 6 |
| 18 | Cross-region TimeMatch results | ✅ PDF available — verified | Table 3 |
| 19 | T³S vs TPE controlled ablation (DS+TPE) | ✅ PDF available — verified | Section 5.7, Appendix E, Table 6 |
| 20 | Model-agnostic applicability (no PE needed) | ✅ PDF available — verified | Sections 5.7, E.2 |
| 21 | Training details (100 epochs, RTX 4090, ~3 days) | ✅ PDF available — verified | Appendix G |
| 22 | GitHub repo: https://github.com/moturkoglu/T3S | ✅ PDF available — verified | Abstract, Appendix G |
| 23 | SwissCrop on HuggingFace | ✅ PDF available — verified | Appendix F footnote 4 |
| 24 | Limitation: temperature as sole phenological driver | ✅ PDF available — verified | Section 6 |

---

## Summary for Thesis Context

T³S demonstrates that replacing calendar-time sampling with cumulative growing degree days (cGDD) thermal-time sampling substantially improves cross-year crop mapping generalization and uncertainty calibration, with no architectural changes required. Key takeaways relevant to the thesis (sugarcane water-salinity stress, GDD/thermal time R4):

1. **Thermal time alignment matters more than model capacity** — Galileo foundation model underperforms vanilla U-TAE; T³S alignment closes most of the gap.
2. **Uncertainty calibration improves dramatically** (4× ECE reduction) — valuable for operational deployment where miscalibration leads to costly decisions.
3. **Label-scarcity robustness** — T³S on 10% labels beats full-data U-TAE; relevant for the thesis's label-free/anomaly-detection pivot.
4. **Early-season viability** — T³S stable at 50th-percentile cutoff; relevant for in-season monitoring.
5. **Input-level preprocessing** — applies to architectures without modifiable positional encoding (including CNN-based and frozen foundation models), broadening applicability to thesis backbones.

**Deferred**: Findings-13 implications pending ERA5 wiring. All PDF-derived claims above are verified.
