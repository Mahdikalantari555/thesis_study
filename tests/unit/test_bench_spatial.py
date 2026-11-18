"""The benchmark artifact must exist and be self-consistent (task 1.2 / G5).

The spec requires that runtime estimates come from a measured artifact rather
than assumptions, and that the lazy-vs-materialized decision cites the same
artifact. These tests run the benchmark on a synthetic store (seconds, no
archive) and assert the artifact's contract.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _load_bench():
    spec = importlib.util.spec_from_file_location(
        "bench_spatial", REPO / "scripts" / "bench_spatial_representations.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bench_spatial"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def artifact(tmp_path_factory):
    out = tmp_path_factory.mktemp("bench")
    bench = _load_bench()
    rc = bench.main([
        "--out", str(out), "--batch-size", "1", "--lazy-reads", "2",
        "--cycles", "2", "--synthetic-size", "8", "--epochs", "2",
    ])
    assert rc == 0
    files = sorted(out.glob("spatial_*.json"))
    assert files, "benchmark wrote no artifact"
    return json.loads(files[-1].read_text())


def test_artifact_records_environment_and_source(artifact):
    for key in ("protocol", "created", "python", "torch", "platform", "cpu_count",
                "data_source", "synthetic"):
        assert key in artifact, key
    assert artifact["synthetic"] is True


def test_data_access_is_measured_with_a_cited_decision(artifact):
    da = artifact["data_access"]
    assert da["lazy_random"]["n_reads"] > 0
    assert da["lazy_random"]["seconds_per_read"] > 0
    assert da["materialized"]["n_cycles"] > 0
    assert da["decision"] in ("lazy", "materialize-per-field")
    assert ">2x" in da["decision_rule"]
    assert da["bulk_speedup"] >= 0


def test_every_representation_is_timed_with_support(artifact):
    reps = artifact["representations"]
    assert set(reps) == {"R1_32px", "R2_16px", "R3_32px", "R1_pixelwise_32px"}
    for name, r in reps.items():
        assert r["samples_per_second"] > 0, name
        assert r["step_seconds"] > 0
        assert r["epoch_seconds_at_100_samples"] > 0
        assert r["peak_ram_mb"] > 0
        assert 0 <= r["cpu_utilization"] <= 100
        # 30 m GSD: side_m = px * 30, area_ha = px^2 * 0.09
        side_m = r["window_px"] * 30.0
        assert r["spatial_support"]["side_m"] == pytest.approx(side_m, rel=1e-9)
        assert r["spatial_support"]["area_ha"] == pytest.approx(
            (side_m ** 2) / 10_000.0, rel=1e-6
        )


def test_estimates_are_extrapolated_not_guessed(artifact):
    for name, r in artifact["representations"].items():
        expected = r["step_seconds"] * 100
        assert r["epoch_seconds_at_100_samples"] == pytest.approx(expected, rel=0.01), name


def test_capacity_and_geometry_are_part_of_the_artifact(artifact):
    assert "capacity" in artifact
    assert "flags" in artifact["capacity"]
    memo = artifact["geometry_memo"]
    assert memo["default_window_px"] == 32
    assert memo["excluded_window_px"] == 64
    assert artifact["spatial_arithmetic"]["ha_per_px"] == pytest.approx(0.09)


def test_r2_is_cheaper_than_r1(artifact):
    """A 16 px window must cost less than a 32 px one — sanity on the timing."""
    r1 = artifact["representations"]["R1_32px"]["step_seconds"]
    r2 = artifact["representations"]["R2_16px"]["step_seconds"]
    assert r2 < r1


def test_peak_ram_helper_is_positive():
    bench = _load_bench()
    assert bench.peak_ram_mb() > 0
