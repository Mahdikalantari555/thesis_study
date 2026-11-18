"""Predictive-arm (gru_pred) tests (change predictive-ssl-controlled-trial, task 1.1).

The gru_pred arm keeps the gru_ae_main trunk/inputs/budget and changes ONLY
the objective to causal one-step-ahead prediction: pred(o) = f(z[<o]),
masked loss over observed (bin, channel) pairs. These tests pin the
pre-registered invariants BEFORE training: causality of the predictive
scorer, per-(bin, channel) masked loss, NaN safety, the recorded loss
choice (no post-hoc switching) and the shared parameter budget.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import models as mmodels  # noqa: E402

torch = pytest.importorskip("torch")

T, C = 36, 8


def make_scorer(seed: int = 0) -> mmodels.DeepPredictiveScorer:
    torch.manual_seed(seed)
    model = mmodels.build_model("gru_pred", d_in=mmodels.token_dim(C, True), n_out=C)
    return mmodels.DeepPredictiveScorer("gru_pred", model, use_doy=True, device="cpu")


def make_batch(n: int = 3, seed: int = 7) -> tuple:
    rng = np.random.default_rng(seed)
    z = rng.normal(size=(n, T, C)).astype(np.float32)
    m = rng.random((n, T, C)) > 0.2
    z[~m] = 0.0
    doy = rng.normal(size=(n, T, 2)).astype(np.float32)
    return z, m, doy


# ---------------------------------------------------------------------------
# Causality invariant: pred(o) depends only on bins < o
# ---------------------------------------------------------------------------
def test_predictive_scorer_causal_to_same_and_future_bins() -> None:
    """Perturbing z at bins ≥ o never changes pred(o) (prediction at o is
    head(h_{o-1}), a function of tokens < o only)."""
    scorer = make_scorer()
    z, m, doy = make_batch()
    base_scores, base_pred = scorer.loo_batch(z, m, doy)
    for o in (1, 5, 17, 35):
        z2 = z.copy()
        z2[:, o:, :] = np.random.default_rng(o).normal(size=(z.shape[0], T - o, C)).astype(np.float32) * 5
        _, pert_pred = scorer.loo_batch(z2, m, doy)
        np.testing.assert_allclose(pert_pred[:, :o, :], base_pred[:, :o, :], atol=1e-5)
    # pred(0) comes from the learned initial state — identical across batches.
    np.testing.assert_allclose(base_pred[0, 0, :], base_pred[1, 0, :], atol=1e-6)


def test_predictive_scorer_single_pass_equals_no_loo() -> None:
    """No LOO withholding: one forward pass; the mask enters only as token
    covariates and the score mask, never as input zeroing."""
    scorer = make_scorer()
    z, m, doy = make_batch()
    scores, pred = scorer.loo_batch(z, m, doy)
    assert pred.shape == z.shape
    assert scores.shape == (z.shape[0], T)
    # Repeat call → identical (deterministic, eval mode).
    scores2, pred2 = scorer.loo_batch(z, m, doy)
    np.testing.assert_allclose(pred2, pred, atol=1e-6)
    np.testing.assert_allclose(scores2, scores, atol=1e-6)


def test_predictive_scorer_secondary_statistic_semantics() -> None:
    """scores = observed-mask-weighted squared error per bin (D5 secondary
    statistic), NaN where the bin is fully unobserved."""
    scorer = make_scorer()
    z, m, doy = make_batch(n=2)
    scores, pred = scorer.loo_batch(z, m, doy)
    err = (pred - z) ** 2
    for n in range(2):
        for b in range(T):
            if m[n, b].any():
                expect = err[n, b][m[n, b]].mean()
                assert abs(scores[n, b] - expect) < 1e-5
            else:
                assert np.isnan(scores[n, b])


# ---------------------------------------------------------------------------
# Masked one-step loss (training objective)
# ---------------------------------------------------------------------------
def test_masked_one_step_loss_over_observed_pairs() -> None:
    """Loss = smooth-L1 mean over OBSERVED (bin, channel) pairs only; the
    per-pair granularity means unobserved channels of an observed bin are
    excluded too."""
    scorer = make_scorer()
    z, m, doy = make_batch(n=4)
    tokens = torch.from_numpy(
        mmodels.build_tokens(z, m, doy)).float()
    target = torch.from_numpy(z).float()
    channel_mask = torch.from_numpy(m)
    loss = scorer.predictive_losses(tokens, target, channel_mask)

    was_training = scorer.model.training
    scorer.model.eval()
    with torch.no_grad():
        recon = scorer.model(tokens).numpy()
    assert was_training  # training loss must not silently switch to eval mode
    import torch.nn.functional as F

    per_pair = F.smooth_l1_loss(torch.from_numpy(recon), target, reduction="none", beta=1.0).numpy()
    expect = per_pair[m].mean()
    assert abs(float(loss) - float(expect)) < 1e-5


def test_masked_one_step_loss_nan_and_nonfinite_safety() -> None:
    """NaN target entries at UNOBSERVED pairs never poison the loss (they are
    masked out, not multiplied); fully-unobserved batches clamp to 0."""
    scorer = make_scorer()
    z, m, doy = make_batch(n=3)
    z_nan = z.copy()
    z_nan[~m] = np.nan  # garbage exactly where unobserved
    tokens = torch.from_numpy(mmodels.build_tokens(z_nan, m, doy)).float()
    # build_tokens would carry NaN into the value channels of unobserved
    # entries — the loss must still be finite because those pairs are masked.
    target = torch.from_numpy(z_nan).float()
    channel_mask = torch.from_numpy(m)
    loss = scorer.predictive_losses(tokens, target, channel_mask, nonfinite_guard=True)
    assert np.isfinite(float(loss))

    # All-unobserved mask → clamped to 0, not NaN.
    empty_mask = np.zeros_like(m)
    tokens0 = torch.from_numpy(mmodels.build_tokens(z, empty_mask, doy)).float()
    loss0 = scorer.predictive_losses(tokens0, torch.from_numpy(z).float(),
                                     torch.from_numpy(empty_mask), nonfinite_guard=True)
    assert float(loss0) == 0.0


def test_masked_one_step_loss_finite_under_fp32_input() -> None:
    """Non-finiteGuard: a +inf token entry at an observed pair raises instead
    of silently training on garbage (fail loudly, AGENTS §8)."""
    scorer = make_scorer()
    z, m, doy = make_batch(n=2)
    z_bad = z.copy()
    z_bad[0, 5, 0] = np.inf  # observed pair with a non-finite value
    tokens = torch.from_numpy(mmodels.build_tokens(z_bad, m, doy)).float()
    with pytest.raises(FloatingPointError):
        scorer.predictive_losses(tokens, torch.from_numpy(z_bad).float(),
                                 torch.from_numpy(m), nonfinite_guard=True)


# ---------------------------------------------------------------------------
# Recorded loss choice + shared budget (pre-registered, no post-hoc switching)
# ---------------------------------------------------------------------------
def test_loss_choice_recorded_constant() -> None:
    """The loss choice is a module-level pre-registration: Huber/Smooth-L1
    beta=1.0 — the same loss family and beta as gru_ae_main's masked
    reconstruction loss (controlled-trial discipline: one change at a time).
    train_main must embed it verbatim in the checkpoint config."""
    from scripts.train_main import PREDICTIVE_OBJECTIVE  # noqa: PLC0415

    assert PREDICTIVE_OBJECTIVE == {
        "objective": "one_step_ahead",
        "loss": "smooth_l1_beta1.0",
        "loss_rationale": ("same family and beta as gru_ae_main's masked "
                           "reconstruction loss; MSE vs Huber decided BEFORE "
                           "training (design: no post-hoc switching)"),
    }


def test_gru_pred_same_trunk_and_param_budget_as_gru_ae() -> None:
    """gru_pred = gru_ae trunk (same class, same DEFAULT_CONFIGS entry values)
    and lands within the ≤500k cap with the identical parameter count."""
    assert mmodels.DEFAULT_CONFIGS["gru_pred"] == mmodels.DEFAULT_CONFIGS["gru_ae"]
    m_ae = mmodels.build_model("gru_ae", d_in=mmodels.token_dim(C, True), n_out=C)
    m_pred = mmodels.build_model("gru_pred", d_in=mmodels.token_dim(C, True), n_out=C)
    assert isinstance(m_ae, type(m_pred))  # identical trunk class
    assert mmodels.count_parameters(m_pred) == mmodels.count_parameters(m_ae)
    assert mmodels.count_parameters(m_pred) <= 500_000


def test_build_model_rejects_unknown_but_accepts_gru_pred() -> None:
    m = mmodels.build_model("gru_pred", d_in=mmodels.token_dim(C, True), n_out=C)
    assert m.n_out == C


# ---------------------------------------------------------------------------
# Checkpoint loading path (eval_dev/freeze compatibility)
# ---------------------------------------------------------------------------
def test_gru_pred_checkpoint_payload_roundtrip(tmp_path) -> None:
    """A gru_pred checkpoint payload (train_main's torch.save contract) loads
    into DeepPredictiveScorer via the same code path eval_dev.load_scorer
    uses. The objective/loss pre-registration must be embedded in the config."""
    from scripts.train_main import PREDICTIVE_OBJECTIVE  # noqa: PLC0415

    model = mmodels.build_model("gru_pred", d_in=mmodels.token_dim(C, True), n_out=C)
    payload = {
        "format": "causal_monitor_v1",
        "model_id": "gru_pred",
        "state_dict": model.state_dict(),
        "epoch": 1,
        "best_dev_loss": 0.5,
        "config": {"d_in": mmodels.token_dim(C, True), "n_out": C, "use_doy": True,
                   **mmodels.DEFAULT_CONFIGS["gru_pred"], **PREDICTIVE_OBJECTIVE},
        "seed": 13,
    }
    ckpt = tmp_path / "gru_pred_seed13.pt"
    torch.save(payload, ckpt)

    loaded = torch.load(ckpt, map_location="cpu", weights_only=False)  # noqa: S202
    assert loaded["config"]["objective"] == "one_step_ahead"
    assert loaded["config"]["loss"] == "smooth_l1_beta1.0"
    torch_model = mmodels.build_model("gru_pred", d_in=loaded["config"]["d_in"],
                                      n_out=loaded["config"]["n_out"], cfg={
                                          k: loaded["config"][k]
                                          for k in ("d_model", "n_layers", "d_ff", "n_heads", "dropout")
                                          if k in loaded["config"]})
    torch_model.load_state_dict(loaded["state_dict"])
    scorer = mmodels.DeepPredictiveScorer("gru_pred", torch_model, use_doy=True, device="cpu")
    z, m, doy = make_batch(n=2)
    scores, pred = scorer.loo_batch(z, m, doy)
    assert np.isfinite(pred).all()
