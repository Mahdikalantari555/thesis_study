"""Patch-level training CLI (task 1.4) — the owner runs it, never the agent.

What this script is responsible for, and what it deliberately refuses to do:

* **Estimate before run.** ``--estimate-runtime`` prints per-epoch, per-seed,
  total wall-time and disk BEFORE any gradient step (spec scenario "Owner runs
  training on own hardware").
* **Resume is safe or it fails.** The checkpoint carries model/optimizer/
  scheduler/RNG state plus a config hash; a hash mismatch after any config
  change is a hard error rather than a silently different run.
* **Progress is observable.** ``progress.jsonl`` per epoch and a final
  wall-time summary, so an interrupted job can be diagnosed.
* **The holdout cannot leak.** The Dataset construction path requires the
  frozen manifest and raises without it (``training-holdout-invariant``).
* **Trimmed loss is scheduled.** Top-5 % trimming activates only after a
  warm-up (``--trim-after-epoch``), per the task's "after 10-epoch warm-up".

The §7 report fields (seeds, data_source, split hashes, git sha, device, wall
time) are written into ``run_manifest.json`` next to the checkpoints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
from functools import partial
from pathlib import Path

import numpy as np
import torch

from ssl_anomaly.io import patches as P
from ssl_anomaly.models.patch_cnn_gru import build_patch_model, scorer_id
from ssl_anomaly.monitor import holdout as H
from ssl_anomaly.monitor import splits as S
from ssl_anomaly.train import contamination as CT
from ssl_anomaly.train import patch_data as PD
from ssl_anomaly.train import run_plan as RP

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "checkpoints" / "patch"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):  # pragma: no cover
        return "unknown"


def config_hash(cfg: dict) -> str:
    """Stable hash of everything that changes what the training produces."""
    keys = (
        "arch", "seed", "epochs", "batch_size", "lr", "weight_decay", "d_model",
        "n_horizons", "aux_weight", "horizon_weights", "burn_in_bins",
        "trim_top_frac", "trim_after_epoch", "grad_clip", "max_fields",
        "data_source", "holdout_sha256", "norm_sha256", "covariates", "input_protocol",
        "splits_sha256", "admitted_cycles_sha256", "max_cycles", "contaminate_seed", "smoke",
        # patch-contamination-absorption task 1.2: a resumed run whose
        # contamination configuration changed is a different experiment.
        "contaminate_fraction", "trimmed_loss", "curation",
    )
    payload = {k: cfg.get(k) for k in keys}
    blob = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def pick_device(requested: str = "auto") -> str:
    if requested != "auto":
        return requested
    return "cuda" if torch.cuda.is_available() else "cpu"


def _rng_state(state: dict) -> dict:
    out = {
        "torch": torch.get_rng_state(),
        "numpy": np.random.get_state(),
    }
    if torch.cuda.is_available():
        out["cuda"] = torch.cuda.get_rng_state_all()
    return out


def _restore_rng(state: dict) -> None:
    torch.set_rng_state(state["torch"])
    np.random.set_state(state["numpy"])
    if "cuda" in state and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(state["cuda"])


def save_checkpoint(path: Path, *, model, optimizer, scheduler, epoch: int,
                    cfg: dict, rng: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict() if scheduler is not None else None,
        "epoch": int(epoch),
        "config": cfg,
        "config_hash": config_hash(cfg),
        "rng": rng,
    }, path)


def load_checkpoint(path: Path, *, model, optimizer=None, scheduler=None,
                    cfg: dict | None = None) -> dict:
    """Restore a checkpoint, refusing a config-hash mismatch.

    A resumed run whose configuration changed is a *different* run; silently
    continuing would mix two experiments in one set of weights.
    """
    ck = torch.load(path, map_location="cpu", weights_only=False)
    if cfg is not None:
        want = config_hash(cfg)
        if ck.get("config_hash") != want:
            raise RuntimeError(
                f"config hash mismatch: checkpoint {str(ck.get('config_hash'))[:12]} vs "
                f"current {want[:12]} — resume would mix two configurations. "
                "Pass --resume-checkpoint with the matching config, or start fresh."
            )
    model.load_state_dict(ck["model"])
    if optimizer is not None and ck.get("optimizer") is not None:
        optimizer.load_state_dict(ck["optimizer"])
    if scheduler is not None and ck.get("scheduler") is not None:
        scheduler.load_state_dict(ck["scheduler"])
    if ck.get("rng"):
        _restore_rng(ck["rng"])
    return ck


def build_optimizer(model, cfg: dict):
    params = [p for p in model.parameters() if p.requires_grad]
    return torch.optim.AdamW(params, lr=cfg["lr"], weight_decay=cfg["weight_decay"])


def build_scheduler(optimizer, epochs: int, *, warmup: int = 1):
    """Linear warm-up then cosine decay to 5 % of the base LR."""
    def fn(step: int) -> float:
        if step < warmup:
            return (step + 1) / max(1, warmup)
        p = (step - warmup) / max(1, epochs - warmup)
        return 0.05 + 0.95 * 0.5 * (1.0 + math.cos(math.pi * min(1.0, p)))
    return torch.optim.lr_scheduler.LambdaLR(optimizer, fn)


def _contaminate_values(raw, obs, in_field, *, rec: dict):
    """Apply the preregistered raw-unit perturbation before standardization."""
    from ssl_anomaly.monitor.patch_perturbations import FOOTPRINT_PROTOCOL, inject_patch_drop
    from ssl_anomaly.train.contamination import CONTAMINATION_INDEX

    return inject_patch_drop(
        raw, obs, index=CONTAMINATION_INDEX, delta=float(rec["delta"]),
        onset_bin=rec["onset_bin"], shape=rec["family"], duration=rec["n_bins_window"],
        footprint=FOOTPRINT_PROTOCOL, in_field=in_field, level_id=rec.get("level_id"),
    ).x


def trim_schedule(epoch: int, cfg: dict) -> float:
    """Top-fraction trimming active only after the warm-up epoch."""
    return float(cfg["trim_top_frac"]) if epoch >= int(cfg["trim_after_epoch"]) else 0.0


def mask_burn_in(obs: np.ndarray, burn_in: int) -> np.ndarray:
    """Drop the first ``burn_in`` bins from the loss mask (state warm-up)."""
    if burn_in <= 0:
        return obs
    out = np.array(obs, copy=True)
    out[:, :burn_in] = False
    return out


# ---------------------------------------------------------------------------
# runtime estimate (task 1.4 / G5)
# ---------------------------------------------------------------------------
def estimate_runtime(ds, *, cfg: dict, device: str, n_seeds: int) -> dict:
    """Time ONE real batch, then extrapolate. No optimisation step is kept."""
    n = len(ds)
    if n == 0:
        raise SystemExit("dataset is empty — check --max-fields / the holdout manifest")
    bs = int(cfg["batch_size"])
    model = build_patch_model(
        use_cnn=cfg["arch"] == "patch_cnn_gru",
        n_covariates=PD.N_COVARIATES,
        d_model=int(cfg["d_model"]),
        n_horizons=int(cfg["n_horizons"]),
    ).to(device)
    idx = np.random.default_rng(0).choice(n, size=min(bs, n), replace=False)
    batch = PD.collate([ds.sample(int(i)) for i in idx])
    tensors = {
        "x": torch.from_numpy(batch["x"]).to(device),
        "obs": torch.from_numpy(batch["obs"]).to(device),
        "pv": torch.from_numpy(batch["pixel_valid"]).to(device),
        "cov": torch.from_numpy(batch["covariates"]).to(device),
    }
    params = sum(p.numel() for p in model.parameters())
    t0 = time.time()
    out = model(tensors["x"], tensors["pv"], covariates=tensors["cov"])
    loss, _ = model.hybrid_loss(out, tensors["x"], tensors["obs"])
    loss.backward()
    dt = time.time() - t0
    est = PD.estimate_epoch_seconds(n, seconds_per_sample=dt, batch_size=bs)
    # Checkpoint disk: weights + Adam m/v (fp32) per epoch, plus the progress log.
    ck_bytes = params * 4 * 3
    total = est["seconds_per_epoch"] * int(cfg["epochs"]) * n_seeds
    return {
        "device": device,
        "n_parameters": int(params),
        "probe_batch_seconds": round(dt, 4),
        "n_samples": n,
        "n_batches_per_epoch": est["n_batches"],
        "seconds_per_epoch": round(est["seconds_per_epoch"], 2),
        "epochs": int(cfg["epochs"]),
        "seeds": n_seeds,
        "total_seconds": round(total, 1),
        "total_hours": round(total / 3600.0, 2),
        "checkpoint_bytes_per_epoch": int(ck_bytes),
        "checkpoint_bytes_total": int(ck_bytes * int(cfg["epochs"]) * n_seeds),
        "progress_log_bytes_estimate": int(160 * int(cfg["epochs"]) * n_seeds),
    }


# ---------------------------------------------------------------------------
# training
# ---------------------------------------------------------------------------
def train_one_seed(ds, *, cfg: dict, out_dir: Path, device: str, smoke: bool,
                   resume_from: Path | None, progress_path: Path,
                   contaminations: dict[int, dict] | None = None) -> dict:
    torch.manual_seed(int(cfg["seed"]))
    np.random.seed(int(cfg["seed"]))
    model = build_patch_model(
        use_cnn=cfg["arch"] == "patch_cnn_gru",
        n_covariates=PD.N_COVARIATES,
        d_model=int(cfg["d_model"]),
        n_horizons=int(cfg["n_horizons"]),
    ).to(device)
    opt = build_optimizer(model, cfg)
    sched = build_scheduler(opt, int(cfg["epochs"]))
    start_epoch = 0
    if resume_from is not None:
        ck = load_checkpoint(resume_from, model=model, optimizer=opt,
                             scheduler=sched, cfg=cfg)
        start_epoch = int(ck["epoch"]) + 1
        print(f"[patch] resumed from {resume_from.name} at epoch {start_epoch}")

    epochs = 1 if smoke else int(cfg["epochs"])
    bs = int(cfg["batch_size"])
    n = len(ds)
    t_start = time.time()
    history: list[dict] = []
    # one real batch kept for the benchmarking block (task 1.2): MACs and
    # inference time must be measured on the shapes actually trained on.
    example: tuple | None = None

    for epoch in range(start_epoch, epochs):
        model.train()
        order = np.random.default_rng([int(cfg["seed"]), epoch]).permutation(n)
        trim = trim_schedule(epoch, cfg)
        run_loss, run_n = 0.0, 0
        for b0 in range(0, n, bs):
            idx = order[b0:b0 + bs]
            if idx.size == 0:
                continue
            samples = []
            for i in idx:
                rec = (contaminations or {}).get(int(i))
                transform = partial(_contaminate_values, rec=rec) if rec is not None else None
                samples.append(ds.sample(int(i), transform=transform))
            batch = PD.collate(samples)
            obs = mask_burn_in(batch["obs"], int(cfg["burn_in_bins"]))
            if example is None:
                example = (torch.from_numpy(batch["x"][:1]).cpu(),
                           torch.from_numpy(batch["pixel_valid"][:1]).cpu(),
                           torch.from_numpy(batch["covariates"][:1]).cpu())
            x = torch.from_numpy(batch["x"]).to(device)
            out = model(
                x,
                torch.from_numpy(batch["pixel_valid"]).to(device),
                covariates=torch.from_numpy(batch["covariates"]).to(device),
            )
            loss, parts = model.hybrid_loss(
                out, x, torch.from_numpy(obs).to(device),
                weights=tuple(cfg["horizon_weights"]),
                aux_weight=float(cfg["aux_weight"]),
                trimmed_top_frac=trim,
            )
            if not torch.isfinite(loss):
                raise RuntimeError(
                    f"non-finite loss at epoch {epoch} — refusing to save weights"
                )
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                [p for p in model.parameters() if p.requires_grad],
                float(cfg["grad_clip"]),
            )
            opt.step()
            run_loss += float(loss.detach()) * idx.size
            run_n += idx.size
        sched.step()

        rec = {
            "stage": "patch_train", "arch": cfg["arch"], "seed": int(cfg["seed"]),
            "epoch": epoch, "epochs": epochs,
            "train_loss": round(run_loss / max(1, run_n), 6),
            "trim_frac": trim,
            "lr": float(opt.param_groups[0]["lr"]),
            "wall_s": round(time.time() - t_start, 1),
        }
        history.append(rec)
        with progress_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"[patch] epoch {epoch}/{epochs} loss={rec['train_loss']:.4f} "
              f"trim={trim} lr={rec['lr']:.2e}")

        ck_path = out_dir / f"epoch{epoch:03d}.pt"
        save_checkpoint(ck_path, model=model, optimizer=opt, scheduler=sched,
                        epoch=epoch, cfg=cfg, rng=_rng_state({}))
        save_checkpoint(out_dir / "last.pt", model=model, optimizer=opt,
                        scheduler=sched, epoch=epoch, cfg=cfg, rng=_rng_state({}))

    wall = time.time() - t_start
    return {"history": history, "wall_time_s": round(wall, 1),
            "n_parameters": int(sum(p.numel() for p in model.parameters())),
            "final_epoch": epochs - 1, "model": model, "example": example}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Patch-level causal training (owner-run; use --smoke / "
                    "--estimate-runtime first).",
    )
    p.add_argument("--arch", choices=["patch_cnn_gru", "patch_pixelwise"],
                   default="patch_cnn_gru")
    p.add_argument("--store", default=str(REPO_ROOT / "data" / "processed" / P.PATCH_STORE_NAME))
    p.add_argument("--splits", type=Path, default=S.SPLITS_LOCKED_PATH,
                   help="verified locked splits that the store and holdout both reference")
    p.add_argument("--norm", default=None,
                   help=f"frozen normalization json (default: next to the store, {P.NORM_STATS_NAME})")
    p.add_argument("--holdout-manifest", default=None,
                   help=f"frozen holdout json (default: {H.HOLDOUT_MANIFEST_PATH})")
    p.add_argument("--out", default=str(DEFAULT_OUT))
    p.add_argument("--seed", type=int, default=13)
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--d-model", type=int, default=64)
    p.add_argument("--n-horizons", type=int, default=3)
    p.add_argument("--aux-weight", type=float, default=0.3)
    p.add_argument("--horizon-weights", default="1.0,0.5,0.25")
    p.add_argument("--burn-in-bins", type=int, default=8)
    p.add_argument("--trim-top-frac", type=float, default=0.05)
    p.add_argument("--trim-after-epoch", type=int, default=10)
    p.add_argument("--grad-clip", type=float, default=1.0)
    p.add_argument("--max-fields", type=int, default=None)
    p.add_argument("--max-cycles", type=int, default=None)
    p.add_argument("--device", default="auto")
    p.add_argument("--smoke", action="store_true", help="one epoch, tiny subset, no full run")
    p.add_argument("--estimate-runtime", action="store_true",
                   help="print wall-time/disk estimates and exit WITHOUT training")
    p.add_argument("--resume", action="store_true", help="resume from <out>/last.pt")
    p.add_argument("--no-benchmark", action="store_true",
                   help="skip the benchmarking block in the manifest (debug/smoke only)")
    p.add_argument("--resume-checkpoint", default=None, help="explicit checkpoint path")
    p.add_argument("--seeds", default=None,
                   help="comma-separated seeds for the estimate (they are launched separately)")
    # ---- contamination axis (patch-contamination-absorption task 1.2) ----
    p.add_argument("--contaminate-fraction", type=float, default=0.0,
                   help="share of TRAIN cycles receiving the S4-persistent ndvi injection "
                        "before training (0 = clean; the frozen protocol default)")
    p.add_argument("--contaminate-seed", type=int, default=13,
                   help="seed for the contaminated-cycle selection (recorded in the manifest)")
    p.add_argument("--trimmed-loss", choices=["on", "off"], default="on",
                   help="top-5%% trimmed loss after the warm-up epoch")
    p.add_argument("--curation", choices=["on", "off"], default="off",
                   help="two-phase run: drop the worst 2%% of train cycles after epoch 0 "
                        "and continue; removed ids are written to the manifest")
    return p


def cfg_from_args(args) -> dict:
    return {
        "arch": args.arch,
        "seed": int(args.seed),
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "lr": float(args.lr),
        "weight_decay": float(args.weight_decay),
        "d_model": int(args.d_model),
        "n_horizons": int(args.n_horizons),
        "aux_weight": float(args.aux_weight),
        "horizon_weights": [float(x) for x in str(args.horizon_weights).split(",")],
        "burn_in_bins": int(args.burn_in_bins),
        "trim_top_frac": float(args.trim_top_frac),
        "trim_after_epoch": int(args.trim_after_epoch),
        "grad_clip": float(args.grad_clip),
        "max_fields": args.max_fields,
        "max_cycles": args.max_cycles,
        "contaminate_seed": int(args.contaminate_seed),
        "input_protocol": PD.PATCH_INPUT_PROTOCOL,
        "smoke": args.smoke,
        "n_channels": P.N_CHANNELS,
        "n_covariates": PD.N_COVARIATES,
        "use_cnn": args.arch == "patch_cnn_gru",
        "data_source": str(args.store),
        "covariates": list(PD.COVARIATES),
        **CT.contamination_config(
            args.contaminate_fraction,
            trimmed=args.trimmed_loss == "on",
            curation=args.curation == "on",
        ),
    }


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    cfg = cfg_from_args(args)
    device = pick_device(args.device)

    store_path = Path(args.store)
    if not store_path.exists():
        raise SystemExit(
            f"patch store not found: {store_path}\n"
            "Run scripts/extract_patches.py on the data-archive machine first "
            "(patch-data-pipeline task 2.1), then --estimate-runtime / --smoke."
        )
    root = P.open_store(store_path)
    manifest = P.validate_store(root)

    norm_path = Path(args.norm) if args.norm else store_path.parent / P.NORM_STATS_NAME
    norm = P.load_patch_norm(norm_path)                # verifies the self-hash
    cfg["norm_sha256"] = P.norm_stats_sha256(norm)

    holdout = (
        H.load_holdout_manifest(path=Path(args.holdout_manifest))
        if args.holdout_manifest else H.load_holdout_manifest()
    )
    cfg["holdout_sha256"] = H.holdout_manifest_hash(holdout)

    splits = S.load_splits_locked(path=args.splits, verify_cycle_files=False)
    cfg["splits_sha256"] = splits["manifest_sha256"]
    all_fields = [int(f) for f in np.asarray(root["field_ids"][:])]
    if args.max_fields:
        all_fields = all_fields[: int(args.max_fields)]
    ds = PD.PatchCycleDataset(
        root, all_fields, splits_manifest=splits, holdout_manifest=holdout, norm=norm,
        max_cycles=args.max_cycles,
    )
    cfg["admitted_cycles_sha256"] = hashlib.sha256(
        json.dumps([(c.key, c.start_day, c.end_day) for c in ds.cycles]).encode()
    ).hexdigest()
    print(f"[patch] store {store_path} ({manifest.get('n_fields', '?')} fields)")
    print(f"[patch] {len(ds)} field-cycles from {len(ds.fields)} trainable fields "
          f"({len(ds.excluded_by_holdout)} excluded by the holdout manifest)")
    contamination_meta: dict = {"fraction": float(cfg["contaminate_fraction"])}
    contaminations: dict[int, dict] | None = None
    if cfg["contaminate_fraction"] > 0:
        keys = [c.key for c in ds.cycles]
        row_by_key = {key: i for i, key in enumerate(keys)}
        excluded = set(ds.excluded_by_holdout)
        chosen = CT.select_contaminated_cycles(
            keys, fraction=cfg["contaminate_fraction"],
            seed=int(args.contaminate_seed), excluded_fields=excluded,
        )
        rows = [row_by_key[key] for key in chosen]
        contaminations = CT.plan_contamination(rows, seed=int(args.contaminate_seed))
        print(f"[patch] contaminating {len(rows)}/{len(ds)} train cycles "
              f"(S4 persistent ndvi, seed {args.contaminate_seed})")
        contamination_meta = {
            "fraction": float(cfg["contaminate_fraction"]),
            "seed": int(args.contaminate_seed),
            "level_id": CT.CONTAMINATION_LEVEL,
            "family": CT.CONTAMINATION_FAMILY,
            "index": CT.CONTAMINATION_INDEX,
            "n_selected": len(rows),
            "selected_keys": chosen,
            "onsets": {str(k): v["onset_bin"] for k, v in contaminations.items()},
            "value_scale": 1.0,
            "units": "physical NDVI before frozen normalization",
        }

    print(f"[patch] arch={args.arch} device={device} params≈"
          f"{build_patch_model(use_cnn=args.arch == 'patch_cnn_gru', n_covariates=PD.N_COVARIATES, d_model=args.d_model, n_horizons=args.n_horizons).param_report()['n_parameters']}")

    seeds = ([int(s) for s in str(args.seeds).split(",")]
             if args.seeds else [int(args.seed)])
    if args.estimate_runtime:
        est = estimate_runtime(ds, cfg=cfg, device=device, n_seeds=len(seeds))
        est["config_hash"] = config_hash(cfg)
        print(json.dumps(est, indent=2))
        print("[patch] estimate only — nothing was trained. "
              "Re-run without --estimate-runtime to train.")
        return 0

    out_dir = Path(args.out) / f"{args.arch}_seed{args.seed}" / (
        "_smoke" if args.smoke else ""
    )
    resume_from = None
    if args.resume_checkpoint:
        resume_from = Path(args.resume_checkpoint)
    elif args.resume:
        resume_from = out_dir / "last.pt"
    if resume_from is not None and not resume_from.is_file():
        raise FileNotFoundError(f"no patch checkpoint to resume at {resume_from}")
    if resume_from is None and any(out_dir.glob("*.pt")):
        raise RuntimeError(f"patch checkpoints already exist in {out_dir}; use a new --out or resume")
    out_dir.mkdir(parents=True, exist_ok=True)
    progress_path = out_dir / "progress.jsonl"

    run_norm = out_dir / P.NORM_STATS_NAME
    if run_norm.exists() and P.load_patch_norm(run_norm)["sha256"] != norm["sha256"]:
        raise RuntimeError(f"frozen checkpoint norm does not match {norm_path}: {run_norm}")

    run = train_one_seed(ds, cfg=cfg, out_dir=out_dir, device=device, smoke=args.smoke,
                         resume_from=resume_from, progress_path=progress_path,
                         contaminations=contaminations)
    if not run_norm.exists():
        P.save_patch_norm(norm, run_norm)
    manifest_path = out_dir / "run_manifest.json"
    if resume_from is not None and not run["history"] and manifest_path.is_file():
        print(f"[patch] run already complete; kept {manifest_path}")
        return 0
    trained_model = run.pop("model")
    example = run.pop("example")
    report = {
        "protocol": "patch_train_v2",
        "input_protocol": cfg["input_protocol"],
        "splits_sha256": cfg["splits_sha256"],
        "unnormalized_channels": sorted(ds.unnormalized_channels),
        "arch": args.arch,
        "scorer_id": scorer_id(args.arch == "patch_cnn_gru"),
        "config": {k: v for k, v in cfg.items() if k != "horizon_weights"} | {
            "horizon_weights": cfg["horizon_weights"],
        },
        "config_hash": config_hash(cfg),
        "git_sha": git_sha(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "device": device,
        "data_source": str(store_path),
        "holdout_sha256": cfg["holdout_sha256"],
        "norm_sha256": cfg["norm_sha256"],
        "n_field_cycles": len(ds),
        "n_trainable_fields": len(ds.fields),
        "n_excluded_by_holdout": len(ds.excluded_by_holdout),
        "smoke": bool(args.smoke),
        **{k: run[k] for k in ("wall_time_s", "n_parameters", "final_epoch")},
        "history": run["history"],
        "contamination": contamination_meta,
        "curation": {"enabled": bool(cfg["curation"]), "top_frac": CT.CURATION_TOP_FRAC},
    }
    # Benchmarking block (patch-full-run-and-ablations 1.2). Measured on the
    # venue actually used and recorded as such; a field that could not be
    # measured is None with a reason, never zero. --no-benchmark exists for
    # debugging smoke runs only, and the manifest then says so.
    if not args.no_benchmark and example is not None:
        block = RP.benchmark_block(trained_model, example)
        report["benchmark"] = block
        report["benchmark"]["per_field_cycle_note"] = (
            "one field-cycle = one forward pass over a full (T, C, S, S) patch"
        )
        missing = RP.validate_manifest(report, require_benchmark=False)
        report["manifest_missing_fields"] = missing
        if missing:
            print(f"[patch] WARNING manifest incomplete: {missing}", file=sys.stderr)
    else:
        report["benchmark"] = None
        report["benchmark_absent_reason"] = "--no-benchmark"
    manifest_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[patch] done in {run['wall_time_s']}s — wrote {out_dir / 'run_manifest.json'}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
