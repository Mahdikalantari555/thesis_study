"""Local tile server for full-extent RGB / NDVI raster overlays.

Serves 256x256 PNG tiles reprojected on the fly from the raw Landsat scene
GeoTIFFs (UTM 39N) to Web Mercator (EPSG:3857) so Leaflet can overlay them on
the platform map:

    GET /tiles/<date>/<rgb|ndvi>/<z>/<x>/<y>.png   ->  image/png
    GET /scenes                                    ->  scene index JSON

Only stdlib http.server is used (no Flask/FastAPI); rasterio WarpedVRT does the
reprojection per tile request and open datasets are kept in an LRU cache so a
pan across one scene does not reopen the GeoTIFFs (design decision 1 / risk
mitigation in add-rgb-ndvi-tile-layer). Each cached dataset carries its own
lock held across GDAL reads, so the concurrent requests a browser map issues
cannot crash the process (wire-platform-to-real-data decision 1). Zoom is
clamped to 8-14; requests outside that range, unknown dates and unavailable
layers get a 404 with a transparent image/png body (never JSON, which <img>
consumers ORB-block), which the frontend treats as "tile absent" and renders
nothing (graceful degradation). HEAD is supported on all routes and successful
tiles carry Cache-Control: max-age=3600.

Usage:
    python scripts/serve_tiles.py \
        --scenes-dir D:/RS/Thesis/Data/Metric/scenes --port 8765
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import re
import sys
import threading
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

# rasterio emits a benign "GDAL_DATA is not defined" warning on this machine.
warnings.filterwarnings("ignore")

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_tile_index import build_index  # noqa: E402

TILE_SIZE = 256
MIN_Z, MAX_Z = 8, 14
# Web Mercator sphere: half-width of the EPSG:3857 world (metres).
WEB_MERC_HALF = math.pi * 6378137.0

LAYERS = ("rgb", "ndvi")
TILE_RE = re.compile(r"^/tiles/(\d{4}-\d{2}-\d{2})/(rgb|ndvi)/(\d+)/(\d+)/(\d+)\.png$")

# NDVI colormap: a fixed green -> yellow -> brown ramp, high NDVI = green.
# Stops are (ndvi value, rgb) and are linearly interpolated per channel.
NDVI_STOPS = [
    (-0.20, (110, 75, 45)),
    (0.05, (160, 115, 60)),
    (0.20, (215, 195, 105)),
    (0.35, (230, 220, 130)),
    (0.50, (150, 200, 110)),
    (0.70, (60, 150, 70)),
    (1.00, (25, 110, 50)),
]


def tile_bounds(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    """Web Mercator bounds (xmin, ymin, xmax, ymax) of a slippy-map tile."""
    n = 2**z
    res = 2 * WEB_MERC_HALF / n / TILE_SIZE
    xmin = -WEB_MERC_HALF + x * TILE_SIZE * res
    ymax = WEB_MERC_HALF - y * TILE_SIZE * res
    return xmin, ymax - TILE_SIZE * res, xmin + TILE_SIZE * res, ymax


class WarpedBand:
    """One band GeoTIFF plus its EPSG:3857 WarpedVRT (closed together).

    ``lock`` guards the GDAL handle itself: ThreadingHTTPServer serves one
    thread per request and a shared WarpedVRT read concurrently from two
    threads faults the whole process with a native access violation
    (0xC0000005). Every read of ``vrt`` holds this lock (wire-platform-to-
    real-data decision 1).
    """

    def __init__(self, path: Path):
        self.src = rasterio.open(path)
        self.vrt = WarpedVRT(self.src, crs="EPSG:3857", resampling=Resampling.bilinear)
        self.lock = threading.Lock()

    def close(self) -> None:
        try:
            self.vrt.close()
        finally:
            self.src.close()


class BandCache:
    """Thread-safe LRU cache of open WarpedVRTs, closed on eviction.

    The design calls for caching opened datasets because per-tile reopen is
    the main I/O cost; the cache is bounded so RAM stays predictable when the
    user pans across many scenes.
    """

    def __init__(self, maxsize: int):
        self.maxsize = maxsize
        self._entries: collections.OrderedDict[tuple[str, str], WarpedBand] = collections.OrderedDict()
        self._lock = threading.Lock()

    def get(self, scene_dir: Path, band: str) -> WarpedBand:
        key = (str(scene_dir), band)
        with self._lock:
            hit = self._entries.get(key)
            if hit is not None:
                self._entries.move_to_end(key)
                return hit
            opened = WarpedBand(scene_dir / f"{band}.tif")
            self._entries[key] = opened
            while len(self._entries) > self.maxsize:
                _, evicted = self._entries.popitem(last=False)
                self._close(evicted)
            return opened

    @staticmethod
    def _close(band: WarpedBand) -> None:
        # Take the band's read lock so an in-flight tile render finishes
        # before its GDAL handles are closed (lock order is always
        # cache lock -> band lock, so this cannot deadlock).
        with band.lock:
            try:
                band.close()
            except Exception:
                pass

    def close_all(self) -> None:
        with self._lock:
            while self._entries:
                _, evicted = self._entries.popitem()
                self._close(evicted)


class StretchStats:
    """Per-scene RGB percent stretch (lo/hi per band), shared by all tiles.

    Computing the 2-98% stretch per tile made neighbouring tiles normalise
    independently — visible brightness seams at every tile boundary. The
    stretch is now derived once per scene from a decimated full-scene read
    and reused for every tile of that scene (wire-platform-to-real-data
    follow-up: consistent RGB mosaic).
    """

    __slots__ = ("lo", "hi")

    def __init__(self, lo: dict[str, float], hi: dict[str, float]):
        self.lo = lo
        self.hi = hi


class SceneStretchCache:
    """Small thread-safe LRU of per-scene stretch statistics (8 scenes)."""

    def __init__(self, maxsize: int = 8):
        self.maxsize = maxsize
        self._entries: collections.OrderedDict[str, StretchStats] = collections.OrderedDict()
        self._lock = threading.Lock()

    def get(self, scene_dir: Path, band_cache: "BandCache") -> StretchStats:
        key = str(scene_dir)
        with self._lock:
            hit = self._entries.get(key)
            if hit is not None:
                self._entries.move_to_end(key)
                return hit
        stats = self._compute(scene_dir, band_cache)
        with self._lock:
            self._entries[key] = stats
            while len(self._entries) > self.maxsize:
                self._entries.popitem(last=False)
        return stats

    @staticmethod
    def _compute(scene_dir: Path, band_cache: "BandCache") -> StretchStats:
        # One decimated read of the whole warped scene per band: statistically
        # sufficient for a 2-98% stretch and computed once per scene.
        lo, hi = {}, {}
        for band in ("red", "green", "blue"):
            warped = band_cache.get(scene_dir, band)
            with warped.lock:
                sample = warped.vrt.read(1, out_shape=(512, 512), resampling=Resampling.bilinear, masked=True)
            arr = np.ma.filled(sample.astype("float64"), np.nan)
            vals = arr[np.isfinite(arr) & (arr > 0)]
            if vals.size:
                lo[band], hi[band] = (float(v) for v in np.percentile(vals, [2.0, 98.0]))
            else:
                lo[band], hi[band] = 0.0, 1.0
        return StretchStats(lo, hi)


def read_vrt_window(vrt, xmin: float, ymin: float, xmax: float, ymax: float) -> np.ndarray:
    """Read a 256x256 tile from a WarpedVRT as float64 with NaN outside.

    WarpedVRT forbids boundless reads, so the requested window is clipped to
    the VRT extent; the clipped part is read with decimated resampling and
    placed back into a NaN canvas at the correct fractional offset. Returns
    an all-NaN array for tiles that do not intersect the scene at all.
    """
    t = vrt.transform
    res_x, res_y = t.a, -t.e  # t.e is negative
    col = (xmin - t.c) / res_x
    row = (t.f - ymax) / res_y
    w = (xmax - xmin) / res_x
    h = (ymax - ymin) / res_y
    out = np.full((TILE_SIZE, TILE_SIZE), np.nan, dtype="float64")
    col0, row0 = max(col, 0.0), max(row, 0.0)
    col1, row1 = min(col + w, float(vrt.width)), min(row + h, float(vrt.height))
    if col1 <= col0 or row1 <= row0:
        return out
    fx0, fy0 = (col0 - col) / w, (row0 - row) / h
    fx1, fy1 = (col1 - col) / w, (row1 - row) / h
    sub_cols = max(1, round((fx1 - fx0) * TILE_SIZE))
    sub_rows = max(1, round((fy1 - fy0) * TILE_SIZE))
    win = Window(col_off=col0, row_off=row0, width=col1 - col0, height=row1 - row0)
    data = vrt.read(1, window=win, out_shape=(sub_rows, sub_cols), resampling=Resampling.bilinear, masked=True)
    arr = np.ma.filled(data.astype("float64"), np.nan)
    px0 = min(TILE_SIZE, max(0, round(fx0 * TILE_SIZE)))
    py0 = min(TILE_SIZE, max(0, round(fy0 * TILE_SIZE)))
    arr = arr[: TILE_SIZE - py0, : TILE_SIZE - px0]
    out[py0 : py0 + arr.shape[0], px0 : px0 + arr.shape[1]] = arr
    return out


def _apply_colormap(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Map NDVI values through NDVI_STOPS into an RGB uint8 HxWx3 array."""
    clipped = np.clip(values, NDVI_STOPS[0][0], NDVI_STOPS[-1][0])
    stop_vals = [s[0] for s in NDVI_STOPS]
    rgb = np.zeros((TILE_SIZE, TILE_SIZE, 3), dtype="uint8")
    for ch in range(3):
        ramp = np.array([s[1][ch] for s in NDVI_STOPS], dtype="float64")
        mapped = np.interp(clipped, stop_vals, ramp)
        rgb[..., ch] = np.where(valid, mapped.astype("uint8"), 0)
    return rgb


