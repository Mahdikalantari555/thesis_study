"""Mask-aware cycle tensors, train-only robust normalization, DOY channels.

Design D3 / spec model-development-protocol ("Mask-aware inputs"):
- Model inputs carry a value tensor and a per-band observation mask. Missing
  values are zeroed *only together with* mask 0 and never contribute to the
  reconstruction loss or the score.
- The cycle tensors here are rebuilt from stats.zarr WITHOUT the interior-gap
  interpolation the original training NPZ applied (those bins had no
  observation; marking them observed would overstate provenance). The cycle
  set and admission rules mirror ``scripts/segment_and_export_cycles_490.py``
  exactly, and alignment with the original NPZ is asserted.
- Normalization is robust (median, MAD×1.4826) per band × phase bin, computed
  from train cycles only, and saved with the checkpoint sidecar.
- sin/cos DOY (R3) are added as auxiliary input channels for every candidate
  model; they are covariates (always present), never reconstruction targets.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from ssl_anomaly.io.stats_zarr import StatsZarrReader, load_stats_zarr

log = logging.getLogger("ssl_anomaly.monitor.inputs")

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = REPO_ROOT.parent
STATS_ZARR_PATH = WORKSPACE_ROOT / "Data/Processed/satellite/stats.zarr"
MASKED_NPZ_PATH = REPO_ROOT / "data/interim/growth_cycles_490_masked.npz"
CYCLES_PARQUET_PATH = REPO_ROOT / "data/processed/cycles_490.parquet"
CYCLES_NPZ_PATH = REPO_ROOT / "data/interim/growth_cycles_490.npz"

BIN_DAYS = 15
MAX_CYCLE_DAYS = 540
N_BINS = 36
MAD_K = 1.4826
SCALE_FLOOR = 1e-3

# Physical sanity ranges (raw units): reflectance bands 0..1, LST in KELVIN
# (stats.zarr stores LST_B10 in K; the platform exporter converts to °C at
# display time, export_platform_data.py `lst_c = lst - 273.15`). The robust
# per-bin normalization makes the unit shift irrelevant to the model, and
# temperature *differences* (MAD) are identical in K and °C, so MAD-scaled
# perturbations are unaffected.
PHYSICAL_RANGES: dict[str, tuple[float, float]] = {
    "blue": (-0.1, 1.6), "green": (-0.1, 1.6), "red": (-0.1, 1.6),
    "nir": (-0.1, 1.6), "swir1": (-0.1, 1.6), "swir2": (-0.1, 1.6),
    "lst": (180.0, 350.0),
}


# ---------------------------------------------------------------------------
# Masked cycle tensors rebuilt from stats.zarr (no interpolation)
# ---------------------------------------------------------------------------
def rebuild_masked_cycles(
    *,
    zarr_path: str | Path = STATS_ZARR_PATH,
    cycles_parquet_path: Path = CYCLES_PARQUET_PATH,
    verify_alignment: bool = True,
    reader: StatsZarrReader | None = None,
) -> dict:
    """Rebuild per-cycle tensors with TRUE per-band observation masks.

    Mirrors ``scripts/segment_and_export_cycles_490.py`` (segmentation params,
    admission rules, nanmedian binning) except that interior-gap interpolation
    is NOT applied: a bin/band that had no valid observation stays NaN with
    mask 0.

    Returns dict with:
        X: (N, 36, 8) float32 values, NaN where unobserved
        M: (N, 36, 8) bool observation mask
        field_ids, start_dates, end_dates, harvest_days: (N,) arrays
        cycle_keys: list of "<field>:<cycle_id>" (parquet cycle_id)
        band_names: list of 8 channel names (ndvi + 7 bands)
    """
    if reader is None:
        reader = load_stats_zarr(zarr_path)
    fields = reader.fields
    dates = reader.dates
    bands = reader.bands
    b_idx = reader.band_index

    times = dates.to_numpy().astype("datetime64[D]")
    epoch = times[0]
    time_days = (times - epoch).astype(int)

    indices = reader.compute_indices("median")
    ndvi = indices["ndvi"]
    valid_frac = reader.valid_frac
    median_cube = reader.get_stat("median")

    from ssl_anomaly.phenology.cycles import segment_cycles

    # Segment per field exactly like the NPZ exporter (which produced the
    # canonical cycles_490.parquet).
    seg_rows: list[dict] = []
    for fi, fid in enumerate(fields):
        field_cycles = segment_cycles(
            field_id=int(fid),
            times_days=time_days,
            ndvi=ndvi[fi],
            quality=valid_frac[fi],
            min_cycle_days=180,
            max_cycle_days=MAX_CYCLE_DAYS,
            min_prominence=0.15,
            plateau_frac=0.7,
            rise_frac=0.15,
        )
        for c in field_cycles:
            seg_rows.append(c.to_dict())
    seg_df = pd.DataFrame(seg_rows)

    # Align with the canonical parquet: same segmentation must reproduce it.
    canon = pd.read_parquet(cycles_parquet_path)
    for col in ("field", "t_start", "t_end", "censored", "start_harvest", "cycle_id"):
        if col not in canon.columns:
            raise ValueError(f"cycles parquet missing column {col}")
    if len(seg_df) != len(canon):
        raise ValueError(
            f"Segmentation produced {len(seg_df)} cycles but parquet has {len(canon)}; "
            "the canonical cycle file has drifted."
        )
    for col in ("field", "t_start", "t_end", "censored", "start_harvest", "cycle_id"):
        a = seg_df[col].to_numpy()
        b = canon[col].to_numpy()
        if not np.array_equal(a, b):
            raise ValueError(
                f"Segmentation drift in column {col} vs cycles_490.parquet. Refusing to build."
            )

    channel_names = ["ndvi"] + bands
    n_channels = len(channel_names)

    rows_X: list[np.ndarray] = []
    rows_M: list[np.ndarray] = []
    fids: list[int] = []
    starts: list[str] = []
    ends: list[str] = []
    harvests: list[int] = []
    keys: list[str] = []

    for row_i, (_, row) in enumerate(canon.iterrows()):
        if bool(row["censored"]):
            continue
        fid = int(row["field"])
        fi = int(np.where(fields == fid)[0][0])

        start_day = int(row["t_start"])
        end_day = int(row["t_end"])
        harvest_day = int(row.get("start_harvest", row["t_start"]))

        start_dt = times[0] + np.timedelta64(start_day, "D")
        end_dt = times[0] + np.timedelta64(end_day, "D")
        harvest_dt = times[0] + np.timedelta64(harvest_day, "D")
        if end_dt <= start_dt:
            continue

        obs_mask = (times >= start_dt) & (times < end_dt)
        if int(obs_mask.sum()) < 3:
            continue

        obs_times = times[obs_mask]
        dsh = (obs_times - harvest_dt).astype(int)
        valid_obs = (dsh >= 0) & (dsh < MAX_CYCLE_DAYS)
        if int(valid_obs.sum()) < 3:
            continue

        dsh_valid = dsh[valid_obs]
        ndvi_obs = ndvi[fi, obs_mask][valid_obs]
        cube_obs = median_cube[fi, obs_mask][valid_obs]

        x = np.full((N_BINS, n_channels), np.nan, dtype=np.float32)
        m = np.zeros((N_BINS, n_channels), dtype=bool)

        assigned = dsh_valid // BIN_DAYS
        for b in np.unique(assigned):
            if b >= N_BINS:
                continue
            b_mask = assigned == b
            ndvi_vals = ndvi_obs[b_mask]
            finite_ndvi = np.isfinite(ndvi_vals)
            if finite_ndvi.any():
                x[int(b), 0] = float(np.nanmedian(np.where(finite_ndvi, ndvi_vals, np.nan)))
                m[int(b), 0] = True
            for ci, bname in enumerate(bands):
                vals = cube_obs[b_mask, b_idx[bname]]
                finite = np.isfinite(vals)
                if finite.any():
                    x[int(b), ci + 1] = float(np.nanmedian(np.where(finite, vals, np.nan)))
                    m[int(b), ci + 1] = True

        # Admission mirrors the NPZ exporter: ≥3 bins with observed NDVI.
        if int(m[:, 0].sum()) < 3:
            continue

        rows_X.append(x)
        rows_M.append(m)
        fids.append(fid)
        starts.append(str(start_dt))
        ends.append(str(end_dt))
        harvests.append(harvest_day)
        keys.append(f"{fid}:{int(row['cycle_id'])}")

    X = np.stack(rows_X).astype(np.float32)
    M = np.stack(rows_M)

    # Assert alignment with the original NPZ (same cycles, same order).
    if verify_alignment and Path(CYCLES_NPZ_PATH).exists():
        ref = np.load(CYCLES_NPZ_PATH, allow_pickle=True)
        ref_fids = ref["field_ids"].astype(np.int64)
        ref_starts = [str(pd.Timestamp(str(d)).date()) for d in ref["start_dates"]]
        our_starts = [str(pd.Timestamp(s).date()) for s in starts]
        if len(ref_fids) != len(fids) or not np.array_equal(ref_fids, np.array(fids, dtype=np.int64)) \
                or ref_starts != our_starts:
            raise ValueError(
                "Rebuilt cycles do not align with growth_cycles_490.npz (count/field/start). "
                "The masked tensor builder must mirror the original exporter."
            )

    # Physical sanity check (§8 checklist: band/unit mistakes).
    for ci, name in enumerate(channel_names):
        lo, hi = PHYSICAL_RANGES.get(name, (np.nan, np.nan))
        vals = X[:, :, ci][M[:, :, ci]]
        if vals.size and (vals.min() < lo or vals.max() > hi):
            raise ValueError(
                f"Channel {name} outside physical range [{lo}, {hi}]: "
                f"min={vals.min():.3f}, max={vals.max():.3f}"
            )

    return {
        "X": X,
        "M": M,
        "field_ids": np.array(fids, dtype=np.int64),
        "start_dates": np.array(starts, dtype=object),
        "end_dates": np.array(ends, dtype=object),
        "harvest_days": np.array(harvests, dtype=np.int64),
        "cycle_keys": keys,
        "band_names": channel_names,
    }


def load_masked_cycles(
    *,
    cache_path: Path = MASKED_NPZ_PATH,
    force_rebuild: bool = False,
) -> dict:
    """Load (or build once and cache) the masked cycle tensors."""
    if not force_rebuild and Path(cache_path).exists():
        d = np.load(cache_path, allow_pickle=True)
        return {
            "X": d["X"],
            "M": d["M"],
            "field_ids": d["field_ids"],
            "start_dates": d["start_dates"],
            "end_dates": d["end_dates"],
            "harvest_days": d["harvest_days"],
            "cycle_keys": [str(k) for k in d["cycle_keys"]],
            "band_names": [str(b) for b in d["band_names"]],
            "source": str(cache_path),
        }
    out = rebuild_masked_cycles()
    Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cache_path,
        X=out["X"], M=out["M"], field_ids=out["field_ids"],
        start_dates=out["start_dates"], end_dates=out["end_dates"],
        harvest_days=out["harvest_days"],
        cycle_keys=np.array(out["cycle_keys"], dtype=object),
        band_names=np.array(out["band_names"], dtype=object),
    )
    out["source"] = str(cache_path)
    return out


# ---------------------------------------------------------------------------
# DOY auxiliary channels (R3)
# ---------------------------------------------------------------------------
def doy_channels(harvest_days: np.ndarray, *, bin_days: int = BIN_DAYS, n_bins: int = N_BINS) -> np.ndarray:
    """sin/cos of the day-of-year at each bin midpoint; shape (N, n_bins, 2).

    Bin b covers days [harvest + b·bin_days, harvest + (b+1)·bin_days); the
    midpoint carries the phase. Always "observed" (covariates, never targets).
    """
    n = len(harvest_days)
    doy_day = np.arange(n_bins) * bin_days + bin_days / 2.0  # (36,)
    offsets = (harvest_days.astype("int64")[:, None] + doy_day[None, :]).ravel()  # (N*36,)
    dates = pd.Timestamp("2013-03-30") + pd.to_timedelta(offsets, unit="D")  # 1-D DatetimeIndex
    doy = np.asarray(dates.dayofyear, dtype=np.float64).reshape(n, n_bins)
    ang = 2.0 * np.pi * doy / 365.25
    return np.stack([np.sin(ang), np.cos(ang)], axis=-1).astype(np.float32)


# ---------------------------------------------------------------------------
# Robust normalization (train-only, per band × phase bin)
# ---------------------------------------------------------------------------
def fit_robust_norm(
    X: np.ndarray, M: np.ndarray, *,
    scale_floor: float = SCALE_FLOOR,
) -> dict:
    """Fit median / MAD×1.4826 per (phase bin, band) on TRAIN cycles only.

    Bins or bands without enough observed train values fall back to the
    band-global median/MAD, then to 0 / scale_floor. Also stores the raw
    robust range (q95−q05 per band, observed train bins) used as the NRMSE
    denominator.
    """
    N, B, C = X.shape
    median = np.zeros((B, C), dtype=np.float64)
    scale = np.zeros((B, C), dtype=np.float64)
    n_used = np.zeros((B, C), dtype=np.int64)

    for c in range(C):
        for b in range(B):
            vals = X[:, b, c][M[:, b, c]].astype(np.float64)
            n_used[b, c] = vals.size
            if vals.size >= 8:
                median[b, c] = float(np.median(vals))
                mad = float(np.median(np.abs(vals - median[b, c])))
                scale[b, c] = mad * MAD_K
        # Bin-level fallback to band-global stats.
        vals_all = X[:, :, c][M[:, :, c]].astype(np.float64)
        weak = n_used[:, c] < 8
        if vals_all.size and weak.any():
            g_med = float(np.median(vals_all))
            g_scale = float(np.median(np.abs(vals_all - g_med))) * MAD_K
            median[weak, c] = g_med
            scale[weak, c] = g_scale if g_scale > 0 else scale_floor

    scale = np.where(scale > 0, scale, scale_floor)

    robust_range = np.ones(C, dtype=np.float64)
    for c in range(C):
        vals = X[:, :, c][M[:, :, c]].astype(np.float64)
        if vals.size >= 8:
            q05, q95 = np.percentile(vals, [5, 95])
            robust_range[c] = max(float(q95 - q05), scale_floor)

    return {
        "median": median,
        "scale": scale,
        "robust_range": robust_range,
        "n_used": n_used,
        "mad_k": MAD_K,
        "scale_floor": scale_floor,
    }


def apply_norm(norm: dict, X: np.ndarray, M: np.ndarray) -> np.ndarray:
    """Robust-z the values; unobserved entries become exactly 0 (mask stays)."""
    z = (X.astype(np.float64) - norm["median"][None, :, :]) / norm["scale"][None, :, :]
    z = np.where(M, z, 0.0)
    return z.astype(np.float32)


def save_norm(norm: dict, path: str | Path, meta: dict | None = None) -> None:
    """Save normalization stats (npz) + provenance sidecar (json)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        median=norm["median"], scale=norm["scale"],
        robust_range=norm["robust_range"], n_used=norm["n_used"],
    )
    meta = dict(meta or {})
    meta.update({
        "mad_k": norm["mad_k"],
        "scale_floor": norm["scale_floor"],
        "computed_from": "train split only (cycles listed in splits_locked.json train)",
    })
    Path(str(path) + ".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def load_norm(path: str | Path) -> dict:
    d = np.load(path)
    meta = json.loads(Path(str(path) + ".json").read_text(encoding="utf-8"))
    return {
        "median": d["median"], "scale": d["scale"],
        "robust_range": d["robust_range"], "n_used": d["n_used"],
        "mad_k": float(meta.get("mad_k", MAD_K)),
        "scale_floor": float(meta.get("scale_floor", SCALE_FLOOR)),
        "meta": meta,
    }
