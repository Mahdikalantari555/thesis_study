"""Field-aligned patch geometry and the per-pixel patch tensor store.

Change ``patch-data-pipeline``. The store ``Data/Processed/satellite/patches.zarr``
holds, for every admitted field-cycle of the locked splits, per-pixel per-bin
values for the 8 B1 channels on a field-aligned ``32×32`` grid.

Geometry contract (spec "Geometry is field-aligned"):
- a field's bounding box is cropped from the scene and **padded, never
  resampled**, to ``S×S`` (default 32);
- the stored static ``in_field`` mask excludes pixels of neighbouring fields,
  so different phenophases cannot leak into spatial context;
- invalid pixel-bins are stored as NaN with ``pixel_valid = 0`` — never
  zero-filled and never interpolated (AGENTS.md §8).

This module is deliberately free of rasterio/geopandas imports at module load:
geometry is pure array math so it is testable without the geo stack. The
export driver (``scripts/extract_patches.py``) does the raster work and calls
:func:`field_window`, :func:`crop_and_pad`, :func:`aggregate_bin` here.
"""

from __future__ import annotations

import hashlib
import json
import logging
import warnings
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

log = logging.getLogger("ssl_anomaly.io.patches")

# ---------------------------------------------------------------------------
# Frozen schema constants (spec "Patch tensor store")
# ---------------------------------------------------------------------------
PATCH_SIZE = 32                     # locked default; --patch-size exists but is not swept
DEFAULT_PATCH_SIZE = PATCH_SIZE
CHANNELS: tuple[str, ...] = (
    "ndvi", "blue", "green", "red", "nir", "swir1", "swir2", "lst",
)                                   # = B1's channel set (scripts/trial_common.py:17)
N_CHANNELS = len(CHANNELS)
N_BINS = 36
BIN_DAYS = 15
MAX_CYCLE_DAYS = 540
SENSOR_IDS: dict[str, int] = {"L8": 1, "L9": 2, "unknown": 0}
SENSOR_NAMES: dict[int, str] = {v: k for k, v in SENSOR_IDS.items()}

PATCH_STORE_NAME = "patches.zarr"
MANIFEST_NAME = ".manifest.jsonl"
NORM_STATS_NAME = "norm_stats.json"
PROVENANCE_NAME = "provenance.json"

QA_BITS_USED = (
    "fill(0)", "dilated_cloud(1)", "cirrus(2)", "cloud(3)", "cloud_shadow(4)", "snow(5)",
)


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class FieldWindow:
    """Where a field's patch lives inside the raster grid.

    ``row0/col0`` are the bbox origin (raster pixel indices, may be negative
    when the polygon touches the raster edge); ``height/width`` the bbox size;
    ``pad_top/pad_left`` the padding applied to centre the bbox in ``size×size``
    (bottom/right padding is implied by the size).
    """

    row0: int
    col0: int
    height: int
    width: int
    size: int = DEFAULT_PATCH_SIZE
    pad_top: int = 0
    pad_left: int = 0

    @property
    def pad_bottom(self) -> int:
        return self.size - self.height - self.pad_top

    @property
    def pad_right(self) -> int:
        return self.size - self.width - self.pad_left

    def as_dict(self) -> dict[str, int]:
        return {
            "row0": int(self.row0), "col0": int(self.col0),
            "height": int(self.height), "width": int(self.width),
            "size": int(self.size),
            "pad_top": int(self.pad_top), "pad_left": int(self.pad_left),
        }

    def to_bbox_origin(self) -> tuple[int, int]:
        """Stored ``bbox_origin`` = the patch's top-left corner in raster space."""
        return (int(self.row0 - self.pad_top), int(self.col0 - self.pad_left))


