# Finding 16 — Development protocol results: architecture screen, alarm statistic, and the 1×MAD severity finding

> Change: `train-and-finalize-main-architecture` (tasks §1–§7, §9, §10).
> Date: 2026-11-14. Splits: **manifest v2** (`data/processed/splits_locked.json`,
> sha256 `9aa5eb11…`, audit exclusions applied; superseded v1 archived as
> `splits_locked_superseded_fbe9ba97f148.json`).
> Ladder rung of every claim below: **L2** (controlled deviations on train/dev
> cycles) except the final-test paragraph (locked test, still **L2** — see §5).
> Seeds `[13, 42, 2026]` everywhere; device CPU; git sha `81b2a58f`… (final
> numbers re-run after the split correction; see §1).

## 1. Protocol corrections applied before these numbers

Two protocol defects were found and corrected during the session; the numbers
below come from the corrected pipeline:

1. **NaN contamination in the causal transformer** (found via the
   `train_main.py` NaN/Inf guard + a minimal reproduction): fully-masked
   (padded) query rows of `CausalMaskedTransformer` produced NaN, and the next
   attention block spread it to observed rows through `0 × NaN = NaN` in the
   masked weights. This silently zeroed the loss at many training bins
   (41.7 % of bins are unobserved). Fixed (`nan_to_num` on the attention
   output of fully-masked rows, `masked_tf.py`); **all models retrained**.
2. **Finding-14 D2 exclusions were missing from the split manifest**: the
   cycle-audit outcome (38 segmentation-error cycles excluded) was recorded as
   "applied by `build_locked_splits.py`" but v1 of the manifest did not apply
   it. Rebuilt (v2): train 462→447, dev 73→69, test 174→171; the 16 remaining
   excluded cycles were already monitoring-only. **Everything re-run.**

## 2. Masked-reconstruction quality (L1)

Dev masked reconstruction loss (best epoch, early stopping on clean dev):

| model | dev recon loss (3 seeds) |
|---|---|
| masked_transformer | 0.20–0.21 |
| gru_ae | 0.24–0.28 |
| b1_phasez_causal | n/a (fit statistics) |

Masked NRMSE per band on clean dev (mean over bands, raw units ÷ robust range):
gru_ae **0.158**, no-LST 0.164, no-DOY 0.169 — both ablations are worse, and
AUC-PR (below) strongly prefers the full input set. **LST and the sin/cos DOY
channels are kept** (D3's no-LST preference would only apply if performance
were equal; it is not: AUC-PR 0.447 vs 0.329/0.333).

## 3. Architecture screen (L2, primary dev metric)

Primary: detection rate at 1×MAD injected severity at a cycle-level FAR ≤ 5 %
calibrated on clean dev, k ∈ {1,2} chosen on dev, mean ± std over 3 seeds.
Alarm statistic: trailing-3-bin channel-max of per-(bin,channel)-normalized
z² with a causal field-offset correction (§4).

| model | det@1MAD | median delay | AUC-PR@50 % | τ (normalized) | k |
|---|---|---|---|---|---|
| masked_transformer | 0.065 ± 0.019 | 97 d | 0.445 | 4.6–5.3 | 1 |
| **gru_ae (main)** | **0.060 ± 0.033** | **80 d** | **0.446** | 5.6–6.1 | 1 |
| b1_phasez_causal | 0.073 ± 0.038 | 25 d | 0.441 | 4.46 | 1 |

All three overlap within seed spread. The **simplicity rule (D4) selects
gru_ae_main** (cheaper deep baseline, 174 k parameters, and the best
AUC-PR/delay among the deep models). B1 remains competitive at this severity —
an honest, expected result: the climatology reference needs no adaptation to
the injected history, while the deep models absorb persistent shifts (§4).

## 4. The alarm statistic: three measured defects and their fixes

The dev metric was rebuilt twice inside the dev loop (each change logged in
`reports/dev_log.csv`; the D5 mean-z² statistic is kept as a reported
secondary):

- **Change #1 — channel-max instead of the 8-channel mean.** A 1×MAD
  single-band shift moves the mean-over-channels z² by only +0.02–0.10 while
  the null cycle-max sits at 2.5–6: the mean dilutes band-specific anomalies
  by the channel count (paired measurement).
- **Change #2 — trailing window + per-cell normalization + field-offset
  correction.** Three further mechanisms were measured:
  (a) per-bin null scales differ by ~10× (residual variance ≠ across-field
  dispersion) → per-(bin,channel) q95 normalizer from clean dev;
  (b) field-level offsets produce residuals of many MADs at tight-scale bins
  → causal running-median offset correction (BFAST-Monitor-style history
  model); (c) an expanding mean dilutes the onset transition over ~30 bins
  (AUC-PR 0.12 < prevalence) → trailing 3-bin window, because a
  leave-one-bin-out scorer conditions on injected history and absorbs
  persistent shifts — **the detectable signal is the transition**, not the
  level.

