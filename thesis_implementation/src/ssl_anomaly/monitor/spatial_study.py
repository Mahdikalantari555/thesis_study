"""Spatial-representation study: the pure analysis half of finding 24.

Change ``compare-spatial-representation-strategies``. Everything here is
data-free and unit-testable; the scripts that touch the archive only call it.

The study's whole point is that a comparison table is only honest if the
comparisons are paired and the arithmetic is stated. So this module owns:

* :func:`spatial_support` — the fixed 30 m arithmetic (1 px = 0.09 ha, a 16x16
  crop = 23 ha) and the minimum resolvable anomaly per representation, so no
  row can be published without its spatial support.
* :func:`geometry_memo` — the measured field-size distribution that justifies
  excluding the 64x64 window (median side 16.7 px, max 19.6 px).
* :func:`crossing_table` — the four-cell detectability crossing (patch-only /
  zonal-only / both / neither) per severity level with Wilson CIs and an exact
  two-sided sign test over the discordant pairs, because "patches detect what
  farm means cannot" is a PAIRED claim.
* :func:`alarm_frequency_diagnostic` — per-pixel chronicity: alarm frequency,
  successive-cycle top-q Jaccard overlap, and the entropy of the per-pixel
  alarm distribution. A detector that flags the same pixels every cycle is
  reporting heterogeneity, not events.
* :func:`static_pattern_normalizer` — the per-field per-pixel climatology of a
  field's own clean cycles, used as an alternative normalizer so a chronic
  offset cannot masquerade as an event.
* :func:`capacity_flag`, :func:`render_comparison_table`,
  :func:`noise_null_gap` — the equal-budget bookkeeping and the one table.

Why the sign test and not a t-test: the discordant pairs are counts, the
sample is small (one observation per field per level), and a paired t-test on
two-level data is not a test. The exact binomial sign test on
``n_patch_only`` vs ``n_zonal_only`` is the honest paired statement, and it is
what the pre-registration promises ("a paired test over fields").
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# Landsat-30 m arithmetic, fixed by the spec (never re-derived at runtime).
GSD_M = 30.0
HA_PER_PX = (GSD_M ** 2) / 10_000.0            # 0.09 ha
CAPACITY_FLAG = 0.20                           # >±20 % deviation is flagged

# Measured field-size distribution of the 490-field archive: median field side
# 16.7 px, max 19.6 px. The 64x64 window is excluded by default because a
# patch of that size would be 3.8x the median field, i.e. mostly neighbours.
FIELD_SIDE_MEDIAN_PX = 16.7
FIELD_SIDE_MAX_PX = 19.6
EXCLUDED_WINDOW = 64

# Representations of the ladder, in report order.
REPRESENTATIONS: tuple[str, ...] = ("R0", "R0.5", "R1", "R2", "R3")


def spatial_support(size_px: int, *, gsd_m: float = GSD_M) -> dict:
    """Spatial support of an ``size_px x size_px`` window, in px/m/ha."""
    n = int(size_px)
    if n <= 0:
        raise ValueError(f"window size must be positive, got {size_px}")
    ha_per_px = (gsd_m ** 2) / 10_000.0
    return {
        "size_px": n,
        "side_m": round(n * gsd_m, 1),
        "area_px": n * n,
        "area_ha": round(n * n * ha_per_px, 3),
        "min_resolvable_ha": round(ha_per_px, 3),
        "min_resolvable_m2": round(gsd_m * gsd_m, 1),
    }


def geometry_memo(*, median_side_px: float = FIELD_SIDE_MEDIAN_PX,
                  max_side_px: float = FIELD_SIDE_MAX_PX) -> dict:
    """The recorded geometry decision (spec: measured, not assumed).

    A window is admissible only when the largest field still fits inside it;
    a 32 px window has 1.63x margin over the largest measured field and is the
    locked default. The 64 px window is 3.27x the median field — nearly all of
    it would be neighbours — so it stays behind an explicit flag.
    """
    margin32 = 32 / max_side_px - 1.0
    margin64 = EXCLUDED_WINDOW / max_side_px - 1.0
    return {
        "median_field_side_px": median_side_px,
        "max_field_side_px": max_side_px,
        "default_window_px": 32,
        "default_window_margin_over_max_field": round(margin32, 3),
        "excluded_window_px": EXCLUDED_WINDOW,
        "excluded_window_ratio_to_median_field": round(EXCLUDED_WINDOW / median_side_px, 2),
        "excluded_window_margin_over_max_field": round(margin64, 3),
        "reason": (
            "a 64 px window is dominated by neighbouring fields and padding for every "
            "measured field; allowing it by default would put the farm-boundary "
            "invariant's geometry beyond what the archive supports"
        ),
        "decision": "32 px default; 64 px only behind an explicit flag",
    }


# ---------------------------------------------------------------------------
# Equal budget
# ---------------------------------------------------------------------------
def capacity_flag(param_counts: dict[str, int], *, tolerance: float = CAPACITY_FLAG) -> dict:
    """Flag representations whose capacity deviates >±tolerance from the median.

    The median is used (not the mean) so one oversized arm cannot redefine the
    band; the flags are informational — the spec requires them next to the
    result, never bans the arm.
    """
    counts = {k: int(v) for k, v in param_counts.items() if v}
    if not counts:
        return {"reference": None, "flags": {}}
    ref = float(np.median(list(counts.values())))
    flags = {
        k: {
            "n_parameters": v,
            "relative_deviation": round((v - ref) / ref, 4),
            "flagged": bool(abs((v - ref) / ref) > tolerance),
        }
        for k, v in counts.items()
    }
    return {"reference": ref, "tolerance": tolerance, "flags": flags}


# ---------------------------------------------------------------------------
# Detectability crossing (paired)
# ---------------------------------------------------------------------------
def sign_test(n_a: int, n_b: int) -> dict:
    """Exact two-sided binomial sign test on the discordant pair counts."""
    n = int(n_a) + int(n_b)
    if n == 0:
        return {"n_discordant": 0, "p_value": 1.0, "favours": None}
    k = min(int(n_a), int(n_b))
    # exact two-sided p: 2 * P(X <= k) with X ~ Bin(n, 0.5), capped at 1
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    p = min(1.0, 2.0 * tail)
    favours = None
    if n_a != n_b:
        favours = "patch" if n_a > n_b else "zonal"
    return {"n_discordant": n, "p_value": round(p, 6), "favours": favours}


def crossing_table(
    patch_detected: dict[str, np.ndarray],   # level_id -> (n,) bool per field-injection
    zonal_detected: dict[str, np.ndarray],
    *,
    wilson_ci=None,
) -> dict:
    """The four-cell detectability table per severity level, paired by injection.

    Both inputs must be aligned: index ``i`` is the SAME injected field-cycle
    for both representations. A length mismatch is a hard error — pairing is
    the point, and a silent zip would compare different populations.
    """
    if wilson_ci is None:
        from ssl_anomaly.monitor.scoring import wilson_ci as _w

        wilson_ci = _w

    out: dict[str, dict] = {}
    for level in sorted(set(patch_detected) & set(zonal_detected)):
        p = np.asarray(patch_detected[level], dtype=bool)
        z = np.asarray(zonal_detected[level], dtype=bool)
        if p.shape != z.shape:
            raise ValueError(
                f"level {level}: patch has {p.size} injections, zonal has {z.size} — "
                "the crossing table is paired and the arrays must be aligned"
            )
        n = int(p.size)
        cells = {
            "patch_only": int(np.sum(p & ~z)),
            "zonal_only": int(np.sum(~p & z)),
            "both": int(np.sum(p & z)),
            "neither": int(np.sum(~p & ~z)),
        }
        rate_p = float(p.mean()) if n else float("nan")
        rate_z = float(z.mean()) if n else float("nan")
        out[level] = {
            "n": n,
            **cells,
            "patch_rate": rate_p,
            "zonal_rate": rate_z,
            "patch_rate_ci95": list(wilson_ci(int(p.sum()), n)) if n else [np.nan, np.nan],
            "zonal_rate_ci95": list(wilson_ci(int(z.sum()), n)) if n else [np.nan, np.nan],
            "paired": sign_test(cells["patch_only"], cells["zonal_only"]),
        }
    return out


# ---------------------------------------------------------------------------
# Chronicity diagnostics
# ---------------------------------------------------------------------------
def alarm_frequency_diagnostic(
    pixel_paths: np.ndarray,   # (N, T, S, S) per-pixel score paths (NaN absent)
    tau: float,
    in_field: np.ndarray,      # (N, S, S) or (S, S) bool
    *,
    top_q: float = 0.10,
) -> dict:
    """Per-pixel chronicity readout on CLEAN cycles.

    Returns the alarm frequency per pixel (share of observed bins above τ), the
    Jaccard overlap between successive cycles' top-q pixel sets, and the
    normalised entropy of the alarm-count distribution. A field whose pixels
    alarm in most cycles, with high successive overlap, is reporting a static
    pattern — this is the measurement the spec asks for, not a heuristic.
    """
    p = np.asarray(pixel_paths, dtype=np.float64)
    if p.ndim != 4:
        raise ValueError(f"pixel_paths must be (N, T, S, S), got {p.shape}")
    N, T, S, _ = p.shape
    infield = np.asarray(in_field, dtype=bool)
    if infield.ndim == 2:
        infield = np.broadcast_to(infield[None], (N, S, S))

    freq = np.full((N, S, S), np.nan)
    for n in range(N):
        obs = np.isfinite(p[n]) & infield[n][None]
        cnt = obs.sum(axis=0)
        alarms = (p[n] > tau) & obs
        with np.errstate(invalid="ignore", divide="ignore"):
            freq[n] = np.where(cnt > 0, alarms.sum(axis=0) / np.maximum(cnt, 1), np.nan)

    overlaps: list[float] = []
    for n in range(N - 1):
        a = _top_mask(p[n], infield[n], top_q)
        b = _top_mask(p[n + 1], infield[n + 1], top_q)
        union = int((a | b).sum())
        overlaps.append(float((a & b).sum() / union) if union else float("nan"))

    per_field = []
    for n in range(N):
        f = freq[n][infield[n]]
        f = f[np.isfinite(f)]
        counts = f * T
        per_field.append({
            "n_pixels": int(f.size),
            "share_pixels_alarming_in_most_bins": float(np.mean(f >= 0.5)) if f.size else float("nan"),
            "mean_alarm_frequency": float(np.mean(f)) if f.size else float("nan"),
            "alarm_count_entropy": _entropy(counts),
        })
    return {
        "per_field": per_field,
        "mean_alarm_frequency": float(np.nanmean([d["mean_alarm_frequency"] for d in per_field]))
        if per_field else float("nan"),
        "mean_successive_topq_jaccard": (float(np.nanmean(overlaps)) if overlaps
                                         else float("nan")),
        "top_q": float(top_q),
        "tau": float(tau),
    }


def _top_mask(path: np.ndarray, infield: np.ndarray, q: float) -> np.ndarray:
    vals = np.where(np.isfinite(path) & infield, path, -np.inf)
    k = max(1, int(np.ceil(q * max(1, int(infield.sum())))))
    # argpartition must only see the in-field entries, or its top-k indices
    # would address the flattened (S,S) grid through a mis-shaped view.
    idx = np.flatnonzero(infield)
    if idx.size == 0:
        return np.zeros_like(infield, dtype=bool)
    sel = vals.ravel()[idx]
    k = min(k, idx.size)
    top = idx[np.argpartition(sel, -k)[-k:]]
    out = np.zeros(infield.size, dtype=bool)
    out[top] = True
    return (out.reshape(infield.shape)) & infield


def _entropy(counts: np.ndarray) -> float:
    c = np.asarray(counts, dtype=np.float64)
    c = c[np.isfinite(c) & (c > 0)]
    if c.size <= 1:
        return 0.0
    p = c / c.sum()
    return float(-(p * np.log(p)).sum() / np.log(c.size))


# ---------------------------------------------------------------------------
# Static-pattern (chronic offset) control
# ---------------------------------------------------------------------------
def static_pattern_normalizer(
    pixel_values: np.ndarray,   # (N_clean, T, S, S) a field's own clean history
    *,
    floor_quantile: float = 5.0,
) -> dict:
    """Per-pixel clean climatology of ONE field (the static-pattern control).

    The per-pixel median across that field's clean cycles is the chronic
    offset; subtracting it asks "is this pixel anomalous FOR THIS PIXEL", as
    opposed to the population-sigma question. The scale is floored at the
    ``floor_quantile`` percentile of the field's own per-pixel MAD so a
    suspiciously quiet pixel cannot manufacture infinite z scores.
    """
    v = np.asarray(pixel_values, dtype=np.float64)
    if v.ndim != 4:
        raise ValueError(f"pixel_values must be (N, T, S, S), got {v.shape}")
    with np.errstate(all="ignore"):
        med = np.nanmedian(v, axis=(0, 1))                       # (S, S)
        mad = np.nanmedian(np.abs(v - med[None, None]), axis=(0, 1))
    scale = 1.4826 * mad
    pos = scale[np.isfinite(scale) & (scale > 0)]
    floor = float(np.percentile(pos, floor_quantile)) if pos.size else 1.0
    scale = np.where(np.isfinite(scale) & (scale > 0), np.maximum(scale, floor), floor)
    return {
        "median": med,
        "scale": scale,
        "floor": floor,
        "n_clean_cycles": int(v.shape[0]),
        "n_pixels_with_history": int(np.isfinite(med).sum()),
    }


def static_pattern_scores(
    pixel_values: np.ndarray,   # (T, S, S)
    normalizer: dict,
) -> np.ndarray:
    """z² against the field's own clean climatology."""
    v = np.asarray(pixel_values, dtype=np.float64)
    z = (v - normalizer["median"]) / normalizer["scale"]
    return np.where(np.isfinite(v), z * z, np.nan)


