# Study Note — Manrique et al. 2024

**Paper:** Castro Manrique, D.R.; Lopes, P.M.O.; Nascimento, C.R.; Ribeiro, E.P.; Silva, A.S.d. (2024). Phenological monitoring of irrigated sugarcane using Google Earth Engine, time series, and TIMESAT in the Brazilian semi-arid. *AgriEngineering*, 6(4), 3799–3822. https://doi.org/10.3390/agriengineering6040217

**PDF:** `D:\RS\Thesis\New_papers\agriengineering-06-00217-v2.pdf` — text extracted with `pypdf` 6.19.0 (conda env `geo`). Raw extract saved alongside as `Manrique-2024-raw-extract.txt`.

---

## 1. Verified APA 7th citation

[PDF available - verified]

Castro Manrique, D. R., Lopes, P. M. O., Nascimento, C. R., Ribeiro, E. P., & Silva, A. S. d. (2024). Phenological monitoring of irrigated sugarcane using Google Earth Engine, time series, and TIMESAT in the Brazilian semi-arid. *AgriEngineering*, 6(4), 3799–3822. https://doi.org/10.3390/agriengineering6040217

- Received: 1 July 2024; Revised: 26 September 2024; Accepted: 26 September 2024; Published: 18 October 2024.
- Open access (CC BY 4.0), MDPI, Basel, Switzerland.
- Academic editors: Fatwa Ramdani, Riswan S. Sianturi, Adi Wibowo.
- Correspondence: P. M. O. Lopes (pabricio.lopes@ufrpe.br).

---

## 2. Key findings relevant to sugarcane phenology / harvest-date detection

[PDF available - verified] All items below are drawn from the extracted PDF text.

### Phenology & seasonality
- Study area: irrigated sugarcane in the São Francisco Valley, Juazeiro–Bahia, Brazil (≈9°20′S–9°40′S, 40°13′W–40°0′W, ≈396 masl), hot semi-arid (BSh) climate, rainfall <600 mm/yr, highly irregular.
- 131.06 ha study area; 121.50 ha sugarcane divided into 13 plots (6.88–11.64 ha each); drip irrigation; manual harvest.
- Two varieties: SP 79-1011 (2001–2012) and VAT/VAP 90-212 (after planting renewal in 2012/2013).
- 19 phenological cycles over 2001–2020 from MODIS NDVI time series.
- NDVI time series did **not** follow rainfall — irrigated with São Francisco River water, not regional rainfall.
- Agricultural calendar: SP 79-1011 emergence Oct, establishment Oct–Nov, max development Apr–Jun, harvest Sep–Oct. VAT 90-212 emergence Jul, establishment Aug, max development Feb–Mar, harvest Jun–Jul.
- End of vegetative cycle (= harvest date) is critical for harvest planning, pest/disease control, and market forecasting.

### Harvest-date validation (TIMESAT vs. observed, SP 79-1011, 2006–2012, 13 plots)
- Pearson correlation r = 0.99 ("almost perfect")
- Adjusted R² = 0.99
- Willmott concordance index d = 0.99
- Performance index e = r × d = 0.99 ("excellent"/"great")
- Mean error (ME) = −3.92 days → tendency to **underestimate** harvest date
- **Mean absolute error (MAE) = 10.45 days (≈10 days)**
- RMSE = 11.87 days
- Shapiro–Wilk: harvest dates approximately normally distributed (all plots except plot 7).
- Student's t-test: no significant difference between observed and estimated mean harvest dates (p > 0.05).
- Plots 1, 3, 4, and 7 showed higher precision (MAE 4–9 days); other plots MAE 26–40 days.
- Individual plot results (area ha / r / R² / ME / MAE / RMSE): 1/11.64, 2/8.07, 3/9.89, 4/10.27, 5/11.19, 6/10.16, 7/11.10, 8/9.71, 9/9.26, 10/6.88, 11/7.51, 12/7.85, 13/7.97; total area 121.5 ha.

### Caveats / limitations (from paper)
- MOD13Q1 pixel size = 250 m (≈6.25 ha); authors advise caution when applying operationally to areas **smaller than** the 6.25 ha pixel size.
- Harvest data for 2014–2017 not made available by producer (contract termination); 2018–2020 also unavailable.
- TIMESAT validation period limited to 2006–2012 for SP 79-1011.

---

## 3. Methods used (GEE, TIMESAT, segmentation)

[PDF available - verified] unless noted.

