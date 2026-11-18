## ADDED Requirements

### Requirement: Patch absorption measurement

The system SHALL measure, for each patch arm, the error at three
checkpoints (before onset, first step after onset, several steps after) on
persistent-family injections and the absorption ratio A_patch (mean
residual on injected anomalies for a model trained with them present ÷ the
same for a model trained clean), reporting it against gru_ae_main's
α ≈ 0.45 and gru_pred's measured A. The absorption ratio SHALL be a
required field in every future arm report.

#### Scenario: Absorption is quantified, not asserted

- **WHEN** a patch arm is evaluated on persistent injections
- **THEN** the three-checkpoint error profile and A_patch with bootstrap
  CIs over injected cycles are reported next to the reconstruction arm's
  measured α

### Requirement: Contamination sensitivity experiment (E7)

The system SHALL train patch arms with persistent/ndvi S4 injected into
{0%, 5%, 10%} of train field-cycles × trimmed-loss {on, off} × one
curation round {on, off} (curation removes a pre-registered top-2% of
train field-cycles scored by the clean model, with removed ids recorded in
the run manifest), and SHALL report A_patch and clean MDM80 per cell.
σ tables and alarm calibration SHALL always be re-fitted from the CLEAN dev
residuals of the retrained model. The adopted configuration SHALL be the
highest A_patch whose clean MDM80 stays within one standard error of the
clean baseline, preferring the simpler configuration on ties; if no
configuration meaningfully reduces absorption, the honest negative SHALL be
recorded and the memory-augmented escalation SHALL go to the owner as a
separate decision.

#### Scenario: Curation is auditable

- **WHEN** the curation round removes training cycles
- **THEN** the removed cycle ids are written to the run manifest and the
  retraining uses the remaining set with a recorded count

#### Scenario: Clean performance is protected

- **WHEN** a contaminated-training configuration is adopted
- **THEN** its clean MDM80 on the unchanged protocol is within one standard
  error of the clean-trained baseline, and the calibration used only clean
  dev residuals
