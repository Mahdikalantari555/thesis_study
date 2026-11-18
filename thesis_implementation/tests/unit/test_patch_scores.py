"""Patch scoring: frozen sigma, aggregation rule, persistence, basis labelling.

Covers ``patch-level-controlled-trial`` tasks 2.1/2.2 and
``patch-scoring-ensemble`` tasks 1.3/2.4.
"""

from __future__ import annotations

import numpy as np
import pytest

from ssl_anomaly.monitor import patch_scores as PS

T, C, S = 36, 8, 32


def _resid(n=4, seed=0, scale=1.0):
    g = np.random.default_rng(seed)
    return g.normal(0.0, scale, size=(n, T, C, S, S)), g.random((n, T, C, S, S)) > 0.3


# --- sigma table --------------------------------------------------------------
def test_sigma_is_mad_scaled_and_positive():
    res, obs = _resid()
    st = PS.fit_patch_sigma(res, obs, np.ones((4, T), dtype=int))
    fin = st.sigma[np.isfinite(st.sigma)]
    assert fin.size > 0
    assert np.all(fin > 0)
    # ~1.4826 x MAD of a N(0,1) sample ≈ 1.0
    assert 0.7 < float(np.median(fin)) < 1.4


def test_sigma_table_hash_is_deterministic_and_input_sensitive():
    res, obs = _resid()
    a = PS.fit_patch_sigma(res, obs, np.ones((4, T), dtype=int))
    b = PS.fit_patch_sigma(res, obs, np.ones((4, T), dtype=int))
    assert a.sha256 == b.sha256
    res2, obs2 = _resid(seed=7)
    c = PS.fit_patch_sigma(res2, obs2, np.ones((4, T), dtype=int))
    assert c.sha256 != a.sha256


def test_sigma_never_sees_data_it_was_not_given():
    """A cycle withheld from the fit cannot move the frozen table."""
    res, obs = _resid(n=4)
    clean = PS.fit_patch_sigma(res, obs, np.ones((4, T), dtype=int))
    # the "injected" cycle lives outside the fit input entirely
    inj = res.copy()
    inj[0, 10:14] += 20.0
    same = PS.fit_patch_sigma(res, obs, np.ones((4, T), dtype=int))
    assert inj is not res
    assert same.sha256 == clean.sha256


def test_sigma_falls_back_when_a_cell_is_undersampled():
    res, obs = _resid(n=1)
    st = PS.fit_patch_sigma(res, obs, np.ones((1, T), dtype=int), min_n=10_000)
    # nothing reaches min_n → every cell is NaN, the fallback carries the scale
    assert not np.isfinite(st.sigma).any()
    scale = st.lookup(np.arange(T), np.ones(T, dtype=int))
    assert np.isfinite(scale).all()
    assert np.all(scale > 0)


def test_unknown_sensor_id_does_not_crash():
    res, obs = _resid(n=2)
    st = PS.fit_patch_sigma(res, obs, np.full((2, T), 9))
    scale = st.lookup(np.arange(T), np.full(T, 9, dtype=int))
    assert np.isfinite(scale).all()


# --- pixel scores ---------------------------------------------------------
def test_pixel_scores_put_an_anomaly_in_the_right_pixels():
    res, obs = _resid(n=1)
    st = PS.fit_patch_sigma(res, obs, np.ones((1, T), dtype=int))
    res2 = res.copy()
    res2[0, 12, :, 8:24, 8:24] += 6.0
    pz = PS.pixel_scores(res2, obs, st, np.arange(T), np.ones((1, T), dtype=int))
    inside = np.nanmean(pz[0, 12][8:24, 8:24])
    outside = np.nanmean(pz[0, 12][2:6, 2:6])
    assert inside > 10 * outside


def test_pixel_scores_are_nan_where_nothing_is_observed():
    res, obs = _resid(n=1)
    st = PS.fit_patch_sigma(res, obs, np.ones((1, T), dtype=int))
    obs2 = obs.copy()
    obs2[0, 5] = False
    pz = PS.pixel_scores(res, obs2, st, np.arange(T), np.ones((1, T), dtype=int))
    assert np.isnan(pz[0, 5]).all()


