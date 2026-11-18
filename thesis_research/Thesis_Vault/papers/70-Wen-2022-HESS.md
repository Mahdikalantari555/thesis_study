# 70 — Combined Drought + Salinity Crop-Stress Monitoring via Five Sentinel-2 Traits (Wen et al., 2022)

**Full Citation:** Wen, W., Timmermans, J., Chen, Q., & van Bodegom, P. M. (2022). Monitoring the combined effects of drought and salinity stress on crops using remote sensing in the Netherlands. *Hydrology and Earth System Sciences*, 26, 4537–4552. https://doi.org/10.5194/hess-26-4537-2022
**Status:** ✅ Full read (2026-10-04)

---

## What It Does

First satellite-based, real-life large-scale assessment of individual vs co-occurring drought and salinity stress on crops: five Sentinel-2-derived functional traits (LAI, FAPAR, FVC, Cab, Cw) for maize and potato are statistically tested (two-way + one-way ANOVAs) across six stress classes over the 2018 extreme summer drought in the Netherlands (138.74 km²).

## Key Methodology

- **Trait retrieval**: SNAP "biophysical processor" — ANN trained on a PROSAIL simulated database; canopy traits (LAI, FAPAR, FVC, CCC, CWC) at 10 m from Sentinel-2 L2A; leaf traits derived as Cab = CCC/LAI, Cw = CWC/LAI
- **Stress maps**: drought = SPEI-3 (Apr–Oct 2018, 214 d; no/moderate/severe thresholds); salinity = topsoil chloride from nationwide fresh–salt groundwater dataset (0.1–0.8 / 0.8–2.5 / ≥2.5 g/L); overlay → 9 co-occurrence classes, merged to 6 (no stress, MD, SD, salinity (MS+SS), MD+MS, MD+SS)
- **Statistics**: two-way ANOVA (stress class × date) per crop × trait; one-way ANOVAs + Tukey HSD per month (May, June, July, September); SPSS 27.0

## Relevance to Thesis

**High** — This is the closest combined water+salinity RS benchmark; the paper our CNN-Mamba+SSL+XAI framework must supersede:
- ✅ Establishes the exact statistical baseline to beat (stress-class × date ANOVA, R² 0.326–0.796, variance dominated by date not stress)
- ✅ Confirms combined stress is real, significant, and time-specific (date × stress interaction p < 0.05, strongest for FVC) — motivates temporal (Mamba) modeling
- ✅ Drought > salinity sensitivity in farmers' fields; salinity effect concentrated early-season on Cab — supports water-first thesis framing
- ✅ Multi-trait rationale (each trait responds differently to drought vs salinity) supports multi-index/multi-trait inputs
- ⚠️ Crops are maize + potato (temperate C3), not sugarcane; North Holland ≠ Amirkabir/Khuzestan agro-climate
- ⚠️ "Ground truth" is mapped proxies (SPEI + groundwater chloride at 250 m), no in-situ stress measurements — weak-label setting our SSL approach improves on
- ❌ Pure hypothesis testing on class means; no predictive model, no per-field disentanglement, no ML/DL
- ❌ Interaction never quantified in magnitude — only significance of Tukey comparisons among discrete classes
- ❌ No XAI; no independent accuracy validation of retrieved traits

## Key Takeaway

Class-mean ANOVA over proxy-defined stress maps explains only 0.326–0.796 of trait variance — and most of that is phenology (date), not stress. Combined stress is confirmed as non-additive and time-specific, with drought dominating salinity. This is precisely the ceiling a predictive, per-field, temporally-aware deep learning framework with XAI-based disentanglement replaces.

---

*Linked from: [[Literature-Matrix]]*

---

## Verified Findings (Full Read, 2026-10-04)

### 1. Trait retrieval — RTM, inversion, bands, validation

- **RTM + inversion**: PROSAIL. "The biophysical processor within the SNAP toolbox derives the five traits, namely LAI, FAPAR, FVC, canopy chlorophyll content (CCC), and canopy water content (CWC)... This processor utilizes an artificial neural network (ANN) approach, trained using the PROSAIL simulated database (Weiss and Baret, 2016)" (Section 2.3, p. 4541). Reference: S2ToolBox Level 2 products ATBD v1.1 (Weiss & Baret, 2016, in reference list, p. 4552). ANN trained on **canopy** traits (not leaf traits × multiplication) to improve network performance; leaf counterparts obtained by division: "CCC and CWC thus need to be divided by LAI to obtain Cab (i.e., CCC/LAI) and Cw (i.e., CWC/LAI)" (Section 2.3, p. 4541).
- **Bands**: Sentinel-2 L2A, 10 m and 20 m bands; "those with a 20 m resolution (B5, B6, B7, B8A, B11, and B12) were resampled to the 10 m resolution of B3 and B4" (Section 2.2.1, p. 4540–4541). Retrieval at 10 m per month.
- **Scenes**: "In total, eight cloud-free scenes were found (21 April 2018, 6 May 2018, 26 May 2018, 30 June 2018, 18 July 2018, 13 September 2018, and 28 October 2018)" (Section 2.2.1, p. 4541) — note: only **seven** dates are listed despite "eight scenes" (inconsistency as printed). August scenes (4–29 Aug 2018) were found but omitted because "none were of high quality" (Section 2.2.1, p. 4541).
- **Filtering**: quality flags removed; ditch mask built from April imagery (no crops planted, only ditch vegetation) and applied to other months; per-variable, per-date only data "within the 95 % confidence interval" retained (Section 2.3, p. 4541).
- **Validation accuracy/RMSE per trait**: NOT FOUND. No independent accuracy assessment (RMSE/R²/validate-vs-measured) of the retrieved traits is reported anywhere in the paper; the quality-flag + 95 % interval filtering substitutes for validation.

