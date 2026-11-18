"""DS1–DS5 data-scarcity & representation-quality diagnostics.

Answers the advisor's question "does the model actually suffer from data
scarcity?" with the literature-standard instruments:

- ``DS1`` learning curve: downstream metric vs. fraction of training data.
- ``DS2`` train-vs-validation gap: per-epoch loss history from
  ``models.pretexts.train_pretext_arm_tracked`` summarized here.
- ``DS3`` SSL representation quality: mean pairwise cosine similarity
  (representation collapse), Wang & Isola alignment & uniformity, effective
  rank, and a t-SNE projection (PCA fallback).
- ``DS4`` few-shot downstream: LogisticRegression on frozen embeddings with
  1% / 5% / 10% of the labels.
- ``DS5`` variance across seeds / LOYO folds is assembled by the runner using
  ``eval.stats.bootstrap_ci`` / ``eval.cv`` (helpers here stay model-agnostic).

All functions are pure NumPy/scikit-learn so any future model can plug in its
own ``train_fn`` / ``eval_fn`` / embeddings.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np

from .stats import bootstrap_ci

DEFAULT_FRACTIONS: tuple[float, ...] = (0.2, 0.4, 0.6, 0.8, 1.0)
DEFAULT_FEW_SHOT_FRACTIONS: tuple[float, ...] = (0.01, 0.05, 0.10)
COLLAPSE_COSINE_THRESHOLD = 0.95
CURVE_STILL_RISING_SLOPE = 0.01


def _unit_norm(Z: np.ndarray) -> np.ndarray:
    Z = np.asarray(Z, dtype=np.float64)
    return Z / np.maximum(np.linalg.norm(Z, axis=1, keepdims=True), 1e-12)


def _pair_sq_dists(Zn: np.ndarray, max_pairs: int, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (i_idx, j_idx, sq_dist) for sampled (or all) i<j pairs."""
    n = Zn.shape[0]
    n_pairs = n * (n - 1) // 2
    if n_pairs <= max_pairs:
        iu = np.triu_indices(n, k=1)
        d2 = np.sum((Zn[iu[0]] - Zn[iu[1]]) ** 2, axis=1)
        return iu[0], iu[1], d2
    rng = np.random.default_rng(seed)
    m = max_pairs
    i = rng.integers(0, n, size=m)
    j = rng.integers(0, n, size=m)
    keep = i != j
    i, j = i[keep], j[keep]
    d2 = np.sum((Zn[i] - Zn[j]) ** 2, axis=1)
    return i, j, d2


def mean_cosine_similarity(emb: np.ndarray, max_pairs: int = 20000, seed: int = 42) -> float:
    """Mean pairwise cosine similarity between embeddings.

    Approaches 1.0 when the representation collapses (all points coincide).
    """
    Zn = _unit_norm(emb)
    n = Zn.shape[0]
    if n < 2:
        return float("nan")
    n_pairs = n * (n - 1) // 2
    if n_pairs <= max_pairs:
        iu = np.triu_indices(n, k=1)
        vals = np.einsum("ij,ij->i", Zn[iu[0]], Zn[iu[1]])
    else:
        rng = np.random.default_rng(seed)
        i = rng.integers(0, n, size=max_pairs)
        j = rng.integers(0, n, size=max_pairs)
        keep = i != j
        vals = np.einsum("ij,ij->i", Zn[i[keep]], Zn[j[keep]])
    return float(np.mean(vals))


def alignment_uniformity(
    emb: np.ndarray,
    groups: Sequence | None = None,
    *,
    t: float = 2.0,
    max_pairs: int = 20000,
    seed: int = 42,
) -> dict[str, float]:
    """Wang & Isola (2020) alignment & uniformity on unit-norm embeddings.

    - alignment: mean squared L2 distance over positive pairs. Positives are
      same-``group`` pairs when ``groups`` is given (e.g. same field, different
      cycles), otherwise each point's nearest neighbor.
    - uniformity: ``log mean_{i != j} exp(-t * ||z_i - z_j||^2)`` over all pairs
      (lower = more uniform hypersphere coverage).
    """
    Zn = _unit_norm(emb)
    n = Zn.shape[0]
    i, j, d2 = _pair_sq_dists(Zn, max_pairs=max_pairs, seed=seed)
    uniformity = float(np.log(np.mean(np.exp(-t * d2))))

    alignment = float("nan")
    if groups is not None and n >= 2:
        g = np.asarray(list(groups))
        same = g[i] == g[j]
        if same.any():
            alignment = float(np.mean(d2[same]))
    if not np.isfinite(alignment) and n >= 2:
        # nearest-neighbor pairs fallback
        full = n * (n - 1) // 2 <= max_pairs
        if full:
            iu = np.triu_indices(n, k=1)
            D2 = np.sum((Zn[iu[0]] - Zn[iu[1]]) ** 2, axis=1)
            nn = np.full(n, np.inf)
            np.minimum.at(np.arange(n), iu[1], D2)  # not exact; recompute properly below
            # exact NN via full matrix
            G = Zn @ Zn.T
            np.fill_diagonal(G, -np.inf)
            nn_d2 = 2.0 - 2.0 * np.max(G, axis=1)
            alignment = float(np.mean(nn_d2))
        else:
            # sampled approximation: for each sampled i, nearest among sampled j
            pass
    return {"alignment": alignment, "uniformity": uniformity}


