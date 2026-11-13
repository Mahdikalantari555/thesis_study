"""Tiny-CNN-Mamba: Lightweight 1D CNN + Bidirectional Selective State Space Model.

Combines 1D convolutional spectral-temporal front-end with a pure PyTorch
Bidirectional Selective State Space Model (SSM) back-end. Provides O(L)
computational scaling for crop phenological sequences with zero external CUDA/C++
dependency requirements.
"""

from __future__ import annotations

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class SelectiveSSM(nn.Module):
    """Pure-PyTorch Selective State Space Model (Mamba primitive).

    Implements input-dependent parameter discretization (Zero-Order Hold)
    and selective recurrence:
        h_t = exp(Δ_t * A) * h_{t-1} + (Δ_t * B_t) * x_t
        y_t = C_t * h_t + D * x_t
    """

    def __init__(self, d_model: int, d_state: int = 16) -> None:
        super().__init__()
        self.d_model = d_model
        self.d_state = d_state

        # Continuous A diagonal parameter (structured negative real initialization)
        A = torch.arange(1, d_state + 1, dtype=torch.float32).repeat(d_model, 1)
        self.A_log = nn.Parameter(torch.log(A))  # A = -exp(A_log)

        # Skip connection D
        self.D = nn.Parameter(torch.ones(d_model))

        # Input-dependent projections: Δ, B, C
        self.x_proj = nn.Linear(d_model, d_model + 2 * d_state, bias=False)
        self.dt_proj = nn.Linear(d_model, d_model, bias=True)

        # Initialize dt_proj bias to small positive values (softplus scale)
        dt_init_std = 0.02
        nn.init.uniform_(self.dt_proj.weight, -dt_init_std, dt_init_std)
        # log(exp(1) - 1) ~ 0.54
        nn.init.constant_(self.dt_proj.bias, math.log(math.exp(0.1) - 1.0))

    def _selective_scan(self, u: torch.Tensor, reverse: bool = False) -> torch.Tensor:
        """Run sequential selective scan over time.

        Parameters
        ----------
        u: (B, T, d_model)
        reverse: If True, scans backward in time.

        Returns
        -------
        y: (B, T, d_model)
        """
        B, T, D = u.shape
        N = self.d_state
        A = -torch.exp(self.A_log)  # (D, N)

        # Project inputs to selective parameters
        # x_dbl: (B, T, D + 2*N)
        x_dbl = self.x_proj(u)
        delta_in = x_dbl[:, :, :D]  # (B, T, D)
        B_mat = x_dbl[:, :, D : D + N]  # (B, T, N)
        C_mat = x_dbl[:, :, D + N :]  # (B, T, N)

        delta = F.softplus(self.dt_proj(delta_in))  # (B, T, D)

        # Discretize: dA = exp(delta * A) -> (B, T, D, N)
        # dB = delta * B -> (B, T, D, N)
        dA = torch.exp(delta.unsqueeze(-1) * A.unsqueeze(0).unsqueeze(0))
        dB = delta.unsqueeze(-1) * B_mat.unsqueeze(2)  # (B, T, D, N)

        # Scan loop
        h = torch.zeros(B, D, N, device=u.device, dtype=u.dtype)
        ys = []

        time_indices = range(T - 1, -1, -1) if reverse else range(T)
        for t in time_indices:
            u_t = u[:, t, :].unsqueeze(-1)  # (B, D, 1)
            dA_t = dA[:, t, :, :]  # (B, D, N)
            dB_t = dB[:, t, :, :]  # (B, D, N)
            C_t = C_mat[:, t, :].unsqueeze(1)  # (B, 1, N)

            # Recurrence: h = dA * h + dB * u
            h = dA_t * h + dB_t * u_t  # (B, D, N)
            # Output: y = h * C^T
            y_t = (h * C_t).sum(dim=-1)  # (B, D)
            ys.append(y_t)

        if reverse:
            ys.reverse()

        y = torch.stack(ys, dim=1)  # (B, T, D)
        return y + u * self.D

    def forward(self, x: torch.Tensor, reverse: bool = False) -> torch.Tensor:
        return self._selective_scan(x, reverse=reverse)