## 5. The 1×MAD severity finding (the headline result)

Even after all three fixes, **detection at the agreed severities stays near
zero for every candidate, including B1**:

| severity | detection rate (gru_ae, seed mean) |
|---|---|
| 0.5×MAD | 0.00–0.08 |
| 1×MAD | 0.04–0.10 |
| 1.5×MAD | 0.00 |
| 2×MAD | 0.00–0.09 |
| 4×MAD | 0.08–0.10 |
| 6×MAD | 0.08–0.15 |
| 8×MAD | 0.13–0.45 |

Mechanism (measured, not assumed): the "clean" dev cycles contain **natural
extremes of 10–20 MAD** at observation level (e.g. swir2 = 0.364 vs train
median 0.095 at one bin — a bare-soil signature; LST residuals ≈ 30 K). At a
5 % cycle-level FAR, the budget is consumed by these natural outlier cycles
(τ lands at 4.6–6.1 in normalized units, i.e. ~4–6× the per-cell q95), so an
injection whose step is 1×MAD — the size of ordinary across-field variability
— cannot lift the alarm path. In addition, some of the "false" alarms are
plausibly **real, unlabeled events** (harvest operations, soil exposure): at
L2 we cannot tell false from real without independent evidence (L4).

**Consequences:**

- The D6 target ("main ≥ B1 + 0.05 with non-overlapping 3-seed ranges") is
  **not evaluable at 1×MAD on this archive** and was NOT met on the locked
  test either (§6). Recorded as a finding per the spec's honest-outcome
  requirement; no goalpost moving.
- Task OQ6 (advisor: realistic perturbation magnitudes for Amirkabir
  sugarcane) now has a concrete answer to bring: realistic detectable
  anomalies in this archive start around **6–8×MAD** for single-band steps of
  2–5-bin duration, OR the FAR calibration must move from cycle-level to
  bin-level (or exclude known operation events) — a protocol decision, not a
  code defect.
- Model tuning against the primary metric (task 6.2) is paused until the
  severity/FAR protocol is decided by the advisor; tuning on a metric with no
  dynamic range would optimize noise.

## 6. Locked final test (run once, `--final-test`)

Test split (manifest v2): 171 cycles / 128 fields (starts ≥ 2024-01-01 plus
the contiguous test block), scored causally with the frozen sidecar
thresholds (τ, k, per-cell normalizer, field-offset correction — all frozen
on dev, never re-fit on test):

| | gru_ae_main (frozen seed 2026) | b1_phasez_causal |
|---|---|---|
| clean-test FAR | 0.064 | 0.070 |
| det@1MAD | 0.067 [CI95 0.020–0.125] | 0.052 [CI95 0.000–0.118] |

(bootstrap over fields, 1000 reps). Gap +1.5 pts, CIs overlap → **D6 target
not met; `ladder_rung` stays "L2"** in the sidecar
(`reports/final_test_gru_ae_main.json`). The dev-calibrated 5 % FAR also
transfers imperfectly (test FAR 6.4 %) — consistent with the §5 mechanism
(the test period has its own natural outliers).

## 7. Artifacts

- Frozen: `checkpoints/gru_ae_main.pt` + `gru_ae_main.json` (τ 6.056, k 1,
  FAR achieved 4.3 %, per-cell normalizer, per-seed dev metrics, params
  174 008, FLOPs estimate 12.5 M MACs/cycle, splits sha256, ladder L2).
- Per-run metrics: `reports/dev/<run>/metrics_*.json` (per-seed + mean/std,
  full provenance: data_source, n, date range, seeds, git sha, device, wall
  time, splits sha256, ladder_rung).
- Experiment log: `reports/dev_log.csv` (schema-validated; every eval run
  appends one row).
- Final test: `reports/final_test_gru_ae_main.json`.
- Pipeline logs: `reports/pipeline_v2_*.log`, `reports/dev_matrix_20261114_*.log`.

## 8. Limitations (explicit)

- Dev is small (69 cycles): FAR calibration and per-type tables are noisy;
  per-type × phase cells hold ~5–10 injections at 1×MAD.
- Injection severities are MAD-scaled by ACROSS-FIELD variability (design
  D6); the relevant noise for within-field detection is the model residual —
  the two diverge exactly at the transition bins the detector targets. The
  advisor answer should decide whether severities stay MAD-of-population or
  move to residual-scaled.
- The platform payload (contract v5) shows the frozen model's causal scores
  with `stressFlag` ∈ {normal, suspected_stress, no_data} and honest naming;
  all flags are **suspected stress (anomaly), not stress** until L4.
