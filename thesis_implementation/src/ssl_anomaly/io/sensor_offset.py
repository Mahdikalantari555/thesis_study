"""L8/L9 band-offset estimation from near-coincident pairs (task 2.5).

Landsat 8 and Landsat 9 are radiometrically close but not identical, and once
L9 enters the archive a sensor change sits inside the same time series the
anomaly scores are computed on. A field that is normal in every agronomic
sense can therefore drift across the L9 cutover — which the temporal-
generalization cell in ``patch-generalization-suite`` would otherwise report as
"temporal degradation".

This module estimates the offset per band from **near-coincident pairs**: one
L8 cycle and one L9 cycle of the SAME field whose acquisition days differ by at
most a few days, so the vegetation between them is (nearly) unchanged and the
difference is dominated by sensor + atmosphere. It is deliberately conservative:

* an offset is only returned when the number of usable pairs clears
  :data:`MIN_PAIRS` — with too few pairs the uncertainty is wider than the
  effect, and applying it would add noise dressed up as calibration;
* the estimate is the MEDIAN difference (Landsat pairs carry cloud/BRDF
  outliers that a mean follows), with the CI from the MAD, and both are
  reported so a reader can see the effect is or is not resolvable;
* an offset whose CI straddles zero is reported as ``resolved=False`` and
  :func:`apply_offsets` REFUSES to apply it unless the caller asks for
  ``allow_unresolved`` explicitly.

Direction convention: an offset is ``median(value_L8 - value_L9)`` expressed in
the units of the reference sensor, so :func:`apply_offsets` converts L8 values
INTO the L9 reference frame by subtracting it. ``REFERENCE_SENSOR`` is L9
because L9 is the sensor the series ends on; converting the older sensor into
the newer frame keeps the most recent data untouched.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MIN_PAIRS = 10               # below this the CI is wider than the effect
MAX_GAP_DAYS = 3             # "near-coincident"; 8-day phasing + cloud gaps
REFERENCE_SENSOR = "L9"
APPLIED_TAG = "sensor_offset_applied"

# Pre-registered acceptance for the applied-vs-not comparison (task 2.5).
# Keeping the offsets must (a) not raise the L8-only alarm rate beyond its
# Wilson CI, and (b) shrink the sensor-era score gap. Neither condition alone
# justifies re-scoring the archive, so both are required.
L8_ONLY_FAR_INCREASE_TOL = 0.0     # no increase permitted at all
MIN_ERA_GAP_REDUCTION_FRAC = 0.25  # must cut the era gap by >= 25 %


@dataclass(frozen=True)
class CycleRef:
    """One cycle of one field, with what the pair search needs."""

    field_id: int
    cycle_id: int
    day: int
    sensor: str          # "L8" / "L9"


@dataclass
class BandOffset:
    band: str
    offset: float                    # median(L8 - L9)
    ci_low: float
    ci_high: float
    n_pairs: int
    mad: float
    resolved: bool                   # CI excludes zero
    sigma: float = 0.0               # robust sigma = 1.4826 * MAD

    def to_dict(self) -> dict:
        return {
            "band": self.band, "offset": round(self.offset, 5),
            "ci_low": round(self.ci_low, 5), "ci_high": round(self.ci_high, 5),
            "n_pairs": self.n_pairs, "mad": round(self.mad, 5),
            "robust_sigma": round(self.sigma, 5),
            "resolved": self.resolved,
            "convention": f"median({self.band}_L8 - {self.band}_L9)",
        }


# ---------------------------------------------------------------------------
# Pair search
# ---------------------------------------------------------------------------
def find_pairs(cycles, *, max_gap_days: int = MAX_GAP_DAYS) -> list[tuple[CycleRef, CycleRef]]:
    """Near-coincident cross-sensor pairs, deterministically ordered.

    Pairs are (L8, L9) and only within one field — two fields on the same day
    differ by soil, not by sensor. A cycle appears in at most ONE pair per
    partner day (the closest), so a long L8 cycle is not counted three times
    against three nearby L9 overpasses; that would understate the uncertainty.
    """
    by_field: dict[int, list[CycleRef]] = {}
    for c in cycles:
        by_field.setdefault(c.field_id, []).append(c)

    pairs: list[tuple[CycleRef, CycleRef]] = []
    for fid in sorted(by_field):
        groups = by_field[fid]
        l8 = [c for c in groups if c.sensor == "L8"]
        l9 = [c for c in groups if c.sensor == "L9"]
        for a in l8:
            best = None
            for b in l9:
                gap = abs(a.day - b.day)
                if gap > max_gap_days:
                    continue
                key = (gap, b.day, b.cycle_id)
                if best is None or key < best[0]:
                    best = (key, b)
            if best is not None:
                pairs.append((a, best[1]))
    return sorted(pairs, key=lambda p: (p[0].field_id, p[0].day, p[1].day))


# ---------------------------------------------------------------------------
# Estimation
# ---------------------------------------------------------------------------
def _robust_ci(diffs: np.ndarray) -> tuple[float, float, float]:
    """Median difference with a MAD-derived 95 % CI (normal-theory on sigma)."""
    med = float(np.median(diffs))
    mad = float(np.median(np.abs(diffs - med)))
    sigma = 1.4826 * mad
    se = sigma / np.sqrt(max(1, diffs.size))
    return med, med - 1.96 * se, med + 1.96 * se, sigma


def band_offset(band: str, diffs, *, min_pairs: int = MIN_PAIRS) -> BandOffset:
    """One band's offset from its per-pair differences (L8 minus L9)."""
    d = np.asarray([x for x in np.asarray(diffs, dtype=float).ravel() if np.isfinite(x)])
    if d.size == 0:
        raise ValueError(f"band {band}: no finite pair differences")
    med, lo, hi, sigma = _robust_ci(d)
    return BandOffset(
        band=band, offset=med, ci_low=lo, ci_high=hi, n_pairs=int(d.size),
        mad=float(np.median(np.abs(d - med))), sigma=sigma,
        # "resolved" needs BOTH enough pairs and a CI that excludes zero.
        resolved=bool(d.size >= min_pairs and (lo > 0.0 or hi < 0.0)),
    )


