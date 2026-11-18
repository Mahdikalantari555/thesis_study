"""Estimate L8/L9 band offsets from the patch store (task 2.5).

Owner-run: it reads the real store. It writes a JSON table that
``scripts/train_patch.py``/scoring can apply, plus the pre-registered
applied-vs-not comparison plan.

    python scripts/sensor_offset.py --store Data/Processed/patches/patches.zarr \\
        --out reports/sensor_offset.json

Refusals, on purpose:

* fewer than ``--min-pairs`` usable pairs per band -> the band is reported
  UNRESOLVED and the script still exits 0 (a null result is a result);
* ``--require-resolved`` turns that into a non-zero exit for a pipeline that
  must not proceed on an un-calibrated offset;
* the offsets are NOT applied here — application is a flag on the scoring path
  (``sensor_offset_applied`` in the run manifest), so the two arms of the
  comparison share one checkpoint and one scorer.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ssl_anomaly.io import patches as P
from ssl_anomaly.io import sensor_offset as SO

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_cycles(root) -> tuple[list[SO.CycleRef], dict]:
    """Cycle references with day + sensor, from the store's own arrays.

    ``sensor_id`` in the store is PER BIN, not per cycle: a cycle spans up to
    540 days and can be crossed by the L8/L9 cutover, so a cycle can genuinely
    contain bins from both sensors. Such a cycle is NOT a usable pair member —
    the difference it contributes is part cycle, part sensor change — so it is
    skipped and counted. The second return value is that accounting.
    """
    field_ids = np.asarray(root["field_ids"][:], dtype=np.int64)
    start = np.asarray(root["cycle_start_day"][:], dtype=np.int64)
    sensor = np.asarray(root["sensor_id"][:], dtype=np.int64)     # (F, C, BINS)
    valid = np.asarray(root["cycle_valid"][:], dtype=np.uint8)
    n_obs = np.asarray(root["n_obs"][:])                          # (F, C, BINS)
    names = {v: k for k, v in P.SENSOR_IDS.items()}
    out: list[SO.CycleRef] = []
    mixed = unknown = empty = 0
    for i, fid in enumerate(field_ids):
        for j in range(start.shape[1]):
            if not valid[i, j]:
                continue
            seen = sensor[i, j][n_obs[i, j] > 0]
            if seen.size == 0:
                empty += 1
                continue
            ids = sorted({int(s) for s in np.unique(seen)})
            if len(ids) > 1:
                mixed += 1
                continue
            s = names.get(ids[0], "unknown")
            if s not in ("L8", "L9"):
                unknown += 1
                continue
            out.append(SO.CycleRef(field_id=int(fid), cycle_id=int(j),
                                   day=int(start[i, j]), sensor=s))
    stats = {"n_cycles_labelled": len(out), "n_mixed_sensor_cycles": mixed,
             "n_unknown_sensor_cycles": unknown, "n_empty_cycles": empty,
             "note": "a cycle whose observed bins span both sensors cannot be a pair member"}
    return out, stats


def make_sampler(root):
    field_ids = [int(f) for f in np.asarray(root["field_ids"][:], dtype=np.int64)]
    index = {fid: i for i, fid in enumerate(field_ids)}

    def sample(ref: SO.CycleRef):
        i = index.get(ref.field_id)
        if i is None or ref.cycle_id >= root["values"].shape[1]:
            return None, None
        # values: (field, cycle, bin, channel, S, S) -> pool over bins
        v = np.asarray(root["values"][i, ref.cycle_id, :, :, :, :], dtype=np.float64)
        pv = np.asarray(root["pixel_valid"][i, ref.cycle_id, :, :, :, :])
        inf = np.asarray(root["in_field"][i, 0])          # (1, S, S) -> (S, S)
        if v.size == 0:
            return None, None
        # pv is (BINS, 1, S, S): observed if ANY bin saw the pixel. A pixel
        # seen in no bin cannot contribute a mean for this cycle.
        obs = np.asarray(pv, dtype=bool).reshape(pv.shape[0], pv.shape[-2], pv.shape[-1]).any(axis=0)
        mask = obs & (inf > 0)
        if not mask.any():
            return None, None
        vals = np.nanmean(v, axis=0)                       # (channel, S, S)
        return vals, mask

    return sample


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--store", required=True)
    ap.add_argument("--out", default=str(REPO_ROOT / "reports" / "sensor_offset.json"))
    ap.add_argument("--bands", default=",".join(P.CHANNELS))
    ap.add_argument("--min-pairs", type=int, default=SO.MIN_PAIRS)
    ap.add_argument("--max-gap-days", type=int, default=SO.MAX_GAP_DAYS)
    ap.add_argument("--require-resolved", action="store_true",
                    help="exit non-zero if any band's offset is unresolved")
    ap.add_argument("--dry-run", action="store_true", help="find pairs only, write nothing")
    args = ap.parse_args(argv)

    root = P.open_store(args.store, mode="r")
    cycles, cycle_stats = load_cycles(root)
    pairs = SO.find_pairs(cycles, max_gap_days=args.max_gap_days)
    print(f"[offset] {len(cycles)} single-sensor cycles -> {len(pairs)} near-coincident pairs")
    if cycle_stats["n_mixed_sensor_cycles"]:
        print(f"[offset] skipped {cycle_stats['n_mixed_sensor_cycles']} mixed-sensor cycles")
    if args.dry_run:
        return 0
    if not pairs:
        print("[offset] no pairs within the gap window — nothing to estimate",
              file=sys.stderr)
        return 1

    bands = tuple(b.strip() for b in args.bands.split(",") if b.strip())
    table = SO.estimate_offsets(pairs, make_sampler(root), bands=bands,
                                min_pairs=args.min_pairs,
                                channel_names=tuple(P.CHANNELS))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "protocol": "sensor_offset_v1",
        "store": str(args.store),
        "max_gap_days": int(args.max_gap_days),
        "cycle_accounting": cycle_stats,
        **table,
        "comparison": SO.comparison_plan(
            n_l8_cycles=sum(1 for c in cycles if c.sensor == "L8"),
            n_l9_cycles=sum(1 for c in cycles if c.sensor == "L9"),
        ),
    }
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(dict(table["bands"].items()), indent=2))
    print(f"[offset] {table['resolved_count']}/{len(table['bands'])} bands resolved -> {out}")

    if args.require_resolved and table["resolved_count"] < len(table["bands"]):
        unresolved = [b for b, v in table["bands"].items() if not v["resolved"]]
        print(f"[offset] refusing: unresolved bands {unresolved}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
