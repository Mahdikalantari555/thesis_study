# Findings 14 — Stage-Conditioned Anomaly Detection with Confidence Envelope

## Problem

Standard anomaly detection flags any NDVI drop below baseline as anomalous. This misclassifies natural phenological decline (senescence, pre-harvest drying, dormancy) as stress. The user requirement: **guess phenology stages and do NOT mark natural greenness decrease as anomaly**.

## Method

Stage-conditioned thresholds with a npphen-style confidence envelope:

1. **Input:** `growth_cycles_490.npz` (799 non-censored cycles × 36 bins × 8 channels), `cycles_490.parquet` (cycle boundaries).
2. **Phenology stage assignment:** Each cycle-bin is assigned a stage by normalized progress within the cycle:
   - progress = (bin_index × bin_days) / cycle_length_days
   - S1 establishment/growth: 0.00–0.25
   - S2 vegetative/reproductive: 0.25–0.60
   - S3 maturity/senescence: 0.60–0.85
   - S4 harvest/dormancy: 0.85–1.00
3. **Confidence envelope:** Pool NDVI values per stage across all cycles; compute median and MAD (median absolute deviation). Lower envelope = median − 2×MAD.
4. **Anomaly flag:** A cycle-bin is flagged only if NDVI < lower_envelope[stage]. Natural within-stage decline that stays inside the envelope is NOT flagged.

## Results

Run: `python scripts/stage_conditioned_anomaly.py --all` (seed=20261111, 370 fields, 799 cycles)

| Metric | Value |
|---|---|
| Fields processed | 370 |
| Non-censored cycles | 799 |
| Valid observations | 18,505 |
| Anomalies flagged | 1,774 |
| Flag rate | 9.59% |
| Wall time | 16.16 s |

### Per-stage envelopes (all cycles pooled)

| Stage | n | median | MAD | lower envelope | upper envelope |
|---|---|---|---|---|---|
| S1 establishment/growth | 6,866 | 0.297 | 0.121 | 0.055 | 0.539 |
| S2 vegetative/reproductive | 9,561 | 0.651 | 0.063 | 0.525 | 0.778 |
| S3 maturity/senescence | 2,033 | 0.317 | 0.172 | −0.027 | 0.660 |
| S4 harvest/dormancy | 45 | 0.176 | 0.034 | 0.108 | 0.244 |

### Key insight

**S3 (maturity/senescence) lower envelope = −0.027** — effectively no lower bound since NDVI cannot be negative. This means natural NDVI decline during senescence is **never flagged** as anomalous. Stress is only flagged when NDVI drops below what is normally expected for that phenology stage.

During S2 (vegetative/reproductive), the lower bound is 0.525 — strict, so unexpected NDVI drops during peak growth are flagged.

## Output files

- `reports/stage_conditioned_anomaly/stage_conditioned_anomaly.parquet` — per-bin results (field, cycle_id, bin_index, progress, stage, ndvi, envelope_*, is_anomaly)
- `reports/stage_conditioned_anomaly/stage_conditioned_anomalies_only.parquet` — flagged anomalies only
- `reports/stage_conditioned_anomaly/summary.json` — run summary with envelopes, counts, wall time, git SHA

## Script

`scripts/stage_conditioned_anomaly.py` — supports `--smoke` (20 fields, ~1s) and `--all` (370 fields, ~16s).

## Open questions

1. S4 (harvest/dormancy) has only 45 pooled samples — end-of-cycle bins are often cloudy. More data or wider bins may stabilize this envelope.
2. No ground-truth plant/harvest dates available; phenology stages are guessed from normalized cycle progress (per user requirement).
3. The 9.59% flag rate needs validation against known stress events — no labeled ground truth exists yet.
