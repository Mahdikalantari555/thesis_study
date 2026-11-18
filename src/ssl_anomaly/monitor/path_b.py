"""Path-B anomaly families: relational breaks and phenology-shape warps.

Change ``anomaly-definition-path-b`` tasks 1.1-1.4. This module is
**verdict-independent machinery**: it defines and applies the families, and
touches no arm and no report. Evaluating them (§2) is hard-gated on both
path-C gates failing, and :func:`require_path_c_failure` is the gate file that
enforces it.

Why new families at all: an absolute NDVI drop is the one anomaly shape a
pixel-wise autoencoder can learn to expect from the marginal distribution
alone. The families here are chosen to be *relational* or *shape* anomalies —
invisible in any single-bin marginal, visible only if the model represents the
dependence between bands or the shape of a season:

* **Relational (1.1/1.2)** — a phenophase-binned robust relation model
  (``NDVI→LST``, ``swir1|NDVI``) fitted on TRAIN cycles only and frozen with a
  hash. An anomaly is a departure from the FITTED RELATION at severity
  ``k × MAD`` of the relation residual: the NDVI drop with LST held (or
  ε-lowered by ≤ 0.5 K, so the pair stays physical), or a swir1 shift along
  the relation-violating direction with NDVI fixed. Both marginals stay
  in-distribution; only the joint does not.
* **Shape (1.3)** — a temporal warp of the field-cycle's own series
  (green-up delay {2,4} bins, grand-growth compression {20,40}%, early
  senescence {2,4} bins), clipped to the admitted bins and carrying the
  covariates the warp implies. The warp moves values ACROSS bins, so a model
  that only learns per-bin marginals sees values it has seen before.

Vocabulary discipline (design risk note): these are departures from learned
relations/shapes, NOT validated stress. Nothing here names stress, and the
injection records keep the anomaly wording for the report layer to enforce.

Both field-level ``(T, C)`` and patch-tensor ``(T, C, S, S)`` appliers are
provided; they share the relation model and the severity conversion, so a
relational anomaly means the same thing at both representations.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import numpy as np

# Relation pairs the change names: (response, predictor).
RELATION_PAIRS: tuple[tuple[str, str], ...] = (("lst", "ndvi"), ("swir1", "ndvi"))

# Severity ladder in units of the relation-residual MAD. The S-naming is kept
# only for table compatibility next to the index-drop ladder; every record is
# labelled "relational" so the two are never silently pooled.
RELATIONAL_LEVELS: tuple[tuple[str, float], ...] = (
    ("S1", 1.0), ("S2", 2.0), ("S4", 4.0), ("S6", 6.0),
)
# The temperature is never allowed to follow an NDVI drop by more than this:
# a large coupled change is a different (physical) anomaly, not a decoupling.
LST_EPSILON_MAX_K = 0.5

# Phenophase bins for the relation fit (2-bin groups, like the sigma tables).
PHASE_BIN = 2
MIN_FIT_N = 30

# Warp families and their magnitudes.
GREENUP_DELAYS = (2, 4)          # bins
GROWTH_COMPRESSION = (0.20, 0.40)  # fraction of the grand-growth span
SENESCENCE_SHIFTS = (2, 4)       # bins

FAMILY_RELATIONAL = "relational"
FAMILY_SHAPE = "phenology_shape"

# Structural bins that may never be moved by a warp: a warp that pushes the
# season outside the cycle it was segmented from produces a different cycle,
# not a deformed one.
def admitted_bins(n_bins: int, *, burn_in: int = 2) -> np.ndarray:
    return np.arange(int(burn_in), int(n_bins), dtype=np.int64)


# ---------------------------------------------------------------------------
# 1.1 Relation model
# ---------------------------------------------------------------------------
@dataclass
class RelationFit:
    """Frozen phenophase-binned robust linear fits, one per relation pair."""

    pairs: dict[str, dict] = field(default_factory=dict)
    sha256: str = ""
    n_cycles: int = 0
    fitted_on: str = "train cycles only"

    def group_of(self, bin_idx: int) -> int:
        return int(bin_idx) // PHASE_BIN

    def predict(self, pair: str, bin_idx: int, predictor_value: np.ndarray) -> np.ndarray:
        """Fitted response and its robust residual scale at one bin."""
        rec = self.pairs[pair]
        g = self.group_of(bin_idx)
        slope = rec["slope"][g]
        intercept = rec["intercept"][g]
        scale = rec["scale"][g]
        if not np.isfinite(slope):
            raise ValueError(
                f"relation {pair} has no fit for bin {bin_idx} (group {g}); the "
                "train cycles did not cover it and a fabricated slope would make "
                "the whole family meaningless"
            )
        return slope * np.asarray(predictor_value, dtype=np.float64) + intercept, float(scale)


def _robust_line(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """Theil-Sen slope/intercept and the MAD of the residuals.

    Theil-Sen (median of pairwise slopes) is used rather than OLS because the
    relation has to survive the outliers ON TRAIN cycles — an OLS line would be
    tilted by exactly the anomalous cycles the family is meant to detect.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if x.size < MIN_FIT_N:
        return float("nan"), float("nan"), float("nan")
    n = x.size
    idx = np.linspace(0, n - 1, min(n, 400)).astype(int)   # bounded pairwise cost
    xs, ys = x[idx], y[idx]
    dx = xs[:, None] - xs[None, :]
    dy = ys[:, None] - ys[None, :]
    sel = np.abs(dx) > 1e-9
    slopes = dy[sel] / dx[sel]
    if slopes.size == 0:
        return float("nan"), float("nan"), float("nan")
    slope = float(np.median(slopes))
    intercept = float(np.median(y - slope * x))
    resid = y - (slope * x + intercept)
    scale = 1.4826 * float(np.median(np.abs(resid - np.median(resid))))
    return slope, intercept, max(scale, 1e-6)


