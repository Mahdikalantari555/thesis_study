"""Tests for mask-aware inputs, train-only normalization and DOY channels
(tasks 2.1–2.4, spec "Mask-aware inputs and train-only normalization")."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import inputs as minputs  # noqa: E402
from ssl_anomaly.monitor import models as mmodels  # noqa: E402


def make_synthetic(n=6, T=36, C=8, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(0.4, 0.1, size=(n, T, C)).astype(np.float32)
    X[:, :, 7] = rng.normal(30, 5, size=(n, T))  # LST in °C
    M = np.ones((n, T, C), dtype=bool)
    # Punch holes: unobserved bins/bands.
    M[:, 30:, 7] = False
    M[0, 5:9, 0] = False
    X[~M] = np.nan
    return X, M


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------
def test_fit_norm_train_only() -> None:
    """Stats must not see non-train cycles: perturbing them changes nothing."""
    X, M = make_synthetic(n=8)
    train = np.zeros(8, dtype=bool)
    train[:4] = True
    s1 = minputs.fit_robust_norm(X[train], M[train])
    X2 = X.copy()
    X2[~train] += 1000.0
    s2 = minputs.fit_robust_norm(X2[train], M[train])
    assert np.allclose(s1["median"], s2["median"])
    assert np.allclose(s1["scale"], s2["scale"])


def test_apply_norm_zero_where_unobserved() -> None:
    """Unobserved entries become exactly 0 in z-space (with mask 0)."""
    X, M = make_synthetic()
    s = minputs.fit_robust_norm(X, M)
    z = minputs.apply_norm(s, X, M)
    assert np.all(np.isfinite(z)), "no NaN may reach the model"
    assert np.allclose(z[~M], 0.0)
    assert z[~M].max() == 0.0


def test_scale_floor_no_zero_scale() -> None:
    """Constant band (MAD=0) must not produce a zero scale."""
    X, M = make_synthetic(n=10)
    X[:, :, 3] = 0.5  # constant channel
    s = minputs.fit_robust_norm(X, M)
    assert np.all(s["scale"] > 0)


def test_norm_roundtrip_save_load(tmp_path: Path) -> None:
    X, M = make_synthetic()
    s = minputs.fit_robust_norm(X, M)
    p = tmp_path / "norm.npz"
    minputs.save_norm(s, p, meta={"run": "t"})
    s2 = minputs.load_norm(p)
    assert np.allclose(s["median"], s2["median"])
    assert np.allclose(s["scale"], s2["scale"])
    assert np.allclose(s["robust_range"], s2["robust_range"])


# ---------------------------------------------------------------------------
# DOY channels
# ---------------------------------------------------------------------------
def test_doy_channels_shape_and_range() -> None:
    d = minputs.doy_channels(np.array([100, 500], dtype=np.int64))
    assert d.shape == (2, 36, 2)
    assert np.all(np.isfinite(d))
    assert np.all(np.abs(d) <= 1.0 + 1e-6)
    # sin/cos must lie on the unit circle.
    r = np.hypot(d[..., 0], d[..., 1])
    assert np.allclose(r, 1.0, atol=1e-5)


def test_doy_channels_depend_on_harvest() -> None:
    """Different harvest dates → different seasonal phase (R3 motivation)."""
    d1 = minputs.doy_channels(np.array([0], dtype=np.int64))
    d2 = minputs.doy_channels(np.array([200], dtype=np.int64))
    assert not np.allclose(d1, d2)


# ---------------------------------------------------------------------------
# Token building
# ---------------------------------------------------------------------------
def test_build_tokens_no_nan() -> None:
    X, M = make_synthetic(n=3)
    s = minputs.fit_robust_norm(X, M)
    z = minputs.apply_norm(s, X, M)
    doy = minputs.doy_channels(np.full(3, 150, dtype=np.int64))
    tok = mmodels.build_tokens(z[0], M[0], doy[0])
    assert tok.shape == (36, 18)
    assert np.all(np.isfinite(tok))
    # Mask-flag block mirrors the observation mask.
    assert np.array_equal(tok[:, 8:16] > 0.5, M[0])


def test_token_dim() -> None:
    assert mmodels.token_dim(8, use_doy=True) == 18
    assert mmodels.token_dim(8, use_doy=False) == 16


# ---------------------------------------------------------------------------
# Masked reconstruction: masked entries give zero loss (task 2.3)
# ---------------------------------------------------------------------------
def test_masked_entries_zero_loss() -> None:
    """Loss must be exactly zero when no loss-masked entry is observed."""
    import torch

    from ssl_anomaly.models.gru_ae import CausalGRUAE

    torch.manual_seed(0)
    model = CausalGRUAE(d_in=18, n_out=8, d_model=32)
    B, T = 2, 36
    x = torch.randn(B, T, 18)
    target = torch.randn(B, T, 8)
    channel_mask = torch.zeros(B, T, 8, dtype=torch.bool)  # nothing observed
    pretext = torch.ones(B, T, dtype=torch.bool)
    loss, tok = model.masked_reconstruction_loss(x, pretext, target, channel_mask=channel_mask)
    assert float(loss) == 0.0
    assert torch.all(tok == 0)


def test_loss_positive_with_observed() -> None:
    import torch

    from ssl_anomaly.models.gru_ae import CausalGRUAE

    torch.manual_seed(0)
    model = CausalGRUAE(d_in=18, n_out=8, d_model=32)
    B, T = 2, 36
    x = torch.randn(B, T, 18)
    target = torch.randn(B, T, 8)
    channel_mask = torch.ones(B, T, 8, dtype=torch.bool)
    pretext = torch.zeros(B, T, dtype=torch.bool)
    pretext[:, 10] = True
    loss, _ = model.masked_reconstruction_loss(x, pretext, target, channel_mask=channel_mask)
    assert float(loss) > 0.0


# ---------------------------------------------------------------------------
# Masked tensor archive (strict, requires the cached rebuild)
# ---------------------------------------------------------------------------
MASKED_NPZ = minputs.MASKED_NPZ_PATH


@pytest.mark.real_data
def test_masked_archive_consistency() -> None:
    assert MASKED_NPZ.is_file(), f"masked cycle archive cache missing: {MASKED_NPZ}"
    d = minputs.load_masked_cycles()
    X, M = d["X"], d["M"]
    assert X.shape[1:] == (36, 8)
    assert M.shape == X.shape
    assert np.all(np.isnan(X[~M])), "values must be NaN exactly where unobserved"
    assert np.all(np.isfinite(X[M])), "observed entries must be finite"
    # Alignment with the canonical NPZ cycle list.
    ref = np.load(minputs.CYCLES_NPZ_PATH, allow_pickle=True)
    assert len(d["cycle_keys"]) == ref["X"].shape[0]
    # LST physical range — stats.zarr stores KELVIN (§8: band/unit mistakes).
    lst = X[:, :, 7][M[:, :, 7]]
    assert lst.min() > 180 and lst.max() < 350, "LST out of physical Kelvin range"
