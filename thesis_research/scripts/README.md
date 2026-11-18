# Scripts Directory

## Structure

```
scripts/
├── preprocessing/          # Data download and preprocessing
│   ├── download_s2.py
│   ├── download_l8.py
│   ├── download_ecostress.py
│   ├── download_era5.py
│   └── preprocess.py
│
├── features/              # Feature extraction
│   ├── indices.py
│   ├── thermal.py
│   ├── embeddings_prithvi.py
│   └── embeddings_alphaearth.py
│
├── models/                # Model training and evaluation
│   ├── anomaly_detection.py
│   ├── classifier.py
│   ├── active_learning.py
│   └── evaluate.py
│
├── active_learning/       # Active learning loop
│   ├── uncertainty_sampling.py
│   ├── diversity_sampling.py
│   └── hybrid_sampling.py
│
└── utils/                 # Utility functions
    ├── gee_utils.py
    ├── raster_utils.py
    ├── vector_utils.py
    └── viz_utils.py
```

## Usage

```bash
# Example: extract Prithvi embeddings
python scripts/features/embeddings_prithvi.py \
  --input data/raw/sentinel2/ \
  --output data/processed/embeddings/ \
  --model ibm-nasa-geospatial/Prithvi-EO-2.0-600M \
  --batch-size 8
```

## Notes

- All scripts should be run from the repository root.
- Use `argparse` for command-line arguments.
- Log all runs with timestamps and parameters.
