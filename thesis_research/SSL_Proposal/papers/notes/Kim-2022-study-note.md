# Study note — Kim et al. 2022

## Citation (verified via Crossref/AAAI, 2026-11-11)

Kim, H., et al. (2022). Towards a Rigorous Evaluation of Time-Series Anomaly Detection. Proceedings of the AAAI Conference on Artificial Intelligence (AAAI-22), 36(7), 20680. DOI: 10.1609/aaai.v36i7.20680

PDF: `D:\RS\Thesis\New_papers\02239-KimS.pdf` (downloaded)

## Key findings relevant to this thesis

- Argues that many time-series anomaly detection papers use flawed evaluation protocols
- Proposes a more rigorous evaluation framework with proper temporal train/test splits
- Emphasizes the need for multiple random seeds and statistical significance testing

## Methods used

- Systematic review of time-series anomaly detection literature
- Identification of common evaluation flaws (data leakage, look-ahead bias, single seed)
- Proposed evaluation protocol with temporal splitting and multiple seeds
- Statistical significance testing for comparing anomaly detection methods

## Findings-13 implications

- Relevant for validation ladder L1–L5: every claim states its rung
- Relevant for §7 ML review checklist: single seed, missing baselines, stale reports
- Supports the random-init encoder control (R6) and proper baseline comparisons (B0/B1/random encoder)

## TO VERIFY FROM PDF

- Specific evaluation flaws identified in remote sensing anomaly detection papers
- Recommended number of random seeds for statistical significance
- Whether the framework applies to multivariate time series (NDVI + LST)

Status: citation verified; PDF available at `D:\RS\Thesis\New_papers\02239-KimS.pdf`; PDF text not extracted (pypdf/PyPDF2 availability not confirmed in this session).
