#!/usr/bin/env python3
"""Freeze patch median/IQR statistics using verified locked train cycles only."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tqdm import tqdm

from ssl_anomaly.io import patches as P
from ssl_anomaly.monitor import holdout as H
from ssl_anomaly.monitor import splits as S


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--splits", type=Path, default=S.SPLITS_LOCKED_PATH)
    parser.add_argument("--holdout-manifest", type=Path, default=H.HOLDOUT_MANIFEST_PATH)
    parser.add_argument(
        "--out", type=Path, help="new sidecar (default: norm_stats.json beside the store)"
    )
    args = parser.parse_args(argv)
    out = args.out or args.store.parent / P.NORM_STATS_NAME
    try:
        if out.exists():
            raise FileExistsError(
                f"normalization sidecar already exists at {out}; choose a new --out"
            )
        splits = S.load_splits_locked(path=args.splits, verify_cycle_files=False)
        holdout = H.load_holdout_manifest(path=args.holdout_manifest)
        norm = P.build_patch_norm(
            root=P.open_store(args.store),
            splits_manifest=splits,
            holdout_manifest=holdout,
            progress=lambda cycles: tqdm(
                cycles, desc="Fit train-only patch normalization", unit="cycle"
            ),
        )
        P.save_patch_norm(norm, out)
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print(f"Patch normalization aborted: {exc}", file=sys.stderr)
        return 2
    print(
        f"Wrote {out}: {norm['n_train_cycles']} locked train cycles, "
        f"SHA-256 {P.norm_stats_sha256(norm)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
