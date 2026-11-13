"""Lightning module for SSL training + checkpointing."""

from __future__ import annotations

import logging
from typing import Any

import lightning as L
import torch

from ..config import SSLCfg
from ..models.gru_ae import GRUAutoencoder
from ..models.masked_tf import MaskedTransformer

log = logging.getLogger("ssl_anomaly.train.lit")


class SSLLitModule(L.LightningModule):
    """Lightning wrapper around GRU-AE / Masked Transformer with masked Huber loss."""

    def __init__(
        self,
        d_in: int,
        cfg: SSLCfg,
    ) -> None:
        super().__init__()
        self.save_hyperparameters(ignore=[])
        self.cfg = cfg
        self.d_in = d_in
        if cfg.model == "gru_ae":
            self.model = GRUAutoencoder(
                d_in=d_in,
                d_model=cfg.gru_ae.d_model,
                n_layers=cfg.gru_ae.n_layers,
                dropout=cfg.gru_ae.dropout,
                bidirectional_enc=cfg.gru_ae.bidirectional_enc,
            )
        elif cfg.model == "transformer":
            self.model = MaskedTransformer(
                d_in=d_in,
                d_model=cfg.transformer.d_model,
                n_heads=cfg.transformer.n_heads,
                n_layers=cfg.transformer.n_layers,
                d_ff=cfg.transformer.d_ff,
                dropout=cfg.transformer.dropout,
                max_len=cfg.transformer.max_len,
                pos_encoding=cfg.transformer.pos_encoding,
            )
        else:
            raise ValueError(f"Unknown model: {cfg.model}")

    # ----- forward ------------------------------------------------------
    def forward(self, batch: dict) -> tuple[torch.Tensor, torch.Tensor]:
        if isinstance(self.model, GRUAutoencoder):
            return self.model(batch["tokens"], lengths=batch.get("lengths"))
        return self.model(
            batch["tokens"],
            mask=batch.get("mask"),
            key_padding_mask=batch.get("pamask"),
        )

    def _compute_loss(self, batch: dict) -> torch.Tensor:
        target = batch.get("original")
        if isinstance(self.model, GRUAutoencoder):
            loss, _ = self.model.masked_reconstruction_loss(
                batch["tokens"],
                batch["mask"],
                lengths=batch.get("lengths"),
                delta=self.cfg.huber_delta,
                trim_frac=self.cfg.trim_loss_frac,
                target=target,
            )
        else:
            loss, _ = self.model.masked_reconstruction_loss(
                batch["tokens"],
                batch["mask"],
                key_padding_mask=batch.get("pamask"),
                delta=self.cfg.huber_delta,
                trim_frac=self.cfg.trim_loss_frac,
                target=target,
            )
        return loss

    # ----- lightning hooks ---------------------------------------------
    def training_step(self, batch: dict, batch_idx: int) -> torch.Tensor:
        loss = self._compute_loss(batch)
        self.log("train/loss", loss, on_step=True, on_epoch=True, prog_bar=True)
        return loss

    def validation_step(self, batch: dict, batch_idx: int) -> torch.Tensor:
        loss = self._compute_loss(batch)
        self.log("val/loss", loss, on_step=False, on_epoch=True, prog_bar=True)
        return loss

    def configure_optimizers(self) -> dict[str, Any]:
        opt = torch.optim.AdamW(
            self.parameters(), lr=self.cfg.lr, weight_decay=self.cfg.weight_decay
        )
        sched = torch.optim.lr_scheduler.ReduceLROnPlateau(
            opt, mode="min", factor=0.5, patience=max(2, self.cfg.early_stop_patience // 2)
        )
        return {
            "optimizer": opt,
            "lr_scheduler": {"scheduler": sched, "monitor": "val/loss", "interval": "epoch"},
        }

    # ----- inference helpers -------------------------------------------
    @torch.no_grad()
    def embed(self, tokens: torch.Tensor, pamask: torch.Tensor | None = None,
              lengths: torch.Tensor | None = None) -> torch.Tensor:
        if isinstance(self.model, GRUAutoencoder):
            _, emb = self.model(tokens, lengths=lengths)
        else:
            _, emb = self.model(tokens, mask=None, key_padding_mask=pamask)
        return emb

    @torch.no_grad()
    def reconstruct(
        self, tokens: torch.Tensor, pamask: torch.Tensor | None = None,
        lengths: torch.Tensor | None = None, mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        if isinstance(self.model, GRUAutoencoder):
            recon, _ = self.model(tokens, lengths=lengths)
        else:
            recon, _ = self.model(tokens, mask=mask, key_padding_mask=pamask)
        return recon
