# Data Directory (documentation only)

> **Note:** The actual data (~10 GB) lives **outside** this repository, at `D:/RS/Thesis/Data/` (root level). This `thesis_research/data/` folder holds only documentation (`DATA_SUMMARY.md`, this README) — no rasters or raw scenes are stored here. See `D:/RS/Thesis/Data/DATA_SUMMARY.md` for the authoritative inventory.

## Structure

```
data/
├── DATA_SUMMARY.md        # Full inventory + stats of the RS dataset (authoritative)
├── README.md              # This file
├── Metric/                # Landsat 8/9 (path/row 165/039, 166/038) METRIC ET pipeline
│   ├── scenes/            # 607 raw Landsat scenes (2013-03-30 → 2026-09-10) + MTL + qa_pixel
│   └── products/          # 539 processed scenes × 35 raster types (30 m, EPSG:32639, 496×472)
│       └── interpolation/ # Daily gap-filled ETaDaily + CWSI_ET rasters (4,375 files each)
├── RoI/                   # Study area
│   ├── Extent.*           # RoI polygon (WGS84; 142.29 km², Khuzestan sugarcane district)
│   ├── Farms.geojson      # 490 farm polygons (20 blocks, ~12,120 ha)
│   └── Farms_subset.geojson  # 32 farms (block R11, 812.4 ha) — held-out validation subset
├── Scripts/               # METRIC pipeline, QA, interpolation, visualization (30+ files)
└── Weather/               # ERA5-style weather for the study point
    ├── metric_input/      # Daily inputs + weather_combined.csv (5,002 rows, 2013-01-01 → 2026-09-11)
    ├── raw/               # Hourly raw parquet
    └── features/          # Engineered hourly features (120,048 rows × 32 cols)
```

## Notes

- Large raster files (`.tif`, `.tiff`) and raw scene folders are gitignored.
- Store only metadata, manifests, and small CSVs/GeoJSONs in this directory; rasters stay local.
- `DATA_SUMMARY.md` is the authoritative inventory — regenerate/refresh it after any data change rather than hand-editing counts here.
- Analysis CRS: WGS84 (EPSG:4326) for vectors; UTM 39N (EPSG:32639) at 30 m for rasters.
- Study area: 142.29 km² sugarcane irrigation district, Khuzestan, Iran (lon 48.205–48.357 E, lat 30.963–31.094 N). See `RoI/Extent.*` and `DATA_SUMMARY.md` §2.
- Key target variables: ETaDaily, ETinst, ETrF, LE, H, G, LST, CWSI_ET, CWSI_LST, TVDI, SI_T, VSWI, NDVI/EVI/SAVI and other spectral indices, plus weather/soil-moisture features.
- Data-quality caveats (see `DATA_SUMMARY.md` §7): 68 scenes excluded from products; all scenes classified LOW_QUALITY by METRIC with frequent cold-pixel dT warnings; metadata missing for 2022-08-07; one malformed variety label; 87 fallow farms (no age/variety); farm attribute vs. geometry area differs by ~0.4%.
- Preprocessing scripts live in `scripts/` (root) and `data/Scripts/` (METRIC pipeline); outputs land in `data/Metric/products/`.