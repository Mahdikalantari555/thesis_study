# Extract: PST-ePrint-13057-article.pdf

*First ~4 pages, extracted with pdftotext on 2026-10-04. Source: D:\RS\Thesis\New_papers$f*

---

PLANT SCIENCE TODAY                                                                               eISSN 2348-1900
Vol 13(sp2): 1-18
https://doi.org/10.14719/pst.13057

REVIEW ARTICLE

 Recent trends in crop water stress monitoring using remote
                    sensing technologies: A review

S Gokul1, V Manivannan1*, K Thirukumaran1, P Boominathan2, R Jagadeeswaran3, R Raja4, G Prabukumar1,
                                                        M Asritha1 & K Surya1

   1Department of Agronomy, Agricultural College and Research Institute, Tamil Nadu Agricultural University, Coimbatore 641 003,Tamil Nadu, India
2Department of Crop Physiology, Agricultural College and Research Institute, Tamil Nadu Agricultural University, Coimbatore 641 003, Tamil Nadu, India

      3Department of Remote Sensing and GIS, Agricultural College and Research Institute, Tamil Nadu Agricultural University, Coimbatore 641 003,
                                                                                   Tamil Nadu, India

                           4ICAR-Central Institute for Cotton Research (CICR), Regional Station, Coimbatore 641 003, Tamil Nadu, India

*Correspondence email - manivannanv@tnau.ac.in

Received: 04 December 2025; Accepted: 10 April 2026; Available online: Version 1.0: 04 June 2026

Cite this article: Gokul S, Manivannan V, Thirukumaran K, Boominathan P, Jagadeeswaran R, Raja R, Prabukumar G, Asritha M, Surya K. Recent
           trends in crop water stress monitoring using remote sensing technologies: A review. Plant Science Today. 2026; 13(sp2): 1-18.
                                                                    https://doi.org/10.14719/pst.13057

Abstract

Unmanned aerial vehicle (UAV) based remote sensing has emerged as a disruptive technology for detecting crop water stress (CWS) in real time,
precisely and at low cost offering significant advancements over conventional approaches. The study examined the red green blue (RGB),
multispectral (MSP), hyperspectral (HSP), thermal image sensors integrated with UAVs, which offers a high-spatial and temporal resolution of
physiological indicators such as chlorophyll content and canopy cover, canopy temperature, stomatal conductance. The study highlights that in
spring maize, random forest (RF) models using UAV-derived MSP and thermal indices with leaf area index (LAI) performed well (R² > 0.575, root
mean square error (RMSE) < 0.073) with accurate detection of crop water content at the 9th leaf and milking stages, as well as stomatal
conductance at tasseling and silking stages. Combining UAV-derived spectral and textural features enhanced model accuracy in cotton, with
extreme gradient boosting (XGBoost) showing the highest performance for canopy equivalent water thickness (CEWT) (R² = 0.75) and crop water
stress index (CWSI) (R² = 0.90). Despite significant advances, problems remain in standardising data acquisition procedures, decreasing
fluctuations due to environmental variability and combining UAV-derived data into reliable decision-support systems for precise irrigation
management. The review emphasises key research gaps, such as the demand for strong cross-regional validation, real-time monitoring and the
development of compatible systems linking UAV imagery data with ground sensors and crop models. Overall, advances in UAV-based remote
sensing technology are altering crop water stress (CWS) detection, creating new potential to enhance agricultural resilience, boost resource-
efficient management and focusing on increasing concerns with respect to climate-induced water stress.

Keywords: canopy temperature; multispectral; spectral indices; thermal sensor; unmanned aerial vehicle

Introduction                                                             processes of crops, significantly impacting crop production and
                                                                         quality (6). A lack of water availability causes physiological and
The global population is anticipated to reach almost 10 billion by       biochemical alterations that affect photosynthetic rate and
2050 (1). As a result, food production must increase rapidly in the      development processes, indicating crop water stress (CWS) (7).
face of input shortages (water), climatic uncertainty and                Crops subjected to moisture stress result in stomatal closure, which
environmental sustainability (2). At present, 80-90 % of the             lowers transpiration and evaporation, resulting in increased canopy
freshwater resource is used globally in agriculture and roughly two-     temperature. Leaf temperature, stomatal conductance, soil
third of the freshwater is used for agricultural irrigation (3). In      moisture content, canopy water content and evapotranspiration
contrast, the availability of agricultural water supplies is being       (ET) are some of the biochemical and biophysical metrics identified
threatened by climate change, raising global water shortages,            as possible indicators of crop water status (8). A change in irrigation
frequent dry spells and global warming. The world's dryland area         frequency is expected to result in a 10-27 % reduction in maize
has grown substantially over the past decade and there has been a        yield (9). Conventional techniques for assessing agricultural water
significant increase in the frequency, possibility and extent of         stress include measuring the soil moisture content, examining
droughts. As a result, there has been a $30 billion global loss in crop  meteorological factors and monitoring various physiological
production (4).                                                          indicators, including stomatal conductivity and water potential (10).
                                                                         Even though these techniques can provide precise information
        Plant abiotic stress, which includes water stress, generally     regarding the degree of CWS, they are destructive, time-consuming
