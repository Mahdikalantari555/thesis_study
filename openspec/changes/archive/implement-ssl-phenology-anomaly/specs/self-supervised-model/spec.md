# Spec Delta

## Purpose
Train masked self-supervised models on field-level cycle sequences and derive reconstruction and embedding-based anomaly scores.

## ADDED Requirements

### Requirement: Cycle tokenization
The system SHALL represent each cycle as a token sequence with one token per real observation, including robust standardized bands, valid fraction, time delta, and conditioning variables.

#### Scenario: Missing observation
- **WHEN** a phase has no observation
- **THEN** no token is created for it

### Requirement: Masked pretext task
The system SHALL randomly mask 15 to 30 percent of tokens plus consecutive blocks of 1 to 3 tokens, and SHALL use Huber loss on masked tokens.

#### Scenario: Cloud-gap mimicry
- **WHEN** a consecutive block is masked
- **THEN** the model must reconstruct the missing observations from context

### Requirement: Trimmed loss
The system SHALL discard the highest-loss fraction of samples in each batch to reduce sensitivity to contaminated training data.

#### Scenario: Anomalous training cycle
- **WHEN** an anomalous cycle has high reconstruction loss
- **THEN** it is less likely to dominate the batch loss

### Requirement: Gated model training
The system SHALL train SSL models only after the statistical baseline passes its gate, and SHALL compare against that baseline.

#### Scenario: No improvement
- **WHEN** SSL does not beat the baseline with confidence intervals
- **THEN** its role is limited to embedding and retrieval

### Requirement: Anomaly scores
The system SHALL produce anomaly scores from reconstruction residuals and kNN embedding distance, scaled to z units using normal-cycle statistics.

#### Scenario: Score combination
- **WHEN** combining SSL scores
- **THEN** rank averaging is used only if each score individually beats the baseline

### Requirement: Leakage prevention
The system SHALL exclude the validation farm subset from training, baseline construction, model selection, and tuning.

#### Scenario: Validation subset
- **WHEN** a field belongs to the validation subset
- **THEN** it is not used in any training or baseline step
