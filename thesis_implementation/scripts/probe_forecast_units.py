#!/usr/bin/env python3
"""Forecast-unit probe (change forecast-unit-probe; finding-20 path-C pre-test).

READ-ONLY, dev split only, zero training. Replaces gru_ae_main's LOO
prediction with PRE-REGISTERED untrained causal forecasters (persist / med3 /
trend4 — fixed a priori, no tuning) inside the otherwise IDENTICAL production
statistic (causal offset correction → per-(bin, channel) q95 from CLEAN
calibration residuals → trailing-3 channel-max → τ, k via choose_threshold at
the 5 % cycle-level FAR target), then runs the finding-18 severity sweep
UNCHANGED on the independent evaluation subset (salt `mdm80_eval_subset_v1`,
hash 6186edf8a06f82d3, identical injections rounds=2). B1 (frozen climatology)
is recomputed in the same harness as the reference arm and crosschecked
against its recorded finding-18 detection rates (0 mismatches required).

Per arm per cell (24 cells): detection rate + Wilson CI, median delay,
event-FAR (POT gap ≤ 2), MDM80 (">S6" censoring allowed), and the finding-20
waterfall quantities via diagnostics.decompose_injection (stage-1 onset
residual in z units AND in forecast-σ units = r/√q95 of the onset cell;
offset subtraction; SNR; post-onset absorption of the carry-forward
forecasters — reported, not hidden).

PRE-REGISTERED decision rule (evaluated verbatim, no goalpost movement):
  SUCCESS  ≥1 untrained arm with NON-CENSORED MDM80 ≤ S5 on persistent/ndvi
           and clean FAR within budget (calibrated cycle-FAR ≤ 5 % AND clean
           event-FAR on the evaluation subset ≤ 5 %) → path C justified; the
           measured MDM80 becomes the trained arm's target floor.
  NEGATIVE all untrained arms censored ">S6" on persistent/ndvi → honest
           negative; redirect weight to path B.
  otherwise → no arm met the success condition (recorded verbatim).

Writes ONLY reports/dev/<run_id>/probe_<arm>_seed2026.json + probe_summary.json
(+ progress jsonl). No threshold/model/platform writes, no test access. The
frozen gru_ae_main sidecar is verified byte-identical at exit.

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
from ssl_anomaly.monitor import forecast_units as funits  # noqa: E402
from ssl_anomaly.monitor import inputs as minputs  # noqa: E402
from ssl_anomaly.monitor import models as mmodels  # noqa: E402
from ssl_anomaly.monitor import perturbations as mpert  # noqa: E402
from ssl_anomaly.monitor import protocol as mproto  # noqa: E402
from ssl_anomaly.monitor import scoring as mscoring  # noqa: E402
from ssl_anomaly.monitor import severity_table as sev  # noqa: E402
from ssl_anomaly.monitor import splits as msplits  # noqa: E402

BAND_NAMES = ["ndvi", "blue", "green", "red", "nir", "swir1", "swir2", "lst"]
# Channels each injected index physically moves (decomposition reported on the
# alarm-driving channel — the production statistic takes the max over
# channels; savi drops live on red(3)+nir(4) via the sum-preserving solver).
CHANNELS_BY_INDEX = {"ndvi": (0,), "savi": (3, 4)}
EVAL_PARTITION_SALT = "mdm80_eval_subset_v1"   # must match scripts/eval_dev.py
EVAL_HASH_EXPECTED = "6186edf8a06f82d3"        # recorded independent eval subset
GRU_AE_RUN_ID = "gru_ae_20261114"              # frozen normalization source
B1_RUN_ID = "b1_20261114"                      # frozen B1 statistics source
B1_FROZEN_SEED = 2026
FAR_TARGET = 0.05
MDM80_TARGET = 0.80            # mirrors scripts/eval_dev.py verbatim
MDM80_CENSORED = 7             # numeric sentinel for ">S6" (ordering only)
PROBE_ARMS = ("persist", "med3", "trend4", "b1")
UNTRAINED_ARMS = ("persist", "med3", "trend4")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run-id", required=True, help="output run dir under reports/dev/ (probe writes only here)")
    p.add_argument("--gru-ae-run-id", default=GRU_AE_RUN_ID,
                   help="run id supplying the frozen train-split normalization (norm_stats.npz)")
    p.add_argument("--b1-run-id", default=B1_RUN_ID,
                   help="run id supplying the frozen B1 statistics")
    p.add_argument("--seed", type=int, default=B1_FROZEN_SEED,
                   help="frozen seed of the B1 statistics + output suffix")
    p.add_argument("--rounds", type=int, default=2,
                   help="injection rounds per cell (2 = identical injection set to the finding-18 sweep)")
    p.add_argument("--far", type=float, default=FAR_TARGET)
    p.add_argument("--smoke", action="store_true", help="6 eval cycles, 1 round (calibration unchanged)")
    p.add_argument("--notes", default="")
    return p.parse_args(argv)


def load_b1(run_id: str, seed: int) -> mmodels.B1PhaseZCausal:
    d = np.load(mproto.CHECKPOINTS_DEV_DIR / run_id / f"b1_phasez_causal_seed{seed}.npz",
                allow_pickle=True)
    b1 = mmodels.B1PhaseZCausal(use_doy=bool(d["use_doy"]), min_n=8)
    b1.median = d["median"]
    b1.scale = d["scale"]
    if "robust_range" in d.files:
        b1.robust_range = d["robust_range"]
    return b1


def arm_z_pred(arm: str, norm: dict | None, b1: mmodels.B1PhaseZCausal | None,
               X: np.ndarray, M: np.ndarray, doy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(z, pred_z) for one arm, mirroring diagnose_reconstruction.arm_z_pred.

    - untrained forecasters: z = apply_norm(frozen train-split norm, X, M);
      pred_z = causal one-step forecast of z from observed bins < o (same
      channel only); NaN where history is insufficient/broken.
    - B1: z = (X − median[g_bin, bin])/scale[g_bin, bin] with per-BIN season
      groups from its own DOY keying (returns a (T,) group array, not a
      per-cycle group); its prediction is 0 in this z-space.
    """
    if arm == "b1":
        assert b1 is not None
        N, T, C = X.shape
        med = np.empty((N, T, C), dtype=np.float64)
        scale = np.empty((N, T, C), dtype=np.float64)
        for i in range(N):
            g = (b1.season_group(doy[i, :, 0]) if b1.use_doy
                 else np.zeros(T, dtype=np.int64))  # (T,) per-bin groups
            med[i] = b1.median[g, np.arange(T)]
            scale[i] = b1.scale[g, np.arange(T)]
        z = np.where(M, (X.astype(np.float64) - med) / scale, 0.0)
        return z, np.zeros_like(z)
    assert norm is not None
    z = minputs.apply_norm(norm, X, M)
    pred = funits.forecast_batch(arm, z, M)
    return z, pred


