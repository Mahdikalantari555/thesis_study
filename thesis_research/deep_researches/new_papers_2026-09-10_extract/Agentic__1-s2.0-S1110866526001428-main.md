# 1-s2.0-S1110866526001428-main.pdf

- Category: Agentic
- Pages: 18
- Path: D:\RS\Thesis\New_papers\Agentic\1-s2.0-S1110866526001428-main.pdf

## Metadata

```json
{
  "/Creator": "Elsevier",
  "/CrossMarkDomains[1]": "elsevier.com",
  "/CreationDate--Text": "1st July 2026",
  "/robots": "noindex",
  "/ElsevierWebPDFSpecifications": "7.0.1",
  "/ModDate": "D:20260701175130Z",
  "/doi": "10.1016/j.eij.2026.101025",
  "/Title": "From evolution to autonomous modeling: need-driven self-system and intelligent agent self-evolution for remote sensing detection",
  "/Keywords": "Autonomous Intelligence,Need-Driven Self-System Structural Model,Self-evolution model of intelligent agents,Remote sensing,Object detection",
  "/CreationDate": "D:20260701120458Z",
  "/Producer": "Acrobat Distiller 8.1.0 (Windows)",
  "/Subject": "Egyptian Informatics Journal, 35 (2026) 101025. doi:10.1016/j.eij.2026.101025",
  "/CrossMarkDomains[2]": "sciencedirect.com",
  "/Author": "Bowen Sun"
}
```

## First pages


