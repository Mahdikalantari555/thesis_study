# remotesensing-11-01240.pdf

- Category: Agricultural
- Pages: 24
- Path: D:\RS\Thesis\New_papers\Agricultural\remotesensing-11-01240.pdf

## Metadata

```json
{
  "/Author": "Max Gerhards, Martin Schlerf, Kaniska Mallick and Thomas Udelhoven",
  "/Title": "Challenges and Future Perspectives of Multi-/Hyperspectral Thermal Infrared Remote Sensing for Crop Water-Stress Detection: A Review",
  "/Subject": "Thermal infrared (TIR) multi-/hyperspectral and sun-induced fluorescence (SIF) approaches together with classic solar-reflective (visible, near-, and shortwave infrared reflectance (VNIR)/SWIR) hyperspectral remote sensing form the latest state-of-the-art techniques for the detection of crop water s",
  "/Creator": "LaTeX with hyperref package",
  "/Producer": "pdfTeX-1.40.18",
  "/Keywords": "remote sensing; thermal infrared (TIR); water stress; crop stress; evapotranspiration (ET) modeling; emissivity; temperature; drought; water use",
  "/CreationDate": "D:20190524174230+08'00'",
  "/ModDate": "D:20190524174230+08'00'",
  "/Trapped": "/False",
  "/PTEX.Fullbanner": "This is pdfTeX, Version 3.14159265-2.6-1.40.18 (TeX Live 2017/W32TeX) kpathsea version 6.2.3"
}
```

## First pages


===== PAGE 1 =====
remote sensing  
Review
Challenges and Future Perspectives of
Multi-/Hyperspectral Thermal Infrared Remote
Sensing for Crop Water-Stress Detection: A Review
Max Gerhards 1,2, *
 , Martin Schlerf 2, Kaniska Mallick 2
 and Thomas Udelhoven 1
