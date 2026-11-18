#!/usr/bin/env python3
"""Dev-metric evaluation — two protocols (spec model-development-protocol).

**severity** (default; change literature-grounded-severity-protocol):
- Injections: the verified severity table (S1 −0.02 … S6 −0.40 absolute
  index drops) × {acute, persistent} × {ndvi, savi} on the INDEPENDENT
  evaluation subset of dev (disjoint from the threshold-calibration subset,
  deterministic hash partition; the partition hash is recorded).
- Calibration: τ at the 5 % cycle-level FAR on the calibration subset's clean
  cycles; k ∈ {1, 2} chosen by detection rate on calibration-subset injections
  of the S3/acute/ndvi cell (the moderate verified anchor).
- Primary: MDM80 per duration family and index — the lowest level with
  detection rate ≥ 0.80 at the calibrated threshold; censored ">S6" when no
  level reaches 0.80. Secondary: per-level detection with Wilson CIs,
  event-level FAR (declustering, gap ≤ 2 bins), partial-cycle AUC-PR at
  25/50/75 %, masked NRMSE, per-phase breakdown.
- The MAD-scaled D6 statistic (1×MAD headline) is retired; `lst_rise` stays
  runnable only in the legacy protocol (owner decision 2026-11-14).

**legacy** (finding-16 continuity, flagged "legacy" in every artifact):
the interim MAD-scaled perturbation set with detection@1×MAD as primary.

Writes reports/dev/<run_id>/metrics_<model>_sev_<scorer>.json (severity) or
metrics_<model>.json (legacy) with per-seed + mean/std provenance, appends one
row to reports/dev_log.csv (with severity_table_sha256 + eval subset hash),
and streams progress to progress_eval_<model>_sev_<scorer>.jsonl.

Forbidden: this script never reads CWSI, ETa, y_stress, yield or test cycles
(enforced by the forbidden-target unit test and the split guard).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import holdout as mholdout  # noqa: E402
from ssl_anomaly.monitor import inputs as minputs  # noqa: E402
from ssl_anomaly.monitor import models as mmodels  # noqa: E402
from ssl_anomaly.monitor import normal_bank as nbank  # noqa: E402
from ssl_anomaly.monitor import patch_scores as mpscores  # noqa: E402
from ssl_anomaly.monitor import perturbations as mpert  # noqa: E402
from ssl_anomaly.monitor import protocol as mproto  # noqa: E402
from ssl_anomaly.monitor import scoring as mscoring  # noqa: E402
from ssl_anomaly.monitor import severity_table as sev  # noqa: E402
from ssl_anomaly.monitor import splits as msplits  # noqa: E402

BAND_NAMES = ["ndvi", "blue", "green", "red", "nir", "swir1", "swir2", "lst"]
SCORER_CHOICES = ("recon_only", "bank", "fused_max", "fused_weighted",
                  "patch_cnn_gru", "patch_pixelwise")
PATCH_SCORERS = ("patch_cnn_gru", "patch_pixelwise")
# Patch arms live on a different scale from the field-level arms, so no shared
# tau exists. They are evaluated through the empirical-p-value adapter
# (PatchArmScorer), which is why this list is separate rather than a branch
# inside arm_paths().
PATCH_ARTIFACTS = {
    "model": "patch_model.pt",
    "sigma": "patch_sigma.npz",
    "norm": "patch_norm.json",
}
EVAL_PARTITION_SALT = "mdm80_eval_subset_v1"
MDM80_TARGET = 0.80
MDM80_CENSORED = 7  # numeric sentinel for ">S6" (ordering only; reported as ">S6")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run-id", required=True, help="training run id (checkpoints/dev/<run_id>/)")
    p.add_argument("--model", required=True, choices=["masked_transformer", "gru_ae", "gru_pred", "b1", *PATCH_SCORERS])
    p.add_argument("--protocol", choices=["severity", "legacy"], default="severity",
                   help="severity = literature-grounded sweep (headline); legacy = finding-16 MAD-scaled continuity")
    p.add_argument("--scorer", choices=SCORER_CHOICES, default="recon_only",
                   help="scoring arm (severity protocol; bank arms are Phase B of normal-bank-novelty-scoring)")
    p.add_argument("--patch-store", default=None,
                   help="patches.zarr for --scorer patch_* (default: data/processed/patches.zarr)")
    p.add_argument("--patch-run", default=None,
                   help="run id holding patch_model.pt / patch_sigma.npz / patch_norm.json "
                        "(default: --run-id)")
    p.add_argument("--patch-checkpoint", type=Path,
                   help="explicit patch trainer checkpoint (e.g. <out>/<arch>_seed<seed>/last.pt)")
    p.add_argument("--patch-norm", type=Path, help="same-run frozen patch normalization")
    p.add_argument("--patch-sigma", type=Path, help="same-run frozen sigma from clean dev calibration")
    p.add_argument("--holdout-manifest", type=Path, default=mholdout.HOLDOUT_MANIFEST_PATH,
                   help="frozen holdout for patch scoring provenance")
    p.add_argument("--bank-k", type=int, choices=[1, 5], default=5)
    p.add_argument("--bank-distance", choices=["knn", "mahalanobis"], default="knn")
    p.add_argument("--seeds", default="13,42,2026", help="seeds to evaluate (default: 13,42,2026)")
    p.add_argument("--far", type=float, default=0.05)
    p.add_argument("--rounds", type=int, default=2,
                   help="severity sweep: injection rounds per cell (each round injects every eval cycle once)")
    p.add_argument("--n-per-stratum", type=int, default=8,
                   help="legacy protocol only: injected cycles per dev cycle per round")
    p.add_argument("--extended-severity", action="store_true", default=True,
                   help="legacy protocol only: diagnostic 4/6/8×MAD sweep (finding 16)")
    p.add_argument("--no-extended-severity", dest="extended_severity", action="store_false")
    p.add_argument("--shapes", default="acute,persistent",
                   help="temporal shapes for the severity sweep, comma-separated. "
                        "'gradual' (change gradual-severity-shape) adds the third primary "
                        "shape as EXTRA columns; the acute/persistent injection sets and "
                        "their hashes are untouched, so recorded findings stay comparable. "
                        "Allowed: acute, persistent, gradual.")
    p.add_argument("--smoke", action="store_true", help="tiny subset for agent smoke runs")
    p.add_argument("--device", default=None)
    p.add_argument("--notes", default="")
    return p.parse_args(argv)


def load_patch_artifacts(run_id: str, *, checkpoint_path: Path | None = None,
                         norm_path: Path | None = None, sigma_path: Path | None = None) -> tuple:
    """Load the same-run checkpoint, normalization and frozen σ. Never refit."""
    import torch

    from ssl_anomaly.io import patches as P
    from ssl_anomaly.models.patch_cnn_gru import build_patch_model
    from ssl_anomaly.train.patch_data import COVARIATES, N_COVARIATES, PATCH_INPUT_PROTOCOL

    root = checkpoint_path.parent if checkpoint_path else mproto.CHECKPOINTS_DEV_DIR / run_id
    model_path = checkpoint_path or root / PATCH_ARTIFACTS["model"]
    sigma_file = sigma_path or root / PATCH_ARTIFACTS["sigma"]
    norm_file = norm_path or root / (P.NORM_STATS_NAME if checkpoint_path else PATCH_ARTIFACTS["norm"])
    for label, path in (("model", model_path), ("sigma", sigma_file), ("norm", norm_file)):
        if not path.is_file():
            raise FileNotFoundError(
                f"patch {label} artifact not found: {path} — the patch arm needs the "
                "checkpoint, the frozen sigma table and the norm sidecar from the SAME "
                "run; nothing is inferred or refitted here."
            )

    payload = torch.load(model_path, map_location="cpu", weights_only=False)
    cfg = payload["config"]
    if cfg.get("input_protocol") != PATCH_INPUT_PROTOCOL:
        raise ValueError("patch checkpoint predates the corrected input protocol; do not rescore legacy weights")
    if (cfg.get("n_channels") != P.N_CHANNELS or cfg.get("n_covariates") != N_COVARIATES
            or cfg.get("covariates") != list(COVARIATES)):
        raise ValueError("patch checkpoint channels/covariates do not match the input protocol")
    norm = P.load_patch_norm(norm_file)
    if norm["sha256"] != cfg.get("norm_sha256"):
        raise ValueError("patch checkpoint and frozen normalization hashes differ")
    for key in ("splits_sha256", "holdout_sha256"):
        if not norm.get(key) or norm[key] != cfg.get(key):
            raise ValueError(f"patch checkpoint and normalization disagree on {key}")
    model = build_patch_model(
        use_cnn=bool(cfg["use_cnn"]),
        n_channels=P.N_CHANNELS,
        d_model=int(cfg["d_model"]),
        n_covariates=N_COVARIATES,
        n_horizons=int(cfg["n_horizons"]),
        stem_widths=tuple(cfg.get("stem_widths", (44, 60))),
    )
    model.load_state_dict(payload["state_dict"] if "state_dict" in payload else payload["model"])

    with np.load(sigma_file, allow_pickle=False) as sd:
        sigma = mpscores.PatchSigmaTable(
            sigma=sd["sigma"], fallback=sd["fallback"], n=sd["n"],
            min_n=int(sd["min_n"]), sha256=str(sd["sha256"]),
        )
        expected = {"model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
                    "norm_sha256": norm["sha256"], "input_protocol": PATCH_INPUT_PROTOCOL}
        if any(k not in sd.files or str(sd[k]) != v for k, v in expected.items()):
            raise ValueError("patch sigma is not bound to this checkpoint and input protocol")
    if sigma.sha256 != mpscores.sigma_table_sha256(sigma.sigma, sigma.fallback, sigma.n):
        raise ValueError("patch sigma table failed its sha256 check")
    return model, sigma, norm, cfg


def build_patch_arm(arm: str, model, cfg: dict, device: str, *, sigma,
                    in_field: np.ndarray) -> mpscores.PatchDeepScorer:
    """Keep the scorer label tied to the checkpoint's architecture."""
    from ssl_anomaly.models.patch_cnn_gru import scorer_id

    want_cnn = arm == "patch_cnn_gru"
    if bool(cfg["use_cnn"]) is not want_cnn:
        raise ValueError(f"checkpoint use_cnn={cfg['use_cnn']} does not match scorer {arm}")
    return mpscores.PatchDeepScorer(
        scorer_id(want_cnn), model, sigma,
        in_field=in_field, n_channels=int(cfg["n_channels"]), device=device,
    )


