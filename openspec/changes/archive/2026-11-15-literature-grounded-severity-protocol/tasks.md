# Tasks — literature-grounded-severity-protocol

## 1. Severity table as verified config

- [x] 1.1 `src/ssl_anomaly/monitor/severity_table.py`: the S1–S6 ladder as a frozen dataclass/dict
      with `source` (citation+DOI), `verification` ∈ {verified_full_text, verified_abstract,
      design_choice, rejected}, `confidence`, `delta_ndvi`, `duration_bins`, `persistent` flag; hash
      function for the sidecar. Unit test: hash stability + `rejected` levels refuse to load.
- [x] 1.2 Extend `perturbations.py` with the index-drop family: absolute-Δ injection on ndvi/savi
      (separate axes), persistent variant (4–6 bins), per-field % of own grand-growth median computed
      at injection time, physical-range floor, never erasing observations. Unit tests: onset = ground
      truth; masks unchanged; ranges respected; SAVI axis independent. DONE: sum-preserving red/nir solve in `_solve_savi_drop`; 9 new tests in `test_monitor_perturbations.py` green.
- [x] 1.3 Retire MAD-scaled D6 magnitudes from the headline path (keep the code path for the
      finding-16 continuity report, flagged `legacy`); `lst_rise` stays runnable for diagnostics but
      is excluded from the primary metric per the owner decision (2026-11-14). DONE: `--protocol legacy` keeps the D6 path; severity is the default headline.

## 2. MDM sweep + event-level FAR

- [x] 2.1 `scoring.py`: event declustering (gap ≤ 2 bins → one event) + `event_false_alarm_rate`
      (events hitting no injection window / time span; extra alarms inside a hit window not
      double-counted). Unit tests with synthetic alarm paths (adjacent bins, gap-2, gap-3). DONE: `test_event_far.py` 9 tests green (sktime hit-window semantics pinned).
- [x] 2.2 `eval_dev.py`: severity sweep S1–S6 × {acute, persistent} × {ndvi, savi} → per-level
      detection rates (Wilson CI) + `mdm80` per family per index; independent-eval-cycle subset
      (disjoint from calibration subset when dev size permits) with recorded hash; B1 identical sweep. DONE: deterministic hash partition 35/34 (eval hash `6186edf8a06f82d3`, identical across arms).
- [x] 2.3 `metrics.json` schema extension (mdm80, event_far, severity_table_hash) +
      `test_dev_log_schema.py` update; dev_log rows carry the sweep hash. DONE: 5 new columns (protocol/scorer/severity_table_sha256/eval_subset_sha256/mdm80); existing 26 rows migrated with empty values.
- [x] 2.4 Rerun the dev matrix for the three frozen architectures + B1 (CPU, ≤15 min/seed budget
      unchanged; agent runs smoke only — full run handed to the user per AGENTS §7). DONE under session mandate 2026-11-14 (agent-run CPU eval sweeps): gru_ae 41.4 s, b1 22.0 s, masked_transformer 51.2 s wall — all MDM80 censored >S6 (finding 18).

## 3. Freeze/final-test integration (gated)

- [x] 3.1 `freeze_main_model.py`: sidecar gains `severity_table_sha256` + `mdm80` fields; the 5 %
      cycle-level calibration rule and τ/k semantics unchanged. DONE: `--attach-severity` adds severity_table_sha256 + mdm80; platform threshold block (τ 6.0556, k 1, per-cell q95) verified byte-identical.
- [x] 3.2 `--final-test`: one locked test run of the sweep on the test split (same isolation rules);
      bootstrap CIs over fields for MDM80 and per-level detection; report event-level FAR on test. DONE (run ONCE): 171 cycles / 128 fields; target (a) margin −0.006, (b) both-censored ties → NOT met; ladder stays L2.
- [x] 3.3 Finding 18 (`docs/findings/18_severity_reanchor_results.md`) with verified-source table,
      MDM curves, honest statement of which levels remain undetectable; finding 16 cross-ref. DONE: `docs/findings/18_severity_reanchor_results.md` (Persian, persian-writing skill) + 00_index row 18.

## 4. Gates

- [x] 4.1 Unit tests for perturbations/scoring/severity table (TDD-first, per repo convention).
- [x] 4.2 Platform untouched → contract/bilingual gates not required; if any payload field changes,
      run the §4 gates before done. DONE: platform untouched; sidecar threshold block byte-identical (verified programmatically).
