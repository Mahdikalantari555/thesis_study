"""Harvest detection and cycle segmentation.

A harvest is defined (per spec) as an NDVI trough with sufficient prominence
that is preceded by a high plateau and followed by a rise. Cycles are the
intervals between consecutive detected harvests; the first/last cycles are
censored. Replants reset the ratoon counter.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from ..utils.arrays import hampel_filter
from .smoothing import to_daily_grid, whittaker_tune_lambda

log = logging.getLogger("ssl_anomaly.phenology.cycles")


@dataclass(frozen=True)
class Cycle:
    field: int
    cycle_id: int
    t_start: int  # inclusive day index (start of cycle, just after start_harvest)
    t_end: int  # exclusive day index (end of cycle, just before end_harvest)
    start_harvest: int  # day of harvest that BEGINS this cycle (-1 for leading censored)
    end_harvest: int  # day of harvest that ENDS this cycle (last day for trailing censored)
    censored: bool
    kind: str  # "plant" | "ratoon"
    ratoon_no: int
    ndvi_at_harvest: float = float("nan")

    @property
    def length_days(self) -> int:
        return int(self.t_end - self.t_start)

    def to_dict(self) -> dict:
        return {
            "field": int(self.field),
            "cycle_id": int(self.cycle_id),
            "t_start": int(self.t_start),
            "t_end": int(self.t_end),
            "start_harvest": int(self.start_harvest),
            "end_harvest": int(self.end_harvest),
            # Retain 'harvest_day' for backward-compat (end harvest) — scripts
            # can migrate to start_harvest for dsh computation.
            "harvest_day": int(self.end_harvest),
            "length_days": self.length_days,
            "censored": bool(self.censored),
            "kind": self.kind,
            "ratoon_no": int(self.ratoon_no),
            "ndvi_at_harvest": float(self.ndvi_at_harvest),
        }


def detect_harvests(
    grid_days: np.ndarray,
    ndvi_smooth: np.ndarray,
    *,
    min_prominence: float = 0.15,
    min_cycle_days: int = 180,
    plateau_frac: float = 0.7,
    rise_frac: float = 0.15,
) -> np.ndarray:
    """Detect harvest indices into ``grid_days`` (daily grid).

    1. Find deep troughs via scipy find_peaks(-ndvi).
    2. Require a high plateau before (mean over preceding window ≥ frac*max).
    3. Require a rise after (NDVI ≥ trough + rise_frac within min_cycle_days).
    """
    y = np.asarray(ndvi_smooth, dtype=np.float64)
    n = y.size
    if n < min_cycle_days:
        return np.array([], dtype=np.int64)

    ymax = float(np.nanmax(y))
    ymin = float(np.nanmin(y))
    prom = max(min_prominence, 0.1 * (ymax - ymin))
    troughs, props = find_peaks(-y, prominence=prom, distance=min_cycle_days // 2)

    keep: list[int] = []
    for idx in troughs:
        # Plateau before: look at 60-day window ending min_cycle_days before trough
        pre_start = max(0, idx - int(min_cycle_days * 0.7))
        pre_end = max(pre_start + 1, idx - 30)
        pre = y[pre_start:pre_end]
        if pre.size == 0 or np.nanmean(pre) < plateau_frac * ymax:
            continue
        # Rise after: require NDVI to rise by rise_frac*(ymax-ymin) within min_cycle_days
        post_end = min(n, idx + min_cycle_days)
        post = y[idx:post_end]
        trough_val = y[idx]
        if post.size < 30:
            continue
        if np.nanmax(post) < trough_val + rise_frac * (ymax - trough_val):
            continue
        keep.append(int(idx))

    return np.array(keep, dtype=np.int64)


def _detect_replant(
    grid_days: np.ndarray,
    ndvi_smooth: np.ndarray,
    harvests: np.ndarray,
    *,
    gap_days: int = 120,
    low_ndvi: float = 0.3,
) -> set[int]:
    """Return a set of harvest indices after which a replant occurs (reset ratoon).

    A replant is signaled by a long post-harvest period with NDVI below ``low_ndvi``
    before the next rise (gap_days), or by a gap between harvests exceeding
    twice min_cycle_days with low NDVI throughout.
    """
    replant = set()
    for i in range(len(harvests) - 1):
        h0, h1 = harvests[i], harvests[i + 1]
        gap = h1 - h0
        seg = ndvi_smooth[h0:h1]
        if seg.size == 0:
            continue
        days_below = np.sum(seg < low_ndvi)
        if days_below >= gap_days or gap > 540:
            replant.add(i)
    return replant


def segment_cycles(
    field_id: int,
    times_days: np.ndarray,
    ndvi: np.ndarray,
    quality: np.ndarray | None = None,
    *,
    lam: float | None = None,
    min_prominence: float = 0.15,
    min_cycle_days: int = 180,
    max_cycle_days: int = 540,
    plateau_frac: float = 0.7,
    rise_frac: float = 0.15,
    replant_gap_days: int = 120,
    replant_low_ndvi: float = 0.3,
    hampel_window: int = 5,
    hampel_sigma: float = 3.0,
) -> list[Cycle]:
    """Segment harvest-driven cycles for a single field.

    Parameters
    ----------
    field_id:
        Field identifier (stored on each Cycle).
    times_days:
        1-D int array, days-since-epoch for each observation (sorted or will be sorted).
    ndvi:
        Observed NDVI values at those times.
    quality:
        Optional quality weights (valid_frac x cloud proximity).
    lam:
        Whittaker smoothing parameter; if None, tuned by CV.
    """
    times_days = np.asarray(times_days, dtype=np.int64)
    ndvi = np.asarray(ndvi, dtype=np.float64)

    # Sort and drop NaNs
    order = np.argsort(times_days)
    times_days, ndvi = times_days[order], ndvi[order]
    if quality is not None:
        quality = np.asarray(quality, dtype=np.float64)[order]
    finite = np.isfinite(ndvi)
    times_days, ndvi = times_days[finite], ndvi[finite]
    if quality is not None:
        quality = quality[finite]
    if times_days.size < 30:
        log.debug("Field %d has too few observations (%d); no cycles", field_id, times_days.size)
        return []

    # Hampel outlier removal so single cloud-missed points aren't called harvests
    outlier_mask = hampel_filter(times_days, ndvi, window=hampel_window, n_sigma=hampel_sigma)
    ndvi_clean = ndvi.copy()
    ndvi_clean[outlier_mask] = np.nan
    keep = np.isfinite(ndvi_clean)
    if keep.sum() < 20:
        return []
    times_days, ndvi_clean = times_days[keep], ndvi_clean[keep]
    if quality is not None:
        quality = quality[keep]

    if lam is None:
        lam, _ = whittaker_tune_lambda(times_days, ndvi_clean, quality)
        log.debug("Field %d: chosen lambda=%.2f", field_id, lam)

    grid, ys = to_daily_grid(times_days, ndvi_clean, quality=quality, lam=float(lam))

    harvest_idx = detect_harvests(
        grid, ys,
        min_prominence=min_prominence,
        min_cycle_days=min_cycle_days,
        plateau_frac=plateau_frac,
        rise_frac=rise_frac,
    )
    if harvest_idx.size == 0:
        return []

    replant_harvests = _detect_replant(
        grid, ys, harvest_idx, gap_days=replant_gap_days, low_ndvi=replant_low_ndvi
    )

    # Build cycles:
    #  - lead-in: from series start to first harvest → censored plant cycle
    #    (start_harvest = -1; dsh not meaningful but end_harvest = first harvest)
    #  - between harvests h[i]..h[i+1]: complete cycle, start_harvest=h[i], end_harvest=h[i+1]
    #  - trailing: last harvest to series end → censored cycle
    cycles: list[Cycle] = []
    # Leading
    cycles.append(
        Cycle(
            field=field_id,
            cycle_id=0,
            t_start=int(grid[0]),
            t_end=int(grid[harvest_idx[0]]),
            start_harvest=-1,
            end_harvest=int(grid[harvest_idx[0]]),
            censored=True,
            kind="plant",
            ratoon_no=0,
            ndvi_at_harvest=float(ys[harvest_idx[0]]),
        )
    )
    ratoon_no = 0
    cid = 1
    last_complete_kind = "plant"
    for i in range(harvest_idx.size - 1):
        h0, h1 = harvest_idx[i], harvest_idx[i + 1]
        length = h1 - h0
        if length < min_cycle_days or length > max_cycle_days:
            continue
        if i in replant_harvests:
            ratoon_no = 0
            kind = "plant"
        else:
            ratoon_no += 1
            kind = "ratoon"
        last_complete_kind = kind
        cycles.append(
            Cycle(
                field=field_id,
                cycle_id=cid,
                t_start=int(grid[h0]),
                t_end=int(grid[h1]),
                start_harvest=int(grid[h0]),
                end_harvest=int(grid[h1]),
                censored=False,
                kind=kind,
                ratoon_no=ratoon_no,
                ndvi_at_harvest=float(ys[h1]),
            )
        )
        cid += 1
    # Trailing
    hlast = harvest_idx[-1]
    cycles.append(
        Cycle(
            field=field_id,
            cycle_id=cid,
            t_start=int(grid[hlast]),
            t_end=int(grid[-1]) + 1,
            start_harvest=int(grid[hlast]),
            end_harvest=int(grid[-1]),
            censored=True,
            kind=last_complete_kind,
            ratoon_no=max(0, ratoon_no),
            ndvi_at_harvest=float(ys[hlast]),
        )
    )
    return cycles


def cycles_to_dataframe(cycles: list[Cycle]) -> pd.DataFrame:
    return pd.DataFrame([c.to_dict() for c in cycles])
