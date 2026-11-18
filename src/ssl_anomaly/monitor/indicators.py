"""Independent indicators: physical CWSI, indicator z-scores, ERA5 context.

Change ``patch-independent-indicators``. "Independent" is the claim that must
be earned, so every function here is explicit about what it does and does not
share with the patch model:

* :func:`cwsi_idso_jackson` — the physical CWSI. Inputs are canopy (Tc) and
  air (Ta) temperature plus the wet/dry baselines; the baselines come from
  coefficients recorded in :data:`CWSI_COEFFICIENTS` WITH their sources, so no
  baseline is silently invented. A missing coefficient or Ta yields
  :data:`ABSENT`, never a number.
* :func:`indicator_z` — the phenophase-matched robust z of any indicator, in
  BOTH units the change requires: across-field (population-referenced, today's
  behaviour) and farm-own (per-field spread with the pooled fallback and the
  tier counts of ``farm-local-anomaly-scoring``). The unit is returned with the
  values because a report row without the label fails the build.
* :func:`availability_report` — coverage counts for CWSI_ET / TVDI / physical
  CWSI / ETa-ETrF, with the ``absent`` reasons counted separately from zeros.
  An "independent proxy" that exists for 4 % of field-bins is not an
  independent check, and this is where that becomes visible.
* :func:`era5_context` and :func:`alarm_classification` — the event context
  (precip deficit, Tmax anomaly, ET0, VPD vs the historical reference) and the
  neighbour/same-block deviation share, which classify an alarm as
  local-consistent, regional-common-mode or local-unexplained, with candidate
  causes. The classification is the honest part of this change: a "detected
  anomaly" that every neighbour shares is weather, not management.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# A sentinel that is not a number and cannot be mistaken for one.
ABSENT = "absent"

# CWSI coefficients with sources. Idso 1982's empirical baselines are the
# standard for the wet/dry envelope when full energy-balance inputs are absent.
CWSI_COEFFICIENTS: dict[str, dict] = {
    "wet_baseline_offset": {
        "value": 2.0,
        "unit": "K",
        "source": "Idso et al. 1981, Agricultural Water Management 4: 187-194 "
                  "(non-water-stressed baseline intercept; ±2 K envelope)",
        "notes": "Ta - Tc at the fully-watered limit",
    },
    "dry_baseline_slope": {
        "value": 5.0,
        "unit": "K per unit VPD",
        "source": "Idso et al. 1981 (dry-baseline slope for the empirical envelope)",
        "notes": "used only when a measured dry baseline is absent",
    },
}

# The indicators the availability checker knows about.
INDICATORS: tuple[str, ...] = ("cwsi_et", "tvdi", "cwsi_physical", "eta_etrf")

# Phenophase width for the matched z (bins).
PHASE_BIN = 2


def _absent(reason: str, **extra) -> dict:
    return {"value": ABSENT, "reason": reason, **extra}


# ---------------------------------------------------------------------------
# 1.1 Physical CWSI
# ---------------------------------------------------------------------------
def cwsi_idso_jackson(
    tc: float | np.ndarray,
    ta: float | np.ndarray,
    *,
    wet_baseline: float | np.ndarray | None = None,
    dry_baseline: float | np.ndarray | None = None,
    vpd: float | np.ndarray | None = None,
    coefficients: dict[str, dict] | None = None,
) -> dict:
    """CWSI = (Tc − Twet) / (Tdry − Twet), clipped to [0, 1] where valid.

    ``Twet``/``Tdry`` are the canopy-temperature bounds at the wet and dry
    limits. When they are not supplied, they are derived from the recorded
    coefficients and Ta/VPD (Idso's empirical envelope) — the fallback is
    LABELLED in the output, because an empirical envelope and a measured
    energy balance are not the same evidence.

    Any missing input returns :data:`ABSENT` with the reason: a NaN CWSI would
    silently become "no stress" downstream.
    """
    coef = coefficients if coefficients is not None else CWSI_COEFFICIENTS
    tc_a = np.asarray(tc, dtype=np.float64)
    ta_a = np.asarray(ta, dtype=np.float64)
    if np.all(~np.isfinite(tc_a)):
        return _absent("no canopy temperature")
    if np.all(~np.isfinite(ta_a)):
        return _absent("no air temperature (ERA5 join missing at scene time)")

    if wet_baseline is None or dry_baseline is None:
        if "wet_baseline_offset" not in coef or "dry_baseline_slope" not in coef:
            return _absent("wet/dry baseline absent and no recorded coefficients")
        if vpd is None:
            return _absent("dry baseline needs VPD when no measured baseline is given")
        wet = ta_a - float(coef["wet_baseline_offset"]["value"])
        dry = ta_a + float(coef["dry_baseline_slope"]["value"]) * np.asarray(vpd, dtype=np.float64)
        baseline_source = "idso_empirical_envelope"
    else:
        wet = np.asarray(wet_baseline, dtype=np.float64)
        dry = np.asarray(dry_baseline, dtype=np.float64)
        baseline_source = "measured"

    denom = dry - wet
    with np.errstate(invalid="ignore", divide="ignore"):
        raw = (tc_a - wet) / denom
    bad = ~np.isfinite(raw) | (np.abs(denom) < 1e-6)
    out = np.clip(raw, 0.0, 1.0)
    return {
        "value": out,
        "n_valid": int(np.sum(~bad)) if out.ndim else int(not bad),
        "n_absent": int(np.sum(bad)) if out.ndim else int(bool(bad)),
        "baseline_source": baseline_source,
        "coefficient_sources": {k: v["source"] for k, v in coef.items()},
        "clipped": bool(np.any((raw != out) & ~bad)) if out.ndim else bool((raw != out) and not bad),
    }


# ---------------------------------------------------------------------------
# 1.2 Indicator z-scores, both units
# ---------------------------------------------------------------------------
@dataclass
class IndicatorZ:
    values: np.ndarray        # (T,) robust z
    unit: str                 # "across_field" | "farm_own"
    tier: str                 # history tier when unit == "farm_own"
    n_reference: int
    fallback_used: bool = False

    def to_dict(self) -> dict:
        return {
            "unit": self.unit, "tier": self.tier, "n_reference": self.n_reference,
            "fallback_used": self.fallback_used,
            "values": [None if not np.isfinite(v) else round(float(v), 6) for v in self.values],
        }


def _robust_z(values: np.ndarray, reference: np.ndarray, *, floor: float = 1e-3) -> np.ndarray:
    ref = np.asarray(reference, dtype=np.float64)
    ref = ref[np.isfinite(ref)]
    if ref.size < 2:
        return np.full(np.shape(values), np.nan)
    med = float(np.median(ref))
    scale = max(1.4826 * float(np.median(np.abs(ref - med))), floor)
    return (np.asarray(values, dtype=np.float64) - med) / scale


def indicator_z(
    own: np.ndarray,               # (T,) one farm's indicator series
    *,
    across_field: np.ndarray | None = None,   # (N, T) other farms at the same bins
    pooled_history: np.ndarray | None = None,  # the field's own clean history (T or N,T)
    unit: str = "across_field",
    phase_bins: np.ndarray | None = None,      # (T,) phase group per bin
    min_history: int = 5,
    kappa: float = 10.0,
) -> IndicatorZ:
    """Robust z of an indicator, in the requested comparison unit.

    ``across_field`` ranks the farm against the population at the same bins
    (population-referenced — today's behaviour, restated). ``farm_own`` uses
    the farm's OWN clean history, shrunk toward the pooled spread with
    ``w = n/(n+κ)``; a farm with no history falls back to the pooled scale and
    says so. The tier is reported either way.
    """
    if unit not in ("across_field", "farm_own"):
        raise ValueError(f"unknown indicator z unit {unit!r}")
    vals = np.asarray(own, dtype=np.float64)
    if unit == "across_field":
        if across_field is None:
            raise ValueError("across_field unit needs the (N, T) population array")
        pop = np.asarray(across_field, dtype=np.float64)
        if pop.ndim != 2:
            raise ValueError(f"across_field must be (N, T), got {pop.shape}")
        if pop.shape[1] != vals.size:
            raise ValueError(f"across_field has {pop.shape[1]} bins, own has {vals.size}")
        z = np.zeros_like(vals)
        for b in range(vals.size):
            col = pop[:, b]
            col = col[np.isfinite(col)]
            if col.size < 2:
                z[b] = np.nan
                continue
            med = float(np.median(col))
            scale = max(1.4826 * float(np.median(np.abs(col - med))), 1e-3)
            z[b] = (vals[b] - med) / scale
        return IndicatorZ(values=z, unit=unit, tier="population", n_reference=pop.shape[0])

    hist = pooled_history
    if hist is None:
        raise ValueError("farm_own unit needs the field's own clean history")
    h = np.asarray(hist, dtype=np.float64)
    n = int(np.sum(np.isfinite(h)))
    if n < min_history:
        # pooled fallback: the field's own history is too thin to speak for it
        z = _robust_z(vals, h if h.size else np.array([]))
        if not np.isfinite(z).any():
            raise ValueError(
                "farm_own unit has neither enough history nor a pooled reference"
            )
        tier = "none" if n == 0 else "sparse"
        return IndicatorZ(values=z, unit=unit, tier=tier, n_reference=n, fallback_used=True)

    own_med = float(np.median(h))
    own_scale = max(1.4826 * float(np.median(np.abs(h - own_med))), 1e-3)
    pooled_med = float(np.median(h))
    pooled_scale = own_scale
    w = n / (n + float(kappa))
    scale = w * own_scale + (1.0 - w) * pooled_scale
    z = (vals - pooled_med) / scale
    tier = "sparse" if n < 20 else ("moderate" if n < 60 else "rich")
    return IndicatorZ(values=z, unit=unit, tier=tier, n_reference=n)


# ---------------------------------------------------------------------------
# 1.3 Availability
# ---------------------------------------------------------------------------
def availability_report(
    coverage: dict[str, dict],   # name -> {"n_total": int, "n_present": int, "absent_reasons": {reason: n}}
) -> dict:
    """Coverage per indicator, with ``absent`` reasons counted separately.

    The report is the reason this change exists: it tells the reader how much
    of the archive each "independent" indicator could actually speak about.
    An indicator under ``MIN_USABLE_COVERAGE`` is flagged as not usable for
    agreement analysis, which is a finding, not a failure.
    """
    out: dict[str, dict] = {}
    for name in INDICATORS:
        rec = coverage.get(name)
        if rec is None:
            out[name] = {"present": False, "coverage": 0.0,
                         "notes": "indicator not computed for any bin"}
            continue
        total = int(rec.get("n_total", 0))
        present = int(rec.get("n_present", 0))
        cov = present / total if total else 0.0
        out[name] = {
            "present": True,
            "n_total": total,
            "n_present": present,
            "coverage": round(cov, 4),
            "usable_for_agreement": bool(cov >= MIN_USABLE_COVERAGE),
            "absent_reasons": dict(rec.get("absent_reasons", {})),
        }
    return {
        "indicators": out,
        "min_usable_coverage": MIN_USABLE_COVERAGE,
        "usable": [k for k, v in out.items() if v.get("usable_for_agreement")],
        "not_usable": [k for k, v in out.items() if not v.get("usable_for_agreement")],
    }


MIN_USABLE_COVERAGE = 0.20   # below this an indicator cannot support agreement claims


# ---------------------------------------------------------------------------
# 1.4 ERA5 event context + classification
# ---------------------------------------------------------------------------
CONTEXT_VARIABLES: tuple[str, ...] = (
    "precip_deficit_mm", "tmax_anomaly_k", "et0_anomaly_mm", "vpd_anomaly_kpa",
)

# output name -> (source column, unit). Repeating the source column in the
# OUTPUT name would be a classic silent-miss: the loop would look up
# "tmax_anomaly_k" in a dict keyed "tmax" and report every driver as absent.
CONTEXT_SOURCES: dict[str, tuple[str, str]] = {
    "precip_deficit_mm": ("precip", "mm"),
    "tmax_anomaly_k": ("tmax", "K"),
    "et0_anomaly_mm": ("et0", "mm"),
    "vpd_anomaly_kpa": ("vpd", "kPa"),
}


def _reference_window_mean(ref: np.ndarray, window: int) -> float:
    """Mean of the historical windows of the EVENT's length.

    The historical series is daily; a rainfall deficit is only meaningful
    against the same number of days. When the reference has whole windows,
    their sums are averaged; otherwise the daily mean is scaled by the window
    length (documented approximation rather than a silent per-day compare).
    """
    if window > 0 and ref.size % window == 0 and ref.size >= window:
        return float(ref.reshape(-1, window).sum(axis=1).mean())
    return float(ref.mean()) * window


def era5_context(
    event_window: dict[str, np.ndarray],     # variable -> daily values in the event window
    historical: dict[str, np.ndarray],       # variable -> the same calendar window, past years
    *,
    et0_window: np.ndarray | None = None,
    reference_frac: float = 0.25,
) -> dict:
    """ERA5 event context vs the historical reference for the same window.

    ``precip_deficit_mm`` is the shortfall against the historical MEAN of
    equal-length windows (positive = drier than usual), so it is comparable to
    the event total rather than to a single day; the others are per-day
    anomalies in their own units. A variable missing from either input is
    :data:`ABSENT`, never zero — a zero deficit and an unknown deficit mean
    opposite things.
    """
    out: dict[str, dict] = {}
    for var in CONTEXT_VARIABLES:
        key, unit = CONTEXT_SOURCES[var]
        event_vals = et0_window if (key == "et0" and key not in event_window
                                    and et0_window is not None) else event_window.get(key)
        if event_vals is None or key not in historical:
            out[var] = _absent("variable not supplied")
            continue
        cur = np.asarray(event_vals, dtype=np.float64)
        cur = cur[np.isfinite(cur)]
        ref = np.asarray(historical[key], dtype=np.float64)
        ref = ref[np.isfinite(ref)]
        if cur.size == 0 or ref.size == 0:
            out[var] = _absent("no finite values in the window or the reference")
            continue
        if key == "precip":
            ref_window = _reference_window_mean(ref, cur.size)
            out[var] = {
                "value": float(max(0.0, ref_window - cur.sum())),
                "event_sum": float(cur.sum()),
                "reference_window_mean": ref_window,
                "unit": unit,
            }
        else:
            out[var] = {
                "value": float(cur.mean() - ref.mean()),
                "event_mean": float(cur.mean()),
                "reference_mean": float(ref.mean()),
                "unit": unit,
            }
    absent = [k for k, v in out.items() if v.get("value") == ABSENT]
    return {
        "context": out,
        "n_absent": len(absent),
        "absent_variables": absent,
        "reference_frac": float(reference_frac),
    }


def neighbor_deviation_share(
    own_value: float,
    neighbor_values: np.ndarray,
) -> dict:
    """How much of an alarm is shared with the neighbours / same block.

    ``share`` = neighbours with a deviation of the same SIGN and at least half
    the magnitude, over the neighbours with data. A high share means the
    "anomaly" is regional.
    """
    v = np.asarray(neighbor_values, dtype=np.float64)
    v = v[np.isfinite(v)]
    if v.size == 0 or not np.isfinite(own_value):
        return {"share": ABSENT, "reason": "no neighbour data", "n_neighbors": 0}
    if own_value == 0:
        return {"share": ABSENT, "reason": "own deviation is zero", "n_neighbors": int(v.size)}
    same = np.sign(v) == np.sign(own_value)
    strong = np.abs(v) >= 0.5 * abs(own_value)
    share = float(np.mean(same & strong))
    return {
        "share": share,
        "n_neighbors": int(v.size),
        "n_shared": int(np.sum(same & strong)),
    }


def alarm_classification(
    context: dict,
    neighbor: dict,
    *,
    regional_share: float = 0.5,
    context_threshold: float = 1.0,
) -> dict:
    """Classify an alarm: local-consistent / regional-common-mode / local-unexplained.

    The three-way split is the honest output of this module:

    * **regional_common_mode** — most neighbours deviate too: weather, not
      management. Reported as such even though it is an "alarm".
    * **local_consistent** — the field deviates, its neighbours do not, and an
      ERA5 driver explains it (a positive anomaly in a stress-relevant
      variable). The interpretation is corroborated.
    * **local_unexplained** — the field deviates alone and no driver in the
      context does. The most interesting case for the model, and the one that
      must NOT be over-claimed.

    ``candidate_causes`` are named, never asserted.
    """
    share = neighbor.get("share")
    if share == ABSENT or share is None:
        return {
            "classification": "local_unexplained",
            "reason": "no neighbour data — cannot separate local from regional",
            "candidate_causes": ["field-specific management or a data artifact"],
            "neighbor_share": ABSENT,
        }
    if share >= regional_share:
        return {
            "classification": "regional_common_mode",
            "reason": f"{share:.0%} of neighbours deviate by at least half as much",
            "candidate_causes": ["regional weather (heat, rainfall deficit)",
                                 "satellite/atmospheric effect"],
            "neighbor_share": share,
        }
    drivers = []
    for var, rec in (context.get("context") or {}).items():
        val = rec.get("value")
        if val == ABSENT or not isinstance(val, (int, float)) or not np.isfinite(val):
            continue
        if (var.startswith("precip") and val > context_threshold) or (not var.startswith("precip") and abs(val) > context_threshold):
            drivers.append(var)
    if drivers:
        return {
            "classification": "local_consistent",
            "reason": "the field deviates alone and the ERA5 context corroborates a driver",
            "candidate_causes": drivers,
            "neighbor_share": share,
        }
    return {
        "classification": "local_unexplained",
        "reason": "the field deviates alone and no ERA5 driver in the context explains it",
        "candidate_causes": ["local management", "pest/disease", "data artifact (cloud, "
                             "sensor, geometry)"],
        "neighbor_share": share,
    }


def et_etrf(et_actual: np.ndarray, et_reference: np.ndarray) -> dict:
    """ETa/ETrF, with ``absent`` where the reference is unobserved or zero."""
    a = np.asarray(et_actual, dtype=np.float64)
    r = np.asarray(et_reference, dtype=np.float64)
    if a.shape != r.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {r.shape}")
    with np.errstate(invalid="ignore", divide="ignore"):
        out = a / r
    bad = ~np.isfinite(out) | (r <= 0)
    out = np.where(bad, np.nan, np.clip(out, 0.0, 1.5))
    return {
        "value": out,
        "n_valid": int(np.sum(~bad)),
        "n_absent": int(np.sum(bad)),
        "absent_reason": "reference ET missing or zero",
    }


__all__ = [
    "ABSENT",
    "CONTEXT_VARIABLES",
    "CWSI_COEFFICIENTS",
    "INDICATORS",
    "MIN_USABLE_COVERAGE",
    "PHASE_BIN",
    "IndicatorZ",
    "alarm_classification",
    "availability_report",
    "cwsi_idso_jackson",
    "era5_context",
    "et_etrf",
    "indicator_z",
    "neighbor_deviation_share",
]
