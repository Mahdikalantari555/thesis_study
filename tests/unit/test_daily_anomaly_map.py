from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np

SCRIPTS_DIR = str(Path(__file__).resolve().parents[2] / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def test_daily_anomaly_and_map_color_changes(tmp_path: Path, tmp_data_dir, monkeypatch):
    """Verify compute_daily_anomaly produces per-bin z-scores and map colors change per date."""
    from build_baseline import main as build_baseline
    from compute_daily_anomaly import compute_daily_anomaly_df
    from make_map_custom import anomaly_color, build_custom_map

    monkeypatch.chdir(tmp_path)
    assert build_baseline() == 0
    df = compute_daily_anomaly_df(
        zarr_path=tmp_data_dir / "fields.zarr",
        cycles_path=tmp_data_dir / "cycles.parquet",
        baseline_path=tmp_data_dir / "baseline.npz",
    )
    assert not df.empty
    assert {"field", "date", "bin_idx", "anomaly"}.issubset(df.columns)
    assert np.all(np.isfinite(df["anomaly"].values))

    # Within a single cycle, different observation dates must yield varying scores (not constant cycle-level)
    within_cycle_stds = (
        df.groupby(["field", "cycle_id"])["anomaly"]
        .agg(["count", "std"])
        .query("count >= 5")["std"]
    )
    assert len(within_cycle_stds) > 0
    assert float(within_cycle_stds.median()) > 0.1

    daily_out = tmp_path / "daily_anomaly.parquet"
    html_out = tmp_path / "anomaly_map_custom.html"
    df.to_parquet(daily_out, index=False)

    out_path, diag = build_custom_map(
        zarr_path=tmp_data_dir / "fields.zarr",
        daily_path=daily_out,
        out_path=html_out,
    )
    assert out_path.exists()
    assert diag["fields_with_color_changes"] >= 15
    assert diag["total_color_transitions"] >= 100

    html = out_path.read_text(encoding="utf-8")
    assert "Daily anomaly score (S)" in html
    assert re.search(r"var data = \{.*\};", html)
    assert anomaly_color(1.5) == "#22c55e"
    assert anomaly_color(5.0) == "#eab308"
    assert anomaly_color(9.0) == "#dc2626"
    assert anomaly_color(None) == "#888888"
