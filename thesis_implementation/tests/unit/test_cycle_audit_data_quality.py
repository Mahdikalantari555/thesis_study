"""Regression tests for the 2026-11-14 cycle-audit fixes.

BUG 1: audit_cycles.py flagged cycles overlapping OTHER fields' cycles in the
same block (staggered harvest makes that normal); design D2 requires overlap
against the SAME field's neighbouring cycles only. The 96.7% flag rate and its
"BLOCKING" verdict were void.

BUG 2: data_quality_report.py recounted cycles by filtering stats_long on
band == "ndvi" — a band that does not exist — so the recount silently
returned 0. NDVI must be computed from red + nir.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def audit():
    return _load("audit_cycles")


@pytest.fixture(scope="module")
def dqr():
    return _load("data_quality_report")


def _cycle(field, cycle_id, t_start, t_end, length=None, **kw):
    c = {
        "field": field,
        "cycle_id": cycle_id,
        "t_start": t_start,
        "t_end": t_end,
        "length_days": length if length is not None else t_end - t_start,
        "kind": "ratoon",
        "ratoon_no": 1,
        "start_harvest": t_start,
        "end_harvest": t_end,
        "s_date": pd.Timestamp("2020-01-01") + pd.Timedelta(days=t_start),
        "e_date": pd.Timestamp("2020-01-01") + pd.Timedelta(days=t_end),
        "year": 2020,
        "block": kw.pop("block", "L08"),
    }
    c.update(kw)
    return c


class TestOverlapFlag:
    """compute_flags: same-field overlap only (BUG 1 regression)."""

    def test_same_field_overlap_flagged(self, audit):
        cycles = [
            _cycle(1, 0, 0, 100),
            _cycle(1, 1, 50, 150),  # overlaps cycle 0 of the same field
        ]
        flags = audit.compute_flags(cycles)
        assert "overlap_with_neighbour" in flags[(1, 0)]
        assert "overlap_with_neighbour" in flags[(1, 1)]

    def test_cross_field_overlap_NOT_flagged(self, audit):
        # Two different fields in the same block, harvests staggered by years:
        # calendar overlap is normal agronomy, never a segmentation error.
        cycles = [
            _cycle(52, 0, 19746, 20142, block="L08"),
            _cycle(53, 0, 18170, 18571, block="L08"),  # 401 days, in range
        ]
        flags = audit.compute_flags(cycles)
        assert flags[(52, 0)] == []
        assert flags[(53, 0)] == []

    def test_adjacent_cycles_not_flagged(self, audit):
        # Cycles tiling the axis share a boundary; exclusive end must not flag.
        cycles = [
            _cycle(1, 0, 0, 250),
            _cycle(1, 1, 250, 490),
        ]
        flags = audit.compute_flags(cycles)
        assert flags[(1, 0)] == []
        assert flags[(1, 1)] == []

    def test_length_flag(self, audit):
        cycles = [_cycle(1, 0, 0, 100)]  # 100 days < 240
        flags = audit.compute_flags(cycles)
        assert "length_out_of_range" in flags[(1, 0)]


class TestStratifiedSample:
    def test_deterministic_and_capped(self, audit):
        rng = np.random.RandomState(7)
        cycles = [
            _cycle(f, 0, 0, 100 + 40 * i, block=f"L0{i % 3}")
            for i, f in enumerate(range(12))
        ]
        for c in cycles:
            c["year"] = 2013 + (c["field"] % 3)
        a = audit.stratified_sample(cycles, 6, np.random.RandomState(7))
        b = audit.stratified_sample(cycles, 6, np.random.RandomState(7))
        assert len(a) == 6
        assert [(c["field"], c["cycle_id"]) for c in a] == [(c["field"], c["cycle_id"]) for c in b]
        blocks = {c["block"] for c in a}
        assert len(blocks) >= 2  # strata are represented


def _band_rows(field_id, dates, band, values):
    return pd.DataFrame({
        "field_id": field_id,
        "date": pd.to_datetime(dates),
        "band": band,
        "mean": values,
        "median": values,
        "std": np.zeros(len(dates)),
        "valid_frac": np.ones(len(dates)),
    })


def _trapezoid(length, ndvi_max=0.85, ndvi_min=0.2):
    y = np.full(length, ndvi_min)
    p1, p2 = length // 4, (3 * length) // 4
    y[:p1] = np.linspace(ndvi_min, ndvi_max, p1)
    y[p1:p2] = ndvi_max
    y[p2:] = np.linspace(ndvi_max, ndvi_min, length - p2)
    return y


def _ndvi_to_bands(ndvi, base_date="2015-01-01", cadence=8, rng=None):
    """Sample an NDVI series at `cadence`-day cadence (with noise + dropped obs,
    mirroring tests/unit/test_cycles.py) and emit red/nir band rows (nir+red = 1).
    A noiseless series over-smooths under CV-tuned Whittaker and yields no cycles."""
    ndvi = np.asarray(ndvi, dtype=float)
    t = np.arange(0, ndvi.size, cadence)
    obs = ndvi[t] + (rng.normal(0, 0.01, t.size) if rng is not None else 0.0)
    if rng is not None:
        keep = rng.random(t.size) > 0.15
        t, obs = t[keep], obs[keep]
    dates = pd.to_datetime(base_date) + pd.to_timedelta(t, unit="D")
    red = (1.0 - obs) / 2.0
    nir = (1.0 + obs) / 2.0
    return _band_rows(1, dates, "red", red), _band_rows(1, dates, "nir", nir)


class TestRecountCycles:
    def test_counts_cycles_from_red_nir(self, dqr, rng):
        ndvi = np.concatenate([
            _trapezoid(340), _trapezoid(340), _trapezoid(330),
        ])
        red, nir = _ndvi_to_bands(ndvi, rng=rng)
        stats_long = pd.concat([red, nir], ignore_index=True)
        farms = pd.DataFrame({"field_id": [1], "block": ["L08"]})
        total, err, details = dqr.recount_cycles(farms, stats_long)
        assert err is None
        assert total >= 1
        assert details["fields_scanned"] == 1
        assert details["fields_errors"] == 0
        assert details["fields_skipped_no_data"] == 0

    def test_field_without_red_nir_is_counted_as_skipped(self, dqr):
        # A field with only LST rows must be counted as skipped, not silently
        # folded into a 0 (BUG 2 regression).
        dates = pd.date_range("2015-01-01", periods=60, freq="16D")
        stats_long = _band_rows(2, dates, "lst", np.full(60, 300.0))
        farms = pd.DataFrame({"field_id": [2], "block": ["L08"]})
        total, err, details = dqr.recount_cycles(farms, stats_long)
        assert err is None
        assert total == 0
        assert details["fields_skipped_no_data"] == 1

    def test_missing_ndvi_band_filter_would_return_zero(self, dqr):
        # Documents the old failure mode: filtering on band == 'ndvi' matches
        # nothing because stats_long carries blue/green/lst/nir/red/swir1/swir2.
        ndvi = np.concatenate([_trapezoid(340), _trapezoid(340)])
        red, nir = _ndvi_to_bands(ndvi)
        stats_long = pd.concat([red, nir], ignore_index=True)
        assert (stats_long["band"] == "ndvi").sum() == 0
