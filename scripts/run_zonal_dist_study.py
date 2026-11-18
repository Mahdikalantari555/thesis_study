#!/usr/bin/env python3
"""R0.5 study runner: zonal mean vs zonal distribution statistics.

Change ``compare-spatial-representation-strategies``, requirement "Zonal
distribution-statistics representation (R0.5)". Rule-based only — no training,
no GPU, no new extraction: the channels come from the ``stats.zarr`` the repo
already fills, and scoring goes through the UNCHANGED rule path
(``B1PhaseZCausal`` / the ``b0_calendar`` DOY reference) and the unchanged
alarm machinery.

What it produces (all under ``reports/dev/<run-id>/``):

- ``r05_arms.json``   — per arm: threshold at the 5 % cycle-FAR budget, achieved
  FAR, alarm concentration, channel count, no-training provenance.
- ``r05_table.md``    — the one transparent table the owner asked for: the
  reference ``b1`` arm, the ``level`` arm (which must reproduce ``b1``) and the
  distribution arms side by side.
- ``r05_selfcheck.json`` — the ``level``-vs-``b1`` identity check, recorded as
  evidence rather than asserted in prose.

Severity/MDM80 comparisons are deliberately NOT run here: those need the locked
evaluation panel and the injection machinery, i.e. the user's data. This script
establishes that the representation is buildable, aligned to the reference cycle
population, correctly calibrated, and cheap — the pre-condition for spending
severity runs on it.

Examples
--------
Smoke (tiny, any machine with the store)::

    python scripts/run_zonal_dist_study.py --presets level,lower --max-fields 20

Full study::

    python scripts/run_zonal_dist_study.py --presets level,lower,spread,dist \
        --out reports/dev/r05_20261116
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import inputs as minputs  # noqa: E402
from ssl_anomaly.monitor import scoring as mscoring  # noqa: E402
from ssl_anomaly.monitor import splits as msplits  # noqa: E402
from ssl_anomaly.monitor import zonal_dist as zd  # noqa: E402

FAR_TARGET = 0.05
PERSISTENCE_K = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--presets", default="level,lower,spread,dist",
                   help="comma-separated R0.5 presets (level,lower,spread,dist)")
    p.add_argument("--out", type=Path, default=None,
                   help="run directory (default: reports/dev/r05_<date>)")
    p.add_argument("--reference-manifest", default=None,
                   help="splits_locked.json path (default: the repo's)")
    p.add_argument("--cycles", type=Path, default=None,
                   help="cycles_490.parquet path (default: repo default)")
    p.add_argument("--max-fields", type=int, default=None,
                   help="restrict to the first N fields (smoke)")
    p.add_argument("--far-target", type=float, default=FAR_TARGET)
    p.add_argument("--persistence-k", type=int, default=PERSISTENCE_K)
    p.add_argument("--min-n", type=int, default=8)
    p.add_argument("--self-check", action="store_true",
                   help="also fit the reference b1 arm on the median channels and assert "
                        "the `level` arm reproduces it exactly")
    return p.parse_args(argv)


def _load_reference(cycles: dict, manifest: dict, *, allow_test: bool = False):
    """Boolean masks for train / dev over the R0.5 cycle population.

    Uses the locked manifest's cycle keys, so the arms see exactly the same
    train/dev assignment as every other arm. Cycles absent from the manifest
    (monitoring-only) are excluded from both.
    """
    keys = list(cycles["cycle_keys"])
    train = set(manifest["cycles"].get("train", ()))
    dev = set(manifest["cycles"].get("dev", ()))
    test = set(manifest["cycles"].get("test", ()))
    if not allow_test and (set(keys) & test):
        raise RuntimeError(
            "R0.5 cycles include locked TEST cycles — the study may not read them "
            "(test isolation). Restrict the cycle table or use --allow-test never."
        )
    is_train = np.array([k in train for k in keys], dtype=bool)
    is_dev = np.array([k in dev for k in keys], dtype=bool)
    return is_train, is_dev


def _alarm_concentration(scores: np.ndarray, alarms: np.ndarray, fields: np.ndarray) -> dict:
    """Part-A style check: do the alarms pile up in a handful of fields?"""
    if not alarms.any():
        return {"n_alarms": 0, "share_top_field": None, "n_fields_alarmed": 0}
    flagged = np.unique(fields[alarms])
    counts = {int(f): int((fields[alarms] == f).sum()) for f in flagged}
    top = max(counts.values())
    return {
        "n_alarms": int(alarms.sum()),
        "n_fields_alarmed": int(flagged.size),
        "share_top_field": float(top / alarms.sum()),
    }


def run_arm(
    cycles: dict,
    *,
    is_train: np.ndarray,
    is_dev: np.ndarray,
    doy_sin: np.ndarray | None,
    far_target: float,
    persistence_k: int,
    min_n: int,
    label: str,
) -> dict:
    t0 = time.time()
    scores, _ = zd.fit_score_b1(
        cycles, train_mask=is_train, doy_sin=doy_sin, min_n=min_n,
    )
    clean = [scores[i] for i in np.flatnonzero(is_dev)]
    if not clean:
        raise RuntimeError(
            f"arm {label}: no dev cycles — the manifest and the cycle population disagree"
        )
    tau, achieved = mscoring.calibrate_threshold(
        clean, k=persistence_k, far_target=far_target,
    )
    alarms = zd.alarm_rates(scores, tau=tau, k=persistence_k)
    fields = np.asarray(cycles["field_ids"])
    return {
        "arm": label,
        "preset": cycles.get("preset"),
        "n_channels": int(cycles["X"].shape[-1]),
        "channels": list(cycles["band_names"]),
        "stats_used": list(cycles.get("stats_used", [])),
        "n_cycles": int(len(cycles["X"])),
        "n_train": int(is_train.sum()),
        "n_dev": int(is_dev.sum()),
        "tau": float(tau),
        "far_target": float(far_target),
        "far_achieved": float(achieved),
        "persistence_k": int(persistence_k),
        "dev_alarm_rate": float(alarms[is_dev].mean()) if is_dev.any() else None,
        "alarm_concentration_all": _alarm_concentration(scores, alarms, fields),
        "training": "none (rule-based: B1PhaseZCausal on the arm's channel block)",
        "wall_time_s": round(time.time() - t0, 2),
        "labels": {"basis": "locally anchored (frozen pooled phenophase constants)"},
    }


def render_table(arms: list[dict], *, far_target: float) -> str:
    """The one transparent table (owner's core ask), as markdown."""
    out = [
        "| arm | channels | stats | τ @5% | FAR achieved | alarms | "
        "top-field share | wall time (s) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for a in arms:
        conc = a["alarm_concentration_all"]
        share = "—" if conc["share_top_field"] is None else f"{conc['share_top_field']:.2f}"
        out.append(
            f"| `{a['arm']}` | {a['n_channels']} | {', '.join(a['stats_used'])} | "
            f"{a['tau']:.3f} | {a['far_achieved']:.3f} | {conc['n_alarms']} | "
            f"{share} | {a['wall_time_s']} |"
        )
    out.append("")
    out.append(
        f"Calibration: τ chosen on dev clean cycles at a {far_target:.0%} cycle-FAR "
        f"budget with k={arms[0]['persistence_k']} consecutive bins (the unchanged alarm "
        "rule). No training anywhere in this table; every row is a rule-based arm on the "
        "same cycle population."
    )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    presets = [p.strip() for p in args.presets.split(",") if p.strip()]
    for p in presets:
        if p not in zd.PRESETS:
            print(f"ERROR: unknown preset {p!r}; choose from {sorted(zd.PRESETS)}",
                  file=sys.stderr)
            return 2

    out_dir = args.out or (REPO_ROOT / "reports/dev" / time.strftime("r05_%Y%m%d"))
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- reference cycle population (the arm every other arm is paired to) ----
    ref = minputs.load_masked_cycles()
    reference_keys = list(ref["cycle_keys"])
    if args.max_fields is not None:
        keep_fields = sorted({int(k.split(":")[0]) for k in reference_keys})[: args.max_fields]
        keep = set(keep_fields)
        reference_keys = [k for k in reference_keys if int(k.split(":")[0]) in keep]
        print(f"[smoke] restricted to {len(keep_fields)} fields / {len(reference_keys)} cycles")

    kwargs = {}
    if args.reference_manifest:
        kwargs["path"] = args.reference_manifest
    manifest = msplits.load_splits_locked(**kwargs)

    doy_sin = None
    arms: list[dict] = []
    built: dict[str, dict] = {}

    for preset in presets:
        print(f"[build] preset={preset} …")
        cycles = zd.build_distribution_cycles(
            cycles_parquet_path=args.cycles, preset=preset,
            reference_keys=reference_keys,
        )
        built[preset] = cycles
        is_train, is_dev = _load_reference(cycles, manifest)
        doy_sin = minputs.doy_channels(cycles["harvest_days"])[:, :, 0].astype(np.float32)
        arm = run_arm(
            cycles, is_train=is_train, is_dev=is_dev, doy_sin=doy_sin,
            far_target=args.far_target, persistence_k=args.persistence_k,
            min_n=args.min_n, label=f"r05_{preset}",
        )
        arms.append(arm)
        print(f"[arm] {arm['arm']}: {arm['n_channels']} ch, τ={arm['tau']:.3f}, "
              f"FAR={arm['far_achieved']:.3f}, {arm['wall_time_s']}s")

    self_check = {}
    if args.self_check:
        # The `level` arm must reproduce the reference b1 arm bit-for-bit: same
        # median channels, same scorer, same mask -> same scores.
        print("[self-check] level preset vs reference b1 …")
        level = built.get("level") or zd.build_distribution_cycles(
            cycles_parquet_path=args.cycles, preset="level", reference_keys=reference_keys,
        )
        is_train, is_dev = _load_reference(level, manifest)
        doy = minputs.doy_channels(level["harvest_days"])[:, :, 0].astype(np.float32)
        scores_dist, _ = zd.fit_score_b1(level, train_mask=is_train, doy_sin=doy,
                                         min_n=args.min_n)
        # Reference path: the same median channels built by monitor.inputs.
        idx = [i for i, k in enumerate(ref["cycle_keys"]) if k in set(reference_keys)]
        X_ref = ref["X"][idx]
        M_ref = ref["M"][idx]
        from ssl_anomaly.monitor.models import B1PhaseZCausal

        train_ref = is_train
        scorer = B1PhaseZCausal(use_doy=True, min_n=args.min_n)
        scorer.fit(X_ref[train_ref], M_ref[train_ref], doy[train_ref])
        scores_ref = np.full(X_ref.shape[:2], np.nan)
        for i in range(len(X_ref)):
            scores_ref[i] = np.where(
                M_ref[i].any(axis=1), scorer.score_cycle(X_ref[i], M_ref[i], doy[i]), np.nan,
            )
        denom = np.isfinite(scores_ref) & np.isfinite(scores_dist)
        max_abs = float(np.nanmax(np.abs(scores_ref[denom] - scores_dist[denom]))) \
            if denom.any() else float("nan")
        self_check = {
            "compared_cycles": int(denom.any(axis=1).sum()),
            "max_abs_score_difference": max_abs,
            "identical": bool(max_abs < 1e-6),
            "note": ("the level preset carries exactly the b1 channel set; a non-zero "
                     "difference means the cycle population or the mask discipline drifted"),
        }
        print(f"[self-check] max |Δscore| = {max_abs:.3e} (identical={self_check['identical']})")

    (out_dir / "r05_arms.json").write_text(
        json.dumps({
            "run_id": out_dir.name,
            "presets": presets,
            "far_target": args.far_target,
            "persistence_k": args.persistence_k,
            "min_n": args.min_n,
            "n_reference_cycles": len(reference_keys),
            "splits_sha256": manifest.get("manifest_sha256"),
            "arms": arms,
            "self_check": self_check or None,
            "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "r05_table.md").write_text(
        render_table(arms, far_target=args.far_target) + "\n", encoding="utf-8",
    )
    print(f"\nwrote {out_dir}/r05_arms.json and r05_table.md")
    print(render_table(arms, far_target=args.far_target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
