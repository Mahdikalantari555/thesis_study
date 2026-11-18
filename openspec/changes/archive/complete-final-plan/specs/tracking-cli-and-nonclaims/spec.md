# Spec Delta

## Purpose

Provides local SQLite MLflow provenance tracking, complete Hydra configuration files, wired `ssl-anomaly` Click CLI subcommands, updated DVC stages, and thesis findings documentation explicitly enforcing literature non-goals and non-claims.

## ADDED Requirements

### Requirement: Local SQLite MLflow tracking and wired CLI subcommands
The system SHALL log runs, parameters, metrics, `git SHA`, `uv.lock` hash, `splits.json` hash, and seeds to `sqlite:///mlruns/mlflow.db`, provide composable YAML configs under `conf/`, and execute real pipeline logic across `ssl-anomaly` CLI subcommands (`baseline`, `train`, `evaluate`, `export`, `rq1`..`rq8`).

#### Scenario: Tracked run and CLI subcommands execute locally without placeholder warnings
- **WHEN** pipeline runs log to the local tracker and `ssl-anomaly` subcommands are invoked
- **THEN** SQLite MLflow records provenance tags and metrics locally and CLI subcommands exit with code 0 without placeholder no-op messages

### Requirement: Findings documentation with explicit literature non-goals and non-claims
The system SHALL document empirical `RQ1–RQ8` results in `docs/findings/` while explicitly stating literature non-goals (no Phase 3 3D-CAE, multi-crop, web-GIS, ONNX/edge, or extra Rust expansion) and non-claims (never claiming "first label-free crop-stress detection", framing strictly as long-archive Landsat optical+thermal field-level anomaly detection with independent proxy validation).

#### Scenario: Findings index and RQ report preserve non-claims and non-goals
- **WHEN** `docs/findings/00_index.md` and `docs/findings/11_rq1_to_rq8_empirical_framework.md` are inspected
- **THEN** all `RQ1–RQ8` metrics with confidence intervals, the `anomaly != stress` rule, and all five literature non-goals/non-claims are explicitly documented
