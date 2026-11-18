# Earth-Agent-Pro: Towards Real-World Full-Chain Earth Observation with Agents

**Authors:** Lv, Z., Dang, C., Feng, Y., et al.  
**Year:** 2026  
**Venue:** arXiv  
**DOI / arXiv:** arXiv:2609.12533v1  
**Local PDF:** 2609.12533v1.pdf  
**Type:** methods  
**Thesis relevance:** High  

## Summary
Earth-Agent-Pro targets real-world full-chain Earth observation with agents. It uses Plan-and-Execute with expert skills, workflow-centered memory, and Planner SFT + Executor GRPO. It introduces Earth-Bench-Pro (744 questions, including 248 open-world) covering domains such as Agriculture & Drought, and evaluates with GPT-5-as-judge on a Qwen3.5-9B tuned backbone.

## Methods / Architecture
- Plan-and-Execute with expert skills
- Workflow-centered memory
- Planner supervised fine-tuning (SFT) + Executor GRPO
- Earth-Bench-Pro: 744 questions (248 open-world); domains include Agriculture & Drought
- GPT-5-as-judge evaluation; Qwen3.5-9B tuned

## Key quantitative results
- GPT-5: 66.13% LLM-as-Judge on Earth-Bench-OW
- +20.95 pp vs ReAct; +24.44 pp vs Tools-In-Order
- Qwen3.5-9B: 38.31% → 50.00% (+11.69 pp) after tuning

## Relevance to thesis
Full-chain EO (acquisition → compute → answer) is the closest published architecture to an autonomous crop-stress monitoring pipeline spanning data retrieval, index computation, and interpretable reasoning.

## Gaps / opportunities
- LLM-as-judge reliability for quantitative agronomic metrics needs complementary ground-truth checks
- Agriculture & Drought domain breadth vs fine-grained crop-stress taxonomies
- Opportunity to extend Plan-and-Execute skills with water-stress what-if simulators (AgriWorld-style)

## Citation (APA 7th)
Lv, Z., Dang, C., Feng, Y., et al. (2026). *Earth-Agent-Pro: Towards Real-World Full-Chain Earth Observation with Agents*. arXiv:2609.12533v1.

---
*Note written 2026-09-10 from first-page extract. Verify numbers in full PDF before formal proposal use.*
