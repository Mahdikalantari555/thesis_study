#!/usr/bin/env python3
"""Interactive Folium time-slider map using per-date daily_anomaly.parquet."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import folium
import pandas as pd
import xarray as xr
from folium.plugins import TimeSliderChoropleth
from make_map_custom import anomaly_color, load_fields_gdf

OUT = Path("reports/figures/anomaly_timeslider.html")


def main() -> int:
    daily = pd.read_parquet("data/processed/daily_anomaly.parquet")
    ds = xr.open_zarr("data/processed/fields.zarr")
    fields = ds.coords["field"].values

    if daily.empty:
        print("No daily anomaly records")
        return 1

    styledict: dict[str, dict[str, dict]] = {}
    for fid, sub in daily.groupby("field"):
        styledict[str(int(fid))] = {}
        for _, r in sub.iterrows():
            ts = int(pd.Timestamp(str(r["date"])[:10]).timestamp())
            styledict[str(int(fid))][str(ts)] = {
                "color": anomaly_color(float(r["anomaly"])),
                "opacity": 0.7,
            }

    gdf = load_fields_gdf(fields)
    bounds = gdf.total_bounds
    center = [float(0.5 * (bounds[1] + bounds[3])), float(0.5 * (bounds[0] + bounds[2]))]
    geojson = json.loads(gdf.to_json())
    for feat in geojson["features"]:
        feat["id"] = str(feat["properties"]["field"])

    m = folium.Map(location=center, zoom_start=13, tiles=None)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite",
        overlay=False,
        control=True,
    ).add_to(m)

    TimeSliderChoropleth(
        data=geojson,
        styledict=styledict,
        name="Daily anomaly over time",
    ).add_to(m)

    folium.LayerControl().add_to(m)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(OUT))
    print("Time-slider map saved to", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
