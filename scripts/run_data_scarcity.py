#!/usr/bin/env python3
# ruff: noqa: E402
"""DS1-DS5 data-scarcity & representation-quality diagnostics (Finding 12).

Answers the advisor's question — *does the model actually suffer from data
scarcity on the available archive?* — with the literature-standard
instruments, per pretext arm and seed:

  DS1  learning curve: downstream AUC-PR vs. fraction of training cycles
  DS2  train-vs-validation gap from per-epoch loss history (inner 85/15 split)
  DS3  SSL representation quality on frozen embeddings: mean pairwise cosine
       similarity (collapse), Wang & Isola alignment/uniformity, effective
       rank, t-SNE projection (PNG + coords in JSON)
  DS4  few-shot downstream: LogisticRegression on frozen embeddings with
       1% / 5% / 10% of the labels (weak-proxy labels, explicitly NOT
       validated stress)
  DS5  variance across seeds and Leave-One-Year-Out folds

Runs on the real 32-farm ``fields.zarr`` (539 Landsat dates, 2013-2026) when
available, or on the calibrated 490-field × 13.5-year simulator
(``--simulate-490-if-missing`` / ``--source simulate490``).

Outputs: ``reports/data_scarcity.json``, ``reports/data_scarcity.csv``,
``reports/figures/data_scarcity_*.png``.

Usage:
  python scripts/run_data_scarcity.py
  python scripts/run_data_scarcity.py --source simulate490 --max-loyo-years 4
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from ssl_anomaly.eval import (
    add_source_argument,
    build_provenance,
    load_real490_archive,
    require_real_archive,
    simulated_output_path,
)
from ssl_anomaly.utils.throttle import limit_threads

limit_threads(2)

import numpy as np
import pandas as pd
import torch

torch.set_num_threads(2)

from sklearn.metrics import average_precision_score

from ssl_anomaly.eval.data_scarcity import (
    DEFAULT_FEW_SHOT_FRACTIONS,
    DEFAULT_FRACTIONS,
    embedding_quality_report,
    few_shot_probe,
    learning_curve,
    summarize_train_val_history,
    tsne_projection,
)
from ssl_anomaly.eval.probing import extract_frozen_embeddings
from ssl_anomaly.models.pretexts import (
    score_cycle_pretext,
    train_pretext_arm,
    train_pretext_arm_tracked,
)
from ssl_anomaly.utils.logging import get_logger

log = get_logger("ssl_anomaly.scripts.data_scarcity")

WEAK_PROXY_LABEL_NOTE = (
    "weak_proxy_top20pct_mean_cwsi_not_validated_stress"
)

REAL490_REQUIRED_KEYS = ("tokens", "field_ids", "years", "bands")


def _real490_to_tokens(X: np.ndarray, bands: list[str]) -> list[np.ndarray]:
    """Convert real490 archive X (N, K, C) into token list compatible with data-scarcity tooling."""
    K = X.shape[1]
    tau = np.linspace(0.0, 1.0, K, dtype=np.float32)[:, None]
    med = np.nanmedian(X, axis=0)
    mad = np.maximum(np.nanmedian(np.abs(X - med[None, :, :]), axis=0) * 1.4826, 1e-4)
    tokens = []
    for i in range(len(X)):
        z = np.nan_to_num((X[i] - med) / mad, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
        tokens.append(np.hstack([z, tau]).astype(np.float32))
    return tokens


def _ensure_cycles_parquet(zarr_p: Path, cyc_p: Path) -> Path:
    """Build ``cycles.parquet`` from ``fields.zarr`` via harvest segmentation if missing."""
    if cyc_p.exists():
        return cyc_p
    import xarray as xr

    from ssl_anomaly.phenology.cycles import segment_cycles

    ds = xr.open_zarr(zarr_p)
    times = ds.coords["time"].values
    epoch = times[0]
    days = (times - epoch).astype("timedelta64[D]").astype(int)
    ndvi = ds["ndvi"].values
    valid = ds["valid_frac"].values
    fields = ds.coords["field"].values
    rows = []
    for fi, fid in enumerate(fields):
        cycles = segment_cycles(
            int(fid), days, ndvi[fi], quality=valid[fi], min_cycle_days=180, max_cycle_days=540
        )
        rows.extend(c.to_dict() for c in cycles)
    df = pd.DataFrame(rows)
    cyc_p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cyc_p)
    log.info("wrote %s (%d cycles)", cyc_p, len(df))
    return cyc_p


def _load_real_archive(zarr_p: Path, cyc_p: Path) -> dict:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import xarray as xr
    from compare_ssl_models import _load_records_and_cwsi

    cyc_p = _ensure_cycles_parquet(zarr_p, cyc_p)
    records, tok, bands, cwsi_arr = _load_records_and_cwsi(zarr_p, cyc_p)

    ds = xr.open_zarr(zarr_p)
    epoch = ds.coords["time"].values[0]
    n_dates = int(ds.sizes["time"])
    cycles_df = pd.read_parquet(cyc_p)
    year_of: dict[tuple[int, int], int] = {}
    for _, row in cycles_df.iterrows():
        if row["censored"]:
            continue
        y = (epoch + np.timedelta64(int(row["t_start"]), "D")).astype("datetime64[Y]").astype(int) + 1970
        year_of[(int(row["field"]), int(row["cycle_id"]))] = int(y)

    years = np.array([year_of.get((r.field_id, r.cycle_id), -1) for r in records], dtype=int)
    finite = np.isfinite(cwsi_arr)
    thr = np.nanquantile(cwsi_arr[finite], 0.80) if finite.any() else np.nan
    labels = np.where(finite & (cwsi_arr >= thr), 1, 0).astype(int)

    return {
        "source": "real_32_farm_zarr",
        "tokens": [r.tokens for r in records],
        "train_mask": np.array([not r.is_validation for r in records], dtype=bool),
        "field_ids": np.array([r.field_id for r in records], dtype=int),
        "years": years,
        "labels": labels,
        "bands": list(bands),
        "n_bands": len(bands),
        "n_fields": int(len({r.field_id for r in records})),
        "n_dates": n_dates,
        "label_source": WEAK_PROXY_LABEL_NOTE,
        "epoch": epoch,
        "cycles_df": cycles_df,
    }


def _load_real490_archive(seed: int = 42) -> dict:
    """Load the real 490-field archive via load_real490_archive (fail-closed)."""
    archive = load_real490_archive()
    X = archive["X"]
    bands = archive["bands"]
    field_ids = archive["field_ids"]
    years = archive["start_years"]
    labels = archive.get("y_stress", np.zeros(len(X))).astype(int)
    n_dates = archive.get("provenance", {}).get("n_dates", None)

    tokens = _real490_to_tokens(X, bands)

    # Reserve last 6 fields as validation holdout
    all_fields = sorted(set(field_ids.tolist()))
    val_fields = set(all_fields[-6:]) if len(all_fields) >= 6 else set()
    train_mask = np.array([int(f) not in val_fields for f in field_ids], dtype=bool)

    return {
        "source": "real490",
        "tokens": tokens,
        "train_mask": train_mask,
        "field_ids": field_ids,
        "years": years,
        "labels": labels,
        "bands": list(bands),
        "n_bands": len(bands),
        "n_fields": len(all_fields),
        "n_dates": n_dates,
        "label_source": "weak_proxy_top20pct_mean_cwsi_not_validated_stress (absent -> zeros)",
        "epoch": None,
        "cycles_df": None,
        "provenance": archive.get("provenance", {}),
    }


def _load_simulated_archive(seed: int = 42) -> dict:
    from ssl_anomaly.eval.cv import simulate_490_field_archive

    arch = simulate_490_field_archive(seed=seed)
    X = arch["X"]
    fids = np.asarray(arch["field_ids"], dtype=int)
    years = np.asarray(arch["start_years"], dtype=int)
    labels = np.asarray(arch["y_stress"], dtype=int)
    bands = list(arch["bands"])
    all_fields = sorted(set(fids.tolist()))
    val_fields = set(all_fields[-6:]) if len(all_fields) >= 6 else set()
    train_mask = np.array([f not in val_fields for f in fids], dtype=bool)
    return {
        "source": "simulated_490_field_13_5yr_calibrated_fallback",
        "tokens": [np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32) for x in X],
        "train_mask": train_mask,
        "field_ids": fids,
        "years": years,
        "labels": labels,
        "bands": bands,
        "n_bands": len(bands),
        "n_fields": len(all_fields),
        "n_dates": None,
        "label_source": "simulated_y_stress_labels (simulated scaling check only)",
        "epoch": None,
        "cycles_df": None,
    }


def _perturb_pool(tokens: list[np.ndarray], bands: list[str], seed: int) -> tuple[list[np.ndarray], np.ndarray]:
    """Fixed perturbed-vs-clean evaluation pool (same construction as RQ2)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from run_rq2_pretexts import PERTURB_KINDS, _perturb_tokens

    rng = np.random.default_rng(seed + 999)
    clean = list(tokens)
    pert: list[np.ndarray] = []
    for kind in PERTURB_KINDS:
        pert.extend(_perturb_tokens(t, bands, kind, rng) for t in tokens)
    pool = clean + pert
    y = np.array([0] * len(clean) + [1] * len(pert), dtype=np.int32)
    return pool, y


