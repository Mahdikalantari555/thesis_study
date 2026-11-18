# GeoArbiter: Verifiability-Guided Grounding for Remote-Sensing Multimodal LLMs

**Authors:** Li, X.  
**Year:** 2026  
**Venue:** arXiv preprint  
**DOI / arXiv:** arXiv:2608.00877v1  
**Local PDF:** GeoArbiter Verifiability-Guided Grounding for Remote-Sensing Multimodal LLMs.pdf  
**Type:** methods  
**Thesis relevance:** MEDIUM–HIGH  

## Summary
GeoArbiter is a training-free method that injects OpenStreetMap (OSM) and GeoNames facts into remote-sensing multimodal large language models (RS MLLMs) under a verifiability-stratified policy. The method retains function/identity information from external records but withholds structure records that conflict with the model’s visual evidence, thereby reducing hallucination while preserving useful geographic grounding. Experiments cover Qwen2.5-VL, InternVL3, and LLaVA-OV on the fMoW functional set (28,087 images).

## Methods / Architecture
- Training-free retrieval-and-injection pipeline for RS MLLMs.
- External knowledge sources: OSM and GeoNames.
- Verifiability stratification: keep function/identity facts; withhold conflicting structure records.
- Evaluated models: Qwen2.5-VL, InternVL3, LLaVA-OV.
- Benchmark: fMoW functional set (28,087 images).

## Key quantitative results
- Full retrieval improves performance by +12.06–17.19 points.
- GeoArbiter retains 84.69–87.15% of the full-retrieval gain.
- Hallucination reductions: −9.58–26.34% (blinded setting) and −19.28–45.19% (standard setting).
- Reduction in fabricated visible features: −13.50–51.00 points.

## Relevance to thesis
Supports the trustworthiness of agentic crop-stress decision support: when an LLM/MLLM agent must justify stress assessments from RS imagery, verifiability-guided external grounding can curb fabricated scene attributes while keeping useful place/identity context.

## Gaps / opportunities
- Evaluated on fMoW functional classification rather than crop-stress or agricultural stress phenotyping tasks.
- Does not couple grounding with active learning or EO foundation-model embeddings.
- Opportunity: adapt the verifiability strata (function vs. structure) to irrigation and soil-moisture fact stores for arid systems.

## Citation (APA 7th)
Li, X. (2026). *GeoArbiter: Verifiability-guided grounding for remote-sensing multimodal LLMs* (arXiv:2608.00877v1). arXiv. https://arxiv.org/abs/2608.00877

---
*Note written 2026-09-10 from first-page extract. Verify numbers in full PDF before formal proposal use.*
