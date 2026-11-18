# REMSA: Foundation Model Selection for Remote Sensing via a Constraint-Aware Agent

**Authors:** Chen, B., Bök, T. E., Rasti, B., Markl, V., & Demir, B.  
**Year:** 2025  
**Venue:** arXiv preprint  
**DOI / arXiv:** arXiv:2511.17442v3  
**Local PDF:** REMSA Foundation Model Selection for Remote Sensing via a Constraint-Aware Agent.pdf  
**Type:** methods  
**Thesis relevance:** VERY HIGH  

## Summary
This paper introduces REMSA, a constraint-aware agent for selecting remote-sensing foundation models (RSFMs), supported by RS-FMD, a schema-guided database of more than 160 RSFMs spanning RGB, multispectral, hyperspectral, SAR, and LiDAR modalities. REMSA follows a pipeline of query interpretation → constraint extraction → retrieval → clarification → ranking → explanation → memory. Code is released at github.com/be-chen/REMSA.

## Methods / Architecture
- RS-FMD: schema-guided database of >160 RSFMs (RGB, multispectral, hyperspectral, SAR, LiDAR).
- REMSA agent pipeline: query → constraints → retrieval → clarification → ranking → explanation → memory.
- Evaluation design: 100 expert scenarios × 4 systems × 3 LLMs × top-3 candidates = 3,000 expert-scored configurations.
- Compared systems include a naive agent, dense retrieval, and unstructured RAG.
- Code: github.com/be-chen/REMSA

## Key quantitative results
- 3,000 expert-scored configurations (100 scenarios × 4 systems × 3 LLMs × top-3).
- REMSA outperforms the naive agent, dense retrieval, and unstructured RAG baselines.
- Exact score magnitudes are not stated in the first-page extract; verify against the full PDF before formal proposal use.

## Relevance to thesis
Core citation for EO foundation-model selection under modality, task, and compute constraints (e.g., choosing among Prithvi, CROMA, SatMAE, Galileo, TerraMind for arid crop-stress monitoring). Provides a principled agent pattern and a structured FM registry.

## Gaps / opportunities
- Selection task is general RSFM choice, not crop-stress-specific fine-tuning or active-learning budgeting.
- Integration with downstream stress-detection pipelines (e.g., auto-select FM then adapt with AL loops) is left open.
- RS-FMD could be extended with stress-task metadata for agricultural applications.

## Citation (APA 7th)
Chen, B., Bök, T. E., Rasti, B., Markl, V., & Demir, B. (2025). *REMSA: Foundation model selection for remote sensing via a constraint-aware agent* (arXiv:2511.17442v3). arXiv. https://arxiv.org/abs/2511.17442

---
*Note written 2026-09-10 from first-page extract. Verify numbers in full PDF before formal proposal use.*