def _auc_pr_on_pool(model, pool: list[np.ndarray], y: np.ndarray, ref_tokens: list[np.ndarray], n_bands: int) -> float:
    with torch.no_grad():
        ref = extract_frozen_embeddings(model, ref_tokens) if model.arm != "masked_recon" else None
        if model.arm == "masked_recon":
            ref = None
        scores = np.array([score_cycle_pretext(model, t, ref) for t in pool])
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(average_precision_score(y, scores))


def _make_figures(out_dir: Path, arm: str, tsne_coords: np.ndarray, labels: np.ndarray, lc: dict) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(5, 4))
    sc = ax.scatter(tsne_coords[:, 0], tsne_coords[:, 1], c=labels, cmap="coolwarm", s=18, alpha=0.8)
    ax.set_title(f"t-SNE frozen embeddings — {arm}")
    fig.colorbar(sc, ax=ax, label="label (0 normal / 1 weak-proxy positive)")
    fig.tight_layout()
    fig.savefig(out_dir / f"data_scarcity_tsne_{arm}.png", dpi=110)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5, 4))
    fr = [p["fraction"] for p in lc["points"]]
    mu = [p[f"{lc['metric']}_mean"] for p in lc["points"]]
    lo = [p[f"{lc['metric']}_ci_95"][0] for p in lc["points"]]
    hi = [p[f"{lc['metric']}_ci_95"][1] for p in lc["points"]]
    ax.errorbar(fr, mu, yerr=[np.array(mu) - np.array(lo), np.array(hi) - np.array(mu)], marker="o")
    ax.set_xlabel("fraction of training cycles")
    ax.set_ylabel(lc["metric"])
    ax.set_title(f"Learning curve — {arm} (still rising at 100%: {lc['still_rising_at_100pct']})")
    fig.tight_layout()
    fig.savefig(out_dir / f"data_scarcity_learning_curve_{arm}.png", dpi=110)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description="DS1-DS5 data-scarcity diagnostics.")
    add_source_argument(ap, default="real490")
    ap.add_argument("--zarr", default=None, type=Path)
    ap.add_argument("--cycles", default=None, type=Path)
    ap.add_argument("--simulate-490-if-missing", action="store_true")
    ap.add_argument("--arms", default="anomaly_degradation,masked_recon")
    ap.add_argument("--seeds", default="42,43,44")
    ap.add_argument("--epochs", default=30, type=int)
    ap.add_argument("--fractions", default=",".join(str(f) for f in DEFAULT_FRACTIONS))
    ap.add_argument("--fewshot-fractions", default=",".join(str(f) for f in DEFAULT_FEW_SHOT_FRACTIONS))
    ap.add_argument("--fewshot-repeats", default=20, type=int)
    ap.add_argument("--max-loyo-years", default=4, type=int)
    ap.add_argument("--out", default="reports/data_scarcity.json", type=Path)
    ap.add_argument("--out-csv", default="reports/data_scarcity.csv", type=Path)
    ap.add_argument("--figures", default="reports/figures", type=Path)
    args = ap.parse_args()

    source = args.source
    out_path = args.out

    if source == "real490":
        arch = _load_real490_archive(seed=42)
        prov = arch.get("provenance", {})
        out_path = args.out
    elif source == "real":
        arch = _load_real_archive(
            args.zarr or Path("data/processed/fields.zarr"),
            args.cycles or Path("data/processed/cycles.parquet"),
        )
        prov = {}
    elif source == "simulate490" or source == "simulated":
        arch = _load_simulated_archive(seed=42)
        prov = {
            "data_source": "simulated",
            "n_fields": arch["n_fields"],
            "n_cycles": len(arch["tokens"]),
            "n_dates": arch["n_dates"],
            "seeds": [42],
        }
        out_path = simulated_output_path(args.out)
    else:
        print(f"Unknown source: {source}", file=sys.stderr)
        return 1

    seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
    fractions = [float(x.strip()) for x in args.fractions.split(",") if x.strip()]
    fs_fractions = [float(x.strip()) for x in args.fewshot_fractions.split(",") if x.strip()]
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]

    tokens = arch["tokens"]
    train_idx = np.where(arch["train_mask"])[0]
    train_toks = [tokens[i] for i in train_idx]
    n_bands = arch["n_bands"]
    bands = arch["bands"]
    labels = arch["labels"]
    years = arch["years"]
    field_ids = arch["field_ids"]

    log.info(
        "source=%s n_cycles=%d n_train=%d n_fields=%d n_dates=%s labels_source=%s",
        arch["source"], len(tokens), len(train_toks), arch["n_fields"], arch["n_dates"], arch["label_source"],
    )

    pool, pool_y = _perturb_pool(tokens, bands, seed=7)

    def eval_fn_factory(ref_tokens: list[np.ndarray]):
        def eval_fn(model) -> float:
            return _auc_pr_on_pool(model, pool, pool_y, ref_tokens, n_bands)
        return eval_fn

    report: dict = {
        "provenance": prov,
        "data_source": prov.get("data_source", arch["source"]),
        "source": source,
        "n_cycles": len(tokens),
        "n_train_cycles": len(train_toks),
        "n_fields": arch["n_fields"],
        "n_dates": arch["n_dates"],
        "label_source": arch["label_source"],
        "seeds": seeds,
        "fractions": fractions,
        "fewshot_fractions": fs_fractions,
        "epochs": args.epochs,
        "arms": {},
    }

    csv_rows: list[dict] = []

    for arm in arms:
        t_arm = time.perf_counter()
        arm_report: dict = {}

        # ---- DS1 learning curve (per seed; eval pool fixed) ----
        def train_fn(frac: float, seed: int, arm=arm):
            rng = np.random.default_rng(seed)
            k = max(2, int(round(frac * len(train_toks))))
            idx = rng.choice(len(train_toks), size=min(k, len(train_toks)), replace=False)
            sub = [train_toks[i] for i in idx]
            model = train_pretext_arm(arm, sub, n_bands, epochs=args.epochs, batch_size=16, lr=1.2e-3, seed=seed)
            return model, sub

        def make_eval():
            # eval_fn needs the model's own training subset as reference
            def eval_fn(ms):
                model, sub = ms
                return _auc_pr_on_pool(model, pool, pool_y, sub, n_bands)
            return eval_fn

        lc = learning_curve(train_fn, make_eval(), fractions=fractions, seeds=seeds, metric_name="auc_pr")
        arm_report["learning_curve"] = lc

        # ---- DS2 train/val gap (inner 85/15 split per seed) ----
        gap_per_seed: dict[str, dict] = {}
        for seed in seeds:
            rng = np.random.default_rng(seed)
            perm = rng.permutation(len(train_toks))
            n_val = max(2, int(0.15 * len(perm)))
            va_idx = perm[:n_val]
            tr_idx = perm[n_val:]
            model, history = train_pretext_arm_tracked(
                arm,
                [train_toks[i] for i in tr_idx],
                n_bands,
                val_tokens=[train_toks[i] for i in va_idx],
                epochs=args.epochs,
                batch_size=16,
                lr=1.2e-3,
                seed=seed,
            )
            s = summarize_train_val_history(history)
            s.pop("train_loss_curve", None)
            s.pop("val_loss_curve", None)
            gap_per_seed[str(seed)] = s
        gaps = [g["gap_final"] for g in gap_per_seed.values() if np.isfinite(g.get("gap_final", np.nan))]
        of_sus = [g.get("overfitting_suspected", False) for g in gap_per_seed.values()]
        arm_report["train_val_gap"] = {
            "per_seed": gap_per_seed,
            "gap_final_mean": float(np.mean(gaps)) if gaps else float("nan"),
            "overfitting_suspected_any_seed": bool(any(of_sus)),
        }

        # ---- DS3 embedding quality + t-SNE (full-data model per seed) ----
        eq_per_seed: dict[str, dict] = {}
        fs_per_seed: dict[str, dict] = {}
        tsne_coords = None
        for seed in seeds:
            model = train_pretext_arm(arm, train_toks, n_bands, epochs=args.epochs, batch_size=16, lr=1.2e-3, seed=seed)
            embs = extract_frozen_embeddings(model, tokens)
            eq = embedding_quality_report(embs, groups=field_ids, seed=seed)
            eq_per_seed[str(seed)] = eq
            fs = few_shot_probe(
                embs, labels, fractions=fs_fractions, n_repeats=args.fewshot_repeats, seed=seed
            )
            fs["label_source"] = arch["label_source"]
            fs_per_seed[str(seed)] = fs
            if seed == seeds[0]:
                tsne_coords = tsne_projection(embs, seed=seed)
        eq_mean = {
            k: float(np.nanmean([eq_per_seed[s][k] for s in eq_per_seed if np.isfinite(eq_per_seed[s].get(k, np.nan))]))
            for k in ("mean_cosine_sim", "alignment", "uniformity", "effective_rank", "effective_rank_ratio")
        }
        eq_mean["collapse_suspected"] = bool(np.mean([eq_per_seed[s]["collapse_suspected"] for s in eq_per_seed]) > 0.5)
        arm_report["embedding_quality"] = {"per_seed": eq_per_seed, "mean": eq_mean}
        arm_report["few_shot"] = {"per_seed": fs_per_seed}
        if tsne_coords is not None:
            arm_report["tsne_coords"] = [[float(a), float(b)] for a, b in tsne_coords]

        # ---- DS5 LOYO folds: full-data downstream AUC-PR per held-out year ----
        uniq_years = sorted({int(y) for y in years if y > 0})
        valid_years = [y for y in uniq_years if int((years == y).sum()) >= 3 and int((years != y).sum()) >= 10]
        if len(valid_years) > args.max_loyo_years:
            sel = np.linspace(0, len(valid_years) - 1, args.max_loyo_years).round().astype(int)
            valid_years = [valid_years[i] for i in sel]
        loyo_folds = []
        for yr in valid_years:
            te_idx = np.where(years == yr)[0]
            tr_idx = np.where((years != y) & arch["train_mask"])[0] if False else np.where((years != yr) & arch["train_mask"])[0]
            if len(te_idx) < 3 or len(tr_idx) < 10:
                continue
            sub_tr = [tokens[i] for i in tr_idx]
            model = train_pretext_arm(arm, sub_tr, n_bands, epochs=args.epochs, batch_size=16, lr=1.2e-3, seed=42)
            te_tokens = [tokens[i] for i in te_idx]
            rng = np.random.default_rng(7)
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from run_rq2_pretexts import PERTURB_KINDS, _perturb_tokens

            pert = []
            for kind in PERTURB_KINDS:
                pert.extend(_perturb_tokens(t, bands, kind, rng) for t in te_tokens)
            lp = te_tokens + pert
            ly = np.array([0] * len(te_tokens) + [1] * len(pert), dtype=np.int32)
            ap_ = _auc_pr_on_pool(model, lp, ly, sub_tr, n_bands)
            loyo_folds.append({"held_out_year": int(yr), "n_test_cycles": int(len(te_idx)), "auc_pr": ap_})
        loyo_vals = [f["auc_pr"] for f in loyo_folds if np.isfinite(f["auc_pr"])]
        arm_report["loyo_full_data"] = {
            "per_fold": loyo_folds,
            "auc_pr_mean": float(np.mean(loyo_vals)) if loyo_vals else float("nan"),
            "auc_pr_std": float(np.std(loyo_vals)) if loyo_vals else float("nan"),
        }

        # ---- DS5 seed std for headline metrics ----
        full_pt = next(p for p in lc["points"] if abs(p["fraction"] - 1.0) < 1e-9)
        seed_std = {
            "learning_curve_100pct_auc_pr_std": float(np.std(full_pt["per_seed"])),
            "mean_cosine_sim_std": float(np.std([eq_per_seed[s]["mean_cosine_sim"] for s in eq_per_seed])),
            "alignment_std": float(np.nanstd([eq_per_seed[s]["alignment"] for s in eq_per_seed])),
        }
        arm_report["seed_variance"] = seed_std

        # ---- verdict ----
        fs10 = fs_per_seed[str(seeds[0])]["per_fraction"].get("frac_0.1", {})
        fs1 = fs_per_seed[str(seeds[0])]["per_fraction"].get("frac_0.01", {})
        fs_drop = float(fs10.get("auc_roc_mean", np.nan) - fs1.get("auc_roc_mean", np.nan))
        flags = {
            "learning_curve_still_rising": lc["still_rising_at_100pct"],
            "train_val_overfitting_suspected": arm_report["train_val_gap"]["overfitting_suspected_any_seed"],
            "representation_collapse_suspected": eq_mean["collapse_suspected"],
            "few_shot_auc_drop_1pct_vs_10pct": fs_drop,
            "few_shot_drop_flag": bool(np.isfinite(fs_drop) and fs_drop > 0.2),
            "loyo_auc_pr_std": arm_report["loyo_full_data"]["auc_pr_std"],
            "seed_std_learning_curve": seed_std["learning_curve_100pct_auc_pr_std"],
        }
        arm_report["verdict"] = {
            "flags": flags,
            "data_scarcity_suspected": bool(
                flags["learning_curve_still_rising"]
                or flags["train_val_overfitting_suspected"]
                or flags["representation_collapse_suspected"]
                or flags["few_shot_drop_flag"]
            ),
        }
        arm_report["elapsed_seconds"] = time.perf_counter() - t_arm
        report["arms"][arm] = arm_report

        # CSV rows
        for p in lc["points"]:
            csv_rows.append({"arm": arm, "diagnostic": "DS1_learning_curve", "key": f"frac_{p['fraction']}",
                             "auc_pr_mean": p["auc_pr_mean"], "ci_lo": p["auc_pr_ci_95"][0], "ci_hi": p["auc_pr_ci_95"][1]})
        csv_rows.append({"arm": arm, "diagnostic": "DS1_slope_last_segment", "key": "slope_80_to_100", "auc_pr_mean": lc["slope_last_segment"]})
        csv_rows.append({"arm": arm, "diagnostic": "DS2_gap_final_mean", "key": "gap", "auc_pr_mean": arm_report["train_val_gap"]["gap_final_mean"]})
        for k, v in eq_mean.items():
            csv_rows.append({"arm": arm, "diagnostic": "DS3_embedding_quality", "key": k, "auc_pr_mean": v if isinstance(v, float) else float(v)})
        for fk, fv in fs_per_seed[str(seeds[0])]["per_fraction"].items():
            csv_rows.append({"arm": arm, "diagnostic": "DS4_few_shot", "key": fk, "auc_pr_mean": fv.get("auc_roc_mean", np.nan)})
        csv_rows.append({"arm": arm, "diagnostic": "DS5_loyo_std", "key": "auc_pr_std", "auc_pr_mean": arm_report["loyo_full_data"]["auc_pr_std"]})
        csv_rows.append({"arm": arm, "diagnostic": "verdict", "key": "data_scarcity_suspected", "auc_pr_mean": float(arm_report["verdict"]["data_scarcity_suspected"])})

        if tsne_coords is not None:
            _make_figures(args.figures, arm, tsne_coords, labels, lc)
        log.info("arm=%s done in %.1fs | verdict scarcity=%s", arm, arm_report["elapsed_seconds"], arm_report["verdict"]["data_scarcity_suspected"])

    args.out = out_path
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))
    pd.DataFrame(csv_rows).to_csv(args.out_csv, index=False)
    log.info("wrote %s and %s", args.out, args.out_csv)
    print(json.dumps({a: report["arms"][a]["verdict"] for a in report["arms"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