1 University of Trier, Faculty of Geography and Geosciences, Department of Environmental Remote Sensing &
Geoinformatics, Behringstrasse, D-54296 Trier, Germany; udelhoven@uni-trier.de
2 Luxembourg Institute of Science and Technology (LIST), Environmental Research and Innovation (ERIN)
Department, 41 Rue du Brill, L-4422 Belvaux, Luxembourg; martin.schlerf@list.lu (M.S.);
kaniska.mallick@list.lu (K.M.)
* Correspondence: gerhardsm@uni-trier.de or max.gerhards@yahoo.de
Received: 16 April 2019; Accepted: 17 May 2019; Published: 24 May 2019
/gid00030/gid00035/gid00032/gid00030/gid00038/gid00001/gid00033/gid00042/gid00045/gid00001
/gid00048/gid00043/gid00031/gid00028/gid00047/gid00032/gid00046
Abstract: Thermal infrared (TIR) multi-/hyperspectral and sun-induced ﬂuorescence (SIF) approaches
together with classic solar-reﬂective (visible, near-, and shortwave infrared reﬂectance (VNIR)/SWIR)
hyperspectral remote sensing form the latest state-of-the-art techniques for the detection of crop
water stress. Each of these three domains requires dedicated sensor technology currently in place
for ground and airborne applications and either have satellite concepts under development (e.g.,
HySPIRI/SBG (Surface Biology and Geology), Sentinel-8, HiTeSEM in the TIR) or are subject to
satellite missions recently launched or scheduled within the next years (i.e., EnMAP and PRISMA
(PRecursore IperSpettrale della Missione Applicativa, launched on March 2019) in the VNIR/SWIR,
Fluorescence Explorer (FLEX) in the SIF). Identiﬁcation of plant water stress or drought is of utmost
importance to guarantee global water and food supply. Therefore, knowledge of crop water status
over large farmland areas bears large potential for optimizing agricultural water use. As plant
responses to water stress are numerous and complex, their physiological consequences a ﬀect the
electromagnetic signal in diﬀerent spectral domains. This review paper summarizes the importance of
water stress-related applications and the plant responses to water stress, followed by a concise review
of water-stress detection through remote sensing, focusing on TIR without neglecting the comparison
to other spectral domains (i.e., VNIR /SWIR and SIF) and multi-sensor approaches. Current and
planned sensors at ground, airborne, and satellite level for the TIR as well as a selection of commonly
used indices and approaches for water-stress detection using the main multi-/hyperspectral remote
sensing imaging techniques are reviewed. Several important challenges are discussed that occur
when using spectral emissivity, temperature-based indices, and physically-based approaches for
water-stress detection in the TIR spectral domain. Furthermore, challenges with data processing
and the perspectives for future satellite missions in the TIR are critically examined. In conclusion,
information from multi-/hyperspectral TIR together with those from VNIR/SWIR and SIF sensors
within a multi-sensor approach can provide profound insights to actual plant (water) status and the
rationale of physiological and biochemical changes. Synergistic sensor use will open new avenues
for scientists to study plant functioning and the response to environmental stress in a wide range
of ecosystems.
Keywords: remote sensing; thermal infrared (TIR); water stress; crop stress; evapotranspiration (ET)
modeling; emissivity; temperature; drought; water use
Remote Sens.2019, 11, 1240; doi:10.3390/rs11101240 www.mdpi.com /journal/remotesensing
===== PAGE 2 =====
Remote Sens.2019, 11, 1240 2 of 24
1. Importance of Water-Stress Detection
Water-deﬁcit stress, usually shortened to water or drought stress, describes the plant physiological
responses induced by a lack of available water due to either soil water deﬁcit or high evaporative
demand of the atmosphere. Water stress induces dehydration in the plant and prevents plant cells
from keeping water concentrations at an acceptable and healthy level [1,2]. Therefore, water stress is
one of the most critical abiotic stressors limiting plant growth, crop yield and quality concerning food
production [3,4].
Since the global population is projected to grow by about 2.3 billion people between 2015 and 2050
and societies are changing from low to medium per capita income, global food demand is expected
to double within the same time [5–7]. Therefore, one of the most challenging tasks of our generation
is to meet the second Sustainable Development Goal as deﬁned in the 2030 agenda for sustainable
development by the United Nations: “End hunger, achieve food security and improved nutrition and
promote sustainable agriculture” [8]. In this respect, agricultural processes need to be optimized and
innovative farming methods must be developed to guarantee global food supply, as arable land and
environmental resources have almost reached the limits of sustainability.
Water is the most valuable resource of our planet. Presently, agriculture consumes 80–90% of the
freshwater used by humans worldwide and about two thirds of this freshwater is required for crop
irrigation [9]. Therefore, the ultimate goal must be a reduction in the amount of water used per unit
yield [10].
In addition, anthropogenic climate change is predicted to cause an increase of 1.0–2.5◦C in the
annual mean global temperature over the next 50 years with a tremendous impact on agriculture [11].
Consequently, evapotranspiration (ET) rates will increase and thus, the demand of water for crop
irrigation will further rise. At the same time, extreme weather events such as droughts will appear
more frequently and be more severe. These facts add some extra pressure to increasing global water
scarcity and the need for saving water.
Hence, it is desired to reduce the amount of water used per unit yield by reducing yield loss
and by reducing the amount of water used for irrigation. To achieve this goal, early detection and
monitoring of plant responses to water stress in agricultural crops are mandatory. Remote sensing
oﬀers the opportunity to acquire high spatial, spectral and temporal resolution data as input for
precision agriculture [12]. Precision agriculture promises great potential to close the yield gap by
optimizing food production using the right management practice at the right place and the right time
while keeping the consumption of resources at an environmentally sustainable level [13].
2. Plant Responses to Water Stress
Plant responses to water stress are numerous and complex (see [ 4,14–16] for comprehensive
reviews). They appear synergistically or antagonistically and are modiﬁed by co-occurring plant
stresses under ﬁeld conditions (Figure 1) [ 4,17,18]. Therefore, it remains di ﬃcult to detect and
monitor plant water deﬁcit based on a single plant response [ 19]. In general, water deﬁcit causes
physiological and biochemical changes which induce a reduction in photosynthesis and thus plant
growth [16]. However, the timing, intensity, and duration of water stress are crucial to determine the
plant physiological responses and their impact on plant metabolism [20]. For example, under mild
water-stress conditions, plant regulation of water loss and uptake still allows the plant to maintain
relative leaf water content with no or only little change in photosynthetic capacity. In contrast, severe
water deﬁcit induces serious physiological and biochemical changes, which lead to e ﬀects ranging
from inhibition of photosynthesis and growth to leaf wilting and the loss of key pigments such as
chlorophyll and thus to irreversible damages to the photosynthetic machinery [15–17]. Hence, plants
have developed multiple mechanisms to prevent severe damage through water stress [21].
===== PAGE 3 =====
Remote Sens.2019, 11, 1240 3 of 24
Remote Sens. 2019, 11, x FOR PEER REVIEW 3 of 24 
 
 90 
