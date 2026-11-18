#!/usr/bin/env python3
"""3-seed × 3-model development matrix (task 5b.3), resume-aware and smoke-gated.

Runs ``scripts/train_main.py`` then ``scripts/eval_dev.py`` for every
(model, seed) combination, skipping completed steps (checkpoint + metrics
already present), so re-invoking continues where the last run stopped::

    python scripts/run_dev_matrix.py                 # full matrix
    python scripts/run_dev_matrix.py --smoke         # agent smoke pass
    python scripts/run_dev_matrix.py --models gru_ae --seeds 42
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

MODELS = ("masked_transformer", "gru_ae", "b1")
SEEDS = (13, 42, 2026)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--models", default=",".join(MODELS))
    p.add_argument("--seeds", default=",".join(str(s) for s in SEEDS))
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--skip-eval", action="store_true", help="train only")
    p.add_argument("--rounds", type=int, default=10, help="injection rounds for eval_dev")
    args = p.parse_args(argv)

    models = [m for m in args.models.split(",") if m]
    seeds = [int(s) for s in args.seeds.split(",") if s]
    date = time.strftime("%Y%m%d")

    failures: list[str] = []
    for model in models:
        run_id = f"{model}_{date}" + ("_smoke" if args.smoke else "")
        # --- Train every seed (skip completed checkpoints) ---
        train_failed = False
        for seed in seeds:
            ckpt_dir = REPO_ROOT / "checkpoints/dev" / run_id
            suffix = "npz" if model == "b1" else "pt"
            stem = "b1_phasez_causal" if model == "b1" else model
            ckpt = ckpt_dir / f"{stem}_seed{seed}.{suffix}"
            cmd = [PY, "-X", "utf8", str(REPO_ROOT / "scripts/train_main.py"),
                   "--model", model, "--seed", str(seed), "--run-id", run_id]
            if args.smoke:
                cmd.append("--smoke")
            if ckpt.exists():
                print(f"[skip-train] {ckpt.name} exists ({run_id})")
                continue
            print(f"[train] {' '.join(str(c) for c in cmd)}", flush=True)
            r = subprocess.run(cmd, cwd=REPO_ROOT)
            if r.returncode != 0:
                failures.append(f"train {model} seed {seed} exit {r.returncode}")
                train_failed = True
                break

        if args.skip_eval or train_failed:
            continue

        # --- One eval over all seeds (one metrics.json + one dev_log row) ---
        metrics_name = f"metrics_{model}" + ("_smoke" if args.smoke else "")
        metrics_path = REPO_ROOT / "reports/dev" / run_id / f"{metrics_name}.json"
        if metrics_path.exists():
            try:
                have = set(json.loads(metrics_path.read_text(encoding="utf-8"))["seeds"])
                if set(seeds) <= have:
                    print(f"[skip-eval] {metrics_path.name} covers seeds {sorted(seeds)}")
                    continue
            except Exception:
                pass  # re-evaluate on unreadable metrics
        eval_cmd = [PY, "-X", "utf8", str(REPO_ROOT / "scripts/eval_dev.py"),
                    "--run-id", run_id, "--model", model,
                    "--seeds", ",".join(str(s) for s in seeds), "--rounds", str(args.rounds)]
        if args.smoke:
            eval_cmd.append("--smoke")
        print(f"[eval] {' '.join(str(c) for c in eval_cmd)}", flush=True)
        r = subprocess.run(eval_cmd, cwd=REPO_ROOT)
        if r.returncode != 0:
            failures.append(f"eval {model} exit {r.returncode}")

    if failures:
        print(f"\nMATRIX FAILURES ({len(failures)}):")
        for f in failures:
            print(f"  {f}")
        return 1
    print("\nMatrix complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
