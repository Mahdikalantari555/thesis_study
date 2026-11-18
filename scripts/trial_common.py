"""Shared harness for the predictive-SSL controlled trial part scripts
(change predictive-ssl-controlled-trial).

Keeps arm-loading, partition and calibration logic in ONE place so parts A–D
score every arm through identical code paths. Read-only over the frozen
artifacts; trial outputs land under reports/dev/<trial run id>/ only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import inputs as minputs  # noqa: E402
from ssl_anomaly.monitor import models as mmodels  # noqa: E402
from ssl_anomaly.monitor import protocol as mproto  # noqa: E402
from ssl_anomaly.monitor import scoring as mscoring  # noqa: E402
from ssl_anomaly.monitor import splits as msplits  # noqa: E402

BAND_NAMES = ["ndvi", "blue", "green", "red", "nir", "swir1", "swir2", "lst"]
CHANNELS_BY_INDEX = {"ndvi": (0,), "savi": (3, 4)}
EVAL_PARTITION_SALT = "mdm80_eval_subset_v1"   # must match scripts/eval_dev.py
EVAL_HASH_EXPECTED = "6186edf8a06f82d3"
NDVI_CHANNEL = 0
LST_CHANNEL = 7
SEV_SCORER = "recon_only"  # the trial's scoring arm in every severity metrics file


def add_common_args(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
    p.add_argument("--trial-run-id", default="trial_predictive_20261114",
                   help="output run dir under reports/dev/ (trial writes only here)")
    p.add_argument("--b1-run-id", default="b1_20261114")
    p.add_argument("--gru-ae-run-id", default="gru_ae_20261114")
    p.add_argument("--gru-pred-run-id", default="gru_pred_20261114")
    p.add_argument("--frozen-seed", type=int, default=2026,
                   help="frozen seed of the b1/gru_ae reference arms")
    p.add_argument("--gru-pred-seeds", default="13,42,2026")
    p.add_argument("--notes", default="")
    return p


def gru_pred_seeds(args) -> list[int]:
    return [int(s) for s in str(args.gru_pred_seeds).split(",")]


def load_context():
    """(manifest, data, dev sel, calib_idx, eval_idx, eval_hash) — the eval
    hash is asserted against the recorded independent evaluation subset."""
    manifest = msplits.load_splits_locked()
    data = minputs.load_masked_cycles()
    sel = mproto.select_splits(data, manifest, splits=("dev",))
    cycle_keys = list(sel["cycle_keys"])
    order = sorted(range(len(cycle_keys)),
                   key=lambda i: hashlib.sha256((EVAL_PARTITION_SALT + cycle_keys[i]).encode("utf-8")).hexdigest())
    n_eval = max(4, int(round(0.5 * len(cycle_keys))))
    eval_idx = sorted(order[-n_eval:])
    calib_idx = sorted(order[:-n_eval])
    eval_keys = sorted(cycle_keys[i] for i in eval_idx)
    eval_hash = hashlib.sha256(json.dumps(eval_keys).encode("utf-8")).hexdigest()[:16]
    if eval_hash != EVAL_HASH_EXPECTED:
        raise RuntimeError(
            f"evaluation subset hash {eval_hash} != recorded {EVAL_HASH_EXPECTED} "
            "(partition drift — STOP, do not run the trial on a moved subset)")
    return manifest, data, sel, calib_idx, eval_idx, eval_hash


def severity_entry(run_id: str, model: str, seed: int, *, smoke: bool = False) -> dict:
    """The per-seed entry (τ, k, per-cell q95, cells, mdm80) of a run's
    severity metrics (the frozen dev calibration of that arm). Smoke runs
    read the ``_smoke``-suffixed metrics file."""
    suffix = "_smoke" if smoke else ""
    path = mproto.DEV_DIR / run_id / f"metrics_{model}_sev_{SEV_SCORER}{suffix}.json"
    metrics = json.loads(path.read_text(encoding="utf-8"))
    cand = [r for r in metrics["per_seed"] if int(r["seed"]) == int(seed)]
    if not cand:
        raise RuntimeError(f"seed {seed} not in {path}")
    entry = cand[0]
    n_ch = len(entry["nrmse_per_band"])
    entry["_q95"] = np.array(entry["per_bin_q95"], dtype=np.float64).reshape(36, n_ch)
    entry["_metrics_path"] = str(path.relative_to(REPO_ROOT))
    return entry


def load_arm_scorer(run_id: str, model: str, seed: int, device: str = "cpu"):
    """(scorer, norm) for any trial/reference arm — mirrors eval_dev.load_scorer."""
    import torch

    ckpt_dir = mproto.CHECKPOINTS_DEV_DIR / run_id
    if model == "b1":
        d = np.load(ckpt_dir / f"b1_phasez_causal_seed{seed}.npz", allow_pickle=True)
        b1 = mmodels.B1PhaseZCausal(use_doy=bool(d["use_doy"]), min_n=8)
        b1.median = d["median"]
        b1.scale = d["scale"]
        if "robust_range" in d.files:
            b1.robust_range = d["robust_range"]
        return b1, None
    payload = torch.load(ckpt_dir / f"{model}_seed{seed}.pt", map_location=device, weights_only=False)
    cfg = payload["config"]
    torch_model = mmodels.build_model(model, d_in=cfg["d_in"], n_out=cfg["n_out"], cfg={
        k: cfg[k] for k in ("d_model", "n_layers", "d_ff", "n_heads", "dropout") if k in cfg
    })
    torch_model.load_state_dict(payload["state_dict"])
    scorer_cls = mmodels.DeepPredictiveScorer if model == "gru_pred" else mmodels.DeepCausalScorer
    scorer = scorer_cls(model, torch_model, use_doy=bool(cfg.get("use_doy", True)), device=device)
    norm = minputs.load_norm(mproto.DEV_DIR / run_id / "norm_stats.npz")
    return scorer, norm


def arm_clean_z2(scorer, norm, X: np.ndarray, M: np.ndarray, doy: np.ndarray):
    """(z2, m_eff) clean squared residuals for one arm, mirroring the probe's
    effective-mask semantics (NaN-prediction bins do not score)."""
    if isinstance(scorer, mmodels.B1PhaseZCausal):
        N, T, C = X.shape
        z2 = np.zeros((N, T, C))
        for i in range(N):
            g = (scorer.season_group(doy[i, :, 0]) if scorer.use_doy
                 else np.zeros(T, dtype=np.int64))  # (T,) per-bin groups
            med = scorer.median[g, np.arange(T)]
            scale = scorer.scale[g, np.arange(T)]
            zc = np.where(M[i], (X[i].astype(np.float64) - med) / scale, 0.0)
            resid_corr = mscoring.causal_offset_correct(zc[None], M[i][None])[0]
            z2[i] = resid_corr * resid_corr * M[i]
        return z2, M
    z = minputs.apply_norm(norm, X, M)
    _, pred_z = scorer.loo_batch(z, M, doy)
    m_eff = M & np.isfinite(pred_z)
    resid = np.where(m_eff, z - pred_z, 0.0)
    resid_corr = mscoring.causal_offset_correct(resid, m_eff)
    return (resid_corr * resid_corr) * m_eff, m_eff


def arm_z_pred_both(scorer, norm, X_nat: np.ndarray, M: np.ndarray, doy: np.ndarray):
    """(z, pred) for NATURAL cycles (both tensors needed by part C)."""
    if isinstance(scorer, mmodels.B1PhaseZCausal):
        N, T, C = X_nat.shape
        z = np.zeros((N, T, C))
        pred = np.zeros((N, T, C))
        for i in range(N):
            g = (scorer.season_group(doy[i, :, 0]) if scorer.use_doy
                 else np.zeros(T, dtype=np.int64))
            med = scorer.median[g, np.arange(T)]
            scale = scorer.scale[g, np.arange(T)]
            z[i] = np.where(M[i], (X_nat[i].astype(np.float64) - med) / scale, 0.0)
        return z, pred
    z = minputs.apply_norm(norm, X_nat, M)
    _, pred = scorer.loo_batch(z, M, doy)
    return z, pred


def provenance(args, manifest: dict, eval_hash: str, sel: dict, *, smoke: bool) -> dict:
    return {
        "ladder_rung": "L2",
        "claim_noun": "synthetic anomaly",
        "data_source": "real490 (masked rebuild from stats.zarr)",
        "splits_locked_sha256": manifest["manifest_sha256"],
        "eval_subset_sha256": eval_hash,
        "git_sha": mproto.git_sha(),
        "device": "cpu",
        "date_range": {"first": str(sel["start_dates"][0])[:10],
                       "last": str(sel["end_dates"][-1])[:10]},
        "smoke": bool(smoke),
        "notes": args.notes,
    }


def out_dir(args) -> Path:
    d = mproto.DEV_DIR / args.trial_run_id
    d.mkdir(parents=True, exist_ok=True)
    return d
