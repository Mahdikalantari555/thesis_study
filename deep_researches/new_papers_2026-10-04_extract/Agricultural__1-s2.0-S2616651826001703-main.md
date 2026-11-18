# Extract: 1-s2.0-S2616651826001703-main.pdf

*First ~4 pages, extracted with pdftotext on 2026-10-04. Source: D:\RS\Thesis\New_papers$f*

---

                                                       H2Open Journal 9 (2026) 100024
                                               Contents lists available at ScienceDirect

                                           H2Open Journal

                           journal homepage: www.elsevier.com/locate/issn/2616-6518/

Remote sensing-based assessment of evapotranspiration and crop                              ]]]]
water stress in the Volta Basin, 2000-2023
                                                                                            ]]]]]]
Rachel Olawoyin, George Owusu Amoah, Jones Abrefa Danquah

Department of Geography and Regional Planning, University of Cape Coast, Cape Coast, Ghana

ARTICLE INFO               ABSTRACT

Keywords:                  Climate variability continues to threaten agriculture in the Volta River Basin of West Africa, a region
Surface temperature index  highly sensitive to temperature, rainfall, and land-use change. Using satellite products from the
Crop water stress          Moderate Resolution Imaging Spectroradiometer (MODIS), Climate Hazards Group InfraRed
Thermal stress             Precipitation with Station data (CHIRPS), and European Space Agency (ESA) satellite missions
Climate variability        (2000-2023), this study conducted a spatiotemporal assessment of land surface temperature, evapo­
Vegetation dynamics        transpiration (ET), and the Crop Water Stress Index (CWSI). CWSI was estimated using a land surface
Water scarcity             temperature-vegetation index (LST-NDVI) triangular approach to evaluate vegetation water stress
                           across the basin. The results reveal basin-wide warming, with the strongest temperature increases
                           occurring in the southern parts of the basin, while persistent vegetation decline was observed in
                           northern and central zones, where vegetation greenness ranged from -0.143 to 0.769. The most
                           favorable crop conditions occurred in areas with higher rainfall and vegetation cover, reflected in
                           higher evapotranspiration and lower crop-water stress, whereas northern regions exhibited high crop-
                           water stress (mean CWSI  0.975; range 0.955-0.996). Evapotranspiration showed strong positive
                           relationships with rainfall (r  0.99) and vegetation greenness (NDVI; r  0.96), and a strong negative
                           relationship with crop-water stress (r  -0.96). Land-cover change analysis revealed a 74.76% decline
                           in wetlands, a 51.50% reduction in cropland, and a 58.05% increase in built-up areas, contributing to
                           increasing thermal and hydrological stress across the basin. These findings highlight the need for
                           ecosystem restoration, climate-smart agriculture, and adaptive land-use planning to enhance agri­
                           cultural resilience and safeguard food security across the Volta Basin.

1. Introduction

    Water availability remains the biggest challenge to global agricultural sustainability, manifesting in the form of climate variability
that affects crop production levels. Evapotranspiration (ET), a critical component of the hydrologic cycle, is the rate at which water is
evaporated from the Earth's surface and transpired by plants and is a key parameter to be used in monitoring crop water usage and
soil water condition (Mu et al., 2011). Temperature and rainfall fluctuations, compounded by warming, have intensified water-
management challenges. Sub-Saharan Africa is both highly vulnerable and highly adaptable since rain-fed agriculture is pervasive
and adaptability and capacity are low (Niang et al., 2022).

    The Volta River Basin typifies vulnerability, with climatic uncertainty, land use and land cover changes, and scarcity of water
jeopardizing agriculture (Abunyewah et al., 2023; Amisigo et al., 2015). The transboundary basin supplies water for domestic use,

   Corresponding author.
     E-mail address: rachel.olawoyin@ucc.edu.gh (R. Olawoyin).

https://doi.org/10.1016/j.htopen.2026.100024

