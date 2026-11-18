#!/usr/bin/env python3
"""Trial part B — severity protocol UNCHANGED, three arms recomputed in the
same run (predictive-ssl-controlled-trial, task 2.2).

Runs scripts/eval_dev.py --protocol severity for the three arms on
trial-scoped copies of the frozen run artifacts (checkpoints + norm), so the
recorded finding-18 metrics files stay byte-identical, then crosschecks the
B1 and gru_ae_main recomputed per-cell detection rates against the RECORDED
finding-18 values at rounds=2 — 0 mismatches required; any drift is a defect
to report, not to absorb.

Identical injections by construction: inject_index_drop_dataset is a
deterministic function of (X, M, level, family, index, round). Read-only over
the frozen artifacts; writes reports/dev/<trial-run-id>/ + trial-scoped run
dirs + dev_log rows (honest record of the recompute runs).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ssl_anomaly.monitor import protocol as mproto  # noqa: E402
from trial_common import add_common_args, gru_pred_seeds  # noqa: E402

ARMS = ("b1", "gru_ae", "gru_pred")


def parse_args():
    import argparse

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--smoke", action="store_true", help="smoke through eval_dev's own --smoke")
    add_common_args(p)
    return p.parse_args()


def stage_trial_run(src_run_id: str, model: str, seeds: list[int], trial_run_id: str) -> None:
    """Copy the frozen artifacts a severity run needs into a trial-scoped run
    dir (norm + checkpoints); the originals are never written."""
    src_reports = mproto.DEV_DIR / src_run_id
    dst_reports = mproto.DEV_DIR / trial_run_id
    dst_reports.mkdir(parents=True, exist_ok=True)
    norm_src = src_reports / "norm_stats.npz"
    if norm_src.exists():
        shutil.copyfile(norm_src, dst_reports / "norm_stats.npz")
        side = src_reports / "norm_stats.npz.json"
        if side.exists():
            shutil.copyfile(side, dst_reports / "norm_stats.npz.json")
    dst_ckpt = mproto.CHECKPOINTS_DEV_DIR / trial_run_id
    dst_ckpt.mkdir(parents=True, exist_ok=True)
    src_ckpt = mproto.CHECKPOINTS_DEV_DIR / src_run_id
    for seed in seeds:
        name = (f"b1_phasez_causal_seed{seed}.npz" if model == "b1"
                else f"{model}_seed{seed}.pt")
        src = src_ckpt / name
        if not src.exists():
            raise FileNotFoundError(
                f"missing checkpoint for the {model} arm: {src} — has training finished?")
        shutil.copyfile(src, dst_ckpt / name)


def crosscheck_recorded(model: str, src_run_id: str, trial_run_id: str, seeds: list[int]) -> dict:
    """Per-cell detection rates (and τ/k) of the trial recompute vs the
    RECORDED finding-18 metrics — 0 mismatches required at rounds=2."""
    rec_path = mproto.DEV_DIR / src_run_id / f"metrics_{model}_sev_recon_only.json"
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    tri = json.loads((mproto.DEV_DIR / trial_run_id /
                      f"metrics_{model}_sev_recon_only.json").read_text(encoding="utf-8"))
    mismatches = []
    for seed in seeds:
        r = [x for x in rec["per_seed"] if int(x["seed"]) == seed][0]
        t = [x for x in tri["per_seed"] if int(x["seed"]) == seed][0]
        if abs(float(r["tau"]) - float(t["tau"])) > 1e-9:
            mismatches.append(f"seed{seed} tau {r['tau']} vs {t['tau']}")
        if int(r["k"]) != int(t["k"]):
            mismatches.append(f"seed{seed} k {r['k']} vs {t['k']}")
        for key, rcell in r["cells"].items():
            got = t["cells"][key]["detection_rate"]
            if abs(float(rcell["detection_rate"]) - float(got)) > 1e-9:
                mismatches.append(f"seed{seed} {key}: {rcell['detection_rate']} vs {got}")
    return {
        "reference": str(rec_path.relative_to(REPO_ROOT)),
        "seeds_compared": seeds,
        "n_cells_per_seed": len(rec["per_seed"][0]["cells"]),
        "mismatches": mismatches,
        "pass": len(mismatches) == 0,
    }


def main() -> int:
    args = parse_args()
    t0 = time.time()
    py = sys.executable
    suffix = "20261114"
    arms = [
        ("b1", args.b1_run_id, [args.frozen_seed]),
        ("gru_ae", args.gru_ae_run_id, [args.frozen_seed]),
        ("gru_pred", args.gru_pred_run_id, gru_pred_seeds(args)),
    ]
    outputs = {}
    crosschecks = {}
    for model, src_run_id, seeds in arms:
        trial_run_id = f"trial_{model}_{suffix}"
        stage_trial_run(src_run_id, model, seeds, trial_run_id)
        cmd = [py, "-X", "utf8", str(REPO_ROOT / "scripts" / "eval_dev.py"),
               "--model", model, "--run-id", trial_run_id,
               "--seeds", ",".join(str(s) for s in seeds), "--protocol", "severity"]
        if args.smoke:
            cmd.append("--smoke")
        print(f"[part-b] running: {' '.join(cmd)}")
        proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=3600)
        if proc.returncode != 0:
            print(proc.stdout[-3000:])
            print(proc.stderr[-3000:], file=sys.stderr)
            raise RuntimeError(f"eval_dev failed for {model} (exit {proc.returncode})")
        out_path = (mproto.DEV_DIR / trial_run_id /
                    f"metrics_{model}_sev_recon_only{'_smoke' if args.smoke else ''}.json")
        outputs[model] = str(out_path.relative_to(REPO_ROOT))
        print(f"[part-b] {model}: metrics → {out_path.name}")

    if not args.smoke:
        # The recompute crosscheck is meaningful only at rounds=2 on the full
        # eval subset (the smoke subset cannot reproduce n=68 rates).
        for model, src_run_id, seeds in arms[:2]:  # b1 + gru_ae recorded references
            crosschecks[model] = crosscheck_recorded(model, src_run_id,
                                                     f"trial_{model}_{suffix}", seeds)
            cc = crosschecks[model]
            print(f"[part-b] crosscheck {model} vs recorded finding-18: "
                  f"{'PASS (0 mismatches)' if cc['pass'] else f'FAIL {cc['mismatches'][:6]}'}")

    od = mproto.DEV_DIR / args.trial_run_id
    od.mkdir(parents=True, exist_ok=True)
    # Three-arm comparison table (per seed: MDM80 + key cells + event-FAR).
    comparison = {}
    for model in ARMS:
        trial_run_id = f"trial_{model}_{suffix}"
        name = f"metrics_{model}_sev_recon_only{'_smoke' if args.smoke else ''}.json"
        metrics = json.loads((mproto.DEV_DIR / trial_run_id / name).read_text(encoding="utf-8"))
        comparison[model] = [
            {"seed": r["seed"], "tau": r["tau"], "k": r["k"],
             "far_achieved": r["far_achieved"],
             "mdm80": {k: v["value"] for k, v in r["mdm80"].items()},
             "cells_S6": {key: r["cells"][key]["detection_rate"]
                          for key in r["cells"] if key.startswith("S6")},
             "event_far_clean_eval": r["event_far_clean_eval"]["event_far"]}
            for r in metrics["per_seed"]
        ]
    summary = {
        "type": "trial_part_b_severity",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "wall_time_s": round(time.time() - t0, 1),
        "protocol": "severity_sweep_v1 (unchanged finding-18 protocol)",
        "ladder_rung": "L2",
        "claim_noun": "synthetic anomaly",
        "smoke": bool(args.smoke),
        "notes": args.notes,
        "outputs": outputs,
        "recompute_crosscheck_vs_finding18": crosschecks,
        "three_arm_comparison": comparison,
    }
    out = od / "part_b_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[part-b] summary → {out} (wall {time.time() - t0:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
