# Change: patch-independent-indicators

## Why

Owner feature 15 demands comparison with TVDI, CWSI, ETa and
spectral-temporal indices; the architecture document §10 (E10) defines the
program — phenophase-matched indicator z-scores, rank agreement, enrichment,
timing — with three explicit cautions (shared inputs with the model;
weather/irrigation responsiveness; disagreement = information, not
failure). The field-level part-D machinery exists (trial_part_d), and
CWSI_ET is PRESENT as a 32-field subset in stats_current.zarr, but nothing
adapts this to the patch arms, and the todo item 7 (physical Idso/Jackson
CWSI from ERA5 air temperature) — a strictly better indicator than the
current heuristic — is still unimplemented. This change is the proxy-evidence
bridge toward L4 (its ceiling stays L3 + proxy agreement until advisor item
A2 supplies real ground truth).

## What Changes

- **Part-D adaptation for patch arms** — flagged (field, bin) events from
  patch scorers (and their per-pixel event maps) vs available indicators,
  with the same agreement statistics as field-level part D: Spearman rank
  correlation, enrichment (share of top-5% flagged field-cycles exceeding
  the indicator's own threshold vs chance), and timing (alarms lead /
  coincide with / lag indicator exceedance).
- **Physical CWSI (todo item 7 merged)** — Idso/Jackson CWSI
  (Tc − Ta)/(Tc_upper − Ta_lower) from per-scene LST + ERA5 air
  temperature (already joined), replacing the hard-coded (20 °C, 25 °C)
  heuristic for the indicator comparisons; Idso baseline coefficients
  cited and recorded in the model card; where baselines are unavailable
  for the local climate, the indicator is `absent` — never synthesized.
- **Indicator availability check FIRST** — CWSI_ET (32-field subset),
  TVDI (derived from per-scene LST/NDVI field stats), physical CWSI (new),
  ETa/ETrF (absent as processed field stats → `absent`); anything
  unavailable is `absent`, never a placeholder.
- **LST-independence analysis (E10 tie-in)** — indicator agreement compared
  for the arm WITH LST vs the E6 LST-off arm (checkpoint dependency on
  `patch-full-run-and-ablations`); agreement read as corroboration ONLY
  for indicators that do not share the arm's inputs (document §10 caution).
- **Phenophase-matched z-scores** for every indicator (same 2-bin
  phenophase grouping as the model σ tables) — comparing raw indicator
  values against phase-aware models is a category error the document
  explicitly warns about.
- **Weather + neighbor external consistency (owner validation guide §4,
  2026-11-15)** — event-level weather context from the already-joined ERA5
  (precipitation deficit vs historical reference, unusual Tmax, ET0 rise,
  VPD rise) and neighbor/regional context (do adjacent / same-block fields
  also deviate in the same period?) — each alarm classified as
  local-with-consistent-weather / regional-common-mode / local-unexplained.
  Disagreement is NOT model error by default: disease, salinity, pest or
  management alternatives are recorded as candidate causes. The adjacency
  source links to todo item 11 (registry-aware neighbor graphs; block
  adjacency as the v1 fallback).
- **Explicit non-goals:** no L4 claims (A2-gated); no platform wiring of
  indicators (separate queued items 1–2); no new model training except the
  E6 dependency noted above.
