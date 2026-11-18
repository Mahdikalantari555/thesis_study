"""Spectral indices computed from raw reflectance/temperature bands.

Computed AFTER ingest (per the design doc) so input ablations don't require
re-ingestion. NDVI uses SR_B4 (red) / SR_B5 (NIR). When LST is present we
also expose it as-is.
"""

from __future__ import annotations

import numpy as np
import xarray as xr


def _safe_div(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    out = np.full_like(a, np.nan, dtype=np.float32)
    mask = np.isfinite(a) & np.isfinite(b) & (b != 0)
    out[mask] = a[mask] / b[mask]
    return out


def ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    return _safe_div(nir - red, nir + red)


def evi(red: np.ndarray, nir: np.ndarray, blue: np.ndarray,
         g: float = 2.5, c1: float = 6.0, c2: float = 7.5, l: float = 1.0) -> np.ndarray:
    denom = nir + c1 * red - c2 * blue + l
    return _safe_div(g * (nir - red), denom)


def ndwi(nir: np.ndarray, swir: np.ndarray) -> np.ndarray:
    """NDWI using NIR and SWIR (SR_B5/SR_B6)."""
    return _safe_div(nir - swir, nir + swir)


def add_spectral_indices(ds: xr.Dataset, *, prefix: str = "") -> xr.Dataset:
    """Add NDVI / EVI / NDWI variables to an xarray fields-zarr dataset.

    Operates on the ``median`` variable (field, time, band) and adds new
    coordinate entries to the band dimension for computed indices.
    """
    med = ds["median"]
    band = list(ds.coords["band"].values)

    def get(name: str) -> np.ndarray:
        if name not in band:
            raise KeyError(f"Band {name} not in dataset; available: {band}")
        idx = band.index(name)
        return med.values[..., idx]

    new_vars = {}
    new_bands = list(band)

    if "SR_B4" in band and "SR_B5" in band and "NDVI" not in band:
        ndvi_arr = ndvi(get("SR_B4"), get("SR_B5"))
        new_vars["NDVI"] = ndvi_arr
        if "NDVI" not in new_bands:
            new_bands.append("NDVI")

    if {"SR_B2", "SR_B4", "SR_B5"}.issubset(band) and "EVI" not in band:
        evi_arr = evi(get("SR_B4"), get("SR_B5"), get("SR_B2"))
        new_vars["EVI"] = evi_arr
        if "EVI" not in new_bands:
            new_bands.append("EVI")

    if {"SR_B5", "SR_B6"}.issubset(band) and "NDWI" not in band:
        ndwi_arr = ndwi(get("SR_B5"), get("SR_B6"))
        new_vars["NDWI"] = ndwi_arr
        if "NDWI" not in new_bands:
            new_bands.append("NDWI")

    if not new_vars:
        return ds

    # Build a new (field, time, band) array including new bands
    n_fields, n_times, _ = med.shape
    n_new = len(new_vars)
    new_med = np.concatenate(
        [med.values, np.zeros((n_fields, n_times, n_new), dtype=np.float32)], axis=2
    )
    for i, (name, arr) in enumerate(new_vars.items()):
        new_med[..., len(band) + i] = arr

    new_ds = xr.Dataset(
        {"median": (("field", "time", "band"), new_med), **{k: v for k, v in ds.data_vars.items() if k != "median"}},
        coords={
            **{k: v for k, v in ds.coords.items() if k != "band"},
            "band": np.array(new_bands, dtype=object),
        },
        attrs=dict(ds.attrs),
    )
    # Copy over mean if present, filling new bands with NaN
    if "mean" in ds.data_vars:
        mean_arr = ds["mean"].values
        new_mean = np.concatenate(
            [mean_arr, np.full((n_fields, n_times, n_new), np.nan, dtype=np.float32)], axis=2
        )
        new_ds["mean"] = (("field", "time", "band"), new_mean)
    # Re-attach valid_frac
    if "valid_frac" in ds.data_vars:
        new_ds["valid_frac"] = ds["valid_frac"]
    return new_ds
