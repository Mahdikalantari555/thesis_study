"""RQ4 (Gap G8) Cloud-Robustness & Phase Stability Evaluators (E-ALIGN, E-SEG, E-NORM).

Quantifies anomaly-detection retention across observation completeness levels
(100% ~10d cadence -> 75% ~16d -> 50% ~24d -> 35% ~monthly + winter cloud blocks)
comparing SSL WITH explicit ``date/Δt`` conditioning vs. SSL WITHOUT ``date/Δt``
conditioning, alongside ``docs/final_plan.md`` §4.4 experiments ``E-ALIGN``,
``E-SEG``, and ``E-NORM``.
"""

from __future__ import annotations

import warnings

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import average_precision_score

from ..baseline import (
    aggregate_band_scores,
    fit_baseline,
    recall_at_alert_budget,
    score_cycle,
    trimmed_normal_cycles,
)
from .stats import spearman_correlation

COMPLETENESS_LEVELS = (1.00, 0.75, 0.50, 0.35)


def subsample_cloud_completeness(
    tok_seq: np.ndarray,
    completeness: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Subsample an irregular cycle token array to ``completeness`` fraction (with cloud blocks).

    Returns ``(sub_tokens, kept_indices)`` preserving chronological order.
    """
    T = tok_seq.shape[0]
    if completeness >= 0.999 or T <= 5:
        return tok_seq.copy(), np.arange(T, dtype=np.int64)

    target_k = max(4, int(round(T * float(completeness))))
    keep = np.ones(T, dtype=bool)
    # Inject a realistic contiguous cloud block first (winter overcast)
    blk_len = min(T - target_k, max(1, int(round((1.0 - completeness) * T * 0.45))))
    if blk_len > 0 and T - blk_len >= 4:
        s = int(rng.integers(1, max(2, T - blk_len)))
        keep[s : s + blk_len] = False

    rem_drop = int(keep.sum()) - target_k
    if rem_drop > 0:
        avail = np.where(keep)[0]
        drop_i = rng.choice(avail, size=min(rem_drop, avail.size - 4), replace=False)
        keep[drop_i] = False

    idx = np.where(keep)[0]
    sub = tok_seq[idx].copy()
    return sub, idx


def prepare_conditioned_tokens(
    X_cycles: np.ndarray,
    med: np.ndarray,
    scale: np.ndarray,
    *,
    include_date_dt: bool = True,
) -> list[np.ndarray]:
    """Convert ``(N, K, B)`` binned cycles into irregular observed-only token sequences.

    Each observed bin ``k`` becomes a token ``[standardized_bands (B), dsh_norm, dt_norm, sin_doy, cos_doy]``.
    When ``include_date_dt=False``, the 4 temporal/gap coordinates are zeroed so the
    Transformer relies purely on discrete sequence index ``0..L-1``.
    """
    N, K, B = X_cycles.shape
    tau_grid = np.linspace(0.0, 1.0, K, dtype=np.float32)
    out: list[np.ndarray] = []
    for i in range(N):
        obs = np.any(np.isfinite(X_cycles[i]), axis=-1)
        idx = np.where(obs)[0]
        if idx.size < 4:
            idx = np.arange(min(6, K))
        z = (X_cycles[i, idx] - med[None, :]) / scale[None, :]
        z = np.nan_to_num(z, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

        if include_date_dt:
            dsh_n = tau_grid[idx][:, None]
            dt = np.diff(idx.astype(np.float32), prepend=idx[0] - 1.0)[:, None] / 4.0
            ang = 2.0 * np.pi * dsh_n
            t_feats = np.hstack([dsh_n, dt, np.sin(ang), np.cos(ang)]).astype(np.float32)
        else:
            t_feats = np.zeros((idx.size, 4), dtype=np.float32)
        out.append(np.hstack([z, t_feats]).astype(np.float32))
    return out


def recompute_dt_after_subsample(
    sub_tok: np.ndarray,
    *,
    include_date_dt: bool,
) -> np.ndarray:
    """Update ``Δt`` from preserved physical ``dsh_n`` after cloud subsampling."""
    out = sub_tok.copy()
    if not include_date_dt:
        out[:, -4:] = 0.0
        return out
    dsh_n = out[:, -4:-3]  # exact physical tau in [0, 1] preserved from full cycle!
    phys_bin = dsh_n[:, 0] * 35.0
    dt = np.diff(phys_bin, prepend=phys_bin[0] - 1.0)[:, None] / 4.0
    ang = 2.0 * np.pi * dsh_n
    out[:, -4:] = np.hstack([dsh_n, dt, np.sin(ang), np.cos(ang)]).astype(np.float32)
    return out


class IrregularDateConditionedTransformer(nn.Module):
    """1D Transformer comparing explicit ``date/Δt`` conditioning vs discrete ``0..L-1`` index."""

    def __init__(
        self,
        d_in: int,
        n_bands: int,
        *,
        include_date_dt: bool,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 3,
        d_ff: int = 128,
        dropout: float = 0.1,
        max_len: int = 64,
    ) -> None:
        super().__init__()
        self.n_bands = n_bands
        self.include_date_dt = include_date_dt
        self.band_proj = nn.Linear(n_bands, d_model)
        self.mask_token = nn.Parameter(torch.zeros(1, 1, d_model))
        nn.init.normal_(self.mask_token, std=0.02)

        if include_date_dt:
            self.phase_pos = nn.Embedding(max_len, d_model)
            nn.init.normal_(self.phase_pos.weight, std=0.02)
            self.dt_proj = nn.Linear(3, d_model)
            self.discrete_pos = None
        else:
            self.phase_pos = None
            self.dt_proj = None
            self.discrete_pos = nn.Parameter(torch.zeros(1, max_len, d_model))
            nn.init.normal_(self.discrete_pos, std=0.02)

        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_ff,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=n_layers)
        self.norm = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, n_bands)

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor | None = None,
        key_padding_mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        B, L, _ = x.shape
        h = self.band_proj(x[:, :, : self.n_bands])
        if mask is not None:
            h = torch.where(mask.unsqueeze(-1), self.mask_token.expand(B, L, -1), h)

        if self.include_date_dt and self.phase_pos is not None and self.dt_proj is not None:
            dsh_n = x[:, :, self.n_bands]
            p_idx = torch.clamp((dsh_n * 35.0).round().long(), 0, self.phase_pos.num_embeddings - 1)
            dt_doy = x[:, :, self.n_bands + 1 : self.n_bands + 4]
            h = h + self.phase_pos(p_idx) + 0.15 * self.dt_proj(dt_doy)
        elif self.discrete_pos is not None:
            h = h + self.discrete_pos[:, :L, :]

        safe_pad = key_padding_mask
        if safe_pad is not None:
            all_pad = safe_pad.all(dim=1)
            if all_pad.any():
                safe_pad = safe_pad.clone()
                safe_pad[all_pad, 0] = False

        z = self.norm(self.encoder(h, src_key_padding_mask=safe_pad))
        return self.head(z), z


def train_irregular_ssl(
    train_seqs: list[np.ndarray],
    n_bands: int,
    *,
    include_date_dt: bool,
    epochs: int = 25,
    lr: float = 1.5e-3,
    seed: int = 42,
) -> nn.Module:
    """Train IrregularDateConditionedTransformer with completeness augmentation."""
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    d_in = train_seqs[0].shape[1]
    T_max = max(t.shape[0] for t in train_seqs)

    model = IrregularDateConditionedTransformer(
        d_in=d_in,
        n_bands=n_bands,
        include_date_dt=include_date_dt,
        d_model=64,
        n_heads=4,
        n_layers=3,
        d_ff=128,
        dropout=0.1,
        max_len=max(64, T_max + 4),
    )
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    N = len(train_seqs)
    idx_all = np.arange(N)
    model.train()
    for _ in range(epochs):
        rng.shuffle(idx_all)
        for s in range(0, N, 32):
            b_idx = idx_all[s : s + 32]
            aug_seqs = []
            for ii in b_idx:
                comp = float(rng.choice([1.0, 0.85, 0.65, 0.45]))
                sub, _ = subsample_cloud_completeness(train_seqs[ii], comp, rng)
                sub = recompute_dt_after_subsample(sub, include_date_dt=include_date_dt)
                aug_seqs.append(sub)

            L_max = max(a.shape[0] for a in aug_seqs)
            bsz = len(aug_seqs)
            bx = np.zeros((bsz, L_max, d_in), dtype=np.float32)
            bp = np.ones((bsz, L_max), dtype=bool)
            bm = np.zeros((bsz, L_max), dtype=bool)
            for j, a in enumerate(aug_seqs):
                Lj = a.shape[0]
                bx[j, :Lj] = a
                bp[j, :Lj] = False
                m_j = rng.random(Lj) < 0.28
                if not m_j.any():
                    m_j[Lj // 2] = True
                bm[j, :Lj] = m_j

            bx_t = torch.from_numpy(bx)
            bp_t = torch.from_numpy(bp)
            bm_t = torch.from_numpy(bm)
            xin = bx_t.clone()
            xin[:, :, :n_bands][bm_t] = 0.0

            recon, _ = model(xin, mask=bm_t, key_padding_mask=bp_t)
            err = F.smooth_l1_loss(recon, bx_t[:, :, :n_bands], reduction="none", beta=1.0).mean(dim=-1)
            loss = (err * bm_t.float()).sum() / bm_t.float().sum().clamp(min=1.0)
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()

    model.eval()
    return model


@torch.no_grad()
def score_irregular_ssl_batch(
    model: nn.Module,
    seqs: list[np.ndarray],
    n_bands: int,
) -> np.ndarray:
    """Batched sliding-mask reconstruction score on variable-length sequences."""
    N = len(seqs)
    d_in = seqs[0].shape[1]
    L_max = max(s.shape[0] for s in seqs)
    bx = np.zeros((N, L_max, d_in), dtype=np.float32)
    bp = np.ones((N, L_max), dtype=bool)
    for i, s in enumerate(seqs):
        L = s.shape[0]
        bx[i, :L] = s
        bp[i, :L] = False

    bx_t = torch.from_numpy(bx)
    bp_t = torch.from_numpy(bp)
    tok_rms = np.full((N, L_max), np.nan, dtype=np.float64)

    for st in range(0, L_max, 3):
        en = min(L_max, st + 3)
        bm = torch.zeros((N, L_max), dtype=torch.bool)
        bm[:, st:en] = ~bp_t[:, st:en]
        xin = bx_t.clone()
        xin[:, st:en, :n_bands] = 0.0
        recon, _ = model(xin, mask=bm, key_padding_mask=bp_t)
        diff = (recon[:, st:en, :] - bx_t[:, st:en, :n_bands]).numpy()
        rms = np.sqrt(np.mean(diff**2, axis=-1))
        rms[(bp_t[:, st:en]).numpy()] = np.nan
        tok_rms[:, st:en] = rms

    out = np.zeros(N, dtype=np.float64)
    for i in range(N):
        fin = np.sort(tok_rms[i][np.isfinite(tok_rms[i])])
        out[i] = float(np.mean(fin[-min(3, fin.size) :])) if fin.size else 0.0
    return out


def evaluate_e_align_three_metrics(
    X_by_axis: dict[str, np.ndarray],
    field_ids: np.ndarray,
    seed: int = 42,
) -> dict[str, dict]:
    """Compute the 3 quantitative E-ALIGN metrics from ``docs/final_plan.md`` §4.4:
      1. Within-bin MAD scatter across normal cycles (lower = tighter phase alignment)
      2. Leave-one-out median prediction MAE
      3. Anomaly score Spearman stability under 30% random observation dropout
    """
    rng = np.random.default_rng(seed)
    results: dict[str, dict] = {}
    for axis_name, X_ax in X_by_axis.items():
        X_by_f: dict[int, list[np.ndarray]] = {}
        for row, f in zip(X_ax, field_ids):
            X_by_f.setdefault(int(f), []).append(row)
        X_by_f_arr = {f: np.stack(v, axis=0) for f, v in X_by_f.items()}

        act = trimmed_normal_cycles(
            {"all": X_ax},
            strata_per_cycle={"all": np.ones(len(X_ax), dtype=bool)},
            X_by_field=X_by_f_arr,
            min_n=4,
            q=0.15,
            iters=3,
        )["all"]
        X_norm = X_ax[act]

        with warnings.catch_warnings(), np.errstate(all="ignore"):
            warnings.simplefilter("ignore", category=RuntimeWarning)
            # Normalize each band by its global IQR so axes are comparable in unitless units
            g_q75, g_q25 = np.nanpercentile(X_norm, [75, 25], axis=(0, 1))
            b_iqr = np.where((g_q75 - g_q25) > 1e-6, g_q75 - g_q25, 1.0)
            X_norm_u = X_norm / b_iqr[None, None, :]

            med_all = np.nanmedian(X_norm_u, axis=0)
            mad_all = np.nanmedian(np.abs(X_norm_u - med_all[None, :, :]), axis=0) * 1.4826
            within_bin_mad = float(np.nanmean(mad_all))

            # Leave-one-out median prediction MAE across normal cycles
            loo_errs = []
            for i in range(len(X_norm_u)):
                keep = np.ones(len(X_norm_u), dtype=bool)
                keep[i] = False
                m_loo = np.nanmedian(X_norm_u[keep], axis=0)
                loo_errs.append(float(np.nanmean(np.abs(X_norm_u[i] - m_loo))))
            loo_mae = float(np.nanmean(loo_errs))

        # 30% observation deletion rank stability
        bl = fit_baseline({"all": X_norm}, X_by_f_arr, min_n=4)
        sc_full = np.array(
            [
                float(np.nanmax(aggregate_band_scores(score_cycle(xc, bl, "all", field_id=int(f)))))
                for xc, f in zip(X_ax, field_ids)
            ]
        )
        drop_rhos = []
        for _ in range(5):
            X_drop = X_ax.copy()
            drop_m = rng.random(X_drop.shape[:2]) < 0.30
            X_drop[drop_m, :] = np.nan
            sc_d = np.array(
                [
                    float(
                        np.nan_to_num(
                            np.nanmax(aggregate_band_scores(score_cycle(xc, bl, "all", field_id=int(f)))),
                            nan=0.0,
                        )
                    )
                    for xc, f in zip(X_drop, field_ids)
                ]
            )
            rho, _ = spearman_correlation(sc_full, sc_d)
            if np.isfinite(rho):
                drop_rhos.append(rho)

        results[axis_name] = {
            "within_bin_normalized_mad": within_bin_mad,
            "loo_median_mae": loo_mae,
            "dropout_30pct_spearman_stability": float(np.mean(drop_rhos)) if drop_rhos else np.nan,
        }
    return results


def evaluate_e_norm_trimming_stability(
    X_b1: np.ndarray,
    field_ids: np.ndarray,
    q_values: tuple[float, ...] = (0.0, 0.10, 0.15, 0.20, 0.30),
) -> dict[str, float]:
    """E-NORM: Spearman rank correlation of cycle anomaly scores across trimming ``q``."""
    X_by_f: dict[int, list[np.ndarray]] = {}
    for row, f in zip(X_b1, field_ids):
        X_by_f.setdefault(int(f), []).append(row)
    X_by_f_arr = {f: np.stack(v, axis=0) for f, v in X_by_f.items()}

    scores_by_q: dict[float, np.ndarray] = {}
    for q in q_values:
        if q <= 0.0:
            act = np.ones(len(X_b1), dtype=bool)
        else:
            act = trimmed_normal_cycles(
                {"all": X_b1},
                strata_per_cycle={"all": np.ones(len(X_b1), dtype=bool)},
                X_by_field=X_by_f_arr,
                min_n=4,
                q=float(q),
                iters=3,
            )["all"]
        bl = fit_baseline({"all": X_b1[act]}, X_by_f_arr, min_n=4)
        sc = []
        for xc, f in zip(X_b1, field_ids):
            s = aggregate_band_scores(score_cycle(xc, bl, "all", field_id=int(f)))
            fin = np.sort(s[np.isfinite(s)])
            sc.append(float(np.mean(fin[-min(3, fin.size) :])) if fin.size else 0.0)
        scores_by_q[q] = np.array(sc, dtype=np.float64)

    ref = scores_by_q[0.15]
    return {
        f"q_{q:.2f}_vs_0.15_spearman": spearman_correlation(ref, scores_by_q[q])[0]
        for q in q_values
    }


def run_cloud_completeness_benchmark(
    X_all: np.ndarray,
    y_true: np.ndarray,
    *,
    epochs: int = 22,
    seeds: tuple[int, ...] = (42, 43, 44),
) -> dict:
    """Sweep completeness from 100% (~10d) to 35% (~monthly) comparing date/Δt SSL vs unconditioned SSL."""
    norm_mask = y_true == 0
    X_tr = X_all[norm_mask][:260]
    n_bands = X_all.shape[-1]
    K = X_all.shape[1]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        med = np.nanmedian(X_tr, axis=(0, 1))
        mad = np.nanmedian(np.abs(X_tr - med[None, None, :]), axis=(0, 1)) * 1.4826
    med = np.where(np.isfinite(med), med, 0.0)
    scale = np.where(np.isfinite(mad) & (mad > 1e-4), mad, 1.0)

    bl = fit_baseline({"all": X_tr}, {}, min_n=5)

    out_by_comp: dict[str, dict] = {}
    models_cache: list[tuple[nn.Module, nn.Module]] = []
    for seed in seeds:
        tr_cond = prepare_conditioned_tokens(X_tr, med, scale, include_date_dt=True)
        tr_uncond = prepare_conditioned_tokens(X_tr, med, scale, include_date_dt=False)
        m_cond = train_irregular_ssl(tr_cond, n_bands, include_date_dt=True, epochs=epochs, seed=seed)
        m_uncond = train_irregular_ssl(tr_uncond, n_bands, include_date_dt=False, epochs=epochs, seed=seed)
        models_cache.append((m_cond, m_uncond))

    ev_full_cond = prepare_conditioned_tokens(X_all, med, scale, include_date_dt=True)

    for comp in COMPLETENESS_LEVELS:
        cond_prs, uncond_prs, b1_prs = [], [], []
        cond_r10, uncond_r10, b1_r10 = [], [], []

        for si, seed in enumerate(seeds):
            rng = np.random.default_rng(seed + int(comp * 1000))
            m_cond, m_uncond = models_cache[si]

            sub_cond, sub_uncond = [], []
            X_b1_sub = np.full_like(X_all, np.nan)
            for i, seq in enumerate(ev_full_cond):
                obs_bins = np.where(np.any(np.isfinite(X_all[i]), axis=-1))[0]
                if obs_bins.size < 4:
                    obs_bins = np.arange(seq.shape[0])
                sub, rel_idx = subsample_cloud_completeness(seq, comp, rng)
                kept_bins = obs_bins[rel_idx]
                sub_cond.append(recompute_dt_after_subsample(sub, include_date_dt=True))
                sub_uncond.append(recompute_dt_after_subsample(sub, include_date_dt=False))
                X_b1_sub[i, kept_bins] = X_all[i, kept_bins]

            sc_c = score_irregular_ssl_batch(m_cond, sub_cond, n_bands)
            sc_u = score_irregular_ssl_batch(m_uncond, sub_uncond, n_bands)
            sc_b1 = np.zeros(len(X_all), dtype=np.float64)
            for i in range(len(X_all)):
                s_bin = aggregate_band_scores(score_cycle(X_b1_sub[i], bl, "all"))
                fin = np.sort(s_bin[np.isfinite(s_bin)])
                sc_b1[i] = float(np.mean(fin[-min(3, fin.size) :])) if fin.size else 0.0

            cond_prs.append(float(average_precision_score(y_true, sc_c)))
            uncond_prs.append(float(average_precision_score(y_true, sc_u)))
            b1_prs.append(float(average_precision_score(y_true, sc_b1)))
            cond_r10.append(recall_at_alert_budget(y_true, sc_c, 0.10))
            uncond_r10.append(recall_at_alert_budget(y_true, sc_u, 0.10))
            b1_r10.append(recall_at_alert_budget(y_true, sc_b1, 0.10))

        key = f"completeness_{int(comp*100)}pct"
        out_by_comp[key] = {
            "completeness": comp,
            "approx_cadence_days": round(12.0 / comp, 1),
            "ssl_with_date_dt_auc_pr": float(np.mean(cond_prs)),
            "ssl_without_date_dt_auc_pr": float(np.mean(uncond_prs)),
            "delta_date_dt_gain": float(np.mean(cond_prs) - np.mean(uncond_prs)),
            "b1_phase_zscore_auc_pr": float(np.mean(b1_prs)),
            "ssl_with_date_dt_recall_10pct": float(np.mean(cond_r10)),
            "ssl_without_date_dt_recall_10pct": float(np.mean(uncond_r10)),
            "b1_recall_10pct": float(np.mean(b1_r10)),
        }
    return out_by_comp
