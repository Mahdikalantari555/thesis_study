# remotesensing-18-01420-v2.pdf

- Category: Agricultural
- Pages: 36
- Path: D:\RS\Thesis\New_papers\Agricultural\remotesensing-18-01420-v2.pdf

## Metadata

```json
{
  "/Keywords": "electrical conductivity (ECe); machine learning; hyperspectral imaging; precision agriculture",
  "/Creator": "LaTeX with hyperref",
  "/ModDate": "D:20260511094458+02'00'",
  "/Trapped": "/False",
  "/CreationDate": "D:20260511153749+08'00'",
  "/Producer": "pdfTeX-1.40.25; modified using OpenPDF 1.4.2",
  "/Subject": "Soil salinization poses a persistent threat to irrigated agroecosystems, yet remote sensing-based salinity assessment remains predominantly calibrated against bulk electrical conductivity without fully integrating crop physiological variability. This review examines the evolution of remote sensing a",
  "/PTEX.Fullbanner": "This is pdfTeX, Version 3.141592653-2.6-1.40.25 (TeX Live 2023) kpathsea version 6.3.5",
  "/Author": "Zhassulan Smanov, Jilili Abuduwaili, Alim Samat, Kanat Samarkhanov, Shakhislam Laiskhanov, Kanat Kulymbet, Azamat Yershibul, Saken Duisekov, Assiya Massakbayeva and Zhanerke Sharapkhanova",
  "/Title": "Role of Crop Salt Tolerance in Enhancing Remote Sensing-Based Soil Salinity Mapping Across Irrigated Agroecosystems: A Review"
}
```

## First pages


===== PAGE 1 =====
Academic Editor: Mohammadmehdi
Saberioon
Received: 26 February 2026
Revised: 18 April 2026
Accepted: 29 April 2026
Published: 3 May 2026
Copyright: © 2026 by the authors.
Licensee MDPI, Basel, Switzerland.
This article is an open access article
distributed under the terms and
conditions of the Creative Commons
Attribution (CC BY) license.
Review
Role of Crop Salt Tolerance in Enhancing Remote Sensing-Based
Soil Salinity Mapping Across Irrigated
Agroecosystems: A Review
Zhassulan Smanov 1, Jilili Abuduwaili 2,3,4,5
 , Alim Samat 2,3,4,5
 , Kanat Samarkhanov 6, *
 ,
Shakhislam Laiskhanov 7, Kanat Kulymbet 8
 , Azamat Yershibul 8
 , Saken Duisekov 8,9 , Assiya Massakbayeva 4,10