# ---------------------------------------------------------------------------
# Noise null + the single table
# ---------------------------------------------------------------------------
def noise_null_gap(mdm_coherent: float, mdm_white: float) -> dict:
    """The coherent-minus-white gap that separates "spatial" from "noise".

    A positive gap means coherent-footprint injections are detected at a lower
    severity than equal-footprint white noise, i.e. the advantage comes from
    spatial coherence rather than from averaging more pixels. The result is a
    DIAGNOSTIC: ``gate_eligible`` is hard-coded False so no caller can promote
    it into a severity gate by accident.
    """
    return {
        "mdm80_coherent": mdm_coherent,
        "mdm80_white": mdm_white,
        "gap": (mdm_white - mdm_coherent),
        "favours_coherence": bool(mdm_white > mdm_coherent),
        "diagnostic_only": True,
        "gate_eligible": False,
        "note": "white-noise MDM80 never enters a severity gate or a censoring decision",
    }


@dataclass
class ComparisonRow:
    """One representation's row in the single transparent table."""

    name: str                     # R0 / R0.5 / R1 / R2 / R3
    arm: str                      # the concrete arm (b1, r05_dist, patch_cnn_gru, ...)
    representation: str           # zonal_mean / zonal_dist / patch / sub_crop / multi_scale
    basis: str                    # farm_local / population_ranked
    n_parameters: int | None = None
    window_px: int | None = None
    mdm80: dict[str, float | str] = field(default_factory=dict)      # shape/index -> level
    localization_auprc: float | None = None
    far_achieved: float | None = None
    epoch_seconds: float | None = None
    peak_ram_mb: float | None = None
    throughput_samples_s: float | None = None
    confound: str | None = None   # stated, never inferred (spec scenario)
    notes: str = ""

    def to_dict(self) -> dict:
        support = spatial_support(self.window_px) if self.window_px else None
        return {
            "name": self.name, "arm": self.arm,
            "representation": self.representation, "basis": self.basis,
            "n_parameters": self.n_parameters, "window_px": self.window_px,
            "spatial_support": support,
            "mdm80": self.mdm80, "localization_auprc": self.localization_auprc,
            "far_achieved": self.far_achieved, "epoch_seconds": self.epoch_seconds,
            "peak_ram_mb": self.peak_ram_mb,
            "throughput_samples_s": self.throughput_samples_s,
            "confound": self.confound, "notes": self.notes,
        }


