"""Controlled SSL pretext objectives on a shared 1D Transformer backbone (RQ2 / Gap G3).

Provides three self-supervised pretext arms with identical encoder architecture,
parameter budget, and sequence interface:
  1. ``masked_recon``: Random + cloud-block masked Huber reconstruction.
  2. ``traj_contrastive``: InfoNCE / NT-Xent trajectory-contrastive learning over
     stochastic cloud-gap and spectral-jittered cycle views.
  3. ``anomaly_degradation``: AnomalyBERT-style self-supervised token degradation
     replacement (contextual swap, local dip, spike, drift) + token discriminator.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .masked_tf import SinusoidalPositionalEncoding, TransformerBlock

PRETEXT_ARMS = ("masked_recon", "traj_contrastive", "anomaly_degradation", "time2agri")


class PretextTransformer(nn.Module):
    """Shared 1-D Transformer encoder supporting all three RQ2 pretext arms."""

    def __init__(
        self,
        d_in: int,
        n_bands: int,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 3,
        d_ff: int = 256,
        dropout: float = 0.1,
        max_len: int = 128,
        arm: str = "masked_recon",
    ) -> None:
        super().__init__()
        if arm not in PRETEXT_ARMS:
            raise ValueError(f"Unsupported arm={arm!r}; expected {PRETEXT_ARMS}")
        self.d_in = d_in
        self.n_bands = n_bands
        self.d_model = d_model
        self.arm = arm

        self.input_proj = nn.Linear(d_in, d_model)
        self.mask_embed = nn.Parameter(torch.zeros(1, 1, d_model))
        nn.init.normal_(self.mask_embed, std=0.02)
        self.pos = SinusoidalPositionalEncoding(d_model, max_len=max_len, dropout=dropout)
        self.blocks = nn.ModuleList(
            [TransformerBlock(d_model, n_heads, d_ff, dropout=dropout) for _ in range(n_layers)]
        )
        self.ln_f = nn.LayerNorm(d_model)
        self.embed_proj = nn.Linear(d_model, d_model)

        if arm == "masked_recon":
            self.task_head = nn.Sequential(
                nn.Linear(d_model, d_model),
                nn.GELU(),
                nn.Linear(d_model, d_in),
            )
        elif arm in ("traj_contrastive", "time2agri"):
            self.task_head = nn.Sequential(
                nn.Linear(d_model, d_model),
                nn.GELU(),
                nn.Linear(d_model, 32),
            )
        else:  # anomaly_degradation
            self.task_head = nn.Sequential(
                nn.Linear(d_model, d_model),
                nn.GELU(),
                nn.Linear(d_model, 1),
            )

    def encode_sequence(
        self,
        x: torch.Tensor,
        mask: torch.Tensor | None = None,
        key_padding_mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Return ``(h_seq: (B, T, d_model), pooled_emb: (B, d_model))``."""
        B, T, _ = x.shape
        h = self.input_proj(x)
        if mask is not None:
            m = mask.unsqueeze(-1).to(h.dtype)
            h = h * (1.0 - m) + self.mask_embed * m
        h = self.pos(h)

        if key_padding_mask is None:
            pad = torch.zeros(B, T, dtype=torch.bool, device=h.device)
        else:
            pad = key_padding_mask.clone()
            all_pad = pad.all(dim=1)
            if all_pad.any():
                pad[all_pad, 0] = False

        for blk in self.blocks:
            h = blk(h, key_padding_mask=pad)
        h = self.ln_f(h)

        obs = ~pad
        if mask is not None:
            obs = obs & ~mask
        denom = obs.sum(dim=1, keepdim=True).clamp(min=1).to(h.dtype)
        emb = (h * obs.unsqueeze(-1).to(h.dtype)).sum(dim=1) / denom
        emb = self.embed_proj(emb)
        return h, emb


