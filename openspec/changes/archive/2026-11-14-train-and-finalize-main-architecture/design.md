# Design: Train and Finalize the Main Architecture

Decisions agreed with the user on 2026-11-10. Anything marked **(proposed)** is the agent's default and still open to the user.

## D1. Task framing: causal field monitoring

- **Unit of output**: one status per (field, Landsat acquisition date that has data for that field): `normal`, `suspected_stress`, or `no_data`. A day without an acquisition gets no new status. The platform may show the last status together with "days since last observation".
- **Causality**: the status at date *t* uses only observations at or before *t* within the current growth cycle (plus the frozen model and train statistics). Later observations must never change the status already issued for *t*. Revised scores may be stored separately as `retrospective`, but they are never used for metrics.
- **Naming**: until L4 validation, the positive class is called *suspected stress (anomaly)* in code, docs and UI. Never call it "stress". The type of stress is not predicted.
- **Validation-ladder rungs covered by this change**:
  - L1: the model learns normal temporal growth (masked NRMSE).
  - L2: it detects controlled deviations (injected perturbations).
  - L3 is only *measured once*, on the locked test, when the model is frozen.

## D2. Data splits (frozen, locked test)

- **Source**: real490 archive (`stats.zarr`, `cycles_490.parquet`, `growth_cycles_490.npz`) loaded through `load_real490_archive()` only.
- **Locked test**:
  - Every uncensored cycle that starts on or after 2024-01-01.
  - Every cycle of fields in one **spatially contiguous** block, chosen by field-centroid coordinates rather than the hash blocks in `build_splits_490.py`. Hash blocks scatter neighbouring fields across splits, which leaks shared weather and management (spatial autocorrelation).
  - Censored, in-progress 2025–26 cycles go to a separate `monitoring_only` set. The platform may display them, but they never enter metrics.
- **Dev**:
  - Uncensored cycles starting in 2023 that are not in the test block.
  - All cycles of a second contiguous block.
- **Train**: the rest, restricted to cycles that end before 2024-01-01, so no train cycle overlaps the test period in time. The number of cycles dropped by this rule is logged.
- **Contiguous blocks (proposed)**: about 10 % of fields each, chosen as the k-means cluster of field centroids (k = 10) whose size is closest to 10 %. The seed and centroid file are recorded.
- **Manifest**: `data/processed/splits_locked.json` holds the cycle ids per split, SHA-256 of the cycle file and of the manifest, creation date, and git SHA. It is created once and never regenerated in this change. Training and evaluation scripts refuse to run if the hash differs.
- **Test access**: no script may read test cycles except `scripts/freeze_main_model.py --final-test`, which is run once by the user after the plateau.

## D3. Inputs

- **Tensor**: per cycle, 36 days-since-harvest bins × channels (NDVI + blue, green, red, nir, swir1, swir2, lst), plus an **observation mask** channel per band (1 = observed, 0 = missing). The model sees *(value, mask)*. Missing values are set to 0 *only together with* mask = 0, and loss is computed only on observed entries.
- **Normalization**: robust z-score per band and phase bin, using the median and MAD × 1.4826 from train cycles only, stored in the checkpoint sidecar.
- **Ablation**: the main model is also trained without the LST channel. If the two perform similarly, the no-LST variant is preferred for later L4 validation against CWSI (which is built from LST). This is noted in the dev log.

## D4. Models

| Id | Role | Notes |
|---|---|---|
| `masked_transformer_main` | Main SSL model | Causal attention mask; pretext = masked reconstruction of observed bins only (no injected-anomaly pretext, so dev perturbations stay unseen). |
| `gru_ae_main` | Cheap deep baseline (B4) | Unidirectional GRU; next-bin / masked reconstruction. |
| `b1_phasez_causal` | Reference | Phase-aware robust z-score using train statistics; causal by construction. |
| `b0_calendar` | Floor | Day-of-year climatology. |

- **Parameter caps**: at most 500 k parameters per model. Masked TF and GRU-AE are compared at similar parameter counts (within ±20 %).
- **Seeds**: 3 seeds per configuration (fixed list `[13, 42, 2026]`).
- **Simplicity rule**: if Masked TF and GRU-AE differ by less than the seed spread, GRU-AE is chosen as main (simpler).

## D5. Scoring and the binary flag

- **Per-bin score**: the causal prediction error of the current bin from earlier bins, as observed-mask-weighted MSE in z-space. The squash `1 − exp(−MSE)` is kept for display only; thresholds are set on raw scores.
- **Per-acquisition score**: the score of the bin containing that acquisition, computed at that acquisition time.
- **Alarm rule (proposed)**: `suspected_stress` when the score exceeds threshold τ at k consecutive acquisitions, with k ∈ {1, 2} chosen on dev.
- **Threshold**: τ is calibrated on **clean dev cycles** so that at most 5 % of them raise any alarm over their whole length (cycle-level false-alarm rate). The bin-level false-alarm rate is also reported. τ, k, and the calibration set hash are stored in the sidecar.