===== PAGE 1 =====
Full Length Article
From evolution to autonomous modeling: need-driven self-system and 
intelligent agent self-evolution for remote sensing detection
Bowen Sun
a
, Xiaofeng Wang
b
, Mengqi Gao
a , **
, Yi Du
a
, Shi Dong
c , *
a
School of Computer and Information Engineering, Shanghai Polytechnic University, Shanghai 201209, China
b
College of Information Engineering, Shanghai Maritime University, Shanghai 201306, China
c
School of Computer Science and Technology, Zhoukou Normal University, Zhoukou 466001, China
ARTICLE INFO
Keywords:
Autonomous Intelligence
Need-Driven Self-System Structural Model
Self-evolution model of intelligent agents
Remote sensing
Object detection
ABSTRACT
Artificial General Intelligence (AGI) has developed rapidly with the rise of large language models and computer 
vision. However, existing approaches remain highly dependent on massive datasets and computational resources, 
which prevents them from achieving true autonomous intelligence. To address this limitation, we propose a 
Need-Driven Self-System Model inspired by organism evolutionary learning. Building upon this model and the 
reinforcement learning model, we present the Self-evolution model of intelligent agents, it constructs a self- 
adaptive framework to enable intelligent agents to emulate the learning mechanisms of biological organisms 
and humans. A key feature of this framework is its supports for unsupervised autonomous learning without heavy 
reliance on external supervision. To validate this approach, we employed our Self-evolution model of intelligent 
agents to guide the construction of a new model for remote sensing image object detection, subsequently con -
ducting experiments to verify its feasibility. Experimental results demonstrate that the proposed method achieves 
competitive performance without dependence on large-scale labelled data. These findings demonstrate that the 
framework provides a promising alternative pathway toward autonomous intelligence, offering not only theo -
retical insights, but also practical applicability in real-world tasks.
1. Introduction
The pursuit of Artificial General Intelligence (AGI) constitutes a 
fundamental goal in computer science, tracing its origins to Alan 
Turing's seminal work in the 1940 s on computing machinery and 
intelligent behavior [1] . Since then, principles inspired by neuroscience 
— including neural network structures [2] , synaptic plasticity [3] , and 
neural dynamics [4,5] — have driven remarkable progress in replicating 
aspects of human intelligence within artificial systems. In recent years, 
large language models (LLMs) have demonstrated unprecedented suc -
cess in natural language processing (NLP), enabling machines to 
converse with humans, solve mathematical problems, generate visual 
content, and follow user reasoning chains [6 – 8] . Empirical studies 
further benchmark state-of-the-art AI models such as ChatGPT-3.5, 
ChatGPT-4.0, and Google Gemini, demonstrating impressive reasoning 
and problem-solving capabilities across specialized domains [9] . Simi -
larly, in computer vision (CV), models such as Segment Anything Model 
(SAM) aim to unify downstream tasks through large-scale training [10] . 
Despite these advances, the diversity of CV problems and the scarcity of 
annotated data for many domains still pose significant challenges.
Notwithstanding significant advances, contemporary approaches 
remain constrained by several critical limitations. Hierarchical 
reasoning model [11] and comprehensive surveys on LLMs for AGI [12]
suggest that existing methods are heavily dependent on large-scale 
datasets and extensive pre-training, suffer from limited generalization 
to novel tasks, and lack intrinsic mechanisms for truly autonomous, 
unsupervised learning and evolutionary adaptation. In the domain of 
computer vision, even state-of-the-art models such as the Large Vision 
Diffusion Transformer(LaVin-DiT) [13] , unified multimodal framework 
for general low-level vision(Lumina-OmniLV) [14] are predominantly 
task-specific and contingent upon the availability of large-scale anno -
tated datasets, thereby restricting their capacity to generalize across 
diverse visual tasks. Overall, these limitations highlight a fundamental 
research gap: currently, there is a lack of models capable of self-driven, 
unsupervised evolution. Here, the term “ evolution ” refers to processes 
analogous to the learning and adaptive mechanisms observed in 
* Corresponding author.
** Corresponding author.
E-mail addresses: mqgao@sspu.edu.cn (M. Gao), njbsok@163.com (S. Dong). 
Contents lists available at ScienceDirect
Egyptian Informatics Journal
journal homepag e: www.scien cedirect.co m
https://doi.org/10.1016/j.eij.2026.101025
Received 18 August 2025; Received in revised form 10 September 2025; Accepted 27 June 2026  
Egyptian Informatics Journal 35 (2026) 101025 
Available online 1 July 2026 
1110-8665/© 2026 THE AUTHORS. Published by Elsevier BV on behalf of Faculty of Computers and Artiϧcial Intelligence, Cairo University. This is an open access 
article under the CC BY-NC-ND license ( http://creativecommons.org/licenses/by-nc-nd/4.0/ ). 
===== PAGE 2 =====
biological and human systems. To bridge this gap, we must move beyond 
the traditional reliance on large-scale pre-training and domain-specific 
engineering. Instead, theoretical mechanisms should be developed to 
enable artificial agents to autonomously learn and evolve.
In addressing the challenges of autonomous learning, this study 
identifies that the foundation of self-driven evolution in organisms and 
humans lies in intrinsic needs. Building upon this insight, we propose a 
theoretical model of a need-driven self-system structure, which for -
malizes the internal evolution mechanisms of organisms and humans 
through conceptual modeling and mathematical representation. This 
self-system structure is then integrated with a reinforcement learning 
framework, leveraging the need selection and evaluation mechanisms to 
enhance the agent’s loss function. The result is a need-driven intelligent 
agent self-evolution model, whose feasibility and effectiveness are 
verified through comprehensive simulation experiments.
To further demonstrate the model’s generalizability, it is applied to a 
practical computer vision task: object detection in Synthetic Aperture 
Radar (SAR) images. This application validates the robustness of the 
proposed theoretical framework and its capacity to guide modeling in 
complex real-world scenarios.
The primary innovations of this work are as follows: 
1. Based on theoretical foundations from the evolutionary history of 
biology and neuroscience, the paper proposes a theoretical model of 
a need-driven self-system structure, describing the evolutionary 
processes of organisms and humans through mathematical formulas.
2. The paper combines the reinforcement learning model of intelligent 
agents with the proposed self-system structure model, presenting the 
need-driven intelligent agent self-evolution model. Simulation ex -
periments are conducted to verify the effectiveness of the theory and 
model.
3. Following the methodology and reasoning logic of the self-system 
structure model and self-evolution model, the paper applies them 
to guide the modeling of ship detection tasks in Synthetic Aperture 
Radar (SAR) images. The constructed model is then experimentally 
validated using publicly available datasets.
The structure of the paper is organized into several sections. The 
second part primarily introduces the research progress on large models 
for general visual tasks and reinforcement learning models related to 
intrinsic needs. The third part presents the theoretical directions and 
model structures corresponding to each innovation point. The fourth 
part conducts corresponding simulation experiments and experimental 
validations with real datasets, followed by results analysis. The fifth part 
concludes and discusses the findings of this paper.
2. Related work
The development of AGI has been profoundly shaped by advances in 
natural language processing. The landmark GPT-3 [15] introduced few- 
shot learning capabilities, establishing a cornerstone for the develop -
ment of large-scale language models and AGI. Building upon this foun -
dation, Lei et al. [16] proposed an open-source Large Language Model to 
surpass GPT-4 Turbo and GPT-4o(AutoCoder), a framework that en -
hances code large language models by leveraging Agent-Interaction 
Execution-Verified(AIEV-Instruct) to strengthen instruction-following 
in code generation tasks. Extending this trajectory, Xu et al. [17]
demonstrated that large language models without grounding capture 
non-sensorimotor aspects of human concepts but fail to accurately 
represent sensorimotor features, highlighting the importance of multi -
modal learning. These breakthroughs in NLP established the foundation 
for the design of large vision models. In the field of computer vision, 
Radford et al. [18] transfered nontrivially to most tasks and was often 
competitive with a fully supervised baseline without the need for any 
dataset specific training. Rombach et al. [19] proposed Latent Diffusion 
Models(LDMs), which perform diffusion in the latent space of pretrained 
autoencoders to achieve high-quality, flexible, and computationally 
efficient image generation for tasks such as inpainting, class-conditional 
synthesis, text-to-image translation, and super-resolution. The SAM 
proposed by Kirillov et al. [10] achieves zero-shot image segmentation 
by leveraging a promptable foundation model capable of generalizing to 
arbitrary objects without task-specific training. Wu et al. [20] proposed 
an end-to-end generalist multimodal large model (MLLM) for hundreds 
of vision-language tasks(VisionLLM v2), to unify visual perception, un -
derstanding, and generation within a single framework. Wu et al. [21]
proposed a unified image generation model that excels in multiple do -
mains(OmniGen2), an open-source generative model with separate text 
and image decoders, enabling unified solutions for text-to-image, image 
editing, and in-context generation with strong performance.
With the widespread adoption and research of general intelligent 
models in the field of computer vision, there have been corresponding 
explorations specifically in the domain of remote sensing images. 
Savathrakis et al. [22] proposed a three-component method leveraging 
SAM for Horizontal Bounding Boxes (HBB-based) object segmentation, 
morphological filtering for artifact removal, and contour detection for 
optimal Oriented Bounding Boxes(OBB) generation. Sun et al. [23]
proposed a generative self-supervised learning framework(RingMo), to 
bridge the domain gap and enhance generalization in remote sensing 
image interpretation by leveraging large-scale unlabeled data. Hong 
et al. [24] proposed SpectralGPT, a 3D generative pre-trained trans -
former for spectral remote sensing data, which achieves breakthrough 
performance on four downstream tasks through progressive training and 
multi-target reconstruction. Chen et al. [25] proposed RSPrompter, a 
prompt learning method that enables SAM to achieve automated 
semantic-aware instance segmentation in remote sensing images 
without manual guidance. Hu et al. [26] proposed RSICap, a human- 
annotated remote sensing image-text dataset, to enable effective 
training of large vision-language models for comprehensive scene and 
object understanding in remote sensing applications. It is not difficult to 
observe that the above-mentioned general intelligent models all rely on 
large-scale data for training. This approach imposes extremely high re -
quirements on computing power and costs. However, it does not high -
light the crucial element of model autonomy.
Building on the remarkable advances of large language models and 
vision foundation models, it is increasingly evide
