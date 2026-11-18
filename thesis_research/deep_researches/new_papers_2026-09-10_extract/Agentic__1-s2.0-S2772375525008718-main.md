# 1-s2.0-S2772375525008718-main.pdf

- Category: Agentic
- Pages: 12
- Path: D:\RS\Thesis\New_papers\Agentic\1-s2.0-S2772375525008718-main.pdf

## Metadata

```json
{
  "/Creator": "Elsevier",
  "/CrossMarkDomains[1]": "elsevier.com",
  "/CrossmarkMajorVersionDate": "2010-04-23",
  "/CreationDate--Text": "9th December 2025",
  "/ElsevierWebPDFSpecifications": "7.0.1",
  "/robots": "noindex",
  "/ModDate": "D:20251209153746Z",
  "/Author": "Deus F. Kandamali",
  "/doi": "10.1016/j.atech.2025.101640",
  "/Title": "CottonBot: An AI-driven cotton farming assistant and irrigation advisor using LLM-RAG and agentic AI tools",
  "/Keywords": "Chatbot,AI agents,Model context protocol (MCP),Retrieval-augmented generation (RAG),Large language models (LLM),\"Soil moisture sensors, IoT sensors\",Weather forecasting",
  "/CreationDate": "D:20251209143910Z",
  "/Producer": "Acrobat Distiller 8.1.0 (Windows)",
  "/Subject": "Smart Agricultural Technology, 12 (2025) 101640. doi:10.1016/j.atech.2025.101640",
  "/CrossMarkDomains[2]": "sciencedirect.com",
  "/CrossmarkDomainExclusive": "true"
}
```

## First pages


