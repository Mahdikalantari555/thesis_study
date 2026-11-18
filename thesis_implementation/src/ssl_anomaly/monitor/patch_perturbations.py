"""Patch-tensor and gradual-shape injections (task 2.3 + gradual-severity-shape).

Two things live here because they share one invariant — *the field-level and
patch-level protocols must be the same injection*:

1. **Patch-tensor appliers** (``patch-level-controlled-trial`` task 2.3):
   the S1–S6 × {acute, persistent} × {ndvi, savi} ladder applied to a
   (T, C, S, S) patch tensor, with a per-pixel footprint so the extent sweep
   {0.1, 0.3, 0.6, 1.0} and the localization probe (0.3) need no code change,
   plus the pre-registered ``spatial="white"`` diagnostic mode (a random
   in-field pixel subset with the same mean footprint, seed-fixed) used ONLY
   by the noise null and excluded from every severity gate.
2. **Gradual ramps** (``gradual-severity-shape`` tasks 1.1/1.2): the third
   temporal shape — δ·min(1, t/D) over D ∈ {3, 4, 6} bins then held to cycle
   end, for {ndvi, savi}, with the sum-preserving red/nir SAVI solver applied
   per bin at the bin's partial δ.

The field-level ``inject_index_drop`` and the patch applier here are checked
against each other by ``test_patch_perturbations.py``: applying the same
parameters to a patch whose in-field pixels share one value must reproduce the
field-level tensor bin for bin (spec scenario "field-level AND patch-tensor
appliers produce identical per-bin δ profiles"). That equality is the whole
point — otherwise the patch arm's severity numbers are not comparable to
findings 18/22.

Q10 audit note (PatchFinder, arXiv 2506.17657, 2025) motivated the *shape* of
this module rather than a citation: that work shows patch-level models react to
the spatial layout of a stressor, so a single full-footprint injection cannot
separate "sees stress" from "sees area". Hence the extent axis (1) and the
white-noise null, both pre-registered here, both kept out of the primary gates.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ssl_anomaly.monitor.perturbations import (
    CH_NDVI,
    CH_NIR,
    CH_RED,
    NDVI_PHYSICAL_RANGE,
    REFLECTANCE_PHYSICAL_RANGE,
    _solve_savi_drop,
    savi_from_red_nir,
)

# Temporal shapes. ``acute``/``persistent`` are the frozen protocol; ``gradual``
# is the third primary shape; the last two are SECONDARY diagnostics that must
# never enter a primary gate (spec "Secondary shapes stay secondary").
SHAPE_ACUTE = "acute"
SHAPE_PERSISTENT = "persistent"
SHAPE_GRADUAL = "gradual"
SHAPE_PEAK = "peak_disruption"
SHAPE_RECOVERY = "recovery_disruption"

PRIMARY_SHAPES: tuple[str, ...] = (SHAPE_ACUTE, SHAPE_PERSISTENT, SHAPE_GRADUAL)
SECONDARY_SHAPES: tuple[str, ...] = (SHAPE_PEAK, SHAPE_RECOVERY)

# Ramp durations offered by the spec, and the recovery-duration options.
GRADUAL_DURATIONS: tuple[int, ...] = (3, 4, 6)
RECOVERY_HOLD_BINS: tuple[int, ...] = (3, 6)

# Pre-registered extent sweep (task 2.3 / compare-spatial-representation).
FOOTPRINT_PROTOCOL = 1.0      # every primary-gate injection
FOOTPRINT_LOCALIZATION = 0.3  # the localization probe
EXTENT_SWEEP: tuple[float, ...] = (0.1, 0.3, 0.6, 1.0)

SPATIAL_CONTIGUOUS = "contiguous"
SPATIAL_WHITE = "white"        # diagnostic null only — never a gate input


def ramp_profile(duration: int, n_bins: int, onset: int, *, n_steps: int | None = None) -> np.ndarray:
    """δ multipliers per bin: ``min(1, t/D)`` for t = 0..D-1, then 1.0.

    Returns an ``(n_bins,)`` array in [0, 1]. Bins after the ramp are held at
    1.0 (the spec's "then held to cycle end"); bins before onset are 0.
    """
    d = int(duration)
    if d < 1:
        raise ValueError(f"ramp duration must be ≥ 1 bin, got {d}")
    n_steps = int(n_steps if n_steps is not None else n_bins)
    prof = np.zeros(n_steps, dtype=np.float64)
    for t in range(n_steps):
        b = onset + t
        if b < 0 or b >= n_bins:
            continue
        prof[t] = min(1.0, (t + 1) / d)
    return prof


def onset_for_shape(shape: str, n_bins: int, phase_start: int, duration: int) -> int:
    """Onset bin, with the gradual ramp guaranteed to fit inside the cycle.

    For ``gradual`` the onset is pulled earlier when the requested phase left
    too few bins: the spec requires the full ramp to fit, so the honest move is
    to shift the onset (recorded) rather than to truncate the ramp silently.
    """
    if shape != SHAPE_GRADUAL:
        return int(phase_start)
    required = int(duration)
    latest = max(1, n_bins - required)
    return int(min(phase_start, latest))


def footprint_mask(
    in_field: np.ndarray,        # (S, S) bool
    footprint: float,
    *,
    rng: np.random.Generator | None = None,
    spatial: str = SPATIAL_CONTIGUOUS,
    center: tuple[int, int] | None = None,
) -> np.ndarray:
    """Pixels that receive the injection, as a bool (S, S) map.

    ``contiguous``: the in-field pixels nearest a centre (a compact blob,
    deterministic given ``center`` — defaults to the in-field centroid).
    ``white``: a random in-field subset of the same SIZE (same mean footprint,
    no spatial structure) — the diagnostic null, seed-fixed by ``rng``.
    """
    if spatial not in (SPATIAL_CONTIGUOUS, SPATIAL_WHITE):
        raise ValueError(f"unknown spatial mode {spatial!r}")
    m = np.asarray(in_field, dtype=bool)
    n_in = int(m.sum())
    if n_in == 0:
        return np.zeros_like(m)
    n_target = int(max(1, round(float(footprint) * n_in))) if footprint > 0 else 0
    n_target = min(n_target, n_in)
    out = np.zeros_like(m)
    if n_target == 0:
        return out
    if n_target == n_in:
        return m.copy()

    ys, xs = np.nonzero(m)
    if spatial == SPATIAL_WHITE:
        if rng is None:
            raise ValueError("spatial='white' requires a seeded rng (seed-fixed null)")
        sel = rng.choice(n_in, size=n_target, replace=False)
        out[ys[sel], xs[sel]] = True
        return out

    cy, cx = center if center is not None else (float(ys.mean()), float(xs.mean()))
    d2 = (ys - cy) ** 2 + (xs - cx) ** 2
    order = np.argsort(d2, kind="stable")
    out[ys[order[:n_target]], xs[order[:n_target]]] = True
    return out


@dataclass
class PatchInjection:
    """Result of one patch-tensor injection."""

    x: np.ndarray                 # (T, C, S, S) perturbed values
    m: np.ndarray                 # (T, C, S, S) observation mask (unchanged)
    footprint_mask: np.ndarray    # (S, S) pixels touched
    onset_bin: int
    shape: str
    index: str
    severity: float
    duration_bins: int
    meta: dict = field(default_factory=dict)

    @property
    def hash_payload(self) -> dict:
        """The canonical, hashable description of this injection."""
        return {
            "shape": self.shape, "index": self.index,
            "severity": round(float(self.severity), 6),
            "onset_bin": int(self.onset_bin),
            "duration_bins": int(self.duration_bins),
            "n_pixels": int(self.footprint_mask.sum()),
            "spatial": self.meta.get("spatial"),
            "ramp_duration": self.meta.get("ramp_duration"),
            "level_id": self.meta.get("level_id"),
        }

    def to_hash_record(self) -> dict:
        """Canonical record hashed into the injection-set identity."""
        import hashlib
        import json

        payload = self.hash_payload
        blob = json.dumps(payload, sort_keys=True)
        rec = dict(payload)
        rec["sha256"] = hashlib.sha256(blob.encode("utf-8")).hexdigest()
        return rec


def _profile(shape: str, n_bins: int, onset: int, duration: int, *, ramp: int | None) -> np.ndarray:
    """δ multiplier per bin for each temporal shape.

    acute:       1.0 over ``duration`` bins, then 0
    persistent:  1.0 over ``duration`` bins, then 0  (duration differs)
    gradual:     δ·min(1, t/D) then held to cycle end
    """
    prof = np.zeros(n_bins, dtype=np.float64)
    if shape in (SHAPE_ACUTE, SHAPE_PERSISTENT):
        prof[onset: min(n_bins, onset + int(duration))] = 1.0
        return prof
    if shape == SHAPE_GRADUAL:
        d = int(ramp or duration)
        for b in range(onset, n_bins):
            prof[b] = min(1.0, (b - onset + 1) / d)
        return prof
    raise ValueError(f"unsupported shape {shape!r}")


def inject_patch_drop(
    x: np.ndarray,               # (T, C, S, S) values
    m: np.ndarray,               # (T, C, S, S) bool observation mask
    *,
    index: str,
    delta: float,
    onset_bin: int,
    shape: str = SHAPE_ACUTE,
    duration: int = 1,
    in_field: np.ndarray | None = None,
    footprint: float = FOOTPRINT_PROTOCOL,
    spatial: str = SPATIAL_CONTIGUOUS,
    rng: np.random.Generator | None = None,
    ramp_duration: int | None = None,
    level_id: str | None = None,
) -> PatchInjection:
    """Inject one index drop into a patch tensor, per pixel, per bin.

    ``index``: ``"ndvi"`` (channel 0 shifted by −δ·profile(b)) or ``"savi"``
    (the sum-preserving red/nir solver at the bin's partial δ, per pixel —
    never fabricated as a channel). Only observed entries are modified and the
    mask is never changed, exactly like the field-level applier.

    ``in_field`` defaults to "every pixel with any observation", so a caller
    that has already masked the tensor cannot inject outside the field by
    accident; passing the stored ``in_field`` explicitly is preferred.
    """
    if index not in ("ndvi", "savi"):
        raise ValueError(f"unknown index {index!r}")
    T, C, S, _ = x.shape
    if m.shape != x.shape:
        raise ValueError(f"mask shape {m.shape} != values shape {x.shape}")
    values = x.astype(np.float64, copy=True)
    mask = np.asarray(m, dtype=bool)
    if in_field is None:
        in_field = mask.any(axis=(0, 1))
    fm = footprint_mask(in_field, footprint, rng=rng, spatial=spatial)
    onset = onset_for_shape(shape, T, int(onset_bin), int(ramp_duration or duration))
    prof = _profile(shape, T, onset, duration, ramp=ramp_duration)

    realized: list[float] = []
    n_floored = 0
    n_skipped = 0
    n_touched = 0

    if index == "ndvi":
        ch = CH_NDVI
        lo, hi = NDVI_PHYSICAL_RANGE
        for b in range(T):
            mult = prof[b]
            if mult <= 0:
                continue
            sel = mask[b, ch] & fm
            if not sel.any():
                n_skipped += 1
                continue
            target = values[b, ch][sel] - delta * mult
            floored = np.clip(target, lo, hi)
            n_floored += int(np.sum(floored != target))
            n_touched += int(sel.sum())
            values[b, ch][sel] = floored
            realized.append(float(delta * mult))
    else:
        lo_r, hi_r = REFLECTANCE_PHYSICAL_RANGE
        for b in range(T):
            mult = prof[b]
            if mult <= 0:
                continue
            sel = mask[b, CH_RED] & mask[b, CH_NIR] & fm
            if not sel.any():
                n_skipped += 1
                continue
            ys, xs = np.nonzero(sel)
            got: list[float] = []
            for yy, xx in zip(ys, xs):
                solved = _solve_savi_drop(
                    float(values[b, CH_RED, yy, xx]), float(values[b, CH_NIR, yy, xx]),
                    float(delta * mult),
                )
                if solved is None:
                    continue
                red_new, nir_new = solved
                for ch, val in ((CH_RED, red_new), (CH_NIR, nir_new)):
                    f = min(max(val, lo_r), hi_r)
                    if f != val:
                        n_floored += 1
                    values[b, ch, yy, xx] = f
                got.append(float(
                    savi_from_red_nir(x[b, CH_RED, yy, xx], x[b, CH_NIR, yy, xx])
                    - savi_from_red_nir(values[b, CH_RED, yy, xx], values[b, CH_NIR, yy, xx])
                ))
            n_touched += len(got)
            if got:
                realized.append(float(np.mean(got)))

    inj = PatchInjection(
        x=values.astype(x.dtype, copy=False), m=mask, footprint_mask=fm,
        onset_bin=onset, shape=shape, index=index, severity=float(delta),
        duration_bins=int(ramp_duration or duration),
        meta={
            "spatial": spatial, "footprint_requested": float(footprint),
            "footprint_realized": float(fm.sum() / max(1, np.asarray(in_field, bool).sum())),
            "ramp_duration": (int(ramp_duration or duration) if shape == SHAPE_GRADUAL else None),
            "level_id": level_id,
            "profile": [round(float(v), 6) for v in prof],
            "delta_realized_per_active_bin": [round(v, 6) for v in realized],
            "n_bins_touched": int(np.sum(prof > 0)),
            "n_skipped_bins": n_skipped,
            "n_floored_values": n_floored,
            "n_pixel_bins_touched": n_touched,
            "savi_solver": "sum-preserving red/nir solve" if index == "savi" else None,
        },
    )
    return inj


def inject_patch_recovery(
    x: np.ndarray,
    m: np.ndarray,
    *,
    index: str,
    delta: float,
    onset_bin: int,
    drop_bins: int,
    mode: str,
    hold_bins: int = 3,
    in_field: np.ndarray | None = None,
    footprint: float = FOOTPRINT_PROTOCOL,
    level_id: str | None = None,
) -> PatchInjection:
    """SECONDARY diagnostic: failure-to-recover or slow-recovery after a drop.

    ``mode="fail"``: the dropped level is held for ``hold_bins`` more bins.
    ``mode="slow"``: the series ramps back at half the natural slope (i.e. over
    2× ``drop_bins``, capped at cycle end).

    This never enters a primary gate (spec "Secondary shapes stay secondary").
    """
    if mode not in ("fail", "slow"):
        raise ValueError(f"unknown recovery mode {mode!r}")
    T = x.shape[0]
    values = x.astype(np.float64, copy=True)
    mask = np.asarray(m, dtype=bool)
    if in_field is None:
        in_field = mask.any(axis=(0, 1))
    fm = footprint_mask(in_field, footprint)
    prof = np.zeros(T, dtype=np.float64)
    prof[onset_bin: min(T, onset_bin + drop_bins)] = 1.0
    if mode == "fail":
        s = onset_bin + drop_bins
        prof[s: min(T, s + hold_bins)] = 1.0
    else:
        s = onset_bin + drop_bins
        span = max(1, 2 * drop_bins)
        for t in range(T - s):
            prof[s + t] = max(0.0, 1.0 - (t + 1) / span)

    if index == "ndvi":
        lo, hi = NDVI_PHYSICAL_RANGE
        for b in range(T):
            if prof[b] <= 0:
                continue
            sel = mask[b, CH_NDVI] & fm
            if not sel.any():
                continue
            values[b, CH_NDVI][sel] = np.clip(
                values[b, CH_NDVI][sel] - delta * prof[b], lo, hi
            )
    else:
        lo_r, hi_r = REFLECTANCE_PHYSICAL_RANGE
        for b in range(T):
            if prof[b] <= 0:
                continue
            sel = mask[b, CH_RED] & mask[b, CH_NIR] & fm
            for yy, xx in zip(*np.nonzero(sel)):
                solved = _solve_savi_drop(
                    float(values[b, CH_RED, yy, xx]), float(values[b, CH_NIR, yy, xx]),
                    float(delta * prof[b]),
                )
                if solved is None:
                    continue
                red_new, nir_new = solved
                values[b, CH_RED, yy, xx] = min(max(red_new, lo_r), hi_r)
                values[b, CH_NIR, yy, xx] = min(max(nir_new, lo_r), hi_r)

    inj = PatchInjection(
        x=values.astype(x.dtype, copy=False), m=mask, footprint_mask=fm,
        onset_bin=int(onset_bin), shape=SHAPE_RECOVERY, index=index,
        severity=float(delta), duration_bins=int(drop_bins),
        meta={
            "spatial": SPATIAL_CONTIGUOUS, "recovery_mode": mode,
            "hold_bins": int(hold_bins) if mode == "fail" else None,
            "level_id": level_id, "secondary": True,
            "profile": [round(float(v), 6) for v in prof],
        },
    )
    return inj


def injection_set_sha256(injections: list[PatchInjection]) -> str:
    """SHA-256 over the whole injection set (the sidecar's identity)."""
    import hashlib
    import json

    recs = [i.to_hash_record() for i in injections]
    blob = json.dumps(recs, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


__all__ = [
    "EXTENT_SWEEP",
    "FOOTPRINT_LOCALIZATION",
    "FOOTPRINT_PROTOCOL",
    "GRADUAL_DURATIONS",
    "PRIMARY_SHAPES",
    "RECOVERY_HOLD_BINS",
    "SECONDARY_SHAPES",
    "SHAPE_ACUTE",
    "SHAPE_GRADUAL",
    "SHAPE_PEAK",
    "SHAPE_PERSISTENT",
    "SHAPE_RECOVERY",
    "SPATIAL_CONTIGUOUS",
    "SPATIAL_WHITE",
    "PatchInjection",
    "footprint_mask",
    "inject_patch_drop",
    "inject_patch_recovery",
    "injection_set_sha256",
    "onset_for_shape",
    "ramp_profile",
]
