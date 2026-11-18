"""Training-set contamination + the A_patch absorption statistic.

Change ``patch-contamination-absorption``. The question: if a fraction of the
training cycles carry an undetected stress (the realistic situation — labels
are unavailable), does the model start RECONSTRUCTING that stress instead of
flagging it? The aerial-MIM literature predicts "extended anomalies get
reconstructed"; this module is how that prediction is measured rather than
assumed.

Three pieces:

1. :func:`select_contaminated_cycles` — which train field-cycles get the
   injection. Seed-fixed, exact fraction, and it refuses to touch a field the
   holdout manifest excludes. The returned ids go into the run manifest so the
   contamination is reproducible and auditable.
2. :func:`contaminate_dataset` — the S4 persistent ndvi profile from the frozen
   severity table, applied through the SHARED field-level applier, so the
   contamination is the same physical perturbation the evaluation uses.
3. :func:`absorption_a` / :func:`absorption_bootstrap` — A_patch, the fraction
   of the injected signal that survives into the model's output. A = 1 means
   the anomaly is fully passed through (the model is a good detector); A → 0
   means it is reconstructed away (absorption). The bootstrap CI is over
   injected cycles, because the cycles — not the pixels — are the independent
   unit.

Curation (``--curation``) is a two-phase run: score every train cycle with the
epoch-1 model, drop the top-2 %, retrain. :func:`curation_select` does the
selection deterministically and records the removed ids.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ssl_anomaly.monitor.perturbations import (
    CH_NDVI,
    inject_index_drop,
)
from ssl_anomaly.monitor.severity_table import (
    PERSISTENT_DURATION_BINS,
    PERSISTENT_FAMILY,
    SEVERITY_TABLE,
)

# The pre-registered contamination level: S4 persistent — the strongest level
# that is still plausibly "undetected" at the operating point (S5/S6 are
# detected by every arm and would make the experiment trivial).
CONTAMINATION_LEVEL = "S4"
CONTAMINATION_FAMILY = PERSISTENT_FAMILY
CONTAMINATION_INDEX = "ndvi"

# Curation removes this share of the worst-scoring train cycles.
CURATION_TOP_FRAC = 0.02


def select_contaminated_cycles(
    cycle_keys: list[str],
    *,
    fraction: float,
    seed: int,
    excluded_fields: set[int] | None = None,
) -> list[str]:
    """Pick ``round(fraction · n)`` cycles, seed-fixed, holdout-safe.

    ``excluded_fields`` is the holdout set (or any other exclusion); a cycle
    whose field is excluded can never be selected, so contamination cannot
    become a back door into the holdout.
    """
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"contamination fraction must be in [0, 1], got {fraction}")
    keys = [k for k in cycle_keys if _field_of(k) not in (excluded_fields or set())]
    n = int(round(fraction * len(cycle_keys)))
    if n == 0:
        return []
    if n > len(keys):
        raise ValueError(
            f"cannot contaminate {n} of {len(cycle_keys)} cycles: only {len(keys)} "
            "are eligible after the holdout exclusion"
        )
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(keys), size=n, replace=False)
    return sorted(keys[int(i)] for i in pick)


def _field_of(key: str) -> int:
    """Field id from a ``"<field>:<cycle>"`` key (or a bare int string)."""
    head = str(key).split(":")[0]
    try:
        return int(head)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"cycle key {key!r} does not start with a field id") from exc


def plan_contamination(
    rows: list[int],
    *,
    seed: int = 0,
    level_id: str = CONTAMINATION_LEVEL,
    phase_bins: tuple[int, int] = (1, 35),
    value_scale: float = 1.0,
) -> dict[int, dict]:
    """Decide each contaminated row's onset WITHOUT touching any values.

    ``value_scale`` is the raw→model value divisor (the frozen per-channel IQR
    for patch arms, whose tensors are standardized). Keeping it in the plan
    means the manifest states the injected magnitude in BOTH units.

    Separating the plan from the application lets the training loop apply the
    contamination per sample (the Dataset is lazy) while the run manifest
    records exactly the same plan. One definition, two consumers — so the
    manifest can never describe a different injection than the one trained on.
    """
    rng = np.random.default_rng(seed)
    delta = {lv.level_id: lv.delta_ndvi for lv in SEVERITY_TABLE}[level_id]
    plan: dict[int, dict] = {}
    for i in rows:
        onset = int(rng.integers(phase_bins[0], max(phase_bins[0] + 1, phase_bins[1])))
        plan[int(i)] = {
            "row": int(i), "onset_bin": onset, "level_id": level_id,
            "delta": float(delta), "family": CONTAMINATION_FAMILY,
            "index": CONTAMINATION_INDEX,
            "n_bins_window": PERSISTENT_DURATION_BINS,
            "value_scale": float(value_scale),
        }
    return plan


def contaminate_dataset(
    X: np.ndarray,           # (N, T, C) values
    M: np.ndarray,           # (N, T, C) mask
    indices: list[int],      # rows to contaminate
    *,
    level_id: str = CONTAMINATION_LEVEL,
    rng: np.random.Generator | None = None,
    phase_bins: tuple[int, int] = (1, 35),
) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Apply the S4-persistent ndvi drop to the selected rows.

    The onset is drawn inside ``phase_bins`` so the contamination is not
    always planted at the same phenological point; the exact bin is recorded
    per injection (a contamination that always lands mid-season would test a
    much narrower question).
    """
    plan = plan_contamination(
        list(indices), seed=0 if rng is None else int(rng.integers(0, 2**31 - 1)),
        level_id=level_id, phase_bins=phase_bins,
    )
    out = np.array(X, copy=True)
    meta: list[dict] = []
    for i in indices:
        rec = plan[int(i)]
        res = inject_index_drop(
            out[int(i)], M[int(i)], index=CONTAMINATION_INDEX,
            onset_bin=rec["onset_bin"], duration=rec["n_bins_window"],
            delta=rec["delta"], family=rec["family"],
        )
        out[int(i)] = res.x
        meta.append(dict(rec))
    return out, np.array(M, copy=True), meta


