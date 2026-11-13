"""Local SQLite MLflow provenance tracker (``docs/final_plan.md`` §6).

Logs git commit SHA, ``splits.json`` SHA256 fingerprint, RNG seed, parameters,
scalar metrics, and JSON/CSV artifacts to ``sqlite:///mlruns/mlflow.db`` with zero
external server dependencies.
"""

from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any


def get_git_commit_sha() -> str:
    """Return current HEAD commit SHA or ``'unknown'``."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True, timeout=3
        )
        return out.strip()
    except Exception:
        return "unknown"


def compute_file_sha256(path: str | Path) -> str:
    """Compute SHA256 hex digest of ``path`` (or ``'missing'`` if absent)."""
    p = Path(path)
    if not p.exists():
        return "missing"
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@contextmanager
def track_experiment_run(
    experiment_name: str = "ssl_sugarcane_anomaly",
    run_name: str | None = None,
    *,
    db_path: str | Path = "mlruns/mlflow.db",
    splits_path: str | Path = "data/processed/splits.json",
    seed: int = 42,
    params: dict[str, Any] | None = None,
) -> Iterator[Any]:
    """Context manager wrapping an MLflow SQLite run with full provenance tags."""
    import mlflow

    db_file = Path(db_path).resolve()
    db_file.parent.mkdir(parents=True, exist_ok=True)
    art_dir = (db_file.parent / "artifacts").resolve()
    art_dir.mkdir(parents=True, exist_ok=True)

    tracking_uri = f"sqlite:///{db_file}"
    mlflow.set_tracking_uri(tracking_uri)
    exp = mlflow.get_experiment_by_name(experiment_name)
    if exp is None:
        mlflow.create_experiment(experiment_name, artifact_location=art_dir.as_uri())
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tags(
            {
                "git_commit_sha": get_git_commit_sha(),
                "splits_sha256": compute_file_sha256(splits_path),
                "seed": str(seed),
            }
        )
        if params:
            mlflow.log_params({k: str(v) for k, v in params.items()})
        yield run


def log_run_metrics_and_artifacts(
    metrics: dict[str, float],
    artifacts: list[str | Path] | None = None,
) -> None:
    """Log finite scalar metrics and existing artifact files into the active MLflow run."""
    import math

    import mlflow

    clean_m = {
        k: float(v)
        for k, v in metrics.items()
        if isinstance(v, (int, float)) and math.isfinite(float(v))
    }
    if clean_m:
        mlflow.log_metrics(clean_m)
    if artifacts:
        for a in artifacts:
            ap = Path(a)
            if ap.exists():
                mlflow.log_artifact(str(ap))
