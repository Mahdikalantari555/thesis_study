# Data Directory — canonical location

This is the **canonical data directory** for the thesis (`D:/RS/Thesis/Data/`, ~10 GB). It lives at the repository root, **outside** `thesis_research/`, because rasters/raw scenes are gitignored and too large to commit.

## Structure

```
Data/
├── DATA_SUMMARY.md        # Full inventory + stats (authoritative)
├── README.md              # This file
├── Metric/                # Landsat 8/9 METRIC ET pipeline
│   ├── scenes/            # 607 raw Landsat scenes (2013-03-30 → 2026-09-10)
│   └── products/          # 539 scene files × 35 raster types (30 m, EPSG:32639) — 538 usable dates (2022-08-07 metadata corrupted)
│       └── interpolation/ # Daily gap-filled ETaDaily + CWSI_ET (4,375 files each)
├── RoI/                   # Study area + 490 farm polygons + 32-farm validation subset
├── Processed/             # Farm-level standardized dataset (PRD V1.0)
│   ├── satellite/         # stats (8 distribution stats) + pixels (farm-masked) + zonal checkpoints
│   ├── weather/           # shared temporal covariate (daily + 3/7/14/30d windows)
│   ├── coordinates/       # farms metadata + farm_pixels (subset reads)
│   ├── indices/           # optional spectral indices (empty by default)
│   ├── interim/           # field_mask_full.tif (490 farms, 30m)
│   ├── manifests/
│   └── README.md          # schema + subset-read guide + heavy extraction
├── Scripts/               # METRIC pipeline, QA, interpolation, visualization
└── Weather/               # ERA5-style weather + engineered features
```

## Notes

- Large rasters (`.tif`/`.tiff`) and raw scenes are gitignored; only metadata/small CSVs/GeoJSONs are tracked.
- `DATA_SUMMARY.md` is the authoritative inventory — refresh it after any data change.
- A documentation-only mirror of this README exists at `thesis_research/data/README.md`.
- Study area: 142.29 km² sugarcane irrigation district, Khuzestan, Iran. Analysis CRS: UTM 39N (EPSG:32639) at 30 m.
## Processed Data (added 2026-11-03)

`Data/Processed/` is the standardized, farm-level dataset for self-supervised learning
and anomaly detection, per PRD V1.0. It contains two parallel datasets:

- **Statistical**: `satellite/stats.zarr` (490 farm x 538 time x 7 band) with 8 distribution
  stats (mean/median/std/p10/p25/p75/p90/iqr) + valid_frac + n_pixels, plus long/wide parquet.
- **Pixel-level**: `satellite/pixels/*.parquet` (538 scenes x 133,822 farm-masked pixels).

Weather is stored as a shared temporal covariate (`weather/weather_shared.parquet`,
`weather/weather_aligned.parquet`) with retrospective 3/7/14/30d windows and no future leakage.

See `Data/Processed/README.md` and `Data/DATA_SUMMARY.md` (section 9) for full schema,
subset-read examples, and the heavy-extraction scripts (`thesis_implementation/scripts/`).