referred to as drought stress, poses a major constraint for crop         and labour-intensive (11).
production if it persists for a prolonged period (5). Water stress
negatively affects the physiological growth and developmental

                                    Plant Science Today, ISSN 2348-1900 (online)
GOKUL ET AL                                                                                                                               2

        To overcome these restrictions, quick and non-destructive          CWS evaluation methods is essential for effective irrigation control
CWS sensors have been developed. For rapid acquisition of digital          and eliminating irrelevant crop stress (20).
data, remote sensing is combined with a variety of optical sensors
like red green blue (RGB), multispectral (MSP), hyperspectral (HSP)        Different methods of crop water stress assessment
and thermal images. The platforms are employed using satellites,
airplanes, unmanned aerial vehicles (UAVs) and handheld devices.           Ground-truth measurements
Artificial intelligence (AI) systems can be used to analyse these digital
data and assess the physical and chemical characteristics of crops         Soil-based approaches: Traditional soil-based methods for
(12). Crop classification, yield forecasting, disease and pest             detecting CWS rely on in situ soil moisture assessment and
identification and management and CWS assessment all have been             atmospheric variables to evaluate the loss of moisture from the soil-
performed using remote sensing technology (13-16). Recently, UAVs          plant system (21). Different methods based on soil analysis are
evolved into modern field phenotyping platforms supplying high             summarised in Table 1.
spatio-temporal resolution data for crop water status monitoring
and are less expensive, flexible and less dependent on climatic            Table 1. Various soil-based approaches for detecting crop water
factors (17).                                                              stress

        Despite rapid developments in remote sensing technologies          Technique           Advantages Disadvantages                   Reference
for estimating CWS, current studies are scattered across multiple
crucial aspects. Most prior studies typically focus on single-sensor       Direct method                                                      (22)
techniques, such as MSP or HSP data and thermal and were limited
to specific methodological frameworks, unable to provide an                Gravimetric         Very accurate Slow, destructive,               (23)
integrated representation across platforms. Additionally, there is a                                                    lab needed            (24)
distinct gap in the detailed analysis on the integrated use of UAV-                                                                           (25)
based high-resolution data and satellite observations, notably for         Indirect methods                                                   (26)
large-scale stress monitoring under various agro-climatic conditions.                                                                         (27)
Furthermore, recent advances in machine learning (ML) and AI               Neutron scattering    Accurate, fast        Costly, not for        (28)
approaches for CWS monitoring have not been extensively                                                                 shallow soil,         (29)
investigated in conjunction with conventional biophysical and              Gamma-ray           High resolution
spectral indices. In addition, important operational limitations like as   Time domain                                    radiation
data fusion, scalability, cost-effectiveness and real-time applicability   reflectometry         Stable, non-
in precision irrigation management have received inadequate                Capacitance              invasive             Expensive,
critical attention.                                                        sensor                                         hazardous
                                                                           Frequency domain     Cheaper, site-
        In order to address these gaps, the current review delivers an     reflectometry            specific          Costly, errors in
extensive analysis of the recent trends in CWS assessment using            Tensiometer                                 saline/wet soil
remote sensing technologies, integrating findings from MSP, HSP                                Better in dry soil,
and thermal sensing platforms, including satellite and UAV-based           Resistive (Gypsum)        precise          Needs frequent
systems. To assesses the role of recent analytical methodologies,                                                        calibration
such as ML and data-driven models, while also aiming at the multi-                             Cheap, good for
scale feasibility and constraints of existing techniques. The paper                                deep soil        Less accurate when
also identifies significant research gaps and provides future                                                         wet, calibration
prospective for establishing strong, scalable and decision-support                               Very low cost
frameworks for precision agriculture.                                                                                Limited range, not
                                                                                                                     for dry/saline soil
