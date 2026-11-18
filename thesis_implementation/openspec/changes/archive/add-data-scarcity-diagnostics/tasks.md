# Tasks — Data-Scarcity & Representation-Quality Diagnostics (`DS1–DS5`)

## 1. Environment & packaging
- [x] 1.1 Create `.venv`, install project deps + `torch`/`matplotlib` from PyPI; `pip install -e . --no-deps`
- [x] 1.2 Add `matplotlib>=3.8` to `pyproject.toml` dependencies and regenerate `uv.lock` (`uv lock`)
- [x] 1.3 Add root `environment.yaml` (conda env spec mirroring pyproject) for non-uv users
- [x] 1.4 Register `data_scarcity` stage in `dvc.yaml`

## 2. Core implementation
- [x] 2.1 Implement `src/ssl_anomaly/eval/data_scarcity.py` (`mean_cosine_similarity`, `alignment_uniformity`, `embedding_quality_report`, `learning_curve`, `few_shot_probe`, `tsne_projection`); export from `eval/__init__.py`
- [x] 2.2 Add `train_pretext_arm_tracked` (+ shared `_arm_batch_loss` helper) to `src/ssl_anomaly/models/pretexts.py` without changing `train_pretext_arm`
- [x] 2.3 Create `scripts/run_data_scarcity.py` (data loading like `run_rq2_pretexts.py`, weak-proxy CWSI labels, DS1–DS5 orchestration, JSON/CSV/PNG outputs)

## 3. Tests
- [x] 3.1 Add `tests/unit/test_data_scarcity.py` (synthetic-embedding identities for collapse/alignment/uniformity, dummy-trainer learning-curve plumbing, few-shot shapes, tracked-trainer history)
- [x] 3.2 Run new unit tests + full `pytest` suite; fix regressions

## 4. Run on available data & reports
- [x] 4.1 Generate `data/processed/cycles.parquet` via `python -m ssl_anomaly.cli segment` on `fields.zarr`
- [x] 4.2 Run `scripts/run_data_scarcity.py` on the real 32-farm archive (and `--simulate-490-if-missing` pass if time allows) → `reports/data_scarcity.{json,csv}` + figures

## 5. Docs
- [x] 5.1 Write `docs/findings/12_data_scarcity_diagnostics.md` with measured numbers; update `docs/findings/00_index.md`
- [x] 5.2 Write `docs/eval_protocol_future_models.md` (mandatory protocol + scarcity thresholds for future models)

## 6. Commit & push
- [x] 6.1 Commit all changes on `arena/c9a04559-thesis-implementation` and push to origin
