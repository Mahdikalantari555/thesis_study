#!/usr/bin/env python3
"""Trial part C — the absorption experiment (predictive-ssl-controlled-trial,
task 2.3; finding-20 hypothesis, direct test).

For persistent-family injections (S1–S6 × persistent × {ndvi, savi}, the
identical sweep machinery, rounds=2, independent evaluation subset), each
arm's one-step error at the owner's THREE CHECKPOINTS on the alarm-driving
channel:

  1. before onset        — the clean forecast error at the same bins
  2. first step after    — the error spike at the onset bin
  3. several steps after — the mean error at bins onset+2 … onset+5

Reported in z units AND forecast-σ units, with the persistence ratio
(post/onset step: does the error PERSIST through the sustained drop, or decay
as the prediction adapts?) and the finding-20 absorption ratio A computed by
``diagnostics.decompose_injection`` UNCHANGED — so gru_pred's A is directly
comparable to gru_ae's measured α ≈ 0.38–0.50. Pre-registered honest caveat:
a fast adaptive predictive model COULD also absorb (recursive state feeding
on its own predictions); that is exactly what this part measures — a NEGATIVE
result is recorded as such, not tuned away.

Interpretation limit (finding 20): S1–S2 absorption values are
noise-saturated → interpret S4+ only. Read-only; writes
reports/dev/<trial-run-id>/part_c_*.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ssl_anomaly.monitor import diagnostics as mdiag  # noqa: E402
from ssl_anomaly.monitor import inputs as minputs  # noqa: E402
from ssl_anomaly.monitor import perturbations as mpert  # noqa: E402
from ssl_anomaly.monitor import scoring as mscoring  # noqa: E402
from ssl_anomaly.monitor import severity_table as sev  # noqa: E402
from ssl_anomaly.monitor import trial_parts as tparts  # noqa: E402
from trial_common import (  # noqa: E402
    CHANNELS_BY_INDEX, add_common_args, arm_z_pred_both, gru_pred_seeds,
    load_context, out_dir, provenance, severity_entry,
)


def parse_args():
    import argparse

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rounds", type=int, default=2)
    p.add_argument("--smoke", action="store_true")
    add_common_args(p)
    return p.parse_args()


def part_c_arm(model: str, run_id: str, seed: int, sel: dict, eval_idx: list[int],
               rounds: int, *, smoke: bool = False) -> dict:
    t0 = time.time()
    entry = severity_entry(run_id, model, seed, smoke=smoke)
    tau, k, q95 = entry["tau"], entry["k"], entry["_q95"]
    from trial_common import load_arm_scorer

    scorer, norm = load_arm_scorer(run_id, model, seed)
    Xe, Me = sel["X"][eval_idx], sel["M"][eval_idx]
    doye = minputs.doy_channels(sel["harvest_days"])[eval_idx]
    z_nat_all, pred_nat_all = arm_z_pred_both(scorer, norm, Xe, Me, doye)

    cells: dict[str, list] = {}
    for lv in sev.load_table():
        for index in ("ndvi", "savi"):
            key = f"{lv.level_id}/persistent/{index}"
            records: list[dict] = []
            for rnd in range(max(1, rounds)):
                results = mpert.inject_index_drop_dataset(
                    Xe, Me, level_id=lv.level_id, family=sev.PERSISTENT_FAMILY,
                    index=index, round_idx=rnd,
                )
                Xinj = np.stack([r.x for r in results])
                Minj = np.stack([r.m for r in results])
                zinj_all, predinj_all = arm_z_pred_both(
                    scorer, norm, Xinj, Minj, doye[[r.source_row for r in results]])
                for j, r in enumerate(results):
                    per_ch = {}
                    for ch in CHANNELS_BY_INDEX[index]:
                        d = mdiag.decompose_injection(
                            z_inj=zinj_all[j], pred_z=predinj_all[j],
                            z_natural=z_nat_all[r.source_row], mask=Minj[j], q95=q95,
                            tau=float(tau), k=int(k), onset_bin=r.onset_bin,
                            duration=r.meta["n_bins_window"], channel=ch,
                        )
                        per_ch[ch] = d
                    # Alarm-driving channel: largest onset normalized
                    # contribution (the production statistic maxes channels).
                    d_best = per_ch[max(per_ch, key=lambda c: (
                        per_ch[c].normalized_contribution
                        if np.isfinite(per_ch[c].normalized_contribution) else -np.inf))]
                    ck = tparts.checkpoint_errors(
                        zinj_all[j], predinj_all[j],
                        z_nat_all[r.source_row], pred_nat_all[r.source_row],
                        Minj[j], q95, r.onset_bin,
                    )
                    records.append({
                        "onset_bin": int(r.onset_bin),
                        "phase": r.phase,
                        "channel": int(d_best.channel) if hasattr(d_best, "channel") else None,
                        "absorption_A": (float(d_best.absorption)
                                         if d_best.absorption is not None else float("nan")),
                        "onset_residual_sigma": float(d_best.onset_residual_sigma),
                        **{kk: vv for kk, vv in ck.items()},
                    })
            cells[key] = records

    def _med(values: list) -> float:
        arr = np.asarray([float(v) for v in values
                          if v is not None and np.isfinite(float(v))], dtype=np.float64)
        return float(np.median(arr)) if arr.size else float("nan")

    summary_cells = {}
    for key, recs in cells.items():
        summary_cells[key] = {
            "n": len(recs),
            "absorption_A_median": _med([r["absorption_A"] for r in recs]),
            "pre_error_fsigma_median": _med([r.get("pre_error_fsigma") for r in recs]),
            "onset_step_error_fsigma_median": _med([r.get("onset_step_error_fsigma") for r in recs]),
            "post_steps_error_fsigma_median": _med([r.get("post_steps_error_fsigma") for r in recs]),
            "persistence_ratio_median": _med([r.get("persistence_ratio") for r in recs]),
        }
    print(f"[part-c:{model}:{seed}] "
          + " ".join(f"{kk.split('/')[0]}:A={vv['absorption_A_median']:.2f}"
                     for kk, vv in summary_cells.items() if kk.startswith("S"))
          + f" (wall {time.time() - t0:.1f}s)")
    return {
        "model": model, "run_id": run_id, "seed": seed,
        "tau": float(tau), "k": int(k),
        "calibration_source": entry["_metrics_path"],
        "rounds": max(1, rounds),
        "n_injections_total": sum(len(v) for v in cells.values()),
        "cells": summary_cells,
        "records": {kk: vv for kk, vv in cells.items()},
        "wall_time_s": round(time.time() - t0, 1),
    }


def main() -> int:
    args = parse_args()
    t0 = time.time()
    manifest, data, sel, calib_idx, eval_idx, eval_hash = load_context()
    rounds = args.rounds
    if args.smoke:
        eval_idx = eval_idx[:6]
        rounds = 1
        print(f"[part-c] SMOKE: eval subset reduced to {len(eval_idx)} cycles, rounds=1")

    arms = [("b1", args.b1_run_id, args.frozen_seed),
            ("gru_ae", args.gru_ae_run_id, args.frozen_seed)]
    arms += [("gru_pred", args.gru_pred_run_id, s) for s in gru_pred_seeds(args)]

    od = out_dir(args)
    per_arm = {}
    outputs = {}
    for model, run_id, seed in arms:
        rep = part_c_arm(model, run_id, seed, sel, eval_idx, rounds, smoke=args.smoke)
        path = od / f"part_c_{model}_seed{seed}.json"
        path.write_text(json.dumps(rep, indent=2), encoding="utf-8")
        per_arm[f"{model}:{seed}"] = {k: rep[k] for k in ("cells", "n_injections_total")}
        outputs[f"{model}:{seed}"] = str(path.relative_to(Path(__file__).resolve().parent.parent))

    # The gate quantities (raw material for the five-gate table): A(gru_pred)
    # vs A(gru_ae) at S4–S6 persistent (interpret S4+ only — finding 20) and
    # the persistence ratios.
    def _a(arm: str, level: str, index: str) -> float:
        r = per_arm.get(arm)
        if r is None:
            return float("nan")
        return r["cells"].get(f"{level}/persistent/{index}", {}).get("absorption_A_median", float("nan"))

    gate_material = {}
    for level in ("S4", "S5", "S6"):
        for index in ("ndvi", "savi"):
            gate_material[f"{level}/persistent/{index}"] = {
                "A_gru_ae": _a(f"gru_ae:{args.frozen_seed}", level, index),
                "A_gru_pred_per_seed": {s: _a(f"gru_pred:{s}", level, index)
                                        for s in gru_pred_seeds(args)},
                "A_b1": _a(f"b1:{args.frozen_seed}", level, index),
            }
    summary = {
        "type": "trial_part_c_absorption",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "wall_time_s": round(time.time() - t0, 1),
        "hypothesis": ("predictive error persists through a sustained drop "
                       "(A(gru_pred) ≈ 0) vs reconstruction absorption "
                       "(A(gru_ae) ≈ 0.38–0.50); honest caveat: an adaptive "
                       "predictive model could also absorb — measured, not tuned"),
        "interpretation_limit": "S1–S2 absorption is noise-saturated (finding 20); interpret S4+ only",
        **provenance(args, manifest, eval_hash, sel, smoke=args.smoke),
        "per_arm": per_arm,
        "gate_material_S4_to_S6": gate_material,
        "outputs": outputs,
    }
    (od / "part_c_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[part-c] summary → {od / 'part_c_summary.json'} (wall {time.time() - t0:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
