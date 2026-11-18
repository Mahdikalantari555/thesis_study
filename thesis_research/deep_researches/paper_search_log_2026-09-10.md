# Paper Search Log — 2026-09-10

**Purpose:** Document all papers discovered during extended search for crop stress, salinity, water stress, sugarcane, and related methodology papers.

---

## Search Strategy

### Sources Used
- **arXiv API** (`export.arxiv.org/api/query`) — primary source for recent papers
- **OpenAlex API** (`api.openalex.org`) — metadata and citation data
- **Semantic Scholar API** — blocked (403 Forbidden)
- **Web search** — blocked (API key required)
- **SID.ir / IranDoc** — blocked (curl requests rejected)

### Search Queries Used
1. `crop stress detection satellite remote sensing`
2. `salinity water stress discrimination satellite time series`
3. `sugarcane salinity drought remote sensing Landsat Sentinel`
4. `Mamba state space model remote sensing Earth observation`
5. `self-supervised learning satellite time series`
6. `explainable AI remote sensing interpretability`
7. `vegetation stress detection satellite time series`
8. `crop salinity drought satellite遥感遥感`
9. `random forest SVM machine learning drought salinity crop spectral`
10. `plant physiology crop physiology water stress salinity spectral reflectance phenology`
11. `CWSI crop water stress index satellite remote sensing`
12. `stress discrimination mixed stress concurrent stress drought salinity remote sensing satellite`
13. `phenology growth cycle stress detection drought monitoring satellite time series`
14. `TVDI VHI vegetation health index drought stress satellite`
15. `irrigation management precision agriculture salinity drought remote sensing satellite`

---

## Papers Found (New Discoveries)

### Category A: Directly Relevant to Thesis (SSL + SITS + Stress)

| # | ID | Title | Year | arXiv ID | Relevance |
|---|-----|-------|------|----------|-----------|
| A1 | STS-NET | Spatio-Temporal Stress Network for Self-Supervised Crop Stress Detection using Satellite Image Time Series | 2026 | 2607.18791 | Very High — SSL + SITS + stress detection |
| A2 | EigenCL | Temporal Vegetation Index-Based Unsupervised Crop Stress Detection via Eigenvector-Guided Contrastive Learning | 2025 | 2506.03394 | High — unsupervised VI-based stress detection |
| A3 | Sugar-Beet | Sugar-Beet Stress Detection using Satellite Image Time Series (3D Autoencoder) | 2025 | 2507.13514 | High — same sugar-crop family, 3D-CNN approach |
| A4 | XAI-VI | XAI-Guided Enhancement of Vegetation Indices for Crop Mapping | 2024 | 2407.08298 | Medium-High — bridges XAI and VI methodology |
| A5 | Informed-Learn | Informed Learning for Estimating Drought Stress at Fine-Scale Resolution | 2025 | 2510.18648 | Medium — physics-informed ML philosophy |
| A6 | DeepSalt | DeepSalt: Bridging Laboratory and Satellite Spectra through Domain Adaptation for Large-Scale Soil Salinity Estimation | 2025 | 2510.23124 | High — salinity estimation from satellite |

### Category B: Methodology & Plant Stress Physics

| # | ID | Title | Year | arXiv ID | Relevance |
|---|-----|-------|------|----------|-----------|
| B1 | Spectro-Review | Optical Spectroscopic Imaging for Early Detection of Salinity Stress in Plants: A Review | 2025 | 2509.02265 | Medium — spectral signature reference |
| B2 | Stress-Physio | The Optimization of Crop Response to Climatic Stress through Modulation of Plant Stress Response Mechanisms | 2025 | 2506.01714 | Medium — physiological basis for mixed stress |
| B3 | DroughtSet | DroughtSet: Understanding Drought Through Spatial-Temporal Learning | 2024 | 2412.15075 | Low-Medium — temporal drought monitoring |
| B4 | Sugarcane-Review | Sugarcane Health Monitoring With Satellite Spectroscopy and Machine Learning: A Review | 2024 | 2404.16844 | Critical — directly about your crop |
| B5 | SSL-Irrigation | Self-Supervised Contrastive Learning for Irrigation Detection in Satellite Imagery | 2021 | 2108.05484 | Medium — SSL methodology for water RS |
| B6 | Salinity-Mgmt | To Reduce Soil Salinity: The Role of Irrigation and Water Management in Global Arid Regions | 2022 | 2204.02029 | Medium — long-term salinity dynamics from space |
| B7 | VegHealth-ML | A Machine Learning Approach to Forecasting Remotely Sensed Vegetation Health | 2016 | 1602.06335 | Low — classical ML baseline |

### Category C: Related Applied Papers

