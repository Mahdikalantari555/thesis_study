"""Cycle audit per design D2 (openspec/changes/data-and-phenology-readiness/design.md).

Stratified sample of 60 cycles (recorded seed), per-cycle PNG plot, flags:
  length < 240 or > 480 d, no clear NDVI drop, < 6 valid obs,
  overlap with the field's own neighbouring cycle, peak NDVI < 0.4.

NDVI is computed from red + nir bands (stats_long has no 'ndvi' band).

Fixes (2026-11-14):
  - `overlap_with_neighbour` previously compared a cycle against cycles of
    OTHER fields in the same block. Staggered harvest across fields makes
    calendar overlap normal, which produced the meaningless 96.7 % flag rate
    (and a void "BLOCKING" verdict). Per design D2 ("overlap with the
    neighbouring cycle", split/merged error class) the flag now checks the
    SAME field's cycles only. Given `segment_cycles` tiles cycles between
    consecutive harvests, a non-zero count would mean a segmentation
    regression; 0 is the expected, clean result.
  - Sampling now covers the full non-censored population (no 240-cycle scan
    cap) and stratifies by start year x cycle-length tercile x field block,
    per D2. Every cycle with a sanity flag is added to the reviewed set.
  - Plots are rendered with PIL (matplotlib `savefig` segfaults with
    0xC0000005 in this environment): NDVI + LST(deg C) + valid_frac with the
    cycle's harvest dates marked.

Outputs reports/cycle_audit/audit.csv, per-cycle PNG plots, summary JSON.

Usage:
  python scripts/audit_cycles.py --smoke   # agent smoke test (fast, ~10 cycles)
  python scripts/audit_cycles.py --all     # full audit: 60 stratified + flagged (user run)
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(r"D:\RS\Thesis\thesis_implementation")
SRC_ROOT = REPO_ROOT / "src"
DATA_ROOT = Path(r"D:\RS\Thesis\Data\Processed")
REPORTS = REPO_ROOT / "reports" / "cycle_audit"
PLOTS = REPORTS / "plots"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from ssl_anomaly.phenology.cycles import segment_cycles  # noqa: E402
    _HAS_SEG = True
except Exception:  # pragma: no cover - import environment dependent
    _HAS_SEG = False

SEED = 20261111
N_CYCLES = 60
N_SMOKE = 10
MAX_SCAN_FIELDS_SMOKE = 60   # scan up to 60 fields to find ones with NDVI data
MAX_SCAN_FIELDS_ALL = None   # scan all fields (full population, per D2)

LEN_MIN, LEN_MAX = 240, 480  # sanity-flag length bounds (days)
DROP_MIN = 0.10              # min (max-min) NDVI over the cycle
NVALID_MIN = 6               # min valid observations per cycle
PEAK_MIN = 0.40              # min peak NDVI


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except Exception:
        return "unknown"


def load_tables():
    farms = pd.read_parquet(DATA_ROOT / "coordinates" / "farms.parquet")
    stats_long = pd.read_parquet(DATA_ROOT / "satellite" / "stats_long.parquet")
    stats_long["date"] = pd.to_datetime(stats_long["date"])
    return farms, stats_long


def field_frames(stats_long: pd.DataFrame) -> dict:
    """One sorted sub-frame per field, computed once (repeated filtering is too slow)."""
    return {int(fid): f.sort_values("date") for fid, f in stats_long.groupby("field_id")}


def get_field_obs(sf: pd.DataFrame) -> pd.DataFrame | None:
    """Per-date observation frame for one field: ndvi (from red+nir), lst degC, valid_frac."""
    if sf is None or sf.empty:
        return None
    red = sf[sf["band"] == "red"][["date", "median"]].rename(columns={"median": "red"})
    nir = sf[sf["band"] == "nir"][["date", "median"]].rename(columns={"median": "nir"})
    if red.empty or nir.empty:
        return None
    m = pd.merge(red, nir, on="date", how="inner")
    if len(m) < 30:
        return None
    r = m["red"].to_numpy(dtype="float64")
    n = m["nir"].to_numpy(dtype="float64")
    denom = n + r
    ndvi = np.full(len(m), np.nan)
    good = np.abs(denom) > 1e-9
    ndvi[good] = (n[good] - r[good]) / denom[good]
    m["ndvi"] = ndvi
    lst = sf[sf["band"] == "lst"][["date", "mean"]].rename(columns={"mean": "lst"})
    vf = sf[["date", "valid_frac"]].drop_duplicates("date")
    m = m.merge(lst, on="date", how="left").merge(vf, on="date", how="left")
    m["lst_c"] = m["lst"] - 273.15
    m = m[np.isfinite(m["ndvi"])].reset_index(drop=True)
    if len(m) < 30:
        return None
    return m[["date", "ndvi", "lst_c", "valid_frac"]]


def collect_cycles(obs_by_field: dict, field_block: dict, max_scan: int | None = None):
    """Segment every scanned field; returns (non-censored cycles, skipped counts).

    obs_by_field maps field_id -> processed per-date frame (ndvi, lst_c, valid_frac);
    fields missing from it were skipped by get_field_obs."""
    if not _HAS_SEG:
        raise RuntimeError("segmentation import unavailable (ssl_anomaly.phenology.cycles)")
    epoch = pd.Timestamp("1970-01-01")
    field_ids = sorted(obs_by_field.keys())
    max_scan = max_scan if max_scan is not None else len(field_ids)
    cycles: list[dict] = []
    scanned = errors = 0
    for fid in field_ids:
        if scanned >= max_scan:
            break
        scanned += 1
        obs = obs_by_field[fid]
        days = (obs["date"] - epoch).dt.days.values.astype("int64")
        try:
            for c in segment_cycles(fid, days, obs["ndvi"].to_numpy(dtype="float64")):
                if c.censored:
                    continue
                cycles.append({
                    "field": fid,
                    "cycle_id": int(c.cycle_id),
                    "t_start": int(c.t_start),
                    "t_end": int(c.t_end),
                    "length_days": int(c.length_days),
                    "kind": c.kind,
                    "ratoon_no": int(c.ratoon_no),
                    "start_harvest": int(c.start_harvest),
                    "end_harvest": int(c.end_harvest),
                    "s_date": epoch + pd.Timedelta(days=int(c.start_harvest)),
                    "e_date": epoch + pd.Timedelta(days=int(c.end_harvest)),
                    "year": int((epoch + pd.Timedelta(days=int(c.start_harvest))).year),
                    "block": field_block.get(fid),
                })
        except Exception:
            errors += 1
            continue
        if scanned % 25 == 0:
            print(f"  scanned {scanned} fields, collected {len(cycles)} cycles so far")
    skipped = {"fields_scanned": scanned, "fields_errors": errors}
    return cycles, skipped


def add_profile(c: dict, obs: pd.DataFrame) -> None:
    """Attach NDVI profile stats for flag computation."""
    epoch = pd.Timestamp("1970-01-01")
    days = (obs["date"] - epoch).dt.days.values
    pmask = (days >= c["start_harvest"]) & (days < c["end_harvest"])
    prof = obs["ndvi"].to_numpy()[pmask]
    c["n_obs_in_cycle"] = int(pmask.sum())
    if prof.size == 0:
        return
    c["ndvi_drop"] = float(np.nanmax(prof) - np.nanmin(prof))
    c["n_valid"] = int(np.isfinite(prof).sum())
    c["ndvi_max"] = float(np.nanmax(prof))
    c["ndvi_mean"] = float(np.nanmean(prof))


def compute_flags(cycles: list[dict]) -> dict:
    """Sanity flags per design D2. Overlap is checked against the SAME field's
    neighbouring cycles only (split/merged-cycle error class)."""
    by_field: dict[int, list[dict]] = {}
    for c in cycles:
        by_field.setdefault(c["field"], []).append(c)
    flags: dict[tuple, list[str]] = {}
    for fid, clist in by_field.items():
        clist_sorted = sorted(clist, key=lambda c: c["t_start"])
        for c in clist_sorted:
            fl = []
            if c["length_days"] < LEN_MIN or c["length_days"] > LEN_MAX:
                fl.append("length_out_of_range")
            if c.get("ndvi_drop") is not None and c["ndvi_drop"] < DROP_MIN:
                fl.append("no_clear_ndvi_drop")
            if c.get("n_valid") is not None and c["n_valid"] < NVALID_MIN:
                fl.append("few_valid_obs")
            if c.get("ndvi_max") is not None and c["ndvi_max"] < PEAK_MIN:
                fl.append("peak_ndvi_low")
            # Same-field neighbouring-cycle overlap. segment_cycles tiles cycles
            # between consecutive harvests, so >0 here means a segmentation
            # regression (this replaces the cross-field check that produced the
            # invalid 96.7 % rate).
            for o in clist_sorted:
                if o is c:
                    continue
                if c["t_start"] < o["t_end"] and o["t_start"] < c["t_end"]:
                    fl.append("overlap_with_neighbour")
                    break
            flags[(c["field"], c["cycle_id"])] = fl
    return flags


def stratified_sample(cycles: list[dict], n_target: int, rng: np.random.RandomState):
    """Proportional allocation over strata (start year, length tercile, block)."""
    if not cycles:
        return []
    lens = np.array([c["length_days"] for c in cycles], dtype=float)
    q1, q2 = np.quantile(lens, [1 / 3, 2 / 3])
    strata: dict[tuple, list[dict]] = {}
    for c in cycles:
        ter = 0 if c["length_days"] <= q1 else (1 if c["length_days"] <= q2 else 2)
        strata.setdefault((c["year"], ter, c["block"]), []).append(c)
    chosen: list[dict] = []
    for key in sorted(strata, key=lambda k: str(k)):
        clist = strata[key]
        n = max(1, int(round(n_target * len(clist) / len(cycles))))
        idx = rng.choice(len(clist), size=min(n, len(clist)), replace=False)
        chosen.extend(clist[int(i)] for i in idx)
    if len(chosen) > n_target:
        keep = set(rng.choice(len(chosen), size=n_target, replace=False).tolist())
        chosen = [c for i, c in enumerate(chosen) if i in keep]
    return chosen


def _font(size: int):
    for name in ("arial.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
        except Exception:
            continue
    return ImageFont.load_default(size=size)


def plot_cycle_png(c: dict, obs: pd.DataFrame, flags: list[str], out_path: Path) -> None:
    """NDVI + LST(deg C) + valid_frac with the cycle's harvest dates marked (PIL)."""
    span = obs[(obs["date"] >= c["s_date"]) & (obs["date"] < c["e_date"])]
    if span.empty:
        span = obs.iloc[0:0]
    W, H = 1000, 560
    L, R, T, B, GAP = 78, 20, 56, 34, 14
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    f_title, f_lab, f_tick = _font(16), _font(13), _font(11)

    title = (f"field {c['field']} cycle {c['cycle_id']} | block {c['block']} | "
             f"{c['kind']} ratoon {c['ratoon_no']} | len {c['length_days']} d | "
             f"{c['s_date'].date()} -> {c['e_date'].date()}")
    d.text((L, 10), title, fill="black", font=f_title)
    d.text((L, 32), "flags: " + (";".join(flags) if flags else "(none)"), fill=(150, 30, 30), font=f_lab)

    x0, x1 = L, W - R
    dmin, dmax = c["s_date"], c["e_date"]
    span_days = max((dmax - dmin).days, 1)

    def xd(dt):
        return x0 + (dt - dmin).days / span_days * (x1 - x0)

    ph = (H - T - B - 2 * GAP) / 3
    panels = [
        ("NDVI", span["ndvi"], (0.0, 1.0), (30, 90, 200)),
        ("LST (C)", span["lst_c"], (0.0, 60.0), (200, 60, 30)),
        ("valid_frac", span["valid_frac"], (0.0, 1.0), (90, 140, 90)),
    ]
    for pi, (label, series, (vlo, vhi), color) in enumerate(panels):
        top = T + pi * (ph + GAP)
        bot = top + ph
        d.rectangle([x0, top, x1, bot], outline=(190, 190, 190))
        d.text((6, top + ph / 2 - 8), label, fill="black", font=f_lab)
        vals = pd.to_numeric(series, errors="coerce").to_numpy(dtype="float64")
        dates = span["date"].to_numpy()
        pts = []
        for dt, v in zip(dates, vals):
            if not np.isfinite(v):
                continue
            vc = min(max(float(v), vlo), vhi)
            pts.append((xd(pd.Timestamp(dt)), bot - (vc - vlo) / (vhi - vlo) * (ph - 4) - 2))
        if len(pts) > 1:
            d.line(pts, fill=color, width=2)
        for dt, v in zip(dates, vals):
            if np.isfinite(v) and pi == 2:
                vc = min(max(float(v), vlo), vhi)
                y = bot - (vc - vlo) / (vhi - vlo) * (ph - 4) - 2
                d.ellipse([xd(pd.Timestamp(dt)) - 1, y - 1, xd(pd.Timestamp(dt)) + 1, y + 1], fill=color)
        for hd in (c["s_date"], c["e_date"]):
            xh = xd(hd)
            d.line([(xh, top), (xh, bot)], fill=(180, 40, 40), width=1)
        lo, hi = (0.0, 1.0) if pi != 1 else (0.0, 60.0)
        d.text((x0 + 4, top + 2), f"{hi:.0f}" if pi == 1 else f"{hi:.1f}", fill=(120, 120, 120), font=f_tick)
        d.text((x0 + 4, bot - 14), f"{lo:.0f}" if pi == 1 else f"{lo:.1f}", fill=(120, 120, 120), font=f_tick)

    years = pd.date_range(dmin.replace(month=1, day=1), dmax, freq="YS")
    for y in years:
        xg = xd(y)
        if x0 <= xg <= x1:
            d.line([(xg, H - B), (xg, T)], fill=(230, 230, 230))
            d.text((xg - 16, H - B + 4), str(y.year), fill="black", font=f_tick)
    d.text((x0, H - B + 4), dmin.date().isoformat(), fill=(120, 120, 120), font=f_tick)

    img.save(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    smoke = bool(args.smoke and not args.all)
    n_target = N_SMOKE if smoke else N_CYCLES
    max_scan = MAX_SCAN_FIELDS_SMOKE if smoke else MAX_SCAN_FIELDS_ALL

    farms, stats_long = load_tables()
    field_block = farms.set_index("field_id")["block"].to_dict()
    frames = field_frames(stats_long)
    obs_by_field = {}
    for fid, f in frames.items():
        obs = get_field_obs(f)
        if obs is not None:
            obs_by_field[fid] = obs
    n_no_ndvi = len(frames) - len(obs_by_field)  # fields whose red/nir series is unusable
    print(f"Collecting cycles (seed={SEED}, target={n_target}, scan_limit={max_scan})...")
    cycles, skipped = collect_cycles(obs_by_field, field_block, max_scan=max_scan)
    skipped["fields_no_ndvi_total"] = n_no_ndvi
    print(f"Collected {len(cycles)} non-censored cycles ({skipped})")

    # Profiles for the whole population (cached per-field obs frames).
    for c in cycles:
        add_profile(c, obs_by_field[c["field"]])

    flags = compute_flags(cycles)

    rng = np.random.RandomState(SEED)
    chosen = stratified_sample(cycles, n_target, rng)
    chosen_keys = {(c["field"], c["cycle_id"]) for c in chosen}
    extras = [c for c in cycles
              if flags.get((c["field"], c["cycle_id"])) and (c["field"], c["cycle_id"]) not in chosen_keys]

    REPORTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    for old in PLOTS.glob("*.png"):  # plots are pure per-run output; purge stale ones
        old.unlink()

    rows = []
    n_plots = 0
    for reason, group in (("stratum", chosen), ("flagged", extras)):
        for c in group:
            fl = flags.get((c["field"], c["cycle_id"]), [])
            obs = obs_by_field[c["field"]]
            span = obs[(obs["date"] >= c["s_date"]) & (obs["date"] < c["e_date"])]["ndvi"]
            rows.append({
                "field": c["field"],
                "cycle_id": c["cycle_id"],
                "year": c["year"],
                "block": c["block"],
                "kind": c["kind"],
                "ratoon_no": c["ratoon_no"],
                "start_harvest": c["start_harvest"],
                "end_harvest": c["end_harvest"],
                "length_days": c["length_days"],
                "ndvi_mean": c.get("ndvi_mean", np.nan),
                "ndvi_min": float(np.nanmin(span)) if c.get("n_valid") else np.nan,
                "ndvi_max": c.get("ndvi_max", np.nan),
                "ndvi_drop": c.get("ndvi_drop", np.nan),
                "n_valid": c.get("n_valid", 0),
                "flags": ";".join(fl),
                "selected_reason": reason,
            })
            plot_path = PLOTS / f"field{c['field']}_cycle{c['cycle_id']}.png"
            try:
                plot_cycle_png(c, obs, fl, plot_path)
                n_plots += 1
            except Exception as e:  # plot failure must not invalidate the CSV
                print(f"  plot failed for field {c['field']} cycle {c['cycle_id']}: {e}")

    csv_path = REPORTS / "audit.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else
                           ["field", "cycle_id", "year", "block", "kind", "ratoon_no", "start_harvest",
                            "end_harvest", "length_days", "ndvi_mean", "ndvi_min", "ndvi_max",
                            "ndvi_drop", "n_valid", "flags", "selected_reason"])
        w.writeheader()
        w.writerows(rows)

    flag_counts: dict[str, int] = {}
    for r in rows:
        for fl in r["flags"].split(";") if r["flags"] else []:
            flag_counts[fl] = flag_counts.get(fl, 0) + 1
    summary = {
        "script": "scripts/audit_cycles.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": git_sha(),
        "seed": SEED,
        "smoke": smoke,
        "n_population": len(cycles),
        "n_fields_scanned": skipped["fields_scanned"],
        "fields_no_ndvi_total": skipped["fields_no_ndvi_total"],
        "fields_errors": skipped["fields_errors"],
        "n_audited": len(rows),
        "n_stratum": len(chosen),
        "n_flagged_extra": len(extras),
        "plots_written": n_plots,
        "flag_counts": flag_counts,
        "notes": [
            "overlap_with_neighbour = same-field neighbouring-cycle overlap per D2 "
            "(cross-field variant was a bug; its 96.7% rate is void)",
            "plots rendered with PIL (matplotlib savefig segfaults in this environment)",
        ],
    }
    (REPORTS / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {csv_path} ({len(rows)} rows: {len(chosen)} stratum + {len(extras)} flagged), "
          f"{n_plots} plots in {PLOTS}, summary.json")


if __name__ == "__main__":
    main()
