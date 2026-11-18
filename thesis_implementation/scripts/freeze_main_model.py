#!/usr/bin/env python3
"""Freeze the main monitor model (tasks 7.1/7.2, design D7).

Three modes:

**Freeze** (agent may run after plateau)::

    python scripts/freeze_main_model.py --model masked_transformer --run-id <id>

Selects the best seed by the dev primary metric from the run's
``reports/dev/<run_id>/metrics_<model>.json``, copies the checkpoint to
``checkpoints/<id>_main.pt`` and writes the sidecar ``<id>_main.json``
(architecture config, normalization stats path + arrays, τ, k, hashes, seeds,
dev metrics, parameter count, ``ladder_rung: "L2"``).

**Attach severity** (change literature-grounded-severity-protocol, task 3.1)::

    python scripts/freeze_main_model.py --model gru_ae --run-id <id> --attach-severity

Adds ``severity_table_sha256`` + ``mdm80`` (+ provenance of the severity
metrics file and the independent evaluation-subset hash) to the EXISTING
frozen sidecar. The platform-serving threshold block (τ, k, per-cell
normalizer — the frozen finding-16 calibration consumed by the exporter) is
carried over untouched, so the platform contract stays byte-identical apart
from the new provenance fields.

**Final test** (user runs ONCE)::

    python scripts/freeze_main_model.py --model gru_ae --run-id <id> --final-test
           [--protocol severity|legacy]

``--protocol legacy``: the finding-16 locked test (det@1×MAD + clean FAR).
``--protocol severity`` (default): the literature-grounded sweep on the locked
test split — per-level detection with field bootstrap CIs, MDM80 per family ×
index with bootstrap CIs, event-level FAR — for the frozen seed of the main
model AND ``b1_phasez_causal``, evaluated against the dual-axis target
((a) detection margin ≥ 0.05 at the pre-registered S3/acute/ndvi cell,
(b) MDM80(main) ≤ MDM80(B1)). ``ladder_rung`` becomes L3 only if the target
holds; otherwise it stays L2 and the honest negative is recorded. Test access
is exclusive to this entry point (spec test-isolation).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import inputs as minputs  # noqa: E402
from ssl_anomaly.monitor import models as mmodels  # noqa: E402
from ssl_anomaly.monitor import perturbations as mpert  # noqa: E402
from ssl_anomaly.monitor import protocol as mproto  # noqa: E402
from ssl_anomaly.monitor import scoring as mscoring  # noqa: E402
from ssl_anomaly.monitor import severity_table as sev  # noqa: E402
from ssl_anomaly.monitor import splits as msplits  # noqa: E402

MODEL_ID_MAP = {
    "masked_transformer": "masked_transformer_main",
    "gru_ae": "gru_ae_main",
    # predictive-ssl-controlled-trial: the gru_pred arm freezes with the same
    # sidecar schema (τ, k, per-bin q95, frozen seed, hashes).
    "gru_pred": "gru_pred_main",
}
BAND_NAMES = ["ndvi", "blue", "green", "red", "nir", "swir1", "swir2", "lst"]
MDM80_TARGET = 0.80
MDM80_CENSORED = 7  # numeric sentinel for ">S6" (ordering only)
PRIMARY_CELL = ("S3", "acute", "ndvi")  # pre-registered target cell (moderate verified anchor)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--model", required=True, choices=["masked_transformer", "gru_ae", "gru_pred"])
    p.add_argument("--run-id", required=True)
    p.add_argument("--final-test", action="store_true",
                   help="run the locked final test ONCE (user-only) and set ladder_rung")
    p.add_argument("--protocol", choices=["severity", "legacy"], default="severity",
                   help="final-test protocol (severity = literature-grounded sweep)")
    p.add_argument("--scorer", default="recon_only", help="scoring arm for the severity final test")
    p.add_argument("--attach-severity", action="store_true",
                   help="add severity_table_sha256 + mdm80 to the existing frozen sidecar (task 3.1)")
    p.add_argument("--seeds", default="13,42,2026")
    p.add_argument("--rounds", type=int, default=10, help="legacy final-test injection rounds")
    p.add_argument("--bootstrap", type=int, default=1000)
    p.add_argument("--notes", default="")
    return p.parse_args(argv)


def load_scorer_and_norm(model: str, seed: int, run_id: str, device: str):
    import torch

    ckpt_dir = mproto.CHECKPOINTS_DEV_DIR / run_id
    norm = minputs.load_norm(mproto.DEV_DIR / run_id / "norm_stats.npz")
    payload = torch.load(ckpt_dir / f"{model}_seed{seed}.pt", map_location=device, weights_only=False)
    cfg = payload["config"]
    torch_model = mmodels.build_model(model, d_in=cfg["d_in"], n_out=cfg["n_out"], cfg={
        k: cfg[k] for k in ("d_model", "n_layers", "d_ff", "n_heads", "dropout") if k in cfg
    })
    torch_model.load_state_dict(payload["state_dict"])
    scorer_cls = mmodels.DeepPredictiveScorer if model == "gru_pred" else mmodels.DeepCausalScorer
    scorer = scorer_cls(model, torch_model, use_doy=bool(cfg.get("use_doy", True)), device=device)
    return scorer, norm, mmodels.count_parameters(torch_model), cfg


def load_b1(run_id: str, seed: int):
    d = np.load(mproto.CHECKPOINTS_DEV_DIR / run_id / f"b1_phasez_causal_seed{seed}.npz", allow_pickle=True)
    b1 = mmodels.B1PhaseZCausal(use_doy=bool(d["use_doy"]), min_n=8)
    b1.median, b1.scale = d["median"], d["scale"]
    b1.robust_range = d["robust_range"] if "robust_range" in d.files else None
    return b1


def score_arrays(scorer, norm, X, M, doy, statistic: str = "z2"):
    """Per-bin statistics for one split.

    statistic="z2": per-(bin, channel) squared z-space residuals (input to the
    cumulative alarm statistic). statistic="mean": D5 mean-z² (secondary).
    """
    if isinstance(scorer, mmodels.B1PhaseZCausal):
        N, T, C = X.shape
        scores = np.full((N, T), np.nan)
        z2 = np.zeros((N, T, C))
        for i in range(N):
            g = scorer.season_group(doy[i, :, 0]) if scorer.use_doy else np.zeros(T, dtype=np.int64)
            med = scorer.median[g, np.arange(T)]
            scale = scorer.scale[g, np.arange(T)]
            zc = np.where(M[i], (X[i] - med) / scale, 0.0)
            zc_corr = mscoring.causal_offset_correct(zc[None], M[i][None])[0]
            z2[i] = zc_corr * zc_corr * M[i]
            scores[i] = scorer.score_cycle(X[i], M[i], doy[i, :, 0])
        return z2 if statistic == "z2" else scores
    z = minputs.apply_norm(norm, X, M)
    scores, pred_z = scorer.loo_batch(z, M, doy)
    if statistic == "mean":
        return scores
    resid = z - pred_z
    resid_corr = mscoring.causal_offset_correct(resid, M)
    return (resid_corr * resid_corr) * M


def eval_split(scorer, norm, X, M, doy, tau: float, k: int, rounds: int, seed_base: int,
               cell_q95: np.ndarray | None = None):
    """Clean FAR + injected detection on one split's arrays.

    ``cell_q95`` is the FROZEN dev calibration normalizer (36×8, from the
    sidecar threshold block); the test split is never re-normalized from its
    own data.
    """
    z2 = score_arrays(scorer, norm, X, M, doy, statistic="z2")
    paths = mscoring.cumulative_channel_max(z2, M, cell_q95)
    n = X.shape[0]
    far = float(np.mean([mscoring.alarm_per_cycle(paths[i], tau, k) for i in range(n)]))

    # Perturbation sizing: train stats sidecar for deep runs, B1's own pooled
    # stats otherwise (scale = MAD × 1.4826, identical in K and °C).
    scale = norm["scale"] if norm is not None else (
        scorer.scale[0] if scorer.scale.ndim == 3 else scorer.scale
    )
    det, delays, types, fields_idx = [], [], [], []
    for rnd in range(rounds):
        rng = np.random.default_rng(seed_base + rnd)
        cfg_pert = mpert.PerturbationConfig(n_per_stratum=min(n, 16), durations=(1, 2, 3, 5))
        results = mpert.inject_dataset(X, M, scale, cfg_pert, rng)
        Xinj = np.stack([r.x for r in results])
        Minj = np.stack([r.m for r in results])
        doy_inj = doy[[r.source_row for r in results]]
        z2_inj = score_arrays(scorer, norm, Xinj, Minj, doy_inj, statistic="z2")
        paths_inj = mscoring.cumulative_channel_max(z2_inj, Minj, cell_q95)
        for j, r in enumerate(results):
            if abs(r.severity - 1.0) > 1e-9:
                continue
            fb = mscoring.first_alarm_bin(paths_inj[j], tau, k, r.onset_bin)
            det.append(1 if fb >= 0 else 0)
            delays.append((fb - r.onset_bin) * 15 if fb >= 0 else np.nan)
            types.append(r.pert_type)
            fields_idx.append(int(r.source_row))
    return {
        "far_clean": far,
        "detection_rate_1mad": float(np.mean(det)) if det else float("nan"),
        "median_delay_days": float(np.nanmedian(delays)) if det and np.isfinite(delays).any() else float("nan"),
        "n_clean": n,
        "n_injected_1mad": len(det),
        "det_flags": det,
        "field_rows": fields_idx,
        "types": types,
        "clean_paths": paths,
    }


def bootstrap_ci_fields(det_flags: list[int], field_rows: list[int], field_ids: np.ndarray,
                        reps: int, seed: int) -> tuple[float, float]:
    """95 % CI of the detection rate, resampling FIELDS with replacement."""
    rng = np.random.default_rng(seed)
    rows_by_field: dict[int, list[int]] = {}
    for row, fidx in enumerate(field_rows):
        rows_by_field.setdefault(int(field_ids[fidx]), []).append(row)
    fields = sorted(rows_by_field)
    if len(fields) < 2:
        return float("nan"), float("nan")
    stats = []
    for _ in range(reps):
        sample = rng.choice(fields, size=len(fields), replace=True)
        flags = [f for fid in sample for f in rows_by_field[int(fid)]]
        stats.append(np.mean([det_flags[f] for f in flags]))
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))


def _severity_seed_entry(metrics: dict) -> tuple[dict, str]:
    """Frozen-seed selection from SEVERITY dev metrics (gru_pred freeze; the
    trial has no legacy metrics file). Pre-registered rule, recorded verbatim
    in the sidecar notes: LOWEST sum of the four MDM80 sentinels (censored
    ">S6" = 7), ties → higher detection at S6/persistent/ndvi, ties → lower
    seed. Dev-side only (no test access)."""
    per_seed = metrics["per_seed"]
    best = min(per_seed, key=lambda r: (
        sum(r["mdm80"][k]["sentinel"]
            for k in ("acute/ndvi", "acute/savi", "persistent/ndvi", "persistent/savi")),
        -r["cells"]["S6/persistent/ndvi"]["detection_rate"],
        r["seed"],
    ))
    rule = ("frozen seed = lowest sum of the four MDM80 sentinels in the dev severity sweep "
            "(censored >S6 = 7); ties → higher S6/persistent/ndvi detection, then lower seed")
    return best, rule


def freeze(args) -> int:
    manifest = msplits.load_splits_locked()
    metrics_path = mproto.DEV_DIR / args.run_id / f"metrics_{args.model}.json"
    if not metrics_path.exists():
        # gru_pred (predictive-ssl-controlled-trial): no legacy-protocol file —
        # select the frozen seed from the run's severity metrics instead.
        sev_path = _severity_metrics_path(args.model, args.run_id, args.scorer)
        if not sev_path.exists():
            raise FileNotFoundError(
                f"neither {metrics_path} nor {sev_path} exists — run scripts/eval_dev.py first")
        metrics_path = sev_path
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    if "detection_rate_1mad" in metrics["per_seed"][0]:
        # Legacy path: best seed by primary metric (ties → lowest seed); ties
        # and ranges are part of the report, the sidecar carries all seeds'.
        per_seed = metrics["per_seed"]
        best = max(per_seed, key=lambda r: (r["detection_rate_1mad"], -r["seed"]))
        seed_rule = "best dev detection_rate_1mad (ties → lowest seed)"
    else:
        best, seed_rule = _severity_seed_entry(metrics)
    seed = best["seed"]
    device = metrics.get("device", "cpu")

    scorer, norm, params, cfg = load_scorer_and_norm(args.model, seed, args.run_id, device)
    model_id = MODEL_ID_MAP[args.model]

    # Model-card FLOPs: estimated forward MACs per cycle (36-token sequence),
    # flagged as an estimate — an exact count needs a profiler, which is out
    # of scope here (task 10.6 requires the field; honest labelling applies).
    flops_est = {
        "gru_ae": 2 * params * 36,
        "gru_pred": 2 * params * 36,
        "masked_transformer": 2 * params * 36,
    }[args.model]

    ckpt_src = mproto.CHECKPOINTS_DEV_DIR / args.run_id / f"{args.model}_seed{seed}.pt"
    ckpt_dst = REPO_ROOT / "checkpoints" / f"{model_id}.pt"
    ckpt_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ckpt_src, ckpt_dst)

    sidecar = {
        "model_id": model_id,
        "family": args.model,
        "formula_id": f"{model_id}:causal_bin_mse",
        "created": time.strftime("%Y-%m-%d"),
        "git_sha": mproto.git_sha(),
        "data_source": "real490 (masked rebuild from stats.zarr)",
        "band_order": BAND_NAMES,
        "n_bins": 36,
        "bin_days": 15,
        "architecture_config": cfg,
        "parameter_count": params,
        "flops_estimated_macs_forward_per_cycle": int(flops_est),
        "training_wall_time_s_per_seed": metrics.get("wall_time_s"),
        "use_doy_channels": bool(cfg.get("use_doy", True)),
        "normalization": {
            "median": norm["median"].tolist(),
            "scale": norm["scale"].tolist(),
            "robust_range": norm["robust_range"].tolist(),
            "norm_stats_file": str((mproto.DEV_DIR / args.run_id / "norm_stats.npz").relative_to(REPO_ROOT)),
            "computed_from": "train split only",
        },
        "threshold": best,  # tau, k, far target/achieved + calibration n
        "persistence_k": int(best["k"]),
        "ladder_rung": "L2",
        "splits_locked_sha256": manifest["manifest_sha256"],
        "seeds": metrics["seeds"],
        "frozen_seed": seed,
        "frozen_seed_selection_rule": seed_rule,
        "dev_metrics_summary": (
            {
                "primary_mean": metrics["primary"]["mean"],
                "primary_std": metrics["primary"]["std"],
                "median_delay_days": metrics["median_delay_days"]["mean"],
                "aucpr_partial": per_seed[0]["aucpr_partial"],
                "nrmse_per_band": per_seed[0]["nrmse_per_band"],
            } if "primary" in metrics else
            {
                "protocol": metrics.get("protocol"),
                "mdm80_frozen_seed": {k: v["value"] for k, v in best["mdm80"].items()},
                "mdm80_aggregate": _aggregate_mdm80(metrics["per_seed"]),
                "aucpr_partial": best["aucpr_partial"],
                "nrmse_per_band": best["nrmse_per_band"],
            }
        ),
        "dev_metrics_file": str(metrics_path.relative_to(REPO_ROOT)),
        "training_run_id": args.run_id,
        "notes": args.notes,
    }
    sidecar["manifest_sha256"] = json.dumps(
        {k: sidecar[k] for k in sorted(sidecar)}, sort_keys=True, default=str
    )
    sidecar_path = REPO_ROOT / "checkpoints" / f"{model_id}.json"
    sidecar_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    print(f"[freeze] {ckpt_dst}")
    if "detection_rate_1mad" in best:
        print(f"[freeze] sidecar {sidecar_path} (ladder_rung=L2, seed {seed} "
              f"det@1MAD={best['detection_rate_1mad']:.3f})")
    else:
        print(f"[freeze] sidecar {sidecar_path} (ladder_rung=L2, seed {seed}, "
              f"selection: {seed_rule})")
    return 0


def final_test(args) -> int:
    manifest = msplits.load_splits_locked()
    metrics_path = mproto.DEV_DIR / args.run_id / f"metrics_{args.model}.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    per_seed = metrics["per_seed"]
    best = max(per_seed, key=lambda r: (r["detection_rate_1mad"], -r["seed"]))
    seed, tau, k = best["seed"], best["tau"], best["k"]
    device = "cpu"

    # The ONLY test-split access in the codebase:
    data = minputs.load_masked_cycles()
    sel = mproto.select_splits(data, manifest, splits=("test",), allow_test=True)
    X, M = sel["X"], sel["M"]
    doy = minputs.doy_channels(sel["harvest_days"])
    field_ids = sel["field_ids"]

    scorer, norm, params, cfg = load_scorer_and_norm(args.model, seed, args.run_id, device)
    if not best.get("per_bin_q95"):
        raise RuntimeError(
            "The dev metrics for this run predate alarm-statistic change #2 "
            "(no per_bin_q95 cells recorded). Re-run scripts/eval_dev.py for the run first."
        )
    cell_q95 = np.array(best["per_bin_q95"], dtype=np.float64).reshape(36, 8)
    main_res = eval_split(scorer, norm, X, M, doy, tau, k, args.rounds,
                          seed_base=77_000 + seed, cell_q95=cell_q95)

    # B1 lives in its own run dir (b1_<same date suffix as the main run>).
    # run_id pattern "<model>_<date>" where model itself contains underscores.
    suffix = args.run_id.rsplit("_", 1)[1] if "_" in args.run_id else time.strftime("%Y%m%d")
    b1_run_id = f"b1_{suffix}"
    b1 = load_b1(b1_run_id, seed)
    # B1's τ, k, normalizer from the same dev calibration (metrics of the b1 run).
    b1_metrics_path = mproto.DEV_DIR / b1_run_id / "metrics_b1.json"
    b1_tau, b1_k, b1_cell = None, 1, None
    if b1_metrics_path.exists():
        bm = json.loads(b1_metrics_path.read_text(encoding="utf-8"))
        cand = [r for r in bm["per_seed"] if r["seed"] == seed] or bm["per_seed"]
        b1_tau, b1_k = cand[0]["tau"], cand[0]["k"]
        if cand[0].get("per_bin_q95"):
            b1_cell = np.array(cand[0]["per_bin_q95"], dtype=np.float64).reshape(36, 8)
    if b1_tau is None or b1_cell is None:
        raise FileNotFoundError(
            f"B1 dev metrics (with per_bin_q95 cells) not found at {b1_metrics_path} — "
            "re-run scripts/eval_dev.py for the b1 run first."
        )
    b1_res = eval_split(b1, None, X, M, doy, b1_tau, b1_k, args.rounds,
                        seed_base=88_000 + seed, cell_q95=b1_cell)

    ci_main = bootstrap_ci_fields(main_res["det_flags"], main_res["field_rows"], field_ids,
                                  args.bootstrap, seed=seed)
    ci_b1 = bootstrap_ci_fields(b1_res["det_flags"], b1_res["field_rows"], field_ids,
                                args.bootstrap, seed=seed)

    target_gap = main_res["detection_rate_1mad"] - b1_res["detection_rate_1mad"]
    non_overlap = ci_main[0] > ci_b1[1]
    target_met = target_gap >= 0.05 and non_overlap
    ladder = "L3" if target_met else "L2"

    report = {
        "type": "final_test",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "git_sha": mproto.git_sha(),
        "model_id": MODEL_ID_MAP[args.model],
        "frozen_seed": seed,
        "n_test_cycles": int(X.shape[0]),
        "n_test_fields": int(np.unique(field_ids).size),
        "date_range": {
            "first": str(sel["start_dates"][0])[:10],
            "last": str(sel["end_dates"][-1])[:10],
        },
        "splits_locked_sha256": manifest["manifest_sha256"],
        "far_target": 0.05,
        "far_clean_main": main_res["far_clean"],
        "far_clean_b1": b1_res["far_clean"],
        "detection_rate_1mad_main": main_res["detection_rate_1mad"],
        "detection_rate_1mad_b1": b1_res["detection_rate_1mad"],
        "median_delay_days_main": main_res["median_delay_days"],
        "bootstrap_ci95_fields_main": list(ci_main),
        "bootstrap_ci95_fields_b1": list(ci_b1),
        "bootstrap_reps": args.bootstrap,
        "target": {"gap_needed": 0.05, "gap_observed": target_gap,
                   "ci_non_overlap": bool(non_overlap), "met": bool(target_met)},
        "ladder_rung_result": ladder,
        "note": (
            "L3 measured as synthetic-perturbation detection on locked test "
            "(unseen years + spatial block). Real-stress agreement (L4) is "
            "future work; 'suspected_stress' naming unchanged."
        ),
    }
    out = REPO_ROOT / "reports" / f"final_test_{MODEL_ID_MAP[args.model]}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Update the frozen sidecar's ladder rung when the target holds.
    model_id = MODEL_ID_MAP[args.model]
    sidecar_path = REPO_ROOT / "checkpoints" / f"{model_id}.json"
    if sidecar_path.exists():
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        sidecar["ladder_rung"] = ladder
        sidecar["final_test_file"] = str(out.relative_to(REPO_ROOT))
        sidecar_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")

    print(json.dumps({k: report[k] for k in (
        "far_clean_main", "far_clean_b1", "detection_rate_1mad_main",
        "detection_rate_1mad_b1", "bootstrap_ci95_fields_main",
        "bootstrap_ci95_fields_b1", "ladder_rung_result")}, indent=2))
    print(f"[final-test] report → {out}")
    if not target_met:
        print("[final-test] D6 target NOT met — reported as a finding; rung stays L2 "
              "(spec: honest outcome, no goalpost moving).")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.attach_severity:
        return attach_severity(args)
    if args.final_test:
        if args.protocol == "severity":
            return final_test_severity(args)
        return final_test(args)
    return freeze(args)


def _severity_metrics_path(model: str, run_id: str, scorer: str) -> Path:
    return mproto.DEV_DIR / run_id / f"metrics_{model}_sev_{scorer}.json"


def _frozen_seed_entry(metrics: dict, sidecar: dict) -> dict:
    """The per-seed entry of the sidecar's frozen seed (consistency check)."""
    seed = sidecar["frozen_seed"]
    cand = [r for r in metrics["per_seed"] if r["seed"] == seed]
    if not cand:
        raise RuntimeError(
            f"frozen seed {seed} not present in the severity metrics per_seed "
            f"({[r['seed'] for r in metrics['per_seed']]})"
        )
    return cand[0]


