# Thesis Research Repository

**MSc Thesis:** Crop Stress Monitoring in Arid and Semi-Arid Agriculture Using GeoAI, Foundation Models, and Active Learning  
**Student:** [Name]  
**Supervisor:** [Name]  
**University:** Shahid Beheshti University  
**Department:** Remote Sensing and Geoinformatics  
**Year:** 2026–2028

---

## Repository Structure

```
thesis_research/
├── AGENTS.md                  # Guidelines for AI agents working on this repo
├── README.md                  # This file
├── .gitignore                 # Excludes papers/, data/, models/
│
├── lit_review/                # Literature review and gap analysis
│   ├── README.md
│   ├── 00_paper_links.md              # Direct PDF download links
│   ├── 00_thesis_literature_review.md # Main literature review
│   ├── phase1_stress_detection_methods.md
│   └── papers_not_downloaded.md
│
├── papers/                    # Downloaded PDFs (LOCAL ONLY, gitignored)
│
├── memory/                    # Persistent findings log
│   ├── 2026-09-06-initial-findings.md
│   └── ...
│
├── data/                      # Data directory structure
│   ├── raw/                   # Raw satellite imagery, weather data, field boundaries
│   ├── processed/             # Preprocessed data, indices, features
│   └── external/              # Public datasets (CropHarvest, SoilGrids, etc.)
│
├── scripts/                   # Python/GEE processing scripts
│   ├── preprocessing/
│   ├── features/
│   ├── models/
│   ├── active_learning/
│   └── utils/
│
├── notebooks/                 # Jupyter notebooks for exploration and reporting
│
├── outputs/                   # Results, figures, tables, maps
│   ├── figures/
│   ├── tables/
│   └── maps/
│
└── proposal/                  # Thesis proposal drafts and final version
    ├── draft/
    └── final/
```

---

## Quick Start

### Prerequisites
- Python 3.9+
- Google Earth Engine account
- NVIDIA GPU (recommended for foundation model fine-tuning)

### Installation
```bash
# Clone the repository
git clone <repo-url>
cd thesis_research

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Key Dependencies
- `torch`, `torchvision` — Deep learning
- `huggingface-hub` — Foundation model weights
- `rasterio`, `geopandas` — Geospatial data processing
- `earthengine-api` — Google Earth Engine
- `scikit-learn`, `shap` — ML and explainability
- `lightning` or `torchgeo` — Training frameworks

---

## Workflow

1. **Literature Review:** Start with `lit_review/00_thesis_literature_review.md`
2. **Data Preparation:** Use `scripts/preprocessing/` to download and preprocess satellite data
3. **Feature Extraction:** Use `scripts/features/` for indices and foundation model embeddings
4. **Model Training:** Use `scripts/models/` for anomaly detection and classification
5. **Active Learning:** Use `scripts/active_learning/` for the labeling loop
6. **Results:** Export figures and tables to `outputs/`

---

## Memory System

All significant findings, decisions, and lessons learned are logged in `memory/`.  
Before starting any task, read the latest memory file. After completing any task, update the memory log.

---

## Citation

If you use this work, please cite the relevant papers listed in `lit_review/00_paper_links.md`.

---

## License

This repository is for academic use only. See individual file headers for specific licenses.

---

*Last updated: 2026-09-06*