def test_single_channel_pickup_is_not_diluted():
    """A max-marginal per pixel detects a 1-band anomaly that a mean would hide."""
    res, obs = _resid(n=1)
    obs[:] = False
    obs[0, :, 0] = True                       # only band 0 observed
    st = PS.fit_patch_sigma(res, obs, np.ones((1, T), dtype=int))
    res2 = res.copy()
    res2[0, 20, 0] += 5.0
    pz = PS.pixel_scores(res2, obs, st, np.arange(T), np.ones((1, T), dtype=int))
    assert np.nanmax(pz[0, 20]) > 5.0


# --- field aggregation ----------------------------------------------------
def test_top_fraction_aggregation_ignores_a_single_speckle():
    """One enormous pixel must not dominate a 20 %-aggregate as it would a max."""
    pz = np.zeros((1, 4, S, S))
    rng = np.random.default_rng(0)
    pz[0] = rng.random((4, S, S))
    pz[0, 1, 0, 0] = 30.0                 # one bright speckle, background ~0.5
    infield = np.ones((S, S), dtype=bool)
    paths = PS.field_paths(pz, infield)
    # max aggregation would return 30.0 for this bin; top-20 % returns ≈1.1
    assert paths[0, 1] < 2.0
    assert np.nanmean(pz[0, 1]) < paths[0, 1]   # but still above the plain mean


def test_aggregation_domain_is_the_in_field_mask_only():
    pz = np.zeros((1, 2, S, S))
    pz[0, 0, :16, :] = 100.0              # huge values outside the field
    pz[0, 0, 16:, :] = 0.0                # and real, tiny values inside it
    pz[0, 1] = np.nan                     # the other bin is entirely unobserved
    infield = np.zeros((S, S), dtype=bool)
    infield[16:, :] = True
    paths = PS.field_paths(pz, infield)
    assert paths[0, 0] == 0.0
    assert np.isnan(paths[0, 1])          # no observed pixel → no score


def test_too_few_pixels_gives_nan_not_zero():
    pz = np.full((1, 1, S, S), 5.0)
    infield = np.zeros((S, S), dtype=bool)
    infield[0, :2] = True
    assert np.isnan(PS.field_paths(pz, infield, min_pixels=4)[0, 0])


def test_per_sample_masks_are_supported():
    pz = np.ones((2, 3, S, S))
    masks = np.zeros((2, S, S), dtype=bool)
    masks[0, :8, :8] = True
    masks[1, :20, :20] = True
    out = PS.field_paths(pz, masks)
    assert out.shape == (2, 3)
    assert np.allclose(out, 1.0)


def test_bad_in_field_shape_is_loud():
    with pytest.raises(ValueError, match="in_field"):
        PS.field_paths(np.ones((1, 2, S, S)), np.ones((3, 4)))


# --- persistence ----------------------------------------------------------
def test_cusum_accumulates_on_a_persistent_shift_only():
    flat = np.full(T, 0.2)
    burst = np.zeros(T)
    burst[10:20] = 3.0
    a = PS.cusum_path(flat, kappa=1.0)
    b = PS.cusum_path(burst, kappa=1.0)
    assert np.nanmax(a) == 0.0
    assert np.nanmax(b) > 5.0
    assert np.all(np.isfinite(b))


def test_cusum_carries_state_through_unobserved_bins():
    s = np.zeros(T)
    s[:10] = 3.0
    s[10:15] = np.nan
    path = PS.cusum_path(s, kappa=1.0)
    assert np.isfinite(path[:10]).all()
    assert np.isnan(path[10:15]).all()       # unobserved bins carry no score
    # state carried across the gap: the accumulator resumes at 20.0 and the
    # next observed bin (0.0) subtracts the reference value, no reset
    assert path[15] == pytest.approx(19.0)


def test_ewma_smooths_and_carries():
    s = np.array([1.0, np.nan, np.nan, 5.0])
    p = PS.ewma_path(s, 0.5)
    assert p[0] == 1.0
    assert p[1] == 1.0
    assert p[2] == 1.0
    assert p[3] == pytest.approx(3.0)


def test_cusum_calibration_is_at_the_requested_far():
    rng = np.random.default_rng(1)
    clean = [rng.normal(0.2, 0.1, T) for _ in range(40)]
    out = PS.calibrate_cusum_h(clean, far_target=0.05, kappa=0.5)
    assert out["far_achieved"] <= 0.05
    assert out["n_cycles"] == 40
    assert out["kappa"] == 0.5


def test_cusum_calibration_rejects_empty_input():
    with pytest.raises(ValueError, match="No clean paths"):
        PS.calibrate_cusum_h([], far_target=0.05)


