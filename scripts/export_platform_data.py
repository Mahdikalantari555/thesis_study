"""Export Khuzestan farm GeoJSON (WGS84), time series, and model scores into platform/src/data/.

Converts Data/Processed/coordinates/farms.geojson to EPSG:4326 (WGS84), merges
farm attributes from farms.parquet, extracts multi-spectral indices from stats.zarr,
runs checkpoint-backed anomaly inference per field cycle, and serializes
browser-ready JSON for the React/Vite visualization platform.

Contract v5: every observation carries a causal ``stressFlag``
(``normal`` | ``suspected_stress`` | ``no_data`` | null), the checkpoint id
behind it and its split tag (``train`` | ``dev`` | ``test`` | ``monitoring``);
every field carries ``ladderRung`` from the main checkpoint sidecar. Scores
resolve ONLY from real checkpoints (model) or are null + ``absent`` — the v4
CWSI proxy fallback was removed as circular (spec ``model-output-ingest``).
Missing/broken checkpoints degrade to ``absent`` instead of crashing
(``--no-models`` forces that path for every slot).
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
PLATFORM_DATA_DIR = ROOT_DIR / "platform/src/data"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("export_platform_data")

sys.path.insert(0, str(SCRIPT_DIR))
from platform_channels import CONTRACT_VERSION, SCORE_CHECKPOINTS, SCORE_NAMES, by_name  # type: ignore
from load_model_checkpoints import (  # type: ignore
    LoadedCausalModel,
    LoadedModel,
    load_model_checkpoints,
    score_formula_id,
    squash_bin_error,
)
from cycle_inputs import (  # type: ignore
    SPLIT_MONITORING,
    build_cycle_split_map,
    build_field_cycles,
    build_field_cycles_masked,
    cycle_split_tag,
    lookup_masked_cycle_bin,
    resolve_observation_scores_v5,
    resolve_stress_flag,
)

REVISIT_DAYS = 9.3  # informational: Landsat revisit cadence (kept for docs)

# ── Anomaly desk payload (add-halqeh-anomaly-desk) ────────────────────────────
# The desk replays the frozen 2026-11-11 stage-conditioned run: every case of
# the run's parquet (no curation — design D1), the run's summary envelopes and
# the farm registry identity. Naive-cut counts are computed here, never quoted.
DESK_NAIVE_CUT = 0.40
DESK_STAGE_SHORT = {
    "S1_establishment_growth": "S1",
    "S2_vegetative_reproductive": "S2",
    "S3_maturity_senescence": "S3",
    "S4_harvest_dormancy": "S4",
}
DESK_PARQUET_PATH = ROOT_DIR / "reports/stage_conditioned_anomaly/stage_conditioned_anomaly.parquet"
DESK_SUMMARY_PATH = ROOT_DIR / "reports/stage_conditioned_anomaly/summary.json"
DESK_PAYLOAD_PATH = PLATFORM_DATA_DIR / "desk_khuzestan.json"


class ContractViolation(ValueError):
    pass


def clean_text(v) -> str:
    """Registry text verbatim; NaN/None -> "" (never a generated default)."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none") else s


def validate_observation(field_id: int, sample_date: str, channel: str, value: float | None) -> None:
    if value is None:
        return
    spec = by_name(channel)
    lo, hi = spec.physical_range
    if value < lo or value > hi:
        raise ContractViolation(
            f"field {field_id} sample {sample_date} channel {channel}: {value} outside [{lo}, {hi}]"
        )


def clamp(x: float, lo: float, hi: float) -> float:
    return float(min(hi, max(lo, x)))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export platform data with checkpoint-backed anomaly scores")
    p.add_argument(
        "--no-models",
        action="store_true",
        help="Skip checkpoint inference entirely; every score slot is null with provenance 'absent'",
    )
    p.add_argument(
        "--desk-only",
        action="store_true",
        help="Only export the anomaly-desk payload (desk_khuzestan.json) from the "
        "stage-conditioned run artifacts + farm registry; skips zarr/checkpoint scoring",
    )
    p.add_argument(
        "--checkpoints-dir",
        type=Path,
        default=ROOT_DIR / "checkpoints",
        help="Directory holding the model checkpoints + sidecars (default: checkpoints/)",
    )
    return p.parse_args()