Figure 1. Most important relationships between primary plant stresses, the induced plant responses, 91 
and the multi-/hyperspectral remote sensing techni ques for the detection of environmental stresses 92 
(modified after Jones and Vaughan [19]). 93 
The first plant response to water stress is stomatal closure, which prevents transpirational water 94 
loss (e.g., [4,15,17]). In particular, stomatal closure is the response to either a deficit in soil water sup-95 
ply or to low-humidity atmosphere with high ev aporative demand. It is commonly assumed that 96 
stomatal response is rather linked to soil water content than to leaf water content. This suggests that 97 
stomata are most likely triggered by chemical signals, such as the accumulation of abscisic acid (ABA) 98 
in dehydrated roots rather than by a reduced cell turgor [4]. However, under severe and/or prolonged 99 
water stress, cell turgor, and leaf water content is also reduced [15]. As a consequence, the exchange 100 
of water vapor between plants and atmosphere is reduced by stomatal closure and thus, the evapo-101 
rative cooling effect is decreased resulting in an  overall increase of plant surface temperature com-102 
pared to a plant which does not suffer from water stress [14,18,22].  103 
However, the stomata not only control plant tran spiration but also plant respiration which in-104 
hibits CO2 uptake and fixation. As a result of stomatal closure, the photosynthetic rate is reduced, 105 
which causes a reduction in cell division and thus slows down leaf growth and reduces the rate of 106 
leaf surface area expansion. A persistent water deficit will further damage the photosynthetic ma-107 
chinery through loss of chlorophyll, which finally  introduces changes in leaf color and wilting 108 
[15,16,20]. Another plant response to water stress is  the change in sun-induced fluorescence (SIF). 109 
While the photosynthetic rate is reduced by a decreased CO 2 uptake due to stomatal closure, irradi-110 
ance and absorbed photosynthetically active radiat ion (fAPAR) remain constant. In general, energy 111 
absorbed by plant pigments (i.e., the chlorophylls and carotenoids) is dissipated by three competitive 112 
processes (i.e., photosynthesis, SIF, and heat emis sion). Consequently, a reduced photochemistry as 113 
induced by water stress results in several physiological mechanisms to protect the plant against pho-114 
toinhibition. These mechanisms foster non-photochemical quenching (NPQ) and reduce SIF [23,24].  115 
Besides these plant responses to water stress, osmotic adjustment is a further strategy to prevent 116 
irreversible damage. Osmotic adjustment describes the process of the accumulation of solutes such 117 
as carbohydrates and proteins to maintain the cell turgor at osmotic equilibrium [25]. 118 
In summary, plant responses to water stress can be recognized as a sequence of physiological 119 
and biochemical changes depending on the severity and duration of plant water deficit. Hence, the 120 
detection of water-stress symptoms is a function of time and depends on the plant responses to water 121 
deficit and their corresponding physiological changes, which may be sensitive to different remote 122 
sensing techniques.  123 
Figure 1. Most important relationships between primary plant stresses, the induced plant responses,
and the multi-/hyperspectral remote sensing techniques for the detection of environmental stresses
(modiﬁed after Jones and Vaughan [19]).
The ﬁrst plant response to water stress is stomatal closure, which prevents transpirational water
loss (e.g., [ 4,15,17]). In particular, stomatal closure is the response to either a deﬁcit in soil water
supply or to low-humidity atmosphere with high evaporative demand. It is commonly assumed that
stomatal response is rather linked to soil water content than to leaf water content. This suggests that
stomata are mo
