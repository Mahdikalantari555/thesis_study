"""Reader adapter for Data/Processed/satellite/stats.zarr.

Reads 490 fields across 538 acquisition dates and 7 spectral/thermal bands.
Provides array access, quality masking, index calculations, and xarray conversion.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import xarray as xr
import zarr

log = logging.getLogger("ssl_anomaly.io.stats_zarr")

EXPECTED_BANDS = ("blue", "green", "red", "nir", "swir1", "swir2", "lst")
BASE_DATE = pd.Timestamp("2013-03-30 00:00:00")


@dataclass
class StatsZarrReader:
    """Adapter for opening and reading stats.zarr dataset."""

    zarr_path: Path | str = "Data/Processed/satellite/stats.zarr"

    def __post_init__(self) -> None:
        self.path = Path(self.zarr_path)
        if not self.path.exists():
            # Check relative to repo root if current working dir is thesis_implementation
            alt_path = Path("..") / self.zarr_path
            if alt_path.exists():
                self.path = alt_path.resolve()
            else:
                raise FileNotFoundError(f"stats.zarr not found at {self.path} or {alt_path}")
        self._group = zarr.open_group(str(self.path), mode="r")
        self._validate_schema()

    def _validate_schema(self) -> None:
        """Validate array dimensions and coordinates according to spec."""
        fields = self.fields
        dates = self.dates
        bands = self.bands

        if len(fields) != 490:
            raise ValueError(f"Expected 490 fields, got {len(fields)}")
        if len(dates) != 538:
            raise ValueError(f"Expected 538 dates, got {len(dates)}")
        if len(bands) != 7:
            raise ValueError(f"Expected 7 bands, got {len(bands)}")

        expected_start = pd.Timestamp("2013-03-30")
        expected_end = pd.Timestamp("2026-09-10")
        if dates[0] != expected_start or dates[-1] != expected_end:
            raise ValueError(
                f"Date range mismatch: expected {expected_start} to {expected_end}, "
                f"got {dates[0]} to {dates[-1]}"
            )

    @property
    def fields(self) -> np.ndarray:
        return np.asarray(self._group["field"][:], dtype=np.int64)

    @property
    def dates(self) -> pd.DatetimeIndex:
        time_days = np.asarray(self._group["time"][:], dtype=np.int64)
        return BASE_DATE + pd.to_timedelta(time_days, unit="D")

    @property
    def bands(self) -> list[str]:
        raw_bands = self._group["band"][:]
        return [b.decode("utf-8") if isinstance(b, bytes) else str(b) for b in raw_bands]

    @property
    def band_index(self) -> dict[str, int]:
        return {b: i for i, b in enumerate(self.bands)}

    @property
    def sensor(self) -> np.ndarray:
        raw_sensor = self._group["sensor"][:]
        return np.array([s.decode("utf-8") if isinstance(s, bytes) else str(s) for s in raw_sensor])

    @property
    def valid_frac(self) -> np.ndarray:
        return np.asarray(self._group["valid_frac"][:], dtype=np.float32)

    def get_stat(self, stat_name: str = "median") -> np.ndarray:
        """Read a 3D statistic array of shape (490, 538, 7)."""
        if stat_name not in self._group:
            raise KeyError(f"Statistic '{stat_name}' not found in stats.zarr")
        return np.asarray(self._group[stat_name][:], dtype=np.float32)

    def compute_indices(self, stat_name: str = "median") -> dict[str, np.ndarray]:
        """Compute primary vegetation and moisture indices.

        Returns:
            Dict mapping index names ('ndvi', 'ndmi', 'savi', 'lst') to (490, 538) arrays.
        """
        cube = self.get_stat(stat_name)
        b_idx = self.band_index

        red = cube[:, :, b_idx["red"]]
        nir = cube[:, :, b_idx["nir"]]
        swir1 = cube[:, :, b_idx["swir1"]]
        lst = cube[:, :, b_idx["lst"]]

        eps = 1e-8
        ndvi = (nir - red) / (nir + red + eps)
        ndmi = (nir - swir1) / (nir + swir1 + eps)
        savi = 1.5 * (nir - red) / (nir + red + 0.5 + eps)

        return {
            "ndvi": np.clip(ndvi, -1.0, 1.0),
            "ndmi": np.clip(ndmi, -1.0, 1.0),
            "savi": np.clip(savi, -1.5, 1.5),
            "lst": lst,
        }

    def get_filtered_stat(
        self,
        stat_name: str = "median",
        min_valid_frac: float = 0.50,
    ) -> np.ndarray:
        """Read statistic array masked with NaN where valid_frac < min_valid_frac."""
        arr = self.get_stat(stat_name).copy()
        mask = self.valid_frac < min_valid_frac  # (490, 538)
        arr[mask, :] = np.nan
        return arr

    def to_xarray(self, stat_names: tuple[str, ...] = ("median", "mean", "std")) -> xr.Dataset:
        """Convert stats.zarr to xarray Dataset with coordinates."""
        fields = self.fields
        dates = self.dates
        bands = self.bands

        data_vars = {}
        for s in stat_names:
            if s in self._group:
                data_vars[s] = (("field", "time", "band"), self.get_stat(s))

        data_vars["valid_frac"] = (("field", "time"), self.valid_frac)

        indices = self.compute_indices("median")
        for idx_name, idx_arr in indices.items():
            data_vars[idx_name] = (("field", "time"), idx_arr)

        return xr.Dataset(
            data_vars=data_vars,
            coords={
                "field": fields,
                "time": dates.to_numpy(),
                "band": np.array(bands, dtype=object),
                "sensor": (("time",), self.sensor),
            },
            attrs={
                "crs": "EPSG:32639",
                "pixel_size_m": 30.0,
                "source": "Data/Processed/satellite/stats.zarr",
            },
        )


def load_stats_zarr(path: str | Path = "Data/Processed/satellite/stats.zarr") -> StatsZarrReader:
    """Helper function to instantiate reader adapter."""
    return StatsZarrReader(path)
