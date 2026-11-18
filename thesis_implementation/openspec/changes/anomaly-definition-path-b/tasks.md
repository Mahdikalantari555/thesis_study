# Tasks — anomaly-definition-path-b

## 1. Family machinery (verdict-independent, TDD-first)

- [x] 1.1 Relation model: phenophase-binned robust fits (NDVI→LST;
      swir1|NDVI) on train cycles only, frozen + sha; leakage tests.
- [x] 1.2 Relational appliers: decoupled NDVI-drop (LST held/ε-lowered) and
      band-relation break, severity in relation-residual MAD units,
      field-level AND patch-tensor appliers; unit tests on profiles.
- [x] 1.3 Phenology-shape appliers: green-up delay {2,4} bins, grand-growth
      compression {20,40}%, early senescence {2,4} bins; clip-to-admitted-
      bins; covariate consistency tests.
- [x] 1.4 Gate file: the both-gates-failed condition encoded and tested
      (tasks §2 refuse to run without it).

## 2. Evaluation (HARD-GATED on both path-C failures)

- [ ] 2.1 Injection sets + hashes for the new families; B0/B1-class
      references recomputed in the same runs.
- [ ] 2.2 User-run sweeps through the unchanged protocol; per-pixel
      localization for relational families on patch scorers.
- [ ] 2.3 Persian finding (persian-writing skill): does the deep advantage
      appear on relational/shape anomalies where the document and
      deep-research predict it; anomaly-vs-stress wording discipline; L2
      ceiling; verdict = finding + owner decision, not silent adoption.

## Implementation notes (§1 complete, verdict-independent)

`src/ssl_anomaly/monitor/path_b.py`, 32 tests in `tests/unit/test_path_b.py`.

- **1.1** `fit_relations` — phenophase-binned Theil-Sen fits of `lst|ndvi` and
  `swir1|ndvi` with the residual MAD as the severity scale, frozen with a
  hash. Theil-Sen rather than OLS because the train cycles contain the very
  anomalies the family must detect; the test plants decoupled cycles on train
  and proves the line does not move. A bin the train cycles never covered keeps
  NaN and `predict` raises — a fabricated slope would make the family
  meaningless.
- **1.2** `inject_relational_break` at k·MAD for k ∈ {1,2,4,6}: NDVI dropped
  with LST held (or ε-lowered, hard-capped at 0.5 K — a larger coupled change
  is a physical anomaly, not a decoupling), and the swir1 break with NDVI
  fixed. Both field-level `(T,C)` and patch `(T,C,S,S)` appliers share the
  relation model. The realized deviation is MEASURED BACK in the declared unit
  and recorded, so an unreachable level is visible. The mask is never changed.
- **1.3** `warp_shape` for green-up delay {2,4}, growth compression {20,40} %,
  early senescence {2,4}, anchored on the cycle's OWN observed series (not a
  population template). **The mask is returned verbatim** and a value is
  written only into an OBSERVED bin: writing into an unobserved bin would
  invent an observation, and a missing→present transition is trivially
  detectable — the family would measure mask bookkeeping instead of phenology.
  `n_skipped_unobserved` records how much of the warp was lost; the covariate
  consequence is recorded with the result.
- **1.4** `require_path_c_failure` / `load_gates` / `write_gates` — fail-closed
  on a missing file, a missing gate, an empty verdict and on any pass. The gate
  is the change's conditionality mechanism, so it refuses rather than warns.

Wording discipline is enforced in the records: both families carry
`wording: "anomaly (...) — not stress"`, and no `pert_type` contains "stress".

Still hard-gated: 2.1–2.3 (evaluation, Persian finding).
