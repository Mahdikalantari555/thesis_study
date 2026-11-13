#!/usr/bin/env python3
"""E-INTRA: Pixel / sub-field harvest detection and intra-field harvest-date scatter.

Runs harvest detection across pixel trajectories for each of the 32 subset farms,
matches pixel harvest dates to field-level harvests, and reports within-field
scatter (std, IQR, P90-P10 in days) against the 2-observation-interval (~30 day)
Phase 3 gate threshold.

Supports two input modes:
  1. Direct raster pixel mode (--products-dir + --field-mask / --fields) when
     per-scene NDVI GeoTIFFs are available on disk.
  2. Zarr spatial-dispersion sub-field ensemble mode (default fallback when raw
     rasters are absent), reconstructing sub-field pixel Red/NIR/NDVI trajectories
     from observed per-field, per-date ``median`` and spatial ``std`` in fields.zarr.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from ssl_anomaly.backends import get_backend
from ssl_anomaly.eval.stats import bootstrap_ci
from ssl_anomaly.phenology.cycles import detect_harvests
from ssl_anomaly.utils.arrays import hampel_filter
from ssl_anomaly.utils.logging import get_logger
from ssl_anomaly.utils.throttle import limit_threads

log = get_logger("ssl_anomaly.scripts.eintra")


def _select_backend():
    try:
        return get_backend("rust")
    except NotImplementedError:
        return get_backend("numpy")


def compute_field_pixel_scatter(
    field_id: int,
    t_days: np.ndarray,
    field_ndvi: np.ndarray,
    pixel_ndvi: np.ndarray,
    valid_frac: np.ndarray | None = None,
    *,
    lam: float = 100.0,
    min_prominence: float = 0.15,
    min_cycle_days: int = 180,
    plateau_frac: float = 0.7,
    rise_frac: float = 0.15,
    match_window_days: int = 90,
    gate_threshold_days: float = 30.0,
    backend=None,
) -> dict:
    """Run harvest detection on field-median and ``(n_pixels, T)`` pixel series for one farm."""
    bk = backend or _select_backend()
    t_days = np.asarray(t_days, dtype=np.int64)
    order = np.argsort(t_days)
    t_days = t_days[order]
    field_ndvi = np.asarray(field_ndvi, dtype=np.float64)[order]
    pixel_ndvi = np.asarray(pixel_ndvi, dtype=np.float64)[:, order]
    q = (
        np.asarray(valid_frac, dtype=np.float64)[order]
        if valid_frac is not None
        else np.ones_like(field_ndvi)
    )

    finite_f = np.isfinite(field_ndvi)
    if int(finite_f.sum()) < 30:
        return {
            "field": int(field_id),
            "n_pixels": int(pixel_ndvi.shape[0]),
            "n_field_harvests": 0,
            "n_matched_harvests": 0,
            "mean_std_days": np.nan,
            "max_std_days": np.nan,
            "mean_iqr_days": np.nan,
            "mean_p90_p10_days": np.nan,
            "exceeds_2_obs_intervals": False,
            "per_harvest": [],
        }

    # Clean single-date cloud outliers on field series
    out_f = hampel_filter(t_days[finite_f], field_ndvi[finite_f], window=5, n_sigma=3.0)
    f_clean = field_ndvi.copy()
    fin_idx = np.where(finite_f)[0]
    f_clean[fin_idx[out_f]] = np.nan

    t0 = int(t_days.min())
    t1 = int(t_days.max())
    n_grid = t1 - t0 + 1
    grid = np.arange(t0, t1 + 1, dtype=np.int64)
    obs_pos = (t_days - t0).astype(np.int64)

    # Stack field series (row 0) + pixel series (rows 1..P) into one batch for Whittaker
    n_pix = pixel_ndvi.shape[0]
    y_batch = np.zeros((1 + n_pix, n_grid), dtype=np.float64)
    w_batch = np.zeros((1 + n_pix, n_grid), dtype=np.float64)

    f_ok = np.isfinite(f_clean) & (q > 0)
    y_batch[0, obs_pos[f_ok]] = f_clean[f_ok]
    w_batch[0, obs_pos[f_ok]] = q[f_ok]

    for p in range(n_pix):
        yp = pixel_ndvi[p].copy()
        fp = np.isfinite(yp)
        if int(fp.sum()) >= 15:
            out_p = hampel_filter(t_days[fp], yp[fp], window=5, n_sigma=3.0)
            p_idx = np.where(fp)[0]
            yp[p_idx[out_p]] = np.nan
        ok_p = np.isfinite(yp) & (q > 0)
        y_batch[1 + p, obs_pos[ok_p]] = yp[ok_p]
        w_batch[1 + p, obs_pos[ok_p]] = q[ok_p]

    smoothed = bk.whittaker_batch(y_batch, w_batch, lam=float(lam))
    field_smooth = smoothed[0]
    field_h_idx = detect_harvests(
        grid,
        field_smooth,
        min_prominence=min_prominence,
        min_cycle_days=min_cycle_days,
        plateau_frac=plateau_frac,
        rise_frac=rise_frac,
    )
    field_h_days = grid[field_h_idx] if field_h_idx.size else np.array([], dtype=np.int64)

    pixel_h_days: list[np.ndarray] = []
    for p in range(n_pix):
        if np.sum(w_batch[1 + p] > 0) < 20:
            pixel_h_days.append(np.array([], dtype=np.int64))
            continue
        ph_idx = detect_harvests(
            grid,
            smoothed[1 + p],
            min_prominence=min_prominence,
            min_cycle_days=min_cycle_days,
            plateau_frac=plateau_frac,
            rise_frac=rise_frac,
        )
        pixel_h_days.append(grid[ph_idx] if ph_idx.size else np.array([], dtype=np.int64))

    per_harvest: list[dict] = []
    for hi, hd in enumerate(field_h_days):
        offsets = []
        matched_days = []
        for ph in pixel_h_days:
            if ph.size == 0:
                continue
            diffs = ph - int(hd)
            nearest_i = int(np.argmin(np.abs(diffs)))
            if abs(int(diffs[nearest_i])) <= match_window_days:
                offsets.append(float(diffs[nearest_i]))
                matched_days.append(float(ph[nearest_i]))
        if len(matched_days) >= 3:
            arr_m = np.array(matched_days, dtype=np.float64)
            std_d = float(np.std(arr_m, ddof=1))
            q25, q75 = np.percentile(arr_m, [25, 75])
            q10, q90 = np.percentile(arr_m, [10, 90])
            per_harvest.append(
                {
                    "harvest_idx": int(hi),
                    "field_harvest_day": int(hd),
                    "n_pixels_matched": len(matched_days),
                    "pixel_detection_rate": float(len(matched_days) / max(1, n_pix)),
                    "std_days": std_d,
                    "iqr_days": float(q75 - q25),
                    "p90_p10_days": float(q90 - q10),
                    "median_offset_days": float(np.median(offsets)),
                }
            )

    stds = [h["std_days"] for h in per_harvest]
    iqrs = [h["iqr_days"] for h in per_harvest]
    spans = [h["p90_p10_days"] for h in per_harvest]
    mean_std = float(np.mean(stds)) if stds else np.nan
    max_std = float(np.max(stds)) if stds else np.nan
    mean_iqr = float(np.mean(iqrs)) if iqrs else np.nan
    mean_span = float(np.mean(spans)) if spans else np.nan

    return {
        "field": int(field_id),
        "n_pixels": int(n_pix),
        "n_field_harvests": int(field_h_days.size),
        "n_matched_harvests": len(per_harvest),
        "mean_std_days": mean_std,
        "max_std_days": max_std,
        "mean_iqr_days": mean_iqr,
        "mean_p90_p10_days": mean_span,
        "exceeds_2_obs_intervals": bool(np.isfinite(mean_std) and mean_std > gate_threshold_days),
        "per_harvest": per_harvest,
    }


def extract_pixels_from_raster_stack(
    raster_stack: np.ndarray,  # (T, H, W) NDVI
    field_mask: np.ndarray,  # (H, W) int field ids (1..F)
    max_pixels_per_field: int = 64,
    seed: int = 42,
) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Extract (field_median_ndvi, pixel_ndvi_matrix) per field from a 3-D raster stack."""
    rng = np.random.default_rng(seed)
    fids = sorted(int(f) for f in np.unique(field_mask) if f > 0)
    out: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for fid in fids:
        ys, xs = np.where(field_mask == fid)
        if ys.size == 0:
            continue
        pix_all = raster_stack[:, ys, xs].T.astype(np.float64)  # (N_pix, T)
        with np.errstate(all="ignore"):
            f_med = np.nanmedian(pix_all, axis=0)
        if pix_all.shape[0] > max_pixels_per_field:
            sel = rng.choice(pix_all.shape[0], size=max_pixels_per_field, replace=False)
            pix_sub = pix_all[np.sort(sel)]
        else:
            pix_sub = pix_all
        out[fid] = (f_med, pix_sub)
    return out