def field_window(
    polygon_mask: np.ndarray,
    *,
    size: int = DEFAULT_PATCH_SIZE,
    inner_buffer_px: int = 0,
) -> FieldWindow | None:
    """Derive the padded window for one field from its rasterised polygon.

    ``polygon_mask`` is a boolean array where True = this field's pixels.
    Returns ``None`` when the field has no pixel (nothing to extract).

    The bbox is centred inside ``size×size`` so that a field smaller than the
    patch sits in the middle — never resized (spec: "no resampling of pixel
    values occurs"). A field larger than ``size`` would not fit; that is a hard
    error rather than a silent crop, because 100 % of the 490 fields fit in
    theory (median 16.7 px, max 19.6 px) and a violation means the geometry
    assumptions changed.
    """
    mask = np.asarray(polygon_mask, dtype=bool)
    if mask.ndim != 2:
        raise ValueError(f"polygon_mask must be 2-D, got shape {mask.shape}")
    rows = np.flatnonzero(mask.any(axis=1))
    cols = np.flatnonzero(mask.any(axis=0))
    if rows.size == 0 or cols.size == 0:
        return None

    if inner_buffer_px:
        mask = _inner_buffer(mask, int(inner_buffer_px))
        if not mask.any():
            return None  # buffer consumed the whole field — recorded by the caller
        rows = np.flatnonzero(mask.any(axis=1))
        cols = np.flatnonzero(mask.any(axis=0))

    row0, row1 = int(rows[0]), int(rows[-1]) + 1
    col0, col1 = int(cols[0]), int(cols[-1]) + 1
    height, width = row1 - row0, col1 - col0
    if height > size or width > size:
        raise ValueError(
            f"field bounding box {height} x {width} px exceeds the {size} x {size} patch. "
            "The 32 px patch was sized from the measured field distribution (median 16.7, "
            "max 19.6 px); a larger field means either --patch-size must grow or the "
            "geometry memo is out of date — do not silently crop."
        )
    pad_top = (size - height) // 2
    pad_left = (size - width) // 2
    return FieldWindow(
        row0=row0, col0=col0, height=height, width=width,
        size=size, pad_top=pad_top, pad_left=pad_left,
    )


def _inner_buffer(mask: np.ndarray, px: int) -> np.ndarray:
    """Erode the polygon mask by ``px`` pixels (4-connected), no scipy needed."""
    out = mask.copy()
    for _ in range(int(px)):
        padded = np.pad(out, 1, constant_values=False)
        eroded = (
            out
            & padded[:-2, 1:-1] & padded[2:, 1:-1]
            & padded[1:-1, :-2] & padded[1:-1, 2:]
        )
        out = eroded
    return out


def crop_and_pad(
    array: np.ndarray,
    window: FieldWindow,
    *,
    fill: float = np.nan,
    dtype: np.dtype | str | None = None,
) -> np.ndarray:
    """Crop ``array`` to ``window`` and pad it into ``size×size`` (no resampling).

    ``array`` may be the full raster, or any array already aligned to the same
    grid. Pixels outside ``array`` (negative origins at the raster edge) are
    filled with ``fill`` — NaN by default, never a fabricated value.
    """
    arr = np.asarray(array)
    if arr.ndim != 2:
        raise ValueError(f"array must be 2-D, got shape {arr.shape}")
    out_dtype = np.dtype(dtype) if dtype is not None else arr.dtype
    out = np.full((window.size, window.size), fill, dtype=out_dtype)

    src_r0, src_c0 = window.row0, window.col0
    dst_r0, dst_c0 = window.pad_top, window.pad_left

    # Clip the bbox to the raster bounds on both sides.
    r_lo = max(0, -src_r0)
    c_lo = max(0, -src_c0)
    r_hi = min(window.height, arr.shape[0] - src_r0)
    c_hi = min(window.width, arr.shape[1] - src_c0)
    if r_hi <= r_lo or c_hi <= c_lo:
        return out  # window lies entirely outside the raster

    block = arr[
        src_r0 + r_lo : src_r0 + r_hi,
        src_c0 + c_lo : src_c0 + c_hi,
    ]
    out[
        dst_r0 + r_lo : dst_r0 + r_hi,
        dst_c0 + c_lo : dst_c0 + c_hi,
    ] = block.astype(out_dtype, copy=False)
    return out


def patch_in_field_mask(polygon_mask: np.ndarray, window: FieldWindow) -> np.ndarray:
    """The static ``in_field`` mask on the patch grid (uint8 0/1).

    Pixels outside the field polygon are 0 — including pixels of *neighbouring*
    fields that fall inside the same bounding box, which is what keeps
    different phenophases out of the spatial context.
    """
    m = crop_and_pad(polygon_mask, window, fill=False, dtype=bool)
    return m.astype(np.uint8)


# ---------------------------------------------------------------------------
# Per-pixel per-bin aggregation
# ---------------------------------------------------------------------------
@dataclass
class BinAggregate:
    """One (field, cycle, bin) slice of the store."""

    values: np.ndarray          # (C, S, S) float16/float32, NaN where invalid
    pixel_valid: np.ndarray     # (S, S) uint8
    n_obs: int                  # acquisitions contributing to this bin
    sensor_id: int              # majority sensor id in this bin


