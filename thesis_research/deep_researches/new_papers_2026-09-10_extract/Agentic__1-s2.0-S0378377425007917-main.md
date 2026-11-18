# 1-s2.0-S0378377425007917-main.pdf

- Category: Agentic
- Pages: 16
- Path: D:\RS\Thesis\New_papers\Agentic\1-s2.0-S0378377425007917-main.pdf

## Metadata

```json
{
  "/Creator": "Elsevier",
  "/CrossMarkDomains[1]": "elsevier.com",
  "/CrossmarkMajorVersionDate": "2010-04-23",
  "/CreationDate--Text": "6th January 2026",
  "/ElsevierWebPDFSpecifications": "7.0.1",
  "/robots": "noindex",
  "/ModDate": "D:20260106162740Z",
  "/Author": "Ling Zhang",
  "/doi": "10.1016/j.agwat.2025.110077",
  "/Title": "A novel framework for pixel-wise estimation of irrigation water use by integrating remote sensing and reanalysis data",
  "/Keywords": "Irrigation water use,Remote sensing and reanalysis,Irrigation estimation model,Soil moisture,Evapotranspiration,China",
  "/CreationDate": "D:20260106161256Z",
  "/Producer": "Acrobat Distiller 8.1.0 (Windows)",
  "/Subject": "Agricultural Water Management, 323 (2026) 110077. doi:10.1016/j.agwat.2025.110077",
  "/CrossMarkDomains[2]": "sciencedirect.com",
  "/CrossmarkDomainExclusive": "true"
}
```

## First pages