def build_desk_registry(merged: "gpd.GeoDataFrame") -> dict[str, dict]:
    """Desk-side farm registry: identity fields keyed ``F-###``.

    Mirrors the farm_records composition below exactly (same clean_text rules,
    same name/municipality join) minus polygon/baselineHealth — the desk payload
    contract test asserts desk metadata == the farms payload, so any divergence
    between the two compositions fails the gate.
    """
    registry: dict[str, dict] = {}
    for _, row in merged.iterrows():
        fid = int(row["field_id"])
        code = clean_text(row.get("farm"))
        block = clean_text(row.get("block"))
        office = clean_text(row.get("office"))
        management = clean_text(row.get("management"))
        variety = clean_text(row.get("variety")) or None
        area_raw = row.get("area_ha")
        area = float(area_raw) if area_raw is not None and pd.notna(area_raw) else None
        geom = row["geometry"]
        registry[f"F-{fid:03d}"] = {
            "code": code or None,
            "name": (f"{code} · {office}" if office else code) or None,
            "farm": block or None,
            "municipality": " · ".join(x for x in (office, management) if x) or None,
            "variety": variety,
            "areaHa": round(area, 1) if area is not None else None,
            "lat": round(float(geom.centroid.y), 5),
            "lng": round(float(geom.centroid.x), 5),
        }
    return registry


def export_desk_payload(registry: dict[str, dict], out_path: Path) -> dict:
    """Replay the frozen stage-conditioned run into ``desk_khuzestan.json``.

    Every (field, cycle) case of the run's parquet (design D1 — the Grok
    build's 12-case hand-pick is replaced by the complete replay), per-bin
    envelope values verbatim from the parquet, run totals recomputed from the
    parquet (naive-cut counts computed, never quoted), envelopes + provenance
    from the run's summary.json, and registry identity from the farms source.
    Missing run artifacts are a hard error — no stale or partial replay.
    """
    missing = [p for p in (DESK_PARQUET_PATH, DESK_SUMMARY_PATH) if not p.exists()]
    if missing:
        raise ContractViolation(
            "desk export needs the stage-conditioned run artifacts, missing: "
            + ", ".join(str(p) for p in missing)
            + " — run scripts/stage_conditioned_anomaly.py --all first"
        )

    df = pd.read_parquet(DESK_PARQUET_PATH)
    with open(DESK_SUMMARY_PATH, encoding="utf-8") as f:
        summary = json.load(f)

    flag_mask = df["is_anomaly"].astype(bool)
    naive_mask_all = df["ndvi"] < DESK_NAIVE_CUT
    overlap = int((naive_mask_all & flag_mask).sum())
    flags_total = int(flag_mask.sum())
    naive_total = int(naive_mask_all.sum())

    stage_rows: dict[str, dict] = {s: {"n": 0, "flags": 0, "naive": 0} for s in DESK_STAGE_SHORT.values()}
    cases: list[dict] = []
    for (fid, cycle), g in df.groupby(["field", "cycle_id"], sort=True):
        g = g.sort_values("bin_index", kind="stable")
        flags = int(g["is_anomaly"].sum())
        naive = int((g["ndvi"] < DESK_NAIVE_CUT).sum())
        reg = registry.get(f"F-{fid:03d}")
        s2 = g.loc[g["stage"] == "S2_vegetative_reproductive", "ndvi"]
        s3 = g.loc[g["stage"] == "S3_maturity_senescence", "ndvi"]
        flagged = g.loc[flag_mask.loc[g.index]]
        deepest = float((flagged["envelope_lower"] - flagged["ndvi"]).max()) if flags else 0.0
        case = {
            "id": f"{int(fid)}-{int(cycle)}",
            "field": int(fid),
            "fieldId": f"F-{fid:03d}",
            "code": reg["code"] if reg else None,
            "name": reg["name"] if reg else None,
            "farm": reg["farm"] if reg else None,
            "municipality": reg["municipality"] if reg else None,
            "variety": reg["variety"] if reg else None,
            "areaHa": reg["areaHa"] if reg else None,
            "lat": reg["lat"] if reg else None,
            "lng": reg["lng"] if reg else None,
            "cycle": int(cycle),
            "lengthDays": int(g["cycle_length_days"].iloc[0]),
            "censored": bool(g["censored"].iloc[0]),
            "start": str(g["bin_date"].iloc[0]),
            "end": str(g["bin_date"].iloc[-1]),
            "flags": flags,
            "naive": naive,
            "deepest": round(deepest, 3),
            "s2max": round(float(s2.max()), 3) if len(s2) else None,
            "s3min": round(float(s3.min()), 3) if len(s3) else None,
            "kind": "slip" if flags else "spared",
            "bins": [
                {
                    "i": int(r.bin_index),
                    "p": round(float(r.progress), 4),
                    "stage": DESK_STAGE_SHORT[r.stage],
                    "v": round(float(r.ndvi), 4),
                    "lo": round(float(r.envelope_lower), 4),
                    "hi": round(float(r.envelope_upper), 4),
                    "med": round(float(r.envelope_median), 4),
                    "d": str(r.bin_date),
                    "f": bool(r.is_anomaly),
                }
                for r in g.itertuples()
            ],
        }
        for st, gg in g.groupby("stage", sort=True):
            row = stage_rows[DESK_STAGE_SHORT[st]]
            row["n"] += int(len(gg))
            row["flags"] += int(gg["is_anomaly"].sum())
            row["naive"] += int((gg["ndvi"] < DESK_NAIVE_CUT).sum())
        cases.append(case)

    # Prime directive 2: NaN never reaches the payload — fail loudly instead.
    def _finite(x, where: str) -> None:
        if x is None or isinstance(x, (str, bool)):
            return
        if not math.isfinite(float(x)):
            raise ContractViolation(f"desk payload: non-finite value at {where}")

    for case in cases:
        for key in ("lat", "lng", "areaHa", "deepest", "s2max", "s3min"):
            _finite(case[key], f"{case['id']}.{key}")
        for b in case["bins"]:
            for key in ("p", "v", "lo", "hi", "med"):
                _finite(b[key], f"{case['id']}.bin{b['i']}.{key}")

    envelopes = {}
    for long_id, short_id in DESK_STAGE_SHORT.items():
        e = summary["stage_envelopes"][long_id]
        envelopes[short_id] = {
            "median": round(float(e["median"]), 4),
            "mad": round(float(e["mad"]), 4),
            "lo": round(float(e["lower"]), 4),
            "hi": round(float(e["upper"]), 4),
            "n": int(e["n"]),
        }

    places = [
        {"n": int(fid[2:]), "lat": rec["lat"], "lng": rec["lng"]}
        for fid, rec in sorted(registry.items())
    ]

    payload = {
        "contractVersion": 1,
        "generated": str(summary["generated_at"])[:10],
        "source": "reports/stage_conditioned_anomaly/stage_conditioned_anomaly.parquet",
        "provenance": {
            "gitSha": summary.get("git_sha"),
            "generatedAt": summary["generated_at"],
            "dataSource": summary["data_source"],
            "seed": int(summary["seed"]),
            "binDays": int(summary["bin_days"]),
            "envelopeK": float(summary["envelope_k"]),
            "naiveCut": DESK_NAIVE_CUT,
            "parquet": "reports/stage_conditioned_anomaly/stage_conditioned_anomaly.parquet",
            "summary": "reports/stage_conditioned_anomaly/summary.json",
            "registry": "Data/Processed/coordinates/farms.geojson + Data/Processed/coordinates/farms.parquet",
            "exporter": "scripts/export_platform_data.py",
        },
        "totals": {
            "fieldsInRun": int(df["field"].nunique()),
            "fieldsInRegistry": len(registry),
            "cycles": int(df.groupby(["field", "cycle_id"]).ngroups),
            "validObsReported": int(summary["n_valid_obs"]),
            "rows": int(len(df)),
            "flags": flags_total,
            "flagRate": float(summary["flag_rate"]),
            "binDays": int(summary["bin_days"]),
            "envelopeK": float(summary["envelope_k"]),
            "naiveCut": DESK_NAIVE_CUT,
            "naiveOnly": naive_total - overlap,
            "envelopeOnly": flags_total - overlap,
            "overlap": overlap,
        },
        "envelopes": envelopes,
        "stageRows": [
            {"s": s, **stage_rows[s]} for s in sorted(stage_rows)
        ],
        "cases": cases,
        "places": places,
    }

    atomic_dump(out_path, payload)
    size_kb = out_path.stat().st_size / 1024
    log.info(
        "Desk payload: %d cases, %d bins, %d flags (%d naive-only / %d envelope-only / "
        "%d overlap) → %s (%.0f KB)",
        len(cases), sum(len(c["bins"]) for c in cases), flags_total,
        naive_total - overlap, flags_total - overlap, overlap, out_path, size_kb,
    )
    return payload


