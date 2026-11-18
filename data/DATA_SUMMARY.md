# Data Summary — RS Thesis (Khuzestan sugarcane)

Generated from `D:\RS\Thesis\Data`. Remote-sensing METRIC ET pipeline outputs + weather + RoI/farm vectors.

## 1. Folder overview

| Folder | Contents |
|---|---|
| `Metric/` | Landsat scenes, METRIC products, interpolation, metadata, visualizations |
| `RoI/` | Study-area polygon (`Extent.*`) + farm polygons (`Farms.geojson`, `Farms_subset.geojson`) |
| `Scripts/` | Pipeline, QA, interpolation, visualization scripts (30+ files) |
| `Weather/` | ERA5-style hourly/daily weather, features, combined CSV |

## 2. Region of Interest (RoI)

- CRS: WGS84 (EPSG:4326); analysis projected to UTM 39N (EPSG:32639).
- Extent bounds (lon/lat): 48.2051–48.3567 E, 30.9630–31.0937 N.
- Extent bounds (UTM): 233053–247763 E, 3428560–3443056 N.
- **RoI area: 142.29 km² (14,228.6 ha).**
- Raster grid: 30 m resolution, 496 × 472 px (~210.7 km² scene tile, clipped to RoI).

## 3. Farms (`Farms.geojson`, 490 polygons)

- All farms are sugarcane (`نیشکر`); single crop type.
- Blocks: 20 blocks (R01–R16, L02, L04, L06, L08); R08 has most farms (38), R07 fewest (8).
- Management: "تولید دوم" 251 farms (6,248.1 ha); "تولید یکم" 239 farms (5,872.1 ha).
- Offices: 4 offices (~120 farms / ~3,000 ha each).
- Status: cultivated (`داشت`) 402 farms / 9,964.9 ha; fallow (`آیش`) 87 farms / 2,145.3 ha; 1 unclassified (10.0 ha).
- Varieties: CP69-1062 (239), CP73-21 (58), CP48-103 (44), CP57-614 (24), IRC99-02 (18), SP70-1143 (16), IR01-412 (3), 1 malformed label.
- Age classes: R01 106, P 105, R02 91, R03 40, R04 20, R05 17, R06 12, R07 6, R08–R11 ≤2 each; 87 fallow (NaN age).
- **Total farm area (attribute): 12,120.2 ha; cultivated 9,965.0 ha; fallow 2,145.3 ha.**
- Geometry-derived area: 12,070.6 ha (0.4% difference from attribute).
- Farm size: 4.9–34.0 ha, mean 24.7 ha.
- Farms cover ~85.2% of RoI area.
- `Farms_subset.geojson`: 32 farms, all block R11, total 812.4 ha (cultivated 658.7 ha) — likely the validation/analysis subset.

### Farm area by block (ha)

| Block | Farms | Area (ha) | Cultivated (ha) |
|---|---:|---:|---:|
| L02 | 19 | 399.2 | 342.7 |
| L04 | 24 | 598.8 | 522.3 |
| L06 | 24 | 611.1 | 509.6 |
| L08 | 24 | 604.2 | 502.3 |
| R01 | 20 | 502.9 | 426.0 |
| R02 | 18 | 435.6 | 384.6 |
| R03 | 20 | 508.2 | 406.3 |
| R04 | 20 | 501.3 | 399.4 |
| R05 | 20 | 509.0 | 407.0 |
| R06 | 22 | 555.1 | 444.6 |
| R07 | 8 | 156.2 | 148.5 |
| R08 | 38 | 894.0 | 712.4 |
| R09 | 10 | 253.9 | 228.0 |
| R10 | 31 | 755.4 | 605.3 |
| R11 | 32 | 812.4 | 658.7 |
| R12 | 32 | 800.5 | 621.5 |
| R13 | 32 | 795.0 | 652.0 |
| R14 | 32 | 814.6 | 661.6 |
| R15 | 32 | 800.6 | 647.6 |
| R16 | 32 | 812.2 | 684.6 |

## 4. Landsat scenes (`Metric/scenes`)

- Scene folders: **607** (unique dates, no duplicates).
- Date range: 2013-03-30 → 2026-09-10.
- Paths/rows: 165/039 and 166/038 (2 tiles covering Khuzestan).
- Sensors: Landsat 8 (451 scenes) + Landsat 9 (156 scenes) — all `oli_tirs`.
- MTL cloud cover (whole scene): 0.0–29.8%, mean 3.7%.
- MTL cloud cover (land): 0.0–37.8%, mean 3.1%.
- Scenes per year: 2013 28, 2014 35, 2015 29, 2016 39, 2017 31, 2018 31, 2019 36, 2020 35, 2021 40, 2022 45, 2023 63, 2024 74, 2025 73, 2026 48.
- Every scene has `MTL.json` and `qa_pixel.tif`.

