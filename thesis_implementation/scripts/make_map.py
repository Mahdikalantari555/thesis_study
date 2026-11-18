"""Create an interactive choropleth map of anomaly burden per field (Folium)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import geopandas as gpd
import folium

OUT = Path("reports/figures/anomaly_map.html")

scores = pd.read_parquet("data/processed/scores.parquet")
# aggregate burden per field (max over cycles)
agg = scores.groupby("field")["burden"].max().reset_index()
agg.columns = ["field", "max_burden"]

gdf = gpd.read_file("D:/RS/Thesis/Data/RoI/Farms_subset.geojson")
# field id mapping: use index+1 to match ingest field ids (1..32)
gdf = gdf.reset_index(drop=True)
gdf["field"] = gdf.index + 1
gdf = gdf.merge(agg, on="field", how="left")
gdf["max_burden"] = gdf["max_burden"].fillna(0)

# centroid for map center
center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]

m = folium.Map(location=center, zoom_start=12, tiles=None)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri World Imagery",
    name="Satellite",
    overlay=False,
    control=True,
).add_to(m)

folium.Choropleth(
    geo_data=gdf.__geo_interface__,
    name="Anomaly burden",
    data=gdf,
    columns=["field", "max_burden"],
    key_on="feature.properties.field",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name="Max anomaly burden per field",
).add_to(m)

# add popup with field id and burden
for _, row in gdf.iterrows():
    folium.Marker(
        location=[row.geometry.centroid.y, row.geometry.centroid.x],
        popup=f"Field {row['field']}: burden={row['max_burden']:.3f}",
        icon=folium.DivIcon(html=f"<div style='font-size:9px'>{row['field']}</div>"),
    ).add_to(m)

OUT.parent.mkdir(parents=True, exist_ok=True)
m.save(str(OUT))
print("Map saved to", OUT)
