# 10 — Hourly/Daily CWSI in Khuzestan Sugarcane (Zoratipour et al., 2026)

**Full Citation:** Zoratipour, E., Veysi, S., Mohammadi, A.S., Boroomand Nasab, S., & Naseri, A.A. (2026). Deriving hourly and daily crop water stress index through the lens of proximal sensing in sugarcane fields. *Ain Shams Engineering Journal*, 17, 103903.  
**DOI:** [10.1016/j.asej.2025.103903](https://doi.org/10.1016/j.asej.2025.103903)  
**Status:** ✅ Full read (2026-10-04)  
**Themes:** #CWSI #Study-area #Methodology

---

## What It Does

Measures hourly and daily CWSI in sugarcane fields using stationary proximal thermal sensors, then links to satellite-scale inference.

## Study Area

- **Amirkabir Agro-Industrial Unit**, Khuzestan (same as Motlagh et al. 2026)
- 14,000 ha total, ~10,000 ha under sugarcane
- Fields uniform ~25 ha ("Each field spanning 25 ha"); **"400 fields" is NOT stated in this paper** — it is a derived estimate (10,000 ha ÷ 25 ha). The 1000 m × 250 m geometry comes from paper #24 (§2.1), not #10.
- Semi-arid, 25°C avg temp, 198 mm annual rain
- Peak water demand: July–September

## Methodology

### Proximal Sensing Setup
- **Sensor:** Apogee SI-411 IRt/c infrared thermometer — CORRECTED from "SI-111 H" per §2.2, p.2 (reported accuracy ±0.2 °C for 10–40 °C, resolution 0.01 °C, spectral range 8–14 μm)
- **Mount:** 3m iron base, 45° zenith angle, 10–30 cm from canopy
- **Logging:** CR1000X data loggers
- **Period:** July–September 2023, 6:00–18:00 daily
- **Measurements:** Canopy temperature (Tc), air temperature (Ta), relative humidity

### CWSI Calculation
```
CWSI = (Tc - Ta - NWSB) / (UL - NWSB)

Where:
  NWSB (Non-Water Stress Baseline) = f(VPD, Ta)
  UL (Upper Limit) = stressed reference
```

## Key Findings

| Finding | Value | Implication |
|---------|-------|-------------|
| **CWSI threshold for irrigation** | **0.4–0.5** | Our validation benchmark |
| **Peak stress times** | 10:00 AM and 14:00 (two peaks) | Landsat overpass (~10:30) captures morning peak |
| **Daily CWSI minimum** | 2 days post-irrigation | Confirms irrigation response timing |
| **Strongest correlation** | Soil moisture 0–90 cm depth | Root-zone moisture drives CWSI |
| **Summer rain** | Minimal — "winter precipitation predominates and summer precipitation is minimal" (§2.1, p.2) | Near-pure evaporative demand stress |

### Validation
- **NOT FOUND in full text (2026-10-04):** the previously listed "stem water potential R² = 0.526" and "stomatal conductance R² = 0.517" appear nowhere in the paper. Limitations (§4, p.15) explicitly state that "Direct physiological measurements, such as stomatal conductance, leaf water potential, or chlorophyll fluorescence, were not concurrently collected." Do not cite these numbers.
- Daily CWSI strongly influenced by soil moisture (0–90 cm, r = −0.66; 0–30 cm r = −0.64; §3.6, p.11; Fig. 10, p.14)
- Cross-correlation: CWSI changes lead soil-moisture change by ~1–2 days (optimal lag −1 to −2 d); strongest r = −0.808, p < 0.05, Replicate 4 (Fig. 11, p.14)

## Direct Implications for Thesis

1. **CWSI = 0.4–0.5 threshold** — use as ground-truth validation for satellite-derived CWSI
2. **July–September window** — focus analysis on these 3 months (matches Motlagh et al.)
3. **Two-peak daily pattern** — Landsat 10:30 overpass captures morning peak; good timing
4. **Proximal → satellite bridge** — their methodology validates satellite CWSI inference
5. **No summer rain** — simplifies stress attribution (no confounding precipitation)

## CWSI Computation for Our Pipeline

Following their approach:
```python
# Simplified empirical CWSI (from their Eq. 1)
CWSI = (Ts - Ts_cold) / (Ts_hot - Ts_cold)

Where:
  Ts = canopy temperature per pixel (from Landsat LST)
  Ts_cold = well-watered vegetation pixel (min LST)
  Ts_hot = bare soil / non-transpiring pixel (max LST)
```

Use Landsat-MODIS fused LST (STRFM) for daily coverage, following Motlagh et al. (2026).

---

## Verified Full-Text Findings (2026-10-04)

Full read of `papers/10-Zoratipour-2026-Hourly-Daily-CWSI-Proximal.pdf` (17 pp; ASEJ 17:103903; printed pages = PDF pages). Every number below was checked against the PDF text.

### Study site & design (verified)
- **Site:** "Amir Kabir Agro Industry Unit" (acknowledgments: "Amir Kahir Sugarcane Agro-Industry"), Khuzestan — one of eight sugarcane agro-business companies in southern Khuzestan; gross area 14,000 ha; annual cultivation 9,000–10,000 ha; uniform field size ~25 ha (§2.1, p.2; Fig. 1, p.3).
- **Climate:** semi-arid (Gaussian classification, synoptic station data); annual mean T 25 °C (Tmin/Tmax 17/34 °C); annual precipitation 198 mm; winter precipitation predominates, summer minimal; "July, August, and September have the highest peak water consumption" (§2.1, p.2).
- **Fields/instruments:** 4 fields = Plant, Ratoon 1, Ratoon 2, Ratoon 3; 3 proximal stations per field = 12 points (Fig. 2, p.4; Table 1, p.3). Soil sampled at 0–30/30–60/60–90 cm (gravimetric); textures clay loam & silty clay (Table 1). Tc via stationary Apogee SI-411 IRt/c; Ta probe ±0.2 °C; RH ±2%; 3-m base, 45° zenith, 10–30 cm from canopy; CR1000X loggers; ERA5-Land used only to fill hourly solar radiation (SR) and 2-m wind (U2) (§2.1–2.2, pp.2–3).
- **No satellite imagery is used in this paper** — purely proximal. Period: July–September 2023, 06:00–18:00 daily (Abstract; §4, p.15: "data collected from July–September 2023) in a single agro-industrial unit").
- **CWSI:** Idso et al. (1981) Eq (1): CWSI = [(Tc−Ta) − (Tc−Ta)LL] / [(Tc−Ta)UL − (Tc−Ta)LL]; LL = a + b·VPD (Eq 6), UL = a − b·VPG (Eq 7); baselines derived per age & month (Table 2, p.9); observed VPD range 2–15 kPa (§3.1, p.5).

### Threshold & decision rule (verified)
- Abstract (p.1): "**A CWSI threshold in the range of 0.4–0.5 is proposed for initiating irrigation**, supporting high-resolution monitoring for improved field water management."
- Conclusions (§5, p.15): "a CWSI threshold of 0.5 is proposed as a trigger for irrigation initiation in sugarcane field under similar arid conditions."
- §3.3 classification (p.9): at midday "when 0.1 < CWSI < 0.5, the crop is assumed to be stressed, CWSI > 0.5 moderately stressed, and severely stressed CWSI = 1.0 [1]"; Fig. 8d marks a "Severe Stress Threshold 0.45" (p.12).
- Physiological anchor: mean CWSI = 0.50 ± 0.02 on DAI 5 = tipping point; Tukey HSD F(5,26) = 52.71, p < 0.001; DAI 2 minimum (0.33 ± 0.03), DAI 7–9 maximum (0.60–0.62) (Tables 3–4, p.12; "robustly validates the CWSI threshold of 0.5 proposed in this study", p.11).

### Hourly vs daily (verified)
- Two peaks of the hourly stress function: solar radiation (10:00) and wind speed (14:00) (Abstract; Fig. 7, p.11). Hourly CWSI rises 06:00→10:00, dips abruptly 10:00→12:00, rises again to 14:00, eases to 18:00 (§3.2, p.6).
- "Hourly monitoring should be carried out around 10:00–15:00" (§3.2, p.6); "the most appropriate time to measure CWSI and related parameters was at 11:00 to 12:00 am, which corresponds to the daily average of the CWSI" (§3.3, p.8) — supports using ~10:30 overpass data (thesis inference; note 10:00–12:00 is the intra-day dip, not the morning peak itself).
- Daily CWSI minimum 2 days post-irrigation (0.27 at soil moisture 0.30 ≈ field capacity); daily CWSI range 0.16–0.52; maximum ~0.27–0.66 about 9 days after irrigation (§3.3, p.9).
- Soil moisture: strongest negative CWSI correlations at 0–90 cm (r = −0.66) and 0–30 cm (r = −0.64) (§3.6, p.11; Fig. 10, p.14); cross-correlation optimal lag −1 to −2 days (CWSI leads soil moisture), best r = −0.808, p < 0.05 (Fig. 11, p.14).
- Two-factor ANOVA: DAI p < 0.001; crop age p = 0.038; interaction p = 0.939 (Table 3, p.12). Ratoon 3 fields show elevated CWSI (possible resistance/reduced stomatal conductance, p.11).

### Salinity (verified — qualitative only, never measured)
- Mentioned as a regional challenge (Intro, p.2: "water logging, soil salinity, and a tropical climate pose significant challenges in this region") and discussed as a CWSI confounder: "In saline soils, a significant portion of the total soil water potential is attributed to osmotic potential... the crop may exhibit elevated CWSI values as stomatal closure and reduced transpiration occur in response to osmotic stress rather than actual soil water deficit. Therefore, in sugarcane systems affected by salinity, both soil moisture and salinity dynamics must be considered jointly when interpreting CWSI behavior and defining irrigation thresholds" (§3.6, p.13).
- Limitations (§4, p.15): "other abiotic stresses prevalent in the region, such as soil salinity and periodic waterlogging... were not explicitly measured or statistically separated in this analysis." → **No EC/soil-salinity data anywhere in this paper.**

### Repo-claim verification

| # | Repo claim | Verdict | Evidence (section/page) |
|---|------------|---------|--------------------------|
| 1 | CWSI threshold 0.4–0.5 for irrigation decisions | VERIFIED — stated in this paper only (not in #24 or #25) | Abstract p.1; §5 p.15 (trigger 0.5); §3.3 p.9 classification; Fig. 8d 0.45 |
| 4 | Hourly vs daily comparison; two peaks 10:00 & 14:00 | VERIFIED | Abstract p.1; §3.2 p.6; Fig. 7 p.11 |
| 4 | July–September critical irrigation window | VERIFIED | §2.1 p.2 ("highest peak water consumption"); Abstract (period Jul–Sep 2023) |
| 4 | Proximal vs satellite agreement | NOT FOUND — no satellite data used; ERA5-Land only for SR/U2 (satellite validation happens in #24/#25) | §2.1–2.2 pp.2–3 |
| 5 | Site = Amirkabir; 14,000 ha; ~25 ha fields; Jul–Sep 2023 | VERIFIED | §2.1 p.2; Fig. 1 p.3; §4 p.15 |
| 5 | 400 fields | NOT FOUND (not stated; derived 10,000 ha ÷ 25 ha) | §2.1 p.2 |
| 5 | Soil salinity measurements | NOT FOUND — qualitative discussion only | Intro p.2; §3.6 p.13; §4 p.15 |
| — | CWSI vs stem water potential R² = 0.526; stomatal conductance R² = 0.517 | NOT FOUND / REFUTED — Limitations state these were not collected | §4 p.15 |
| — | Sensor = Apogee SI-111 | CORRECTED → Apogee SI-411 IRt/c | §2.2 p.2 |
| — | Summer rain "None" | PARTIAL → "minimal" | §2.1 p.2 |

---

*Linked from: [[Literature-Matrix]], [[00-Thesis-Overview]]*