## D6. Development metric (agreed)

- **Perturbations**: injected into dev cycles. Severity is given in multiples of the train MAD of the affected band at that phase bin (0.5, 1, 1.5, 2 × MAD). Start phase is early / mid / late, and duration is 1–5 bins.
- **Interim perturbation set**, used until the literature review and advisor answer:
  1. NDVI drop
  2. LST rise
  3. Phenology delay
  4. Growth stall (plateau)
  5. Early senescence
  6. Transient drop with recovery
- **Primary**: detection rate at a cycle-level false-alarm rate of 5 %, at 1×MAD, averaged over perturbation types and phases, mean ± std over 3 seeds. It is reported with the **median detection delay** (days from injected onset to first alarm).
- **Secondary**:
  - AUC-PR at partial cycles (scores using only the first 25 / 50 / 75 % of bins).
  - Masked NRMSE per band on clean dev cycles (L1).
  - Severity curve from 0.5 to 2×MAD.
  - Per-type and per-phase breakdown.
- **Target**: main model detection rate ≥ B1 PhaseZ causal + 0.05, with the 3-seed ranges not overlapping. If the target is not reached at plateau, that is reported as a finding; no goalpost moving.
- **Plateau**: one change per experiment (depth/width, mask ratio, lr, epochs, augmentation, band weights, k). The model is frozen after three consecutive changes that each improve the primary metric by less than max(0.01, seed std).
- **Forbidden during development**: any use of CWSI, ETa, `y_stress`, yield, or test cycles for model selection, threshold choice, or early stopping. Early stopping uses dev **masked reconstruction loss**, not the perturbation metric, to keep the metric for selection only.

## D7. Platform output (contract v5)

- **Checkpoint**: `checkpoints/<id>.pt` plus `<id>.json` sidecar with:
  - architecture config
  - normalization stats
  - τ and k
  - split manifest hash and git SHA
  - seeds and train date
  - dev metrics
  - parameter count
  - `ladder_rung: "L2"` (becomes L3 only after the final test)
- **Exporter**:
  - For each observation it writes `scores.masked_transformer`, `scores.gru_ae`, `scoreProvenance` (`model` or `absent`), and `stressFlag` (`normal` / `suspected_stress` / `no_data`).
  - It also writes `stressFlagModel` (which checkpoint decided the flag) and `formulaId` `<id>:causal_bin_mse`.
- **Removal of circular fallbacks**: the CWSI proxy fallback is removed for SSL slots. A missing checkpoint gives `absent` (the CWSI affine rule is circular for anomaly validation).
- **Contract mirroring**: `platform_channels.py` and `channels.ts` stay mirrors, enforced by the contract test.
- **Contract change**: version 4 → 5, with legacy payloads handled as today.

## D8. Execution and compute rules

- **Device**: auto-detected (`cpu` or `cuda`), so the same command runs on the laptop, the lab GPU, or Colab.
- **Laptop budget**: at most 15 min per seed. Each run logs wall time.
- **Progress display**: a progress bar per epoch (tqdm) showing epoch, train loss, dev reconstruction loss, and ETA. The run writes `reports/dev/<run_id>/progress.jsonl` and supports `--resume` from the last checkpoint.
- **Smoke test**: `--smoke` uses 1 epoch, 16 cycles, and runs in under 2 min. The agent runs **only** smoke tests and unit tests. Any run beyond that is delivered as an exact terminal command for the user, and only after smoke and unit tests pass (AGENTS.md §6).
- **Experiment log**: every run appends one row to `reports/dev_log.csv` with run id, date, single change vs parent, config hash, seeds, primary metric mean/std, delay, secondaries, params, wall time, and device.

## D9. Incremental training (placeholder)

- **Interface stub**: `ssl_anomaly.train.incremental.fine_tune(checkpoint, new_cycles, *, trim_top_frac)` raises `NotImplementedError`.
- **Docstring and design note**: each completed season, fine-tune on newly finished cycles after trimming the highest-scoring ones, so anomalies are not learned as normal.
- **Vision link**: farmer reports later feed active learning.
- **Status**: no tests beyond the stub's existence.

## D10. Risks

- **Small n**: about 800 cycles before the splits, so the test may hold only around 100. Report confidence intervals (bootstrap over fields) on the final test.
- **Unrealistic perturbations**: synthetic perturbations may not resemble real stress. This is mitigated by the literature review and the advisor question; it is an explicit L2 limitation.
- **Temporal train cutoff**: the cutoff reduces training data. The count is logged, and if it removes more than 15 % of cycles it is raised with the user.

## D11. Data-readiness decision record (from data-and-phenology-readiness D1–D5)

