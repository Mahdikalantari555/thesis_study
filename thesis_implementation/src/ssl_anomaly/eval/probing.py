"""RQ7: Frozen-Feature Environmental & Agronomic Probing of Pretrained SSL Representations.

Tests what physical and agro-climatic quantities (``ET0``, cumulative ``GDD``,
solar ``radiation``, ``ETa_deficit``, and ``ratoon_stage``) are linearly decodable
from **frozen** cycle embeddings across all 3 SSL pretext arms vs. an untrained
random-projection Transformer baseline.
"""

from __future__ import annotations

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression, RidgeCV
from sklearn.metrics import r2_score, roc_auc_score
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.preprocessing import StandardScaler

from ..models.pretexts import PRETEXT_ARMS, PretextTransformer, train_pretext_arm


@torch.no_grad()
def extract_frozen_embeddings(model: PretextTransformer, toks: list[np.ndarray]) -> np.ndarray:
    """Extract mean-pooled frozen encoder representations ``(N, d_model)``."""
    model.eval()
    N = len(toks)
    d = toks[0].shape[1]
    T_max = max(t.shape[0] for t in toks)
    X_pad = np.zeros((N, T_max, d), dtype=np.float32)
    P_pad = np.ones((N, T_max), dtype=bool)
    for i, t in enumerate(toks):
        L = t.shape[0]
        X_pad[i, :L] = t
        P_pad[i, :L] = False
    _, emb = model.encode_sequence(torch.from_numpy(X_pad), key_padding_mask=torch.from_numpy(P_pad))
    return emb.numpy().astype(np.float64)


def probe_continuous_targets(
    embeddings: np.ndarray,
    targets: dict[str, np.ndarray],
    *,
    n_splits: int = 5,
    seed: int = 42,
) -> dict[str, float]:
    """5-fold RidgeCV probing R^2 for continuous agro-meteorological targets."""
    kf = KFold(n_splits=min(n_splits, len(embeddings)), shuffle=True, random_state=seed)
    out: dict[str, float] = {}
    for name, y in targets.items():
        fin = np.isfinite(y)
        X_use, y_use = embeddings[fin], y[fin]
        if len(y_use) < 12 or np.std(y_use) < 1e-8:
            out[f"{name}_r2"] = np.nan
            continue
        preds = np.zeros_like(y_use, dtype=np.float64)
        for tr, va in kf.split(X_use):
            sc = StandardScaler().fit(X_use[tr])
            reg = RidgeCV(alphas=np.logspace(-2, 3, 15)).fit(sc.transform(X_use[tr]), y_use[tr])
            preds[va] = reg.predict(sc.transform(X_use[va]))
        out[f"{name}_r2"] = float(r2_score(y_use, preds))
    return out


def probe_binary_target(
    embeddings: np.ndarray,
    y_bin: np.ndarray,
    *,
    n_splits: int = 5,
    seed: int = 42,
) -> float:
    """5-fold LogisticRegression AUC-ROC for binary agronomic regime (e.g., plant/early vs late ratoon)."""
    y_int = np.asarray(y_bin, dtype=int)
    if np.unique(y_int).size < 2 or np.min(np.bincount(y_int)) < n_splits:
        return np.nan
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    probs = np.zeros(len(y_int), dtype=np.float64)
    for tr, va in skf.split(embeddings, y_int):
        sc = StandardScaler().fit(embeddings[tr])
        clf = LogisticRegression(C=1.0, max_iter=500).fit(sc.transform(embeddings[tr]), y_int[tr])
        probs[va] = clf.predict_proba(sc.transform(embeddings[va]))[:, 1]
    return float(roc_auc_score(y_int, probs))


def run_rq7_probing_suite(
    train_toks: list[np.ndarray],
    eval_toks: list[np.ndarray],
    n_bands: int,
    continuous_targets: dict[str, np.ndarray],
    binary_targets: dict[str, np.ndarray] | None = None,
    *,
    epochs: int = 24,
    seed: int = 42,
) -> list[dict]:
    """Compare frozen representations of Untrained Random Encoder vs all 3 SSL Pretext Arms."""
    rows: list[dict] = []
    d_in = train_toks[0].shape[1]

    # 0. Untrained random-weights baseline (measures purely architectural reservoir projection)
    torch.manual_seed(seed)
    rand_model = PretextTransformer(d_in=d_in, n_bands=n_bands, arm="masked_recon")
    rand_emb = extract_frozen_embeddings(rand_model, eval_toks)
    r0: dict = {"encoder_source": "untrained_random_encoder"}
    r0.update(probe_continuous_targets(rand_emb, continuous_targets, seed=seed))
    if binary_targets:
        for bname, by in binary_targets.items():
            r0[f"{bname}_auc"] = probe_binary_target(rand_emb, by, seed=seed)
    rows.append(r0)

    # 1..3. Pretrained SSL pretext arms
    for arm in PRETEXT_ARMS:
        model = train_pretext_arm(arm, train_toks, n_bands=n_bands, epochs=epochs, batch_size=32, seed=seed)
        emb = extract_frozen_embeddings(model, eval_toks)
        row: dict = {"encoder_source": f"ssl_{arm}"}
        row.update(probe_continuous_targets(emb, continuous_targets, seed=seed))
        if binary_targets:
            for bname, by in binary_targets.items():
                row[f"{bname}_auc"] = probe_binary_target(emb, by, seed=seed)
        rows.append(row)

    return rows
