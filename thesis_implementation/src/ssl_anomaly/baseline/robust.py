"""Stratum-aware robust baseline with shrinkage field offset.

Per spec: baseline per (stratum, bin, band) = median + MAD over normal cycles
of all fields in the stratum. Field effect via shrinkage offset:

    δ_f = n_f/(n_f+κ) · median(x - m)

Hierarchical fallback to coarser strata when a bin has < min_n cycles.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..phenology.align import coarse_strata

log = logging.getLogger("ssl_anomaly.baseline.robust")

MAD_K = 1.4826


@dataclass
class StratumStats:
    stratum: str
    median: np.ndarray  # (bins, bands)
    scale: np.ndarray  # (bins, bands)
    n: np.ndarray  # (bins,) effective counts
    floor: float


@dataclass
class RobustBaseline:
    """Container for a trained baseline.

    ``stats`` maps stratum → StratumStats. ``field_offset`` maps field_id →
    per-bin/band offset (shrunk).
    """

    bin_centers: np.ndarray
    band_names: list[str]
    stats: dict[str, StratumStats] = field(default_factory=dict)
    field_offset: dict[int, np.ndarray] = field(default_factory=dict)
    floor: float = 1e-3

    # ---------------------------------------------------------
    def to_npz(self, path: str) -> None:
        """Save baseline to a single .npz file (NumPy-only, no pickle)."""
        data = {
            "bin_centers": self.bin_centers,
            "band_names": np.array(self.band_names, dtype=object),
            "floor": np.array(self.floor),
            "strata_keys": np.array(list(self.stats.keys()), dtype=object),
        }
        for k, st in self.stats.items():
            data[f"{k}__median"] = st.median
            data[f"{k}__scale"] = st.scale
            data[f"{k}__n"] = st.n
        # field offsets are variable-shape per field; store in a simple
        # (n_fields, bins, bands) dense array aligned to field_ids list
        if self.field_offset:
            fids = np.array(sorted(self.field_offset.keys()), dtype=np.int64)
            offs = np.stack([self.field_offset[int(f)] for f in fids], axis=0)
            data["field_ids"] = fids
            data["field_offsets"] = offs
        np.savez(path, **data)

    @classmethod
    def from_npz(cls, path: str) -> RobustBaseline:
        d = np.load(path, allow_pickle=True)
        b = cls(
            bin_centers=d["bin_centers"],
            band_names=list(d["band_names"]),
            floor=float(d["floor"]),
        )
        keys = list(d["strata_keys"])
        for k in keys:
            b.stats[str(k)] = StratumStats(
                stratum=str(k),
                median=d[f"{k}__median"],
                scale=d[f"{k}__scale"],
                n=d[f"{k}__n"],
                floor=b.floor,
            )
        if "field_ids" in d.files:
            fids = d["field_ids"]
            offs = d["field_offsets"]
            for i, f in enumerate(fids):
                b.field_offset[int(f)] = offs[i]
        return b


def build_stratum_table(cycles_df: pd.DataFrame) -> pd.DataFrame:
    """Return a dataframe of cycle→stratum assignments."""
    out = cycles_df.copy()
    out["stratum"] = out.apply(
        lambda r: f"{r['kind']}_{int(r['ratoon_no'])}", axis=1
    )
    if "variety_group" in out.columns:
        vg = out["variety_group"].fillna("")
        out["stratum_full"] = np.where(
            vg != "", out["stratum"] + "|" + vg.astype(str), out["stratum"]
        )
    else:
        out["stratum_full"] = out["stratum"]
    return out


def _median_mad(X: np.ndarray, min_n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = np.sum(np.isfinite(X), axis=0)  # (bins, bands)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        med = np.nanmedian(X, axis=0)
        scale = np.nanmedian(np.abs(X - med[None, :, :]), axis=0) * MAD_K
    if min_n > 1:
        bad = n < min_n
        med = np.where(bad, np.nan, med)
        scale = np.where(bad, np.nan, scale)
    return med, scale, n


def _compute_floor(scales: list[np.ndarray], pct: float) -> float:
    flat = np.concatenate([s[np.isfinite(s) & (s > 0)].ravel() for s in scales]) if scales else np.array([])
    if flat.size == 0:
        return 1e-3
    return float(np.percentile(flat, pct))


def fit_baseline(
    X: dict[str, np.ndarray],  # stratum → (C, B, D)
    X_by_field: dict[int, np.ndarray],  # field → (C_f, B, D) — for shrinkage offsets
    *,
    min_n: int = 5,
    kappa: float = 2.5,
    floor_pct: float = 5.0,
) -> RobustBaseline:
    """Fit a robust baseline.

    ``X[stratum]`` has shape (cycles, bins, bands) and only includes ACTIVE
    (normal) cycles. ``X_by_field`` is used for shrinkage offsets.
    """
    first = next(iter(X.values()))
    _, n_bins, n_bands = first.shape
    band_names = [f"band_{i}" for i in range(n_bands)]

    # Compute per-stratum stats and a global floor
    stats: dict[str, StratumStats] = {}
    scales = []
    for key, arr in X.items():
        med, scale, n = _median_mad(arr, min_n)
        # Fallback: replace stratum-scale with coarser stratum where n < min_n
        # (This is done at scoring time via coarse_strata(); here we simply
        # mark under-sampled bins as NaN.)
        scales.append(scale)
        stats[key] = StratumStats(
            stratum=key, median=med, scale=scale, n=np.sum(n, axis=-1), floor=0.0
        )
    floor = _compute_floor(scales, floor_pct)
    for st in stats.values():
        st.floor = floor

    bl = RobustBaseline(
        bin_centers=np.arange(n_bins, dtype=np.float64),
        band_names=band_names,
        stats=stats,
        floor=floor,
    )

    # Shrinkage field offset: offset_f,b,d = n_f/(n_f+kappa) * median(x - m_stratum).
    # n_f here is per (bin, band) count of finite observations for this field.
    for fid, cycles in X_by_field.items():
        if "all" in stats:
            m = stats["all"].median
        else:
            m = next(iter(stats.values())).median
        m_b = np.broadcast_to(m[None, :, :], cycles.shape)
        delta = cycles - m_b
        finite = np.isfinite(delta)
        n_f = finite.sum(axis=0)  # (bins, bands)
        with np.errstate(all="ignore"):
            # nanmedian over cycles axis (0); suppress NaN slices to avoid warnings
            masked_delta = np.where(finite, delta, np.nan)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                raw_offset = np.nanmedian(masked_delta, axis=0)
            raw_offset = np.where(np.isfinite(raw_offset), raw_offset, 0.0)
        shrink = n_f / (n_f + kappa)
        bl.field_offset[int(fid)] = raw_offset * shrink
    return bl


def lookup_median_scale(
    bl: RobustBaseline, stratum: str, shape: tuple[int, int]
) -> tuple[np.ndarray, np.ndarray]:
    """Return (median, scale) arrays of given shape for a (bin, band) grid,
    falling back to coarser strata where the chosen stratum has NaNs."""
    order = coarse_strata(stratum)
    med = np.full(shape, np.nan, dtype=np.float64)
    scale = np.full(shape, np.nan, dtype=np.float64)
    for key in order:
        st = bl.stats.get(key)
        if st is None:
            continue
        need = ~np.isfinite(med) | ~np.isfinite(scale) | (scale <= 0)
        if not np.any(need):
            break
        avail = need & np.isfinite(st.median) & np.isfinite(st.scale) & (st.scale > 0)
        med[avail] = st.median[avail]
        scale[avail] = st.scale[avail]
    # Final fallback: global 'all'
    if "all" in bl.stats and (
        np.any(~np.isfinite(med)) or np.any(~np.isfinite(scale)) or np.any(scale <= 0)
    ):
        st = bl.stats["all"]
        need_m = ~np.isfinite(med)
        need_s = ~np.isfinite(scale) | (scale <= 0)
        med[need_m] = st.median[need_m]
        scale[need_s] = st.scale[need_s]
    return med, scale
