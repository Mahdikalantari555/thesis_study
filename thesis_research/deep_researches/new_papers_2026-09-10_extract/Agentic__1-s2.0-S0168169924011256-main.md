# 1-s2.0-S0168169924011256-main.pdf

- Category: Agentic
- Pages: 23
- Path: D:\RS\Thesis\New_papers\Agentic\1-s2.0-S0168169924011256-main.pdf

## Metadata

```json
{
  "/Creator": "Elsevier",
  "/CrossMarkDomains[1]": "elsevier.com",
  "/CrossmarkMajorVersionDate": "2010-04-23",
  "/CreationDate--Text": "8th February 2025",
  "/ElsevierWebPDFSpecifications": "7.0.1",
  "/robots": "noindex",
  "/ModDate": "D:20250208021002Z",
  "/Author": "Nijhum Paul",
  "/doi": "10.1016/j.compag.2024.109734",
  "/Keywords": "Plant stress,Computer vision,Deep learning,Image processing,Imaging sensor,Precision agriculture",
  "/Producer": "Acrobat Distiller 8.1.0 (Windows)",
  "/CreationDate": "D:20250208001126Z",
  "/Title": "Deep learning for plant stress detection: A comprehensive review of technologies, challenges, and future directions",
  "/Subject": "Computers and Electronics in Agriculture, 229 (2025) 109734. doi:10.1016/j.compag.2024.109734",
  "/CrossMarkDomains[2]": "sciencedirect.com",
  "/CrossmarkDomainExclusive": "true"
}
```

## First pages