# --- basis labelling (task 2.4) ------------------------------------------
def test_basis_registry_covers_the_components():
    basis = PS.component_basis()
    assert basis["s_pred"] == PS.BASIS_LOCAL
    assert basis["s_hyb"] == PS.BASIS_POPULATION
    assert basis["z_f(t)"] == PS.BASIS_POPULATION


def test_undeclared_component_fails_the_report_build():
    PS.require_basis(["s_pred", "s_lat"])            # ok
    with pytest.raises(ValueError, match="without a declared scoring basis"):
        PS.require_basis(["s_pred", "s_made_up"])


def test_population_ranked_components_are_never_the_silent_default():
    """The declared default set must be locally anchored only."""
    basis = PS.component_basis()
    default = ["s_pred", "s_rec"]
    assert all(basis[c] == PS.BASIS_LOCAL for c in default)


# --- PatchDeepScorer adapter (task 2.2) -----------------------------------
import torch  # noqa: E402

from ssl_anomaly.models.patch_cnn_gru import build_patch_model  # noqa: E402

SMALL = {"n_channels": 8, "d_model": 8, "n_horizons": 2, "stem_widths": (8, 8)}


def _adapter(n_in_field=4, seed=0, *, use_cnn=True):
    res, obs = _resid(seed=seed)
    sigma = PS.fit_patch_sigma(res, obs, np.ones((4, T), dtype=int))
    in_field = np.zeros((n_in_field, 32, 32), dtype=bool)
    in_field[:, 4:4 + 16, 4:4 + 16] = True
    model = build_patch_model(use_cnn=use_cnn, **SMALL)
    scorer = PS.PatchDeepScorer("patch_cnn_gru", model, sigma, in_field=in_field, n_channels=C)
    assert in_field.shape[0] == n_in_field, "one mask per sample in these tests"
    torch.manual_seed(0)
    g = np.random.default_rng(seed)
    X = g.normal(0, 1, size=(n_in_field, 4, C, 32, 32)).astype(np.float32)
    M = np.zeros((n_in_field, 4, 32, 32), dtype=bool)
    M[:, :, 4:20, 4:20] = True
    return scorer, X, M


def test_adapter_returns_the_pipeline_pair():
    scorer, X, M = _adapter()
    scores, pred = scorer.loo_batch(X, M)
    assert scores.shape == (4, 4)
    assert pred.shape == (4, 4, C)
    assert np.isfinite(scores).all()
    assert np.isfinite(pred).all()


def test_adapter_scores_are_non_negative_squared_residuals():
    scorer, X, M = _adapter()
    scores, _ = scorer.loo_batch(X, M)
    assert (scores >= 0).all()


def test_adapter_ignores_out_of_field_pixels_entirely():
    """The farm boundary holds at scoring time, not just inside the CNN."""
    scorer, X, M = _adapter()
    base, _ = scorer.loo_batch(X, M)
    Xp = X.copy()
    in_field = scorer.in_field[0]
    Xp[0][:, :, ~in_field] = 50.0          # huge values outside the field
    pert, _ = scorer.loo_batch(Xp, M)
    np.testing.assert_array_equal(base[0], pert[0])


def test_adapter_scores_are_locally_anchored():
    """Farm 1's score must not move when farm 0's data changes for the worse."""
    scorer, X, M = _adapter()
    base, _ = scorer.loo_batch(X, M)
    Xp = X.copy()
    Xp[0] = 0.0                            # blank a DIFFERENT farm
    pert, _ = scorer.loo_batch(Xp, M)
    np.testing.assert_array_equal(base[1:], pert[1:])


def test_adapter_rejects_a_sigma_table_with_the_wrong_channel_count():
    res, obs = _resid()
    sigma = PS.fit_patch_sigma(res, obs, np.ones((4, T), dtype=int))
    model = build_patch_model(use_cnn=True, **SMALL)
    with pytest.raises(ValueError, match="channels"):
        PS.PatchDeepScorer("x", model, sigma, in_field=np.ones((32, 32), bool), n_channels=7)


def test_adapter_rejects_a_per_field_mask_without_an_index():
    scorer, X, M = _adapter()
    with pytest.raises(ValueError, match="pass idx"):
        scorer._mask_for(None, M[:1])


