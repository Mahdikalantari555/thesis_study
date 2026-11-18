# Spec Delta

## Purpose

Quantifies anomaly-detection robustness across cloud-induced observation cadence degradation (`16-day` to `monthly`) with and without explicit `date/Δt` conditioning alongside `E-ALIGN`/`E-SEG`/`E-NORM` stability checks (RQ4), and measures early-detection lead time in days prior to index threshold alarms under Leave-One-Year-Out validation (RQ5).

## ADDED Requirements

### Requirement: Cloud-completeness degradation with date and delta-t conditioning test (RQ4)
The system SHALL evaluate anomaly detection performance across progressive observation completeness levels (`100%`, `75%`, `50%`, `35%` corresponding to ~16-day down to ~monthly cadences and winter cloud blocks), comparing SSL with explicit `date/Δt` conditioning against SSL without `date/Δt` conditioning and statistical baselines, alongside `E-ALIGN`, `E-SEG`, and `E-NORM` stability metrics.

#### Scenario: Cadence degradation sweep reports completeness curve and delta-t benefit
- **WHEN** `run_rq4_cloud_and_stability.py` subsamples observation sequences from 100% down to 35% completeness
- **THEN** the system outputs `AUC-PR` and `Recall@5%` at each completeness level for `date/Δt`-conditioned SSL, unconditioned SSL, and B1/B2, plus `E-ALIGN`, `E-SEG`, and `E-NORM` stability tables

### Requirement: Leave-One-Year-Out early-detection lead-time measurement (RQ5)
The system SHALL measure first-detection lead time in days (`t_index_alarm - t_model_alarm`) at matched false-alarm budgets under Leave-One-Year-Out validation on progressive stress onset trajectories and natural multi-year episodes, comparing SSL against operational NDVI/index thresholds and referencing the 12-day EigenCL benchmark.

#### Scenario: Progressive stress onset yields day-level lead-time comparison
- **WHEN** `run_rq5_early_detection.py` evaluates SSL and operational NDVI threshold alarms at an equal 5% false-alarm rate on progressive stress episodes
- **THEN** the system reports median and mean detection delay in days, lead-time advantage over NDVI thresholds with 95% CIs, and comparison against the 12-day reference point