def to_contract_v5(series_by_field: dict[str, list[dict]], ladder_rung: str | None = None) -> dict:
    """Compact the per-observation maps into the v5 wire format.

    v5 extends the v4 compact payload (shared ``axis`` + per-field numeric
    arrays + RLE provenance) with the causal stress-flag fields:

      - ``stressFlag``: per observation ``normal`` | ``suspected_stress`` |
        ``no_data`` | null (null = no model-backed flag available), RLE-encoded
        like the provenance series;
      - ``stressFlagModel``: checkpoint id per observation (null when absent);
      - ``split``: ``train`` | ``dev`` | ``test`` | ``monitoring`` per
        observation — split membership only controls which cycles enter
        metrics, never what is displayed;
      - ``ladderRung`` per field from the main checkpoint sidecar
        (``"L2"``/``"L3"``, null without a checkpoint — the validation-ladder
        rung every flag claim is bounded by);
      - ``scoreFormulas``: per score key the formula id its ``model``-provenance
        observations carry (``<stem>:causal_bin_mse`` for the causal main
        checkpoints, ``<stem>_490:bin_mse_1mexp`` for the legacy ones).

    There is no ``proxyFormulaId`` in v5: no observation ever carries the
    removed CWSI proxy formula.
    """

    def rle(values: list) -> list:
        runs: list[list] = []
        for v in values:
            if runs and runs[-1][0] == v:
                runs[-1][1] += 1
            else:
                runs.append([v, 1])
        return runs

    axis = [o["date"] for o in next(iter(series_by_field.values()))]
    channels = ["ndvi", "evi", "savi", "ndmi", "tvdi", "cwsi", "eta", "lst", "precip", "temp"]
    fields_out: dict[str, dict] = {}
    for fid, obs_list in series_by_field.items():
        fields_out[fid] = {
            "channels": {c: [o[c] for o in obs_list] for c in channels},
            "scores": {k: [o["scores"][k] for o in obs_list] for k in SCORE_NAMES},
            "channelProvenance": {c: rle([o["provenance"][c] for o in obs_list]) for c in channels},
            "scoreProvenance": {k: rle([o["scoreProvenance"][k] for o in obs_list]) for k in SCORE_NAMES},
            "stressFlag": rle([o["stressFlag"] for o in obs_list]),
            "stressFlagModel": rle([o["stressFlagModel"] for o in obs_list]),
            "split": rle([o["split"] for o in obs_list]),
            "ladderRung": ladder_rung,
        }
    return {
        "contractVersion": 5,
        "axis": axis,
        "collinearity": next(iter(series_by_field.values()))[0]["scoreCollinearity"],
        "checkpoints": dict(SCORE_CHECKPOINTS),
        "scoreFormulas": {k: fid for k in SCORE_NAMES if (fid := score_formula_id(k)) is not None},
        "fields": fields_out,
    }


