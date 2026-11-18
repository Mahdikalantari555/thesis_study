# Study note — Gu & Dao (Mamba)

## Citation (verified via arXiv, 2026-11-11)

Gu, A., & Dao, T. (2023). Mamba: Linear-Time Sequence Modeling with Selective State Spaces. arXiv. https://arxiv.org/abs/2312.00752

PDF: `D:\RS\Thesis\New_papers\mamba.pdf` (downloaded)

## Key findings relevant to this thesis

- Mamba is a selective state space model (SSM) that achieves linear-time sequence modeling
- Outperforms Transformers on long sequences while maintaining comparable quality
- Selective scanning mechanism allows the model to focus on relevant parts of the sequence
- Relevant for satellite image time series (SITS) where sequence length can be large (538 dates)

## Methods used

- Selective State Space (S6) layer: input-dependent SSM parameters
- Hardware-aware parallel algorithm for efficient training
- Linear-time complexity with respect to sequence length
- Can be used as a drop-in replacement for Transformer attention layers

## Findings-13 implications

- Relevant for State Space Models in remote sensing: Mamba-based encoders as alternatives to Transformers
- Relevant for the vision.md later items (multi-crop, intra-field, edge/Frugal AI)
- Linear-time scaling is relevant for 538-date Landsat archive (2013–2026)

## TO VERIFY FROM PDF

- Whether Mamba has been applied to remote sensing / satellite image time series
- Memory efficiency compared to Transformers for long SITS sequences
- Whether selective scanning helps with irregularly sampled data

Status: citation verified; PDF available at `D:\RS\Thesis\New_papers\mamba.pdf`; PDF text not extracted (pypdf/PyPDF2 availability not confirmed in this session).
