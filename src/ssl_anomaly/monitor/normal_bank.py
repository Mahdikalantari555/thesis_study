"""Normal-bank novelty scoring on the frozen GRU encoder (change
normal-bank-novelty-scoring).

Evidence base (research/ssl-stress-advantage/REPORT.md F3): objective-family
ranking on TSB-AD-M puts representation + distance-to-normal-bank scoring
(≈0.48 VUS-PR) above deep reconstruction (≈0.37 — our current family), with
the advantage concentrated on level-shift and relational (cross-channel)
anomalies — the persistent/chronic signatures of this archive's synthetic
family. This module adds a DEV-ONLY scoring arm:

- Bank source: **train-split cycles only** (manifest-gated;
  :func:`build_bank` refuses any non-train cycle and test access stays
  locked behind ``scripts/freeze_main_model.py --final-test``).
- Embeddings: frozen ``gru_ae_main`` encoder hidden state at each observed
  bin (causal: bin b's embedding depends only on tokens ≤ b — no future-bin
  leakage; unobserved bins contribute nothing and are excluded).
- Bank keys: (bin index, band-mask signature class) so a query bin is
  compared only against bank bins with comparable observation patterns;
  sparse cells fall back to the pooled same-signature class, then to the
  global pool — every fallback recorded per scored bin.
- Distance: k-NN (k ∈ {1, 5}) or per-cell diagonal robust Mahalanobis
  (median/MAD scaling; full covariance is rank-deficient at n≈450, d=200 —
  the diagonal robust form is the defensible choice).
- Null normalization: per-cell q95 of the bank members' leave-one-out
  distances (the common-null convention of the reconstruction statistic).
  Row sets larger than ``Q95_SUBSAMPLE`` are deterministically subsampled
  (fixed seed) for distances, stats and the null alike — approximate k-NN on
  the pooled/global classes, exact on direct cells.
  Fully-unobserved query bins score ``absent`` (NaN), never 0.

No fine-tuning anywhere; the frozen checkpoint, sidecar and platform payload
are untouched by this arm (adoption is a separate future change).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import numpy as np

from ssl_anomaly.monitor.splits import assert_no_test_cycles

BANK_NAME = "normal_bank_v1"
Q95_SUBSAMPLE = 512  # pooled/global cap (deterministic, seed-fixed); direct cells stay full
_Q95_SEED = 2026
SCALE_FLOOR = 1e-3
MAD_K = 1.4826

CellKey = tuple  # ("cell", bin, sig) | ("pooled", sig) | ("global",)


def mask_signature(m_bin: np.ndarray) -> str:
    """Band-mask signature class of one bin: "1" observed / "0" unobserved."""
    return "".join("1" if bool(v) else "0" for v in np.asarray(m_bin, dtype=bool))


def gru_embedding_fn(scorer):
    """Embedding extractor for the frozen GRU encoder (``gru_ae`` family).

    Returns ``embed(z (N,T,C), m (N,T,C), doy (N,T,2)|None) -> (N,T,d)``:
    the GRU hidden state AFTER consuming token b — bin b's embedding depends
    only on tokens ≤ b (causal by architecture; verified in
    ``test_gru_embeddings_shape_and_causality``). Forces eval mode.
    """
    import torch

    from ssl_anomaly.monitor.models import build_tokens

    model = scorer.model
    if not hasattr(model, "gru") or not hasattr(model, "h0"):
        raise ValueError("gru_embedding_fn requires the CausalGRUAE encoder (gru_ae family)")

    @torch.no_grad()
    def embed(z: np.ndarray, m: np.ndarray, doy: np.ndarray | None) -> np.ndarray:
        was_training = model.training
        model.eval()
        try:
            tokens = build_tokens(
                z.astype(np.float32), m.astype(bool),
                doy.astype(np.float32) if (doy is not None and scorer.use_doy) else None,
            )
            x = torch.from_numpy(tokens).float().to(scorer.device)
            B, T, _ = x.shape
            h0 = model.h0.expand(model.n_layers, B, model.d_model).contiguous()
            h_all, _ = model.gru(x, h0)  # (B, T, d_model) state AFTER each token
            return h_all.cpu().numpy()
        finally:
            if was_training:
                model.train()

    return embed


@dataclass
class NormalBank:
    """Immutable normal bank over frozen-encoder embeddings."""

    vectors: np.ndarray            # (E, d) float32 — one row per observed bank bin
    bin_idx: np.ndarray            # (E,) bin index of each entry
    class_keys: np.ndarray         # (E,) mask-signature of each entry
    cycle_ids: np.ndarray          # (E,) "<field>:<cycle_id>" provenance per entry
    splits: np.ndarray             # (E,) split label per entry ("train")
    k: int
    distance: str                  # "knn" | "mahalanobis"
    min_class_count: int
    encoder_checkpoint_sha256: str
    split_hash: str
    n_cycles: int
    _cells: dict = field(default_factory=dict, repr=False)    # (bin, sig) -> row indices
    _pooled: dict = field(default_factory=dict, repr=False)   # sig -> rows (all bins)
    _global: np.ndarray | None = field(default=None, repr=False)
    _subsampled: dict = field(default_factory=dict, repr=False)  # CellKey -> row subset
    _q95: dict = field(default_factory=dict, repr=False)         # CellKey -> null q95
    _stats: dict = field(default_factory=dict, repr=False)       # CellKey -> (med, scale)

    # -- manifest --------------------------------------------------------
    def manifest(self) -> dict:
        """bank.json sidecar payload (split hash, encoder hash, stats)."""
        classes, counts = np.unique(self.class_keys, return_counts=True)
        man = {
            "name": BANK_NAME,
            "n_entries": int(self.vectors.shape[0]),
            "n_cycles": int(self.n_cycles),
            "embedding_dim": int(self.vectors.shape[1]),
            "k": int(self.k),
            "distance": self.distance,
            "min_class_count": int(self.min_class_count),
            "encoder_checkpoint_sha256": self.encoder_checkpoint_sha256,
            "split_hash": self.split_hash,
            "splits_present": sorted(set(self.splits.tolist())),
            "class_counts": {str(c): int(n) for c, n in zip(classes, counts)},
            "n_cells_direct": len(self._cells),
            "n_classes_pooled": len(self._pooled),
            "row_subsample_cap": Q95_SUBSAMPLE,
        }
        man["manifest_sha256"] = hashlib.sha256(
            json.dumps(man, sort_keys=True).encode("utf-8")).hexdigest()
        return man

    # -- cell resolution ---------------------------------------------------
    def _resolve(self, b: int, sig: str) -> tuple[np.ndarray | None, str, CellKey]:
        """Row set + fallback flag + cache key for a query bin (spec scenario
        'Mask-class comparison')."""
        cell = self._cells.get((b, sig))
        if cell is not None and len(cell) >= self.min_class_count:
            return self._rows_for(("cell", b, sig), cell), "direct", ("cell", b, sig)
        pooled = self._pooled.get(sig)
        if pooled is not None and len(pooled) >= self.min_class_count:
            return self._rows_for(("pooled", sig), pooled), "pooled", ("pooled", sig)
        if self._global is not None and len(self._global):
            return self._rows_for(("global",), self._global), "global", ("global",)
        return None, "absent", ("absent",)

    def _rows_for(self, key: CellKey, rows: np.ndarray) -> np.ndarray:
        """Deterministic subsample of oversized row sets (pooled/global);
        direct cells (≤ ~n_train per bin) stay full."""
        if len(rows) <= Q95_SUBSAMPLE:
            return rows
        cached = self._subsampled.get(key)
        if cached is None:
            rng = np.random.default_rng(_Q95_SEED)
            cached = np.sort(rng.choice(rows, size=Q95_SUBSAMPLE, replace=False))
            self._subsampled[key] = cached
        return cached

    # -- distances ---------------------------------------------------------
    def _stats_for(self, key: CellKey, rows: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Diagonal robust stats (median, MAD×1.4826 floored) of a row set."""
        if key not in self._stats:
            V = self.vectors[rows].astype(np.float64)
            med = np.median(V, axis=0)
            scale = np.maximum(np.median(np.abs(V - med[None, :]), axis=0) * MAD_K, SCALE_FLOOR)
            self._stats[key] = (med, scale)
        return self._stats[key]

    def _distance(self, q: np.ndarray, rows: np.ndarray, key: CellKey,
                  exclude_pos: int | None = None) -> float:
        """Distance of query vector q to a row set (k-NN or diagonal robust
        Mahalanobis). ``exclude_pos`` removes one member (leave-one-out)."""
        if self.distance == "knn":
            V = self.vectors[rows]
            d2 = np.sum((V - q[None, :].astype(V.dtype)) ** 2, axis=1)
            if exclude_pos is not None and len(d2) > 1:
                d2 = np.delete(d2, exclude_pos)
            kk = min(self.k, len(d2))
            if kk == 0:
                return float("nan")
            if len(d2) > kk:
                part = np.argpartition(d2, kk - 1)[:kk]
                return float(np.sqrt(np.mean(d2[part])))
            return float(np.sqrt(np.mean(d2)))
        med, scale = self._stats_for(key, rows)
        zs = (q.astype(np.float64) - med) / scale
        return float(np.sqrt(np.mean(zs * zs)))

    def _loo_q95(self, key: CellKey, rows: np.ndarray) -> float:
        """q95 of the members' leave-one-out distances to their own row set —
        the common-null basis of the normalization (k-NN: self excluded;
        Mahalanobis: in-sample stats approximation, documented — the member's
        own contribution to med/scale is O(1/n) and the FAR calibration is
        re-done per variant on clean cycles, so a slightly low null is
        conservative and consistent)."""
        dists = []
        if self.distance == "knn":
            for i in range(len(rows)):
                dists.append(self._distance(self.vectors[rows[i]], rows, key, exclude_pos=i))
        else:
            med, scale = self._stats_for(key, rows)
            V = self.vectors[rows].astype(np.float64)
            zs = (V - med[None, :]) / scale[None, :]
            dists = np.sqrt(np.mean(zs * zs, axis=1)).tolist()
        dists = [d for d in dists if np.isfinite(d)]
        return float(np.percentile(dists, 95)) if dists else 1.0

    def _q95_for(self, key: CellKey, rows: np.ndarray) -> float:
        if key not in self._q95:
            self._q95[key] = max(self._loo_q95(key, rows), SCALE_FLOOR)
        return self._q95[key]

    # -- scoring -----------------------------------------------------------
    def score_batch(
        self,
        embeddings: np.ndarray,  # (N, T, d) frozen-encoder embeddings
        masks: np.ndarray,       # (N, T, C) observation mask of the query cycles
        doy: np.ndarray | None = None,  # unused (call-site symmetry)
    ) -> tuple[np.ndarray, dict]:
        """Per-bin novelty scores normalized to the common null (q95 basis).

        Returns (scores (N, T), meta) where meta["fallback"] is an (N, T)
        string array: "absent" (fully-unobserved bin → NaN score), "direct"
        (exact (bin, class) cell), "pooled" (same-signature class across all
        bins), "global".
        """
        del doy
        N, T, _ = embeddings.shape
        scores = np.full((N, T), np.nan)
        fallback = np.empty((N, T), dtype=object)
        fallback[:, :] = "absent"
        if self._global is None:
            self._global = np.arange(self.vectors.shape[0], dtype=np.int64)
        for n in range(N):
            for b in range(T):
                if not masks[n, b].any():
                    continue  # absent (NaN score, "absent" flag)
                sig = mask_signature(masks[n, b])
                rows, fb, key = self._resolve(b, sig)
                if rows is None:
                    continue
                dist = self._distance(embeddings[n, b], rows, key)
                scores[n, b] = dist / self._q95_for(key, rows)
                fallback[n, b] = fb
        return scores, {"fallback": fallback}