def estimate_offsets(
    pairs,
    sample_fn,
    *,
    bands: tuple[str, ...],
    min_pairs: int = MIN_PAIRS,
    in_field_only: bool = True,
    channel_names: tuple[str, ...] | None = None,
) -> dict:
    """Per-band offsets from ``pairs``; ``sample_fn(ref)`` returns the cycle's
    ``(values, valid)`` with ``values`` shaped ``(C, S, S)`` and ``valid`` the
    boolean in-field mask.

    Pixels are pooled per pair as the MEAN over in-field valid pixels, which is
    what the zonal/field-level representation sees; pooling at pixel level
    would let a big field dominate the estimate.

    ``channel_names`` names the channel axis of what ``sample_fn`` returns; it
    defaults to ``bands`` (i.e. "the array rows ARE the requested bands"), which
    is only right when the caller slices the channels itself. A caller passing
    the store's full channel set must say so, or every band would be read off
    the wrong row — an offset for "red" estimated from "blue" and applied
    silently.
    """
    names = tuple(channel_names) if channel_names is not None else tuple(bands)
    missing = [b for b in bands if b not in names]
    if missing:
        raise ValueError(f"bands {missing} are not in the channel axis {names}")
    rows = {b: names.index(b) for b in bands}
    diffs: dict[str, list[float]] = {b: [] for b in bands}
    used = 0
    for a, b in pairs:
        va, ma = sample_fn(a)
        vb, mb = sample_fn(b)
        if va is None or vb is None:
            continue
        va = np.asarray(va, dtype=float)
        vb = np.asarray(vb, dtype=float)
        ma = np.asarray(ma, dtype=bool)
        mb = np.asarray(mb, dtype=bool)
        mask = (ma & mb) if in_field_only else np.ones_like(ma & mb)
        if not mask.any():
            continue
        used += 1
        for band in bands:
            sa = va[rows[band]][mask]
            sb = vb[rows[band]][mask]
            sa = sa[np.isfinite(sa)]
            sb = sb[np.isfinite(sb)]
            if sa.size == 0 or sb.size == 0:
                continue
            diffs[band].append(float(sa.mean() - sb.mean()))

    out: dict[str, dict] = {}
    skipped: list[str] = []
    for band in bands:
        d = diffs[band]
        if len(d) < 2:
            skipped.append(band)
            continue
        out[band] = band_offset(band, d, min_pairs=min_pairs).to_dict()
    return {
        "reference_sensor": REFERENCE_SENSOR,
        "n_pairs_found": len(pairs),
        "n_pairs_used": used,
        "min_pairs": int(min_pairs),
        "bands": out,
        "skipped_bands": skipped,
        "resolved_count": sum(1 for v in out.values() if v["resolved"]),
        "note": (
            "an offset is only resolvable when it clears MIN_PAIRS and its CI "
            "excludes zero; unresolved bands are reported, never applied silently"
        ),
    }


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
def apply_offsets(
    values: np.ndarray,
    sensor: str,
    offsets: dict,
    *,
    bands: tuple[str, ...],
    allow_unresolved: bool = False,
) -> tuple[np.ndarray, dict]:
    """Convert one cycle's values INTO the reference (L9) frame.

    ``values`` is ``(C, ...)``; only finite entries move, so NaN/cloud pixels
    stay NaN and a masked pixel can never acquire a value through calibration.
    Returns the array and a record of what was applied (for the manifest).
    """
    out = np.array(values, dtype=float, copy=True)
    if sensor == REFERENCE_SENSOR:
        return out, {"sensor": sensor, "applied": [], "reason": "already the reference"}

    table = offsets.get("bands", offsets)
    applied: list[str] = []
    refused: list[str] = []
    for i, band in enumerate(bands):
        rec = table.get(band)
        if rec is None:
            refused.append(f"{band}: no estimate")
            continue
        if not rec.get("resolved") and not allow_unresolved:
            refused.append(f"{band}: CI straddles zero (unresolved)")
            continue
        out[i] = np.where(np.isfinite(out[i]), out[i] - float(rec["offset"]), out[i])
        applied.append(band)
    return out, {"sensor": sensor, "applied": applied, "refused": refused,
                 "allow_unresolved": bool(allow_unresolved),
                 "reference_sensor": REFERENCE_SENSOR}