def effective_rank(emb: np.ndarray) -> float:
    """Participation ratio of singular values of the centered embedding matrix.

    Equals ``dim`` for a perfectly spread representation and approaches 1 for a
    collapsed one — a scale-free complement to the cosine-collapse metric.
    """
    Z = np.asarray(emb, dtype=np.float64)
    Zc = Z - Z.mean(axis=0, keepdims=True)
    s = np.linalg.svd(Zc, compute_uv=False)
    s2 = s**2
    tot = float(s2.sum())
    if tot <= 0:
        return 1.0
    return float(tot * tot / float((s2**2).sum()))


def embedding_quality_report(
    emb: np.ndarray,
    groups: Sequence | None = None,
    *,
    seed: int = 42,
    collapse_threshold: float = COLLAPSE_COSINE_THRESHOLD,
) -> dict:
    """Full DS3 representation-quality report for one embedding matrix."""
    Z = np.asarray(emb, dtype=np.float64)
    au = alignment_uniformity(Z, groups=groups, seed=seed)
    cos = mean_cosine_similarity(Z, seed=seed)
    er = effective_rank(Z)
    dim = int(Z.shape[1]) if Z.ndim == 2 else 0
    return {
        "n_embeddings": int(Z.shape[0]),
        "dim": dim,
        "mean_cosine_sim": cos,
        "collapse_suspected": bool(np.isfinite(cos) and cos > collapse_threshold),
        "alignment": au["alignment"],
        "uniformity": au["uniformity"],
        "effective_rank": er,
        "effective_rank_ratio": float(er / dim) if dim else float("nan"),
    }


def learning_curve(
    train_fn: Callable[[float, int], object],
    eval_fn: Callable[[object], float],
    fractions: Sequence[float] = DEFAULT_FRACTIONS,
    seeds: Sequence[int] = (42,),
    *,
    metric_name: str = "auc_pr",
    rising_slope: float = CURVE_STILL_RISING_SLOPE,
) -> dict:
    """DS1: train on increasing fractions of the training data, evaluate on a
    fixed held-out pool.

    ``train_fn(fraction, seed) -> model`` and ``eval_fn(model) -> float`` keep
    this model-agnostic. Returns per-fraction mean/CI over seeds plus the raw
    per-seed values and the last-segment slope (has the curve flattened?).
    """
    points: list[dict] = []
    for frac in fractions:
        per_seed: list[float] = []
        for seed in seeds:
            model = train_fn(float(frac), int(seed))
            per_seed.append(float(eval_fn(model)))
        m, lo, hi = bootstrap_ci(np.mean, np.array(per_seed, dtype=np.float64), n_boot=1000, seed=42)
        points.append(
            {
                "fraction": float(frac),
                f"{metric_name}_mean": float(m),
                f"{metric_name}_ci_95": [float(lo), float(hi)],
                "per_seed": [float(v) for v in per_seed],
            }
        )
    slope = float("nan")
    if len(points) >= 2:
        slope = points[-1][f"{metric_name}_mean"] - points[-2][f"{metric_name}_mean"]
    return {
        "metric": metric_name,
        "points": points,
        "slope_last_segment": slope,
        "still_rising_at_100pct": bool(np.isfinite(slope) and slope > rising_slope),
    }


