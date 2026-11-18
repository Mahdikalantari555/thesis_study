"""STS-Net: Spatio-Temporal Convolutional Autoencoder for Crop Phenology Anomaly Detection.

Inspired by Dalal et al. (2026) spatio-temporal autoencoders for multi-spectral time series.
Uses 1D temporal-spectral convolutional blocks with multi-scale receptive fields
to reconstruct normal crop trajectories and detect anomalies via reconstruction error.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class ConvBlock1D(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 3, stride: int = 1) -> None:
        super().__init__()
        padding = kernel_size // 2
        self.conv = nn.Conv1d(in_channels, out_channels, kernel_size, stride=stride, padding=padding)
        self.norm = nn.BatchNorm1d(out_channels)
        self.act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.norm(self.conv(x)))


class ResConvBlock1D(nn.Module):
    def __init__(self, channels: int, kernel_size: int = 3) -> None:
        super().__init__()
        padding = kernel_size // 2
        self.conv1 = nn.Conv1d(channels, channels, kernel_size, padding=padding)
        self.norm1 = nn.BatchNorm1d(channels)
        self.act = nn.GELU()
        self.conv2 = nn.Conv1d(channels, channels, kernel_size, padding=padding)
        self.norm2 = nn.BatchNorm1d(channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = x
        h = self.act(self.norm1(self.conv1(x)))
        h = self.norm2(self.conv2(h))
        return self.act(h + res)


class STSNetAutoencoder(nn.Module):
    """Spatio-Temporal Convolutional Autoencoder (STS-Net).

    Parameters
    ----------
    d_in:
        Number of input channels (bands / features).
    d_model:
        Hidden representation channel dimension.
    latent_dim:
        Dimension of the compressed bottleneck embedding.
    dropout:
        Dropout probability.
    """

    def __init__(
        self,
        d_in: int,
        d_model: int = 64,
        latent_dim: int = 32,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.d_in = d_in
        self.d_model = d_model
        self.latent_dim = latent_dim

        # Encoder: (B, d_in, T) -> (B, d_model, T/2) -> (B, d_model, T/4)
        self.stem = nn.Sequential(
            nn.Conv1d(d_in, d_model // 2, kernel_size=5, padding=2),
            nn.BatchNorm1d(d_model // 2),
            nn.GELU(),
            nn.Conv1d(d_model // 2, d_model, kernel_size=3, padding=1),
            nn.BatchNorm1d(d_model),
            nn.GELU(),
        )
        self.enc_res = ResConvBlock1D(d_model, kernel_size=3)
        self.pool1 = nn.MaxPool1d(2, stride=2, return_indices=True)

        self.enc_mid = ConvBlock1D(d_model, d_model, kernel_size=3)
        self.pool2 = nn.MaxPool1d(2, stride=2, return_indices=True)

        # Bottleneck projection
        self.proj_latent = nn.Sequential(
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(d_model, latent_dim),
            nn.GELU(),
        )

        # Decoder: mirrors encoder
        self.unpool2 = nn.MaxUnpool1d(2, stride=2)
        self.dec_mid = ConvBlock1D(d_model, d_model, kernel_size=3)

        self.unpool1 = nn.MaxUnpool1d(2, stride=2)
        self.dec_res = ResConvBlock1D(d_model, kernel_size=3)

        self.head = nn.Sequential(
            nn.Conv1d(d_model, d_model // 2, kernel_size=3, padding=1),
            nn.BatchNorm1d(d_model // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Conv1d(d_model // 2, d_in, kernel_size=1),
        )

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor | None = None,
        key_padding_mask: torch.Tensor | None = None,
        lengths: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Encode and reconstruct multi-temporal cycle.

        Parameters
        ----------
        x:
            Tensor of shape (B, T, d_in).

        Returns
        -------
        recon:
            Reconstructed tensor of shape (B, T, d_in).
        embedding:
            Latent bottleneck embedding of shape (B, latent_dim).
        """
        B, T, C = x.shape
        # Permute to (B, C, T) for 1D convolutions
        h = x.permute(0, 2, 1)

        # Stem & first block
        h = self.stem(h)
        h = self.enc_res(h)
        size1 = h.size()
        h, idx1 = self.pool1(h)

        # Second block
        h = self.enc_mid(h)
        size2 = h.size()
        h, idx2 = self.pool2(h)

        # Latent bottleneck embedding
        embedding = self.proj_latent(h)

        # Decode with unpooling to recover exact temporal dimensions
        h = self.unpool2(h, idx2, output_size=size2)
        h = self.dec_mid(h)

        h = self.unpool1(h, idx1, output_size=size1)
        h = self.dec_res(h)

        recon = self.head(h)  # (B, C, T)
        recon = recon.permute(0, 2, 1)  # (B, T, C)

        return recon, embedding

    def compute_anomaly_score(
        self,
        x: torch.Tensor,
        recon: torch.Tensor | None = None,
        reduction: str = "none",
    ) -> torch.Tensor:
        """Compute Huber (smooth L1) reconstruction anomaly score.

        Parameters
        ----------
        x: (B, T, C)
        recon: (B, T, C) or None (computed via forward)
        reduction: "none" -> (B, T), "cycle" -> (B,)

        Returns
        -------
        Anomaly score tensor.
        """
        if recon is None:
            recon, _ = self.forward(x)

        # Huber loss per (batch, time, band)
        err = F.smooth_l1_loss(recon, x, reduction="none", beta=0.1)
        # Average across feature channels
        per_bin = err.mean(dim=-1)  # (B, T)

        if reduction == "cycle":
            return per_bin.mean(dim=-1)
        return per_bin
