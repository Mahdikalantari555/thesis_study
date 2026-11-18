# CottonBot: An AI-driven cotton farming assistant and irrigation advisor using LLM-RAG and agentic AI tools

**Authors:** Kandamali, D. F., Porter, W. M., Porter, E., McLemore, A., & Rains, G. C.  
**Year:** 2025  
**Venue:** Smart Agricultural Technology, 12, 101640  
**DOI / arXiv:** 10.1016/j.atech.2025.101640  
**Local PDF:** 1-s2.0-S2772375525008718-main.pdf  
**Type:** methods  
**Thesis relevance:** HIGH  

## Summary
CottonBot is an AI-driven cotton farming assistant and irrigation advisor that combines retrieval-augmented generation (RAG) over the Georgia Cotton Production Guide with agentic tool-calling for soil moisture sensors and weather APIs. The system runs Llama 3.1 locally via Ollama, uses LangChain with FAISS or Chroma for vector stores, and delivers a FastAPI backend with a Flutter mobile frontend.

## Methods / Architecture
- RAG corpus: Georgia Cotton Production Guide.
- Agentic tool-calling: soil moisture sensors, weather APIs.
- LLM: Llama 3.1, run locally with Ollama.
- Orchestration: LangChain.
- Vector stores: FAISS and Chroma.
- Application stack: FastAPI + Flutter.

## Key quantitative results
- Best retrieval configuration: all-MiniLM-L6-v2 embeddings + FAISS.
- Best response generation: Llama 3.1.
- Detailed quantitative tables are not provided in the first-page extract; verify against the full PDF.

## Relevance to thesis
Provides a concrete RAG + IoT irrigation agent pattern for arid systems: local LLM, domain-guide retrieval, and live sensor tool calls offer a deployable template that can be extended with EO foundation-model stress scores and active-learning label acquisition.

## Gaps / opportunities
- Cotton- and Georgia-specific; transferability to arid multi-crop settings needs adaptation.
- No EO-FM or satellite stress-detection integration in the described pipeline.
- Opportunity: replace/augment sensor tools with RS-FM embeddings (Prithvi, CROMA, etc.) and REMSA-style model selection for broader coverage.

## Citation (APA 7th)
Kandamali, D. F., Porter, W. M., Porter, E., McLemore, A., & Rains, G. C. (2025). CottonBot: An AI-driven cotton farming assistant and irrigation advisor using LLM-RAG and agentic AI tools. *Smart Agricultural Technology*, *12*, 101640. https://doi.org/10.1016/j.atech.2025.101640

---
*Note written 2026-09-10 from first-page extract. Verify numbers in full PDF before formal proposal use.*
