"""Temporal XAI Attribution Suite (RQ6 / Gap G6).

Implements four complementary attribution methods for 1D self-supervised crop
anomaly detectors:
  1. ``integrated_gradients_attribution`` — exact Riemann path integral (pure PyTorch autograd)
  2. ``temporal_grad_cam_attribution`` — 1D Temporal Grad-CAM on encoder token activations
  3. ``window_occlusion_attribution`` — temporal-spectral patch replacement sensitivity
  4. ``temporal_shap_attribution`` — KernelSHAP coalition regression over (block, band) players

All attributions map cleanly to phase bins ``(T, n_bands)`` and aggregate into the
three agronomic sugarcane growth stages:
  - ``emergence_tillering`` (DSH 0–120 d, bins 0..7)
  - ``grand_growth`` (DSH 120–300 d, bins 8..19)
  - ``maturation_ripening`` (DSH 300–540 d, bins 20..35)
"""

from __future__ import annotations

import numpy as np
import torch

from ..models.pretexts import PretextTransformer

SUGARCANE_STAGE_BINS: dict[str, tuple[int, int]] = {
    "emergence_tillering": (0, 8),
    "grand_growth": (8, 20),
    "maturation_ripening": (20, 36),
}


def differentiable_cycle_score(
    model: PretextTransformer,
    x: torch.Tensor,
) -> torch.Tensor:
    """Compute a smooth differentiable scalar anomaly score for batch ``x`` ``(B, T, d_in)``.

    - For ``anomaly_degradation``: smooth log-sum-exp over per-token anomaly probabilities
      ``sigmoid(task_head(h))``.
    - For ``masked_recon``: block-masked squared reconstruction residual aggregated via
      smooth top-k ``logsumexp``.
    """
    B, T, _ = x.shape
    nb = model.n_bands
    if model.arm == "anomaly_degradation":
        h, _ = model.encode_sequence(x)
        logits = model.task_head(h).squeeze(-1)  # (B, T)
        tok_energy = torch.nn.functional.softplus(logits)
        return torch.logsumexp(tok_energy * 2.0, dim=-1) / 2.0

    # Masked reconstruction: 4-fold interleaved mask pass so every token is reconstructed from context
    errs = torch.zeros((B, T), device=x.device, dtype=x.dtype)
    for rem in range(4):
        m = torch.zeros((B, T), dtype=torch.bool, device=x.device)
        m[:, rem::4] = True
        xin = x.clone()
        xin[:, rem::4, :nb] = 0.0
        h, _ = model.encode_sequence(xin, mask=m)
        rec = model.task_head(h)
        sq = ((rec[:, rem::4, :nb] - x[:, rem::4, :nb]) ** 2).mean(dim=-1)
        errs[:, rem::4] = torch.sqrt(sq + 1e-6)
    return torch.logsumexp(errs * 2.5, dim=-1) / 2.5


