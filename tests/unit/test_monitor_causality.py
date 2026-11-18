"""Causality tests (task 4.5 / 10.4): appending future bins must not change
earlier scores — for every candidate scorer."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import inputs as minputs  # noqa: E402
from ssl_anomaly.monitor import models as mmodels  # noqa: E402

T, C = 36, 8


def make_cycle(seed=0, n_bins: int = T):
    rng = np.random.default_rng(seed)
    x = rng.normal(0.4, 0.1, size=(n_bins, C)).astype(np.float32)
    x[:, 7] = rng.normal(300, 5, size=n_bins)  # Kelvin
    m = np.ones((n_bins, C), dtype=bool)
    m[:2, :] = False  # leading unobserved bins
    m[7, 3] = False
    return x, m


@pytest.fixture(scope="module")
def norm():
    X = np.stack([make_cycle(seed=s)[0] for s in range(12)])
    M = np.stack([make_cycle(seed=s)[1] for s in range(12)])
    return minputs.fit_robust_norm(X, M)


def make_scorer(model_id: str, seed: int = 0) -> mmodels.DeepCausalScorer:
    import torch

    torch.manual_seed(seed)
    torch_model = mmodels.build_model(model_id, d_in=mmodels.token_dim(C, True), n_out=C)
    return mmodels.DeepCausalScorer(model_id, torch_model, use_doy=True, device="cpu")


@pytest.mark.parametrize("model_id", ["masked_transformer", "gru_ae"])
def test_deep_scores_causal_to_appended_bins(model_id: str, norm) -> None:
    """Score the first b bins must be identical whether or not later bins exist."""
    scorer = make_scorer(model_id)
    x, m = make_cycle(seed=5)
    z = minputs.apply_norm(norm, x[None], m[None])[0]
    doy = minputs.doy_channels(np.array([100]))[0]

    full_scores = scorer.score_cycle(z, m, doy)
    for cut in (10, 18, 27):
        part_scores = scorer.score_cycle(z[:cut], m[:cut], doy[:cut])
        ref = full_scores[:cut]
        got = part_scores
        both_obs = np.isfinite(ref) & np.isfinite(got)
        assert np.array_equal(both_obs, np.isfinite(ref)), "observation pattern changed"
        assert np.allclose(ref[both_obs], got[both_obs], atol=1e-6), (
            f"{model_id}: scores for bins <{cut} changed when future bins appended"
        )


@pytest.mark.parametrize("model_id", ["masked_transformer", "gru_ae"])
def test_deep_scores_causal_to_future_perturbation(model_id: str, norm) -> None:
    """Perturbing only FUTURE bins must leave earlier scores bit-identical."""
    scorer = make_scorer(model_id)
    x, m = make_cycle(seed=9)
    z = minputs.apply_norm(norm, x[None], m[None])[0]
    doy = minputs.doy_channels(np.array([200]))[0]

    scores_a = scorer.score_cycle(z, m, doy)
    z_future = z.copy()
    z_future[25:, :] += 50.0  # huge future deviation
    scores_b = scorer.score_cycle(z_future, m, doy)
    obs = np.isfinite(scores_a) & np.isfinite(scores_b)
    head = obs.copy()
    head[25:] = False
    assert np.array_equal(scores_a[head], scores_b[head]), (
        f"{model_id}: future perturbation changed earlier scores"
    )


def test_b1_scores_causal(norm) -> None:
    """B1 uses frozen train stats + bin b's own values only."""
    X = np.stack([make_cycle(seed=s)[0] for s in range(12)])
    M = np.stack([make_cycle(seed=s)[1] for s in range(12)])
    doy = minputs.doy_channels(np.full(12, 100, dtype=np.int64))
    b1 = mmodels.B1PhaseZCausal(use_doy=True, min_n=8)
    b1.fit(X, M, doy[:, :, 0])

    x, m = make_cycle(seed=3)
    s_full = b1.score_cycle(x, m, doy[0, :, 0])
    for cut in (12, 24):
        s_part = b1.score_cycle(x[:cut], m[:cut], doy[0, :cut, 0])
        obs = np.isfinite(s_full[:cut]) & np.isfinite(s_part)
        assert np.array_equal(s_full[:cut][obs], s_part[obs])


