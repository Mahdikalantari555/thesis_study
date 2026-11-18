"""Trial parts A/C/D helper tests (change predictive-ssl-controlled-trial).

Pure-function invariants behind the four-part evaluation: per-field alarm
concentration, temporal stability, the three-checkpoint error profile, and
the TVDI feature-space proxy built from existing per-scene field statistics.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import trial_parts as tp  # noqa: E402


# ---------------------------------------------------------------------------
# Part A helpers
# ---------------------------------------------------------------------------
def test_field_score_distribution_and_concentration() -> None:
    tau = 10.0
    paths = np.full((6, 12), np.nan)
    # Field 1 (cycles 0–3): maxima 8, 12, 9, 20 → 2 flagged
    for i, v in enumerate([8.0, 12.0, 9.0, 20.0]):
        paths[i, :] = v
    # Field 2 (cycles 4–5): maxima 1, 2 → 0 flagged
    paths[4, :] = 1.0
    paths[5, :] = 2.0
    field_ids = np.array([1, 1, 1, 1, 2, 2])
    out = tp.field_score_distribution(paths, tau, field_ids)
    assert out["n_fields"] == 2
    assert out["n_flagged_cycles_total"] == 2
    assert out["fields_with_flags"] == 1
    assert out["top2_field_flag_share"] == 1.0  # all flags in field 1
    assert out["per_field"]["1"]["n_cycles"] == 4
    assert abs(out["per_field"]["1"]["max_over_tau"] - 2.0) < 1e-12
    assert abs(out["per_field"]["2"]["median_max_over_tau"] - 0.15) < 1e-12


def test_temporal_stability_quiet_cycle_has_no_above_tau_bins() -> None:
    tau = 5.0
    paths = np.array([
        np.linspace(1.0, 2.0, 10),          # quiet, low noise
        np.array([1, 2, 6, 1, 1, 1, 1, 1, 1, 1], dtype=float),  # one excursion
    ])
    out = tp.temporal_stability(paths, tau)
    assert out["n_cycles_scored"] == 2
    assert out["above_tau_bins_per_cycle_median"] == 0.5
    assert out["above_tau_bins_per_cycle_max"] == 1


def test_determinism_check_counts_differences() -> None:
    a = np.array([[1.0, np.nan], [3.0, 4.0]])
    assert tp.determinism_check(a, a.copy()) == 0
    b = a.copy()
    b[0, 0] = 1.5
    b[1, 1] = np.nan
    assert tp.determinism_check(a, b) == 2  # one value diff + one NaN-pattern diff


# ---------------------------------------------------------------------------
# Part C — three-checkpoint error profile
# ---------------------------------------------------------------------------
def _mk_cycle(level_nat: float, level_inj: float, drop: float, onset: int = 10) -> tuple:
    """Natural cycle at level_nat; injected drops by `drop` from onset.
    Predictions: natural follows nat perfectly; injected prediction absorbs
    half the drop from onset+1 on (the gru_ae-like behaviour)."""
    T, C = 36, 8
    z_nat = np.full((T, C), level_nat)
    z_inj = np.full((T, C), level_nat)
    z_inj[onset:onset + 5, :] = level_inj - drop
    pred_nat = z_nat.copy()
    pred_inj = z_inj.copy()
    pred_inj[onset, :] = level_nat                       # onset: full residual
    pred_inj[onset + 1:onset + 5, :] = level_inj - drop / 2  # half absorbed
    mask = np.ones((T, C), dtype=bool)
    q95 = np.full((T, C), 0.25)  # forecast-sigma = 0.5 in raw terms
    return z_inj, pred_inj, z_nat, pred_nat, mask, q95, onset


def test_checkpoint_errors_persisting_predictive_error() -> None:
    """A prediction that NEVER absorbs (predictive ideal): post-step errors
    stay at the full drop → persistence_ratio = 1."""
    z_inj, pred_inj, z_nat, pred_nat, mask, q95, onset = _mk_cycle(10.0, 10.0, 2.0)
    pred_inj_persist = np.full_like(z_inj, 10.0)  # prediction stays at natural level
    out = tp.checkpoint_errors(z_inj, pred_inj_persist, z_nat, pred_nat, mask, q95, onset)
    assert out["usable"]
    assert abs(out["pre_error_z"]) < 1e-12
    assert abs(out["onset_step_error_z"] - 2.0) < 1e-12
    assert abs(out["post_steps_error_z"] - 2.0) < 1e-12
    assert abs(out["persistence_ratio"] - 1.0) < 1e-12
    assert abs(out["onset_step_error_fsigma"] - 4.0) < 1e-12  # 2.0 / 0.5


def test_checkpoint_errors_absorbing_prediction_decays() -> None:
    """Half-absorbing prediction: post errors = drop/2 → persistence_ratio 0.5."""
    z_inj, pred_inj, z_nat, pred_nat, mask, q95, onset = _mk_cycle(10.0, 10.0, 2.0)
    out = tp.checkpoint_errors(z_inj, pred_inj, z_nat, pred_nat, mask, q95, onset)
    assert abs(out["post_steps_error_z"] - 1.0) < 1e-12
    assert abs(out["persistence_ratio"] - 0.5) < 1e-12


def test_checkpoint_errors_unusable_when_onset_unobserved() -> None:
    z_inj, pred_inj, z_nat, pred_nat, mask, q95, onset = _mk_cycle(10.0, 10.0, 2.0)
    mask[onset, :] = False
    out = tp.checkpoint_errors(z_inj, pred_inj, z_nat, pred_nat, mask, q95, onset)
    assert not out["usable"]


# ---------------------------------------------------------------------------
# Part D — TVDI feature-space proxy
# ---------------------------------------------------------------------------
def test_tvdi_recovers_dry_and_wet_fields() -> None:
    """Across fields at one bin: high LST at the same NDVI → TVDI ≈ 1; low
    LST → TVDI ≈ 0 (feature-space sanity)."""
    N = 60
    rng = np.random.default_rng(3)
    ndvi = np.full((N, 4), np.nan)
    lst = np.full((N, 4), np.nan)
    nd = rng.uniform(0.2, 0.8, N)
    ndvi[:, 0] = nd
    lst[:, 0] = 25 + 10 * nd + rng.normal(0, 0.3, N)  # LST grows with NDVI
    tvdi, info = tp.tvdis_from_field_stats(ndvi, lst, n_ndvi_bins=5, min_points=8)
    assert info["n_bins_with_envelope"] == 1
    col = tvdi[:, 0]
    assert np.isfinite(col).sum() == N
    # The driest 10 % of fields sit near the dry edge → TVDI close to 1.
    dry_idx = np.argsort(-lst[:, 0])[:6]
    wet_idx = np.argsort(lst[:, 0])[:6]
    assert np.median(col[dry_idx]) > 0.8
    assert np.median(col[wet_idx]) < 0.2
    assert col.min() >= 0.0 and col.max() <= 1.0


def test_tvdi_nan_without_enough_fields() -> None:
    ndvi = np.array([[0.5], [0.6]])
    lst = np.array([[30.0], [28.0]])
    tvdi, info = tp.tvdis_from_field_stats(ndvi, lst, min_points=8)
    assert info["degenerate_bins"] == 1
    assert np.all(np.isnan(tvdi))


def test_indicator_agreement_rate_difference() -> None:
    """Flagged bins concentrate high-indicator values → positive rate
    difference with finite Wilson CIs."""
    rng = np.random.default_rng(5)
    N = 400
    indicator = rng.random((1, N))
    paths = np.full((1, N), np.nan)
    # Flag 50 bins, 80 % of them with indicator > 0.75.
    flag_idx = rng.choice(N, 50, replace=False)
    for j in flag_idx:
        paths[0, j] = 10.0
        indicator[0, j] = 0.1  # unforced flagged bins sit low by construction
    for j in flag_idx[:40]:
        indicator[0, j] = 0.9  # 80 % of flagged bins are high-indicator
    out = tp.indicator_agreement(indicator, paths, tau=5.0)
    assert out["n_flagged_bins_observed"] == 50
    assert out["high_rate_flagged"] == 0.8
    assert out["rate_difference"] > 0.5
    assert all(np.isfinite(v) for v in out["high_rate_flagged_wilson95"])
