"""Patch-level causal scorer: 2D CNN stem → per-location GRU → causal heads.

Change ``patch-level-controlled-trial`` task 1.2, spec "Patch-level controlled
PoC" and "Farm-boundary isolation of patch inputs and scores".

Shape contract (frozen by ``io/patches.py``): a field-cycle patch tensor is
``(T=36 bins, C=8 channels, S=32, S=32)`` fp16 values plus a boolean validity
mask of the same shape. The model consumes ONE field-cycle at a time and
predicts each bin from earlier bins only:

    x  (B, T, C, S, S)  raw or normalized values (NaN-free; caller zero-fills)
    m  (B, T, C, S, S)  bool observation mask  (pixel_valid ∧ in_field, per
                        channel — a channel can be unobserved at a pixel)
       -->  y_hat (B, T, n_out, S, S)   prediction of bin t from bins < t

The **farm boundary is the mask** (spec "Farm-boundary isolation"): the stem
input is ``concat[X·M_in, M_in]`` with ``M_in = pixel_valid ∧ in_field`` — the
mask is squeezed to one channel per bin (a pixel is usable when ANY channel is
observed, matching ``patches.BinAggregate.pixel_valid``), and out-of-field
values are multiplied by zero *before* the first convolution, so no conv, norm
or head can ever read a neighbouring field's values. ``test_patch_model.py``
proves byte-identity of in-field scores under out-of-field perturbation.

Design choices and why (they are load-bearing, not stylistic):

* **GroupNorm only, never BatchNorm.** Masked/zero pixels corrupt batch
  statistics across the batch dimension; GroupNorm normalizes per sample per
  group, so a patch's score cannot depend on which other patches share its
  batch. A dedicated regression test covers degenerate (all-masked) batches.
  The **CNN-off control uses per-pixel channel normalization instead**
  (:class:`PerPixelNorm`), because GroupNorm pools over the spatial extent and
  would let a pixel's value influence its neighbours — exactly the confound
  ``patch_pixelwise`` exists to remove.
* **Per-location GRU, no spatial coupling in the temporal module.** The CNN
  stem is the only place where neighbouring pixels mix (and it is masked at
  the farm boundary); the temporal recurrence runs independently at each of
  the S·S locations. This is the "no pooled latent" requirement: every pixel
  keeps its own hidden state, which is what makes per-pixel score maps and
  pixel-localization metrics possible at all.
* **Causal multi-horizon head (k = 1..3).** The head sees only h_{t-1}, so
  horizons 1..3 predict bins t, t+1, t+2 — the training objective is the
  hybrid of the proposal and the inference-time score still uses horizon 1
  (leave-one-bin-out, matching ``DeepCausalScorer.loo_batch``).
* **CNN-off control ``patch_pixelwise``** is the same class with
  ``use_cnn=False``: the stem collapses to a 1×1 conv (per-pixel channel
  mixing only), so the comparison isolates *spatial context* at identical
  budget, not a different model family.

NaN discipline: this module never sees NaN. ``train/patch_data.py`` zero-fills
unobserved entries and carries the mask separately; ``monitor/patch_scores.py``
unmasks on the way out. ``torch.nan_to_num`` is therefore used only in the loss
as a belt-and-braces guard against fp16 overflow, not as the mechanism.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

# k=1..3 horizons of the causal multi-horizon head (spec: "causal
# multi-horizon input-space prediction k=1–3").
HORIZONS: tuple[int, ...] = (1, 2, 3)
N_HORIZONS = len(HORIZONS)

# Parameter gates from task 1.2: the PoC budget is ≈90k ± 20 % with a hard
# ≤ 500k ceiling (G5 compares compute against gru_ae_main).
TARGET_PARAMS = 90_000
PARAM_TOLERANCE = 0.20
HARD_PARAM_CEILING = 500_000


class PerPixelNorm(nn.Module):
    """LayerNorm over the CHANNEL axis at each pixel — no spatial mixing.

    ``GroupNorm`` normalizes over channel groups *and* the spatial extent, so
    with it a single pixel's perturbation shifts the statistics of every other
    pixel in the patch. That is fatal for the ``patch_pixelwise`` control,
    whose only job is to answer "how much does spatial context contribute?":
    spatial leakage through a normalizer would silently give it part of the
    stem's advantage. ``test_pixelwise_control_does_not_mix_pixels`` pins this
    behaviour, which is why the CNN-off variant uses this module.
    """

    def __init__(self, channels: int) -> None:
        super().__init__()
        self.norm = nn.LayerNorm(channels)

    def forward(self, h: torch.Tensor) -> torch.Tensor:
        """(B, C, H, W) → normalized over C at every (h, w)."""
        return self.norm(h.permute(0, 2, 3, 1)).permute(0, 3, 1, 2)


def _group_norm(channels: int, *, max_groups: int = 8, per_pixel: bool = False) -> nn.Module:
    """GroupNorm with a group count that always divides ``channels``.

    Single-group fallback when the channel count is too small — never
    BatchNorm (see the module docstring).
    """
    if per_pixel:
        return PerPixelNorm(channels)
    g = min(max_groups, channels)
    while g > 1 and channels % g != 0:
        g -= 1
    return nn.GroupNorm(g, channels)


class PatchStem(nn.Module):
    """2D CNN stem: per-bin spatial context, mask-aware, stride-1 throughout.

    Stride stays 1 and no pooling exists, because the per-pixel score map has
    to stay aligned with the 32×32 grid (a downsampled score would need an
    invented interpolation back up — geometry is never resampled elsewhere in
    this project, so it is not introduced here either).

    ``use_cnn=False`` (the ``patch_pixelwise`` control) keeps the same tensor
    shapes and parameter plumbing but replaces the 3×3 spatial convolutions
    with 1×1 ones, so every output pixel sees only its own input pixel.
    """

    def __init__(
        self, in_ch: int, d_model: int, *, use_cnn: bool = True,
        widths: tuple[int, int] = (32, 48),
    ) -> None:
        super().__init__()
        self.use_cnn = use_cnn
        k = 3 if use_cnn else 1
        pad = k // 2
        w1, w2 = widths
        self.conv1 = nn.Conv2d(in_ch, w1, kernel_size=k, padding=pad)
        self.norm1 = _group_norm(w1, per_pixel=not use_cnn)
        self.conv2 = nn.Conv2d(w1, w2, kernel_size=k, padding=pad)
        self.norm2 = _group_norm(w2, per_pixel=not use_cnn)
        self.conv3 = nn.Conv2d(w2, d_model, kernel_size=k, padding=pad)
        self.norm3 = _group_norm(d_model, per_pixel=not use_cnn)
        self.act = nn.GELU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """(B, in_ch, S, S) → (B, d_model, S, S)."""
        h = self.act(self.norm1(self.conv1(x)))
        h = self.act(self.norm2(self.conv2(h)))
        h = self.act(self.norm3(self.conv3(h)))
        return h


class PatchCausalGRU(nn.Module):
    """Causal patch-level multi-horizon predictor (``patch_cnn_gru``).

    One forward pass returns, for every bin ``t`` and horizon ``k``, a
    prediction of bin ``t + k - 1`` made from bins ``≤ t`` — i.e. strictly
    causal in the sense of the spec scenario "x̂_{t+k} depends only on bins
    ≤ t": the GRU state after bin ``t`` has consumed only bins ``0..t``.
    """

    def __init__(
        self,
        n_channels: int = 8,
        d_model: int = 64,
        *,
        use_cnn: bool = True,
        n_horizons: int = N_HORIZONS,
        n_covariates: int = 0,
        stem_widths: tuple[int, int] = (44, 60),
    ) -> None:
        super().__init__()
        self.n_channels = int(n_channels)
        self.d_model = int(d_model)
        self.use_cnn = bool(use_cnn)
        self.n_horizons = int(n_horizons)
        self.n_covariates = int(n_covariates)

        # Stem input: n_channels value planes + 1 mask plane.
        self.stem = PatchStem(
            self.n_channels + 1, d_model, use_cnn=self.use_cnn, widths=stem_widths,
        )

        # Spatial aggregation 3×3 → 1×1 is NOT done: the per-location GRU
        # needs one token per pixel. Flattening is deferred to forward().
        self.gru = nn.GRU(
            input_size=d_model + self.n_covariates,
            hidden_size=d_model,
            num_layers=1,
            batch_first=True,
        )
        self.h0 = nn.Parameter(torch.zeros(1, d_model))

        # k horizons × n_channels predicted per location; the aux recon head
        # is horizon 1, kept as a separate module so the hybrid objective can
        # weight it independently.
        self.head_pred = nn.Linear(d_model, self.n_horizons * self.n_channels)
        self.head_aux = nn.Linear(d_model, self.n_channels)
        self._init_weights()

    def _init_weights(self) -> None:
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                nn.init.zeros_(m.bias)
            elif isinstance(m, nn.GRU):
                for name, p in m.named_parameters():
                    if "weight_ih" in name:
                        nn.init.xavier_uniform_(p)
                    elif "weight_hh" in name:
                        for i in range(3):
                            nn.init.orthogonal_(p[i * p.shape[1] // 3:(i + 1) * p.shape[1] // 3])
                    elif "bias" in name:
                        nn.init.zeros_(p)
        nn.init.zeros_(self.h0)

    # -- input assembly -------------------------------------------------
    def stem_input(self, x: torch.Tensor, pixel_valid: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Build ``concat[X·M_in, M_in]`` per bin — the farm-boundary contract.

        ``x``: (B, T, C, S, S) values, ``pixel_valid``: (B, T, S, S) bool or
        (B, T, 1, S, S). The values are multiplied by the mask BEFORE the
        stem, so out-of-field pixels are numerically zero, not "small".
        Returns the (B, T, C+1, S, S) stem input and the (B, T, S, S) mask.
        """
        if x.ndim != 5:
            raise ValueError(f"x must be (B, T, C, S, S), got {tuple(x.shape)}")
        B, T, C, S, _ = x.shape
        if self.n_channels != C:
            raise ValueError(f"x has {C} channels, model expects {self.n_channels}")
        m = pixel_valid
        if m.ndim == 5:
            if m.shape[2] != 1:
                raise ValueError(f"pixel_valid channel axis must be 1, got {m.shape[2]}")
            m = m[:, :, 0]
        if m.shape != (B, T, S, S):
            raise ValueError(f"pixel_valid must be {(B, T, S, S)}, got {tuple(m.shape)}")
        # One value-plane-dtype mask broadcast over channels: an in-field
        # pixel is usable when ANY channel is observed (matching
        # ``patches.BinAggregate.pixel_valid``); per-channel absence is handled
        # by the loss mask, not by the stem input.
        mf = m.to(dtype=x.dtype).unsqueeze(2)                    # (B, T, 1, S, S)
        m_ch = m.unsqueeze(2).expand(-1, -1, C, -1, -1)
        xm = torch.where(m_ch, x, torch.zeros_like(x))           # masked values
        return torch.cat([xm, mf], dim=2), m

    # -- forward --------------------------------------------------------
    def forward(
        self,
        x: torch.Tensor,
        pixel_valid: torch.Tensor,
        covariates: torch.Tensor | None = None,
    ) -> dict[str, torch.Tensor]:
        """Causal predictions for one batch of field-cycles.

        Returns a dict with
            ``pred``   (B, T, n_horizons, C, S, S)  — pred[t, k] targets bin
                                                      t + k - 1 (zero where
                                                      that bin does not exist)
            ``aux``    (B, T, C, S, S)              — horizon-1 reconstruction
            ``mask``   (B, T, S, S)                 — the effective in-field mask
        """
        B, T = x.shape[0], x.shape[1]
        stem_in, m = self.stem_input(x, pixel_valid)              # (B,T,C+1,S,S)
        h = self.stem(stem_in.reshape(B * T, self.n_channels + 1, *x.shape[-2:]))
        # (B*T, d_model, S, S) → (B, T, S*S, d_model): one token per location.
        d_model = h.shape[1]
        h = h.reshape(B, T, d_model, -1).permute(0, 1, 3, 2)      # (B,T,P,d)
        if covariates is not None:
            if covariates.shape[:2] != (B, T):
                raise ValueError(
                    f"covariates must be (B, T, n_cov), got {tuple(covariates.shape)}"
                )
            cov = covariates.unsqueeze(2).expand(B, T, h.shape[2], covariates.shape[-1])
            h = torch.cat([h, cov.to(h.dtype)], dim=-1)
        elif self.n_covariates:
            raise ValueError(f"model declares {self.n_covariates} covariates but none were given")

        P = h.shape[2]
        tok = h.permute(0, 2, 1, 3).reshape(B * P, T, -1)         # (B*P, T, d_in)
        h0 = self.h0.expand(B * P, -1).unsqueeze(0).contiguous()
        seq, _ = self.gru(tok, h0)                               # (B*P, T, d)
        seq = seq.reshape(B, P, T, d_model).permute(0, 2, 1, 3)   # (B, T, P, d)

        S = x.shape[-2]
        pred = self.head_pred(seq).reshape(B, T, self.n_horizons, self.n_channels, S, S)
        aux = self.head_aux(seq).reshape(B, T, self.n_channels, S, S)

        # Horizon k at bin t predicts bin t+k-1: zero out-of-range slots so a
        # caller flattening (T, k) never mistakes padding for prediction.
        if self.n_horizons > 1:
            keep = torch.zeros(T, self.n_horizons, dtype=pred.dtype, device=pred.device)
            for k in range(self.n_horizons):
                keep[: max(0, T - k), k] = 1.0
            pred = pred * keep[None, :, :, None, None, None]
        return {"pred": pred, "aux": aux, "mask": m}

    # -- losses ---------------------------------------------------------
    def hybrid_loss(
        self,
        out: dict[str, torch.Tensor],
        target: torch.Tensor,
        obs: torch.Tensor,
        *,
        weights: tuple[float, ...] = (1.0, 0.5, 0.25),
        aux_weight: float = 0.3,
        trimmed_top_frac: float = 0.0,
    ) -> tuple[torch.Tensor, dict[str, float]]:
        """Multi-horizon masked Smooth-L1 + masked-recon auxiliary loss.

        ``target``: (B, T, C, S, S) values at every bin; ``obs``: the per-pixel
        per-channel observation mask (NOT the in-field mask — an in-field pixel
        with no acquisition at that bin carries no target).

        ``trimmed_top_frac`` > 0 drops the worst fraction of PER-TOKEN losses
        (robust training against unlabelled residual contamination, task 1.4:
        top-5 % after a 10-epoch warm-up). The caller controls the schedule;
        trimming is a no-op at 0.
        """
        B, T = target.shape[0], target.shape[1]
        C = self.n_channels
        obs_f = obs.to(target.dtype)
        losses: dict[str, float] = {}

        total = target.new_zeros(())
        for k in range(self.n_horizons):
            # Prediction at bin t targets bin t+k-1: shift the target forward.
            if k == 0:
                pred_k, tgt_k, obs_k = out["pred"][:, :, 0], target, obs_f
            else:
                pred_k = out["pred"][:, : max(0, T - k), k]
                tgt_k = target[:, k:]
                obs_k = obs_f[:, k:]
            if pred_k.shape[1] == 0:
                continue
            tok = F.smooth_l1_loss(pred_k, tgt_k, reduction="none").mean(dim=2)  # (B,T,S,S)
            tok = tok * obs_k.mean(dim=2)                                        # any-channel
            tok = self._trim(tok, obs_k.mean(dim=2), trimmed_top_frac)
            denom = obs_k.mean(dim=2).sum().clamp(min=1.0) * B
            lk = tok.sum() / denom
            w = weights[k] if k < len(weights) else weights[-1]
            total = total + w * lk
            losses[f"horizon{k + 1}"] = float(lk.detach())

        aux_tok = F.smooth_l1_loss(out["aux"], target, reduction="none").mean(dim=2)
        aux_w = obs_f.mean(dim=2)
        aux_tok = self._trim(aux_tok, aux_w, trimmed_top_frac) * aux_w
        aux_denom = aux_w.sum().clamp(min=1.0) * B
        l_aux = aux_tok.sum() / aux_denom
        losses["aux"] = float(l_aux.detach())
        total = total + aux_weight * l_aux
        losses["total"] = float(total.detach())
        return total, losses

    @staticmethod
    def _trim(tok: torch.Tensor, w: torch.Tensor, frac: float) -> torch.Tensor:
        """Zero the highest-``frac`` per-token losses among observed tokens."""
        if frac <= 0.0:
            return tok
        flat = tok.reshape(-1)
        obs = w.reshape(-1) > 0
        if not bool(obs.any()):
            return tok
        vals = flat[obs]
        q = torch.quantile(vals.detach(), 1.0 - float(frac)) if vals.numel() > 1 else None
        if q is None:
            return tok
        keep = torch.where(vals <= q, torch.ones_like(vals), torch.zeros_like(vals))
        out = flat.clone()
        out[obs] = flat[obs] * keep
        return out.reshape(tok.shape)

    # -- parameter gate -------------------------------------------------
    def param_report(self) -> dict:
        """Parameter count + the task-1.2 gates (≈90k ±20 %, hard ≤500k)."""
        n = sum(p.numel() for p in self.parameters() if p.requires_grad)
        return {
            "n_parameters": int(n),
            "target": TARGET_PARAMS,
            "within_target_band": bool(
                abs(n - TARGET_PARAMS) <= PARAM_TOLERANCE * TARGET_PARAMS
            ),
            "under_hard_ceiling": bool(n <= HARD_PARAM_CEILING),
        }


def build_patch_model(
    *,
    use_cnn: bool = True,
    n_channels: int = 8,
    d_model: int = 64,
    n_covariates: int = 0,
    n_horizons: int = N_HORIZONS,
    stem_widths: tuple[int, int] = (44, 60),
) -> PatchCausalGRU:
    """Factory for ``patch_cnn_gru`` (``use_cnn=True``) / ``patch_pixelwise``."""
    return PatchCausalGRU(
        n_channels=n_channels,
        d_model=d_model,
        use_cnn=use_cnn,
        n_covariates=n_covariates,
        n_horizons=n_horizons,
        stem_widths=stem_widths,
    )


def scorer_id(use_cnn: bool) -> str:
    """The eval_dev-facing arm name (task 2.4)."""
    return "patch_cnn_gru" if use_cnn else "patch_pixelwise"


__all__ = [
    "HARD_PARAM_CEILING",
    "HORIZONS",
    "N_HORIZONS",
    "PARAM_TOLERANCE",
    "TARGET_PARAMS",
    "PatchCausalGRU",
    "PatchStem",
    "PerPixelNorm",
    "build_patch_model",
    "scorer_id",
]