### Data
- MOD13Q1 Version 6.1 (MODIS/Terra) NDVI: 250 m spatial resolution, 16-day composites, tile h14v09, 460 images, 2001–2020; atmospherically corrected, MVC (maximum value composite), QA pixel flags for clouds/aerosols/shadows.
- Processed via **Google Earth Engine (GEE) Code Editor** (JavaScript) to produce NDVI time series for the study area, then imported into TIMESAT.
- MapBiomas Collection 6 (2006–2012) annual land-use/land-cover maps (Landsat TM) for LULC characterization.
- Meteorological data: UNIVASF Labmet automatic weather station, Juazeiro (2008–2020): rainfall, solar radiation, air temperature, relative humidity.

### TIMESAT software (v3.3; MATLAB 8.2 GUI)
- Five processing stages: (1) IMAGE VIEW — prepare NDVI time series (CSV → ASCII); (2) TSM GUI — quality check + data fitting; (3) TSM_settings — ASCII settings file; (4) Fortran TSF_process — binary files of adjusted phenological parameters; (5) TSF_seas2img / TSF_fit2img — phenological parameter maps per pixel.
- Fitting model: **Savitsky–Golay** (chosen because it fit the NDVI curve and minimized cloud-induced noise); 2 iterations; season start value 0.2; end-of-season value 0.2 (i.e., 20% of seasonal range); seasonal parameter = yes; force minimum value = no.
- Phenological metrics estimated: Start of Season (SOS), End of Season (EOS), Length of Season (LOS), Peak of Season (POS), plus seasonal amplitude and integrals.

### Segmentation
- **Not described in the PDF.** A search of the extracted text found zero occurrences of "segment"/"segmentation". The paper estimates phenological metrics per pixel / per area directly from the MODIS NDVI time series in TIMESAT; it does not report an explicit image-separation/segmentation step. Mark as **[not in PDF — segmentation not described]**.

### Statistical analysis / validation
- Shapiro–Wilk normality test; Student's t-test (equal means); Pearson correlation (r); adjusted R²; RMSE; MAE; Willmott's concordance index (d); Camargo & Sentelhas performance index (e = r × d).
- Computed in Microsoft Excel 365; descriptive statistics visualized in QGIS 3.1.

---

## 4. Findings-13 implications (harvest-date MAE ~10 days; supports D2 30-day threshold)

[Mixed verification — see below]

- **[PDF available - verified]** Harvest-date MAE ≈ 10 days (10.45 days, total area; RMSE 11.87 days; r = 0.99; performance index e = 0.99 "excellent") for TIMESAT-estimated vs. observed SP 79-1011 harvest dates, 2006–2012, 13 plots, 121.5 ha.
- **[Author's framing — not in PDF]** The terms "D2", "30-day threshold", and "Findings-13" do not appear in the PDF (zero occurrences for "threshold", "30-day", "D2", "Findings"). They are treated here as the thesis interpretive framing.
- **Implication (author's framing):** A harvest-date estimation error of ~10 days (MAE) is well within a 30-day decision threshold (D2), supporting use of GEE + MOD13Q1 NDVI + TIMESAT as an operationally viable, low-cost approach for sugarcane harvest-date monitoring where sub-30-day accuracy is acceptable. The authors themselves note the approach is usable "with caution" for areas larger than the 6.25 ha MODIS pixel.

---

## 5. TO VERIFY FROM PDF

| Item | Status | Notes |
|------|--------|-------|
| Full citation (authors, title, journal, year, vol/issue, pages, DOI) | PDF available - verified | Extracted from page 1 of the PDF |
| Journal issue = 6(4) | PDF available - verified | DOI suffix `6040217` and page range 3799–3822 confirm vol. 6; issue inferred from DOI |
| MAE ≈ 10 days (10.45), r = 0.99, R² = 0.99, d = 0.99, e = 0.99, ME = −3.92, RMSE = 11.87 | PDF available - verified | Table 5 + §3.6 (lines ~868–913) |
| Validation window: SP 79-1011, 2006–2012, 13 plots, 121.5 ha | PDF available - verified | §2.2, §3.6, Table 5 |
| GEE Code Editor (JavaScript) + MOD13Q1 NDVI → TIMESAT | PDF available - verified | §2.3, §2.5, Figure 2 |
| TIMESAT v3.3, MATLAB 8.2, Savitsky–Golay, season start/end 0.2 | PDF available - verified | §2.5, Table 2 |
| 19 phenological cycles 2001–2020; NDVI ≠ rainfall | PDF available - verified | §3.3, §4.5, §5 |
| MOD13Q1 250 m ≈ 6.25 ha pixel; caution for small areas | PDF available - verified | §4.8, §5 |
| Segmentation step | Not in PDF | Zero occurrences of "segment"/"segmentation" |
| "D2" / "30-day threshold" / "Findings-13" | Not in PDF | Author's thesis framing; zero occurrences |

---

**Extraction note:** PDF text extracted successfully with `pypdf` 6.19.0 (104,512 characters). Raw extract: `Manrique-2024-raw-extract.txt`. PyPDF2 was not needed (pypdf succeeded).
