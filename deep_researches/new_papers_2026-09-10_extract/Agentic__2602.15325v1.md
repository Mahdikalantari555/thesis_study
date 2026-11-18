# 2602.15325v1.pdf

- Category: Agentic
- Pages: 10
- Path: D:\RS\Thesis\New_papers\Agentic\2602.15325v1.pdf

## Metadata

```json
{
  "/Author": "Zhixing Zhang; Jesen Zhang; Hao Liu; Qinhan Lv; Jing Yang; Kaitong Cai; Keze Wang",
  "/Creator": "arXiv GenPDF (tex2pdf:57610bf)",
  "/DOI": "https://doi.org/10.48550/arXiv.2602.15325",
  "/License": "http://creativecommons.org/licenses/by/4.0/",
  "/PTEX.Fullbanner": "This is pdfTeX, Version 3.141592653-2.6-1.40.28 (TeX Live 2025) kpathsea version 6.4.1",
  "/Producer": "pikepdf 8.15.1",
  "/TemplateVersion": "IJCAI.2026.0",
  "/Title": "AgriWorld:A World Tools Protocol Framework for Verifiable Agricultural Reasoning with Code-Executing LLM Agents",
  "/Trapped": "/False",
  "/arXivID": "https://arxiv.org/abs/2602.15325v1"
}
```

## First pages