# ---------------------------------------------------------------------------
# A_patch: the absorption statistic
# ---------------------------------------------------------------------------
def absorption_a(
    pred_clean: np.ndarray,   # (T, C) model output for the CLEAN cycle
    pred_cont: np.ndarray,    # (T, C) model output for the CONTAMINATED cycle
    x_clean: np.ndarray,      # (T, C) truth, clean
    x_cont: np.ndarray,       # (T, C) truth, contaminated
    mask: np.ndarray,         # (T, C) observation mask
    *,
    onset: int,
    channel: int = CH_NDVI,
) -> dict:
    """A_patch = how much of the injected shift the model's output keeps.

        injected  = x_cont − x_clean          (negative for a drop)
        passed    = pred_cont − pred_clean    (what the model reproduces)
        A         = passed / injected         (per bin, after onset)

    A ≈ 1 → the model predicts the ORIGINAL (clean) state and the residual
    carries the full anomaly (a detector). A ≈ 0 → the model has learned to
    predict the CONTAMINATED state, so the anomaly vanishes into the
    reconstruction (absorption — the failure the experiment looks for).

    Only the onset window is used, and only bins observed in both cycles; the
    ratio is a mean of per-bin ratios weighted by |injected|, so a bin where
    nothing was injected cannot dominate.
    """
    inj = (x_cont[:, channel] - x_clean[:, channel]).astype(np.float64)
    passed = (pred_cont[:, channel] - pred_clean[:, channel]).astype(np.float64)
    ok = mask[:, channel].astype(bool) & np.isfinite(inj) & np.isfinite(passed)
    ok[: int(onset)] = False
    ok[np.abs(inj) < 1e-6] = False
    if not ok.any():
        return {"usable": False, "reason": "no observed post-onset bin with an injected shift"}
    w = np.abs(inj[ok])
    ratios = passed[ok] / inj[ok]
    a = float(np.sum(ratios * w) / np.sum(w))
    return {
        "usable": True,
        "a_patch": a,
        "n_bins": int(ok.sum()),
        "mean_injected": float(np.mean(inj[ok])),
        "mean_passed": float(np.mean(passed[ok])),
        "share_absorbed": float(1.0 - a),
    }


def absorption_bootstrap(
    per_cycle_a: list[float],
    *,
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 0,
) -> dict:
    """Bootstrap CI for A_patch, resampling CYCLES (the independent unit)."""
    vals = np.asarray([v for v in per_cycle_a if np.isfinite(v)], dtype=np.float64)
    if vals.size == 0:
        return {"mean": float("nan"), "ci95": [float("nan")] * 2, "n_cycles": 0}
    if vals.size == 1:
        return {"mean": float(vals[0]), "ci95": [float("nan")] * 2, "n_cycles": 1}
    rng = np.random.default_rng(seed)
    boots = np.array([
        np.mean(rng.choice(vals, size=vals.size, replace=True)) for _ in range(int(n_boot))
    ])
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {
        "mean": float(np.mean(vals)),
        "ci95": [float(lo), float(hi)],
        "n_cycles": int(vals.size),
        "n_boot": int(n_boot),
        "excludes_zero": bool(lo > 0 or hi < 0),
    }


# ---------------------------------------------------------------------------
# Curation
# ---------------------------------------------------------------------------
@dataclass
class CurationSelection:
    keep: list[int]
    removed: list[int]
    threshold: float
    frac: float

    def to_dict(self) -> dict:
        return {
            "n_keep": len(self.keep), "n_removed": len(self.removed),
            "threshold": float(self.threshold), "frac": float(self.frac),
            "removed_ids": list(self.removed),
        }


def curation_select(
    scores: np.ndarray,       # (N,) per-cycle training loss / residual scale
    *,
    top_frac: float = CURATION_TOP_FRAC,
) -> CurationSelection:
    """Two-phase curation: drop the worst ``top_frac`` of train cycles.

    Deterministic given the scores (ties broken by ascending row index, so the
    outcome never depends on the sort implementation), and the removed ids are
    returned so the manifest records exactly what the second phase did not see.
    """
    s = np.asarray(scores, dtype=np.float64).ravel()
    n = s.size
    if n == 0:
        return CurationSelection([], [], float("nan"), float(top_frac))
    k = int(round(top_frac * n))
    order = np.argsort(-s, kind="stable")     # worst first, ties by index
    removed = sorted(int(i) for i in order[:k])
    keep = sorted(int(i) for i in range(n) if i not in set(removed))
    thr = float(s[order[k - 1]]) if k else float("nan")
    return CurationSelection(keep, removed, thr, float(top_frac))


def contamination_config(fraction: float, *, trimmed: bool, curation: bool) -> dict:
    """The contamination axes that MUST be covered by the resume config hash."""
    return {
        "contaminate_fraction": float(fraction),
        "trimmed_loss": bool(trimmed),
        "curation": bool(curation),
    }


__all__ = [
    "CONTAMINATION_FAMILY",
    "CONTAMINATION_INDEX",
    "CONTAMINATION_LEVEL",
    "CURATION_TOP_FRAC",
    "CurationSelection",
    "absorption_a",
    "absorption_bootstrap",
    "contaminate_dataset",
    "contamination_config",
    "curation_select",
    "plan_contamination",
    "select_contaminated_cycles",
]