def attach_severity(args) -> int:
    """Attach severity-protocol results to the EXISTING frozen sidecar (task 3.1).

    Adds ``severity_table_sha256``, ``mdm80`` (frozen seed + 3-seed aggregate),
    the severity metrics path and the independent evaluation-subset hash. The
    platform-serving threshold block (τ, k, per-cell normalizer — the frozen
    finding-16 calibration consumed by the exporter) is carried over untouched;
    only provenance fields are added, so the platform payload built from the
    old block stays consistent with the sidecar (no platform drift).
    """
    model_id = MODEL_ID_MAP[args.model]
    sidecar_path = REPO_ROOT / "checkpoints" / f"{model_id}.json"
    if not sidecar_path.exists():
        raise FileNotFoundError(f"frozen sidecar missing: {sidecar_path} (run freeze first)")
    metrics_path = _severity_metrics_path(args.model, args.run_id, args.scorer)
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    entry = _frozen_seed_entry(metrics, sidecar)

    sidecar["severity_protocol"] = metrics["protocol"]
    sidecar["severity_table_sha256"] = metrics["severity_table_sha256"]
    sidecar["severity_eval_subset_sha256"] = metrics["eval_subset_sha256"]
    sidecar["severity_metrics_file"] = str(metrics_path.relative_to(REPO_ROOT))
    sidecar["mdm80"] = {
        "frozen_seed": sidecar["frozen_seed"],
        "frozen_seed_values": {k: v["value"] for k, v in entry["mdm80"].items()},
        "aggregate": _aggregate_mdm80(metrics["per_seed"]),
        "mdm80_target": MDM80_TARGET,
    }
    sidecar["git_sha"] = mproto.git_sha()
    sidecar["created"] = time.strftime("%Y-%m-%d")
    note = (f"severity-protocol results attached {time.strftime('%Y-%m-%d %H:%M:%S')} "
            f"(table {metrics['severity_table_sha256'][:12]}, eval subset "
            f"{metrics['eval_subset_sha256']}); threshold block unchanged "
            "(platform serving calibration frozen in finding 16)")
    sidecar["notes"] = (sidecar.get("notes", "") + "; " + note).strip("; ")
    sidecar["manifest_sha256"] = json.dumps(
        {k: sidecar[k] for k in sorted(sidecar)}, sort_keys=True, default=str
    )
    sidecar_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    print(f"[attach-severity] sidecar {sidecar_path}")
    print(f"[attach-severity] mdm80 (frozen seed {sidecar['frozen_seed']}): "
          + " ".join(f"{k}={v['value']}" for k, v in entry["mdm80"].items()))
    return 0