def load_scorer(model: str, seed: int, run_id: str, device: str) -> tuple:
    """Load one checkpoint and return (scorer, n_params, n_channels)."""
    import torch

    ckpt_dir = mproto.CHECKPOINTS_DEV_DIR / run_id
    if model == "b1":
        stats_path = ckpt_dir / f"b1_phasez_causal_seed{seed}.npz"
        if not stats_path.exists():
            raise FileNotFoundError(f"B1 stats not found: {stats_path}")
        d = np.load(stats_path, allow_pickle=True)
        b1 = mmodels.B1PhaseZCausal(use_doy=bool(d["use_doy"]), min_n=8)
        b1.median = d["median"]
        b1.scale = d["scale"]
        if "robust_range" in d.files:
            b1.robust_range = d["robust_range"]
        return b1, 0, int(b1.median.shape[-1])
    ckpt_path = ckpt_dir / f"{model}_seed{seed}.pt"
    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")
    payload = torch.load(ckpt_path, map_location=device, weights_only=False)
    cfg = payload["config"]
    torch_model = mmodels.build_model(model, d_in=cfg["d_in"], n_out=cfg["n_out"], cfg={
        k: cfg[k] for k in ("d_model", "n_layers", "d_ff", "n_heads", "dropout") if k in cfg
    })
    torch_model.load_state_dict(payload["state_dict"])
    # gru_pred (predictive-ssl-controlled-trial): the one-step-ahead scorer —
    # same loo_batch signature, naturally causal single pass.
    scorer_cls = mmodels.DeepPredictiveScorer if model == "gru_pred" else mmodels.DeepCausalScorer
    scorer = scorer_cls(
        model, torch_model, use_doy=bool(cfg.get("use_doy", True)), device=device,
    )
    return scorer, mmodels.count_parameters(torch_model), int(cfg["n_out"])


def score_cycles(scorer, X_raw: np.ndarray, M: np.ndarray, doy: np.ndarray, norm: dict | None):
    """Score cycles; returns dict with per-bin statistics + predictions.

    - "mean": observed-mask-weighted MSE in z-space (D5 L1 statistic; secondary)
    - "z2": per-(bin, channel) squared z-space residuals (alarm-statistic input)
    - "pred_raw": withheld-bin predictions mapped back to raw units (NRMSE)

    Deep scorers work in z-space; predictions are mapped back to raw units so
    NRMSE is comparable with B1. B1 predicts the train climatology directly.
    """
    if isinstance(scorer, mmodels.B1PhaseZCausal):
        N, T, C = X_raw.shape
        scores = np.full((N, T), np.nan)
        z2 = np.zeros((N, T, C))
        pred_raw = np.zeros((N, T, C))
        for i in range(N):
            scores[i] = scorer.score_cycle(X_raw[i], M[i], doy[i, :, 0])
            g = scorer.season_group(doy[i, :, 0]) if scorer.use_doy else np.zeros(T, dtype=np.int64)
            med = scorer.median[g, np.arange(T)]
            scale = scorer.scale[g, np.arange(T)]
            pred_raw[i] = med
            zc = np.where(M[i], (X_raw[i] - med) / scale, 0.0)
            # Signed robust-z residual vs the train climatology, then the
            # causal field-offset correction (dev-loop change #2, refined).
            resid_corr = mscoring.causal_offset_correct(zc[None], M[i][None])[0]
            z2[i] = resid_corr * resid_corr * M[i]
        return {"mean": scores, "z2": z2, "pred_raw": pred_raw}
    z = minputs.apply_norm(norm, X_raw, M)
    scores, pred_z = scorer.loo_batch(z, M, doy)
    pred_raw = pred_z * norm["scale"][None] + norm["median"][None]
    resid = z - pred_z  # signed: value − prediction
    resid_corr = mscoring.causal_offset_correct(resid, M)
    z2 = (resid_corr * resid_corr) * M  # zero where unobserved
    return {"mean": scores, "z2": z2, "pred_raw": pred_raw}


# ---------------------------------------------------------------------------
# Severity protocol helpers (change literature-grounded-severity-protocol)
# ---------------------------------------------------------------------------
def partition_calib_eval(
    cycle_keys: list[str],
    *,
    frac_eval: float = 0.5,
    salt: str = EVAL_PARTITION_SALT,
) -> tuple[list[int], list[int], str]:
    """Deterministic disjoint partition of the dev cycles into the threshold
    CALIBRATION subset and the INDEPENDENT EVALUATION subset (spec: the MDM
    sweep uses clean dev cycles disjoint from the calibration subset where
    dev size permits).

    Cycles are ordered by sha256(salt + key) and the last ``frac_eval`` share
    becomes the evaluation subset — deterministic across arms, seeds and
    reruns. Returns (calibration indices, evaluation indices, evaluation
    subset hash = sha256 of the sorted evaluation keys).
    """
    if len(cycle_keys) < 8:
        raise ValueError(
            f"partition_calib_eval needs ≥8 dev cycles for a disjoint split, got {len(cycle_keys)}"
        )
    order = sorted(range(len(cycle_keys)),
                   key=lambda i: hashlib.sha256((salt + cycle_keys[i]).encode("utf-8")).hexdigest())
    n_eval = max(4, int(round(frac_eval * len(cycle_keys))))
    eval_idx = sorted(order[-n_eval:])
    calib_idx = sorted(order[:-n_eval])
    eval_keys = sorted(cycle_keys[i] for i in eval_idx)
    eval_hash = hashlib.sha256(json.dumps(eval_keys).encode("utf-8")).hexdigest()[:16]
    return calib_idx, eval_idx, eval_hash


def arm_paths(
    args: argparse.Namespace,
    recon_paths: np.ndarray,
    bank_scores: np.ndarray | None,
) -> np.ndarray:
    """Paths of the selected scoring arm (Phase-B hook for the bank arms).

    recon_only: the reconstruction alarm statistic unchanged.
    bank/fused_*: require bank scores (Phase B of normal-bank-novelty-scoring).
    """
    if args.scorer == "recon_only":
        return recon_paths
    if bank_scores is None:
        raise RuntimeError(
            f"--scorer {args.scorer} requires bank scores; bank arms land with "
            "normal-bank-novelty-scoring Phase B."
        )
    if args.scorer == "bank":
        return bank_scores
    if args.scorer == "fused_max":
        with np.errstate(invalid="ignore"):
            return np.fmax(recon_paths, bank_scores)
    # fused_weighted: mean of the two statistics; where only one is defined,
    # that one carries the bin (NaN bins stay NaN).
    both = np.isfinite(recon_paths) & np.isfinite(bank_scores)
    out = np.where(both, 0.5 * (recon_paths + bank_scores),
                   np.where(np.isfinite(recon_paths), recon_paths, bank_scores))
    return out