Importance of crop water stress assessment
                                                                                                                       Low accuracy,
                                                                                                                    frequent calibration

                                                                           Evapotranspiration-based measures: Evapotranspiration based
                                                                           measures play a crucial role in monitoring CWS and its relationship
                                                                           with yield. Various indicators, including precipitation, soil moisture,
                                                                           vegetation indices like normalised difference vegetation index (NDVI)
                                                                           and ET, are employed to quantify CWS. Initially, a significant
                                                                           correlation between crop production and the ratio of actual to
                                                                           reference ET (fRET) was demonstrated, which serves as a substitute
                                                                           for water stress (30). Later, established a correlation between relative
                                                                           yield losses and water stress at different phases of crop growth (31).

                                                                           Plant based approaches

                                                                           Plant based approaches for detecting CWS are often more
                                                                           susceptible than soil moisture content techniques. Several plant-
                                                                           based measures are outlined in Table 2.

                                                                            Table 2. Plant-based methods for evaluating crop water stress

Drought stress is a critical abiotic stress that induces dehydration in    Approach       Method Advantages Disadvantages Reference
plants, preventing cells from maintaining acceptable water
concentrations, which ultimately limiting plant growth and crop            Stem water Pressure Accurate, Laborious,
production (18). Therefore, assessing CWS is essential for optimising      potential chamber, non good for discrete data, (32)
crop production, particularly through precision irrigation (19). The                      -transpiring drought
availability of timely irrigation information is vital in agriculture for  ( stem)             leaf  studies time-consuming
enhancing the crop yield but also contributes to ensuring food
security. Detailed studies of crop responses to water stress are                                     Direct water
required to determine drought-tolerant crop species and maintain
the ideal balance between irrigation and yield.                            Relative                  status, Destructive,
                                                                           water content Fresh/dry scalable with intensive                (33)
        Crop water stress (CWS) assessment plays a major role in           (RWC)          weight ratio remote       sampling
defining the environmental interaction of crops and is critical for                                  sensing
effective irrigation scheduling (10). By enabling early identification
and adequate measures routine water stress monitoring can reduce           Leaf water     Scholander Good for Affected by
the risk of economic loss. Further, to minimise yield loss and respond     potential                 stress environment, (34)
with proper agrotechnical solutions, it is essential to evaluate CWS       ( leaf)        chamber    detection time-consuming
before the occurrence of unrecoverable damage. Understanding
                                                                                                     Indicates gas
                                                                           Stomatal                  exchange,      Costly,
                                                                           conductance Infrared scalable with individual leaf (35)
                                                                           (Gs)           porometer remote data, needs skill
                                                                                                     sensing

                                                                                          Thermal                   Complex,
                                                                                          sensors Real-time, expensive,
                                                                           Sap flow     measure sap irrigation influenced by (36)

                                                                                               rate  planning       temp.

             https://plantsciencetoday.online
                                                                                                                                                                        3

Canopy temperature: Canopy temperature has been widely                    landscape levels (40). These indices have been applied to estimate
studied as an indicator of plant water stress. It can be measured         CWS in various crops, including wheat, cotton and maize (41-43).
using thermal imagery or infrared thermometers (37, 38). The              Structure, chlorophyll, lutein and moisture indices are the four main
significance of foliar temperature variations in detecting water deficit  categories of vegetation indices (VI) (44). Structure indices like NDVI,
was established, highlighting the complex relationship between            renormalised difference vegetation index (RDVI) and soil-adjusted
foliar temperature, moisture availability and plant water status (21).    vegetation index (SAVI), are frequently employed to monitor
Infrared thermal images can derive canopy temperature, which has          vegetative cover and canopy structure, both of which are
been found to correlate well with stomatal conductance (39) and           significantly influenced by water stress (45). Chlorophyll indices,
stem water potential (40). However, accurately isolating leaf             including the transformed chlorophyll absorption in reflectance
temperature from the full image is essential to avoid erroneous           index (TCARI) and optimised SAVI combinations, are especially
estimates of canopy temperature due to non-leaf material (39). The        useful for detecting water stress since chlorophyll content declines
measurement of canopy temperature is based on the principle that          under water-limited conditions. The various VIs are presented in
leaf temperature is influenced by transpiration rates, which are in       Table 3. These indices effectively track physiological changes due to
turn governed by stomatal conductance. A decrease in plant water          water stress, particularly in crops like maize, where TCARI/RDVI and
status leads to a reduction in transpiration due to stomatal closure,     TCARI/SAVI combinations showed strong correlations with crop
which increases in leaf temperature. However, relying solely on           water stress index (CWSI) resulting in R² values of 0.47 and 0.50 at
canopy temperature as a proxy for plant water stress has limitations.     reproductive and final stages, respectively and 0.81 and 0.80 for
It cannot directly estimate the physiological status of crops under       TCARI/RDVI and TCARI/SAVI at the late reproductive and final stages,
varying conditions.                                                       respectively (17).

