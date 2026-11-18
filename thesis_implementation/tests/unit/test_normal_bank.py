"""Normal-bank novelty scoring tests (change normal-bank-novelty-scoring, tasks 1.1–1.2).

Bank provenance (train-only, manifest-gated), mask-signature class comparison
with pooled fallback, absent-bin handling, k-NN / robust-Mahalanobis distances,
per-cell q95 normalization, and the causal GRU embedding extraction.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import normal_bank as nbank  # noqa: E402

T, C, D = 36, 8, 16


def fake_embeddings(rng: np.random.Generator, n: int, scale: float = 1.0) -> np.ndarray:
    return (rng.normal(0.0, scale, size=(n, T, D))).astype(np.float32)


def full_masks(n: int) -> np.ndarray:
    return np.ones((n, T, C), dtype=bool)


def make_manifest(train_keys: list[str], test_keys: list[str] | None = None) -> dict:
    keys = train_keys + (test_keys or [])
    return {
        "cycles": {"train": train_keys, "dev": [], "test": (test_keys or []),
                   "monitoring_only": []},
        "counts": {"train": len(train_keys)},
        "cycle_keys": keys,
    }


# ---------------------------------------------------------------------------
# Provenance (spec scenario 'Bank provenance')
# ---------------------------------------------------------------------------
def test_bank_refuses_non_train_cycles() -> None:
    """Every bank entry must come from the train split; a dev or test key in
    the build call is a hard error naming the rule."""
    rng = np.random.default_rng(0)
    emb = fake_embeddings(rng, 4)
    manifest = make_manifest(["f1:1", "f2:2"], test_keys=["f3:3"])
    with pytest.raises(RuntimeError, match="train"):
        nbank.build_bank(emb, full_masks(4), ["f1:1", "f2:2", "f3:3"], manifest)


def test_bank_entries_record_cycle_and_split() -> None:
    rng = np.random.default_rng(1)
    n = 6
    emb = fake_embeddings(rng, n)
    keys = [f"f{i}:1" for i in range(n)]
    manifest = make_manifest(keys)
    bank = nbank.build_bank(emb, full_masks(n), keys, manifest, encoder_sha256="abc123")
    assert set(bank.cycle_ids) == set(keys)
    assert set(bank.splits) == {"train"}
    man = bank.manifest()
    assert man["split_hash"]
    assert man["encoder_checkpoint_sha256"] == "abc123"
    assert man["n_entries"] == n * T
    assert man["n_cycles"] == n
    assert man["manifest_sha256"]


def test_bank_manifest_hash_stable() -> None:
    rng = np.random.default_rng(2)
    emb = fake_embeddings(rng, 3)
    keys = ["a:1", "b:1", "c:1"]
    b1 = nbank.build_bank(emb, full_masks(3), keys, make_manifest(keys))
    b2 = nbank.build_bank(emb.copy(), full_masks(3), keys, make_manifest(keys))
    assert b1.manifest()["manifest_sha256"] == b2.manifest()["manifest_sha256"]


# ---------------------------------------------------------------------------
# Class comparison + fallback (spec scenario 'Mask-class comparison')
# ---------------------------------------------------------------------------
def test_absent_bin_scores_nan_not_zero() -> None:
    """Fully-unobserved bins score `absent` (NaN), never 0."""
    rng = np.random.default_rng(3)
    n = 5
    emb = fake_embeddings(rng, n)
    keys = [f"f{i}:1" for i in range(n)]
    bank = nbank.build_bank(emb, full_masks(n), keys, make_manifest(keys))
    m = full_masks(1)
    m[0, 10, :] = False  # bin 10 fully unobserved
    z = np.zeros((1, T, C), dtype=np.float32)
    scores, meta = bank.score_batch(np.stack([emb[0]]), m, None)
    assert np.isnan(scores[0, 10])
    assert meta["fallback"][0, 10] == "absent"


def test_mask_class_comparison_and_pooled_fallback() -> None:
    """A query bin is compared only against same-signature bank bins; a
    missing/under-counted class falls back to the pooled same-signature class
    (all bins) with a recorded flag."""
    rng = np.random.default_rng(4)
    n = 12  # ≥ min_class_count so the all-observed cells exist directly
    emb = fake_embeddings(rng, n)
    keys = [f"f{i}:1" for i in range(n)]
    m = full_masks(n)
    m[:, 12, 7] = False  # every bank cycle misses LST at bin 12 → signature "11111110" there
    bank = nbank.build_bank(emb, m, keys, make_manifest(keys), min_class_count=8)
    # Query with the ALL-OBSERVED signature everywhere: at bin 12 the
    # (12, "11111111") cell does not exist → pooled "11111111" fallback.
    scores, meta = bank.score_batch(np.stack([emb[0]]), full_masks(1), None)
    assert meta["fallback"][0, 12] == "pooled"
    # Bins whose exact class exists are scored directly.
    assert meta["fallback"][0, 5] == "direct"
    assert np.isfinite(scores[0, 12])


def test_global_fallback_when_pooled_sparse() -> None:
    rng = np.random.default_rng(5)
    n = 3  # tiny bank
    emb = fake_embeddings(rng, n)
    keys = [f"f{i}:1" for i in range(n)]
    m = np.zeros((n, T, C), dtype=bool)
    m[:, :2, :] = True  # 2 observed bins per cycle → pooled class count 6 < 8 → global
    bank = nbank.build_bank(emb, m, keys, make_manifest(keys), min_class_count=8)
    qm = np.zeros((1, T, C), dtype=bool)
    qm[:, :2, :] = True
    scores, meta = bank.score_batch(np.stack([emb[0]]), qm, None)
    assert meta["fallback"][0, 1] == "global"
    assert np.isfinite(scores[0, 1])


def test_injected_bin_scores_higher_than_clean() -> None:
    """A level-shifted query vector scores further from the bank than the
    clean vectors it was built from (task 1.2 acceptance)."""
    rng = np.random.default_rng(6)
    n = 30
    emb = fake_embeddings(rng, n, scale=1.0)
    keys = [f"f{i}:1" for i in range(n)]
    bank = nbank.build_bank(emb, full_masks(n), keys, make_manifest(keys))
    clean_q = emb[0:5]  # bank members themselves (LOO-ish: still near the bank)
    shifted = emb[0:5] + np.float32(8.0)  # level shift in latent space
    m = full_masks(10)
    z = np.concatenate([clean_q, shifted])
    scores, _ = bank.score_batch(z, m, None)
    assert np.nanmean(scores[5:]) > np.nanmean(scores[:5]) + 5.0


def test_knn_k1_and_k5_and_mahalanobis_variants() -> None:
    rng = np.random.default_rng(7)
    n = 40
    emb = fake_embeddings(rng, n)
    keys = [f"f{i}:1" for i in range(n)]
    for k in (1, 5):
        bank = nbank.build_bank(emb, full_masks(n), keys, make_manifest(keys), k=k)
        scores, _ = bank.score_batch(np.stack([emb[0]]), full_masks(1), None)
        assert np.all(np.isfinite(scores[0, :20]))
    bank_m = nbank.build_bank(emb, full_masks(n), keys, make_manifest(keys),
                              distance="mahalanobis")
    scores_m, _ = bank_m.score_batch(np.stack([emb[0]]), full_masks(1), None)
    assert np.all(np.isfinite(scores_m[0, :20]))


def test_no_future_bin_leakage_in_scoring() -> None:
    """Scoring bin b must not depend on bins > b (no future-bin leakage within
    the query window)."""
    rng = np.random.default_rng(8)
    n = 30
    emb = fake_embeddings(rng, n)
    keys = [f"f{i}:1" for i in range(n)]
    bank = nbank.build_bank(emb, full_masks(n), keys, make_manifest(keys))
    q1 = emb[0:1].copy()
    q2 = emb[0:1].copy()
    q2[0, 20:, :] += 100.0  # only future bins changed
    s1, _ = bank.score_batch(q1, full_masks(1), None)
    s2, _ = bank.score_batch(q2, full_masks(1), None)
    # The BANK SCORER itself is per-bin (stateless across bins) — the leakage
    # guarantee comes from the encoder (tested below); this pins the scorer.
    assert np.allclose(s1[0, :20], s2[0, :20])


# ---------------------------------------------------------------------------
# GRU encoder embedding extraction (frozen gru_ae_main encoder)
# ---------------------------------------------------------------------------
def test_gru_embeddings_shape_and_causality() -> None:
    import torch

    from ssl_anomaly.models.gru_ae import CausalGRUAE
    from ssl_anomaly.monitor import models as mmodels

    torch.manual_seed(0)
    model = CausalGRUAE(d_in=18, n_out=8, d_model=D, n_layers=1)
    scorer = mmodels.DeepCausalScorer("gru_ae", model, use_doy=True, device="cpu")
    emb_fn = nbank.gru_embedding_fn(scorer)

    rng = np.random.default_rng(9)
    z = rng.normal(0, 1, size=(1, T, C)).astype(np.float32)
    m = full_masks(1)
    doy = rng.normal(0, 1, size=(1, T, 2)).astype(np.float32)
    e1 = emb_fn(z, m, doy)
    assert e1.shape == (1, T, D)
    z2 = z.copy()
    z2[0, 20:, :] += 50.0  # future bins only
    e2 = emb_fn(z2, m, doy)
    assert np.allclose(e1[0, :20], e2[0, :20], atol=1e-6), "embedding(b) leaked future bins"


def test_gru_embeddings_eval_mode_deterministic() -> None:
    import torch

    from ssl_anomaly.models.gru_ae import CausalGRUAE
    from ssl_anomaly.monitor import models as mmodels

    torch.manual_seed(1)
    model = CausalGRUAE(d_in=18, n_out=8, d_model=D, n_layers=1)
    scorer = mmodels.DeepCausalScorer("gru_ae", model, use_doy=True, device="cpu")
    emb_fn = nbank.gru_embedding_fn(scorer)
    rng = np.random.default_rng(10)
    z = rng.normal(0, 1, size=(2, T, C)).astype(np.float32)
    m = full_masks(2)
    doy = rng.normal(0, 1, size=(2, T, 2)).astype(np.float32)
    e1 = emb_fn(z, m, doy)
    e2 = emb_fn(z, m, doy)
    # Identical repeated outputs prove eval mode during the forward (the
    # wrapper restores the caller's training state afterwards by design).
    assert np.array_equal(e1, e2)
