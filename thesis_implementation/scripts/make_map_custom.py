#!/usr/bin/env python3
"""Custom interactive map: time slider + variable selector + legend using daily_anomaly.parquet."""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import box

DEFAULT_OUT = Path("reports/figures/anomaly_map_custom.html")
CANDIDATE_GEO_PATHS = [
    Path("data/geo/Farms_subset.geojson"),
    Path("data/geo/fields.geojson"),
    Path("data/geo/fields.gpkg"),
    Path("D:/RS/Thesis/Data/RoI/Farms_subset.geojson"),
]


def anomaly_color(val: float | None) -> str:
    """Map per-day modified z-score S to hex fill color."""
    if val is None or not np.isfinite(val):
        return "#888888"
    if val < 3.5:
        return "#22c55e"
    if val < 7.0:
        return "#eab308"
    return "#dc2626"


def load_fields_gdf(field_ids: np.ndarray, fields_path: str | Path | None = None) -> gpd.GeoDataFrame:
    """Load farm polygons from disk or build a schematic Khuzestan R11 grid fallback."""
    candidates = ([Path(fields_path)] if fields_path else []) + CANDIDATE_GEO_PATHS
    for p in candidates:
        if p.exists():
            gdf = gpd.read_file(p).reset_index(drop=True)
            if gdf.crs is not None and str(gdf.crs) != "EPSG:4326":
                gdf = gdf.to_crs("EPSG:4326")
            elif gdf.crs is None:
                gdf = gdf.set_crs("EPSG:4326")
            gdf["field"] = np.arange(1, len(gdf) + 1, dtype=int)
            return gdf

    # Portable schematic grid for 32 R11 sugarcane fields in Khuzestan (~31.50N, 48.68E, ~25 ha/block)
    n_cols = 8
    dx, dy = 0.0053, 0.0045  # ~500m x 500m (~25 ha)
    gap = 0.0005
    lon0, lat0 = 48.660, 31.490
    geoms = []
    fids = [int(f) for f in field_ids]
    for idx, _ in enumerate(fids):
        r, c = divmod(idx, n_cols)
        x0 = lon0 + c * (dx + gap)
        y0 = lat0 + r * (dy + gap)
        geoms.append(box(x0, y0, x0 + dx, y0 + dy))
    return gpd.GeoDataFrame({"field": fids, "geometry": geoms}, crs="EPSG:4326")