def run_severity_protocol(args: argparse.Namespace, manifest: dict, sel: dict, seeds: list[str],
                          device: str, data: dict | None = None) -> tuple[dict, list]:
    """The literature-grounded severity sweep + MDM80 (one run, all seeds)."""
    if args.scorer in PATCH_SCORERS:
        return run_patch_severity_protocol(args, manifest, sel, seeds, device, data=data)
    X, M = sel["X"], sel["M"]
    doy = minputs.doy_channels(sel["harvest_days"])
    N, T, C = X.shape
    cycle_keys = list(sel["cycle_keys"])

    norm = None
    if args.model != "b1":
        norm = minputs.load_norm(mproto.DEV_DIR / args.run_id / "norm_stats.npz")

    if args.smoke:
        rng0 = np.random.default_rng(7)
        keep = rng0.choice(N, size=min(12, N), replace=False)
        X, M, doy = X[keep], M[keep], doy[keep]
        cycle_keys = [cycle_keys[i] for i in keep]
        seeds = seeds[:1]
        args.rounds = 1
        N = X.shape[0]

    # Ablation runs (no-LST) carry fewer channels: slice X/M to the
    # checkpoint's channel count (order preserved; dropped channels are the
    # trailing lst) — same pattern as the legacy protocol.
    _, _, probe_channels = load_scorer(args.model, seeds[0], args.run_id, device)
    channel_count = probe_channels
    if channel_count < X.shape[2]:
        X, M = X[:, :, :channel_count], M[:, :, :channel_count]
    N, T, C = X.shape

    calib_idx, eval_idx, eval_hash = partition_calib_eval(cycle_keys)
    n_calib, n_eval = len(calib_idx), len(eval_idx)
    print(f"[severity] calibration subset n={n_calib}, independent evaluation subset n={n_eval} "
          f"(hash {eval_hash})")

    levels = sev.load_table()
    table_hash = sev.severity_table_hash()
    families = [f.strip() for f in str(args.shapes).split(",") if f.strip()]
    unknown_fams = [f for f in families if f not in sev.PRIMARY_FAMILIES]
    if unknown_fams:
        raise SystemExit(
            f"--shapes got {unknown_fams}; allowed primary shapes are "
            f"{list(sev.PRIMARY_FAMILIES)} (secondary diagnostic shapes never enter "
            "this table — see gradual-severity-shape spec)."
        )
    if sev.ACUTE_FAMILY not in families or sev.PERSISTENT_FAMILY not in families:
        print("[severity] NOTE: the frozen primary shapes are acute+persistent; "
              f"running {families} only. Recorded findings are NOT reproduced by this run.")

    cells_all = [f"{lv.level_id}/{fam}/{idx}"
                 for lv in levels
                 for fam in families
                 for idx in ("ndvi", "savi")]

    # ---- Bank arm setup (Phase B, normal-bank-novelty-scoring) -----------
    bank = None
    emb_fn = None
    if args.scorer != "recon_only":
        if args.model != "gru_ae":
            raise SystemExit(
                "--scorer bank/fused_* is defined on the gru_ae encoder only "
                "(change normal-bank-novelty-scoring); re-run with --model gru_ae."
            )
        sel_train = mproto.select_splits(data, manifest, splits=("train",))
        print(f"[severity] bank arm: building bank from {len(sel_train['cycle_keys'])} train cycles "
              f"(k={args.bank_k}, distance={args.bank_distance}, min_class_count=8)")

    norm_path = mproto.DEV_DIR / args.run_id
    progress_path = norm_path / f"progress_eval_{args.model}_sev_{args.scorer}{'_smoke' if args.smoke else ''}.jsonl"
    norm_path.mkdir(parents=True, exist_ok=True)
    total_steps = len(seeds) * (1 + len(cells_all) * max(1, args.rounds))
    done_steps = 0
    t_start = time.time()

    def progress(**kw) -> None:
        nonlocal done_steps
        done_steps += 1
        rec = {"stage": "severity_sweep", "step": done_steps, "total": total_steps,
               "wall_s": round(time.time() - t_start, 1),
               "eta_s": round((time.time() - t_start) / done_steps * (total_steps - done_steps), 1),
               **kw}
        with progress_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    per_seed: list[dict] = []
    for seed in seeds:
        scorer, params, _ = load_scorer(args.model, seed, args.run_id, device)

        # ---- Bank build (train cycles only, manifest-gated) -----------------
        if args.scorer != "recon_only":
            sel_train = mproto.select_splits(data, manifest, splits=("train",))
            Xtr, Mtr = sel_train["X"], sel_train["M"]
            if Mtr.shape[2] != M.shape[2]:
                Xtr, Mtr = Xtr[:, :, :M.shape[2]], Mtr[:, :, :M.shape[2]]
            doytr = minputs.doy_channels(sel_train["harvest_days"])
            emb_fn = nbank.gru_embedding_fn(scorer)
            ztr = minputs.apply_norm(norm, Xtr, Mtr)
            emb_tr = emb_fn(ztr, Mtr, doytr)
            import hashlib as _h

            ckpt_sha = _h.sha256(
                (mproto.CHECKPOINTS_DEV_DIR / args.run_id / f"{args.model}_seed{seed}.pt").read_bytes()
            ).hexdigest()
            bank = nbank.build_bank(
                emb_tr, Mtr, list(sel_train["cycle_keys"]), manifest,
                min_class_count=8, k=args.bank_k, distance=args.bank_distance,
                encoder_sha256=ckpt_sha,
            )
            bank_manifest_path = (mproto.DEV_DIR / args.run_id /
                                  f"bank_{args.bank_distance}{args.bank_k}_seed{seed}.json")
            bank_manifest_path.write_text(json.dumps(bank.manifest(), indent=2), encoding="utf-8")
            bm = bank.manifest()
            print(f"[severity] bank built: {bm['n_entries']} entries / {bm['n_cycles']} cycles, "
                  f"{bm['n_cells_direct']} direct cells, splits={bm['splits_present']} "
                  f"(manifest {bank_manifest_path.name})")

        def paths_for_batch(Xb: np.ndarray, Mb: np.ndarray, doyb: np.ndarray,
                            z2b: np.ndarray) -> np.ndarray:
            """Alarm paths of the selected arm for one scored batch."""
            recon = mscoring.cumulative_channel_max(z2b, Mb, cell_q95)
            if args.scorer == "recon_only":
                return recon
            zb = minputs.apply_norm(norm, Xb, Mb)
            emb_q = emb_fn(zb, Mb, doyb)
            bank_scores, _fb = bank.score_batch(emb_q, Mb)
            return arm_paths(args, recon, bank_scores)

        # ---- Clean scores (calibration + evaluation) -----------------------
        clean = score_cycles(scorer, X, M, doy, norm)
        # Per-cell normalizer from the CALIBRATION subset only — the
        # evaluation subset stays independent of every statistic input.
        cell_q95 = mscoring.cell_q95_normalizer(clean["z2"][calib_idx], M[calib_idx])
        clean_paths_all = paths_for_batch(X, M, doy, clean["z2"])

        # ---- Threshold (τ, k) on the CALIBRATION subset ---------------------
        ksel = mpert.inject_index_drop_dataset(
            X[calib_idx], M[calib_idx], level_id="S3", family=sev.ACUTE_FAMILY,
            index="ndvi", round_idx=0,
        )
        Xk = np.stack([r.x for r in ksel])
        Mk = np.stack([r.m for r in ksel])
        doyk = doy[calib_idx][[r.source_row for r in ksel]]
        ksel_scores = score_cycles(scorer, Xk, Mk, doyk, norm)
        ksel_paths = paths_for_batch(Xk, Mk, doyk, ksel_scores["z2"])
        threshold, per_k = mscoring.choose_threshold(
            [clean_paths_all[i] for i in calib_idx],
            [ksel_paths[j] for j in range(len(ksel))],
            [r.onset_bin for r in ksel],
            far_target=args.far,
        )
        tau, k = threshold.tau, threshold.k
        progress(seed=seed, cell="threshold_calibration")

        # ---- Severity sweep on the INDEPENDENT evaluation subset ------------
        Xe, Me, doye = X[eval_idx], M[eval_idx], doy[eval_idx]
        clean_eval_paths = clean_paths_all[eval_idx]
        cells: dict[str, dict] = {}
        det_pools: dict[str, list[int]] = {}
        delay_pools: dict[str, list[float]] = {}
        window_pools: dict[str, list] = {}
        path_pool: dict[str, list[np.ndarray]] = {}
        for lv in levels:
            for fam in families:
                for index in ("ndvi", "savi"):
                    key = f"{lv.level_id}/{fam}/{index}"
                    det_flags: list[int] = []
                    delays: list[float] = []
                    windows: list = []
                    paths_list: list[np.ndarray] = []
                    for rnd in range(max(1, args.rounds)):
                        results = mpert.inject_index_drop_dataset(
                            Xe, Me, level_id=lv.level_id, family=fam, index=index, round_idx=rnd,
                        )
                        Xinj = np.stack([r.x for r in results])
                        Minj = np.stack([r.m for r in results])
                        doy_inj = doye[[r.source_row for r in results]]
                        s_inj = score_cycles(scorer, Xinj, Minj, doy_inj, norm)
                        inj_paths = paths_for_batch(Xinj, Minj, doy_inj, s_inj["z2"])
                        for j, r in enumerate(results):
                            fb = mscoring.first_alarm_bin(inj_paths[j], tau, k, r.onset_bin)
                            det_flags.append(1 if fb >= 0 else 0)
                            if fb >= 0:
                                delays.append(float((fb - r.onset_bin) * 15))
                            windows.append([(r.onset_bin, r.onset_bin + r.meta["n_bins_window"])])
                            paths_list.append(inj_paths[j])
                        progress(seed=seed, cell=key, round=rnd)
                    n = len(det_flags)
                    n_det = int(sum(det_flags))
                    lo, hi = mscoring.wilson_ci(n_det, n)
                    efar = mscoring.event_far_from_paths(
                        np.stack(paths_list), windows, tau, gap=2,
                    )
                    cells[key] = {
                        "n": n, "n_detected": n_det,
                        "detection_rate": n_det / max(1, n),
                        "wilson_ci95": [round(lo, 4), round(hi, 4)],
                        "median_delay_days": (float(np.median(delays)) if delays else float("nan")),
                        "event_far": efar["event_far"],
                        "n_events": efar["n_events"], "n_false_events": efar["n_false_events"],
                        "level_id": lv.level_id, "family": fam, "index": index,
                        "delta_ndvi": lv.delta_ndvi, "duration_bins":
                            (sev.PERSISTENT_DURATION_BINS if fam == sev.PERSISTENT_FAMILY
                             else (results[0].meta.get("ramp_bins") or lv.duration_bins)
                             if fam == sev.GRADUAL_FAMILY else lv.duration_bins),
                        "ramp_bins": (results[0].meta.get("ramp_bins")
                                      if fam == sev.GRADUAL_FAMILY else None),
                    }
                    det_pools[key] = det_flags
                    delay_pools[key] = delays
                    window_pools[key] = windows
                    path_pool[key] = paths_list

        # ---- MDM80 per family × index (lowest level with det ≥ 0.80) --------
        mdm80: dict[str, dict] = {}
        for fam in families:
            for index in ("ndvi", "savi"):
                reached = None
                for lv in levels:
                    if cells[f"{lv.level_id}/{fam}/{index}"]["detection_rate"] >= MDM80_TARGET:
                        reached = lv.level_id
                        break
                if reached is None:
                    mdm80[f"{fam}/{index}"] = {
                        "value": ">S6", "sentinel": MDM80_CENSORED, "censored": True,
                        "level_cell": None, "median_delay_days": float("nan"),
                    }
                else:
                    cell = cells[f"{reached}/{fam}/{index}"]
                    mdm80[f"{fam}/{index}"] = {
                        "value": reached, "sentinel": int(reached[1:]), "censored": False,
                        "level_cell": f"{reached}/{fam}/{index}",
                        "median_delay_days": cell["median_delay_days"],
                        "detection_rate_at_mdm": cell["detection_rate"],
                    }

        # ---- Secondary metrics ----------------------------------------------
        # Partial-cycle AUC-PR: the acute/ndvi cells (all levels pooled) vs
        # the evaluation subset's clean cycles — the primary index/family.
        auc_inj_idx = [f"{lv.level_id}/{sev.ACUTE_FAMILY}/ndvi" for lv in levels]
        auc_clean = np.array([
            np.nanmax(np.where(np.isfinite(clean_eval_paths[i]), clean_eval_paths[i], -np.inf))
            for i in range(n_eval)
        ])
        aucpr = {}
        for frac in (0.25, 0.50, 0.75):
            cut = max(1, int(np.ceil(frac * T)))
            inj_max = np.concatenate([
                np.array([np.nanmax(np.where(np.isfinite(p[:cut]), p[:cut], -np.inf))
                          for p in path_pool[key]])
                for key in auc_inj_idx
            ]) if n_eval else np.array([np.nan])
            aucpr[str(frac)] = mscoring.partial_auc_pr(auc_clean, inj_max)
        aucpr_per_level = {
            lv.level_id: mscoring.partial_auc_pr(
                auc_clean,
                np.array([np.nanmax(np.where(np.isfinite(p), p, -np.inf))
                          for p in path_pool[f"{lv.level_id}/{sev.ACUTE_FAMILY}/ndvi"]]),
            ) for lv in levels
        }

        # Clean event-level FAR (every event false — no injection windows).
        clean_efar_eval = mscoring.event_far_from_paths(
            clean_eval_paths, [None] * n_eval, tau, gap=2,
        )
        clean_efar_calib = mscoring.event_far_from_paths(
            clean_paths_all[calib_idx], [None] * n_calib, tau, gap=2,
        )

        # Masked NRMSE per band on clean dev (descriptive; not part of the
        # detection protocol — computed over all clean dev as in finding 16).
        nrmse = mscoring.masked_nrmse_per_band(
            clean["pred_raw"], X, M, norm_robust_range(norm, scorer),
        )
        nrmse_valid = nrmse[np.isfinite(nrmse)]

        # Per-phase breakdown pooled over the acute/ndvi cells (the primary
        # index/family) — onset phases rotate deterministically per round.
        per_phase: dict[str, dict] = {}
        phase_flags: dict[str, list[int]] = {}
        for rnd in range(max(1, args.rounds)):
            results = mpert.inject_index_drop_dataset(
                Xe, Me, level_id="S3", family=sev.ACUTE_FAMILY, index="ndvi", round_idx=rnd,
            )
            for j, r in enumerate(results):
                phase_flags.setdefault(r.phase, []).append(det_pools[f"S3/{sev.ACUTE_FAMILY}/ndvi"][rnd * n_eval + j])
        for ph, flags in phase_flags.items():
            nd_ = int(sum(flags))
            lo, hi = mscoring.wilson_ci(nd_, len(flags))
            per_phase[ph] = {"n": len(flags), "n_detected": nd_,
                             "detection_rate": nd_ / max(1, len(flags)), "wilson_ci95": [lo, hi]}

        # Injection % summary (of each field's own grand-growth median).
        pct_summary = {}
        for rnd in range(max(1, args.rounds)):
            results = mpert.inject_index_drop_dataset(
                Xe, Me, level_id="S3", family=sev.ACUTE_FAMILY, index="ndvi", round_idx=rnd,
            )
            pcts = [r.meta["pct_of_field_median"] for r in results if r.meta["pct_of_field_median"] is not None]
            pct_summary = {"median_pct_of_field_grand_growth_median": float(np.median(pcts)) if pcts else None,
                           "n": len(pcts)}

        per_seed.append({
            "seed": seed,
            "tau": float(tau), "k": int(k),
            "far_target": args.far, "far_achieved": float(threshold.far_achieved),
            "threshold_per_k": per_k,
            "alarm_statistic": "trailing3_window_channel_max_z2_cell_q95_normalized",
            "per_bin_q95": [round(float(v), 6) for row in cell_q95 for v in row],
            "mdm80": mdm80,
            "cells": cells,
            "event_far_clean_eval": clean_efar_eval,
            "event_far_clean_calibration": clean_efar_calib,
            "aucpr_partial": aucpr,
            "aucpr_per_level_acute_ndvi": aucpr_per_level,
            "per_phase_S3_acute_ndvi": per_phase,
            "pct_of_field_median_summary": pct_summary,
            "nrmse_per_band": {b: float(nrmse[i]) for i, b in enumerate(BAND_NAMES[:C])},
            "nrmse_mean": float(np.mean(nrmse_valid)) if nrmse_valid.size else float("nan"),
            "params": params,
            "n_calib_cycles": n_calib, "n_eval_cycles": n_eval,
            "n_injected_total": int(sum(c["n"] for c in cells.values())),
        })

        mdm_str = " ".join(f"{kk}={vv['value']}" for kk, vv in mdm80.items())
        print(f"[seed {seed}] tau={tau:.4f} k={k} far={threshold.far_achieved:.3f} MDM80 {mdm_str}")

    return {
        "protocol": "severity_sweep_v1",
        "shapes": families,
        "scorer": args.scorer,
        "severity_table_sha256": table_hash,
        "eval_subset_sha256": eval_hash,
        "n_calib_cycles": n_calib,
        "n_eval_cycles": n_eval,
        "mdm80_target": MDM80_TARGET,
        "cells_order": cells_all,
        "per_seed": per_seed,
        "seeds": seeds,
    }, per_seed


