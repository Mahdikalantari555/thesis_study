#!/usr/bin/env python3
"""Signal-path decomposition diagnostic (change reconstruction-invariance-diagnostic).

READ-ONLY, dev split only. Re-runs the existing severity-table injections on
the evaluation subset (deterministic, identical to the severity sweep's
injections at the same rounds) and decomposes every injection through the
production statistic stages — residual formation, offset correction,
per-cell q95 normalization, trailing aggregation — against the sweep's
FROZEN calibration (τ, k, per-cell q95 read from the severity metrics of the
frozen seed). Additionally quantifies prediction absorption at post-onset
bins against the counterfactual pre-injection tensor (the reconstruction-
invariance test), attributes the dominant loss stage per cell, and compares
the ranking power (AUC-PR vs matched clean-cycle decompositions) of the raw
onset residual, the q95-normalized contribution and the final path — the
gap localizes ranking power lost by stages 2–4.

Writes reports/dev/<run_id>/diagnostic_<model>.json (+ progress jsonl).
Nothing else is modified; the frozen gru_ae_main sidecar hash is verified
unchanged at exit.

Forbidden: this script never reads CWSI, ETa, y_stress, yield or test cycles.
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

from ssl_anomaly.monitor import diagnostics as mdiag  # noqa: E402
from ssl_anomaly.monitor import inputs as minputs  # noqa: E402
from ssl_anomaly.monitor import models as mmodels  # noqa: E402
from ssl_anomaly.monitor import perturbations as mpert  # noqa: E402
from ssl_anomaly.monitor import protocol as mproto  # noqa: E402
from ssl_anomaly.monitor import severity_table as sev  # noqa: E402
from ssl_anomaly.monitor import splits as msplits  # noqa: E402

BAND_NAMES = ["ndvi", "blue", "green", "red", "nir", "swir1", "swir2", "lst"]
# Channels each injected index physically moves. ndvi is channel 0; a SAVI
# drop is realized by the sum-preserving red/nir solver (nir ↓, red ↑ by the
# same raw amount), so its signal lives on channels red(3) + nir(4). The
# production alarm statistic takes the max over channels, so for savi cells
# the decomposition is reported on the ALARM-DRIVING channel of the two (the
# larger normalized contribution at the onset); the per-cell channel counts
# are recorded alongside.
CHANNELS_BY_INDEX = {"ndvi": (0,), "savi": (3, 4)}
EVAL_PARTITION_SALT = "mdm80_eval_subset_v1"  # must match scripts/eval_dev.py


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run-id", required=True)
    p.add_argument("--b1-run-id", default=None, help="b1 run id (default: b1_<same suffix>)")
    p.add_argument("--seeds", default="2026", help="frozen seed(s) to diagnose (default: 2026)")
    p.add_argument("--rounds", type=int, default=2,
                   help="injection rounds per cell (2 = identical injection set to the severity sweep)")
    p.add_argument("--scorer-metrics-name", default="recon_only",
                   help="severity-metrics variant whose frozen (τ, k, q95) calibration is reused")
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--notes", default="")
    return p.parse_args(argv)


def load_scorer(model: str, seed: int, run_id: str, device: str):
    import torch

    ckpt_dir = mproto.CHECKPOINTS_DEV_DIR / run_id
    if model == "b1":
        d = np.load(ckpt_dir / f"b1_phasez_causal_seed{seed}.npz", allow_pickle=True)
        b1 = mmodels.B1PhaseZCausal(use_doy=bool(d["use_doy"]), min_n=8)
        b1.median = d["median"]
        b1.scale = d["scale"]
        if "robust_range" in d.files:
            b1.robust_range = d["robust_range"]
        return b1
    payload = torch.load(ckpt_dir / f"{model}_seed{seed}.pt", map_location=device, weights_only=False)
    cfg = payload["config"]
    torch_model = mmodels.build_model(model, d_in=cfg["d_in"], n_out=cfg["n_out"], cfg={
        k: cfg[k] for k in ("d_model", "n_layers", "d_ff", "n_heads", "dropout") if k in cfg
    })
    torch_model.load_state_dict(payload["state_dict"])
    return mmodels.DeepCausalScorer(model, torch_model, use_doy=bool(cfg.get("use_doy", True)), device=device)


def frozen_calibration(model: str, run_id: str, seed: int, metrics_name: str) -> dict:
    """τ, k, per-cell q95 from the severity metrics of the frozen seed."""
    path = mproto.DEV_DIR / run_id / f"metrics_{model}_sev_{metrics_name}.json"
    metrics = json.loads(path.read_text(encoding="utf-8"))
    cand = [r for r in metrics["per_seed"] if r["seed"] == seed]
    if not cand:
        raise RuntimeError(f"seed {seed} not in {path}")
    entry = cand[0]
    n_ch = len(entry["nrmse_per_band"])
    return {
        "tau": float(entry["tau"]), "k": int(entry["k"]),
        "q95": np.array(entry["per_bin_q95"], dtype=np.float64).reshape(36, n_ch),
        "sweep_cells": entry["cells"],
        "eval_subset_sha256": metrics["eval_subset_sha256"],
        "severity_table_sha256": metrics["severity_table_sha256"],
        "metrics_path": str(path.relative_to(REPO_ROOT)),
    }


def arm_z_pred(scorer, norm: dict | None, X: np.ndarray, M: np.ndarray, doy: np.ndarray):
    """(z, pred_z) in the arm's EXACT production z-space (mirrors
    eval_dev.score_cycles).

    - Deep arms: z = apply_norm(norm, X, M); pred_z = LOO prediction (z units).
    - B1: z = (X − median[g_bin, bin])/scale[g_bin, bin] with per-BIN season
      groups from its own DOY keying; its prediction is 0 in this space (the
      residual the production statistic feeds forward is z itself).
    """
    if isinstance(scorer, mmodels.B1PhaseZCausal):
        N, T, C = X.shape
        med = np.empty((N, T, C), dtype=np.float64)
        scale = np.empty((N, T, C), dtype=np.float64)
        for i in range(N):
            g = (scorer.season_group(doy[i, :, 0]) if scorer.use_doy
                 else np.zeros(T, dtype=np.int64))  # (T,) per-bin groups
            med[i] = scorer.median[g, np.arange(T)]
            scale[i] = scorer.scale[g, np.arange(T)]
        z = np.where(M, (X.astype(np.float64) - med) / scale, 0.0)
        return z, np.zeros_like(z)
    z = minputs.apply_norm(norm, X, M)
    _, pred_z = scorer.loo_batch(z, M, doy)
    return z, pred_z


def diagnose_arm(args, model: str, run_id: str, seed: int, manifest: dict, data: dict,
                 device: str, progress_path: Path) -> dict:
    t0 = time.time()
    calib = frozen_calibration(model, run_id, seed, args.scorer_metrics_name)
    tau, k, q95 = calib["tau"], calib["k"], calib["q95"]
    n_ch = q95.shape[1]

    sel = mproto.select_splits(data, manifest, splits=("dev",))
    X, M = sel["X"][:, :, :n_ch], sel["M"][:, :, :n_ch]
    doy = minputs.doy_channels(sel["harvest_days"])
    cycle_keys = list(sel["cycle_keys"])

    # Same deterministic partition as the sweep (independent evaluation subset).
    order = sorted(range(len(cycle_keys)),
                   key=lambda i: hashlib.sha256((EVAL_PARTITION_SALT + cycle_keys[i]).encode()).hexdigest())
    n_eval = max(4, int(round(0.5 * len(cycle_keys))))
    eval_idx = sorted(order[-n_eval:])

    norm = None
    if model != "b1":
        norm = minputs.load_norm(mproto.DEV_DIR / run_id / "norm_stats.npz")

    if args.smoke:
        keep = np.array(eval_idx[:6])
        eval_idx = list(keep)
        args.rounds = 1

    scorer = load_scorer(model, seed, run_id, device)
    Xe, Me, doye = X[eval_idx], M[eval_idx], doy[eval_idx]
    n_eval = len(eval_idx)

    # Natural (counterfactual) z-space values + predictions, computed once —
    # the injection never changes them; the natural predictions are the
    # MATCHED NEGATIVES for the stage-wise AUC-PR comparison.
    z_nat_full, pred_nat_full = arm_z_pred(scorer, norm, Xe, Me, doye)

    cells: dict[str, list] = {}
    cells_neg: dict[str, list] = {}
    ch_counts: dict[str, dict] = {}
    sweep_cells = calib["sweep_cells"]
    steps = len(sev.SEVERITY_TABLE) * 2 * 2 * max(1, args.rounds)
    step = 0

    for lv in sev.SEVERITY_TABLE:
        for fam in (sev.ACUTE_FAMILY, sev.PERSISTENT_FAMILY):
            for index in ("ndvi", "savi"):
                key = f"{lv.level_id}/{fam}/{index}"
                decomps: list[mdiag.StageDecomposition] = []
                negs: list[mdiag.StageDecomposition] = []
                ch_used: dict[str, int] = {}
                for rnd in range(max(1, args.rounds)):
                    results = mpert.inject_index_drop_dataset(
                        Xe, Me, level_id=lv.level_id, family=fam, index=index, round_idx=rnd,
                    )
                    Xinj = np.stack([r.x for r in results])
                    Minj = np.stack([r.m for r in results])
                    doy_inj = doye[[r.source_row for r in results]]
                    z_inj_all, pred_z_all = arm_z_pred(scorer, norm, Xinj, Minj, doy_inj)
                    src_rows = [r.source_row for r in results]
                    z_nat_all = z_nat_full[src_rows]
                    pred_nat_all = pred_nat_full[src_rows]
                    mask_nat_all = Me[src_rows]
                    for j, r in enumerate(results):
                        # Decompose on every channel the index physically
                        # moves; report the alarm-driving one (largest onset
                        # normalized contribution — the production statistic
                        # takes the max over channels).
                        per_ch = {
                            ch: mdiag.decompose_injection(
                                z_inj=z_inj_all[j], pred_z=pred_z_all[j],
                                z_natural=z_nat_all[j], mask=Minj[j], q95=q95,
                                tau=tau, k=k, onset_bin=r.onset_bin,
                                duration=r.meta["n_bins_window"], channel=ch,
                            )
                            for ch in CHANNELS_BY_INDEX[index]
                        }
                        # Matched negative: the SAME cycle pre-injection at the
                        # SAME onset/duration/channel policy (clean baseline
                        # for the stage-wise AUC-PR).
                        neg_ch = {
                            ch: mdiag.decompose_injection(
                                z_inj=z_nat_all[j], pred_z=pred_nat_all[j],
                                z_natural=z_nat_all[j], mask=mask_nat_all[j], q95=q95,
                                tau=tau, k=k, onset_bin=r.onset_bin,
                                duration=r.meta["n_bins_window"], channel=ch,
                            )
                            for ch in CHANNELS_BY_INDEX[index]
                        }

                        def _contrib(d: mdiag.StageDecomposition) -> float:
                            return (d.normalized_contribution
                                    if np.isfinite(d.normalized_contribution) else -np.inf)

                        ch_best = max(per_ch, key=lambda c: _contrib(per_ch[c]))
                        decomps.append(per_ch[ch_best])
                        negs.append(neg_ch[ch_best])
                        band = BAND_NAMES[ch_best]
                        ch_used[band] = ch_used.get(band, 0) + 1
                    step += 1
                    rec = {"stage": "decompose", "cell": key, "round": rnd, "step": step,
                           "total": steps, "wall_s": round(time.time() - t0, 1)}
                    with progress_path.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(rec) + "\n")
                cells[key] = decomps
                cells_neg[key] = negs
                ch_counts[key] = ch_used

    summary = mdiag.summarize_cells(cells)

    # Stage-wise AUC-PR per cell (task 1.1): ranking power of the raw onset
    # residual (stage 1) vs the q95-normalized contribution (stage 3) vs the
    # final path (stage 4) against matched clean-cycle decompositions; the
    # stage1→stage4 gap localizes ranking power lost by stages 2–4.
    for key, cell in summary.items():
        pos, neg = cells[key], cells_neg[key]

        def _finite(values: list[float]) -> list[float]:
            return [float(v) for v in values if np.isfinite(v)]

        cell["aucpr"] = {
            "stage1_residual": mdiag.aucpr_stage(
                _finite([abs(d.onset_residual_sigma) for d in pos]),
                _finite([abs(d.onset_residual_sigma) for d in neg])),
            "stage3_contribution": mdiag.aucpr_stage(
                _finite([d.normalized_contribution for d in pos]),
                _finite([d.normalized_contribution for d in neg])),
            "stage4_path": mdiag.aucpr_stage(
                _finite([d.path_max_window for d in pos]),
                _finite([d.path_max_window for d in neg])),
        }

    # Cross-check: the diagnostic's detection rate (identical injection set at
    # rounds=2) must match the sweep's recorded rate at the same cells.
    crosscheck = {}
    for key, s in summary.items():
        sweep_rate = sweep_cells.get(key, {}).get("detection_rate")
        crosscheck[key] = {
            "diagnostic_rate": s["detection_rate"],
            "sweep_rate": sweep_rate,
            "match": None if sweep_rate is None else bool(
                abs(s["detection_rate"] - sweep_rate) < 1e-9),
        }

    wall = time.time() - t0
    return {
        "type": "reconstruction_invariance_diagnostic",
        "model_id": model,
        "run_id": run_id,
        "frozen_seed": seed,
        "protocol": "severity_sweep_v1",
        "scorer_metrics_name": args.scorer_metrics_name,
        "severity_table_sha256": calib["severity_table_sha256"],
        "eval_subset_sha256": calib["eval_subset_sha256"],
        "tau": tau, "k": k,
        "n_eval_cycles": int(n_eval),
        "rounds": max(1, args.rounds),
        "ladder_rung": "L2",
        "claim_noun": "synthetic anomaly",
        "data_source": "real490 (masked rebuild from stats.zarr)",
        "splits_locked_sha256": manifest["manifest_sha256"],
        "git_sha": mproto.git_sha(),
        "device": device,
        "wall_time_s": round(wall, 1),
        "date_range": {"first": str(sel["start_dates"][0])[:10],
                       "last": str(sel["end_dates"][-1])[:10]},
        "cells": summary,
        "decomposition_channel_counts": ch_counts,
        "detection_crosscheck_vs_sweep": crosscheck,
        "smoke": bool(args.smoke),
        "notes": args.notes,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    t0 = time.time()
    device = "cpu"
    seeds = [int(s) for s in args.seeds.split(",")]

    manifest = msplits.load_splits_locked()
    data = minputs.load_masked_cycles()

    sidecar_path = REPO_ROOT / "checkpoints" / "gru_ae_main.json"
    sidecar_sha_before = (hashlib.sha256(sidecar_path.read_bytes()).hexdigest()
                          if sidecar_path.exists() else None)

    suffix = args.run_id.rsplit("_", 1)[1] if "_" in args.run_id else time.strftime("%Y%m%d")
    b1_run_id = args.b1_run_id or f"b1_{suffix}"

    outputs = {}
    for model, run_id in (("gru_ae", args.run_id), ("b1", b1_run_id)):
        for seed in seeds:
            progress_path = mproto.DEV_DIR / run_id / f"progress_diagnostic_{model}_seed{seed}.jsonl"
            progress_path.parent.mkdir(parents=True, exist_ok=True)
            rep = diagnose_arm(args, model, run_id, seed, manifest, data, device, progress_path)
            out_dir = mproto.DEV_DIR / run_id
            out_dir.mkdir(parents=True, exist_ok=True)
            out = out_dir / f"diagnostic_{model}_seed{seed}.json"
            out.write_text(json.dumps(rep, indent=2), encoding="utf-8")
            outputs[f"{model}:{seed}"] = str(out.relative_to(REPO_ROOT))
            bad = [k for k, v in rep["detection_crosscheck_vs_sweep"].items()
                   if v["match"] is False]
            print(f"[diagnostic] {model} seed {seed}: {len(rep['cells'])} cells, "
                  f"crosscheck mismatches={len(bad)} → {out} (wall {rep['wall_time_s']}s)")
            if bad:
                print(f"[diagnostic] WARNING crosscheck mismatch at: {bad[:6]}")

    sidecar_sha_after = (hashlib.sha256(sidecar_path.read_bytes()).hexdigest()
                         if sidecar_path.exists() else None)
    unchanged = sidecar_sha_before == sidecar_sha_after
    print(f"[diagnostic] frozen sidecar byte-identical: {unchanged}")

    summary_path = mproto.DEV_DIR / args.run_id / "diagnostic_summary.json"
    summary_path.write_text(json.dumps({
        "type": "diagnostic_summary",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "wall_time_s": round(time.time() - t0, 1),
        "sidecar_byte_identical": bool(unchanged),
        "outputs": outputs,
        "notes": args.notes,
    }, indent=2), encoding="utf-8")
    print(f"[diagnostic] summary → {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