### 2. ANOVA design (the one to supersede)

- **Design**: two-way ANOVA, factors = **stress combination (6 levels) × time (5 months)**, run separately for each crop (maize, potato) and each trait. Critically: "Since the pixel counts of the six classes of stress combinations... were (highly) different, **drought and salinity were not considered two independent factors**" (Section 2.4, p. 4541). So it is NOT a drought × salinity factorial — it is stress-class × date on class-mean trait values.
- **Response variables**: the five traits LAI, Cab, Cw, FAPAR, FVC (Section 2.4; Table 1).
- **Post hoc**: significant main stress effects followed by "post hoc tests to test whether interaction effects between drought and salinity had occurred"; one-way ANOVAs for May, June, July, September + Tukey HSD among the six stress combinations; SPSS 27.0 (Section 2.4, p. 4541).
- **R² (Table 1, p. 4543)** — verified, matches repo claim of 0.326–0.796:
  - Maize: LAI 0.766, Cab 0.326, Cw 0.590, FAPAR 0.738, FVC 0.761
  - Potato: LAI 0.782, Cab 0.329, Cw 0.571, FAPAR 0.744, FVC 0.796
  - Table 1 note: "R² indicates the percentage that the model concludes the data"; partial eta squared reported per factor.
- **Significance**: all date, stress, and date·stress terms p < 0.001 (printed 0.000) except the maize-LAI stress main effect (F = 1.4, p = 0.226, n.s.; Table 1, p. 4543).
- **Effect-size structure**: "the effects of time in the growing season were much stronger than those of stress or the interaction of date and stress... the effects of the interaction between date and stress were stronger than those of the main effects of stress... The interaction terms were strongest for FVC" (Section 3.1, p. 4541–4542, with Table 1 partial eta squared: e.g., maize LAI date 0.636 vs stress 0.001 vs interaction 0.035).

### 3. Phenology dependence of stress impacts

- Abstract: "the impact level depended strongly on the moment in the growing season" (p. 4537).
- Section 3.1: "the interaction between the effects of time and stress conditions was significant (p < 0.05) (Table 1), indicating that the impact of stress depended on the moment in the growing season" (p. 4542).
- Section 4.2 "Drought and salinity stress differ between growth stages": "during the grain filling (maize) and tuber bulking phase (potato), the sensitivities of these crops are expressed distinctly in the non-harvested aboveground tissues (Figs. 3 and 4), with clear differences in the remote-sensing plant traits" (p. 4545).
- Monthly trajectory (Section 3.2, p. 4542; Fig. 3): maize lowest LAI/FAPAR/FVC under MD+SS in May; June — LAI/FVC dropped most under salinity, potato lowest under SD (significant vs no stress); July — no significant effects; September — significant decreases under MD, MD+MS, MD+SS vs no stress for both crops.
- Cab: "Cab was affected by co-occurring drought and salinity in June and July for potato"; "salinity showed a more severe effect on maize and potato at the early growth stages for Cab" (Section 3.3, p. 4542).

### 4. Drought vs salinity sensitivity — exact results

- Abstract: "with stronger sensitivities to drought than to salinity" (p. 4537).
- Section 3.2: "maize and potato were more sensitive to drought than salinity since no significant change was observed between drought conditions and combinations of drought and salinity stress" (p. 4542).
- Section 3.3: "salinity affected maize less than drought since crop responses were more obvious to drought than salinity for Cw" (p. 4542).
- Section 4 heading: "Drought stress is more important than salinity stress in farmers' conditions" (p. 4543); "We observed that maize and potato were generally more sensitive to drought than salinity in this study (Figs. 3 and 4)" (p. 4545).
- Surprise framing: "we observed that – in contrast to our expectations – the impacts of salinity were not highly pronounced at this scale, with most strong impacts originating due to drought stress during the 2018 drought" (Section 4, p. 4542); since FAO salinity damage thresholds were surpassed wherever salinity was imposed, "salinity impacts on crop performance (by the FAO) may have been overstated" (Section 4.1, p. 4545).
- Conclusions: "both maize and potato responded more prominently to drought, thus demonstrating a stronger sensitivity than to salinity" (Section 5, p. 4548).

### 5. Study area, crops, stresses on the ground

