# Spec Delta

## Purpose

Enforces the literature boundary that statistical or SSL anomaly does not equal crop stress without independent agronomic validation, while evaluating frozen SSL representations via environmental probing (RQ7) and analyzing training contamination and false-alarm confounders (RQ8).

## ADDED Requirements

### Requirement: Independent multi-proxy validation gate separating anomaly from stress
The system SHALL label raw model outputs strictly as `anomaly_score` and SHALL require statistically significant concordance against independent proxies (`ETa`, non-circular `CWSI` evaluated on LST-dropped models, per-cycle `yield` when present, or top-K expert event review) before assigning `proxy_corroborated` or `agronomic_validated` stress status.

#### Scenario: Unvalidated or circular score is blocked from stress claim
- **WHEN** an anomaly detector is evaluated without independent proxy significance or relies solely on LST-included CWSI correlation
- **THEN** the validation gate classifies the claim status as `unverified_anomaly` or `circular_proxy_rejected` rather than `validated_stress`

### Requirement: Frozen SSL environmental linear/ridge probing (RQ7)
The system SHALL evaluate frozen SSL cycle embeddings (without fine-tuning backbone weights) via cross-validated ridge/linear probes predicting agro-environmental targets (`ET0`, cumulative `GDD`, solar `radiation`, `ETa`/moisture regime, and `ratoon` class).

#### Scenario: Frozen SSL embeddings outperform random-init embeddings on agro-climatic probes
- **WHEN** `run_rq7_rq8.py` fits out-of-fold ridge probes on frozen pretrained SSL embeddings versus untrained random-weight embeddings
- **THEN** pretrained embeddings achieve higher out-of-fold $R^2$ / Spearman correlation across environmental targets

### Requirement: Training contamination robustness and false-alarm confounder decomposition (RQ8)
The system SHALL quantify detection degradation across training anomaly contamination rates (`0%` to `30%`) with versus without iterative trimming / trimmed Huber loss, and SHALL decompose natural false alarms across structural confounders (cloud-gap proximity, harvest-boundary proximity, `L8/L9` sensor transition, and ratoon number).

#### Scenario: Trimmed SSL and B1 resist 20% training contamination better than untrimmed
- **WHEN** 0%, 10%, 20%, and 30% contaminated cycles are injected into the training set
- **THEN** the system reports `AUC-PR` retention curves for trimmed versus untrimmed training and outputs a confounder breakdown table for false alarms
