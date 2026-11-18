# 1-s2.0-S2643651525001670-main.pdf

- Category: Agentic
- Pages: 17
- Path: D:\RS\Thesis\New_papers\Agentic\1-s2.0-S2643651525001670-main.pdf

## Metadata

```json
{
  "/CrossMarkDomains[2]": "elsevier.com",
  "/CrossmarkMajorVersionDate": "2010-04-23",
  "/CreationDate": "D:20260328202209+05'30'",
  "/Subject": "Plant Phenomics, 8 (2026) 100161. doi:10.1016/j.plaphe.2025.100161",
  "/Author": "Elshan Musazade",
  "/Creator": "Elsevier",
  "/Producer": "PDFlib+PDI 10.0.2p2 (C++/Win64)",
  "/EPSprocessor": "PStill version 1.84.42",
  "/ElsevierWebPDFSpecifications": "7.0.1",
  "/CrossmarkDomainExclusive": "true",
  "/robots": "noindex",
  "/ModDate": "D:20260328202731+05'30'",
  "/doi": "10.1016/j.plaphe.2025.100161",
  "/CrossMarkDomains[1]": "sciencedirect.com",
  "/Title": "Integration of LLMs and VLMs in plant stress phenotyping: From trait recognition to decision support"
}
```

## First pages


