from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip('torch')

ROOT = Path(__file__).resolve().parents[2]
_SRC = str(ROOT / 'src')
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from ssl_anomaly.models.jepa import JEPAModel  # noqa: E402


def _load_growth_ssl():
    p = ROOT / 'src/ssl_anomaly/eval/growth_ssl.py'
    spec = importlib.util.spec_from_file_location('growth_ssl_jepa', p)
    ssl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ssl)
    return ssl


def _synthetic_cycles(n=12, k=24, d_in=1, seed=3):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, np.pi, k, dtype=np.float32)
    base = np.stack([np.sin(t + 0.2 * b) for b in range(d_in)], axis=-1)
    x = base[None] + rng.normal(0, .05, (n, k, d_in)).astype(np.float32)
    return x.astype(np.float32)


def test_jepa_forward_shapes_and_loss_decreases():
    torch.manual_seed(0)
    x = torch.from_numpy(_synthetic_cycles(n=8, k=16, d_in=3, seed=0))
    clean = x.clone()
    mask = torch.rand(8, 16) < .25
    model = JEPAModel(d_in=3, d_model=32, n_heads=4, n_layers=2, d_ff=64, max_len=32)
    recon, emb = model(x, mask=mask)
    assert recon.shape == x.shape and emb.shape == (8, 32)
    assert torch.isfinite(recon).all() and torch.isfinite(emb).all()

    def step_loss():
        recon, _ = model(x, mask=mask)
        recon_loss = ((recon - clean) ** 2).mean()
        return recon_loss + model.latent_prediction_loss(x, mask, target=clean)

    init_target = next(model.target_encoder.parameters()).detach().clone()
    init = float(step_loss().detach())
    opt = torch.optim.AdamW(model.parameters(), lr=5e-3)
    for _ in range(40):
        loss = step_loss()
        opt.zero_grad(); loss.backward(); opt.step()
    assert float(step_loss().detach()) < init * 0.8
    # EMA target encoder must follow training (it starts as an exact copy).
    assert not torch.allclose(next(model.target_encoder.parameters()), init_target)


def test_jepa_target_encoder_frozen_in_eval():
    torch.manual_seed(0)
    model = JEPAModel(d_in=3, d_model=32, n_heads=4, n_layers=1, d_ff=32, max_len=16)
    before = next(model.target_encoder.parameters()).detach().clone()
    model.eval()
    with torch.no_grad():
        model(torch.randn(2, 8, 3))
    assert torch.equal(next(model.target_encoder.parameters()), before)


def test_masked_ssl_jepa_trains_and_scores():
    ssl = _load_growth_ssl()
    x = _synthetic_cycles()
    x[0, 5, 0] = np.nan  # missing bin must stay unscored
    model = ssl.MaskedSSL('jepa', epochs=2, seed=3).fit(x)
    y = x.copy()
    y[1, 7, 0] = 10.  # injected anomaly
    scores = model.score(y)
    assert scores.shape == (12, 24) and model.parameter_count > 0
    assert np.isnan(scores[0, 5])
    finite = np.isfinite(scores)
    assert finite.sum() > 0 and np.isfinite(scores[finite]).all()
    assert scores[1, 7] > np.nanmedian(scores[1])


def test_masked_ssl_jepa_causal_future_invariance():
    ssl = _load_growth_ssl()
    x = np.arange(24., dtype=float).reshape(3, 8, 1) / 24
    model = ssl.MaskedSSL('jepa', epochs=2, seed=3, causal=True).fit(x)
    original = model.score(x)
    changed = x.copy()
    changed[:, 4:, :] += 1000
    np.testing.assert_allclose(original[:, :4], model.score(changed)[:, :4], atol=1e-6)


def test_masked_ssl_rejects_unknown_architecture():
    ssl = _load_growth_ssl()
    with pytest.raises(ValueError, match='unsupported architecture'):
        ssl.MaskedSSL('bert')
