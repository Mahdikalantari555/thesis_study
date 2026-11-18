#!/usr/bin/env python3
"""Build the frozen training-holdout manifest (change training-holdout-invariant).

The manifest is a PURE DERIVATION of the locked splits
(``data/processed/splits_locked.json``): holdout farms = the locked test-block
fields (whole-field, all periods), holdout dates = every acquisition on/after
the locked ``test_period_start``. No new split semantics are introduced.

Frozen with SHA-256; rebuilding requires ``--force --reason <reason>`` (the locked-splits
discipline). The trainer never re-derives it.

Examples
--------
Build once::

    python scripts/build_holdout_manifest.py

Inspect without writing::

    python scripts/build_holdout_manifest.py --dry-run

Rebuild after an authorised split change::

    python scripts/build_holdout_manifest.py --force --reason "split manifest re-frozen after data refresh"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import holdout as mholdout  # noqa: E402
from ssl_anomaly.monitor import splits as msplits  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Derive and freeze the training-holdout manifest from the locked splits.",
    )
    p.add_argument("--out", type=Path, default=mholdout.HOLDOUT_MANIFEST_PATH,
                   help="output path (default: data/processed/holdout_manifest.json)")
    p.add_argument("--splits-path", type=Path, default=None,
                   help="locked splits manifest (default: the repo's splits_locked.json)")
    p.add_argument("--archive-end", default=None,
                   help="last archive acquisition date (ISO). Rows after it are "
                        "future-by-default holdout; omit if unknown rather than guessing")
    p.add_argument("--force", action="store_true",
                   help="overwrite an existing frozen manifest (requires --reason)")
    p.add_argument("--reason", default=None,
                   help="why the frozen manifest is being replaced (recorded inside it)")
    inspection = p.add_mutually_exclusive_group()
    inspection.add_argument("--dry-run", action="store_true",
                            help="print the derived manifest and write nothing")
    inspection.add_argument("--audit-existing", action="store_true",
                            help="compare the frozen manifest at --out with the locked splits, read-only")
    p.add_argument("--skip-cycle-file-check", action="store_true",
                   help="do not hash-verify the cycle files (inspection on a "
                        "machine without the data archive; NEVER for a real freeze)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.skip_cycle_file_check and not (args.dry_run or args.audit_existing):
        print("ERROR: --skip-cycle-file-check is only allowed for read-only inspection",
              file=sys.stderr)
        return 2
    if args.audit_existing and (args.force or args.archive_end):
        print("ERROR: --audit-existing is read-only and accepts no freeze options", file=sys.stderr)
        return 2

    kwargs = {"verify_cycle_files": not args.skip_cycle_file_check}
    if args.splits_path is not None:
        kwargs["path"] = args.splits_path
    try:
        splits_manifest = msplits.load_splits_locked(**kwargs)
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"ERROR: cannot load the locked splits: {exc}", file=sys.stderr)
        return 2

    try:
        if args.audit_existing:
            frozen = mholdout.load_holdout_manifest(path=args.out)
            print(json.dumps(mholdout.audit_frozen_holdout(frozen, splits_manifest), indent=2))
            mholdout.assert_frozen_holdout_matches_splits(frozen, splits_manifest)
            return 0
        manifest = mholdout.build_holdout_manifest(
            splits_manifest, archive_end_date=args.archive_end,
        )
    except (RuntimeError, KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"derived from splits manifest sha256: "
          f"{str(splits_manifest.get('manifest_sha256'))[:16]}…")
    print(f"holdout farms        : {len(manifest['holdout_farms'])}")
    print(f"holdout date_start   : {manifest['holdout_date_start']}")
    print(f"known farms (freeze) : {len(manifest['known_farm_ids'])}")
    print(f"archive_end_date     : {manifest['archive_end_date'] or 'unset (future dates not checked)'}")
    print(f"manifest sha256      : {manifest['manifest_sha256'][:16]}…")

    if args.dry_run:
        print("\n--dry-run: nothing written. Manifest below.\n")
        print(json.dumps(manifest, indent=2))
        return 0

    if args.force and not (args.reason and args.reason.strip()):
        print("ERROR: --force requires a non-empty --reason", file=sys.stderr)
        return 2

    try:
        path = mholdout.save_holdout_manifest(
            manifest, path=args.out, force=args.force, reason=args.reason,
        )
    except FileExistsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
