"""Unified causal scorers for field monitoring (design D4/D5).

Every candidate exposes the same interface:

    fit(train data) -> fitted scorer
    score_cycle(...) -> (n_bins,) per-bin causal score (NaN where unobserved)

Scores are observed-mask-weighted MSE in z-space for the deep models and mean
squared robust-z for B1 — both are "the causal prediction error of the current
bin from earlier bins", comparable on the same axis. Display squashing
(1 − exp(−MSE)) lives in the exporter only; thresholds are set on raw scores.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import torch

from ssl_anomaly.models.gru_ae import CausalGRUAE
from ssl_anomaly.models.masked_tf import CausalMaskedTransformer

log = logging.getLogger("ssl_anomaly.monitor.models")

N_DATA_CHANNELS = 8


# ---------------------------------------------------------------------------
# Token building (values + observation-mask flags + optional DOY)
# ---------------------------------------------------------------------------
def build_tokens(z: np.ndarray, m: np.ndarray, doy: np.ndarray | None) -> np.ndarray:
    """Stack (values, mask flags, doy) into model input (T, d_in).

    z: (T, C) normalized values (zeros where unobserved);
    m: (T, C) bool observation mask; doy: (T, 2) or None.
    """
    parts = [z.astype(np.float32), m.astype(np.float32)]
    if doy is not None:
        parts.append(doy.astype(np.float32))
    return np.concatenate(parts, axis=-1)


def token_dim(n_channels: int, use_doy: bool) -> int:
    return n_channels * 2 + (2 if use_doy else 0)


# ---------------------------------------------------------------------------
# Deep causal scorers
# ---------------------------------------------------------------------------
@dataclass
class ModelConfig:
    d_model: int
    n_layers: int
    d_ff: int = 160
    n_heads: int = 4
    dropout: float = 0.1

    def to_dict(self) -> dict:
        return {
            "d_model": self.d_model, "n_layers": self.n_layers, "d_ff": self.d_ff,
            "n_heads": self.n_heads, "dropout": self.dropout,
        }


DEFAULT_CONFIGS: dict[str, dict] = {
    # Sized so masked_transformer and gru_ae land within ±20 % parameters
    # (masked_tf ≈165 k, gru_ae ≈174 k; asserted in test_monitor_causality).
    "masked_transformer": {"d_model": 80, "n_layers": 3, "d_ff": 160, "n_heads": 4, "dropout": 0.1},
    "gru_ae": {"d_model": 200, "n_layers": 1, "dropout": 0.1},
    # gru_pred (change predictive-ssl-controlled-trial): the SAME trunk and
    # budget as gru_ae_main — only the training objective differs (causal
    # one-step-ahead prediction). Pre-registered: no architecture redesign.
    "gru_pred": {"d_model": 200, "n_layers": 1, "dropout": 0.1},
}


def build_model(model_id: str, d_in: int, n_out: int, cfg: dict | None = None) -> torch.nn.Module:
    """Instantiate one of the causal deep models."""
    cfg = dict(cfg or DEFAULT_CONFIGS[model_id])
    if model_id == "masked_transformer":
        return CausalMaskedTransformer(
            d_in=d_in, n_out=n_out,
            d_model=cfg["d_model"], n_heads=cfg.get("n_heads", 4),
            n_layers=cfg["n_layers"], d_ff=cfg.get("d_ff", 160),
            dropout=cfg.get("dropout", 0.1),
        )
    if model_id in ("gru_ae", "gru_pred"):
        return CausalGRUAE(
            d_in=d_in, n_out=n_out,
            d_model=cfg["d_model"], n_layers=cfg.get("n_layers", 1),
            dropout=cfg.get("dropout", 0.1),
        )
    raise ValueError(f"Unknown model id {model_id}")


def count_parameters(model: torch.nn.Module) -> int:
    return int(sum(p.numel() for p in model.parameters()))


class DeepCausalScorer:
    """Wraps a causal deep model for token building and leave-one-bin-out scoring."""

    def __init__(
        self,
        model_id: str,
        model: torch.nn.Module,
        n_channels: int = N_DATA_CHANNELS,
        use_doy: bool = True,
        device: str | torch.device = "cpu",
    ) -> None:
        self.model_id = model_id
        self.model = model.to(device)
        self.device = torch.device(device)
        self.n_channels = n_channels
        self.use_doy = use_doy

    # -- tokens ---------------------------------------------------------
    def tokens(self, z: np.ndarray, m: np.ndarray, doy: np.ndarray | None) -> torch.Tensor:
        """(1, T, d_in) input tensor from one cycle."""
        t = build_tokens(z, m, doy if self.use_doy else None)
        return torch.from_numpy(t).float().unsqueeze(0).to(self.device)

    # -- scoring --------------------------------------------------------
    @torch.no_grad()
    def loo_batch(
        self,
        z_batch: np.ndarray,   # (N, T, C) normalized values (zeros where unobserved)
        m_batch: np.ndarray,   # (N, T, C) bool observation mask
        doy_batch: np.ndarray | None,  # (N, T, 2) or None
        *,
        chunk: int = 512,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Batched leave-one-bin-out scoring for N cycles.

        For every observed bin b of a cycle, bin b's value channels are
        withheld (transformer: replaced by the mask embedding; GRU: zeroed)
        and predicted causally from bins ≤ b. Returns:
            scores: (N, T) observed-mask-weighted squared error in z-space
                    (NaN where the bin is unobserved)
            pred_z: (N, T, C) withheld-bin predictions in z-space
        Later bins cannot influence score(b) (causal attention /
        unidirectional GRU); ``.eval()`` + no_grad make it deterministic.
        """
        self.model.eval()
        N, T, C = z_batch.shape
        idx_t = torch.arange(T, device=self.device)

        base = np.concatenate(
            [z_batch.astype(np.float32), m_batch.astype(np.float32),
             (doy_batch.astype(np.float32) if (doy_batch is not None and self.use_doy) else
              np.zeros((N, T, 0), dtype=np.float32))],
            axis=-1,
        )  # (N, T, d_in)

        # Variant (n, b): cycle n with bin b withheld → base[n] with values[b]=0.
        base_t = torch.from_numpy(base).to(self.device)

        scores = np.full((N, T), np.nan)
        pred_z = np.zeros((N, T, C), dtype=np.float32)

        for n0 in range(0, N, max(1, chunk // T)):
            n1 = min(N, n0 + max(1, chunk // T))
            bn = n1 - n0
            variants = base_t[n0:n1].unsqueeze(1).expand(bn, T, T, base_t.shape[-1]).clone()
            eye = torch.eye(T, dtype=torch.bool, device=self.device)
            variants[:, eye] = 0.0  # withhold bin b's value channels in variant b
            vflat = variants.reshape(bn * T, T, -1)
            pretext = torch.eye(T, dtype=torch.bool, device=self.device).unsqueeze(0).expand(bn, T, T).reshape(bn * T, T)
            if self.model_id == "masked_transformer":
                pad_np = ~m_batch[n0:n1].any(axis=-1)  # (bn, T)
                pad = torch.from_numpy(pad_np).to(self.device).unsqueeze(1).expand(bn, T, T).reshape(bn * T, T)
                recon = self.model(vflat, pretext_mask=pretext, key_padding_mask=pad)
            else:
                recon = self.model(vflat)
            recon = recon.reshape(bn, T, T, C)
            # Prediction of bin b in variant b:
            pred = recon[torch.arange(bn, device=self.device)[:, None],
                         torch.arange(T, device=self.device)[None, :],
                         torch.arange(T, device=self.device)[None, :]]  # (bn, T, C)
            pred_z[n0:n1] = pred.cpu().numpy()

            z_t = torch.from_numpy(z_batch[n0:n1].astype(np.float32)).to(self.device)
            m_t = torch.from_numpy(m_batch[n0:n1].astype(np.float32)).to(self.device)
            err = (pred - z_t) ** 2  # (bn, T, C)
            wsum = (err * m_t).sum(dim=-1)
            wcnt = m_t.sum(dim=-1).clamp(min=1.0)
            s = (wsum / wcnt).cpu().numpy()
            unobs = ~m_batch[n0:n1].any(axis=-1)
            s[unobs] = np.nan
            scores[n0:n1] = s
        return scores, pred_z

    @torch.no_grad()
    def score_cycle(self, z: np.ndarray, m: np.ndarray, doy: np.ndarray | None) -> np.ndarray:
        """Per-bin causal score for one cycle: (T,) float, NaN where unobserved."""
        s, _ = self.loo_batch(
            z[None].astype(np.float32), m[None].astype(bool),
            (doy[None] if doy is not None else None),
        )
        return s[0].astype(np.float64)

    @staticmethod
    def _as_tensor(x) -> torch.Tensor:
        """Coerce numpy arrays / tensors to a float32-or-bool tensor."""
        if isinstance(x, torch.Tensor):
            return x
        x = np.asarray(x)
        if x.dtype == np.bool_:
            return torch.from_numpy(x)
        return torch.from_numpy(x.astype(np.float32))

    def recon_losses(
        self,
        tokens_batch,
        pretext,
        target,
        channel_mask,
        key_padding=None,
        delta: float = 1.0,
    ) -> torch.Tensor:
        """Batch masked-reconstruction loss for training (returns scalar).

        Accepts numpy arrays or tensors for pretext/target/masks. NOT under
        ``no_grad`` — gradients must flow (the training loop guards against
        non-finite loss/grads around this call). The caller controls
        train/eval mode (train_main sets ``model.train()`` per epoch; eval
        paths use :meth:`eval_recon_loss` which forces eval mode).
        """
        pretext = self._as_tensor(pretext).to(self.device)
        channel_mask = self._as_tensor(channel_mask).bool().to(self.device)
        if self.model_id == "masked_transformer":
            kp = None if key_padding is None else self._as_tensor(key_padding).bool().to(self.device)
            loss, _ = self.model.masked_reconstruction_loss(
                tokens_batch, pretext, target,
                key_padding_mask=kp, channel_mask=channel_mask, delta=delta,
            )
        else:
            loss, _ = self.model.masked_reconstruction_loss(
                tokens_batch, pretext, target, channel_mask=channel_mask, delta=delta,
            )
        return loss

    @torch.no_grad()
    def eval_recon_loss(
        self,
        tokens_batch,
        pretext,
        target,
        channel_mask,
        key_padding=None,
        delta: float = 1.0,
    ) -> float:
        """Deterministic masked-reconstruction loss on a batch (early stopping).

        Forces eval mode (dropout off) and returns the scalar loss.
        """
        was_training = self.model.training
        self.model.eval()
        try:
            loss = self.recon_losses(tokens_batch, pretext, target, channel_mask, key_padding, delta)
        finally:
            if was_training:
                self.model.train()
        return float(loss.item())


# ---------------------------------------------------------------------------
# Predictive one-step-ahead scorer (change predictive-ssl-controlled-trial)
# ---------------------------------------------------------------------------
class DeepPredictiveScorer:
    """One-step-ahead predictive scorer for the ``gru_pred`` arm.

    ``pred(o) = f(z[<o])``: the trunk's output at position o is
    ``head(h_{o-1})`` — a function of tokens < o only (naturally causal; NO
    LOO withholding and no pretext masking at inference). ``loo_batch`` keeps
    the :class:`DeepCausalScorer` signature so the UNCHANGED production
    pipeline (causal offset correction → per-cell q95 → trailing channel-max
    → τ) consumes it transparently — mirroring the probe's logic with a
    learned forecaster.
    """

    def __init__(
        self,
        model_id: str,
        model: torch.nn.Module,
        n_channels: int = N_DATA_CHANNELS,
        use_doy: bool = True,
        device: str | torch.device = "cpu",
    ) -> None:
        self.model_id = model_id
        self.model = model.to(device)
        self.device = torch.device(device)
        self.n_channels = n_channels
        self.use_doy = use_doy

    @torch.no_grad()
    def loo_batch(
        self,
        z_batch: np.ndarray,   # (N, T, C) normalized values (zeros where unobserved)
        m_batch: np.ndarray,   # (N, T, C) bool observation mask
        doy_batch: np.ndarray | None,  # (N, T, 2) or None
        *,
        chunk: int = 512,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Single-pass one-step-ahead scoring for N cycles (same signature as
        :meth:`DeepCausalScorer.loo_batch`).

        Returns:
            scores: (N, T) observed-mask-weighted squared error in z-space
                    (the D5 secondary statistic; NaN where the bin is
                    unobserved)
            pred_z: (N, T, C) one-step-ahead predictions in z-space; pred at
                    bin o is a function of bins < o only.
        """
        self.model.eval()
        N, T, C = z_batch.shape
        z = np.where(m_batch, z_batch, 0.0)  # sanitize: production z-space semantics
        base = np.concatenate(
            [z.astype(np.float32), m_batch.astype(np.float32),
             (doy_batch.astype(np.float32) if (doy_batch is not None and self.use_doy) else
              np.zeros((N, T, 0), dtype=np.float32))],
            axis=-1,
        )
        base_t = torch.from_numpy(base).to(self.device)
        scores = np.full((N, T), np.nan)
        pred_z = np.zeros((N, T, C), dtype=np.float32)
        for n0 in range(0, N, max(1, chunk // T)):
            n1 = min(N, n0 + max(1, chunk // T))
            recon = self.model(base_t[n0:n1])  # (bn, T, C); position t ← h_{t-1}
            pred_z[n0:n1] = recon.cpu().numpy()
            z_t = torch.from_numpy(z[n0:n1].astype(np.float32)).to(self.device)
            m_t = torch.from_numpy(m_batch[n0:n1].astype(np.float32)).to(self.device)
            err = (recon - z_t) ** 2
            wsum = (err * m_t).sum(dim=-1)
            wcnt = m_t.sum(dim=-1).clamp(min=1.0)
            s = (wsum / wcnt).cpu().numpy()
            unobs = ~m_batch[n0:n1].any(axis=-1)
            s[unobs] = np.nan
            scores[n0:n1] = s
        return scores, pred_z

    @torch.no_grad()
    def score_cycle(self, z: np.ndarray, m: np.ndarray, doy: np.ndarray | None) -> np.ndarray:
        """(T,) per-bin one-step-ahead score for one cycle; NaN where unobserved."""
        s, _ = self.loo_batch(
            z[None].astype(np.float32), m[None].astype(bool),
            (doy[None] if doy is not None else None),
        )
        return s[0].astype(np.float64)

    def _as_tensor(self, x) -> torch.Tensor:
        if isinstance(x, torch.Tensor):
            return x
        x = np.asarray(x)
        if x.dtype == np.bool_:
            return torch.from_numpy(x)
        return torch.from_numpy(x.astype(np.float32))

    def predictive_losses(
        self,
        tokens_batch,          # (B, T, d_in) UNMASKED tokens (values + mask flags + doy)
        target,                # (B, T, C) z values
        channel_mask,          # (B, T, C) bool observation mask
        *,
        delta: float = 1.0,
        nonfinite_guard: bool = False,
    ) -> torch.Tensor:
        """Causal one-step-ahead training loss: smooth-L1 (Huber, ``delta``)
        over OBSERVED (bin, channel) pairs — per-pair granularity (the
        pre-registered objective; the loss choice is recorded in
        ``train_main.PREDICTIVE_OBJECTIVE`` BEFORE training, no post-hoc
        switching).

        The prediction at bin o is the model output at o = head(h_{o-1}), a
        function of tokens < o only — no pretext masking is needed (unlike
        reconstruction, there is no trivial identity to prevent: the target
        bin's value never enters its own prediction).

        ``nonfinite_guard``: raise FloatingPointError when a NON-FINITE value
        sits at an OBSERVED pair (malformed input — fail loudly). NaN garbage
        at UNOBSERVED pairs is sanitized (token value channels → 0, matching
        the production z-space semantics) so it cannot poison the recurrence;
        their loss contribution is excluded by the mask.
        """
        tokens_batch = self._as_tensor(tokens_batch).float().to(self.device)
        target = self._as_tensor(target).float().to(self.device)
        channel_mask = self._as_tensor(channel_mask).bool().to(self.device)
        if nonfinite_guard:
            bad_target = ~torch.isfinite(target) & channel_mask
            if bool(bad_target.any()):
                idx = bad_target.nonzero()[0].tolist()
                raise FloatingPointError(
                    f"non-finite target at an observed (bin, channel) pair: {idx}")
        n_out = self.model.n_out
        vals = tokens_batch[..., :n_out]
        vals = torch.where(channel_mask, vals, torch.zeros_like(vals))
        tokens_clean = torch.cat([vals, tokens_batch[..., n_out:]], dim=-1)
        recon = self.model(tokens_clean)
        import torch.nn.functional as F

        err = F.smooth_l1_loss(recon, target, reduction="none", beta=delta)
        err = torch.where(channel_mask, err, torch.zeros_like(err))
        n = channel_mask.sum().clamp(min=1)
        return err.sum() / n


# ---------------------------------------------------------------------------
# B1 PhaseZ causal reference
# ---------------------------------------------------------------------------
class B1PhaseZCausal:
    """Phase-aware robust z-score using train statistics; causal by construction.

    score(b) = mean over observed channels of z², with
    z = (x_raw − median[phase_bin, band]) / scale[phase_bin, band].

    The statistics come from the TRAIN split only and are frozen at fit time,
    so the score of bin b depends only on bin b's own values and frozen
    constants — no future information.

    ``use_doy=True`` (R3 ablation arm) keys the statistics by a coarse DOY
    season group (sin(2π·doy/365.25) ≥ 0 vs < 0) with hierarchical fallback to
    the pooled phase-bin statistics where the group has fewer than ``min_n``
    observations, mirroring ``baseline/robust.py``.
    """

    def __init__(self, use_doy: bool = True, min_n: int = 8) -> None:
        self.use_doy = use_doy
        self.min_n = min_n
        self.band_names: list[str] = []
        self.median: np.ndarray | None = None  # (G, 36, C) or (1, 36, C)
        self.scale: np.ndarray | None = None
        self.robust_range: np.ndarray | None = None  # (C,) raw-unit q95−q05
        self.mad_k = 1.4826
        self.scale_floor = 1e-3

    @staticmethod
    def season_group(doy_sin: np.ndarray) -> np.ndarray:
        """0/1 group per bin from sin(2π·doy/365.25)."""
        return (np.asarray(doy_sin) >= 0).astype(np.int64)

    def fit(self, X_raw: np.ndarray, M: np.ndarray, doy_sin: np.ndarray | None = None) -> "B1PhaseZCausal":
        N, B, C = X_raw.shape
        G = 2 if self.use_doy else 1
        self.median = np.zeros((G, B, C))
        self.scale = np.zeros((G, B, C))

        groups = (
            self.season_group(doy_sin) if (self.use_doy and doy_sin is not None) else np.zeros((N, B), dtype=np.int64)
        )

        # Pooled per-bin stats first (the fallback for every group).
        pooled_med = np.zeros((B, C))
        pooled_scale = np.zeros((B, C))
        for c in range(C):
            for b in range(B):
                vals = X_raw[:, b, c][M[:, b, c]].astype(np.float64)
                if vals.size >= self.min_n:
                    med = float(np.median(vals))
                    pooled_med[b, c] = med
                    pooled_scale[b, c] = max(float(np.median(np.abs(vals - med))) * self.mad_k, self.scale_floor)
            vals_all = X_raw[:, :, c][M[:, :, c]].astype(np.float64)
            weak = pooled_scale[:, c] <= 0
            if vals_all.size and weak.any():
                med = float(np.median(vals_all))
                pooled_med[weak, c] = med
                pooled_scale[weak, c] = max(
                    float(np.median(np.abs(vals_all - med))) * self.mad_k, self.scale_floor
                )

        for g in range(G):
            self.median[g] = pooled_med
            self.scale[g] = pooled_scale
            if G == 1:
                continue
            for c in range(C):
                for b in range(B):
                    sel = groups[:, b] == g
                    vals = X_raw[sel, b, c][M[sel, b, c]].astype(np.float64)
                    if vals.size >= self.min_n:
                        med = float(np.median(vals))
                        s = float(np.median(np.abs(vals - med))) * self.mad_k
                        if s > 0:
                            self.median[g, b, c] = med
                            self.scale[g, b, c] = s
        self.band_names = [f"ch{i}" for i in range(C)]

        # Raw-unit robust range per band (NRMSE denominator, same definition
        # as inputs.fit_robust_norm so deep models and B1 stay comparable).
        self.robust_range = np.ones(C, dtype=np.float64)
        for c in range(C):
            vals = X_raw[:, :, c][M[:, :, c]].astype(np.float64)
            if vals.size >= 8:
                q05, q95 = np.percentile(vals, [5, 95])
                self.robust_range[c] = max(float(q95 - q05), self.scale_floor)
        return self

    def score_cycle(self, x_raw: np.ndarray, m: np.ndarray, doy_sin: np.ndarray | None) -> np.ndarray:
        """(T,) per-bin mean z² over observed channels; NaN where unobserved.

        x_raw: (T, C) raw values; m: (T, C) bool observation mask;
        doy_sin: (T,) sin-of-DOY per bin (only used when ``use_doy``).
        """
        x = np.asarray(x_raw, dtype=np.float64)
        mb = np.asarray(m, dtype=bool)
        if x.ndim != 2:
            raise ValueError("B1PhaseZCausal.score_cycle expects (T, C) arrays")
        T = x.shape[0]
        if self.use_doy and doy_sin is not None:
            g = self.season_group(np.asarray(doy_sin))  # (T,)
        else:
            g = np.zeros(T, dtype=np.int64)
        rows = np.arange(T)
        med = self.median[g, rows]  # (T, C)
        scale = self.scale[g, rows]
        z = np.where(mb, (x - med) / scale, 0.0)
        wsum = np.where(mb, z * z, 0.0).sum(axis=-1)
        wcnt = np.maximum(mb.sum(axis=-1), 1)
        score = wsum / wcnt
        score[~mb.any(axis=-1)] = np.nan
        return score
