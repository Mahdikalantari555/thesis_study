#!/usr/bin/env python3
"""Pre-flight validator for the development environment (tasks 5b.4, 10.7).

Run before any training/evaluation matrix::

    python scripts/check_dev_env.py

Checks (fail loudly, exit 1):
1. stats.zarr present; cycles parquet + NPZ present.
2. splits_locked.json present; manifest hash valid; cycle-file hashes match.
3. Masked-cycle cache present and consistent with the split cycle keys
   (every non-censored train/dev/test cycle has a tensor row).
4. Observation-mask channels present for every cycle row (mask array with the
   same shape as values) and band order == [ndvi, blue, green, red, nir,
   swir1, swir2, lst].
5. Dev/run artifacts referenced by --run-id (norm stats) when given.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import inputs as minputs  # noqa: E402
from ssl_anomaly.monitor import splits as msplits  # noqa: E402

EXPECTED_BANDS = ["ndvi", "blue", "green", "red", "nir", "swir1", "swir2", "lst"]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-id", default=None, help="also verify a training run's artifacts")
    args = p.parse_args(argv)

    failures: list[str] = []
    oks: list[str] = []

    # 1. Data roots.
    for name, path in [
        ("stats.zarr", minputs.STATS_ZARR_PATH),
        ("cycles parquet", minputs.CYCLES_PARQUET_PATH),
        ("cycles NPZ", minputs.CYCLES_NPZ_PATH),
    ]:
        if Path(path).exists():
            oks.append(f"{name} present")
        else:
            failures.append(f"{name} missing at {path}")

    # 2. Locked splits + hashes.
    try:
        manifest = msplits.load_splits_locked()
        oks.append(
            f"splits_locked.json valid (train {manifest['counts']['train']}, "
            f"dev {manifest['counts']['dev']}, test {manifest['counts']['test']}, "
            f"monitoring {manifest['counts']['monitoring_only']})"
        )
    except RuntimeError as e:
        failures.append(f"locked splits: {e}")
        manifest = None

    # 3. Masked-cycle cache consistency.
    if minputs.MASKED_NPZ_PATH.exists() and manifest is not None:
        data = minputs.load_masked_cycles()
        keys = set(data["cycle_keys"])
        wanted = set()
        for s in ("train", "dev", "test"):
            wanted |= set(manifest["cycles"][s])
        missing = sorted(wanted - keys)
        if missing:
            failures.append(f"{len(missing)} train/dev/test cycles lack tensor rows (e.g. {missing[:3]})")
        else:
            oks.append(f"masked cache covers all {len(wanted)} train/dev/test cycles")
        extra = len(keys - wanted - set(manifest["cycles"]["monitoring_only"]))
        if extra:
            failures.append(f"{extra} cached cycles belong to no split")
        # 4. Mask channels + band order.
        X, M = data["X"], data["M"]
        if M.shape != X.shape or M.dtype != np.bool_:
            failures.append(f"observation mask shape/dtype wrong: {M.shape} {M.dtype}")
        else:
            oks.append(f"observation mask present, coverage {float(M.mean()):.3f}")
        if list(data["band_names"]) != EXPECTED_BANDS:
            failures.append(f"band order drifted: {data['band_names']}")
        else:
            oks.append("band order correct (ndvi + 7 bands)")
        if np.isnan(X[M]).any():
            failures.append("observed entries contain NaN (mask contradiction)")
        no_obs = ~M.any(axis=-1)
        frac = float(no_obs.mean())
        oks.append(f"fully-unobserved bins: {frac:.3f} (excluded via key-padding)")
    elif not minputs.MASKED_NPZ_PATH.exists():
        failures.append(
            f"masked cycle cache missing at {minputs.MASKED_NPZ_PATH} — it builds on first use"
        )

    # 5. Optional run artifacts.
    if args.run_id:
        norm_path = minputs.REPO_ROOT / "reports/dev" / args.run_id / "norm_stats.npz"
        if norm_path.exists():
            oks.append(f"run {args.run_id}: norm stats present")
        else:
            failures.append(f"run {args.run_id}: norm_stats.npz missing at {norm_path}")

    print("check_dev_env:")
    for msg in oks:
        print(f"  OK   {msg}")
    for msg in failures:
        print(f"  FAIL {msg}")
    if failures:
        print(f"\n{len(failures)} check(s) failed")
        return 1
    print(f"\nAll {len(oks)} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
