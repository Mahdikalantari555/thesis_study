# Tasks — Complete Final Plan & Literature Research Questions (`RQ1–RQ8`)

## 1. Phase 1–2 Foundations & RQ1 Operational Baselines (G2, G7)
- [x] 1.1 Add `cusum_detector` and `ewma_detector` slow-drift scorers to `src/ssl_anomaly/baseline/score.py` and `savitzky_golay_8day` comparator to `src/ssl_anomaly/phenology/smoothing.py`
- [x] 1.2 Implement standalone daily `era5.zarr` store and dynamic `T_base` GDD loader in `src/ssl_anomaly/io/era5.py` and generate `data/processed/era5.zarr`
- [x] 1.3 Implement operational baselines (`NDVIThresholdAlarm`, `CWSIThresholdAlarm`, `RFBaseline`, `GBTBaseline`) and equal-alert-budget metrics (`Recall@5%`, `Recall@10%`) in `src/ssl_anomaly/baseline/operational.py`
- [x] 1.4 Implement Leave-One-Year-Out (LOYO), 5-fold spatial-block CV, calendar drift split (`splits.json`), field-cluster bootstrap CIs, and paired Wilcoxon + Holm comparator in `src/ssl_anomaly/eval/cv.py`
- [x] 1.5 Create and run `scripts/run_rq1_benchmark.py` (real 32-farm archive + 490-field × 13.5-year full-archive LOYO benchmark -> `reports/rq1_benchmark.json` & `.csv`)

## 2. RQ2 Pretext Comparison (G3) & RQ3 SSL-Level LST Test (G1)
- [x] 2.1 Implement three controlled SSL pretext arms (`masked_recon`, `traj_contrastive`, `anomaly_degradation`) on a shared 1D Transformer backbone in `src/ssl_anomaly/models/pretexts.py`
- [x] 2.2 Create and run `scripts/run_rq2_pretexts.py` under matched architecture and epoch budgets across 5 seeds (-> `reports/rq2_pretexts.json` & `.csv`)
- [x] 2.3 Create and run `scripts/run_rq3_lst_ssl.py` testing SSL optical-only vs. optical+LST on strictly non-LST targets and moisture regimes (-> `reports/rq3_lst_ssl.json` & `.csv`)

## 3. RQ4 Cloud Robustness (G8), Phase Stability & RQ5 Early Detection (G5)
- [x] 3.1 Implement cloud-completeness degradation (`100% -> 35%`, `16-day -> monthly`) with/without `date/Δt` conditioning plus `E-ALIGN`, `E-SEG`, and `E-NORM` stability evaluators in `src/ssl_anomaly/eval/cloud_robustness.py`
- [x] 3.2 Create and run `scripts/run_rq4_cloud_and_stability.py` (-> `reports/rq4_cloud_and_stability.json` & `.csv`)
- [x] 3.3 Implement LOYO early-detection lead-time evaluator (matched 5% false-alarm budget vs. NDVI threshold and EigenCL 12-day benchmark) in `src/ssl_anomaly/eval/early_detection.py`
- [x] 3.4 Create and run `scripts/run_rq5_early_detection.py` (-> `reports/rq5_early_detection.json` & `.csv`)

## 4. RQ6 Physiology-Validated Temporal XAI (G6)
- [x] 4.1 Implement Temporal SHAP, 1D Temporal Grad-CAM, Integrated Gradients, and Window Occlusion aggregated to phase bins and 3 coarse sugarcane stages in `src/ssl_anomaly/xai/attribution.py`
- [x] 4.2 Implement Deletion/Insertion faithfulness AUC, weight-randomization sanity check, and plant-physiology sign concordance in `src/ssl_anomaly/xai/faithfulness.py`
- [x] 4.3 Create and run `scripts/run_rq6_xai.py` (-> `reports/rq6_xai.json` & `.csv`)

## 5. Independent Validation Gate ("Anomaly != Stress"), RQ7 & RQ8
- [x] 5.1 Implement multi-proxy validation gate (`ETa`, non-circular LST-dropped `CWSI`, optional `yield`, top-K event precision) enforcing `anomaly != stress` in `src/ssl_anomaly/eval/validation_gate.py`
- [x] 5.2 Implement RQ7 frozen-feature environmental ridge/linear probing (`ET0`, `GDD`, `radiation`, `ETa`, `ratoon`) in `src/ssl_anomaly/eval/probing.py`
- [x] 5.3 Implement RQ8 training contamination sweep (`0%–30%`, trimmed vs. untrimmed) and natural false-alarm confounder decomposition in `src/ssl_anomaly/eval/contamination.py`
- [x] 5.4 Create and run `scripts/run_rq7_rq8.py` (-> `reports/rq7_rq8.json` & `.csv`)

## 6. Tracking, CLI, Configs, Tests & Literature-Aligned Documentation
- [x] 6.1 Implement local SQLite MLflow provenance tracker in `src/ssl_anomaly/utils/tracking.py`, add composable Hydra configs under `conf/`, wire `src/ssl_anomaly/cli.py`, and update `dvc.yaml`
- [x] 6.2 Add comprehensive unit tests covering `RQ1–RQ8`, `CUSUM`/`EWMA`, `era5.zarr`, `CV`, `pretexts`, `XAI`, `validation_gate`, `probing`, `contamination`, `tracking`, and `CLI`
- [x] 6.3 Document all `RQ1–RQ8` results, honest limitations, non-goals, and non-claims in `docs/findings/11_rq1_to_rq8_empirical_framework.md`, `docs/findings/00_index.md`, and `docs/findings/08_honest_assessment.md`
