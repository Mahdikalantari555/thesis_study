# REMSA Foundation Model Selection for Remote Sensing via a Constraint-Aware Agent.pdf

- Category: Agentic
- Pages: 29
- Path: D:\RS\Thesis\New_papers\Agentic\REMSA Foundation Model Selection for Remote Sensing via a Constraint-Aware Agent.pdf

## Metadata

```json
{
  "/Author": "Binger Chen; Tacettin Emre Bök; Behnood Rasti; Volker Markl; Begüm Demir",
  "/Creator": "arXiv GenPDF (tex2pdf:a6404ea)",
  "/DOI": "https://doi.org/10.48550/arXiv.2511.17442",
  "/License": "http://arxiv.org/licenses/nonexclusive-distrib/1.0/",
  "/PTEX.Fullbanner": "This is pdfTeX, Version 3.141592653-2.6-1.40.28 (TeX Live 2025) kpathsea version 6.4.1",
  "/Producer": "pikepdf 8.15.1",
  "/Title": "REMSA: Foundation Model Selection for Remote Sensing via a Constraint-Aware Agent",
  "/Trapped": "/False",
  "/arXivID": "https://arxiv.org/abs/2511.17442v3"
}
```

## First pages


===== PAGE 1 =====
Remsa: Foundation Model Selection for Remote Sensing via
a Constraint-Aware Agent
Binger Chen1 ⋆, Tacettin Emre Bök2*, Behnood Rasti3, Volker Markl3, and Begüm Demir3
1 Humboldt-Universität zu Berlin, Berlin, Germany
binger.chen@hu-berlin.de
2 5U AI, Munich, Germany
tacettinemre1@gmail.com
3 Technische Universität Berlin & BIFOLD, Berlin, Germany
behnood.rasti@gmail.com, {volker.markl,demir}@tu-berlin.de
Abstract.Foundation Models (FMs) are increasingly integrated into remote sensing (RS)
pipelines for applications such as environmental monitoring, disaster assessment, and land-use
mapping. These models include unimodal vision encoders trained in a single data modality
and multimodal architectures trained in multiple sensor modalities, such as synthetic aper-
ture radar (SAR), multispectral, and hyperspectral imagery, or jointly in image-text pairs in
vision-language settings. FMs are adapted to diverse perception tasks, such as semantic seg-
mentation, image classification, change detection, and visual question answering, depending
on their pretraining objectives and architectural design. However, selecting the most suit-
able remote sensing foundation model (RSFM) for a specific task remains challenging due
to scattered documentation, heterogeneous formats, and complex deployment constraints.
To address this, we first introduce the RSFM Database (RS-FMD), the first structured
and schema-guided resource covering over 160 RSFMs trained on various data modalities,
spanning different spatial, spectral, and temporal resolutions, considering different learn-
ing paradigms. Built uponRS-FMD, we further presentRemsa(Re mote-sensingM odel
SelectionA gent), a constraint-aware agent that enables automated RSFM selection from nat-
ural language queries.Remsacombines structured FM metadata grounding with task-aware
orchestration for retrieval, clarification, ranking, and explanation. In detail, it interprets user
input, clarifies missing constraints, ranks models via in-context learning, and provides trans-
parent justifications. Our system supports various RS tasks and data modalities, enabling
personalized, reproducible, and efficient FM selection. To evaluateRemsa, we construct
a benchmark of 100 expert-verified RS query scenarios. Each query is evaluated across 4
systems and 3 LLM backbones, with the top-3 selected models assessed by domain experts
using a fixed suitability rubric. This results in3,000expert-scored task–system–model con-
figurations under our rubric-based expert evaluation protocol.Remsaoutperforms multiple
baselines, including naive agent-based method, dense retrieval, and unstructured retrieval
augmented generation approaches, showing its practical utility in real decision-making ap-
plications.Remsaoperates entirely on publicly available metadata of open source RSFMs,
without accessing private or sensitive data. Our code and data are publicly available at:
https://github.com/be-chen/REMSA.
Keywords:Remote Sensing·Foundation Models·Model Selection·Foundation Model
Database·Agents
⋆ Work done while the author was affiliated with Technische Universität Berlin & BIFOLD.
arXiv:2511.17442v3  [cs.CV]  29 Jun 2026
===== PAGE 2 =====
2 B. Chen et al.
1 Introduction
With the growing availability of remote sensing (RS) missions and their onboard sensors (e.g.,
Sentinel-2 [7], Sentinel-1 [34], EnMAP [10]), RS plays an increasingly important role in many
applications such as agriculture, disaster response, urban development, and biodiversity monitor-
ing. These applications increasingly rely on foundation models (FMs) that can generalize across
various RS data modalities with different spatial, spectral, and temporal resolutions, geospatial
extents and applications, while being transferable and effective even with limited labeled data in
downstream RS analysis tasks. Recently, numerous FMs have emerged in the RS domain, offering
powerful capabilities for modeling complex RS data. These models include vision-only encoders
trained on single or multiple RS data modalities (e.g., MMEarth [22], OmniSat [2], MA3E [17])
and vision–language models (VLMs) trained with paired RS data modalities and text (e.g., Geo-
Text [4], LHRS-Bot [21]). These models are pretrained on large-scale and heterogeneous RS datasets
encompassing a diverse range of sensor modalities, including RGB, multispectral, hyperspectral,
synthetic aperture radar (SAR), and light detection and ranging (LiDAR), across multiple spatial
and temporal resolutions. Each FM exhibits its strengths in distinct downstream RS tasks, such as
classification, object detection, change detection, captioning, and visual question answering (VQA).
For instance, in practical RS workflows, change detection typically relies on multitemporal SAR
or optical data inputs, while fine-grained land cover mapping often benefits from high-resolution
optical imagery. This diversity brings new possibilities for multi-modal RS applications, but it also
raises the challenge of selecting the most suitable FM for a given task with data modality and
operational constraints.
Despite these advances, selecting a suitable FM for a specific RS task remains a challenge.
RS practitioners must balance diverse constraints such as the available data modalities and vol-
ume, geographic coverage, computational resources, and task-specific evaluation priorities. These
constraints have been shown to significantly influence RSFM generalization and robustness [25,26].
With hundreds of remote sensing foundation models (RSFMs) now publicly available [11,16] and no
unified structured schema to organize their properties (such as model architectures, training data, or
reported performance), the selection process is often manual, which is time-consuming, error-prone,
and difficult to reproduce. Existing approaches rely on searching across scattered repositories and
publications, manually parsing papers and model cards, and running exhaustive experiments [1,27],
all without guaranteed reproducibility or transparency. Even public RS benchmarks [11,13,30]
mainly compare model accuracy on fixed applications, but they do not address the upstream selec-
tion problem of identifying suitable candidate FMs under user-specific modalities, data availability,
computebudgets,anddeploymenttrade-offs.Thismakesaunified,machine-readabledatabase(DB)
of RSFMs a necessary foundation for any systematic selection and automation.
Recent advances in large language model (LLM) agents have shown the potential of integrating
language models with external tools and structured workflows to support complex tasks [8,12,
18,35]. However, most existing agents target general-purpose question answering or conversational
assistance. To the best of our knowledge, no prior work has developed a domain-specific agent for
FM selection in operational, constraint-heavy RS scenarios. In particular, RS tasks involve complex
trade-offs across sensors, spatial, spectral, and temporal resolutions, as well as data availability.
Existing LLMs lack the domain knowledge and structured access to model documentation to address
these constraints. Hence, such an agent must provide more robust and interpretable solutions.
In this work, we first introduce the RSFM Database (RS-FMD), the first schema-guided re-
source of over 160 RSFMs, covering various data modalities, pretraining strategies, and reported
===== PAGE 3 =====
Remsa: Foundation Model Selection for Remote Sensing via a Constraint-Aware Agent 3
Fig. 1:Architecture ofRemsafor remote sensing foundation model selection.Remsaparses an un-
structured user query, grounds the extracted constraints inRS-FMDand task memory, and orchestrates
retrieval, ranking, clarification, and explanation tools to produce justified model recommendations.
benchmark results. Built onRS-FMD, we proposeRemsa, a first LLM-based agent for auto-
mated FM selection in RS. As shown in Fig. 1,Remsais a modular agent that supports FM
selection through structured query interpretation and task-aware tool invocation. It extracts user
intent from free text input and converts it into constraints. Based on the task state, the agent
orchestrates tools for retrieval fromRS-FMD, ranking FMs, interactive clarification, and justified
explanation. A lightweight memory mechanism further enhances accuracy and personalization. To
evaluateRemsa, we build a new benchmark of realistic user queries and establish a rubric-based
expert evaluation protocol that scores the suitability of selected FMs under user-specified con-
straints. We also implement a set of carefully constructed baselines, ensuring fair and meaningful
comparisons withRemsa.Remsais designed to support a broad range of users, including RS
scientists, machine learning researchers, and industry practitioners who need to identify suitable
RSFMs for their tasks. BecauseRemsaaccepts free-text queries and incorporates structured in-
terpretation together with multi-turn clarification, it can assist even non-experts who may not be
familiar with RS modalities or FM architectures. This makesRemsasuitable for both exploratory
use by practitioners and rigorous FM selection in research settings. AlthoughRemsaadopts a
modular agent design rather than proposing a new visual backbone, our contribution is method-
ological. We formalize RSFM selection as an under-supported stage in practical RS or computer
vision pipelines: deciding how FMs should be compared, selected, and deployed under modality,
data, compute, and application constraints before downstream adaptation. In summary, we make
the followingcontributions:
–We introduceRS-FMD, the first structured and schema-guided DB of over160RSFMs. We will
release it as a community resource with continuous maintenance and updates.
–We proposeRemsa, a modular LLM agent that combines structured metadata grounding, dense
retrieval, in-context ranking, clarification, explanation, memory augmentation components, and
a task-aware orchestration mechanism to support complex FM selection in real RS settings.
–We construct a new benchmark dataset and rubric-based evaluation protocol for FM selection in
RS, comprising 100 realistic query scenarios and3,000expert-scored evaluations across systems,
LLM backbones, and selected models.
===== PAGE 4 =====
4 B. Chen et al.
2 Related Work
Foundation Models and Model Selection.Due to the rapid emergence of FMs, there has
been extensive research into their capabilities and benchmarks [3,6,36]. In RS, recent surveys and
benchmarks [11,27,37] have systematically cataloged FMs and evaluated their performance on
applications such as land cover classification, wildfire scar segmentation, urban change detection,
visual question answering, etc. However, these works primarily focus on descriptive analysis or
standardized evaluation, offering limited support for automated FM selection. Large-scale evalua-
tions such as GEO-Bench-2 [30] further highlight that RSFM performance varies strongly across
capability dimensions, but they mainly evaluate models under fixed benchmark protocols rather
than addressing the upstream problem of selecting suitable FMs under user-specific constraints.
Other work also shows that pretraining data coverage (geographic and sensor diversity) strongly
affects RSFM generalization [25,26]. While current benchmarks document these properties, they
do not use them to guide model choice, further motivating automated FM selection. Addition-
ally, recent capabilities encoding approach estimates a model’s performance on unseen downstream
tasks, reducing the need for exhaustive fine-tuning [1]. Although such performance prediction meth-
ods provide valuable tools for comparative evaluation, they are complementary to our setting. They
rely on standardized transfer evidence and do not address end-to-end FM selection from open-ended
user queries involving modalities, data availability, compute budgets, and deployment constraints.
Moreover, previous surveys and benchma