2616-6518/© 2026 The Author(s). Published by Elsevier Ltd on behalf of IWA Publishing Ltd. This is an open access article under the CC BY license
(http://creativecommons.org/licenses/by/4.0/).
R. Olawoyin, G.O. Amoah and J.A. Danquah     H2Open Journal 9 (2026) 100024

hydropower, and agriculture and sustains millions of livelihoods (Mul et al., 2023). Agriculture generates more than 60% of em­
ployment and 30% of Gross Domestic Product (GDP), yet it is highly responsive to climatic variability. In Ghana, over 24 million
individuals rely on rain-fed agriculture in the basin. Growing water scarcity and unforeseen rainfalls increase the risks of production
and rural poverty, primarily in the north (Yira et al., 2016).

    ET is a central element in regulating vegetation development, soil moisture, and irrigation efficiency, and therefore accurate ET estimation
is essential in the management of waters (Wanniarachchi & Sarukkalige, 2022). Crop moisture stress due to low rainfall and inefficient
irrigation leads to reduced output and increased vulnerability to disease and pests (Ahmad et al., 2021). Observation and tracking ET and
hydrological dynamics of a changing climate minimize the impacts and allow for optimal irrigation scheduling (Fisher et al., 2017; Zhang
et al., 2020). Water stress also has greater socio-economic impacts reduced output, lower incomes, and forced transitions to coping strategies
such as borrowing or emigration (Antwi-Agyei and Nyantakyi-Frimpong (2021). Water availability could reduce crop output by as much as
25% if water availability declines by just 10% in northern Ghana (Antwi-Agyei et al., 2015).

    Large-scale assessment of agricultural water stress and ET has become feasible due to advances in remote sensing. MODIS observations
provide imperative information on land surface temperature, vegetation index, and land-cover dynamics fundamental for the estimation of ET
and water stress detection (Li et al., 2022). However, there are no empirical research studies that well document long-term spatial and
temporal patterns in ET and crop water stress over the Volta Basin, and previous studies have been limited to localized short-term field
measurements (Ahmad et al., 2021; Zhang et al., 2020). This is a knowledge limitation regarding how land-cover modification and climate
variability influence ET and water availability simultaneously. Empirical studies confirm the utility of MODIS-ET data in irrigation perfor­
mance and water allocation, global ET trend mapping (Zhang et al., 2020), and agricultural water stress monitoring in sub-Saharan Africa
(Fisher et al. (2017); Li et al. (2022) improved ET estimation by integrating MODIS and Landsat data, resulting in enhanced accuracy for
heterogeneous cropping systems. However, few studies have applied such methods at the basin scale in the Volta Basin. ET is directly related
to plant growth and yield. Low ET is a measure of water limitation, reduced stomatal conductance, and biomass loss, and high CWSI is linked
to yield loss in maize and millet during dry spells (Leroux et al., 2019). These stressors have resulted in food insecurity over 1.5 million people
in northern Ghana were acutely food insecure in 2022 due to poor rains and crop losses (Akudugu, 2022).

    This study thus examines spatiotemporal ET and crop water stress trends for the Volta Basin (2000-2023) from MODIS data to
consolidate the impacts of land-cover change and climate variability on water yield and crop yield, with the view to facilitating
sustainable agriculture and water management.

2. Materials and methods

2.1. Study area

    The Volta Basin (Fig. 1), as a vast and extensive hydrological system, has an area of more than 400 000 km² and spans six
countries in West Africa: Ghana, Burkina Faso, Togo, Mali, Côte dIvoire, and the Benin Republic. The basin falls between latitudes
5°30N to 14°30N and longitudes 5°30W to 2°30E. Geographically, the basin stretches from the semi-arid Sahelian belt in the north
to a far more humid tropical climate in the south, with a variety of ecological and agroclimatic zones in between.

    There are two principal rainfall regimes in the region. South of latitude 7°N, the rains last from March to November and are
interrupted by a brief dry period in August-September. Late November to March is the principal dry season. In contrast, the northern
area, north of Salaga, has a unimodal rainfall regime between late May and September, with a long dry season extending up to March
or early April. There are, however, new signals of changes in rainfall timing and intensity in both basins, with the start of rainfall
becoming more unpredictable and dry periods longer, primarily as a result of climate change (World Bank, 2022).

    The distribution of annual rainfall throughout the basin is extremely irregular. The southern parts get as much as 1500 mm
annually, and the northern parts get approximately 800 mm or even lower. There is evidence of a downward trend in rainfall amount
in the northern parts and an upward trend in the frequency of severe droughts in the last two decades (Amekudzi et al., 2015; Nkiaka
et al., 2024). The hydrology of the basin is also impacted by groundwater recharge levels and major water infrastructure like the
Akosombo and Bui Dams, which are critical for hydroelectricity and irrigation. The mean annual temperatures vary from 25°C in the
south to 40°C in the north. The recent trends in temperature indicate continued warming, particularly in the dry northern regions,
where the surface temperature increased ERby about 1.5°C-2°C since 2000 (Owusu & Waylen, 2013). Geologically, the basin is
topped by Precambrian rocks overlain widely with lateritic and sandy soils, mainly in the north but not the south, which is made up of
forest-covered alluvial soils of comparatively higher organic content. Water holding capacity, soil fertility, and texture change
spatially throughout the basin, influencing agricultural productivity and crop type (Bationo et al., 2018).

    Agriculture is the prevailing land use and livelihood activity throughout the Volta Basin and employs the majority of the in­
habitants. The principal crops grown include rice, maize, millet, sorghum, and yam, and are both raised under rain-fed and irrigated
systems. All the crops have varying water needs: rice needs 900-1500 mm of water for crop development, maize needs 500-800 mm,
while millet and sorghum are quite drought-tolerant and need 300-600 mm. Consequently, the crops are extremely vulnerable to
rainfall unreliability in addition to thermal stress.

2.2. Data acquisition and processing

    This study conducted a comprehensive spatiotemporal assessment of evapotranspiration (ET) and crop-water stress (CWSI) across the
Volta Basin from 2000 to 2023 using multiple satellite-based datasets. The datasets integrated climatic, biophysical, and land-cover variables
obtained from MODIS, CHIRPS, and ESA WorldCover archives, all processed within the Google Earth Engine (GEE) environment.

                                          2
R. Olawoyin, G.O. Amoah and J.A. Danquah  H2Open Journal 9 (2026) 100024

 Fig. 1. Location map of the Volta River Basin in West Africa showing its transboundary extent across Ghana, Burkina Faso, Togo, Benin, Mali, and Côte dIvoire.

    Evapotranspiration data were derived from the MOD16A2 (Collection 6) product, which provides 8-day composites at 500-meter
spatial resolution (Mu et al., 2011). This dataset applies the Penman-Monteith algorithm, combining vegetation properties, surface
radiation, and meteorological inputs to estimate terrestrial water flux. ET values were converted from 8-day totals to millimeters per
day (mm day¹) by dividing by eight.

    Land surface temperature (LST) was obtained from the MOD11A2 product, an 8-day composite at 1-kilometre resolution (Wan
et al., 2015). LST served as a key indicator of surface energy balance and plant water stress. Vegetation greenness was characterized
using MOD13Q1, which provides 16-day composites of the Normalized Difference Vegetation Index (NDVI) at 250-meter resolution
(Chakouri et al., 2020). NDVI was used to assess vegetation vigour, photosynthetic activity, and vegetation water status.

    Rainfall data were sourced from the Climate Hazards Group Infrared Precipitation with Stations (CHIRPS) dataset, which merges
in-situ rain-gauge data with infrared satellite observations to create 0.05° (5 km) precipitation fields (Funk et al., 2015). CHIRPS
data are especially useful for drought and rainfall variability analyses in regions with sparse ground observations.

    Land-use and land-cover information were extracted from the MODIS MCD12Q1 dataset, which uses the International
Geosphere-Biosphere Programme (IGBP) classification scheme to generate annual global maps at 500 m resolution (Friedl & Sulla-
Menashe, 2019). For higher-resolution mapping, WorldCover 10 m the ESA dataset (2020-2021), derived from Sentinel-1 and
Sentinel-2 imagery, was used to validate and refine land-cover categories (ESA, 2021).

    All datasets underwent pre-processing procedures including quality assurance filtering and cloud masking within Google Earth
Engine. To ensure comparability among datasets with different spatial resolutions (e.g., MODIS ET at 500 m, LST at 1 km, NDVI at
250 m, CHIRPS rainfall at 5 km, and WorldCover at 10 m), all datasets were harmonized to a common spatial resolution of 500 m.
Continuous variables such as ET, NDVI, LST, and rainfall were resampled using bilinear interpolation, while categorical datasets such
as land-cover classes were resampled using the nearest-neighbour method to preserve class integrity. Although resampling may
introduce minor spatial smoothing effects, this approach ensures spatial consistency across datasets and is widely adopted in multi-
source remote sensing studies.

    Temporal aggregation was performed to generate monthly and annual datasets to reduce short-term variability. All data were
clipped to the Volta Basin boundary using basin shapefiles integrated into the GEE environment. Land-cover accuracy was further
validated through comparison with high-resolution Google Earth imagery and ESA WorldCover maps. Statistical analyses including
correlation, regression, and trend detection were conducted within the GEE JavaScript API, while final map visualization was per­
formed in ArcGIS Pro (v3.3), and descriptive statistics were summarized in Microsoft Excel.

                                                                                                             3
R. Olawoyin, G.O. Amoah and J.A. Danquah  H2Open Journal 9 (2026) 100024

Fig. 2. Methodological workflow illustrating data acquisition, preprocessing, analytical procedures, and outputs used for the spatiotemporal assessment of evapo­
transpiration and crop water stress in the Volta River Basin.

2.3. Crop Water Stress Index (CWSI) Estimation

    The Crop Water Stress Index (CWSI) was estimated using a land surface temperature-vegetation index (LST-NDVI) triangular
method, which relates vegetation density to surface temperature to infer crop water stress conditions. This approach exploits the
triangular distribution observed in LST-NDVI feature space, where pixels representing well-watered vegetation typically form the
lower temperature boundary, while water-stressed vegetation approaches the upper temperature boundary (Carlson & Ripley, 1997;
Sandholt et al., 2002).

    CWSI values were computed by normalizing the difference between the observed land surface temperature and the minimum
temperature boundary relative to the full temperature range within the LST-NDVI feature space. The index ranges between 0 (no
water stress) and 1 (maximum water stress), allowing spatial identification of areas experiencing vegetation moisture deficits.

    To avoid overestimation of water stress caused by bare soil pixels, the analysis was restricted to vegetated areas using NDVI
thresholds. Pixels with NDVI values below 0.2, which typically represent bare soil or sparsely vegetated surfaces common in semi-arid
environments, were excluded from the CWSI analysis. This filtering approach ensured that the calculated CWSI values represent
actual vegetation water stress rather than artefacts associated with non-vegetated surfaces.

    The LST-NDVI triangular method has been widely applied for large-scale drought and agricultural water-stress monitoring be­
cause it relies solely on satellite observations and does not require extensive ground-based meteorological measurements (Carlson &
Ripley, 1997; Sandholt et al., 2002).

3. Results

3.1. Normalized Difference Vegetation Index (NDVI) 2000-2023

    Measurement of evapotranspiration (ET) and water stress in crops in the Volta Basin necessitates knowledge of vegetation pat­
terns. NDVI, derived from MODIS, indicates that the distribution of vegetation was fairly stable from 2000 to 2010, with thicker
vegetation to the south and scattered cover to the north (Fig. 3a). NDVI varied from -0.117 to 0.766, with increased values in the

                                                                                                             4