- **Area**: "In our tests over the Netherlands at large spatial scale (138.74 km²)" (Abstract, p. 4537) — repo claim verified. Selected region = province of **North Holland**: "a single region with similar soil type, climate, tillage systems, and irrigation methods... it contained the most (seven out of nine) combinations of drought and salt stress (Fig. 2c)... Moreover, both maize and potato were cultivated across all stress combinations in this province" (Section 2.1.5, p. 4540). MS and SS merged into one "salinity" class → six analyzed classes: no stress, MD, SD, salinity (MS+SS), MD+MS, MD+SS (Section 2.1.5, p. 4540; the seven listed combinations include "SD+SS" while the analyzed six use "MD+SS" — minor internal inconsistency as printed).
- **Crops**: maize and potato (Abstract, p. 4537; Section 2.4). Crop map from the Dutch Key Register of Parcels (BRP), resampled to 250 m (Section 2.1.3, p. 4539).
- **Field counts**: NOT FOUND. No number of fields/parcels is reported; only "the pixel counts of the six classes... were (highly) different" (Section 2.4, p. 4541).
- **Drought definition**: SPEI-3 drought map (3-month sliding window) computed from long-term precipitation + potential evapotranspiration 2004–2018 (Chen et al., 2022); SPEI-3 extracted 1 April–30 October 2018 = 214 days; thresholds (daily −1 and −1.5 scaled to the whole period): no drought cumulative SPEI between −214 and 0, moderate between −321 and −214, severe < −321; resampled to 250 m (Section 2.1.1, p. 4538).
- **Salinity definition**: topsoil salinity map from a nationwide fresh–salt **groundwater** dataset (chloride concentrations, NHI); 15 groundwater layers extracted, "the layer closest to the location's corresponding elevation (according to the digital elevation model), i.e., closest to the soil surface, was selected"; resampled to 250 m; classes no salinity (0.1–0.8 g/L), moderate (0.8–2.5 g/L), severe (≥ 2.5 g/L) "according to the salt-resistant capacity of various crops cultivated in the Netherlands (Mulder et al., 2018; Stuyt, 2016)" (Section 2.1.2, p. 4539).
- **Caveat**: neither stress was verified by in-situ measurement — both stresses are defined by mapped proxies (climate index + groundwater-derived chloride), not field soil sampling or plant measurements. All maps at 250 m vs 10 m traits (Sections 2.1.1–2.1.2).
- Irrigation: area identified as rainfed cropland (ESA CCI) and a temporary national irrigation ban was in force in 2018, so irrigation effects could not be analyzed (Section 4.4, p. 4548).

### 6. Combined-stress interaction statements

- Abstract: "While we found exacerbating effects within co-occurring stresses, the impact level depended strongly on the moment in the growing season. For both crops, LAI, FAPAR, and FVC dropped the most under severe drought stress conditions. The patterns for Cab and Cw were more inhibited by co-occurring drought and salinity" (p. 4537).
- Section 3.3: "It seems that there was a **non-additive effect** of drought and salinity for Cw since the changes were not significant between MD+MS, MD+SS, MD, and salinity conditions" (p. 4542).
- Section 4: "in real farmers' conditions, the co-occurrence of drought and salinity indeed can constitute a severe threat due to its interactive effects on crop growth" (p. 4543).
- Conclusions: "the five investigated traits were more negatively affected by a combination of drought and salinity stress compared to individual stress" (Section 5, p. 4548).
- Counter-nuance (mechanistic, literature-based): "The impacts of combined drought and salinity stress on plant growth, chlorophyll content, water use efficiency, and photosynthesis were less severe compared to drought alone. This indicates compensating effects on carbon assimilation due to osmotic adjustments induced by Na⁺ and Cl⁻ (Hussain et al., 2020). Thus, the detrimental effect of single drought stress on crop growth is considered to be mitigated by salinity" (Section 4.1, p. 4545). The paper thus reports both exacerbation (empirical, class comparisons) and mitigation (cited mechanism) — no quantitative interaction magnitude is ever estimated.

### What the thesis supersedes

- **Group-mean ANOVA on proxy stress classes**: Wen et al. explain trait variance via stress-class × date F-tests (R² 0.326–0.796, dominated by date; Table 1) — our CNN-Mamba+SSL framework replaces class-mean hypothesis testing with **predictive per-field, per-date stress estimation** directly from imagery.
- **Fixed 250 m proxy labels, no ground truth**: stresses are SPEI + groundwater-chloride map overlays, never in-situ verified (Sections 2.1.1–2.1.2) — our SSL/self-supervised pretraining learns stress representation end-to-end without relying on such coarse pseudo-labels.
- **Interaction as significance only**: combined-stress interaction is judged by whether Tukey comparisons among 6 discrete classes differ ("non-additive... not significant", Section 3.3) — our XAI component yields **interpretable, quantitative per-field attribution** of water vs salinity evidence, including interaction timing.
- **RTM-bottlenecked features**: traits come from a PROSAIL-SNAP ANN with no independent validation (Section 2.3; per-trait RMSE NOT FOUND) — a deep multi-temporal architecture learned from reflectance removes this retrieval step and its unquantified error ceiling.
