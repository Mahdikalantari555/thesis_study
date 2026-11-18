# 1-s2.0-S1569843226001111-main.pdf

- Category: Agentic
- Pages: 12
- Path: D:\RS\Thesis\New_papers\Agentic\1-s2.0-S1569843226001111-main.pdf

## Metadata

```json
{
  "/Creator": "Elsevier",
  "/CrossMarkDomains[1]": "elsevier.com",
  "/CrossmarkMajorVersionDate": "2010-04-23",
  "/CreationDate--Text": "28th April 2026",
  "/ElsevierWebPDFSpecifications": "7.0.1",
  "/robots": "noindex",
  "/ModDate": "D:20260428064443Z",
  "/Author": "Chao Liang",
  "/doi": "10.1016/j.jag.2026.105195",
  "/Title": "GeoAgentic-RAG: A Multi-Agent framework for autonomous geospatial reasoning and visual insight generation with LLM",
  "/Keywords": "Geospatial Analysis,Multi-Agent Spatial Reasoning,Spatial Semantic Understanding,Retrieval-Augmented Generation",
  "/CreationDate": "D:20260425113922Z",
  "/Producer": "Acrobat Distiller 8.1.0 (Windows)",
  "/Subject": "International Journal of Applied Earth Observation and Geoinformation, 147 (2026) 105195. doi:10.1016/j.jag.2026.105195",
  "/CrossMarkDomains[2]": "sciencedirect.com",
  "/CrossmarkDomainExclusive": "true"
}
```

## First pages