def aggregate_bin(
    scenes: Sequence[np.ndarray],
    valid_masks: Sequence[np.ndarray],
    *,
    in_field: np.ndarray | None = None,
    dtype: np.dtype | str = np.float16,
) -> BinAggregate:
    """Per-pixel median over the valid acquisitions inside one bin.

    Parameters
    ----------
    scenes
        One ``(C, S, S)`` float array per acquisition in the bin (already
        cropped/padded by the caller). NaN marks an invalid pixel value.
    valid_masks
        One boolean ``(S, S)`` array per acquisition — the QA mask.
    in_field
        Optional ``(S, S)`` 0/1 polygon mask. When given, pixels outside the
        field are forced invalid (they are never asserted as observed).

    Semantics (mirrors the field-level median convention in
    ``monitor/inputs.py``): a pixel-bin is valid iff at least one acquisition
    has QA-valid, finite values; the value is the median of those. No
    interpolation, no zero-fill. ``n_obs`` counts acquisitions with at least
    one valid in-field pixel.
    """
    if len(scenes) != len(valid_masks):
        raise ValueError(
            f"{len(scenes)} scenes but {len(valid_masks)} validity masks"
        )
    if not scenes:
        s = in_field.shape[0] if in_field is not None else 0
        return BinAggregate(
            values=np.full((N_CHANNELS, s, s), np.nan, dtype=dtype),
            pixel_valid=np.zeros((s, s), dtype=np.uint8),
            n_obs=0, sensor_id=SENSOR_IDS["unknown"],
        )

    first = np.asarray(scenes[0])
    if first.ndim != 3:
        raise ValueError(f"scene arrays must be (C, S, S), got {first.shape}")
    c, size, _ = first.shape
    stack = np.full((len(scenes), c, size, size), np.nan, dtype=np.float64)
    valid = np.zeros((len(scenes), size, size), dtype=bool)
    for i, (sc, vm) in enumerate(zip(scenes, valid_masks)):
        arr = np.asarray(sc, dtype=np.float64)
        if arr.shape != (c, size, size):
            raise ValueError(f"scene {i} has shape {arr.shape}, expected {(c, size, size)}")
        stack[i] = arr
        v = np.asarray(vm, dtype=bool)
        if v.shape != (size, size):
            raise ValueError(f"mask {i} has shape {v.shape}, expected {(size, size)}")
        valid[i] = v

    if in_field is not None:
        inside = np.asarray(in_field, dtype=bool)
        if inside.shape != (size, size):
            raise ValueError(f"in_field has shape {inside.shape}, expected {(size, size)}")
        valid &= inside[None, :, :]

    # A pixel is observed in an acquisition when it is QA-valid AND finite.
    observed = valid[:, None, :, :] & np.isfinite(stack)
    any_obs = observed.any(axis=0)                      # (C, S, S)
    with np.errstate(all="ignore"), warnings.catch_warnings():
        # All-NaN slices (whole pixels with no observation) are expected here and
        # stay NaN by design — silence the specific numpy warning, not all of them.
        warnings.filterwarnings("ignore", message="All-NaN slice encountered",
                                category=RuntimeWarning)
        values = np.nanmedian(np.where(observed, stack, np.nan), axis=0)
    values[~any_obs] = np.nan

    pixel_valid = observed.any(axis=0).any(axis=0)       # (S, S) any channel observed
    n_obs = int(observed.any(axis=(1, 2, 3)).sum())

    return BinAggregate(
        values=values.astype(dtype),
        pixel_valid=pixel_valid.astype(np.uint8),
        n_obs=n_obs,
        sensor_id=SENSOR_IDS["unknown"],
    )


def majority_sensor(sensor_ids: Iterable[int]) -> int:
    """Majority sensor id over the acquisitions of one bin (0 when empty)."""
    ids = [int(s) for s in sensor_ids]
    if not ids:
        return SENSOR_IDS["unknown"]
    vals, counts = np.unique(ids, return_counts=True)
    # Deterministic tie-break: the smaller id wins (L8 before L9).
    order = np.lexsort((vals, -counts))
    return int(vals[order[0]])


# ---------------------------------------------------------------------------
# Zarr store: schema, writer, reader
# ---------------------------------------------------------------------------
def store_schema(
    n_fields: int, max_cycles: int, size: int = DEFAULT_PATCH_SIZE,
) -> dict[str, tuple[tuple[int, ...], str]]:
    """Names, shapes and dtypes of every array in the store."""
    return {
        "values": ((n_fields, max_cycles, N_BINS, N_CHANNELS, size, size), "<f2"),
        "pixel_valid": ((n_fields, max_cycles, N_BINS, 1, size, size), "|u1"),
        "in_field": ((n_fields, 1, size, size), "|u1"),
        "bbox_origin": ((n_fields, 2), "<u2"),
        "n_obs": ((n_fields, max_cycles, N_BINS), "|u1"),
        "sensor_id": ((n_fields, max_cycles, N_BINS), "|u1"),
        "field_ids": ((n_fields,), "<i8"),
        "cycle_ids": ((n_fields, max_cycles), "<i8"),
        "cycle_start_day": ((n_fields, max_cycles), "<i8"),
        "cycle_end_day": ((n_fields, max_cycles), "<i8"),
        "cycle_valid": ((n_fields, max_cycles), "|u1"),
    }


