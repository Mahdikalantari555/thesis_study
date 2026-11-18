"""GRU autoencoder for irregular cycle sequences.

Encoder: multi-layer bidirectional GRU → final hidden as embedding.
Decoder: GRU that reconstructs tokens step-by-step conditioned on the embedding.
Operates on packed sequences where padding positions are masked in loss.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class CausalGRUAE(nn.Module):
    """Unidirectional GRU that predicts the current bin from earlier bins only.

    The GRU consumes the input tokens step by step; the reconstruction head
    maps the hidden state *before* consuming bin b (``h_{b-1}``, a learned
    initial state for b = 0) to that bin's value channels. Nothing after bin b
    can influence its prediction, which makes the leave-one-bin-out score
    causal by construction (design D4, ``gru_ae_main``).

    Input tokens are (values, observation-mask flags, optional DOY sin/cos);
    a withheld bin's value channels are zeroed before the forward pass while
    its observation-mask flags stay (they are covariates, not targets).
    """

    def __init__(
        self,
        d_in: int,
        n_out: int,
        d_model: int = 224,
        n_layers: int = 1,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.d_in = d_in
        self.n_out = n_out
        self.d_model = d_model
        self.n_layers = n_layers
        self.gru = nn.GRU(
            input_size=d_in,
            hidden_size=d_model,
            num_layers=n_layers,
            batch_first=True,
            dropout=dropout if n_layers > 1 else 0.0,
            bidirectional=False,
        )
        self.h0 = nn.Parameter(torch.zeros(n_layers, 1, d_model))
        self.head = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, n_out),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Return recon (B, T, n_out) where position t is predicted from h_{t-1}.

        Position 0 is predicted from the learned initial state; position t>0
        from the GRU hidden state after consuming tokens 0..t-1.
        """
        B, T, _ = x.shape
        h0 = self.h0.expand(self.n_layers, B, self.d_model).contiguous()
        h_all, _ = self.gru(x, h0)  # (B, T, d_model) hidden AFTER each token
        # Position 0 is predicted from the learned initial state (last layer);
        # position t>0 from the hidden state after consuming tokens 0..t-1.
        h_init = self.h0[-1].expand(B, 1, self.d_model)  # (B, 1, d_model)
        prev = torch.cat([h_init, h_all[:, :-1, :]], dim=1)
        return self.head(prev.contiguous())

    def masked_reconstruction_loss(
        self,
        x: torch.Tensor,
        pretext_mask: torch.Tensor,
        target: torch.Tensor,
        channel_mask: torch.Tensor | None = None,
        delta: float = 1.0,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Smooth-L1 loss on masked, observed channels only.

        x has the pretext-masked bins' value channels already zeroed.
        channel_mask (B, T, n_out) restricts the loss to observed entries.
        Returns (loss_scalar, per_token_loss (B, T)).
        """
        recon = self.forward(x)
        tok = F.smooth_l1_loss(recon, target, reduction="none", beta=delta).mean(dim=-1)
        loss_mask = pretext_mask.clone()
        if channel_mask is not None:
            loss_mask = loss_mask & channel_mask.any(dim=-1)
        tok = tok * loss_mask.float()
        n = loss_mask.sum(dim=1).clamp(min=1)
        loss = (tok.sum(dim=1) / n).mean()
        return loss, tok


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