def _aggregate_mdm80(per_seed: list[dict]) -> dict:
    """Mean ± std of the MDM80 sentinels per family × index (censored ">S6"
    = 7 for ordering; labels kept)."""
    out = {}
    for fam in (sev.ACUTE_FAMILY, sev.PERSISTENT_FAMILY):
        for index in ("ndvi", "savi"):
            key = f"{fam}/{index}"
            vals = [r["mdm80"][key]["sentinel"] for r in per_seed]
            labels = [r["mdm80"][key]["value"] for r in per_seed]
            arr = np.asarray(vals, dtype=np.float64)
            out[key] = {
                "mean_sentinel": float(arr.mean()), "std_sentinel": float(arr.std(ddof=1)) if len(vals) > 1 else 0.0,
                "per_seed_labels": labels,
                "n_censored": int(sum(1 for v in vals if v == MDM80_CENSORED)),
            }
    return out


def severity_sweep_on_split(
    scorer, norm, X: np.ndarray, M: np.ndarray, doy: np.ndarray,
    tau: float, k: int, cell_q95: np.ndarray,
    field_ids: np.ndarray, *,
    rounds: int, seed_base: int, bootstrap: int,
) -> dict:
    """The severity sweep on any split (used by --final-test on the locked
    test split): per-cell detection + Wilson CI + field bootstrap CI, MDM80
    per family × index with a bootstrap CI, event-level FAR per cell and on
    clean cycles."""
    levels = sev.load_table()
    n, T = X.shape[0], X.shape[1]
    clean_scores = None  # scored lazily by the caller via score_arrays
    del clean_scores

    cells: dict[str, dict] = {}
    det_by_cell: dict[str, list[int]] = {}
    field_by_cell: dict[str, list[int]] = {}
    windows_by_cell: dict[str, list] = {}
    paths_by_cell: dict[str, list] = {}
    delays_by_cell: dict[str, list] = {}
    for lv in levels:
        for fam in (sev.ACUTE_FAMILY, sev.PERSISTENT_FAMILY):
            for index in ("ndvi", "savi"):
                key = f"{lv.level_id}/{fam}/{index}"
                det_flags: list[int] = []
                delays: list[float] = []
                windows: list = []
                paths_list: list[np.ndarray] = []
                field_rows: list[int] = []
                for rnd in range(max(1, rounds)):
                    results = mpert.inject_index_drop_dataset(
                        X, M, level_id=lv.level_id, family=fam, index=index, round_idx=rnd,
                    )
                    Xinj = np.stack([r.x for r in results])
                    Minj = np.stack([r.m for r in results])
                    doy_inj = doy[[r.source_row for r in results]]
                    z2_inj = score_arrays(scorer, norm, Xinj, Minj, doy_inj, statistic="z2")
                    inj_paths = mscoring.cumulative_channel_max(z2_inj, Minj, cell_q95)
                    for j, r in enumerate(results):
                        fb = mscoring.first_alarm_bin(inj_paths[j], tau, k, r.onset_bin)
                        det_flags.append(1 if fb >= 0 else 0)
                        if fb >= 0:
                            delays.append(float((fb - r.onset_bin) * 15))
                        windows.append([(r.onset_bin, r.onset_bin + r.meta["n_bins_window"])])
                        paths_list.append(inj_paths[j])
                        field_rows.append(int(r.source_row))
                nd_, nn = int(sum(det_flags)), len(det_flags)
                lo, hi = mscoring.wilson_ci(nd_, nn)
                cells[key] = {
                    "n": nn, "n_detected": nd_, "detection_rate": nd_ / max(1, nn),
                    "wilson_ci95": [round(lo, 4), round(hi, 4)],
                    "median_delay_days": float(np.median(delays)) if delays else float("nan"),
                    "event_far": mscoring.event_far_from_paths(
                        np.stack(paths_list), windows, tau, gap=2)["event_far"],
                    "level_id": lv.level_id, "family": fam, "index": index,
                }
                det_by_cell[key] = det_flags
                field_by_cell[key] = field_rows
                windows_by_cell[key] = windows
                paths_by_cell[key] = paths_list
                delays_by_cell[key] = delays

    # MDM80 + field bootstrap CIs.
    def mdm_from_flags(flags_by_cell: dict[str, list[int]]) -> dict:
        out = {}
        for fam in (sev.ACUTE_FAMILY, sev.PERSISTENT_FAMILY):
            for index in ("ndvi", "savi"):
                reached = None
                for lv in levels:
                    f = flags_by_cell[f"{lv.level_id}/{fam}/{index}"]
                    if sum(f) / max(1, len(f)) >= MDM80_TARGET:
                        reached = lv.level_id
                        break
                out[f"{fam}/{index}"] = (
                    {"value": reached, "sentinel": int(reached[1:]), "censored": False}
                    if reached else
                    {"value": ">S6", "sentinel": MDM80_CENSORED, "censored": True}
                )
        return out

    mdm80 = mdm_from_flags(det_by_cell)

    # Bootstrap over FIELDS: resample fields, rebuild flags per replicate,
    # recompute per-cell rates and the MDM80 sentinel.
    rng = np.random.default_rng(2026)
    fields_sorted = np.unique(field_ids)
    if len(fields_sorted) >= 2 and bootstrap > 0:
        rows_by_field: dict[int, list[int]] = {}
        for row, fidx in enumerate(field_ids):
            rows_by_field.setdefault(int(fidx), []).append(row)
        cell_boot: dict[str, list[float]] = {k: [] for k in det_by_cell}
        mdm_boot: dict[str, list[int]] = {k: [] for k in mdm80}
        for _ in range(bootstrap):
            sample = rng.choice(fields_sorted, size=len(fields_sorted), replace=True)
            sample_set = {int(s) for s in sample}
            boot_flags: dict[str, list[int]] = {}
            for key, flags in det_by_cell.items():
                idxs = [j for j, frow in enumerate(field_by_cell[key]) if frow in sample_set]
                boot_flags[key] = [flags[j] for j in idxs] if idxs else [0]
            for key, f in boot_flags.items():
                cell_boot[key].append(sum(f) / max(1, len(f)))
            boot_mdm = mdm_from_flags(boot_flags)
            for key in mdm80:
                mdm_boot[key].append(boot_mdm[key]["sentinel"])
        for key in cells:
            cells[key]["bootstrap_ci95_fields"] = [
                float(np.percentile(cell_boot[key], 2.5)), float(np.percentile(cell_boot[key], 97.5))]
        for key in mdm80:
            mdm80[key]["bootstrap_ci95_sentinel"] = [
                float(np.percentile(mdm_boot[key], 2.5)), float(np.percentile(mdm_boot[key], 97.5))]

    clean_z2 = score_arrays(scorer, norm, X, M, doy, statistic="z2")
    clean_paths = mscoring.cumulative_channel_max(clean_z2, M, cell_q95)
    clean_efar = mscoring.event_far_from_paths(clean_paths, [None] * n, tau, gap=2)
    return {
        "cells": cells, "mdm80": mdm80, "event_far_clean": clean_efar,
        "n_cycles": int(n), "n_fields": int(len(fields_sorted)),
        "det_by_cell": det_by_cell, "field_by_cell": field_by_cell,
        "clean_far_cycle_level": float(np.mean([
            mscoring.alarm_per_cycle(clean_paths[i], tau, k) for i in range(n)])),
    }