===== PAGE 1 =====
GeoAgentic-RAG: A Multi-Agent framework for autonomous geospatial 
reasoning and visual insight generation with LLM
Chao Liang
a
, Yuanzheng Cui
a , b , *
, Run Shi
c
, Guixiang Zha
d
, Xin Yin
e
, Mingzhong Xiao
f
,  
Dong Xu
g
, Xuejun Duan
a , b
, Bo Huang
h , *
a
State Key Laboratory of Lake and Watershed Science for Water Security, Nanjing Institute of Geography and Limnology, Chinese Academy of Sciences, Nanjing 211135, 
China
b
University of Chinese Academy of Sciences, Nanjing 211135, China
c
Guangzhou Institute of Geography, Guangdong Academy of Sciences, Guangzhou 510070, China
d
College of Geography and Remote Sensing, Hohai Uninversity, Nanjing 210024, China
e
Nanjing Hydraulic Research Institute, Nanjing 210029, China
f
School of Civil Engineering, Sun Yat-sen University, Zhuhai 519082, China
g
Department of Geography, National University of Singapore, Singapore, 119077, Singapore
h
Department of Geography, The University of Hong Kong, Hong Kong S.A.R., China
ARTICLE INFO
Keywords:
Geospatial Analysis
Multi-Agent Spatial Reasoning
Spatial Semantic Understanding
Retrieval-Augmented Generation
ABSTRACT
Conventional Retrieval-Augmented Generation (RAG) systems have limited effectiveness in geospatial question 
answering because text-based similarity retrieval cannot adequately represent spatial semantics such as topology 
and spatial context. To overcome this limitation, we propose GeoAgentic-RAG, a multi-agent framework that 
enables multimodal large language models (MLLMs) to perform autonomous geospatial reasoning. The frame -
work integrates natural language query parsing, semantic-spatial retrieval, and executable geospatial analysis 
within a unified, agent-based workflow. Multiple specialized agents collaboratively interpret user queries, 
retrieve relevant vector and raster datasets from a unified geospatial database, decompose analytical tasks, 
generate valid spatial logic, and produce interpretable analytical results. We evaluate GeoAgentic-RAG using a 
benchmark of geospatial retrieval, feature characterization, and spatial relational reasoning tasks in Nanjing and 
Guangzhou. The proposed framework achieves a pass rate of 85.3% and an answer correctness of 88.3%, out -
performing conventional RAG methods and representative code-generation baselines. These results demonstrate 
that agent-based integration of retrieval and spatial analysis substantially improves the reliability of geospatial 
question answering and provides a practical framework for the next-generation intelligent GIS applications.
1. Introduction
The rapid advancement of artificial intelligence (AI), particularly the 
progress of Large Language Models (LLMs) in fields such as Natural 
Language Processing (NLP) and information retrieval ( Arslan et al., 
2024 ) has introduced new opportunities for data retrieval and genera -
tive reasoning. Among recent innovations, Retrieval-Augmented Gen -
eration (RAG) has become a central approach for improving semantic 
comprehension and factual consistency of generative models ( Edge 
et al., 2025; Vidivelli et al., 2024 ). RAG combines external knowledge 
retrieval with text generation, allowing models to incorporate relevant 
information from external databases or document repositories during 
response generation. This integration improves both the accuracy and 
coherence of generated output. As a result, it has become a central 
approach for strengthening the semantic reasoning capability of large- 
scale language models ( Arslan et al., 2024 ).
Geographic Information Systems (GIS) provide the computational 
foundation for acquiring, managing, analysing, and visualizing spatial 
data ( Syafiq and Azri, 2023 ). They support a wide range of applications, 
including smart city planning ( Lee and Yang, 2025 ), environmental 
monitoring ( Zhao et al., 2024 ), natural hazard management ( Maleki and 
Mohammadalizadehkorde, 2022 ), community commercial vitality 
evaluating( Cui et al. 2025 ) and urban traffic control ( Wang et al., 2023 ). 
Spatial data differ substantially from textual or visual data because they 
contain multi-dimensional and heterogeneous elements, including 
geographic coordinates, topological relations, geometric structures, and 
* Corresponding authors..
E-mail addresses: yzcui@niglas.ac.cn (Y. Cui), bohuang@hku.hk (B. Huang). 
Contents lists available at ScienceDirect
International Journal of Applied Earth  
Observation and Geoinformation
journal homep age: www.elsevi er.com/locate /jag
https://doi.org/10.1016/j.jag.2026.105195
Received 9 November 2025; Received in revised form 13 January 2026; Accepted 17 February 2026  
International Journal of Applied Earth Observation and Geoinformation 147 (2026) 105195 
Available online 20 February 2026 
1569-8432/© 2026 The Authors. Published by Elsevier B.V. This is an open access article under the CC BY license ( http://creativecommons.org/licenses/by/4.0/ ). 
===== PAGE 2 =====
remote sensing rasters. This complexity far exceeds that of conventional 
unstructured data ( Zhu and Zhou, 2021 ). However, existing RAG 
frameworks have been developed primarily for linguistic and visual 
domains and do not model spatial relationships, geographic semantics, 
or spatiotemporal contexts. As a result, they perform poorly in tasks such 
as spatial question answering, geographic retrieval, and spatial content 
generation. When spatial operations such as spatial overlay, context 
fusion, and topological analysis are required, their performance de -
teriorates further, constraining the application of RAG in geospatial 
intelligence ( Li and Ning, 2023 ).
Integrating RAG into GIS research therefore represents both an 
extension of NLP methods and a potential shift in how spatial semantics 
and geospatial reasoning are approached. RAG technology offers three 
key advantages in this context. First, it supports natural language-driven 
geospatial question-answering (Geospatial QA), allowing users to query 
and reason over spatial data without explicit knowledge of GIS com -
mands or syntax. Second, its retrieval mechanism can incorporate het -
erogeneous spatial sources, such as remote sensing imagery, vector 
entities, and geographic knowledge bases, into a unified space, enabling 
the development of semantically enhanced spatial models. Third, the 
generative component of RAG can translate analytical results into 
interpretable, context-aware linguistic responses, providing a natural 
interaction layer for geospatial decision support systems. These capa -
bilities offer a technical foundation for the continued evolution of GIS 
toward higher levels of intelligence, interoperability, and accessibility.
Despite these prospects, major challenges remain. Existing RAG 
systems lack dedicated spatial indexing and spatial parsing modules 
capable of representing spatial proximity, containment, and connectiv -
ity. Similarly, current language models are limited in their ability to 
capture spatiotemporal correlations and semantic constraints among 
geographic entities. They also lack the ability to interpret map seman -
tics, layer hierarchies, and spatial logic. Addressing these issues requires 
a hybrid architecture that integrates spatial perception, geographic 
reasoning, and language generation within a single operational frame -
work in order to link LLMs more directly with GIS.
To meet this need, this study introduces GeoAgentic-RAG, a multi- 
agent RAG framework designed for geospatial semantic reasoning and 
autonomous analytical processing. In contrast to conventional systems, 
GeoAgentic-RAG can identify required datasets automatically, retrieve 
relevant GIS resources from local or distributed databases, and perform 
visualization and analytical tasks without manual specification of data 
paths or operations. Through multi-agent collaboration and context- 
driven task allocation, the framework integrates structured GIS data 
and natural language inputs to support complex spatial problem solving, 
semantic retrieval, and geographic context generation. It represents the 
first attempt to embed spatially aware agents within a RAG architecture, 
creating a closed-loop workflow that spans data retrieval, analysis, and 
visualization stages. This framework establishes a new technical para -
digm for the integration of GIScience and large language models.
This paper presents the design principles, core components, and 
technical architecture of GeoAgentic-RAG, and evaluate its performance 
across several geospatial retrieval and reasoning tasks. Experimental 
results demonstrate that the framework improves the efficiency, accu -
racy, and interpretability of geographic information processing. These 
findings indicate that GeoAgentic-RAG provides an effective and scal -
able solution for intelligent geospatial applications, including smart city 
governance, environmental monitoring, and disaster management.
2. Related works
RAG combines information retrieval with natural language genera -
tion to enhance the factual and contextual accuracy of large language 
models. In its standard architecture, a retrieval module searches for 
documents relevant to a user query, and a generation module produces 
responses conditioned on both the retrieved content and the query itself 
( Arslan et al., 2024; Li et al., 2022 ). This hybrid design allows generative 
models to address knowledge-intensive tasks that exceed the scope of 
their pre-trained parameters. Conventional LLMs rely solely on static 
corpora; once training is completed, their parameters remain fixed. 
Consequently, they perform poorly when confronted with time-sensitive 
information or domain-specific knowledge. For instance, an LLM may 
return outdated or inaccurate results when asked about newly published 
research or rapidly evolving technical fields. RAG mitigates these 
shortcomings by retrieving up-to-date information from external data -
bases or literature repositories and integrating it into the generation 
process ( Bao et al., 2025 ). In practice, the system identifies several 
relevant text passages, combines them with the user query to form an 
augmented prompt, and passes the result to the generator to produce 
contextually consistent answers. This procedure improves factual 
grounding and supports complex reasoning tasks as long-form question 
answering and multi-hop reasoning ( Iscan et al., 2024 ).
Early implementations of RAG are confined largely to text generation 
tasks, including question answering, text summarization, and machine 
translation. These studies establish the foundation for its widespread 
adoption in natural language processing. As research progressed, 
various extensions have been proposed to improve adaptability and ef -
ficiency ( Li et al., 2022 ). Adaptive-RAG ( Jeong et al., 2024 ) employs a 
dynamic parser that adjusts retrieval strategies according to question 
complexity, maintaining balance between computational efficiency and 
semantic coverage. TableGPT ( Zha et al., 2023 ) adapts RAG to struc -
tured data by translating table content into SQL queries, enabling da -
tabases to be accessed through natural language instructions. Other 
work focuses on text-parsing modules and document loaders that 
transform heterogeneous knowledge sources into uniform textual input, 
improving retrieval accuracy. A persistent difficulty in these models is 
the occurrence of “hallucinations”, where generated text deviates from 
the retrieved facts ( Hager et al., 2024 ). GraphRAG ( Edge et al., 2025 ) 
addresses this issue by introducing graph-based indexing and annotated 
representations that strengthen semantic accuracy between retrieved 
and generated content.
With the maturation of the field, RAG has expanded beyond pure text 
to multi-modal applications. In computer vision, RA-CM3 ( Yasunaga 
et al., 2023 ) integrates image understanding with textual reasoning ( Bai 
et al., 2023 ), marking one of 