def reconstruct_subfield_pixels_from_zarr(
    ds: xr.Dataset,
    n_pixels_per_field: int = 48,
    spatial_persistence: float = 0.65,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, dict[int, tuple[np.ndarray, np.ndarray]]]:
    """Reconstruct sub-field pixel NDVI series from observed per-field median & spatial std."""
    rng = np.random.default_rng(seed)
    times = ds.coords["time"].values
    t_days = (times - times.min()).astype("timedelta64[D]").astype(np.int64)
    fields = ds.coords["field"].values
    bands = [str(b) for b in ds.coords["band"].values]
    med = ds["median"].values  # (F, T, B)
    std = ds["std"].values if "std" in ds.data_vars else np.zeros_like(med)
    vf = ds["valid_frac"].values

    r_idx = bands.index("SR_B4")
    n_idx = bands.index("SR_B5")
    rho = float(np.clip(spatial_persistence, 0.0, 0.95))
    transient_scale = float(np.sqrt(1.0 - rho**2))

    per_field: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for fi, fid_raw in enumerate(fields):
        fid = int(fid_raw)
        r_med = med[fi, :, r_idx].astype(np.float64)
        n_med = med[fi, :, n_idx].astype(np.float64)
        r_std = np.nan_to_num(std[fi, :, r_idx].astype(np.float64), nan=0.0)
        n_std = np.nan_to_num(std[fi, :, n_idx].astype(np.float64), nan=0.0)

        denom_f = n_med + r_med
        f_ndvi = np.where(
            np.isfinite(denom_f) & (denom_f > 0), (n_med - r_med) / np.where(denom_f > 0, denom_f, 1.0), np.nan
        )

        T = t_days.size
        # Persistent sub-field spatial factor (e.g., head-to-tail irrigation/harvest gradient)
        z_spatial = rng.normal(0.0, 1.0, size=(n_pixels_per_field, 1))
        eps_n = rng.normal(0.0, 1.0, size=(n_pixels_per_field, T))
        eps_r = rng.normal(0.0, 1.0, size=(n_pixels_per_field, T))

        u_nir = rho * z_spatial + transient_scale * eps_n
        # Red is negatively correlated with NIR across canopy vs harvested soil
        u_red = -0.7 * rho * z_spatial + transient_scale * (-0.5 * eps_n + np.sqrt(0.75) * eps_r)

        nir_p = np.clip(n_med[None, :] + u_nir * n_std[None, :], 0.005, 1.0)
        red_p = np.clip(r_med[None, :] + u_red * r_std[None, :], 0.005, 1.0)
        pix_ndvi = (nir_p - red_p) / np.maximum(nir_p + red_p, 1e-6)
        pix_ndvi[:, ~np.isfinite(f_ndvi)] = np.nan
        per_field[fid] = (f_ndvi, pix_ndvi)

    return t_days, vf, per_field