def build_bank(
    embeddings: np.ndarray,   # (N, T, d) frozen-encoder embeddings of the bank cycles
    masks: np.ndarray,        # (N, T, C) observation masks
    cycle_keys: list[str],
    manifest: dict,
    *,
    min_class_count: int = 8,
    k: int = 5,
    distance: str = "knn",
    encoder_sha256: str = "",
) -> NormalBank:
    """Build the normal bank from TRAIN cycles (manifest-gated).

    Every cycle key must belong to ``manifest["cycles"]["train"]``; any dev
    or test key is a hard error (bank provenance requirement). Entries record
    their cycle id and split ("train").
    """
    if distance not in ("knn", "mahalanobis"):
        raise ValueError(f"unknown bank distance {distance!r}")
    if k not in (1, 5):
        raise ValueError(f"bank k must be 1 or 5, got {k}")
    train = set(manifest["cycles"]["train"])
    offenders = [key for key in cycle_keys if key not in train]
    if offenders:
        raise RuntimeError(
            f"Normal bank may only be built from train-split cycles; non-train keys "
            f"{offenders[:5]}{'…' if len(offenders) > 5 else ''} refused "
            "(assert_no_test_cycles applies; bank provenance scenario)."
        )
    assert_no_test_cycles(cycle_keys, manifest, context="normal_bank.build_bank")

    N, T, D = embeddings.shape
    vecs: list[np.ndarray] = []
    bins: list[int] = []
    classes: list[str] = []
    cycles: list[str] = []
    splits: list[str] = []
    cells: dict[tuple[int, str], list[int]] = {}
    pooled: dict[str, list[int]] = {}
    for n in range(N):
        for b in range(T):
            m_bin = masks[n, b]
            if not m_bin.any():
                continue  # unobserved bins contribute nothing
            if not np.isfinite(embeddings[n, b]).all():
                continue  # defensive: non-finite embeddings excluded
            sig = mask_signature(m_bin)
            idx = len(vecs)
            vecs.append(embeddings[n, b].astype(np.float32))
            bins.append(b)
            classes.append(sig)
            cycles.append(cycle_keys[n])
            splits.append("train")
            cells.setdefault((b, sig), []).append(idx)
            pooled.setdefault(sig, []).append(idx)

    split_hash = hashlib.sha256(
        json.dumps(sorted(manifest["cycles"]["train"])).encode("utf-8")).hexdigest()[:16]
    bank = NormalBank(
        vectors=np.stack(vecs) if vecs else np.zeros((0, D), dtype=np.float32),
        bin_idx=np.asarray(bins, dtype=np.int64),
        class_keys=np.asarray(classes, dtype=object),
        cycle_ids=np.asarray(cycles, dtype=object),
        splits=np.asarray(splits, dtype=object),
        k=k, distance=distance, min_class_count=min_class_count,
        encoder_checkpoint_sha256=encoder_sha256,
        split_hash=split_hash,
        n_cycles=N,
        _cells={key: np.asarray(rows, dtype=np.int64) for key, rows in cells.items()},
        _pooled={sig: np.asarray(rows, dtype=np.int64) for sig, rows in pooled.items()},
    )
    bank._global = np.arange(bank.vectors.shape[0], dtype=np.int64)
    return bank
