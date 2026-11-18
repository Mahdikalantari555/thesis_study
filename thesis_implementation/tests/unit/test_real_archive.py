"""Tests for real 490-field archive loader and provenance (rerun-rq-suite-on-real-490)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure src is importable
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.eval.real_archive import (
    get_archive_provenance,
    load_real490_archive,
    require_real_archive,
)


@pytest.mark.real_data
class TestRealArchiveLoader:
    def test_loads_expected_shape(self):
        arch = load_real490_archive()
        assert arch["X"].ndim == 3
        assert arch["X"].shape[1] == 36  # 15-day bins
        assert arch["X"].shape[2] == 8   # ndvi + 7 bands
        assert arch["bands"] == ["ndvi", "blue", "green", "red", "nir", "swir1", "swir2", "lst"]
        assert len(arch["field_ids"]) == arch["X"].shape[0]
        assert len(arch["start_years"]) == arch["X"].shape[0]
        assert arch["X"].shape[0] > 0

    def test_provenance_complete(self):
        arch = load_real490_archive()
        prov = arch["provenance"]
        required = [
            "data_source", "n_fields", "n_cycles", "n_dates",
            "first_acquisition_date", "last_acquisition_date",
            "cycle_file_sha256", "git_sha", "splits_sha256",
            "stats_zarr_sha256",
        ]
        for key in required:
            assert key in prov, f"missing provenance key: {key}"
            assert prov[key] is not None and prov[key] != "", f"empty provenance: {key}"
        assert prov["data_source"] == "real490"
        assert prov["n_dates"] == 538
        assert prov["first_acquisition_date"] == "2013-03-30"
        assert prov["last_acquisition_date"] == "2026-09-10"
        assert prov["n_cycles"] == arch["X"].shape[0]
        assert prov["n_fields"] == 490  # spec R1: total fields in stats.zarr, not just those with cycles

    def test_get_archive_provenance(self):
        arch = load_real490_archive()
        prov = get_archive_provenance(arch)
        assert prov["data_source"] == "real490"

    def test_absent_proxies_no_32farm_fields(self):
        arch = load_real490_archive()
        prov = arch["provenance"]
        # Proxies must be absent or from METRIC zonal stats, never from 32-farm cwsi_et
        assert prov.get("eta_deficit_source") in ("absent", "metric_zonal_eta_daily")
        assert prov.get("cwsi_source") in ("absent", "metric_zonal_cwsi_et")
        assert prov.get("y_stress_proxy") in (
            "weak_proxy_top20pct_mean_cwsi_not_validated_stress",
            "real_cwsi_et_zonal_top20pct",
        )
        # No cwsi_et borrowed from fields.zarr
        assert np.all(np.isnan(arch["eta_deficit"]))
        assert np.all(np.isnan(arch["cwsi"]))

class TestMissingArchive:
    def test_missing_files_fails_closed(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_real490_archive(
                stats_zarr_path=tmp_path / "nope.zarr",
                cycles_parquet_path=tmp_path / "nope.parquet",
                npz_path=tmp_path / "nope.npz",
            )

    def test_require_real_archive_exits_on_missing(self, tmp_path):
        with pytest.raises(SystemExit) as exc:
            require_real_archive(
                stats_zarr_path=tmp_path / "nope.zarr",
                cycles_parquet_path=tmp_path / "nope.parquet",
                npz_path=tmp_path / "nope.npz",
            )
        assert exc.value.code == 1
