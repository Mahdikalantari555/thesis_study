"""Unit tests for literature SSL models: STS-Net, Tiny-CNN-Mamba, and Time2Agri."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from ssl_anomaly.models.cnn_mamba import TinyCNNMamba
from ssl_anomaly.models.pretexts import Time2AgriModel, info_nce_loss, make_time2agri_views
from ssl_anomaly.models.sts_net import STSNetAutoencoder


def test_sts_net_forward_backward_and_dimensions():
    """Verify STS-Net forward/backward pass, tensor shapes, and Huber loss."""
    torch.manual_seed(42)
    B, T, C = 4, 36, 8
    x = torch.randn(B, T, C, requires_grad=True)

    model = STSNetAutoencoder(d_in=C, d_model=32, latent_dim=16)
    params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    assert params > 5_000, f"Expected >5k params, got {params}"

    recon, emb = model(x)
    assert recon.shape == (B, T, C), f"Unexpected recon shape {recon.shape}"
    assert emb.shape == (B, 16), f"Unexpected emb shape {emb.shape}"

    # Compute reconstruction anomaly score
    scores = model.compute_anomaly_score(x, recon)
    assert scores.shape == (B, T)
    assert torch.all(torch.isfinite(scores))

    # Backward pass
    loss = scores.mean()
    loss.backward()
    assert x.grad is not None and torch.all(torch.isfinite(x.grad))


def test_tiny_cnn_mamba_forward_backward_and_dimensions():
    """Verify Tiny-CNN-Mamba pure-PyTorch Bidirectional SSM forward/backward."""
    torch.manual_seed(42)
    B, T, C = 4, 36, 8
    x = torch.randn(B, T, C, requires_grad=True)

    model = TinyCNNMamba(d_in=C, d_model=32, d_state=8, n_layers=2, latent_dim=16)
    params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    assert params > 5_000, f"Expected >5k params, got {params}"

    recon, emb = model(x)
    assert recon.shape == (B, T, C), f"Unexpected recon shape {recon.shape}"
    assert emb.shape == (B, 16), f"Unexpected emb shape {emb.shape}"

    scores = model.compute_anomaly_score(x, recon)
    assert scores.shape == (B, T)
    assert torch.all(torch.isfinite(scores))

    # Backward pass
    loss = scores.mean()
    loss.backward()
    assert x.grad is not None and torch.all(torch.isfinite(x.grad))


def test_time2agri_augmentations_and_contrastive_head():
    """Verify Time2Agri views, trajectory contrastive projections, and InfoNCE loss."""
    torch.manual_seed(42)
    rng = np.random.default_rng(42)
    B, T, C = 4, 36, 8
    tokens = torch.randn(B, T, C)
    pad_mask = torch.zeros((B, T), dtype=torch.bool)
    pad_mask[:, 30:] = True  # Last 6 positions padded

    # Test augmentations
    v1, p1, v2, p2 = make_time2agri_views(tokens, pad_mask, n_bands=C, rng=rng)
    assert v1.shape == tokens.shape
    assert v2.shape == tokens.shape
    assert p1.shape == pad_mask.shape
    assert p2.shape == pad_mask.shape
    # Check that views are augmented (not identical)
    assert not torch.allclose(v1, tokens)
    assert not torch.allclose(v2, tokens)

    # Test model & projections
    model = Time2AgriModel(d_in=C, n_bands=C, d_model=32, proj_dim=16, n_heads=2, n_layers=2)
    proj, pooled = model(tokens, key_padding_mask=pad_mask)
    assert proj.shape == (B, 16)
    assert pooled.shape == (B, 32)
    # Projections should be L2-normalized
    norms = torch.norm(proj, dim=-1)
    assert torch.allclose(norms, torch.ones_like(norms), atol=1e-5)

    # InfoNCE loss
    z1, _ = model(v1, key_padding_mask=p1)
    z2, _ = model(v2, key_padding_mask=p2)
    loss = info_nce_loss(z1, z2, temperature=0.15)
    assert torch.isfinite(loss) and loss > 0
    loss.backward()
