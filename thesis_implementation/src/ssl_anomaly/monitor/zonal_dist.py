"""Zonal distribution statistics: the R0.5 representation (change
``compare-spatial-representation-strategies``, requirement "Zonal
distribution-statistics representation (R0.5)").

The owner's representation comparison asks for three arms — Zonal Mean,
**Spatial Statistics**, Patch-based. The middle arm needs no new data: the
store already holds ``mean/std/p10/p25/p75/p90/iqr`` per (field, date, band)
for all 490 fields × 538 dates (``scripts/extract_stats.py:33``), but every
consumer today reads only ``median``
(``monitor/inputs.py:95``, ``scripts/export_platform_data.py:454``,
``scripts/segment_and_export_cycles_490.py:55``).

This module turns those stored statistics into model-ready cycle tensors on
the SAME 36-bin grid as ``monitor/inputs.rebuild_masked_cycles``, so the
existing rule-based scorers (``B1PhaseZCausal``, the ``b0_calendar`` DOY
path) and the unchanged alarm machinery consume them without modification.
No training, no GPU, no extraction.

Channel presets
---------------
``level``
    median per band + NDVI(median red, nir) — 8 channels. **Reproduces `b1`
    exactly**; the regression test asserts it, so the distribution arms can
    never quietly diverge from the reference.
``lower``
    the prompt's literal "lower distribution quantiles" question: p10 per
    band + NDVI(p10 red, p10 nir) — 8 channels. Scoring only this block keeps
    the answer undiluted by the multivariate aggregate.
``spread``
    std + IQR per band — 14 channels (within-field variability).
``dist``
    every statistic (45 channels) — the joint arm.

An NDVI channel is built only for ``median``, ``p10`` and ``p25`` (the level
and lower-quantile statistics). The upper quantiles stay per-band: the upper
tail of a crop ratio is far less diagnostic for stress, and adding it would
inflate the tensor without a hypothesis behind it.

Note on non-linearity: an index cannot be reconstructed from a single
non-linear statistic in general, so ``ndvi_p10`` is computed from the p10
*red* and p10 *nir* values (a genuine lower-quantile NDVI) and is documented
as such. No std-of-NDVI channel is fabricated — the std of a ratio is not the
ratio of stds, and inventing it would be a silent data error.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

log = logging.getLogger("ssl_anomaly.monitor.zonal_dist")

N_BINS = 36
BIN_DAYS = 15
MAX_CYCLE_DAYS = 540

BANDS: tuple[str, ...] = ("blue", "green", "red", "nir", "swir1", "swir2", "lst")
# Statistics read from stats.zarr; "median" doubles as the R0 level channel.
STATS: tuple[str, ...] = ("median", "std", "p10", "p25", "p75", "iqr")

PRESETS: dict[str, tuple[str, ...]] = {
    "level": ("median",),
    "lower": ("p10",),
    "spread": ("std", "iqr"),
    "dist": ("median", "std", "p10", "p25", "p75", "iqr"),
}

# Statistics for which an NDVI channel is built from this statistic's own
# red/nir values (see the module docstring).
INDEX_STATS: tuple[str, ...] = ("median", "p10", "p25")

# Channels are non-negative by construction; a negative value means a corrupt
# statistic, not a physical observation.
NON_NEGATIVE_STATS: tuple[str, ...] = ("std", "iqr")


@dataclass(frozen=True)
class ChannelSpec:
    """One channel of the R0.5 tensor.

    ``index`` is set for index channels (ndvi) built from the same statistic's
    red/nir values; ``band`` is set for raw per-band statistics.
    """

    name: str
    stat: str
    band: str | None = None
    index: str | None = None

    def __str__(self) -> str:  # pragma: no cover - display only
        return self.name


def channel_specs(preset: str = "dist") -> list[ChannelSpec]:
    """Build the channel list for a preset (see the module docstring)."""
    if preset not in PRESETS:
        raise KeyError(f"unknown preset {preset!r}; choose from {sorted(PRESETS)}")
    stats = PRESETS[preset]
    specs: list[ChannelSpec] = []
    for stat in stats:
        if stat in INDEX_STATS:
            # Index channel from this statistic's red/nir (documented above).
            specs.append(ChannelSpec(name=f"ndvi_{stat}", stat=stat, index="ndvi"))
        for band in BANDS:
            specs.append(ChannelSpec(name=f"{band}_{stat}", stat=stat, band=band))
    return specs


def channel_names(preset: str = "dist") -> list[str]:
    return [s.name for s in channel_specs(preset)]


def _ndvi_from(red: np.ndarray, nir: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    return np.clip((nir - red) / (nir + red + eps), -1.0, 1.0)


def stat_channels(
    cubes: dict[str, np.ndarray],
    band_index: dict[str, int],
    specs: Sequence[ChannelSpec],
) -> dict[str, np.ndarray]:
    """Resolve every channel spec to a ``(F, D)`` array from the stat cubes.

    ``cubes`` maps statistic name → ``(n_fields, n_dates, n_bands)`` array.
    """
    out: dict[str, np.ndarray] = {}
    for spec in specs:
        if spec.stat not in cubes:
            raise KeyError(
                f"statistic {spec.stat!r} was not loaded; the channel {spec.name} "
                "cannot be built (never fabricate it)"
            )
        cube = cubes[spec.stat]
        if spec.index == "ndvi":
            red = cube[:, :, band_index["red"]]
            nir = cube[:, :, band_index["nir"]]
            out[spec.name] = _ndvi_from(red, nir)
        elif spec.band is not None:
            out[spec.name] = cube[:, :, band_index[spec.band]]
        else:  # pragma: no cover - guarded by construction
            raise ValueError(f"channel spec {spec.name} has neither band nor index")
    return out


def bin_cycle(
    values_by_channel: dict[str, np.ndarray],
    channel_order: Sequence[str],
    *,
    times_days: np.ndarray,
    start_day: int,
    end_day: int,
    harvest_day: int,
    n_bins: int = N_BINS,
    bin_days: int = BIN_DAYS,
    max_cycle_days: int = MAX_CYCLE_DAYS,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Aggregate one field-cycle's per-date channels onto the 36-bin grid.

    Mirrors ``monitor/inputs.rebuild_masked_cycles`` exactly: per-bin
    ``nanmedian`` of the observed dates, mask 0 where nothing was observed,
    admission requires ≥3 bins with observed NDVI. Returns ``None`` when the
    cycle is not admitted.
    """
    sel = (times_days >= start_day) & (times_days < end_day)
    if int(sel.sum()) < 3:
        return None
    dsh = times_days[sel] - harvest_day
    keep = (dsh >= 0) & (dsh < max_cycle_days)
    if int(keep.sum()) < 3:
        return None
    dsh = dsh[keep]

    x = np.full((n_bins, len(channel_order)), np.nan, dtype=np.float32)
    m = np.zeros((n_bins, len(channel_order)), dtype=bool)
    assigned = dsh // bin_days
    for b in np.unique(assigned):
        if b < 0 or b >= n_bins:
            continue
        in_bin = assigned == b
        for ci, name in enumerate(channel_order):
            vals = values_by_channel[name][sel][keep][in_bin]
            finite = np.isfinite(vals)
            if finite.any():
                x[int(b), ci] = float(np.nanmedian(vals[finite]))
                m[int(b), ci] = True

    ndvi_idx = 0 if channel_order and channel_order[0].startswith("ndvi") else None
    if ndvi_idx is None:
        raise ValueError(
            "channel_order must start with the ndvi channel — the admission rule "
            "(>=3 bins with observed NDVI) mirrors the canonical cycle builder"
        )
    if int(m[:, ndvi_idx].sum()) < 3:
        return None
    return x, m


