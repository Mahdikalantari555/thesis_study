## Design — patch-scoring-ensemble

### Scoring stack (document §8, adapted to the cycle-bin grid)

All component scores are computed per patch arm (`patch_cnn_gru`,
`patch_pixelwise`) and, where the interface allows, re-used for field-level
arms for comparison. Component z-scores share the frozen σ tables
(channel × 2-bin phenophase group × sensor; 1.4826 × MAD of dev residuals)
from the PoC — no re-fitting inside this change.

- `s_pred` (exists from the PoC) = mean z² over k∈{1,2,3} and channels.
- `s_rec` = masked-mode reconstruction residual z², 8 repeated random masks
  (mask ~1–3 whole bins or one channel group per repeat, seed-fixed),
  averaged.
- `s_lat` = Mahalanobis² of h(p,t) to the phenophase-binned Gaussian on
  train latents (low-rank factorization, rank ≤ 16, shrinkage on the
  diagonal); fitted on train split ONLY, frozen + sha.
- `s_hyb` = mean of the within-phenophase percentile ranks of s_pred and
  s_rec over the dev population (rank statistics fitted on dev only).
- Persistence: per-bin field score z_f(t) → CUSUM (κ, h at 1%/5% FAR) and
  the EWMA alternative; per-arm cycle score = max_t C_t.

### Decisions

1. **Selection discipline.** Which components enter the final hybrid, and
   which aggregation rule wins, is decided ONLY on the synthetic validation
   set + dev cycle-FAR; the decision matrix is pre-registered in
   `scripts/` before the first evaluation run (trial_gates pattern).
2. **C1 as measurement, not opinion.** Both severity units are computed on
   the same 490-field archive and reported as a conversion table
   (across-field MAD ↔ phenophase-binned residual MAD per channel); the
   recorded decision states which unit the severity ladder uses and why.
3. **C2 as a comparable rule, not a replacement.** The SHAZAM per-DOY rule
   is calibrated at the same 5% FAR budget and reported next to q95;
   if it dominates on dev (lower MDM at equal FAR), the swap is recorded
   and re-frozen — never both rules active at once.
4. **Common-mode subtraction default off.** The date-wise cross-field
   median subtraction cancels weather/sensor common-mode but reads all
   fields' contemporaneous scores; default OFF for the locked evaluation,
   ON only as a reported sensitivity variant.

### Risks

- Rank statistics fitted on dev can drift when applied to other periods —
  reported as the score-drift metric (ties into the generalization suite).
- CUSUM costs detection delay (document §8 table) — delay is reported
  alongside every persistence result, never hidden.
