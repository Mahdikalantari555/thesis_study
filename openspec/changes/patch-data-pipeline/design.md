## Design — patch-data-pipeline

### Decisions

1. **S = 32, one patch per field, no tiling.** Measured field sides
   (median 16.7 px, p90 17.0, max 19.6) make 32×32 sufficient for every
   field plus margin. This deviates from the architecture document's
   S∈{16,32} tiling proposal — justified by the measurement recorded in the
   proposal. A `--patch-size` flag exists; the default is locked to 32 for
   the trial.

2. **Cycle-bin grid, not raw dates.** The document prefers raw irregular
   dates with Δt covariates; this pipeline aggregates to the EXISTING
   15-day × 36-bin cycle grid so the patch trial can run through the
   UNCHANGED severity/MDM80/FAR machinery — findings 18/20/21/22
   comparability is the point of the PoC. The cost is temporal smoothing of
   sudden single-date drops inside a bin median; the document's Δt
   covariate is replaced by days-since-last-valid-observation and per-bin
   observation count (computed by the trial change, not stored here).
   Documented deviation, carried into finding 23.

3. **8 channels = B1's channel set** (`scripts/trial_common.py:17`) so
   patch arms and the existing arms run identical channel budgets. The
   document's 7-channel no-LST variant stays an ablation for the later
   full run (E6), not the PoC.

4. **Per-pixel per-bin aggregation = median of valid acquisitions.**
   Mirrors the field-level median convention in `monitor/inputs.py`. A
   pixel-bin is valid iff ≥1 valid acquisition falls inside the bin; the
   count is stored so the trainer can weight and attribute.

5. **QA masking reused, not reinvented.** `io/landsat.py:45` quality_mask
   (fill, dilated cloud, cirrus, cloud, shadow, snow) is applied per pixel
   per scene before aggregation; masked pixels are excluded from
   aggregation — never zero-filled and treated as observed (AGENTS.md §8).
   valid_frac semantics stay identical to stats.zarr.

6. **Strict normalization split.** Per-channel per-sensor median/IQR from
   TRAIN fields within TRAIN periods only. The document's same-date
   cross-field median for LST is NOT adopted in v1: it reads all fields'
   values at a date, crossing the locked split boundary; recorded as an
   ablation with the leakage caveat.

7. **Storage layout** (`patches.zarr`, fp16, zarr v2):
   - `values` (F, C_cycles, 36, 8, 32, 32) — NaN where pixel-bin invalid
   - `pixel_valid` (F, C_cycles, 36, 1, 32, 32) uint8
   - `in_field` (F, 1, 32, 32) uint8 (static polygon mask)
   - `bbox_origin` (F, 2) uint16
   - `n_obs` (F, C_cycles, 36) uint8; `sensor_id` (F, C_cycles, 36) uint8
   - `cycle_ids`, `cycle_start_day`, `cycle_end_day`, and `cycle_valid`
   - `norm_stats.json`: `stats` keyed by sensor, then channel; median/IQR and
     observation count, with train cycle keys and lock/sidecar hashes
   - attrs: git sha, source product ids, QA bit list, cycles table sha,
     splits sha, creation date.
   Size ≈1.0 GB fp16 (1,717 usable cycles × 36 bins × 8 × 1024 px × 2 B) —
   not including padding slots. Training lazily reads admitted cycles.

8. **Resume = per-field manifest.** The exporter reads scenes for one field
   at a time and appends one JSON line per completed field to `.manifest.jsonl`
   inside the store. `--resume` skips those fields and checks the locked cycle
   binding and export selection; partial cycles do not become valid.

### Risks

- **Extraction cost** (538 dates × 490 fields × 8 bands, per-pixel):
  measured by `--estimate-runtime` before any full run; expected order
  1–3 h on the laptop (the ~33-min platform exporter reads the same
  rasters once per scene; masked per-field reads add the difference).
  Handed to the user as an exact command — the agent never launches long
  jobs (AGENTS.md §7).
- **LST at 30 m** is resampled from ~100 m thermal: a 17×17 field holds
  few independent thermal samples. Accepted for channel parity with B1;
  the caveat travels into the trial's interpretation.
- **Sensor mix inside one bin** (L8+L9 acquisitions): majority sensor per
  bin is recorded (`sensor_id`); no harmonization offsets in v1 —
  per-sensor σ standardization at scoring time handles the residual bias
  (document §7.3); cross-sensor offset estimation stays a later ablation.

### Audit follow-up

The exporter converts the source half-open window to inclusive offsets
(`cycle_end_day = t_end - 1`) and binds them to the locked epoch; training and the offline sidecar builder share the locked-train cycle
selector. Missing binding metadata is an error, not an inferred epoch. The
sidecar's `stats` envelope is consumed by the same transform in training and
scoring. Missing or zero-IQR entries for an individual sensor/channel retain raw
units; a missing or malformed envelope is rejected. Existing stores/checkpoints
are not migrated in place.
