# Study note — Joshi et al. 2024

## Citation (verified via Crossref, 2026-11-11)

Joshi, N., Simms, D.M., Burgess, P.J. (2024). Automating the Derivation of Sugarcane Growth Stages from Earth Observation Time Series. *Remote Sensing* 16:4244. DOI: 10.3390/rs16224244.

## What it implies for this thesis (from findings 13)

- L8 + S2 TOA, sugarcane, India, 326+356 farms.
- Method: BISE (30-day window) → resample 14-day → FFT → Difference-of-Gaussians for troughs; FAO two-crop model for growth stages.
- SOS/EOS vs visual labels: R² 0.72–0.84, RMSE 17–27 days after outlier removal; outliers from residual cloud breaking a single chip.
- Implication: harvest-date error in literature is 10–27 days → the D2 30-day segmentation threshold is reasonable.
- Implication: current segmentation (find_peaks on −NDVI, prominence ≥ 0.15, prior-plateau ≥ 0.7 max, post-trough rise ≥ 0.15 within 180 days, length 180–540 days) matches Joshi/Kavats logic → keep (R1).

Status: citation verified; PDF downloaded 2026-11-11 (thesis_research/papers/). TO VERIFY section cleared — PDF available for direct reading.

