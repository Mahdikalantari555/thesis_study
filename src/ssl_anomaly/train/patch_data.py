"""Dataset + covariate builder over ``patches.zarr`` (task 1.3).

A training sample is one **(field, cycle)** pair: the whole 36-bin patch tensor
of that field-cycle. Three invariants are structural, not conventions:

1. **Holdout isolation** (``training-holdout-invariant``): the store contains
   every field, including the frozen holdout farms, because extraction is
   global and one-shot. The Dataset therefore filters with the shared
   ``monitor/holdout.py`` helper and *fails closed* — a missing or unreadable
   manifest is an error, never "train on everything". The holdout filter is
   applied to the locked train cycle keys and inclusive calendar bounds
   before any observation is read.
2. **Normalization is frozen** (``patch-data-pipeline`` task 2.2): the
   per-channel × per-sensor median/IQR artifact is loaded read-only and its
   hash is checked; nothing is fitted here. ``build_patch_norm`` does the
   fitting, on train fields × train cycles only.
3. **NaN is absence** (patch store contract): unobserved pixel-bins are
   zero-filled for the model and carried by the mask. The loss mask is the
   per-channel observation mask ``obs`` — NOT the in-field mask — because an
   in-field pixel with no acquisition at that bin has no target.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ssl_anomaly.io import patches as P
from ssl_anomaly.monitor.holdout import HoldoutViolationError

# 8 covariates, fixed order (task 1.3): sin/cos DOY, cycle age, days since last
# valid, log1p n_obs, sensor one-hot L8/L9, field-level in-field fraction.
COVARIATES: tuple[str, ...] = (
    "doy_sin", "doy_cos", "cycle_age", "days_since_valid",
    "log1p_n_obs", "sensor_l8", "sensor_l9", "infield_frac",
)
N_COVARIATES = len(COVARIATES)
PATCH_INPUT_PROTOCOL = "patch_inputs_v2"
MAX_OBSERVATION_COUNT = np.iinfo(np.uint8).max


@dataclass(frozen=True)
class PatchSample:
    """One field-cycle in model-ready form."""

    field_id: int
    cycle_id: int
    x: np.ndarray        # (T, C, S, S) float32, zero where unobserved
    obs: np.ndarray      # (T, C, S, S) bool, per-channel observation
    pixel_valid: np.ndarray  # (T, S, S) bool, in-field ∧ any channel observed
    covariates: np.ndarray   # (T, COVARIATES) float32
    start_day: int = 0


def build_covariates(
    cycle_start_day: np.ndarray,   # (T,) days since the cycle start (bin grid)
    n_obs: np.ndarray,             # (T,) acquisitions with ≥1 finite in-field pixel
    sensor_id: np.ndarray,         # (T,) 0/1/2
    in_field_frac: float,          # fraction of the patch inside the field
    *,
    bin_days: int = P.BIN_DAYS,
    n_bins: int = P.N_BINS,
    epoch: str = "2013-03-30",
) -> np.ndarray:
    """The 8-covariate matrix, ``(T, N_COVARIATES)`` float32.

    ``doy_sin``/``doy_cos`` use the same absolute-date convention as
    ``monitor.inputs.doy_channels`` (2013-03-30 epoch), so patch and zonal
    arms agree on what a season is. ``cycle_age`` is the bin index (a cycle
    always starts at the field's harvest date, so age = bins since start).
    ``days_since_valid`` is the causal gap: the number of bins since the last
    bin with ≥1 valid pixel (0 for the current bin when it is observed;
    carried forward otherwise, capped at ``n_bins``).
    """
    start = np.asarray(cycle_start_day, dtype=np.int64).ravel()
    if start.size == 1:
        start = np.full(n_bins, int(start[0]), dtype=np.int64)
    if start.size != n_bins:
        raise ValueError(f"cycle_start_day must be scalar or ({n_bins},), got {start.shape}")
    no = np.asarray(n_obs, dtype=np.float64).ravel()
    sid = np.asarray(sensor_id, dtype=np.int64).ravel()
    if no.size != n_bins or sid.size != n_bins:
        raise ValueError(f"n_obs/sensor_id must be ({n_bins},)")

    # Absolute DOY at each bin midpoint, same epoch as monitor.inputs.
    mid = start + np.arange(n_bins) * bin_days + bin_days / 2.0
    # Same convention as monitor.inputs.doy_channels: the absolute calendar
    # day from the shared epoch, so both arms agree on where the season is.
    origin = pd.Timestamp(epoch)
    doy = np.array(
        [(origin + pd.Timedelta(days=int(d))).day_of_year for d in mid],
        dtype=np.float64,
    )
    ang = 2.0 * np.pi * doy / 365.25

    age = np.arange(n_bins, dtype=np.float64)
    since = np.full(n_bins, float(n_bins))
    last = -1
    for b in range(n_bins):
        if no[b] > 0:
            last = b
        since[b] = float(b - last) if last >= 0 else float(n_bins)

    out = np.zeros((n_bins, N_COVARIATES), dtype=np.float32)
    out[:, 0] = np.sin(ang)
    out[:, 1] = np.cos(ang)
    out[:, 2] = age / max(1, n_bins - 1)
    out[:, 3] = since / max(1, n_bins)
    if not np.isfinite(no).all() or np.any((no < 0) | (no > MAX_OBSERVATION_COUNT)):
        raise ValueError("n_obs must contain valid uint8 acquisition counts")
    out[:, 4] = np.log1p(no) / np.log1p(MAX_OBSERVATION_COUNT)
    out[:, 5] = (sid == P.SENSOR_IDS["L8"]).astype(np.float32)
    out[:, 6] = (sid == P.SENSOR_IDS["L9"]).astype(np.float32)
    out[:, 7] = float(in_field_frac)
    return out


def read_cycle_inputs(root, cycle: P.PatchCycle, *, epoch: str) -> dict:
    """Read one cycle with a polygon mask and the shared causal covariates."""
    values, obs, sensors, in_field = P.read_patch_observations(root, cycle)
    n_obs = np.asarray(root["n_obs"][cycle.row, cycle.column])
    cov = build_covariates(np.array([cycle.start_day]), n_obs, sensors,
                           float(in_field.mean()), epoch=epoch)
    return {"raw": values, "obs": obs, "sensor_id": sensors, "in_field": in_field,
            "covariates": cov}


class PatchCycleDataset:
    """Lazy training view restricted to admissible locked train cycles."""

    def __init__(
        self,
        root,
        field_ids: np.ndarray | list[int],
        *,
        splits_manifest: dict,
        holdout_manifest: dict,
        norm: dict,
        max_cycles: int | None = None,
    ) -> None:
        if holdout_manifest is None:
            raise ValueError("holdout_manifest is required (training-holdout-invariant)")
        self.cycles, self.excluded_by_holdout = P.select_patch_train_cycles(
            root, field_ids=field_ids, max_cycles=max_cycles,
            splits_manifest=splits_manifest, holdout_manifest=holdout_manifest,
        )
        self.norm = norm
        self._stats = P.patch_norm_stats(norm)
        P.validate_patch_norm_binding(root, norm, splits_manifest, holdout_manifest)
        self.epoch = P.patch_epoch(root)
        self.root = root
        self.fields = sorted({c.field_id for c in self.cycles})
        self.unnormalized_channels: set[str] = set()

    def __len__(self) -> int:
        return len(self.cycles)

    def sample(
        self, i: int, *, transform: Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray] | None = None,
    ) -> PatchSample:
        cycle = self.cycles[i]
        row, col = cycle.row, cycle.column
        # Only a read-only store is supported. Still fail fast if its identity
        # or dates were replaced between admission and this value read.
        if (
            not self.root["cycle_valid"][row, col]
            or int(self.root["field_ids"][row]) != cycle.field_id
            or int(self.root["cycle_ids"][row, col]) != cycle.cycle_id
            or int(self.root["cycle_start_day"][row, col]) != cycle.start_day
            or int(self.root["cycle_end_day"][row, col]) != cycle.end_day
            or P.patch_epoch(self.root) != self.epoch
        ):
            raise HoldoutViolationError(f"patch cycle metadata changed after admission: {cycle.key}")
        data = read_cycle_inputs(self.root, cycle, epoch=self.epoch)
        raw, obs = data["raw"].astype(np.float32), data["obs"]
        if transform is not None:
            raw = transform(raw, obs, data["in_field"])
        x, missing = P.normalize_patch(raw, obs, data["sensor_id"], self._stats)
        self.unnormalized_channels.update(missing)
        return PatchSample(
            field_id=cycle.field_id, cycle_id=cycle.cycle_id, x=x, obs=obs,
            pixel_valid=obs.any(axis=1), covariates=data["covariates"], start_day=cycle.start_day,
        )


def collate(samples: list[PatchSample]) -> dict[str, np.ndarray]:
    """Stack samples into batch arrays for the model/loss."""
    return {
        "x": np.stack([s.x for s in samples]).astype(np.float32),
        "obs": np.stack([s.obs for s in samples]).astype(bool),
        "pixel_valid": np.stack([s.pixel_valid for s in samples]).astype(bool),
        "covariates": np.stack([s.covariates for s in samples]).astype(np.float32),
        "field_ids": np.array([s.field_id for s in samples], dtype=np.int64),
        "cycle_ids": np.array([s.cycle_id for s in samples], dtype=np.int64),
    }


def estimate_epoch_seconds(
    n_samples: int, *, seconds_per_sample: float, batch_size: int = 8,
) -> dict:
    """Runtime estimate helper shared by ``--estimate-runtime`` (task 1.4)."""
    n_batches = int(np.ceil(max(1, n_samples) / max(1, batch_size)))
    per_epoch = n_batches * float(seconds_per_sample)
    return {
        "n_samples": int(n_samples),
        "batch_size": int(batch_size),
        "n_batches": n_batches,
        "seconds_per_sample": float(seconds_per_sample),
        "seconds_per_epoch": per_epoch,
    }


__all__ = [
    "COVARIATES",
    "N_COVARIATES",
    "PATCH_INPUT_PROTOCOL",
    "PatchCycleDataset",
    "PatchSample",
    "build_covariates",
    "collate",
    "estimate_epoch_seconds",
    "read_cycle_inputs",
]