def _load_raster_mode_if_available(
    products_dir: Path, field_mask_path: Path, max_pixels: int, seed: int
) -> tuple[np.ndarray, np.ndarray, dict[int, tuple[np.ndarray, np.ndarray]]] | None:
    if not products_dir.exists() or not field_mask_path.exists():
        return None
    import rasterio

    tifs = sorted([p for p in products_dir.glob("*.tif") if "_interp" not in p.name])
    if not tifs:
        return None
    with rasterio.open(field_mask_path) as msrc:
        fmask = msrc.read(1)
    dates = []
    layers = []
    for p in tifs:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", p.name)
        if not m:
            continue
        dates.append(np.datetime64(m.group(1)))
        with rasterio.open(p) as src:
            layers.append(src.read(1).astype(np.float32))
    if not layers:
        return None
    times = np.array(dates, dtype="datetime64[D]")
    t_days = (times - times.min()).astype("timedelta64[D]").astype(np.int64)
    stack = np.stack(layers, axis=0)
    extracted = extract_pixels_from_raster_stack(stack, fmask, max_pixels_per_field=max_pixels, seed=seed)
    vf = np.ones((len(extracted), len(t_days)), dtype=np.float64)
    return t_days, vf, extracted


def run_eintra(
    zarr_path: str | Path = "data/processed/fields.zarr",
    products_dir: str | Path = "D:/RS/Thesis/Data/Metric/products/NDVI",
    field_mask_path: str | Path = "data/interim/field_mask.tif",
    *,
    n_pixels: int = 48,
    lam: float = 100.0,
    gate_threshold_days: float = 30.0,
    seed: int = 42,
) -> dict:
    """Execute E-INTRA across the 32 subset farms and summarize intra-field scatter."""
    bk = _select_backend()
    raster_loaded = _load_raster_mode_if_available(
        Path(products_dir), Path(field_mask_path), max_pixels=n_pixels, seed=seed
    )
    if raster_loaded is not None:
        source_mode = "raster_geotiff_pixels"
        t_days, vf_all, field_map = raster_loaded
    else:
        source_mode = "zarr_spatial_std_subfield_ensemble"
        ds = xr.open_zarr(zarr_path)
        t_days, vf_all, field_map = reconstruct_subfield_pixels_from_zarr(
            ds, n_pixels_per_field=n_pixels, seed=seed
        )

    per_field_results: list[dict] = []
    for idx, (fid, (f_ndvi, pix_ndvi)) in enumerate(sorted(field_map.items())):
        vf_f = vf_all[idx] if idx < vf_all.shape[0] else None
        res = compute_field_pixel_scatter(
            fid,
            t_days=t_days,
            field_ndvi=f_ndvi,
            pixel_ndvi=pix_ndvi,
            valid_frac=vf_f,
            lam=lam,
            gate_threshold_days=gate_threshold_days,
            backend=bk,
        )
        per_field_results.append(res)

    valid_stds = np.array(
        [r["mean_std_days"] for r in per_field_results if np.isfinite(r["mean_std_days"])],
        dtype=np.float64,
    )
    valid_iqrs = np.array(
        [r["mean_iqr_days"] for r in per_field_results if np.isfinite(r["mean_iqr_days"])],
        dtype=np.float64,
    )
    valid_spans = np.array(
        [r["mean_p90_p10_days"] for r in per_field_results if np.isfinite(r["mean_p90_p10_days"])],
        dtype=np.float64,
    )

    if valid_stds.size >= 2:
        std_mean, std_lo, std_hi = bootstrap_ci(np.mean, valid_stds, n_boot=1000, seed=seed)
        iqr_mean, iqr_lo, iqr_hi = bootstrap_ci(np.mean, valid_iqrs, n_boot=1000, seed=seed)
    elif valid_stds.size == 1:
        std_mean = std_lo = std_hi = float(valid_stds[0])
        iqr_mean = iqr_lo = iqr_hi = float(valid_iqrs[0])
    else:
        std_mean = std_lo = std_hi = np.nan
        iqr_mean = iqr_lo = iqr_hi = np.nan

    n_exceeding = int(sum(1 for r in per_field_results if r["exceeds_2_obs_intervals"]))
    n_with_harvests = int(valid_stds.size)
    frac_exceeding = float(n_exceeding / max(1, n_with_harvests))

    return {
        "source_mode": source_mode,
        "backend": bk.name,
        "n_farms_total": len(per_field_results),
        "n_farms_with_detected_harvests": n_with_harvests,
        "n_pixels_per_farm": int(n_pixels),
        "gate_threshold_days": float(gate_threshold_days),
        "mean_within_field_std_days": std_mean,
        "mean_within_field_std_ci_95": [std_lo, std_hi],
        "median_within_field_std_days": float(np.median(valid_stds)) if valid_stds.size else np.nan,
        "mean_within_field_iqr_days": iqr_mean,
        "mean_within_field_iqr_ci_95": [iqr_lo, iqr_hi],
        "mean_within_field_p90_p10_days": float(np.mean(valid_spans)) if valid_spans.size else np.nan,
        "n_farms_exceeding_30d_std": n_exceeding,
        "frac_farms_exceeding_30d_std": frac_exceeding,
        "prioritize_phase3": bool(frac_exceeding > 0.25),
        "per_field": per_field_results,
    }