def atomic_dump(path: Path, obj: dict) -> None:
    """Write JSON atomically. ``allow_nan=False``: NaN/Infinity never serialize —
    a non-finite value is a defect to fix at the source, not to ship."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False)
    os.replace(tmp, path)


def main() -> None:
    args = parse_args()
    PLATFORM_DATA_DIR.mkdir(parents=True, exist_ok=True)

    geojson_path = ROOT_DIR.parent / "Data/Processed/coordinates/farms.geojson"
    parquet_path = ROOT_DIR.parent / "Data/Processed/coordinates/farms.parquet"
    zarr_path = ROOT_DIR.parent / "Data/Processed/satellite/stats.zarr"
    weather_path = ROOT_DIR.parent / "Data/Processed/weather/weather_aligned.parquet"

    log.info("Loading farm polygons and metadata...")
    gdf = gpd.read_file(geojson_path)
    df_meta = pd.read_parquet(parquet_path)

    # Registry merge happens up front so both the full export and --desk-only
    # share the identical farm-identity composition.
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    merged = gdf.merge(df_meta, on="field_id", how="left")

    if args.desk_only:
        registry = build_desk_registry(merged)
        export_desk_payload(registry, DESK_PAYLOAD_PATH)
        return

    # Real weather (ERA5 reanalysis) joined on the acquisition date below.
    # precip <- precipitation_sum, temp <- temperature_mean; observation dates
    # without a weather row stay null and are labelled "absent" (never invented).
    weather_by_date: dict[str, tuple[float, float]] = {}
    if weather_path.exists():
        wdf = pd.read_parquet(weather_path)
        for _, wr in wdf.iterrows():
            key = pd.Timestamp(wr["acquisition_date"]).strftime("%Y-%m-%d")
            p, t_ = wr.get("precipitation_sum"), wr.get("temperature_mean")
            if pd.notna(p) and pd.notna(t_):
                weather_by_date[key] = (float(p), float(t_))
        log.info("Weather aligned: %d dated rows from %s", len(weather_by_date), weather_path.name)
    else:
        log.warning("weather_aligned.parquet not found — precip/temp stay null with provenance 'absent'")

    if args.no_models:
        models: dict[str, object | None] = {}
        model_status: dict[str, str] = {}
        log.info("--no-models given: every score slot stays null with provenance 'absent' (no proxy in v5)")
    else:
        models, model_status = load_model_checkpoints(args.checkpoints_dir)
    loaded_ids = sorted(mid for mid, st in model_status.items() if st == "loaded")
    missing_ids = sorted(mid for mid, st in model_status.items() if st == "missing")
    failed_ids = sorted(mid for mid, st in model_status.items() if st == "failed")
    log.info(
        "Score provenance plan: model=%s missing=%s failed=%s (v5: no proxy fallback — "
        "unresolved slots are null + 'absent')",
        loaded_ids or "[]", missing_ids or "[]", failed_ids or "[]",
    )

    sys.path.insert(0, str(ROOT_DIR / "src"))
    from ssl_anomaly.io.stats_zarr import load_stats_zarr

    reader = load_stats_zarr(zarr_path)
    indices = reader.compute_indices("median")
    ndvi_cube = indices["ndvi"]
    ndmi_cube = indices["ndmi"]
    savi_cube = indices["savi"]
    lst_cube = indices["lst"]
    valid_cube = reader.valid_frac
    dates = reader.dates
    cube = reader.get_stat("median")

    # Observation axis: EVERY acquisition date in the cube, first row to last
    # row — no synthetic mid-month sampling. Each observation *is* a real
    # Landsat acquisition, so sampleDate == acquisitionDate, months with two
    # acquisitions appear twice, and the staleness guard ("no acquisition
    # within window") becomes structurally impossible. A date can still be
    # invalid per field (low valid_frac / out-of-range LST) — that stays the
    # honest "missing" state.
    sample_dates = [pd.Timestamp(d) for d in dates]
    log.info(
        "Observation axis: %d acquisition dates %s → %s (all cube dates, no monthly resampling)",
        len(sample_dates), sample_dates[0].date(), sample_dates[-1].date(),
    )

    day_times = dates.to_numpy().astype("datetime64[D]")
    time_days = (day_times - day_times[0]).astype(int)
    acq_day_num = time_days  # day number per acquisition index

    # Split tagging (contract v5): cycle -> train|dev|test|monitoring from the
    # locked manifest. Computed in-process; missing files degrade to
    # "monitoring" for everything (never a fabricated in-sample tag).
    split_map = build_cycle_split_map(ROOT_DIR)

    # Masked cycle tensors (NO interior-gap interpolation — the exact input
    # semantics of the causal main checkpoints), censored in-progress cycles
    # INCLUDED for display + split tagging (they never enter metrics). Built
    # for every field regardless of checkpoint availability: the split tag of
    # each observation comes from the cycle containing its acquisition date.
    masked_cycles_by_field: dict[int, list] = {}
    masked_rows: list = []
    log.info("Building masked per-field cycle tensors (no interpolation, censored included)...")
    for fi, fid in enumerate(reader.fields):
        built = build_field_cycles_masked(
            int(fid), time_days, ndvi_cube[fi], valid_cube[fi], cube[fi], reader.band_index,
            include_censored=True,
        )
        masked_cycles_by_field[int(fid)] = built
        masked_rows.extend(built)
    log.info(
        "Built %d masked cycles across %d fields (%d censored kept for display)",
        len(masked_rows), len(masked_cycles_by_field), sum(1 for c in masked_rows if c.censored),
    )

    # Causal main checkpoint scoring (v5): RAW z-space per-bin scores.
    new_raw_errs: dict[str, np.ndarray] = {}
    causal_keys = [k for k, m in models.items() if isinstance(m, LoadedCausalModel)]
    if masked_rows and causal_keys:
        X_masked = np.stack([c.x for c in masked_rows])  # NaN where unobserved
        M_masked = np.stack([c.mask for c in masked_rows])
        H_masked = np.array([c.harvest_day for c in masked_rows], dtype=np.int64)
        for key in causal_keys:
            loaded = models[key]
            assert isinstance(loaded, LoadedCausalModel)
            log.info("Running causal checkpoint inference with %s on %d masked cycles...", key, len(masked_rows))
            new_raw_errs[key] = loaded.score_cycles(X_masked, M_masked, H_masked)

    # Legacy checkpoints keep their pipeline: interpolated (non-censored) cycle
    # tensors, squashed per-bin scores.
    legacy_cycles_by_field: dict[int, list] = {}
    legacy_squashed_errs: dict[str, np.ndarray] = {}
    legacy_keys = [k for k, m in models.items() if isinstance(m, LoadedModel)]
    if legacy_keys:
        legacy_rows: list = []
        log.info("Building interpolated per-field cycle tensors for legacy checkpoints...")
        for fi, fid in enumerate(reader.fields):
            built = build_field_cycles(
                int(fid), time_days, ndvi_cube[fi], valid_cube[fi], cube[fi], reader.band_index,
            )
            legacy_cycles_by_field[int(fid)] = built
            legacy_rows.extend(built)
        log.info("Built %d scoreable legacy cycles across %d fields", len(legacy_rows), len(legacy_cycles_by_field))
        if legacy_rows:
            X_all = np.stack([c.x for c in legacy_rows])
            for mid in legacy_keys:
                loaded = models[mid]
                assert isinstance(loaded, LoadedModel)
                log.info("Running checkpoint inference with %s on %d cycles...", mid, len(legacy_rows))
                legacy_squashed_errs[mid] = squash_bin_error(loaded.score_cycles(X_all))
    else:
        log.info("Skipping legacy checkpoint inference (no legacy models loaded)")

    # Main model for the causal stress flag: masked_transformer_main if loaded,
    # else gru_ae_main; tau/persistence-k come from its sidecar. Without a main
    # model (or without a calibrated threshold) stressFlag stays null everywhere
    # — never fabricated, never "normal" by default.
    main_key: str | None = None
    for cand in ("masked_transformer", "gru_ae"):
        if model_status.get(cand) == "loaded" and isinstance(models.get(cand), LoadedCausalModel):
            main_key = cand
            break
    main_errs: np.ndarray | None = new_raw_errs.get(main_key) if main_key else None
    main_tau: float | None = None
    main_k: int = 1
    ladder_rung: str | None = None
    stress_flag_model: str | None = None
    if main_key is not None:
        main_loaded = models[main_key]
        assert isinstance(main_loaded, LoadedCausalModel)
        thr = main_loaded.threshold or {}
        main_tau = thr.get("tau")
        main_k = int(thr.get("k", main_loaded.sidecar.get("persistence_k") or 1))
        ladder_rung = main_loaded.ladder_rung
        stress_flag_model = main_loaded.model_id
        if main_tau is None:
            log.warning(
                "Main checkpoint %s has no calibrated threshold in its sidecar — "
                "stressFlag stays null for every observation",
                main_loaded.model_id,
            )
        else:
            log.info(
                "Stress flag: model=%s tau=%.4f k=%d ladder_rung=%s",
                stress_flag_model, float(main_tau), main_k, ladder_rung or "n/a",
            )
    else:
        log.info("No causal main checkpoint loaded — stressFlag stays null for every observation")

    log.info("Building farm records...")
    farm_records = []
    series_by_field: dict[str, list[dict]] = {}
    total_samples = 0
    weather_matched = 0
    weather_dated = 0

    for _, row in merged.iterrows():
        fid = int(row["field_id"])
        # Real registry attributes (farms.parquet). Missing values stay
        # empty/null — synthesized defaults ("Khuzestan Unit …", CP69-1062,
        # 25 ha) were removed in wire-platform-to-real-data.
        code = clean_text(row.get("farm"))
        block = clean_text(row.get("block"))
        office = clean_text(row.get("office"))
        management = clean_text(row.get("management"))
        variety = clean_text(row.get("variety")) or None
        area_raw = row.get("area_ha")
        area = float(area_raw) if area_raw is not None and pd.notna(area_raw) else None

        geom = row["geometry"]
        centroid_lat = round(float(geom.centroid.y), 5)
        centroid_lng = round(float(geom.centroid.x), 5)

        simplified = geom.simplify(0.0001, preserve_topology=True)
        coords = []
        if simplified.geom_type == "Polygon":
            coords = [[round(pt[1], 5), round(pt[0], 5)] for pt in simplified.exterior.coords]
        elif simplified.geom_type == "MultiPolygon":
            largest = max(simplified.geoms, key=lambda p: p.area)
            coords = [[round(pt[1], 5), round(pt[0], 5)] for pt in largest.exterior.coords]

        field_key = f"F-{fid:03d}"
        fi = fid - 1

        field_masked_cycles = masked_cycles_by_field.get(fid, [])
        field_legacy_cycles = legacy_cycles_by_field.get(fid, [])

        farm_obs = []
        field_ndvi = ndvi_cube[fi]
        field_ndmi = ndmi_cube[fi]
        field_savi = savi_cube[fi]
        field_lst = lst_cube[fi]
        field_valid = valid_cube[fi]

        for step_i, sd in enumerate(sample_dates):
            total_samples += 1
            # Every sample date IS an acquisition (axis = cube dates), so the
            # observation index is the cube time index directly.
            ai = step_i
            acq_date = sd
            acq_key = acq_date.strftime("%Y-%m-%d")
            weather_dated += 1
            wrec = weather_by_date.get(acq_key)
            if wrec is not None:
                weather_matched += 1
                precip_v, temp_v = wrec
            else:
                precip_v, temp_v = None, None
            red_v = float(cube[fi, ai, reader.band_index["red"]])
            nir_v = float(cube[fi, ai, reader.band_index["nir"]])
            blue_v = float(cube[fi, ai, reader.band_index["blue"]])
            denom = nir_v + 6.0 * red_v - 7.5 * blue_v + 1.0
            evi = 2.5 * (nir_v - red_v) / denom if abs(denom) > 1e-8 else None

            val_ndvi = float(field_ndvi[ai])
            val_ndmi = float(field_ndmi[ai])
            val_savi = float(field_savi[ai])
            lst_c = float(field_lst[ai] - 273.15)
            if not (15.0 <= lst_c <= 55.0):
                lst_c = None

            valid = bool(field_valid[ai] >= 0.50)
            if not valid:
                val_ndvi = None
                val_ndmi = None
                val_savi = None
                evi = None
                lst_c = None

            cwsi = None
            eta = None
            if val_ndvi is not None and lst_c is not None:
                cwsi = clamp((lst_c - 20.0) / 25.0 * (1.0 - val_ndvi), 0.0, 1.0)
                eta = clamp(val_ndvi * 6.5, 0.5, 7.5)
            tvdi = (cwsi * 0.9) if cwsi is not None else None

            # Checkpoint-backed anomaly scores (contract v5): causal main
            # checkpoints score the masked cycle bin containing the acquisition
            # date, legacy checkpoints the interpolated one; everything else is
            # null + "absent" (no proxy fallback in v5).
            day_num = int(acq_day_num[ai])
            scores, score_prov, score_formula = resolve_observation_scores_v5(
                day_num,
                field_masked_cycles,
                field_legacy_cycles,
                new_raw_errs=new_raw_errs,
                legacy_squashed_errs=legacy_squashed_errs,
            )

            # Split tag from the masked cycle containing the acquisition date.
            masked_hit = lookup_masked_cycle_bin(field_masked_cycles, day_num)
            if masked_hit is not None:
                split = cycle_split_tag(field_masked_cycles[masked_hit[0]], split_map)
            else:
                split = SPLIT_MONITORING

            # Causal stress flag: raw score prefix of the current cycle
            # (bins <= the acquisition's bin — appending future observations
            # never changes an issued status), compared against the sidecar
            # tau with persistence k. Unavailable without a main model.
            stress_flag = None
            if main_errs is not None and main_tau is not None and masked_hit is not None:
                mrow, mbin = masked_hit
                bin_observed = bool(np.isfinite(main_errs[mrow, mbin]))
                stress_flag = resolve_stress_flag(main_errs[mrow, : mbin + 1], main_tau, main_k, bin_observed)

            ndvi_r = round(val_ndvi, 3) if val_ndvi is not None else None
            evi_r = round(evi, 3) if evi is not None else None
            savi_r = round(val_savi, 3) if val_savi is not None else None
            ndmi_r = round(val_ndmi, 3) if val_ndmi is not None else None
            tvdi_r = round(tvdi, 3) if tvdi is not None else None
            cwsi_r = round(cwsi, 3) if cwsi is not None else None
            eta_r = round(eta, 2) if eta is not None else None
            lst_r = round(lst_c, 1) if lst_c is not None else None

            precip_r = round(precip_v, 2) if precip_v is not None else None
            temp_r = round(temp_v, 1) if temp_v is not None else None

            values = {
                "ndvi": ndvi_r,
                "evi": evi_r,
                "savi": savi_r,
                "ndmi": ndmi_r,
                "tvdi": tvdi_r,
                "cwsi": cwsi_r,
                "eta": eta_r,
                "lst": lst_r,
                "precip": precip_r,
                "temp": temp_r,
            }
            for ch, v in values.items():
                validate_observation(fid, sd.strftime("%Y-%m-%d"), ch, v)

            provenance = {
                "ndvi": "observed" if ndvi_r is not None else "absent",
                "evi": "proxy" if evi_r is not None else "absent",
                "savi": "observed" if savi_r is not None else "absent",
                "ndmi": "observed" if ndmi_r is not None else "absent",
                "tvdi": "proxy" if tvdi_r is not None else "absent",
                "cwsi": "proxy" if cwsi_r is not None else "absent",
                "eta": "proxy" if eta_r is not None else "absent",
                "lst": "observed" if lst_r is not None else "absent",
                # ERA5 reanalysis is legitimately "modelled" — but only when a
                # value exists; an unmatched date stays null + "absent".
                "precip": "modelled" if precip_r is not None else "absent",
                "temp": "modelled" if temp_r is not None else "absent",
            }

            obs = {
                "date": sd.strftime("%Y-%m-%d"),
                "sampleDate": sd.strftime("%Y-%m-%d"),
                "idx": step_i,
                "acquisitionDate": acq_date.strftime("%Y-%m-%d"),
                "missing": ndvi_r is None,
                "stalenessReason": None if ndvi_r is not None else "invalid acquisition",
                "ndvi": ndvi_r,
                "evi": evi_r,
                "savi": savi_r,
                "ndmi": ndmi_r,
                "tvdi": tvdi_r,
                "cwsi": cwsi_r,
                "eta": eta_r,
                "lst": lst_r,
                "precip": precip_r,
                "temp": temp_r,
                "scores": scores,
                "scoreProvenance": score_prov,
                "scoreFormulaId": score_formula,
                "provenance": provenance,
                "scoreCollinearity": "cwsi",
                "stressFlag": stress_flag,
                "stressFlagModel": stress_flag_model,
                "split": split,
            }
            farm_obs.append(obs)

        series_by_field[field_key] = farm_obs

        farm_records.append({
            "id": field_key,
            "code": code,
            "name": f"{code} · {office}" if office else code,
            # Real registry columns: farm = the physical block identifier,
            # municipality = administrative office (+ management unit). Both are
            # Persian registry text passed through verbatim (FA renders naturally).
            "farm": block,
            "municipality": " · ".join(x for x in (office, management) if x),
            "block": block,
            "areaHa": round(area, 1) if area is not None else None,
            "variety": variety,
            "planted": None,
            "harvest": None,
            "centroid": [centroid_lat, centroid_lng],
            "polygon": coords,
            "baselineHealth": round(float(np.nanmean(ndvi_cube[fi, :])), 2) if np.any(np.isfinite(ndvi_cube[fi, :])) else None,
            "neighbors": [],
            "contractVersion": CONTRACT_VERSION,
        })

    # neighbors ranked
    for i, f1 in enumerate(farm_records):
        c1 = f1["centroid"]
        cands = []
        for j, f2 in enumerate(farm_records):
            if i == j:
                continue
            c2 = f2["centroid"]
            dist = math.hypot((c1[0] - c2[0]) * 111.0, (c1[1] - c2[1]) * 95.0)
            if dist < 1.8:
                cands.append((dist, f2["id"]))
        cands.sort()
        f1["neighbors"] = [nid for _, nid in cands[:4]]

    prov_tally: dict[str, int] = {}
    model_tally: dict[str, int] = {}
    flag_tally: dict[str, int] = {}
    split_tally: dict[str, int] = {}
    for obs_list in series_by_field.values():
        for o in obs_list:
            for key, st in (o.get("scoreProvenance") or {}).items():
                prov_tally[st] = prov_tally.get(st, 0) + 1
                if st == "model":
                    model_tally[key] = model_tally.get(key, 0) + 1
            fl = o.get("stressFlag")
            flag_tally[str(fl)] = flag_tally.get(str(fl), 0) + 1
            sp = o.get("split")
            split_tally[str(sp)] = split_tally.get(str(sp), 0) + 1
    log.info(
        "Score provenance tally over observation x score key: model=%d absent=%d",
        prov_tally.get("model", 0), prov_tally.get("absent", 0),
    )
    log.info("Model-backed scores per model id: %s", model_tally)
    log.info("Stress flag tally: %s", flag_tally)
    log.info("Split tally: %s", split_tally)

    farms_json_path = PLATFORM_DATA_DIR / "farms_khuzestan.json"
    atomic_dump(farms_json_path, farm_records)
    log.info("Saved %d Khuzestan farm definitions to %s", len(farm_records), farms_json_path)

    # Desk payload (add-halqeh-anomaly-desk): registry identity from the just-
    # built farm_records, run artifacts from the frozen 2026-11-11 replay.
    desk_registry = {
        fr["id"]: {
            "code": fr["code"] or None,
            "name": fr["name"] or None,
            "farm": fr["farm"] or None,
            "municipality": fr["municipality"] or None,
            "variety": fr["variety"],
            "areaHa": fr["areaHa"],
            "lat": fr["centroid"][0],
            "lng": fr["centroid"][1],
        }
        for fr in farm_records
    }
    export_desk_payload(desk_registry, DESK_PAYLOAD_PATH)

    series_json_path = PLATFORM_DATA_DIR / "series_khuzestan.json"
    atomic_dump(series_json_path, to_contract_v5(series_by_field, ladder_rung=ladder_rung))
    log.info("Saved series for %d farms to %s (contract v5 compact)", len(series_by_field), series_json_path)
    n_missing = sum(1 for obs_list in series_by_field.values() for o in obs_list if o["missing"])
    log.info(
        "Observations: %d (%d fields x %d acquisition dates); %d invalid acquisitions rendered as missing",
        total_samples, len(series_by_field), len(next(iter(series_by_field.values()))), n_missing,
    )
    if weather_dated:
        frac = weather_matched / weather_dated
        log.info(
            "Weather join coverage: %d/%d dated observations matched weather_aligned.parquet (%.1f%%); non-null fraction precip=%.3f temp=%.3f",
            weather_matched, weather_dated, 100.0 * frac, frac, frac,
        )
    else:
        log.warning("Weather join coverage: no observations to match against")


if __name__ == "__main__":
    main()
