"""GRU autoencoder for irregular cycle sequences.

Encoder: multi-layer bidirectional GRU → final hidden as embedding.
Decoder: GRU that reconstructs tokens step-by-step conditioned on the embedding.
Operates on packed sequences where padding positions are masked in loss.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class GRUAutoencoder(nn.Module):
    """Small GRU autoencoder; CPU-friendly baseline SSL model.

    Parameters
    ----------
    d_in:
        Token feature dimension.
    d_model:
        Hidden size.
    n_layers:
        Number of stacked GRU layers in encoder/decoder.
    dropout:
        Dropout between GRU layers.
    bidirectional_enc:
        Whether the encoder GRU is bidirectional.
    """

    def __init__(
        self,
        d_in: int,
        d_model: int = 64,
        n_layers: int = 2,
        dropout: float = 0.1,
        bidirectional_enc: bool = True,
    ) -> None:
        super().__init__()
        self.d_in = d_in
        self.d_model = d_model
        self.n_layers = n_layers
        self.bidirectional_enc = bidirectional_enc

        self.encoder = nn.GRU(
            input_size=d_in,
            hidden_size=d_model,
            num_layers=n_layers,
            batch_first=True,
            dropout=dropout if n_layers > 1 else 0.0,
            bidirectional=bidirectional_enc,
        )
        enc_hidden = d_model * (2 if bidirectional_enc else 1)
        self.proj_enc = nn.Linear(enc_hidden, d_model)

        self.decoder = nn.GRU(
            input_size=d_in,
            hidden_size=d_model,
            num_layers=n_layers,
            batch_first=True,
            dropout=dropout if n_layers > 1 else 0.0,
        )
        self.out = nn.Linear(d_model, d_in)

    def forward(
        self,
        x: torch.Tensor,
        lengths: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Encode and decode.

        Parameters
        ----------
        x: (B, T, d_in)
        lengths: (B,) long tensor of true lengths (before padding).

        Returns
        -------
        recon : (B, T, d_in) — reconstructed tokens (including positions)
        embed : (B, d_model) — cycle embedding
        """
        B, T, _ = x.shape
        if lengths is not None:
            packed = nn.utils.rnn.pack_padded_sequence(
                x, lengths.cpu(), batch_first=True, enforce_sorted=False
            )
            _, h_n = self.encoder(packed)
        else:
            _, h_n = self.encoder(x)

        if self.bidirectional_enc:
            # h_n: (num_layers*2, B, d_model); combine directions
            h_n = h_n.view(self.n_layers, 2, B, self.d_model)
            h_last = torch.cat([h_n[-1, 0], h_n[-1, 1]], dim=-1)
        else:
            h_last = h_n[-1]
        embed = torch.tanh(self.proj_enc(h_last))

        # Decoder: initial hidden state is tiled embedding repeated across layers
        dec_h0 = embed.unsqueeze(0).expand(self.n_layers, -1, -1).contiguous()
        # Autoregressive? For a simple GRU-AE baseline we feed the (masked) input
        # and let the decoder reconstruct — akin to a denoising AE.
        dec_out, _ = self.decoder(x, dec_h0)
        recon = self.out(dec_out)
        return recon, embed

    def masked_reconstruction_loss(
        self,
        x: torch.Tensor,
        mask: torch.Tensor,
        lengths: torch.Tensor | None = None,
        delta: float = 1.0,
        trim_frac: float = 0.0,
        target: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Huber loss on masked tokens, with optional trimming of high-loss samples.

        Returns (loss_scalar, per_token_loss) where per_token_loss has shape (B, T).
        """
        recon, _ = self.forward(x, lengths)
        tgt = x if target is None else target
        # Huber / smooth L1
        tok_loss = F.smooth_l1_loss(recon, tgt, reduction="none", beta=delta)
        tok_loss = tok_loss.mean(dim=-1)  # (B, T)
        tok_loss = tok_loss * mask.float()
        # Per-sample loss (mean over masked tokens)
        n_masked = mask.sum(dim=1).clamp(min=1)
        per_sample = tok_loss.sum(dim=1) / n_masked
        if trim_frac > 0.0 and per_sample.numel() > 1:
            keep = max(1, int(per_sample.numel() * (1 - trim_frac)))
            thresh = torch.kthvalue(per_sample, keep).values
            keep_mask = per_sample <= thresh
            loss = per_sample[keep_mask].mean()
        else:
            loss = per_sample.mean()
        return loss, tok_loss
