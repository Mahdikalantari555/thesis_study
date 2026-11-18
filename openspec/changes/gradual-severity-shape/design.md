## Design — gradual-severity-shape

### Injection mechanics

The ramp perturbs per-bin NDVI/SAVI by δ_t = δ · min(1, t / D) for bins
t = onset..onset+D−1 (D ∈ {3, 4, 6}, recorded per injection), then holds at
δ. Applied identically at field level (existing perturbations machinery)
and per-pixel on patch tensors (the patch applier from the PoC gains the
ramp mode). The SAVI sum-preserving red/nir solver applies per bin with the
bin's current δ_t — so intermediate ramp bins are physically consistent
(red/nir adjusted for the partial drop), not interpolated.

### Detection semantics

A ramp is deliberately the case where one-step prediction adapts: the
residual spikes early, then decays as the state tracks the drift (document
§5). The expected detectors are (a) the prediction score's ONSET transient,
(b) CUSUM/persistence accumulation (`patch-scoring-ensemble`), and
(c) B0's phenophase-matched climatology. The report therefore always shows
gradual results for: each deep arm, b1, and b0_calendar — the B0 column is
mandatory, and "deep arm fails gradual, B0 catches it" is a valid,
reportable outcome that feeds the final hybrid score design (B0 as a score
component, document §8 table).

### Ordering and hashing

- New injection-set hashes (gradual family) recorded in the severity table
  sidecar; acute/persistent hashes untouched.
- If the patch PoC has already started with the 2-shape protocol, gradual
  runs as a strictly additive third sweep on the SAME frozen checkpoints —
  no retraining, no recalibration beyond the frozen σ tables (the σ tables
  are fitted on CLEAN dev residuals and do not depend on injection shapes).

### Secondary shapes mechanics (peak / recovery)

- **Peak magnitude:** scale the cycle's peak plateau (argmax bin ± 1) down
  by δ with the same index-drop solver; **peak timing:** shift the plateau
  k ∈ {2, 3} bins later via a minimal plateau-move (values moved, covariate
  DOY/cycle-age left consistent with the moved series, clipped to admitted
  bins). A minimal self-contained plateau-move is implemented here — the
  full phenology warp machinery stays in path-B scope.
- **Recovery:** reuse the acute applier for the drop (depth δ, duration
  d bins), then (i) failure-to-recover: hold the dropped level r ∈ {3, 6}
  bins where the field's own history shows recovery, or (ii) slow-recovery:
  ramp back at half the natural slope for r bins then normal. The event =
  drop + recovery pathology, scored as one injection (MDM anchored to δ;
  duration recorded per injection).
- Both shapes are SECONDARY: they add report columns; they never enter the
  pre-registered primary gates. Pre-registration happens here before any
  peak/recovery result exists, which is what keeps them honest.

### Risks

- Post-hoc shape addition could look like protocol shopping — mitigated by
  the fact that arms are never tuned on injections (calibration is clean-dev
  FAR only) and by pre-registering the gradual δ grid here, before any
  gradual result exists.
- Ramp duration interacts with cycle-end censoring (onset too late ⇒ ramp
  truncated); onsets are sampled so the full ramp fits inside the cycle,
  recorded per injection.