def build_custom_map(
    zarr_path: str | Path = "data/processed/fields.zarr",
    daily_path: str | Path = "data/processed/daily_anomaly.parquet",
    out_path: str | Path = DEFAULT_OUT,
    fields_path: str | Path | None = None,
) -> tuple[Path, dict]:
    """Generate the interactive HTML map from per-date daily_anomaly.parquet and return diagnostics."""
    ds = xr.open_zarr(zarr_path)
    times = pd.to_datetime(ds.coords["time"].values)
    fields = ds.coords["field"].values
    bands = list(ds.coords["band"].values)

    if "ndvi" in ds.data_vars:
        ndvi_all = ds["ndvi"].values
    else:
        from ssl_anomaly.phenology import add_spectral_indices

        ds_idx = add_spectral_indices(ds)
        ndvi_all = ds_idx["median"].sel(band="NDVI").values

    lst_all = (
        ds["median"].sel(band="ST_B10").values
        if "ST_B10" in bands
        else np.full((len(fields), len(times)), np.nan, dtype=np.float32)
    )
    cwsi_all = (
        ds["cwsi_et"].values
        if "cwsi_et" in ds.data_vars
        else np.full((len(fields), len(times)), np.nan, dtype=np.float32)
    )

    daily = pd.read_parquet(daily_path)
    anomaly_map: dict[int, dict[str, float]] = {int(fid): {} for fid in fields}
    for _, r in daily.iterrows():
        fid = int(r["field"])
        d = str(r["date"])[:10]
        val = float(r["anomaly"])
        if np.isfinite(val) and fid in anomaly_map:
            prev = anomaly_map[fid].get(d)
            anomaly_map[fid][d] = val if prev is None else max(prev, val)

    dates = sorted({d.strftime("%Y-%m-%d") for d in times})
    timestamps = [int(pd.Timestamp(d).timestamp()) for d in dates]
    date_to_ti = {d.strftime("%Y-%m-%d"): ti for ti, d in enumerate(times)}

    data: dict[str, dict[str, dict]] = {}
    color_series_by_field: dict[int, list[str]] = {int(fid): [] for fid in fields}

    for fi, fid_raw in enumerate(fields):
        fid = int(fid_raw)
        data[str(fid)] = {}
        for d_str, ts in zip(dates, timestamps):
            ti = date_to_ti[d_str]
            anom_val = anomaly_map[fid].get(d_str)
            ndvi_v = float(ndvi_all[fi, ti]) if np.isfinite(ndvi_all[fi, ti]) else None
            lst_v = float(lst_all[fi, ti]) if np.isfinite(lst_all[fi, ti]) else None
            cwsi_v = float(cwsi_all[fi, ti]) if np.isfinite(cwsi_all[fi, ti]) else None
            data[str(fid)][str(ts)] = {
                "ndvi": round(ndvi_v, 4) if ndvi_v is not None else None,
                "lst": round(lst_v, 2) if lst_v is not None else None,
                "cwsi": round(cwsi_v, 4) if cwsi_v is not None else None,
                "anomaly": round(float(anom_val), 4) if anom_val is not None else None,
            }
            if anom_val is not None:
                color_series_by_field[fid].append(anomaly_color(anom_val))

    # Pick first date with valid daily anomaly scores as initial slider position
    initial_idx = 0
    for idx, d_str in enumerate(dates):
        if any(d_str in anomaly_map[int(fid)] for fid in fields):
            initial_idx = idx
            break

    gdf = load_fields_gdf(fields, fields_path=fields_path)
    bounds = gdf.total_bounds  # minx, miny, maxx, maxy
    center_lat = float(0.5 * (bounds[1] + bounds[3]))
    center_lon = float(0.5 * (bounds[0] + bounds[2]))

    geojson = json.loads(gdf.to_json())
    for feat in geojson["features"]:
        feat["id"] = str(feat["properties"]["field"])

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Daily Phenology-Aware Anomaly Map</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  body {{ margin:0; font-family: sans-serif; }}
  #map {{ height: 80vh; }}
  #controls {{ padding: 10px; background: #f0f0f0; display: flex; gap: 20px; align-items: center; flex-wrap: wrap; }}
  #legend {{ padding: 10px; background: #fff; border: 1px solid #ccc; margin: 10px; display: inline-block; }}
  .legend-item {{ display: flex; align-items: center; gap: 5px; margin: 2px 0; }}
  .legend-color {{ width: 20px; height: 14px; border: 1px solid #333; }}
  #slider-container {{ flex: 1; min-width: 300px; }}
  #date-label {{ font-weight: bold; min-width: 120px; }}
</style>
</head>
<body>
<div id="controls">
  <label>Variable:
    <select id="var-select">
      <option value="anomaly">Daily anomaly score (S)</option>
      <option value="ndvi">NDVI</option>
      <option value="lst">LST (K)</option>
      <option value="cwsi">CWSI-ET</option>
    </select>
  </label>
  <div id="slider-container">
    <input type="range" id="time-slider" min="0" max="{len(timestamps) - 1}" value="{initial_idx}" style="width:100%">
  </div>
  <span id="date-label">{dates[initial_idx]}</span>
</div>
<div id="legend"></div>
<div id="map"></div>
<script>
var data = {json.dumps(data)};
var geojson = {json.dumps(geojson)};
var timestamps = {json.dumps(timestamps)};
var dates = {json.dumps(dates)};

var map = L.map('map').setView([{center_lat}, {center_lon}], 13);
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
  attribution: 'Esri World Imagery',
  maxZoom: 18
}}).addTo(map);

var geoLayer = L.geoJSON(geojson, {{
  style: function(feature) {{
    return {{ fillColor: '#888888', weight: 1, color: '#333', fillOpacity: 0.7 }};
  }},
  onEachFeature: function(feature, layer) {{
    layer.bindPopup('Field ' + feature.properties.field);
  }}
}}).addTo(map);

function colorForAnomaly(v) {{
  if (v === null || v === undefined || Number.isNaN(v)) return '#888888';
  if (v < 3.5) return '#22c55e';
  if (v < 7.0) return '#eab308';
  return '#dc2626';
}}
function colorForNDVI(v) {{
  if (v === null || v === undefined) return '#888888';
  var t = Math.min(Math.max(v, 0), 0.8) / 0.8;
  var r = Math.round(139 * (1 - t) + 34 * t);
  var g = Math.round(90 * (1 - t) + 139 * t);
  var b = Math.round(43 * (1 - t) + 34 * t);
  return 'rgb(' + r + ',' + g + ',' + b + ')';
}}
function colorForLST(v) {{
  if (v === null || v === undefined) return '#888888';
  var t = Math.min(Math.max((v - 300) / 30, 0), 1);
  var r = Math.round(220 * t);
  var g = Math.round(100 * (1 - t));
  var b = Math.round(220 * (1 - t));
  return 'rgb(' + r + ',' + g + ',' + b + ')';
}}
function colorForCWSI(v) {{
  if (v === null || v === undefined) return '#888888';
  var t = Math.min(Math.max(v, 0), 1);
  var r = Math.round(34 + 200 * t);
  var g = Math.round(139 * (1 - t));
  var b = Math.round(34 * (1 - t));
  return 'rgb(' + r + ',' + g + ',' + b + ')';
}}

