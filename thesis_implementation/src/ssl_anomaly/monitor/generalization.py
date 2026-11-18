"""Spatial / temporal generalization folds and the sensor-era stratification.

Change ``patch-generalization-suite`` tasks 1.1 and 1.3 (data-free half).

The 10 k-means blocks (``monitor/splits.py``, seed 13) are paired into 5
folds by **geographic adjacency of block centroids** — nearest-pair greedy,
seed-fixed, hash-recorded — so a held-out fold is a contiguous region rather
than a scatter of fields. Everything here is pure array work; nothing reads a
dataset, so the fold definition can be tested, frozen and re-checked before any
training run exists.

Three properties are load-bearing and each has its own test:

* **Partition** — every block is in exactly one fold, and every field of every
  block is in exactly one fold's field list. A duplicated field would train on
  the data it is evaluated on, which no downstream metric would reveal.
* **Contiguity** — a fold is a pair of ADJACENT blocks, so its held-out region
  is a connected area. Report the fold's mean intra-pair distance next to the
  mean inter-fold distance; a fold pair that is not nearer to itself than to
  other folds is a warning, not a failure (the study area is a strip, so the
  nearest neighbour of an end block is the next one along).
* **Leakage** — per-fold normalization is re-fitted from IN-FOLD TRAIN cycles
  only. :func:`refit_norm_in_fold` is where that is enforced, and the test
  plants a holdout field with an absurd value and proves the in-fold stats do
  not move.

Sensor eras (1.3): Landsat 9 enters the archive partway through, so period and
sensor are confounded. :func:`sensor_era` maps a date to L8/L9/unknown from the
scene metadata, :func:`threshold_stability` checks that the frozen ``τ``/``k``
do not need a per-year refit, and :func:`year_drift` measures the
quantile shift of one statistic across years so a temporal "degradation" can be
attributed to a sensor change instead of to generalization.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import numpy as np

N_FOLDS = 5
N_BLOCKS = 10

# Sensor ids as stored in patches.zarr (io/patches.SENSOR_IDS).
SENSOR_L8 = 1
SENSOR_L9 = 2
SENSOR_UNKNOWN = 0
SENSOR_NAMES = {SENSOR_L8: "L8", SENSOR_L9: "L9", SENSOR_UNKNOWN: "unknown"}


# ---------------------------------------------------------------------------
# 1.1 Fold construction
# ---------------------------------------------------------------------------
@dataclass
class Fold:
    """One held-out fold: a pair of blocks and the fields/cycles it owns."""

    fold_id: int
    blocks: tuple[int, int]
    held_out_fields: list[int]
    train_blocks: list[int]
    train_fields: list[int]
    mean_intra_distance: float = float("nan")
    mean_inter_distance: float = float("nan")

    def to_dict(self) -> dict:
        return {
            "fold_id": int(self.fold_id),
            "blocks": list(self.blocks),
            "held_out_fields": sorted(int(f) for f in self.held_out_fields),
            "train_blocks": sorted(int(b) for b in self.train_blocks),
            "train_fields": sorted(int(f) for f in self.train_fields),
            "mean_intra_distance": (None if not np.isfinite(self.mean_intra_distance)
                                    else round(float(self.mean_intra_distance), 3)),
            "mean_inter_distance": (None if not np.isfinite(self.mean_inter_distance)
                                    else round(float(self.mean_inter_distance), 3)),
        }


def _pairwise(points: np.ndarray) -> np.ndarray:
    p = np.asarray(points, dtype=np.float64)
    return np.sqrt(((p[:, None, :] - p[None, :, :]) ** 2).sum(-1))


def pair_blocks_by_adjacency(
    centroids: np.ndarray,
    *,
    block_of_field: np.ndarray | None = None,
    blocks: dict[str, list[int]] | None = None,
    n_folds: int = N_FOLDS,
    seed: int = 13,
) -> list[tuple[int, int]]:
    """Pair blocks into folds by nearest centroid (greedy, seed-fixed).

    Greedy nearest-pair: repeatedly take the globally closest pair of
    UNPAIRED blocks. Ties are broken by (lower index first, then higher) so the
    result does not depend on dict ordering. ``seed`` is recorded in the
    provenance but the algorithm is deterministic; it exists so a future
    stochastic variant cannot change the fold definition silently.
    """
    c = np.asarray(centroids, dtype=np.float64)
    if c.ndim != 2 or c.shape[1] != 2:
        raise ValueError(f"centroids must be (n_blocks, 2), got {c.shape}")
    n = c.shape[0]
    if n != n_folds * 2:
        raise ValueError(f"{n} blocks cannot be paired into {n_folds} folds of 2")
    d = _pairwise(c)
    np.fill_diagonal(d, np.inf)
    free = set(range(n))
    pairs: list[tuple[int, int]] = []
    while free:
        best = None
        for i in sorted(free):
            for j in sorted(free):
                if j <= i:
                    continue
                key = (float(d[i, j]), i, j)
                if best is None or key < best:
                    best = key
        _, i, j = best
        pairs.append((i, j))
        free -= {i, j}
    return sorted(pairs)


def block_centroids(block_of_field: dict[int, int], field_xy: dict[int, tuple[float, float]],
                    *, n_blocks: int = N_BLOCKS) -> np.ndarray:
    """Centroid of each block from the field coordinates it owns."""
    out = np.full((n_blocks, 2), np.nan)
    for b in range(n_blocks):
        members = [xy for f, xy in field_xy.items() if block_of_field.get(int(f)) == b]
        if not members:
            continue
        out[b] = np.mean(np.asarray(members, dtype=np.float64), axis=0)
    if np.isnan(out).any():
        raise ValueError(
            f"block(s) {np.flatnonzero(np.isnan(out[:, 0])).tolist()} have no field "
            "coordinates — a fold cannot be built on an empty block"
        )
    return out


def build_folds(
    block_of_field: dict[int, int],
    field_xy: dict[int, tuple[float, float]],
    *,
    blocks: dict[str, list[int]] | None = None,
    n_folds: int = N_FOLDS,
    n_blocks: int = N_BLOCKS,
) -> list[Fold]:
    """The 5 folds, each holding out one adjacent block pair."""
    cent = block_centroids(block_of_field, field_xy, n_blocks=n_blocks)
    pairs = pair_blocks_by_adjacency(cent, n_folds=n_folds)
    d = _pairwise(cent)
    by_block: dict[int, list[int]] = {}
    for fid, b in block_of_field.items():
        by_block.setdefault(int(b), []).append(int(fid))
    missing = [b for b in range(n_blocks) if b not in by_block]
    if missing:
        raise ValueError(f"blocks without any field: {missing}")

    folds: list[Fold] = []
    for k, (a, b) in enumerate(pairs):
        held = sorted(by_block[a] + by_block[b])
        train_blocks = [x for x in range(n_blocks) if x not in (a, b)]
        train_fields = sorted(f for x in train_blocks for f in by_block[x])
        intra = float(d[a, b])
        inter = float(np.mean([d[a, x] for x in train_blocks] + [d[b, x] for x in train_blocks]))
        folds.append(Fold(
            fold_id=k, blocks=(int(a), int(b)), held_out_fields=held,
            train_blocks=train_blocks, train_fields=train_fields,
            mean_intra_distance=intra, mean_inter_distance=inter,
        ))
    _assert_partition(folds, block_of_field, n_folds=n_folds)
    return folds


def _assert_partition(folds: list[Fold], block_of_field: dict[int, int],
                      *, n_folds: int) -> None:
    """Refuse a fold set that does not partition the fields exactly once."""
    seen: dict[int, int] = {}
    for f in folds:
        for fid in f.held_out_fields:
            if fid in seen:
                raise ValueError(
                    f"field {fid} is held out by folds {seen[fid]} and {f.fold_id} — "
                    "a duplicated field would be trained on the data it is judged on"
                )
            seen[fid] = f.fold_id
    all_fields = {int(f) for f in block_of_field}
    missing = sorted(all_fields - set(seen))
    if missing:
        raise ValueError(f"{len(missing)} fields are not held out by any fold: {missing[:5]}")
    if len(folds) != n_folds:
        raise ValueError(f"built {len(folds)} folds, expected {n_folds}")


def folds_sha256(folds: list[Fold]) -> str:
    """Stable hash of the fold definition (the frozen pre-registration)."""
    payload = [f.to_dict() for f in folds]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Per-fold normalization (leakage guard)
# ---------------------------------------------------------------------------
def refit_norm_in_fold(
    values: np.ndarray,        # (N, T, C, S, S) raw
    mask: np.ndarray,          # (N, T, C, S, S) observed
    sensor_ids: np.ndarray,    # (N, T)
    in_fold_train: np.ndarray, # (N,) bool: this cycle is an in-fold TRAIN cycle
    channel_names: tuple[str, ...],
    *,
    min_n: int = 20,
) -> dict:
    """Re-fit the frozen normalization dict from IN-FOLD TRAIN cycles only.

    The store's sidecar is a whole-store artifact; using it inside a fold would
    leak the held-out region's distribution into the training transform. Only
    cycles with ``in_fold_train`` contribute, and a channel × sensor cell with
    fewer than ``min_n`` observations is left OUT of the returned dict (the
    caller keeps raw units and records the fact) rather than being filled from
    the whole store.
    """
    v = np.asarray(values, dtype=np.float64)
    m = np.asarray(mask, dtype=bool)
    s = np.asarray(sensor_ids, dtype=np.int64)
    keep = np.asarray(in_fold_train, dtype=bool)
    if keep.shape != (v.shape[0],):
        raise ValueError(f"in_fold_train must be ({v.shape[0]},), got {keep.shape}")
    if m.shape != v.shape:
        raise ValueError(f"mask shape {m.shape} != values {v.shape}")
    if not keep.any():
        raise ValueError("no in-fold train cycles — refusing to fit an empty transform")
    # Fold the spatial extent into the sample axis first: the statistics are per
    # (sensor, channel) over ALL in-field pixels, and keeping the 4-D shape made
    # the index expression below broadcast a (N, T) mask against (N, T, S, S).
    nx, T, C = v.shape[0], v.shape[1], v.shape[2]
    vf = v.reshape(nx, T, C, -1)
    mf = m.reshape(nx, T, C, -1)
    out: dict[str, dict] = {}
    for sid in sorted({int(x) for x in np.unique(s[keep])} | {SENSOR_UNKNOWN}):
        per_ch: dict[str, dict] = {}
        sel = keep[:, None] & (s == sid)              # (N, T)
        for ci, name in enumerate(channel_names):
            vals = vf[:, :, ci][sel[:, :, None] & mf[:, :, ci]]
            vals = vals[np.isfinite(vals)]
            if vals.size < min_n:
                per_ch[name] = {"median": None, "iqr": None, "n": int(vals.size)}
                continue
            q25, q75 = np.percentile(vals, [25.0, 75.0])
            per_ch[name] = {
                "median": float(np.median(vals)),
                "iqr": float(max(q75 - q25, 1e-6)),
                "n": int(vals.size),
            }
        out[SENSOR_NAMES.get(sid, str(sid))] = per_ch
    return out


def norm_uses_only_in_fold(values: np.ndarray, mask: np.ndarray, sensor_ids: np.ndarray,
                           in_fold_train: np.ndarray, channel_names: tuple[str, ...],
                           *, probe_row: int) -> tuple[dict, dict]:
    """Fit twice — once with ``probe_row`` excluded — for the leakage test.

    Returns the two dicts so a test can assert equality. This helper exists
    because "the held-out data cannot move the transform" is a claim that has to
    be checked, not asserted in a docstring.
    """
    a = refit_norm_in_fold(values, mask, sensor_ids, in_fold_train, channel_names)
    keep_b = np.asarray(in_fold_train, dtype=bool).copy()
    keep_b[probe_row] = False
    if not keep_b.any():
        raise ValueError("excluding the probe leaves no train cycles")
    b = refit_norm_in_fold(values, mask, sensor_ids, keep_b, channel_names)
    return a, b


# ---------------------------------------------------------------------------
# 1.3 Sensor eras + drift
# ---------------------------------------------------------------------------
@dataclass
class SensorEra:
    name: str
    start: str | None
    end: str | None
    n_cycles: int = 0

    def to_dict(self) -> dict:
        return {"name": self.name, "start": self.start, "end": self.end,
                "n_cycles": int(self.n_cycles)}


def sensor_era(dates: np.ndarray, sensor_ids: np.ndarray) -> list[SensorEra]:
    """Contiguous runs of the same sensor over the date axis.

    A run changes when the sensor changes; an ``unknown`` acquisition is
    reported as its own era instead of being attributed to the neighbouring
    sensor (attribution would silently move L8 cycles into the L9 era and make
    the confound look smaller than it is).
    """
    d = np.asarray(dates).astype("datetime64[D]")
    s = np.asarray(sensor_ids, dtype=np.int64)
    if d.shape != s.shape:
        raise ValueError(f"dates {d.shape} and sensor ids {s.shape} must align")
    if d.size == 0:
        return []
    order = np.argsort(d)
    d, s = d[order], s[order]
    eras: list[SensorEra] = []
    start = 0
    for i in range(1, d.size + 1):
        if i == d.size or s[i] != s[start]:
            eras.append(SensorEra(
                name=SENSOR_NAMES.get(int(s[start]), str(s[start])),
                start=str(d[start]), end=str(d[i - 1]), n_cycles=int(i - start),
            ))
            start = i
    return eras


def era_shares(sensor_ids: np.ndarray) -> dict[str, float]:
    s = np.asarray(sensor_ids, dtype=np.int64).ravel()
    if s.size == 0:
        return {}
    names = np.array([SENSOR_NAMES.get(int(x), str(int(x))) for x in s])
    vals, counts = np.unique(names, return_counts=True)
    return {str(v): float(c) / s.size for v, c in zip(vals, counts)}


def year_drift(
    statistic: np.ndarray,    # (N,) one number per cycle (e.g. the clean path max)
    years: np.ndarray,        # (N,) year label per cycle
    *,
    quantiles: tuple[float, ...] = (0.5, 0.9),
) -> dict:
    """Quantile shift of a statistic across years, relative to the first year.

    A temporal "degradation" that coincides with a sensor change is a
    measurement artifact until proven otherwise; this is the number that shows
    it. The reference year is the FIRST year present, and every later year is
    reported as the absolute and relative shift of each quantile.
    """
    v = np.asarray(statistic, dtype=np.float64)
    y = np.asarray(years)
    if v.shape != y.shape:
        raise ValueError(f"statistic {v.shape} and years {y.shape} must align")
    ok = np.isfinite(v)
    if not ok.any():
        return {"reference_year": None, "per_year": {}}
    uniq = sorted({int(x) for x in y[ok]})
    ref = uniq[0]
    ref_v = v[ok & (y == ref)]
    ref_q = {str(q): float(np.quantile(ref_v, q)) for q in quantiles}
    per_year = {}
    for yr in uniq:
        vals = v[ok & (y == yr)]
        if vals.size == 0:
            continue
        q = {str(qq): float(np.quantile(vals, qq)) for qq in quantiles}
        per_year[str(yr)] = {
            "n": int(vals.size),
            "quantiles": q,
            "abs_shift": {k: q[k] - ref_q[k] for k in q},
            "rel_shift": {k: ((q[k] - ref_q[k]) / abs(ref_q[k]) if ref_q[k] else None)
                          for k in q},
        }
    return {"reference_year": ref, "per_year": per_year}


def threshold_stability(
    clean_paths: np.ndarray,   # (N, T) per-cycle alarm paths
    tau: float,
    k: int,
    years: np.ndarray,
    *,
    max_extra_far: float = 0.02,
) -> dict:
    """Is the FROZEN ``τ``/``k`` still valid in every year (no refit allowed)?

    Computes the per-year cycle-level FAR at the frozen threshold and reports
    whether any year exceeds the calibration FAR by more than
    ``max_extra_far``. Refitting per year would make the temporal column
    uninterpretable (each year would be calibrated to itself), so the answer
    must be a statement about stability, not a new threshold.
    """
    from . import scoring as mscoring

    p = np.asarray(clean_paths, dtype=np.float64)
    y = np.asarray(years)
    if p.ndim != 2:
        raise ValueError(f"clean_paths must be (N, T), got {p.shape}")
    if p.shape[0] != y.size:
        raise ValueError(f"{p.shape[0]} paths for {y.size} years")
    # The production rule, reused verbatim: k CONSECUTIVE observed bins above
    # tau. Re-implementing it here with a moving average would silently change
    # what "stable" means (a moving average alarms on a single spike).
    overall = float(np.mean([mscoring.alarm_per_cycle(row, tau, k) for row in p]))
    per_year: dict[str, dict] = {}
    for yr in sorted({int(x) for x in y}):
        sel = y == yr
        pw = p[sel]
        alarms = np.array([mscoring.alarm_per_cycle(row, tau, k) for row in pw], dtype=bool)
        far = float(alarms.mean()) if alarms.size else float("nan")
        per_year[str(yr)] = {"n": int(sel.sum()), "far": round(far, 4)}
    fars = [v["far"] for v in per_year.values() if np.isfinite(v["far"])]
    worst = max(fars) if fars else float("nan")
    return {
        "tau": float(tau), "k": int(k),
        "per_year": per_year,
        "worst_year_far": worst,
        "stable": bool(np.isfinite(worst) and (worst - overall) <= max_extra_far),
        "overall_far": round(overall, 4),
        "note": "refitting tau per year is NOT applied — the question is whether the "
                "frozen rule survives, not whether a new one can be found",
    }


__all__ = [
    "N_BLOCKS",
    "N_FOLDS",
    "SENSOR_L8",
    "SENSOR_L9",
    "SENSOR_NAMES",
    "SENSOR_UNKNOWN",
    "Fold",
    "SensorEra",
    "block_centroids",
    "build_folds",
    "era_shares",
    "folds_sha256",
    "norm_uses_only_in_fold",
    "pair_blocks_by_adjacency",
    "refit_norm_in_fold",
    "sensor_era",
    "threshold_stability",
    "year_drift",
]