def run_patch_severity_protocol(args: argparse.Namespace, manifest: dict, sel: dict,
                                seeds: list[str], device: str,
                                data: dict | None = None) -> tuple[dict, list]:
    """The severity sweep for a PATCH arm (``patch_cnn_gru`` / control).

    The cells, the severity table, the shapes and the MDM80 rule are the ones
    the field-level arms use — only the scoring path differs, and it differs in
    exactly two documented ways:

    * The tensors come from ``patches.zarr`` joined on ``(field_id, cycle_id)``
      (``patch_eval.patch_batch_for_cycles``), never by row position.
    * The alarm path is an empirical p-value against the CALIBRATION subset's
      clean paths (``PatchArmScorer``), because the two arms' raw statistics are
      not on a common scale and a shared tau would be an artefact of units.

    The split partition is the SAME hash partition, so the evaluation subset is
    identical to the one the field-level runs used.
    """
    from ssl_anomaly.monitor import patch_eval as pE

    store_path = Path(args.patch_store) if args.patch_store else (
        REPO_ROOT / "data" / "processed" / "patches.zarr")
    if not store_path.exists():
        raise SystemExit(
            f"patch store not found: {store_path} — the patch arm needs patches.zarr "
            "(owner runs scripts/extract_patches.py; this is a data task, not a code task)"
        )
    from ssl_anomaly.io import patches as P

    root = P.open_store(store_path)
    epoch = np.datetime64(P.validate_locked_patch_store(root, manifest), "D")
    patch_run = args.patch_run or args.run_id
    holdout = mholdout.load_holdout_manifest(path=args.holdout_manifest)
    mholdout.assert_frozen_holdout_matches_splits(holdout, manifest)

    cycle_keys = list(sel["cycle_keys"])
    msplits.assert_no_test_cycles(cycle_keys, manifest, context="patch dev evaluation")
    if not set(cycle_keys) <= set(manifest["cycles"]["dev"]):
        raise ValueError("patch dev evaluation only accepts locked dev cycle keys")
    index = P.patch_cycle_index(root)
    for key, start, end in zip(cycle_keys, sel["start_dates"], sel["end_dates"], strict=True):
        cycle = index.get(key)
        if cycle is None:
            raise ValueError(f"requested dev patch cycle {key} is not in the store")
        if (epoch + np.timedelta64(cycle.start_day, "D") != np.datetime64(start, "D")
                or epoch + np.timedelta64(cycle.end_day + 1, "D") != np.datetime64(end, "D")):
            raise ValueError(f"patch bounds for {key} disagree with the locked dev cycle")
    fids = [index[key].field_id for key in cycle_keys]
    cids = [index[key].cycle_id for key in cycle_keys]

    model, sigma, norm, cfg = load_patch_artifacts(
        patch_run, checkpoint_path=args.patch_checkpoint, norm_path=args.patch_norm,
        sigma_path=args.patch_sigma,
    )
    if seeds != [cfg.get("seed")]:
        raise ValueError("patch evaluation requires exactly the seed in the checkpoint")
    if cfg.get("smoke") and not args.smoke:
        raise ValueError("smoke-trained patch weights can only be scored with --smoke")
    P.validate_patch_norm_binding(root, norm, manifest, holdout)
    batch = pE.patch_batch_for_cycles(root, fids, cids, norm=norm)

    calib_idx, eval_idx, eval_hash = partition_calib_eval(cycle_keys)
    print(f"[patch-severity] {len(cycle_keys)} dev cycles joined to the store; "
          f"calibration n={len(calib_idx)}, evaluation n={len(eval_idx)} (hash {eval_hash})")

    scorer = build_patch_arm(args.scorer, model, cfg, device, sigma=sigma,
                             in_field=batch["in_field"])
    # evaluate_subset slices -> each sample's in-field mask row must be named
    row_of_sample = np.arange(len(cycle_keys))
    ref_paths = pE.patch_reference_paths(
        scorer, batch, reference_idx=np.asarray(calib_idx),
        field_row=row_of_sample,
    )
    arm = mpscores.PatchArmScorer(scorer, ref_paths)
    tau, k = 0.05, 1          # p-value scale: tau on the -log10(p) path
    print(f"[patch-severity] reference paths: {ref_paths.shape}; "
          f"alarm path = -log(empirical p) against the calibration subset")

    levels = sev.load_table()
    families = [f.strip() for f in str(args.shapes).split(",") if f.strip()]
    eval_batch = {key: value[eval_idx] if isinstance(value, np.ndarray) else value
                  for key, value in batch.items()}
    cells: dict[str, dict] = {}
    for lv in levels:
        for fam in families:
            for index in ("ndvi", "savi"):
                key = f"{lv.level_id}/{fam}/{index}"
                det_flags: list[int] = []
                delays: list[float] = []
                for rnd in range(max(1, args.rounds)):
                    cell = pE.patch_arm_scores(
                        arm, eval_batch,
                        level_id=lv.level_id, family=fam, index=index, round_idx=rnd,
                        field_row=row_of_sample[eval_idx],
                    )
                    # -log10(p) is already the standardized path (p is uniform on
                    # clean data, so q95(=-log10 0.05) normalizes it exactly);
                    # the channel axis is a single channel and the mask is the
                    # one the scorer used.
                    paths = -np.log10(np.clip(cell["p_value"], 1e-12, 1.0))[:, :, None]
                    q95 = np.full((paths.shape[1], 1), -np.log10(0.05))
                    inj_paths = mscoring.cumulative_channel_max(
                        paths,
                        np.repeat(cell["observed"][:, :, None], 1, axis=2),
                        q95,
                    )
                    for j in range(inj_paths.shape[0]):
                        fb = mscoring.first_alarm_bin(inj_paths[j], tau, k, 0)
                        det_flags.append(1 if fb >= 0 else 0)
                        if fb >= 0:
                            delays.append(float(fb * 15))
                n = len(det_flags)
                n_det = int(sum(det_flags))
                lo, hi = mscoring.wilson_ci(n_det, n)
                cells[key] = {
                    "n": n, "n_detected": n_det, "detection_rate": n_det / max(1, n),
                    "wilson_ci95": [round(lo, 4), round(hi, 4)],
                    "median_delay_days": float(np.median(delays)) if delays else None,
                    "level_id": lv.level_id, "family": fam, "index": index,
                    "delta_ndvi": lv.delta_ndvi,
                }

    mdm80: dict[str, dict] = {}
    for fam in families:
        for index in ("ndvi", "savi"):
            reached = next((lv.level_id for lv in levels
                            if cells[f"{lv.level_id}/{fam}/{index}"]["detection_rate"]
                            >= MDM80_TARGET), None)
            mdm80[f"{fam}/{index}"] = (
                {"value": ">S6", "sentinel": MDM80_CENSORED, "censored": True,
                 "level_cell": None, "median_delay_days": None}
                if reached is None else
                {"value": reached, "sentinel": int(reached[1:]), "censored": False,
                 "level_cell": f"{reached}/{fam}/{index}",
                 "median_delay_days": cells[f"{reached}/{fam}/{index}"]["median_delay_days"],
                 "detection_rate_at_mdm": cells[f"{reached}/{fam}/{index}"]["detection_rate"]}
            )

    per_seed = [{
        "seed": int(seeds[0]) if seeds else 0,
        "tau": float(tau), "k": int(k),
        "alarm_statistic": "neg_log_empirical_p_vs_calibration_subset",
        "mdm80": mdm80, "cells": cells,
        "patch_sigma_sha256": sigma.sha256,
        "patch_norm_sha256": norm["sha256"],
        "unnormalized_channels": batch["unnormalized_channels"],
        "holdout_sha256": holdout["manifest_sha256"],
        "params": sum(p.numel() for p in model.parameters()),
        "patch_run": str(args.patch_checkpoint or patch_run),
        "axis": "patch-level representation (per-pixel, in-field aggregation)",
        "n_calib_cycles": len(calib_idx), "n_eval_cycles": len(eval_idx),
        "n_injected_total": int(sum(c["n"] for c in cells.values())),
    }]
    return {
        "protocol": "severity_sweep_patch_v1",
        "input_protocol": cfg["input_protocol"],
        "n_channels": cfg["n_channels"],
        "shapes": families, "scorer": args.scorer,
        "eval_subset_sha256": eval_hash,
        "n_calib_cycles": len(calib_idx), "n_eval_cycles": len(eval_idx),
        "mdm80_target": MDM80_TARGET,
        "cells_order": [f"{lv.level_id}/{fam}/{idx}" for lv in levels
                        for fam in families for idx in ("ndvi", "savi")],
        "severity_table_sha256": sev.severity_table_hash(),
        "per_seed": per_seed, "seeds": seeds,
    }, per_seed