def render_rgb(bands: dict[str, np.ndarray], stretch: StretchStats | None = None) -> np.ndarray:
    """256x256x4 RGBA uint8 from red/green/blue reflectance.

    With ``stretch`` (the per-scene statistics from SceneStretchCache) every
    tile of a scene shares one contrast window — no seams between neighbouring
    tiles. Without it, the stretch falls back to per-tile percentiles (only
    used by tests).
    """
    valid = np.ones((TILE_SIZE, TILE_SIZE), dtype=bool)
    for name in ("red", "green", "blue"):
        arr = bands[name]
        valid &= np.isfinite(arr) & (arr > 0)
    rgb = np.zeros((TILE_SIZE, TILE_SIZE, 4), dtype="uint8")
    if valid.any():
        for i, name in enumerate(("red", "green", "blue")):
            if stretch is not None:
                lo, hi = stretch.lo[name], stretch.hi[name]
            else:
                arr_v = bands[name][valid]
                lo, hi = (float(v) for v in np.percentile(arr_v, [2.0, 98.0]))
            scaled = np.clip((bands[name] - lo) / max(hi - lo, 1e-9), 0.0, 1.0)
            rgb[..., i] = np.where(valid, (scaled * 255).astype("uint8"), 0)
    rgb[..., 3] = np.where(valid, 255, 0)
    return rgb


