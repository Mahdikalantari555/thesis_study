#!/usr/bin/env python3
"""Build data/processed/splits_locked.json once (design D2, task 1.1/1.2).

Run exactly once before any training; the manifest is never regenerated inside
the change. Logs split sizes and the cycles dropped by the temporal cutoff
(task 1.4 checkpoint: >15 % of uncensored cycles dropped must be raised).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor.splits import (  # noqa: E402
    SPLITS_LOCKED_PATH,
    build_splits_locked,
)


def main() -> int:
    import argparse

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--force", default=None,
                   help="rebuild an existing manifest; value is recorded as the rebuild reason")
    args = p.parse_args()

    if SPLITS_LOCKED_PATH.exists() and not args.force:
        print(f"REFUSING: {SPLITS_LOCKED_PATH} already exists (built once, never regenerated). "
              "Use --force <reason> for a protocol-corrected rebuild (the old file is kept as "
              "splits_locked_superseded_<sha>.json).")
        return 1

    manifest = build_splits_locked()
    n_uncensored = sum(
        manifest["counts"][s] for s in ("train", "dev", "test")
    )
    dropped = manifest["n_dropped_train_cutoff"] + manifest["n_dropped_dev_cutoff"]
    drop_frac = dropped / max(1, n_uncensored + dropped)

    if args.force:
        import shutil
        old = json.loads(SPLITS_LOCKED_PATH.read_text(encoding="utf-8"))
        old_sha = old.get("manifest_sha256", "unknown")[:12]
        superseded = SPLITS_LOCKED_PATH.parent / f"splits_locked_superseded_{old_sha}.json"
        shutil.copyfile(SPLITS_LOCKED_PATH, superseded)
        print(f"Superseded manifest archived: {superseded}")
        manifest["rebuild_of"] = {
            "superseded_manifest_sha256_prefix": old_sha,
            "reason": args.force,
            "note": "downstream artifacts trained on the superseded manifest are invalid "
                    "and were re-run (models, evaluations, freeze, final test)",
        }
        # Re-hash after adding rebuild_of.
        manifest.pop("manifest_sha256", None)
        manifest["manifest_sha256"] = __import__(
            "ssl_anomaly.monitor.splits", fromlist=["manifest_hash"]
        ).manifest_hash(manifest)

    SPLITS_LOCKED_PATH.parent.mkdir(parents=True, exist_ok=True)
    SPLITS_LOCKED_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote {SPLITS_LOCKED_PATH}")
    print(f"manifest_sha256: {manifest['manifest_sha256'][:16]}…")
    print(f"git_sha: {manifest['git_sha']}")
    print(f"kmeans: seed={manifest['kmeans']['seed']}, k={manifest['kmeans']['n_blocks']}, "
          f"test_block={manifest['kmeans']['test_block']} "
          f"({manifest['kmeans']['block_sizes'][str(manifest['kmeans']['test_block'])]} fields), "
          f"dev_block={manifest['kmeans']['dev_block']} "
          f"({manifest['kmeans']['block_sizes'][str(manifest['kmeans']['dev_block'])]} fields)")
    for name in ("train", "dev", "test", "monitoring_only"):
        n_fields = len(manifest[f"{name}_fields"])
        print(f"  {name:16s}: {manifest['counts'][name]:5d} cycles / {n_fields} fields")
    print(f"Temporal-cutoff drops: train {manifest['n_dropped_train_cutoff']}, "
          f"dev {manifest['n_dropped_dev_cutoff']} "
          f"({100 * drop_frac:.1f}% of uncensored non-block cycles)")

    if drop_frac > 0.15:
        print(
            "WARNING (task 1.4 checkpoint): the temporal cutoff drops more than 15 % of "
            "uncensored non-block cycles — this must be raised with the user."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
