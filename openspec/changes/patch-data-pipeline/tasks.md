# Tasks — patch-data-pipeline

## 1. Geometry + reader (TDD-first)

- [x] 1.1 Unit tests: bbox crop/pad to 32×32 (no resampling) for the
      measured size extremes (2.27 ha and 34.6 ha fields); polygon mask
      excludes neighbouring fields; inner-buffer flag default off
      (`tests/unit/test_patch_geometry.py`, 20 tests).
- [x] 1.2 `src/ssl_anomaly/io/patches.py`: geometry module (bbox origins,
      pad, polygon rasterization on the patch grid) + zarr writer/reader
      with schema validation (io/stats_zarr.py pattern: dims, dtypes,
      NaN discipline). Implemented: `FieldWindow`/`field_window`,
      `crop_and_pad`, `patch_in_field_mask` (neighbour exclusion),
      `store_schema`/`create_store`/`validate_store`/`open_store`,
      `output_sha256`. Pure-array geometry — rasterio/geopandas are imported
      only by the export driver, so the module is testable without the geo
      stack.
- [x] 1.3 Unit tests: per-pixel per-bin median aggregation on a synthetic
      tiny cube (known medians, NaN propagation, n_obs and sensor_id
      recording, valid_frac semantics identical to stats.zarr).
      `aggregate_bin` + `majority_sensor`; 12 aggregation tests in
      `tests/unit/test_patch_geometry.py`.

## 2. Exporter

- [x] 2.1 `scripts/extract_patches.py`: scene loop reusing the
      extract_pixels.py source resolution + io/landsat.py QA/scale handling
      verbatim; writes patches.zarr + `.manifest.jsonl`; flags
      --fields/--dates/--smoke/--estimate-runtime/--resume/--patch-size
      (default locked 32).
- [x] 2.2 Normalization artifact builder: per-channel × per-sensor
      median/IQR on train fields × train periods ONLY; frozen sidecar with
      sha256 + splits sha; unit test proving dev/test fields contribute
      nothing. `fit_patch_norm`/`build_patch_norm`/`save`/`load_patch_norm`
      (hash-verified, fail-closed); a planted 9.0-valued holdout field in the
      test store is proven not to move the train median.
- [x] 2.3 Provenance manifest (products, QA bits, scale factors, git sha,
      cycles sha, splits sha, output sha256) + schema validation test.
      `Provenance.validate()` refuses an incomplete record (AGENTS.md §2.4);
      `output_sha256` is deterministic and value-sensitive.
      The store binds to the locked split/cycle source; its held-out data is
      for evaluation. The norm and training runs, not the all-split exporter,
      also bind the frozen holdout hash.
- [ ] 2.4 Agent executes `--smoke` and `--estimate-runtime`, reviews the
      output (shapes, NaN discipline, plausible QA fractions), then hands
      the FULL run to the user as an exact command (conda env geo, cwd,
      expected wall time from the estimate, output paths) — the agent
      never launches it.

## 3. Verification gates

- [x] 3.1 New-module pytest green (40 tests: `test_patch_geometry.py`,
      `test_patch_store.py`; also green alongside the 37 holdout tests).
      Re-run under the geo env once the exporter lands — nothing here imports
      rasterio/geopandas, so the result should be identical.
- [ ] 3.2 After the user-run extraction: verify store schema, counts and
      hashes; record estimated vs actual wall time; confirm the existing
      suite (contract + bilingual 50) stays green and untouched.

### 2.1 notes

`scripts/extract_patches.py` + `tests/unit/test_extract_patches.py` (34 tests,
including an end-to-end run on synthetic GeoTIFFs). Field-major windowed reads,
resume through `.manifest.jsonl`, `--estimate-runtime` (no raster is opened),
`--smoke`, `--fields`, `--dates`, `--resume`, `--patch-size`.

Four defects were found while testing it, three of them in code this change
touches:

1. **Scene dates vs cycle offsets.** `cycles.parquet` stores `t_start` as a day
   OFFSET from the archive epoch; scene dates are absolute. Comparing them
   directly shifts every cycle by decades, so every bin comes out empty
   instead of failing. Added `day_index()` and an explicit `--epoch` (default:
   the locked `base_date` for training-compatible exports), and the epoch is
   recorded in provenance.
2. **Double-scaling.** The shipped `*.tif` scenes are already reflectance/K
   (`extract_stats.py` reads them as-is), so applying the C2 L2 factors turns
   everything into NaN. `--band-scale {auto,native,landsat}` with per-scene
   inference (reflectance stays `native`), recorded in provenance.
3. **`io.landsat.apply_scale_sr` tested the saturation limit against raw DN**
   (`arr > 1.6` where `arr` is DN in the thousands), so every DN-valued scene
   became all-NaN. Fixed to test the SCALED value; this affects
   `io/landsat.load_scene` and `io/zonal` too, which is the point.
4. **The "no QA" fallback resurrected fully cloudy scenes.** `valid` was
   replaced by "any finite band" whenever it came back empty — including when
   QA existed and said *cloud*. Now the fallback applies only when the QA
   raster is missing.

Also: `create_store` allocates `field_ids` but cannot fill it, so the driver
writes it and a later run refuses (`exit 3`) to mix a different field
selection into an existing store.

## Audit follow-up

- [x] A.1 Preserve locked cycle IDs and bind the cycle-window bounds, epoch and
      source hashes at extraction; test that scenes after cycle end stay absent.
- [x] A.2 Build and load the verified `stats` sidecar on locked train cycles;
      test a producer-to-training/scoring round trip and bad provenance refusal.
- [ ] A.3 Re-extract and review production-sized artifacts on the authorized
      archive before relying on new patch results.
