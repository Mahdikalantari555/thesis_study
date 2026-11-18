## ADDED Requirements

### Requirement: Normal-bank novelty scoring arm

The system SHALL provide a dev-only scoring arm that computes a latent novelty score for each
observed bin as the distance of the frozen `gru_ae_main` encoder embedding to a normal bank built
exclusively from train-split cycles, comparable only against bank bins with the same
band-mask-signature class (pooled fallback with a recorded flag where a class is too sparse), fused
with the existing channel-max reconstruction statistic and calibrated with the SAME 5 %
cycle-level FAR rule and the SAME severity sweep as the literature-grounded protocol. The arm SHALL
be evaluated against `recon_only` and `b1_phasez_causal` under identical splits, metrics and seeds
protocol; the frozen checkpoint sidecar and the platform payload SHALL NOT change unless a
follow-up freeze change explicitly replaces them.

#### Scenario: Bank provenance
- **WHEN** the normal bank is built
- **THEN** every bank entry records its cycle id and split, a unit test asserts all entries come
  from the `train` split, and a `bank.json` sidecar stores the split hash, encoder checkpoint hash
  and bank statistics

#### Scenario: Mask-class comparison
- **WHEN** a dev bin with a given observed-band mask signature is scored
- **THEN** its distance is computed only against bank bins of the same signature class (or the
  recorded pooled fallback), and fully-unobserved bins score `absent` rather than 0

#### Scenario: Fusion recalibration
- **WHEN** a fusion variant (max or weighted sum) is evaluated
- **THEN** its alarm threshold is re-calibrated on clean cycles for that variant so the 5 %
  cycle-level FAR budget holds by construction, and the calibration hash is stored with the result

#### Scenario: No platform drift
- **WHEN** this change completes without an adoption decision
- **THEN** `checkpoints/gru_ae_main.json`, the registry versions and the exported payload are
  byte-identical to their pre-change state
