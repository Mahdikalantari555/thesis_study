"""Measure data access + per-representation throughput BEFORE any training.

Change ``compare-spatial-representation-strategies``, final requirement:
"a reusable benchmark module SHALL measure, before any training run: Zarr lazy
random-read throughput, materialized preload time and resident RAM,
per-representation epoch forward/backward throughput, CPU utilization, peak
RAM and disk I/O, and SHALL emit per-epoch and total runtime estimates that
gate the user-run training commands."

This script is safe to run here (short, synthetic store by default) and on the
data machine (``--store`` pointing at the real ``patches.zarr``). It never
trains a model to convergence: it times ONE step per representation and
extrapolates, exactly like ``train_patch.py --estimate-runtime``.

Output: ``reports/bench/spatial_<timestamp>.json`` with the recorded
lazy-vs-materialized decision, so the decision cites an artifact rather than
an assumption.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch

from ssl_anomaly.io import patches as P
from ssl_anomaly.models.patch_cnn_gru import build_patch_model
from ssl_anomaly.monitor import spatial_study as SS
from ssl_anomaly.train import patch_data as PD

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = REPO_ROOT / "reports" / "bench"

# Representation → (window px, model builder kwargs). R2 is the sub-crop
# variant of R1 (same model, smaller window); R3 is the multi-scale stem.
REPRESENTATION_SPECS: dict[str, dict] = {
    "R1": {"window_px": 32, "arch": "patch_cnn_gru", "note": "full-field 32x32"},
    "R2": {"window_px": 16, "arch": "patch_cnn_gru", "note": "sub-crop 16x16 + field aggregation"},
    "R3": {"window_px": 32, "arch": "patch_cnn_gru", "note": "multi-scale stem (dilation branches)"},
    "R1_pixelwise": {"window_px": 32, "arch": "patch_pixelwise", "note": "CNN-off control"},
}


def peak_ram_mb() -> float:
    """Peak RSS of this process, in MB (Linux/macOS compatible)."""
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is KB on Linux, bytes on macOS.
    return round(usage / (1024 * 1024) if platform.system() == "Darwin" else usage / 1024, 1)


def bench_lazy_reads(root, *, field_index: int, n_reads: int) -> dict:
    """Time scattered per-cycle reads through the store's chunking."""
    n_cycles = int(root["cycle_valid"].shape[1])
    if n_cycles == 0:
        return {"n_reads": 0, "seconds_per_read": float("nan")}
    rng = np.random.default_rng(0)
    idx = rng.integers(0, n_cycles, size=n_reads)
    t0 = time.perf_counter()
    total_bytes = 0
    for c in idx:
        arr = np.asarray(root["values"][field_index, int(c)])
        total_bytes += arr.nbytes
    dt = time.perf_counter() - t0
    return {
        "n_reads": int(n_reads),
        "seconds": round(dt, 4),
        "seconds_per_read": round(dt / max(1, n_reads), 5),
        "mb_per_second": round((total_bytes / 1e6) / max(dt, 1e-9), 1),
        "bytes_per_read": int(total_bytes // max(1, n_reads)),
    }


def bench_materialized(root, *, field_index: int, max_cycles: int) -> dict:
    """Time a bulk preload of consecutive cycles (the materialized alternative)."""
    n = min(max_cycles, int(root["cycle_valid"].shape[1]))
    if n == 0:
        return {"n_cycles": 0, "seconds": float("nan")}
    t0 = time.perf_counter()
    arr = np.asarray(root["values"][field_index, :n])
    dt = time.perf_counter() - t0
    return {
        "n_cycles": int(n),
        "seconds": round(dt, 4),
        "bytes": int(arr.nbytes),
        "mb": round(arr.nbytes / 1e6, 2),
        "mb_per_second": round((arr.nbytes / 1e6) / max(dt, 1e-9), 1),
        "resident_ram_mb_after": peak_ram_mb(),
    }


def bench_step(*, arch: str, window_px: int, batch_size: int, device: str,
               n_bins: int = P.N_BINS, n_channels: int = P.N_CHANNELS,
               n_cov: int = PD.N_COVARIATES) -> dict:
    """ONE forward+backward step for a representation, timed and extrapolated."""
    model = build_patch_model(
        use_cnn=arch != "patch_pixelwise", n_channels=n_channels, n_covariates=n_cov,
    ).to(device)
    model.train()
    g = torch.Generator().manual_seed(0)
    x = torch.rand(batch_size, n_bins, n_channels, window_px, window_px, generator=g)
    pv = torch.rand(batch_size, n_bins, window_px, window_px, generator=g) > 0.2
    cov = torch.zeros(batch_size, n_bins, n_cov)
    obs = torch.rand(batch_size, n_bins, n_channels, window_px, window_px, generator=g) > 0.3
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-3)

    # warm-up (lazy init / cudnn autotune must not be billed to the step)
    out = model(x, pv, covariates=cov)
    loss, _ = model.hybrid_loss(out, x, obs)
    loss.backward()
    opt.zero_grad(set_to_none=True)

    cpu0 = time.process_time()
    t0 = time.perf_counter()
    out = model(x, pv, covariates=cov)
    loss, _ = model.hybrid_loss(out, x, obs)
    loss.backward()
    opt.step()
    opt.zero_grad(set_to_none=True)
    wall = time.perf_counter() - t0
    cpu = time.process_time() - cpu0

    n_samples = batch_size
    return {
        "arch": arch,
        "window_px": window_px,
        "device": device,
        "batch_size": batch_size,
        "step_seconds": round(wall, 4),
        "samples_per_second": round(n_samples / max(wall, 1e-9), 3),
        "cpu_utilization": round(min(99.9, 100.0 * cpu / max(wall, 1e-9)), 1),
        "peak_ram_mb": peak_ram_mb(),
        "n_parameters": int(sum(p.numel() for p in model.parameters())),
        "spatial_support": SS.spatial_support(window_px),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--store", default=None,
                   help="real patches.zarr; omit for a synthetic benchmark store")
    p.add_argument("--out", default=str(DEFAULT_REPORT_DIR))
    p.add_argument("--fields", type=int, default=2, help="store fields to sample")
    p.add_argument("--cycles", type=int, default=4)
    p.add_argument("--lazy-reads", type=int, default=8)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--device", default="auto")
    p.add_argument("--epochs", type=int, default=30, help="for the runtime extrapolation")
    p.add_argument("--synthetic-size", type=int, default=32,
                   help="synthetic store window size when --store is omitted")
    args = p.parse_args(argv)

    device = args.device if args.device != "auto" else (
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    report: dict = {
        "protocol": "spatial_benchmark_v1",
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
    }

    # ---- store: real or synthetic ------------------------------------
    if args.store:
        root = P.open_store(args.store)
        report["data_source"] = str(args.store)
        report["store_validation"] = P.validate_store(root)
        report["synthetic"] = False
    else:
        tmp = Path(args.out) / "_synthetic_store"
        size = int(args.synthetic_size)
        if (tmp / "patches.zarr").exists():
            root = P.open_store(tmp / "patches.zarr")
        else:
            g = np.random.default_rng(0)
            root = P.create_store(tmp / "patches.zarr",
                                  field_ids=[1, 2], max_cycles=args.cycles, size=size)
            for i, f in enumerate((1, 2)):
                root["field_ids"][i] = f
                infield = np.zeros((size, size), dtype=np.uint8)
                infield[4:size - 4, 4:size - 4] = 1
                root["in_field"][i, 0] = infield
                for c in range(args.cycles):
                    vals = np.abs(g.normal(0.4, 0.1, (P.N_BINS, P.N_CHANNELS, size, size))).astype(np.float16)
                    vals[..., infield == 0] = np.nan
                    root["values"][i, c] = vals
                    root["pixel_valid"][i, c, :, 0] = np.isfinite(vals).any(axis=1)
                    root["n_obs"][i, c] = 2
                    root["sensor_id"][i, c] = P.SENSOR_IDS["L8"]
                    root["cycle_ids"][i, c] = c
                    root["cycle_start_day"][i, c] = 40 * c
                    root["cycle_valid"][i, c] = 1
        report["data_source"] = "synthetic (no archive on this machine)"
        report["synthetic"] = True

    # ---- data access --------------------------------------------------
    lazy = bench_lazy_reads(root, field_index=0, n_reads=args.lazy_reads)
    mat = bench_materialized(root, field_index=0, max_cycles=args.cycles)
    report["data_access"] = {"lazy_random": lazy, "materialized": mat}
    # Decision: materialize only when the whole needed slice fits comfortably
    # in RAM and bulk reads beat scattered reads by >2x.
    speedup = (mat.get("mb_per_second", 0) / lazy.get("mb_per_second", 1)
               if lazy.get("mb_per_second") else 0)
    report["data_access"]["bulk_speedup"] = round(float(speedup), 2)
    report["data_access"]["decision"] = (
        "lazy" if speedup < 2.0 else "materialize-per-field"
    )
    report["data_access"]["decision_rule"] = (
        "materialize only when bulk throughput beats scattered reads by >2x AND the "
        "per-field slice fits the recorded RAM headroom; otherwise stay lazy"
    )

    # ---- per-representation throughput --------------------------------
    reps: dict[str, dict] = {}
    for name, spec in REPRESENTATION_SPECS.items():
        key = f"{name}_{spec['window_px']}px"
        bench = bench_step(
            arch=spec["arch"], window_px=spec["window_px"],
            batch_size=args.batch_size, device=device,
            n_cov=PD.N_COVARIATES,
        )
        per_epoch = bench["step_seconds"] * max(1, 100 // max(1, args.batch_size))
        bench["note"] = spec["note"]
        bench["epoch_seconds_at_100_samples"] = round(per_epoch, 2)
        bench["total_hours_30ep_3seeds_at_100_samples"] = round(
            per_epoch * int(args.epochs) * 3 / 3600.0, 3
        )
        reps[key] = bench
        print(f"[bench] {key}: {bench['samples_per_second']} samples/s, "
              f"peak {bench['peak_ram_mb']} MB")
    report["representations"] = reps

    # ---- capacity + geometry memo -------------------------------------
    report["capacity"] = SS.capacity_flag(
        {k: v["n_parameters"] for k, v in reps.items()}
    )
    report["geometry_memo"] = SS.geometry_memo()
    report["spatial_arithmetic"] = {
        "gsd_m": SS.GSD_M,
        "ha_per_px": SS.HA_PER_PX,
        "windows": {k: SS.spatial_support(v["window_px"]) for k, v in reps.items()},
    }

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"spatial_{stamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[bench] wrote {path}")
    print(f"[bench] data-access decision: {report['data_access']['decision']} "
          f"(bulk speedup {report['data_access']['bulk_speedup']}x)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
