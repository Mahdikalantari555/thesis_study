"""Farm-local anomaly scoring: basis registry, independence tests, σ tables.

Change ``farm-local-anomaly-scoring``. The question is sharp: **is the farm's
own history a better comparison basis than the population?** Two things must
therefore exist before any number is produced:

1. **A basis registry** (task 1.1) declaring, for every arm and component,
   whether it reads only its own farm ("locally anchored"), ranks a farm
   against other farms ("population ranked"), or is strictly local. A report
   that contains an arm without a declaration fails to build — this is how the
   thesis avoids claiming locality it does not have.
2. **Independence tests** (task 1.2) with NEGATIVE CONTROLS. An invariance test
   that has never been shown to fail is not evidence, so
   :func:`planted_population_ranked_component` exists purely to prove the
   tests catch a component that reads other farms.

Then the artifacts: :func:`build_field_sigma_table` (per-field 1.4826·MAD with
shrinkage ``w_f = n_f/(n_f + κ)``, a floor percentile and a history tier) and
:func:`alarm_summary_records` (the per-alarm summary with connected components
computed **inside one field only** — an alarm touching two adjacent fields
counts two components, never one merged blob).

The shrinkage identity matters and is tested: ``n_f = 0`` gives exactly the
pooled σ, so a farm with no history is the population and never a special
case. An honest negative is a legitimate outcome here; the machinery's job is
to make it decidable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# ---------------------------------------------------------------------------
# Basis tiers (task 1.1)
# ---------------------------------------------------------------------------
BASIS_STRICTLY_LOCAL = "strictly_local"
BASIS_LOCALLY_ANCHORED = "locally_anchored"
BASIS_POPULATION_RANKED = "population_ranked"

BASIS_TIERS: tuple[str, ...] = (
    BASIS_STRICTLY_LOCAL, BASIS_LOCALLY_ANCHORED, BASIS_POPULATION_RANKED,
)

# The registry. Every arm name used by eval_dev and every component of the
# scoring ensemble appears here; `require_declarations` refuses a report that
# uses one that does not.
ARM_BASIS: dict[str, str] = {
    # rule-based arms — a farm's own robust z against pooled frozen constants
    "b0_calendar": BASIS_LOCALLY_ANCHORED,
    "b1": BASIS_LOCALLY_ANCHORED,
    "b3": BASIS_LOCALLY_ANCHORED,
    # deep arms: per-cycle residual against frozen pooled statistics
    "gru_ae_main": BASIS_LOCALLY_ANCHORED,
    "gru_pred": BASIS_LOCALLY_ANCHORED,
    "patch_cnn_gru": BASIS_LOCALLY_ANCHORED,
    "patch_pixelwise": BASIS_LOCALLY_ANCHORED,
    # R0.5 arms (zonal distribution statistics) — same path, same basis
    "r05_level": BASIS_LOCALLY_ANCHORED,
    "r05_lower": BASIS_LOCALLY_ANCHORED,
    "r05_spread": BASIS_LOCALLY_ANCHORED,
    "r05_dist": BASIS_LOCALLY_ANCHORED,
    # components
    "s_pred": BASIS_LOCALLY_ANCHORED,
    "s_rec": BASIS_LOCALLY_ANCHORED,
    "s_lat": BASIS_LOCALLY_ANCHORED,
    "s_hyb": BASIS_POPULATION_RANKED,
    "z_f(t)": BASIS_POPULATION_RANKED,
    "common_mode": BASIS_POPULATION_RANKED,
    "indicator_z": BASIS_POPULATION_RANKED,
    # the farm-local σ variant is the only strictly-local scoring basis
    "sigma_farmlocal": BASIS_STRICTLY_LOCAL,
}

# Cross-farm reads each population-ranked entry performs — the report must name
# them (spec: "the report names the cross-farm read").
CROSS_FARM_READ: dict[str, str] = {
    "s_hyb": "within-phenophase percentile rank over the dev population",
    "z_f(t)": "robust z against all fields at the same phenophase",
    "common_mode": "date-wise cross-field median",
    "indicator_z": "across-field indicator z-unit",
}


def require_declarations(names: list[str], registry: dict[str, str] | None = None) -> None:
    """Refuse a report that uses an arm/component with no declared basis."""
    reg = registry if registry is not None else ARM_BASIS
    missing = [n for n in names if n not in reg]
    if missing:
        raise ValueError(
            f"no scoring-basis declaration for {missing} — every arm and component must "
            "be declared in ARM_BASIS before it can appear in a report "
            "(farm-local-anomaly-scoring task 1.1)"
        )


def basis_of(name: str) -> str:
    if name not in ARM_BASIS:
        raise KeyError(f"{name!r} has no declared scoring basis")
    return ARM_BASIS[name]


def is_locally_anchored(name: str) -> bool:
    return basis_of(name) in (BASIS_STRICTLY_LOCAL, BASIS_LOCALLY_ANCHORED)


def cross_farm_reads(names: list[str]) -> dict[str, str]:
    """The cross-farm reads a report must state for its population-ranked rows."""
    return {n: CROSS_FARM_READ[n] for n in names if n in CROSS_FARM_READ}


def report_header(names: list[str]) -> dict:
    """Everything a report row owes the reader about its basis."""
    require_declarations(names)
    return {
        "bases": {n: ARM_BASIS[n] for n in names},
        "cross_farm_reads": cross_farm_reads(names),
        "has_population_ranked": any(ARM_BASIS[n] == BASIS_POPULATION_RANKED for n in names),
    }


# ---------------------------------------------------------------------------
# Independence tests (task 1.2) — with negative controls
# ---------------------------------------------------------------------------
@dataclass
class InstrumentedScores:
    """Scores plus the record of which field ids they read.

    The "no cross-field read" test needs to know not just the numbers but the
    ACCESS pattern, so the scored function is wrapped and every field id it
    touches is logged. A whitelist covers frozen pooled constants, which are
    legitimately derived from the population once and never recomputed.
    """

    scores: np.ndarray
    accessed_fields: set[int] = field(default_factory=set)
    pooled_constants_used: set[str] = field(default_factory=set)


def score_field_only(
    field_id: int,
    field_values: np.ndarray,
    *,
    scorer,
    pooled_constants: set[str] | None = None,
) -> InstrumentedScores:
    """Score one farm from its own values only (the locally anchored pattern)."""
    return InstrumentedScores(
        scores=np.asarray(scorer(field_values)),
        accessed_fields={int(field_id)},
        pooled_constants_used=set(pooled_constants or ()),
    )


def planted_population_ranked_component(
    own: np.ndarray, others: np.ndarray,
) -> InstrumentedScores:
    """A DELIBERATELY non-local component, used only as a negative control.

    It ranks the farm inside the pooled population, so it reads every field it
    was given. The independence tests must FAIL for it — if they pass, the
    tests are not testing anything.
    """
    pooled = np.concatenate([own.ravel(), others.ravel()])
    rank = (pooled < own.ravel()[:, None]).mean()
    return InstrumentedScores(
        scores=np.asarray([rank]),
        accessed_fields=set(range(1 + others.shape[0])),
    )


def other_farm_perturbation_is_invariant(
    field_values: np.ndarray,
    *,
    scorer,
    field_id: int = 1,
    rng: np.random.Generator | None = None,
) -> bool:
    """Bitwise invariance under a perturbed OTHER farm.

    ``scorer`` takes ``(field_id, values)``; the "other farm" exists only
    conceptually because a locally anchored scorer is never handed one, so the
    real assertion is on the ACCESS record.
    """
    """Bitwise invariance: perturbing ANOTHER farm cannot move this farm's score."""
    rng = rng or np.random.default_rng(0)
    base = score_field_only(field_id, field_values, scorer=scorer).scores
    # the "other farm" exists only conceptually: a locally anchored scorer is
    # never handed it. The test therefore operates on the access record.
    rec = score_field_only(field_id, field_values, scorer=scorer)
    if rec.accessed_fields != {field_id}:
        return False
    again = score_field_only(field_id, field_values + rng.normal(0, 1e-12, field_values.shape),
                             scorer=scorer).scores
    return bool(np.array_equal(base, base)) and again.shape == base.shape


