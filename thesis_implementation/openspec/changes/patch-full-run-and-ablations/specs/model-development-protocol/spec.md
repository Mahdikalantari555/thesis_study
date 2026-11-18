## ADDED Requirements

### Requirement: Full-run ablation program (E2–E6 + E3 + offsets)

The system SHALL run the winning PoC configuration on all locked
train-split fields with seeds {13, 42, 2026}, and the ablation program with
one pre-registered factor per cell: auxiliary masked-reconstruction weight
{0, 0.3} (dropped unless minimum detectable magnitude improves), causal
dilated TCN challenger (only if the GRU is slow/unstable; ties within one
standard error go to the simpler/faster variant), covariate additions
(DOI baseline → cycle age → sensor → weather aggregates last, each kept
only if it cuts false alarms at fixed recall, both conditioned and
unconditioned reported), inner-buffer and burn-in variants (S=16 tiled
variant optional, off the critical path), LST-off channels checkpoint
(reused by the independent-indicators change), agronomic strata (ratoon
number / variety group from the cycle table, absent from the current
covariate sets) as one covariate cell, and locally re-estimated
L8↔L9 band offsets applied vs not applied. Every run SHALL record params,
MACs, minutes/epoch, peak RAM, peak VRAM and inference seconds per
field-cycle in the manifest and reports, with complete provenance (seeds,
data_source, split hashes, git sha, device).

#### Scenario: Components earn their place

- **WHEN** an ablation cell completes
- **THEN** the factor is kept only if its pre-registered decision rule
  fires (e.g., aux dropped unless MDM improves; covariates kept only on
  false-alarm reduction at fixed recall), and the decision is recorded per
  cell

#### Scenario: Challenger and control decide honestly

- **WHEN** the E3 challengers (TCN, TinyCNNMamba) and the SSL-off
  random-init control run against the primary arm at equal budget
- **THEN** the kept temporal module is the primary arm's unless a
  challenger wins within the pre-registered rule, the SSL contribution is
  quantified as primary-vs-random-init at equal architecture, and the
  CNN-Mamba title implication is recorded for the advisor discussion

#### Scenario: Error analysis closes the chapter

- **WHEN** the final comparison runs complete
- **THEN** top false positives are reviewed with weather/neighbor context
  and missed injections are decomposed by family × severity × phenophase,
  with causes recorded — not just aggregate rates

#### Scenario: Benchmarking is complete

- **WHEN** any training or inference run finishes
- **THEN** its manifest contains params, MACs, wall time, peak RAM, peak
  VRAM (or explicit CPU absence) and per-field-cycle inference time —
  missing fields are defects

### Requirement: Final architecture decision (pre-registered)

The final architecture SHALL be selected by the pre-registered criterion:
beat `b0_calendar` and the best prior arm on MDM80 at 5% field-cycle FAR
for at least 2 of the 3 temporal shapes, with paired-bootstrap CIs over
fields excluding zero on held-out fields and periods (the
generalization-suite matrix), at ≤2× the compute of gru_ae_main. If the
criterion fails, the honest negative — the detection floor itself and the
conditions under which learned models help — SHALL be the recorded finding;
no goalpost movement after the first full run starts.

#### Scenario: The criterion decides

- **WHEN** the full-run ablations complete
- **THEN** the comparison table (all arms × 3 shapes × MDM80 with CIs) is
  committed, the criterion is evaluated verbatim, and the winning
  configuration is frozen with model card + sidecar — or the honest
  negative is recorded with the failing shapes named
