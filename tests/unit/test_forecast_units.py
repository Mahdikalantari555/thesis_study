"""Forecast-unit probe forecaster tests (change forecast-unit-probe, task 1.1).

The untrained causal forecasters (persist / med3 / trend4) are PRE-REGISTERED
arms: causality (bin o predicted from observed bins < o only), the gap rule
(observed-bin distance > 2 breaks the history → NaN), NaN-on-insufficient-
history semantics, and trend4's exactness / med3's robustness on synthetic
series are the invariants the probe's decision rests on.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import forecast_units as funits  # noqa: E402

ARMS = ("persist", "med3", "trend4")


# ---------------------------------------------------------------------------
# Causality invariant: perturbing bins ≥ o never changes the prediction at o
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("arm", ARMS)
def test_causality_prediction_at_o_never_sees_bins_ge_o(arm: str) -> None:
    rng = np.random.default_rng(7)
    T, C = 36, 3
    z = rng.normal(size=(T, C))
    mask = np.ones((T, C), dtype=bool)
    base = funits.forecast_batch(arm, z[None], mask[None])[0]
    for o in range(1, T):
        z2 = z.copy()
        z2[o:] = rng.normal(size=(T - o, C)) * 10.0  # perturb bins ≥ o
        pert = funits.forecast_batch(arm, z2[None], mask[None])[0]
        if np.isfinite(base[o]).any():
            np.testing.assert_allclose(pert[o], base[o], atol=1e-12)
    # The very first bin has no history → NaN for every arm.
    assert np.all(np.isnan(base[0]))


@pytest.mark.parametrize("arm", ARMS)
def test_causality_per_channel_independence(arm: str) -> None:
    """A channel's prediction uses that channel's history only (pre-registered
    arm definition: no cross-channel features)."""
    rng = np.random.default_rng(11)
    T, C = 24, 4
    z = rng.normal(size=(1, T, C))
    mask = np.ones((1, T, C), dtype=bool)
    base = funits.forecast_batch(arm, z, mask)[0]
    z2 = z.copy()
    z2[:, :, 1] += 100.0  # perturb channel 1 only
    pert = funits.forecast_batch(arm, z2, mask)[0]
    np.testing.assert_allclose(pert[:, 0], base[:, 0], atol=1e-12)
    np.testing.assert_allclose(pert[:, 2], base[:, 2], atol=1e-12)


# ---------------------------------------------------------------------------
# Mask / gap handling
# ---------------------------------------------------------------------------
def test_persist_last_observed_value_and_bridging() -> None:
    T = 12
    z = np.arange(T, dtype=np.float64)[None, :, None] * 1.0  # z[b] = b
    mask = np.ones((1, T, 1), dtype=bool)
    pred = funits.forecast_batch("persist", z, mask)[0, :, 0]
    # Observed everywhere → pred(o) = o − 1 (last observed bin).
    np.testing.assert_allclose(pred[1:], np.arange(T - 1))
    assert np.isnan(pred[0])
    # One unobserved bin: gap of 1 ≤ 2 → bridged by the previous observed value.
    mask2 = mask.copy()
    mask2[0, 5, 0] = False
    pred2 = funits.forecast_batch("persist", z, mask2)[0, :, 0]
    assert pred2[5] == 4.0  # bridge over the unobserved bin 5
    assert pred2[6] == 4.0  # last observed bin < 6 is still 4
    # A gap of 3 bins (observed ≤ 4, next observed at 8) breaks history → NaN at 8.
    mask3 = mask.copy()
    mask3[0, 5:8, 0] = False
    pred3 = funits.forecast_batch("persist", z, mask3)[0, :, 0]
    assert pred3[4] == 3.0
    assert np.isnan(pred3[8])  # distance from the last observed bin (4) is 4 > 2
    # History restarts after the break: pred at 9 = z[8].
    assert pred3[9] == 8.0


def test_gap_gt2_breaks_history_for_all_arms() -> None:
    """An observed-bin distance > 2 breaks the window for every arm → NaN at
    the first bin after the gap; med3/trend4 may still score later bins but
    only from post-break history."""
    T = 14
    z = np.ones((T, 1)) * 5.0
    z[:5, 0] = 1.0  # pre-gap level
    mask = np.ones((1, T, 1), dtype=bool)
    mask[0, 5:8, 0] = False  # observed bins: 0–4, then 8+
    for arm in ARMS:
        pred = funits.forecast_batch(arm, z[None], mask)[0, :, 0]
        assert np.isnan(pred[8]), f"{arm} must not extrapolate across the gap"


def test_nan_on_insufficient_history() -> None:
    """persist/med3 need ≥1 history bin; trend4 needs a 4-bin window."""
    T = 10
    z = np.ones((1, T, 1))
    mask = np.ones((1, T, 1), dtype=bool)
    assert np.isnan(funits.forecast_batch("persist", z, mask)[0, 0, 0])
    assert np.isnan(funits.forecast_batch("med3", z, mask)[0, 0, 0])
    # trend4 needs 4 observed bins in the window: bins 1–3 → NaN, bin 4 → score.
    pred_t = funits.forecast_batch("trend4", z, mask)[0, :, 0]
    assert np.all(np.isnan(pred_t[1:4]))
    assert np.isfinite(pred_t[4])
    # Unobserved bins never contribute history (mask respected): the
    # prediction written AT an unobserved bin is unused by the consumer
    # (the statistic multiplies residuals by the mask), but bin 4's history
    # must exclude bin 3's value.
    mask2 = mask.copy()
    mask2[0, 3, 0] = False
    z3 = z.copy()
    z3[0, 3, 0] = 999.0  # garbage at the unobserved bin — must never leak
    pred = funits.forecast_batch("med3", z3, mask2)[0, :, 0]
    assert pred[4] == 1.0  # median of the observed history (no 999)


def test_trend4_uses_only_the_gap_connected_window() -> None:
    """trend4's 4-bin window is cut at a >2-bin break: with observed bins
    0,1,2,3 (level 1) and 10,11,12,13 (level 9), the prediction at 13 uses
    only bins 10–12 + 13's own window (post-break), NOT the pre-gap bins."""
    T = 14
    z = np.ones((T, 1))
    z[10:, 0] = 9.0
    mask = np.ones((1, T, 1), dtype=bool)
    mask[0, 4:10, 0] = False  # break between bin 3 and bin 10
    pred = funits.forecast_batch("trend4", z[None], mask)[0, :, 0]
    # Window for bin 12 = observed bins 10, 11 (size 2 < 4) → NaN.
    assert np.isnan(pred[12])
    # Window for bin 13 = 10, 11, 12 (size 3 < 4) → NaN; trend4 never bridges
    # the break to reach 4 bins.
    assert np.isnan(pred[13])


