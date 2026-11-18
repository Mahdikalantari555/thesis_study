# An LLM-based multi-agent system for remote sensing analysis.pdf

- Category: Agentic
- Pages: 26
- Path: D:\RS\Thesis\New_papers\Agentic\An LLM-based multi-agent system for remote sensing analysis.pdf

## Metadata

```json
{
  "/CreationDate": "D:20260102123250+05'30'",
  "/Creator": "PTC Arbortext Publishing Engine",
  "/Keywords": "Remote sensing analysis; large language models; multi-agent systems; workflow",
  "/ModDate": "D:20260102123250+05'30'",
  "/Producer": "PDFlib+PDI 9.2.0 (C++/Win64)",
  "/Title": "An LLM-based multi-agent system for remote sensing analysis"
}
```

## First pages


===== PAGE 1 =====
Big Earth Data
ISSN: 2096-4471 (Print) 2574-5417 (Online) Journal homepage: www.tandfonline.com/journals/tbed20
An LLM-based multi-agent system for remote
sensing analysis
Zhelun Sun, Yuyu Zhou & Jun Yang
To cite this article: Zhelun Sun, Yuyu Zhou & Jun Yang (08 Jan 2026): An LLM-based multi-agent
system for remote sensing analysis, Big Earth Data, DOI: 10.1080/20964471.2025.2600178
To link to this article:  https://doi.org/10.1080/20964471.2025.2600178
© 2026 The Author(s). Published by Taylor
& Francis Group and Science Press on
behalf of the International Society for
Digital Earth, supported by the International
Research Center of Big Data for Sustainable
Development Goals.
View supplementary material 
Published online: 08 Jan 2026.
Submit your article to this journal 
Article views: 3011
View related articles 
View Crossmark data
Citing articles: 4 View citing articles 
Full Terms & Conditions of access and use can be found at
https://www.tandfonline.com/action/journalInformation?journalCode=tbed20
===== PAGE 2 =====
RESEARCH ARTICLE
An LLM-based multi-agent system for remote sensing analysis
Zhelun Sun
a
, Yuyu Zhou
b 
and Jun Yang
a
a
Department of Earth System Science, Institute for Global Change Studies, Ministry of Education Key 
Laboratory for Earth System Modeling, Tsinghua University, Beijing China; 
b
Department of Geography, The 
University of Hong Kong, Hong Kong, China
ABSTRACT
Remote sensing analysis converts remotely sensed data into action -
able insights across diverse fields. However, traditional data-driven 
approaches frequently overlook the technical challenges encountered 
by end-users lacking remote sensing expertise. To address this issue, 
we proposed a multi-agent system framework based on a large lan -
guage model, designed to facilitate remote sensing analysis for non- 
experts. The framework consists of three main modules: Data, which 
includes remote sensing datasets and supplementary information; 
Tools, encompassing algorithms and visualization tools; and Brain, 
which provides AI-driven task management and reasoning. We 
employed a prototype system called ExpertsRS, developed on the 
AutoGen framework and DeepSeek-V3, to validate the proposed fra -
mework. This prototype features three LLM-powered agents with dis -
tinct roles and functionalities, collaborating to fulfill user requests. The 
system was evaluated through two experiments. The first experiment 
demonstrated that ExpertsRS could translate ambiguous queries into 
structured analytical workflows and produce outputs comparable to 
those of human experts. The second experiment indicated that 
ExpertsRS outperformed both a baseline LLM and a single-agent con -
figuration in planning efficiency and result accuracy, with only 
a modest increase in token usage. Our system underscores the poten -
tial of large language model-based multi-agent system to assist end- 
users in overcoming technical barriers in remote sensing analysis.
ARTICLE HISTORY 
Received 2 June 2025  
Accepted 8 November 2025 
KEYWORDS 
Remote sensing analysis; 
large language models; 
multi-agent systems; 
workflow
1. Introduction
Remote sensing has become a vital tool for understanding and managing the 
Earth’s surface, offering essential geospatial data that supports various applications 
such as environmental monitoring (Du et al., 2014 ; Yuan et al., 2020 ), urban 
planning (Ni et al., 2023 ; Shi et al., 2024 ; Yin et al., 2021 ), and disaster manage -
ment (Evans et al., 2014 ; Zheng et al., 2025 ). In the era of Big Data, the amount, 
diversity, and complexity of remote sensing data have grown rapidly, including 
multi-temporal, multi-spectral, and multi-source datasets (Li et al., 2016 ). This swift 
CONTACT Jun Yang 
 larix@tsinghua.edu.cn 
 Department of Earth System Science, Tsinghua University, Beijing, 