Decisions below are adopted from `docs/findings/13_literature_phenology_and_perturbations.md` (R1–R8) and `docs/findings/17_stage_conditioned_thresholds.md` (stage-conditioned thresholds; path updated 2026-11-14 after the duplicate finding-14 renumber — the file was `14_stage_conditioned_thresholds.md` when this change was written). They gate the start of training sections 2–5 of this change.

**R1 — Segmentation:** Keep current harvest-driven cycle segmentation (`src/ssl_anomaly/phenology/cycles.py` + `smoothing.py`): Whittaker λ by CV on full series, `find_peaks(−NDVI)` prominence ≥ 0.15, prior-plateau ≥ 0.7 max, post-trough rise ≥ 0.15 in 180 days, length 180–540 days, replant detected by NDVI < 0.3 for 120 days. Matches Kavats 2020 / Joshi 2024 logic.

**R2 — Causality / harvest confirmation:** New cycle opens only after harvest confirmation (proposed: 2 valid later observations or 45 days, whichever first — assumption, no direct source). In-between observations = `no_data` / `harvest_pending`.

**R3 — Time axis:** Keep DSH 36×15-day bins as main axis; add sin/cos DOY as auxiliary input (Sadbhave 2025 +8 F1; Wijesingha & Beila 2026). Normalized cycle progress (0–1) rejected as non-causal. GDD/thermal time deferred until ERA5 is wired.

**R4 — Model input:** Masked TF round 1 uses 36 bins. Irregular-token variant deferred as a single later change.

**R5 — Perturbation catalogue:** P1–P8 with magnitudes in MAD-of-phase (all assumptions, swept 0.5–2×MAD): P1 NDVI drop (water deficit, mid, Jul–Sep, gradual, 30–60 d, partial recovery) KEEP; P2 LST/CWSI rise (fast, 1–3 obs, full recovery) KEEP but require no-LST ablation; P3 P1+P2 together ADD; P4 phenology delay KEEP; P5 early growth plateau KEEP; P6 early senescence CONDITIONAL; P7 one-observation transient dip CONDITIONAL (require ≥2 obs); P8 chronic whole-season salinity drop EXCLUDED from transient metric.

**R6 — Training mask:** Sampled from real valid_frac/cloud pattern (GloSSR).

**R7 — BFAST Monitor:** B3 = BFAST Monitor on DSH axis optional.

**R8 — Cycle recount:** RESOLVED 2026-11-14. `data_quality_report.py --all` (recount fixed to compute NDVI from red+nir) = **800 non-censored cycles** (0 errors, 490 fields); matches the archive's 799 within 1 trailing-censoring cycle. findings-02's 1704 is stale. Audit→archive match: 93/94 sampled cycles by (field, cycle_id), lengths within 15 d (start_harvest differs only by epoch convention). The binned NPZ covers 370 fields with ≥1 non-censored cycle.

**R9 — Cycle audit outcome (2026-11-14, findings 14):** Agent pre-labeled all 94 audited plots (user delegated confirmation after reviewing the procedure; agent-only judgment is a recorded limitation). Result: 67 correct / 19 merged / 6 split / 2 harvest_shift. The dominant defect is systematic: 18/19 long (>480 d) cycles are two annual seasons joined by a missed winter harvest (interior trough 0.10–0.25 + full regrow) — the same failure family as Kavats 2020 (missed harvest) and Rodigheri 2023 (second crop missed by all packages). Rates: reviewed set 28.7 % [20.6, 38.6]; population estimate 7.9 % [4.7, 16.3]. **D2 rule outcome: <10 % at the point estimate → proceed to training with exclusions:** `reports/cycle_audit/exclusion_cycles.csv` (38 cycles = 35 sanity-flagged + 3 unflagged agent-labeled errors) must be excluded from dev/test by `build_locked_splits.py` (task 1.1), which joins on (field, cycle_id) and logs the actual dropped count. The CI upper bound (16.3 %) does not exclude the tuning band, so a segmentation-tuning change proposal (winter-trough prominence; see findings 15 §7) stays recommended. Method write-up: `docs/findings/15_cycle_segmentation_method.md`.

**Findings 14 — Stage-conditioned anomaly detection:** Implemented in `scripts/stage_conditioned_anomaly.py`. Stage-conditioned thresholds with npphen-style confidence envelope prevent flagging natural phenological decline (senescence/harvest/dormancy) as stress. Results (--all, seed=20261111, 370 fields, 799 cycles): 18,505 valid obs, 1,774 flagged (9.59%). S3 maturity/senescence lower envelope = −0.027 → natural decline never flagged. S2 vegetative lower envelope = 0.525 → unexpected drops during growth are flagged.

**Gate:** Training sections 2–5 of this change stay open until the user approves this decision record (task 4.2).
