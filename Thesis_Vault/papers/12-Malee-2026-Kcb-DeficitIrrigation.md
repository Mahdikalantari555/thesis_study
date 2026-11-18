# 12 — Sugarcane Kcb Calibration + Deficit Irrigation (Malee et al., 2026)

**Full Citation:** Malee, C., Phattaralerphong, J., Kositsakulchai, E., Rattanasornphatdee, S., Luepromchai, E., & Kachenchart, B. (2026). Enhancing water productivity in sugarcane cultivation by integrating basal crop coefficient with deficit irrigation. *Agricultural Water Management*, 333, 110529.
**DOI:** [10.1016/j.agwat.2026.110529](https://doi.org/10.1016/j.agwat.2026.110529) | Open Access | Thailand (Mahidol Univ. + Khon Kaen partners)
**Status:** ✅ Full read (2026-10-04)
**Themes:** #Sugarcane #Kcb #Deficit-irrigation #AquaCrop #Calibration-context

---

## ⚠️ Provenance Note

This is a **Thailand** study — **not Khuzestan**. The matrix row and PDF slot for #12 were mis-filed until 2026-10-04: the file at `papers/12-Malee-…` was actually the Motlagh Ky paper (#76), and the REAL Malee PDF sat in `archived_duplicates/` as `ref-Enhancing-Water-Productivity-…` (mis-labeled a duplicate). Recovered and promoted 2026-10-04; see `papers/ARCHIVED_DUPLICATES.md`.

## What It Does

Calibrates **FAO-56 dual-Kc coefficients for sugarcane cultivar KK3 (Khon Kaen 3)** from two weighing lysimeters (full irrigation vs **50% MAD** deficit) over two seasons (2020/21, 2021/22) in **central Thailand (Aw — tropical savanna)**, then feeds the calibrated coefficients into **SIMDualKc** (calibration) and **AquaCrop** (scenario simulation) to optimize deficit-irrigation scheduling and water productivity.

## Verified Key Results

| Item | Value | Source |
|------|-------|--------|
| Calibrated Kcb (initial / mid / late) | **0.15 / 1.11 / 0.49** | Table, p.8 |
| vs FAO-56 Kcb | 0.15 / 1.20 / 0.70 | same table (initial matches; mid & late lower locally) |
| Calibrated Kc (single) / Ke | initial 0.36 (Ke 0.21) · mid **1.15** (Ke 0.05) · late 0.49 (Ke 0.00) · avg 0.95 | same table |
| lysimeter precision | ±0.16 kg (±0.07 mm); 30-s logging | §2 |
| FI trigger | 10–15% ASW depletion (non-stress reference) | §2.2 |
| Deficit scenario verdict | **25% and 50% MAD** "significantly reduced crop water use while maintaining competitive sugarcane yields"; rainfed loses yield to rainfall variability | §3 |
| Yield / ET (2020/21) | FI 113,570 vs 50% MAD 107,680 kg/ha cane; ET 11,708 vs 11,680 m³/ha | table p.8 |

## Implications for the Thesis

1. **Calibration-transfer caution, quantified:** mid-season Kcb 1.11 (Thailand, Aw climate, KK3) vs FAO-56 1.20 — even within one crop, cultivar + climate shift coefficients by ~8%. Khuzestan (arid, different varieties CP69-1062/IRC99-02/CP73-21 per #11) needs its own calibration; use Malee as the *method template* (lysimeter → SIMDualKc → AquaCrop), not as constants.
2. **Mid-season Kcb ≈ 1.11 aligns with the Jul–Sep stress window** (#76 Ky peak early July) — the high-demand phase our water branch must resolve.
3. **Deficit irrigation viability (25–50% MAD)**: supports framing our monitor as a *deficit-management* tool — moderate stress is agronomically intended, so the Water_Only class includes planned deficit, not only harm. (Label-design nuance: severity thresholds matter more than binary stress.)
4. **ET near-equality under deficit** (11,680 vs 11,708 m³/ha with −5% yield): canopy-energy signals under moderate deficit change little — another reason water-stress detection needs temporal dynamics + thermal sensitivity, not static ET proxies.
5. AquaCrop as the **physics-guided constraint candidate** if we add model-informed priors (kept optional in 04-Thesis-Design).

## Quotable Verbatim

1. "The calibrated Kcb values reflected the crop's phenological water demands and were 0.15, 1.11 and 0.49 for initial growth, mid-season and late-season stages, respectively." — Results
2. "the moderate deficit irrigation regimes (25% and 50% MAD) significantly reduced crop water use while maintaining competitive sugarcane yields." — §3
3. "In contrast, the rainfed system demonstrated yield losses due to rainfall variability." — §3

## Cautions

- 2 lysimeters × 2 seasons, one cultivar, one climate — small-n agronomy; scenario numbers are model-simulated (AquaCrop), not field-tested.
- Don't cite for Khuzestan constants; cite for the calibration workflow and deficit-irrigation framing.
- Salinity: not a topic (2 incidental mentions only).

## Links

- Matrix row: #12 (rewritten 2026-10-04 after mis-file fix)
- Pairs with #76 (local Ky) for the water-accounting layer of the label design