def fit_relations(
    X: np.ndarray,        # (N, T, C) raw values
    M: np.ndarray,        # (N, T, C) bool observation mask
    channel_names: tuple[str, ...],
    *,
    pairs: tuple[tuple[str, str], ...] = RELATION_PAIRS,
    phase_bin: int = PHASE_BIN,
) -> RelationFit:
    """Fit and freeze the relation model (caller passes TRAIN cycles only).

    This function cannot know the splits, so the leakage guarantee lives with
    the caller (``train/protocol.select_splits``) — the same division of
    responsibility as ``patches.fit_patch_norm``, and the tests prove that
    excluded cycles cannot move the frozen parameters by construction.
    """
    X = np.asarray(X, dtype=np.float64)
    M = np.asarray(M, dtype=bool)
    N, T, C = X.shape
    names = tuple(channel_names)
    out: dict[str, dict] = {}
    for response, predictor in pairs:
        if response not in names or predictor not in names:
            raise ValueError(
                f"relation {response}<-{predictor} needs both channels; have {names}"
            )
        ri, pi = names.index(response), names.index(predictor)
        G = int(np.ceil(T / phase_bin))
        slope = np.full(G, np.nan)
        intercept = np.full(G, np.nan)
        scale = np.full(G, np.nan)
        count = np.zeros(G, dtype=np.int64)
        for g in range(G):
            lo, hi = g * phase_bin, min(T, (g + 1) * phase_bin)
            if lo >= hi:
                continue
            sel = M[:, lo:hi, ri] & M[:, lo:hi, pi]
            xs = X[:, lo:hi, pi][sel]
            ys = X[:, lo:hi, ri][sel]
            count[g] = xs.size
            s, b, mad = _robust_line(xs, ys)
            slope[g], intercept[g], scale[g] = s, b, mad
        out[f"{response}|{predictor}"] = {
            "slope": slope.tolist(), "intercept": intercept.tolist(),
            "scale": scale.tolist(), "n": count.tolist(),
            "phase_bin": int(phase_bin),
        }
    fit = RelationFit(pairs=out, n_cycles=int(N))
    fit.sha256 = relation_fit_sha256(fit)
    return fit


