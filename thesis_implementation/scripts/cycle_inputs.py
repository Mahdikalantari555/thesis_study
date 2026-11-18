"""Per-field-cycle input tensors and score provenance resolution.

Two cycle tensor builders live here:

* :func:`build_field_cycles` (LEGACY, unchanged) — ``(36, 8)`` tensors with the
  interior-gap interpolation the original training NPZ applied
  (``data/interim/growth_cycles_490.npz``). The legacy literature checkpoints
  (``sts_net_490`` …) score these, exactly as before contract v5.
* :func:`build_field_cycles_masked` (v5) — the SAME segmentation, binning and
  admission rules but WITHOUT interior-gap interpolation: a bin/band with no
  finite date value stays NaN + mask False. This mirrors
  ``src/ssl_anomaly/monitor/inputs.py::rebuild_masked_cycles`` — the input
  semantics the causal main checkpoints (``masked_transformer_main``,
  ``gru_ae_main``) were trained on. Censored in-progress cycles can be kept
  (``include_censored=True``) for display; they never enter metrics.

Also hosts the v5 score resolution (model hit or ``absent`` — the CWSI proxy
formula was REMOVED in v5 as circular; spec ``model-output-ingest``), the
causal stress-flag rule (tau / persistence-k, bins <= t only) and the
cycle-to-split mapping from ``data/processed/splits_locked.json``.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

from platform_channels import SCORE_CHECKPOINTS, SCORE_NAMES  # type: ignore
from load_model_checkpoints import score_formula_id, squash_bin_error  # type: ignore

log = logging.getLogger("cycle_inputs")

BIN_DAYS = 15
MAX_CYCLE_DAYS = 540
N_BINS = int(np.ceil(MAX_CYCLE_DAYS / BIN_DAYS))  # 36

# Split tag values written per observation in contract v5 payloads.
SPLIT_TRAIN = "train"
SPLIT_DEV = "dev"
SPLIT_TEST = "test"
SPLIT_MONITORING = "monitoring"


@dataclass(frozen=True)
class CycleTensor:
    """One non-censored phenology cycle binned into ``(N_BINS, 1 + n_bands)``."""

    field_id: int
    t_start: int  # inclusive day number (== start_harvest for complete cycles)
    t_end: int  # exclusive day number
    harvest_day: int  # day number of the harvest that begins this cycle
    x: np.ndarray  # (N_BINS, 1 + len(bands)) float32, NaN where unobserved


@dataclass(frozen=True, eq=False)
class MaskedCycleTensor:
    """One cycle binned into ``(N_BINS, n_channels)`` WITHOUT gap interpolation.

    ``x`` holds NaN wherever a bin/band had no finite observation value and
    ``mask`` is the matching boolean observation mask — the exact input
    semantics of the masked rebuild the causal main checkpoints were trained on
    (``ssl_anomaly.monitor.inputs.rebuild_masked_cycles``).
    """

    field_id: int
    t_start: int  # inclusive day number
    t_end: int  # exclusive day number
    harvest_day: int  # day number of the harvest that begins this cycle
    censored: bool  # in-progress/incomplete cycle (display-only, never metrics)
    cycle_ordinal: int  # per-field segmentation ordinal == parquet cycle_id
    x: np.ndarray  # (N_BINS, n_channels) float32, NaN where unobserved
    mask: np.ndarray  # (N_BINS, n_channels) bool observation mask


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


def build_field_cycles_masked(
    field_id: int,
    times_days: np.ndarray,
    ndvi: np.ndarray,
    quality: np.ndarray,
    cube: np.ndarray,
    band_index: dict[str, int],
    *,
    include_censored: bool = False,
    bin_days: int = BIN_DAYS,
    max_days: int = MAX_CYCLE_DAYS,
) -> list[MaskedCycleTensor]:
    """Masked (never-interpolated) cycle tensors — the v5 causal-model input.

    Mirrors :func:`build_field_cycles` segmentation (``segment_cycles``:
    min 180 d, max 540 d, prominence 0.15, plateau 0.7, rise 0.15), 15-day DSH
    binning, per-bin/band nanmedian aggregation and the admission rules
    (>= 3 observations in the span, >= 3 valid-DSH observations, >= 3
    NDVI-observed bins) EXCEPT that interior-gap interpolation is NOT applied:
    a bin/band with no finite observation value stays NaN with mask False,
    exactly like ``ssl_anomaly.monitor.inputs.rebuild_masked_cycles`` — the
    tensors the causal main checkpoints were trained on.

    ``include_censored=True`` also returns censored in-progress cycles (used
    for display and split tagging; they never enter metrics).
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
    band_names = list(band_index.keys())
    n_channels = 1 + len(band_names)

    out: list[MaskedCycleTensor] = []
    for ordinal, c in enumerate(field_cycles):
        if c.censored and not include_censored:
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

        x = np.full((N_BINS, n_channels), np.nan, dtype=np.float32)
        m = np.zeros((N_BINS, n_channels), dtype=bool)
        assigned_bins = dsh_valid // bin_days
        for b in np.unique(assigned_bins):
            if b >= N_BINS:
                continue
            b_mask = assigned_bins == b
            ndvi_vals = ndvi_obs[b_mask]
            finite_ndvi = np.isfinite(ndvi_vals)
            if finite_ndvi.any():
                x[int(b), 0] = float(np.nanmedian(np.where(finite_ndvi, ndvi_vals, np.nan)))
                m[int(b), 0] = True
            for bname in band_names:
                vals = cube_obs[b_mask, band_index[bname]]
                finite = np.isfinite(vals)
                if finite.any():
                    x[int(b), 1 + band_index[bname]] = float(np.nanmedian(np.where(finite, vals, np.nan)))
                    m[int(b), 1 + band_index[bname]] = True

        # Admission mirrors the NPZ exporter: >= 3 bins with observed NDVI.
        if int(m[:, 0].sum()) < 3:
            continue

        out.append(
            MaskedCycleTensor(
                field_id=int(field_id),
                t_start=start_day,
                t_end=end_day,
                harvest_day=harvest_day,
                censored=bool(c.censored),
                cycle_ordinal=int(ordinal),
                x=x,
                mask=m,
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


def lookup_masked_cycle_bin(
    cycles: list[MaskedCycleTensor],
    day_num: int,
    *,
    bin_days: int = BIN_DAYS,
    n_bins: int = N_BINS,
) -> tuple[int, int] | None:
    """Map an acquisition day number to a masked-cycle ``(row, phase_bin)`` or ``None``.

    Same semantics as :func:`lookup_cycle_bin` but over masked cycle tensors
    (which may include censored cycles when built with ``include_censored=True``).
    A day inside a cycle span whose DSH exceeds the bin range maps to ``None``.
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


# ---------------------------------------------------------------------------
# Split tagging (contract v5): cycle -> train | dev | test | monitoring
# ---------------------------------------------------------------------------
def build_cycle_split_map(repo_root: Path | str | None = None) -> dict[tuple[int, int, int], str]:
    """Map ``(field, t_start, t_end)`` -> split tag from the locked split files.

    Reads ``data/processed/cycles_490.parquet`` (cycle identity) and
    ``data/processed/splits_locked.json`` (manifest["cycles"] lists of
    ``"<field>:<cycle_id>"`` keys over {train, dev, test, monitoring_only}).
    Computed in-process on every export run (cheap; no new data files are
    written). Missing files degrade to an empty map (everything "monitoring")
    with a warning — split tagging never claims in-sample membership without
    the manifest. ``monitoring_only`` is reported as ``"monitoring"``.
    """
    import pandas as pd

    root = Path(repo_root) if repo_root is not None else ROOT_DIR
    parquet_path = root / "data/processed/cycles_490.parquet"
    manifest_path = root / "data/processed/splits_locked.json"

    if not parquet_path.exists() or not manifest_path.exists():
        log.warning(
            "Split files missing (%s / %s) — every observation tagged '%s'",
            parquet_path.name, manifest_path.name, SPLIT_MONITORING,
        )
        return {}

    canon = pd.read_parquet(parquet_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    split_of_key: dict[str, str] = {}
    for split, keys in (manifest.get("cycles") or {}).items():
        tag = SPLIT_MONITORING if split == "monitoring_only" else str(split)
        for key in keys:
            split_of_key[str(key)] = tag

    out: dict[tuple[int, int, int], str] = {}
    for row in canon.itertuples(index=False):
        key = f"{int(row.field)}:{int(row.cycle_id)}"
        out[(int(row.field), int(row.t_start), int(row.t_end))] = split_of_key.get(key, SPLIT_MONITORING)
    log.info(
        "Split map: %d cycles (train/dev/test/monitoring = %d/%d/%d/%d)",
        len(out),
        sum(1 for v in out.values() if v == SPLIT_TRAIN),
        sum(1 for v in out.values() if v == SPLIT_DEV),
        sum(1 for v in out.values() if v == SPLIT_TEST),
        sum(1 for v in out.values() if v == SPLIT_MONITORING),
    )
    return out


def cycle_split_tag(
    cycle: MaskedCycleTensor | CycleTensor,
    split_map: dict[tuple[int, int, int], str],
) -> str:
    """Split tag for one built cycle; unmapped cycles count as monitoring."""
    return split_map.get((int(cycle.field_id), int(cycle.t_start), int(cycle.t_end)), SPLIT_MONITORING)


# ---------------------------------------------------------------------------
# v5 score resolution: model hit or "absent" (no proxy fallback)
# ---------------------------------------------------------------------------
def resolve_observation_scores_v5(
    day_num: int,
    masked_cycles: list[MaskedCycleTensor],
    legacy_cycles: list[CycleTensor],
    *,
    new_raw_errs: dict[str, np.ndarray],
    legacy_squashed_errs: dict[str, np.ndarray],
    bin_days: int = BIN_DAYS,
    n_bins: int = N_BINS,
) -> tuple[dict[str, float | None], dict[str, str], dict[str, str | None]]:
    """Resolve one observation's score map + provenance + formula ids (contract v5).

    ``new_raw_errs`` holds RAW per-bin scores ``(n_masked_cycles, N_BINS)`` from
    the causal main checkpoints (NaN at unobserved bins); the display value is
    squashed here via ``1 - exp(-raw)``. ``legacy_squashed_errs`` holds already
    squashed per-bin scores from the legacy checkpoints. Resolution per score
    key:
      1. causal checkpoint loaded and the day maps to a finite masked bin ->
         ``("model", "<stem>:causal_bin_mse")``;
      2. legacy checkpoint loaded and the day maps to a finite interpolated
         bin -> ``("model", "<stem>_490:bin_mse_1mexp")``;
      3. otherwise (missing/failed checkpoint, unmapped day) -> score ``None``
         with provenance ``"absent"`` — for ALL slots including the b0/b1
         baselines. The CWSI proxy formula was removed in v5 (circular with
         the model's own inputs; spec ``model-output-ingest``).
    """
    scores: dict[str, float | None] = {}
    provenance: dict[str, str] = {}
    formula: dict[str, str | None] = {}
    for key in SCORE_NAMES:
        if key in new_raw_errs:
            hit = lookup_masked_cycle_bin(masked_cycles, day_num, bin_days=bin_days, n_bins=n_bins)
            if hit is not None:
                row, b = hit
                v = float(new_raw_errs[key][row, b])
                if np.isfinite(v):
                    scores[key] = round(float(squash_bin_error(v)), 3)
                    provenance[key] = "model"
                    formula[key] = score_formula_id(key)
                    continue
        elif key in legacy_squashed_errs:
            hit = lookup_cycle_bin(legacy_cycles, day_num, bin_days=bin_days, n_bins=n_bins)
            if hit is not None:
                row, b = hit
                v = float(legacy_squashed_errs[key][row, b])
                if np.isfinite(v):
                    scores[key] = round(v, 3)
                    provenance[key] = "model"
                    formula[key] = score_formula_id(key)
                    continue
        scores[key] = None
        provenance[key] = "absent"
        formula[key] = None
    return scores, provenance, formula


# ---------------------------------------------------------------------------
# Causal stress flag (tau / persistence-k alarm rule)
# ---------------------------------------------------------------------------
def resolve_stress_flag(
    raw_bin_scores: np.ndarray,
    tau: float,
    k: int,
    bin_observed: bool,
) -> str:
    """Causal per-acquisition status from raw per-bin scores of the current cycle.

    ``raw_bin_scores`` is the score PREFIX of the cycle (bins <= the current
    bin — later bins never influence the result, so appending future
    observations cannot change an already-issued status). ``bin_observed``
    says whether the current bin carries a finite model score.

    Returns:
      - ``"suspected_stress"``: the run of ``k`` consecutive observed bins
        ending at the current bin is entirely above ``tau`` (alarm completed);
      - ``"normal"``: the current bin is observed but no alarm run completes here;
      - ``"no_data"``: the current bin is unobserved (or no scores exist).

    The positive class means "suspected stress (anomaly)" until L4 validation.
    """
    s = np.asarray(raw_bin_scores, dtype=np.float64).ravel()
    if not bin_observed or s.size == 0 or not np.isfinite(s[-1]):
        return "no_data"
    if k <= 1:
        return "suspected_stress" if s[-1] > tau else "normal"
    if s.size < k:
        return "normal"
    window = s[-int(k):]
    if np.isfinite(window).all() and bool((window > tau).all()):
        return "suspected_stress"
    return "normal"


__all__ = [
    "CycleTensor", "MaskedCycleTensor", "BIN_DAYS", "MAX_CYCLE_DAYS", "N_BINS",
    "SPLIT_TRAIN", "SPLIT_DEV", "SPLIT_TEST", "SPLIT_MONITORING",
    "build_field_cycles", "build_field_cycles_masked", "lookup_cycle_bin",
    "lookup_masked_cycle_bin", "build_cycle_split_map", "cycle_split_tag",
    "resolve_observation_scores_v5", "resolve_stress_flag",
]
