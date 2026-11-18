# Design — Empirical Thesis Suite (`RQ1–RQ8` & Literature Gaps `G1–G8`)

## Context

See `proposal.md` for why this change addresses literature gaps **G1–G8** and research questions **RQ1–RQ8**. Locally in Git, `data/processed/fields.zarr` contains the 32-farm `Farms_subset` (`539` Landsat dates, `2014–2025`), while the full 490-field GeoTIFF archive resides externally (`D:/RS/Thesis/...`). Every RQ runner therefore accepts `--zarr` (running immediately on the real 32-farm archive AND supporting drop-in execution on the 490-field Zarr) plus a realistic **490-field × 13.5-year Khuzestan sugarcane simulator** mode (`--simulate-490-if-missing`) calibrated from the empirical spectral/thermal/weather statistics of `fields.zarr` so full-scale Leave-One-Year-Out (LOYO) and spatial-block CV scaling are verified end-to-end on CPU.

## Goals / Non-Goals

**Goals:**
- Answer **RQ1–RQ8** reproducibly with controlled budgets, Leave-One-Year-Out & spatial-block CV, equal-alert-budget operational comparators (`NDVI`/`CWSI` alarms, `RF`/`GBT`), non-circular multi-proxy validation (`anomaly ≠ stress`), physiology-validated temporal XAI, frozen-feature probing, and contamination analysis.
- Complete the remaining Phase 1–2 `docs/final_plan.md` items (`CUSUM`/`EWMA`, 8-day `Savitzky-Golay`, standalone `era5.zarr`, `E-ALIGN`/`E-SEG`/`E-NORM`, SQLite `MLflow` tracking, `conf/` YAMLs, and wired `ssl-anomaly` CLI).

**Non-Goals (Strictly Enforced per Literature Synthesis):**
- **NO Patch-level / intra-field 3D-CAE or `cube.zarr`** (`E-INTRA` passed with `0/31` farms exceeding 30 days → field-mean stands).
- **NO Multi-crop, Web-GIS labeling, or knowledge-fusion modules** (deferred to post-thesis "Later").
- **NO ONNX / quantization / edge export** (only after FP32 model acceptance on full archive).
- **NO Rust expansion beyond the already-completed gated `G3` kernels**.
- **NO overclaiming "first label-free crop-stress detection"** (EigenCL, Sadbhave et al. exist); frame strictly as *"controlled field-level study on a long multi-year Landsat optical+thermal archive, separating anomaly detection from independently validated crop stress."*

## Decisions

1. **RQ1 Operational Baselines & Equal Alert Budgets (`src/ssl_anomaly/baseline/operational.py`)**:
   - Compare all detectors at fixed operational alert budgets (`Recall@5%` and `Recall@10%` top-ranked cycle alerts, where random = `0.05` / `0.10`) plus `AUC-PR`:
     - `NDVIThresholdAlarm`: flags cycles whose mid-season NDVI drops below $-z_{\alpha}$ or fixed quantile of training-fold peak/plateau NDVI.
     - `CWSIThresholdAlarm`: operational evaporative-stress index alarm (evaluated strictly on non-CWSI targets to avoid tautology).
     - `RFBaseline` & `GBTBaseline`: `RandomForestClassifier` and `HistGradientBoostingClassifier` (scikit-learn native XGBoost-equivalent histogram GBDT, zero extra wheel needed) trained inside each LOYO/spatial fold on engineered cycle features using weak training-fold proxy/self-degraded labels.

2. **RQ2 Controlled Three-Arm Pretext Comparison (`src/ssl_anomaly/models/pretexts.py`)**:
   - Share the **exact same 1D Transformer encoder (`d_model=64, n_heads=4, n_layers=3, ~161K params`)**, optimizer (`AdamW`), and epoch budget across three heads:
     - *Arm 1 (`masked_recon`)*: Masked token Huber reconstruction + sliding-block test residual.
     - *Arm 2 (`traj_contrastive`)*: Temperature-scaled InfoNCE ($\tau=0.2$) over two stochastic phenology-preserving views per cycle (temporal cloud-subsampling vs. small spectral/$\Delta t$ jitter) + cosine kNN anomaly distance to normal training embeddings.
     - *Arm 3 (`anomaly_degradation`)*: AnomalyBERT-style self-supervised token degradation (replacing random 2–5 token blocks with out-of-cycle contextual swaps, local amplitude drops, or linear drift) trained with token-wise binary cross-entropy, scoring test cycles via predicted degradation probability.