===== PAGE 1 =====
AgriWorld: A World–Tools–Protocol Framework for Verifiable Agricultural
Reasoning with Code-Executing LLM Agents
Zhixing Zhang∗ ,jesen Zhang ∗ ,Hao Liu,Qinhan Lv,Jing Yang,Kaitong Cai,Keze
Wang†
Sun Yat-sen University
Abstract
Foundation models for agriculture are increas-
ingly trained on massive spatiotemporal data
(e.g., multi-spectral remote sensing, soil grids,
and field-level management logs) and achieve
strong performance on forecasting and moni-
toring. However, these models lack language-
based reasoning and interactive capabilities,
limiting their usefulness in real-world agro-
nomic workflows. Meanwhile, large language
models (LLMs) excel at interpreting and gen-
erating text, but cannot directly reason over
high-dimensional, heterogeneous agricultural
datasets. We bridge this gap with an agen-
tic framework for agricultural science. It pro-
vides a Python execution environment, AGRI-
WORLD, exposing unified tools for geospa-
tial queries over field parcels, remote-sensing
time-series analytics, crop growth simulation,
and task-specific predictors (e.g., yield, stress,
and disease risk). On top of this environment,
we design a multi-turn LLM agent, AGRO-
REFLECTIVE, that iteratively writes code, ob-
serves execution results, and refines its anal-
ysis via an execute–observe–refine loop. We
introduce AGROBENCH, with scalable data
generation for diverse agricultural QA span-
ning lookups, forecasting, anomaly detection,
and counterfactual “what-if” analysis. Exper-
iments outperform text-only and direct tool-
use baselines, validating execution-driven re-
flection for reliable agricultural reasoning.
1 Introduction
Large language models (LLMs) are increasingly used as
general-purpose assistants for scientific work: they can
follow complex instructions, explain concepts, summa-
rize documents, and generate code that automates parts of
an analysis [1]. Yet, in many scientific domains, answer-
ing even a seemingly simple question requires operating
∗Equal contribution.
†Corresponding author: kezewang@gmail.com
overhigh-dimensional, heterogeneous, and spatiotem-
poral numerical data—not purely textual context [2; 3].
This mismatch has motivated tool-augmented and code-
executing agents that connect LLMs to external pro-
grams and datasets, enabling conclusions to be grounded
in computation and verified through intermediate results
rather than surface-form text [4; 5; 6; 7; 8; 9 ]. Agri-
culture is a particularly compelling and challenging set-
ting for executable scientific assistants [10]. Modern
agronomic decision making relies on diverse data prod-
ucts, including multi-spectral remote sensing time se-
ries, soil and terrain grids, field-parcel boundaries, field-
level management logs, and local weather streams [11;
12; 13 ]. Practical questions are inherently spatiotem-
poral and unit-sensitive: they require parcel–pixel–grid
alignment, stage-specific temporal windows, and care-
ful handling of measurement scales [14; 15; 16; 17 ].
Meanwhile, foundation models trained on large agro-
nomic corpora can be effective for narrow predictive ob-
jectives (e.g., forecasting and monitoring) [18; 19 ], but
they often lack language-facing interfaces for interac-
tive analysis, “what-if” exploration, and transparent, in-
spectable reasoning steps [20]. Conversely, LLMs excel
at natural-language interaction but cannot natively ma-
nipulate structured agronomic datasets, and thus may
produce answers that are plausible yet difficult to ver-
ify [21; 22; 23] . The gap becomes evident in everyday
workflows. Consider a query such as:“Which parcels
are likely to experience water stress next week, and what
irrigation adjustment would mitigate the risk?”A reli-
able solution requires more than recalling facts. It must
(i) perform geospatial filtering and joins across entities
(fields, administrative regions, sensor footprints)[24; 25;
26], (ii) compute and visualize remote-sensing indica-
tors over time with correct aggregation windows [27],
(iii) incorporate soil properties and exogenous drivers
such as weather [28; 29 ], and (iv) run a simulator or
predictor to evaluate counterfactual interventions[30; 31;
32]. In practice, agronomists orchestrate an ecosys-
tem of tools—GIS operations, time-series analytics,
crop growth simulators, and task-specific models [33]
—and translate computational artifacts into actionable
recommendations[20; 34]. Without a programmatic in-
terface and an execution loop, an LLM has no principled
arXiv:2602.15325v1  [cs.AI]  17 Feb 2026
===== PAGE 2 =====
way to check coordinate systems, validate intermediate
computations, or correct subtle errors in spatial joins,
temporal windows, and unit conversions, making purely
text-based responses brittle and hard to trust for scien-
tific use[35; 36]. We propose an agentic framework for
agricultural science that makes LLM-based analysisex-
ecutable, auditable, and reproducible. Our design fol-
lows aWorld–Tools–Protocolabstraction.Worldpro-
vides a Python execution environment, AGRIWORLD,
which exposes unified APIs for core agricultural oper-
ations: (1) geospatial querying over field parcels and ad-
ministrative regions, (2) remote-sensing time-series an-
alytics and anomaly statistics, (3) crop growth simula-
tion with support for counterfactual interventions, and
(4) task-specific predictors such as yield, stress, and dis-
ease risk.Toolsin AGRIWORLDreturn inspectable inter-
mediate artifacts (e.g., tables, plots, and derived masks),
allowing analyses to be grounded in concrete compu-
tations and audited step-by-step.Protocolstandardizes
task specification and evaluation throughexecutable ref-
erences and checkerswhenever the underlying question
admits programmatic validation, enabling scalable and
reproducible comparisons. On top of AGRIWORLD, we
introduce AGRO-REFLECTIVE, a multi-turn LLM agent
that alternates between writing code, executing it, and
refining its analysis based on execution feedback [37].
This execution-driven reflection is crucial in agriculture,
where minor mistakes in coordinate systems, aggregation
windows, or units can invalidate the final conclusion[38;
5]. Rather than treating tool calls as one-shot add-ons
to generation, AGRO-REFLECTIVEuses intermediate ar-
tifacts as first-class signals to diagnose errors, revise hy-
potheses, and converge to a checkable solution. To evalu-
ate such agents systematically, we build a verifiable eval-
uation suiteon top of an existing agricultural bench-
markby converting questions into tool-grounded in-
stances with deterministic reference code and executable
checker functions. This suite covers a broad spectrum
of capabilities: basic lookups (indices, phenology, and
resource use), forecasting and monitoring, anomaly de-
tection, and counterfactual intervention analysis. Impor-
tantly, the executable design enables fine-grained diagno-
sis of failure modes (e.g., spatial misalignment, incorrect
temporal windows, unit errors, and ungrounded claims),
beyond coarse end-answer accuracy [39; 40].
The maincontributionsare three-fold:
•AGRIWORLD: an executable agricultural environ-
ment.We introduce a Python environment that uni-
fies geospatial querying, remote-sensing time-series
analytics, crop simulation, and task-specific predic-
tors through consistent APIs, enabling grounded and
auditable agronomic analyses.
•AGRO-REFLECTIVE: an execution-driven reflec-
tive agent.We propose a multi-turn agent that iter-
atesexecute–observe–refine, using intermediate arti-
facts to self-correct and produce tool-grounded analy-
sis traces rather than one-shot text.
•A verifiable evaluation suite with executable check-
ers.Built on top of an existing benchmark, we pro-
vide a scalable task generation and scoring pipeline
with deterministic reference programs and executable
checkers spanning lookups, forecasting, anomaly de-
tection, and counterfactual interventions, enabling re-
producible comparisons against text-only and direct
tool-use baselines.
2 Related Work
Tool-augmented LLM agents and executable reason-
ing.A growing line of work augments LLMs with ex-
ternal tools (APIs, code interpreters, and symbolic mod-
ules) [41; 42; 43]to ground answers in computation rather
than purely textual generation [44; 45; 46; 47; 48; 49;
50]. Such systems typically couple a planner with tool in-
vocation, enabling multi-step problem solving over struc-
tured resources and producing intermediate results that
can be inspected. Our work aligns with this direction but
targets a domain where correctness hinges on spatiotem-
poral alignment, unit consistency, and reproducible exe-
cution traces. We thus emphasize (i) a domain-grounded
environment that exposes typed operations and auditable
artifacts, and (ii) a protocol that makes evaluation ex-
ecutable whenever possible, beyond text-only answer
matching.
Scientific and data-centric agents for domain work-
flows.Recent “scientific assistants” and “data analysis
agents” aim to automate parts of research workflows by
writing code, operating over datasets, and iteratively re-
fining hypotheses using execution feedback [51; 52; 53;
54; 55]. Parallel efforts in geospatial analytics, remote
sensing pipelines, and decision-support systems have de-
veloped mature toolchains for spatial joins, raster pro-
cessing, and time-series modeling, but these pipelines are
typically engineered for experts and are not language-
interactive[56; 57; 58; 59 ]. We bridge these threads by
providing an agricultural world model (AGRIWORLD)
that unifies geospatial, remote-sensing, weather, and
management data with simulation/prediction backends,
and by designing an execution-driven agent (AGRO-
REFLECTIVE) that treats debugging signals (e.g., CRS
mismatches, window drift) as first-class feedback for
self-correction.
Benchmarks and verifiable evaluation for agentic sys-
tems.Evaluating agents remains challenging because
free-form responses can be plausible yet incorrect [60],
and failures often stem from latent mistakes in interme-
diate steps. Existing benchmarks commonly score fi-
nal textual answers, sometimes with reference solutions,
but often without executable checkers that can validate
constraints, tolerances, and counterfactual claims [61].
Complementary work has proposed programmatic eval-
uation, unit tests, or environment-based scoring to en-
able reproducible assessment and failure diagnosis [62].
Our protocol follows this verifiable-evaluation philoso-
phy by compiling questions into tool-grounded instances
with deterministic reference programs and executable
checker functions, enabling scalable comparison across
===== PAGE 3 =====
agent variants and fine-grained attribution of errors (spa-
tial misalignment, temporal window errors, unit mis-
matches, and ungrounded claims).
3 Method
3.1 The World–Tools–Protocol Framework
Current LLMs lack the intrinsic capability to process
high-dimensional spatiotemporal data[63]. To bridge this
gap, we formalize an agricultural assistant not merely
as a chatbot, but as an agentAoperating within a rig-
orousWorld–Tools–Protocolframework (see Figure 1).
This framework consists of an executable environment
E(AGRIWORLD), a set of grounded functional toolsF,
and a verifiable specification protocolV.
As illustrated in Figure 1, the workflow initiates from
theState SpaceS, which encapsulates diverse agricul-
tural data types includingGeographical Locationand
Wind Field Representation. These inputs are processed
through specialized tools forSpatial Query,Spatio-
temporal Analysis,Crop Simulation, andTask Pre-
diction. To ensure consistency across heterogeneous
sources, the system employs aCoordinate Alignment
mechanism that converts the initialPre-training Se-
quenceinto a standardizedAligned Sequence(denoted
asg→kg). Crucially, the reasoning process is not open-
ended; anAgentactively monitors the execution timeline
to detect andFixpotentialTemporal Errors. The agent
enforces strict verification pr
