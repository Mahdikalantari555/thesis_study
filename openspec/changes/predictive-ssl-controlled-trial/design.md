# Design — predictive-ssl-controlled-trial

## Context

Finding 20's decision matrix attributes the detection failure to stage 1 —
the objective/unit — and measures partial absorption (α ≈ 0.38–0.50) of
persistent drops in the reconstruction prediction. The owner directs a single
controlled trial instead of architecture shopping. The trial keeps EVERYTHING
fixed except the objective; the companion `forecast-unit-probe` change first
estimates, with zero training, how much of the gap the predictive unit alone
can close (its best untrained MDM80 becomes this trial's measured target
floor).

## Arm definition (the only design freedom, fixed a priori)

`gru_pred`: same trunk/inputs/normalization/budget as `gru_ae_main`
(identical d_model/n_layers/dropout/params class, ≤500k parameters), trained
with a causal one-step-ahead objective:

- target: z[o] (all 8 channels), input: z[<o] only (causal GRU state — no
  masking/LOO needed at inference; the prediction at o never sees ≥ o);
- loss: masked MSE (or Huber if MSE is unstable — chosen BEFORE training and
  recorded; no post-hoc switching) over observed (bin, channel) pairs;
- DOY conditioning identical to gru_ae_main;
- seeds {13, 42, 2026}; train split only; `--resume`, progress.jsonl,
  wall-time summary per AGENTS §7; training commands handed to the user.
- Serving/statistic: `pred(o) = f(z[<o])` feeds the UNCHANGED production
  pipeline (causal offset correction → per-cell q95 from clean calibration
  residuals → trailing-3 channel-max → τ at 5% cycle-FAR) — so the only
  difference vs gru_ae_main is the trained prediction function, mirroring the
  probe's logic with a learned forecaster.
- Sidecar: same schema as gru_ae_main (τ, k, per-bin q95, frozen seed,
  hashes) via `freeze_main_model.py`; the one locked `--final-test` run
  remains the only reader of test cycles.

## Part A — natural data (before any injection)

On the dev evaluation subset, clean cycles only, at each arm's calibrated τ:

- cycle-level FAR and event-level FAR (POT gap ≤ 2, production semantics);
- per-field score distribution (median/IQR of clean path maxima per field —
  is the score concentrated in a few fields?);
- temporal stability (per-field score consistency across the cycle's bins
  and across the two rounds' clean re-scores).

Gate: the new arm must NOT exceed the 5% cycle-FAR budget and must not show
alarm concentration in a handful of fields (a sensitivity-without-specificity
failure).

## Part B — severity protocol UNCHANGED

The finding-18 protocol verbatim: S1–S6 × {acute, persistent} × {ndvi, savi},
identical injections (rounds=2, eval subset hash `6186edf8a06f82d3`), MDM80
(≥0.80 detection at 5% cycle-FAR, ">S6" censoring), event-FAR, Wilson CIs,
AUPRC per family (with prevalence reported), median detection delay in days.
B1 and gru_ae_main numbers recomputed in the same run for the identical
injection set (no cross-report borrowing).

## Part C — absorption experiment (finding-20 hypothesis, direct test)

For persistent-family injections, the predictive model's error at three
checkpoints (owner's design):

1. before onset (baseline clean forecast error at the same bins),
2. the first step after onset (error spike size, in forecast-σ units),
3. several steps after onset (does the error persist or decay?).

Reported alongside the finding-20 absorption ratio A (convex α form) computed
by `diagnostics.decompose_injection` unchanged — so GRU-Pred's absorption is
directly comparable to GRU-AE's measured α ≈ 0.38–0.50. Expected if the
mechanism holds: A(gru_pred) ≈ 0 (sustained shift unpredictable from
history) vs A(gru_ae) ≈ 0.45. An honest caveat is pre-registered: a fast
adaptive predictive model COULD also absorb (recursive state feeding on its
own predictions); that is exactly what part C measures — a NEGATIVE result
here is recorded as such, not tuned away.

## Part D — independent-indicator agreement (proxy evidence, never proof)

On natural dev cycles (no injection; no test data): compare each arm's
flagged (field, bin) events against independent remote-sensing stress
indicators — CWSI_ET / CWSI_LST, ETa/ETrF deficits, TVDI (only if computable
from EXISTING per-scene LST/NDVI field statistics), NDVI/SAVI temporal
behavior. Data-availability gate FIRST: any indicator not already available
under `Data/Processed` is recorded `absent` — never synthesized, never
proxied silently (prime directive 2).

Honest dependence structure stated in the finding: the model input includes
LST and NDVI, and CWSI/ETa/TVDI are LST- and/or NDVI-derived — agreement is
CORROBORATING evidence for output validity (proxy agreement toward L4), not
independent ground truth and not proof of stress; the noun stays "suspected
stress" / "synthetic anomaly"; no L4 claim is made from correlation alone.

## Conditions held fixed (owner's list, binding)

- Splits Train/Validation(=dev calibration)/Evaluation unchanged
  (`splits_locked` sha `9aa5eb11…`); test cycles read ONLY by the locked
  final-test path.
- Thresholds calibrated only on the dev calibration subset at the 5%
  cycle-level FAR target.
- Identical inputs for all three arms (8 channels + DOY); weather/feature
  ablations are a SEPARATE future experiment, not this trial.
- Every arm scored on the same farms, dates and injected events.

## Pre-registered decision gates (owner's table — evaluated verbatim)

| gate | criterion | verdict rule |
|---|---|---|
| FAR | clean cycle-/event-FAR within the 5% budget | must pass, else the arm is invalid regardless of detection |
| Synthetic detection | better than gru_ae_main at realistic severities | primary: non-censored MDM80(persistent/ndvi) < gru_ae_main's (or >S6 → any non-censored value wins); secondary: S4–S6 persistent detection with Wilson CIs, then savi/acute |
| Persistent anomaly | predictive error persists through sustained drops | part C: A(gru_pred) < A(gru_ae) and non-decaying checkpoint errors |
| Independent validation | consistency with spectral/ET proxies | part D agreement above chance with CIs (corroborating only) |
| Generalization | not confined to few fields / one period | detections spread across fields and cycles; stable across seeds {13,42,2026} |

DECISION: all gates pass → predictive objective becomes the main development
path. Synthetic-detection gate fails → path B (anomaly definition:
multivariate/relational + phenology-shape families) — NOT more architecture
trials. Mixed outcome → recorded honestly per gate; the owner decides with
the findings in hand. No goalpost moving after the run starts; no spec-target
edits.

## Risks

- The predictive arm could win part B while failing part D (synthetic-only
  advantage) — the gates force the full readout; partial success is reported
  as such.
- One-step prediction on smoothly evolving NDVI may have very small clean
  residuals → outlier bins (masking artifacts, cloud-edge BRDF) could
  dominate the q95 calibration; the per-(bin,channel) q95 + 5% FAR
  calibration handles bin-specific scale, and residual heavy tails would
  surface in part A's FAR gates, not be tuned away.
- Seed spread: 3 seeds are trained; single-seed claims are not made.
- Wall-time: ≤15 min/seed on laptop; if the budget is exceeded the run is
  stopped and reported, not silently continued.