Vegetation indices for crop water stress monitoring                       Crop water stress index

Vegetation indices (VIs) are increasingly utilised for monitoring crop    An important factor of crop-atmospheric interactions, CWS is "an
water levels and enhancing irrigation schedules at the canopy and         index of water stress using leaf scale and plant temperature analysis

Table 3. Detection of plant water stress utilising reflectance indices

Spectral indices                       Formula                                           Crop stress indicators References

reflectance index (TCARI) Transformed chlorophyll absorption in 3 [(R700 - R670) - 0.2(R700 - R7550) × (R700/R670)] stomatal conductance Leaf water potential and (46)

Optimised soil adjusted vegetation             (1+0.16) (R700 - R 550)                   Stomatal conductance,  (46)
index (OSAVI)                                   (R800 + R670) + 0.16                     leaf water potential
Normalised difference vegetation
(NDVI)                                                R800 - R 670                       Stomatal conductance,  (47)
Photochemical reflectance index (PRI)                 R800 + R 670                       leaf water potential
Renormalised difference vegetation                     R570 - R531
index (RDVI)                                           R570 + R 531                      Chlorophyll fluorescence, stomatal conductance (48)
Normalised photochemical reflectance
index (NPRI)                                            R800 - R670                      Stomatal conductance, leaf water potential (49)
                                                         R800 - R670
OSAVI/TCARI                                                                              Stomatal conductance, (50)
                                                            PRI                          chlorophyll fluorescence
                                                        RDI × R700
                                                                                         Stomatal conductance,  (46)
                                                               R670                      leaf water potential
                                                                                   R700

                                       3(R700 - R670) - 0.2(R700 - R550) ×
                                                                                   R670

                                                   (1 + 0.16)(R700 - R550)
                                                     (R800 + R670) + 0316

Simple ratio water index (SRWI)        R860                                              Leaf water potential   (51)
                                       R1240

Water index (WI)                                 R860                                    Leaf water potential   (51)
Normalised difference water index               R1240
(NDWI)                                                                                   Leaf water potential   (52)
                                            R860 - R1240
                                           R860 + R 1240

                                       Plant Science Today, ISSN 2348-1900 (online)
GOKUL ET AL                                                               4

approaches" and is essential for efficient irrigation. To measure the   infrared (TIR) sensors using ground vehicles, satellites and UAV. Red
water deficit level of crops utilising canopy temperature (Tc), air     green blue sensors collect the visible spectrum, whereas MSP and
temperature (Ta) and vapor pressure deficit (VPD). The empirical        HSP sensors acquire infrared bands for more detailed plant analysis
CWSI was initially proposed and followed by the development of          (63, 64). Infrared cameras are particularly useful for determining water
theoretical method for calculating the CWSI based on upper and          stress by measuring Tc and transpiration rates (65).
lower limits (Tsmax and Tsmin) by combining formulas of the
Penman-Monteith and energy balance theory (53, 54). However, the                These technologies facilitate data collection without direct
application of this method may be limited due to the number of          physical interaction, enabling precise crop temperature
parameters required for obtaining the CWSI baseline. Previous study     measurements and specific information crucial for irrigation
suggested a method that uses wet and dry reference surfaces to          scheduling (66). Remote sensing systems, which include both
make estimation simple (Eqn. 1) (55).                                   active (backscatter-based) and passive (reflectance-based)
                                                                        sensors, are deployed on various platforms such as ground
             CWSI =         Tc - Twet   (Eqn. 1)                        vehicles, satellites and aircraft (67). Radio detection and ranging
                           Tdry - Twet                                  (RADAR) and light detection and ranging (LiDAR) are examples of
                                                                        active sensors, whereas affordable RGB, MSP, HSP and TIR are
where, Tc = Canopy temperature, Twet = Temperature of a                 examples of passive sensors (68). Remote sensing techniques, by
                                                                        examining regions of the electromagnetic spectrum including