===== PAGE 1 =====
A novel framework for pixel-wise estimation of irrigation water use by 
integrating remote sensing and reanalysis data
Ling Zhang
a
, Tao Che
a , *
, Kun Zhang
b
, Donghai Zheng
c
, Xin Li
c
a
Key Laboratory of Cryospheric Science and Frozen Soil Engineering, Heihe Remote Sensing Experimental Research Station, Northwest Institute of Eco-Environment and 
Resources, Chinese Academy of Sciences, Lanzhou 730000, China
b
School of Geospatial Engineering and Science, Sun Yat-Sen University, Zhuhai, China
c
National Tibetan Plateau Data Center, State Key Laboratory of Tibetan Plateau Earth System, Resource and Environment, Institute of Tibetan Plateau Research, Chinese 
Academy of Sciences, Beijing 100101, China
ARTICLE INFO
Handling Editor Xiying Zhang
Keywords:
Irrigation water use
Remote sensing and reanalysis
Irrigation estimation model
Soil moisture
Evapotranspiration
China
ABSTRACT
Accurate and spatially explicit estimates of irrigation water use (IWU) are essential for understanding the earth 
system dynamics in the Anthropocene. Recent advances in remote sensing have spurred growing interest in 
satellite-based IWU estimation. However, large-scale IWU estimates remain limited in both accuracy and spatial 
resolution due to inherent deficiencies in satellite observations and methodological constraints. Here, we present 
a novel framework for spatially explicit IWU estimation by integrating satellite-based soil moisture and evapo -
transpiration (ET) products with reanalysis data. Within this framework, we developed two alternative models: 
one based on root zone soil moisture (RSM) and the other on surface soil moisture (SSM), both grounded in soil 
water balance principles. The models estimate IWU by quantifying differences in soil moisture, ET, and drainage 
between natural and irrigated conditions. Both the RSM- and SSM-based models perform well in predicting 
prefecture-level IWU during the validation period, achieving coefficients of determination (R²) between 0.72 and 
0.90 and root mean square errors (RMSE) of 0.55 – 0.66 km³ /year, depending on the spatial scale of calibration (i. 
e., province, prefecture, or subregion). By combining our framework with different satellite products, we produce 
ensemble IWU estimates at 1 km resolution across China. The resulting dataset reveals a clear increasing trend in 
China ’ s IWU from 2001 to 2020, primarily driven by the expansion of irrigated area, while its interannual 
variability is largely controlled by fluctuations in IWU per unit irrigated area. This dataset shows a significant 
advancement in both accuracy and spatial detail over existing datasets and will be useful for irrigation-related 
research and agricultural water management in China.
1. Introduction
Irrigation mitigates crop vulnerability to drought and heat stress, 
positioning as a key strategy for climate change adaptation ( Zhu and 
Burney, 2022; Zhu et al., 2022; Driscoll et al., 2024 ). It plays a pivotal 
role in ensuring global food security ( Zaveri and B. Lobell, 2019; Wang 
et al., 2021 ), contributing to 40 % of the world ’ s food supply while 
occupying only 20 % of global croplands ( UNESCO World Water 
Assessment Programme, 2019 ). Globally, irrigation is the largest con -
sumer of freshwater, accounting for ~70 % of total water withdrawals 
and ~90 % of consumptive water use ( Siebert and D ¨oll, 2010; Qin et al., 
2019 ). Over the past two decades, the area equipped for irrigation has 
expanded by 11 % globally, driving substantial gains in crop 
productivity ( Mehta et al., 2024 ). However, the widespread use of irri -
gation has far-reaching impacts on the earth system, including alter -
ations to the surface energy balance, hydrological processes, and 
biogeochemical cycles, while simultaneously placing increasing pres -
sure on freshwater resources ( McDermid et al., 2023; Yang et al., 2023; 
Driscoll et al., 2024; Qin et al., 2024 ). Given irrigation ’ s central role in 
both food production and Earth system dynamics, there is a pressing 
need to understand the spatiotemporal patterns of irrigation water use 
(IWU).
IWU is a broad term that may refer to total irrigation water with -
drawals (from rivers, reservoirs, or aquifers), field-level irrigation water 
applications, or consumptive irrigation water use through evapotrans -
piration. Numerous efforts have been made to estimate IWU, which can 
* Corresponding author.
E-mail address: chetao@lzb.ac.cn (T. Che). 
Contents lists available at ScienceDirect
Agricultural Water Management
journal homepag e: www.el sevier.com/loc ate/agwa t
https://doi.org/10.1016/j.agwat.2025.110077
Received 29 August 2025; Received in revised form 5 November 2025; Accepted 9 December 2025  
Agricultural Water Management 323 (2026) 110077 
Available online 13 December 2025 
0378-3774/© 2025 The Authors. Published by Elsevier B.V. This is an open access article under the CC BY-NC-ND license ( http://creativecommons.org/licenses/by- 
nc-nd/4.0/ ). 
===== PAGE 2 =====
be broadly categorized into three main approaches: physical modeling, 
machine learning, and remote sensing. Physical modeling estimates IWU 
using process-based models such as hydrological, land surface, or crop 
models ( D ¨oll and Siebert, 2002; J ¨agermeyr et al., 2015; Huang et al., 
2020; Yin et al., 2020b; Zhou et al., 2020b; Han et al., 2023 ). While these 
models can produce IWU estimates at high spatial and temporal reso -
lution, they often suffer considerable uncertainty arising from over -
simplified or inconsistent representations of irrigation processes and the 
limited availability of direct IWU observations for model calibration ( Hu 
et al., 2016; Chen et al., 2019; Foster et al., 2019; Zaussinger et al., 2019; 
Koch et al., 2020 ). In contrast, machine learning (ML) techniques do not 
require predefined physical assumptions and are particularly effective at 
capturing complex interactions and nonlinear relationships between 
IWU and its controlling factors ( Wongso et al., 2020; Bhattarai et al., 
2021; Zhang et al., 2022c; Lu et al., 2023; Alkon and Wang, 2024 ). This 
makes ML a promising alternative to physical models for IWU estimation 
( Majumdar et al., 2020, 2022; Filippelli et al., 2022; Bo et al., 2024; Ott 
et al., 2024 ). However, ML approaches are often criticized for their 
“ black box ” nature ( Ma et al., 2023; Jung et al., 2024 ), and their pre -
dictive performance depends greatly on the quantity and quality of the 
training data. Given that IWU observations are unavailable in many 
regions due to technical, economic, or political constraints ( Foster et al., 
2020 ), the application of ML methods for IWU estimation remains 
challenging.
Remote sensing techniques have advanced considerably over the 
past few decades, making it increasingly feasible to estimate IWU from 
space ( Zhang et al., 2022a; Dari et al., 2023a ). Leveraging satellite ob -
servations and hydrological principles, remote sensing-based IWU esti -
mation has emerged as a rapidly growing area of research across both 
the remote sensing and hydrology communities ( Foster et al., 2020; 
Brookfield et al., 2023 ). Existing remote sensing approaches to IWU 
estimation can be classified into two main categories: soil 
moisture-based and evapotranspiration (ET)-based methods ( Dari et al., 
2023b; Kragh et al., 2023a ).
Soil moisture-based approach approaches estimate IWU by detecting 
irrigation-induced changes in soil moisture ( Zaussinger et al., 2019; 
Zohaib and Choi, 2020 ) or by applying soil water balance frameworks 
such as the Soil Moisture to Rain (SM2RAIN) algorithm that conceptu -
alize irrigation as an equivalent to rainfall ( Brocca et al., 2013, 2018 ). 
These methods have been successfully applied across a wide range of 
spatial scales, from field to global levels ( Filippucci et al., 2020; Dari 
et al., 2022, 2023b; Zhang et al., 2022a ). However, soil moisture-based 
approaches generally require high-temporal-resolution soil moisture 
data and often produce IWU estimates at coarse spatial resolutions, with 
a tendency to underestimate actual IWU ( Zhang and Long, 2021 ). These 
limitations primarily arise from the inherent shortcomings of satellite 
soil moisture products (e.g., low spatial resolution, data gaps) and the 
shortcomings of estimation algorithms. Another strand of soil 
moisture-based methods estimates irrigation by assimilating 
satellite-derived soil moisture into land surface models equipped with 
irrigation modules ( Abolafia Rosenzweig et al., 2019; Jalilvand et al., 
2023; Busschaert et al., 2024; Laluet et al., 2024 ). While effective at 
local scales, the applicability of these data assimilation approaches to 
larger regions remains limited, as they typically require extensive cali -
bration against in situ measurements and are sensitive to regional het -
erogeneity in irrigation practices, making them both time-consuming 
and computationally intensive ( Majumdar et al., 2020; Olivera-Guerra 
et al., 2023 ).
In contrast, ET-based approaches estimate irrigation by analyzing 
residuals between satellite-derived ET and baseline values obtained 
either from hydrological or land surface models under rainfed condi -
tions, or from hydrologically similar neighboring pixels ( Cheema et al., 
2014; van Eekelen et al., 2015; Pe ˜na-Arancibia et al., 2016; Chen et al., 
2019; Koch et al., 2020; Yin et al., 2020a; Brombacher et al., 2022; Boser 
et al., 2024 ). Compared with soil moisture-based methods, ET-based 
approaches offer notable advantages, particularly in enabling IWU 
estimation at finer spatial resolutions — ranging from 30 m to 1 km ( Koch 
et al., 2020; Boser et al., 2024 ). Furthermore, ET is directly linked to 
plant transpiration in response to irrigation, whereas soil moisture 
provides only an indirect estimate ( Kragh et al., 2023a, 2023b ). How -
ever, ET-based methods typically neglect irrigation-induced changes in 
soil moisture and subsurface drainage, thereby quantifying only the 
consumptive component of water use rather than the total irrigation 
water applied or withdrawn ( Laluet et al., 2024 ). This limitation com -
plicates validation efforts, as consumptive use cannot be directly 
measured ( Zhang et al., 2022c ). In practice, consumptive water use is 
often converted to actual IWU using irrigation efficiency, yet this 
parameter is difficult to determine accurately at fine spatial scales, 
introducing substantial uncertainty ( Puy and Lankford, 2022 ). An 
alternative strategy is to calibrate hydrological or soil water balance 
models against satellite-derived ET and estimate IWU inversely through 
embedded irrigation modules. However, this inverse modeling approach 
is computationally expensive, especially when applied at national or 
global scales; and meanwhile, the results are highly sensitive to model 
assumptions on irrigation process.
Despite considerable progress in satellite-based IWU estimation, 
several limitations remain. First, although many studies have demon -
strated promising performance at local or basin scales, few have tested 
the transferability of their models across broader spatial domains, 
resulting in a scarcity of publicly available, remotely sensing-derived 
IWU datasets ( Dari et al., 2023b ). Existing global-scale IWU products 
are typically characterized by coarse spatial resolution (e.g., 0.25
◦
) and 
limited accuracy ( Chen et al., 2019; Zhang et al., 2022a ), which restrict 
their applicability for regional or local-scale analyses. Second, neither 
soil moisture nor ET al.one can fully capture irrigation inputs. Recent 
studies have highlighted the advantages of jointly using soil moisture 
and ET for IWU estimation ( Zhang and Long, 2021; Kragh et al., 2023a ), 
yet most existing approaches exclusively on one of these variables 
( Supplementary Table S1 ). Third, few studies have compared their IWU 
estimation approaches against 
