#!/usr/bin/env python3
"""Run the read-only, acquisition-level decomposition awareness study."""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from threadpoolctl import threadpool_limits  # noqa: E402

from ssl_anomaly.decomposition_study import decompose as dec  # noqa: E402
from ssl_anomaly.decomposition_study.data import BRANCHES, read_zonal, smoke_panel, split_panel  # noqa: E402
from ssl_anomaly.decomposition_study.experiment import (  # noqa: E402
    SEEDS,
    Run,
    benchmark,
    compare_protocols,
    json_save,
    study_case,
)
from ssl_anomaly.monitor.holdout import HOLDOUT_MANIFEST_PATH  # noqa: E402
from ssl_anomaly.monitor.splits import SPLITS_LOCKED_PATH  # noqa: E402

DEFAULT_STATS = REPO.parent / "Data/Processed/satellite/stats.zarr"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("benchmark", "scores", "ablation", "all"),
        help="benchmark (default real), scores (no SSL), ablation, or all (default smoke)",
    )
    parser.add_argument(
        "--stats-zarr", type=Path, help=f"canonical zonal store (default: {DEFAULT_STATS})"
    )
    parser.add_argument(
        "--holdout-manifest", type=Path, help="existing hash-verified frozen holdout"
    )
    parser.add_argument("--splits-path", type=Path, help="locked splits referenced by the freeze")
    parser.add_argument("--train-before", help="exclusive training end (default: 2021-01-01)")
    parser.add_argument("--evaluate-from", help="inclusive evaluation start (default: 2022-01-01)")
    parser.add_argument("--min-valid-frac", type=float, default=0.50)
    parser.add_argument(
        "--method",
        choices=dec.METHODS,
        default="harmonic",
        help="decomposition method used by ablation/standalone scoring",
    )
    parser.add_argument("--protocol", choices=("both", *dec.PROTOCOLS), default="both")
    parser.add_argument(
        "--epochs", type=int, help="fixed budget for every arm (default: 12, smoke: 1)"
    )
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--indicators", type=Path, help="optional observed TVDI/CWSI/ETa table")
    parser.add_argument("--adjacency", type=Path, help="optional polygon-derived field pairs")
    parser.add_argument(
        "--out", type=Path, help="dedicated output directory (never the main pipeline)"
    )
    parser.add_argument(
        "--smoke", action="store_true", help="use a small, explicitly simulated fixture"
    )
    parser.add_argument("--resume", action="store_true", help="resume the identical run in --out")
    parser.add_argument(
        "--quiet", action="store_true", help="suppress progress bars, not the JSONL log"
    )
    args = parser.parse_args(argv)
    if args.smoke and any(
        (args.stats_zarr, args.holdout_manifest, args.splits_path, args.indicators, args.adjacency)
    ):
        parser.error("--smoke does not accept real archive, manifest or evidence arguments")
    if not 1 <= args.threads <= 8 or (args.epochs is not None and not 1 <= args.epochs <= 50):
        parser.error("threads must be 1-8 and epochs must be 1-50")
    return args


def run(args: argparse.Namespace) -> Run:
    stage = args.stage or ("all" if args.smoke else "benchmark")
    # Read and admit the intended source before creating output or loading a model.
    if args.smoke:
        panel = smoke_panel()
        train, evaluate = "2017-01-01", "2018-01-01"
    else:
        panel = read_zonal(
            args.stats_zarr or DEFAULT_STATS,
            args.holdout_manifest or HOLDOUT_MANIFEST_PATH,
            args.min_valid_frac,
            splits_path=args.splits_path or SPLITS_LOCKED_PATH,
        )
        train, evaluate = "2021-01-01", "2022-01-01"
    split = split_panel(panel, args.train_before or train, args.evaluate_from or evaluate)
    out = args.out or REPO / "data/studies/decomposition_aware_ssl" / (
        f"{'smoke_' if args.smoke else ''}{stage}"
    )
    neural = stage in ("ablation", "all")
    settings = {
        "stage": stage,
        "method": args.method,
        "protocols": dec.PROTOCOLS if args.protocol == "both" else (args.protocol,),
        "seeds": SEEDS if neural else (),
        "device": "cpu",
        "threads": args.threads,
        "epochs": (args.epochs or (1 if args.smoke else 12)) if neural else 0,
        "optional_evidence": {
            name: {
                "path": str(path.resolve()),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for name, path in (("indicators", args.indicators), ("adjacency", args.adjacency))
            if path is not None
        },
    }
    if neural:
        import torch

        from ssl_anomaly.decomposition_study import ssl

        if args.device == "cuda" and not torch.cuda.is_available():
            raise ValueError("--device cuda requested but CUDA is unavailable")
        if args.device == "cuda" or (
            args.device == "auto" and not args.smoke and torch.cuda.is_available()
        ):
            settings["device"] = "cuda"
        torch.set_num_threads(args.threads)
        settings.update(
            torch_version=str(torch.__version__),
            optimizer={
                "name": "AdamW",
                "lr": ssl.LR,
                "batch_fields": ssl.BATCH,
                "block_acquisitions": ssl.BLOCK,
                "context_drop_probability": ssl.CONTEXT_DROP,
                "warmup_acquisitions": ssl.WARMUP,
                "hidden_size": ssl.HIDDEN,
            },
        )
    job = Run(out, panel, split, settings, resume=args.resume, quiet=args.quiet)
    job.record(
        event="start", stage=stage, resume=args.resume, data_source=panel.provenance["data_source"]
    )
    protocols = settings["protocols"]
    methods = dec.METHODS if stage in ("benchmark", "all") else (args.method,)
    series = benchmark(job, methods, protocols)
    summaries = {}
    for branch in BRANCHES if stage != "benchmark" else ():
        for protocol in protocols:
            case = study_case(
                job,
                branch,
                protocol,
                series[branch, protocol],
                args.indicators,
                args.adjacency,
            )
            summaries[f"{branch}/{protocol}"] = {
                "report": f"{branch}_{protocol}/summary.json",
                "multi_branch_gate": case["multi_branch_gate"],
                "model_runs": len(case["models"]),
                "synthetic_scenarios": len(case["synthetic_sensitivity"]),
            }
    pair_report = stage != "benchmark" and args.protocol == "both"
    if pair_report:
        compare_protocols(job, series)
    total = time.perf_counter() - job.start
    json_save(
        job.out / "summary.json",
        {
            "provenance": job.provenance,
            "benchmark": "benchmark.json",
            "cases": summaries,
            "protocol_comparison": "protocol_comparison.json" if pair_report else None,
            "invocation_wall_seconds": total,
            "stress_ground_truth": "absent",
            "stage": stage,
        },
    )
    job.record(event="finished", wall_seconds=total)
    print(
        f"[{panel.provenance['data_source']}] {stage}: {len(panel.fields)} fields x {len(panel.dates)} "
        f"acquisitions; {len(summaries)} study cases; {total:.1f} s; {job.out / 'summary.json'}"
    )
    return job


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        with threadpool_limits(limits=args.threads):
            run(args)
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(f"Study aborted: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
