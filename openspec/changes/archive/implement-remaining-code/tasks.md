# Tasks — Implement Remaining Code

## 1. Per-day anomaly
- [x] 1.1 Ensure compute_daily_anomaly.py uses per-bin z-score (not cycle-level)
- [x] 1.2 Update make_map_custom.py to use daily_anomaly.parquet
- [x] 1.3 Verify map colors change per date

## 2. Rust backend
- [x] 2.1 Implement PyO3 binding in rust/src/lib.rs
- [x] 2.2 Add maturin build config
- [x] 2.3 Compile in WSL
- [x] 2.4 Add parity test (rtol=1e-6)
- [x] 2.5 Document build steps in rust/README.md

## 3. Ablation
- [x] 3.1 Create scripts/run_ablation.py (input.drop multirun)
- [x] 3.2 Run weather on/off, LST on/off
- [x] 3.3 Report metric change with CI

## 4. E-INTRA
- [x] 4.1 Create scripts/run_eintra.py (pixel-level harvest detection)
- [x] 4.2 Run on 32 subset farms
- [x] 4.3 Report harvest-date scatter within field

## 5. B0/B2/B3 baselines
- [x] 5.1 Implement B0 (calendar z-score) in baseline/
- [x] 5.2 Implement B2 (GDD/landmark axis)
- [x] 5.3 Implement B3 (IsolationForest/ECOD)
- [x] 5.4 Add comparison script

## 6. GRU-AE (M-A)
- [x] 6.1 Test existing GRU-AE code
- [x] 6.2 Add to train_ssl.py as model option
- [x] 6.3 Compare with Transformer

## 7. Documentation
- [x] 7.1 Update findings with new results
- [x] 7.2 Update 00_index.md