def estimate_store_bytes(n_fields: int, n_cycles: int, size: int = DEFAULT_PATCH_SIZE) -> int:
    """Uncompressed size estimate (the ~1.0 GB figure quoted in the proposal)."""
    return int(
        n_cycles * N_BINS * N_CHANNELS * size * size * 2      # fp16 values
        + n_cycles * N_BINS * size * size                      # uint8 validity
        + n_fields * size * size                               # in_field
        + n_cycles * N_BINS * 2                                # n_obs + sensor
        + n_fields * 2 + n_cycles * 8 * 3                      # origins + cycle arrays
    )


def open_store(path: str | Path, *, mode: str = "r"):
    """Open (or create) a patches.zarr group. Imported lazily: zarr only here."""
    import zarr

    return zarr.open_group(str(path), mode=mode)


def create_store(
    path: str | Path,
    *,
    field_ids: Sequence[int],
    max_cycles: int,
    size: int = DEFAULT_PATCH_SIZE,
    attrs: dict[str, Any] | None = None,
):
    """Create the store with the frozen schema and chunking.

    Chunks keep per-(field, cycle) reads cheap: ``values`` is chunked one cycle
    at a time, so the Dataset can lazily read a single field-cycle.
    """
    import zarr

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    root = zarr.open_group(str(path), mode="w")
    schema = store_schema(len(field_ids), max_cycles, size)
    for name, (shape, dtype) in schema.items():
        if name == "values":
            chunks = (1, 1, N_BINS, N_CHANNELS, size, size)
        elif name == "pixel_valid":
            chunks = (1, 1, N_BINS, 1, size, size)
        elif name == "in_field":
            chunks = (1, 1, size, size)
        elif name in ("n_obs", "sensor_id"):
            chunks = (1, 1, N_BINS)          # per-cycle reads stay cheap
        elif name.startswith("cycle_"):
            chunks = (1, max_cycles)
        else:
            # 1-D arrays (field_ids): one chunk, matching the array's rank.
            chunks = tuple(int(s) for s in shape)
        opts = {
            "shape": tuple(int(s) for s in shape),
            "dtype": dtype,
            "chunks": chunks,
            "fill_value": (float("nan") if np.dtype(dtype).kind == "f" else 0),
        }
        # zarr 3 exposes create_array; zarr 2 only create_dataset.
        creator = getattr(root, "create_array", None)
        if creator is not None:
            creator(name, overwrite=True, **opts)
        else:  # pragma: no cover - zarr 2 path
            root.create_dataset(name, overwrite=True, **opts)
    root.attrs.update(attrs or {})
    root.attrs["schema"] = {k: {"shape": list(v[0]), "dtype": v[1]} for k, v in schema.items()}
    root.attrs["channel_order"] = list(CHANNELS)
    root.attrs["patch_size"] = int(size)
    return root


def validate_store(root, *, expected_fields: int | None = None) -> dict:
    """Validate the on-disk store against the frozen schema.

    Raises ``ValueError`` naming the first defect — a missing array, a wrong
    dtype, a wrong channel axis, or a field count that disagrees with the
    registry. Returns a summary dict for the provenance record.
    """
    missing = [k for k in store_schema(1, 1) if k not in root]
    if missing:
        raise ValueError(f"patch store is missing arrays: {missing}")

    values = root["values"]
    if len(values.shape) != 6:
        raise ValueError(f"values must be 6-D (F, C, 36, 8, S, S), got {values.shape}")
    n_fields, max_cycles, n_bins, n_ch, size, size2 = values.shape
    if n_bins != N_BINS:
        raise ValueError(f"values bin axis is {n_bins}, expected {N_BINS}")
    if n_ch != N_CHANNELS:
        raise ValueError(f"values channel axis is {n_ch}, expected {N_CHANNELS}")
    if size != size2:
        raise ValueError(f"patch is not square: {size} x {size2}")
    if expected_fields is not None and n_fields != expected_fields:
        raise ValueError(f"store holds {n_fields} fields, registry says {expected_fields}")

    if root.attrs.get("channel_order") != list(CHANNELS):
        raise ValueError(f"patch store channel_order must be {list(CHANNELS)}")
    for name, (shape, dtype) in store_schema(n_fields, max_cycles, size).items():
        if root[name].shape != shape or root[name].dtype != np.dtype(dtype):
            raise ValueError(f"{name} shape/dtype does not match the patch schema")

    return {
        "n_fields": int(n_fields),
        "max_cycles": int(max_cycles),
        "n_bins": int(n_bins),
        "n_channels": int(n_ch),
        "patch_size": int(size),
        "n_cycles_recorded": int(np.asarray(root["cycle_valid"][:]).sum()),
        "bytes_estimate": estimate_store_bytes(int(n_fields), int(max_cycles), int(size)),
    }


