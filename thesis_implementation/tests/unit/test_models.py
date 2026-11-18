from __future__ import annotations

import numpy as np
import torch

from ssl_anomaly.models.gru_ae import GRUAutoencoder
from ssl_anomaly.models.masked_tf import MaskedTransformer


def _random_batch(rng, B=4, T=30, d=8):
    tokens = torch.from_numpy(rng.normal(0, 1, size=(B, T, d)).astype(np.float32))
    mask = torch.zeros(B, T, dtype=torch.bool)
    mask[:, 5:10] = True
    pamask = torch.zeros(B, T, dtype=torch.bool)
    pamask[:, -3:] = True
    tokens[mask] = 0.0
    lengths = torch.full((B,), T - 3, dtype=torch.long)
    return tokens, mask, pamask, lengths


def test_gru_ae_forward(rng):
    torch.manual_seed(0)
    tokens, mask, pamask, lengths = _random_batch(rng)
    model = GRUAutoencoder(d_in=8, d_model=32, n_layers=1, dropout=0.0)
    recon, emb = model(tokens, lengths=lengths)
    assert recon.shape == tokens.shape
    assert emb.shape == (tokens.shape[0], 32)


def test_gru_ae_loss(rng):
    torch.manual_seed(1)
    tokens, mask, pamask, lengths = _random_batch(rng)
    model = GRUAutoencoder(d_in=8, d_model=32, n_layers=1, dropout=0.0)
    loss, per_tok = model.masked_reconstruction_loss(tokens, mask, lengths=lengths)
    assert torch.isfinite(loss)
    assert per_tok.shape == (tokens.shape[0], tokens.shape[1])
    # Trimmed loss should also work
    loss_t, _ = model.masked_reconstruction_loss(tokens, mask, lengths=lengths, trim_frac=0.2)
    assert torch.isfinite(loss_t)


def test_transformer_forward(rng):
    torch.manual_seed(2)
    tokens, mask, pamask, lengths = _random_batch(rng)
    model = MaskedTransformer(d_in=8, d_model=32, n_heads=4, n_layers=2, d_ff=64, max_len=64)
    recon, emb = model(tokens, mask=mask, key_padding_mask=pamask)
    assert recon.shape == tokens.shape
    assert emb.shape == (tokens.shape[0], 32)


def test_transformer_loss(rng):
    torch.manual_seed(3)
    tokens, mask, pamask, lengths = _random_batch(rng)
    model = MaskedTransformer(d_in=8, d_model=32, n_heads=4, n_layers=2, d_ff=64, max_len=64)
    loss, per_tok = model.masked_reconstruction_loss(tokens, mask, key_padding_mask=pamask)
    assert torch.isfinite(loss)
    assert per_tok.shape == tokens.shape[:2]