def render_ndvi(bands: dict[str, np.ndarray]) -> np.ndarray:
    """256x256x4 RGBA uint8 NDVI tile: (nir - red) / (nir + red), fixed ramp."""
    red, nir = bands["red"], bands["nir08"]
    valid = np.isfinite(red) & np.isfinite(nir) & (red > 0) & (nir > 0)
    ndvi = np.zeros((TILE_SIZE, TILE_SIZE), dtype="float64")
    ndvi[valid] = (nir[valid] - red[valid]) / np.maximum(nir[valid] + red[valid], 1e-9)
    rgb = np.zeros((TILE_SIZE, TILE_SIZE, 4), dtype="uint8")
    rgb[..., :3] = _apply_colormap(ndvi, valid)
    rgb[..., 3] = np.where(valid, 255, 0)
    return rgb


def encode_png(rgba: np.ndarray) -> bytes:
    """Encode an HxWx4 uint8 array as PNG via rasterio's MemoryFile driver."""
    with rasterio.MemoryFile() as mem:
        with mem.open(driver="PNG", width=TILE_SIZE, height=TILE_SIZE, count=4, dtype="uint8") as dst:
            dst.write(np.transpose(rgba, (2, 0, 1)))
        return mem.read()


# Fully transparent 256x256 PNG: the body of every tile-route error response.
# Leaflet loads tiles via <img>, so JSON error bodies get ORB-blocked
# (net::ERR_BLOCKED_BY_ORB); an image-typed transparent body renders as
# "tile absent" instead (wire-platform-to-real-data decision 2).
TRANSPARENT_TILE_PNG = encode_png(np.zeros((TILE_SIZE, TILE_SIZE, 4), dtype="uint8"))


