#!/usr/bin/env python3
"""Train the causal monitor models (design D8, tasks §5, §5b, §10).

Examples
--------
Smoke (agent-only, <2 min)::

    python scripts/train_main.py --model masked_transformer --smoke

Full single seed::

    python scripts/train_main.py --model masked_transformer --seed 13

What it does
------------
- Loads the locked splits (hash-verified) and slices train+dev only.
- Asserts the frozen holdout manifest (hash-verified) before the first batch:
  no holdout farm or holdout-period cycle may reach training — fail-closed
  (change training-holdout-invariant; manifest sha recorded in the run
  manifest).
- Fits train-only robust normalization (per band × phase bin).
- Trains the causal model with masked reconstruction of observed bins
  (no injected-anomaly pretext), early stopping on dev masked reconstruction
  loss (never on the perturbation metric; forbidden-target rule).
- Gradient clipping + NaN/Inf guard (fail loudly); deterministic seeding;
  progress bar + progress.jsonl; --resume; run_manifest.json.
- Saves checkpoints/dev/<run_id>/<model>_seed<seed>.pt (+ optimizer state)
  and the fitted normalization sidecar next to it.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import holdout as mholdout  # noqa: E402
from ssl_anomaly.monitor import inputs as minputs  # noqa: E402
from ssl_anomaly.monitor import models as mmodels  # noqa: E402
from ssl_anomaly.monitor import protocol as mproto  # noqa: E402
from ssl_anomaly.monitor import splits as msplits  # noqa: E402

SEEDS_DEFAULT = (13, 42, 2026)

# Pre-registered gru_pred objective (change predictive-ssl-controlled-trial,
# task 1.1): the loss choice is recorded BEFORE training — no post-hoc
# switching. Huber/Smooth-L1 with beta=1.0: the SAME loss family and beta as
# gru_ae_main's masked reconstruction loss, so the controlled trial changes
# ONE thing (what is predicted) and not two (also the loss shape).
PREDICTIVE_OBJECTIVE = {
    "objective": "one_step_ahead",
    "loss": "smooth_l1_beta1.0",
    "loss_rationale": ("same family and beta as gru_ae_main's masked "
                       "reconstruction loss; MSE vs Huber decided BEFORE "
                       "training (design: no post-hoc switching)"),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True, choices=["masked_transformer", "gru_ae", "gru_pred", "b1"])
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--epochs", type=int, default=60)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--mask-ratio", type=float, default=0.3, help="fraction of observed bins withheld per sample")
    p.add_argument("--no-doy", action="store_true", help="ablation: drop the sin/cos DOY channels (task 2.4)")
    p.add_argument("--no-lst", action="store_true", help="ablation: drop the LST channel (design D3 no-LST variant)")
    p.add_argument("--smoke", action="store_true", help="1 epoch, 16 cycles, <2 min (agent-only runs)")
    p.add_argument("--resume", action="store_true", help="resume from the last saved checkpoint")
    p.add_argument("--run-id", default=None, help="run id (default: <model>_s<seed>_<date>)")
    p.add_argument("--patience", type=int, default=8, help="early-stopping patience (epochs)")
    p.add_argument("--device", default=None, help="cpu | cuda (default: auto)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    t_start = time.time()

    seeds = [args.seed]
    if args.smoke:
        args.epochs = 1
    run_id = args.run_id or f"{args.model}_s{args.seed}_{time.strftime('%Y%m%d')}"
    run_dir = mproto.DEV_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ckpt_dir = mproto.CHECKPOINTS_DEV_DIR / run_id
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    device = args.device or ("cuda" if _cuda_available() else "cpu")

    # ---- Protocol: locked splits + masked tensors (train+dev only) --------
    manifest = msplits.load_splits_locked()
    data = minputs.load_masked_cycles()
    sel = mproto.select_splits(data, manifest, splits=("train", "dev"))

    # ---- Standing holdout invariant (training-holdout-invariant) ----------
    # Fail-closed: the frozen manifest is hash-verified and every cycle about to
    # be seen by this training path is checked against it BEFORE the first
    # batch. A violation aborts training with the offending (field, cycle)
    # pairs named; it is never a warning.
    holdout_manifest = mholdout.load_holdout_manifest()
    mholdout.assert_frozen_holdout_matches_splits(holdout_manifest, manifest)
    # Masked-cycle metadata stores the exclusive parquet t_end.
    end_days = pd.to_datetime(list(sel["end_dates"]), format="mixed", errors="coerce")
    last_data_days = end_days - pd.Timedelta(days=1)
    mholdout.assert_train_only(
        [int(f) for f in sel["field_ids"]],
        list(sel["cycle_keys"]),
        [str(d) for d in sel["start_dates"]],
        cycle_end_dates=last_data_days,
        manifest=holdout_manifest,
        context=f"train_main.py(model={args.model}, seed={args.seed})",
    )
    n_holdout_farms = len({int(f) for f in sel["field_ids"]}
                         & set(holdout_manifest["holdout_farms"]))
    print(f"[holdout] manifest {holdout_manifest['manifest_sha256'][:12]}… verified; "
          f"0 holdout farms / cycles in the training inputs")

    is_train = np.array([k in set(manifest["cycles"]["train"]) for k in sel["cycle_keys"]])
    X_all, M_all = sel["X"], sel["M"]  # raw values + observation masks
    if args.no_lst:
        # D3 no-LST variant: drop the last channel (order ndvi…swir2, lst).
        X_all, M_all = X_all[:, :, :-1], M_all[:, :, :-1]
        sel = dict(sel)
        sel["X"], sel["M"] = X_all, M_all
        sel["band_names"] = list(sel["band_names"])[:-1]
    if args.smoke:
        # Spec: --smoke = 1 epoch on 16 train cycles, < 2 min. Keep a few dev
        # cycles so the dev-loss path is exercised too.
        idx_train = np.where(is_train)[0][:16]
        idx_dev = np.where(~is_train)[0][:4]
        keep_idx = np.concatenate([idx_train, idx_dev])
        keep = np.zeros(len(sel["cycle_keys"]), dtype=bool)
        keep[keep_idx] = True
        for k, v in list(sel.items()):
            if isinstance(v, np.ndarray) and len(v) == len(keep):
                sel[k] = v[keep]
        sel["cycle_keys"] = [sel["cycle_keys"][i] for i in keep_idx]
        is_train = np.isin(np.arange(len(keep_idx)), np.arange(len(idx_train)))
        X_all, M_all = sel["X"], sel["M"]
    n_train = int(is_train.sum())
    n_dev = int(len(sel["cycle_keys"]) - n_train)
    print(f"[protocol] train cycles={n_train}, dev cycles={n_dev}, device={device}")

    # ---- Train-only robust normalization ----------------------------------
    stats = minputs.fit_robust_norm(X_all[is_train], M_all[is_train])
    norm_path = run_dir / "norm_stats.npz"
    minputs.save_norm(stats, norm_path, meta={
        "run_id": run_id, "model_id": args.model, "seed": args.seed,
        "n_train_cycles": n_train, "splits_locked_sha256": manifest["manifest_sha256"],
        "holdout_manifest_sha256": holdout_manifest["manifest_sha256"],
        "n_holdout_farms": n_holdout_farms,
    })

    z_all = minputs.apply_norm(stats, X_all, M_all)
    doy_all = minputs.doy_channels(sel["harvest_days"])

    use_doy = not args.no_doy
    d_in = mmodels.token_dim(X_all.shape[2], use_doy)
    n_out = X_all.shape[2]

    # ---- B1: no gradient training; fit + save and exit --------------------
    if args.model == "b1":
        b1 = mmodels.B1PhaseZCausal(use_doy=True, min_n=8)
        b1.fit(X_all[is_train], M_all[is_train], doy_all[is_train, :, 0])
        np.savez_compressed(
            ckpt_dir / f"b1_phasez_causal_seed{args.seed}.npz",
            median=b1.median, scale=b1.scale, robust_range=b1.robust_range,
            use_doy=np.array(b1.use_doy),
            band_names=np.array(["ndvi", "blue", "green", "red", "nir", "swir1", "swir2", "lst"], dtype=object),
        )
        wall = time.time() - t_start
        _write_manifest(run_dir, args, seeds, wall, device, {}, n_train, n_dev, manifest, params=0)
        print(f"[b1] fitted train statistics in {wall:.1f}s → {ckpt_dir}")
        return 0

    # ---- Torch setup -------------------------------------------------------
    import torch

    flags = mproto.seed_everything(args.seed)
    torch.set_num_threads(max(1, _cpu_threads()))

    cfg = dict(mmodels.DEFAULT_CONFIGS[args.model])
    model = mmodels.build_model(args.model, d_in=d_in, n_out=n_out, cfg=cfg)
    params = mmodels.count_parameters(model)
    if params > 500_000:
        raise ValueError(f"{args.model} has {params} parameters (>500k cap)")
    scorer_cls = mmodels.DeepPredictiveScorer if args.model == "gru_pred" else mmodels.DeepCausalScorer
    scorer = scorer_cls(args.model, model, use_doy=use_doy, device=device)
    print(f"[model] {args.model} params={params:,} d_in={d_in} doy={use_doy}"
          + (f" objective={PREDICTIVE_OBJECTIVE['objective']} loss={PREDICTIVE_OBJECTIVE['loss']}"
             if args.model == "gru_pred" else ""))

    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    ckpt_path = ckpt_dir / f"{args.model}_seed{args.seed}.pt"

    start_epoch = 0
    best_dev = float("inf")
    best_state = None
    if args.resume and ckpt_path.exists():
        payload = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(payload["state_dict"])
        if "optimizer" in payload:
            opt.load_state_dict(payload["optimizer"])
        start_epoch = int(payload.get("epoch", 0))
        best_dev = float(payload.get("best_dev_loss", float("inf")))
        print(f"[resume] from epoch {start_epoch} (best dev loss {best_dev:.4f})")

    # ---- Data tensors ------------------------------------------------------
    Xtr = torch.from_numpy(z_all[is_train]).float()
    Mtr = torch.from_numpy(M_all[is_train]).float()
    Dtr = torch.from_numpy(doy_all[is_train]).float() if use_doy else None
    key_pad_tr = torch.from_numpy(~M_all[is_train].any(axis=-1)).bool()

    Xdev_t = torch.from_numpy(z_all[~is_train]).float()
    Mdev_t = torch.from_numpy(M_all[~is_train]).float()
    Ddev_t = torch.from_numpy(doy_all[~is_train]).float() if use_doy else None
    key_pad_dev = torch.from_numpy(~M_all[~is_train].any(axis=-1)).bool()

    # Dev pretext masks: fixed per cycle for stable early stopping
    # (derived deterministically from [seed, cycle index]; resume-safe).
    dev_pretext = _fixed_pretext(M_all[~is_train], args.seed, args.mask_ratio)

    progress_path = run_dir / "progress.jsonl"
    if not args.resume or not progress_path.exists():
        progress_path.write_text("", encoding="utf-8")

    C = n_out
    rng = np.random.default_rng(args.seed * 1_000_003 + 17)
    order = np.arange(n_train)
    patience_left = args.patience
    history: list[dict] = []

    for epoch in range(start_epoch, args.epochs):
        t_ep = time.time()
        rng.shuffle(order)
        model.train()
        losses: list[float] = []
        for b0 in range(0, n_train, args.batch_size):
            idx = order[b0:b0 + args.batch_size]
            if len(idx) == 0:
                continue
            x = Xtr[idx]
            m = Mtr[idx]
            d = Dtr[idx] if Dtr is not None else None
            if args.model == "gru_pred":
                # One-step-ahead objective (pre-registered): NO pretext
                # masking — the prediction at bin o is head(h_{o-1}), a
                # function of tokens < o only, so there is no trivial identity
                # to prevent. Masked smooth-L1 over observed (bin, channel)
                # pairs; the loss choice was recorded before training.
                tokens = torch.from_numpy(mmodels.build_tokens(
                    x.numpy(), m.numpy(),
                    d.numpy() if d is not None else None,
                )).float()
                loss = scorer.predictive_losses(tokens, x, m.bool(), nonfinite_guard=True)
            else:
                pretext_np = _sample_pretext(M_all[is_train][idx], args.mask_ratio, rng)
                pretext = torch.from_numpy(pretext_np)
                tokens_np = mmodels.build_tokens(
                    x.numpy(), m.numpy(),
                    d.numpy() if d is not None else None,
                )
                # Withheld bins: value channels zeroed in the input (GRU) or
                # replaced by the mask embedding inside the model (transformer).
                tokens_np = tokens_np.copy()
                tokens_np[pretext_np, :C] = 0.0
                tokens = torch.from_numpy(tokens_np).float()
                target = x
                channel_mask = m.bool()
                if args.model == "masked_transformer":
                    kp = key_pad_tr[idx]
                    loss = scorer.recon_losses(tokens, pretext, target, channel_mask, key_padding=kp)
                else:
                    loss = scorer.recon_losses(tokens, pretext, target, channel_mask)
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            if not torch.isfinite(loss):
                raise FloatingPointError(f"Non-finite loss at epoch {epoch} batch {b0}: {loss.item()}")
            for pname, p in model.named_parameters():
                if p.grad is not None and not torch.isfinite(p.grad).all():
                    raise FloatingPointError(f"Non-finite gradient in {pname} at epoch {epoch}")
            opt.step()
            losses.append(float(loss.item()))

        train_loss = float(np.mean(losses)) if losses else float("nan")

        # Dev loss (deterministic): masked reconstruction for the recon arms,
        # the same one-step-ahead masked loss for gru_pred (no pretext, hence
        # deterministic by construction).
        model.eval()
        dev_losses: list[float] = []
        with torch.no_grad():
            for b0 in range(0, n_dev, args.batch_size):
                x = Xdev_t[b0:b0 + args.batch_size]
                m = Mdev_t[b0:b0 + args.batch_size]
                d = Ddev_t[b0:b0 + args.batch_size] if Ddev_t is not None else None
                if args.model == "gru_pred":
                    tokens = torch.from_numpy(mmodels.build_tokens(
                        x.numpy(), m.numpy(), d.numpy() if d is not None else None)).float()
                    vl = float(scorer.predictive_losses(tokens, x, m.bool(), nonfinite_guard=True))
                else:
                    pretext = dev_pretext[b0:b0 + args.batch_size]
                    tokens_np = mmodels.build_tokens(x.numpy(), m.numpy(), d.numpy() if d is not None else None).copy()
                    tokens_np[pretext, :C] = 0.0  # pretext is already a numpy array
                    tokens = torch.from_numpy(tokens_np).float()
                    channel_mask = m.bool()
                    if args.model == "masked_transformer":
                        kp = key_pad_dev[b0:b0 + args.batch_size]
                        vl = scorer.eval_recon_loss(tokens, pretext, x, channel_mask, key_padding=kp)
                    else:
                        vl = scorer.eval_recon_loss(tokens, pretext, x, channel_mask)
                dev_losses.append(vl)
        dev_loss = float(np.mean(dev_losses)) if dev_losses else float("nan")

        eta = time.time() - t_start
        rec = {
            "epoch": epoch + 1, "train_loss": train_loss,
            ("dev_one_step_loss" if args.model == "gru_pred" else "dev_recon_loss"): dev_loss,
            "epoch_s": round(time.time() - t_ep, 2), "wall_s": round(eta, 1),
            "eta_s": round(eta / (epoch + 1 - start_epoch) * max(1, args.epochs - epoch - 1), 1),
        }
        history.append(rec)
        with progress_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(
            f"epoch {epoch + 1}/{args.epochs} | train {train_loss:.4f} | dev {dev_loss:.4f} "
            f"| {rec['epoch_s']}s/ep | ETA {rec['eta_s']}s",
            flush=True,
        )

        if dev_loss < best_dev - 1e-6:
            best_dev = dev_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience_left = args.patience
        else:
            patience_left -= 1
            if patience_left <= 0 and not args.smoke:
                print(f"[early-stop] no dev improvement for {args.patience} epochs")
                break

        torch.save(
            {
                "format": "causal_monitor_v1",
                "model_id": args.model,
                "state_dict": model.state_dict(),
                "optimizer": opt.state_dict(),
                "epoch": epoch + 1,
                "best_dev_loss": best_dev,
                "config": _ckpt_config(args, d_in, n_out, use_doy, cfg),
                "seed": args.seed,
                "mask_ratio": (0.0 if args.model == "gru_pred" else args.mask_ratio),
            },
            ckpt_path,
        )

    if best_state is not None:
        model.load_state_dict(best_state)

    wall = time.time() - t_start
    torch.save(
        {
            "format": "causal_monitor_v1",
            "model_id": args.model,
            "state_dict": model.state_dict(),
            "epoch": history[-1]["epoch"] if history else 0,
            "best_dev_loss": best_dev,
            "config": _ckpt_config(args, d_in, n_out, use_doy, cfg),
            "seed": args.seed,
            "mask_ratio": (0.0 if args.model == "gru_pred" else args.mask_ratio),
        },
        ckpt_path,
    )
    _write_manifest(run_dir, args, seeds, wall, device, flags, n_train, n_dev, manifest, params=params)
    print(f"[done] {args.model} seed {args.seed}: best dev loss {best_dev:.4f}, wall {wall:.1f}s")
    print(f"[done] checkpoint: {ckpt_path}")
    return 0


def _ckpt_config(args, d_in: int, n_out: int, use_doy: bool, cfg: dict) -> dict:
    """Checkpoint config: shared keys + the pre-registered objective block for
    gru_pred (the loss choice travels with the checkpoint — no post-hoc
    switching can be hidden)."""
    out = {"d_in": d_in, "n_out": n_out, "use_doy": use_doy, **cfg}
    if args.model == "gru_pred":
        out.update(PREDICTIVE_OBJECTIVE)
    return out


def _sample_pretext(m: np.ndarray, mask_ratio: float, rng: np.random.Generator) -> np.ndarray:
    """Random pretext mask over OBSERVED bins; unobserved bins never masked."""
    out = np.zeros(m.shape[:2], dtype=bool)
    for i in range(m.shape[0]):
        obs_bins = np.where(m[i].any(axis=-1))[0]
        if obs_bins.size == 0:
            continue
        n_mask = max(1, int(round(mask_ratio * obs_bins.size)))
        sel = rng.choice(obs_bins, size=min(n_mask, obs_bins.size), replace=False)
        out[i, sel] = True
    return out


def _fixed_pretext(m: np.ndarray, seed: int, mask_ratio: float) -> np.ndarray:
    """Deterministic per-cycle pretext mask for dev loss (resume-safe)."""
    out = np.zeros(m.shape[:2], dtype=bool)
    for i in range(m.shape[0]):
        r = np.random.default_rng((seed * 7_919 + i) % (2**32))
        obs_bins = np.where(m[i].any(axis=-1))[0]
        if obs_bins.size == 0:
            continue
        n_mask = max(1, int(round(mask_ratio * obs_bins.size)))
        sel = r.choice(obs_bins, size=min(n_mask, obs_bins.size), replace=False)
        out[i, sel] = True
    return out


def _cuda_available() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def _cpu_threads() -> int:
    import os

    return min(8, os.cpu_count() or 4)


def _write_manifest(
    run_dir: Path, args, seeds: list[int], wall: float, device: str, flags: dict,
    n_train: int, n_dev: int, manifest: dict, *, params: int,
) -> None:
    from ssl_anomaly.monitor.protocol import config_hash

    cfg = {
        "model": args.model, "epochs": args.epochs, "batch_size": args.batch_size,
        "lr": args.lr, "mask_ratio": args.mask_ratio, "use_doy": not args.no_doy,
        "seed": args.seed, "smoke": bool(args.smoke),
    }
    if args.model == "gru_pred":
        cfg["objective"] = PREDICTIVE_OBJECTIVE["objective"]
        cfg["loss"] = PREDICTIVE_OBJECTIVE["loss"]
    payload = {
        "run_id": args.run_id or f"{args.model}_s{args.seed}",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "git_sha": mproto.git_sha(),
        "splits_locked_sha256": manifest["manifest_sha256"],
        "config": cfg,
        "config_hash": config_hash(cfg),
        "seeds": seeds,
        "device": device,
        "wall_time_s": round(wall, 1),
        "n_train_cycles": n_train,
        "n_dev_cycles": n_dev,
        "determinism_flags": flags,
        "parameter_count": params,
        "data_source": "real490 (masked rebuild from stats.zarr)",
    }
    manifest_path = run_dir / "run_manifest.json"
    if manifest_path.exists():
        # One manifest per run_id, shared by its seeds: union the seeds and
        # keep the first creation date (each seed run updates this file).
        try:
            prev = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["seeds"] = sorted(set(prev.get("seeds", [])) | set(seeds))
            payload["created"] = prev.get("created", payload["created"])
            payload["wall_time_s"] = round(float(prev.get("wall_time_s", 0)) + wall, 1)
        except Exception:
            pass
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
