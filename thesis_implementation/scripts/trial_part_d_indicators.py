#!/usr/bin/env python3
"""Trial part D — agreement with independent remote-sensing stress
indicators (predictive-ssl-controlled-trial, task 2.4).

DATA-AVAILABILITY GATE FIRST (prime directive 2): every indicator not already
available under ``Data/Processed`` is recorded ``absent`` — never synthesized,
never proxied silently. Verified availability (2026-11-14, runtime-rechecked):

  - CWSI_ET: PRESENT for a 32-field subset — ``satellite/stats_current.zarr``
    variable ``cwsi_et`` (field × 539 scene dates). Matched to (cycle, bin)
    cells whose 15-day bin window contains a scene date; uncovered cells stay
    NaN (absent), never filled. CWSI_LST has NO processed field artifact
    (METRIC rasters only) → ``absent``.
  - ETa / ETrF: ``absent`` as processed field statistics (METRIC rasters under
    ``Data/Metric/products/`` only; aggregating rasters is a new processing
    step outside this read-only trial).
  - TVDI: computable from EXISTING per-scene per-field LST/NDVI statistics
    (the design's explicit allowance) — computed here as a DERIVED proxy via
    the across-field NDVI–LST feature space at each bin (Sandholt-style).
  - NDVI/SAVI temporal behaviour: available from the natural dev cycles.

DEPENDENCE STRUCTURE (stated verbatim in every output): the model input
includes LST and NDVI; CWSI_ET derives from the METRIC energy balance (which
consumes LST) and TVDI / the NDVI-deficit proxy are LST- and/or NDVI-derived
— agreement is CORROBORATING evidence for output validity (proxy agreement
toward L4), NOT independent ground truth and NOT proof of stress. The noun
stays "suspected stress" / "synthetic anomaly"; no L4 claim is made from
correlation alone.

Read-only; writes reports/dev/<trial-run-id>/part_d_*.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ssl_anomaly.monitor import inputs as minputs  # noqa: E402
from ssl_anomaly.monitor import scoring as mscoring  # noqa: E402
from ssl_anomaly.monitor import trial_parts as tparts  # noqa: E402
from trial_common import (  # noqa: E402
    LST_CHANNEL, NDVI_CHANNEL, add_common_args, arm_clean_z2, gru_pred_seeds,
    load_context, out_dir, provenance, severity_entry,
)

DATA_PROCESSED = Path(r"D:\RS\Thesis\Data\Processed")


def availability_check() -> dict:
    """Runtime re-verification of the processed-data availability gate."""
    sat = DATA_PROCESSED / "satellite"

    def _find(patterns: list[str]) -> list[str]:
        hits: list[str] = []
        for pat in patterns:
            hits += [str(p.relative_to(DATA_PROCESSED)) for p in sat.rglob(pat)]
        return sorted(set(hits))[:10]

    cwsi_hits = _find(["*cwsi*", "*CWSI*"])
    eta_hits = _find(["*eta*", "*ETa*", "*etrf*", "*ETrF*"])
    tvdi_hits = _find(["*tvdi*", "*TVDI*"])
    cwsi_et_present = any("stats_current.zarr" in h and h.replace("\\", "/").endswith("/cwsi_et")
                          for h in cwsi_hits)
    return {
        "gate": "indicators already available under Data/Processed; anything else = absent",
        "CWSI_ET": {
            "status": ("present_32field_subset" if cwsi_et_present else
                       "absent" if not cwsi_hits else "present_unverified"),
            "processed_hits": cwsi_hits,
            "note": ("satellite/stats_current.zarr variable cwsi_et (32 fields × 539 scene "
                     "dates) — the ONLY processed CWSI artifact; matched to (cycle, bin) cells "
                     "whose 15-day bin window contains a scene date, uncovered cells stay "
                     "NaN (absent); CWSI_LST has no processed field artifact (METRIC rasters "
                     "under Data/Metric/products/CWSI_LST only, out of trial scope)"),
        },
        "CWSI_LST": {
            "status": "absent",
            "processed_hits": [h for h in cwsi_hits if "CWSI_LST" in h],
            "note": "no processed field stats under Data/Processed (METRIC rasters only)",
        },
        "ETa_ETrF": {
            "status": "present" if eta_hits else "absent",
            "processed_hits": eta_hits,
            "note": ("Data/Metric/products/ETaDaily + ETrF rasters exist; no processed "
                     "field stats under Data/Processed"),
        },
        "TVDI": {
            "status": "derived_from_existing_stats" if not tvdi_hits else "present",
            "processed_hits": tvdi_hits,
            "note": ("no stored TVDI artifact; computable from EXISTING per-scene per-field "
                     "LST/NDVI statistics (design allowance) — DERIVED proxy, Sandholt-style "
                     "across-field NDVI–LST feature space per bin; disclosed LST/NDVI dependence"),
        },
        "ndvi_savi_temporal": {
            "status": "present",
            "note": "channels of the natural dev cycles themselves (total model-input dependence, disclosed)",
        },
    }


def ndvi_deficit_proxy(ndvi_2d: np.ndarray, mask_2d: np.ndarray) -> np.ndarray:
    """Per-(field, bin) NDVI deviation from the ACROSS-FIELD median at the same
    bin (phenology-phase-referenced), in across-field MAD units. Negative =
    deficit vs the phase norm. Derived from the model's own input channel —
    corroborating proxy only (disclosed). Accepts (N, T) arrays."""
    N, T = ndvi_2d.shape
    out = np.full((N, T), np.nan)
    for b in range(T):
        col = ndvi_2d[:, b]
        m = mask_2d[:, b].astype(bool)
        if m.sum() < 8:
            continue
        med = np.median(col[m])
        mad = float(np.median(np.abs(col[m] - med))) * 1.4826
        if mad <= 0:
            continue
        out[:, b] = np.where(m, (col - med) / mad, np.nan)
    return out


def part_d_arm(model: str, run_id: str, seed: int, sel: dict, tau_source: str,
               indicators: dict, *, smoke: bool = False) -> dict:
    entry = severity_entry(run_id, model, seed, smoke=smoke)
    tau, k, q95 = entry["tau"], entry["k"], entry["_q95"]
    from trial_common import load_arm_scorer

    scorer, norm = load_arm_scorer(run_id, model, seed)
    X, M = sel["X"], sel["M"]
    doy = minputs.doy_channels(sel["harvest_days"])
    z2, m_eff = arm_clean_z2(scorer, norm, X, M, doy)
    paths = mscoring.cumulative_channel_max(z2, m_eff, q95)
    n = X.shape[0]
    cycle_far = float(np.mean([mscoring.alarm_per_cycle(paths[i], tau, k) for i in range(n)]))
    agreement = {
        name: tparts.indicator_agreement(ind["values"], paths, tau,
                                         threshold_quantile=ind["threshold_quantile"])
        for name, ind in indicators.items()
    }
    print(f"[part-d:{model}:{seed}] cleanFAR(dev)={cycle_far:.4f} "
          + " ".join(f"{kk}:Δ={vv['rate_difference']:.3f}" for kk, vv in agreement.items()
                     if np.isfinite(vv["rate_difference"])))
    return {
        "model": model, "run_id": run_id, "seed": seed,
        "tau": float(tau), "k": int(k),
        "calibration_source": entry["_metrics_path"],
        "n_dev_cycles": int(n),
        "cycle_far_clean_dev": cycle_far,
        "agreement": agreement,
    }


def load_cwsi_et() -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """(values (F, T), field_ids (F,), scene_dates (T,)) of the processed
    CWSI_ET artifact (stats_current.zarr; 32-field subset) — or None when
    absent (the gate decides at runtime)."""
    zarr_path = DATA_PROCESSED / "satellite" / "stats_current.zarr"
    if not zarr_path.exists():
        return None
    import xarray as xr

    ds = xr.open_zarr(zarr_path, consolidated=False)
    if "cwsi_et" not in ds.data_vars:
        return None
    vals = np.asarray(ds["cwsi_et"].values, dtype=np.float64)
    fields = np.asarray(ds["field"].values, dtype=np.int64)
    dates = np.asarray(ds["time"].values).astype("datetime64[D]")
    return vals, fields, dates


def cwsi_et_grid(cwsi: tuple, field_ids: np.ndarray, start_dates: np.ndarray,
                 n_bins: int, bin_days: int = 15) -> tuple[np.ndarray, dict]:
    """Map the (F, T) CWSI_ET scene-date table onto the (N, T_bins) cycle-bin
    grid: bin b of a cycle covers [start + b·bin_days, start + (b+1)·bin_days);
    a scene date inside the window supplies the value; bins with no scene in
    the window stay NaN (absent — never filled, never interpolated)."""
    vals, cwsi_fields, dates = cwsi
    field_to_row = {int(f): i for i, f in enumerate(cwsi_fields)}
    date_to_col = {np.datetime64(d): i for i, d in enumerate(dates)}
    N = len(field_ids)
    out = np.full((N, n_bins), np.nan)
    n_matched = 0
    for n in range(N):
        row = field_to_row.get(int(field_ids[n]))
        if row is None:
            continue  # field not covered by the 32-field subset
        start = np.datetime64(str(start_dates[n])[:10], "D")
        for b in range(n_bins):
            lo = start + np.timedelta64(b * bin_days, "D")
            hi = lo + np.timedelta64(bin_days, "D")  # exclusive
            for d, col in date_to_col.items():
                if lo <= d < hi:
                    v = float(vals[row, col])
                    if np.isfinite(v):
                        out[n, b] = v
                        n_matched += 1
                    break  # first scene in the window (scenes are ≥5 days apart)
    return out, {"n_cycles_with_field_coverage": int(sum(1 for f in field_ids
                                                         if int(f) in field_to_row)),
                 "n_matched_cells": n_matched,
                 "n_cells_total": int(N * n_bins),
                 "note": ("first scene whose date falls inside each 15-day bin window; "
                          "fields outside the 32-field subset stay entirely absent")}


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--smoke", action="store_true")
    add_common_args(p)
    args = p.parse_args()
    t0 = time.time()
    manifest, data, sel, calib_idx, eval_idx, eval_hash = load_context()
    if args.smoke:
        sel = dict(sel)
        keep = np.arange(min(12, sel["X"].shape[0]))
        for kk in ("X", "M", "field_ids"):
            sel[kk] = sel[kk][keep]
        sel["harvest_days"] = sel["harvest_days"][keep]
        print(f"[part-d] SMOKE: dev cycles reduced to {len(keep)}")

    # ---- Indicators (availability gate first) -------------------------------
    avail = availability_check()
    X, M = sel["X"], sel["M"]
    n_bins = X.shape[1]
    # TVDI from EXISTING per-scene per-field LST/NDVI statistics (raw units);
    # 5 NDVI quantile bins so ~14 fields per bin clear min_points at the dev
    # set size (69 fields).
    ndvi_raw = np.where(M[:, :, NDVI_CHANNEL], X[:, :, NDVI_CHANNEL], np.nan)
    lst_raw = np.where(M[:, :, LST_CHANNEL], X[:, :, LST_CHANNEL], np.nan)
    tvdi, envelope_info = tparts.tvdis_from_field_stats(ndvi_raw, lst_raw,
                                                        n_ndvi_bins=5, min_points=8)
    envelope_info["n_ndvi_bins"] = 5
    # CWSI_ET (32-field subset) mapped by 15-day bin windows.
    cwsi = load_cwsi_et()
    cwsi_info = {"status": "absent (artifact missing at runtime)"}
    if cwsi is not None:
        cwsi_grid, cwsi_info = cwsi_et_grid(cwsi, sel["field_ids"],
                                            sel["start_dates"], n_bins)
    else:
        cwsi_grid = np.full(X.shape[:2], np.nan)
    # Phenology-phase-referenced NDVI deficit (across-field MAD units at the
    # same bin) — computed on the raw NDVI channel of the dev archive.
    ndvi_raw_full = np.where(M[:, :, NDVI_CHANNEL], X[:, :, NDVI_CHANNEL], 0.0)
    ndvi_deficit = -ndvi_deficit_proxy(
        ndvi_raw_full, M[:, :, NDVI_CHANNEL])  # positive = deficit (high = dry-like)
    indicators = {
        "tvdi_derived_proxy": {"values": tvdi, "threshold_quantile": 0.75},
        "ndvi_phase_deficit_mad": {"values": ndvi_deficit, "threshold_quantile": 0.75},
    }
    if cwsi is not None and np.isfinite(cwsi_grid).any():
        indicators["cwsi_et_32field_subset"] = {"values": cwsi_grid,
                                                "threshold_quantile": 0.75}

    arms = [("b1", args.b1_run_id, args.frozen_seed),
            ("gru_ae", args.gru_ae_run_id, args.frozen_seed)]
    arms += [("gru_pred", args.gru_pred_run_id, s) for s in gru_pred_seeds(args)]
    od = out_dir(args)
    per_arm = {}
    outputs = {}
    for model, run_id, seed in arms:
        rep = part_d_arm(model, run_id, seed, sel,
                         f"metrics_{model}_sev_recon_only.json", indicators,
                         smoke=args.smoke)
        path = od / f"part_d_{model}_seed{seed}.json"
        path.write_text(json.dumps(rep, indent=2), encoding="utf-8")
        per_arm[f"{model}:{seed}"] = rep
        outputs[f"{model}:{seed}"] = str(path.relative_to(Path(__file__).resolve().parent.parent))

    summary = {
        "type": "trial_part_d_indicators",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "wall_time_s": round(time.time() - t0, 1),
        "availability": avail,
        "cwsi_et_coverage": cwsi_info,
        "dependence_structure": (
            "the model input includes LST and NDVI; CWSI_ET derives from the METRIC energy "
            "balance (which consumes LST), and TVDI / the NDVI-deficit proxy are LST- and/or "
            "NDVI-derived — agreement is CORROBORATING evidence for output validity (proxy "
            "agreement toward L4), NOT independent ground truth and NOT proof of stress; the "
            "noun is 'suspected stress' / 'synthetic anomaly'; no L4 claim is made from "
            "correlation alone"),
        "tvdi_envelope": {"min_points": 8, "n_ndvi_bins": 5, "edge_quantile": 0.9,
                          **envelope_info},
        "indicator_definitions": {
            "cwsi_et_32field_subset": ("processed per-field CWSI_ET from stats_current.zarr "
                                       "(32-field subset), matched by 15-day bin windows; "
                                       "high CWSI = more water stress"),
            "tvdi_derived_proxy": ("per bin: across-field NDVI–LST feature space of the dev "
                                   "cycles at that bin; dry edge = q90 LST per NDVI quintile, "
                                   "wet edge = q10; TVDI = (LST−wet)/(dry−wet) clipped [0,1]"),
            "ndvi_phase_deficit_mad": ("per bin: (across-field median NDVI − field NDVI) / "
                                       "across-field MAD (×1.4826); positive = deficit vs the "
                                       "phenology phase norm"),
        },
        **provenance(args, manifest, eval_hash, sel, smoke=args.smoke),
        "per_arm": per_arm,
        "outputs": outputs,
    }
    (od / "part_d_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[part-d] summary → {od / 'part_d_summary.json'} (wall {time.time() - t0:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