===== PAGE 1 =====
CottonBot: An AI-driven cotton farming assistant and irrigation advisor 
using LLM-RAG and agentic AI tools
Deus F. Kandamali
a , *
, Wesley M. Porter
c
, Erin Porter
d
, Alex McLemore
d
, Glen C. Rains
a , b
a
College of Engineering, University of Georgia, Tifton, GA 31793, USA
b
Department of Entomology, College of Agricultural and Environmental Sciences, University of Georgia
c
Department of Crop and Soil Sciences, University of Georgia, Tifton, GA 31793, USA
d
Abraham Baldwin Agricultural College, Tifton, GA 31793, USA
ARTICLE INFO
Keywords:
Chatbot
AI agents
Model context protocol (MCP)
Retrieval-augmented generation (RAG)
Large language models (LLM)
Soil moisture sensors, IoT sensors
Weather forecasting
ABSTRACT
Digital agriculture is transforming crop management by enabling data-driven decision-making. This study in -
troduces CottonBot, an AI-powered assistant designed to support cotton farmers with comprehensive farming 
guidelines, including pest management, soil fertilization, weed control, nematode management, and real-time, 
context-aware, farm-specific irrigation recommendations. Unlike traditional retrieval augmented generation 
(RAG) based systems that rely solely on static knowledge bases, CottonBot integrates RAG with agentic large 
language model (LLM) tools, utilizing farm-specific soil moisture sensors and local weather forecast APIs to 
deliver dynamic, actionable, and field-specific recommendations. The system leverages open-weight LLMs and 
runs locally through Ollama framework, ensuring cost-efficiency, data privacy, and accessibility in resource- 
limited settings. The study ’ s experimental setup combined RAG with LLM-based agentic tools. Within the RAG 
framework, we evaluated multiple embedding models using two retrieval backends: FAISS (Facebook AI simi -
larity search) and Chroma (a vector database). The embedding model, all-MiniLM-L6-v2 paired with FAISS 
achieved the highest retrieval performance, while Llama 3.1 produced the most faithful and semantically ac -
curate responses. For real-time irrigation support, CottonBot ’ s agentic tool interprets weighted soil moisture data 
to provide crop-specific recommendations, demonstrating its utility beyond text retrieval. Finally, CottonBot was 
deployed as a cross-platform mobile application using FastAPI and Flutter for both iOS and Android. Results 
indicate that CottonBot enhances decision-making support for cotton farmers, leading to more efficient water use 
and improved crop yields.
1. Introduction
The global demand for food production continues to escalate with 
population growth, placing immense pressure on agriculture to achieve 
higher yields with fewer resources. Among the emerging technologies 
addressing this challenge, artificial intelligence (AI) [ 1 – 3 ] and particu -
larly large language models (LLMs) [ 4 – 8 ] has proven transformative in 
advancing precision agriculture through improved decision-making and 
operational efficiency. Cotton production, a vital component of U.S. 
agriculture, is sensitive to water and nitrogen use efficiency, pest out -
breaks, and weed pressure [ 9 ]. Each of these can have a significant in -
fluence on crop yield and quality. However, many cotton producers still 
depend on manual field observations, static guidelines, and experiential 
knowledge, which are often inadequate under fast-changing field 
conditions.
Although agricultural knowledge is increasingly digitized and 
available through PDFs, spreadsheets, and web-based resources, farmers 
frequently struggle to extract actionable insights in a timely manner due 
to information overload, time constraints, or limited digital literacy. 
This challenge has sparked interest in conversational AI tools that can 
deliver timely, personalized advice through intuitive interfaces, 
commonly known as chatbots. Traditional rule-based chatbots [ 10 – 16 ] 
have offered limited utility in this space due to their static nature and 
shallow natural language understanding, making them unsuitable for 
handling the complexity of modern, domain-specific agricultural 
queries.
Recent developments in LLMs have enabled generative AI chatbots to 
perform dynamic, context-aware reasoning across diverse fields 
* Corresponding author.
E-mail address: soler.deus@uga.edu (D.F. Kandamali). 
Contents lists available at ScienceDirect
Smart Agricultural Technology
journal homepag e: www.jou rnals.elsevie r.com/smart- agricultura l-technology
https://doi.org/10.1016/j.atech.2025.101640
Received 1 October 2025; Received in revised form 13 November 2025; Accepted 13 November 2025  
Smart Agricultural Technology 12 (2025) 101640 
Available online 14 November 2025 
2772-3755/© 2025 The Authors. Published by Elsevier B.V. This is an open access article under the CC BY license ( http://creativecommons.org/licenses/by/4.0/ ). 
===== PAGE 2 =====
including various agricultural domains. These systems can interpret 
unstructured queries, support multilingual interactions, and generate 
responses tailored to the user ’ s context. However, LLMs are limited by 
the fixed scope of their pre-trained data and are prone to hallucinations 
when faced with domain-specific or real-time questions such as deter -
mining optimal irrigation based on crop stage and current soil condi -
tions. To address these shortcomings, Retrieval-Augmented Generation 
(RAG) [ 17 – 21 ] framework was introduced. These systems combine 
LLMs with external structured and unstructured knowledge sources, 
enhancing factual grounding and contextual relevance at inference time.
RAG agricultural applications have shown promising results across a 
range of domains, including crop diagnostics, traceability, and advisory 
services. AgroLLM is a RAG-based chatbot that integrates open-source 
agricultural documents and uses FAISS (Facebook AI similarity search) 
similarity search to achieve high performance in contextual relevance 
[ 22 ]. while multimodal systems support inclusive, user-friendly inter -
action across literacy levels [ 6 , 23 , 24 ]. Other notable implementations, 
such as BeefBot [ 25 ] and crop-specific optimization bots [ 7 , 8 ], 
demonstrate significant improvements in relevance, precision, and 
recall. However, most existing systems remain limited by their reliance 
on static document corpora and lack integration with real-time envi -
ronmental data to make real-time decisions, which is a critical need in 
data-intensive precision agriculture.
To address the limitations of existing agricultural chatbots, this study 
introduces CottonBot, a domain-specific, AI-driven conversational as -
sistant tailored for cotton farmers in Georgia, USA. CottonBot employs a 
hybrid architecture that integrates the open-source LLM (Llama3) via 
the Ollama framework with a RAG pipeline to produce contextually 
grounded responses. The system does two major things: (1) it retrieves 
static expert knowledge from the 2024 Georgia cotton production guide 
[ 26 ] (developed by the UGA extension team) to provide comprehensive 
agronomic assistance, including pest management, fertilization, and 
crop development best practices, and (2) it leverages real-time, field- -
specific data through agent tool calling, dynamically interfacing with 
farm-specific IoT soil moisture sensors and weather forecasting APIs to 
deliver adaptive irrigation recommendations based on current envi -
ronmental conditions. To ensure accessibility and scalability, CottonBot 
is deployed as a mobile application using Flutter and FastAPI, offering a 
seamless, user-friendly interface. By relying entirely on open-source 
technologies, the system presents a cost-effective alternative to com -
mercial LLM-based platforms that depend on paid API subscriptions 
without compromising accuracy, relevance, or responsiveness.
2. Materials and methods
2.1. Data collection and RAG knowledge base construction
This study uses two key data streams to support intelligent, context- 
aware decision-making in cotton farming: (1) a static knowledge-base 
for the RAG pipeline which is derived from the 2024 Georgia cotton 
production guide [ 26 ], providing expert agronomic guidance on prac -
tices such as fertilization, pest control, weed management, nematode 
management, irrigation decisions, and overall cotton management 
guidelines; and (2) dynamic, farm-specific data for real-time irrigation 
decision obtained from real-time soil moisture readings via 
RealmFive-installed watermark sensors in the 4D-Project farm called 
Digital and Data-Driven Demonstration (D.A.T.A) farm on the Abraham 
Baldwins Agricultural College (ABAC), Tifton Georgia - USA and 
weather forecasting data retrieved from the OpenWeatherMap APIs. By 
combining these data modalities, the system delivers both generalized 
farming advice from RAG and localized, real-time and farm-specific 
irrigation recommendations from live sensors.
The 4D-farm has 4 fields namely; North Pivot, South Pivot, Front 
Field and West Field with a total of 12 soil moisture sensors installed and 
one weather station shared across them as shown in Fig. 1 . Both North 
and south pivots have 4 soil moisture sensors each while the front and 
south pivots have two each, both represented as white and black markets 
in Fig. 1 .
The Georgia Cotton Production Guide, produced by the University of 
Georgia Cotton Team with support from the Georgia Cotton Commis -
sion, is a comprehensive extension handbook. It provides an in-depth, 
region-specific synthesis of agronomic best practices for Georgia and 
the broader southeastern U.S., covering variety selection, planting 
windows, soil fertility and fertilization, irrigation scheduling, integrated 
pest management (weeds, insects, diseases/nematodes), and harvest/ 
defoliation.
The handbook ’ s expert-curated content spans both structured (ta -
bles, charts, decision thresholds, formulas) and unstructured (narrative) 
materials addressing plant growth monitoring, insect scouting, pest and 
disease management, nematode control, irrigation scheduling, and in -
tegrated decision-support systems. The document is processed using 
LangChain framework for loading, chunking, and semantic embedding. 
The resulting embeddings are indexed in the vector database to enable 
fast and scalable similarity search. At query time, the system retrieves 
the most relevant document chunks and passes them through a RAG 
pipeline, allowing a LLM to generate accurate, localized context-aware 
responses.
Fig. 1. The (D.A.T.A) 4D-Project Farm at the ABAC showing fields sensors distribution and field weather station.
D.F. Kandamali et al.                                                                                                                                                                                                                          Smart Agricultural Technology 12 (2025) 101640 
2 
===== PAGE 3 =====
2.2. Vector embeddings
Following knowledge base construction, the proposed system em -
ploys vector embeddings to enable efficient semantic retrieval. Em -
beddings are numerical representations of text (both from user queries 
and knowledge base documents) that capture underlying semantic 
meaning. By projecting text into a high-dimensional vector space, em -
beddings allow semantically related content to cluster together, even 
when the exact wording differs.
Experiments conducted in this study employed six (6) open-source 
embedding models: all-MiniLM-L6-v2 from Sentence-Transformers, 
jina-embeddings-v2-base-en from Jina AI, intfloat/e5-base and e5- 
mistral-7b-instruct from HuggingFace, and bge-base-en-v1.5 and bge- 
m3 from the Beijing Academy of Artificial Intelligence (BAAI). These 
models were evaluated using two vector databases: Chroma and FAISS, 
to compare their retrieval performance in terms of semantic similarity 
and latency. The embedding pipeline consisted of three main tasks: (i) 
encoding semantically meaningfu
