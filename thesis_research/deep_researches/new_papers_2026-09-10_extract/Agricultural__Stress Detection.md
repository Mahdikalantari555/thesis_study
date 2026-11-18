# Stress Detection.pdf

- Category: Agricultural
- Pages: 27
- Path: D:\RS\Thesis\New_papers\Agricultural\Stress Detection.pdf

## Metadata

```json
{
  "/Producer": "pypdf"
}
```

## First pages


===== PAGE 1 =====
Please do not remove this page
Toward Resilience in Broadacre Agriculture: A
Methodological Review of Remote Sensing in
Crop Productivity, Phenology, and Environmental
Stress Detection
Shen, Jianxiu; Wang, Hai; Tareque, Hasnein
https://researchportal.murdoch.edu.au/esploro/outputs/journalArticle/Toward-Resilience-in-Broadacre-Agriculture-A/991005845962207891/filesAndLi
nks?index=0
Shen, J., Wang, H., & Tareque, H. (2025). Toward Resilience in Broadacre Agriculture: A Methodological
Review of Remote Sensing in Crop Productivity, Phenology, and Environmental Stress Detection. Remote
Sensing (Basel, Switzerland), 17(23), Article 3886. https://doi.org/10.3390/rs17233886
Published Version: https://doi.org/10.3390/rs17233886
Downloaded On 2026/09/17 15:35:25 +0800
© 2025 by the authors.
Open
CC BY V4.0

===== PAGE 2 =====
Academic Editor: Liang Sun
Received: 28 October 2025
Revised: 22 November 2025
Accepted: 27 November 2025
Published: 29 November 2025
Citation: Shen, J.; Wang, H.; Tareque,
H. Toward Resilience in Broadacre
Agriculture: A Methodological
Review of Remote Sensing in Crop
Productivity, Phenology, and
Environmental Stress Detection.
Remote Sens.2025, 17, 3886. https://
doi.org/10.3390/rs17233886
Copyright: © 2025 by the authors.
Licensee MDPI, Basel, Switzerland.
This article is an open access article
distributed under the terms and
conditions of the Creative Commons
Attribution (CC BY) license
(https://creativecommons.org/
licenses/by/4.0/).
Review
Toward Resilience in Broadacre Agriculture: A Methodological
Review of Remote Sensing in Crop Productivity, Phenology, and
Environmental Stress Detection
Jianxiu Shen 1, *
 , Hai Wang 2
 and Hasnein Tareque 1