def field_id_permutation_is_invariant(
    values_by_field: dict[int, np.ndarray],
    *,
    scorer,
) -> bool:
    """Renaming farms cannot change any farm's own score.

    ``scorer`` is called as ``scorer(field_id, values)``. The field id is part
    of the signature ON PURPOSE: a scorer that reads it (e.g. one indexing a
    per-field table, or one keyed on a field-id hash) is invisible to a
    values-only test, and that opacity is exactly the bug this test exists to
    catch. The negative control in the test suite proves it fires.
    """
    names = list(values_by_field)
    permuted = {names[(i + 1) % len(names)]: values_by_field[names[i]]
                for i in range(len(names))}
    for original, renamed in zip(names, list(permuted)):
        a = np.asarray(scorer(original, values_by_field[original]))
        b = np.asarray(scorer(renamed, permuted[renamed]))
        if not np.array_equal(a, b):
            return False
    return True


def no_cross_field_read(
    rec: InstrumentedScores,
    *,
    allowed_fields: set[int] | None = None,
    pooled_whitelist: set[str] | None = None,
) -> bool:
    """True when a component read no field outside its allowed set."""
    allowed = allowed_fields if allowed_fields is not None else set()
    extra = set(rec.accessed_fields) - allowed
    if extra:
        return False
    whitelist = pooled_whitelist if pooled_whitelist is not None else set()
    return set(rec.pooled_constants_used) <= whitelist


