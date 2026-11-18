# Design — forecast-unit-probe

## Context

Finding 20 measured the σ-unit mismatch: the alarm statistic needs
≈3.5σ (gru_ae) / ≈4.9σ (B1) per bin at onset bins, while the verified ladder
S1–S6 delivers 0.36–2.68σ in the train-per-bin σ unit. A one-step-ahead
residual lives in a DIFFERENT unit — the field's own short-term
(un)predictability. On clean data, adjacent observed NDVI bins differ by
roughly the acquisition noise + within-field dynamics (expected 0.01–0.02
NDVI, vs 0.20 across-cycle spread), so the same absolute drop is expected to
be ~3–10× larger in forecast-σ units. This probe measures that gain WITHOUT
training anything: same injections, same statistic, same calibration rules —
only the "prediction" function changes.

## Arms (pre-registered; no tuning)

All forecasters are causal (bin o predicted from observed bins < o only),
operate in the frozen z-space of gru_ae_main's train-split normalization, and
return NaN where history is insufficient (the bin does not score — same
"absent" semantics as the production statistic).

| arm | prediction at bin o | clean-residual semantics |
|---|---|---|
| `persist` | last observed value (any gap ≤ 2 bins bridged by the previous observed value; else NaN) | one-bin persistence error |
| `med3` | median of the last ≤3 observed values | short-window local level |
| `trend4` | OLS linear fit on the last 4 observed bins, extrapolated one step | local trend continuation |
| `b1` (reference, existing) | frozen train climatology median per (season-group, bin) | already measured (finding 18/20) |

Gap rule: an observed bin at distance > 2 breaks the history window (the
forecaster returns NaN rather than extrapolating across long gaps).

## Statistic + calibration (identical to production)

For each arm: r = (z − pred)·mask → `causal_offset_correct` →
per-(bin,channel) q95 from the CLEAN residuals of the dev CALIBRATION subset
only → `cumulative_channel_max` → `choose_threshold` (5% cycle-level FAR) on
the calibration subset → severity sweep on the INDEPENDENT evaluation subset
(same partition salt, hash `6186edf8a06f82d3`, identical injections rounds=2,
n=68 per cell).

Note documented honestly: for `persist`, r is a first difference and the
offset correction subtracts the median of the last ≤6 differences — this is
the production semantics applied unchanged (the probe tests the unit INSIDE
the existing statistic, not a new statistic).

## Readout

Per arm per cell (24 cells): detection rate + Wilson CI, median delay,
event-FAR (POT gap ≤2), MDM80 per family × index (censored ">S6" allowed),
and the finding-20 waterfall quantities (stage-1 onset residual in
forecast-σ units; absorption at post-onset bins where defined) — the
absorption of a persistence/trend forecaster is structurally ~0 for
persistent drops within the bridged window (it carries the injected level
forward), which is itself informative and must be reported, not hidden:
a forecaster that CARRIES the drop forward keeps the residual large only
while the drop persists — this is the pre-registered mechanism question.

## Pre-registered decision rule

- PRIMARY: MDM80 on `persistent/ndvi` (the chronic-stress signature family;
  findings 13/16). SECONDARY: persistent/savi, acute/ndvi, acute/savi.
- SUCCESS: ≥1 untrained arm reaches non-censored MDM80 ≤ S5 on
  persistent/ndvi with clean event-FAR within the 5% cycle-FAR budget →
  path C (forecasting/predictive-coding objective) justified; the measured
  MDM80 becomes the target floor for the trained predictive arm
  (`predictive-ssl-controlled-trial`).
- NEGATIVE: all arms censored ">S6" on persistent/ndvi → record the honest
  negative (ladder below the information floor at 5% cycle-FAR for these
  statistics); path C retraining upside is unproven; redirect weight to
  path B (anomaly definition) and/or event-level accumulation analysis.
- No intermediate tuning: if a forecaster's calibration degenerates
  (degenerate q95, τ at a boundary), it is RECORDED as a finding, not fixed
  by tweaking the arm definitions.

## Honest labeling

- Every claim L2; noun "synthetic anomaly"; scope limited to the
  single-index absolute-drop family; no test access; no threshold/model/
  platform change; the probe writes only `reports/`.
- Risks: persistence/trend residuals have heavy tails at phenological
  transitions (rapid growth) — the per-(bin,channel) q95 normalizer handles
  bin-specific scale by construction; the residual risk (heavy tails
  surviving q95) would show up as elevated clean event-FAR and is part of
  the readout, not something to tune away.
- Confounding documented: these untrained forecasters use no learned
  representation; a SUCCESS verdict justifies path C but does not guarantee
  a trained predictive model beats them — that comparison IS the
  `predictive-ssl-controlled-trial` change.
