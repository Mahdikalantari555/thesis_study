# Tasks — forecast-unit-probe

## 1. Forecasters (TDD-first)

- [x] 1.1 `src/ssl_anomaly/monitor/forecast_units.py`: causal forecasters
      `persist`, `med3`, `trend4` in the frozen z-space, with the gap rule
      (history broken by an observed-bin distance > 2) and NaN-on-insufficient-
      history semantics; a batch entry point returning (z, pred_z) compatible
      with `diagnostics.decompose_injection` and the scoring pipeline.
      Unit tests: causality invariant (perturbing bins ≥ o never changes the
      prediction at o); mask/gap handling (NaN after a >2-bin gap; NaN with
      insufficient history); `trend4` exactness on synthetic linear series;
      `med3` robustness to a single outlier in history.
- [x] 1.2 `scripts/probe_forecast_units.py`: per-arm calibration on the clean
      dev CALIBRATION subset (per-(bin,channel) q95; τ, k via
      `choose_threshold` at the 5% cycle-level FAR target), then the identical
      severity sweep on the independent evaluation subset (same partition
      salt/hash, identical injections rounds=2) — per-cell detection + Wilson
      CI + median delay + event-FAR + MDM80 (censoring allowed) + the
      finding-20 waterfall (stage-1 onset residual in forecast-σ units,
      post-onset absorption). Full provenance (git sha, splits hash, subset
      hash, severity-table hash, wall time) + progress.jsonl + `--smoke`.
      Writes only `reports/dev/<run_id>/probe_<arm>_seed2026.json` +
      `probe_summary.json`. No threshold/model/platform writes, no test read.

## 2. Run + readout

- [x] 2.1 Run the probe (agent-run; CPU, minutes): all three untrained arms +
      the B1 reference numbers recomputed in the same harness; verify
      internal consistency (each arm's detection reproduces its own
      calibration's k/τ semantics; smoke green before the full run).
- [x] 2.2 Evaluate the PRE-REGISTERED decision rule (success = non-censored
      MDM80 ≤ S5 on persistent/ndvi with event-FAR within budget; negative =
      all censored) — record verbatim, no goalpost movement, no tuning.

## 3. Finding + gated follow-up link

- [x] 3.1 Finding 21 (`docs/findings/21_forecast_unit_probe.md`, Persian,
      persian-writing skill): forecast-σ onset-residual scale table, MDM80
      per arm, decision-rule verdict, absorption behavior of carry-forward
      forecasters, explicit scope limit (single-index drop family);
      + 00_index row.
- [x] 3.2 `todo.md` §D2: link the outcome as the measured pre-training
      evidence for `predictive-ssl-controlled-trial` (success → the trained
      arm's target floor = the probe's best MDM80; negative → weight shifts
      to path B).

## 4. Gates

- [x] 4.1 Unit tests green (new + existing severity/diagnostic suites);
      `--smoke` green before any full run.
- [x] 4.2 `openspec validate forecast-unit-probe`; no platform impact
      (probe writes only `reports/`).
