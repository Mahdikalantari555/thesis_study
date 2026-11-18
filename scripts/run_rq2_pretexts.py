# ruff: noqa: E402
#!/usr/bin/env python3
"""RQ2 (Gap G3): Controlled comparison of three SSL pretext objectives under matched budgets.

Compares on the identical 1D Transformer backbone (d_model=64, n_layers=3, ~161K params),
epoch schedule, and learning rate across 5 seeds:
  1. ``masked_recon`` (Masked Observation Reconstruction)
  2. ``traj_contrastive`` (Trajectory-Contrastive InfoNCE)
  3. ``anomaly_degradation`` (AnomalyBERT-style Self-Supervised Degradation Discrimination)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from ssl_anomaly.utils.throttle import limit_threads

limit_threads(2)

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import average_precision_score, roc_auc_score

torch.set_num_threads(2)

from ssl_anomaly.baseline import recall_at_alert_budget
from ssl_anomaly.eval import (
    add_source_argument,
    build_provenance,
    load_real490_archive,
    simulate_490_field_archive,
    simulated_output_path,
)
from ssl_anomaly.eval.stats import bootstrap_ci, spearman_correlation
from ssl_anomaly.models.pretexts import PRETEXT_ARMS, score_cycle_pretext, train_pretext_arm
from ssl_anomaly.utils.logging import get_logger

log = get_logger("ssl_anomaly.scripts.rq2")

PERTURB_KINDS = ("ndvi_drop", "lst_spike", "phase_shift", "early_senescence")


class _SimpleRecord:
    """Minimal record adapter for real490/simulated archives used by RQ2."""

    def __init__(self, tokens, is_validation, field_id, cycle_id):
        self.tokens = tokens
        self.is_validation = is_validation
        self.field_id = field_id
        self.cycle_id = cycle_id


def _resolve_band(bands: list[str], aliases: dict | None, *names: str) -> int | None:
    """Map a Landsat-style band name onto a column index of ``bands``.

    ``bands`` on the real490 archive is lowercase (``red``/``nir``/``lst``/
    ``ndvi``) while the simulator and the 32-farm zarr use Sentinel/Landsat
    codes (``SR_B4``/``SR_B5``/``ST_B10``). Try the literal name first, then the
    archive's own alias table, then the English equivalent.
    """
    bmap = {b: i for i, b in enumerate(bands)}
    for n in names:
        if n in bmap:
            return bmap[n]
    for n in names:
        if aliases and n in aliases:
            return int(aliases[n])
    return None


def _perturb_tokens(
    tok_arr: np.ndarray,
    bands: list[str],
    kind: str,
    rng: np.random.Generator,
    aliases: dict | None = None,
) -> np.ndarray:
    out = tok_arr.copy()
    T = out.shape[0]
    r_i = _resolve_band(bands, aliases, "SR_B4", "red")
    n_i = _resolve_band(bands, aliases, "SR_B5", "nir")
    nd_i = _resolve_band(bands, aliases, "NDVI", "ndvi")
    lst_i = _resolve_band(bands, aliases, "ST_B10", "lst")
    L = min(4, max(2, T // 5))
    s = int(rng.integers(1, max(2, T - L)))

    if kind == "ndvi_drop":
        if n_i is not None:
            out[s : s + L, n_i] -= 2.8
        if nd_i is not None:
            out[s : s + L, nd_i] -= 3.0
        if r_i is not None:
            out[s : s + L, r_i] += 2.0
    elif kind == "lst_spike":
        if lst_i is not None:
            out[s : s + L, lst_i] += 3.2
    elif kind == "phase_shift":
        out[:, : len(bands)] = np.roll(out[:, : len(bands)], shift=max(2, T // 5), axis=0)
    elif kind == "early_senescence":
        st = int(0.65 * T)
        ramp = np.linspace(0.5, 3.0, max(1, T - st), dtype=np.float32)
        if n_i is not None:
            out[st:, n_i] -= ramp
        if nd_i is not None:
            out[st:, nd_i] -= ramp
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="RQ2 controlled 3-arm SSL pretext comparison.")
    add_source_argument(ap, default="real490")
    ap.add_argument("--zarr", default=None, type=Path)
    ap.add_argument("--cycles", default=None, type=Path)
    ap.add_argument("--epochs", default=45, type=int)
    ap.add_argument("--seeds", default="42,43,44,45,46", type=str)
    ap.add_argument("--out", default="reports/rq2_pretexts.json", type=Path)
    args = ap.parse_args()

    source = args.source
    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    out_path = args.out

    if source == "real490":
        archive = load_real490_archive()  # fail-closed
        prov = build_provenance(archive, seeds=seeds)
    elif source == "simulated":
        archive = simulate_490_field_archive(n_fields=490, n_years=13.5, seed=seeds[0])
        archive["provenance"] = {
            "data_source": "simulated",
            "n_fields": int(np.unique(archive["field_ids"]).size),
            "n_cycles": archive["X"].shape[0],
            "n_dates": 0,
            "first_acquisition_date": "",
            "last_acquisition_date": "",
            "cycle_file_sha256": "simulated",
            "git_sha": "unknown",
            "splits_sha256": "unknown",
            "seeds": seeds,
            "y_stress_proxy": "simulated_top20pct_cwsi",
            "eta_deficit_source": "simulated",
            "cwsi_source": "simulated",
        }
        prov = archive["provenance"]
        out_path = simulated_output_path(args.out)
    elif source == "real32":
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from compare_ssl_models import _load_records_and_cwsi

        records, tok, bands, cwsi_arr = _load_records_and_cwsi(args.zarr or Path("data/processed/fields.zarr"),
                                                               args.cycles or Path("data/processed/cycles.parquet"))
        n_bands = len(bands)
        train_toks = [r.tokens for r in records if not r.is_validation]
        all_toks_clean = [r.tokens for r in records]

        arm_summary: dict[str, dict] = {}
        for arm in PRETEXT_ARMS:
            prs, rocs, rec5s, rec10s, times_s = [], [], [], [], []
            per_kind: dict[str, list[float]] = {k: [] for k in PERTURB_KINDS}
            real_scores_seeds = []
            n_params = 0

            for seed in seeds:
                t0 = time.perf_counter()
                model = train_pretext_arm(
                    arm, train_toks, n_bands, epochs=args.epochs, batch_size=16, lr=1.2e-3, seed=seed
                )
                times_s.append(time.perf_counter() - t0)
                n_params = int(sum(p.numel() for p in model.parameters() if p.requires_grad))

                with torch.no_grad():
                    ref_embs = np.stack(
                        [model.encode_sequence(torch.from_numpy(t).unsqueeze(0))[1][0].numpy() for t in train_toks],
                        axis=0,
                    )

                real_sc = np.array([score_cycle_pretext(model, t, ref_embs) for t in all_toks_clean])
                real_scores_seeds.append(real_sc)

                rng = np.random.default_rng(seed + 200)
                s_prs, s_rocs, s_r5, s_r10 = [], [], [], []
                for kind in PERTURB_KINDS:
                    pert = [_perturb_tokens(t, bands, kind, rng) for t in all_toks_clean]
                    sc_clean = np.array([score_cycle_pretext(model, t, ref_embs) for t in all_toks_clean])
                    sc_pert = np.array([score_cycle_pretext(model, t, ref_embs) for t in pert])
                    sc_15 = np.concatenate([np.tile(sc_clean, 5), sc_pert])

                    yt_15 = np.array([0] * len(all_toks_clean) * 5 + [1] * len(pert), dtype=np.int32)
                    yt_50 = np.array([0] * len(all_toks_clean) + [1] * len(pert), dtype=np.int32)
                    sc_50 = np.concatenate([sc_clean, sc_pert])
                    ap = float(average_precision_score(yt_50, sc_50))
                    roc = float(roc_auc_score(yt_50, sc_50))
                    r5 = recall_at_alert_budget(yt_15, sc_15, alert_rate=0.05)
                    r10 = recall_at_alert_budget(yt_15, sc_15, alert_rate=0.10)

                    s_prs.append(ap)
                    s_rocs.append(roc)
                    s_r5.append(r5)
                    s_r10.append(r10)
                    per_kind[kind].append(ap)

                prs.append(float(np.mean(s_prs)))
                rocs.append(float(np.mean(s_rocs)))
                rec5s.append(float(np.mean(s_r5)))
                rec10s.append(float(np.mean(s_r10)))

            pr_m, pr_lo, pr_hi = bootstrap_ci(np.mean, np.array(prs), n_boot=1000, seed=42)
            roc_m, roc_lo, roc_hi = bootstrap_ci(np.mean, np.array(rocs), n_boot=1000, seed=42)
            mean_real = np.mean(real_scores_seeds, axis=0)
            rho_cw, p_cw = spearman_correlation(mean_real, cwsi_arr)

            arm_summary[arm] = {
                "n_parameters": n_params,
                "mean_train_seconds": float(np.mean(times_s)),
                "auc_pr": pr_m,
                "auc_pr_ci_95": [pr_lo, pr_hi],
                "auc_roc": roc_m,
                "auc_roc_ci_95": [roc_lo, roc_hi],
                "recall_at_5pct_budget": float(np.mean(rec5s)),
                "recall_at_10pct_budget": float(np.mean(rec10s)),
                "per_perturbation_auc_pr": {k: float(np.mean(per_kind[k])) for k in PERTURB_KINDS},
                "cwsi_spearman_rho": rho_cw,
                "cwsi_pval": p_cw,
            }

        report = {
            "provenance": {
                "data_source": "real32",
                "n_fields": len(set(archive["field_ids"]) if isinstance(archive, dict) and "field_ids" in archive else 0),
                "n_cycles": archive["X"].shape[0] if isinstance(archive, dict) else 0,
                "seeds": seeds,
            },
            "data_source": "real32",
            "backbone": "PretextTransformer(d_model=64, n_heads=4, n_layers=3)",
            "epochs": args.epochs,
            "seeds": seeds,
            "arms": arm_summary,
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2))

        rows = [
            {
                "pretext_arm": arm,
                "data_source": "real32",
                "n_params": m["n_parameters"],
                "train_sec": m["mean_train_seconds"],
                "auc_pr": m["auc_pr"],
                "auc_pr_ci_lo": m["auc_pr_ci_95"][0],
                "auc_pr_ci_hi": m["auc_pr_ci_95"][1],
                "auc_roc": m["auc_roc"],
                "recall_at_5pct": m["recall_at_5pct_budget"],
                "recall_at_10pct": m["recall_at_10pct_budget"],
                "ndvi_drop_pr": m["per_perturbation_auc_pr"]["ndvi_drop"],
                "lst_spike_pr": m["per_perturbation_auc_pr"]["lst_spike"],
                "phase_shift_pr": m["per_perturbation_auc_pr"]["phase_shift"],
                "early_senescence_pr": m["per_perturbation_auc_pr"]["early_senescence"],
                "cwsi_rho": m["cwsi_spearman_rho"],
            }
            for arm, m in arm_summary.items()
        ]
        df = pd.DataFrame(rows)
        df.to_csv(out_path.with_suffix(".csv"), index=False)
        print("\n=== RQ2 Controlled SSL Pretext Comparison (real32, 5 Seeds) ===")
        print(df.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
        return 0
    else:
        log.error("Unknown source: %s", source)
        return 1

    # Build records from archive (real490 or simulated)
    bands = archive.get("bands", ["ndvi", "blue", "green", "red", "nir", "swir1", "swir2", "lst"])
    band_aliases = archive.get("band_aliases") or {}
    n_bands = len(bands)
    X = archive["X"]
    field_ids = archive["field_ids"]

    # Real 490-field archive carries NaN for cloud-masked / unobserved cells
    # (about 36% of values). The pretext objectives treat a zeroed band vector as
    # "no observation" and none of the arms sanitise non-finite input, so NaN in
    # propagates through the reconstruction / embedding and turns every score into
    # NaN, which then makes average_precision_score raise. Follow the existing
    # in-repo convention (see eval/cloud_robustness.py, eval/early_detection.py)
    # and map non-finite cells to 0.0 once, before the tokens reach the model.
    n_nan_cells = int(np.isnan(X).sum())
    if n_nan_cells:
        log.info(
            "Sanitising %d non-finite cells (%.1f%%) in archive X before pretext training/scoring",
            n_nan_cells,
            100.0 * float(np.isnan(X).mean()),
        )
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

    # Create simple records from archive X data
    records = []
    for i in range(len(X)):
        records.append(_SimpleRecord(
            tokens=X[i],
            is_validation=False,
            field_id=int(field_ids[i]),
            cycle_id=i,
        ))

    train_toks = [r.tokens for r in records]
    all_toks_clean = [r.tokens for r in records]

    arm_summary: dict[str, dict] = {}
    for arm in PRETEXT_ARMS:
        prs, rocs, rec5s, rec10s, times_s = [], [], [], [], []
        per_kind: dict[str, list[float]] = {k: [] for k in PERTURB_KINDS}
        real_scores_seeds = []
        n_params = 0

        for seed in seeds:
            t0 = time.perf_counter()
            model = train_pretext_arm(
                arm, train_toks, n_bands, epochs=args.epochs, batch_size=16, lr=1.2e-3, seed=seed
            )
            times_s.append(time.perf_counter() - t0)
            n_params = int(sum(p.numel() for p in model.parameters() if p.requires_grad))

            with torch.no_grad():
                ref_embs = np.stack(
                    [model.encode_sequence(torch.from_numpy(t).unsqueeze(0))[1][0].numpy() for t in train_toks],
                    axis=0,
                )

            real_sc = np.array([score_cycle_pretext(model, t, ref_embs) for t in all_toks_clean])
            real_scores_seeds.append(real_sc)

            rng = np.random.default_rng(seed + 200)
            s_prs, s_rocs, s_r5, s_r10 = [], [], [], []
            for kind in PERTURB_KINDS:
                pert = [_perturb_tokens(t, bands, kind, rng, aliases=band_aliases) for t in all_toks_clean]
                sc_clean = np.array([score_cycle_pretext(model, t, ref_embs) for t in all_toks_clean])
                sc_pert = np.array([score_cycle_pretext(model, t, ref_embs) for t in pert])
                sc_15 = np.concatenate([np.tile(sc_clean, 5), sc_pert])

                yt_15 = np.array([0] * len(all_toks_clean) * 5 + [1] * len(pert), dtype=np.int32)
                yt_50 = np.array([0] * len(all_toks_clean) + [1] * len(pert), dtype=np.int32)
                sc_50 = np.concatenate([sc_clean, sc_pert])

                if not (np.isfinite(sc_50).all() and np.isfinite(sc_15).all()):
                    n_bad = int((~np.isfinite(sc_50)).sum() + (~np.isfinite(sc_15)).sum())
                    log.warning(
                        "Arm %s seed %d kind %s produced %d non-finite anomaly scores; "
                        "AUC-PR/recall undefined for this arm-kind, skipping it.",
                        arm, seed, kind, n_bad,
                    )
                    continue

                ap = float(average_precision_score(yt_50, sc_50))
                roc = float(roc_auc_score(yt_50, sc_50))
                r5 = recall_at_alert_budget(yt_15, sc_15, alert_rate=0.05)
                r10 = recall_at_alert_budget(yt_15, sc_15, alert_rate=0.10)

                s_prs.append(ap)
                s_rocs.append(roc)
                s_r5.append(r5)
                s_r10.append(r10)
                per_kind[kind].append(ap)

            if not s_prs:
                log.warning(
                    "Arm %s seed %d produced no finite anomaly scores for any perturbation kind; "
                    "skipping this seed.",
                    arm, seed,
                )
                continue

            prs.append(float(np.mean(s_prs)))
            rocs.append(float(np.mean(s_rocs)))
            rec5s.append(float(np.mean(s_r5)))
            rec10s.append(float(np.mean(s_r10)))

        if not prs:
            log.error(
                "Arm %s produced no usable AUC-PR across %d seeds; recording it as not_run.",
                arm, len(seeds),
            )
            arm_summary[arm] = {
                "status": "not_run",
                "note": (
                    "No finite anomaly scores were produced for this pretext arm, so "
                    "AUC-PR / AUC-ROC / recall are undefined. This happens on the real "
                    "490-field archive before CWSI/ETa zonal extraction is wired, where "
                    "--source simulated is the only source with scoreable labels."
                ),
                "n_parameters": n_params,
                "mean_train_seconds": float(np.mean(times_s)) if times_s else float("nan"),
                "auc_pr": float("nan"),
                "auc_pr_ci_95": [float("nan"), float("nan")],
                "auc_roc": float("nan"),
                "auc_roc_ci_95": [float("nan"), float("nan")],
                "recall_at_5pct_budget": float("nan"),
                "recall_at_10pct_budget": float("nan"),
                "per_perturbation_auc_pr": {k: float("nan") for k in PERTURB_KINDS},
                "cwsi_spearman_rho": float("nan"),
                "cwsi_pval": float("nan"),
            }
            continue

        pr_m, pr_lo, pr_hi = bootstrap_ci(np.mean, np.array(prs), n_boot=1000, seed=42)
        roc_m, roc_lo, roc_hi = bootstrap_ci(np.mean, np.array(rocs), n_boot=1000, seed=42)
        mean_real = np.mean(real_scores_seeds, axis=0)

        arm_summary[arm] = {
            "n_parameters": n_params,
            "mean_train_seconds": float(np.mean(times_s)),
            "auc_pr": pr_m,
            "auc_pr_ci_95": [pr_lo, pr_hi],
            "auc_roc": roc_m,
            "auc_roc_ci_95": [roc_lo, roc_hi],
            "recall_at_5pct_budget": float(np.mean(rec5s)),
            "recall_at_10pct_budget": float(np.mean(rec10s)),
            "per_perturbation_auc_pr": {k: float(np.mean(per_kind[k])) for k in PERTURB_KINDS},
            "cwsi_spearman_rho": float("nan"),
            "cwsi_pval": float("nan"),
        }

    report = {
        "provenance": prov,
        "data_source": prov["data_source"],
        "source": source,
        "n_fields": prov["n_fields"],
        "n_cycles": prov["n_cycles"],
        "backbone": "PretextTransformer(d_model=64, n_heads=4, n_layers=3)",
        "epochs": args.epochs,
        "seeds": seeds,
        "arms": arm_summary,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))

    rows = [
        {
            "pretext_arm": arm,
            "data_source": prov["data_source"],
            "n_params": m["n_parameters"],
            "train_sec": m["mean_train_seconds"],
            "auc_pr": m["auc_pr"],
            "auc_pr_ci_lo": m["auc_pr_ci_95"][0],
            "auc_pr_ci_hi": m["auc_pr_ci_95"][1],
            "auc_roc": m["auc_roc"],
            "recall_at_5pct": m["recall_at_5pct_budget"],
            "recall_at_10pct": m["recall_at_10pct_budget"],
            "ndvi_drop_pr": m["per_perturbation_auc_pr"]["ndvi_drop"],
            "lst_spike_pr": m["per_perturbation_auc_pr"]["lst_spike"],
            "phase_shift_pr": m["per_perturbation_auc_pr"]["phase_shift"],
            "early_senescence_pr": m["per_perturbation_auc_pr"]["early_senescence"],
            "cwsi_rho": m["cwsi_spearman_rho"],
        }
        for arm, m in arm_summary.items()
    ]
    df = pd.DataFrame(rows)
    df.to_csv(out_path.with_suffix(".csv"), index=False)
    print(f"\n=== RQ2 Controlled SSL Pretext Comparison (source={prov['data_source']}, {len(seeds)} Seeds) ===")
    print(df.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
