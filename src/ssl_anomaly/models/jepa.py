"""JEPA: Joint-Embedding Predictive Architecture for phenological anomaly detection.

A context encoder encodes the observed bins (masked bins replaced with a learned
MASK token) and a predictor network estimates the latent representation of the
masked target tokens in embedding space. Targets come from an EMA copy of the
context encoder (no gradients, see ``latent_prediction_loss``); a lightweight
decoder maps the predicted latents back to the input space so the standard
growth-validation scoring (masked reconstruction error) applies.
"""

from __future__ import annotations

import copy

import torch
import torch.nn as nn
import torch.nn.functional as F


class _EncoderBlock(nn.Module):
    def __init__(self, d_model: int, n_heads: int, d_ff: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
        self.ff = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout),
        )
        self.ln1 = nn.LayerNorm(d_model)
        self.ln2 = nn.LayerNorm(d_model)

    def forward(self, x: torch.Tensor, key_padding_mask=None) -> torch.Tensor:
        h = self.ln1(x)
        a, _ = self.attn(h, h, h, key_padding_mask=key_padding_mask, need_weights=False)
        x = x + a
        x = x + self.ff(self.ln2(x))
        return x


class JEPAModel(nn.Module):
    """JEPA with masked-token prediction and an input-space decoder head."""

    def __init__(
        self,
        d_in: int,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 3,
        d_ff: int = 256,
        dropout: float = 0.1,
        max_len: int = 128,
        ema_momentum: float = 0.996,
    ) -> None:
        super().__init__()
        self.d_in = d_in
        self.d_model = d_model
        self.ema_momentum = ema_momentum

        self.input_proj = nn.Linear(d_in, d_model)
        self.mask_embed = nn.Parameter(torch.zeros(1, 1, d_model))
        nn.init.normal_(self.mask_embed, std=0.02)
        self.pos = nn.Embedding(max_len, d_model)

        self.context_encoder = nn.ModuleList(
            [_EncoderBlock(d_model, n_heads, d_ff, dropout=dropout) for _ in range(n_layers)]
        )
        self.target_encoder = copy.deepcopy(self.context_encoder)
        for p in self.target_encoder.parameters():
            p.requires_grad_(False)

        self.predictor = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, d_model),
        )
        self.decoder = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, d_in),
        )
        self.ln_f = nn.LayerNorm(d_model)
        self.embed_proj = nn.Linear(d_model, d_model)

    def _encode(self, encoder, x, mask, pad):
        B, T, _ = x.shape
        h = self.input_proj(x)
        if mask is not None:
            m = mask.unsqueeze(-1).to(h.dtype)
            h = h * (1 - m) + self.mask_embed * m
        pos = torch.arange(T, device=x.device)
        h = h + self.pos(pos).unsqueeze(0)
        for blk in encoder:
            h = blk(h, key_padding_mask=pad)
        h = self.ln_f(h)
        return h

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor | None = None,
        key_padding_mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        B, T, _ = x.shape
        if key_padding_mask is None:
            pad = torch.zeros(B, T, dtype=torch.bool, device=x.device)
        else:
            pad = key_padding_mask
        # Context: masked tokens replaced
        ctx = self._encode(self.context_encoder, x, mask, pad)
        # Predict masked positions
        pred = self.predictor(ctx)
        recon = self.decoder(pred)
        # Embedding: mean pool over observed tokens
        obs = ~pad
        if mask is not None:
            obs = obs & ~mask
        denom = obs.sum(dim=1, keepdim=True).clamp(min=1).to(ctx.dtype)
        emb = (ctx * obs.unsqueeze(-1).to(ctx.dtype)).sum(dim=1) / denom
        emb = self.embed_proj(emb)
        # EMA update target encoder (no grad; training steps only so eval-time
        # scoring never mutates the model).
        if self.training and torch.is_grad_enabled():
            with torch.no_grad():
                for pc, pt in zip(self.context_encoder.parameters(), self.target_encoder.parameters()):
                    pt.data.mul_(self.ema_momentum).add_(pc.data, alpha=1 - self.ema_momentum)
        return recon, emb

    def latent_prediction_loss(
        self,
        x: torch.Tensor,
        mask: torch.Tensor | None = None,
        key_padding_mask: torch.Tensor | None = None,
        target: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """I-JEPA-style loss: MSE between predicted and target latents.

        The predictor estimates the latents of the masked bins from the context
        encoding; targets are the EMA target-encoder representations of the same
        bins encoded without masking (stop-grad). ``target`` may override the
        sequence given to the target encoder (e.g. the un-corrupted tokens).
        """
        B, T, _ = x.shape
        pad = torch.zeros(B, T, dtype=torch.bool, device=x.device) if key_padding_mask is None else key_padding_mask
        ctx = self._encode(self.context_encoder, x, mask, pad)
        with torch.no_grad():
            tgt = self._encode(self.target_encoder, x if target is None else target, None, pad)
        pred = self.predictor(ctx)
        sel = ~pad if mask is None else mask & ~pad
        if not sel.any():
            return pred.sum() * 0.0
        return F.mse_loss(pred[sel], tgt[sel])

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
