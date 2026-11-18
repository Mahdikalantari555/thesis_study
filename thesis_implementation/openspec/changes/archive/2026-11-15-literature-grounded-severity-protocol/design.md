# Design — literature-grounded-severity-protocol

## Context

Finding 16 + VERIFICATION.md (research workspace) establish: realistic stress = 0.5–2.5× across-field
MAD; measured detection floor 6–8×MAD; the metric needs a severity axis with dynamic range and an
honest account of natural extremes. Owner decision binds the family to NDVI/SAVI index drops.

## Merged verified severity ladder

| Level | ΔNDVI (abs) | % of our grand-growth median ≈0.66 | × across-field MAD (0.066) | Duration (15-d bins) | Anchor (verification status) |
|---|---|---|---|---|---|
| S1 | −0.02 | 3.0 % | 0.30 | 1 | design choice — below documented response |
| S2 | −0.05 | 7.6 % | 0.76 | 1–2 | Clay 2012 flag leaf −5.68 % (verified: abstract + citing summary) |
| S3 | −0.08 | 12.1 % | 1.21 | 2 | Clay 2012 stem extension −10.26 % (same status) |
| S4 | −0.16 | 24.2 % | 2.42 | 2–3 | interpolation S3→S5 (design choice) |
| S5 | −0.28 | 42.4 % | 4.24 | 3–4 | Kiranmai 2025 double-skip −30–40 %, 0.76→0.45–0.51 (verified full text) |
| S6 | −0.40 | 60.6 % | 6.06 | 4–5 | Kiranmai 2025 withholding ≈ −50 %, 0.76→0.37 (verified full text); brackets the 6–8×MAD floor |

- Each level also runs a **persistent variant** (4–6 bins, same Δ) for the salinity-like chronic
  signature; magnitude is unsourced in the literature — the variant is labeled experimental.
- **SAVI** repeats the identical absolute deltas as a separate injection axis; no physiological
  equivalence with NDVI is claimed anywhere.
- Injection mechanics: absolute Δ applied to the observed value (floored at the physical range),
  never erasing observations; onset = ground truth; masks unchanged. Percent columns are also
  computed per field against **its own** grand-growth median at injection time.
- Stage placement: grand growth primary (Dingre et al. 2021, Irrig. Drainage — verified existence);
  tillering/ripening in the stage-sensitivity breakdown only.

## Metrics

- **Primary (dev):** `MDM80` = min severity level achieving detection rate ≥ 0.80 at the 5 %
  cycle-level FAR, per duration family (acute / persistent) and index (NDVI / SAVI); seeds
  [13, 42, 2026]; B1 gets the identical sweep. Lower is better; the main-vs-B1 comparison becomes a
  magnitude ratio with real dynamic range.
- **Secondary:** per-level detection rates with Wilson CIs; **event-level FAR** — consecutive alarmed
  bins merged into events with a minimum separation of 2 bins (POT declustering precedent, pyextremes
  r-separation), FAR = events hitting no injection window / time span (sktime `FalseAlarmRate`
  semantics: extra alarms inside a hit window are not double-counted); partial-cycle AUC-PR 25/50/75 %;
  masked NRMSE. Threshold *calibration* remains the 5 % cycle-level rule (advisor-gated).
- **Independent evaluation cycles:** the MDM sweep uses clean dev cycles disjoint from the threshold
  calibration subset where the dev size permits; the split hash of the evaluation subset is recorded.
- Original mean-z² statistic and finding-16 channel-max statistic remain reported for continuity.

## Honest-labeling rules

- The table ships in code as a config dict with `source`, `verification`, `confidence` per level.
- Excluded from design use (VERIFICATION.md §4): French 2020 −5 %/10-day numbers (paper real,
  numbers unverified); Claude's uncited "2026 maize salinity study"; ESA WorldView-2 spatial σ as
  temporal noise; wheat-0.78 as the % reference for our fields.
- All claims stay at ladder rung **L2**; the noun is "synthetic anomaly", never "stress".
- If the advisor later supplies magnitudes, the table is config-only — no code change.

## Risks

- Dev has 69 cycles; per-level cells will be small → report Wilson CIs and seed std, avoid
  per-level × per-stage fine tables in the headline.
- S6 duration × level interactions may look "better" purely from longer exposure — the MDM is
  reported per duration family to prevent silent cross-family comparisons.
- Event-level FAR is a *reported* metric; changing the calibrated threshold semantics is explicitly
  out of scope (advisor-gated).