def integrated_gradients_attribution(
    model: PretextTransformer,
    x_tok: np.ndarray,
    baseline_tok: np.ndarray,
    *,
    steps: int = 24,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute Integrated Gradients ``(T, n_bands)`` + raw input gradients ``dS/dx`` at ``x``.

    Returns ``(ig_attr_tb, grad_at_x_tb)``.
    """
    model.eval()
    nb = model.n_bands
    x1 = torch.from_numpy(x_tok.astype(np.float32))
    x0 = torch.from_numpy(baseline_tok.astype(np.float32))

    alphas = torch.linspace(1.0 / steps, 1.0, steps, dtype=torch.float32).view(steps, 1, 1)
    # Only interpolate spectral bands; keep temporal coordinates fixed to x1
    interp = x1.unsqueeze(0).repeat(steps, 1, 1)
    interp[:, :, :nb] = x0[:, :nb].unsqueeze(0) + alphas * (x1[:, :nb] - x0[:, :nb]).unsqueeze(0)
    interp.requires_grad_(True)

    with torch.backends.cudnn.flags(enabled=False):
        scores = differentiable_cycle_score(model, interp)
        scores.sum().backward()

    grads = interp.grad[:, :, :nb].detach().numpy()  # (steps, T, nb)
    avg_grad = np.mean(grads, axis=0)
    ig = (x_tok[:, :nb] - baseline_tok[:, :nb]) * avg_grad
    grad_at_x = grads[-1]
    return ig.astype(np.float64), grad_at_x.astype(np.float64)


def temporal_grad_cam_attribution(
    model: PretextTransformer,
    x_tok: np.ndarray,
    baseline_tok: np.ndarray,
) -> np.ndarray:
    """Compute 1D Temporal Grad-CAM on final Transformer encoder activations ``(T, n_bands)``."""
    model.eval()
    nb = model.n_bands
    xt = torch.from_numpy(x_tok.astype(np.float32)).unsqueeze(0).requires_grad_(True)
    saved_h: dict[str, torch.Tensor] = {}

    def _fwd_hook(_mod: torch.nn.Module, _inp: tuple, out: torch.Tensor) -> None:
        out.retain_grad()
        saved_h["h"] = out

    handle = model.ln_f.register_forward_hook(_fwd_hook)
    try:
        with torch.backends.cudnn.flags(enabled=False):
            sc = differentiable_cycle_score(model, xt)
            sc.sum().backward()
    finally:
        handle.remove()

    h = saved_h["h"]  # (B_pass, T, d_model)
    gh = h.grad  # (B_pass, T, d_model)
    # 1D Token LayerCAM / Grad-CAM: avoid LayerNorm temporal sign cancellation
    cam_t = torch.relu(gh * h).sum(dim=-1).mean(dim=0).detach().numpy()  # (T,)
    cam_t = cam_t / (np.max(cam_t) + 1e-8)

    # Distribute temporal CAM across spectral channels via signed input-gradient sensitivity
    gx = xt.grad[0, :, :nb].detach().numpy()
    delta_grad = (x_tok[:, :nb] - baseline_tok[:, :nb]) * gx
    w_band = np.abs(delta_grad)
    w_sum = np.sum(w_band, axis=-1, keepdims=True) + 1e-8
    return (cam_t[:, None] * (delta_grad / w_sum * nb)).astype(np.float64)


@torch.no_grad()
def window_occlusion_attribution(
    model: PretextTransformer,
    x_tok: np.ndarray,
    baseline_tok: np.ndarray,
    *,
    window: int = 2,
) -> np.ndarray:
    """Measure anomaly-score reduction when each ``(t..t+w, b)`` patch is replaced by baseline."""
    model.eval()
    T = x_tok.shape[0]
    nb = model.n_bands
    x_base_t = torch.from_numpy(x_tok.astype(np.float32)).unsqueeze(0)
    s_orig = float(differentiable_cycle_score(model, x_base_t).item())

    pert_list = []
    coords = []
    for t in range(T):
        t_end = min(T, t + window)
        for b in range(nb):
            xp = x_tok.copy()
            xp[t:t_end, b] = baseline_tok[t:t_end, b]
            pert_list.append(xp)
            coords.append((t, b))

    batch_t = torch.from_numpy(np.stack(pert_list, axis=0).astype(np.float32))
    s_pert = differentiable_cycle_score(model, batch_t).numpy()
    attr = np.zeros((T, nb), dtype=np.float64)
    for (t, b), sp in zip(coords, s_pert):
        attr[t, b] = s_orig - float(sp)
    return attr


@torch.no_grad()
def temporal_shap_attribution(
    model: PretextTransformer,
    x_tok: np.ndarray,
    baseline_tok: np.ndarray,
    *,
    n_time_blocks: int = 6,
    n_samples: int = 96,
    seed: int = 42,
) -> np.ndarray:
    """Compute KernelSHAP attributions over ``(temporal_block, band)`` coalitions ``(T, n_bands)``."""
    model.eval()
    rng = np.random.default_rng(seed)
    T = x_tok.shape[0]
    nb = model.n_bands
    edges = np.linspace(0, T, n_time_blocks + 1).round().astype(int)
    M = n_time_blocks * nb

    # Sample binary coalitions z in {0, 1}^M with Shapley kernel weights
    Z = np.zeros((n_samples + 2, M), dtype=np.float64)
    Z[0, :] = 0.0
    Z[1, :] = 1.0
    weights = np.ones(n_samples + 2, dtype=np.float64) * 1e4

    ks = np.arange(1, M)
    shap_p = (M - 1.0) / (ks * (M - ks))
    shap_p = shap_p / shap_p.sum()

    for i in range(n_samples):
        k = int(rng.choice(ks, p=shap_p))
        on = rng.choice(M, size=k, replace=False)
        Z[i + 2, on] = 1.0
        weights[i + 2] = 1.0

    X_coal = np.repeat(baseline_tok[None, :, :], n_samples + 2, axis=0).astype(np.float32)
    for i in range(n_samples + 2):
        for blk in range(n_time_blocks):
            t0, t1 = edges[blk], edges[blk + 1]
            for b in range(nb):
                if Z[i, blk * nb + b] > 0.5:
                    X_coal[i, t0:t1, b] = x_tok[t0:t1, b]

    y = differentiable_cycle_score(model, torch.from_numpy(X_coal)).numpy().astype(np.float64)
    y0 = y[0]
    # Weighted ridge Shapley regression: y - y0 ~ Z @ phi
    W = weights[:, None]
    ZtW = (Z * W).T
    lhs = ZtW @ Z + 1e-3 * np.eye(M)
    rhs = ZtW @ (y - y0)
    phi = np.linalg.solve(lhs, rhs)  # (M,)

    attr = np.zeros((T, nb), dtype=np.float64)
    for blk in range(n_time_blocks):
        t0, t1 = edges[blk], edges[blk + 1]
        span = max(1, t1 - t0)
        for b in range(nb):
            attr[t0:t1, b] = phi[blk * nb + b] / span
    return attr


def aggregate_to_sugarcane_stages(attr_tb: np.ndarray) -> dict[str, float]:
    """Aggregate ``(T, n_bands)`` absolute attributions into the 3 coarse sugarcane stages."""
    T = attr_tb.shape[0]
    total = float(np.sum(np.abs(attr_tb))) + 1e-12
    out: dict[str, float] = {}
    for stage, (b0, b1) in SUGARCANE_STAGE_BINS.items():
        s0 = int(round(b0 * T / 36.0))
        s1 = int(round(b1 * T / 36.0))
        out[stage] = float(np.sum(np.abs(attr_tb[s0:s1])) / total)
    return out