function getColor(varName, v) {{
  if (varName === 'anomaly') return colorForAnomaly(v);
  if (varName === 'ndvi') return colorForNDVI(v);
  if (varName === 'lst') return colorForLST(v);
  if (varName === 'cwsi') return colorForCWSI(v);
  return '#888888';
}}

function getValue(varName, d) {{
  if (!d) return null;
  if (varName === 'anomaly') return d.anomaly;
  if (varName === 'ndvi') return d.ndvi;
  if (varName === 'lst') return d.lst;
  if (varName === 'cwsi') return d.cwsi;
  return null;
}}

var currentVar = 'anomaly';
var currentIdx = {initial_idx};

function updateMap() {{
  var ts = timestamps[currentIdx];
  var dateStr = dates[currentIdx];
  document.getElementById('date-label').textContent = dateStr;
  geoLayer.eachLayer(function(layer) {{
    var fid = String(layer.feature.properties.field);
    var d = data[fid] ? data[fid][String(ts)] : null;
    var v = getValue(currentVar, d);
    layer.setStyle({{ fillColor: getColor(currentVar, v), fillOpacity: 0.7 }});
    var sTxt = (d && d.anomaly !== null) ? d.anomaly.toFixed(2) : 'N/A';
    var nTxt = (d && d.ndvi !== null) ? d.ndvi.toFixed(3) : 'N/A';
    layer.setPopupContent('Field ' + fid + ' (' + dateStr + ')<br>S: ' + sTxt + '<br>NDVI: ' + nTxt);
  }});
  updateLegend();
}}

function updateLegend() {{
  var leg = document.getElementById('legend');
  var html = '<b>Legend: ' + currentVar + '</b><br>';
  if (currentVar === 'anomaly') {{
    html += '<div class="legend-item"><div class="legend-color" style="background:#22c55e"></div> &lt; 3.5 (normal)</div>';
    html += '<div class="legend-item"><div class="legend-color" style="background:#eab308"></div> 3.5 - 7.0 (moderate)</div>';
    html += '<div class="legend-item"><div class="legend-color" style="background:#dc2626"></div> &ge; 7.0 (anomaly)</div>';
    html += '<div class="legend-item"><div class="legend-color" style="background:#888888"></div> Unobserved / censored</div>';
  }} else if (currentVar === 'ndvi') {{
    html += '<div class="legend-item"><div class="legend-color" style="background:rgb(139,90,43)"></div> 0.0 (low)</div>';
    html += '<div class="legend-item"><div class="legend-color" style="background:rgb(34,139,34)"></div> 0.8 (high)</div>';
  }} else if (currentVar === 'lst') {{
    html += '<div class="legend-item"><div class="legend-color" style="background:rgb(0,100,220)"></div> 300 K (cool)</div>';
    html += '<div class="legend-item"><div class="legend-color" style="background:rgb(220,0,0)"></div> 330 K (hot)</div>';
  }} else if (currentVar === 'cwsi') {{
    html += '<div class="legend-item"><div class="legend-color" style="background:rgb(34,139,34)"></div> 0 (no stress)</div>';
    html += '<div class="legend-item"><div class="legend-color" style="background:rgb(234,0,0)"></div> 1 (high stress)</div>';
  }}
  leg.innerHTML = html;
}}

document.getElementById('time-slider').addEventListener('input', function() {{
  currentIdx = parseInt(this.value);
  updateMap();
}});
document.getElementById('var-select').addEventListener('change', function() {{
  currentVar = this.value;
  updateMap();
}});

updateMap();
</script>
</body>
</html>
"""

    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(html, encoding="utf-8")

    fields_changing_color = sum(
        1 for cols in color_series_by_field.values() if len(set(cols)) >= 2
    )
    total_transitions = sum(
        sum(1 for a, b in itertools.pairwise(cols) if a != b)
        for cols in color_series_by_field.values()
    )
    diagnostics = {
        "n_fields": int(len(fields)),
        "n_dates": int(len(dates)),
        "n_daily_records": int(len(daily)),
        "fields_with_color_changes": int(fields_changing_color),
        "total_color_transitions": int(total_transitions),
        "initial_date": dates[initial_idx],
    }
    return out_p, diagnostics


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate interactive daily anomaly map.")
    ap.add_argument("--zarr", default="data/processed/fields.zarr", type=Path)
    ap.add_argument("--daily", default="data/processed/daily_anomaly.parquet", type=Path)
    ap.add_argument("--fields", default=None, type=Path)
    ap.add_argument("--out", default=DEFAULT_OUT, type=Path)
    args = ap.parse_args()

    out_p, diag = build_custom_map(
        zarr_path=args.zarr,
        daily_path=args.daily,
        out_path=args.out,
        fields_path=args.fields,
    )
    print(f"Custom map saved to {out_p} | diagnostics={json.dumps(diag)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