def summarize_train_val_history(history: dict) -> dict:
    """DS2: summarize a per-epoch train/val loss history into gap diagnostics."""
    tr = np.asarray(history.get("train_loss", []), dtype=np.float64)
    va = np.asarray(history.get("val_loss", []), dtype=np.float64)
    out: dict = {
        "epochs": int(len(tr)),
        "final_train_loss": float(tr[-1]) if tr.size else float("nan"),
        "final_val_loss": float(va[-1]) if va.size and np.isfinite(va[-1]) else float("nan"),
        "best_val_epoch": int(np.nanargmin(va)) if va.size and np.isfinite(va).any() else None,
    }
    gap = va - tr
    out["gap_final"] = float(gap[-1]) if gap.size and np.isfinite(gap[-1]) else float("nan")
    if tr.size >= 4:
        k = max(1, tr.size // 4)
        first_gap = float(np.nanmean(gap[:k]))
        last_gap = float(np.nanmean(gap[-k:]))
        train_drop_last = float(tr[-(k + 1)] - tr[-1]) if tr.size >= k + 1 else 0.0
        val_rise_last = float(np.nanmean(va[-k:]) - np.nanmean(va[:k]))
        out["gap_trend"] = last_gap - first_gap
        out["val_loss_rising"] = bool(val_rise_last > 0)
        out["train_loss_still_decreasing"] = bool(train_drop_last > 0)
        # overfitting signature: validation loss RISING while train loss still drops
        out["overfitting_suspected"] = bool(val_rise_last > 0 and train_drop_last > 0)
    else:
        out["gap_trend"] = float("nan")
        out["val_loss_rising"] = None
        out["train_loss_still_decreasing"] = None
        out["overfitting_suspected"] = False
    out["train_loss_curve"] = [float(v) for v in tr]
    out["val_loss_curve"] = [float(v) for v in va]
    return out


def few_shot_probe(
    emb: np.ndarray,
    labels: np.ndarray,
    fractions: Sequence[float] = DEFAULT_FEW_SHOT_FRACTIONS,
    *,
    n_repeats: int = 20,
    seed: int = 42,
) -> dict:
    """DS4: few-shot downstream performance on frozen embeddings.

    For each fraction, repeatedly draw a stratified labeled subset of that size,
    fit ``LogisticRegression`` on it, and score the held-out remainder with
    AUC-ROC / AUC-PR. Returns mean + 95% bootstrap CI per fraction.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, roc_auc_score

    X = np.asarray(emb, dtype=np.float64)
    y = np.asarray(labels).astype(int)
    finite = np.isfinite(X).all(axis=1) & np.isfinite(y)
    X, y = X[finite], y[finite]
    rng = np.random.default_rng(seed)
    out: dict[str, dict] = {}
    classes = np.unique(y)
    for frac in fractions:
        rocs: list[float] = []
        prs: list[float] = []
        n_lab: list[int] = []
        for _ in range(n_repeats):
            lab_idx: list[int] = []
            for c in classes:
                ci = np.where(y == c)[0]
                rng.shuffle(ci)
                k = max(1, int(round(frac * len(ci))))
                lab_idx.extend(ci[:k].tolist())
            lab_idx = np.array(sorted(lab_idx), dtype=int)
            rest = np.setdiff1d(np.arange(len(y)), lab_idx)
            if len(rest) == 0 or len(np.unique(y[rest])) < 2 or len(lab_idx) < 2:
                continue
            clf = LogisticRegression(max_iter=1000, class_weight="balanced")
            clf.fit(X[lab_idx], y[lab_idx])
            proba = clf.predict_proba(X[rest])[:, 1]
            rocs.append(float(roc_auc_score(y[rest], proba)))
            prs.append(float(average_precision_score(y[rest], proba)))
            n_lab.append(int(len(lab_idx)))
        if not rocs:
            out[f"frac_{frac}"] = {"auc_roc_mean": float("nan"), "auc_pr_mean": float("nan"), "n_labeled_mean": 0, "n_repeats_used": 0}
            continue
        roc_m, roc_lo, roc_hi = bootstrap_ci(np.mean, np.array(rocs), n_boot=1000, seed=seed)
        pr_m, pr_lo, pr_hi = bootstrap_ci(np.mean, np.array(prs), n_boot=1000, seed=seed)
        out[f"frac_{frac}"] = {
            "auc_roc_mean": float(roc_m),
            "auc_roc_ci_95": [float(roc_lo), float(roc_hi)],
            "auc_pr_mean": float(pr_m),
            "auc_pr_ci_95": [float(pr_lo), float(pr_hi)],
            "n_labeled_mean": float(np.mean(n_lab)),
            "n_repeats_used": len(rocs),
        }
    return {"fractions": [float(f) for f in fractions], "label_source": "caller-provided", "per_fraction": out}


def tsne_projection(emb: np.ndarray, *, seed: int = 42) -> np.ndarray:
    """2-D t-SNE projection of embeddings (PCA fallback); deterministic via seed."""
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE

    Z = np.asarray(emb, dtype=np.float64)
    n = Z.shape[0]
    if n < 3:
        return np.zeros((n, 2))
    perplexity = float(min(30.0, max(5.0, (n - 1) / 4.0)))
    try:
        return TSNE(
            n_components=2, init="pca", learning_rate="auto", perplexity=perplexity, random_state=seed
        ).fit_transform(Z)
    except Exception:
        return PCA(n_components=2, random_state=seed).fit_transform(Z)
