# Recent Trends in Crop Water Stress Monitoring Using Remote Sensing Technologies: A Review

**Authors:** Gokul, S., Manivannan, V., Thirukumaran, K., Boominathan, P., Jagadeeswaran, R., Raja, R., Prabukumar, G., Asritha, M., Surya, K.
**Year:** 2026
**Venue:** *Plant Science Today*, 13(sp2), 1–18
**DOI / ID:** 10.14719/pst.13057
**Local PDF:** `D:\RS\Thesis\thesis_research\papers\73-Gokul-2026-UAV-CropWaterStress-Review.pdf`
**Type:** review (UAV-focused)
**Thesis relevance:** Medium-high — UAV CWSI benchmarks + irrigation DSS gap framing

## Summary
Reviews UAV-based remote sensing for real-time, low-cost crop water stress (CWS) detection, covering RGB, multispectral (MSP), hyperspectral (HSP), and thermal sensors and the physiological indicators they retrieve (chlorophyll content, canopy cover, canopy temperature, stomatal conductance). Highlights ML benchmarks: in spring maize, random forest on UAV MSP+thermal indices with LAI performs well (R² > 0.575, RMSE < 0.073) for crop water content at the 9th-leaf and milking stages and stomatal conductance at tasseling/silking. In cotton, combining UAV spectral + textural features with XGBoost gives the best canopy equivalent water thickness (R² = 0.75) and CWSI (R² = 0.90). Remaining problems: standardizing acquisition, environmental-variability noise, and integrating UAV data into reliable irrigation decision-support. Gaps: cross-regional validation, real-time monitoring, and compatible systems linking UAV imagery with ground sensors and crop models.

## Methods / Approach
- Review of UAV sensor classes × physiological indicators × ML models
- Benchmark synthesis across maize (RF) and cotton (XGBoost) case studies
- Gap analysis: standardization, validation, DSS integration

## Key quantitative results
- Maize: RF (MSP+thermal+LAI) R² > 0.575, RMSE < 0.073, stage-specific
- Cotton: XGBoost CEWT R² = 0.75; CWSI R² = 0.90 (spectral+textural features)

## Relevance to thesis
Provides up-to-date UAV-scale CWSI/CEWT ML benchmarks that satellite-scale results can be compared against (Khuzestan proximal/UAV validation design). Its stated gaps — cross-regional validation and coupling with crop models — echo Berger 2022 and support the thesis argument that current CWS monitoring is fragmented across scales. Also a citation for growth-stage dependence of water-stress signals (9th-leaf/milking/tasseling specificity), reinforcing the temporal-modeling motivation.

## Gaps / opportunities
- UAV scale only; no satellite multi-year archive analysis
- Single-stress (water) focus; salinity absent
- ML models are classical (RF/XGBoost) on engineered indices — no representation learning

## Citation (APA 7th)
- Gokul, S., Manivannan, V., Thirukumaran, K., Boominathan, P., Jagadeeswaran, R., Raja, R., Prabukumar, G., Asritha, M., & Surya, K. (2026). Recent trends in crop water stress monitoring using remote sensing technologies: A review. *Plant Science Today*, *13*(sp2), 1–18. https://doi.org/10.14719/pst.13057

---
*Note written 2026-10-04 from first-page extract. Verify numbers in full PDF before formal proposal use.*
