"""Masked 1-D Transformer encoder for self-supervised cycle modeling.

Design choices inspired by Presto (Tseng et al. 2023) and MAE-style masked
autoencoders, but adapted to irregular, unequal-length field cycles with
a learned <[BOS_never_used_51bce0c785ca2f68081bfa7d91973934]> token and structured (random + block) masking that mimics
cloud gaps.
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F


class SinusoidalPositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 256, dropout: float = 0.1) -> None:
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        pe = torch.zeros(max_len, d_model)
        pos = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
        div = torch.exp(torch.arange(0, d_model, 2, dtype=torch.float32) * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(pos * div)
        pe[:, 1::2] = torch.cos(pos * div)
        self.register_buffer("pe", pe.unsqueeze(0))  # (1, max_len, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        T = x.size(1)
        return self.dropout(x + self.pe[:, :T])


class LearnedPositionalEncoding(nn.Module):
    def __init__(self, d_model: int, max_len: int = 256, dropout: float = 0.1) -> None:
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        self.emb = nn.Embedding(max_len, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        T = x.size(1)
        pos = torch.arange(T, device=x.device)
        return self.dropout(x + self.emb(pos).unsqueeze(0))


class TransformerBlock(nn.Module):
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

    def forward(self, x: torch.Tensor, key_padding_mask: torch.Tensor | None = None) -> torch.Tensor:
        # key_padding_mask: True = ignore (batch, T)
        h = self.ln1(x)
        a, _ = self.attn(
            h, h, h,
            key_padding_mask=key_padding_mask,
            need_weights=False,
        )
        x = x + a
        x = x + self.ff(self.ln2(x))
        return x


class CausalTransformerBlock(nn.Module):
    """TransformerBlock restricted to a causal attention pattern.

    ``attn_mask`` is the standard (T, T) boolean mask where True = forbidden;
    position t may attend only to positions <= t. Dropout follows the parent
    convention and is disabled by ``.eval()``.
    """

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
        self.d_model = d_model

    def forward(
        self,
        x: torch.Tensor,
        key_padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        T = x.size(1)
        causal = torch.triu(
            torch.ones(T, T, dtype=torch.bool, device=x.device), diagonal=1
        )
        h = self.ln1(x)
        a, _ = self.attn(
            h, h, h,
            attn_mask=causal,
            key_padding_mask=key_padding_mask,
            need_weights=False,
        )
        # Fully-masked query rows (unobserved/padded positions under a causal
        # mask) come out of MHA as NaN; torch's masked softmax cannot normalize
        # an empty key set. Their content is unused padding, but if left as NaN
        # they contaminate every later query that attends them through
        # 0 × NaN = NaN in the masked attention weights (measured: NaN spread
        # from padded rows to observed rows in the next block). Zero them.
        a = torch.nan_to_num(a, nan=0.0)
        x = x + a
        x = x + self.ff(self.ln2(x))
        return x


class CausalMaskedTransformer(nn.Module):
    """Causal 1-D Transformer with masked reconstruction of observed bins only.

    Input tokens are (values, observation-mask flags, optional DOY sin/cos);
    the reconstruction head outputs the value channels only. The pretext masks
    a subset of the *observed* bins; a masked bin must be predicted from bins
    at or before its own index (causal attention), never from the future —
    this is what makes the leave-one-bin-out score causal (design D4/D5).
    """

    def __init__(
        self,
        d_in: int,
        n_out: int,
        d_model: int = 80,
        n_heads: int = 4,
        n_layers: int = 3,
        d_ff: int = 160,
        dropout: float = 0.1,
        max_len: int = 64,
    ) -> None:
        super().__init__()
        self.d_in = d_in
        self.n_out = n_out
        self.d_model = d_model
        self.input_proj = nn.Linear(d_in, d_model)
        self.mask_embed = nn.Parameter(torch.zeros(1, 1, d_model))
        nn.init.normal_(self.mask_embed, std=0.02)
        self.pos = SinusoidalPositionalEncoding(d_model, max_len=max_len, dropout=dropout)
        self.blocks = nn.ModuleList(
            [CausalTransformerBlock(d_model, n_heads, d_ff, dropout=dropout) for _ in range(n_layers)]
        )
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, n_out),
        )

    def forward(
        self,
        x: torch.Tensor,
        pretext_mask: torch.Tensor | None = None,
        key_padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Return recon (B, T, n_out).

        x: (B, T, d_in); pretext_mask: (B, T) bool True where the bin is
        withheld (value replaced by the learned mask embedding);
        key_padding_mask: (B, T) bool True = padding (fully unobserved bins).
        """
        h = self.input_proj(x)
        if pretext_mask is not None:
            m = pretext_mask.unsqueeze(-1).to(h.dtype)
            h = h * (1 - m) + self.mask_embed.expand_as(h) * m
        h = self.pos(h)
        pad = key_padding_mask if key_padding_mask is not None else torch.zeros(
            x.shape[0], x.shape[1], dtype=torch.bool, device=x.device
        )
        for blk in self.blocks:
            h = blk(h, key_padding_mask=pad)
        h = self.ln_f(h)
        return self.head(h)

    def masked_reconstruction_loss(
        self,
        x: torch.Tensor,
        pretext_mask: torch.Tensor,
        target: torch.Tensor,
        key_padding_mask: torch.Tensor | None = None,
        channel_mask: torch.Tensor | None = None,
        delta: float = 1.0,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Smooth-L1 loss on masked, observed channels only.

        x: (B, T, d_in); pretext_mask: (B, T); target: (B, T, n_out) the value
        channels; channel_mask: (B, T, n_out) bool observation mask (loss is
        computed only on observed entries — masked entries give zero loss).
        Returns (loss_scalar, per_token_loss (B, T)).
        """
        recon = self.forward(x, pretext_mask=pretext_mask, key_padding_mask=key_padding_mask)
        tok = F.smooth_l1_loss(recon, target, reduction="none", beta=delta).mean(dim=-1)  # (B, T)
        # Fully-unobserved (padded) query positions attend to an empty key set
        # under the causal mask → their recon is NaN. Those positions are
        # excluded by the loss mask, so zero the NaNs first to keep 0 * NaN
        # out of the reduction.
        tok = torch.nan_to_num(tok, nan=0.0)
        loss_mask = pretext_mask.clone()
        if channel_mask is not None:
            loss_mask = loss_mask & channel_mask.any(dim=-1)
        if key_padding_mask is not None:
            loss_mask = loss_mask & ~key_padding_mask
        tok = tok * loss_mask.float()
        n = loss_mask.sum(dim=1).clamp(min=1)
        loss = (tok.sum(dim=1) / n).mean()
        return loss, tok


class MaskedTransformer(nn.Module):
    """1-D Transformer encoder with masked (denoising) reconstruction head.

    Masked tokens are replaced with a learnable MASK embedding before the
    encoder runs. A lightweight head projects each encoded position back
    to the original feature dimension.
    """

    def __init__(
        self,
        d_in: int,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 3,
        d_ff: int = 256,
        dropout: float = 0.1,
        max_len: int = 128,
        pos_encoding: str = "sine",
    ) -> None:
        super().__init__()
        self.d_in = d_in
        self.d_model = d_model
        self.input_proj = nn.Linear(d_in, d_model)
        self.mask_embed = nn.Parameter(torch.zeros(1, 1, d_model))
        nn.init.normal_(self.mask_embed, std=0.02)
        if pos_encoding == "learned":
            self.pos = LearnedPositionalEncoding(d_model, max_len=max_len, dropout=dropout)
        else:
            self.pos = SinusoidalPositionalEncoding(d_model, max_len=max_len, dropout=dropout)
        self.blocks = nn.ModuleList(
            [TransformerBlock(d_model, n_heads, d_ff, dropout=dropout) for _ in range(n_layers)]
        )
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, d_in),
        )
        # Embedding head: mean-pool over observed (non-masked, non-pad) tokens
        self.embed_proj = nn.Linear(d_model, d_model)

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor | None = None,
        key_padding_mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        x: (B, T, d_in)
        mask: (B, T) bool, True where tokens are masked (replaced with mask embed)
        key_padding_mask: (B, T) bool, True where tokens are padding (ignore in attention)
        Returns (recon, embed): both (B,T,d_in) and (B,d_model)
        """
        B, T, _ = x.shape
        h = self.input_proj(x)
        if mask is not None:
            m = mask.unsqueeze(-1).to(h.dtype)
            h = h * (1 - m) + self.mask_embed * m
        h = self.pos(h)
        if key_padding_mask is None:
            pad = torch.zeros(B, T, dtype=torch.bool, device=h.device)
        else:
            pad = key_padding_mask
        for blk in self.blocks:
            h = blk(h, key_padding_mask=pad)
        h = self.ln_f(h)
        recon = self.head(h)
        # Embedding: mean-pool over non-pad, non-masked tokens (or non-pad if no mask)
        obs = ~pad
        if mask is not None:
            obs = obs & ~mask
        denom = obs.sum(dim=1, keepdim=True).clamp(min=1).to(h.dtype)
        emb = (h * obs.unsqueeze(-1).to(h.dtype)).sum(dim=1) / denom
        emb = self.embed_proj(emb)
        return recon, emb

    def masked_reconstruction_loss(
        self,
        x: torch.Tensor,
        mask: torch.Tensor,
        key_padding_mask: torch.Tensor | None = None,
        delta: float = 1.0,
        trim_frac: float = 0.0,
        target: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        recon, _ = self.forward(x, mask=mask, key_padding_mask=key_padding_mask)
        tgt = x if target is None else target
        tok_loss = F.smooth_l1_loss(recon, tgt, reduction="none", beta=delta).mean(dim=-1)  # (B, T)
        # Loss only on masked tokens (and ignore padding)
        loss_mask = mask.clone()
        if key_padding_mask is not None:
            loss_mask = loss_mask & ~key_padding_mask
        tok_loss = tok_loss * loss_mask.float()
        n = loss_mask.sum(dim=1).clamp(min=1)
        per_sample = tok_loss.sum(dim=1) / n
        if trim_frac > 0.0 and per_sample.numel() > 1:
            keep = max(1, int(per_sample.numel() * (1 - trim_frac)))
            thresh = torch.kthvalue(per_sample, keep).values
            loss = per_sample[per_sample <= thresh].mean()
        else:
            loss = per_sample.mean()
        return loss, tok_loss
