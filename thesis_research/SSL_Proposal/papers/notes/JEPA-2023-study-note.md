# Study note — Assran et al. (JEPA, Meta AI)

## Citation (verified via Meta AI / arXiv, 2026-11-11)

Assran, M., et al. (2023). Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture (JEPA). Meta AI. https://arxiv.org/abs/2301.08243 (JEPA paper series)

PDF: `D:\RS\Thesis\New_papers\jepa.pdf` (downloaded)

## Key findings relevant to this thesis

- JEPA learns representations by predicting a target embedding from a context embedding, without reconstructing pixel values
- Avoids the collapse problems of contrastive learning while not requiring generative reconstruction
- Shows that joint-embedding predictive approaches can learn useful visual representations without labels

## Methods used

- Joint-embedding predictive architecture: context encoder + target encoder + predictor
- Representation learning through prediction in embedding space (not pixel space)
- Stop-gradient on target encoder (similar to BYOL)
- No mask-and-reconstruct; instead predict target representation from context representation

## Findings-13 implications

- Relevant for R6: random-init encoder control mandatory in every comparison
- Relevant for SSL design: masked modeling alternatives for irregular time series
- Supports the Masked TF approach in this thesis (reconstruct masked tokens from visible context)

## TO VERIFY FROM PDF

- Whether JEPA has been applied to time series / remote sensing data
- Computational efficiency compared to masked autoencoders
- Whether the approach handles multivariate inputs (NDVI + LST)

Status: citation verified; PDF available at `D:\RS\Thesis\New_papers\jepa.pdf`; PDF text not extracted (pypdf/PyPDF2 availability not confirmed in this session).