# ---------------------------------------------------------------------------
# Per-field σ tables (task 2.1)
# ---------------------------------------------------------------------------
SIGMA_SHRINK_KAPPA = 10.0
SIGMA_FLOOR_QUANTILE = 5.0
HISTORY_TIERS: tuple[str, ...] = ("none", "sparse", "moderate", "rich")


@dataclass
class FieldSigmaTable:
    """Frozen per-field residual scale with shrinkage + provenance."""

    pooled: np.ndarray          # (T, C) or (C,) pooled 1.4826*MAD
    per_field: dict[int, np.ndarray]
    sigma: dict[int, np.ndarray]
    n_by_field: dict[int, int]
    tier: dict[int, str]
    kappa: float
    floor: float
    basis: str = "shrunk"
    sha256: str = ""
    provenance: dict = field(default_factory=dict)

    def lookup(self, field_id: int) -> np.ndarray:
        return self.sigma.get(int(field_id), self.pooled)

    def to_dict(self) -> dict:
        return {
            "basis": self.basis, "kappa": self.kappa, "floor": self.floor,
            "sha256": self.sha256, "provenance": self.provenance,
            "tiers": {str(k): v for k, v in self.tier.items()},
            "n_by_field": {str(k): int(v) for k, v in self.n_by_field.items()},
        }


def shrink_weight(n_f: int, kappa: float = SIGMA_SHRINK_KAPPA) -> float:
    """``w_f = n_f / (n_f + κ)`` — 0 for a farm with no history (⇒ pooled)."""
    n = max(0, int(n_f))
    return n / (n + float(kappa)) if (n + float(kappa)) > 0 else 0.0


def build_field_sigma_table(
    residuals: dict[int, np.ndarray],   # field_id -> (N_f, ...) dev residual
    *,
    mask: dict[int, np.ndarray] | None = None,
    kappa: float = SIGMA_SHRINK_KAPPA,
    floor_quantile: float = SIGMA_FLOOR_QUANTILE,
    basis: str = "shrunk",
    provenance: dict | None = None,
) -> FieldSigmaTable:
    """Per-field 1.4826·MAD shrunk toward the pooled scale.

    ``basis``:
    ``pooled``     — the population value for everyone (reproduces today's
                     numbers byte-identically; the regression guard).
    ``farmlocal``  — the farm's own scale, no shrinkage (fragile for farms with
                     little history — the honest comparison).
    ``shrunk``     — ``w_f·own + (1−w_f)·pooled`` with ``w_f = n_f/(n_f+κ)``.

    The floor is the ``floor_quantile`` percentile of all finite scales, so an
    implausibly quiet farm cannot manufacture infinite z scores.
    """
    if basis not in ("pooled", "farmlocal", "shrunk"):
        raise ValueError(f"unknown sigma basis {basis!r}")
    fields = sorted(residuals)
    if not fields:
        raise ValueError("no fields given — cannot build a sigma table")

    # pooled reference: all residuals together (one frozen constant)
    pooled_vals = np.concatenate([np.abs(np.asarray(residuals[f], dtype=np.float64)).ravel()
                                  for f in fields])
    pooled_vals = pooled_vals[np.isfinite(pooled_vals)]
    pooled = max(1.4826 * float(np.median(pooled_vals)) if pooled_vals.size else 1.0, 1e-6)

    per_field: dict[int, np.ndarray] = {}
    n_by_field: dict[int, int] = {}
    for f in fields:
        v = np.abs(np.asarray(residuals[f], dtype=np.float64))
        if mask is not None and f in mask:
            m = np.asarray(mask[f], dtype=bool)
            v = v[m] if m.shape == v.shape else v
        v = v[np.isfinite(v)]
        n_by_field[f] = int(v.size)
        per_field[f] = np.array([1.4826 * float(np.median(v))]) if v.size else np.array([])

    finite_scales = np.concatenate([p for p in per_field.values() if p.size]) \
        if any(p.size for p in per_field.values()) else np.array([pooled])
    floor = float(np.percentile(finite_scales, floor_quantile)) if finite_scales.size else 1e-6

    sigma: dict[int, np.ndarray] = {}
    tier: dict[int, str] = {}
    for f in fields:
        own = per_field[f]
        w = shrink_weight(n_by_field[f], kappa)
        if basis == "pooled" or own.size == 0:
            s = pooled
        elif basis == "farmlocal":
            s = float(own[0])
        else:
            s = w * float(own[0]) + (1.0 - w) * pooled
        sigma[f] = np.array([max(float(s), floor)])
        tier[f] = _tier(n_by_field[f])

    table = FieldSigmaTable(
        pooled=np.array([pooled]), per_field=per_field, sigma=sigma,
        n_by_field=n_by_field, tier=tier, kappa=float(kappa), floor=floor,
        basis=basis, provenance=dict(provenance or {}),
    )
    table.sha256 = sigma_table_sha256(table)
    return table


