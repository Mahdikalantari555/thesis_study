"""Per-field-cycle input tensors and score provenance resolution.

Builds ``(phase_bins, bands)`` cycle tensors from ``stats.zarr`` time series
exactly the way ``scripts/segment_and_export_cycles_490.py`` built the training
data (``data/interim/growth_cycles_490.npz``): ``segment_cycles`` harvest
segmentation from ``src/ssl_anomaly/phenology/cycles.py``, 15-day phase bins
over at most 540 days (36 bins), channel 0 = NDVI followed by the 7 zarr bands,
median-aggregated observations per bin, interior single-gap interpolation.

Also hosts the CWSI proxy score rule (the pre-v3 exporter behaviour) and the
per-observation resolution between real checkpoint scores (``"model"``) and the
proxy fallback (``"proxy"``) / unavailable checkpoints (``"absent"``).
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

from platform_channels import (  # type: ignore
    PROXY_SCORE_FORMULA_ID,
    SCORE_CHECKPOINTS,
    SCORE_NAMES,
)

log = logging.getLogger("cycle_inputs")

BIN_DAYS = 15
MAX_CYCLE_DAYS = 540
N_BINS = int(np.ceil(MAX_CYCLE_DAYS / BIN_DAYS))  # 36

# Proxy rule coefficients (unchanged from the pre-v3 exporter block).
PROXY_OFFSETS = {
    "b0_calendar": 0.18,
    "b1_dsh": 0.15,
    "b1_cusum": 0.12,
    "masked_transformer": 0.14,
    "sts_net": 0.11,
    "tiny_cnn_mamba": 0.10,
    "time2agri": 0.12,
}
PROXY_WEIGHTS = {
    "b0_calendar": 0.65,
    "b1_dsh": 0.80,
    "b1_cusum": 0.85,
    "masked_transformer": 0.92,
    "sts_net": 0.94,
    "tiny_cnn_mamba": 0.96,
    "time2agri": 0.90,
}


def _clamp(x: float, lo: float, hi: float) -> float:
    return float(min(hi, max(lo, x)))


def proxy_scores(cwsi: float | None) -> dict[str, float]:
    """The CWSI proxy rule: ``clamp(offset + max(0, cwsi - 0.45) * weight)``."""
    stress_sig = max(0.0, (cwsi or 0.0) - 0.45)
    return {
        key: round(_clamp(PROXY_OFFSETS[key] + stress_sig * PROXY_WEIGHTS[key], 0.05, 0.95), 3)
        for key in SCORE_NAMES
    }


@dataclass(frozen=True)
class CycleTensor:
    """One non-censored phenology cycle binned into ``(N_BINS, 1 + n_bands)``."""

    field_id: int
    t_start: int  # inclusive day number (== start_harvest for complete cycles)
    t_end: int  # exclusive day number
    harvest_day: int  # day number of the harvest that begins this cycle
    x: np.ndarray  # (N_BINS, 1 + len(bands)) float32, NaN where unobserved


def build_field_cycles(
    field_id: int,
    times_days: np.ndarray,
    ndvi: np.ndarray,
    quality: np.ndarray,
    cube: np.ndarray,
    band_index: dict[str, int],
    *,
    bin_days: int = BIN_DAYS,
    max_days: int = MAX_CYCLE_DAYS,
) -> list[CycleTensor]:
    """Bin all non-censored cycles of one field the way the training NPZ was built.

    Mirrors ``scripts/segment_and_export_cycles_490.py`` (censored cycles and
    cycles with too few observations are skipped) so checkpoint inputs match the
    training distribution.
    """
    from ssl_anomaly.phenology.cycles import segment_cycles

    field_cycles = segment_cycles(
        field_id=field_id,
        times_days=np.asarray(times_days, dtype=np.int64),
        ndvi=ndvi,
        quality=quality,
        min_cycle_days=180,
        max_cycle_days=max_days,
        min_prominence=0.15,
        plateau_frac=0.7,
        rise_frac=0.15,
    )

    times = np.asarray(times_days, dtype=np.int64)
    epoch_day = int(times[0]) if times.size else 0
    band_names = list(band_index.keys())
    n_channels = 1 + len(band_names)

    out: list[CycleTensor] = []
    for c in field_cycles:
        if c.censored:
            continue
        start_day = int(c.t_start)
        end_day = int(c.t_end)
        harvest_day = int(c.start_harvest)
        if end_day <= start_day:
            continue

        obs_mask = (times >= start_day) & (times < end_day)
        if int(obs_mask.sum()) < 3:
            continue

        obs_days = times[obs_mask]
        dsh = obs_days - harvest_day
        valid_obs = (dsh >= 0) & (dsh < max_days)
        if int(valid_obs.sum()) < 3:
            continue

        dsh_valid = dsh[valid_obs]
        ndvi_obs = np.asarray(ndvi, dtype=np.float64)[obs_mask][valid_obs]
        cube_obs = np.asarray(cube, dtype=np.float64)[obs_mask][valid_obs]  # (n_obs, n_bands)

        x_cycle = np.full((N_BINS, n_channels), np.nan, dtype=np.float32)
        assigned_bins = dsh_valid // bin_days
        for b in np.unique(assigned_bins):
            if b >= N_BINS:
                continue
            b_mask = assigned_bins == b
            x_cycle[int(b), 0] = np.nanmedian(ndvi_obs[b_mask])
            for bname in band_names:
                x_cycle[int(b), 1 + band_index[bname]] = np.nanmedian(cube_obs[b_mask, band_index[bname]])

        observed_bins = np.where(np.isfinite(x_cycle[:, 0]))[0]
        if len(observed_bins) < 3:
            continue

        # Interpolate isolated interior gaps (replicates the training exporter).
        first_b, last_b = int(observed_bins[0]), int(observed_bins[-1])
        for ch in range(n_channels):
            series = x_cycle[:, ch]
            for b in range(first_b + 1, last_b):
                if np.isnan(series[b]):
                    prev_val = series[b - 1]
                    next_idx = None
                    for look in range(b + 1, min(b + 3, last_b + 1)):
                        if np.isfinite(series[look]):
                            next_idx = look
                            break
                    if next_idx is not None and np.isfinite(prev_val):
                        series[b] = prev_val + (series[next_idx] - prev_val) * (1 / (next_idx - b + 1))
            x_cycle[:, ch] = series

        out.append(
            CycleTensor(
                field_id=int(field_id),
                t_start=start_day,
                t_end=end_day,
                harvest_day=harvest_day,
                x=x_cycle,
            )
        )
    return out


def lookup_cycle_bin(
    cycles: list[CycleTensor],
    day_num: int,
    *,
    bin_days: int = BIN_DAYS,
    n_bins: int = N_BINS,
) -> tuple[int, int] | None:
    """Map an acquisition day number to ``(cycle_row, phase_bin)`` or ``None``.

    Cycles are the non-censored, buildable ones; days inside censored or
    skipped spans (or before harvest-day semantics) fall back to ``None``.
    """
    for row, c in enumerate(cycles):
        if c.t_start <= day_num < c.t_end:
            dsh = day_num - c.harvest_day
            if 0 <= dsh < n_bins * bin_days:
                b = dsh // bin_days
                if b < n_bins:
                    return row, int(b)
            return None
    return None


def resolve_observation_scores(
    day_num: int,
    cycles: list[CycleTensor],
    *,
    model_errs: dict[str, np.ndarray],
    model_status: dict[str, str],
    cwsi: float | None,
    force_proxy: bool = False,
    bin_days: int = BIN_DAYS,
    n_bins: int = N_BINS,
) -> tuple[dict[str, float | None], dict[str, str], dict[str, str | None]]:
    """Resolve one observation's score map + provenance + formula ids.

    ``model_errs`` holds per-bin scores ``(n_cycles, N_BINS)`` that were already
    squashed by :func:`load_model_checkpoints.squash_bin_error`
    (``1 - exp(-raw_err)``); the model score is that value rounded — it must NOT
    be squashed again. Resolution per score key (contract v3):
      1. checkpoint loaded and the day maps to a finite bin -> ``"model"``;
      2. checkpoint expected but failed to reconstruct -> score ``None`` with
         ``"absent"`` (never a faked number);
      3. otherwise (no artifact / unmapped day / ``--no-models``) -> the CWSI
         proxy rule with ``"proxy"`` and ``PROXY_SCORE_FORMULA_ID``.
    """
    hit = None if force_proxy else lookup_cycle_bin(cycles, day_num, bin_days=bin_days, n_bins=n_bins)
    proxy = proxy_scores(cwsi)
    scores: dict[str, float | None] = {}
    provenance: dict[str, str] = {}
    formula: dict[str, str | None] = {}
    for key in SCORE_NAMES:
        if hit is not None and key in model_errs:
            row, b = hit
            v = float(model_errs[key][row, b])
            if np.isfinite(v):
                scores[key] = round(v, 3)
                provenance[key] = "model"
                formula[key] = f"{key}_490:bin_mse_1mexp"
                continue
        if not force_proxy and model_status.get(key) == "failed":
            scores[key] = None
            provenance[key] = "absent"
            formula[key] = None
            continue
        scores[key] = proxy[key]
        provenance[key] = "proxy"
        formula[key] = PROXY_SCORE_FORMULA_ID
    return scores, provenance, formula


__all__ = [
    "CycleTensor", "BIN_DAYS", "MAX_CYCLE_DAYS", "N_BINS", "PROXY_OFFSETS",
    "PROXY_WEIGHTS", "proxy_scores", "build_field_cycles", "lookup_cycle_bin",
    "resolve_observation_scores",
]