def final_test_severity(args) -> int:
    """Locked final test of the severity protocol (run ONCE; the only test
    reader). Sweeps the frozen seed of the main model AND B1 on the test
    split with their DEV-calibrated (τ, k, per-cell normalizer) from the
    severity metrics files, evaluates the dual-axis pre-registered target and
    writes reports/final_test_<model>_severity.json."""
    manifest = msplits.load_splits_locked()
    main_metrics = json.loads(
        _severity_metrics_path(args.model, args.run_id, args.scorer).read_text(encoding="utf-8"))
    sidecar_path = REPO_ROOT / "checkpoints" / f"{MODEL_ID_MAP[args.model]}.json"
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    seed = sidecar["frozen_seed"]
    entry = _frozen_seed_entry(main_metrics, sidecar)
    tau, k = entry["tau"], entry["k"]
    cell_q95 = np.array(entry["per_bin_q95"], dtype=np.float64).reshape(36, 8)

    # The ONLY test-split access in the codebase:
    data = minputs.load_masked_cycles()
    sel = mproto.select_splits(data, manifest, splits=("test",), allow_test=True)
    X, M = sel["X"], sel["M"]
    doy = minputs.doy_channels(sel["harvest_days"])
    field_ids = sel["field_ids"]

    scorer, norm, params, _cfg = load_scorer_and_norm(args.model, seed, args.run_id, "cpu")
    print(f"[final-test:severity] main {MODEL_ID_MAP[args.model]} seed {seed} "
          f"tau={tau:.4f} k={k}; test cycles={X.shape[0]}")
    main_res = severity_sweep_on_split(
        scorer, norm, X, M, doy, tau, k, cell_q95, field_ids,
        rounds=1, seed_base=77_000 + seed, bootstrap=args.bootstrap)

    # B1: dev-calibrated severity metrics of the b1 run (same date suffix).
    suffix = args.run_id.rsplit("_", 1)[1] if "_" in args.run_id else time.strftime("%Y%m%d")
    b1_run_id = f"b1_{suffix}"
    b1_metrics_path = mproto.DEV_DIR / b1_run_id / f"metrics_b1_sev_{args.scorer}.json"
    b1_metrics = json.loads(b1_metrics_path.read_text(encoding="utf-8"))
    b1_entry = ([r for r in b1_metrics["per_seed"] if r["seed"] == seed] or b1_metrics["per_seed"])[0]
    b1 = load_b1(b1_run_id, seed)
    b1_res = severity_sweep_on_split(
        b1, None, X, M, doy, b1_entry["tau"], b1_entry["k"],
        np.array(b1_entry["per_bin_q95"], dtype=np.float64).reshape(36, 8), field_ids,
        rounds=1, seed_base=88_000 + seed, bootstrap=args.bootstrap)

    # ---- Dual-axis pre-registered target --------------------------------
    # gru_pred (predictive-ssl-controlled-trial): the finding-18 dual-axis
    # target is NOT imported into this trial — the trial's own five gates
    # govern the decision; the final test records the sweep for the report
    # only and the rung stays L2 (all trial claims are L2 synthetic-anomaly
    # claims).
    trial_mode = args.model == "gru_pred"
    primary_key = "/".join(PRIMARY_CELL)
    a_margin = main_res["cells"][primary_key]["detection_rate"] - b1_res["cells"][primary_key]["detection_rate"]
    a_evaluable = (main_res["cells"][primary_key]["n"] > 0 and b1_res["cells"][primary_key]["n"] > 0)
    target_a = bool(a_evaluable and a_margin >= 0.05)

    b_pairs = {}
    both_censored_all = True
    for fam in (sev.ACUTE_FAMILY, sev.PERSISTENT_FAMILY):
        for index in ("ndvi", "savi"):
            key = f"{fam}/{index}"
            ms, bs = main_res["mdm80"][key], b1_res["mdm80"][key]
            both_censored = ms["censored"] and bs["censored"]
            both_censored_all = both_censored_all and both_censored
            b_pairs[key] = {
                "main": ms["value"], "b1": bs["value"],
                "main_sentinel": ms["sentinel"], "b1_sentinel": bs["sentinel"],
                "main_leq_b1": ms["sentinel"] <= bs["sentinel"],
                "evaluable": not both_censored,
            }
    # (b) counts as met only when it is evaluable as an advantage: an
    # equal-by-censoring tie (both arms ">S6") carries no information.
    primary_pair = b_pairs[f"{sev.ACUTE_FAMILY}/ndvi"]
    target_b = bool(primary_pair["evaluable"] and primary_pair["main_leq_b1"])

    # Dev-side 3-seed ranges (the spec's non-overlap wording lives on dev):
    if trial_mode:
        dev_a = dev_b = None
        overall = None
        ladder = "L2"
    else:
        dev_a = _dev_margin_check(main_metrics, b1_metrics, PRIMARY_CELL)
        dev_b = _dev_mdm80_check(main_metrics, b1_metrics)
        overall = bool(target_a or target_b or dev_a["met"] or dev_b["met"])
        ladder = "L3" if overall else "L2"

    report = {
        "type": "final_test_severity",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "git_sha": mproto.git_sha(),
        "model_id": MODEL_ID_MAP[args.model],
        "scorer": args.scorer,
        "protocol": "severity_sweep_v1",
        "severity_table_sha256": main_metrics["severity_table_sha256"],
        "frozen_seed": seed,
        "n_test_cycles": int(X.shape[0]),
        "n_test_fields": int(np.unique(field_ids).size),
        "date_range": {
            "first": str(sel["start_dates"][0])[:10],
            "last": str(sel["end_dates"][-1])[:10],
        },
        "splits_locked_sha256": manifest["manifest_sha256"],
        "far_target": 0.05,
        "threshold_source": "dev severity metrics (frozen seed); platform sidecar threshold block untouched",
        "main": {k: main_res[k] for k in ("cells", "mdm80", "event_far_clean",
                                          "clean_far_cycle_level", "n_cycles", "n_fields")},
        "b1": {k: b1_res[k] for k in ("cells", "mdm80", "event_far_clean",
                                      "clean_far_cycle_level", "n_cycles", "n_fields")},
        "target": {
            "pre_registered_primary_cell": "/".join(PRIMARY_CELL),
            "a_margin_observed": a_margin, "a_met_test": target_a,
            "a_dev_3seed": dev_a,
            "b_pairs": b_pairs, "b_met_test": target_b, "b_dev_3seed": dev_b,
            "met": overall,
            "trial_mode": bool(trial_mode),
            "note": ("(a) margin ≥ 0.05 at the pre-registered S3/acute/ndvi cell; "
                     "(b) MDM80(main) ≤ MDM80(B1); a both-censored tie is NOT an "
                     "advantage and does not meet (b). Dev-side: 3-seed ranges.")
                    if not trial_mode else
                    ("gru_pred trial mode: the finding-18 dual-axis target is NOT "
                     "imported — the predictive-ssl-controlled-trial's five "
                     "pre-registered gates govern; this report records the locked "
                     "test sweep for the trial readout; ladder stays L2."),
        },
        "ladder_rung_result": ladder,
        "claim_noun": "synthetic anomaly",
        "ladder_rung_claim": "L2",
        "note": (
            "Severity sweep on locked test (synthetic anomalies; 'stress' naming "
            "not used). L3 only when the pre-registered dual-axis target holds; "
            "L4 (real-stress agreement) remains future work."
        ),
    }
    out = REPO_ROOT / "reports" / f"final_test_{MODEL_ID_MAP[args.model]}_severity.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    sidecar["ladder_rung"] = ladder
    sidecar["final_test_severity_file"] = str(out.relative_to(REPO_ROOT))
    sidecar["manifest_sha256"] = json.dumps(
        {k: sidecar[k] for k in sorted(sidecar)}, sort_keys=True, default=str
    )
    sidecar_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")

    print(json.dumps({
        "target_a_margin": a_margin, "target_a_met": target_a,
        "target_b_pairs": {k: (v["main"], v["b1"], v["evaluable"]) for k, v in b_pairs.items()},
        "target_b_met": target_b, "ladder_rung_result": ladder,
        "trial_mode": trial_mode,
    }, indent=2, default=str))
    print(f"[final-test] report → {out}")
    if trial_mode:
        print("[final-test] gru_pred trial mode: five gates of "
              "predictive-ssl-controlled-trial govern; rung stays L2.")
    elif not overall:
        print("[final-test] dual-axis target NOT met — honest negative recorded "
              "(spec: no goalpost moving, rung stays L2).")
    return 0