# ---------------------------------------------------------------------------
# trend4 exactness / med3 robustness on synthetic series
# ---------------------------------------------------------------------------
def test_trend4_exact_on_linear_series() -> None:
    """A perfect linear series is extrapolated exactly (OLS on the last 4
    observed bins, one step ahead)."""
    T = 20
    a, b = 3.0, 0.5
    t = np.arange(T, dtype=np.float64)
    z = (a + b * t)[None, :, None]
    mask = np.ones((1, T, 1), dtype=bool)
    pred = funits.forecast_batch("trend4", z, mask)[0, :, 0]
    ok = np.isfinite(pred)
    np.testing.assert_allclose(pred[ok], (a + b * t[ok]), rtol=1e-10, atol=1e-10)


def test_trend4_flat_series_predicts_the_level() -> None:
    T = 12
    z = np.full((1, T, 1), 7.5)
    mask = np.ones((1, T, 1), dtype=bool)
    pred = funits.forecast_batch("trend4", z, mask)[0, :, 0]
    ok = np.isfinite(pred)
    np.testing.assert_allclose(pred[ok], 7.5, atol=1e-12)


def test_med3_robust_to_single_outlier_in_history() -> None:
    """median-of-last-3 is unaffected by one outlier where persist is not."""
    T = 10
    z = np.full((1, T, 1), 10.0)
    mask = np.ones((1, T, 1), dtype=bool)
    z[0, 6, 0] = 1000.0  # single outlier bin
    med3 = funits.forecast_batch("med3", z, mask)[0, :, 0]
    persist = funits.forecast_batch("persist", z, mask)[0, :, 0]
    assert med3[7] == 10.0  # median{z4,z5,z6} = median{10,10,1000}
    assert med3[8] == 10.0  # median{z5,z6,z7} = median{10,1000,10}
    assert persist[7] == 1000.0  # persist carries the outlier (by definition)


def test_med3_median_of_last_up_to_three() -> None:
    T = 8
    z = np.array([1.0, 2.0, 3.0, 10.0, 20.0, 30.0, 40.0, 50.0])[None, :, None]
    mask = np.ones((1, T, 1), dtype=bool)
    pred = funits.forecast_batch("med3", z, mask)[0, :, 0]
    assert pred[1] == 1.0           # history {1}
    assert pred[2] == 1.5           # median{1,2}
    assert pred[3] == 2.0           # median{1,2,3}
    assert pred[4] == 3.0           # median{2,3,10}
    assert pred[5] == 10.0          # median{3,10,20}


# ---------------------------------------------------------------------------
# Batch entry point / output contract
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("arm", ARMS)
def test_batch_shape_and_history_contract(arm: str) -> None:
    """Batch contract: shape preserved; unobserved values never enter the
    history (a prediction sits at an unobserved bin too, but it is derived
    from observed bins < o only — the consumer's mask gates its use); the
    first observed bin of each channel has no history → NaN."""
    rng = np.random.default_rng(3)
    N, T, C = 5, 36, 8
    z = rng.normal(size=(N, T, C))
    mask = rng.random((N, T, C)) > 0.2
    pred = funits.forecast_batch(arm, z, mask)
    assert pred.shape == (N, T, C)
    # No observed bin before o + gap-broken history → NaN at o.
    for n in range(N):
        for c in range(C):
            obs = np.where(mask[n, :, c])[0]
            if obs.size == 0:
                assert np.all(np.isnan(pred[n, :, c]))
                continue
            assert np.isnan(pred[n, obs[0], c])  # first observed bin: no history
            for o in range(obs[0] + 1, T):
                last = obs[obs < o][-1]
                if o - last > 2:
                    assert np.isnan(pred[n, o, c])


def test_unknown_arm_raises() -> None:
    z = np.ones((1, 6, 1))
    mask = np.ones((1, 6, 1), dtype=bool)
    with pytest.raises(ValueError):
        funits.forecast_batch("bogus", z, mask)
