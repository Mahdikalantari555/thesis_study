# Spec: Literature SSL Models

## Purpose

Defines the architecture, training objectives, and evaluation interfaces for self-supervised crop anomaly detection models grounded in recent remote-sensing literature, specifically STS-Net, Tiny-CNN-Mamba, and Time2Agri.

## ADDED Requirements

### Requirement: STS-Net spatio-temporal autoencoder
The system SHALL implement the STS-Net autoencoder architecture using spatio-temporal convolutions to learn normal crop phenological representations and score anomalies via multi-band reconstruction error.

#### Scenario: Anomaly scoring via reconstruction error
- **WHEN** an input cycle tensor of shape (batch, phase_bins, bands) is passed to the trained STS-Net model
- **THEN** the model outputs a reconstructed tensor of identical shape and computes per-bin Huber anomaly scores without requiring ground truth labels.

### Requirement: Tiny-CNN-Mamba state space model
The system SHALL implement the Tiny-CNN-Mamba architecture combining lightweight 1D convolutional layers for local spectral-temporal feature extraction with a Bidirectional Selective State Space (Mamba) block for capturing long-term phenology dependencies.

#### Scenario: Linear complexity sequence modeling
- **WHEN** processing full-length cycle sequences (e.g. 36 phase bins across 540 days)
- **THEN** the model computes hidden states with linear computational complexity O(L) relative to sequence length and outputs latent representations for anomaly classification or reconstruction.

### Requirement: Time2Agri trajectory contrastive learning
The system SHALL implement Time2Agri-inspired agricultural pretext tasks, including trajectory contrastive loss (NT-Xent) over augmented phenological curves and multi-temporal cloud-gap masking.

#### Scenario: Contrastive trajectory representation
- **WHEN** two stochastically augmented views of the same normal crop cycle are presented to the Time2Agri encoder
- **THEN** the model minimizes the distance between positive trajectory pairs in embedding space while maximizing separation from negative cycles.

### Requirement: Standardized evaluation protocol
All literature SSL models SHALL adhere to the established benchmark harness, supporting train-only fitting, validation-only quantile thresholding, spatial block holdout, and affiliation-based event metrics.

#### Scenario: Prospective benchmark execution
- **WHEN** evaluating STS-Net, Tiny-CNN-Mamba, or Time2Agri on the temporal test set
- **THEN** the harness evaluates points and events strictly without access to test labels during threshold selection and reports paired point AUC-PR, event recall, and delay.
