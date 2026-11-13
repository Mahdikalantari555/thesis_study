# Study note — Dumeur et al. 2024 (ALISE)

## Citation (verified via arXiv, 2026-11-11)

Dumeur, A., et al. (2024). ALISE: Irregular Satellite Image Time Series Learning. arXiv:2407.08448. https://arxiv.org/abs/2407.08448

PDF: `D:\RS\Thesis\New_papers\2407.08448v2.pdf` (downloaded)

## Key findings relevant to this thesis

- ALISE addresses irregularly sampled satellite image time series (SITS), which is directly relevant to Landsat data with missing acquisitions due to clouds.
- Proposes a masked autoencoding approach for irregular SITS that can handle variable temporal gaps between observations.
- Demonstrates that irregular SITS learning can outperform regularly resampled approaches when cloud cover is high.

## Methods used

- Masked autoencoder architecture adapted for irregular time series
- Temporal masking that respects the actual observation times (not resampled to regular grid)
- Positional encoding based on actual observation dates
- Reconstruction-based pre-training followed by fine-tuning for downstream tasks

## Findings-13 implications

- Relevant for R4: irregular-token variant as a later change after Masked TF round 1 uses 36 DSH bins
- Relevant for R3: time axis considerations — ALISE shows that respecting actual observation times can improve performance over regular resampling
- Supports the decision to keep DSH 36×15-day bins as main axis while adding sin/cos DOY as auxiliary input (rather than switching to fully irregular tokens)

## TO VERIFY FROM PDF

- Exact masking strategy and mask ratio used
- Whether the approach handles multi-year data with seasonal gaps
- Computational cost compared to regular-grid approaches

Status: citation verified; PDF available at `D:\RS\Thesis\New_papers\2407.08448v2.pdf`; PDF text not extracted (pypdf/PyPDF2 availability not confirmed in this session).