def arm_z2(z: np.ndarray, pred: np.ndarray, M: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Squared residuals after the UNCHANGED production offset correction.

    Bins whose forecast is NaN do not score ("absent" semantics): they are
    excluded from the mask (they contribute nothing to the statistic and to
    the offset history). Returns (z2, effective_mask)."""
    m_eff = M & np.isfinite(pred)
    resid = np.where(m_eff, z - pred, 0.0)
    resid_corr = mscoring.causal_offset_correct(resid, m_eff)
    z2 = (resid_corr * resid_corr) * m_eff
    return z2, m_eff


def partition_calib_eval(cycle_keys: list[str]) -> tuple[list[int], list[int], str]:
    """Deterministic disjoint calibration/evaluation partition (same salt and
    rule as scripts/eval_dev.partition_calib_eval; the evaluation-subset hash
    is asserted against the recorded 6186edf8a06f82d3)."""
    if len(cycle_keys) < 8:
        raise ValueError(f"partition needs ≥8 dev cycles, got {len(cycle_keys)}")
    order = sorted(range(len(cycle_keys)),
                   key=lambda i: hashlib.sha256((EVAL_PARTITION_SALT + cycle_keys[i]).encode("utf-8")).hexdigest())
    n_eval = max(4, int(round(0.5 * len(cycle_keys))))
    eval_idx = sorted(order[-n_eval:])
    calib_idx = sorted(order[:-n_eval])
    eval_keys = sorted(cycle_keys[i] for i in eval_idx)
    eval_hash = hashlib.sha256(json.dumps(eval_keys).encode("utf-8")).hexdigest()[:16]
    return calib_idx, eval_idx, eval_hash


def evaluate_decision_rule(per_arm: dict[str, dict]) -> dict:
    """The pre-registered decision rule, verbatim (no goalpost movement)."""
    detail: dict[str, dict] = {}
    for arm in UNTRAINED_ARMS:
        r = per_arm[arm]
        mdm = r["mdm80"]["persistent/ndvi"]
        far_calib = r["far_achieved"]
        far_event_eval = r["event_far_clean_eval"]["event_far"]
        conds = {
            "non_censored_mdm80_persistent_ndvi": not mdm["censored"],
            "mdm80_le_S5": (not mdm["censored"]) and mdm["sentinel"] <= 5,
            "calibrated_cycle_far_within_budget": bool(far_calib <= FAR_TARGET + 1e-12),
            "clean_event_far_eval_within_budget": bool(far_event_eval <= FAR_TARGET + 1e-12),
        }
        detail[arm] = {
            "mdm80_persistent_ndvi": mdm["value"],
            "far_achieved_cycle": far_calib,
            "clean_event_far_eval": far_event_eval,
            "conditions": conds,
            "success": bool(all(conds.values())),
        }
    successes = [a for a in UNTRAINED_ARMS if detail[a]["success"]]
    all_censored = all(per_arm[a]["mdm80"]["persistent/ndvi"]["censored"] for a in UNTRAINED_ARMS)
    if successes:
        # Target floor = the best (lowest) successful MDM80 sentinel; ties
        # broken by the lower median delay at the MDM80 level.
        def _floor_key(a: str) -> tuple:
            mdm = per_arm[a]["mdm80"]["persistent/ndvi"]
            delay = mdm.get("median_delay_days", np.inf)
            delay = delay if (delay is not None and np.isfinite(delay)) else 1e18
            return (mdm["sentinel"], delay)

        best = min(successes, key=_floor_key)
        verdict = {
            "outcome": "success",
            "verdict_text": ("path C (forecasting/predictive-coding objective) justified; "
                             f"target floor = {best} MDM80 = "
                             f"{detail[best]['mdm80_persistent_ndvi']} on persistent/ndvi"),
            "successful_arms": successes,
            "target_floor_arm": best,
            "all_censored": False,
        }
    elif all_censored:
        verdict = {
            "outcome": "negative_all_censored",
            "verdict_text": ("honest negative: the realistic severity ladder is below the "
                             "information floor of these statistics at 5% cycle-FAR; path C "
                             "retraining upside is unproven; weight shifts to path B "
                             "(anomaly definition) and/or event-level accumulation analysis"),
            "successful_arms": [],
            "target_floor_arm": None,
            "all_censored": True,
        }
    else:
        verdict = {
            "outcome": "no_success_not_all_censored",
            "verdict_text": ("no untrained arm met the success condition (non-censored MDM80 ≤ S5 "
                             "on persistent/ndvi within the FAR budget); recorded verbatim — "
                             "neither the success nor the all-censored outcome"),
            "successful_arms": [],
            "target_floor_arm": None,
            "all_censored": False,
        }
    return {"rule": ("SUCCESS = ≥1 untrained arm non-censored MDM80 ≤ S5 on persistent/ndvi with "
                     "clean cycle- and event-FAR within the 5% budget; NEGATIVE = all arms censored "
                     ">S6 on persistent/ndvi"),
            "per_arm": detail,
            **verdict}


def probe_arm(arm: str, args: argparse.Namespace, X: np.ndarray, M: np.ndarray, doy: np.ndarray,
              cycle_keys: list[str], calib_idx: list[int], eval_idx: list[int],
              norm: dict | None, b1: mmodels.B1PhaseZCausal | None,
              progress_path: Path) -> dict:
    """One probe arm: calibration on the clean CALIBRATION subset only, then
    the unchanged finding-18 sweep on the INDEPENDENT evaluation subset."""
    t0 = time.time()
    n_ch = X.shape[2]

    def progress(**kw) -> None:
        rec = {"stage": "probe", "arm": arm, "wall_s": round(time.time() - t0, 1), **kw}
        with progress_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    # ---- Clean scores (calibration + evaluation) ---------------------------
    z_all, pred_all = arm_z_pred(arm, norm, b1, X, M, doy)
    z2_all, m_eff_all = arm_z2(z_all, pred_all, M)
    cell_q95 = mscoring.cell_q95_normalizer(z2_all[calib_idx], m_eff_all[calib_idx])
    clean_paths = mscoring.cumulative_channel_max(z2_all, m_eff_all, cell_q95)

    # ---- Threshold (τ, k) on the CALIBRATION subset (production semantics) --
    ksel = mpert.inject_index_drop_dataset(
        X[calib_idx], M[calib_idx], level_id="S3", family=sev.ACUTE_FAMILY,
        index="ndvi", round_idx=0,
    )
    Xk = np.stack([r.x for r in ksel])
    Mk = np.stack([r.m for r in ksel])
    zk, predk = arm_z_pred(arm, norm, b1, Xk, Mk, doy[calib_idx][[r.source_row for r in ksel]])
    z2k, mek = arm_z2(zk, predk, Mk)
    ksel_paths = mscoring.cumulative_channel_max(z2k, mek, cell_q95)
    threshold, per_k = mscoring.choose_threshold(
        [clean_paths[i] for i in calib_idx],
        [ksel_paths[j] for j in range(len(ksel))],
        [r.onset_bin for r in ksel],
        far_target=args.far,
    )
    tau, k = threshold.tau, threshold.k
    progress(step="threshold_calibration", tau=float(tau), k=int(k),
             far_achieved=float(threshold.far_achieved))
    if tau >= 1e9 or not np.isfinite(tau):
        # Pre-registered: degenerate calibration is a finding, not something
        # to tune away. Record and continue (the sweep still runs).
        print(f"[probe:{arm}] WARNING degenerate calibration: tau={tau}")

    # ---- Severity sweep on the INDEPENDENT evaluation subset ----------------
    Xe, Me, doye = X[eval_idx], M[eval_idx], doy[eval_idx]
    n_eval = len(eval_idx)
    levels = sev.load_table()
    cells: dict[str, dict] = {}
    det_flags_by_cell: dict[str, list[int]] = {}
    decomps: dict[str, list] = {}
    window_pools: dict[str, list] = {}
    path_pool: dict[str, list[np.ndarray]] = {}
    delay_pools: dict[str, list[float]] = {}
    for lv in levels:
        for fam in (sev.ACUTE_FAMILY, sev.PERSISTENT_FAMILY):
            for index in ("ndvi", "savi"):
                key = f"{lv.level_id}/{fam}/{index}"
                det_flags: list[int] = []
                delays: list[float] = []
                windows: list = []
                paths_list: list[np.ndarray] = []
                cell_decomps: list = []
                for rnd in range(max(1, args.rounds)):
                    results = mpert.inject_index_drop_dataset(
                        Xe, Me, level_id=lv.level_id, family=fam, index=index, round_idx=rnd,
                    )
                    Xinj = np.stack([r.x for r in results])
                    Minj = np.stack([r.m for r in results])
                    zinj, predinj = arm_z_pred(
                        arm, norm, b1, Xinj, Minj, doye[[r.source_row for r in results]])
                    z2inj, meinj = arm_z2(zinj, predinj, Minj)
                    inj_paths = mscoring.cumulative_channel_max(z2inj, meinj, cell_q95)
                    for j, r in enumerate(results):
                        fb = mscoring.first_alarm_bin(inj_paths[j], tau, k, r.onset_bin)
                        det_flags.append(1 if fb >= 0 else 0)
                        if fb >= 0:
                            delays.append(float((fb - r.onset_bin) * 15))
                        windows.append([(r.onset_bin, r.onset_bin + r.meta["n_bins_window"])])
                        paths_list.append(inj_paths[j])
                        # Waterfall on the alarm-driving channel (largest onset
                        # normalized contribution — production max rule). The
                        # decomposition mask is the EFFECTIVE mask (bins whose
                        # forecast is NaN do not score): a raw NaN prediction
                        # would otherwise poison the offset history and the
                        # trailing path with NaN (gru_ae/B1 predictions are
                        # always finite, so production never saw this).
                        z_nat_j = z_all[eval_idx[r.source_row]]
                        per_ch = {
                            ch: mdiag.decompose_injection(
                                z_inj=zinj[j], pred_z=predinj[j],
                                z_natural=z_nat_j, mask=meinj[j], q95=cell_q95,
                                tau=float(tau), k=int(k), onset_bin=r.onset_bin,
                                duration=r.meta["n_bins_window"], channel=ch,
                            )
                            for ch in CHANNELS_BY_INDEX[index]
                        }

                        def _contrib(d: mdiag.StageDecomposition) -> float:
                            return (d.normalized_contribution
                                    if np.isfinite(d.normalized_contribution) else -np.inf)

                        cell_decomps.append(per_ch[max(per_ch, key=lambda c: _contrib(per_ch[c]))])
                    progress(cell=key, round=rnd)
                n = len(det_flags)
                n_det = int(sum(det_flags))
                lo, hi = mscoring.wilson_ci(n_det, n)
                efar = mscoring.event_far_from_paths(np.stack(paths_list), windows, tau, gap=2)
                cells[key] = {
                    "n": n, "n_detected": n_det,
                    "detection_rate": n_det / max(1, n),
                    "wilson_ci95": [round(lo, 4), round(hi, 4)],
                    "median_delay_days": (float(np.median(delays)) if delays else float("nan")),
                    "event_far": efar["event_far"],
                    "n_events": efar["n_events"], "n_false_events": efar["n_false_events"],
                    "level_id": lv.level_id, "family": fam, "index": index,
                    "delta_ndvi": lv.delta_ndvi,
                    "duration_bins": (sev.PERSISTENT_DURATION_BINS if fam == sev.PERSISTENT_FAMILY
                                      else lv.duration_bins),
                }
                det_flags_by_cell[key] = det_flags
                delay_pools[key] = delays
                window_pools[key] = windows
                path_pool[key] = paths_list
                decomps[key] = cell_decomps

    # ---- MDM80 per family × index (mirrors scripts/eval_dev.py verbatim) ----
    mdm80: dict[str, dict] = {}
    for fam in (sev.ACUTE_FAMILY, sev.PERSISTENT_FAMILY):
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

    # ---- Clean event FAR (eval + calibration subsets) -----------------------
    clean_efar_eval = mscoring.event_far_from_paths(
        clean_paths[eval_idx], [None] * n_eval, tau, gap=2)
    clean_efar_calib = mscoring.event_far_from_paths(
        clean_paths[calib_idx], [None] * len(calib_idx), tau, gap=2)

    # ---- Finding-20 waterfall summary + forecast-σ units --------------------
    waterfall = mdiag.summarize_cells(decomps)
    for key, w in waterfall.items():
        # Onset residual in FORECAST-σ units: r_onset / sqrt(q95 of the onset
        # cell) — the clean one-step-residual scale of THIS arm (the unit the
        # per-bin statistic requirement sqrt(τ·q95) is expressed in).
        fsig = [abs(d.onset_residual_sigma) / np.sqrt(d.cell_q95)
                for d in decomps[key] if np.isfinite(d.cell_q95) and d.cell_q95 > 0]
        w["onset_residual_fsigma"] = mdiag._med_iqr(fsig)
        # Post-offset requirement ratio: r′/sqrt(τ·q95) = sqrt(snr1).
        w["requirement_ratio_after_correction"] = mdiag._med_iqr(
            [np.sqrt(d.snr1) for d in decomps[key] if np.isfinite(d.snr1) and d.snr1 >= 0])

    # ---- Internal consistency: detection recomputed from stored paths/τ/k ---
    recompute_mismatch = 0
    for key, flags in det_flags_by_cell.items():
        for j, p in enumerate(path_pool[key]):
            fb = mscoring.first_alarm_bin(p, tau, k, window_pools[key][j][0][0])
            if (1 if fb >= 0 else 0) != flags[j]:
                recompute_mismatch += 1

    wall = time.time() - t0
    return {
        "type": "forecast_unit_probe",
        "arm": arm,
        "trained": False,
        "frozen_seed": args.seed,
        "protocol": "severity_sweep_v1",
        "severity_table_sha256": sev.severity_table_hash(),
        "eval_subset_sha256": args._eval_hash,
        "splits_locked_sha256": args._manifest_sha,
        "git_sha": mproto.git_sha(),
        "device": "cpu",
        "wall_time_s": round(wall, 1),
        "smoke": bool(args.smoke),
        "ladder_rung": "L2",
        "claim_noun": "synthetic anomaly",
        "data_source": "real490 (masked rebuild from stats.zarr)",
        "date_range": {"first": str(args._start_dates[0])[:10],
                       "last": str(args._end_dates[-1])[:10]},
        "n_calib_cycles": len(calib_idx), "n_eval_cycles": n_eval,
        "rounds": max(1, args.rounds),
        "far_target": args.far,
        "tau": float(tau), "k": int(k), "far_achieved": float(threshold.far_achieved),
        "threshold_per_k": per_k,
        "per_cell_q95_flat": [round(float(v), 6) for row in cell_q95 for v in row],
        "alarm_statistic": "trailing3_window_channel_max_z2_cell_q95_normalized",
        "prediction_semantics": (f"untrained causal one-step forecast arm={arm} "
                                 "(same-channel history; gap>2 breaks history → bin does not score)"),
        "mdm80": mdm80,
        "cells": cells,
        "event_far_clean_eval": clean_efar_eval,
        "event_far_clean_calibration": clean_efar_calib,
        "waterfall": waterfall,
        "internal_consistency": {
            "detection_recompute_mismatches": int(recompute_mismatch),
        },
        "notes": args.notes,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    t0 = time.time()

    manifest = msplits.load_splits_locked()
    args._manifest_sha = manifest["manifest_sha256"]
    data = minputs.load_masked_cycles()
    sel = mproto.select_splits(data, manifest, splits=("dev",))
    args._start_dates, args._end_dates = sel["start_dates"], sel["end_dates"]

    X, M = sel["X"], sel["M"]
    doy = minputs.doy_channels(sel["harvest_days"])
    cycle_keys = list(sel["cycle_keys"])
    calib_idx, eval_idx, eval_hash = partition_calib_eval(cycle_keys)
    if eval_hash != EVAL_HASH_EXPECTED:
        raise RuntimeError(
            f"evaluation subset hash {eval_hash} != recorded {EVAL_HASH_EXPECTED} "
            "(partition drift — STOP, do not run the probe on a moved subset)")
    args._eval_hash = eval_hash
    print(f"[probe] dev cycles={len(cycle_keys)} calib={len(calib_idx)} eval={len(eval_idx)} "
          f"(hash {eval_hash})")

    norm = minputs.load_norm(mproto.DEV_DIR / args.gru_ae_run_id / "norm_stats.npz")
    b1 = load_b1(args.b1_run_id, args.seed)

    if args.smoke:
        keep = np.array(eval_idx[:6])
        eval_idx = [int(i) for i in keep]
        args.rounds = 1
        print(f"[probe] SMOKE: eval subset reduced to {len(eval_idx)} cycles, rounds=1")

    out_dir = mproto.DEV_DIR / args.run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    sidecar_path = REPO_ROOT / "checkpoints" / "gru_ae_main.json"
    sidecar_sha_before = (hashlib.sha256(sidecar_path.read_bytes()).hexdigest()
                          if sidecar_path.exists() else None)

    per_arm: dict[str, dict] = {}
    outputs: dict[str, str] = {}
    for arm in PROBE_ARMS:
        progress_path = out_dir / f"progress_probe_{arm}.jsonl"
        rep = probe_arm(arm, args, X, M, doy, cycle_keys, calib_idx, eval_idx, norm, b1,
                        progress_path)
        out_path = out_dir / f"probe_{arm}_seed{args.seed}.json"
        out_path.write_text(json.dumps(rep, indent=2), encoding="utf-8")
        per_arm[arm] = rep
        outputs[arm] = str(out_path.relative_to(REPO_ROOT))
        mdm_str = " ".join(f"{kk}={vv['value']}" for kk, vv in rep["mdm80"].items())
        print(f"[probe:{arm}] tau={rep['tau']:.4f} k={rep['k']} far={rep['far_achieved']:.4f} "
              f"MDM80 {mdm_str} wall={rep['wall_time_s']}s → {out_path.name}")

    # ---- B1 crosscheck against the recorded finding-18 numbers --------------
    # Meaningful only at rounds=2 on the FULL evaluation subset (the smoke's
    # 6-cycle subset cannot reproduce n=68 rates); τ/k are checked either way.
    if args.smoke:
        b1_crosscheck = {
            "pass": None, "skipped": "smoke (eval subset reduced; τ/k equality still verified)",
            "tau_match": abs(float(per_arm["b1"]["tau"]) - 9.1524) < 1e-3,
        }
    else:
        b1_crosscheck = {"required_mismatches": 0}
        try:
            ref_path = mproto.DEV_DIR / args.b1_run_id / "metrics_b1_sev_recon_only.json"
            ref = json.loads(ref_path.read_text(encoding="utf-8"))
            ref_entry = [r for r in ref["per_seed"] if int(r["seed"]) == int(args.seed)][0]
            mismatches = []
            if abs(float(ref_entry["tau"]) - float(per_arm["b1"]["tau"])) > 1e-9:
                mismatches.append(f"tau {ref_entry['tau']} vs {per_arm['b1']['tau']}")
            if int(ref_entry["k"]) != int(per_arm["b1"]["k"]):
                mismatches.append(f"k {ref_entry['k']} vs {per_arm['b1']['k']}")
            for key, ref_cell in ref_entry["cells"].items():
                got = per_arm["b1"]["cells"][key]["detection_rate"]
                if abs(float(ref_cell["detection_rate"]) - got) > 1e-9:
                    mismatches.append(f"{key}: {ref_cell['detection_rate']} vs {got}")
            b1_crosscheck = {
                "reference": str(ref_path.relative_to(REPO_ROOT)),
                "reference_seed": int(args.seed),
                "mismatches": mismatches,
                "n_cells_compared": len(ref_entry["cells"]),
                "pass": len(mismatches) == 0,
            }
            print(f"[probe] B1 crosscheck vs finding-18 recorded rates: "
                  f"{'PASS (0 mismatches)' if not mismatches else f'FAIL {mismatches[:6]}'}")
        except FileNotFoundError as e:
            b1_crosscheck = {"pass": None, "error": str(e)}
            print(f"[probe] B1 crosscheck SKIPPED (reference metrics not found: {e})")

    decision = evaluate_decision_rule(per_arm)
    print(f"[probe] DECISION RULE [{decision['outcome']}]: {decision['verdict_text']}")

    sidecar_sha_after = (hashlib.sha256(sidecar_path.read_bytes()).hexdigest()
                         if sidecar_path.exists() else None)
    unchanged = sidecar_sha_before == sidecar_sha_after
    print(f"[probe] frozen sidecar byte-identical: {unchanged}")

    summary = {
        "type": "forecast_unit_probe_summary",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "wall_time_s": round(time.time() - t0, 1),
        "run_id": args.run_id,
        "frozen_seed": args.seed,
        "smoke": bool(args.smoke),
        "rounds": max(1, args.rounds),
        "eval_subset_sha256": eval_hash,
        "severity_table_sha256": sev.severity_table_hash(),
        "splits_locked_sha256": manifest["manifest_sha256"],
        "git_sha": mproto.git_sha(),
        "ladder_rung": "L2",
        "claim_noun": "synthetic anomaly",
        "sidecar_byte_identical": bool(unchanged),
        "outputs": outputs,
        "mdm80_per_arm": {a: per_arm[a]["mdm80"] for a in PROBE_ARMS},
        "calibration_per_arm": {a: {"tau": per_arm[a]["tau"], "k": per_arm[a]["k"],
                                    "far_achieved": per_arm[a]["far_achieved"],
                                    "event_far_clean_eval": per_arm[a]["event_far_clean_eval"],
                                    "event_far_clean_calibration": per_arm[a]["event_far_clean_calibration"]}
                                for a in PROBE_ARMS},
        "onset_residual_fsigma_persistent_ndvi": {
            a: {lv.level_id: per_arm[a]["waterfall"].get(f"{lv.level_id}/persistent/ndvi", {}).get(
                "onset_residual_fsigma")
                for lv in sev.load_table()}
            for a in PROBE_ARMS
        },
        "b1_crosscheck_vs_finding18": b1_crosscheck,
        "decision_rule": decision,
        "notes": args.notes,
    }
    summary_path = out_dir / "probe_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[probe] summary → {summary_path} (wall {time.time() - t0:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