3. **RQ3 Non-Circular SSL-Level Thermal (`LST`) Test (`scripts/run_rq3_lst_ssl.py`)**:
   - Train `MaskedTransformer` with `SR_B2..SR_B7 + ST_B10` vs. `SR_B2..SR_B7` only across 5 seeds. Evaluate **exclusively on non-LST targets**: (a) optical canopy perturbations (`ndvi_drop`, `early_senescence`, `phase_shift`), (b) natural `ETa` / evaporative-fraction deficit regimes where `LST` is held out at test time or evaluated via optical reconstruction + frozen-embedding `ET0`/`ETa` probe $R^2$.

4. **RQ4 Cloud-Completeness & `date/Δt` Conditioning (`src/ssl_anomaly/eval/cloud_robustness.py`)**:
   - Subsample real cycle sequences to `100%`, `75%` (~16-day), `50%` (~24-day), and `35%` (~monthly + winter contiguous cloud blocks) completeness, comparing `MaskedTransformer` trained **with** `dtime + dsh + sin/cos(DOY)` token features vs. **without** temporal coordinates (positional index only) and vs. `B1`/`B2-GDD`.

5. **RQ5 Early Detection Lead Time (`src/ssl_anomaly/eval/early_detection.py`)**:
   - Calibrate per-step alert thresholds on clean validation cycles of each LOYO fold to achieve an identical **5% false-alarm rate**, then measure the day of first alarm $t_{\text{alarm}} - t_{\text{onset}}$ on progressive ramp-stress episodes and natural multi-year stress trajectories, reporting $\Delta t_{\text{early}} = t_{\text{NDVI}} - t_{\text{SSL}}$ (days) against EigenCL's 12-day reference.

6. **RQ6 Physiology-Validated Temporal XAI (`src/ssl_anomaly/xai/`)**:
   - Implement **Temporal KernelSHAP** (weighted linear regression over coalition masks of `(stage_window, channel_group)`), **1D Temporal Grad-CAM** ($\text{ReLU}(\sum_d \bar{g}_d A_{t,d})$ on the final Transformer encoder block), **Integrated Gradients** (32-step Riemann integral), and **Window Occlusion**.
   - Validate via **Deletion AUC**, **Insertion AUC**, **Weight-Randomization Sanity Check**, and **Physiology Sign Concordance** (checking signed channel residual/attribution alignment with biophysical stress directions: $\Delta \text{NIR} < 0$, $\Delta \text{NDVI} < 0$, $\Delta \text{NDMI} < 0$, $\Delta \text{ST\_B10} > 0$, $\Delta \text{SR\_B6/B7} > 0$).

7. **Independent Validation Gate (`anomaly ≠ stress`) + RQ7 & RQ8**:
   - `validation_gate.py` enforces explicit status tags (`unverified_anomaly`, `circular_proxy_rejected`, `proxy_corroborated`, `multi_source_validated`) based on Holm-adjusted significance across non-circular proxies (`ETa`, LST-dropped `CWSI`, optional `yield`, top-$K$ event precision).
   - `probing.py` (RQ7) fits RidgeCV / LogisticRegressionCV on **frozen** SSL embeddings across spatial folds; `contamination.py` (RQ8) sweeps `0%, 5%, 10%, 20%, 30%` training contamination and regresses natural false-alarm rates against cloud-gap length, harvest-edge distance, `L8/L9` sensor flag, and ratoon number.

## Risks / Trade-offs

- **[Risk] 32-farm local archive vs. 490-field full archive** → *Mitigation*: Every RQ script runs on the real 32-farm `fields.zarr` AND runs a 490-field × 13.5-year empirically calibrated archive validation pass, reporting both sets of numbers transparently without conflating simulated scaling with real 490-field claims.
- **[Risk] CWSI circularity inflating thermal claims** → *Mitigation*: Hard-coded check in `validation_gate.py` and `run_rq3_lst_ssl.py` rejects any `CWSI` validation where `ST_B10` was an active model input.
