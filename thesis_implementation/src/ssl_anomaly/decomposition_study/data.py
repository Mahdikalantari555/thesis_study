"""Read the QA-filtered zonal archive without opening held-out values."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd
import zarr

from ssl_anomaly.io.stats_zarr import BASE_DATE
from ssl_anomaly.monitor.holdout import (
    assert_frozen_holdout_matches_splits,
    assert_train_only,
    load_holdout_manifest,
    train_only_mask,
)
from ssl_anomaly.monitor.splits import SPLITS_LOCKED_PATH, load_splits_locked

BANDS = ("blue", "green", "red", "nir", "swir1", "swir2")
INDICES = ("ndvi", "evi", "ndmi")
BRANCHES = ("bands", "indices")
NIR = BANDS.index("nir")
ORIGIN = np.datetime64(BASE_DATE.date(), "D")


@dataclass(frozen=True)
class Panel:
    fields: np.ndarray
    dates: np.ndarray  # day resolution; original acquisition dates
    optical: np.ndarray  # (field, acquisition, band); absent is NaN
    quality: np.ndarray  # original field/acquisition valid pixel fraction
    provenance: dict

    @property
    def days(self) -> np.ndarray:
        return (self.dates - ORIGIN).astype(int)

    def branch(self, name: str) -> np.ndarray:
        if name == "bands":
            return self.optical
        if name != "indices":
            raise ValueError(f"Unknown branch {name!r}")
        blue, _, red, nir, swir1, _ = self.optical.transpose(2, 0, 1)

        def ratio(numerator, denominator, limit=None):
            result = np.divide(
                numerator,
                denominator,
                out=np.full_like(numerator, np.nan),
                where=np.isfinite(denominator) & (denominator > 1e-6),
            )
            if limit is not None:
                result[np.abs(result) > limit] = np.nan  # not silently clipped
            return result

        return np.stack(
            (
                ratio(nir - red, nir + red, 1),
                ratio(2.5 * (nir - red), nir + 6 * red - 7.5 * blue + 1),
                ratio(nir - swir1, nir + swir1, 1),
            ),
            axis=-1,
        )

    def with_optical(self, values: np.ndarray) -> Panel:
        return replace(self, optical=values)


@dataclass(frozen=True)
class Split:
    train_end: int  # exclusive array indices
    cal_end: int
    n_dates: int

    @property
    def blocks(self) -> tuple[slice, slice, slice]:
        return (
            slice(0, self.train_end),
            slice(self.train_end, self.cal_end),
            slice(self.cal_end, self.n_dates),
        )

    def describe(self, dates: np.ndarray) -> dict:
        return {
            name: {
                "first": str(dates[s.start]),
                "last": str(dates[s.stop - 1]),
                "n_dates": s.stop - s.start,
            }
            for name, s in zip(("train", "calibration", "evaluation"), self.blocks)
        }


def split_panel(panel: Panel, train_before: str, evaluate_from: str) -> Split:
    cuts = np.array([train_before, evaluate_from], dtype="datetime64[D]")
    if np.isnat(cuts).any() or cuts[0] >= cuts[1]:
        raise ValueError("Expected train-before < evaluate-from (ISO dates)")
    train, cal = map(int, np.searchsorted(panel.dates, cuts))
    split = Split(train, cal, len(panel.dates))
    for name, block in zip(("training", "calibration", "evaluation"), split.blocks):
        if block.stop - block.start < 5 or not np.isfinite(panel.optical[:, block]).any():
            raise ValueError(f"Insufficient admissible {name} observations after frozen holdout/QC")
    return split


def _fields_and_dates(group) -> tuple[np.ndarray, np.ndarray]:
    fields, times = np.asarray(group["field"][:]), np.asarray(group["time"][:])
    for name, arr in (("field", fields), ("time", times)):
        if (
            arr.ndim != 1
            or arr.size == 0
            or arr.dtype.kind not in "iu"
            or len(np.unique(arr)) != len(arr)
        ):
            raise ValueError(f"Invalid zonal {name} coordinate (expected unique integers)")
    if (fields <= 0).any() or (times < 0).any() or (np.diff(times.astype(int)) <= 0).any():
        raise ValueError("Invalid field identifiers or non-monotonic Landsat dates")
    return fields.astype(int), ORIGIN + times.astype("timedelta64[D]")


def read_zonal(
    path: Path,
    manifest_path: Path,
    min_valid_frac: float,
    *,
    splits_path: Path = SPLITS_LOCKED_PATH,
) -> Panel:
    """Read only eligible field/date slices. Do not train on a manifest inferred here."""
    if not 0 < min_valid_frac <= 1:
        raise ValueError("min_valid_frac must be in (0, 1]")
    if not path.is_dir():
        raise FileNotFoundError(f"Canonical polygon zonal stats.zarr not found at {path}")
    manifest = load_holdout_manifest(path=manifest_path)
    if (
        not manifest.get("known_farm_ids")
        or not manifest.get("holdout_farms")
        or not manifest.get("holdout_date_start")
    ):
        raise ValueError("Frozen holdout manifest lacks required admission constraints")
    # Only the split manifest is needed for zonal membership, not its cycle tensors.
    splits = load_splits_locked(path=splits_path, verify_cycle_files=False)
    assert_frozen_holdout_matches_splits(manifest, splits)
    cutoff = np.datetime64(manifest["holdout_date_start"], "D")
    archive_end = np.datetime64(manifest.get("archive_end_date") or "NaT", "D")
    if np.isnat(cutoff):
        raise ValueError("Frozen holdout cutoff is not a date")
    group = zarr.open_group(str(path), mode="r")
    fields, dates = _fields_and_dates(group)
    names = [b.decode() if isinstance(b, bytes) else str(b) for b in group["band"][:]]
    if len(set(names)) != len(names) or not set(BANDS).issubset(names):
        raise ValueError(f"Zonal band coordinate must contain each of {BANDS} exactly once")
    if group["median"].shape != (len(fields), len(dates), len(names)):
        raise ValueError("Zonal median shape does not match coordinates")
    if group["valid_frac"].shape != (len(fields), len(dates)):
        raise ValueError("Invalid zonal valid_frac shape")
    fi = np.flatnonzero(train_only_mask(fields, manifest=manifest))
    date_ok = (dates < cutoff) & (dates != np.datetime64("2022-08-07"))
    if not np.isnat(archive_end):
        date_ok &= dates <= archive_end
    ti = np.flatnonzero(date_ok)
    if fi.size == 0 or ti.size == 0:
        raise ValueError("No admissible zonal fields/dates under the frozen holdout manifest")
    assert_train_only(fields[fi], manifest=manifest, context="decomposition study fields")
    assert_train_only(
        np.repeat(fields[fi[0]], len(ti)),
        cycle_start_dates=pd.to_datetime(dates[ti]),
        manifest=manifest,
        context="decomposition study dates",
    )
    quality = np.asarray(group["valid_frac"].oindex[fi, ti], dtype=np.float32)
    raw = np.asarray(
        group["median"].oindex[fi, ti, [names.index(b) for b in BANDS]], dtype=np.float32
    )
    quality_ok = np.isfinite(quality) & (quality >= min_valid_frac) & (quality <= 1)
    plausible = np.isfinite(raw) & (raw >= -0.1) & (raw <= 1.6)
    raw = np.where(quality_ok[..., None] & plausible, raw, np.nan).astype(np.float32)
    return Panel(
        fields[fi],
        dates[ti],
        raw,
        quality,
        {
            "data_source": "processed_polygon_zonal_stats",
            "source_path": str(path.resolve()),
            "archive_fields": len(fields),
            "archive_dates": len(dates),
            "holdout_manifest_sha256": manifest["manifest_sha256"],
            "splits_manifest_sha256": splits["manifest_sha256"],
            "holdout_cutoff": str(cutoff),
            "excluded_fields": len(fields) - len(fi),
            "excluded_dates": len(dates) - len(ti),
            "min_valid_frac": min_valid_frac,
            "rejected_values_on_qc_passed_dates": int((quality_ok[..., None] & ~plausible).sum()),
            "index_provenance": "ratios of polygon optical band medians, not pixel-index medians",
        },
    )


def smoke_panel() -> Panel:
    """Only for explicit smoke tests; never an alternative input for real runs."""
    rng = np.random.default_rng(2026)
    days = np.arange(0, 6 * 366, 13)
    days[1:] += rng.integers(-3, 4, size=len(days) - 1)
    season = np.sin(days[None, :] * 2 * np.pi / 365.2425 + np.arange(4)[:, None] * 0.45)
    signal = np.stack(
        [
            0.10 - 0.02 * season,
            0.14 - 0.03 * season,
            0.16 - 0.04 * season,
            0.36 + 0.12 * season,
            0.22 - 0.04 * season,
            0.17 - 0.03 * season,
        ],
        axis=-1,
    )
    raw = signal + days[None, :, None] / 160_000 + rng.normal(0, 0.009, size=signal.shape)
    quality = np.where(rng.random(size=raw.shape[:2]) < 0.07, 0.2, 0.92)
    raw[quality < 0.5] = np.nan
    return Panel(
        np.arange(1, 5),
        ORIGIN + days.astype("timedelta64[D]"),
        raw.astype(np.float32),
        quality.astype(np.float32),
        {"data_source": "simulated_smoke", "fixture_seed": 2026},
    )
