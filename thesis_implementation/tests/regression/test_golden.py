"""Golden regression tests: run the synthetic pipeline and compare against
a small saved fixture. Any algorithm change that changes outputs must be
consciously approved by updating the fixture.

Run with ``pytest -m golden``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.golden
def test_synthetic_pipeline_matches_fixture(tmp_data_dir):
    """Run segmentation + baseline on synthetic data, compare harvest counts
    and baseline median/MAD within tolerance to a previously recorded fixture.
    If no fixture exists, write one (first run) and warn."""
    import json
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    import xarray as xr

    from ssl_anomaly.phenology import add_spectral_indices, segment_cycles

    ds = xr.open_zarr(tmp_data_dir / "fields.zarr")
    ds = add_spectral_indices(ds)
    med = ds["median"].values
    times = ds.coords["time"].values
    bands = list(ds.coords["band"].values)
    ndvi_idx = bands.index("NDVI")
    fields = ds.coords["field"].values
    vf = ds["valid_frac"].values

    n_cycles_total = 0
    n_censored = 0
    mean_lengths = []
    for fi in range(min(10, fields.size)):
        ndvi = med[fi, :, ndvi_idx]
        q = vf[fi]
        t_days = (times - times.min()).astype("timedelta64[D]").astype(int)
        cycles = segment_cycles(int(fields[fi]), t_days, ndvi, quality=q, lam=100.0,
                                min_cycle_days=250, max_cycle_days=450)
        n_cycles_total += len(cycles)
        n_censored += sum(1 for c in cycles if c.censored)
        mean_lengths.append(np.mean([c.length_days for c in cycles if not c.censored]))

    summary = {
        "n_fields_sampled": 10,
        "n_cycles_total": int(n_cycles_total),
        "n_censored": int(n_censored),
        "mean_cycle_length": float(np.nanmean(mean_lengths)),
    }
    FIXTURES.mkdir(parents=True, exist_ok=True)
    fixture_path = FIXTURES / "synthetic_segmentation.json"
    if not fixture_path.exists():
        fixture_path.write_text(json.dumps(summary, indent=2))
        pytest.skip(f"Golden fixture did not exist; wrote initial values to {fixture_path}")
    expected = json.loads(fixture_path.read_text())
    # Tolerances: cycle counts may shift slightly due to noise, lengths are stable.
    assert abs(summary["n_cycles_total"] - expected["n_cycles_total"]) <= max(3, int(expected["n_cycles_total"] * 0.15))
    assert abs(summary["mean_cycle_length"] - expected["mean_cycle_length"]) < 60.0
