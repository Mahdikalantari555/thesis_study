# 2026-10-24 — SSL scalable config + extension proposals

**Task:** User asked for assessment of SSL proposal vs their goal (label-free stress anomaly, multi-crop, sub-field, laptop-lightweight, ETaDaily/CWSI, cross-year same season, knowledge phase later) and to write a new file with proposals.

## Deliverable
- `SSL_Proposal/scalable_config_and_extensions.md` — new file with:
  - Core principle: single config drives model size/spatial level/inputs/device; profiles edge/laptop/server; only accuracy changes.
  - Config schema (YAML) covering system/model/spatial/input/anomaly/baseline.
  - Priority item 2: sub-field/pixel-level anomaly maps (Landsat 30m).
  - Priority item 5: cross-year/season alignment with multi-year normal baseline + crop calendar.
  - Other items (multi-crop, ETa/CWSI input toggle, knowledge/RAG phase, code impl, data QC, contamination, lightweight target, XAI) as expansion roadmap.
  - Roadmap + open decisions.
- README.md updated with new file row.

## Key design decision recorded
Code must be configurable by system capability (drone → server); no profile-specific branches in training code; profile change affects accuracy only.

## Status
Docs only; no implementation yet. Open decisions: default profile, spatial level, normal years, ETa/CWSI as input vs validation, crop calendar availability.