100084, People’s Republic of China
Supplemental data for this article can be accessed online at https://doi.org/10.1080/20964471.2025.2600178
BIG EARTH DATA                                            
https://doi.org/10.1080/20964471.2025.2600178
© 2026 The Author(s). Published by Taylor & Francis Group and Science Press on behalf of the International Society for Digital Earth, 
supported by the International Research Center of Big Data for Sustainable Development Goals.  
This is an Open Access article distributed under the terms of the Creative Commons Attribution-NonCommercial License ( http:// 
creativecommons.org/licenses/by-nc/4.0/ ), which permits unrestricted non-commercial use, distribution, and reproduction in any medium, 
provided the original work is properly cited. The terms on which this article has been published allow the posting of the Accepted 
Manuscript in a repository by the author(s) or with their consent.
===== PAGE 3 =====
increase in data volume necessitates innovative approaches to enhance data 
accessibility, usability, and analysis, enabling effective extraction of meaningful 
information.
Remote sensing analysis transforms remotely sensed data into actionable informa -
tion, forming the foundation for various applications (Rolf et al., 2024 ; Zhang et al.,  
2022b ). The analytical framework has progressed rapidly. Initially, pixel-based methods 
focused on spectral attributes at the pixel level, dominating the field (Blaschke & 
Strobl, 2001 ; Fisher, 1997 ). Advancements in spatial resolution and image processing 
have given rise to object-based approaches, which more closely mirror human visual 
interpretation (Blaschke, 2010 ; Blaschke et al., 2014 ). Deep learning techniques have 
revolutionized remote sensing analysis, with convolutional neural networks (CNNs) 
being extensively utilized for feature extraction and classification. Additionally, models 
such as ResNet (He et al., 2015 ), U-Net (Ronneberger et al., 2015 ), and Vision 
Transformers (ViTs) (Dosovitskiy et al., 2021 ) exhibit exceptional performance in 
scene classification, segmentation, and change detection (Mei et al., 2024 ; Shi et al.,  
2023 ). Moreover, Remote Sensing Foundation Models (RSFMs), pretrained on extensive 
geospatial datasets and subsequently fine-tuned for various tasks, are garnering 
increasing interest (Guo et al., 2023 ; Hong et al., 2024b ; Mai et al., 2023 ; Sun et al.,  
2023 ). Despite these advances, the aforementioned methods are primarily data-driven, 
emphasizing technical processing and accuracy rather than end-user accessibility 
(Arvor et al., 2019 ; Zhang et al., 2022a ). A persistent disconnect remains between 
experts and end users as remote sensing research evolves. While experts develop new 
sensors and techniques, end users encounter difficulties applying these methodologies 
to real-world decision-making (Ravichandran, 2024 ). This gap constrains the accessi -
bility and societal impact of remote sensing applications.
Researchers have explored various methodologies to incorporate users into the remote 
sensing analysis workflow. A primary strategy emphasizes interactive web-based plat -
forms that facilitate data access and analysis via user-friendly interfaces. Cloud-based 
applications such as AIEARTH (Alibaba DAMO Academy , 2022 ), Earth Map (Morales et al.,  
2023 ), and Imagery Explorer (Esri, 2024 ) encapsulate complex datasets and analytical 
tools, enabling users to explore open-source satellite imagery with pre-configured analy -
sis functionalities. Additionally, an emerging approach utilizes natural language interac -
tion as a more intuitive means for users to engage with remote sensing data (Lobry et al.,  
2020 ; Tuia et al., 2021 ). Extensive research has concentrated on the semantic extraction 
and intelligent interpretation of remote sensing imagery. Initial efforts adapted classical 
computer vision tasks—such as image captioning, visual grounding, and visual question 
answering (VQA)—to the remote sensing domain to improve access to information 
contained within remote sensing data (Lu et al., 2018 ; Qu et al., 2016 ; Zhan et al., 2023 ). 
Recent developments in large language models (LLMs) have led to the creation of Multi- 
Modal Large Language Models (MMLMs) specifically designed for remote sensing appli -
cations, including RSGPT (Hu et al., 2023 ), GeoChat (Kuckreja et al., 2023 ), EarthGPT (Zhang 
et al., 2024d ), and SkyEyeGPT (Zhan et al., 2025 ). These models integrate textual, visual, 
and data inputs from various sensors, enhancing language interaction capabilities and 
providing remarkable reasoning performance. Furthermore, efforts are underway to 
leverage LLMs in developing automated GIS analysis tools for professionals, such as LLM- 
Geo (Li & Ning, 2023 ), GeoGPT (Zhang et al., 2024e ), GeoAgent (Chen et al., 2024 ), and Geo 
2
 Z. SUN ET AL.
