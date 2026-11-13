# Spec Delta

## Purpose

Evaluates controlled self-supervised pretext objectives (`masked_recon`, `traj_contrastive`, and AnomalyBERT-style `anomaly_degradation`) under matched model capacity and compute budgets (RQ2), and tests whether thermal `LST` measurably improves SSL representations on non-thermal targets (RQ3).

## ADDED Requirements

### Requirement: Controlled three-arm SSL pretext comparison under matched budgets (RQ2)
The system SHALL implement and compare masked observation reconstruction, trajectory-contrastive InfoNCE learning, and AnomalyBERT-style synthetic-anomaly degradation discrimination on the identical 1D Transformer backbone, parameter budget, and training schedule.

#### Scenario: Three pretext arms train under matched epoch and parameter budgets
- **WHEN** `run_rq2_pretexts.py` trains `masked_recon`, `traj_contrastive`, and `anomaly_degradation` across multiple seeds
- **THEN** all three arms use the same encoder architecture and report comparable out-of-fold anomaly detection `AUC-PR`, `Recall@5%`, and 95% confidence intervals

### Requirement: Non-circular SSL-level optical versus optical-plus-LST representation test (RQ3)
The system SHALL train SSL models with and without the thermal `ST_B10` (`LST`) channel across multiple seeds and evaluate anomaly detection and frozen-representation quality strictly on non-LST targets (`ETa` deficit, optical canopy perturbations, and non-thermal moisture regimes).

#### Scenario: Optical+LST vs optical-only SSL evaluated without LST circularity
- **WHEN** `run_rq3_lst_ssl.py` compares SSL trained on `SR_B2..SR_B7 + ST_B10` against SSL trained on `SR_B2..SR_B7` alone
- **THEN** evaluation excludes `ST_B10` perturbations and CWSI-circular targets and reports paired metric deltas with 95% bootstrap confidence intervals
