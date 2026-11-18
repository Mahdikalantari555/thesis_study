#!/usr/bin/env python3
"""Trial part A — natural-data false-alarm behaviour (predictive-ssl-
controlled-trial, task 2.1; owner's design verbatim).

On the dev evaluation subset, CLEAN cycles only, at each arm's calibrated τ
(from its severity-metrics dev calibration): cycle-level FAR, event-level FAR
(POT gap ≤ 2), per-field clean-score distribution (median/IQR of clean path
maxima per field — is the score concentrated in a few fields?) and temporal
stability (per-cycle path profile + recomputation determinism).

Gate: the new arm must NOT exceed the 5 % cycle-FAR budget and must not show
alarm concentration in a handful of fields. Read-only; writes
reports/dev/<trial-run-id>/part_a_*.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ssl_anomaly.monitor import scoring as mscoring  # noqa: E402
from ssl_anomaly.monitor import trial_parts as tparts  # noqa: E402
from trial_common import (  # noqa: E402
    add_common_args, arm_clean_z2, gru_pred_seeds, load_context, out_dir,
    provenance, severity_entry,
)


def parse_args():
    import argparse

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--smoke", action="store_true")
    add_common_args(p)
    return p.parse_args()


def part_a_arm(model: str, run_id: str, seed: int, sel: dict, eval_idx: list[int],
               *, smoke: bool = False, progress: bool = True) -> dict:
    t0 = time.time()
    entry = severity_entry(run_id, model, seed, smoke=smoke)
    tau, k, q95 = entry["tau"], entry["k"], entry["_q95"]
    scorer, norm = None, None
    from trial_common import load_arm_scorer  # local: heavy torch import

    scorer, norm = load_arm_scorer(run_id, model, seed)
    Xe = sel["X"][eval_idx]
    Me = sel["M"][eval_idx]
    from ssl_anomaly.monitor import inputs as minputs

    doye = minputs.doy_channels(sel["harvest_days"])[eval_idx]
    z2, m_eff = arm_clean_z2(scorer, norm, Xe, Me, doye)
    paths = mscoring.cumulative_channel_max(z2, m_eff, q95)
    z2_b, m_eff_b = arm_clean_z2(scorer, norm, Xe, Me, doye)  # determinism recompute
    paths_b = mscoring.cumulative_channel_max(z2_b, m_eff_b, q95)

    n = len(eval_idx)
    cycle_far = float(np.mean([mscoring.alarm_per_cycle(paths[i], tau, k) for i in range(n)]))
    efar = mscoring.event_far_from_paths(paths, [None] * n, tau, gap=2)
    field_ids = sel["field_ids"][eval_idx]
    dist = tparts.field_score_distribution(paths, tau, field_ids)
    stability = tparts.temporal_stability(paths, tau)
    det = tparts.determinism_check(paths, paths_b)
    if progress:
        print(f"[part-a:{model}:{seed}] cycleFAR={cycle_far:.4f} evFAR={efar['event_far']:.5f} "
              f"flagged={dist['n_flagged_cycles_total']}/{n} top2share={dist['top2_field_flag_share']:.2f} "
              f"det_mismatch={det} (wall {time.time() - t0:.1f}s)")
    return {
        "model": model, "run_id": run_id, "seed": seed,
        "tau": float(tau), "k": int(k),
        "calibration_source": entry["_metrics_path"],
        "n_eval_cycles": n,
        "cycle_far_clean_eval": cycle_far,
        "far_budget": 0.05,
        "cycle_far_within_budget": bool(cycle_far <= 0.05 + 1e-12),
        "event_far_clean_eval": efar,
        "field_distribution": dist,
        "temporal_stability": stability,
        "determinism_recompute_mismatches": det,
        "gate_no_concentration": bool(dist["n_flagged_cycles_total"] == 0
                                      or dist["top2_field_flag_share"] < 0.5),
        "wall_time_s": round(time.time() - t0, 1),
    }


def main() -> int:
    args = parse_args()
    t0 = time.time()
    manifest, data, sel, calib_idx, eval_idx, eval_hash = load_context()
    if args.smoke:
        eval_idx = eval_idx[:6]
        print(f"[part-a] SMOKE: eval subset reduced to {len(eval_idx)} cycles")

    arms: list[tuple[str, str, int]] = [
        ("b1", args.b1_run_id, args.frozen_seed),
        ("gru_ae", args.gru_ae_run_id, args.frozen_seed),
    ]
    arms += [("gru_pred", args.gru_pred_run_id, s) for s in gru_pred_seeds(args)]

    per_arm = {}
    outputs = {}
    od = out_dir(args)
    for model, run_id, seed in arms:
        rep = part_a_arm(model, run_id, seed, sel, eval_idx, smoke=args.smoke)
        path = od / f"part_a_{model}_seed{seed}.json"
        path.write_text(json.dumps(rep, indent=2), encoding="utf-8")
        per_arm[f"{model}:{seed}"] = rep
        outputs[f"{model}:{seed}"] = str(path.relative_to(Path(__file__).resolve().parent.parent))

    summary = {
        "type": "trial_part_a_natural",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "wall_time_s": round(time.time() - t0, 1),
        "gate": ("cycle-FAR within the 5% budget on clean evaluation cycles; no alarm "
                 "concentration in a handful of fields (top-2 flag share < 0.5 when any "
                 "flags exist)"),
        **provenance(args, manifest, eval_hash, sel, smoke=args.smoke),
        "per_arm": per_arm,
        "outputs": outputs,
    }
    (od / "part_a_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[part-a] summary → {od / 'part_a_summary.json'} (wall {time.time() - t0:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