well-watered leaf, Tdry = Temperature of a leaf with fully closed       ultraviolet (10-380 nm), visible (400-700 nm) and near-infrared
                                                                        spectra (850-1700 nm), provide indirect indicators of water stress
stomata.                                                                through leaf biochemical attributes (69). This technology is
                                                                        especially effective for monitoring drought stress and provides
        The CWSI index ranges from 0-1, where 0 or lower baselines      early detection for efficient irrigation scheduling and scaling
indicate no stress and plant transpiration at its maximum rate, while   information from the leaf to the field level (40).
1 or upper baselines indicate severe water stress (56). To get around
this constraint, the hybrid CWSI an empirical upper limit coupled       Ground-truth measurements
with a theoretical lower limit has been proposed as a way to lower
the demand for complex atmospheric observations with greater            Infrared thermometer: An efficient technique for determining
accuracy.                                                               specific plant water stress, infrared thermometry is frequently used
                                                                        to schedule irrigation for a wide range of crops. This approach,
Additionally, the water deficit index (WDI), derived from the           which focuses on Tc measurement was demonstrated earlier and
                                                                        further studies have used spectral indices based on Tc and its
CWSI, uses similar principles but is specifically designed to account   variation to detect CWS (21, 70, 71). Water stressed and non-water
                                                                        stressed baselines for irrigated maize in Colorado, USA, were
for composite plant-soil surfaces under various micrometeorological     established by combining infrared thermometry with
                                                                        relevant meteorological data (72).
conditions (Eqn. 2) (57).
                                                                                Canopy temperature is precisely estimated by infrared
             WDI = 1- Eact              (Eqn. 2)                        sensors since they can detect emitted radiation. This makes it a
                                                                        valuable tool for assessing crop water status (73). The SI-111 infrared
                           Epot                                         radiometer (IRR) sensor, which measures surface temperature by
                                                                        converting thermal energy from surfaces, is commonly used for this
        where, Eact = Actual latent heat flux density and Epot =        purpose, offering a measurement range from - 60-110 °C, with a
Potential latent heat flux density.                                     manufacturer accuracy of ± 0.5 ° C (74).

        Recent works have reviewed alternative indices based on                 Infrared thermography has been employed for quantitative
infrared thermometers that involve lower data than CWSI for             estimation of crop stress using both index-based and physically
predicting CWS. The canopy temperature ratio (Tc ratio) measured        based approaches. One common method to quantify water stress is
over completely irrigated and water-deficit can serve as alternate for  the CWSI derived from infrared thermometry (54, 75). This technique
the water stress coefficient (Ks) used in the reference ET-crop         has been used successfully for satellite and drone-based remote
coefficient (58). The results indicate that the Tc ratio is a suitable  sensing applications.
empirical measure of Ks for assessing crop ET under water deficit
conditions and facilitates the application of crop coefficient method   Satellite-based remote sensing
for scheduling deficit irrigation. Deficit-irrigated sunflowers grown
under arid/semi-arid conditions responded well to irrigation            The solar or optical-spectral domain of the electromagnetic range
scheduling and water stress monitoring using Tc based the degrees       (0.4-2.5 µm; visible and near infrared (VNIR)/shortwave infrared
above non-stressed (DANS) approach (59). In addition, a single          (SWIR)) has been the primary focus of remote sensing of vegetation
measurement Tc metric degree above canopy threshold (DACT)              for the past 40 years. Various MSP and HSP cameras have been
was used for detecting water stress in maize (60). Among four           developed as a result of this approach and are currently being
thermal remote sensing indices-based approaches (CWSI, DANS,            utilised on the ground (like ASD FieldSpec and Spectral Evolution
DACT and Tc ratio), DANS and DACT are sensitive to CWS as               PSR+), in the air (such as AVIRIS, HyMap, HySpex and Aisa FENIX)
compared to CWSI, although it requires more data for computing          and space (such as Landsat, SPOT, MODIS, IKONOS and
crop ET coefficients (61).                                              HYPERION). These optical-reflective systems depend on the
                                                                        spectral reflectance characteristics of plant leaves, the canopy and
Remote sensing approaches for assessing crop water stress               the soil background (76).

Remote sensing provides a time-efficient, non-destructive and
precise method for assessing CWS, addressing the challenges of
traditional field measurements, which are labour-intensive and
disruptive (62). It offers insights into spatial and temporal crop
variability, enabling more comprehensive analysis and forecasting.
Crop water stress is mostly assessed with RGB, HSP, MSP and thermal

                                        https://plantsciencetoday.online