===== PAGE 1 =====
Computers and Electronics in Agriculture 229 (2025) 109734
Available online 13 December 2024
0168-1699/© 2024 The Authors. Published by Elsevier B.V. This is an open access article under the CC BY-NC-ND license (http://creativecommons.org/licenses/by-
nc-nd/4.0/).
Deep learning for plant stress detection: A comprehensive review of 
technologies, challenges, and future directions
Nijhum Paul
a , b
, G.C. Sunil
a
, David Horvath
c
, Xin Sun
a , *
a
Department of Agricultural and Biosystems Engineering, North Dakota State University, Fargo, ND 58108, USA
b
Genomics, Phenomics and Bioinformatics program, North Dakota State University, Fargo, ND 58108, USA
c
USDA-ARS-ETSARC, Weed and insect biology unit, Fargo, ND 58102, USA
ARTICLE INFO
Keywords:
Plant stress
Computer vision
Deep learning
Image processing
Imaging sensor
Precision agriculture
ABSTRACT
Deep learning (DL)-based systems have emerged as powerful methods for the diagnosis and treatment of plant 
stress, offering high accuracy and efficiency in analyzing imagery data. This review paper aims to present a 
thorough overview of the state-of-the-art DL technologies for plant stress detection. For this purpose, a systematic 
literature review was conducted to identify relevant articles for highlighting the technologies and approaches 
currently employed in the development of a DL-based plant stress detection system, specifically the advancement 
of image-based data collection systems, image preprocessing techniques, and deep learning algorithms and their 
applications in plant stress classification, disease detection, and segmentation tasks. Additionally, this review 
emphasizes the challenges and future directions in collecting and preprocessing image data, model development, 
and deployment in real-world agricultural settings. Some of the key findings from this review paper are: Training 
data: (i) Most plant stress detection models have been trained on Red Green Blue (RGB) images; (ii) Data 
augmentation can increase both the quantity and variation of training data; (iii) Handling multimodal inputs (e. 
g., image, temperature, humidity) allows the model to leverage information from diverse sources, which can 
improve prediction accuracy; Model Design and Efficiency: (i) Self-supervised learning (SSL) and Few-shot 
learning (FSL)-based methods may be better than transfer learning (TL)-based models for classifying plant 
stress when the number of labeled training images are scarce; (ii) Custom designed DL architectures for a specific 
stress and plant type can have better performance than the state-of-the-art DL architectures in terms of efficiency, 
overfitting, and accuracy; (iii) The multi-task learning DL structure reuses most of the network architecture while 
performing multiple tasks (e.g., estimate stress type and severity) simultaneously, which makes the learning 
much faster; Application and Practicality: (i) Training data collected from different growth settings or environ -
mental conditions is important to increase the generalizability of the DL model; (ii) Overlapping stress symptoms 
can confuse the DL model; overlapping stress symptoms can be identified as a separate label such as “ others ” to 
solve this problem; (iii) Plant stress detection apps should have offline accessibility because remote field areas 
may not have internet access. This review can help shape the development of novel approaches, strategies, and 
applications that address the present gaps and challenges in plant stress detection.
Abbreviations: AI, Artificial Intelligence; AWSR, Accuracy of water stress recognition; AWTR, Accuracy of three water treatments recognition; CAE, Convolutional 
autoencoders; C-Drop, Clustering-based drop; CNN, Convolutional Neural Network; CWSI, Crop Water Stress Index; DCNN, Deep convolutional neural network; DL, 
Deep learning; ELISA, Enzyme-linked immunosorbent assay; FCN, Fully convolutional neural network; FSL, Few shot learning; GAN, Generative adversarial network; 
IDC, Iron deficiency chlorosis; IoU, Intersection over Union; ITK-net, “ image-text ” multi-modal collaborative representation and knowledge assistance network; 
LSTM, Long short-term memory; MCE, Multiscale conformer encoder; ML, Machine learning; MTL, Multi-task learning; NasNet, Neural Architecture Search Network; 
NDVI, Normalized difference vegetation index; NearIR, Near-infrared; PRISMA, Preferred reporting items for systematic reviews and meta -analyses; PSPNet, Pyramid 
Scene Parsing Network; RCNN, Region-Based Convolutional Neural Network; ResNet, Residual network; RGB, Red Green Blue; SMOTE, Synthetic minority over -
sampling technique; sRN, Simple recurrent network; SSD, Single shot detector; SSL, Self-supervised learning; SVM, Support vector machine; TL, Transfer learning; 
UAV, Unmanned aerial vehicle; UGV, Unmanned ground vehicle; VGG, Visual geometry group; ViT, Vision Transformer; YOLO, You Only Look Once.
* Corresponding author.
E-mail address: xin.sun@ndsu.edu (X. Sun). 
Contents lists available at ScienceDirect
Computers and Electronics in Agriculture
journal homep age: www. elsevier.com/ locate/comp ag
https://doi.org/10.1016/j.compag.2024.109734
Received 23 July 2024; Received in revised form 14 November 2024; Accepted 28 November 2024  
===== PAGE 2 =====
Computers and Electronics in Agriculture 229 (2025) 109734
2
1. Introduction
In recent years, image-based deep learning models (DL) have 
demonstrated remarkable success in precision agriculture, including 
yield prediction, phenotyping, weed detection, soil nutrient and field 
condition monitoring, irrigation management, and plant stress detec -
tion. Plant stress is one of the greatest hazards to crops, significantly 
reducing both quality and production ( Cattivelli et al., 2008 ). Therefore, 
rapid and accurate diagnosis of plant stress is urgently needed in crop 
measurement ( Gao et al., 2020b ). DL has emerged as a powerful tool for 
plant stress detection and monitoring through its advanced capabilities 
for analyzing and interpreting complex patterns in plant images and 
spectral data. DL-based stress detection systems can support farmers in 
making prompt, well-informed decisions that can significantly enhance 
the profitability, quality, and health of their crops. Additionally, DL can 
reduce the subjectiveness in measures of phenotypic responses of plants 
to treatments and thus improve scientific analyses.
The selection of DL architecture depends on input data, such as the 
varied complexities of visual symptoms exhibited by different plant 
stressor types. Some plant stressors have spatially localized effects, such 
as localized pest damage or disease lesions, while others affect the entire 
plant or field uniformly, such as drought stress. Plant stressors can be 
categorized into biotic and abiotic factors ( Fig. 1 ). Biotic stress factors 
include pathogens such as fungi, bacteria, viruses, and pests that infect 
plants, leading to a wide range of symptoms, including discoloration, 
wilting, and even plant death ( Georgieva and Vassileva, 2023 ). Abiotic 
stress encompasses environmental conditions that limit plant growth, 
such as extreme temperature, drought, flooding, salinity, metal, and 
nutrients (Y. Zhang et al., 2023 ). These stressors can adversely affect 
plant metabolism, physiological processes, and overall growth, leading 
to reduced yield and crop losses. It is crucial to detect these stressors to 
maximize the agricultural productivity and minimize resource use. 
Several studies have utilized image-based DL systems in detecting both 
biotic and abiotic stresses, such as fungal and bacterial diseases ( Venal 
et al., 2020 ), iron deficiency ( Li et al., 2020 ), drought stress ( Dao et al., 
2021a ), nitrogen deficiency ( Azimi et al., 2021a ), salt stress ( Khotimah 
et al., 2022 ), herbicide damage ( G ´omez-Zamanillo et al., 2023 ), potas -
sium deficiency ( Ghosal et al., 2018 ), light stress ( Hao et al., 2020 ), and 
chemical injury ( Venal et al., 2019 ). These DL-based models have been 
proven better than the traditional methods for plant stress detection in 
terms of efficiency and scalability.
Farmers and agronomists often rely on visual observation to identify 
signs of stress, such as wilting, discoloration, or abnormal growth pat -
terns. However, this method is admittedly subjective and error-prone 
( Ghosal et al., 2018 ) and requires specialized knowledge and/or 
considerable manpower ( Chen et al., 2023 ). Unlike subjective human 
observation, DL models provide objective and consistent analysis of 
plant stress across large areas, reducing human error and variability in 
detection and leading to more reliable results. Another traditional 
approach for plant stress detection is testing soil and plant tissue samples 
for nutrient content and other chemical properties. Although these tests 
provide valuable information, they are destructive methods, and they 
can be time-consuming and may not provide real-time data, whereas DL 
models are faster and can provide real-time diagnosis. Another tradi -
tional method is chlorophyll fluorescence measurement ( Kalaji et al., 
2023 ), which can assess the efficiency of photosynthesis and identify 
stress related to light absorption and energy transfer. However, this 
process often requires controlled environments. Molecular-based ap -
proaches, such as ELISA are time-consuming, labor-intensive, and not 
suitable for rapid, large-scale screening and monitoring ( Galieni et al., 
2021 ); in contrast, DL models can analyze large volumes of image data 
quickly, enabling rapid screening and monitoring of plant stress across 
extensive agricultural fields.
Imagery data is widely utilized in plant stress detection due to its 
ability to represent plant stress symptoms, like discoloration, wilting, 
and necrosis. Moreover, collecting data using imaging sensors (e.g., 
RGB, multispectral, hyperspectral) that are mounted on machines (i.e., 
unmanned ground vehicles [UGV], unmanned aerial vehicles [UAV], 
satellites, and airplanes) is non-destructive and applicable over large 
geographical areas ( Shin et al., 2021a ). The development of DL methods 
has revolutionized image analysis tasks. DL models provide high per -
formance in computer vision tasks, such as classification, object 
Fig. 1. Illustration of biotic and abiotic plant stressors.
N. Paul et al.                                                                                                                                                                                                                                    
===== PAGE 3 =====
Computers and Electronics in Agriculture 229 (2025) 109734
3
detection, segmentation, and augmentation. The accessibility of modern 
deep learning frameworks such as TensorFlow and PyTorch have made 
it easier for practitioners to implement, train, and deploy deep learning 
models, leading to widespread adoption in various fields. There are 
several DL architectures being used in plant stress detection tasks, such 
as VGG16, ResNet, Inception, EfficientNet, Xception, ShuffleNet, and 
MobileNet.
The objective of this paper is to summarize the current state-of-the- 
art in different stages of developing a plant stress detection system, 
including image acquisition, preprocessing and deep learning methods. 
This review discusses emerging trends, common methodologies, and 
recurring patterns, which can help researchers and practitioners to un -
derstand the prevailing approaches and areas of focus within the field. 
Additionally, it assesses the effectiveness of various deep learning 
models and techniques, which can be useful in determining the 
strengths, weaknesses, and potential areas for development of current 
methodologies. Furthermore, it identifies challenges and gaps in current 
approaches and proposes future directions for potential solutions of 
these issues. This gui
