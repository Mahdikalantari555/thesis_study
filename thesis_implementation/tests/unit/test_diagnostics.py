"""Signal-path decomposition tests (change reconstruction-invariance-diagnostic, task 1.1).

The decomposition mirrors the production statistic exactly (causal_offset_correct
→ cell q95 → cumulative_channel_max) so stage quantities and detection flags are
consistent with the severity sweep.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import diagnostics as mdiag  # noqa: E402
from ssl_anomaly.monitor import scoring as mscoring  # noqa: E402

T, C = 36, 8
CH = 0


def make_cycle(pred_level: float = 0.0, resid_tail: float = 0.0) -> tuple:
    """Hand-made cycle: prediction = pred_level everywhere (z units); the
    natural value equals the prediction (zero clean residual) unless
    resid_tail adds a constant field residual to the last bins."""
    z = np.zeros((T, C), dtype=np.float64)
    pred = np.full((T, C), pred_level, dtype=np.float64)
    z[:, :] = pred_level
    if resid_tail:
        z[max(0, 10):18, CH] += resid_tail  # preceding-history residual (z units)
        pred[max(0, 10):18, CH] = pred_level  # prediction stays; residual = resid_tail
    mask = np.ones((T, C), dtype=bool)
    z_nat = z.copy()
    return z, pred, mask, z_nat


def inject_drop(z: np.ndarray, onset: int, duration: int, delta_sigma: float) -> np.ndarray:
    z = z.copy()
    z[onset:onset + duration, CH] -= delta_sigma
    return z


def decompose(z_inj, pred, mask, z_nat, q95, tau, onset, duration, k=1):
    return mdiag.decompose_injection(
        z_inj=z_inj, pred_z=pred, z_natural=z_nat, mask=mask,
        q95=q95, tau=tau, k=k, onset_bin=onset, duration=duration, channel=CH,
    )


# ---------------------------------------------------------------------------
# Stage 1–4 waterfall on a hand-made cycle
# ---------------------------------------------------------------------------
def test_onset_residual_is_the_full_drop_with_clean_history() -> None:
    """Clean history (zero residuals) → the onset residual equals the drop in
    σ units and the offset subtraction is ~0."""
    z, pred, mask, z_nat = make_cycle()
    z_inj = inject_drop(z, onset=18, duration=1, delta_sigma=6.0)
    q95 = np.full((T, C), 2.0)
    d = decompose(z_inj, pred, mask, z_nat, q95, tau=6.0, onset=18, duration=1)
    assert d.onset_residual_sigma == pytest.approx(-6.0, abs=1e-6)  # signed (drop)
    assert d.offset_subtraction == pytest.approx(0.0, abs=1e-6)
    assert d.normalized_contribution == pytest.approx(36.0 / 2.0)
    assert d.snr1 == pytest.approx((36.0 / 2.0) / 6.0)


def test_offset_correction_subtracts_history_residual() -> None:
    """A constant −5σ residual on the preceding observed bins (field running
    below its baseline) is subtracted from the onset residual: the drop shrinks
    from −6σ to −1σ — the stage 2 loss channel (signed values stored)."""
    z, pred, mask, z_nat = make_cycle(resid_tail=-5.0)
    z_inj = inject_drop(z, onset=18, duration=1, delta_sigma=6.0)
    q95 = np.full((T, C), 2.0)
    d = decompose(z_inj, pred, mask, z_nat, q95, tau=6.0, onset=18, duration=1)
    assert d.onset_residual_sigma == pytest.approx(-6.0, abs=1e-6)
    assert d.offset_subtraction == pytest.approx(-5.0, abs=1e-6)
    assert d.residual_after_correction == pytest.approx(-1.0, abs=1e-6)
    assert d.normalized_contribution == pytest.approx(1.0 / 2.0)


def test_trailing_window_dilutes_a_single_bin_spike() -> None:
    """Stage 4: with a 3-bin trailing mean and a 1-bin spike (neighbour bins
    clean, zero residual), the path at the onset is the contribution ÷ 3."""
    z, pred, mask, z_nat = make_cycle()
    z_inj = inject_drop(z, onset=18, duration=1, delta_sigma=6.0)
    q95 = np.full((T, C), 2.0)
    d = decompose(z_inj, pred, mask, z_nat, q95, tau=6.0, onset=18, duration=1)
    assert d.path_max_window == pytest.approx((36.0 / 2.0) / 3.0, rel=1e-6)
    assert d.detected is False  # (36/2)/3 = 6 = τ boundary → not above; pick clearer numbers below


def test_persistent_spike_survives_aggregation() -> None:
    """A 3-bin −6σ drop: every trailing window inside the drop holds ≥1
    injected bin → path = contribution (no dilution) → detected when above τ."""
    z, pred, mask, z_nat = make_cycle()
    z_inj = inject_drop(z, onset=18, duration=3, delta_sigma=6.0)
    q95 = np.full((T, C), 2.0)
    d = decompose(z_inj, pred, mask, z_nat, q95, tau=6.0, onset=18, duration=3)
    assert d.path_max_window == pytest.approx(36.0 / 2.0, rel=1e-6)
    assert d.detected is True


def test_detection_matches_production_statistic() -> None:
    """The decomposition's `detected` flag must agree with the production
    first_alarm_bin on the same path (cross-check, spec scenario)."""
    rng = np.random.default_rng(0)
    z = rng.normal(0, 1, size=(T, C))
    pred = rng.normal(0, 1, size=(T, C))
    mask = np.ones((T, C), dtype=bool)
    z_nat = z.copy()
    z_inj = inject_drop(z, onset=20, duration=2, delta_sigma=4.0)
    q95 = np.full((T, C), 3.0)
    d = decompose(z_inj, pred, mask, z_nat, q95, tau=1.0, onset=20, duration=2)
    # Rebuild the production path independently.
    r = (z_inj - pred) * mask
    r_corr = mscoring.causal_offset_correct(r[None], mask[None])[0]
    z2 = (r_corr * r_corr) * mask
    path = mscoring.cumulative_channel_max(z2[None], mask[None], q95)[0]
    fb = mscoring.first_alarm_bin(path, tau=1.0, k=1, onset_bin=20)
    assert d.detected == (fb >= 0)


# ---------------------------------------------------------------------------
# Absorption (post-onset, spec scenario 'Absorption quantified')
# ---------------------------------------------------------------------------
def test_absorption_zero_when_prediction_stays_natural() -> None:
    z, pred, mask, z_nat = make_cycle()
    z_inj = inject_drop(z, onset=18, duration=5, delta_sigma=6.0)
    # Prediction equals the natural level everywhere → not absorbed.
    a = mdiag.absorption_ratio(pred, z_inj, z_nat, mask, bins=list(range(19, 23)), channel=CH)
    assert a == pytest.approx(0.0, abs=1e-6)


def test_absorption_one_when_prediction_tracks_injection() -> None:
    z, pred, mask, z_nat = make_cycle()
    z_inj = inject_drop(z, onset=18, duration=5, delta_sigma=6.0)
    pred_inj = pred.copy()
    pred_inj[19:23, CH] = z_inj[19:23, CH]  # prediction fully tracks the injected level
    a = mdiag.absorption_ratio(pred_inj, z_inj, z_nat, mask, bins=list(range(19, 23)), channel=CH)
    assert a == pytest.approx(1.0, abs=1e-6)


def test_absorption_nan_without_a_real_change() -> None:
    z, pred, mask, z_nat = make_cycle()
    z_inj = z.copy()  # nothing injected → denominator 0
    a = mdiag.absorption_ratio(pred, z_inj, z_nat, mask, bins=[19, 20, 21], channel=CH)
    assert np.isnan(a)


# ---------------------------------------------------------------------------
# Cell aggregation + decision attribution
# ---------------------------------------------------------------------------
def test_cell_summary_and_attribution() -> None:
    """Aggregating decompositions produces medians + IQR and a dominant-loss
    stage; the normalization stage is attributed when the contribution is
    below τ but the residual was born large."""
    z, pred, mask, z_nat = make_cycle()
    z_inj = inject_drop(z, onset=18, duration=1, delta_sigma=6.0)
    q95 = np.full((T, C), 50.0)  # outlier-inflated normalizer
    d = decompose(z_inj, pred, mask, z_nat, q95, tau=6.0, onset=18, duration=1)
    summary = mdiag.summarize_cells({"S6/acute/ndvi": [d]})
    cell = summary["S6/acute/ndvi"]
    assert cell["n"] == 1
    assert cell["onset_residual_sigma"]["median"] == pytest.approx(abs(d.onset_residual_sigma))
    assert cell["attributed_stage"] == "stage3_normalization"  # 36/50 < τ=6, residual born (6σ ≥ 3σ)
    assert cell["snr2"]["median"] == pytest.approx(d.snr2)


def test_attribution_prefers_stage1_for_small_residual() -> None:
    z, pred, mask, z_nat = make_cycle()
    z_inj = inject_drop(z, onset=18, duration=1, delta_sigma=1.0)  # small step
    q95 = np.full((T, C), 2.0)
    d = decompose(z_inj, pred, mask, z_nat, q95, tau=6.0, onset=18, duration=1)
    summary = mdiag.summarize_cells({"S1/acute/ndvi": [d]})
    assert summary["S1/acute/ndvi"]["attributed_stage"] == "stage1_residual"


# ---------------------------------------------------------------------------
# Stage-wise AUC-PR (task 1.1: raw onset residual vs final path ranking power)
# ---------------------------------------------------------------------------
def test_aucpr_perfect_separation() -> None:
    """Injected scores all above clean scores → AUC-PR 1.0 (each stage)."""
    assert mdiag.aucpr_stage([5.0, 4.0, 3.0], [1.0, 0.5, 0.2]) == pytest.approx(1.0)


def test_aucpr_known_mixed_case() -> None:
    """Hand-computed average precision: scores desc 0.9(pos) 0.8(neg) 0.2(pos)
    0.1(neg) → AP = 1.0·0.5 + (2/3)·0.5 = 0.8333."""
    assert mdiag.aucpr_stage([0.9, 0.2], [0.8, 0.1]) == pytest.approx(0.8333333, abs=1e-4)


def test_aucpr_reversed_ranking_is_low() -> None:
    """Clean scores above injected scores → poor ranking power (< 0.5)."""
    assert mdiag.aucpr_stage([0.1, 0.2], [0.8, 0.9]) < 0.5


def test_aucpr_nan_without_two_classes() -> None:
    """Degenerate inputs (no negatives / no positives) → NaN, not a crash."""
    assert np.isnan(mdiag.aucpr_stage([1.0, 2.0], []))
    assert np.isnan(mdiag.aucpr_stage([], [1.0, 2.0]))