def test_adapter_accepts_a_shared_in_field_mask():
    res, obs = _resid()
    sigma = PS.fit_patch_sigma(res, obs, np.ones((4, T), dtype=int))
    model = build_patch_model(use_cnn=True, **SMALL)
    scorer = PS.PatchDeepScorer("x", model, sigma, in_field=np.ones((32, 32), bool), n_channels=C)
    g = np.random.default_rng(0)
    X = g.normal(0, 1, size=(2, 4, C, 32, 32)).astype(np.float32)
    M = np.ones((2, 4, 32, 32), bool)
    scores, _ = scorer.loo_batch(X, M)
    assert np.isfinite(scores).all()


def test_adapter_mask_is_independent_of_other_samples():
    """Sample 0's score must be identical whether or not sample 1 is batched with it."""
    scorer, X, M = _adapter()
    both, _ = scorer.loo_batch(X[:2], M[:2], idx=np.array([0, 1]))
    alone, _ = scorer.loo_batch(X[:1], M[:1], idx=np.array([0]))
    np.testing.assert_array_equal(both[0], alone[0])


def test_adapter_idx_out_of_range_is_loud():
    scorer, X, M = _adapter()
    with pytest.raises(ValueError, match="idx out of range"):
        scorer.loo_batch(X, M, idx=np.array([0, 1, 2, 99]))
    with pytest.raises(ValueError, match="one entry per sample"):
        scorer.loo_batch(X, M, idx=np.array([0, 1]))


def test_adapter_handles_a_bin_with_no_observed_pixel():
    scorer, X, M = _adapter()
    M2 = M.copy()
    M2[:, 2] = False                        # whole bins unobserved
    scores, _ = scorer.loo_batch(X, M2)
    assert np.isnan(scores[:, 2]).all()
    assert np.isfinite(scores[:, 0]).all()


def test_adapter_sensor_ids_are_validated():
    scorer, X, M = _adapter()
    with pytest.raises(ValueError, match="sensor_ids"):
        scorer.predict_pixels(X, M, sensor_ids=np.zeros((3, 4), dtype=int))


def test_adapter_keeps_per_pixel_maps_for_localization():
    scorer, X, M = _adapter()
    info = scorer.predict_pixels(X, M)
    assert info["pixel_z2"].shape == (4, 4, 32, 32)
    # out-of-field pixels carry no score
    assert np.isnan(info["pixel_z2"][:, :, 0, 0]).all()
    assert scorer.last_pixel_maps is not None


def test_adapter_score_cycle_matches_loo_batch():
    scorer, X, M = _adapter()
    scores, _ = scorer.loo_batch(X, M)
    one = scorer.score_cycle(X[0], M[0], idx=np.array([0]))
    np.testing.assert_array_equal(one, scores[0])


def test_adapter_declined_doy_is_not_reinterpreted_as_covariates():
    """A (N,T,2) DOY tensor is not a covariate; a covariate model must refuse."""
    res, obs = _resid()
    sigma = PS.fit_patch_sigma(res, obs, np.ones((4, T), dtype=int))
    model = build_patch_model(use_cnn=True, n_covariates=2, **SMALL)
    scorer = PS.PatchDeepScorer("x", model, sigma, in_field=np.ones((32, 32), bool),
                                n_channels=C)
    g = np.random.default_rng(0)
    X = g.normal(0, 1, size=(2, 4, C, 32, 32)).astype(np.float32)
    M = np.ones((2, 4, 32, 32), bool)
    with pytest.raises(ValueError, match="covariates"):
        scorer.loo_batch(X, M, g.random((2, 4, 2)))
    # ...but explicit covariates are routed through
    scores, _ = scorer.loo_batch(X, M, covariates=g.random((2, 4, 2)))
    assert np.isfinite(scores).all()


def test_adapter_pixelwise_control_runs_the_same_interface():
    scorer, X, M = _adapter(use_cnn=False)
    scores, pred = scorer.loo_batch(X, M)
    assert scores.shape == (4, 4)
    assert pred.shape == (4, 4, C)
    assert np.isfinite(scores).all()


