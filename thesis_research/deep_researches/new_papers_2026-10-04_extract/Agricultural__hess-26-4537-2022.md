# Extract: hess-26-4537-2022.pdf

*First ~4 pages, extracted with pdftotext on 2026-10-04. Source: D:\RS\Thesis\New_papers$f*

---

Hydrol. Earth Syst. Sci., 26, 4537-4552, 2022
https://doi.org/10.5194/hess-26-4537-2022
© Author(s) 2022. This work is distributed under
the Creative Commons Attribution 4.0 License.

Monitoring the combined effects of drought and salinity stress on
crops using remote sensing in the Netherlands

Wen Wen1, Joris Timmermans1,2,3, Qi Chen1, and Peter M. van Bodegom1
1Institute of Environmental Sciences (CML), Leiden University, Box 9518, 2300 RA Leiden, the Netherlands
2Institute for Biodiversity and Ecosystem Dynamics, University of Amsterdam, 1090 GE Amsterdam, the Netherlands
3Lifewatch ERIC, vLab & Innovation Centre, 1090 GE Amsterdam, the Netherlands

Correspondence: Wen Wen (w.wen@cml.leidenuniv.nl)

Received: 2 February 2022 - Discussion started: 22 February 2022
Revised: 16 August 2022 - Accepted: 17 August 2022 - Published: 13 September 2022

Abstract. Global sustainable agricultural systems are un-         possibility of potential large-scale application for sustainable
der threat, due to increasing and co-occurring drought and        food security.
salinity stresses. Combined effects of these stresses on agri-
cultural crops have traditionally been evaluated in small-        1 Introduction
scale experimental studies. Consequently, large-scale stud-
ies need to be performed to increase our understanding and        Food production is required to increase by 70 % to satisfy
assessment of the combined impacts in agricultural prac-          the growing population demand by the year 2050 (Godfray
tice in real-life scenarios. This study aims to provide a new     et al., 2010). Meanwhile, food security is becoming increas-
monitoring approach using remote-sensing observations to          ingly threatened due to the increasing abiotic stresses under
evaluate the joint impacts of drought and salinity on crop        the influence of global climate change; abiotic stresses in-
traits. In our tests over the Netherlands at large spatial scale  cluding drought, soil salinity, nutrient stress, and heavy met-
(138.74 km2), we calculated five functional traits for both       als are estimated to constrain crop productivity by 50 %-
maize and potato from Sentinel-2 observations, namely leaf        80 % (Shinozaki et al., 2015). Of these stresses, drought and
area index (LAI), the fraction of absorbed photosynthetically     salinity stress have been identified as the two main factors
active radiation (FAPAR), the fraction of vegetation cover        to limit crop growth, affecting respectively 40 % and 11 %
(FVC), leaf chlorophyll content (Cab), and leaf water con-        of the global irrigated areas (Dunn et al., 2020; FAO et al.,
tent (Cw). Individual and combined effects of the stresses on     2020). With drought and salinity forecasted to increase spa-
the seasonal dynamics in crop traits were determined using        tially and in severity (Rozema and Flowers, 2008; Schwalm
both one-way and two-way analyses of variance (ANOVAs).           et al., 2017; Trenberth et al., 2013), and with predictions of
We found that both stresses (individual and co-occurring) af-     higher co-occurrence around the world (Corwin, 2020; Jones
fected the functional traits of both crops significantly (with    and van Vliet, 2018; Wang et al., 2013), food production will
R2 ranging from 0.326 to 0.796) though with stronger sen-         be more deeply challenged by both stresses.
sitivities to drought than to salinity. While we found exacer-
bating effects within co-occurrent stresses, the impact level        Numerous small-scale experimental studies for a large va-
depended strongly on the moment in the growing season. For        riety of crops have shown that the impact of co-occurring
both crops, LAI, FAPAR, and FVC dropped the most under            drought and salinity stress is exacerbated. Co-occurrence of
severe drought stress conditions. The patterns for Cab and        drought and salinity stress is found to decrease the yield of
Cw were more inhibited by co-occurring drought and salin-         spinach (Ors and Suarez, 2017) and the forage grass Panicum
ity. Consequently, our study constitutes a way towards eval-      antidotale (Hussain et al., 2020) more compared with the oc-
uating drought and salinity impacts in agriculture, with the      currence of one of these stresses only. Likewise, cotton root
                                                                  growth tends to be more inhibited under the co-occurrence of

Published by Copernicus Publications on behalf of the European Geosciences Union.
4538                                                               W. Wen et al.: Monitoring the combined effects of drought