def build_distribution_cycles(
    *,
    reader=None,
    cycles_parquet_path: Path | str | None = None,
    preset: str = "dist",
    stats: Sequence[str] | None = None,
    n_bins: int = N_BINS,
    reference_keys: Sequence[str] | None = None,
) -> dict:
    """Build the R0.5 cycle tensors from the existing ``stats.zarr``.

    Parameters
    ----------
    reader
        An object exposing ``fields``, ``dates``, ``bands``, ``band_index`` and
        ``get_stat(name)`` — ``StatsZarrReader`` in production, a fake in tests.
    cycles_parquet_path
        The canonical cycle table (``data/processed/cycles_490.parquet``).
    preset
        One of :data:`PRESETS` (``level``/``lower``/``spread``/``dist``).
    stats
        Explicit statistic list; overrides ``preset``'s statistics when given
        (the channel set still follows the preset's structure).
    reference_keys
        Optional ``"<field>:<cycle>"`` list the result MUST match exactly (the
        cycle set of ``load_masked_cycles``). A mismatch is a hard error, so a
        distribution arm can never be scored on a different cycle population
        than the reference arm.
    """
    import pandas as pd

    from ssl_anomaly.monitor.inputs import CYCLES_PARQUET_PATH

    if reader is None:
        from ssl_anomaly.io.stats_zarr import StatsZarrReader

        reader = StatsZarrReader()

    path = Path(cycles_parquet_path) if cycles_parquet_path else CYCLES_PARQUET_PATH
    if not Path(path).exists():
        raise RuntimeError(
            f"cycle table missing at {path}. The R0.5 builder reads the SAME canonical "
            "cycle grid as the other arms; run scripts/segment_and_export_cycles_490.py "
            "once (or point --cycles at the existing table)."
        )
    canon = pd.read_parquet(path)
    for col in ("field", "t_start", "t_end", "censored", "start_harvest", "cycle_id"):
        if col not in canon.columns:
            raise ValueError(f"cycles table missing column {col!r}")

    fields = np.asarray(reader.fields, dtype=np.int64)
    band_index = dict(reader.band_index)
    dates = pd.DatetimeIndex(reader.dates)
    times_days = (dates - dates[0]).days.to_numpy().astype(np.int64)

    specs = channel_specs(preset)
    if stats is not None:
        wanted = tuple(stats)
        specs = [ChannelSpec(name=f"{s.band or 'ndvi'}_{s.stat}", stat=s.stat,
                             band=s.band, index=s.index)
                 for s in specs if s.stat in wanted]
        if not specs:
            raise ValueError(f"stats={stats} selects no channels of preset {preset!r}")

    used_stats = sorted({s.stat for s in specs})
    cubes: dict[str, np.ndarray] = {}
    for stat in used_stats:
        try:
            cubes[stat] = np.asarray(reader.get_stat(stat), dtype=np.float32)
        except KeyError as exc:
            raise RuntimeError(
                f"statistic {stat!r} is not present in the store — R0.5 needs the "
                "distribution statistics scripts/extract_stats.py writes "
                f"(mean/std/p10/p25/p75/p90/iqr). {exc}"
            ) from exc
        if cubes[stat].shape[:2] != (len(fields), len(dates)):
            raise ValueError(
                f"stat {stat!r} has shape {cubes[stat].shape}, expected "
                f"({len(fields)}, {len(dates)}, n_bands)"
            )

    per_field = stat_channels(cubes, band_index, specs)
    order = [s.name for s in specs]

    # Light sanity check: spread statistics cannot be negative.
    for name in order:
        stat = next(s.stat for s in specs if s.name == name)
        if stat in NON_NEGATIVE_STATS:
            vals = per_field[name]
            finite = vals[np.isfinite(vals)]
            if finite.size and float(finite.min()) < -1e-6:
                raise ValueError(
                    f"channel {name} has negative values (min {finite.min():.6f}); a "
                    "negative std/iqr means the statistic is corrupt, not the crop"
                )

    rows_x: list[np.ndarray] = []
    rows_m: list[np.ndarray] = []
    fids: list[int] = []
    starts: list[str] = []
    ends: list[str] = []
    harvests: list[int] = []
    keys: list[str] = []

    for _, row in canon.iterrows():
        if bool(row["censored"]):
            continue
        fid = int(row["field"])
        hit = np.flatnonzero(fields == fid)
        if hit.size == 0:
            continue
        fi = int(hit[0])

        start_day = int(row["t_start"])
        end_day = int(row["t_end"])
        harvest_day = int(row.get("start_harvest", row["t_start"]))
        if end_day <= start_day:
            continue

        sliced = {name: per_field[name][fi] for name in order}
        built = bin_cycle(
            sliced, order,
            times_days=times_days, start_day=start_day, end_day=end_day,
            harvest_day=harvest_day, n_bins=n_bins,
        )
        if built is None:
            continue
        x, m = built

        rows_x.append(x)
        rows_m.append(m)
        fids.append(fid)
        starts.append(str(dates[0] + pd.Timedelta(days=start_day)))
        ends.append(str(dates[0] + pd.Timedelta(days=end_day)))
        harvests.append(harvest_day)
        keys.append(f"{fid}:{int(row['cycle_id'])}")

    if not rows_x:
        raise RuntimeError("no cycles were built — check the cycle table and store alignment")

    out = {
        "X": np.stack(rows_x).astype(np.float32),
        "M": np.stack(rows_m),
        "field_ids": np.array(fids, dtype=np.int64),
        "start_dates": np.array(starts, dtype=object),
        "end_dates": np.array(ends, dtype=object),
        "harvest_days": np.array(harvests, dtype=np.int64),
        "cycle_keys": keys,
        "band_names": order,
        "preset": preset,
        "stats_used": used_stats,
    }

    if reference_keys is not None and list(reference_keys) != list(keys):
        ref = set(reference_keys)
        got = set(keys)
        missing = sorted(ref - got)[:5]
        extra = sorted(got - ref)[:5]
        raise RuntimeError(
            "R0.5 cycle population differs from the reference arm "
            f"(ref {len(ref)} cycles, got {len(got)}): missing {missing}, "
            f"unexpected {extra}. The distribution arm must be scored on the SAME "
            "cycles as every other arm — fix the alignment, never the check."
        )
    return out


# ---------------------------------------------------------------------------
# Scoring through the unchanged rule-based path
# ---------------------------------------------------------------------------
def fit_score_b1(
    cycles: dict,
    *,
    train_mask: np.ndarray,
    doy_sin: np.ndarray | None = None,
    min_n: int = 8,
):
    """Fit ``B1PhaseZCausal`` on TRAIN cycles and score every cycle.

    The scorer is channel-agnostic, so the distribution blocks ride the exact
    same statistical path as the reference ``b1`` arm — that is what makes the
    three-way comparison a comparison of REPRESENTATIONS rather than of
    scoring rules. Returns ``(scores (N, 36), b1_scorer)``; NaN where the bin
    has no observation.
    """
    from ssl_anomaly.monitor.models import B1PhaseZCausal

    X = np.asarray(cycles["X"], dtype=np.float32)
    M = np.asarray(cycles["M"], dtype=bool)
    train = np.asarray(train_mask, dtype=bool)
    if train.shape != (len(X),):
        raise ValueError(f"train_mask shape {train.shape} != {len(X)} cycles")
    if not train.any():
        raise ValueError("train_mask selects no cycle — cannot fit the scorer")

    scorer = B1PhaseZCausal(use_doy=doy_sin is not None, min_n=min_n)
    scorer.fit(X[train], M[train], None if doy_sin is None else np.asarray(doy_sin)[train])

    scores = np.full((len(X), X.shape[1]), np.nan, dtype=np.float64)
    for i in range(len(X)):
        s = scorer.score_cycle(
            X[i], M[i], None if doy_sin is None else np.asarray(doy_sin)[i],
        )
        scores[i] = np.where(M[i].any(axis=1), s, np.nan)
    return scores, scorer


def alarm_rates(scores: np.ndarray, tau: float, k: int) -> np.ndarray:
    """Per-cycle alarm flag with the existing persistence rule (k bins above τ).

    Delegates to ``monitor.scoring.alarm_per_cycle`` so the R0.5 arms use the
    UNCHANGED alarm machinery rather than a look-alike.
    """
    from ssl_anomaly.monitor.scoring import alarm_per_cycle

    return np.array([bool(alarm_per_cycle(s, tau, k)) for s in scores], dtype=bool)


def calendar_doy_bins(bins: np.ndarray, start_day: int, *, bin_days: int = BIN_DAYS,
                      n_calendar: int = N_BINS) -> np.ndarray:
    """Map each cycle bin to a calendar-DOY bin index in ``[0, n_calendar)``.

    ``b0_calendar`` scores a cycle against its calendar position rather than
    its harvest-relative position, so the same 36-bin tensor is re-indexed by
    the absolute day at each bin midpoint (``start_day + b·bin_days + 15``).
    """
    abs_bins = (int(start_day) + np.asarray(bins, dtype=np.int64) * bin_days) % 365
    return np.clip((abs_bins / 365.0 * n_calendar).astype(np.int64), 0, n_calendar - 1)


def fit_score_calendar(
    cycles: dict,
    *,
    train_mask: np.ndarray,
    start_days: np.ndarray,
    min_n: int = 8,
    n_calendar: int = N_BINS,
) -> tuple[np.ndarray, np.ndarray]:
    """The ``b0_calendar``-equivalent scoring path on the SAME channels.

    ``b1_dist`` asks "is this cycle anomalous for its phase?"; this asks "is it
    anomalous for its calendar position?" — the DOY variant the R0.5 task list
    requires. The statistics are fitted on TRAIN cycles only, keyed by calendar
    bin, and pooled across fields (no per-field terms), exactly like
    ``B1PhaseZCausal`` with ``use_doy=False`` but on the calendar axis.

    Returns ``(scores (N, 36), used_mask (N, 36))``. A cycle bin whose calendar
    bin has fewer than ``min_n`` train observations falls back to the cycle-bin
    statistics, so no bin is silently unscored.
    """
    X = np.asarray(cycles["X"], dtype=np.float64)
    M = np.asarray(cycles["M"], dtype=bool)
    train = np.asarray(train_mask, dtype=bool)
    starts = np.asarray(start_days, dtype=np.int64)
    if train.shape != (len(X),):
        raise ValueError(f"train_mask shape {train.shape} != {len(X)} cycles")
    if len(starts) != len(X):
        raise ValueError(f"start_days length {len(starts)} != {len(X)} cycles")
    if not train.any():
        raise ValueError("train_mask selects no cycle — cannot fit the calendar scorer")

    T, C = X.shape[1], X.shape[2]
    bins = np.arange(T)
    cal_med = np.full((n_calendar, C), np.nan)
    cal_scale = np.full((n_calendar, C), np.nan)

    # Pooled per-cycle-bin statistics (the fallback, and the degenerate guard).
    pooled_med = np.full((T, C), np.nan)
    pooled_scale = np.full((T, C), np.nan)
    for b in range(T):
        for c in range(C):
            v = X[train, b, c][M[train, b, c]]
            if v.size >= min_n:
                pooled_med[b, c] = float(np.median(v))
                pooled_scale[b, c] = max(
                    1.4826 * float(np.median(np.abs(v - pooled_med[b, c]))), 1e-3
                )
    global_med = np.array([
        float(np.median(X[train, :, c][M[train, :, c]])) if M[train, :, c].any() else 0.0
        for c in range(C)
    ])
    global_scale = np.array([
        max(1.4826 * float(np.median(np.abs(
            X[train, :, c][M[train, :, c]] - global_med[c]
        ))), 1e-3) if M[train, :, c].any() else 1.0
        for c in range(C)
    ])
    pooled_med = np.where(np.isfinite(pooled_med), pooled_med, global_med)
    pooled_scale = np.where(np.isfinite(pooled_scale) & (pooled_scale > 0),
                            pooled_scale, global_scale)

    cal_of = np.stack([calendar_doy_bins(bins, s, n_calendar=n_calendar) for s in starts])
    for k in range(n_calendar):
        for c in range(C):
            vals: list[np.ndarray] = []
            for i in np.flatnonzero(train):
                sel = cal_of[i] == k
                v = X[i, sel, c][M[i, sel, c]]
                if v.size:
                    vals.append(v)
            if not vals:
                continue
            allv = np.concatenate(vals)
            if allv.size >= min_n:
                cal_med[k, c] = float(np.median(allv))
                cal_scale[k, c] = max(
                    1.4826 * float(np.median(np.abs(allv - cal_med[k, c]))), 1e-3
                )

    scores = np.full((len(X), T), np.nan)
    for i in range(len(X)):
        cidx = cal_of[i]
        med = np.where(np.isfinite(cal_med[cidx]), cal_med[cidx], pooled_med)
        scale = np.where(np.isfinite(cal_scale[cidx]) & (cal_scale[cidx] > 0),
                         cal_scale[cidx], pooled_scale)
        z = np.where(M[i], (X[i] - med) / scale, 0.0)
        cnt = np.maximum(M[i].sum(axis=1), 1)
        s = (z * z * M[i]).sum(axis=1) / cnt
        scores[i] = np.where(M[i].any(axis=1), s, np.nan)
    return scores, M


def pathmax_scores(
    scores: np.ndarray,
    channels: Sequence[int],
    mask: np.ndarray,
    *,
    absolute: bool = False,
) -> np.ndarray:
    """Per-bin MAX over a channel subset instead of the mean over all channels.

    The R0.5 arm's question is whether the lower quantile carries a signal the
    level misses. Averaging the p10 z² together with seven other p10 channels
    answers a different question, so this path-max variant reports each
    channel's own evidence: ``max_{c ∈ channels} z²``.

    ``absolute=False`` (default) expects per-channel z² already, so the caller
    passes ``(X, M)`` through the same decomposition used for the mean path.
    NaN where no channel of the subset is observed.
    """
    z2 = np.asarray(scores, dtype=np.float64)      # (N, T, C) squared z
    m = np.asarray(mask, dtype=bool)
    sub = list(channels)
    if z2.ndim != 3 or z2.shape[2] != m.shape[2]:
        raise ValueError(f"scores {z2.shape} and mask {m.shape} disagree on channels")
    if any(c < 0 or c >= z2.shape[2] for c in sub):
        raise ValueError(f"channel index out of range for {z2.shape[2]} channels")
    sel_m = m[:, :, sub]
    vals = np.where(sel_m, z2[:, :, sub], -np.inf)
    with np.errstate(invalid="ignore"):
        out = vals.max(axis=2)
    if absolute:
        out = np.abs(out)
    out[~sel_m.any(axis=2)] = np.nan
    return out