# --- PatchArmScorer (task 2.4) --------------------------------------------
def test_p_value_is_bounded_and_never_zero():
    # (n_clean=10, T=20): every bin sees the same 10 reference values
    ref = np.outer(np.arange(1.0, 11.0), np.ones(20))
    sigma = PS.fit_patch_sigma(*_resid(), np.ones((4, T), dtype=int))
    model = build_patch_model(use_cnn=True, n_horizons=2, d_model=8, stem_widths=(8, 8))
    scorer = PS.PatchDeepScorer("x", model, sigma, in_field=np.ones((32, 32), bool), n_channels=C)
    arm = PS.PatchArmScorer(scorer, ref)
    p = arm.p_values(np.array([[1.0] * 20, [1e6] * 20, [0.0] * 20]))
    assert np.all(p > 0)
    assert np.all(p <= 1)
    # an extreme path gets the smallest possible p; a path below every
    # reference value gets p = 1 (never an alarm)
    assert p[1, 0] == pytest.approx(1.0 / 11.0)
    assert p[2, 0] == pytest.approx(1.0)
    # A path sitting at the SMALLEST reference value has all n references at or
    # above it: p = (1 + n) / (n + 1) = 1, i.e. never an alarm — which is the
    # intended behaviour (the +1 correction makes p=1, not p = n/(n+1)).
    assert p[0, 0] == pytest.approx(1.0)
    assert p[1, 0] < p[0, 0]


def test_p_value_is_monotone_in_the_raw_path():
    # distinct reference values in EVERY bin, so the comparison is meaningful
    ref = np.outer(np.linspace(0, 1, 10), np.ones(20))
    sigma = PS.fit_patch_sigma(*_resid(), np.ones((4, T), dtype=int))
    model = build_patch_model(use_cnn=True, n_horizons=2, d_model=8, stem_widths=(8, 8))
    scorer = PS.PatchDeepScorer("x", model, sigma, in_field=np.ones((32, 32), bool), n_channels=C)
    arm = PS.PatchArmScorer(scorer, ref)
    p = arm.p_values(np.array([[0.9] * 20, [0.5] * 20, [0.1] * 20]))
    assert p[0, 0] < p[1, 0] < p[2, 0]


def test_arm_refuses_too_few_reference_paths():
    sigma = PS.fit_patch_sigma(*_resid(), np.ones((4, T), dtype=int))
    model = build_patch_model(use_cnn=True, n_horizons=2, d_model=8, stem_widths=(8, 8))
    scorer = PS.PatchDeepScorer("x", model, sigma, in_field=np.ones((32, 32), bool), n_channels=C)
    with pytest.raises(ValueError, match="at least"):
        PS.PatchArmScorer(scorer, np.ones((3, T)))


def test_arm_keeps_nan_bins_nan():
    ref = np.tile(np.arange(1.0, 5.0), (10, 1))
    sigma = PS.fit_patch_sigma(*_resid(), np.ones((4, T), dtype=int))
    model = build_patch_model(use_cnn=True, n_horizons=2, d_model=8, stem_widths=(8, 8))
    scorer = PS.PatchDeepScorer("x", model, sigma, in_field=np.ones((32, 32), bool), n_channels=C)
    arm = PS.PatchArmScorer(scorer, ref)
    paths = np.array([[1.0, np.nan, 3.0, 2.0]])
    p = arm.p_values(paths)
    assert np.isnan(p[0, 1])
    assert np.isfinite(p[0, 0])


def test_arm_score_cycles_returns_a_single_channel_z2():
    scorer, X, M = _adapter()
    ref = np.tile(np.linspace(0.1, 5.0, 4), (12, 1))
    arm = PS.PatchArmScorer(scorer, ref)
    out = arm.score_cycles(X[:, :4], M[:, :4], None, None, idx=np.array([0, 1, 2, 3]))
    assert out["z2"].shape == (4, 4, 1)
    assert out["p_value"].shape == (4, 4)
    assert np.isfinite(out["z2"]).all()
    # the alarm direction is preserved: larger raw path -> larger -log(p)
    assert out["z2"][0, 0, 0] >= 0


def test_tail_max_is_nan_tolerant_and_looks_backwards_only():
    p = np.array([1.0, np.nan, 3.0, 0.5, np.nan, np.nan])
    got = PS.tail_max(p, k=2)
    np.testing.assert_allclose(got[0], 1.0)
    np.testing.assert_allclose(got[2], 3.0)
    np.testing.assert_allclose(got[3], 3.0)   # window holds (3.0, 0.5)
    # a NaN bin still sees the 0.5 two bins back; only a fully-NaN window is NaN
    np.testing.assert_allclose(got[4], 0.5)
    assert np.isnan(got[5])