@dataclass(frozen=True)
class PatchCycle:
    field_id: int
    cycle_id: int
    row: int
    column: int
    start_day: int
    end_day: int

    @property
    def key(self) -> str:
        return f"{self.field_id}:{self.cycle_id}"


def patch_epoch(root) -> str:
    try:
        return date.fromisoformat(root.attrs["cycle_epoch"]).isoformat()
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("patch store lacks a valid cycle_epoch; re-extract to a new store") from exc


def patch_cycle_index(root) -> dict[str, PatchCycle]:
    """Index valid store slots by stable field/cycle identity, not column number."""
    fields = np.asarray(root["field_ids"][:], dtype=int)
    if np.any(fields <= 0) or len(set(fields)) != fields.size:
        raise ValueError("patch store field_ids must be positive and unique")
    ids, starts, ends = (
        np.asarray(root[name][:]) for name in ("cycle_ids", "cycle_start_day", "cycle_end_day")
    )
    index = {}
    for row, col in np.argwhere(root["cycle_valid"][:]):
        cycle = PatchCycle(int(fields[row]), int(ids[row, col]), int(row), int(col),
                           int(starts[row, col]), int(ends[row, col]))
        if cycle.key in index:
            raise ValueError(f"duplicate patch cycle: {cycle.key}")
        index[cycle.key] = cycle
    return index


def validate_locked_patch_store(root, splits_manifest: dict) -> str:
    """Check the schema and locked cycle provenance without opening value chunks."""
    validate_store(root)
    epoch = patch_epoch(root)
    expected_hash = splits_manifest.get("cycle_file_hashes", {}).get("cycles_parquet_sha256")
    if (
        not expected_hash
        or root.attrs.get("cycle_source_sha256") != expected_hash
        or root.attrs.get("splits_manifest_sha256") != splits_manifest["manifest_sha256"]
        or epoch != splits_manifest.get("base_date")
    ):
        raise ValueError("patch store cycle provenance disagrees with locked splits; re-extract to a new store")
    return epoch


def select_patch_train_cycles(
    root, *, splits_manifest: dict, holdout_manifest: dict,
    field_ids: Sequence[int] | None = None, max_cycles: int | None = None,
) -> tuple[list[PatchCycle], list[int]]:
    """Admit locked train cycles before loading any arrays of observed values."""
    from ssl_anomaly.monitor import holdout as H

    H.assert_frozen_holdout_matches_splits(holdout_manifest, splits_manifest)
    epoch = validate_locked_patch_store(root, splits_manifest)
    store_fields = [int(f) for f in root["field_ids"][:]]
    wanted = store_fields if field_ids is None else list(dict.fromkeys(int(f) for f in field_ids))
    missing = sorted(set(wanted) - set(store_fields))
    if missing:
        raise ValueError(f"requested fields are not in the store: {missing[:5]}")
    keep = H.train_only_mask(wanted, manifest=holdout_manifest)
    excluded = [f for f, admitted in zip(wanted, keep) if not admitted]
    eligible = {f for f, admitted in zip(wanted, keep) if admitted}
    if not eligible:
        raise ValueError("every requested field is a holdout field or unknown at the freeze")
    train_keys = set(splits_manifest["cycles"]["train"])
    admitted = [cycle for key, cycle in patch_cycle_index(root).items()
                if key in train_keys and cycle.field_id in eligible]
    if not admitted:
        raise ValueError("no admissible locked train cycles are present in the patch store")
    assert_patch_train_cycles(admitted, epoch=epoch, holdout_manifest=holdout_manifest)
    if max_cycles is not None:
        if max_cycles < 1:
            raise ValueError("max_cycles must be positive")
        per_field: dict[int, int] = {}
        selected = []
        for cycle in sorted(admitted, key=lambda c: (c.row, c.start_day, c.column)):
            count = per_field.get(cycle.field_id, 0)
            if count < max_cycles:
                selected.append(cycle)
                per_field[cycle.field_id] = count + 1
        admitted = selected
    assert_patch_count_bounds(root, admitted)
    return admitted, excluded


def assert_patch_train_cycles(cycles, *, epoch: str, holdout_manifest: dict) -> None:
    from ssl_anomaly.monitor import holdout as H

    origin = np.datetime64(epoch, "D")
    H.assert_train_only(
        [c.field_id for c in cycles], [c.key for c in cycles],
        [origin + np.timedelta64(c.start_day, "D") for c in cycles],
        cycle_end_dates=[origin + np.timedelta64(c.end_day, "D") for c in cycles],
        manifest=holdout_manifest, context="patch cycle admission",
    )


