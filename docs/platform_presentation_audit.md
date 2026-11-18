# Platform presentation-readiness audit (UI/UX + researcher perspective)

**Date:** 2026-11-07 · **Scope:** all 8 views, data layer, i18n, payloads, tile server ·
**Standard:** every value on screen must be traceable to a real artifact under
`Data/Processed/` or an explicit "absent/not recorded" state; every label must
describe what the data actually is. Findings feed change
`wire-platform-to-real-data` (tasks §2–§7).

## Verdict

The platform is structurally presentation-ready (8 coherent views, bilingual
RTL/LTR, provenance chips, bug-audit discipline), but a reviewer would catch
**four claims that are not true today**. All are fixable in one pass; none
require new views or contract changes.

## P0 — integrity blockers (a false claim on screen)

| # | Finding | Evidence | Fix |
|---|---------|----------|-----|
| A1 | **SSL scores shown are the CWSI proxy formula, not the trained models.** Every observation's `scoreProvenance` is `proxy` for all 7 model ids, while `checkpoints/sts_net_490.pt`, `tiny_cnn_mamba_490.pt`, `time2agri_490.pt` exist. The last export ran without checkpoint inference, so the "SSL Transformer / STS-Net / Tiny-CNN-Mamba / Time2Agri" labels present proxy values as model output. | `series_khuzestan.json` obs0 `scoreProvenance` all `proxy`; checkpoints present | Re-export **without** `--no-models`; verify `model` provenance appears for the 3 checkpoint models |
| A2 | **Fabricated field attributes.** `farm` = f-string `Khuzestan Unit {code[:3]}`, `municipality` = `Amir Kabir / Debal Khazai Agro-Industry (Block …)`, `variety` defaults to `CP69-1062`, `areaHa` to 25, `block` to `R01` — none of these come from the registry. | `export_platform_data.py:343-345`, `mock.ts:126-143` | Map real `farms.parquet` columns; empty when the registry is empty |
| A3 | **Null weather labelled "Modelled".** `precip`/`temp` are 100% null yet `provenanceDefault: 'modelled'` renders blue "Modelled" chips next to "—" values. | payload `prov.precip=temp=modelled`, value null | Join `weather_aligned.parquet` (real reanalysis); null → `absent`; normalizer force `absent` on null |
| A4 | **Frontend fabricates data for missing values.** `NUMERIC_FALLBACK = 0.5` turns every absent anomaly score into a fake 0.5 point (pollutes Overview means/anomaly-rates, ModelComparison distributions, Moran's I feeds `?? 0` zeros in Spatial). CSV export writes `0.0000` for null channels. | `mock.ts:259,287`; `Spatial.tsx:17,75`; `Reports.tsx:38` | Scores nullable; finite-only statistics; CSV empty cells for null |

## P1 — honesty of copy (wrong story, right data)

| # | Finding | Fix |
|---|---------|-----|
| B1 | "Demonstration data" badge + banner + overview footers + exports note + spectral note say the data is demo, while it is the real pipeline output | Reword to pipeline-output / dataset-integration wording (`DemoDataBadge` → `PipelineDataBadge`) |
| B2 | Footer cadence "Sentinel-2 / Landsat-like cadence (demonstration)" — wrong sensor (archive is Landsat & METRIC 2013–2026) | "Landsat & METRIC (2013–2026 archive)" |
| B3 | "Mock stress event: …" i18n + dead `stressEvent` machinery (null for all 490 fields) | Remove machinery + strings |
| B4 | "Legacy payload detected — written before contractVersion 2" banner appears although the on-disk payload is v3 (stale `dist/` bundle) | Rebuild; verify notice gone |

## P2 — UX defects in Map Explorer (demo-flow blockers)

| # | Finding | Fix |
|---|---------|-----|
| C1 | "Hide" (field boundaries) unmounts the whole map — raster + basemap vanish; the raster cannot be viewed alone | `MapView` stays mounted; `showFields` prop hides only the polygon layer |
| C2 | Fields opacity slider floors at 20% (`min={0.2}`); raster opacity resets to 1 on scene/layer switch | `min={0}`; mount layers with current `rasterOpacity` |
| C3 | Two date controls (observation slider + "Landsat raster scene" select) that can disagree | One observation-date slider drives field series **and** raster (raster date = that observation's real `acquisitionDate`; no scene → raster off) |

## P3 — accepted limitations (documented, not fixed here)

- `planted`/`harvest` stay "—" (registry has no source column; only `age`).
- Validation event thresholds per indicator are declared constants, documented in-view.
- Chart x-axes keep ISO `YYYY-MM` in both locales; registry Persian strings (اداره…, تولید دوم) pass through verbatim.
- Basemap tiles need network access; the app itself is offline.
- `masked_transformer` has no checkpoint → stays `proxy` with formula id (honest labelling).
  *(Superseded by contract v5: `masked_transformer`/`gru_ae` are wired to the causal main
  checkpoints `masked_transformer_main`/`gru_ae_main` and are `absent` (null score) without
  the artifacts; the CWSI proxy formula no longer exists for any score slot — see
  `docs/platform_score_methods.md` §4.3.)*

## Researcher view (what a committee would ask)

1. "Which model produced these scores?" → after A1, chips answer per score:
   `model` (+ checkpoint id) / `proxy` (+ formula id) / `absent`. Baselines
   B0/B1 are honestly labelled formula-based.
   *(v5 update: scores are `model` or `absent` only — the proxy state was removed; the
   stress-flag chip additionally names the checkpoint and the observation's split, with
   train observations tagged "Train (in-sample)".)*
2. "Is the weather real?" → ERA5 reanalysis joined on acquisition date (A3).
3. "Are the field names real?" → registry pass-through (A2), Persian intact.
4. "What does '—' mean?" → `absent` chip: no acquisition/registry value; never
   a fabricated number (A4).
5. "Can I export this?" → CSVs carry real values with empty cells for absent
   channels and provenance JSON per row (A4).

## Resolution (2026-11-07, same day)

All P0/P1/P2 findings were fixed inside `wire-platform-to-real-data` and
verified by the runtime gate (see `docs/platform_bug_audit.md`, section
"wire-platform-to-real-data"):

- **A1** re-exported with checkpoints: 9,639 `model`-provenance score cells
  (sts_net / tiny_cnn_mamba / time2agri over 799 cycles).
- **A2** real registry columns; 0 synthesized strings (contract test).
- **A3** weather join 100% coverage (21070/21070); null → `absent` everywhere.
- **A4** scores nullable, finite-only statistics, complete-case Moran's I,
  CSV empty cells.
- **B1–B4** copy reworded (badge/banner/footers/exports note), stressEvent
  machinery removed, fresh bundle (legacy notice gone).
- **C1–C3** hide hides only polygons (raster+basemap stay: `tile_nofields.png`
  evidence), opacity floor 0, single date slider drives fields + raster with
  opacity persistence (0.7→0.7 across an RGB→NDVI switch).
- **P3** unchanged (documented limitations).
