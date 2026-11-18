# Change: gradual-severity-shape

## Why

The finding-18 severity protocol tests two temporal shapes only — acute and
persistent. The architecture document §10 defines THREE shapes (sudden,
persistent, **gradual**), calls gradual "the hardest" (a slowly drifting
series is tracked by local state; only an anchor outside the local window —
the phenophase-matched climatology B0 — can catch it), and the pre-registered
full-run success criterion is "beats B0/B1 on MDM80 for **≥2 of the 3
temporal shapes**" — which is undecidable without the third shape. Owner
feature 14 (notes.md) likewise demands ناگهانی/تدریجی/پایدار.

The document's gradual specification: linear ramp over 3–6 observations,
then held. In the 15-day bin grid: linear ramp over 3–6 bins to the final
δ, then held to cycle end.

## What Changes

- **New temporal shape `gradual`** in the severity protocol — same absolute
  δ ladder (S1–S6), families {ndvi, savi}, the existing sum-preserving
  red/nir solver; ramp duration drawn from {3, 4, 6} bins (seed-fixed per
  injection set), δ reached linearly, then held.
- **MDM80 per shape** — every arm report gains MDM80(gradual/ndvi),
  MDM80(gradual/savi) with ">S6" censoring semantics unchanged; the
  three-shape MDM curve becomes the headline quantity (document §10).
- **Protocol hash bump** — new injection-set hashes; existing acute/
  persistent sets and their recorded results are NOT regenerated (findings
  18/21/22 comparability preserved); the new shape is additive.
- **Sequencing** — applied AFTER the `predictive-ssl-controlled-trial`
  verdict (its injection sets are locked mid-trial) and usable by the patch
  PoC immediately (the PoC can adopt the extended protocol; otherwise the
  patch arms run gradual as their first post-PoC evaluation).
- **B0 anchoring check** — the gradual shape must be reported WITH
  `b0_calendar` (phenophase-matched climatology) results, since the
  document predicts no local-state model beats B0 on slow drift; an honest
  negative there is an expected, publishable outcome, not a failure.
- **Secondary diagnostic shapes (owner decision 2026-11-15, guide §3)** —
  **peak-disruption** (reduce the cycle's peak NDVI/SAVI magnitude by δ, or
  shift the peak plateau later by k ∈ {2, 3} bins) and **recovery-
  disruption** (after an acute drop of depth δ over d bins: failure-to-
  recover — hold the dropped level for r ∈ {3, 6} bins — or slow-recovery —
  ramp back at half the natural slope). Both are pre-registered HERE,
  before any result exists, as SECONDARY diagnostic shapes: reported per
  shape through the same machinery, but the primary gates of the trials
  stay on the index-drop acute/persistent/gradual family — no goalpost
  movement. With these two, the guide's five synthetic types are covered
  except growth-delay, which stays inside `anomaly-definition-path-b`'s
  phenology family per the owner's decision.
- **Explicit non-goals:** no new severity levels; no retraining triggered by
  this change; no protocol edits to the locked trial sets; no platform
  changes; growth-delay/phenology warps NOT implemented here (path-B scope).