| # | ID | Title | Year | arXiv ID | Relevance |
|---|-----|-------|------|----------|-----------|
| C1 | Avocado-Stress | Low-Cost Sensing and Classification for Early Stress and Disease Detection in Avocado Plants | 2025 | 2508.13379 | Low — sensor fusion inspiration |
| C2 | Potato-Stress | Potato Crop Stress Identification in Aerial Images using Deep Learning-based Object Detection | 2021 | 2106.07770 | Low — shows limitations of pixel-wise approaches |
| C3 | ScopeMamba | ScopeMamba-YOLO: Widening the Perceptual Scope Inward and Outward for Small Object Detection in Remote Sensing Imagery | 2026 | 2609.10156 | Low — alternative Mamba implementation |
| C4 | S2-Yield-Review | Sentinel-2 for Crop Yield Estimation: A Systematic Review | 2026 | 2603.23779 | Low-Medium — state-of-the-art context |
| C5 | Tomato-Weed | Branched Broomrape Detection in Tomato Farms Using Satellite Imagery and Time-Series | 2025 | 2509.10804 | Low — temporal degradation pattern reference |
| C6 | JEDI | JEDI: JEPA-to-Edge Distillation for Efficient Cropland Segmentation from Satellite Imagery | 2026 | 2609.07915 | Low — foundation model direction |

---

## Key Findings from New Search

### Most Relevant Papers for Your Thesis

1. **STS-NET (2607.18791)** — Closest match to your proposed approach. Uses SSL + SITS + vegetation indices for stress detection.
   - **Gap:** Only uses 4 VIs as input (not raw bands); no Mamba architecture; no temporal XAI
   - **Takeaway:** Proves the SSL+SITS paradigm works for stress detection

2. **EigenCL (2506.03394)** — Shows that temporal NDRE dynamics alone can drive unsupervised stress detection.
   - **Gap:** Drought-only; no salinity; no XAI
   - **Takeaway:** Confirms VI time series are sufficient features for stress detection

3. **Sugarcane Review (2404.16844)** — Only review paper specifically about sugarcane + satellite + ML.
   - **Gap:** General health monitoring, not stress disentanglement
   - **Takeaway:** Essential reference for band selection and index choices specific to sugarcane

4. **DeepSalt (2510.23124)** — Domain adaptation approach for salinity estimation from satellite.
   - **Gap:** No stress interaction modeling; no temporal analysis
   - **Takeaway:** Adaptable methodology for generating salinity stress labels

### Confirmation of Research Gap

Your thesis addresses a **unique combination** not found in any single paper:
- ✅ SSL on SITS (STS-NET, EigenCL do this separately)
- ✅ Sugarcane-specific (only Sugarcane Review covers this)
- ✅ Water-salinity disentanglement (none of the found papers address this)
- ✅ Temporal XAI (confirmed gap by Höhl et al. 2024, still unaddressed)
- ✅ Mixed stress class (Angon et al. 2022 proves necessity, but no DL implementation exists)

### Persian/Iranian Papers Limitation

**Blockers encountered:**
- SID.ir API returns 403 Forbidden for curl requests
- IranDoc / Magiran not accessible via automated tools
- Web search APIs require paid keys (Firecrawl, Parallel, Exa, Keenable all blocked)

**Recommendation:** Manually search these databases in browser:
- https://www.sid.ir — Persian journals full-text
- https://www.magiran.com — magazine/article database
- https://www.noormags.ir — Islamic/cultural studies focus
- https://www.civilica.com — conference proceedings

**Search terms to use:**
- «تنش آبی شوری遥感» (water-salinity stress remote sensing)
- «پایش遥感 منابع آب کشاورزی» (agricultural water resources remote sensing monitoring)
- «شاخصهای گیاهی تشخیص خشکی» (vegetation indices for drought detection)
- «تنش همزمان خشکی و شوری» (concurrent drought and salinity stress)
- «مدلسازی تنش آبی گیاهان با استفاده از دادههای ماهوارهای» (plant water stress modeling using satellite data)

---

## File Locations

All research outputs saved to:
- `thesis_research/deep_researches/new_paper_discoveries_2026-09-10.md` — Full categorization with relevance analysis
- `thesis_research/deep_researches/crop_stress_papers_2026-09-10.md` — Downloadable paper list with PDF links
- `Thesis_Vault/Literature-Matrix.md` — Living literature matrix (updated with 24 new papers)

---

## Next Steps

1. Download top 10 most relevant papers using batch script in `crop_stress_papers_2026-09-10.md`
2. Read Sugarcane Review (2404.16844) for crop-specific methodology
3. Read STS-NET (2607.18791) for SSL+SITS pipeline comparison
4. Manually search Persian databases for local Khuzestan studies
5. Update proposal draft with new references
