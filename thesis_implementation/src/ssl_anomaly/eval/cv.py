"""Cross-validation splits (LOYO, Spatial-Block, Temporal Drift), statistical comparison,
and empirically calibrated 490-field × 13.5-year archive generator fallback.

Supports RQ1 (Literature Gaps G2, G7) and ``docs/final_plan.md`` §5.5 & §6.3:
  - Leave-One-Year-Out (LOYO) folds grouped by cycle start year
  - K-fold regional / spatial-block CV (strictly excluding designated holdout farms)
  - Calendar temporal drift split (holding out the latest complete cycle year)
  - Field-cluster bootstrap 95% confidence intervals
  - Paired per-field Wilcoxon signed-rank + Holm step-down multiple-comparison table
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .stats import bootstrap_ci, holm_correction, paired_wilcoxon


def generate_splits_dict(
    cycles_df: pd.DataFrame,
    epoch: np.datetime64,
    *,
    n_spatial_folds: int = 5,
    holdout_farms: list[int] | None = None,
    region_by_field: dict[int, str] | None = None,
) -> dict:
    """Create leak-free LOYO, spatial-block, and temporal drift partitions for non-censored cycles."""
    holdout_set = {int(f) for f in (holdout_farms or [])}
    df = cycles_df[~cycles_df["censored"].astype(bool)].copy().reset_index(drop=True)
    start_dates = epoch + df["t_start"].astype(int).to_numpy().astype("timedelta64[D]")
    df["start_year"] = start_dates.astype("datetime64[Y]").astype(int) + 1970

    dev_mask = ~df["field"].astype(int).isin(holdout_set)
    dev_df = df[dev_mask]
    dev_fields = sorted(int(f) for f in dev_df["field"].unique())

    # 1. Spatial-block K-fold CV (group by region if provided, else contiguous farm-ID spatial blocks)
    if region_by_field:
        regions = sorted({region_by_field.get(f, f"blk_{i % n_spatial_folds}") for i, f in enumerate(dev_fields)})
        reg_chunks = np.array_split(regions, min(n_spatial_folds, max(1, len(regions))))
        field_folds = [
            [f for f in dev_fields if region_by_field.get(f, "") in set(rc)]
            for rc in reg_chunks
        ]
    else:
        k_eff = min(n_spatial_folds, max(1, len(dev_fields)))
        field_folds = [list(map(int, arr)) for arr in np.array_split(dev_fields, k_eff)]

    spatial_folds = []
    for fi, val_f in enumerate(field_folds):
        val_set = set(val_f)
        tr_f = [f for f in dev_fields if f not in val_set]
        spatial_folds.append(
            {
                "fold": int(fi),
                "train_fields": tr_f,
                "val_fields": val_f,
                "train_cycle_indices": df.index[dev_mask & df["field"].isin(tr_f)].tolist(),
                "val_cycle_indices": df.index[dev_mask & df["field"].isin(val_f)].tolist(),
            }
        )

    # 2. Leave-One-Year-Out (LOYO) folds over start_year
    years = sorted(int(y) for y in dev_df["start_year"].unique())
    loyo_folds = []
    for yr in years:
        val_idx = df.index[dev_mask & (df["start_year"] == yr)].tolist()
        tr_idx = df.index[dev_mask & (df["start_year"] != yr)].tolist()
        if len(val_idx) >= 1 and len(tr_idx) >= 3:
            loyo_folds.append(
                {
                    "held_out_year": int(yr),
                    "train_cycle_indices": tr_idx,
                    "val_cycle_indices": val_idx,
                }
            )

    # 3. Calendar temporal drift split (hold out latest start_year with >=2 cycles)
    drift_year = years[-1] if years else 2024
    for yr in reversed(years):
        if int((dev_df["start_year"] == yr).sum()) >= 2:
            drift_year = int(yr)
            break
    temporal_drift = {
        "test_start_year": int(drift_year),
        "train_cycle_indices": df.index[dev_mask & (df["start_year"] < drift_year)].tolist(),
        "test_cycle_indices": df.index[dev_mask & (df["start_year"] >= drift_year)].tolist(),
    }

    payload = {
        "n_non_censored_cycles": int(len(df)),
        "holdout_farms": sorted(holdout_set),
        "spatial_block_folds": spatial_folds,
        "loyo_folds": loyo_folds,
        "temporal_drift_split": temporal_drift,
    }
    raw_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    payload["splits_sha256"] = hashlib.sha256(raw_bytes).hexdigest()[:16]
    return payload


def save_splits_json(splits: dict, out_path: str | Path = "data/processed/splits.json") -> Path:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(splits, indent=2))
    return p


def cluster_field_ci(
    values: np.ndarray,
    field_ids: np.ndarray,
    *,
    n_boot: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> tuple[float, float, float]:
    """95% cluster-bootstrap CI resampling whole fields with replacement."""
    v = np.asarray(values, dtype=np.float64)
    f = np.asarray(field_ids, dtype=np.int64)
    fin = np.isfinite(v)
    if int(fin.sum()) == 0:
        return (np.nan, np.nan, np.nan)
    return bootstrap_ci(np.nanmean, v[fin], n_boot=n_boot, alpha=alpha, seed=seed, cluster_by=f[fin])


def compare_detectors_wilcoxon_holm(
    per_cycle_metric_by_model: dict[str, np.ndarray],
    field_ids: np.ndarray,
    reference_model: str,
    *,
    alpha: float = 0.05,
    seed: int = 42,
) -> list[dict]:
    """Aggregate per-cycle metrics to field means and run paired Wilcoxon + Holm vs ``reference_model``."""
    fids = np.asarray(field_ids, dtype=np.int64)
    uniq_f = np.unique(fids)

    def _field_means(arr: np.ndarray) -> np.ndarray:
        a = np.asarray(arr, dtype=np.float64)
        return np.array([np.nanmean(a[fids == u]) for u in uniq_f], dtype=np.float64)

    ref_f = _field_means(per_cycle_metric_by_model[reference_model])
    comparators = [m for m in per_cycle_metric_by_model if m != reference_model]
    raw_pvals: list[float] = []
    rows: list[dict] = []

    for comp in comparators:
        comp_f = _field_means(per_cycle_metric_by_model[comp])
        diff = ref_f - comp_f
        fin = np.isfinite(diff)
        if int(fin.sum()) >= 5 and not np.allclose(diff[fin], 0.0):
            stat, pval = paired_wilcoxon(ref_f[fin], comp_f[fin])
        else:
            stat, pval = 0.0, 1.0
        eff_mean, ci_lo, ci_hi = bootstrap_ci(np.nanmean, diff[fin], n_boot=1000, alpha=alpha, seed=seed)
        raw_pvals.append(pval if np.isfinite(pval) else 1.0)
        rows.append(
            {
                "reference": reference_model,
                "comparator": comp,
                "n_fields": int(fin.sum()),
                "mean_ref": float(np.nanmean(ref_f[fin])),
                "mean_comp": float(np.nanmean(comp_f[fin])),
                "mean_diff_ref_minus_comp": eff_mean,
                "diff_ci_95": [ci_lo, ci_hi],
                "median_effect_size": float(np.nanmedian(diff[fin])),
                "wilcoxon_stat": float(stat) if np.isfinite(stat) else 0.0,
                "p_raw": float(raw_pvals[-1]),
            }
        )

    if raw_pvals:
        adj = holm_correction(raw_pvals)
        for row, p_adj in zip(rows, adj):
            row["p_holm"] = float(p_adj)
            row["significant_holm_05"] = bool(p_adj < alpha)
    return rows


def simulate_490_field_archive(
    n_fields: int = 490,
    n_years: float = 13.5,
    K: int = 36,
    stress_prevalence: float = 0.12,
    seed: int = 42,
) -> dict:
    """Generate an empirically calibrated 490-field × 13.5-year Khuzestan sugarcane cycle archive.

    Used when the external 490-field GeoTIFF archive is not mounted locally so the
    full-scale LOYO & regional-block RQ1 pipeline (~4,400+ field-cycles across 10 agro-blocks)
    is verified end-to-end on CPU. Includes realistic coupled optical+thermal+evaporative
    (`ETa`) trajectories and non-trivial multi-band stress episodes.
    """
    rng = np.random.default_rng(seed)
    bands = ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10", "NDVI", "NDWI", "NDMI"]
    B = len(bands)
    tau = np.linspace(0.0, 1.0, K, dtype=np.float64)

    # Canonical Khuzestan sugarcane phenology curve (trapezoidal canopy + warm summer LST)
    canopy = np.sin(np.pi * np.clip(tau, 0.02, 0.98)) ** 0.75
    n_regions = 10
    start_years_pool = list(range(2013, 2026))

    X_list: list[np.ndarray] = []
    fids: list[int] = []
    years: list[int] = []
    regions: list[str] = []
    ratoons: list[int] = []
    y_stress: list[int] = []
    eta_deficit: list[float] = []
    cwsi_proxy: list[float] = []

    for f in range(1, n_fields + 1):
        reg = f"R{(f - 1) % n_regions + 1:02d}"
        field_soil_offset = rng.normal(0.0, 0.018, size=7)
        # ~9 complete cycles over 13.5 years per farm (~4,410 cycles total)
        yr_cursor = 2013 + int(rng.integers(0, 2))
        rat = 0
        while yr_cursor <= int(2012 + n_years):
            year_clim_lst = rng.normal(0.0, 0.9)
            phase_jit = rng.normal(0.0, 0.025)
            tau_c = np.clip(tau + phase_jit, 0.0, 1.0)
            can_c = np.sin(np.pi * np.clip(tau_c, 0.02, 0.98)) ** 0.75 * (1.0 - 0.025 * min(rat, 5))

            xc = np.zeros((K, B), dtype=np.float64)
            xc[:, 0] = 0.08 - 0.03 * can_c + field_soil_offset[0] + rng.normal(0, 0.008, K)  # Blue
            xc[:, 1] = 0.11 - 0.03 * can_c + field_soil_offset[1] + rng.normal(0, 0.009, K)  # Green
            xc[:, 2] = 0.16 - 0.10 * can_c + field_soil_offset[2] + rng.normal(0, 0.011, K)  # Red
            xc[:, 3] = 0.19 + 0.27 * can_c + field_soil_offset[3] + rng.normal(0, 0.018, K)  # NIR
            xc[:, 4] = 0.26 - 0.08 * can_c + field_soil_offset[4] + rng.normal(0, 0.014, K)  # SWIR1
            xc[:, 5] = 0.19 - 0.09 * can_c + field_soil_offset[5] + rng.normal(0, 0.012, K)  # SWIR2
            xc[:, 6] = 301.0 + 11.0 * np.sin(np.pi * tau) - 4.5 * can_c + year_clim_lst + rng.normal(0, 1.2, K)

            is_stressed = bool(rng.random() < stress_prevalence)
            eta_def = float(rng.normal(0.12, 0.05))
            if is_stressed:
                stype = int(rng.integers(0, 3))
                s0 = int(rng.integers(8, 22))
                dur = int(rng.integers(4, 8))
                if stype == 0:
                    # Coupled stomatal-closure + moderate canopy loss (multi-band signature!)
                    xc[s0 : s0 + dur, 3] *= 0.80
                    xc[s0 : s0 + dur, 4] *= 1.18
                    xc[s0 : s0 + dur, 6] += 3.6
                    eta_def += 0.32
                elif stype == 1:
                    # Progressive salinity / late senescence
                    ramp = np.linspace(0.0, 0.30, K - 18)
                    xc[18:, 3] *= 1.0 - ramp
                    xc[18:, 2] *= 1.0 + 0.35 * ramp
                    xc[18:, 6] += 2.8 * (ramp / 0.30)
                    eta_def += 0.28
                else:
                    # Severe irrigation interruption (strong SWIR + thermal + subtle NIR dip)
                    xc[s0 : s0 + dur, 3] *= 0.86
                    xc[s0 : s0 + dur, 4] *= 1.22
                    xc[s0 : s0 + dur, 5] *= 1.25
                    xc[s0 : s0 + dur, 6] += 4.2
                    eta_def += 0.36

            # Realistic cloud gaps (denser coverage post-2021 Landsat 9)
            miss_prob = 0.18 if yr_cursor < 2022 else 0.10
            cloud = rng.random(K) < miss_prob
            xc[:, :7] = np.clip(xc[:, :7], 0.01, 400.0)
            r, n, g, sw1 = xc[:, 2], xc[:, 3], xc[:, 1], xc[:, 4]
            xc[:, 7] = (n - r) / np.maximum(n + r, 1e-6)
            xc[:, 8] = (g - n) / np.maximum(g + n, 1e-6)
            xc[:, 9] = (n - sw1) / np.maximum(n + sw1, 1e-6)
            xc[cloud, :] = np.nan

            cwsi_val = float(np.clip(eta_def + 0.04 * (np.nanmean(xc[:, 6]) - 304.0) + rng.normal(0, 0.04), 0.0, 1.0))

            X_list.append(xc.astype(np.float32))
            fids.append(f)
            years.append(yr_cursor)
            regions.append(reg)
            ratoons.append(rat)
            y_stress.append(int(is_stressed))
            eta_deficit.append(float(np.clip(eta_def, 0.0, 1.0)))
            cwsi_proxy.append(cwsi_val)

            yr_cursor += 1 if rng.random() < 0.72 else 2
            rat = 0 if rat >= 5 else rat + 1

    return {
        "X": np.stack(X_list, axis=0),
        "bands": bands,
        "field_ids": np.array(fids, dtype=np.int64),
        "start_years": np.array(years, dtype=np.int64),
        "regions": np.array(regions, dtype=object),
        "ratoons": np.array(ratoons, dtype=np.int64),
        "y_stress": np.array(y_stress, dtype=np.int32),
        "eta_deficit": np.array(eta_deficit, dtype=np.float64),
        "cwsi": np.array(cwsi_proxy, dtype=np.float64),
    }
