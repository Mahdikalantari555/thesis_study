# Edge-enabled smart agriculture framework: Integrating IoT, lightweight deep learning, and agentic AI for context-aware farming

**Authors:** Tariq, M. U., Saqib, S. M., et al.  
**Year:** 2025  
**Venue:** Results in Engineering, 28, 107342  
**DOI / arXiv:** 10.1016/j.rineng.2025.107342  
**Local PDF:** 1-s2.0-S2590123025033973-main.pdf  
**Type:** methods  
**Thesis relevance:** MEDIUM  

## Summary
The paper proposes an edge-enabled smart agriculture framework that integrates IoT sensors, lightweight deep learning models, and a rule-based agentic AI layer for context-aware farming. Two MiT-B0 Vision Transformers operate at 128×128 resolution on edge CPUs—one for weather (11 classes) and one for crop (5 classes)—and feed a rule-based agentic layer that triggers IoT irrigation, NDVI monitoring, frost responses, drone dispatch, and pest management.

## Methods / Architecture
- Two MiT-B0 ViT backbones at 128×128 on edge CPU.
- Weather classifier: 11 classes; crop classifier: 5 classes.
- Rule-based agentic AI layer for decision orchestration.
- IoT actuators/sensors: irrigation, NDVI, frost, drone, pest subsystems.

## Key quantitative results
- Weather classification accuracy: 88%.
- Crop classification accuracy: 93%.

## Relevance to thesis
Provides an edge decision-loop pattern (sense → classify → agent rules → actuate) relevant to arid irrigation control; however, it does not address EO foundation models, active learning, or LLM-based agents.

## Gaps / opportunities
- Rule-based agentic layer lacks LLM/MLLM reasoning and RAG-grounded explanations.
- No EO-FM or satellite-scale stress detection; focuses on local edge sensing.
- Opportunity: couple lightweight edge classifiers with EO-FM embeddings and LLM agents for hybrid local–satellite stress monitoring.

## Citation (APA 7th)
Tariq, M. U., Saqib, S. M., et al. (2025). Edge-enabled smart agriculture framework: Integrating IoT, lightweight deep learning, and agentic AI for context-aware farming. *Results in Engineering*, *28*, 107342. https://doi.org/10.1016/j.rineng.2025.107342

---
*Note written 2026-09-10 from first-page extract. Verify numbers in full PDF before formal proposal use.*