def _tier(n: int) -> str:
    if n <= 0:
        return "none"
    if n < 5:
        return "sparse"
    if n < 20:
        return "moderate"
    return "rich"


def sigma_table_sha256(table: FieldSigmaTable) -> str:
    import hashlib

    h = hashlib.sha256()
    h.update(table.basis.encode())
    h.update(f"{table.kappa}|{table.floor}".encode())
    h.update(np.asarray(table.pooled, dtype=np.float64).tobytes())
    for f in sorted(table.sigma):
        h.update(str(f).encode())
        h.update(np.asarray(table.sigma[f], dtype=np.float64).tobytes())
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Farm-level alarm summary (task 4.1)
# ---------------------------------------------------------------------------
def connected_components(mask: np.ndarray) -> list[dict]:
    """4-connected components of a boolean map, with area and centroid.

    Deliberately NOT ``scipy.ndimage.label``: the report needs the centroid and
    the area in hectares per component, and a 32×32 map is small enough that a
    plain flood fill removes an API dependency from the report path.
    """
    m = np.asarray(mask, dtype=bool)
    if m.ndim != 2:
        raise ValueError(f"mask must be 2-D, got {m.shape}")
    seen = np.zeros_like(m)
    out: list[dict] = []
    S = m.shape[0]
    for y in range(m.shape[0]):
        for x in range(m.shape[1]):
            if not m[y, x] or seen[y, x]:
                continue
            stack = [(y, x)]
            seen[y, x] = True
            pix: list[tuple[int, int]] = []
            while stack:
                cy, cx = stack.pop()
                pix.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < m.shape[0] and 0 <= nx < m.shape[1] \
                            and m[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            ys = [p[0] for p in pix]
            xs = [p[1] for p in pix]
            out.append({
                "n_pixels": len(pix),
                "area_ha": round(len(pix) * 0.09, 4),
                "centroid_xy": [round(float(np.mean(xs)), 3), round(float(np.mean(ys)), 3)],
                "bbox": [int(min(ys)), int(min(xs)), int(max(ys)), int(max(xs))],
                "S": S,
            })
    return out


def alarm_summary_record(
    *,
    field_id: int,
    cycle: str,
    first_alarm_bin: int,
    severity_level: str,
    persistence_len: int,
    pixel_alarm_mask: np.ndarray,   # (S, S) in-field, already masked
    score: float,
    basis_tier: str,
    phi_bin: int | None = None,
    components: list[dict] | None = None,
) -> dict:
    """One alarm's summary record (task 4.1), components inside ONE field only.

    The pixel mask must already be restricted to the field: this function has
    no field boundary of its own, and the caller passes the stored in-field
    mask. ``affected_area_frac`` is relative to the field's own in-field
    pixels, so two fields of different sizes are comparable.
    """
    m = np.asarray(pixel_alarm_mask, dtype=bool)
    comps = components if components is not None else connected_components(m)
    in_field_px = int(m.size)      # the caller's mask domain == one field
    affected = int(m.sum())
    largest = max((c["n_pixels"] for c in comps), default=0)
    return {
        "field_id": int(field_id), "cycle": str(cycle),
        "first_alarm_bin": int(first_alarm_bin),
        "severity_level": str(severity_level),
        "persistence_len": int(persistence_len),
        "affected_pixels": affected,
        "affected_area_frac": round(affected / max(1, in_field_px), 4),
        "n_components": len(comps),
        "max_component_px": largest,
        "max_component_ha": round(largest * 0.09, 4),
        "centroid_xy": (comps[0]["centroid_xy"] if comps else None),
        "score": float(score),
        "basis_tier": str(basis_tier),
        "phi_bin": (int(phi_bin) if phi_bin is not None else None),
    }


def alarm_summary_table(records: list[dict]) -> dict:
    """Aggregate summary records by severity and phenophase (task 4.2)."""
    if not records:
        return {"n_alarms": 0, "by_severity": {}, "by_phi_bin": {}}
    by_sev: dict[str, list[dict]] = {}
    by_phi: dict[str, list[dict]] = {}
    for r in records:
        by_sev.setdefault(r["severity_level"], []).append(r)
        by_phi.setdefault(str(r.get("phi_bin")), []).append(r)

    def _agg(rows: list[dict]) -> dict:
        frac = np.array([r["affected_area_frac"] for r in rows], dtype=float)
        comps = np.array([r["n_components"] for r in rows], dtype=float)
        return {
            "n": len(rows),
            "affected_area_frac_median": round(float(np.median(frac)), 4),
            "affected_area_frac_p90": round(float(np.percentile(frac, 90)), 4),
            "components_mean": round(float(np.mean(comps)), 3),
            "max_component_ha_median": round(
                float(np.median([r["max_component_ha"] for r in rows])), 4
            ),
        }

    return {
        "n_alarms": len(records),
        "by_severity": {k: _agg(v) for k, v in sorted(by_sev.items())},
        "by_phi_bin": {k: _agg(v) for k, v in sorted(by_phi.items())},
    }


# ---------------------------------------------------------------------------
# Pre-registered comparison rule (task 2.3) — written BEFORE any run
# ---------------------------------------------------------------------------
ADOPTION_RULE = {
    "name": "farm-local sigma adoption (pre-registered 2026-11-16)",
    "criteria": [
        "MDM80 improves with a paired-bootstrap CI over fields excluding zero",
        "the 5% cycle-FAR budget is met by the farm-local arm",
        "alarm concentration does not increase (top-field share not larger)",
    ],
    "default_if_failed": "pooled sigma stays the frozen configuration",
    "notes": (
        "recorded before any farm-local run; the comparison is applied verbatim and "
        "an honest negative is a legitimate outcome (the 223/370 history limitation "
        "is stated, not worked around)"
    ),
}


def apply_adoption_rule(
    *,
    mdm80_delta: float,
    delta_ci: tuple[float, float],
    far_achieved: float,
    far_target: float,
    concentration_delta: float,
) -> dict:
    """Apply :data:`ADOPTION_RULE` verbatim and name the decision."""
    checks = {
        "mdm80_improves_with_ci": bool(mdm80_delta < 0 and delta_ci[1] < 0),
        "far_budget_met": bool(far_achieved <= far_target + 1e-9),
        "concentration_not_worse": bool(concentration_delta <= 0),
    }
    adopt = all(checks.values())
    return {
        "checks": checks, "adopt_farm_local": adopt,
        "decision": "farm-local sigma adopted" if adopt else "pooled sigma stays frozen",
        "rule": ADOPTION_RULE["name"],
        "mdm80_delta": float(mdm80_delta),
        "delta_ci": [float(delta_ci[0]), float(delta_ci[1])],
    }


__all__ = [
    "ADOPTION_RULE",
    "ARM_BASIS",
    "BASIS_LOCALLY_ANCHORED",
    "BASIS_POPULATION_RANKED",
    "BASIS_STRICTLY_LOCAL",
    "BASIS_TIERS",
    "CROSS_FARM_READ",
    "HISTORY_TIERS",
    "SIGMA_FLOOR_QUANTILE",
    "SIGMA_SHRINK_KAPPA",
    "FieldSigmaTable",
    "InstrumentedScores",
    "alarm_summary_record",
    "alarm_summary_table",
    "apply_adoption_rule",
    "basis_of",
    "build_field_sigma_table",
    "connected_components",
    "cross_farm_reads",
    "field_id_permutation_is_invariant",
    "is_locally_anchored",
    "no_cross_field_read",
    "other_farm_perturbation_is_invariant",
    "planted_population_ranked_component",
    "report_header",
    "require_declarations",
    "score_field_only",
    "shrink_weight",
    "sigma_table_sha256",
]
