# Change: forecast-unit-probe

## Why

Finding 20 (signal-path decomposition, 2026-11-14) localized the detection
failure: stages 2–4 of the alarm statistic are exonerated (level-independent
~0.25σ offset subtraction, no trailing dilution for persistent drops, stage-4
AUC-PR 0.91–0.95 > raw residual 0.82–0.86 at S6), and stage 1 dominates in
24/24 cells of BOTH arms — but with a precise interpretation: the onset
residual is born at full size, while its size in the model's σ-unit
(train per-bin robust scale ≈ across-cycle phenological spread, ~0.2 NDVI at
mid-season bins) is only 0.36σ (S1) to 2.68σ (S6/savi-red) against a
≈3.5–4.9σ per-bin requirement from sqrt(τ·q95). The binding constraint is the
UNIT, not the signal and not the score path.

The cheapest test of the remedy family (objective/unit change — path C) needs
NO training: if a prediction measured in "temporal predictability" units
(one-step-ahead within-cycle residual, whose clean scale is the field's own
short-term variability ≈ 0.01–0.02 NDVI rather than the across-cycle spread)
makes the verified severity ladder separable, the path-C retraining is
justified with a measured upside. If it does not, the honest conclusion is
that the smallest ladder levels are below the information floor of these
statistics at 5% cycle-FAR — and retraining would be wasted.

## What Changes

- **Read-only probe, dev split only:** the existing severity-protocol
  machinery with the model's LOO prediction replaced by PRE-REGISTERED,
  untrained causal forecasters (no hyperparameter search, arms fixed a
  priori): `persist` (last observed value), `med3` (median of last ≤3
  observed bins), `trend4` (OLS linear fit on last 4 observed bins,
  one-step extrapolation). B1 (frozen climatology) is already measured and
  serves as the fourth reference arm.
- Identical statistic pipeline: gru_ae_main's frozen train-split
  normalization → residual r = z − pred → causal offset correction →
  per-(bin,channel) q95 from CLEAN calibration residuals → trailing-3
  channel-max → τ at the 5% cycle-level FAR target (choose_threshold on the
  calibration subset, per arm).
- Identical evaluation: the independent evaluation subset
  (hash `6186edf8a06f82d3`), the identical severity injections
  (S1–S6 × {acute,persistent} × {ndvi,savi}, rounds=2), per-cell detection
  rates with Wilson CIs, event-level FAR, MDM80 per family × index, and the
  stage-1 onset residual in forecast-σ units (reusing
  `diagnostics.decompose_injection`).
- **Pre-registered decision rule:** any untrained arm reaching a NON-CENSORED
  MDM80 ≤ S5 on the persistent/ndvi family → the objective/unit remedy
  (path C) is justified with a measured upside; all arms censored ">S6" →
  honest negative: the realistic ladder is below the information floor of
  these statistics at 5% cycle-FAR, redirect to path B (anomaly definition).
- **Finding 21** (`docs/findings/21_forecast_unit_probe.md`, Persian): the
  forecast-unit MDM80 table + decision + explicit scope limit (single-index
  absolute-drop family only).
- **Explicit non-goals:** no retraining, no forecaster tuning, no
  threshold/model/architecture/platform changes, no test access. The probe
  does not replace any serving artifact; it is decision evidence only.

## Impact

- Affected specs: `model-development-protocol` (ADDED requirement:
  forecast-unit probe).
- Affected code: new `src/ssl_anomaly/monitor/forecast_units.py` (causal
  forecasters + tests); new `scripts/probe_forecast_units.py`; finding 21;
  `todo.md` §D2 evidence link.
- NOT affected: frozen checkpoints, sidecars, platform payload, locked
  splits, severity table, calibrated thresholds, trained models.
