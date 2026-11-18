# Outputs Directory

## Structure

```
outputs/
├── figures/               # Publication-ready figures
│   ├── stress_maps/
│   ├── performance/
│   └── xai/
├── tables/                # CSV tables for papers
│   ├── accuracy_metrics.csv
│   ├── confusion_matrix.csv
│   └── shap_summary.csv
└── maps/                  # GeoTIFF maps and shapefiles
    ├── stress_detection/
    ├── stress_differentiation/
    └── uncertainty/
```

## Notes

- Figures should be high-resolution PNG/TIFF for papers.
- Tables should be CSV/Excel for easy import into Word.
- All outputs should be reproducible from scripts and notebooks.
