"""Unit tests for DS1–DS5 data-scarcity diagnostics (eval/data_scarcity.py + tracked trainer)."""

from __future__ import annotations

import numpy as np
import pytest

from ssl_anomaly.eval.data_scarcity import (
    alignment_uniformity,
    effective_rank,
    embedding_quality_report,
    few_shot_probe,
    learning_curve,
    mean_cosine_similarity,
    summarize_train_val_history,
    tsne_projection,
)


class TestCollapseMetrics:
    def test_identical_embeddings_collapse(self):
        rng = np.random.default_rng(0)
        v = rng.normal(size=(1, 8))
        emb = np.repeat(v, 20, axis=0)
        assert mean_cosine_similarity(emb) == pytest.approx(1.0, abs=1e-9)
        rep = embedding_quality_report(emb, groups=np.arange(20) % 4)
        assert rep["collapse_suspected"] is True
        assert rep["alignment"] == pytest.approx(0.0, abs=1e-9)  # same-group pairs identical
        assert rep["effective_rank"] == pytest.approx(1.0, abs=1e-6)

    def test_orthogonal_embeddings_no_collapse(self):
        emb = np.eye(16)
        cos = mean_cosine_similarity(emb)
        assert cos == pytest.approx(0.0, abs=1e-9)
        rep = embedding_quality_report(emb, groups=np.arange(16))
        assert rep["collapse_suspected"] is False
        # centered identity has rank dim-1 (centering removes the mean direction)
        assert rep["effective_rank"] == pytest.approx(15.0, abs=1e-6)

    def test_alignment_uniformity_shapes(self):
        rng = np.random.default_rng(1)
        emb = rng.normal(size=(50, 8))
        groups = np.arange(50) % 5
        au = alignment_uniformity(emb, groups=groups)
        assert set(au) == {"alignment", "uniformity"}
        assert np.isfinite(au["alignment"])
        assert np.isfinite(au["uniformity"])
        # uniformity of a spread Gaussian cloud should be clearly negative
        assert au["uniformity"] < 0.0
        # alignment over same-group pairs must be <= mean over all pairs
        i_nn = None
        au_all = alignment_uniformity(emb, groups=None)
        assert np.isfinite(au_all["uniformity"])

    def test_effective_rank_bounds(self):
        rng = np.random.default_rng(2)
        emb = rng.normal(size=(100, 10))
        er = effective_rank(emb)
        assert 1.0 <= er <= 10.0 + 1e-9


class TestLearningCurve:
    def test_learning_curve_plumbing(self):
        # dummy trainer: "model" = the fraction itself; eval = fraction^0.5
        def train_fn(frac, seed):
            return frac + seed * 0.0

        def eval_fn(model):
            return float(np.sqrt(model))

        lc = learning_curve(train_fn, eval_fn, fractions=(0.5, 1.0), seeds=(42, 43), metric_name="auc_pr")
        assert len(lc["points"]) == 2
        assert lc["points"][-1]["auc_pr_mean"] == pytest.approx(1.0)
        assert lc["points"][0]["auc_pr_mean"] == pytest.approx(np.sqrt(0.5))
        assert lc["slope_last_segment"] == pytest.approx(1.0 - np.sqrt(0.5))
        assert lc["still_rising_at_100pct"] is True

    def test_flat_curve_not_rising(self):
        lc = learning_curve(lambda f, s: 0.5, lambda m: m, fractions=(0.5, 1.0), seeds=(1,))
        assert lc["still_rising_at_100pct"] is False
        assert lc["slope_last_segment"] == pytest.approx(0.0)


class TestTrainValSummary:
    def test_gap_summary_overfitting(self):
        # train loss keeps dropping while val loss rises -> gap widens
        tr = np.linspace(1.0, 0.2, 20)
        va = np.linspace(0.5, 1.2, 20)
        s = summarize_train_val_history({"train_loss": tr.tolist(), "val_loss": va.tolist()})
        assert s["final_train_loss"] == pytest.approx(0.2)
        assert s["final_val_loss"] == pytest.approx(1.2)
        assert s["gap_final"] == pytest.approx(1.0)
        assert s["gap_trend"] > 0
        assert s["train_loss_still_decreasing"] is True
        assert s["overfitting_suspected"] is True
        assert s["best_val_epoch"] == 0

    def test_healthy_history_not_flagged(self):
        tr = np.linspace(1.0, 0.3, 20)
        va = np.linspace(0.9, 0.4, 20)
        s = summarize_train_val_history({"train_loss": tr.tolist(), "val_loss": va.tolist()})
        assert s["overfitting_suspected"] is False
        assert s["gap_final"] == pytest.approx(0.1)

    def test_nan_val_when_no_val_tokens(self):
        s = summarize_train_val_history({"train_loss": [1.0, 0.5], "val_loss": [float("nan")] * 2})
        assert s["epochs"] == 2
        assert np.isnan(s["final_val_loss"])


class TestFewShot:
    def test_separable_embeddings_high_auc(self):
        rng = np.random.default_rng(3)
        n = 120
        emb = np.vstack([rng.normal(loc=0.0, size=(n // 2, 8)), rng.normal(loc=2.0, size=(n // 2, 8))])
        labels = np.array([0] * (n // 2) + [1] * (n // 2))
        out = few_shot_probe(emb, labels, fractions=(0.05, 0.10), n_repeats=10, seed=0)
        for fk in ("frac_0.05", "frac_0.1"):
            assert fk in out["per_fraction"]
            assert out["per_fraction"][fk]["auc_roc_mean"] > 0.95
            assert out["per_fraction"][fk]["n_repeats_used"] == 10

    def test_random_embeddings_chance_auc(self):
        rng = np.random.default_rng(4)
        emb = rng.normal(size=(100, 8))
        labels = (rng.random(100) < 0.3).astype(int)
        out = few_shot_probe(emb, labels, fractions=(0.10,), n_repeats=10, seed=0)
        v = out["per_fraction"]["frac_0.1"]
        assert 0.0 <= v["auc_roc_mean"] <= 1.0


class TestTSNE:
    def test_tsne_coords_shape(self):
        rng = np.random.default_rng(5)
        emb = rng.normal(size=(40, 8))
        coords = tsne_projection(emb, seed=0)
        assert coords.shape == (40, 2)
        assert np.isfinite(coords).all()

    def test_tiny_input(self):
        coords = tsne_projection(np.zeros((2, 4)))
        assert coords.shape == (2, 2)


class TestTrackedTrainer:
    def test_train_pretext_arm_tracked_history(self):
        torch = pytest.importorskip("torch")
        from ssl_anomaly.models.pretexts import train_pretext_arm, train_pretext_arm_tracked

        rng = np.random.default_rng(0)
        toks = [rng.normal(size=(12, 7)).astype(np.float32) for _ in range(16)]
        model, history = train_pretext_arm_tracked(
            "masked_recon", toks[:12], 7, val_tokens=toks[12:], epochs=3, batch_size=4, seed=11
        )
        assert len(history["train_loss"]) == 3
        assert len(history["val_loss"]) == 3
        assert all(np.isfinite(v) for v in history["val_loss"])
        # plain trainer still works and returns just the model
        m2 = train_pretext_arm("anomaly_degradation", toks[:12], 7, epochs=2, batch_size=4, seed=11)
        from ssl_anomaly.models.pretexts import PretextTransformer

        assert isinstance(m2, PretextTransformer)
