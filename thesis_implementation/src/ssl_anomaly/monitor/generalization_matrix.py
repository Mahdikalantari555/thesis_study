"""The cells × folds × sensor-era matrix: planning, aggregation, acceptance.

Change ``patch-generalization-suite`` tasks 1.2 (the planner half) and 2.2
(the report shape). The training/eval runs themselves are owner-executed; what
can be built and tested without data is the matrix SKELETON, the runtime
estimate, the resume records and the aggregation + pre-registered acceptance.

Cell definitions (design §"Fold construction"/"Temporal axis"):

* ``spatial_fold_k`` — train on the 8 in-fold blocks, evaluate on the held-out
  block pair.
* ``temporal`` — train before ``dev_temporal_cutoff``, evaluate after it. This
  is a SEPARATE column, never pooled with the spatial folds: the two measure
  different things and averaging them would hide a temporal collapse.
* ``quadrant`` — one held-out block pair AND the late period.

Acceptance (pre-registered, applied verbatim by :func:`apply_acceptance`):

    spread = max − min of per-fold MDM80 across folds
    pass  ⟺ spread ≤ 2·SE(dev estimate)
             AND no fold loses censoring status
             AND the temporal drop is not material (≤ 1 level)

``apply_acceptance`` returns the verdict WITH the numbers that produced it, so
a failing arm names its failing cells. The thresholds are module constants and
changing them changes every recorded verdict — the function body is a
transcription of the design text and nothing else.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import numpy as np

from . import generalization as G

# Pre-registered acceptance constants (design §Acceptance).
MATERIAL_TEMPORAL_DROP_LEVELS = 1.0     # more than one MDM80 level = material
CENSORED_SENTINEL = 7                   # ">S6", ordering only


@dataclass
class MatrixCell:
    """One row of the planned matrix."""

    cell_id: str
    axis: str                     # "spatial_fold" | "temporal" | "quadrant"
    fold_id: int | None
    held_out_blocks: list[int] = field(default_factory=list)
    train_blocks: list[int] = field(default_factory=list)
    n_train_cycles: int | None = None
    n_eval_cycles: int | None = None
    needs_retrain: bool = True
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "cell_id": self.cell_id, "axis": self.axis, "fold_id": self.fold_id,
            "held_out_blocks": list(self.held_out_blocks),
            "train_blocks": list(self.train_blocks),
            "n_train_cycles": self.n_train_cycles,
            "n_eval_cycles": self.n_eval_cycles,
            "needs_retrain": bool(self.needs_retrain),
            "reason": self.reason,
        }


def plan_matrix(
    folds: list[G.Fold],
    *,
    temporal_cutoff_day: int | None = None,
) -> list[MatrixCell]:
    """The full cell list, with the retrain decision per cell.

    A spatial fold ALWAYS needs a retrain (its training set excludes the fold).
    The temporal cell also needs one unless ``temporal_cutoff_day`` shows the
    existing train split already ends before the cutoff — in which case the
    in-block checkpoint can be reused and the cell is marked as such, which is
    what keeps the 15-runs-per-arm cost from becoming 20.
    """
    cells: list[MatrixCell] = []
    for f in folds:
        cells.append(MatrixCell(
            cell_id=f"spatial_fold_{f.fold_id}", axis="spatial_fold",
            fold_id=f.fold_id, held_out_blocks=list(f.blocks),
            train_blocks=list(f.train_blocks),
            needs_retrain=True,
            reason="held-out blocks are excluded from training by construction",
        ))
        cells.append(MatrixCell(
            cell_id=f"quadrant_fold_{f.fold_id}", axis="quadrant",
            fold_id=f.fold_id, held_out_blocks=list(f.blocks),
            train_blocks=list(f.train_blocks),
            needs_retrain=True,
            reason="held-out blocks AND the late period: no existing checkpoint "
                   "satisfies both",
        ))
    cells.append(MatrixCell(
        cell_id="temporal", axis="temporal", fold_id=None,
        held_out_blocks=[], train_blocks=[],
        needs_retrain=temporal_cutoff_day is None,
        reason=("cutoff unknown — assume a retrain"
                if temporal_cutoff_day is None else
                "train cycles end before the cutoff: reuse the in-block checkpoint"),
    ))
    return cells


def cells_sha256(cells: list[MatrixCell]) -> str:
    payload = [c.to_dict() for c in cells]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Cost control
# ---------------------------------------------------------------------------
def estimate_matrix_runtime(
    cells: list[MatrixCell],
    *,
    seconds_per_epoch: float,
    epochs: int,
    seconds_per_eval_cell: float,
    seeds_screening: int = 1,
    seeds_final: int = 3,
    n_arms_screening: int = 6,
    n_arms_final: int = 2,
) -> dict:
    """Total wall time of the matrix, split into screening and final runs.

    The design restricts 3-seed runs to the arms that reach final claims; this
    estimate makes the consequence explicit, so "just run 3 seeds everywhere"
    cannot happen by accident.
    """
    retrain_cells = [c for c in cells if c.needs_retrain]
    reuse_cells = [c for c in cells if not c.needs_retrain]
    train_s = seconds_per_epoch * max(1, int(epochs))
    screen = (len(retrain_cells) * seeds_screening * n_arms_screening * train_s
              + len(cells) * seeds_screening * n_arms_screening * seconds_per_eval_cell)
    final = (len(retrain_cells) * seeds_final * n_arms_final * train_s
             + len(cells) * seeds_final * n_arms_final * seconds_per_eval_cell)
    return {
        "n_cells": len(cells),
        "n_retrain_cells": len(retrain_cells),
        "n_reuse_cells": len(reuse_cells),
        "seconds_per_training_run": round(train_s, 1),
        "screening_seconds": round(screen, 1),
        "final_seconds": round(final, 1),
        "total_hours": round((screen + final) / 3600.0, 2),
        "assumptions": {
            "seeds_screening": seeds_screening, "seeds_final": seeds_final,
            "arms_screening": n_arms_screening, "arms_final": n_arms_final,
        },
    }


# ---------------------------------------------------------------------------
# Resume records
# ---------------------------------------------------------------------------
def cell_artifact_path(report_dir, arm: str, cell_id: str, seed: int):
    from pathlib import Path as _Path
    return _Path(report_dir) / f"{arm}__{cell_id}__seed{seed}.json"


def completed_cells(report_dir) -> set[tuple[str, str, int]]:
    """Which (arm, cell, seed) triples already have an artifact on disk.

    An artifact counts only if it parses AND carries its own hash, so a torn
    write from an interrupted run is re-done instead of being trusted.
    """
    from pathlib import Path as _Path

    out: set[tuple[str, str, int]] = set()
    d = _Path(report_dir)
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*__*__seed*.json")):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not rec.get("sha256") or "cell_id" not in rec or "arm" not in rec:
            continue
        out.add((str(rec["arm"]), str(rec["cell_id"]), int(rec.get("seed", -1))))
    return out


def write_cell_artifact(report_dir, *, arm: str, cell: MatrixCell, seed: int,
                        metrics: dict) -> object:
    from pathlib import Path as _Path

    payload = {
        "arm": arm, "cell_id": cell.cell_id, "axis": cell.axis,
        "fold_id": cell.fold_id, "seed": int(seed),
        "held_out_blocks": list(cell.held_out_blocks),
        "metrics": metrics,
    }
    payload["sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()
    p = cell_artifact_path(report_dir, arm, cell.cell_id, seed)
    _Path(p).parent.mkdir(parents=True, exist_ok=True)
    _Path(p).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Aggregation + acceptance
# ---------------------------------------------------------------------------
def _sentinel(value) -> float:
    """MDM80 label → numeric sentinel (censored '>S6' → CENSORED_SENTINEL)."""
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value)
    if s.startswith(">"):
        return float(CENSORED_SENTINEL)
    try:
        return float(s.lstrip("S"))
    except ValueError:
        return float("nan")


def aggregate_matrix(records: list[dict]) -> dict:
    """cells × folds, with the dev-estimate SE for the acceptance test.

    ``records`` are per-(arm, cell, seed) metric dicts carrying ``arm``,
    ``cell_id``, ``axis``, ``mdm80`` (per family/index) and optionally
    ``sensor_era`` for the stratified columns.
    """
    cells: dict[str, dict] = {}
    for r in records:
        key = f"{r['arm']}::{r['cell_id']}"
        cells.setdefault(key, {"arm": r["arm"], "cell_id": r["cell_id"],
                               "axis": r.get("axis"), "per_seed": [], "by_era": {}})
        cells[key]["per_seed"].append({
            "seed": r.get("seed"),
            "mdm80": {k: _sentinel(v) for k, v in (r.get("mdm80") or {}).items()},
        })
        era = r.get("sensor_era")
        if era:
            cells[key]["by_era"].setdefault(str(era), []).append(
                {k: _sentinel(v) for k, v in (r.get("mdm80") or {}).items()}
            )

    for rec in cells.values():
        vals = [v for seed in rec["per_seed"] for v in seed["mdm80"].values()
                if np.isfinite(v)]
        rec["mean_sentinel"] = float(np.mean(vals)) if vals else float("nan")
        rec["std_sentinel"] = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
        rec["n_seeds"] = len(rec["per_seed"])
    return {
        "cells": cells,
        "by_axis": {
            axis: sorted(k for k, v in cells.items() if v["axis"] == axis)
            for axis in ("spatial_fold", "temporal", "quadrant")
        },
        "by_era": sorted({e for v in cells.values() for e in v["by_era"]}),
    }


def apply_acceptance(
    matrix: dict,
    *,
    arm: str,
    dev_se_sentinel: float,
    in_block_sentinel: float | None = None,
    material_drop_levels: float = MATERIAL_TEMPORAL_DROP_LEVELS,
) -> dict:
    """The pre-registered L3 acceptance, applied verbatim.

    Three conditions, all reported with their numbers:

    1. ``spread = max − min`` of the per-fold sentinel ≤ ``2·SE``.
    2. No fold is CENSORED when the in-block estimate is not (censoring is not
       a number, so it can never be "within spread").
    3. The temporal cell's drop vs the in-block estimate is ≤
       ``material_drop_levels``.

    A missing fold is a FAIL, not a pass: an arm that could not be evaluated in
    every cell has not demonstrated generalization.
    """
    spatial = [k for k, v in matrix["cells"].items()
               if v["axis"] == "spatial_fold" and v["arm"] == arm]
    temporal = [k for k, v in matrix["cells"].items()
                if v["axis"] == "temporal" and v["arm"] == arm]
    if not spatial:
        return {"arm": arm, "pass": False, "reason": "no spatial folds evaluated"}

    per_fold = {matrix["cells"][k]["cell_id"]: matrix["cells"][k]["mean_sentinel"]
                for k in spatial}
    vals = np.array([v for v in per_fold.values() if np.isfinite(v)])
    if vals.size == 0:
        return {"arm": arm, "pass": False, "reason": "no finite fold statistics"}
    spread = float(vals.max() - vals.min())
    cond_spread = bool(spread <= 2.0 * float(dev_se_sentinel))

    censored_folds = [c for c, v in per_fold.items()
                      if np.isfinite(v) and v >= CENSORED_SENTINEL]
    in_block_censored = (in_block_sentinel is not None
                         and in_block_sentinel >= CENSORED_SENTINEL)
    cond_censoring = bool(in_block_censored or not censored_folds)

    cond_temporal = True
    temporal_drop = None
    if temporal and in_block_sentinel is not None:
        t_val = matrix["cells"][temporal[0]]["mean_sentinel"]
        if np.isfinite(t_val):
            temporal_drop = float(t_val - in_block_sentinel)
            cond_temporal = bool(temporal_drop <= material_drop_levels)
    elif not temporal:
        cond_temporal = False

    verdict = {
        "arm": arm,
        "pass": bool(cond_spread and cond_censoring and cond_temporal),
        "spread": spread,
        "spread_limit": 2.0 * float(dev_se_sentinel),
        "per_fold_sentinel": {k: (None if not np.isfinite(v) else float(v))
                              for k, v in per_fold.items()},
        "conditions": {
            "spread_within_2se": cond_spread,
            "no_new_censoring": cond_censoring,
            "temporal_drop_material_ok": cond_temporal,
        },
        "censored_folds": censored_folds,
        "temporal_drop_levels": temporal_drop,
        "material_drop_limit": float(material_drop_levels),
        "failing_cells": [],
    }
    if not cond_spread:
        worst = max(per_fold, key=lambda c: per_fold[c] if np.isfinite(per_fold[c]) else -1)
        best = min(per_fold, key=lambda c: per_fold[c] if np.isfinite(per_fold[c]) else 9e9)
        verdict["failing_cells"] = [worst, best]
    if not cond_censoring:
        verdict["failing_cells"] = sorted(set(verdict["failing_cells"]) | set(censored_folds))
    return verdict


__all__ = [
    "CENSORED_SENTINEL", "MATERIAL_TEMPORAL_DROP_LEVELS", "MatrixCell",
    "aggregate_matrix", "apply_acceptance", "cell_artifact_path", "cells_sha256",
    "completed_cells", "estimate_matrix_runtime", "plan_matrix",
    "write_cell_artifact",
]