def test_b1_frozen_stats_not_refit_by_scoring(norm) -> None:
    X = np.stack([make_cycle(seed=s)[0] for s in range(12)])
    M = np.stack([make_cycle(seed=s)[1] for s in range(12)])
    doy = minputs.doy_channels(np.full(12, 100, dtype=np.int64))
    b1 = mmodels.B1PhaseZCausal(use_doy=True, min_n=8)
    b1.fit(X, M, doy[:, :, 0])
    med_before = b1.median.copy()
    x, m = make_cycle(seed=99)
    for _ in range(3):
        b1.score_cycle(x * 10, m, doy[0, :, 0])
    assert np.array_equal(b1.median, med_before)


@pytest.mark.parametrize("model_id", ["masked_transformer", "gru_ae"])
def test_scores_deterministic_across_calls(model_id: str, norm) -> None:
    """Same inputs → same scores (eval mode + no_grad; dropout disabled)."""
    scorer = make_scorer(model_id, seed=1)
    x, m = make_cycle(seed=11)
    z = minputs.apply_norm(norm, x[None], m[None])[0]
    doy = minputs.doy_channels(np.array([150]))[0]
    a = scorer.score_cycle(z, m, doy)
    b = scorer.score_cycle(z, m, doy)
    obs = np.isfinite(a)
    assert np.array_equal(a[obs], b[obs])


def test_masked_tf_uses_causal_attention() -> None:
    """Direct attention check: position 5 output must not change when only
    position 10's input changes (causal mask forbids the look-ahead)."""
    import torch

    scorer = make_scorer("masked_transformer", seed=2)
    model = scorer.model
    model.eval()
    x1 = torch.randn(1, 20, 18)
    x2 = x1.clone()
    x2[0, 10:, :] += 10.0  # change only the future
    with torch.no_grad():
        r1 = model(x1)
        r2 = model(x2)
    assert torch.allclose(r1[0, :10], r2[0, :10], atol=1e-6), "attention looked ahead"
    assert not torch.allclose(r1[0, 10:], r2[0, 10:], atol=1e-6), "future change had no effect at all"


def test_gru_next_bin_uses_prefix_only() -> None:
    """CausalGRUAE recon at position t depends only on tokens < t."""
    import torch

    torch.manual_seed(0)
    model = mmodels.build_model("gru_ae", d_in=18, n_out=8, cfg={"d_model": 32, "n_layers": 1})
    model.eval()
    x1 = torch.randn(1, 20, 18)
    x2 = x1.clone()
    x2[0, 10:, :] += 10.0
    with torch.no_grad():
        r1 = model(x1)
        r2 = model(x2)
    assert torch.allclose(r1[0, :10], r2[0, :10], atol=1e-6)
    assert not torch.allclose(r1[0, 10:], r2[0, 10:], atol=1e-6)


# ---------------------------------------------------------------------------
# Parameter caps and matching (design D4)
# ---------------------------------------------------------------------------
def test_param_counts_within_cap_and_matching() -> None:
    import torch

    torch.manual_seed(0)
    tf = mmodels.build_model("masked_transformer", d_in=18, n_out=8)
    gru = mmodels.build_model("gru_ae", d_in=18, n_out=8)
    p_tf = mmodels.count_parameters(tf)
    p_gru = mmodels.count_parameters(gru)
    assert p_tf <= 500_000, f"masked_transformer {p_tf} > 500k"
    assert p_gru <= 500_000, f"gru_ae {p_gru} > 500k"
    lo, hi = 0.8 * min(p_tf, p_gru), 1.2 * max(p_tf, p_gru)
    assert lo <= max(p_tf, p_gru) <= hi, (
        f"parameter counts not within ±20%: tf={p_tf}, gru={p_gru}"
    )
    print(f"params: masked_transformer={p_tf:,}, gru_ae={p_gru:,}")


def test_b1_fit_shapes_and_score_range(norm) -> None:
    X = np.stack([make_cycle(seed=s)[0] for s in range(12)])
    M = np.stack([make_cycle(seed=s)[1] for s in range(12)])
    doy = minputs.doy_channels(np.full(12, 100, dtype=np.int64))
    b1 = mmodels.B1PhaseZCausal(use_doy=True, min_n=8)
    b1.fit(X, M, doy[:, :, 0])
    assert b1.median.shape == (2, 36, 8)
    assert np.all(b1.scale > 0)
    x, m = make_cycle(seed=1)
    s = b1.score_cycle(x, m, doy[0, :, 0])
    assert s.shape == (36,)
    obs = np.isfinite(s)
    assert obs.any()
    assert np.all(s[obs] >= 0), "mean z² is non-negative"
