# 07 — Optical Spectroscopic Imaging for Salinity Stress: Review (Gupta et al., 2025)

**Full Citation:** Gupta, R., Gujrathi, S., Sharma, S., & Bharadwaj, S. (2025). Optical Spectroscopic Imaging for Early Detection of Salinity Stress in Plants: A Review. *arXiv:2509.02265*.  
**PDF:** https://arxiv.org/pdf/2509.02265v1  
**Status:** Read  

## Key Findings

### Three Imaging Modalities Reviewed

| Modality | Wavelength Range | Detects | Sensitivity |
|----------|-----------------|---------|-------------|
| **Fluorescence Imaging** | Visible excitation → red/far-red emission | Photosystem II efficiency, chlorophyll content | Very high — detects stress 3-5 days before visual symptoms |
| **Hyperspectral Imaging** | 400-2500 nm ( VNIR + SWIR) | Pigment composition, water content, biochemical changes | High — identifies specific stress signatures |
| **Thermal Imaging** | 3-5 μm (MWIR), 8-14 μm (LWIR) | Canopy temperature, stomatal conductance, transpiration | Medium — indicates water stress indirectly |

### Key Physiological Responses to Salinity (from paper)

1. **Osmotic phase**: Reduced water potential → stomatal closure → reduced CO₂ uptake
2. **Ionic phase**: Na⁺/Cl⁻ accumulation → K⁺/Ca²⁺ displacement → enzymatic dysfunction
3. **Oxidative stress**: ROS overproduction → membrane lipid peroxidation → cell damage
4. **Photosynthesis impairment**: Chlorophyll degradation → reduced PSII efficiency

### Classification Accuracy Results

| Study | Method | Crop | Accuracy |
|-------|--------|------|----------|
| Multicolor fluorescence + SVM | 5 days post-treatment | Various | 92% |
| Multicolor fluorescence + SVM | 9 days post-treatment | Various | 98% |
| Chlorophyll fluorescence + ResNet50 | Soybean (hydroponic) | Soybean | 98.61% |
| Hyperspectral + PLSR | Wheat (hydroponic) | Wheat | R²~0.79 |
| Thermal + ANN | Multiple genotypes | Various | R²=0.62-0.90 |

### Temperature Increase Under Salinity

| Salinity Level | Temp Increase (°C) | LAI Reduction | Transpiration Reduction |
|---------------|-------------------|---------------|----------------------|
| Slight (S3) | +0.88°C | -19.3% | -1.2% |
| Moderate (S5) | +0.98°C | -31.2% | -6.7% |
| Severe (S7) | +1.19°C | -54.2% | -20.0% |

### Spectral Regions for Salinity Detection

- **Red-edge (700-750nm)**: Chlorophyll degradation sensitivity
- **NIR (750-1300nm)**: Cell structure, biomass changes
- **SWIR (1300-2500nm)**: Water content, ion absorption features
- **PRI (531/570nm)**: Photosynthetic efficiency indicator

## Relevance to Thesis

**Medium** — Essential for understanding spectral signatures of salinity stress:
- ✅ Explains what spectral features change under salinity (informs band selection)
- ✅ Documents temperature increases correlate with salinity severity (thermal channel relevance)
- ✅ Shows fluorescence is most sensitive for early detection (conceptually transferable)
- ✅ Covers both ground-based and airborne/satellite platforms
- ❌ Mostly ground-based/handheld studies, few satellite validations
- ❌ No deep learning architecture details
- ❌ No temporal dynamics analysis

## Key Insight for Thesis

The **thermal response to salinity** (canopy warming due to stomatal closure) is directly measurable from Landsat Band 10 (LST). This provides a physical basis for including thermal data in your water stress detection pipeline. The **red-edge shift** (Band 5/6 in Landsat 8) is the most sensitive spectral region for chlorophyll-related stress — critical for your band selection.
