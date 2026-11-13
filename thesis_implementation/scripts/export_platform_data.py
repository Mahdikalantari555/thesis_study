"""Export Khuzestan farm GeoJSON (WGS84), time series, and model scores into platform/src/data/.

Converts Data/Processed/coordinates/farms.geojson to EPSG:4326 (WGS84), merges
farm attributes from farms.parquet, extracts multi-spectral indices from stats.zarr,
runs checkpoint-backed anomaly inference (STS-Net, Tiny-CNN-Mamba, Time2Agri) per
field cycle, and serializes browser-ready JSON for the React/Vite visualization
platform. Missing/broken checkpoints degrade to the CWSI proxy formula with
``"provenance": "proxy"`` instead of crashing (``--no-models`` forces that path).
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
from platform_channels import CONTRACT_VERSION, PROXY_SCORE_FORMULA_ID, SCORE_CHECKPOINTS, SCORE_NAMES, by_name  # type: ignore
from load_model_checkpoints import load_model_checkpoints, squash_bin_error  # type: ignore
from cycle_inputs import build_field_cycles, resolve_observation_scores  # type: ignore

REVISIT_DAYS = 9.3  # informational: Landsat revisit cadence (kept for docs)


class ContractViolation(ValueError):
    pass


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
        help="Skip checkpoint inference entirely; emit proxy scores with provenance 'proxy'",
    )
    p.add_argument(
        "--checkpoints-dir",
        type=Path,
        default=ROOT_DIR / "checkpoints",
        help="Directory holding the <model>_490.pt checkpoints (default: checkpoints/)",
    )
    return p.parse_args()


def to_contract_v4(series_by_field: dict[str, list[dict]]) -> dict:
    """Compact the per-observation maps into the v4 wire format.

    v3 stored a full object per observation; with the observation axis widened
    to every acquisition date (490 x 538) that cost ~1.1 kB/obs (292 MB) —
    dominated by strings repeated thousands of times. v4 keeps every v3 value
    but stores each series once:

      - ``axis``: the shared acquisition-date list (first row -> last row);
      - ``fields.<id>.channels`` / ``.scores``: numeric arrays indexed by the
        axis (null = absent);
      - ``channelProvenance`` / ``scoreProvenance``: run-length encoded
        ``[state, count]`` pairs per series;
      - everything else is derived on load (``sampleDate``/``acquisitionDate``
        = the axis date, ``scoreFormulaId`` from the provenance state, ``idx``
        from position, ``missing`` = NDVI null, ``stalenessReason`` =
        "invalid acquisition" when missing, ``scoreCollinearity`` shared).

    The runtime decoder (``platform/src/data/data.ts``) reconstructs the exact
    v3-shaped observation objects, so the views are unchanged.
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
        }
    return {
        "contractVersion": 4,
        "axis": axis,
        "collinearity": next(iter(series_by_field.values()))[0]["scoreCollinearity"],
        "checkpoints": dict(SCORE_CHECKPOINTS),
        "proxyFormulaId": PROXY_SCORE_FORMULA_ID,
        "fields": fields_out,
    }


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
        models: dict = {}
        model_status: dict[str, str] = {}
        log.info("--no-models given: all scores will use the CWSI proxy formula (provenance 'proxy')")
    else:
        models, model_status = load_model_checkpoints(args.checkpoints_dir)
    loaded_ids = sorted(mid for mid, st in model_status.items() if st == "loaded")
    missing_ids = sorted(mid for mid, st in model_status.items() if st == "missing")
    failed_ids = sorted(mid for mid, st in model_status.items() if st == "failed")
    log.info(
        "Score provenance plan: model=%s proxy=%s absent=%s (proxy formula %s covers b0/b1 baselines and masked_transformer)",
        loaded_ids or "[]", missing_ids or "[]", failed_ids or "[]", PROXY_SCORE_FORMULA_ID,
    )

    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")

    merged = gdf.merge(df_meta, on="field_id", how="left")

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

    # Per-field-cycle tensors (36 phase bins x 8 channels) built exactly like the
    # training NPZ (scripts/segment_and_export_cycles_490.py), then scored by each
    # loaded checkpoint with leave-one-time-bin-out masked reconstruction.
    day_times = dates.to_numpy().astype("datetime64[D]")
    time_days = (day_times - day_times[0]).astype(int)
    acq_day_num = time_days  # day number per acquisition index

    cycles_by_field: dict[int, list] = {}
    cycle_rows: list = []
    if models:
        log.info("Building per-field cycle tensors for checkpoint inference...")
        for fi, fid in enumerate(reader.fields):
            built = build_field_cycles(
                int(fid), time_days, ndvi_cube[fi], valid_cube[fi], cube[fi], reader.band_index,
            )
            cycles_by_field[int(fid)] = built
            cycle_rows.extend(built)
        log.info("Built %d scoreable cycles across %d fields", len(cycle_rows), len(cycles_by_field))

    model_errs: dict[str, np.ndarray] = {}
    if cycle_rows and models:
        X_all = np.stack([c.x for c in cycle_rows])
        for mid, loaded in models.items():
            if loaded is None:
                continue
            log.info("Running checkpoint inference with %s on %d cycles...", mid, len(cycle_rows))
            model_errs[mid] = squash_bin_error(loaded.score_cycles(X_all))
    elif not models:
        log.info("Skipping checkpoint inference (no models loaded)")

    def clean_text(v) -> str:
        """Registry text verbatim; NaN/None -> "" (never a generated default)."""
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return ""
        s = str(v).strip()
        return "" if s.lower() in ("nan", "none") else s

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

            # Checkpoint-backed anomaly scores (contract v3): loaded models score
            # the cycle bin containing the acquisition date; everything else falls
            # back to the CWSI proxy rule with provenance 'proxy'.
            scores, score_prov, score_formula = resolve_observation_scores(
                int(acq_day_num[ai]),
                cycles_by_field.get(fid, []),
                model_errs=model_errs,
                model_status=model_status,
                cwsi=cwsi,
                force_proxy=args.no_models,
            )

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
    for obs_list in series_by_field.values():
        for o in obs_list:
            for key, st in (o.get("scoreProvenance") or {}).items():
                prov_tally[st] = prov_tally.get(st, 0) + 1
                if st == "model":
                    model_tally[key] = model_tally.get(key, 0) + 1
    log.info(
        "Score provenance tally over observation x score key: model=%d proxy=%d absent=%d",
        prov_tally.get("model", 0), prov_tally.get("proxy", 0), prov_tally.get("absent", 0),
    )
    log.info("Model-backed scores per model id: %s", model_tally)

    def atomic_dump(path, obj):
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        os.replace(tmp, path)

    farms_json_path = PLATFORM_DATA_DIR / "farms_khuzestan.json"
    atomic_dump(farms_json_path, farm_records)
    log.info("Saved %d Khuzestan farm definitions to %s", len(farm_records), farms_json_path)

    series_json_path = PLATFORM_DATA_DIR / "series_khuzestan.json"
    atomic_dump(series_json_path, to_contract_v4(series_by_field))
    log.info("Saved series for %d farms to %s (contract v4 compact)", len(series_by_field), series_json_path)
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
