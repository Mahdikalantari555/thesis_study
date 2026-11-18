"""Patch model: causality, farm-boundary isolation, masking, param gates.

Covers ``patch-level-controlled-trial`` tasks 1.1/1.1b/1.2.
"""

from __future__ import annotations

import pytest
import torch

from ssl_anomaly.models.patch_cnn_gru import (
    HARD_PARAM_CEILING,
    HORIZONS,
    TARGET_PARAMS,
    build_patch_model,
    scorer_id,
)

S = 32
T = 36
C = 8


def _model(use_cnn: bool = True, n_cov: int = 0):
    torch.manual_seed(0)
    m = build_patch_model(use_cnn=use_cnn, n_covariates=n_cov)
    m.eval()
    return m


def _batch(b: int = 2, seed: int = 0):
    g = torch.Generator().manual_seed(seed)
    x = torch.randn(b, T, C, S, S, generator=g)
    pv = torch.rand(b, T, S, S, generator=g) > 0.3
    return x, pv


# --- 1.1 causality ---------------------------------------------------------
def test_future_bins_cannot_change_past_predictions():
    """x̂ at bin t+k−1 depends only on bins ≤ t (spec scenario)."""
    m = _model()
    x, pv = _batch()
    out = m(x, pv)
    x2 = x.clone()
    x2[:, 20:] = torch.randn_like(x2[:, 20:])
    out2 = m(x2, pv)
    # horizon 1 at bins < 20 must be byte-identical
    assert torch.equal(out["pred"][:, :20, 0], out2["pred"][:, :20, 0])


def test_horizon_k_reads_only_up_to_its_anchor_bin():
    """Horizon 3 at bin t predicts t+2, so bins > t must not move it either."""
    m = _model()
    x, pv = _batch()
    out = m(x, pv)
    x2 = x.clone()
    x2[:, 15:] = 0.0
    out2 = m(x2, pv)
    for k in HORIZONS:
        assert torch.equal(out["pred"][:, : 15 - k + 1, k - 1],
                           out2["pred"][:, : 15 - k + 1, k - 1]), f"horizon {k} leaked"


def test_out_of_range_horizon_slots_are_zero():
    """A horizon slot past the cycle end is padding, not a prediction."""
    m = _model()
    x, pv = _batch(b=1)
    out = m(x, pv)
    assert torch.all(out["pred"][:, T - 1, 1:] == 0)
    assert torch.all(out["pred"][:, T - 2, 2:] == 0)


# --- 1.1b farm-boundary isolation -----------------------------------------
def test_out_of_field_values_cannot_change_in_field_scores():
    """Perturbing out-of-field pixels leaves in-field predictions identical."""
    m = _model()
    x, pv = _batch()
    infield = torch.zeros(S, S, dtype=torch.bool)
    infield[6:26, 6:26] = True
    pv = pv & infield
    out = m(x, pv)

    x2 = x.clone()
    x2[:, :, :, ~infield] = 1e3                   # neighbouring field / padding
    out2 = m(x2, pv)
    assert torch.equal(out["pred"], out2["pred"]), "out-of-field values leaked"


def test_neighbouring_field_inside_the_bbox_is_invisible():
    """A synthetic neighbour in the bbox changes nothing in-field."""
    m = _model()
    x, _ = _batch(b=1)
    infield = torch.zeros(1, 1, S, S, dtype=torch.bool)
    infield[:, :, 2:14, 2:14] = True              # our field: bbox is the patch
    pv = infield.expand(1, T, S, S).clone()
    out = m(x, pv)
    x2 = x.clone()
    x2[:, :, 20:30, 20:30] = 50.0                 # neighbour inside the bbox
    out2 = m(x2, pv)
    assert torch.equal(out["pred"], out2["pred"])


def test_stem_input_is_masked_before_the_first_convolution():
    """concat[X·M_in, M_in]: out-of-field values are exactly zero."""
    m = _model()
    x, pv = _batch(b=1)
    infield = torch.zeros(S, S, dtype=torch.bool)
    infield[8:24, 8:24] = True
    pv = pv & infield
    stem_in, got_mask = m.stem_input(x, pv)
    assert stem_in.shape == (1, T, C + 1, S, S)
    assert torch.all(stem_in[:, :, :C][:, :, :, ~infield] == 0)
    assert torch.equal(got_mask, pv)
    # the appended mask plane carries the boundary itself
    plane = stem_in[:, :, C]
    assert torch.all(plane[..., ~infield] == 0)
    assert torch.all(plane[..., infield][pv[..., infield]] == 1)
    assert torch.all(plane[..., infield][~pv[..., infield]] == 0)


def test_in_field_pixel_count_matches_the_mask():
    m = _model()
    x, pv = _batch(b=1)
    infield = torch.zeros(S, S, dtype=torch.bool)
    infield[4:20, 4:20] = True
    pv = pv & infield
    _, got = m.stem_input(x, pv)
    assert int(got.sum()) == int(pv.sum())
    # nothing outside the polygon is ever marked usable
    assert not bool(got[:, :, ~infield].any())


def test_pixelwise_control_has_the_same_interface():
    m_cnn = _model(use_cnn=True)
    m_px = _model(use_cnn=False)
    x, pv = _batch()
    a, b = m_cnn(x, pv), m_px(x, pv)
    assert a["pred"].shape == b["pred"].shape
    assert a["aux"].shape == b["aux"].shape