def info_nce_loss(z1: torch.Tensor, z2: torch.Tensor, temperature: float = 0.2) -> torch.Tensor:
    """Symmetric NT-Xent / InfoNCE contrastive loss between paired trajectory views ``(B, D)``."""
    z1 = F.normalize(z1, dim=-1)
    z2 = F.normalize(z2, dim=-1)
    B = z1.size(0)
    if B < 2:
        return (1.0 - (z1 * z2).sum(dim=-1)).mean()
    reps = torch.cat([z1, z2], dim=0)  # (2B, D)
    sim = (reps @ reps.T) / float(temperature)
    eye = torch.eye(2 * B, dtype=torch.bool, device=z1.device)
    sim = sim.masked_fill(eye, -1e9)
    targets = torch.cat(
        [torch.arange(B, 2 * B, device=z1.device), torch.arange(0, B, device=z1.device)], dim=0
    )
    return F.cross_entropy(sim, targets)


def make_contrastive_views(
    tokens: torch.Tensor,
    pad_mask: torch.Tensor,
    n_bands: int,
    rng: np.random.Generator,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Create two phenology-preserving views via cloud-dropout and micro spectral jitter."""
    B, T, _ = tokens.shape
    v1 = tokens.clone()
    v2 = tokens.clone()

    # View 1: random 20% cloud-dropout padding + slight Gaussian band noise
    drop1 = torch.from_numpy(rng.random((B, T)) < 0.20) & (~pad_mask)
    p1 = pad_mask | drop1
    v1[:, :, :n_bands] += 0.08 * torch.randn_like(v1[:, :, :n_bands])

    # View 2: contiguous 2-3 token cloud gap + small gain/offset jitter
    p2 = pad_mask.clone()
    for i in range(B):
        s = int(rng.integers(0, max(1, T - 3)))
        p2[i, s : s + 2] = True
    scale_j = 1.0 + 0.06 * torch.randn(B, 1, n_bands, dtype=tokens.dtype)
    v2[:, :, :n_bands] = v2[:, :, :n_bands] * scale_j + 0.08 * torch.randn_like(v2[:, :, :n_bands])
    return v1, p1, v2, p2


def make_time2agri_views(
    tokens: torch.Tensor,
    pad_mask: torch.Tensor,
    n_bands: int,
    rng: np.random.Generator,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Time2Agri agricultural trajectory augmentations (Gupta & Sobti 2025).

    Generates two contrastive views using:
      1. Crop calendar phase shift (temporal roll of 1-2 bins within unpadded region).
      2. Multi-temporal cloud gap masking (extended 2-4 consecutive token drops).
      3. Canopy moisture and vegetation gain jitter on spectral channels.
    """
    B, T, d_in = tokens.shape
    v1 = tokens.clone()
    v2 = tokens.clone()
    p1 = pad_mask.clone()
    p2 = pad_mask.clone()

    for i in range(B):
        unpadded = torch.where(~pad_mask[i])[0]
        if len(unpadded) >= 6:
            # View 1: Calendar phase shift (+/- 1-2 bins)
            shift = int(rng.choice([-2, -1, 1, 2]))
            v1_sub = v1[i, unpadded, :n_bands].clone()
            v1[i, unpadded, :n_bands] = torch.roll(v1_sub, shifts=shift, dims=0)

            # View 2: Extended agricultural cloud gap (drop consecutive 2 to 4 bins)
            gap_len = int(rng.integers(2, min(5, len(unpadded) // 2)))
            gap_start = int(rng.integers(0, len(unpadded) - gap_len + 1))
            gap_indices = unpadded[gap_start : gap_start + gap_len]
            p2[i, gap_indices] = True

    # View 1: Mild spectral noise
    v1[:, :, :n_bands] += 0.05 * torch.randn_like(v1[:, :, :n_bands])

    # View 2: Canopy gain scaling on spectral bands
    canopy_scale = 1.0 + 0.08 * torch.randn(B, 1, n_bands, dtype=tokens.dtype, device=tokens.device)
    v2[:, :, :n_bands] = v2[:, :, :n_bands] * canopy_scale + 0.05 * torch.randn_like(v2[:, :, :n_bands])

    return v1, p1, v2, p2


def synthesize_anomalybert_degradation(
    tokens: torch.Tensor,
    pad_mask: torch.Tensor,
    n_bands: int,
    rng: np.random.Generator,
) -> tuple[torch.Tensor, torch.Tensor]:
    """AnomalyBERT-style token degradation replacement returning ``(corrupted_tokens, label_mask)``."""
    B, T, _ = tokens.shape
    out = tokens.clone()
    labels = torch.zeros((B, T), dtype=torch.float32)

    for i in range(B):
        if rng.random() < 0.25:
            # Leave 25% of cycles completely clean to calibrate false-positive baseline
            continue
        valid_idx = np.where(~pad_mask[i].numpy())[0]
        if valid_idx.size < 4:
            continue
        L = int(rng.integers(2, min(6, valid_idx.size)))
        start_pos = int(rng.integers(0, valid_idx.size - L + 1))
        seg = valid_idx[start_pos : start_pos + L]
        mode = int(rng.integers(0, 3))
        if mode == 0 and B >= 2:
            # Contextual patch swap from another cycle at shifted phase
            donor = (i + int(rng.integers(1, B))) % B
            donor_seg = np.clip((seg + T // 3) % T, 0, T - 1)
            out[i, seg, :n_bands] = tokens[donor, donor_seg, :n_bands] + 1.2 * torch.sign(
                torch.randn(len(seg), n_bands)
            )
        elif mode == 1:
            # Localized spectral drop / spike in standardized units
            delta = torch.from_numpy(rng.choice([-2.6, 2.6], size=(1, n_bands)).astype(np.float32))
            out[i, seg, :n_bands] += delta
        else:
            # Progressive multi-step ramp drift
            ramp = torch.linspace(1.2, 3.2, len(seg)).unsqueeze(-1)
            out[i, seg, :n_bands] -= ramp
        labels[i, seg] = 1.0
    return out, labels


def _arm_batch_loss(
    model: PretextTransformer,
    arm: str,
    bx: torch.Tensor,
    bp: torch.Tensor,
    n_bands: int,
    rng: np.random.Generator,
    T_max: int,
) -> torch.Tensor:
    """Per-batch pretext loss for one arm (shared by plain and tracked training)."""
    if arm == "masked_recon":
        bsz = bx.size(0)
        m_np = (rng.random((bsz, T_max)) < 0.25) & (~bp.numpy())
        for bi in range(bsz):
            st = int(rng.integers(0, max(1, T_max - 3)))
            m_np[bi, st : st + 3] = ~bp[bi, st : st + 3].numpy()
            if not m_np[bi].any():
                vp = np.where(~bp[bi].numpy())[0]
                if vp.size:
                    m_np[bi, vp[0]] = True
        m_t = torch.from_numpy(m_np)
        xin = bx.clone()
        xin[:, :, :n_bands][m_t] = 0.0
        h, _ = model.encode_sequence(xin, mask=m_t, key_padding_mask=bp)
        recon = model.task_head(h)
        err = F.smooth_l1_loss(
            recon[:, :, :n_bands], bx[:, :, :n_bands], reduction="none", beta=1.0
        ).mean(dim=-1)
        return (err * m_t.float()).sum() / m_t.float().sum().clamp(min=1.0)

    if arm in ("traj_contrastive", "time2agri"):
        if arm == "time2agri":
            v1, p1, v2, p2 = make_time2agri_views(bx, bp, n_bands, rng)
            temp = 0.15
        else:
            v1, p1, v2, p2 = make_contrastive_views(bx, bp, n_bands, rng)
            temp = 0.20
        _, e1 = model.encode_sequence(v1, mask=None, key_padding_mask=p1)
        _, e2 = model.encode_sequence(v2, mask=None, key_padding_mask=p2)
        z1 = model.task_head(e1)
        z2 = model.task_head(e2)
        return info_nce_loss(z1, z2, temperature=temp)

    # anomaly_degradation
    corrupted, y_deg = synthesize_anomalybert_degradation(bx, bp, n_bands, rng)
    h, _ = model.encode_sequence(corrupted, mask=None, key_padding_mask=bp)
    logits = model.task_head(h).squeeze(-1)
    valid_f = (~bp).float()
    bce = F.binary_cross_entropy_with_logits(logits, y_deg, reduction="none")
    return (bce * valid_f).sum() / valid_f.sum().clamp(min=1.0)


def _pad_tokens(tokens: list[np.ndarray]) -> tuple[torch.Tensor, torch.Tensor, int, int]:
    """Pad a token list into ``(X, padding_mask, T_max, d_in)`` tensors."""
    d_in = tokens[0].shape[1]
    T_max = max(t.shape[0] for t in tokens)
    N = len(tokens)
    X_pad = np.zeros((N, T_max, d_in), dtype=np.float32)
    P_pad = np.ones((N, T_max), dtype=bool)
    for i, t in enumerate(tokens):
        L = t.shape[0]
        X_pad[i, :L] = t
        P_pad[i, :L] = False
    return torch.from_numpy(X_pad), torch.from_numpy(P_pad), T_max, d_in


def train_pretext_arm(
    arm: str,
    train_tokens: list[np.ndarray],
    n_bands: int,
    *,
    epochs: int = 40,
    batch_size: int = 16,
    lr: float = 1.2e-3,
    seed: int = 42,
) -> PretextTransformer:
    """Train one of the three controlled pretext arms under an identical budget."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    X_t, P_t, T_max, d_in = _pad_tokens(train_tokens)

    model = PretextTransformer(
        d_in=d_in, n_bands=n_bands, d_model=64, n_heads=4, n_layers=3, d_ff=128, max_len=max(64, T_max + 4), arm=arm
    )
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    model.train()
    N = len(train_tokens)
    idx_all = np.arange(N)
    for _ in range(epochs):
        rng.shuffle(idx_all)
        for s in range(0, N, batch_size):
            b_idx = idx_all[s : s + batch_size]
            loss = _arm_batch_loss(model, arm, X_t[b_idx], P_t[b_idx], n_bands, rng, T_max)
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()

    model.eval()
    return model


def train_pretext_arm_tracked(
    arm: str,
    train_tokens: list[np.ndarray],
    n_bands: int,
    *,
    val_tokens: list[np.ndarray] | None = None,
    epochs: int = 40,
    batch_size: int = 16,
    lr: float = 1.2e-3,
    seed: int = 42,
) -> tuple[PretextTransformer, dict]:
    """Train a pretext arm while recording per-epoch train and validation loss.

    Returns ``(model, history)`` where ``history["train_loss"]`` and
    ``history["val_loss"]`` are lists of length ``epochs``. Validation loss is
    the mean pretext loss over ``val_tokens`` (batched, under ``no_grad``); when
    ``val_tokens`` is None, ``history["val_loss"]`` is filled with NaN.
    """
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    X_t, P_t, T_max, d_in = _pad_tokens(train_tokens)

    model = PretextTransformer(
        d_in=d_in, n_bands=n_bands, d_model=64, n_heads=4, n_layers=3, d_ff=128, max_len=max(64, T_max + 4), arm=arm
    )
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    if val_tokens:
        X_v, P_v, T_v, _ = _pad_tokens(val_tokens)
    else:
        X_v = P_v = None
        T_v = 0

    history: dict[str, list[float]] = {"train_loss": [], "val_loss": []}
    N = len(train_tokens)
    idx_all = np.arange(N)
    for _ in range(epochs):
        model.train()
        epoch_losses: list[float] = []
        rng.shuffle(idx_all)
        for s in range(0, N, batch_size):
            b_idx = idx_all[s : s + batch_size]
            loss = _arm_batch_loss(model, arm, X_t[b_idx], P_t[b_idx], n_bands, rng, T_max)
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            epoch_losses.append(float(loss.detach()))
        history["train_loss"].append(float(np.mean(epoch_losses)))
        if X_v is not None:
            model.eval()
            vloss: list[float] = []
            with torch.no_grad():
                for s in range(0, len(val_tokens), batch_size):
                    vloss.append(
                        float(_arm_batch_loss(model, arm, X_v[s : s + batch_size], P_v[s : s + batch_size], n_bands, rng, T_v))
                    )
            history["val_loss"].append(float(np.mean(vloss)))
        else:
            history["val_loss"].append(float("nan"))

    model.eval()
    return model, history


@torch.no_grad()
def score_cycle_pretext(
    model: PretextTransformer,
    tok_arr: np.ndarray,
    ref_embeddings: np.ndarray | None = None,
    eval_band_indices: list[int] | None = None,
) -> float:
    """Compute scalar cycle anomaly score for any of the three pretext arms."""
    T, _ = tok_arr.shape
    x = torch.from_numpy(tok_arr).unsqueeze(0)
    pad = torch.zeros((1, T), dtype=torch.bool)
    nb = model.n_bands
    use_b = eval_band_indices if eval_band_indices is not None else list(range(nb))

    if model.arm == "masked_recon":
        tok_rms = np.zeros(T, dtype=np.float64)
        for st in range(0, T, 3):
            en = min(T, st + 3)
            m = torch.zeros((1, T), dtype=torch.bool)
            m[0, st:en] = True
            xin = x.clone()
            xin[0, st:en, :nb] = 0.0
            h, _ = model.encode_sequence(xin, mask=m, key_padding_mask=pad)
            recon = model.task_head(h)
            diff = (recon[0, st:en, use_b] - x[0, st:en, use_b]).numpy()
            tok_rms[st:en] = np.sqrt(np.mean(diff**2, axis=-1))
        s = np.sort(tok_rms)
        return float(np.mean(s[-min(3, T) :]))

    if model.arm in ("traj_contrastive", "time2agri"):
        _, emb = model.encode_sequence(x, mask=None, key_padding_mask=pad)
        e_np = emb[0].numpy()
        e_norm = e_np / max(float(np.linalg.norm(e_np)), 1e-8)
        if ref_embeddings is None or len(ref_embeddings) == 0:
            return float(np.linalg.norm(e_np))
        ref_norm = ref_embeddings / np.maximum(np.linalg.norm(ref_embeddings, axis=1, keepdims=True), 1e-8)
        cos_dist = 1.0 - (ref_norm @ e_norm)
        cos_s = np.sort(cos_dist)
        nz = cos_s[cos_s > 1e-5]
        use = nz if nz.size >= 5 else cos_s
        return float(np.mean(use[: min(5, use.size)]))

    # anomaly_degradation
    h, _ = model.encode_sequence(x, mask=None, key_padding_mask=pad)
    probs = torch.sigmoid(model.task_head(h).squeeze(-1))[0].numpy()
    p_s = np.sort(probs)
    return float(np.mean(p_s[-min(3, T) :]))


class Time2AgriModel(nn.Module):
    """Time2Agri agricultural trajectory contrastive model (Gupta & Sobti 2025)."""

    def __init__(
        self,
        d_in: int,
        n_bands: int,
        d_model: int = 64,
        proj_dim: int = 32,
        n_heads: int = 4,
        n_layers: int = 3,
        d_ff: int = 128,
        dropout: float = 0.1,
        max_len: int = 128,
    ) -> None:
        super().__init__()
        self.d_in = d_in
        self.n_bands = n_bands
        self.d_model = d_model
        self.proj_dim = proj_dim

        self.encoder = PretextTransformer(
            d_in=d_in,
            n_bands=n_bands,
            d_model=d_model,
            n_heads=n_heads,
            n_layers=n_layers,
            d_ff=d_ff,
            dropout=dropout,
            max_len=max_len,
            arm="time2agri",
        )
        self.proj_head = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Linear(d_model, proj_dim),
        )

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor | None = None,
        key_padding_mask: torch.Tensor | None = None,
        lengths: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        h_seq, pooled_emb = self.encoder.encode_sequence(
            x, mask=mask, key_padding_mask=key_padding_mask
        )
        proj_emb = F.normalize(self.proj_head(pooled_emb), dim=-1)
        return proj_emb, pooled_emb

    def encode_trajectory(
        self, x: torch.Tensor, key_padding_mask: torch.Tensor | None = None
    ) -> torch.Tensor:
        """Return normalized contrastive projection embedding of shape (B, proj_dim)."""
        proj_emb, _ = self.forward(x, key_padding_mask=key_padding_mask)
        return proj_emb

    def compute_anomaly_score(
        self,
        x: torch.Tensor,
        ref_embeddings: torch.Tensor | None = None,
        key_padding_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Compute anomaly score based on cosine divergence in contrastive space."""
        z, _ = self.forward(x, key_padding_mask=key_padding_mask)
        if ref_embeddings is None:
            return 1.0 - (z * z).sum(dim=-1)
        ref_norm = F.normalize(ref_embeddings, dim=-1)
        sim = z @ ref_norm.T
        max_sim, _ = sim.max(dim=-1)
        return 1.0 - max_sim
