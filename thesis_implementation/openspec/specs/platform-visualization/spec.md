# platform-visualization Specification

## Purpose
Defines how the platform map renders full-extent RGB and NDVI raster overlays from the frozen Landsat Collection-2 GeoTIFF scenes via a local, on-the-fly tile serving layer, and which artifacts guarantee the frontend only offers dates that actually exist on disk.

## Requirements

### Requirement: Scene index manifest

The system SHALL generate `platform/src/data/scenes_index.json` by scanning the Landsat scene directories, listing every scene with its acquisition date (parsed from MTL.json, falling back to the `landsat_YYYYMMDD_*` directory name), anchor-relative path, EPSG:4326 bounds, band list in canonical order, and `has_rgb`/`has_ndvi` flags, sorted deterministically by date.

#### Scenario: Scene index structure

- **WHEN** `scripts/build_tile_index.py` scans the scenes directory
- **THEN** it emits a JSON object with a `scenes` array whose entries carry exactly `date`, `path`, `bounds` (`[xmin, ymin, xmax, ymax]` in EPSG:4326), `bands`, `has_rgb` and `has_ndvi`, in date order

#### Scenario: Date falls back to the directory name

- **WHEN** a scene's MTL.json is missing or unparseable
- **THEN** the acquisition date is derived from the `landsat_YYYYMMDD_PPP_RRR` directory name instead, so the scene is not silently dropped

#### Scenario: Band flags reflect reality

- **WHEN** a scene directory lacks one or more of the red/green/blue or red/nir08 band GeoTIFFs
- **THEN** the corresponding `has_rgb`/`has_ndvi` flag is `false` and the frontend does not offer that product for that date

### Requirement: On-the-fly raster tile serving

The system SHALL provide a local tile server (`scripts/serve_tiles.py`, stdlib HTTP, no new dependencies) that serves 256×256 PNG tiles per acquisition date at `GET /tiles/<date>/<rgb|ndvi>/<z>/<x>/<y>.png`, reprojecting the UTM scene rasters to Web Mercator (EPSG:3857) per request with `rasterio.vrt.WarpedVRT`, applying a percent stretch for RGB and a fixed green→yellow→brown colormap for NDVI, with nodata rendered transparent, opened datasets kept in a bounded LRU cache, and `GET /scenes` returning the scene index.

#### Scenario: Tile request

- **WHEN** the frontend requests a tile for an indexed date at a zoom level within 8–14
- **THEN** the server responds with a valid 256×256 PNG derived from that scene's GeoTIFF bands

#### Scenario: Zoom clamped to supported range

- **WHEN** a tile is requested outside zoom 8–14, or for an unknown date, layer or a scene missing the requested bands
- **THEN** the server responds 404 rather than rendering from wrong data

#### Scenario: Tiles outside the scene extent are transparent

- **WHEN** a requested tile does not intersect the scene footprint
- **THEN** the server returns a fully transparent PNG so the basemap shows through unchanged

### Requirement: Frontend raster overlay controls

The platform map (`MapExplorer.tsx` / `MapView.tsx`) SHALL expose a scene/date selector populated from `scenes_index.json`, a raster layer toggle (None / RGB / NDVI), and a raster opacity slider (0–1), and SHALL mount a Leaflet `TileLayer` pointing at the local tile server URL only while a scene and layer are selected.

#### Scenario: Layer toggle

- **WHEN** the user selects a scene date and the NDVI layer
- **THEN** the map renders the NDVI tile overlay at the chosen opacity beneath the field polygons, which remain visible and interactive

#### Scenario: Overlay is opt-in

- **WHEN** no scene date is selected (or the layer is None)
- **THEN** no tile layer is mounted and the map shows exactly the pre-existing field-polygon behaviour

### Requirement: Graceful degradation without the tile server

The platform SHALL keep rendering field polygons, basemap and time series when the local tile server is not running; tile load failures SHALL be silent and SHALL NOT crash or obscure the rest of the map.

#### Scenario: Tile server down

- **WHEN** the local tile server is not running while a raster scene is selected
- **THEN** tile requests fail silently (`errorTileUrl` empty, no unhandled errors), and the map still renders the basemap, field polygons and all other views
