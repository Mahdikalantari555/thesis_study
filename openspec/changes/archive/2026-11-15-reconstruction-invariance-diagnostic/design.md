# Design — reconstruction-invariance-diagnostic

## Context

Findings 18/19 (L2): MDM80 ">S6" censored for every arm; B1 ≥ main on the
index-drop family; bank arm no gain. The owner directs a mechanism diagnostic
before any model decision. The alarm statistic (finding 16 §4) is a pipeline:

    z (robust-z inputs) → LOO prediction → residual r = z − pred_z
    → causal offset correction r′ = r − median(last ≤6 observed residuals, per channel)
    → per-(bin,channel) normalization r′²/q95 → trailing-3-bin mean, max over channels
    → threshold τ (5 % cycle-level FAR on the calibration subset)

Each stage can destroy the injected signal. The LOO withholding makes the
decomposition well-defined: the onset bin is predicted from clean context
(no absorption possible), post-onset bins are predicted from injected history
(absorption possible and directly measurable).

## Measured quantities (per injection; medians + IQR per cell)

Let o = onset bin, c = injected channel, Δ = severity drop, and let the
counterfactual natural tensor be the pre-injection X.

1. **Residual formation (is the signal born?)**
   - `r_onset = z(o,c) − pred_z(o,c)` (z units; expectation for a clean
     context: |r| ≈ Δ/scale ≈ 6σ at S6).
   - Report median |r_onset| per (arm, level, family, index) and the fraction
     with |r| ≥ 3σ. A small onset residual means the model itself fails to
     represent the injected level as anomalous (loss/pretext issue).
2. **Offset correction (does the history median eat the onset?)**
   - `sub_onset = median{r(o′,c)} over the last ≤6 observed bins` — the
     quantity subtracted at the onset; report median |sub_onset| and
     |r′|/|r|.
3. **Normalization (does the outlier-inflated q95 kill it?)**
   - contribution `r′²/q95(o,c)`; report the median contribution, the cell
     q95 value, and SNR₁ = contribution/τ.
4. **Aggregation (does the trailing mean dilute it?)**
   - path value at o, o+1, o+2 vs τ; report max path over the injection
     window and SNR₂ = path/τ; detection = SNR₂ > 1 (cross-checks the sweep).
5. **Absorption (post-onset, persistent family)**
   - For injected bins b in (o, o_end): the absorption ratio, a convex weight
     on [0, 1]:
       A = MAE(pred, natural) / (MAE(pred, natural) + MAE(pred, injected))
     A ≈ 1 → prediction fully tracks the injected level (absorbed);
     A ≈ 0 → prediction stays at the natural level; 0.5 → halfway. The
     counterfactual is exact by construction (the pre-injection tensor).
6. **Ranking power before vs after normalization**
   - AUC-PR of onset residuals |r| (stage 1, raw) vs clean baselines, and of
     the final paths — the gap localizes loss introduced by stages 2–4.

## Arms

- `gru_ae_main` (seed 2026 frozen) and `b1_phasez_causal` on the same
  deterministic injections (existing severity table, same eval subset,
  hash `6186edf8a06f82d3`); `masked_transformer` behind an opt-in flag.
- B1's "prediction" is its climatology median (the same LOO interface), so
  the waterfall is directly comparable.

## Decision matrix (recorded in finding 20; remedies are FUTURE changes)

| Dominant loss stage | Verdict | Remedy family (next change, gated) |
|---|---|---|
| Stage 1: onset residual small | model does not represent the step | loss/pretext change (forecasting / predictive-coding — path C) |
| Stage 2: onset subtraction large | history median eats the transient | scoring fix (exclude/correct onset handling) |
| Stage 3: contribution ≪ τ | outlier-inflated per-cell q95 | scoring fix (residual-scaled severity units per finding 16 §8; robust/per-field normalizer) |
| Stage 4: path < τ at onset while contribution > τ | trailing dilution | scoring fix (onset-weighted window) |
| Stage 5: absorption ≈ 1 on persistent family | reconstruction invariance confirmed for persistent drops | pretext/score change targeting level sensitivity (path B/C informed) |

Multiple stages can dominate; the matrix reports the full waterfall, not a
single culprit.

## Honest labeling

- Every claim L2; noun "synthetic anomaly"; the diagnostic changes nothing
  (read-only, dev split, no threshold/target edits, no test access).
- Scope limit stated in the finding: single-index absolute-drop family only;
  no conclusion about relational/multivariate or phenology-shape anomalies.
- Small n (68 injections per cell): medians + IQR, no per-stage fine tables.

## Risks

- Double-counting: stages interact (a large offset subtraction at onset can
  only come from contaminated history; for acute onset the history is clean,
  so a large subtraction would itself be a finding). The waterfall reports
  each stage's marginal effect, not an independent attribution.
- The natural counterfactual is exact by construction (pre-injection tensor),
  so absorption measurement has no estimation error.