drought and salinity than by isolated occurrences (Zhang et        (ANOVAs) were adopted to test the main effects and the
al., 2013). Similarly, the exacerbating effect of co-occurring     interactive effect between stress combinations and time on
stresses limits both maize reproductive growth and grain for-      crop traits. Moreover, the effect of drought and salinity on
mation (Liao et al., 2022). While these studies demonstrate        crop traits was determined across the growing season with
the exacerbating effects of co-occurring drought and salinity      one-way ANOVAs. Consequently, this approach facilitates
stress, they have limitations in projecting the impact towards     the simultaneous monitoring of crop health at various scales
real farmers' conditions due to their small-scale experimental     (regional, national, and continental) across multiple stresses
nature. Thus, there is still a significant knowledge gap con-      (drought and salinity) and multiple species.
cerning the large-scale evaluation of the combined impacts
of drought and salinity.                                           2 Methodology

   Remote sensing (RS) provides a huge potential to close          To achieve our aim of monitoring the impacts of (co-
this knowledge gap due to its capability to monitor continu-       occurring) drought and salinity on agricultural production,
ous large areas at a frequent interval. For this, remote sens-     we developed a new approach to estimate crop traits from
ing has traditionally used vegetation indices, such as Nor-        remote-sensing observations. Specifically, we developed an
malized Difference Vegetation Index (NDVI) (Tucker, 1979).         approach that integrates image-processing techniques, such
However, such indices provide limited information on how           as image classification, co-registration, land surface param-
the impact is achieved (e.g., Wen et al., 2020) and how it         eter retrieval, and time-series analysis. Using these tech-
can be mitigated. With the launch of better multispectral and      niques, we were able to estimate the drought, salinity, and
high-resolution satellite sensors (such as Sentinel-2), new        crop growth.
RS methods (e.g., hyperspectral, thermal infrared, and mi-
crowave) have been identified to detect stress in both natural        To allow for a detailed evaluation, we focused on the 2018
vegetation (Gerhards et al., 2019; Vereecken et al., 2012) as      summer drought in the Netherlands. This period was selected
well as in agricultural applications (Homolova et al., 2013;       because of the extreme drought that affected a large part of
Weiss et al., 2020). Specifically, these new RS methods al-        Europe (Masante and Vogt, 2018). Within parts of the se-
low for the retrieval of plant traits that directly link to plant  lected area, salinity was reported to increase during that same
processes, such as leaf biochemistry and photosynthetic pro-       period (Broekhuizen, 2018). Hence this study area provides
cesses, and thereby provide high potential for agricultural        us with the opportunity to investigate the combined impacts
applications. RS plant traits of specific interest to monitor      of these stresses on crops. In the following paragraphs, we
crop health include leaf area index (LAI) (Wengert et al.,         provide more information on the specific processing steps.
2021), canopy chlorophyll content (Cab · LAI) (Gitelson et
al., 2005), canopy water content (Cw · LAI) (Kriston-Vizi et       2.1 Study area and data
al., 2008), the fraction of absorbed photosynthetically ac-
tive radiation (FAPAR) (Zhang et al., 2015), and the frac-         2.1.1 Drought map
tion of vegetation cover (FVC) (Yang et al., 2018). Canopy
chlorophyll content and mean leaf equivalent water thickness       A drought map of the Netherlands in 2018 was created
(EWT) of maize differed remarkably under drought stress            based on the standardized precipitation evapotranspiration
using hyperspectral remote-sensing data (Zhang and Zhou,           index (SPEI) drought index, which was calculated from
2015). Using a lookup-table approach, LAI and chlorophyll          long-term precipitation data and potential evapotranspira-
content of wheat obtained from a radiative transfer model          tion, from 2004 to 2018 (Chen et al., 2022). Specifically,
showed potential to assess drought levels (Richter et al.,         SPEI was estimated using a 3-month sliding time window,
2008). However, while there have been several attempts to          as this was found best to investigate the impacts on the lo-
monitor the response of crop health with either a drought or       cal ecosystems. We have extracted SPEI-3 data from 1 April
salinity focus, not much research has taken these factors into     to 30 October, in total 214 d, as this coincided with the crop
account simultaneously (Wen et al., 2020).                         growth period of both maize and potato. Then, the drought
                                                                   map was resampled to 250 m resolution using the nearest-
   In this study, we propose a novel approach to estimate,         neighbor interpolation and reprojected to RD_new projec-
compare, and evaluate the impacts of drought, salinity, and        tion. The RD_new projection (EPSG:28992) is a projected
their combination on crop traits using remote sensing. To al-      coordinate reference system of the Netherlands. All maps
low for a detailed evaluation of this approach, we applied         were projected to RD_new projection to create consistent
it to analyze the impacts of the 2018 summer drought in            data layers. We defined -1 and -1.5 as daily thresholds
the Netherlands on agricultural crops. In this, a stress co-       for different drought severity classes according to previous
occurrence map was created by overlaying a high-resolution         classifications (McKee et al., 1993; Tao et al., 2014). Thus,
drought map of 2018 with a groundwater salinity map. Then,         (cumulative) SPEI for no drought should be between -214
we characterized the response of maize and potato to dif-          and 0, SPEI for moderate drought should be between -321
ferent stress conditions based on five plant traits (LAI, FA-      and -214, and for severe drought, SPEI should be lower
PAR, FVC, Cab, and Cw). Two-way analyses of variance