and Zhanerke Sharapkhanova 11
1 Center of Geospatial Sciences “Farabi GIS”, Al-Farabi Kazakh National University,
Almaty 050040, Kazakhstan
2 Key Laboratory of Ecological Safety and Sustainable Development in Arid Lands, Xinjiang Institute of
Ecology and Geography, Chinese Academy of Sciences, Urumqi 830011, China
3 Research Center for Ecology and Environment of Central Asia, Chinese Academy of Sciences,
Urumqi 830011, China
4 University of Chinese Academy of Sciences, Beijing 100049, China
5 China-Kazakhstan Joint Laboratory for Remote Sensing Technology and Application, Al-Farabi Kazakh
National University, 71/19 Al-Farabi Ave., Almaty 050040, Kazakhstan
6 Department of Physical and Economic Geography, The Institute of Natural Sciences, L.N. Gumilyov Eurasian
National University, Astana 010000, Kazakhstan
7 Department of Science and Innovation, International Educational Corporation, Almaty 050043, Kazakhstan
8 U.U. Uspanov Kazakh Research Institute of Soil Science and Agrochemistry, Almaty 050060, Kazakhstan;
qulymbet.qanat@gmail.com (K.K.)
9 Department of Soil Science, Agrochemistry and Ecology, Faculty of Agrobiology, Kazakh National Agrarian
Research University, Almaty 050010, Kazakhstan
10 State Key Laboratory of Tibetan Plateau Earth System, Environment and Resources (TPESER), Nam Co
Observation and Research Station (NAMORS), Institute of Tibetan Plateau Research, Chinese Academy of
Sciences, Beijing 100101, China
11 Laboratory of Geotourism and Geomorphology, Institute of Geography and Water Security,
Almaty 050000, Kazakhstan
* Correspondence: samarkhanov_kb@enu.kz
Highlights
What are the main findings?
• Remote sensing-based salinity mapping has achieved significant methodological
progress (multispectral, hyperspectral, machine learning, and multi-source integration)
but remains predominantly calibrated against bulk electrical conductivity without
explicit physiological embedding.
• Crop salt tolerance acts as a mediating factor within the soil–plant–spectral system,
influencing the stability, interpretation, and transferability of spectral–salinity relation-
ships in irrigated agroecosystems.
What are the implications of the main findings?
• Integrating crop-specific tolerance thresholds and root-zone processes into modeling
frameworks can improve agronomic interpretability and reduce systematic bias in
heterogeneous cropping systems.
• Transitioning from surface-oriented detection toward integrative soil–plant–water–
spectral models enhance the reliability and decision-support value of remote sensing-
based salinity assessments.
Remote Sens.2026, 18, 1420 https://doi.org/10.3390/rs18091420
===== PAGE 2 =====
Remote Sens.2026, 18, 1420 2 of 36
Abstract
Soil salinization poses a persistent threat to irrigated agroecosystems, yet remote sensing-
based salinity assessment remains predominantly calibrated against bulk electrical con-
ductivity without fully integrating crop physiological variability. This review examines
the evolution of remote sensing approaches for soil salinity mapping (1994–2024), with
particular emphasis on the role of crop salt tolerance in shaping spectral interpretation
and mapping accuracy. A systematic synthesis of 58 peer-reviewed studies retrieved from
the Scopus database was conducted using bibliometric analysis and structured full-text
thematic classification to evaluate methodological trends and conceptual integration across
soil, crops, and spectral domains. The results reveal substantial technological advancement,
including multispectral and hyperspectral sensing, machine learning frameworks, and
multi-source data integration. However, most approaches remain surface-oriented and
statistically calibrated, with limited operationalization of crop-specific tolerance thresholds,
root-zone salinity dynamics, and hydrochemical variability. The findings indicate that crop
salt tolerance functions as a mediating factor within the soil–plant–spectral continuum,
influencing the stability and transferability of spectral–salinity relationships. Integrating
physiological tolerance parameters and subsurface processes into modeling frameworks is
essential for improving agronomic interpretability and supporting more reliable salinity
management in irrigated systems.
Keywords: electrical conductivity (ECe); machine learning; hyperspectral imaging;
precision agriculture
1. Introduction
Soil salinization represents a critical challenge to irrigated agriculture, particularly
in arid and semi-arid environments where limited freshwater availability and elevated
evapotranspiration rates accelerate salt accumulation in soils. Along with widespread soil
salinization, it is called osmotic and ionic stress, weakens the process of photosynthesis,
slows down the accumulation of biomass and can lead to significant loss of productivity
of salt-sensitive crops [1,2]. Globally, salinity affects approximately one billion hectares—
equivalent to nearly 20% of all irrigated land—resulting in significant soil degradation and
yield reduction [3]. In response to these pressing concerns, remote sensing (RS) technolo-
gies, encompassing multispectral and hyperspectral platforms, have become indispensable
tools for monitoring and mapping soil salinity across field and regional scales [4–7]. The
integration of vegetation indices such as Normalized Difference Vegetation Index (NDVI),
Soil-Adjusted Vegetation Index (SAVI) and salinity indices such as Salinity Index (SI), and
Normalized Difference Salinity Index (NDSI) with machine learning (ML) algorithms,
including Random Forest (RF), Support Vector Machines (SVMs), and XGBoost, has signif-
icantly improved the reliability and precision of soil salinity classification and mapping
efforts [8–10]. Leaf area, chlorophyll levels, and changes in leaf color and structure are
sensitive to the physiological consequences of salt stress; therefore, NDVI and other related
indices are used to monitor stress in cultivated plants. Salinity results in a leaf area decrease,
chlorosis, necrosis, decreased canopy density, and disruption of water management. These
indices alter photosynthetic activity and spectral reflectance properties, and, accordingly,
these indices can be used as a proxy for determining plant responses to salt stress [1,5,7].
However, most RS approaches tend to consider the land surface as homogeneous,
neglecting critical biological variables, such as crop type and phenological stage, which
can significantly influence spectral reflectance patterns. Notably, as soil salinity intensifies,
https://doi.org/10.3390/rs18091420
===== PAGE 3 =====
Remote Sens.2026, 18, 1420 3 of 36
crop yields decline progressively, and beyond specific thresholds of crop tolerance, growth
may cease entirely [3]. Each crop possesses a unique tolerance level to salinity, and this
variability introduces challenges in accurately assessing soil salinity using vegetation
indices, as spectral responses differ depending on the crop type and its physiological state
under saline stress [11].
In addition to bulk salinity indicators such as ECe, the qualitative composition of
soluble salts and toxic ions (e.g., Cl −, SO42−, HCO3−, and CO32−) plays a decisive role
in determining both the degree of soil salinity and plant response to saline stress [ 12].
Soils with similar ECe values may exhibit markedly different agronomic and physiological
impacts depending on the ionic composition of the aqueous extract, as chloride- and
carbonate-dominated salinity is generally more phytotoxic than sulfate-based salinity due to
differences in osmotic effects, ion toxicity, and crop tolerance mechanisms [13]. Despite this
agronomic significance, most RS-based salinity mapping approaches predominantly rely on
bulk salinity proxies (e.g., ECe and spectral salinity indices) while rarely accounting for ion-
specific toxicity and salt chemistry [14,15]. This limitation introduces additional uncertainty
in spectral interpretation, particularly in irrigated agroecosystems where sodic, chloride,
and sulfate salinity types differentially influence canopy reflectance, crop physiological
tolerance, and vegetation index responses [16].
Despite the rapid advancement of RS technologies and machine learning-based salin-
ity prediction, the biological heterogeneity of cropping systems remains insufficiently
incorporated into salinity mapping frameworks [ 17]. Most RS-based models implicitly
assume uniform vegetation responses to salinity stress, overlooking crop-specific physi-
ological tolerance thresholds, commonly expressed as ECe response levels [ 18,19]. This
omission introduces systematic uncertainty in spectral interpretation, particularly in irri-
gated agroecosystems characterized by mixed cropping patterns and dynamic phenological
stages [20]. Several studies address plant stress detection and soil salinity estimation sepa-
rately [4,19,21–23], whereas explicit integration of quantitative crop tolerance parameters
into predictive salinity frameworks remains limited [24,25]. Consequently, crop response is
frequently incorporated as a spectral proxy rather than as a mechanistic mediator within
soil–plant–spectral interactions, revealing a conceptual gap that remains insufficiently
addressed within current RS-based salinity modeling frameworks [5,10].
The deliberate inclusion of crop salt tolerance terminology reflects the growing recog-
nition of salt-tolerant crops as bio-indicator species in salinity mapping and spatial risk
assessment. In RS analyses, vegetation responses, as captured through variations in canopy
reflectance and vegetation index dynamics, often reflect underlying salinity constraints
and thereby inform spectral interpretation beyond soil signal alone [26]. Several studies
demonstrate that combining vegetation canopy spectral information with crop growth
parameters (e.g., biomass, plant height, water content) significantly enhances the accuracy
of root-zone salinity estimation, particularly under vegetated conditions that obscure direct
soil reflectance [27]. Moreover, vegetation indices are commonly integrated alongside tradi-
tional salinity indices within ML and regression frameworks to improve salinity mapping
under partial canopy cover [28]. Historical evidence also indicates that the presence of halo-
phytic or salt-tolerant plant cover can serve as an indirect indicator of saline conditions in
arid and semi-arid landscapes [21]. Consequently, incorporating crop-specific salt tolerance
parameters into RS-based analyses has the potential to enhance the robustness of spatial
salinity diagnostics and improve the agronomic interpretability of RS-derived assessments.
Moreover, physiological and structural crop heterogeneity further complicates salinity
detection, as spectral responses captured by vegetation indices are strongly modulated
by canopy structure, biomass density, and stress adaptation mechanisms rather than
solely reflecting underlying soil salinity conditions. Under dense vegetation cover, the
https://doi.org/10.3390/rs18091420
===== PAGE 4 =====
Remote Sens.2026, 18, 1420 4 of 36
soil signal becomes increasingly obscured in the visible and near-infrared spectral regions,
reducing the sensitivity of salinity detection models [29,30]. Variations in canopy refl
