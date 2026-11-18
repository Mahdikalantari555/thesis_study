# Design — Implement Remaining Code

## Per-day anomaly
- For each field and date, determine cycle and bin.
- Compute z = (obs - median) / scale per band.
- S = sqrt(mean(z^2)).
- Store in daily_anomaly.parquet (field, date, anomaly).
- Map uses daily anomaly for color.

## Rust backend
- PyO3 binding for robust_baseline and whittaker_batch.
- Compile in WSL (cargo build --release).
- Parity test: rtol=1e-6 vs NumPy.
- Gate G3: only after profiling.

## Ablation
- Hydra multirun over input.drop (LST, weather, each band).
- 5 seeds per config.
- Report metric change with CI.

## E-INTRA
- Run harvest detection at pixel level on 32 subset farms.
- Report harvest-date scatter within field.
- If >2 observation intervals, prioritize Phase 3.

## B0/B2/B3
- B0: calendar z-score (DOY, median/MAD).
- B2: B1 with GDD or landmark axis.
- B3: IsolationForest/ECOD on per-cycle features.

## GRU-AE (M-A)
- Bidirectional GRU encoder → GRU decoder.
- CPU baseline for SSL comparison.