def render_comparison_table(rows: list[ComparisonRow], *, shapes: tuple[str, ...]) -> str:
    """ONE table across the four dimensions the spec names.

    Columns: detection quality (MDM80 per shape/index), spatial sensitivity
    (localization AUPRC + support), temporal consistency (MDM80 stability is
    read from the per-shape spread), computational efficiency (epoch time,
    RAM, throughput, params) — plus the basis label and any stated confound.
    """
    heads = [
        "representation", "arm", "basis", "params",
        "support (ha / min)",
        *[f"MDM80 {s}" for s in shapes],
        "loc-AUPRC", "FAR", "epoch s", "peak MB", "samples/s", "confound",
    ]
    lines = ["| " + " | ".join(heads) + " |", "|" + "---|" * len(heads)]

    def _fmt(v, nd=3):
        if v is None or (isinstance(v, float) and not np.isfinite(v)):
            return "—"
        if isinstance(v, str):
            return v
        return f"{v:.{nd}f}" if isinstance(v, float) else str(v)

    for r in rows:
        support = spatial_support(r.window_px) if r.window_px else None
        sup = (f"{support['area_ha']:.1f} / {support['min_resolvable_ha']:.2f}"
               if support else "zonal (field)")
        cells = [
            f"{r.name} {r.representation}", f"`{r.arm}`", r.basis,
            _fmt(r.n_parameters),
            sup,
            *[_fmt(r.mdm80.get(s)) for s in shapes],
            _fmt(r.localization_auprc),
            _fmt(r.far_achieved),
            _fmt(r.epoch_seconds, 1), _fmt(r.peak_ram_mb, 0),
            _fmt(r.throughput_samples_s, 2),
            r.confound or "—",
        ]
        lines.append("| " + " | ".join(cells) + " |")

    counts = {r.name: (r.n_parameters or 0) for r in rows}
    flags = capacity_flag(counts) if any(counts.values()) else {"flags": {}}
    flagged = [k for k, v in flags["flags"].items() if v["flagged"]]
    lines.append("")
    if flagged:
        lines.append(
            f"Capacity flag (>±{int(CAPACITY_FLAG * 100)} % from the median): "
            + ", ".join(flagged)
        )
    lines.append(
        f"Spatial arithmetic: {int(GSD_M)} m GSD ⇒ 1 px = {HA_PER_PX:.2f} ha; a 16x16 crop "
        f"= {spatial_support(16)['side_m']:.0f} m ≈ {spatial_support(16)['area_ha']:.0f} ha; "
        f"median field side {FIELD_SIDE_MEDIAN_PX} px. A {int(GSD_M)} m pixel bounds every "
        "localization claim regardless of model."
    )
    return "\n".join(lines)


__all__ = [
    "CAPACITY_FLAG",
    "EXCLUDED_WINDOW",
    "FIELD_SIDE_MAX_PX",
    "FIELD_SIDE_MEDIAN_PX",
    "GSD_M",
    "HA_PER_PX",
    "REPRESENTATIONS",
    "ComparisonRow",
    "alarm_frequency_diagnostic",
    "capacity_flag",
    "crossing_table",
    "geometry_memo",
    "noise_null_gap",
    "render_comparison_table",
    "sign_test",
    "spatial_support",
    "static_pattern_normalizer",
    "static_pattern_scores",
]