class TileRequestHandler(BaseHTTPRequestHandler):
    server_version = "AgriTileServer/1.1"
    protocol_version = "HTTP/1.1"

    # Populated by serve() on the server object.
    scenes_by_date: dict[str, list[dict]] = {}
    scenes_dir: Path | None = None
    cache: BandCache | None = None
    stretch_cache: SceneStretchCache | None = None
    index_payload: bytes = b""

    def _send(self, status: int, body: bytes, content_type: str, cacheable: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # Allow fetch() from the vite dev origin (tiles are plain <img> for Leaflet).
        self.send_header("Access-Control-Allow-Origin", "*")
        if cacheable:
            # Scenes are immutable once written, so browsers/Leaflet may reuse
            # a tile for an hour instead of re-requesting on every pan.
            self.send_header("Cache-Control", "max-age=3600")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_json(self, status: int, payload) -> None:
        self._send(status, json.dumps(payload).encode("utf-8"), "application/json")

    def _send_tile_error(self, status: int, reason: str) -> None:
        # Tile routes are consumed by <img>: answer with a transparent PNG so
        # the browser treats it as "tile absent" instead of ORB-blocking a
        # JSON body. The reason is only logged server-side.
        print(f"[serve_tiles] {status} {self.path} ({reason})", flush=True)
        self._send(status, TRANSPARENT_TILE_PNG, "image/png")

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        self._handle_request()

    def do_HEAD(self) -> None:  # noqa: N802 (http.server API)
        # Mirror GET status and headers with no body (Content-Length is still
        # sent, as HEAD semantics require).
        self._handle_request()

    def _handle_request(self) -> None:
        path = urlparse(self.path).path
        if path == "/scenes":
            self._send(200, self.index_payload, "application/json")
            return
        match = TILE_RE.match(path)
        if not match:
            self._send_json(404, {"error": "not found", "path": path})
            return
        date, layer, zs, xs, ys = match.groups()
        z, x, y = int(zs), int(xs), int(ys)
        if not (MIN_Z <= z <= MAX_Z):
            self._send_tile_error(404, f"zoom {z} outside {MIN_Z}-{MAX_Z}")
            return
        candidates = self.scenes_by_date.get(date, [])
        if not candidates:
            self._send_tile_error(404, f"unknown scene date {date}")
            return
        scene = next((s for s in candidates if s.get(f"has_{layer}")), None)
        if scene is None:
            self._send_tile_error(404, f"scene {date} has no {layer} bands")
            return
        try:
            png = self._render_tile(scene["dir"], date, layer, z, x, y)
        except FileNotFoundError as exc:
            self._send_tile_error(404, f"missing band file: {exc}")
            return
        except Exception as exc:  # pragma: no cover — defensive, keeps server alive
            self._send_tile_error(500, f"{type(exc).__name__}: {exc}")
            return
        self._send(200, png, "image/png", cacheable=True)

    def _render_tile(self, scene_dir: Path, date: str, layer: str, z: int, x: int, y: int) -> bytes:
        xmin, ymin, xmax, ymax = tile_bounds(z, x, y)
        band_names = ("red", "green", "blue") if layer == "rgb" else ("red", "nir08")
        bands = {}
        for band in band_names:
            warped = self.cache.get(scene_dir, band)  # type: ignore[union-attr]
            # Hold the handle's own lock across the GDAL read: concurrent
            # reads on one shared WarpedVRT crash the process (0xC0000005).
            with warped.lock:
                bands[band] = read_vrt_window(warped.vrt, xmin, ymin, xmax, ymax)
        if layer == "rgb":
            # Scene-shared contrast window: neighbouring tiles must agree.
            stretch = self.stretch_cache.get(scene_dir, self.cache)  # type: ignore[union-attr]
            rgba = render_rgb(bands, stretch)
        else:
            rgba = render_ndvi(bands)
        return encode_png(rgba)

    def log_message(self, fmt: str, *args) -> None:
        # Minimal one-line request log on stdout.
        print(f"[serve_tiles] {self.address_string()} {fmt % args}", flush=True)


def load_scenes(scenes_dir: Path, index_path: Path) -> list[dict]:
    """Load the manifest (fast path) or build it, attaching absolute dirs."""
    if index_path.exists():
        manifest = json.loads(index_path.read_text(encoding="utf-8"))
        print(f"[serve_tiles] loaded {index_path}", flush=True)
    else:
        manifest = build_index(scenes_dir)
        print("[serve_tiles] scenes_index.json missing — built index in-process", flush=True)
    scenes = []
    for entry in manifest.get("scenes", []):
        scene = dict(entry)
        # "path" is the design-format anchor path; the actual rasters live in
        # scenes_dir/<last component> regardless of where the manifest came from.
        scene["dir"] = scenes_dir / Path(entry["path"]).name
        scenes.append(scene)
    return scenes


def serve(host: str, port: int, scenes_dir: Path, cache_size: int, index_path: Path) -> None:
    scenes = load_scenes(scenes_dir, index_path)
    by_date: dict[str, list[dict]] = collections.defaultdict(list)
    for scene in scenes:
        by_date[scene["date"]].append(scene)
    print(f"[serve_tiles] {len(scenes)} scenes, {len(by_date)} dates, cache={cache_size} bands", flush=True)

    TileRequestHandler.scenes_by_date = dict(by_date)
    TileRequestHandler.scenes_dir = scenes_dir
    TileRequestHandler.cache = BandCache(cache_size)
    TileRequestHandler.stretch_cache = SceneStretchCache()
    TileRequestHandler.index_payload = json.dumps({"scenes": [{k: v for k, v in s.items() if k != "dir"} for s in scenes]}).encode("utf-8")

    server = ThreadingHTTPServer((host, port), TileRequestHandler)
    server.daemon_threads = True
    print(f"[serve_tiles] listening on http://{host}:{port}/tiles/<date>/<rgb|ndvi>/<z>/<x>/<y>.png", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        TileRequestHandler.cache.close_all()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scenes-dir", default="D:/RS/Thesis/Data/Metric/scenes")
    ap.add_argument("--index", default=str(repo_root / "platform/src/data/scenes_index.json"), help="existing manifest to serve from /scenes")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--cache-size", type=int, default=32, help="LRU size in open band datasets")
    args = ap.parse_args()
    serve(args.host, args.port, Path(args.scenes_dir), args.cache_size, Path(args.index))


if __name__ == "__main__":
    sys.exit(main())