def marks_applied(record: dict) -> dict:
    """The manifest stamp — a run either has this or it does not."""
    return {APPLIED_TAG: True, **record}


# ---------------------------------------------------------------------------
# The applied / not-applied comparison (pre-registered)
# ---------------------------------------------------------------------------
def comparison_plan(*, n_l8_cycles: int, n_l9_cycles: int) -> dict:
    """What the two arms are and how the decision is made, BEFORE seeing them."""
    return {
        "arms": ["offsets_off", "offsets_on"],
        "same_checkpoint": True,
        "same_scoring": True,
        "only_difference": "L8 cycles converted into the L9 frame before scoring",
        "n_l8_cycles": int(n_l8_cycles),
        "n_l9_cycles": int(n_l9_cycles),
        "decision_rule": {
            "keep_offsets_iff": [
                "L8-only field-cycle FAR does not increase "
                f"(tolerance {L8_ONLY_FAR_INCREASE_TOL})",
                "the sensor-era score gap shrinks by at least "
                f"{MIN_ERA_GAP_REDUCTION_FRAC:.0%}",
            ],
            "both_required": True,
            "report_always": [
                "per-band offsets with CIs and pair counts",
                "era-stratified MDM80 (L8 era vs L9 era) for each arm",
                "the number of L8 cycles whose score moved",
            ],
        },
    }


def decide_applied(era_gap_off: float, era_gap_on: float, *,
                   l8_far_off: float, l8_far_on: float) -> dict:
    """Apply the pre-registered rule to the two arms' numbers."""
    if era_gap_off <= 0:
        reduction = 0.0
    else:
        reduction = (era_gap_off - era_gap_on) / era_gap_off
    far_ok = (l8_far_on - l8_far_off) <= L8_ONLY_FAR_INCREASE_TOL
    gap_ok = reduction >= MIN_ERA_GAP_REDUCTION_FRAC
    return {
        "keep_offsets": bool(far_ok and gap_ok),
        "era_gap_off": era_gap_off, "era_gap_on": era_gap_on,
        "era_gap_reduction_frac": round(float(reduction), 4),
        "needs_reduction": MIN_ERA_GAP_REDUCTION_FRAC,
        "l8_far_off": l8_far_off, "l8_far_on": l8_far_on,
        "far_ok": bool(far_ok), "gap_ok": bool(gap_ok),
        "reason": (
            "kept: the L8/L9 era gap shrank without new L8-only alarms"
            if far_ok and gap_ok else
            "dropped: " + ", ".join(
                [x for x, ok in (
                    ("L8-only FAR increased", far_ok),
                    ("era gap did not shrink by the required fraction", gap_ok),
                ) if not ok]
            )
        ),
    }


__all__ = [
    "APPLIED_TAG", "L8_ONLY_FAR_INCREASE_TOL", "MAX_GAP_DAYS",
    "MIN_ERA_GAP_REDUCTION_FRAC", "MIN_PAIRS", "REFERENCE_SENSOR", "BandOffset",
    "CycleRef", "apply_offsets", "band_offset", "comparison_plan",
    "decide_applied", "estimate_offsets", "find_pairs", "marks_applied",
]