def _outside_cycle(cycle: PatchCycle) -> np.ndarray:
    return np.arange(N_BINS) * BIN_DAYS > cycle.end_day - cycle.start_day


def assert_patch_count_bounds(root, cycles: Sequence[PatchCycle]) -> None:
    """Preflight metadata for every admitted cycle before fitting or training."""
    from ssl_anomaly.monitor.holdout import HoldoutViolationError

    counts = root["n_obs"]
    for cycle in cycles:
        outside = _outside_cycle(cycle)
        if outside.any() and np.any(counts[cycle.row, cycle.column][outside]):
            raise HoldoutViolationError(f"patch cycle {cycle.key} has acquisition counts after its end")


def read_patch_observations(root, cycle: PatchCycle) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load one admitted cycle; enforce QA/polygon masks in every consumer."""
    from ssl_anomaly.monitor.holdout import HoldoutViolationError

    row, col = cycle.row, cycle.column
    values = np.asarray(root["values"][row, col])
    in_field = np.asarray(root["in_field"][row, 0], dtype=bool)
    finite = np.isfinite(values) & in_field[None, None]
    if finite[_outside_cycle(cycle)].any():
        raise HoldoutViolationError(f"patch cycle {cycle.key} has observations after its end")
    pixels = np.asarray(root["pixel_valid"][row, col], dtype=bool)
    sensors = np.asarray(root["sensor_id"][row, col], dtype=np.int64)
    if not np.isin(sensors, tuple(SENSOR_NAMES)).all():
        raise ValueError(f"patch cycle {cycle.key} has an invalid sensor id")
    return values, finite & pixels, sensors, in_field


# ---------------------------------------------------------------------------
# Frozen normalization artifact (spec "Leakage-free frozen normalization")
# ---------------------------------------------------------------------------
def fit_patch_norm(
    values: np.ndarray,
    sensor_ids: np.ndarray,
    *,
    channel_order: Sequence[str] = CHANNELS,
) -> dict:
    """Per-channel × per-sensor robust median/IQR from TRAIN data only.

    ``values`` is ``(N, C)`-flattened observations paired with a sensor id per
    observation. The CALLER is responsible for passing train-split fields ×
    train periods only — this function has no way to know the splits, so the
    leakage guard lives in :func:`build_patch_norm` and in the exporter's
    selection, and is proven by the tests.

    IQR is used (not MAD) because the store's fp16 values quantise; IQR is
    stable under that quantisation and matches the proposal's wording.
    """
    vals = np.asarray(values, dtype=np.float64)
    sids = np.asarray(sensor_ids, dtype=np.int64)
    if vals.ndim != 2 or vals.shape[1] != len(channel_order):
        raise ValueError(
            f"values must be (N, {len(channel_order)}), got {vals.shape}"
        )
    if len(sids) != len(vals):
        raise ValueError(f"{len(sids)} sensor ids for {len(vals)} rows")

    out: dict[str, dict[str, list[float]]] = {}
    for sid in sorted({int(s) for s in sids} | {SENSOR_IDS["unknown"]}):
        sel = sids == sid
        per_channel = {}
        for ci, name in enumerate(channel_order):
            v = vals[sel, ci]
            v = v[np.isfinite(v)]
            if v.size == 0:
                per_channel[name] = {"median": None, "iqr": None, "n": 0}
                continue
            q25, q75 = np.percentile(v, [25.0, 75.0])
            per_channel[name] = {
                "median": float(np.median(v)),
                "iqr": float(max(q75 - q25, 0.0)),
                "n": int(v.size),
            }
        out[SENSOR_NAMES.get(sid, str(sid))] = per_channel
    return out


def build_patch_norm(*, root, splits_manifest: dict, holdout_manifest: dict,
                     progress=None) -> dict:
    """Fit only after verifying the selected locked train cycles and date bounds."""
    cycles, _ = select_patch_train_cycles(
        root, splits_manifest=splits_manifest, holdout_manifest=holdout_manifest,
    )
    flat_vals, flat_sensors = [], []
    for cycle in progress(cycles) if progress is not None else cycles:
        values, obs, sensors, _ = read_patch_observations(root, cycle)
        for b, sensor in enumerate(sensors):
            pixels = obs[b].any(axis=0)
            if pixels.any():
                flat_vals.append(np.where(obs[b][:, pixels], values[b][:, pixels], np.nan).T)
                flat_sensors.append(np.full(pixels.sum(), sensor, dtype=np.uint8))
    if not flat_vals:
        raise ValueError("no finite in-field train pixel observations — refusing to fit norm stats")

    stats = fit_patch_norm(np.concatenate(flat_vals), np.concatenate(flat_sensors))
    fields = sorted({cycle.field_id for cycle in cycles})
    return {
        "stats": stats,
        "computed_from": "admissible locked train cycles only",
        "train_cycle_keys": sorted(cycle.key for cycle in cycles),
        "field_ids_used": fields,
        "splits_sha256": splits_manifest["manifest_sha256"],
        "holdout_sha256": holdout_manifest["manifest_sha256"],
        "channel_order": list(CHANNELS),
        "n_train_fields": len(fields),
        "n_train_cycles": len(cycles),
        "stat": "median/iqr (per channel, per sensor)",
    }


def validate_patch_norm_binding(root, norm: dict, splits_manifest: dict, holdout_manifest: dict) -> None:
    """Require a norm fitted on admissible locked cycles in the bound store."""
    if (norm.get("splits_sha256") != splits_manifest["manifest_sha256"]
            or norm.get("holdout_sha256") != holdout_manifest["manifest_sha256"]):
        raise ValueError("patch normalization artifact is not bound to these locked splits and holdout")
    norm_keys = norm.get("train_cycle_keys")
    store_keys = patch_cycle_index(root)
    if (not isinstance(norm_keys, list) or not norm_keys
            or not all(isinstance(k, str) for k in norm_keys)
            or len(set(norm_keys)) != len(norm_keys)
            or not set(norm_keys) <= (set(store_keys) & set(splits_manifest["cycles"]["train"]))):
        raise ValueError("patch normalization artifact includes cycles outside this store's locked train set")
    cycles = [store_keys[k] for k in norm_keys]
    assert_patch_train_cycles(cycles, epoch=patch_epoch(root), holdout_manifest=holdout_manifest)


def patch_norm_stats(norm: dict) -> dict:
    """Validate the envelope, allowing an unavailable individual channel scale."""
    if not isinstance(norm, dict):
        raise ValueError("invalid patch normalization artifact: expected a JSON object")
    stats, order = norm.get("stats"), norm.get("channel_order")
    if not isinstance(stats, dict) or not stats or not isinstance(order, (list, tuple)) or tuple(order) != CHANNELS:
        raise ValueError("invalid patch normalization artifact: expected stats and frozen channel_order")
    if not any(stats.values()):
        raise ValueError("invalid patch normalization artifact: no channel records")
    for sensor, channels in stats.items():
        if not isinstance(channels, dict) or sensor not in SENSOR_IDS:
            raise ValueError(f"invalid patch normalization sensor {sensor!r}")
        for channel, record in channels.items():
            if (channel not in CHANNELS or not isinstance(record, dict)
                    or not {"median", "iqr"} <= record.keys()):
                raise ValueError(f"invalid patch normalization channel {sensor}/{channel}")
            for key in ("median", "iqr"):
                x = record.get(key)
                if x is not None and (
                    type(x) not in (int, float) or not np.isfinite(x) or (key == "iqr" and x < 0)
                ):
                    raise ValueError(f"invalid patch normalization {sensor}/{channel}/{key}")
    return stats


def normalize_patch(values, obs, sensors, stats) -> tuple[np.ndarray, set[str]]:
    """Normalize observed model inputs consistently; never center missing values."""
    out = np.where(obs, values, 0.0).astype(np.float32)
    absent = set()
    for sid in np.unique(sensors):
        bins = np.flatnonzero(sensors == sid)
        channels = stats.get(SENSOR_NAMES.get(int(sid), "unknown"), {})
        for ci, ch in enumerate(CHANNELS):
            seen = obs[bins, ci]
            if not seen.any():
                continue
            record = channels.get(ch, {})
            median, iqr = record.get("median"), record.get("iqr")
            if median is None or iqr is None or iqr <= 0:
                absent.add(ch)
                continue
            out[bins, ci] = np.where(seen, (out[bins, ci] - median) / iqr, 0.0)
    return out, absent


def norm_stats_sha256(norm: dict) -> str:
    """Stable SHA-256 over the norm artifact (its ``sha256`` field excluded)."""
    payload = {k: v for k, v in norm.items() if k != "sha256"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def save_patch_norm(norm: dict, path: str | Path) -> Path:
    """Freeze the norm artifact with its own sha256 inside the JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    patch_norm_stats(norm)
    frozen = dict(norm)
    frozen["sha256"] = norm_stats_sha256(norm)
    with path.open("x", encoding="utf-8") as f:
        json.dump(frozen, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    return path


def load_patch_norm(path: str | Path, *, verify: bool = True) -> dict:
    """Load the frozen norm artifact, verifying its sha256 (fail-closed)."""
    path = Path(path)
    if not path.exists():
        raise RuntimeError(
            f"patch normalization artifact missing at {path}. Build it once with "
            "`python scripts/build_patch_norm.py --store <patches.zarr>` (locked train cycles only); "
            "training consumers refuse to start without it."
        )
    norm = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(norm, dict):
        raise ValueError(f"invalid patch normalization artifact at {path}: expected a JSON object")
    if verify:
        recorded = norm.get("sha256")
        if not recorded or norm_stats_sha256(norm) != recorded:
            raise RuntimeError(
                f"patch norm artifact at {path} failed its sha256 check — the frozen "
                "statistics were modified. Refusing to continue (leakage-free "
                "normalization requirement)."
            )
    patch_norm_stats(norm)
    return norm


# ---------------------------------------------------------------------------
# Provenance manifest
# ---------------------------------------------------------------------------
@dataclass
class Provenance:
    """Provenance record written beside the store (spec: provenance manifest)."""

    git_sha: str = "unknown"
    cycles_sha256: str | None = None
    splits_sha256: str | None = None
    holdout_manifest_sha256: str | None = None
    source_products: list[str] = field(default_factory=list)
    qa_bits: list[str] = field(default_factory=lambda: list(QA_BITS_USED))
    scale_factors: dict[str, float] = field(default_factory=dict)
    patch_size: int = DEFAULT_PATCH_SIZE
    channel_order: list[str] = field(default_factory=lambda: list(CHANNELS))
    n_fields: int = 0
    n_cycles: int = 0
    n_dates_done: int = 0
    output_sha256: str | None = None
    created: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = {
            "git_sha": self.git_sha,
            "cycles_sha256": self.cycles_sha256,
            "splits_sha256": self.splits_sha256,
            "holdout_manifest_sha256": self.holdout_manifest_sha256,
            "source_products": list(self.source_products),
            "qa_bits": list(self.qa_bits),
            "scale_factors": dict(self.scale_factors),
            "patch_size": int(self.patch_size),
            "channel_order": list(self.channel_order),
            "n_fields": int(self.n_fields),
            "n_cycles": int(self.n_cycles),
            "n_dates_done": int(self.n_dates_done),
            "output_sha256": self.output_sha256,
            "created": self.created,
        }
        d.update(self.extra)
        return d

    def validate(self) -> None:
        """Refuse to write an incomplete provenance record (AGENTS.md §2.4)."""
        missing = [
            name for name, val in (
                ("cycles_sha256", self.cycles_sha256),
                ("splits_sha256", self.splits_sha256),
                ("created", self.created),
            ) if not val
        ]
        if missing:
            raise ValueError(f"provenance record incomplete: missing {missing}")
        if self.n_fields <= 0:
            raise ValueError("provenance n_fields must be positive")


def output_sha256(root, *, sample: int = 512) -> str:
    """Cheap content hash of the store: shapes + a deterministic value sample."""
    h = hashlib.sha256()
    for name in sorted(store_schema(1, 1)):
        arr = root[name]
        h.update(name.encode())
        h.update(str(arr.shape).encode())
        h.update(str(arr.dtype).encode())
    vals = np.asarray(root["values"][:], dtype=np.float32)
    flat = vals.reshape(-1)
    finite_idx = np.flatnonzero(np.isfinite(flat))
    if finite_idx.size:
        step = max(1, finite_idx.size // sample)
        pick = finite_idx[::step][:sample]
        h.update(np.round(flat[pick], 4).astype(np.float32).tobytes())
    h.update(str(int(np.isfinite(vals).sum())).encode())
    return h.hexdigest()


__all__ = [
    "BIN_DAYS",
    "CHANNELS",
    "DEFAULT_PATCH_SIZE",
    "MANIFEST_NAME",
    "MAX_CYCLE_DAYS",
    "NORM_STATS_NAME",
    "N_BINS",
    "N_CHANNELS",
    "PATCH_SIZE",
    "PATCH_STORE_NAME",
    "PROVENANCE_NAME",
    "QA_BITS_USED",
    "SENSOR_IDS",
    "SENSOR_NAMES",
    "FieldWindow",
    "Provenance",
    "aggregate_bin",
    "assert_patch_count_bounds",
    "assert_patch_train_cycles",
    "build_patch_norm",
    "create_store",
    "crop_and_pad",
    "estimate_store_bytes",
    "field_window",
    "fit_patch_norm",
    "load_patch_norm",
    "majority_sensor",
    "norm_stats_sha256",
    "normalize_patch",
    "open_store",
    "output_sha256",
    "patch_cycle_index",
    "patch_epoch",
    "patch_in_field_mask",
    "patch_norm_stats",
    "read_patch_observations",
    "save_patch_norm",
    "select_patch_train_cycles",
    "store_schema",
    "validate_locked_patch_store",
    "validate_patch_norm_binding",
    "validate_store",
]