1 Department of Primary Industries and Regional Development, Western Australia, Perth 6000, Australia;
hasnein.tareque@dpird.wa.gov.au
2 School of Engineering and Energy, Murdoch University, Murdoch 6150, Australia; hai.wang@murdoch.edu.au
* Correspondence: jenny.shen@dpird.wa.gov.au
Highlights
What are the main findings?
• Remote sensing methodologies for crop performance monitoring were systematically
reviewed across the themes of productivity, phenology, and environmental stress.
• Advances and challenges were identified within individual themes and in their inte-
gration toward holistic monitoring.
What are the implications of the main findings?
• Emerging integration approaches offer pathways beyond monitoring toward decision-
support systems for broadacre agriculture.
• Future directions of advancing resilience-focused applications of remote sensing
are proposed.
Abstract
Large-scale rainfed cropping systems (broadacre agriculture) face intensifying climate and
resource stresses that undermine yield stability and farm livelihoods. Remote sensing (RS)
offers critical tools for improving resilience by monitoring crop performance—productivity,
phenology, and environmental stress—across large areas and timeframes. This review
aims to synthesize methodological advances over the past two decades in applying RS for
broadacre crop monitoring and to identify key challenges and integration opportunities.
Peer-reviewed studies across diverse crops and regions were systematically examined to
evaluate the strengths, limitations, and emerging trends across the three RS application
themes. The review finds that (1) RS enables spatially explicit yield estimation from regional
to paddock scales, with vegetation indices (VIs) and phenology-adjusted metrics closely
correlated with yield. (2) Time-series analyses of RS data effectively capture phenological
transitions critical for forecasting, supported by advances in curve fitting, sensor fusion,
and machine learning. (3) Thermal and multispectral indices support the early detection
of abiotic (drought, heat, salinity) and biotic (pests, disease) stresses, though specificity
remains limited. Across themes, methodological silos and sensor integration barriers hinder
holistic application. Emerging approaches, such as multi-sensor/scale fusion, RS–crop
model data assimilation, and operational and big data integration, provide promising
pathways toward resilience-focused decision support. Future research should define
quantifiable resilience metrics, cross-theme predictive integration, and accessible tools to
guide climate adaptation.
Remote Sens.2025, 17, 3886 https://doi.org/10.3390/rs17233886
===== PAGE 3 =====
Remote Sens.2025, 17, 3886 2 of 26
Keywords: remote sensing; broadacre agriculture; crop productivity; phenology;environmental
stress
1. Introduction
Broadacre farming systems—especially large-scale, rainfed cropping systems, which
account for nearly three-quarters of the world’s cropland extent [ 1]—are under increas-
ing pressure due to climate variability and resource stresses [ 2,3]. Rising temperatures,
shifting rainfall patterns, and more frequent extreme weather events are already under-
mining crop yields and farm profits [2,4,5]. For example, in Australia’s grain belt, climate
change since 2000 has cut average broadacre farm profitability by about 22% [6,7]. Recent
record-breaking droughts (e.g., the driest early-season period on record in 2024) across the
south-west region of Western Australia delayed crop sowing and emergence, highlighting
the vulnerability of current practices to climate extremes [6]. Global studies likewise con-
firm that climate variability, especially heatwaves and drought, is a dominant driver of
year-to-year yield fluctuations, accounting for roughly 20–49% of global crop yield variabil-
ity [2,5,8]. Concurrent hot-and-dry extremes have consistently negative impacts on major
crops, and their occurrence is increasing. For example, the frequency of extreme hot/dry
conditions during wheat seasons has risen several-fold in recent decades [9]. These trends
threaten the reliability of crop production, making resilience a critical goal for broadacre
agriculture [9,10]. In this context, resilience is defined as the capacity of the agricultural
system to withstand, recover from, and adapt after disturbances [10]. Achieving resilience
in broadacre cropping means maintaining productivity under variable climate and resource
conditions and quickly rebounding from stress events. However, developing truly resilient
farming systems is challenging because multiple stressors (such as drought, heat, pests
and disease) often occur in combination [6]. There is a need for improved monitoring and
management strategies that can handle this complexity and safeguard yield stability and
farm incomes under a changing climate.
Remote sensing (RS) technologies—encompassing spaceborne, airborne, unmanned
aerial vehicles (UAVs/drones), and proximal sensors—have revolutionized crop moni-
toring by providing multi-scale, non-destructive observations throughout the growing
season [11]. These technologies are invaluable for tracking three key aspects of crop per-
formance: productivity—yield (quantity and quality), phenology—development timing,
and environmental stress. Modern RS platforms can continuously survey entire fields and
regions, detecting plant traits and symptoms that are often invisible to the human eye [12].
This enables an accurate, early, and spatially detailed view of crop status, supporting timely
management interventions.
Crop productivity, phenology, and stress metrics are complementary facets of crop
performance. Phenological anomalies often foreshadow yield impacts, and early stress
detection enables interventions to safeguard yields. However, studies in the literature using
RS for agriculture tend to focus on either yield estimation, phenology mapping, or stress
detection and assessment, without combining these aspects into a unified framework for
proactive resilience. In addition, a recent comprehensive review of optical remote sensing
for crop stress noted that most studies relied on single-sensor data and single-indicator
stress proxies, rather than exploiting multi-sensor, multi-factor synergies [ 13]. In that
review, most of the research designs were constrained by available sensors and tended
to examine one stress factor at a time [ 13]. The authors identified a clear path forward:
integrating data across multiple sensors and spectral domains to monitor multiple stress re-
sponses simultaneously (a more holistic view) and assimilating those observations into crop
===== PAGE 4 =====
Remote Sens.2025, 17, 3886 3 of 26
models [13]. This points to a gap in current research—the need for integration. Similarly,
while yield prediction studies and phenology studies exist separately, combining phenolog-
ical metrics with yield models has proven beneficial yet is not universally practiced. Few
studies explicitly link shifts in crop phenology due to climate stress with consequent yield
outcomes and stress mitigation strategies [14].
In the context of resilience, this gap is even more pronounced. Resilience, by defini-
tion, spans multiple dimensions (stable yields, adaptive phenology, and stress resistance),
but many investigations tackle these components independently. A farm-systems re-
silience review found that assessments often examine only a subset of performance metrics
(e.g., economic yield or average productivity) and ignore others like temporal variabil-
ity or environmental factors [ 10]. Therefore, there is a recognized need for integrating
crop productivity, phenology, and stress monitoring approaches into a single framework—
especially using remote sensing—as a non-destructive and cost-effective enabler. Without
such integration, we risk missing important interactions, such as how phenological shifts
might buffer yield losses under drought, or how early stress detection might save a season
if coupled with adaptive management [3].
While existing reviews on remote sensing applications have summarized available
sensor platforms and their usage [13] or explained the physiological relevance of spectral
bands [12,13], this review narrows the focus to synthesize recent methodological advances
in applying remote sensing to enhance resilience in rainfed broadacre cropping systems
(e.g., cereal, maize, rice, soybean). Specifically, the review addresses three principal themes:
(1) crop productivity monitoring (production and yield gaps estimation); (2) crop phenology
monitoring and modeling (growth stages and development shifts); and (3) crop stress
detection and assessment (abiotic and biotic stress). By integrating insights across these
domains, this review highlights how RS technologies are evolving from monitoring tools
toward comprehensive decision-support systems that can inform adaptive management
and strengthen resilience under climate change. This paper is structured to first review
thematic advances and limitations in RS applications, then examine integration trends and
challenges toward resilience, and finally outline future directions.
2. Materials and Methods
To ensure comprehensive yet focused coverage of relevant research, a semi-structured
literature search strategy was employed (Table 1). Google Scholar served as the primary
search engine, with the Web of Science and Scopus considered for cross-referencing, to cap-
ture studies spanning multi-disciplinary agriculture, including remote sensing, agronomy,
and climate adaptation.
Keyword combinations were designed to align with the principal themes of this review.
Searches were conducted using Boolean operators (AND, OR) with string combinations:
[“remote sensing” OR “UAV” OR “UAS” OR “drones”] AND [“crop produc*” OR “yield”
OR “crop phenology” OR “crop stress” OR “resilience”].
This inclusive search approach aimed to accommodate terminology differences across
disciplines and to capture studies addressing the intersection of remote sensing applications
and agricultural resilience.
Following the initial search, studies were screened based on title and abstract review
to identify potential relevance, with full-text assessments conducted where necessary.
The inclusion c
