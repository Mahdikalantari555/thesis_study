"""Dev-log schema validation (task 5b.6) and run-manifest requirements."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import protocol as mproto  # noqa: E402

REQUIRED_COLUMNS = {
    "run_id", "date", "model_id", "config_hash", "seeds", "n_train_cycles",
    "n_dev_cycles", "primary_metric_mean", "primary_metric_std",
    "median_delay_days", "far_target", "far_achieved", "tau", "k",
    "aucpr_25", "aucpr_50", "aucpr_75", "nrmse_mean",
    "params", "wall_time_s", "device", "git_sha", "data_source",
    "splits_sha256", "ladder_rung",
    # Severity protocol (literature-grounded-severity-protocol task 2.3).
    "protocol", "scorer", "severity_table_sha256", "eval_subset_sha256", "mdm80",
}


def test_dev_log_columns_cover_spec() -> None:
    """Schema must carry provenance + the agreed metric fields (D6/D8)."""
    missing = REQUIRED_COLUMNS - set(mproto.DEV_LOG_COLUMNS)
    assert not missing, f"dev_log schema missing required columns: {missing}"


def test_append_and_read_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "dev_log.csv"
    row = {c: "" for c in mproto.DEV_LOG_COLUMNS}
    row.update({"run_id": "r1", "model_id": "gru_ae", "primary_metric_mean": 0.5})
    mproto.append_dev_log(row, path=p)
    mproto.append_dev_log({**row, "run_id": "r2"}, path=p)
    rows = mproto.read_dev_log(path=p)
    assert [r["run_id"] for r in rows] == ["r1", "r2"]
    assert rows[0]["primary_metric_mean"] == "0.5"
    # Header matches the schema.
    header = p.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert header == list(mproto.DEV_LOG_COLUMNS)


def test_append_rejects_unknown_and_missing(tmp_path: Path) -> None:
    p = tmp_path / "dev_log.csv"
    base = {c: "" for c in mproto.DEV_LOG_COLUMNS}
    with pytest.raises(ValueError, match="unknown columns"):
        mproto.append_dev_log({**base, "bogus": 1}, path=p)
    with pytest.raises(ValueError, match="missing columns"):
        mproto.append_dev_log({k: v for k, v in base.items() if k != "run_id"}, path=p)


def test_existing_dev_log_rows_conform(tmp_path: Path) -> None:
    """If reports/dev_log.csv exists, its header must match the schema exactly."""
    p = mproto.DEV_LOG_PATH
    if not p.exists():
        pytest.skip("reports/dev_log.csv not created yet")
    header = p.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert header == list(mproto.DEV_LOG_COLUMNS)


def test_mean_std() -> None:
    assert mproto.mean_std([1.0, 2.0, 3.0]) == pytest.approx((2.0, 1.0))
    assert mproto.mean_std([5.0]) == (5.0, 0.0)
    with pytest.raises(ValueError):
        mproto.mean_std([])
