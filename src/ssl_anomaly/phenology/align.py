"""Phase-axis computation and binning.

Primary axis: days-since-harvest (dsh). Comparators: day-of-year (doy),
growing-degree-days-from-harvest (gdd), and a landmark registration axis.
Observations are assigned to ~15-day bins; unobserved bins stay missing.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# ---------------------------- phase axes -------------------------------------


def compute_dsh(harvest_day: int, obs_days: np.ndarray) -> np.ndarray:
    """Days-since-harvest for each observation (0 = harvest day; positive = after).

    Observations before harvest (dsh < 0) are possible in the first censored cycle.
    """
    return np.asarray(obs_days, dtype=np.int64) - int(harvest_day)


def compute_gdd(
    t_mean: np.ndarray,
    obs_days: np.ndarray,
    harvest_day: int,
    t_base: float = 10.0,
    t_cap: float | None = 35.0,
) -> np.ndarray:
    """Cumulative growing-degree-days since harvest.

    ``t_mean`` is daily mean temperature aligned to daily grid covering
    [harvest_day, obs_days.max]. GDD is max(0, T - T_base), with optional
    upper cap (standard agronomic practice).
    """
    start = int(harvest_day)
    end = int(np.max(obs_days))
    daily_days = np.arange(start, end + 1, dtype=np.int64)
    # Build daily Tmean via nearest alignment (caller responsible for alignment
    # if t_mean is irregular; here we assume aligned 1:1).
    if t_mean.size < daily_days.size:
        # Pad with NaNs if coverage is short
        pad = np.full(daily_days.size - t_mean.size, np.nan)
        t_mean = np.concatenate([t_mean, pad])
    daily_gdd = np.maximum(0.0, t_mean[: daily_days.size] - t_base)
    if t_cap is not None:
        daily_gdd = np.minimum(daily_gdd, t_cap - t_base)
    daily_gdd = np.nan_to_num(daily_gdd, nan=0.0)
    cum = np.concatenate([[0.0], np.cumsum(daily_gdd)])
    # cum[i] = total GDD at day daily_days[i]
    obs_idx = np.clip(np.asarray(obs_days, dtype=np.int64) - start, 0, daily_days.size)
    return cum[obs_idx]


def _landmark_warp(grid_phase: np.ndarray, landmarks: tuple[float, float, float, float]) -> np.ndarray:
    """Piecewise-linear landmark registration (placeholder for full spec).

    Landmarks are fractions [0,1] in (harvest, plateau_start, peak, next_harvest).
    We warp onto a standard [0,1] phase axis with landmarks at (0, 1/3, 2/3, 1).
    """
    hs, ps, pk, nh = landmarks
    standard = np.array([0.0, 1 / 3, 2 / 3, 1.0])
    observed = np.array([hs, ps, pk, nh], dtype=float)
    observed = np.clip(observed, 0.0, 1.0)
    if np.any(np.diff(observed) <= 0):
        return np.clip(grid_phase, 0.0, 1.0)
    return np.interp(grid_phase, observed, standard)


# ------------------------------ binning --------------------------------------


@dataclass
class PhaseBins:
    bin_days: int
    n_bins: int
    edges: np.ndarray  # length n_bins+1
    centers: np.ndarray  # length n_bins


def default_phase_bins(bin_days: int = 15, max_cycle_days: int = 540) -> PhaseBins:
    edges = np.arange(0, max_cycle_days + bin_days, bin_days, dtype=np.float64)
    centers = 0.5 * (edges[:-1] + edges[1:])
    return PhaseBins(bin_days=bin_days, n_bins=edges.size - 1, edges=edges, centers=centers)


def phase_bin(
    values: dict[str, np.ndarray],
    dsh: np.ndarray,
    *,
    bin_days: int = 15,
    max_cycle_days: int = 540,
    max_interp_adjacent: int = 1,
) -> dict[str, np.ndarray]:
    """Bin observations into phase bins by days-since-harvest.

    Parameters
    ----------
    values:
        band_name → 1-D array of observations.
    dsh:
        Days-since-harvest for each observation (same length as each band).
    bin_days, max_cycle_days:
        Binning parameters.
    max_interp_adjacent:
        If 1, fill isolated single-bin gaps by linear interpolation between
        observed neighbors. Spec says ≤1 bin.

    Returns
    -------
    dict
        band_name → array of length n_bins; unobserved bins are NaN.
    """
    bins = default_phase_bins(bin_days=bin_days, max_cycle_days=max_cycle_days)
    n_bins = bins.n_bins
    out: dict[str, np.ndarray] = {}
    for name, v in values.items():
        v = np.asarray(v, dtype=np.float64)
        binned = np.full(n_bins, np.nan, dtype=np.float64)
        counts = np.zeros(n_bins, dtype=np.int64)
        # Assign each observation to the bin containing dsh
        # Bins are [edge_i, edge_{i+1}); observations with dsh>=max_cycle_days dropped
        mask = (dsh >= 0) & (dsh < max_cycle_days) & np.isfinite(v)
        dsh_m = dsh[mask]
        v_m = v[mask]
        idx = np.floor(dsh_m / bin_days).astype(np.int64)
        idx = np.clip(idx, 0, n_bins - 1)
        # Simple bin median via sorting — n_obs is small so bincount/groupby suffices
        order = np.argsort(idx)
        idx_s, v_s = idx[order], v_m[order]
        # Split into runs of same idx
        if idx_s.size:
            split_points = np.where(np.diff(idx_s))[0] + 1
            for grp_i, grp_v in zip(
                np.split(idx_s, split_points), np.split(v_s, split_points)
            ):
                bi = int(grp_i[0])
                binned[bi] = np.nanmedian(grp_v)
                counts[bi] = grp_v.size
        # Optional single-bin interpolation
        if max_interp_adjacent > 0:
            obs = ~np.isnan(binned)
            for j in range(1, n_bins - 1):
                if obs[j]:
                    continue
                left = j - 1
                right = j + 1
                if left >= 0 and right < n_bins and obs[left] and obs[right]:
                    binned[j] = 0.5 * (binned[left] + binned[right])
        out[name] = binned
    out["_counts"] = np.array([np.sum(~np.isnan(out[k])) for k in values], dtype=np.int64)
    return out


def assign_stratum(kind: str, ratoon_no: int, variety_group: str | None) -> str:
    """Return a stratum key for baseline pooling."""
    base = f"{kind}_{ratoon_no}"
    if variety_group:
        return f"{base}|{variety_group}"
    return base


def coarse_strata(stratum: str) -> list[str]:
    """Return coarser strata in order of coarsening, ending with 'all'.

    Used when the fine stratum has too few cycles in a bin.
    """
    parts = stratum.split("|")
    out: list[str] = [stratum]
    if len(parts) == 2:
        out.append(parts[0])  # drop variety
    # Drop ratoon number
    kind = parts[0].split("_")[0]
    out.append(kind)
    out.append("all")
    # de-duplicate preserving order
    seen: set[str] = set()
    uniq: list[str] = []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq
