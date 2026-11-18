"""Synthetic perturbations for the development metric.

Two families (owner decision 2026-11-14, change literature-grounded-severity-protocol):

1. **Index-drop family (HEADLINE)** — absolute-Δ drops on NDVI (channel 0) and
   SAVI (realized through the red/nir channels) at the levels of the verified
   severity table (``severity_table.py``: S1 −0.02 … S6 −0.40), in two
   duration variants: acute (1–4 bins, per-level) and persistent (the fixed
   4–6-bin salinity-like chronic variant, labeled experimental — magnitude
   unsourced in the literature). ``inject_index_drop`` / ``inject_index_drop_dataset``.
2. **MAD-scaled interim types (LEGACY, D6)** — severity in multiples of the
   TRAIN MAD of the affected band (0.5 / 1 / 1.5 / 2 × MAD), onset bin kept as
   ground truth. Retired from the headline metric by finding 16 (no dynamic
   range at the 5 % cycle FAR) and the 2026-11-14 owner decision; kept for the
   finding-16 continuity report and ``lst_rise`` diagnostics.

All injections operate on the raw (bins, channels) tensor + observation mask,
modify only observed entries, and never touch CWSI/ETa (none exist in these
tensors — the forbidden-target test enforces this stays true).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ssl_anomaly.monitor.severity_table import (
    GRADUAL_FAMILY,
    GRADUAL_RAMP_BINS,
    PERSISTENT_DURATION_BINS,
    PERSISTENT_FAMILY,
    SEVERITY_TABLE,
)

INTERIM_TYPES: tuple[str, ...] = (
    "ndvi_drop",
    "lst_rise",
    "phenology_delay",
    "growth_stall",
    "early_senescence",
    "transient_drop",
)

SEVERITIES: tuple[float, ...] = (0.5, 1.0, 1.5, 2.0)
PHASES: tuple[str, ...] = ("early", "mid", "late")

CH_NDVI = 0
CH_BLUE, CH_GREEN, CH_RED, CH_NIR, CH_SWIR1, CH_SWIR2 = 1, 2, 3, 4, 5, 6
CH_LST = 7

# ---------------------------------------------------------------------------
# Index-drop family (change literature-grounded-severity-protocol, task 1.2)
# ---------------------------------------------------------------------------
# Absolute-Δ drops on NDVI (channel 0 — a real channel of the tensors) and on
# SAVI. SAVI is NOT a channel of the tensors and is never fabricated: the
# target ΔSAVI is realized by solving the red/nir scaling that produces it
# (see ``_solve_savi_drop`` and finding 18 for the solver documentation).
SAVI_L = 0.5
# Physical ranges for flooring (reflectance bands mirror inputs.PHYSICAL_RANGES;
# NDVI/SAVI are bounded indices).
REFLECTANCE_PHYSICAL_RANGE = (-0.1, 1.6)
NDVI_PHYSICAL_RANGE = (-1.0, 1.0)

# Channels touched by each legacy perturbation type (flagged `legacy` for the
# headline metric since the severity re-anchor; kept for finding-16 continuity
# and lst_rise diagnostics — owner decision 2026-11-14).
TYPE_CHANNELS: dict[str, tuple[int, ...]] = {
    "ndvi_drop": (CH_NDVI,),
    "lst_rise": (CH_LST,),
    "phenology_delay": (CH_NDVI, CH_GREEN, CH_RED, CH_NIR, CH_SWIR1, CH_SWIR2),
    "growth_stall": (CH_NDVI, CH_GREEN, CH_NIR),
    "early_senescence": (CH_NDVI, CH_NIR),
    "transient_drop": (CH_NDVI,),
}


def savi_from_red_nir(red: float, nir: float, L: float = SAVI_L) -> float:
    """SAVI = (1 + L) · (nir − red) / (nir + red + L)."""
    return (1.0 + L) * (nir - red) / (nir + red + L)


def grand_growth_median(x: np.ndarray, m: np.ndarray, channel: int = CH_NDVI) -> tuple[float | None, str]:
    """The field's OWN grand-growth median of one channel (injection-time
    reference for the % reporting column).

    Grand-growth window = middle third of the cycle (bins T/3 … 2T/3), where
    the sugarcane canopy is at maximum development (Dingre et al. 2021 anchor).
    Falls back to all observed bins of the cycle when the window holds no
    observation; returns (None, "absent") for a cycle with no observation of
    the channel at all.
    """
    T = x.shape[0]
    lo, hi = T // 3, (2 * T) // 3
    vals = x[lo:hi, channel][m[lo:hi, channel]]
    vals = vals[np.isfinite(vals)]
    if vals.size:
        return float(np.median(vals)), "grand_growth_bins"
    vals = x[:, channel][m[:, channel]]
    vals = vals[np.isfinite(vals)]
    if vals.size:
        return float(np.median(vals)), "all_observed_bins_fallback"
    return None, "absent"


def _solve_savi_drop(red: float, nir: float, delta: float) -> tuple[float, float] | None:
    """Solve the red/nir pair realizing a target SAVI drop of ``delta``.

    The vegetation signal is the red-edge balance (nir − red); the solver
    shifts that balance while holding the summed reflectance nir + red
    constant (a canopy-amount change at constant brightness — no brightness
    artifact is smuggled into other channels):

        SAVI  = (1+L)(nir − red) / (nir + red + L)
        S     = nir + red (held)
        D'    = (SAVI − Δ)(S + L) / (1+L)   (target nir − red difference)
        nir'  = (S + D') / 2,  red' = (S − D') / 2

    Returns None when the bin cannot realize the drop (nir + red + L ≤ 0,
    i.e. a degenerate SAVI denominator). Flooring to the physical reflectance
    range happens in the caller; the realized Δ is recomputed afterwards.
    """
    s = nir + red
    if s + SAVI_L <= 0:
        return None
    target_savi = savi_from_red_nir(red, nir) - delta
    d_new = target_savi * (s + SAVI_L) / (1.0 + SAVI_L)
    return (s - d_new) / 2.0, (s + d_new) / 2.0  # (red', nir')


@dataclass
class InjectionResult:
    x: np.ndarray  # perturbed (bins, channels)
    m: np.ndarray  # observation mask (unchanged)
    onset_bin: int
    pert_type: str
    severity: float
    phase: str
    source_row: int = -1  # index of the source cycle in the injected array
    meta: dict = field(default_factory=dict)  # index-drop provenance (family, deltas, %)


@dataclass
class PerturbationConfig:
    types: tuple[str, ...] = INTERIM_TYPES
    severities: tuple[float, ...] = SEVERITIES
    phases: tuple[str, ...] = PHASES
    durations: tuple[int, ...] = (1, 2, 3, 5)
    bin_days: int = 15
    n_per_stratum: int = 8


def phase_start_bin(phase: str, n_bins: int) -> int:
    if phase == "early":
        return max(1, n_bins // 6)
    if phase == "mid":
        return n_bins // 2
    if phase == "late":
        return (5 * n_bins) // 6
    raise ValueError(f"Unknown phase {phase}")


def mad_at(bin_idx: int, channel: int, mad: np.ndarray) -> float:
    """Train MAD (raw units) of one band at one phase bin.

    ``mad`` is the per-(bin, channel) scale array from the robust stats
    (scale = MAD × 1.4826); the MAD itself is scale / 1.4826.
    """
    return float(mad[bin_idx, channel]) / 1.4826


def inject_perturbation(
    x: np.ndarray,
    m: np.ndarray,
    *,
    pert_type: str,
    onset_bin: int,
    duration: int,
    severity: float,
    mad: np.ndarray,  # (bins, channels) scale = MAD×1.4826 from train stats
    rng: np.random.Generator | None = None,
) -> InjectionResult:
    """Inject one perturbation into a raw cycle tensor.

    Only observed entries are modified. Returns the perturbed copy with the
    onset bin as ground truth.
    """
    del rng  # injections are deterministic given (type, onset, duration, severity)
    out = x.copy()
    T, C = out.shape
    onset = int(onset_bin)
    end = min(T, onset + int(duration))
    if onset >= T or duration <= 0:
        return InjectionResult(out, m, onset, pert_type, severity, "")

    def obs(bin_idx: int, ch: int) -> bool:
        return bool(m[bin_idx, ch])

    def mad_of(ch: int, b: int) -> float:
        return mad_at(min(b, mad.shape[0] - 1), ch, mad)

    if pert_type == "ndvi_drop":
        # Gradual ramp to full depth, hold, then partial (50 %) recovery.
        for b in range(onset, end):
            frac = (b - onset + 1) / max(1, end - onset)
            depth = severity * mad_of(CH_NDVI, b) * frac
            if obs(b, CH_NDVI):
                out[b, CH_NDVI] -= depth
        for b in range(end, min(T, end + 2)):
            depth = severity * mad_of(CH_NDVI, b) * 0.5 * (1.0 - (b - end) / 2.0)
            if obs(b, CH_NDVI):
                out[b, CH_NDVI] -= depth

    elif pert_type == "lst_rise":
        # Fast rise over the duration bins, full recovery afterwards.
        for b in range(onset, end):
            if obs(b, CH_LST):
                out[b, CH_LST] += severity * mad_of(CH_LST, b)

    elif pert_type == "phenology_delay":
        # Growth trajectory continues as if the crop were `k` bins younger.
        k = max(1, int(round(severity)))  # 1×MAD ↔ 1 bin (15 days)
        channels = TYPE_CHANNELS[pert_type]
        shifted = out.copy()
        for b in range(onset, T):
            src = b - k
            if src < 0:
                continue
            for ch in channels:
                # Never erase observations: shift only where the source bin
                # has a value too; otherwise leave the target untouched.
                if obs(b, ch) and obs(src, ch) and np.isfinite(out[src, ch]):
                    shifted[b, ch] = out[src, ch]
        out = shifted

    elif pert_type == "growth_stall":
        # Canopy frozen at the onset level for the duration (level taken from
        # the first observed bin at or after the onset).
        channels = TYPE_CHANNELS[pert_type]
        for ch in channels:
            level_bin = next((b for b in range(onset, end) if obs(b, ch)), None)
            if level_bin is None:
                continue
            level = out[level_bin, ch]
            for b in range(level_bin, end):
                if obs(b, ch):
                    out[b, ch] = level

    elif pert_type == "early_senescence":
        # Progressive deepening decline, no recovery inside the horizon.
        for b in range(onset, end):
            frac = (b - onset + 1) / max(1, end - onset)
            depth = severity * mad_of(CH_NDVI, b) * frac
            if obs(b, CH_NDVI):
                out[b, CH_NDVI] -= depth
            if obs(b, CH_NIR):
                out[b, CH_NIR] -= 0.5 * severity * mad_of(CH_NIR, b) * frac

    elif pert_type == "transient_drop":
        # One-bin drop then linear recovery over the next two bins.
        if obs(onset, CH_NDVI):
            out[onset, CH_NDVI] -= severity * mad_of(CH_NDVI, onset)
        for b in range(onset + 1, min(T, onset + 3)):
            depth = severity * mad_of(CH_NDVI, b) * (1.0 - (b - onset) / 2.0)
            if depth > 0 and obs(b, CH_NDVI):
                out[b, CH_NDVI] -= depth

    else:
        raise ValueError(f"Unknown perturbation type {pert_type}")

    return InjectionResult(out, m, onset, pert_type, severity, "")


def inject_index_drop(
    x: np.ndarray,
    m: np.ndarray,
    *,
    index: str,
    onset_bin: int,
    duration: int,
    delta: float,
    family: str = "acute",
) -> InjectionResult:
    """Inject one absolute-Δ index drop into a raw cycle tensor.

    ``index`` is ``"ndvi"`` (channel 0 shifted by −Δ, floored at the NDVI
    physical range) or ``"savi"`` (the target ΔSAVI realized through the
    red/nir solver — the savi channel does not exist and is never fabricated).
    Constant Δ over ``duration`` bins starting at ``onset_bin`` (no ramp, no
    recovery — the severity table's honest reading of a level drop). Only
    observed entries are modified; masks are never changed; the onset bin is
    recorded as ground truth for delay measurement.

    ``meta`` carries the provenance recorded at injection time:
    family/index/delta target, per-bin realized deltas (after flooring),
    skipped-bin count (SAVI bins missing red or nir), floored-bin count, and
    the % of the field's OWN grand-growth median.

    For ``family="gradual"`` the applied magnitude at bin b is
    ``delta · min(1, (b − onset + 1)/duration)`` — the ramp then held to cycle
    end (change ``gradual-severity-shape``). ``meta["n_bins_window"]`` stays the
    count of bins the ramp FITS in (``duration``), so onset+window remains a
    valid "the anomaly must be visible by here" window for the event-FAR
    accounting, and ``meta["n_bins_active"]`` records the longer span the
    signal is actually present in.
    """
    if index not in ("ndvi", "savi"):
        raise ValueError(f"Unknown index {index!r} (expected 'ndvi' or 'savi')")
    out = x.copy()
    T = out.shape[0]
    onset = int(onset_bin)
    end = min(T, onset + int(duration))
    realized: list[float] = []
    n_floored = 0
    n_skipped = 0

    gradual = family == GRADUAL_FAMILY
    duration = max(1, int(duration))

    def _mult(b: int) -> float:
        """δ multiplier at bin b: 1.0 for the step families, ramp for gradual."""
        return min(1.0, (b - onset + 1) / duration) if gradual else 1.0

    n_active = (T - onset) if gradual else max(0, end - onset)
    if index == "ndvi":
        for b in range(onset, T if gradual else end):
            mag = delta * _mult(b)
            if not m[b, CH_NDVI] or not np.isfinite(out[b, CH_NDVI]):
                n_skipped += 1
                continue
            target = out[b, CH_NDVI] - mag
            floored = min(max(target, NDVI_PHYSICAL_RANGE[0]), NDVI_PHYSICAL_RANGE[1])
            if floored != target:
                n_floored += 1
            out[b, CH_NDVI] = floored
            realized.append(float(x[b, CH_NDVI] - floored))
    else:  # savi via red/nir solver
        lo_r, hi_r = REFLECTANCE_PHYSICAL_RANGE
        for b in range(onset, T if gradual else end):
            mag = delta * _mult(b)
            if not (m[b, CH_RED] and m[b, CH_NIR]) or not (
                np.isfinite(out[b, CH_RED]) and np.isfinite(out[b, CH_NIR])
            ):
                n_skipped += 1
                continue
            solved = _solve_savi_drop(float(out[b, CH_RED]), float(out[b, CH_NIR]), mag)
            if solved is None:
                n_skipped += 1
                continue
            red_new, nir_new = solved
            for ch, val in ((CH_RED, red_new), (CH_NIR, nir_new)):
                floored = min(max(val, lo_r), hi_r)
                if floored != val:
                    n_floored += 1
                out[b, ch] = floored
            realized.append(float(savi_from_red_nir(x[b, CH_RED], x[b, CH_NIR])
                                  - savi_from_red_nir(out[b, CH_RED], out[b, CH_NIR])))

    field_median, median_source = grand_growth_median(x, m, CH_NDVI)
    pct = None if field_median in (None, 0) else 100.0 * delta / field_median
    return InjectionResult(
        out, m, onset, f"index_drop_{index}", delta, "", -1,
        meta={
            "family": family, "index": index, "delta_target": float(delta),
            "delta_realized": realized, "n_bins_window": max(0, end - onset),
            "n_skipped_bins": n_skipped, "n_floored_bins": n_floored,
            "pct_of_field_median": pct, "field_median_source": median_source,
            "field_grand_growth_median": field_median,
            "savi_solver": "sum-preserving red/nir solve" if index == "savi" else None,
            "ramp_bins": (duration if gradual else None),
            "ramp_profile": ([round(_mult(b), 6) for b in range(onset, min(T, onset + duration))]
                             if gradual else None),
            "n_bins_active": int(n_active),
        },
    )


def inject_index_drop_dataset(
    X: np.ndarray,            # (N, bins, channels) raw values
    M: np.ndarray,            # (N, bins, channels) observation mask
    *,
    level_id: str,
    family: str,
    index: str,
    round_idx: int = 0,
) -> list[InjectionResult]:
    """Inject one severity level into EVERY cycle of the given array.

    The severity sweep needs every (level × family × index) cell measured on
    the same evaluation cycles, so (unlike ``inject_dataset``) all N cycles
    receive one injection. Onset phases rotate deterministically through
    early/mid/late with the round index (cycle i, round r → phase
    ``(i + r) % 3``), giving the per-phase breakdown without random resampling.
    """
    delta = {lv.level_id: lv.delta_ndvi for lv in SEVERITY_TABLE}[level_id]
    if family == GRADUAL_FAMILY:
        # The gradual ramp length cycles through the spec's D in {3, 4, 6} by
        # round so one sweep covers all three ramps; the onset is pulled
        # earlier when needed so the FULL ramp fits inside the cycle, and both
        # are recorded per injection (spec scenario "Ramp physically
        # consistent per bin").
        duration = int(GRADUAL_RAMP_BINS[round_idx % len(GRADUAL_RAMP_BINS)])
    elif family == PERSISTENT_FAMILY:
        duration = PERSISTENT_DURATION_BINS
    else:
        duration = {lv.level_id: lv.duration_bins for lv in SEVERITY_TABLE}[level_id]
    results: list[InjectionResult] = []
    for i in range(X.shape[0]):
        phase = PHASES[(i + round_idx) % len(PHASES)]
        onset = phase_start_bin(phase, X.shape[1])
        if family == GRADUAL_FAMILY:
            onset = min(onset, max(1, X.shape[1] - duration))
        res = inject_index_drop(
            X[i], M[i], index=index, onset_bin=onset, duration=duration,
            delta=delta, family=family,
        )
        res.phase = phase
        res.source_row = i
        res.pert_type = f"index_drop_{index}_{level_id}"
        res.meta["level_id"] = level_id
        results.append(res)
    return results


def sample_strata(
    cfg: PerturbationConfig,
    rng: np.random.Generator,
    n_cycles: int,
) -> list[tuple[str, float, str, int]]:
    """Enumerate the (type, severity, phase, duration) strata for one cycle set.

    Each of the n_per_stratum sampled cycles draws one stratum uniformly, so
    the injected set covers types × phases with severity 1×MAD getting the
    primary weight (severity 1 is sampled twice as often as the others).
    """
    strata: list[tuple[str, float, str, int]] = []
    for _ in range(min(cfg.n_per_stratum, n_cycles)):
        ptype = str(cfg.types[int(rng.integers(len(cfg.types)))])
        phase = str(cfg.phases[int(rng.integers(len(cfg.phases)))])
        # Primary severity (1×MAD) oversampled 2:1 — only when it is part of
        # the configured set (the extended-severity diagnostic sweeps other
        # severities and must not have 1×MAD silently mixed in).
        if 1.0 in cfg.severities and rng.random() < 0.5:
            sev = 1.0
        else:
            sev = float(cfg.severities[int(rng.integers(len(cfg.severities)))])
        duration = int(cfg.durations[int(rng.integers(len(cfg.durations)))])
        strata.append((ptype, sev, phase, duration))
    return strata


def inject_dataset(
    X: np.ndarray,          # (N, bins, channels) raw values
    M: np.ndarray,          # (N, bins, channels) observation mask
    mad: np.ndarray,        # (bins, channels) scale = MAD×1.4826
    cfg: PerturbationConfig,
    rng: np.random.Generator,
) -> list[InjectionResult]:
    """Inject one perturbation into a random subset of the N cycles.

    The subset (size ``min(cfg.n_per_stratum, N)``) is drawn uniformly
    without replacement each round, so repeated rounds cover different
    cycles as well as different strata. Result j corresponds to source cycle
    ``cycle_idx[j]`` (also stored on the result as ``source_row``).
    """
    n = X.shape[0]
    n_inj = min(cfg.n_per_stratum, n)
    cycle_idx = rng.choice(n, size=n_inj, replace=False)
    strata = sample_strata(cfg, rng, n_inj)
    results: list[InjectionResult] = []
    for j, (ptype, sev, phase, duration) in enumerate(strata):
        i = int(cycle_idx[j])
        onset = phase_start_bin(phase, X.shape[1])
        res = inject_perturbation(
            X[i], M[i], pert_type=ptype, onset_bin=onset, duration=duration,
            severity=sev, mad=mad, rng=rng,
        )
        res.phase = phase
        res.source_row = i
        results.append(res)
    return results