===== PAGE 4 =====
Scene GA Plus (GeoScene, 2025 ). These tools facilitate management of single- and multi- 
step GIS workflows through natural language, integrating LLMs into geospatial analysis.
Although significant progress has been made, certain challenges persist. Web-based 
interfaces require a high level of proficiency in data specifications and analytical techni -
ques (Xu et al., 2023a ), leading to a learning curve that users must overcome before 
effectively using the system. Moreover, these platforms face the risk of obsolescence as 
the applications of LLMs in geospatial analysis continue to evolve. MMLMs for remote 
sensing are primarily utilized with high-resolution images and are predominantly limited 
to small-scale interpretive tasks. While they can efficiently respond to fundamental 
inquiries such as “How many houses are in this image?” they are insufficient for addressing 
complex, large-scale analytical workflows that are vital for practical implementation. For 
instance, current MMLMs cannot be readily used to map urban vegetation across an entire 
district, estimate flood conditions within a drainage basin, or assess spatiotemporal 
environmental patterns across broader regions. Automatic GIS analysis tools are appeal -
ing because of the large GIS user community; however, unlike GIS tasks, which have clear 
guidance and parameters, remote sensing analysis often involves ambiguous and chan -
ging information, such as vague user requests (e.g., “assess vegetation health”), complex 
dependencies on domain knowledge, and data that vary over time, space, and sensors. 
Furthermore, GIS tools powered by LLMs mainly serve professionals, thus leaving a gap for 
non-expert users such as policymakers. Despite these challenges, recent innovations are 
increasingly shifting the focus from a data-centric to a user-centric approach in remote 
sensing analysis (Baumann, 2019 ; Tuia et al., 2023 ), fostering the development of more 
accessible and intelligent geospatial tools solutions.
The rapid progress of LLMs and LLM-based agent systems offers new opportunities to 
address the limitations of current approaches. An agent is an autonomous entity capable 
of perceiving its environment, making decisions, and taking actions (Wooldridge & 
Jennings, 1995 ; Xi et al., 2023 ). Combining the agent with LLM enables it to handle 
specific tasks automatically by following natural language instructions with minimal 
guidance (Li et al., 2024 ). However, when addressing a complex remote sensing analysis 
task, a single agent may lack the diverse expertise necessary to effectively manage all 
aspects of the workflow (Du et al., 2023 ). Building on the idea that intelligence can emerge 
from the interaction of multiple smaller agents with specific functions (Minsky, 1986 ), an 
LLM-based multi-agent system utilizes the cooperation of multiple specialized agents, 
similar to the division of labor in human society. LLM-based multi-agent systems have 
already proven effective for solving complex tasks requiring diverse expertise in domains 
such as software development (Hong et al.,), data science (Guo et al., 2024a ), and climate 
science research (Vaghefi et al., 2023 ). An