def aggregate_severity(per_seed: list[dict]) -> dict:
    """Seed aggregation for the severity protocol (mean ± std of the MDM80
    sentinels; pooled per-level detection with Wilson CIs)."""
    mdm_mean = {}
    fams: list[str] = []
    for r in per_seed:
        for key in r["mdm80"]:
            fam = key.split("/")[0]
            if fam not in fams:
                fams.append(fam)
    for fam in fams:
        for index in ("ndvi", "savi"):
            key = f"{fam}/{index}"
            if key not in per_seed[0]["mdm80"]:
                continue
            vals = [r["mdm80"][key]["sentinel"] for r in per_seed]
            labels = [r["mdm80"][key]["value"] for r in per_seed]
            mean, std = mproto.mean_std([float(v) for v in vals])
            mdm_mean[key] = {
                "mean_sentinel": mean, "std_sentinel": std,
                "per_seed_labels": labels,
                "n_censored": int(sum(1 for v in vals if v == MDM80_CENSORED)),
            }
    return {"mdm80": mdm_mean}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    t0 = time.time()
    patch = args.scorer in PATCH_SCORERS
    if patch and (args.model != args.scorer or args.protocol != "severity"):
        raise SystemExit("patch scoring needs matching --model/--scorer and --protocol severity")
    if args.model in PATCH_SCORERS and not patch:
        raise SystemExit("patch models require a patch --scorer")
    seeds = [int(s) for s in args.seeds.split(",")]
    device = args.device or ("cuda" if _cuda() else "cpu")

    manifest = msplits.load_splits_locked()
    data = minputs.load_masked_cycles()
    sel = mproto.select_splits(data, manifest, splits=("dev",))

    if args.protocol == "severity":
        sev_metrics, per_seed = run_severity_protocol(args, manifest, sel, seeds, device, data=data)

        # ---- Aggregate over seeds -------------------------------------------
        wall = time.time() - t0
        agg = aggregate_severity(per_seed)
        N = int(sev_metrics["n_calib_cycles"] + sev_metrics["n_eval_cycles"])
        channel_count = sev_metrics["n_channels"] if patch else len(per_seed[0]["nrmse_per_band"])
        metrics = {
            "run_id": args.run_id,
            "model_id": args.model,
            "protocol": sev_metrics["protocol"],
            "scorer": args.scorer,
            "bank_variant": (f"{args.bank_distance}{args.bank_k}" if args.scorer == "bank" else None),
            "severity_table_sha256": sev_metrics["severity_table_sha256"],
            "eval_subset_sha256": sev_metrics["eval_subset_sha256"],
            "ladder_rung": "engineering_smoke_only" if patch and args.smoke else "L2",
            **({"input_protocol": sev_metrics["input_protocol"]} if patch else {}),
            "patch_run": (per_seed[0].get("patch_run") if per_seed else None),
            "patch_sigma_sha256": (per_seed[0].get("patch_sigma_sha256")
                                   if per_seed else None),
            "claim_noun": "synthetic anomaly",
            "data_source": "real490 (masked rebuild from stats.zarr)",
            "splits_locked_sha256": manifest["manifest_sha256"],
            "git_sha": mproto.git_sha(),
            "seeds": seeds,
            "device": device,
            "wall_time_s": round(wall, 1),
            "far_target": args.far,
            "date_range": {
                "first": str(sel["start_dates"][0])[:10],
                "last": str(sel["end_dates"][-1])[:10],
            },
            "n_dev_cycles": N,
            "n_calib_cycles": sev_metrics["n_calib_cycles"],
            "n_eval_cycles": sev_metrics["n_eval_cycles"],
            "channel_count": channel_count,
            "mdm80_target": MDM80_TARGET,
            "mdm80": agg["mdm80"],
            "smoke": bool(args.smoke),
            "notes": args.notes,
            "per_seed": per_seed,
        }
        out_dir = mproto.DEV_DIR / args.run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = f"_sev_{args.scorer}"
        if args.scorer == "bank":
            suffix += f"_{args.bank_distance}{args.bank_k}"
        if args.smoke:
            suffix += "_smoke"
        out_path = out_dir / f"metrics_{args.model}{suffix}.json"
        if patch:
            # A repeated patch run gets an explicit new id, never a replaced report.
            with out_path.open("x", encoding="utf-8") as output:
                json.dump(metrics, output, indent=2, allow_nan=False)
        else:
            out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        if patch and not args.smoke:
            # The patch score has a different calibration/report contract. Do not
            # append invented field-level FAR, AUPRC, or NRMSE to the dev log.
            print("[dev_log] patch report only; full patch PoC metrics and review are pending")
        if not args.smoke and not patch:
            primary_key = f"{sev.ACUTE_FAMILY}/ndvi"
            mdm_vals = [r["mdm80"][primary_key]["sentinel"] for r in per_seed]
            mdm_mean, mdm_std = mproto.mean_std([float(v) for v in mdm_vals])
            far_max = max(r["far_achieved"] for r in per_seed)
            variant = f"_{args.bank_distance}{args.bank_k}" if args.scorer == "bank" else ""
            row = {
                "run_id": f"{args.run_id}:{args.model}:sev_{args.scorer}{variant}",
                "date": time.strftime("%Y-%m-%d"),
                "model_id": args.model,
                "parent_run_id": "",
                "change_description": "severity sweep S1-S6 (literature-grounded protocol)"
                                      + (f"; {args.notes}" if args.notes else ""),
                "config_hash": mproto.config_hash({
                    "model": args.model, "run_id": args.run_id, "protocol": "severity",
                    "scorer": args.scorer, "rounds": args.rounds, "bank_k": args.bank_k,
                    "bank_distance": args.bank_distance,
                }),
                "seeds": ";".join(str(s) for s in seeds),
                "n_train_cycles": _n_train(manifest),
                "n_dev_cycles": N,
                "primary_metric_mean": round(mdm_mean, 4),
                "primary_metric_std": round(mdm_std, 4),
                "median_delay_days": "",
                "far_target": args.far,
                "far_achieved": round(float(far_max), 4),
                "tau": round(float(np.mean([r["tau"] for r in per_seed])), 4),
                "k": int(np.bincount([r["k"] for r in per_seed]).argmax()),
                "aucpr_25": round(float(np.mean([r["aucpr_partial"]["0.25"] for r in per_seed])), 4),
                "aucpr_50": round(float(np.mean([r["aucpr_partial"]["0.5"] for r in per_seed])), 4),
                "aucpr_75": round(float(np.mean([r["aucpr_partial"]["0.75"] for r in per_seed])), 4),
                "nrmse_mean": round(float(np.mean([r["nrmse_mean"] for r in per_seed
                                                    if np.isfinite(r["nrmse_mean"])])), 4),
                "severity_0p5": "", "severity_1p5": "", "severity_2": "",
                "params": max([r["params"] for r in per_seed]),
                "wall_time_s": round(wall, 1),
                "device": device,
                "git_sha": mproto.git_sha(),
                "data_source": "real490",
                "splits_sha256": manifest["manifest_sha256"],
                "ladder_rung": "L2",
                "patch_run": (per_seed[0].get("patch_run") if per_seed else None),
                "patch_sigma_sha256": (per_seed[0].get("patch_sigma_sha256")
                                       if per_seed else None),
                "protocol": "severity_sweep_patch_v1" if args.scorer in PATCH_SCORERS
                            else "severity_sweep_v1",
                "shapes": sev_metrics["shapes"],
                "scorer": args.scorer,
                "severity_table_sha256": sev_metrics["severity_table_sha256"],
                "eval_subset_sha256": sev_metrics["eval_subset_sha256"],
                "mdm80": json.dumps({k: v["per_seed_labels"] for k, v in agg["mdm80"].items()},
                                    sort_keys=True),
                "notes": args.notes,
            }
            mproto.append_dev_log(row)
            print(f"[dev_log] appended row for {row['run_id']}")

        print(f"[done] metrics → {out_path} (wall {time.time() - t0:.1f}s)")
        return 0

    # ------------------------------------------------------------------
    # LEGACY protocol (finding-16 continuity; flagged "legacy")
    # ------------------------------------------------------------------
    X, M = sel["X"], sel["M"]
    doy = minputs.doy_channels(sel["harvest_days"])
    N, T, C = X.shape

    norm = None
    if args.model != "b1":
        norm_path = mproto.DEV_DIR / args.run_id / "norm_stats.npz"
        norm = minputs.load_norm(norm_path)

    if args.smoke:
        rng0 = np.random.default_rng(7)
        keep = rng0.choice(N, size=min(12, N), replace=False)
        X, M, doy = X[keep], M[keep], doy[keep]
        seeds = seeds[:1]
        args.rounds = 1
        args.n_per_stratum = 2
        N = len(keep)

    # Ablation runs (no-LST) carry fewer channels: slice X/M to the
    # checkpoint's channel count (order preserved; dropped channels are the
    # trailing lst). channel_count recorded in metrics.
    probe_scorer, _, probe_channels = load_scorer(args.model, seeds[0], args.run_id, device)
    channel_count = probe_channels
    if channel_count < X.shape[2]:
        X, M = X[:, :, :channel_count], M[:, :, :channel_count]
    N, T, C = X.shape
    print(f"[eval:legacy] channels={channel_count}, dev cycles={N}, rounds={args.rounds}")

    # Perturbation types touching a dropped channel (no-LST ablation) cannot
    # be injected: restrict to types whose channels all exist.
    usable_types = tuple(
        pt for pt in mpert.INTERIM_TYPES if all(ch < C for ch in mpert.TYPE_CHANNELS[pt])
    )
    dropped_types = [pt for pt in mpert.INTERIM_TYPES if pt not in usable_types]
    if dropped_types:
        print(f"[eval:legacy] dropped-channel injections skipped: {dropped_types}")

    cfg_pert = mpert.PerturbationConfig(types=usable_types, n_per_stratum=args.n_per_stratum)
    per_seed: list[dict] = []

    for seed in seeds:
        scorer, params, _ = load_scorer(args.model, seed, args.run_id, device)

        # ---- Clean dev scores (calibration + NRMSE) -----------------------
        clean = score_cycles(scorer, X, M, doy, norm)
        clean_pred_raw = clean["pred_raw"]

        # ---- Injected dev cycles ------------------------------------------
        inj_z2: list[np.ndarray] = []
        inj_masks: list[np.ndarray] = []
        inj_mean: list[np.ndarray] = []
        inj_meta: list[dict] = []
        for rnd in range(args.rounds):
            rng = np.random.default_rng(10_000 + seed * 97 + rnd)
            results = mpert.inject_dataset(X, M, norm_scale_or_mad(norm, scorer), cfg_pert, rng)
            Xinj = np.stack([r.x for r in results])
            Minj = np.stack([r.m for r in results])
            doy_inj = doy[[r.source_row for r in results]]
            s_inj = score_cycles(scorer, Xinj, Minj, doy_inj, norm)
            for j, r in enumerate(results):
                inj_z2.append(s_inj["z2"][j])
                inj_masks.append(r.m)
                inj_mean.append(s_inj["mean"][j])
                inj_meta.append({
                    "type": r.pert_type, "severity": float(r.severity),
                    "phase": r.phase, "onset_bin": int(r.onset_bin),
                })

        # ---- Alarm statistic (dev-loop change #2) ---------------------------
        # Cumulative channel-max: per-(bin,channel) z² normalized by the
        # clean-dev cell q95, accumulated as a running mean over bins ≤ t,
        # maxed over channels (change #1's cycle-max was dominated by null
        # heavy-tail bins; the paired diagnostic showed even +2.6 onset jumps
        # never lifted the cycle max). The D5 mean-z² stays as a secondary.
        cell_q95 = mscoring.cell_q95_normalizer(clean["z2"], M)
        clean_paths = mscoring.cumulative_channel_max(clean["z2"], M, cell_q95)
        inj_paths = mscoring.cumulative_channel_max(
            np.stack(inj_z2), np.stack(inj_masks), cell_q95,
        )
        clean_norm_list = [clean_paths[i] for i in range(N)]
        inj_norm_list = [inj_paths[j] for j in range(len(inj_meta))]

        # ---- Threshold calibration on clean dev ---------------------------
        sev1_idx = [j for j, meta in enumerate(inj_meta) if abs(meta["severity"] - 1.0) < 1e-9]
        threshold, per_k = mscoring.choose_threshold(
            clean_norm_list,
            [inj_norm_list[j] for j in sev1_idx],
            [inj_meta[j]["onset_bin"] for j in sev1_idx],
            far_target=args.far,
        )
        tau, k = threshold.tau, threshold.k

        # Secondary: D5 mean-z² statistic with its own global calibration
        # (kept for continuity and comparison).
        mean_thr, mean_far = mscoring.calibrate_threshold(
            [clean["mean"][i] for i in range(N)], k=1, far_target=args.far,
        )
        mean_det1 = float(np.mean([
            mscoring.first_alarm_bin(inj_mean[j], mean_thr, 1, inj_meta[j]["onset_bin"]) >= 0
            for j in sev1_idx
        ])) if sev1_idx else float("nan")

        # ---- Detection metrics --------------------------------------------
        def detect_at(sev_: float | None) -> tuple[float, float, list[float]]:
            idx = [j for j, meta in enumerate(inj_meta)
                   if (sev_ is None or abs(meta["severity"] - sev_) < 1e-9)]
            delays = []
            det = 0
            for j in idx:
                fb = mscoring.first_alarm_bin(inj_norm_list[j], tau, k, inj_meta[j]["onset_bin"])
                if fb >= 0:
                    det += 1
                    delays.append((fb - inj_meta[j]["onset_bin"]) * 15)
            rate = det / max(1, len(idx))
            med_delay = float(np.median(delays)) if delays else float("nan")
            return rate, med_delay, delays

        det1, delay1, _ = detect_at(1.0)
        det_all, _, _ = detect_at(None)

        # Severity curve.
        severity_curve = {}
        for sev_ in mpert.SEVERITIES:
            r, dmed, _ = detect_at(sev_)
            severity_curve[str(sev_)] = {"detection_rate": r, "median_delay_days": dmed}

        # Per-type and per-phase tables at 1×MAD.
        per_type: dict[str, dict] = {}
        per_phase: dict[str, dict] = {}
        for ptype in mpert.INTERIM_TYPES:
            idx = [j for j in sev1_idx if inj_meta[j]["type"] == ptype]
            if idx:
                r, dmed, _ = _rate_delay(inj_norm_list, inj_meta, idx, tau, k)
            else:
                r, dmed = float("nan"), float("nan")
            per_type[ptype] = {"n": len(idx), "detection_rate": r, "median_delay_days": dmed}
        for ph in mpert.PHASES:
            idx = [j for j in sev1_idx if inj_meta[j]["phase"] == ph]
            if idx:
                r, dmed, _ = _rate_delay(inj_norm_list, inj_meta, idx, tau, k)
            else:
                r, dmed = float("nan"), float("nan")
            per_phase[ph] = {"n": len(idx), "detection_rate": r, "median_delay_days": dmed}

        # ---- Partial-cycle AUC-PR (1×MAD vs clean) -------------------------
        aucpr = {}
        for frac in (0.25, 0.50, 0.75):
            cut = max(1, int(np.ceil(frac * T)))
            clean_max = np.array([
                np.nanmax(np.where(np.isfinite(s[:cut]), s[:cut], -np.inf)) for s in clean_norm_list
            ])
            inj_max = np.array([
                np.nanmax(np.where(np.isfinite(inj_norm_list[j][:cut]), inj_norm_list[j][:cut], -np.inf))
                for j in sev1_idx
            ])
            aucpr[str(frac)] = mscoring.partial_auc_pr(clean_max, inj_max)

        # ---- Masked NRMSE per band (clean dev, raw units) ------------------
        nrmse = mscoring.masked_nrmse_per_band(
            clean_pred_raw, X, M, norm_robust_range(norm, scorer),
        )
        nrmse_valid = nrmse[np.isfinite(nrmse)]

        # Secondary mean-z² statistic summary on clean dev.
        mean_clean = clean["mean"][np.isfinite(clean["mean"])]

        per_seed.append({
            "seed": seed,
            "tau": float(tau), "k": int(k),
            "far_target": args.far, "far_achieved": float(threshold.far_achieved),
            "threshold_per_k": per_k,
            "alarm_statistic": "trailing3_window_channel_max_z2_cell_q95_normalized",
            "per_bin_q95": [round(float(v), 6) for row in cell_q95 for v in row],
            "secondary_mean_statistic": {
                "tau_k1_far5pct": float(mean_thr),
                "far_achieved": float(mean_far),
                "detection_rate_1mad": mean_det1,
                "clean_q95": float(np.nanpercentile(mean_clean, 95)),
            },
            "detection_rate_1mad": det1,
            "detection_rate_all_severities": det_all,
            "median_delay_days_1mad": delay1,
            "severity_curve": severity_curve,
            "per_type_1mad": per_type,
            "per_phase_1mad": per_phase,
            "aucpr_partial": aucpr,
            "nrmse_per_band": {b: float(nrmse[i]) for i, b in enumerate(BAND_NAMES[:C])},
            "nrmse_mean": float(np.mean(nrmse_valid)) if nrmse_valid.size else float("nan"),
            "params": params,
            "n_clean": int(N), "n_injected": len(inj_meta), "n_injected_1mad": len(sev1_idx),
        })

        # ---- Extended-severity diagnostic (non-protocol, todo OQ6) ---------
        # The protocol severities (0.5–2×MAD) showed no dynamic range: natural
        # outlier cycles consume the 5 % FAR budget (methods §24). This block
        # sweeps 4/6/8×MAD with the SAME frozen (τ, k) to answer "where does
        # detection start?" — the number the advisor question needs.
        extended = {}
        if args.extended_severity and not args.smoke:
            for sev_ext in (4.0, 6.0, 8.0):
                rng_e = np.random.default_rng(20_000 + seed * 131 + int(sev_ext))
                cfg_e = mpert.PerturbationConfig(
                    types=usable_types, severities=(sev_ext,),
                    phases=mpert.PHASES, durations=(2, 3, 5),
                    n_per_stratum=min(N, args.n_per_stratum),
                )
                det_e, delays_e, n_e = 0, [], 0
                for rnd in range(max(2, args.rounds // 2)):
                    results = mpert.inject_dataset(X, M, norm_scale_or_mad(norm, scorer), cfg_e, rng_e)
                    Xinj_e = np.stack([r.x for r in results])
                    Minj_e = np.stack([r.m for r in results])
                    doy_e = doy[[r.source_row for r in results]]
                    z2_e = score_cycles(scorer, Xinj_e, Minj_e, doy_e, norm)["z2"]
                    paths_e = mscoring.cumulative_channel_max(z2_e, Minj_e, cell_q95)
                    for j, r in enumerate(results):
                        n_e += 1
                        fb = mscoring.first_alarm_bin(paths_e[j], tau, k, r.onset_bin)
                        if fb >= 0:
                            det_e += 1
                            delays_e.append((fb - r.onset_bin) * 15)
                extended[str(sev_ext)] = {
                    "detection_rate": det_e / max(1, n_e),
                    "median_delay_days": float(np.median(delays_e)) if delays_e else float("nan"),
                    "n_injected": n_e,
                }
            per_seed[-1]["extended_severity_diagnostic"] = extended
            print(f"[seed {seed}] extended severity: "
                  + " ".join(f"{s}xMAD={v['detection_rate']:.2f}" for s, v in extended.items()))
        print(f"[seed {seed}] det@1MAD={det1:.3f} delay={delay1:.0f}d tau={tau:.4f} k={k} "
              f"far={threshold.far_achieved:.3f} aucpr50={aucpr['0.5']:.3f} "
              f"(mean-stat secondary det {mean_det1:.3f})")

    # ---- Aggregate over seeds ----------------------------------------------
    det_vals = [r["detection_rate_1mad"] for r in per_seed]
    det_mean, det_std = mproto.mean_std(det_vals)
    delay_vals = [r["median_delay_days_1mad"] for r in per_seed if np.isfinite(r["median_delay_days_1mad"])]
    delay_mean, delay_std = mproto.mean_std(delay_vals) if delay_vals else (float("nan"), 0.0)

    wall = time.time() - t0
    metrics = {
        "run_id": args.run_id,
        "model_id": args.model,
        "protocol": "legacy_mad_scaled_v1",
        "ladder_rung": "L2",
        "data_source": "real490 (masked rebuild from stats.zarr)",
        "splits_locked_sha256": manifest["manifest_sha256"],
        "git_sha": mproto.git_sha(),
        "seeds": seeds,
        "device": device,
        "wall_time_s": round(wall, 1),
        "far_target": args.far,
        "date_range": {
            "first": str(sel["start_dates"][0])[:10],
            "last": str(sel["end_dates"][-1])[:10],
        },
        "n_dev_cycles": int(N),
        "channel_count": int(channel_count),
        "n_injected_total": sum(r["n_injected"] for r in per_seed),
        "primary": {
            "name": "detection_rate_at_1MAD",
            "mean": det_mean, "std": det_std,
            "per_seed": det_vals,
        },
        "median_delay_days": {"mean": delay_mean, "std": delay_std},
        "per_seed": per_seed,
        "smoke": bool(args.smoke),
        "notes": args.notes,
    }
    out_dir = mproto.DEV_DIR / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "_smoke" if args.smoke else ""
    out_path = out_dir / f"metrics_{args.model}{suffix}.json"
    out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    if not args.smoke:
        nrmse_vals = [r["nrmse_mean"] for r in per_seed if np.isfinite(r["nrmse_mean"])]
        nrmse_mean = float(np.mean(nrmse_vals)) if nrmse_vals else float("nan")
        auc50 = [r["aucpr_partial"]["0.5"] for r in per_seed if np.isfinite(r["aucpr_partial"]["0.5"])]
        row = {
            "run_id": f"{args.run_id}:{args.model}",
            "date": time.strftime("%Y-%m-%d"),
            "model_id": args.model,
            "parent_run_id": "",
            "change_description": "legacy MAD-scaled continuity (finding 16)"
                                  + (f"; {args.notes}" if args.notes else ""),
            "config_hash": mproto.config_hash({"model": args.model, "run_id": args.run_id,
                                               "protocol": "legacy"}),
            "seeds": ";".join(str(s) for s in seeds),
            "n_train_cycles": _n_train(manifest),
            "n_dev_cycles": int(N),
            "primary_metric_mean": round(det_mean, 4),
            "primary_metric_std": round(det_std, 4),
            "median_delay_days": round(delay_mean, 1) if np.isfinite(delay_mean) else "",
            "far_target": args.far,
            "far_achieved": round(float(np.max([r["far_achieved"] for r in per_seed])), 4),
            "tau": round(float(np.mean([r["tau"] for r in per_seed])), 4),
            "k": int(np.bincount([r["k"] for r in per_seed]).argmax()),
            "aucpr_25": round(float(np.mean([r["aucpr_partial"]["0.25"] for r in per_seed])), 4),
            "aucpr_50": round(float(np.mean(auc50)), 4) if auc50 else "",
            "aucpr_75": round(float(np.mean([r["aucpr_partial"]["0.75"] for r in per_seed])), 4),
            "nrmse_mean": round(nrmse_mean, 4) if np.isfinite(nrmse_mean) else "",
            "severity_0p5": round(float(np.mean([r["severity_curve"]["0.5"]["detection_rate"] for r in per_seed])), 4),
            "severity_1p5": round(float(np.mean([r["severity_curve"]["1.5"]["detection_rate"] for r in per_seed])), 4),
            "severity_2": round(float(np.mean([r["severity_curve"]["2.0"]["detection_rate"] for r in per_seed])), 4),
            "params": max([r["params"] for r in per_seed]),
            "wall_time_s": round(wall, 1),
            "device": device,
            "git_sha": mproto.git_sha(),
            "data_source": "real490",
            "splits_sha256": manifest["manifest_sha256"],
            "ladder_rung": "L2",
            "patch_run": (per_seed[0].get("patch_run") if per_seed else None),
            "patch_sigma_sha256": (per_seed[0].get("patch_sigma_sha256")
                                   if per_seed else None),
            "protocol": "legacy_mad_scaled_v1",
            "scorer": "recon_only",
            "severity_table_sha256": "",
            "eval_subset_sha256": "",
            "mdm80": "",
            "notes": args.notes,
        }
        mproto.append_dev_log(row)
        print(f"[dev_log] appended row for {row['run_id']}")

    print(f"[done] metrics → {out_path} (wall {wall:.1f}s)")
    return 0


def _rate_delay(inj_scores, inj_meta, idx, tau, k) -> tuple[float, float, list[float]]:
    det, delays = 0, []
    for j in idx:
        fb = mscoring.first_alarm_bin(inj_scores[j], tau, k, inj_meta[j]["onset_bin"])
        if fb >= 0:
            det += 1
            delays.append((fb - inj_meta[j]["onset_bin"]) * 15)
    rate = det / max(1, len(idx))
    return rate, (float(np.median(delays)) if delays else float("nan")), delays


def norm_scale_or_mad(norm: dict | None, scorer) -> np.ndarray:
    """The (T, C) scale array (= MAD × 1.4826) used to size perturbations.

    Deep runs use the train-fit stats sidecar; B1 carries its own stats.
    (Legacy protocol only — the severity protocol uses absolute deltas.)
    """
    if norm is not None:
        return norm["scale"]
    return scorer.scale[0] if scorer.scale.ndim == 3 else scorer.scale


def norm_robust_range(norm: dict | None, scorer) -> np.ndarray:
    if norm is not None:
        return norm["robust_range"]
    if scorer.robust_range is not None:
        return scorer.robust_range
    return np.ones(scorer.scale.shape[-1])


def _n_train(manifest: dict) -> int:
    return int(manifest["counts"]["train"])


def _cuda() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


if __name__ == "__main__":
    raise SystemExit(main())