def channel_z2(
    cycles: dict,
    *,
    median: np.ndarray,   # (G, T, C) fit-time medians
    scale: np.ndarray,    # (G, T, C) fit-time scales
    group: np.ndarray,    # (N, T) group index per cycle bin
) -> np.ndarray:
    """Per-channel squared z, ``(N, T, C)``, zero where unobserved.

    ``fit_score_b1`` collapses the channels with a mean; the path-max variant
    above needs the decomposition, so it is exposed here rather than
    re-implemented at the call site (one definition of z, one place to audit).
    """
    X = np.asarray(cycles["X"], dtype=np.float64)
    M = np.asarray(cycles["M"], dtype=bool)
    N, T, C = X.shape
    rows = np.arange(T)
    med = np.asarray(median, dtype=np.float64)[group, rows]      # (N, T, C)
    scl = np.asarray(scale, dtype=np.float64)[group, rows]
    z = np.where(M, (X - med) / scl, 0.0)
    out = np.where(M, z * z, 0.0)
    # Bins with no observation at all are NaN, not zero — a zero would read as
    # "perfectly normal" in every downstream aggregate.
    out[~M.any(axis=2)] = np.nan
    return out


__all__ = [
    "BANDS",
    "BIN_DAYS",
    "INDEX_STATS",
    "MAX_CYCLE_DAYS",
    "NON_NEGATIVE_STATS",
    "N_BINS",
    "PRESETS",
    "STATS",
    "ChannelSpec",
    "alarm_rates",
    "bin_cycle",
    "build_distribution_cycles",
    "calendar_doy_bins",
    "channel_names",
    "channel_specs",
    "channel_z2",
    "fit_score_b1",
    "fit_score_calendar",
    "pathmax_scores",
    "stat_channels",
]