## 5. METRIC products (`Metric/products`)

- Processed scenes in products: **539 files (of 607 downloaded)** — **538 usable dates** (2022-08-07 metadata corrupted; user-confirmed 2026-11-14; 538 is the canonical count everywhere).
- Excluded scenes: **68** (present in `scenes/` but absent from products). Their MTL land cloud cover is higher on average (mean 11.8% vs 2.0% for kept; range 0.0–37.8%); 26 of 68 have ≤5% land cloud, so exclusion is not purely cloud-threshold based (likely pipeline failures/data gaps).
- Product date range: 2013-03-30 → 2026-09-10.
- Raster product types: **35**, each with **539** GeoTIFFs (30 m, EPSG:32639, 496×472, float32):
  Albedo, CWSI_ET, CWSI_LST, Emissivity, ETaClassified, ETaDaily, ETinst, ETqualityClass, ETrF, EVI, FVC, G, GCI, H, LAI, LE, LST, MNDWI, MSI, NDMI, NDSI, NDVI, NIRv, NMDI, RGB, RlDown, RlUp, Rn, Rnl, Rns, RsDown, SAVI, SI_T, TVDI, VSWI.
- Total raster product files: 35 × 539 = **18,865**.
- Metadata GeoJSON: **538** (one missing for 2022-08-07 — **this is the whole 538-vs-539 discrepancy; OQ5 RESOLVED 2026-11-14, user-confirmed: 538 usable dates is canonical**).
- Visualizations: 1,077 PNGs (≈2 per scene: overview + ET map).
- Interpolation (`products/interpolation/`): daily interpolated ETaDaily and CWSI_ET rasters — **4,375 files each** (gap-filled daily series between overpasses).

### Metadata quality summary (n=538)

- `scene_quality`: all 538 flagged `LOW_QUALITY` (METRIC classification).
- Calibration: all 538 `valid = true`.
- Calibration warnings: cold-pixel dT constraint violated 228; dT_cold too large 174; "CALIBRATION WARNING / temperature difference too small" 152; cold-pixel energy-balance violation 41; dT_hot issues 12.
- Valid pixels: mean 0.666 (range 0.413–0.674).
- Metadata "cloud_coverage": mean 0.992 (range 0.711–1.000) — stored as fraction; valid_pixels is the usable-pixel fraction.
- NDVI (scene mean): 0.405 (scene means range embedded); LST (scene mean): 311.3 K.
- Sun elevation: mean 54.7° (range 31.1–69.5°).
- Sensor: `oli_tirs`; raster shape 496×472 for all scenes.

## 6. Weather (`Weather/`)

- Combined daily CSV: `metric_input/weather_combined.csv` — **5,002 rows**, 2013-01-01 → 2026-09-11, **no gaps, no NaNs**.
- Variables: temperature_2m, relative_humidity_2m, wind_speed_10m, surface_pressure, shortwave_radiation, et0_fao_evapotranspiration.
- Hourly raw: `raw/point_01_raw_hourly.parquet`.
- Features: `features/point_01_features.parquet` — 120,048 rows × 32 columns (hourly engineered features: temp/vpd/sw/wind/soil moisture, 3/7/30-day rain & ET0, water balance, anomalies, heat/dryness indices, lat/lon).
- Daily inputs: 5,004 files in `metric_input/` (one per day + combined).
- Location: point 01 at lat 31.032, lon 48.282 (inside RoI).

## 7. Thesis-relevant notes

- Study area: 142.29 km² sugarcane-dominated irrigation district, Khuzestan, Iran; 490 management units.
- Temporal coverage of RS products: 13.5 years (Mar 2013 – Sep 2026), **538 usable** clear-sky Landsat overpasses (8/9; 539 files, 2022-08-07 metadata corrupted), ~16-day revisit; 4,375 daily interpolated ETa/CWSI rasters for time-series analysis.
- Spatial resolution 30 m aligns with farm blocks (~25 ha ≈ 278 pixels), suitable for field-scale ET and water-stress studies.
- Key target variables available: ETaDaily, ETinst, ETrF, LE, H, G, LST, CWSI_ET, CWSI_LST, TVDI, SI_T, VSWI, NDVI/EVI/SAVI and many spectral indices, plus weather/soil-moisture features.
- Data-quality caveats to report: (a) 68 scenes excluded from products; (b) all scenes classified LOW_QUALITY by METRIC with frequent cold-pixel dT warnings; (c) metadata missing for 2022-08-07; (d) one malformed variety label; (e) 87 fallow farms (no age/variety).
- Farm attribute vs geometry area differs by ~0.4%; use geometry area for spatial analysis.
- Farms_subset (32 R11 farms, 812.4 ha) can serve as a held-out validation set.
"
---

## 9. Processed Data (`Data/Processed/`) — PRD V1.0