def relation_fit_sha256(fit: RelationFit) -> str:
    payload = {
        "pairs": {
            k: dict(v.items()) for k, v in fit.pairs.items()
        },
        "phase_bin": PHASE_BIN,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def relation_residual(
    value: np.ndarray, predicted: np.ndarray, scale: float,
) -> float:
    """Residual in MAD units of the frozen relation (the severity unit)."""
    return float((np.asarray(value, dtype=np.float64) - predicted) / max(scale, 1e-9))


# ---------------------------------------------------------------------------
# 1.2 Relational appliers
# ---------------------------------------------------------------------------
@dataclass
class RelationalResult:
    x: np.ndarray
    m: np.ndarray
    onset_bin: int
    pert_type: str
    severity: float
    level_id: str
    pair: str
    meta: dict = field(default_factory=dict)

    def to_hash_record(self) -> dict:
        payload = {
            "pert_type": self.pert_type, "pair": self.pair,
            "severity_mad": round(float(self.severity), 6),
            "onset_bin": int(self.onset_bin), "level_id": self.level_id,
            "duration_bins": self.meta.get("duration_bins"),
        }
        rec = dict(payload)
        rec["sha256"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return rec


def _as_4d(x: np.ndarray) -> tuple[np.ndarray, bool]:
    """Normalize to (T, C, S, S) and report whether the input was field-level.

    ``(T, C)`` is a field cycle (no spatial extent) and ``(T, C, S, S)`` is a
    patch tensor. Note the ndim check: a 2-D input is the FIELD case, not an
    error — an earlier `ndim == 3` test here rejected every field-level call.
    """
    a = np.asarray(x, dtype=np.float64)
    if a.ndim == 2:            # (T, C) field level
        return a[:, :, None, None], True
    if a.ndim == 4:            # (T, C, S, S) patch level
        return a, False
    raise ValueError(f"x must be (T, C) or (T, C, S, S), got {a.shape}")


def inject_relational_break(
    x: np.ndarray,             # (T, C) or (T, C, S, S)
    m: np.ndarray,             # same shape, bool
    fit: RelationFit,
    *,
    pair: str = "lst|ndvi",
    level_id: str = "S4",
    onset_bin: int = 12,
    duration_bins: int = 2,
    lst_epsilon: float = 0.0,
    channel_names: tuple[str, ...] = ("ndvi", "blue", "green", "red", "nir",
                                      "swir1", "swir2", "lst"),
) -> RelationalResult:
    """Break one fitted relation at ``severity × MAD`` — the relational family.

    ``lst|ndvi``: NDVI is dropped so that the fitted NDVI→LST relation is
    violated by ``k`` residual MADs while LST is held (``lst_epsilon=0``) or
    lowered by at most :data:`LST_EPSILON_MAX_K` — the pair stays physically
    plausible, which is the whole point of the family.

    ``swir1|ndvi``: swir1 is shifted along the relation-violating direction
    with NDVI fixed.

    The severity is EXPRESSED in relation-residual MADs and the realized
    deviation is measured back from the perturbed tensor and recorded, so a
    level that could not be reached (clipping, missing observations) is
    visible instead of being assumed.
    """
    levels = dict(RELATIONAL_LEVELS)
    if level_id not in levels:
        raise ValueError(f"unknown relational level {level_id!r}; have {list(levels)}")
    k = levels[level_id]
    arr, field_level = _as_4d(x)
    mask_src = np.asarray(m, dtype=bool)
    mask, _ = _as_4d(mask_src)
    if mask.shape != arr.shape:
        raise ValueError(f"mask shape {mask_src.shape} != values {np.shape(x)}")
    T, C = arr.shape[:2]
    names = tuple(channel_names)
    response, predictor = pair.split("|")
    if "|" not in pair or response not in names or predictor not in names:
        raise ValueError(f"pair {pair!r} must be '<response>|<predictor>' among {names}")
    if lst_epsilon < 0 or lst_epsilon > LST_EPSILON_MAX_K:
        raise ValueError(
            f"lst_epsilon must be within [0, {LST_EPSILON_MAX_K}] K — a larger coupled "
            "change is a different, physical anomaly, not a decoupling"
        )
    out = arr.copy()
    ri, pi = names.index(response), names.index(predictor)
    end = min(T, int(onset_bin) + max(1, int(duration_bins)))
    realized: list[float] = []
    n_skipped = 0

    for b in range(int(onset_bin), end):
        pred, scale = fit.predict(pair, b, out[b, pi])
        if not np.isfinite(pred).all():
            n_skipped += 1
            continue
        resid = out[b, ri] - pred
        shift = k * scale - resid          # push the residual to exactly k·MAD
        if response == "lst":
            # NDVI moves, LST stays: the NDVI change that violates the relation,
            # solved from the fitted slope, and LST held within epsilon.
            slope = fit.pairs[pair]["slope"][fit.group_of(b)]
            if not np.isfinite(slope) or abs(slope) < 1e-9:
                n_skipped += 1
                continue
            d_ndvi = -shift / slope
            obs_p = mask[b, pi]
            out[b, pi] = np.where(obs_p, out[b, pi] + d_ndvi, out[b, pi])
            if lst_epsilon:
                obs_r = mask[b, ri]
                out[b, ri] = np.where(obs_r, out[b, ri] - lst_epsilon, out[b, ri])
            changed = np.abs(d_ndvi)
        else:
            obs_r = mask[b, ri]
            out[b, ri] = np.where(obs_r, out[b, ri] + shift, out[b, ri])
            changed = np.abs(shift)
        if np.any(changed):
            realized.append(float(np.nanmax(changed)))

    # Measured-back deviation, in the same MAD unit the level was declared in.
    achieved = []
    for b in range(int(onset_bin), end):
        pred0, scale = fit.predict(pair, b, arr[b, pi, 0, 0])
        pred1, _ = fit.predict(pair, b, out[b, pi, 0, 0])
        if not np.isfinite(scale):
            continue
        achieved.append(float(np.nanmax(np.abs(
            (out[b, ri, 0, 0] - pred1) - (arr[b, ri, 0, 0] - pred0)) / scale)))
    if field_level:
        out = out[:, :, 0, 0]
        mask = mask[:, :, 0, 0]
    return RelationalResult(
        x=out, m=mask, onset_bin=int(onset_bin),
        pert_type=f"relation_break_{pair}", severity=float(k), level_id=level_id,
        pair=pair,
        meta={
            "family": FAMILY_RELATIONAL, "duration_bins": int(end - onset_bin),
            "n_skipped_bins": n_skipped,
            "realized_shift": realized,
            "achieved_deviation_mad": achieved,
            "target_deviation_mad": float(k),
            "lst_epsilon_k": float(lst_epsilon),
            "severity_unit": "relation_residual_mad",
            "relation_fit_sha256": fit.sha256,
            "wording": "anomaly (departure from a learned relation) — not stress",
        },
    )


# ---------------------------------------------------------------------------
# 1.3 Phenology-shape appliers
# ---------------------------------------------------------------------------
@dataclass
class ShapeResult:
    x: np.ndarray
    m: np.ndarray
    pert_type: str
    family: str
    meta: dict = field(default_factory=dict)

    def to_hash_record(self) -> dict:
        payload = {kk: self.meta.get(kk) for kk in
                   ("pert_type", "shifts", "compression", "n_moved_bins", "anchor_bin")}
        payload["pert_type"] = self.pert_type
        rec = dict(payload)
        rec["sha256"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return rec


def _stage_anchors(x_ndvi: np.ndarray, m_ndvi: np.ndarray) -> dict[str, int]:
    """Green-up onset, grand-growth peak and senescence start from the series.

    Anchors are derived from the OBSERVED NDVI series of this field-cycle
    (never from the population), so the warp is a deformation of this cycle
    rather than a replacement by a population template.
    """
    T = x_ndvi.size
    vals = np.where(m_ndvi, x_ndvi, np.nan)
    if not np.isfinite(vals).any():
        raise ValueError("cannot anchor a warp on a cycle with no observed NDVI")
    peak = int(np.nanargmax(vals))
    obs = np.flatnonzero(np.isfinite(vals))
    lo, hi = int(obs[0]), int(obs[-1])
    span = max(1, hi - lo)
    return {
        "greenup": lo,
        "peak": peak,
        "senescence": min(T - 1, lo + int(round(0.8 * span))),
        "observed_first": lo,
        "observed_last": hi,
    }


def warp_shape(
    x: np.ndarray,            # (T, C) or (T, C, S, S)
    m: np.ndarray,
    *,
    kind: str,                # "greenup_delay" | "growth_compression" | "early_senescence"
    amount: float,
    channel: int = 0,
    burn_in: int = 2,
) -> ShapeResult:
    """Warp the phenology of one cycle along the NDVI channel.

    ``greenup_delay``    — shift the pre-peak rise later by ``amount`` bins.
    ``growth_compression`` — compress the green-up→peak span to
                             ``(1 − amount)`` of its length.
    ``early_senescence`` — move the decline after the peak earlier by
                           ``amount`` bins.

    Mechanics: the affected segment is RESAMPLED onto a shifted bin grid (the
    values that existed are moved, not re-synthesized) and everything outside
    the admitted bins is untouched.

    **The mask is never modified, and a value is only written into a bin where
    the warped channel is actually OBSERVED.** This is deliberately stricter
    than "move the data wherever the warp wants it": writing into an
    unobserved bin would invent an observation, and a missing→present
    transition is trivially detectable — the family would stop measuring
    phenology and start measuring mask bookkeeping. The cost is that a warp
    can be partially realized; ``meta["n_skipped_unobserved"]`` records how
    much of it was, so a weak cell can be recognised as under-injected.
    """
    arr, field_level = _as_4d(x)
    mask_src = np.asarray(m, dtype=bool)
    mask, _ = _as_4d(mask_src)
    if mask.shape != arr.shape:
        raise ValueError(f"mask shape {mask_src.shape} != values {np.shape(x)}")
    T = arr.shape[0]
    adm = admitted_bins(T, burn_in=burn_in)
    anchors = _stage_anchors(arr[:, channel, 0, 0], mask[:, channel, 0, 0])
    out = arr.copy()
    moved = 0
    n_skipped = 0

    def _place(dst: int, src: int) -> bool:
        """Copy bin ``src`` into ``dst`` if ``dst`` is admissible and observed.

        Returns whether the write happened. The mask is read, never written.
        """
        nonlocal moved, n_skipped
        if dst < 0 or dst not in adm:
            n_skipped += 1
            return False
        if not mask[dst, channel].any():
            n_skipped += 1
            return False
        out[dst] = arr[src]
        moved += 1
        return True

    if kind == "greenup_delay":
        src_lo, src_hi = anchors["greenup"], anchors["peak"]
        dst_lo = min(T - 1, src_lo + int(amount))
        dst_hi = min(T - 1, src_hi + int(amount))
        src_lo = int(np.clip(src_lo, adm[0], T - 1))
        seg_idx = np.arange(src_lo, src_hi + 1)
        if seg_idx.size < 2 or dst_lo >= T:
            raise ValueError("green-up segment too short or push outside the cycle")
        target = np.linspace(dst_lo, dst_hi, seg_idx.size).round().astype(int)
        for s, d in zip(seg_idx, target):
            _place(int(d), int(s))
    elif kind == "growth_compression":
        if not (0.0 < amount < 1.0):
            raise ValueError("growth_compression amount must be in (0, 1)")
        lo, peak = anchors["greenup"], anchors["peak"]
        seg_idx = np.arange(lo, peak + 1)
        if seg_idx.size < 3:
            raise ValueError("green-up→peak segment too short to compress")
        n_keep = max(2, int(round(seg_idx.size * (1.0 - amount))))
        keep = np.linspace(0, seg_idx.size - 1, n_keep).round().astype(int)
        target = np.linspace(lo, lo + n_keep - 1, n_keep).round().astype(int)
        # untouched bins in the vacated tail keep their pre-warp content
        for kk, d in zip(keep, target):
            _place(int(d), int(seg_idx[kk]))
    elif kind == "early_senescence":
        sen = anchors["senescence"]
        seg_idx = np.arange(sen, anchors["observed_last"] + 1)
        if seg_idx.size < 2:
            raise ValueError("senescence segment too short")
        shift = int(amount)
        for s in seg_idx:
            _place(int(s) - shift, int(s))
    else:
        raise ValueError(f"unknown shape kind {kind!r}")

    if field_level:
        out = out[:, :, 0, 0]
    return ShapeResult(
        x=out, m=mask_src, pert_type=kind, family=FAMILY_SHAPE,
        meta={
            "kind": kind, "amount": float(amount), "n_moved_bins": int(moved),
            "n_skipped_unobserved": int(n_skipped),
            "anchors": anchors, "anchor_bin": anchors["peak"],
            "admitted_bins": [int(adm[0]), int(adm[-1])],
            "shifts": (int(amount) if kind != "growth_compression" else None),
            "compression": (float(amount) if kind == "growth_compression" else None),
            "covariate_note": "the warp moves values across bins, so cycle-age/DOY "
                              "covariates must be regenerated from the warped series",
            "wording": "anomaly (deformed phenology) — not stress",
        },
    )


def shape_family_table() -> list[dict]:
    """The frozen warp ladder, one record per family member."""
    out = []
    for k in GREENUP_DELAYS:
        out.append({"kind": "greenup_delay", "amount": float(k), "unit": "bins"})
    for c in GROWTH_COMPRESSION:
        out.append({"kind": "growth_compression", "amount": float(c), "unit": "fraction"})
    for k in SENESCENCE_SHIFTS:
        out.append({"kind": "early_senescence", "amount": float(k), "unit": "bins"})
    return out


# ---------------------------------------------------------------------------
# 1.4 The gate file
# ---------------------------------------------------------------------------
GATE_PATH_DEFAULT = "reports/trial_gates/path_c_gates.json"


class PathCGateClosedError(RuntimeError):
    """Raised when path-B evaluation is attempted while its gate is open."""


def require_path_c_failure(
    gates: dict, *, change: str = "anomaly-definition-path-b",
) -> dict:
    """Refuse to run §2 unless BOTH path-C gates are recorded as failed.

    The gate is the whole conditionality mechanism: these families exist as a
    *response* to path-C failing, so running them while path-C still has a
    passing gate would be a fishing expedition presented as pre-registration.
    Fail-closed on missing keys, on an unrecorded value and on any pass.
    """
    if not isinstance(gates, dict) or "gates" not in gates:
        raise PathCGateClosedError(
            f"{change}: no gate file content — the both-gates-failed condition is "
            "not recorded, so §2 may not run"
        )
    rec = gates["gates"]
    results = {}
    for name in ("detection", "generalization"):
        entry = rec.get(name)
        if entry is None:
            raise PathCGateClosedError(f"{change}: gate '{name}' is not recorded")
        verdict = entry.get("verdict") if isinstance(entry, dict) else entry
        if verdict not in ("pass", "fail"):
            raise PathCGateClosedError(
                f"{change}: gate '{name}' has verdict {verdict!r}; only 'pass'/'fail' "
                "are meaningful (an empty slot is not a failure)"
            )
        results[name] = verdict
    if any(v == "pass" for v in results.values()):
        raise PathCGateClosedError(
            f"{change}: path-C gates {results} do not both fail — §2 is closed"
        )
    return {"open": True, "gates": results, "change": change}


def load_gates(path: str = GATE_PATH_DEFAULT) -> dict:
    import json as _json
    from pathlib import Path as _Path

    p = _Path(path)
    if not p.is_file():
        raise PathCGateClosedError(f"gate file not found: {p}")
    return _json.loads(p.read_text(encoding="utf-8"))


def write_gates(path: str, *, detection: str, generalization: str, **extra) -> dict:
    """Record the two verdicts (owner-provided, not inferred by this code)."""
    from pathlib import Path as _Path

    for v in (detection, generalization):
        if v not in ("pass", "fail"):
            raise ValueError(f"verdict must be 'pass' or 'fail', got {v!r}")
    payload = {
        "gates": {"detection": {"verdict": detection},
                  "generalization": {"verdict": generalization}},
        **extra,
    }
    p = _Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


__all__ = [
    "FAMILY_RELATIONAL", "FAMILY_SHAPE", "GATE_PATH_DEFAULT", "GREENUP_DELAYS",
    "GROWTH_COMPRESSION", "LST_EPSILON_MAX_K", "MIN_FIT_N", "PHASE_BIN",
    "RELATIONAL_LEVELS", "RELATION_PAIRS", "SENESCENCE_SHIFTS",
    "PathCGateClosedError", "RelationFit", "RelationalResult", "ShapeResult",
    "admitted_bins", "fit_relations", "inject_relational_break", "load_gates",
    "relation_fit_sha256", "relation_residual", "require_path_c_failure",
    "shape_family_table", "warp_shape", "write_gates",
]