class BidirectionalMambaBlock(nn.Module):
    """Bidirectional Mamba block combining forward and backward selective state space models."""

    def __init__(self, d_model: int, d_state: int = 16, expand: int = 2) -> None:
        super().__init__()
        self.d_model = d_model
        d_inner = d_model * expand
        self.d_inner = d_inner

        self.norm = nn.LayerNorm(d_model)
        # Input projection with gating branch
        self.in_proj = nn.Linear(d_model, 2 * d_inner, bias=False)

        # 1D Depthwise convolution
        self.conv1d = nn.Conv1d(
            d_inner, d_inner, kernel_size=3, padding=1, groups=d_inner, bias=True
        )

        # Forward and backward SSMs
        self.ssm_fwd = SelectiveSSM(d_inner, d_state=d_state)
        self.ssm_bwd = SelectiveSSM(d_inner, d_state=d_state)

        # Merge bidirectional representations
        self.merge = nn.Linear(2 * d_inner, d_inner, bias=False)
        self.out_proj = nn.Linear(d_inner, d_model, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = x
        h = self.norm(x)

        # Project and split into main and gating branch
        xz = self.in_proj(h)  # (B, T, 2*d_inner)
        x_branch, z_branch = xz.chunk(2, dim=-1)

        # 1D Depthwise convolution along time axis
        x_conv = x_branch.permute(0, 2, 1)
        x_conv = F.silu(self.conv1d(x_conv))
        x_conv = x_conv.permute(0, 2, 1)

        # Bidirectional selective scan
        y_fwd = self.ssm_fwd(x_conv, reverse=False)
        y_bwd = self.ssm_bwd(x_conv, reverse=True)
        y_bi = self.merge(torch.cat([y_fwd, y_bwd], dim=-1))

        # Gated multiplicative activation
        y_gated = y_bi * F.silu(z_branch)
        out = self.out_proj(y_gated)

        return out + res


class TinyCNNMamba(nn.Module):
    """Tiny-CNN-Mamba Architecture for Phenological Time-Series Anomaly Detection.

    Parameters
    ----------
    d_in:
        Number of input channels (spectral bands / covariates).
    d_model:
        Hidden sequence representation dimension.
    d_state:
        State space latent dimension.
    n_layers:
        Number of bidirectional Mamba blocks.
    latent_dim:
        Dimension of cycle bottleneck embedding.
    """

    def __init__(
        self,
        d_in: int,
        d_model: int = 64,
        d_state: int = 16,
        n_layers: int = 2,
        latent_dim: int = 32,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.d_in = d_in
        self.d_model = d_model
        self.latent_dim = latent_dim

        # 1D CNN Front-end stem for local spectral-temporal feature extraction
        self.stem = nn.Sequential(
            nn.Conv1d(d_in, d_model, kernel_size=3, padding=1),
            nn.BatchNorm1d(d_model),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Conv1d(d_model, d_model, kernel_size=3, padding=1),
            nn.BatchNorm1d(d_model),
            nn.GELU(),
        )

        # Bidirectional Mamba Back-end
        self.mamba_layers = nn.ModuleList(
            [BidirectionalMambaBlock(d_model, d_state=d_state) for _ in range(n_layers)]
        )

        # Reconstruction and embedding heads
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, d_in)
        self.emb_head = nn.Sequential(
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(d_model, latent_dim),
            nn.GELU(),
        )

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor | None = None,
        key_padding_mask: torch.Tensor | None = None,
        lengths: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.

        Parameters
        ----------
        x: (B, T, d_in)

        Returns
        -------
        recon: (B, T, d_in)
        embedding: (B, latent_dim)
        """
        B, T, C = x.shape
        # CNN front-end
        h_cnn = x.permute(0, 2, 1)
        h_cnn = self.stem(h_cnn)
        h = h_cnn.permute(0, 2, 1)  # (B, T, d_model)

        # SSM back-end
        for layer in self.mamba_layers:
            h = layer(h)

        h = self.norm(h)
        recon = self.head(h)  # (B, T, d_in)

        # Bottleneck embedding
        h_pool = h.permute(0, 2, 1)
        embedding = self.emb_head(h_pool)  # (B, latent_dim)

        return recon, embedding

    def compute_anomaly_score(
        self,
        x: torch.Tensor,
        recon: torch.Tensor | None = None,
        reduction: str = "none",
    ) -> torch.Tensor:
        if recon is None:
            recon, _ = self.forward(x)
        err = F.smooth_l1_loss(recon, x, reduction="none", beta=0.1)
        per_bin = err.mean(dim=-1)
        if reduction == "cycle":
            return per_bin.mean(dim=-1)
        return per_bin
