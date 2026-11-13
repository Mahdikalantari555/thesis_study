# Spec Delta

## MODIFIED Requirements

### Requirement: On-the-fly raster tile serving

The system SHALL provide a local tile server (`scripts/serve_tiles.py`, stdlib HTTP, no new dependencies) that serves 256×256 PNG tiles per acquisition date at `GET /tiles/<date>/<rgb|ndvi>/<z>/<x>/<y>.png`, reprojecting the UTM scene rasters to Web Mercator (EPSG:3857) per request with `rasterio.vrt.WarpedVRT`, applying a percent stretch for RGB and a fixed green→yellow→brown colormap for NDVI, with nodata rendered transparent, opened datasets kept in a bounded LRU cache, and `GET /scenes` returning the scene index. The server SHALL remain alive and correct under the concurrent tile requests a browser map issues: shared raster handles SHALL be protected so parallel reads cannot corrupt data or crash the process, error responses to tile routes SHALL carry an image-compatible body (transparent PNG) instead of JSON, `HEAD` SHALL be supported for `/scenes` and tile routes, and tile responses SHALL include a `Cache-Control` header.

#### Scenario: Tile request

- **WHEN** the frontend requests a tile for an indexed date at a zoom level within 8–14
- **THEN** the server responds with a valid 256×256 PNG derived from that scene's GeoTIFF bands

#### Scenario: Zoom clamped to supported range

- **WHEN** a tile is requested outside zoom 8–14, or for an unknown date, layer or a scene missing the requested bands
- **THEN** the server responds 404 rather than rendering from wrong data

#### Scenario: Tiles outside the scene extent are transparent

- **WHEN** a requested tile does not intersect the scene footprint
- **THEN** the server returns a fully transparent PNG so the basemap shows through unchanged

#### Scenario: Concurrent browser load does not crash the server

- **WHEN** a browser map pans/zooms so that a dozen tile requests arrive in parallel
- **THEN** every request completes (valid PNG or image-compatible 404), the process stays alive, and a subsequent request still succeeds

#### Scenario: Error responses are image-safe

- **WHEN** a tile is requested for an unknown date or a zoom outside 8–14
- **THEN** the response uses status 404 with `Content-Type: image/png` and a transparent body, not JSON that browsers ORB-block

#### Scenario: HEAD is supported

- **WHEN** `HEAD /scenes` or `HEAD` on a tile route is issued
- **THEN** the server responds with the GET status and headers and no body

## ADDED Requirements

### Requirement: Overlay opacity persists across layer changes

The platform map SHALL apply the currently selected raster opacity to each newly mounted raster overlay, so switching scene date or layer type does not reset the overlay to full opacity.

#### Scenario: Opacity survives a layer switch

- **WHEN** the raster opacity is set to 0.7 and the user switches from RGB to NDVI (or to another scene date)
- **THEN** the new overlay renders at opacity 0.7 without the user moving the slider

### Requirement: Runtime page verification gate

The platform SHALL be verifiable end-to-end in a headless browser: every view renders with zero console errors and zero page exceptions under normal operation, and Map Explorer demonstrably renders Landsat RGB and NDVI tiles on the map with the tile server running and degrades gracefully (basemap + polygons intact) with it stopped.

#### Scenario: All views pass the audit

- **WHEN** the screenshot/console audit script runs over all views
- **THEN** each view reports zero console errors, zero page errors, and a saved screenshot

#### Scenario: Tile rendering evidence

- **WHEN** a scene date and the RGB layer are selected in Map Explorer with the tile server running
- **THEN** the requested tile URLs return PNGs and the composite is visibly rendered on the map; the same holds for NDVI
