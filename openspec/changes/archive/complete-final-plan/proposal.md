# Proposal — Empirical Thesis Suite (`RQ1–RQ8`, Literature Gaps `G1–G8`, and Remaining Phase 1–2 Plan)

## Why

The completed repository work establishes the engineering backbone and statistical baseline ladder (`B0–B3`, `GRU-AE` vs `MaskedTransformer`, `E-INTRA`, and gated Rust kernels), which the literature review identifies as *prerequisites* rather than the thesis's scientific contribution. Answering the literature-mandated empirical questions (**RQ1–RQ8**, addressing gaps **G1–G8**) with controlled pretext comparisons, equal-alert-budget operational baselines, SSL-level thermal tests, cloud-cadence degradation, early-detection lead times, physiology-validated temporal XAI, and strict non-circular multi-proxy validation ("anomaly ≠ stress") is required to turn the platform into a defensible empirical thesis contribution—even when external 490-field GeoTIFFs are absent locally by providing drop-in full-archive runners plus realistic 490-field × 13.5-year simulation fallbacks.

## What Changes

- **RQ1 (Core, G2 + G7) — Full-Archive SSL vs. Operational Baselines under Leave-One-Year-Out & Equal Alert Budgets**:
  - Implement operational threshold alarms (`NDVIThresholdAlarm`, `CWSIThresholdAlarm`) and supervised/weak-label tree baselines (`RFBaseline`, `GBTBaseline` — XGBoost-class gradient boosted trees) evaluated at matched alert budgets (`Recall@5%`, `Recall@10%`, `AUC-PR`) alongside `B0–B3`, `CUSUM`/`EWMA` slow-drift detectors, and SSL.
  - Implement deterministic `splits.json` supporting **Leave-One-Year-Out (LOYO)** validation across multi-year cycles, 5-fold regional/spatial block CV, calendar drift holdout, field-cluster bootstrap 95% CIs, and paired per-field Wilcoxon signed-rank + Holm step-down correction.
  - Provide `scripts/run_rq1_benchmark.py` targeting the **490-field, 13.5-year Landsat archive** (`--zarr`), with an automatic 490-field × 13.5-year Khuzestan sugarcane archive generator fallback when external rasters are unavailable locally, plus standalone `era5.zarr` (`io/era5.py`) and 8-day Savitzky-Golay Sprint-0 comparator (`phenology/smoothing.py`).
- **RQ2 (G3) — Controlled SSL Pretext Comparison under Matched Budgets**:
  - Implement three controlled SSL pretext arms on the identical 1D Transformer backbone, parameter count, and compute budget (`src/ssl_anomaly/models/pretexts.py` + `scripts/run_rq2_pretexts.py`):
    1. *Masked observation reconstruction* (`masked_recon`),
    2. *Trajectory-contrastive learning* (`traj_contrastive`, InfoNCE across temporal/cloud-gap & spectral-jittered cycle views),
    3. *Synthetic-anomaly degradation detection* (`anomaly_degradation`, AnomalyBERT-style contextual replacement & drift discrimination).
- **RQ3 (G1) — SSL-Level Optical + Thermal (`LST`) Representation Test**:
  - Implement `scripts/run_rq3_lst_ssl.py` testing whether adding `ST_B10` (`LST`) measurably improves SSL representations and anomaly detection over optical-only inputs on strictly **non-LST evaluation targets** (optical canopy collapse, `ETa` evaporative deficit, and frozen-feature moisture probing) to eliminate thermal circularity.
- **RQ4 (G8) — Cloud-Robustness (`16-day → monthly`) & Phase Stability (`E-ALIGN`, `E-SEG`, `E-NORM`)**:
  - Implement `src/ssl_anomaly/eval/cloud_robustness.py` and `scripts/run_rq4_cloud_and_stability.py` quantifying detection performance across observation completeness (`100%` ~8–16d → `75%` ~16d → `50%` ~24d → `35%` ~monthly cadence) **with vs. without explicit `date/Δt` conditioning**, alongside `E-ALIGN` (3-metric axis selection), `E-SEG` ($\pm 16, \pm 32$ d harvest shifts), and `E-NORM` ($q \in \{0, 0.1, 0.2, 0.3\}$).
- **RQ5 (G5) — Early Detection Lead-Time Benchmark (EigenCL 12-Day Reference)**:
  - Implement `src/ssl_anomaly/eval/early_detection.py` and `scripts/run_rq5_early_detection.py` measuring days of early warning ($\Delta t_{\text{early}}$) before operational NDVI/index thresholds at equal false-alarm rates under LOYO validation on progressive stress trajectories and natural multi-year episodes, benchmarked against EigenCL's 12-day reference.