def _dev_margin_check(main_metrics: dict, b1_metrics: dict, cell: tuple[str, str, str]) -> dict:
    """Dev-side target (a): per-seed detection margins at the pre-registered
    cell; met iff main ≥ B1 + 0.05 with non-overlapping 3-seed ranges."""
    key = "/".join(cell)
    main_vals = [r["cells"][key]["detection_rate"] for r in main_metrics["per_seed"]]
    b1_vals = [r["cells"][key]["detection_rate"] for r in b1_metrics["per_seed"]]
    lo_main, hi_main = min(main_vals), max(main_vals)
    lo_b1, hi_b1 = min(b1_vals), max(b1_vals)
    gap = lo_main - hi_b1
    return {
        "cell": key, "main_per_seed": main_vals, "b1_per_seed": b1_vals,
        "gap_nonoverlap": gap,
        "met": bool(gap >= 0.05),
    }


def _dev_mdm80_check(main_metrics: dict, b1_metrics: dict) -> dict:
    """Dev-side target (b): MDM80 sentinels per family × index; a pair is met
    iff main ≤ B1 AND at least one side is uncensored (a both-censored tie is
    not an advantage)."""
    pairs = {}
    met_all = True
    for fam in (sev.ACUTE_FAMILY, sev.PERSISTENT_FAMILY):
        for index in ("ndvi", "savi"):
            key = f"{fam}/{index}"
            mv = [r["mdm80"][key]["sentinel"] for r in main_metrics["per_seed"]]
            bv = [r["mdm80"][key]["sentinel"] for r in b1_metrics["per_seed"]]
            evaluable = not (max(mv) == MDM80_CENSORED and max(bv) == MDM80_CENSORED)
            pair_met = evaluable and max(mv) <= min(bv)
            met_all = met_all and pair_met
            pairs[key] = {"main_sentinels": mv, "b1_sentinels": bv,
                          "evaluable": evaluable, "met": pair_met}
    return {"pairs": pairs, "met": bool(met_all)}


if __name__ == "__main__":
    raise SystemExit(main())
