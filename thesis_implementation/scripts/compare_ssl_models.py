#!/usr/bin/env python3
"""Head-to-head comparison of SSL architectures: M-A (GRU-AE) vs M-B (Masked Transformer).

Trains both ``GRUAutoencoder`` and ``MaskedTransformer`` across 5 random seeds on
the real 32-farm subset cycles and compares:
  - Trainable parameter count and CPU training wall-clock time
  - Held-out farm validation masked spectral reconstruction loss (Huber)
  - Synthetic stress detection (AUC-PR & AUC-ROC across 4 stress types) via:
      (a) sliding-block masked reconstruction error,
      (b) kNN cycle embedding distance, and
      (c) rank-averaged combined SSL score
  - Spearman rank correlation with independent METRIC CWSI water-stress proxy
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
import xarray as xr
from scipy.stats import rankdata, spearmanr
from sklearn.metrics import average_precision_score, roc_auc_score
from torch.utils.data import DataLoader

from ssl_anomaly.config import default_config
from ssl_anomaly.eval.stats import bootstrap_ci
from ssl_anomaly.models.gru_ae import GRUAutoencoder
from ssl_anomaly.models.masked_tf import MaskedTransformer
from ssl_anomaly.train.data import CycleDataset, CycleRecord, cycle_collate
from ssl_anomaly.utils.logging import get_logger
from ssl_anomaly.utils.seeds import seed_everything
from ssl_anomaly.utils.throttle import limit_threads

log = get_logger("ssl_anomaly.scripts.compare_ssl")

PERTURB_KINDS = ("ndvi_drop", "lst_spike", "phase_shift", "early_senescence")


def _load_records_and_cwsi(zarr_p: Path, cyc_p: Path):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from train_ssl import build_ssl_records

    records, tok, bands = build_ssl_records(zarr_p, cyc_p)
    ds = xr.open_zarr(zarr_p)
    times = ds.coords["time"].values
    epoch = times[0]
    fields = ds.coords["field"].values
    cwsi_da = ds["cwsi_et"].values
    cycles_df = pd.read_parquet(cyc_p)

    cwsi_by_key: dict[tuple[int, int], float] = {}
    for _, row in cycles_df.iterrows():
        if row["censored"]:
            continue
        fid = int(row["field"])
        fi = int(np.where(fields == fid)[0][0])
        t0 = epoch + np.timedelta64(int(row["t_start"]), "D")
        t1 = epoch + np.timedelta64(int(row["t_end"]), "D")
        m = (times >= t0) & (times < t1)
        sub = cwsi_da[fi, m]
        cwsi_by_key[(fid, int(row["cycle_id"]))] = (
            float(np.nanmean(sub)) if np.any(np.isfinite(sub)) else np.nan
        )

    cwsi_arr = np.array(
        [cwsi_by_key.get((r.field_id, r.cycle_id), np.nan) for r in records],
        dtype=np.float64,
    )
    return records, tok, bands, cwsi_arr


def _build_model(arch: str, d_in: int, cfg) -> torch.nn.Module:
    if arch == "gru_ae":
        return GRUAutoencoder(
            d_in=d_in,
            d_model=cfg.ssl.gru_ae.d_model,
            n_layers=cfg.ssl.gru_ae.n_layers,
            dropout=cfg.ssl.gru_ae.dropout,
            bidirectional_enc=cfg.ssl.gru_ae.bidirectional_enc,
        )
    if arch == "transformer":
        return MaskedTransformer(
            d_in=d_in,
            d_model=cfg.ssl.transformer.d_model,
            n_heads=cfg.ssl.transformer.n_heads,
            n_layers=cfg.ssl.transformer.n_layers,
            d_ff=cfg.ssl.transformer.d_ff,
            dropout=cfg.ssl.transformer.dropout,
            max_len=cfg.ssl.transformer.max_len,
            pos_encoding=cfg.ssl.transformer.pos_encoding,
        )
    raise ValueError(f"Unknown arch={arch!r}")


def _forward_model(
    model: torch.nn.Module,
    tokens: torch.Tensor,
    mask: torch.Tensor | None,
    pamask: torch.Tensor | None,
    lengths: torch.Tensor | None,
) -> tuple[torch.Tensor, torch.Tensor]:
    if isinstance(model, GRUAutoencoder):
        return model(tokens, lengths=lengths)
    return model(tokens, mask=mask, key_padding_mask=pamask)


def _train_single_model(
    arch: str,
    train_recs: list[CycleRecord],
    d_in: int,
    n_bands: int,
    *,
    epochs: int,
    lr: float,
    seed: int,
) -> tuple[torch.nn.Module, float]:
    seed_everything(seed)
    cfg = default_config()
    model = _build_model(arch, d_in, cfg)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    ds = CycleDataset(train_recs)

    def collate(b):
        return cycle_collate(b, mask_ratio=0.25, mask_block_max=3, mask_block_p=0.35)

    dl = DataLoader(ds, batch_size=16, shuffle=True, collate_fn=collate, num_workers=0)

    t0 = time.perf_counter()
    model.train()
    for _ in range(epochs):
        for batch in dl:
            x_in = batch["original"].clone()
            m = batch["mask"]
            # Zero spectral channels on masked positions while preserving temporal coordinates
            x_in_bands = x_in[:, :, :n_bands].clone()
            x_in_bands[m] = 0.0
            x_in[:, :, :n_bands] = x_in_bands

            recon, _ = _forward_model(
                model, x_in, mask=m, pamask=batch["pamask"], lengths=batch["lengths"]
            )
            tok_err = F.smooth_l1_loss(
                recon[:, :, :n_bands], batch["original"][:, :, :n_bands], reduction="none", beta=1.0
            ).mean(dim=-1)
            loss = (tok_err * m.float()).sum() / m.float().sum().clamp(min=1.0)
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()

    elapsed = time.perf_counter() - t0
    model.eval()
    return model, elapsed


@torch.no_grad()
def _sliding_masked_recon_score(
    model: torch.nn.Module,
    tok_arr: np.ndarray,
    n_bands: int,
    block_size: int = 3,
) -> tuple[float, float]:
    """Return ``(mean_band_huber, top3_tok_rms)`` via deterministic sliding block masks."""
    T, d = tok_arr.shape
    orig = torch.from_numpy(tok_arr).unsqueeze(0)  # (1, T, d)
    lengths = torch.tensor([T], dtype=torch.long)
    pamask = torch.zeros((1, T), dtype=torch.bool)

    tok_huber = np.zeros(T, dtype=np.float64)
    tok_rms = np.zeros(T, dtype=np.float64)
    for start in range(0, T, block_size):
        end = min(T, start + block_size)
        m = torch.zeros((1, T), dtype=torch.bool)
        m[0, start:end] = True
        x_in = orig.clone()
        x_in[0, start:end, :n_bands] = 0.0
        recon, _ = _forward_model(model, x_in, mask=m, pamask=pamask, lengths=lengths)
        diff = recon[0, start:end, :n_bands] - orig[0, start:end, :n_bands]
        hub = F.smooth_l1_loss(
            recon[0, start:end, :n_bands], orig[0, start:end, :n_bands], reduction="none", beta=1.0
        ).mean(dim=-1)
        rms = torch.sqrt((diff**2).mean(dim=-1))
        tok_huber[start:end] = hub.numpy()
        tok_rms[start:end] = rms.numpy()

    sorted_rms = np.sort(tok_rms)
    top3 = float(np.mean(sorted_rms[-min(3, T) :]))
    return float(np.mean(tok_huber)), top3


@torch.no_grad()
def _embed_cycle(model: torch.nn.Module, tok_arr: np.ndarray) -> np.ndarray:
    T = tok_arr.shape[0]
    x = torch.from_numpy(tok_arr).unsqueeze(0)
    lengths = torch.tensor([T], dtype=torch.long)
    pamask = torch.zeros((1, T), dtype=torch.bool)
    _, emb = _forward_model(model, x, mask=None, pamask=pamask, lengths=lengths)
    return emb[0].numpy()


def _knn_distance(emb: np.ndarray, ref_embs: np.ndarray, k: int = 5) -> float:
    dists = np.linalg.norm(ref_embs - emb[None, :], axis=1)
    dists_s = np.sort(dists)
    # Exclude exact self-match (~0) if scoring training record
    nonzero = dists_s[dists_s > 1e-6]
    use = nonzero if nonzero.size >= k else dists_s
    return float(np.mean(use[: min(k, use.size)]))


def _perturb_standardized_tokens(
    tok_arr: np.ndarray,
    bands: list[str],
    kind: str,
    rng: np.random.Generator,
) -> np.ndarray:
    """Inject standardized-space anomaly (~2.5-3.5 MAD units) into spectral channels."""
    out = tok_arr.copy()
    T = out.shape[0]
    bmap = {b: i for i, b in enumerate(bands)}
    r_i = bmap["SR_B4"]
    n_i = bmap["SR_B5"]
    nd_i = bmap["NDVI"]
    lst_i = bmap["ST_B10"]

    if kind == "ndvi_drop":
        L = min(4, max(2, T // 5))
        s = int(rng.integers(1, max(2, T - L)))
        out[s : s + L, n_i] -= 2.8
        out[s : s + L, nd_i] -= 3.0
        out[s : s + L, r_i] += 2.0
    elif kind == "lst_spike":
        L = min(4, max(2, T // 5))
        s = int(rng.integers(1, max(2, T - L)))
        out[s : s + L, lst_i] += 3.2
    elif kind == "phase_shift":
        shift = max(2, T // 5)
        out[:, : len(bands)] = np.roll(out[:, : len(bands)], shift=shift, axis=0)
    elif kind == "early_senescence":
        s = int(0.65 * T)
        ramp = np.linspace(0.5, 3.0, max(1, T - s), dtype=np.float32)
        out[s:, n_i] -= ramp
        out[s:, nd_i] -= ramp
    else:
        raise ValueError(kind)
    return out


def _rank_combine(s1: np.ndarray, s2: np.ndarray) -> np.ndarray:
    n = max(1, len(s1))
    return 0.5 * (rankdata(s1) / n + rankdata(s2) / n)


def run_ssl_comparison(
    zarr_p: Path = Path("data/processed/fields.zarr"),
    cyc_p: Path = Path("data/processed/cycles.parquet"),
    *,
    epochs: int = 45,
    lr: float = 1e-3,
    seeds: tuple[int, ...] = (42, 43, 44, 45, 46),
) -> dict:
    records, tok, bands, cwsi_arr = _load_records_and_cwsi(zarr_p, cyc_p)
    n_bands = len(bands)
    d_in = tok.d_feature
    train_recs = [r for r in records if not r.is_validation]
    val_recs = [r for r in records if r.is_validation]

    cfg = default_config()
    out_models: dict[str, dict] = {}

    for arch in ("gru_ae", "transformer"):
        probe = _build_model(arch, d_in, cfg)
        n_params = int(sum(p.numel() for p in probe.parameters() if p.requires_grad))

        val_losses: list[float] = []
        train_times: list[float] = []
        recon_prs: list[float] = []
        knn_prs: list[float] = []
        comb_prs: list[float] = []
        comb_rocs: list[float] = []
        per_kind_pr: dict[str, list[float]] = {k: [] for k in PERTURB_KINDS}
        real_scores_seeds: list[np.ndarray] = []

        for seed in seeds:
            model, elapsed = _train_single_model(
                arch, train_recs, d_in, n_bands, epochs=epochs, lr=lr, seed=seed
            )
            train_times.append(elapsed)

            # Validation masked reconstruction loss on held-out farms
            v_hubs = [_sliding_masked_recon_score(model, r.tokens, n_bands)[0] for r in val_recs]
            val_losses.append(float(np.mean(v_hubs)))

            ref_embs = np.stack([_embed_cycle(model, r.tokens) for r in train_recs], axis=0)

            # Real cycle scores for CWSI correlation
            r_rec_s = np.array(
                [_sliding_masked_recon_score(model, r.tokens, n_bands)[1] for r in records]
            )
            r_knn_s = np.array(
                [_knn_distance(_embed_cycle(model, r.tokens), ref_embs) for r in records]
            )
            real_scores_seeds.append(_rank_combine(r_rec_s, r_knn_s))

            # Synthetic injection across all records
            rng = np.random.default_rng(seed + 100)
            seed_r_pr, seed_k_pr, seed_c_pr, seed_c_roc = [], [], [], []
            for kind in PERTURB_KINDS:
                pert_toks = [_perturb_standardized_tokens(r.tokens, bands, kind, rng) for r in records]
                all_toks = [r.tokens for r in records] + pert_toks
                y_true = np.array([0] * len(records) + [1] * len(records), dtype=np.int32)

                s_rec = np.array(
                    [_sliding_masked_recon_score(model, t, n_bands)[1] for t in all_toks]
                )
                s_knn = np.array(
                    [_knn_distance(_embed_cycle(model, t), ref_embs) for t in all_toks]
                )
                s_comb = _rank_combine(s_rec, s_knn)

                ap_r = float(average_precision_score(y_true, s_rec))
                ap_k = float(average_precision_score(y_true, s_knn))
                ap_c = float(average_precision_score(y_true, s_comb))
                roc_c = float(roc_auc_score(y_true, s_comb))

                seed_r_pr.append(ap_r)
                seed_k_pr.append(ap_k)
                seed_c_pr.append(ap_c)
                seed_c_roc.append(roc_c)
                per_kind_pr[kind].append(ap_c)

            recon_prs.append(float(np.mean(seed_r_pr)))
            knn_prs.append(float(np.mean(seed_k_pr)))
            comb_prs.append(float(np.mean(seed_c_pr)))
            comb_rocs.append(float(np.mean(seed_c_roc)))

        mean_real = np.mean(real_scores_seeds, axis=0)
        ok_cw = np.isfinite(cwsi_arr) & np.isfinite(mean_real)
        rho, pval = spearmanr(mean_real[ok_cw], cwsi_arr[ok_cw])

        vl_m, vl_lo, vl_hi = bootstrap_ci(np.mean, np.array(val_losses), n_boot=1000, seed=42)
        cp_m, cp_lo, cp_hi = bootstrap_ci(np.mean, np.array(comb_prs), n_boot=1000, seed=42)
        cr_m, cr_lo, cr_hi = bootstrap_ci(np.mean, np.array(comb_rocs), n_boot=1000, seed=42)

        out_models[arch] = {
            "n_parameters": n_params,
            "mean_train_seconds": float(np.mean(train_times)),
            "val_band_huber_loss": vl_m,
            "val_band_huber_ci_95": [vl_lo, vl_hi],
            "recon_only_auc_pr": float(np.mean(recon_prs)),
            "embed_knn_only_auc_pr": float(np.mean(knn_prs)),
            "combined_auc_pr": cp_m,
            "combined_auc_pr_ci_95": [cp_lo, cp_hi],
            "combined_auc_roc": cr_m,
            "combined_auc_roc_ci_95": [cr_lo, cr_hi],
            "per_perturbation_auc_pr": {k: float(np.mean(per_kind_pr[k])) for k in PERTURB_KINDS},
            "cwsi_spearman_rho": float(rho),
            "cwsi_spearman_pval": float(pval),
        }

    return {
        "n_cycles_total": len(records),
        "n_train_cycles": len(train_recs),
        "n_val_cycles": len(val_recs),
        "d_in": d_in,
        "n_bands": n_bands,
        "epochs": epochs,
        "seeds": list(seeds),
        "models": out_models,
    }


def main() -> int:
    limit_threads(2)
    ap = argparse.ArgumentParser(description="Compare GRU-AE (M-A) vs Masked Transformer (M-B).")
    ap.add_argument("--zarr", default="data/processed/fields.zarr", type=Path)
    ap.add_argument("--cycles", default="data/processed/cycles.parquet", type=Path)
    ap.add_argument("--epochs", default=45, type=int)
    ap.add_argument("--lr", default=1e-3, type=float)
    ap.add_argument("--seeds", default="42,43,44,45,46", type=str)
    ap.add_argument("--out", default="reports/ssl_comparison.json", type=Path)
    args = ap.parse_args()

    seeds = tuple(int(s.strip()) for s in args.seeds.split(",") if s.strip())
    report = run_ssl_comparison(args.zarr, args.cycles, epochs=args.epochs, lr=args.lr, seeds=seeds)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))

    rows = []
    for arch, m in report["models"].items():
        rows.append(
            {
                "model": arch,
                "n_parameters": m["n_parameters"],
                "mean_train_seconds": m["mean_train_seconds"],
                "val_band_huber_loss": m["val_band_huber_loss"],
                "recon_only_auc_pr": m["recon_only_auc_pr"],
                "embed_knn_only_auc_pr": m["embed_knn_only_auc_pr"],
                "combined_auc_pr": m["combined_auc_pr"],
                "combined_auc_roc": m["combined_auc_roc"],
                "ndvi_drop_pr": m["per_perturbation_auc_pr"]["ndvi_drop"],
                "lst_spike_pr": m["per_perturbation_auc_pr"]["lst_spike"],
                "phase_shift_pr": m["per_perturbation_auc_pr"]["phase_shift"],
                "early_senescence_pr": m["per_perturbation_auc_pr"]["early_senescence"],
                "cwsi_spearman_rho": m["cwsi_spearman_rho"],
                "cwsi_pval": m["cwsi_spearman_pval"],
            }
        )
    csv_path = args.out.with_suffix(".csv")
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)

    log.info("Wrote SSL comparison to %s and %s", args.out, csv_path)
    print("\n=== SSL Architecture Comparison: M-A (GRU-AE) vs M-B (Transformer) ===")
    print(df.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