- **RQ6 (G6) — Physiology-Validated Temporal XAI**:
  - Implement `src/ssl_anomaly/xai/` and `scripts/run_rq6_xai.py` providing **Temporal SHAP** (coalition Shapley values over phase windows & bands), **1D Temporal Grad-CAM**, **Integrated Gradients**, and **Temporal Window Occlusion**, validated via **Deletion/Insertion faithfulness AUC**, **weight-randomization sanity checks**, and **plant-physiology sign concordance** (negative `NIR`/`NDVI`/`NDMI` + positive `LST` stomatal-closure warming + positive `SWIR`/`Red`).
- **Independent Multi-Proxy Validation Gate ("Anomaly ≠ Stress") & RQ7–RQ8**:
  - Enforce explicit `anomaly ≠ stress` gating (`src/ssl_anomaly/eval/validation_gate.py`) validating raw anomaly scores against `ETa`, non-circular `CWSI` (using LST-dropped models), optional `yield`, and top-$K$ expert event review before permitting stress-corroborated claims.
  - Implement **RQ7** (`src/ssl_anomaly/eval/probing.py`: frozen-feature linear/ridge probing of agro-meteorological regimes `ET0`, `GDD`, `ETa`, `radiation`, `ratoon`) and **RQ8** (`src/ssl_anomaly/eval/contamination.py`: training contamination sweep $0\text{--}30\%$ + false-alarm confounder decomposition across cloud gaps, harvest edges, `L8/L9` transitions, and ratoon age) in `scripts/run_rq7_rq8.py`.
- **Tracking, CLI, & Strict Literature Non-Goals / Non-Claims**:
  - Add local SQLite MLflow tracking (`utils/tracking.py`), complete `conf/` YAML files, wire `ssl-anomaly` Click CLI subcommands, update `dvc.yaml`, and document all `RQ1–RQ8` results in `docs/findings/` while strictly upholding the literature **Non-Goals**:
    - *Excluded by design*: Patch-level / intra-field 3D-CAE (`E-INTRA` passed), multi-crop / web-GIS labeling / knowledge fusion, ONNX / quantization / edge export, and additional Rust beyond gated `G3`.
    - *Explicit non-claim*: Never claim "first label-free crop-stress detection" (acknowledging EigenCL, Sadbhave, etc.); frame strictly as *"controlled field-level study on a long multi-year Landsat optical+thermal archive, distinguishing statistical/SSL anomalies from validated crop stress."*

## Capabilities

### New Capabilities
- `rq1-archive-and-operational-baselines`: Full-archive (490-field, 13.5-year + synthetic fallback) Leave-One-Year-Out & spatial-block CV benchmark against NDVI/CWSI threshold alarms and RF/GBT baselines at equal alert budgets, plus CUSUM/EWMA slow-drift, Savitzky-Golay 8-day comparator, and standalone `era5.zarr`.
- `rq2-rq3-ssl-pretexts-and-lst`: Controlled three-arm SSL pretext comparison (`masked_recon`, `traj_contrastive`, `anomaly_degradation`) under matched budgets and non-circular SSL-level optical vs. optical+LST representation testing.
- `rq4-rq5-cloud-and-early-detection`: Observation-completeness cloud-robustness evaluation (`16-day` to `monthly`) with/without `date/Δt` conditioning, `E-ALIGN`/`E-SEG`/`E-NORM` stability checks, and LOYO early-detection lead-time measurement against EigenCL's 12-day benchmark.
- `rq6-temporal-xai-physiology`: Temporal SHAP, 1D Grad-CAM, Integrated Gradients, and window occlusion with deletion/insertion faithfulness AUC, weight-randomization sanity checks, and plant-physiology sign-direction validation.
- `validation-gate-and-rq7-rq8`: Multi-proxy `anomaly != stress` validation gate (`ETa`, non-circular `CWSI`, `yield`, top-$K$ review), RQ7 frozen-embedding environmental probing, and RQ8 training contamination & false-alarm confounder analysis.
- `tracking-cli-and-nonclaims`: Local SQLite MLflow provenance tracking, complete Hydra `conf/` tree, wired `ssl-anomaly` CLI subcommands, updated `dvc.yaml`, and thesis findings documenting `RQ1–RQ8` and explicit literature non-claims/non-goals.

### Modified Capabilities

## Impact

- **Code**: Adds modular packages under `src/ssl_anomaly/{baseline/operational.py,io/era5.py,models/pretexts.py,eval/cv.py,eval/cloud_robustness.py,eval/early_detection.py,eval/validation_gate.py,eval/probing.py,eval/contamination.py,xai/,utils/tracking.py}`, updates `baseline/score.py`, `phenology/smoothing.py`, `cli.py`, `conf/`, `dvc.yaml`, and adds `scripts/run_rq{1_benchmark,2_pretexts,3_lst_ssl,4_cloud_and_stability,5_early_detection,6_xai,7_rq8}.py`.
- **Non-Goals Preserved**: Zero Phase 3 3D-CAE/patch expansion, zero multi-crop/web-GIS/knowledge-fusion bloat, zero ONNX/quantization, zero extra Rust crates.
