# Change: literature-grounded-severity-protocol

## Why

Finding 16 (development protocol results) measured that at 1×across-field-MAD injection severity,
**nothing** — including the B1 climatology baseline — detects at a 5 % cycle-level FAR, and detection
starts only at ~6–8×MAD. Converting the verified literature magnitudes into our archive's units shows
realistic stress is only **0.5–2.5× across-field MAD**: the current D6 protocol tests synthetic steps
2–4× larger than real stress, so the headline metric has no dynamic range and task-6.2 tuning would
optimize noise.

Two external research answers (Claude + ChatGPT, 2026-11-14) were independently verified against
primary sources (`D:\RS\Thesis\research\ssl-stress-advantage\VERIFICATION.md`). Verified anchors:
Clay et al. 2012 (wheat NDVI −0.05/−0.08 at two stages), Kiranmai et al. 2025 (maize skip-irrigation:
single skip statistically null, double skip −30–40 %, withholding ≈ −50 %), Casterad et al. 2018
(salinity–NDVI linear-response-plateau, ECe threshold 5.2–10.6 dS/m, persistent ≥8 years). The owner
decision (2026-11-14) binds the synthetic-anomaly family to **vegetation-index drops (NDVI/SAVI)**.

## What Changes

- **Severity re-anchoring:** injections scale by **absolute NDVI/SAVI drops** (S1 −0.02 … S6 −0.40,
  the merged verified table in `design.md`), reported additionally as % of the field's own
  grand-growth median and as multiples of across-field MAD. The interim MAD-scaled D6 set (incl.
  `lst_rise` as a *flagged* injection type) is retired from the headline metric per the owner
  decision; a **persistent (4–6 bin) variant** of the same magnitudes covers the salinity-like
  chronic signature (magnitude unsourced — labeled experimental).
- **Headline metric = MDM80:** minimum detectable magnitude achieving ≥80 % detection at the 5 %
  cycle-level FAR, per model and per B1, from an MDM severity sweep on **independent clean cycles**
  (not the calibration cycles). Dynamic range restored; tuning is no longer noise-fitting.
- **Event-level FAR as a reported secondary:** alarms are declustered into events (EVT/POT-style
  minimum separation), FAR counted per event per unit time (sktime `FalseAlarmRate` precedent) —
  this honestly accounts for natural 10–20-MAD outlier cycles consuming the per-cycle budget.
  Threshold *calibration* stays at the 5 % cycle-level rule until the advisor decides otherwise.
- **Provenance guard:** the severity table ships with source + verification status per level;
  unverified claims (e.g. French 2020 −5 %/10-day numbers; Claude's uncited "2026 maize salinity
  study") are excluded from design use.

## Impact

- Affected specs: `model-development-protocol` (MODIFIED: fixed development metric; target and
  honest outcome; ADDED: severity-table provenance).
- Affected code: `src/ssl_anomaly/monitor/perturbations.py` (index-drop family + persistent variant),
  `src/ssl_anomaly/monitor/scoring.py` (event declustering + event-FAR), `scripts/eval_dev.py`
  (severity sweep + MDM + event-FAR), `scripts/freeze_main_model.py` (sidecar severity provenance),
  tests for all of the above; docs finding 18.
- NOT affected: frozen `checkpoints/gru_ae_main.pt` (no retraining), platform payload/contract,
  locked splits manifest.
