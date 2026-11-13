# Design: Data and Phenology Readiness

## D1. Literature review scope and output

The output is one document, `docs/findings/13_literature_phenology_and_perturbations.md`, with four sections. Each cited paper gets: citation, data (sensor, crop, region), method, what it implies for this thesis, and whether it generalises across crops. Papers already in `thesis_research/SSL_Proposal` (84-paper matrix) are reused first; new searches fill the gaps.

1. **Automatic phenology / season extraction**
   - Methods: TIMESAT (Savitzky-Golay, asymmetric Gaussian, double logistic), phenofit, BFAST / BFAST-monitor, CCDC, shape-model fitting, DTW-based alignment, learned season detection.
   - Criteria: works with irregular Landsat sampling and cloud gaps; can run causally (in-season) or only retrospectively; handles multiple seasons per year and perennial or ratoon crops; reported accuracy against ground truth.
2. **Time-axis representation for SSL**
   - Options: fixed DSH bins (current), normalised cycle progress (0–1), GDD axis, landmark registration, and irregular tokens with timestamp/position encoding (e.g. SITS-BERT, Presto, SITS-Former, TimeMatch-style).
   - For each: whether it supports causal monitoring, missing-data handling, and crop independence.
3. **Realistic sugarcane stress signatures in optical + thermal time series**
   - Stresses: water deficit, salinity, waterlogging, pests and disease, frost, lodging, early ripening or flowering.
   - For each: bands affected, phase, onset speed, duration, typical magnitude, and recovery. This produces the perturbation catalogue with sources.
4. **SSL for irregular, gappy satellite series (short)**
   - Purpose: confirm or challenge the Masked Transformer + GRU-AE choice at this data scale (about 800 cycles).

**Stopping rule**: about 25–40 relevant papers in total, enough for a decision. This is not an exhaustive review.

## D2. Cycle audit

- **Sample**: 60 cycles, stratified by year (2013–2026), cycle length tercile, and field block, plus every cycle with a sanity flag. The seed is recorded.
- **Sanity flags** (automatic, all cycles):
  - length below 240 or above 480 days (proposed)
  - no clear NDVI drop at the start
  - fewer than 6 valid observations
  - overlap with the neighbouring cycle
  - peak NDVI below 0.4 (proposed)
- **Review**: one plot per cycle (NDVI + LST + valid_frac, detected harvest dates marked). The agent pre-labels each plot. The user confirms a subset of 20 on the platform. Error classes: correct, harvest shifted by more than 30 days, split cycle, merged cycles, not sugarcane / fallow, too sparse.
- **Output**: estimated error rate with a Wilson 95 % CI, per class and per year.
- **Decision rule (proposed)**:
  - Error rate below 10 %: proceed, flagged cycles excluded from dev/test metrics.
  - 10–25 %: tune segmentation parameters, as a separate fix proposal.
  - Above 25 %: segmentation becomes a blocking item before training.
- **Ground truth**: if planting or harvest records arrive, segmentation error in days is computed against them. This is optional and never blocking.

## D3. Data quality report

- Per year and per field block:
  - observations per cycle
  - fraction of valid observations
  - LST values outside 15–55 °C
  - bands with NaN fraction
  - acquisitions with `valid_frac` below 0.5
- **Count check**: confirms the 538-vs-539 date discrepancy (todo OQ5).

## D4. Decision record

After D1–D3, a short section added to `train-and-finalize-main-architecture/design.md` records:
- the input time axis (keep DSH 36×15 or change)
- the segmentation parameters
- the final perturbation set and magnitudes, with sources
- the cycle exclusion rule

Each decision cites the review or audit section it rests on. The user approves this record before any training code is written.

## D5. Stage-conditioned anomaly detection

After D1–D4, stage-conditioned anomaly detection is implemented so that natural phenological decline (senescence, pre-harvest drying, dormancy) is not flagged as stress.

- **Method**: each non-censored cycle-bin is assigned a phenology stage by normalized progress within the cycle (progress = bin_index × bin_days / cycle_length_days):
  - S1 establishment/growth: 0.00–0.25
  - S2 vegetative/reproductive: 0.25–0.60
  - S3 maturity/senescence: 0.60–0.85
  - S4 harvest/dormancy: 0.85–1.00
- **Confidence envelope**: NDVI values pooled per stage across all cycles; median and MAD computed; lower envelope = median − 2 × MAD.
- **Anomaly flag**: a cycle-bin is flagged only if NDVI < lower_envelope[stage]. Natural within-stage decline inside the envelope is NOT flagged.
- **Implementation**: `scripts/stage_conditioned_anomaly.py` (supports `--smoke` and `--all`).
- **Output**: `reports/stage_conditioned_anomaly/stage_conditioned_anomaly.parquet`, `.../anomalies_only.parquet`, `.../summary.json`.
- **Results** (--all, seed=20261111, 370 fields, 799 cycles): 18,505 valid obs, 1,774 flagged (9.59%). S3 lower envelope = −0.027 → senescence decline never flagged.
