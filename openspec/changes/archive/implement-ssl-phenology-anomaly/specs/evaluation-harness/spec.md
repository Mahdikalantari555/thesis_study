# Spec Delta

## Purpose
Evaluate anomaly detection methods using synthetic injection, weak proxies, stability tests, and statistically sound comparisons without real labels.

## ADDED Requirements

### Requirement: Synthetic injection
The system SHALL inject controlled anomalies into held-out normal cycles with varied depth, duration, phase, delay, and temperature increase.

#### Scenario: Recall measurement
- **WHEN** synthetic anomalies are injected
- **THEN** recall at a fixed alert rate and detection delay are reported

### Requirement: Weak proxy validation
The system SHALL compare anomaly scores to ETa, yield, and CWSI proxies using Spearman correlation and AUC-PR.

#### Scenario: CWSI circularity
- **WHEN** CWSI is used as a proxy
- **THEN** an LST ablation is also reported

### Requirement: Stability testing
The system SHALL test stability under random observation deletion, harvest-date shifts, trimming thresholds, and seed changes.

#### Scenario: Parameter sensitivity
- **WHEN** the trimming threshold changes
- **THEN** anomaly ranking stability is reported

### Requirement: Statistical comparison
The system SHALL compare methods using paired Wilcoxon signed-rank tests with Holm correction and cluster bootstrap confidence intervals.

#### Scenario: Method comparison
- **WHEN** two methods are compared
- **THEN** effect size and confidence intervals are reported without assuming normality

### Requirement: Cross-validation
The system SHALL use region-blocked cross-validation and SHALL report temporal stability separately.

#### Scenario: Region block
- **WHEN** a region is held out
- **THEN** baseline and normalization statistics are built only from training regions