Hydrol. Earth Syst. Sci., 26, 4537-4552, 2022                      https://doi.org/10.5194/hess-26-4537-2022
W. Wen et al.: Monitoring the combined effects of drought         4539

Figure 1. Technical workflow of the maps and data framework.

than -321 when calculated for the whole growing period            2.1.3 Crop map
(Fig. 2a).
                                                                  The crop map of the Netherlands in 2018 was collected from
2.1.2 Salinity map                                                the Key Register of Parcels (BRP) of the Netherlands En-
                                                                  terprise Agency (https://www.pdok.nl/introductie/-/article/
A topsoil salinity map of the Netherlands was created based       basisregistratie-gewaspercelen-brp-). The crop map was re-
on a nationwide fresh-salt groundwater dataset, which de-         sampled to 250 m resolution and reprojected to RD_new pro-
rived chloride concentrations as a salinity indicator (https:     jection (Fig. 2d).
//data.nhi.nu/, last access: 8 April 2021). To obtain the salin-
ity map of the topsoil, 15 layers of the groundwater salinity     2.1.4 Co-occurrence map of drought and salinity
were extracted from the 3D groundwater salinity map. For
each location, the layer closest to the location's correspond-    The drought map and the salinity map were overlain to evalu-
ing elevation (according to the digital elevation model), i.e.,   ate co-occurrences of drought and salinity of the Netherlands
closest to the soil surface, was selected. The salinity map was   in 2018 (Fig. 2c). By classifying the three stress levels for
resampled to 250 m resolution and reprojected to RD_new           the individual occurrences, we obtained nine stress classes
projection. Ultimately, the salinity map was classified into      of co-occurring drought and salinity, namely no stress, mod-
three levels, namely no salinity (0.1 to 0.8 g L-1), moderate     erate drought only (MD), severe drought only (SD), mod-
salinity (0.8 to 2.5 g L-1), and severe salinity ( 2.5 g L-1),    erate salinity only (MS), severe salinity only (SS), mod-
according to the salt-resistant capacity of various crops cul-    erate drought and moderate salinity (MD + MS), moderate
tivated in the Netherlands (Mulder et al., 2018; Stuyt, 2016)     drought and severe salinity (MD + SS), severe drought and
(Fig. 2b).                                                        moderate salinity (SD + MS), and severe drought and severe
                                                                  salinity (SD + SS).

https://doi.org/10.5194/hess-26-4537-2022                         Hydrol. Earth Syst. Sci., 26, 4537-4552, 2022
4540                                                            W. Wen et al.: Monitoring the combined effects of drought

Figure 2. Map of the Netherlands overlaying (a) drought and (b) salinity to show (c) the co-occurrence of drought and salinity in 2018. The
selected study area is indicated by black lines in panel (c). (d) The associated crop map of the study area in 2018.

2.1.5 Study area selection                                      namely no stress, MD, SD, salinity (MS + SS), MD + MS,
                                                                and MD + SS, were analyzed for the study area.
Based on the national map of the Netherlands (Fig. 2c),
a single region with similar soil type, climate, tillage sys-   2.2 Traits retrieval
tems, and irrigation methods was chosen to minimize the
interference of these factors on the observed trait expres-     2.2.1 Satellite data
sions. The province of North Holland was selected because
it contained the most (seven out of nine) combinations of       The Sentinel-2 mission consists of two satellites equipped
drought and salt stress (Fig. 2c), namely no stress, MD, SD,    with the high-resolution Multispectral Instrument (MSI) in
MS, SS, MD + MS, and SD + SS. Moreover, both maize and          the same orbit. This sensor acquires 13 spectral bands (with
potato were cultivated across all stress combinations in this   varying spatial resolutions) in the visible and near-infrared
province. For further analysis, MS and SS were grouped into     spectrum at 5 d of revisit times (ESA, 2015). In our study,
a new class of salinity stress since the area of MS and SS was  we used both the 10 and 20 m Level 2A observations,
quite limited. Therefore, six classes of stress combinations,   downloaded from the Copernicus Open Access Hub (https:
                                                                //scihub.copernicus.eu/, last access: 20 May 2021), to facil-

Hydrol. Earth Syst. Sci., 26, 4537-4552, 2022                   https://doi.org/10.5194/hess-26-4537-2022
