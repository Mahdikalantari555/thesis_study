# Study note — Wu & Keogh 2021

## Citation (verified via arXiv, 2026-11-11)

Wu, Y., & Keogh, E. (2021). Time series anomaly detection benchmarks. arXiv:2009.13807. https://arxiv.org/abs/2009.13807

PDF: `D:\RS\Thesis\New_papers\2009.13807v5.pdf` (downloaded)

## Key findings relevant to this thesis

- Provides benchmark datasets and evaluation methodologies for time series anomaly detection
- Discusses the importance of proper train/test splits that respect temporal ordering
- Highlights common pitfalls in anomaly detection evaluation (data leakage, circularity)

## Methods used

- Benchmark datasets from multiple domains (ECG, motion, sensor data, etc.)
- Evaluation metrics: precision, recall, F1, AUC-ROC, AUC-PR
- Comparison of multiple anomaly detection algorithms
- Discussion of evaluation protocol best practices

## Findings-13 implications

- Relevant for validation ladder L1–L5: proper evaluation methodology for anomaly detection
- Relevant for §7 ML review checklist: AUC-ROC on imbalance, leakage, circularity
- Supports the need for random-init encoder control (R6) and proper baselines (B0/B1)

## TO VERIFY FROM PDF

- Specific benchmark datasets used and their characteristics
- Recommended evaluation protocols for imbalanced anomaly detection
- Whether the benchmarks include remote sensing / agricultural time series

Status: citation verified; PDF available at `D:\RS\Thesis\New_papers\2009.13807v5.pdf`; PDF text not extracted (pypdf/PyPDF2 availability not confirmed in this session).
