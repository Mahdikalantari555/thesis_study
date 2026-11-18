"""Patch arms inside ``eval_dev.py``: the store→store-free boundary.

Change ``patch-level-controlled-trial`` task 2.4.

`eval_dev.py` is written against FIELD-level cycles — ``(N, T, C)`` arrays in
memory. The patch arms need the ``patches.zarr`` tensors ``(N, T, C, S, S)``
plus their in-field masks. This module is the only place that decides how the
two line up, so the decision is visible and testable instead of being an
ad-hoc branch inside the sweep:

* **The join key is ``(field_id, cycle_id)``, never row position.** A patch
  store and a field-level array can hold the same cycles in different orders;
  joining on position would silently score farm A's patch against farm B's
  cycle, and every downstream metric would look plausible.
* **Missing patch cycles are a hard error, not a dropped sample.** Dropping
  them would change the evaluation population between arms, which is exactly
  the confound the controlled trial exists to remove.
* **The injection is applied in the PATCH tensor** by
  ``monitor/patch_perturbations.py`` with the same severity table, shapes and
  hashes as the field-level ladder — never by re-injecting in field space and
  hoping the patch slice matches.
* **The in-field mask comes from the store**, not from the values: out-of-field
  pixels must never enter the aggregation domain.

The severity sweep consumes a ``score_cycles``-shaped callable, so this module
returns one plus the reference paths needed by ``PatchArmScorer``.
"""

from __future__ import annotations

import numpy as np

from ssl_anomaly.io import patches as P
from ssl_anomaly.train.patch_data import read_cycle_inputs

SENTINEL_ABSENT = "absent"


def patch_batch_for_cycles(
    root,
    field_ids: np.ndarray,
    cycle_ids: np.ndarray,
    *,
    norm: dict,
) -> dict:
    """Join by stable keys and keep raw inputs for physical-unit challenges."""
    epoch = P.patch_epoch(root)
    index = P.patch_cycle_index(root)
    stats = P.patch_norm_stats(norm)
    field_ids = np.asarray(field_ids, dtype=np.int64).ravel()
    cycle_ids = np.asarray(cycle_ids, dtype=np.int64).ravel()
    if field_ids.shape != cycle_ids.shape or not field_ids.size:
        raise ValueError("field_ids and cycle_ids must align and be non-empty")
    keys = [f"{f}:{c}" for f, c in zip(field_ids, cycle_ids)]
    missing = [key for key in keys if key not in index]
    if missing:
        raise ValueError(f"{len(missing)} requested patch cycles are not in the store: {missing[:5]}")
    cycles = [index[key] for key in keys]
    P.assert_patch_count_bounds(root, cycles)
    rows = [read_cycle_inputs(root, cycle, epoch=epoch) for cycle in cycles]
    raw, obs, sensors, in_field, covariates = (
        np.stack([data[key] for data in rows])
        for key in ("raw", "obs", "sensor_id", "in_field", "covariates")
    )
    normalized = [P.normalize_patch(v, m, s, stats) for v, m, s in zip(raw, obs, sensors)]
    x, missing_scales = zip(*normalized)
    return {
        "X": np.stack(x), "unnormalized_channels": sorted(set().union(*missing_scales)), "raw": raw, "obs": obs, "pixel_valid": obs.any(axis=2),
        "in_field": in_field, "sensor_id": sensors, "covariates": covariates,
        "cycles_found": len(keys), "norm_stats": stats,
    }


def _scoring_inputs(batch: dict, rows=slice(None)) -> dict:
    names = {"sensor_ids": "sensor_id", "covariates": "covariates", "obs": "obs"}
    return {kw: batch[key][rows] for kw, key in names.items() if key in batch}


def patch_reference_paths(
    arm_scorer,
    batch: dict,
    *,
    reference_idx: np.ndarray,
    field_row: np.ndarray | None = None,
    chunk: int = 32,
) -> np.ndarray:
    """Clean-calibration paths used by the empirical p-value.

    Restricted to ``reference_idx`` (the CALIBRATION subset). Using the
    evaluation subset as its own reference would make every p-value a rank
    within the set being judged — detection would look perfect and mean
    nothing.
    """
    idx = np.asarray(reference_idx, dtype=np.int64)
    if idx.size == 0:
        raise ValueError("no calibration cycles for the patch arm's reference paths")
    paths = np.full((idx.size, batch["X"].shape[1]), np.nan)
    for n0 in range(0, idx.size, max(1, chunk)):
        sl = idx[n0 : n0 + max(1, chunk)]
        # ``field_row`` names each sample's in-field mask row; it is required
        # when the batch is a SLICE of a larger field table (the evaluation
        # sweep always slices), and omitted when in_field is per-sample.
        extra = ({} if field_row is None
                 else {"idx": np.asarray(field_row)[sl]})
        scores, _pred = arm_scorer.loo_batch(
            batch["X"][sl], batch.get("pixel_valid", batch.get("M"))[sl],
            **extra, **_scoring_inputs(batch, sl),
        )
        paths[n0 : n0 + sl.size] = scores
    return paths


def patch_arm_scores(
    arm,
    batch: dict,
    *,
    level_id: str,
    family: str,
    index: str,
    round_idx: int,
    rng=None,
    field_row: np.ndarray | None = None,
) -> dict:
    """Score one severity cell: inject in the PATCH tensor, then score.

    Returns ``{"z2": (N,T,1), "paths": (N,T), "injections": [...]}``. The
    injections carry their hash payload, so the cell's identity in the report
    is verifiable against the field-level ladder's.
    """
    from ssl_anomaly.monitor import patch_perturbations as ppert
    from ssl_anomaly.monitor import severity_table as sev

    levels = {lv.level_id: lv for lv in sev.load_table()}
    if level_id not in levels:
        raise ValueError(f"unknown severity level {level_id!r}")
    delta = float(levels[level_id].delta_ndvi)
    duration = (sev.PERSISTENT_DURATION_BINS if family == sev.PERSISTENT_FAMILY
                else levels[level_id].duration_bins)

    rng = rng if rng is not None else np.random.default_rng(round_idx)
    injections = []
    Xinj = np.empty_like(batch["X"])
    Minj = batch["pixel_valid"]
    for n in range(batch["X"].shape[0]):
        onset = ppert.onset_for_shape(family, batch["X"].shape[1], 3, int(duration))
        inj = ppert.inject_patch_drop(
            batch["raw"][n].astype(np.float32), batch["obs"][n],
            index=index, delta=delta, onset_bin=onset, shape=family,
            duration=int(duration), in_field=batch["in_field"][n],
            level_id=level_id, rng=rng,
        )
        Xinj[n], _ = P.normalize_patch(
            inj.x, batch["obs"][n], batch["sensor_id"][n], batch["norm_stats"]
        )
        injections.append(inj.to_hash_record())
    extra = {} if field_row is None else {"idx": np.asarray(field_row)}
    out = arm.score_cycles(Xinj, Minj, None, None, **extra, **_scoring_inputs(batch))
    return {"z2": out["z2"], "paths": out["score"], "p_value": out["p_value"],
            "observed": Minj.any(axis=(2, 3)),   # (N, T): any in-field pixel seen
            "injections": injections}