def test_pixelwise_control_does_not_mix_pixels():
    """No stem ⇒ perturbing one pixel cannot change another pixel's score."""
    m = _model(use_cnn=False)
    x, pv = _batch(b=1)
    out = m(x, pv)
    x2 = x.clone()
    x2[:, :, :, 0, 0] += 10.0
    out2 = m(x2, pv)
    d = (out["pred"] - out2["pred"]).abs()
    # every pixel except (0,0) is untouched
    dd = d.detach()
    assert float(dd[:, :, :, 1:, :].max()) == 0.0
    assert float(dd[:, :, :, :, 1:].max()) == 0.0


# --- 1.1 no BatchNorm anywhere --------------------------------------------
def test_no_batch_norm_anywhere():
    for use_cnn in (True, False):
        m = _model(use_cnn=use_cnn)
        kinds = {type(mod).__name__ for mod in m.modules()}
        assert "BatchNorm1d" not in kinds
        assert "BatchNorm2d" not in kinds
        assert "SyncBatchNorm" not in kinds


def test_group_norm_is_invariant_to_batch_composition():
    """A patch's score must not depend on which patches share its batch."""
    m = _model()
    x, pv = _batch(b=3)
    alone = m(x[:1], pv[:1])["pred"]
    together = m(x, pv)["pred"][:1]
    assert torch.equal(alone, together)


def test_degenerate_all_masked_batch_is_finite():
    m = _model()
    x, _ = _batch(b=2)
    pv = torch.zeros(2, T, S, S, dtype=torch.bool)
    out = m(x, pv)
    assert torch.isfinite(out["pred"]).all()
    assert torch.isfinite(out["aux"]).all()


# --- NaN safety / loss ----------------------------------------------------
def test_hybrid_loss_is_finite_and_prefers_correct_predictions():
    m = _model()
    x, pv = _batch(b=2)
    out = m(x, pv)
    obs = torch.rand(2, T, C, S, S, generator=torch.Generator().manual_seed(1)) > 0.4
    good, _ = m.hybrid_loss(out, x, obs)
    bad, _ = m.hybrid_loss(out, x + 5.0, obs)
    assert torch.isfinite(good.detach())
    assert torch.isfinite(bad.detach())
    assert float(bad.detach()) > float(good.detach())


def test_trimmed_loss_is_not_larger_than_untrimmed():
    m = _model()
    x, pv = _batch(b=2)
    out = m(x, pv)
    obs = torch.ones(2, T, C, S, S, dtype=torch.bool)
    plain, _ = m.hybrid_loss(out, x + 3.0, obs)
    trimmed, _ = m.hybrid_loss(out, x + 3.0, obs, trimmed_top_frac=0.05)
    assert float(trimmed.detach()) <= float(plain.detach()) + 1e-6


def test_loss_ignores_unobserved_pixels():
    """Changing an unobserved target cannot change the loss."""
    m = _model()
    x, pv = _batch(b=1)
    out = m(x, pv)
    obs = torch.zeros(1, T, C, S, S, dtype=torch.bool)
    obs[:, :, :, 8:24, 8:24] = True
    a, _ = m.hybrid_loss(out, x, obs)
    t2 = x.clone()
    t2[:, :, :, :8, :] = 99.0
    b, _ = m.hybrid_loss(out, t2, obs)
    assert float(a.detach()) == float(b.detach())


# --- 1.2 parameter gates --------------------------------------------------
def test_cnn_variant_is_inside_the_param_band():
    rep = _model(use_cnn=True).param_report()
    assert rep["within_target_band"], rep
    assert rep["under_hard_ceiling"], rep
    assert abs(rep["n_parameters"] - TARGET_PARAMS) <= 0.20 * TARGET_PARAMS


def test_pixelwise_control_is_cheaper_but_under_the_ceiling():
    cnn = _model(use_cnn=True).param_report()["n_parameters"]
    px = _model(use_cnn=False).param_report()["n_parameters"]
    assert px < cnn
    assert px <= HARD_PARAM_CEILING


def test_scorer_ids_match_the_eval_arm_names():
    assert scorer_id(True) == "patch_cnn_gru"
    assert scorer_id(False) == "patch_pixelwise"


# --- gradient flow --------------------------------------------------------
def test_gradients_reach_stem_and_gru():
    m = build_patch_model(use_cnn=True)
    m.train()
    x, pv = _batch(b=2)
    out = m(x, pv)
    obs = torch.ones(2, T, C, S, S, dtype=torch.bool)
    loss, _ = m.hybrid_loss(out, x, obs)
    loss.backward()
    g_stem = m.stem.conv1.weight.grad
    g_gru = m.gru.weight_ih_l0.grad
    assert g_stem is not None
    assert torch.isfinite(g_stem).all()
    assert g_gru is not None
    assert torch.isfinite(g_gru).all()
    assert float(g_stem.abs().sum()) > 0


def test_shape_errors_are_loud():
    m = _model()
    x, pv = _batch(b=1)
    with pytest.raises(ValueError, match="channel"):
        m(x[:, :, :5], pv)
    with pytest.raises(ValueError, match="channels, model expects"):
        m.stem_input(torch.zeros(1, T, 3, S, S), pv)