Organized farm-level dataset for self-supervised learning and anomaly detection.
Generated 2026-11-03. Two parallel datasets: statistical (8 stats) and pixel-level.

### 9.1 Layout
```
Data/Processed/
├── satellite/
│   ├── stats_long.parquet          # 1,845,340 rows (farm x date x band, long)
│   ├── stats_wide_raw.parquet      # 263,620 rows (farm x date, wide, ML-ready)
│   ├── stats.zarr/                 # (490 farm, 538 time, 7 band) x 8 stats
│   ├── zonal_stats/*.parquet       # 538 per-scene checkpoints
│   ├── pixels/*.parquet            # 538 per-scene farm-masked pixel files
│   ├── quality.parquet             # 538 scenes x 19 metadata fields
│   ├── scene_inventory.parquet     # scene list (date, sensor, cloud, valid pixels)
│   ├── stats_current.zarr/         # legacy mean/median/std (v2)
│   └── derived/                    # cycles, scores, daily_anomaly, baseline (ML outputs)
├── weather/
│   ├── weather_shared.parquet      # 5,003 days x 57 cols (aggregates + 3/7/14/30d windows)
│   └── weather_aligned.parquet     # 539 Landsat dates x windows (retrospective, no leakage)
├── coordinates/
│   ├── farms.parquet               # 490 farms x 12 metadata fields
│   ├── farms.geojson               # farm polygons (UTM 32639)
│   └── farm_pixels.parquet         # 133,822 pixel->farm mapping (row, col, x, y, local_pixel)
├── indices/                        # optional spectral indices (empty by default)
├── interim/field_mask_full.tif     # farm raster mask (490 farms, 30m, 472x496)
├── manifests/
└── README.md
```

### 9.2 Dataset 1 — Statistical (8 distribution stats)
- Bands (harmonized): blue, green, red, nir, swir1, swir2, lst.
- Stats per (farm, date, band): mean, median, std, p10, p25, p75, p90, iqr.
- Plus: valid_frac, n_pixels per farm-date.
- Shape: 490 farms x 538 dates x 7 bands = 1,845,340 long rows.
- Zarr dims: (field=490, time=538, band=7); chunked (490, 2, 7) for fast farm/time slicing.
- Quality: QA-based cloud/cloud-shadow/cirrus/snow masking; nodata excluded; scale/offset applied.

### 9.3 Dataset 2 — Pixel-level (farm-masked)
- Per-scene Parquet: 133,822 pixels x 16 cols (field_id, row, col, x, y, valid, 7 bands, scene_date, sensor, local_pixel).
- 538 scene files. Subset read: filter by field_id or read single scene file.

### 9.4 Weather (shared temporal covariate)
- Daily aggregates from hourly ERA5 raw: temperature (mean/min/max), RH (mean), VPD (mean),
  precipitation (sum), solar (mean/sum), wind (mean), ET0 (sum), soil moisture (mean), soil temp (mean).
- Retrospective windows: 3d, 7d, 14d, 30d (all end at acquisition date — no future leakage).
- Shared across farms (not replicated); optional flat join in stats for convenience.
- Completeness: 5,002 days (2013-01-01..2026-09-11), 0 gaps, 0 NaN; 120,048 hourly rows, 0 gaps/NaN.

### 9.5 Subset reads (fast tests)
```python
import pandas as pd, xarray as xr, glob
farms = pd.read_parquet("Data/Processed/coordinates/farms.parquet")
pixels = pd.read_parquet("Data/Processed/coordinates/farm_pixels.parquet")
farm_px = pixels[pixels.field_id == 5]          # one farm's pixels
w = pd.read_parquet("Data/Processed/weather/weather_shared.parquet")
ds = xr.open_zarr("Data/Processed/satellite/stats.zarr")
sub = ds.sel(field=[1,2,3], time=slice("2023-01-01","2023-06-30"))
px = pd.read_parquet("Data/Processed/satellite/pixels/2023-06-15.parquet")
```

### 9.6 Provenance / code
- Scripts: thesis_implementation/scripts/{prepare_processed,extract_stats,extract_pixels}.py
- All support checkpoint/resume and --max-scenes for smoke tests.
- Zarr v2 (xarray-compatible); CRS EPSG:32639; pixel size 30m.
- Scale/offset: Landsat C2 L2 (SR: 0.0000275, -0.2; ST: 0.00341802, 149.0).
- QA masking: dilated cloud, cirrus, cloud, cloud shadow, snow (bits 1-5).

### 9.7 Known limitations
- stats_current.zarr holds only mean/median/std (legacy); full 8 stats in stats.zarr.
- Pixel-level files are per-scene (not a single Zarr) for subset readability; ~538 x 133k rows.
- Data/Processed has a Windows deny ACE (Everyone: DeleteSubdirectoriesAndFiles); writes in confined
  sandbox mode require staging + copy or ACL repair (backup in .acl-recovery/).
