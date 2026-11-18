# Spec Delta

## Purpose
Export trained models with weights, configuration, and normalization statistics so they can be reproduced, transferred, and later adapted.

## ADDED Requirements

### Requirement: SafeTensors export
The system SHALL export final model weights as SafeTensors without pickle.

#### Scenario: Load release
- **WHEN** a release directory is loaded
- **THEN** weights are restored into a model built from the saved config

### Requirement: Config and stats persistence
The system SHALL save model config and normalization statistics alongside weights, and SHALL require normalization stats for use.

#### Scenario: Missing stats
- **WHEN** normalization stats are absent
- **THEN** the model is not considered usable

### Requirement: Deterministic training
The system SHALL seed all random generators and record git SHA, data version, dependency lock, splits, and seed in experiment tracking.

#### Scenario: Reproduce run
- **WHEN** the same inputs and seed are used
- **THEN** results are reproducible within configured tolerance

### Requirement: Transferable interface
The system SHALL expose a model loading interface that supports future fine-tuning and transfer across fields or crops.

#### Scenario: Fine-tuning
- **WHEN** new field data is available
- **THEN** the exported model can be loaded and fine-tuned without retraining from scratch

### Requirement: Backend abstraction
The system SHALL define a phenology backend interface so future Rust implementations can be swapped without changing callers.

#### Scenario: Backend selection
- **WHEN** backend is set to numpy or rust
- **THEN** the same phenology functions are invoked through the interface
