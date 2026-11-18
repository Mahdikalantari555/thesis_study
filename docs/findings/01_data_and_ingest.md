# یافته ۱ — داده و ingest

## 32 مزرعه (Farms_subset, baseline)

### داده

- Farms_subset.geojson: ۳۲ مزرعهٔ R11 (۸۱۲.۴ ha).
- ۵۳۹ گذر تمیز لندست ۸/۹ (۲۰۱۳-۰۳ تا ۲۰۲۶-۰۹).
- باندها: ۷ باند خام (SR_B2..B7 + ST_B10/LST) + weather (۵ متغیر ERA5).
- **std** در کنار mean/median در zonal stats.

### خروجی

- `fields.zarr`: (field=32, time=539, band=7) + weather (time, 5).
- نرخ NaN ≈ ۰.۷٪.
- `fields.parquet`: متادیتا.

### یافتهٔ کلیدی

ingest روی subset با باندهای خام + weather + std اجرا شد. Pipeline روی دادهٔ واقعی (نه synthetic) کار می‌کند.

## 490 مزرعه (real archive, rerun-rq-suite-on-real-490, verified 2026-11-10)

### داده (canonical)

- `Data/Processed/satellite/stats.zarr`: 490 fields × 538 acquisition dates × 7 bands (SR_B2/SR_B3/SR_B4/SR_B5/SR_B6/SR_B7/ST_B10 → blue, green, red, nir, swir1, swir2, lst), 8 distribution stats + `valid_frac`. Date range: 2013-03-30 → 2026-09-10. Read via `ssl_anomaly.io.stats_zarr.load_stats_zarr`.
- **Date-count reconciliation (task 1.1; RESOLVED 2026-11-14):** `stats.zarr` has 538 dates vs 539 scene files in METRIC products — the **2022-08-07 metadata GeoJSON is missing/corrupted** (see `data/DATA_SUMMARY.md` §5). **538 usable dates is the canonical count** (user-confirmed); `stats.zarr` remains the canonical 490-field archive and provenance reports `n_dates=538`.

### چرخه‌ها (cycles_490, task 1.2)

- Source: `data/processed/cycles_490.parquet` and `data/interim/growth_cycles_490.npz`, produced by `scripts/segment_and_export_cycles_490.py` from `stats.zarr` (36 × 15-day bins, ≤540 days, channels `[ndvi] + [blue,green,red,nir,swir1,swir2,lst]`).
- `cycles_490.parquet`: **1755 total cycles** (956 censored, **799 non-censored**).
- Non-censored coverage: **370 fields** with ≥1 non-censored cycle, **223 fields** with ≥2 non-censored cycles.
- NPZ tensor: `X` shape `(799, 36, 8)` aligned to non-censored cycles.
- `data/processed/fields.zarr` (32-farm) is **not present** under `Data/Processed/` in this workspace; `real32` evaluation paths are unavailable and real-490 is the default (`--source real490`, fail-closed).