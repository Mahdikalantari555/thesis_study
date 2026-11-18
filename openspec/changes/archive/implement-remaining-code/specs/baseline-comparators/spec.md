# Spec Delta

## Purpose

Implement the full baseline ladder (B0 calendar DOY, B2 GDD and landmark axes, B3 IsolationForest and ECOD) and compare GRU-AE against the masked Transformer with statistical confidence intervals.

## ADDED Requirements

### Requirement: Calendar z-score baseline B0
The baseline package SHALL implement a calendar Day-of-Year robust median/MAD z-score baseline (B0) that scores cycles by ~15-day DOY bins without harvest alignment.

#### Scenario: Calendar scoring
- **WHEN** B0 fits and scores field cycles
- **THEN** observations are compared against normal-cycle median and MAD in their corresponding calendar DOY bin

### Requirement: Alternative phase-axis baselines B2
The baseline package SHALL implement B2 phenology baselines aligned by cumulative Growing Degree Days since harvest and by piecewise-linear landmark registration.

#### Scenario: GDD and landmark alignment
- **WHEN** B2 runs with GDD or landmark axes
- **THEN** cycle observations are binned along the selected phase axis and scored with stratum-aware robust statistics

### Requirement: Non-parametric cycle baselines B3
The baseline package SHALL implement IsolationForest and ECOD anomaly detectors operating on per-cycle summary feature vectors.

#### Scenario: Feature-based outlier scoring
- **WHEN** B3 fits on normal training cycles and scores evaluation cycles
- **THEN** both IsolationForest and ECOD produce bounded per-cycle anomaly scores

### Requirement: GRU-AE training and SSL model comparison
The training pipeline SHALL accept `gru_ae` and `transformer` model options via CLI overrides and SHALL compare both SSL architectures on reconstruction loss and anomaly detection metrics.

#### Scenario: Model option selection
- **WHEN** `train_ssl.py` is invoked with `model=gru_ae`
- **THEN** it trains and exports the bidirectional GRU autoencoder release and enables head-to-head comparison with the masked Transformer
