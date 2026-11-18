"""Register / verify / amend the pre-registered run plan (task 1.1).

The owner runs this BEFORE the first launch. The agent never launches training,
but the plan file — the thing that makes "we always intended these cells" checkable
— is generated, hashed and verified here.

    # write (or rewrite) the plan from the runtime assumptions, then review it
    python scripts/run_plan.py --register --seconds-per-epoch 95 --epochs 60

    # before every launch: confirm the file on disk is still the registered one
    python scripts/run_plan.py --verify

    # a change of mind is an amendment, never an edit
    python scripts/run_plan.py --amend --run-id E3_tcn \\
        --reason "E3 trigger fired (max epoch 412 s)" --approved-by owner
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ssl_anomaly.train import run_plan as RP

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = REPO_ROOT / "reports" / "run_plan.json"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--register", action="store_true", help="write the plan file")
    g.add_argument("--verify", action="store_true", help="check the registered hash")
    g.add_argument("--show", action="store_true", help="print the plan")
    g.add_argument("--amend", action="store_true", help="append a recorded amendment")
    ap.add_argument("--plan", default=str(DEFAULT_PLAN))
    ap.add_argument("--seconds-per-epoch", type=float, default=90.0)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--seconds-per-eval", type=float, default=60.0)
    ap.add_argument("--patch-model", default="patch_cnn_gru")
    ap.add_argument("--include-tcn", action="store_true",
                    help="plan the E3 challenger too (only after the trigger fired)")
    ap.add_argument("--run-id", help="(amend) the cell being changed")
    ap.add_argument("--reason", help="(amend) why")
    ap.add_argument("--approved-by", help="(amend) who approved it")
    args = ap.parse_args(argv)

    path = Path(args.plan)

    if args.register:
        if path.exists():
            try:
                RP.load_plan(path)
            except (ValueError, KeyError):
                pass
            else:
                print(f"[plan] {path} is already registered — use --amend to change it",
                      file=sys.stderr)
                return 2
        plan = RP.build_run_plan(
            seconds_per_epoch=args.seconds_per_epoch, epochs=args.epochs,
            seconds_per_eval=args.seconds_per_eval, patch_model=args.patch_model,
            include_tcn=args.include_tcn,
        )
        RP.save_plan(plan, path)
        print(json.dumps(plan["estimate"], indent=2))
        print(f"[plan] registered {plan['cell_count']} cells -> {path}")
        print(f"[plan] sha256 {plan['sha256']}")
        return 0

    try:
        plan = RP.load_plan(path, verify=args.verify if args.amend or args.verify else True)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[plan] {exc}", file=sys.stderr)
        return 1

    if args.verify:
        print(f"[plan] verified: {plan['cell_count']} cells, sha256 {plan['sha256']}")
        return 0

    if args.show:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    if args.amend:
        if not (args.run_id and args.reason and args.approved_by):
            print("[plan] --amend needs --run-id, --reason and --approved-by",
                  file=sys.stderr)
            return 2
        try:
            new = RP.amendment(plan, run_id=args.run_id, reason=args.reason,
                               approved_by=args.approved_by)
        except ValueError as exc:
            print(f"[plan] {exc}", file=sys.stderr)
            return 2
        RP.save_plan(new, path)
        print(f"[plan] amended; new sha256 {new['sha256']}")
        return 0
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