def main() -> int:
    limit_threads(2)
    ap = argparse.ArgumentParser(description="Run E-INTRA pixel/sub-field harvest scatter analysis.")
    ap.add_argument("--zarr", default="data/processed/fields.zarr", type=Path)
    ap.add_argument("--products-dir", default="D:/RS/Thesis/Data/Metric/products/NDVI", type=Path)
    ap.add_argument("--field-mask", default="data/interim/field_mask.tif", type=Path)
    ap.add_argument("--n-pixels", default=48, type=int)
    ap.add_argument("--lam", default=100.0, type=float)
    ap.add_argument("--threshold-days", default=30.0, type=float)
    ap.add_argument("--out", default="reports/eintra.json", type=Path)
    args = ap.parse_args()

    report = run_eintra(
        zarr_path=args.zarr,
        products_dir=args.products_dir,
        field_mask_path=args.field_mask,
        n_pixels=args.n_pixels,
        lam=args.lam,
        gate_threshold_days=args.threshold_days,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))

    csv_rows = [
        {k: v for k, v in r.items() if k != "per_harvest"}
        for r in report["per_field"]
    ]
    csv_path = args.out.with_name("eintra_per_field.csv")
    pd.DataFrame(csv_rows).to_csv(csv_path, index=False)

    log.info("Wrote E-INTRA report to %s and %s", args.out, csv_path)
    print(
        f"E-INTRA ({report['source_mode']}, backend={report['backend']}): "
        f"{report['n_farms_with_detected_harvests']}/{report['n_farms_total']} farms with harvests | "
        f"mean within-field std = {report['mean_within_field_std_days']:.2f} d "
        f"(95% CI [{report['mean_within_field_std_ci_95'][0]:.2f}, {report['mean_within_field_std_ci_95'][1]:.2f}]) | "
        f"mean IQR = {report['mean_within_field_iqr_days']:.2f} d | "
        f"exceeding 30d = {report['n_farms_exceeding_30d_std']}/{report['n_farms_with_detected_harvests']} "
        f"({report['frac_farms_exceeding_30d_std']*100:.1f}%) | "
        f"prioritize_phase3 = {report['prioritize_phase3']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