===== PAGE 1 =====
Review Article
Integration of LLMs and VLMs in plant stress phenotyping: From trait 
recognition to decision support
Elshan Musazade a , Isack Ibrahim Mrisho b , Jinshan Gao a , Xianzhong Feng a,*
a Key Laboratory of Soybean Molecular Design Breeding, Northeast Institute of Geography and Agroecology, Chinese Academy of Sciences, Changchun, 130102, PR 
China
b College of Chinese Medicinal Material, Jilin Agricultural University, Changchun, 130118, PR China
A R T I C L E I N F O
Keywords:
Large language models 
Vision-language models
Plant stress detection
Precision agriculture
Artificial intelligence in phenotyping
A B S T R A C T
The integration of Large Language Models (LLMs) with Vision-Language Models (VLMs) holds transformative 
potential for plant stress phenotyping, enhancing high-throughput crop monitoring, trait identification, and 
decision support. Traditional phenotyping methods, often reliant on manual assessments and task-specific Ma-
chine Learning (ML) models, face persistent limitations in scalability, adaptability, and contextual interpretation, 
especially under complex and overlapping stress conditions. VLMs address these challenges by combining deep 
visual recognition with contextual reasoning, enabling real-time analysis of multimodal inputs such as high-
resolution imagery, agronomic text data, and environmental sensor readings. Complementarily, LLMs 
contribute to text mining, semantic annotation of trait descriptors, and the integration of external knowledge via 
Retrieval-Augmented Generation (RAG), thereby enhancing the interpretability and adaptability of phenotyping 
workflows. This review critically evaluates the emerging role of integrating LLMs with VLMs in plant stress 
phenotyping, highlighting their applications in visual trait recognition, knowledge extraction, and autonomous 
decision-making. We synthesize current advances and identify key challenges, including data quality, domain-
specific generalization, model transparency, and equitable access to AI technologies. As one of the first 
comprehensive reviews on this topic, we propose a forward-looking framework that integrates LLMs, VLMs, and 
RAG systems to enable scalable, explainable, and user-centric phenotyping solutions. This interdisciplinary 
convergence offers a promising pathway toward sustainable and resilient AI-driven agriculture.
1. Introduction
Ensuring global food security amidst accelerating climate change, 
resource constraints, and population growth demands urgent innovation 
in sustainable agriculture [1,2]. A major challenge in this regard is plant 
stress, which significantly constrains agricultural productivity and arises 
from both biotic and abiotic factors. Biotic stresses, including pests, 
pathogens, and weeds, cause yield losses of 17 %–40 %. In contrast, 
abiotic stresses such as drought, extreme temperatures, heavy metal 
toxicity, and salinity can reduce yields by up to 50 %, depending on crop 
species and regional conditions [3,4]. While the combined impact of 
these stressors is substantial, exact global estimates remain challenging 
due to overlapping and interactive effects.
Despite considerable progress in plant breeding and agronomic in-
terventions, current approaches to plant stress phenotyping remain 
insufficient, particularly for rapid diagnosis and adaptive response to
multiple, co-occurring stressors in large-scale agricultural systems. 
Traditional stress detection methods, such as expert field assessments 
and visual inspections, are inherently labor-intensive, subjective, and 
poorly scalable, limiting their suitability for modern precision agricul-
ture [1,5]. Moreover, many stress-induced symptoms, such as leaf 
chlorosis, are nonspecific and overlapping across different stressors (e. 
g., drought vs nutrient deficiency), making accurate diagnosis in field 
conditions highly challenging [6]. Therefore, scalable, accurate, 
real-time stress monitoring systems are urgently needed to enable tar-
geted interventions, mitigate yield losses, and enhance crop resilience. 
Recent advances in Artificial Intelligence (AI), particularly Deep 
Learning (DL) and Large Language Models (LLMs), are opening un-
precedented opportunities for automated and scalable plant stress 
management [7–9]. DL-based approaches, particularly Convolutional 
Neural Networks (CNNs), have demonstrated high accuracy in plant 
disease detection under controlled conditions, with some studies
* Corresponding author.
E-mail address: fengxianzhong@iga.ac.cn (X. Feng).
Contents lists available at ScienceDirect
Plant Phenomics
journal homepage: www.sciencedirect.com/journal/plant-phenomics
https://doi.org/10.1016/j.plaphe.2025.100161
Received 17 April 2025; Received in revised form 20 December 2025; Accepted 27 December 2025
Available online 29 December 2025
2643-6515/© 2026 The Authors. Published by Elsevier B.V. on behalf of Nanjing Agricultural University. This is an open access article under the CC BY license 
(http://creativecommons.org/licenses/by/4.0/).
Plant Phenomics 8 (2026) 100161
===== PAGE 2 =====
reporting results exceeding 99 % on curated datasets [10]. However, 
such performance is not universal and depends heavily on factors such as 
dataset quality, class balance, and the specific crop-disease context. 
Nevertheless, unimodal CNN models that rely exclusively on image data 
face significant challenges, primarily due to the need for large, 
high-quality annotated datasets, which are often lacking for many crops 
and stress conditions [11,12]. These constraints limit their generaliz-
ability and limit their applicability in real-world agricultural environ-
ments, which are inherently diverse, dynamic, and data-scarce.
A promising approach to bridging the expertise gap and enabling 
more flexible phenotype analysis lies in the integration of LLMs and 
Vision-Language Models (VLMs) [13,14]. LLMs, such as OpenAI's GPT 
series [15], Google's PaLM-E [16], and Meta's LLaMA [14], are capable 
of advanced semantic reasoning, few-shot learning (i.e., learning to 
perform tasks using only a few labeled examples), and cross-domain 
generalization from minimal supervision. VLMs are multimodal sys-
tems that combine an image encoder (e.g., CNNs, Vision Transformers 
(ViTs), or MAMBA-based encoders) with a text encoder (typically 
transformer-based), enabling joint alignment of visual and textual rep-
resentations [17,18]. This design allows VLMs to perform cross-modal 
tasks such as image captioning, visual question answering, zero-shot 
classification, and image-based text generation [19–21]. Representa-
tive examples include CLIP, which aligns image-text embeddings at scale 
[22], and GroundingDINO, which enables open-set object detection 
through vision-language grounding [23]. In agricultural domains, VLMs 
facilitate real-time stress phenotyping by fusing high-resolution plant 
imagery with textual annotations and field records, offering enhanced 
interpretability and semantic trait recognition [24,25]. Their ability to 
generalize across stress conditions and crop types makes them especially 
valuable in data-limited settings. Furthermore, VLMs support automated 
dataset generation through captioning and annotation, streamlining 
phenotyping pipelines and reducing manual workload [13].
The integration of these large-scale AI systems represents a trans-
formative leap in plant stress diagnostics. By combining visual recog-
nition with natural language processing, integrated VLM-LLM 
frameworks can process heterogeneous data streams, such as drone 
imagery, sensor inputs (e.g., soil moisture and temperature), and farmer-
generated text, enabling context-aware, adaptive, and real-time stress 
detection [26–30]. The few-shot learning capabilities of LLMs further 
support generalization across diverse phenotyping scenarios, even in the 
absence of large labeled datasets [31,32]. Additionally, their integration 
with remote sensing and proximal sensing platforms allows for localized 
and temporally synchronized decision-making in precision agriculture. 
Despite delays introduced by sources such as satellite imagery or manual 
observations, the fusion of multimodal data streams provides a 
comprehensive spatiotemporal understanding of plant health and stress 
responses, thereby improving the timeliness, precision, and scalability of 
phenotyping interventions [33].
Despite these advances, significant barriers hinder the widespread 
deployment of VLMs in agriculture. These include the scarcity of high-
quality, multimodal datasets, high computational demands for 
training and deployment, and limited adaptability across languages and 
regions, which particularly affect smallholder and resource-limited 
farming systems [34–36]. To overcome these challenges, 
state-of-the-art Natural Language Processing (NLP) methods, such as 
Chain of Thought (CoT) prompting (guiding the model to reason 
step-by-step), Reinforcement Learning from Human Feedback (RLHF) 
(training the model using human preference signals), in-context learning 
(learning from examples provided in the prompt without updating 
model weights), and domain-specific instruction tuning (adapting the 
model using expert-written examples from a specific field), are being 
developed to enhance model alignment and reasoning in complex do-
mains [37]. Nonetheless, further innovation is needed to adapt these 
models to agricultural-specific data and knowledge structures. More-
over, ethical and societal issues, including data privacy, bias, and
equitable access, must be addressed to ensure the responsible adoption 
of AI in agriculture [38,39].
While VLMs and LLMs have gained significant attention in fields such 
as healthcare, robotics, and autonomous systems, their application to 
plant phenotyping, particularly under stress conditions, remains largely 
underexplored. To our knowledge, this is one of the first comprehensive 
reviews to examine how VLMs and LLMs, either independently or in 
synergy, can be applied across the whole plant stress phenotyping 
workflow, from visual trait recognition to intelligent decision support. 
This review critically evaluates the capabilities, limitations, and future 
directions of these models within the context of plant stress diagnostics. 
We highlight how LLMs can enhance vision-based systems through se-
mantic reasoning, knowledge retrieval, and the creation of user-friendly, 
farmer-accessible interfaces. By establishing a conceptual and technical 
foundation, this work aims to support future research and responsible 
deployment of scalable, explainable AI frameworks in agricultural 
phenotyping.
2. Deep Learning, Large Language Models, and recent AI 
advances in plant stress detection
Machine Learning (ML) has emerged as a powerful tool in plant stress 
research, allowing for the analysis of complex datasets through various 
approaches, including supervised, unsupervised, and Reinforcement 
Learning (RL) [40]. Supervised learning involves training models with 
labeled data, such as Multilayer Perceptrons (MLPs), Naive Bayes (NB), 
Support Vector Machines (SVMs), and Random Forests (RF), to predict 
or classify plant stress levels. Unsupervised learning, in contrast, works 
with raw or unlabeled data, applying techniques such as k-means clus-
tering, hierarchical clustering, and Principal Component Analysis (PCA) 
to discover underlying patterns and structures [41]. RL, which learns 
from interactions with the environment to maximize cumulative re-
wards, has been increasingly applied to plant phenomics [42], gene 
function prediction [43], and the identification of stress-responsive gene 
modules [44].
DL, a subset of ML, has become a leading approach in plant stress 
detection and classification due to its superior ability to automatically 
extract complex patterns from large datasets. Among DL methods, CNNs 
are particularly effective for image-based tasks, wher
