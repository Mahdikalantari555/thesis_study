"""Export 32×32 patch store (``patches.zarr``) from Landsat scenes.

Change ``patch-data-pipeline`` task 2.1.

The scene/QA/scale handling is the SAME code the field-level export uses
(:mod:`ssl_anomaly.io.landsat`: ``quality_mask`` / ``apply_scale_sr`` /
``apply_scale_st`` with ``QualityCfg``), so a pixel in a patch and a pixel in
``stats.zarr`` mean the same thing. Geometry, binning and store writing come
from :mod:`ssl_anomaly.io.patches`.

Design notes that matter for correctness:

* **No resampling.** Every read is a windowed crop of the source raster; a
  field smaller than the patch is padded with NaN and its ``in_field`` mask
  says which pixels are real. Neighbouring fields inside the bounding box are
  excluded by the polygon mask, not by cropping the bbox.
* **Field-major, windowed reads.** The store is chunked one (field, cycle) at
  a time, so the driver iterates fields → cycles → the scenes of that cycle and
  reads only the field's 32×32 window per band. Scene-major iteration would
  either rewrite the same chunk once per scene (cost) or hold hundreds of MB of
  patches (memory).
* **Resume at field granularity** through ``.manifest.jsonl``. A partially
  written field is re-done, never half-trusted: the manifest line is appended
  only after the field's chunks are flushed and its content hash recorded.
* **Nothing is fabricated.** A bin with no valid acquisition is written as NaN
  with ``pixel_valid = 0``; a missing scene directory is counted, not skipped
  silently.

Usage (the owner runs these — a full run is hours long):

    python scripts/extract_patches.py --estimate-runtime
    python scripts/extract_patches.py --smoke 3
    python scripts/extract_patches.py --resume
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import date as _date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from ssl_anomaly.io import patches as P  # noqa: E402
from ssl_anomaly.io.landsat import (  # noqa: E402
    apply_scale_sr,
    apply_scale_st,
    quality_mask,
)
from ssl_anomaly.monitor import splits as msplits  # noqa: E402

# ONE_DEGREE default source-resolution (m) for the runtime estimate.
PIXEL_SIZE_M = 30.0
# Seconds for one scene open + one 32x32 window read per band. Measured
# conservatively from the field-level exporter; used ONLY by --estimate-runtime.
SEC_PER_SCENE_READ = 0.004
SEC_PER_FIELD_FLUSH = 0.05

SR_FILE_MAP = {
    "blue": "blue.tif", "green": "green.tif", "red": "red.tif",
    "nir": "nir08.tif", "swir1": "swir16.tif", "swir2": "swir22.tif",
}
ST_FILE_MAP = {"lst": "lwir11.tif"}


# ---------------------------------------------------------------------------
# Cycles and binning (pure)
# ---------------------------------------------------------------------------
def load_cycles(path: str | Path, *, require_cycle_ids: bool = False) -> np.ndarray:
    """Return non-censored (field, stable cycle_id, start, last data day) rows.

    The cycle table is half-open, matching the zonal/baseline builders:
    the stored inclusive data bound is ``t_end - 1``.
    """
    import pandas as pd

    df = pd.read_parquet(path)
    need = {"field", "t_start", "t_end"}
    if require_cycle_ids:
        need.add("cycle_id")
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns {sorted(missing)}")
    if "censored" in df.columns:
        df = df[~df["censored"].astype(bool)]
    if df.empty:
        raise ValueError(f"{path} has no usable (non-censored) cycles")
    df = df.sort_values(["field", "t_start"])
    if "cycle_id" not in df:
        df = df.assign(cycle_id=df.groupby("field").cumcount())  # unbound fixture stores only
    columns = ["field", "cycle_id", "t_start", "t_end"]
    values = df[columns].to_numpy()
    if not np.isfinite(values).all() or not np.equal(values, values.astype(np.int64)).all():
        raise ValueError(f"{path} has invalid cycle identifiers or date offsets")
    if np.any(values[:, 3] <= values[:, 2]) or df.duplicated(["field", "cycle_id"]).any():
        raise ValueError(f"{path} has inverted bounds or duplicate (field, cycle_id) pairs")
    values = values.astype(np.int64)
    values[:, 3] -= 1
    return values


def bin_of_day(day: int, cycle_start_day: int, *, bin_days: int = P.BIN_DAYS,
               n_bins: int = P.N_BINS) -> int:
    """Bin index of an acquisition, or ``-1`` when outside the cycle window.

    This grid is half-open on the right. The exporter also clips scenes to the
    actual source-cycle interval, which can end before the grid does.
    """
    dsh = int(day) - int(cycle_start_day)
    if dsh < 0 or dsh >= bin_days * n_bins:
        return -1
    return int(dsh // bin_days)


def assign_bins(days: np.ndarray, cycle_start_day: int, **kw) -> np.ndarray:
    """Vectorised :func:`bin_of_day` over acquisition days."""
    bins = np.full(len(days), -1, dtype=np.int16)
    for i, d in enumerate(days):
        bins[i] = bin_of_day(int(d), cycle_start_day, **kw)
    return bins


def ndvi_from_red_nir(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """NDVI with the project's NaN discipline (no silent zeros)."""
    r = np.asarray(red, dtype=np.float32)
    n = np.asarray(nir, dtype=np.float32)
    denom = n + r
    out = np.full(r.shape, np.nan, dtype=np.float32)
    ok = np.isfinite(denom) & (np.abs(denom) > 1e-6) & np.isfinite(r) & np.isfinite(n)
    out[ok] = (n[ok] - r[ok]) / denom[ok]
    return out


def infer_band_scale(red: np.ndarray) -> str:
    """Decide whether a scene's pixels are reflectance or raw DN.

    The archive holds both kinds of product (``extract_stats.py`` reads the
    pre-scaled ``*.tif`` files as-is, while ``io/landsat.load_scene`` applies
    the C2 L2 factors to ``SR_B*.TIF``), and applying the factors to already
    scaled reflectance NaNs every pixel (``apply_scale_sr`` treats DN > 1.6 as
    saturated). So the choice is made from the data and RECORDED rather than
    assumed: surface reflectance of vegetation sits within [0, 1.2], raw DN in
    the thousands.
    """
    r = np.asarray(red, dtype=np.float64)
    r = r[np.isfinite(r)]
    if r.size == 0:
        return "unknown"
    return "reflectance" if float(np.median(r)) <= 2.0 else "dn"


def stack_channels(bands: dict[str, np.ndarray], *, size: int = P.DEFAULT_PATCH_SIZE) -> np.ndarray:
    """Assemble ``(C, S, S)`` in ``P.CHANNELS`` order; missing channels are NaN.

    A missing band is NaN for EVERY pixel — never a zero-filled channel, which
    would look like a real reflectance of 0 and enter the per-pixel median.
    """
    out = np.full((P.N_CHANNELS, size, size), np.nan, dtype=np.float32)
    if "red" in bands and "nir" in bands:
        out[P.CHANNELS.index("ndvi")] = ndvi_from_red_nir(bands["red"], bands["nir"])
    for ci, name in enumerate(P.CHANNELS):
        if name == "ndvi":
            continue
        if name in bands:
            out[ci] = bands[name]
    return out


# ---------------------------------------------------------------------------
# Scene discovery (pure apart from glob)
# ---------------------------------------------------------------------------
def scene_date_from_dir(path: Path) -> _date | None:
    """Acquisition date of a scene directory (``landsat_YYYYMMDD_*``)."""
    name = Path(path).name
    for token in name.split("_"):
        if len(token) == 8 and token.isdigit():
            try:
                return _date(int(token[:4]), int(token[4:6]), int(token[6:8]))
            except ValueError:
                return None
    return None


def discover_scenes(scenes_root: str | Path, *, sensor: str | None = None) -> list[tuple[_date, Path]]:
    """All scene directories with a parseable date, sorted by date then name."""
    out: list[tuple[_date, Path]] = []
    for p in sorted(Path(scenes_root).glob("landsat_*")):
        if not p.is_dir():
            continue
        d = scene_date_from_dir(p)
        if d is None:
            continue
        out.append((d, p))
    out.sort(key=lambda t: (t[0], t[1].name))
    return out


def sensor_of(path: Path) -> str:
    """Sensor family from the scene id (``LC08`` → L8, ``LC09`` → L9)."""
    name = Path(path).name.upper()
    if "LC08" in name or "_L8" in name:
        return "L8"
    if "LC09" in name or "_L9" in name:
        return "L9"
    return "unknown"


def find_band_file(scene_dir: Path, band: str) -> Path | None:
    """Locate a band TIF inside a scene directory, exact name first."""
    exact = scene_dir / (SR_FILE_MAP.get(band) or ST_FILE_MAP.get(band) or "")
    if exact.is_file():
        return exact
    want_qa = band.lower().startswith("qa")
    for cand in sorted(scene_dir.glob("*")):
        if cand.suffix.lower() not in (".tif", ".tiff"):
            continue
        stem = cand.stem.lower()
        if band.lower() not in stem:
            continue
        # A band search must not match the QA raster and vice versa (the QA
        # name contains no band token, but "red" is a substring of nothing
        # else — the guard is on the QA side, which DOES contain "qa").
        if want_qa != ("qa" in stem):
            continue
        return cand
    return None


# ---------------------------------------------------------------------------
# Windowed read (pure w.r.t. the rasterio dataset)
# ---------------------------------------------------------------------------
def read_window(
    src,
    window: P.FieldWindow,
    *,
    fill: float = np.nan,
    dtype: np.dtype | str = np.float32,
) -> np.ndarray:
    """Read ``window`` from an open rasterio dataset into a padded patch.

    Uses a windowed read of the intersecting region only, then places it at the
    window's padding offset — the same contract as
    :func:`ssl_anomaly.io.patches.crop_and_pad`, but without materialising the
    full raster. Regions outside the raster stay ``fill`` (NaN), including
    negative origins at the raster edge.
    """
    out = np.full((window.size, window.size), fill, dtype=dtype)
    r0, c0 = window.row0, window.col0
    r_lo, c_lo = max(0, -r0), max(0, -c0)
    r_hi = min(window.height, src.height - r0)
    c_hi = min(window.width, src.width - c0)
    if r_hi <= r_lo or c_hi <= c_lo:
        return out
    import rasterio.windows as rw

    win = rw.Window(
        col_off=c0 + c_lo, row_off=r0 + r_lo,
        width=c_hi - c_lo, height=r_hi - r_lo,
    )
    block = src.read(1, window=win)
    out[
        window.pad_top + r_lo : window.pad_top + r_hi,
        window.pad_left + c_lo : window.pad_left + c_hi,
    ] = block.astype(dtype, copy=False)
    return out


def read_scene_patch(
    scene_dir: Path,
    window: P.FieldWindow,
    *,
    qcfg=None,
    sensor: str = "unknown",
    band_scale: str = "native",
) -> tuple[np.ndarray, np.ndarray]:
    """Load one scene's bands clipped to a field window.

    Returns ``(values (C,S,S), valid (S,S))``. The QA decision is always the
    shared landsat helper.

    ``band_scale``:
    ``native``  — use the stored values (the export that produced
                  ``stats.zarr`` does this; the shipped ``*.tif`` scenes are
                  already reflectance/Kelvin).
    ``landsat`` — apply the Landsat C2 L2 scale/offset first (raw DN scenes).
    ``auto``    — :func:`infer_band_scale` decides from this scene's red band,
                  which is per-scene so a mixed archive cannot silently
                  corrupt half the store.
    """
    import rasterio

    from ssl_anomaly.config import QualityCfg

    qcfg = qcfg or QualityCfg()
    qa_path = find_band_file(scene_dir, "qa_pixel")
    if qa_path is None:
        cands = sorted(list(scene_dir.glob("*QA_PIXEL*")) + list(scene_dir.glob("*qa_pixel*")))
        qa_path = cands[0] if cands else None
    bands: dict[str, np.ndarray] = {}
    valid = np.zeros((window.size, window.size), dtype=bool)
    if qa_path is not None:
        with rasterio.open(qa_path) as src:
            qa = read_window(src, window, fill=1, dtype=np.uint16)
        # fill=1 sets the QA "fill" bit, so out-of-raster pixels are invalid.
        valid = quality_mask(qa, qcfg)
    if band_scale not in ("native", "landsat", "auto"):
        raise ValueError(f"unknown band_scale {band_scale!r}")

    def _load(path: Path, fill: float, dtype) -> np.ndarray:
        with rasterio.open(path) as src:
            return read_window(src, window, fill=fill, dtype=dtype)

    red_path = find_band_file(scene_dir, "red")
    mode = band_scale
    if mode == "auto":
        mode = ("landsat" if red_path is not None
                and infer_band_scale(_load(red_path, np.nan, np.float32)) == "dn" else "native")

    for band in SR_FILE_MAP:
        path = find_band_file(scene_dir, band)
        if path is None:
            continue
        if mode == "landsat":
            bands[band] = apply_scale_sr(_load(path, 0, np.int32), 0.0000275, -0.2)
        else:
            bands[band] = _load(path, np.nan, np.float32)
    for band in ST_FILE_MAP:
        path = find_band_file(scene_dir, band)
        if path is None:
            continue
        if mode == "landsat":
            bands[band] = apply_scale_st(_load(path, 0, np.int32), 0.00341802, 149.0)
        else:
            bands[band] = _load(path, np.nan, np.float32)
    values = stack_channels(bands, size=window.size)
    if qa_path is None:
        # No QA raster at all: fall back to "any finite band", and only then.
        # Applying this fallback when QA EXISTS would resurrect a fully cloudy
        # acquisition as valid — the opposite of what QA is for.
        valid = np.isfinite(values).any(axis=0)
    return values, valid


# ---------------------------------------------------------------------------
# Runtime estimate + manifest
# ---------------------------------------------------------------------------
def day_index(day: _date, epoch: _date) -> int:
    """Days since the archive epoch.

    ``cycles.parquet`` stores ``t_start`` as an OFFSET from the archive's first
    observation, while a scene's date is an absolute day. Comparing the two
    without this conversion silently shifts every cycle by ~40 years and
    extracts into the wrong bins — every bin then looks empty instead of the
    run failing loudly.
    """
    return (day - epoch).days


def estimate_runtime(
    n_fields: int,
    cycles: np.ndarray,
    scenes: list[tuple[_date, Path]],
    *,
    epoch: _date | None = None,
    n_bands: int = 7,
) -> dict:
    """Estimate a full run WITHOUT reading a single raster.

    Counts (field, cycle, scene) triples whose date falls inside the cycle and
    multiplies by the measured per-window-read and per-flush costs. The number
    is deliberately pessimistic: the point is to decide whether a full run fits
    in a night, not to be accurate to the minute.
    """
    by_field: dict[int, list[tuple[int, int]]] = {}
    for fid, _cid, start, end in cycles:
        by_field.setdefault(int(fid), []).append((int(start), int(end)))
    if epoch is None:
        epoch = min((d for d, _p in scenes), default=None)
    if epoch is None:
        return {"n_fields": int(n_fields), "n_scenes": 0, "n_window_reads": 0,
                "estimated_seconds": 0.0, "estimated_minutes": 0.0,
                "assumptions": {"note": "no scenes"}}
    days = np.array([day_index(d, epoch) for d, _p in scenes], dtype=np.int64)
    n_reads = 0
    for spans in by_field.values():
        for start, end in spans:
            last = min(end, start + P.BIN_DAYS * P.N_BINS - 1)
            nb = int(np.sum((days >= start) & (days <= last)))
            n_reads += nb * (n_bands + 1)               # + QA
    sec = n_reads * SEC_PER_SCENE_READ + len(by_field) * SEC_PER_FIELD_FLUSH
    return {
        "n_fields": int(n_fields),
        "n_scenes": len(scenes),
        "n_window_reads": int(n_reads),
        "epoch": epoch.isoformat(),
        "estimated_seconds": round(float(sec), 1),
        "estimated_minutes": round(float(sec) / 60.0, 1),
        "assumptions": {
            "sec_per_window_read": SEC_PER_SCENE_READ,
            "sec_per_field_flush": SEC_PER_FIELD_FLUSH,
            "bands_read_per_scene": n_bands + 1,
        },
    }


def manifest_path(store: Path) -> Path:
    return Path(store) / P.MANIFEST_NAME


def read_manifest(store: Path) -> list[dict]:
    """Read the resume manifest; a corrupt line voids the whole manifest.

    Silently skipping an unparseable line could mark a field as "not done" —
    harmless — but could also hide a torn write. Refusing is the safe direction,
    because the caller then re-extracts the field.
    """
    path = manifest_path(store)
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if "field_id" not in rec:
            raise ValueError(f"{path}: manifest line without field_id")
        out.append(rec)
    return out


def done_fields(store: Path) -> set[int]:
    return {int(r["field_id"]) for r in read_manifest(store)}


def append_manifest(store: Path, **record) -> None:
    """Append one completed-field record (flushed immediately)."""
    path = manifest_path(store)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def field_content_sha256(values: np.ndarray) -> str:
    """Content hash of one field's patch values (NaN-safe, deterministic)."""
    a = np.asarray(values, dtype=np.float32)
    h = hashlib.sha256()
    h.update(str(a.shape).encode())
    h.update(np.nan_to_num(a, nan=-9999.0).tobytes())
    return h.hexdigest()


def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
            check=True,
        ).stdout.strip()
    except Exception:  # pragma: no cover - no git in a wheel install
        return "unknown"


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def export_field(
    root,
    fi: int,
    field_id: int,
    *,
    mask: np.ndarray,
    cycles_of_field: list[tuple[int, int, int]],
    scenes_by_day: dict[int, Path],
    size: int,
    window: P.FieldWindow,
    in_field: np.ndarray,
    band_scale: str = "auto",
) -> dict:
    """Extract and write one field's patches. Returns a summary record."""
    t0 = time.time()
    field_values = np.full(
        (len(cycles_of_field), P.N_BINS, P.N_CHANNELS, size, size), np.nan, dtype=np.float32,
    )
    n_scenes_used = 0
    for ci, (_cid, start, end) in enumerate(cycles_of_field):
        per_bin: dict[int, list[tuple[np.ndarray, np.ndarray, str]]] = {}
        for dsh_bin in range(P.N_BINS):
            per_bin[dsh_bin] = []
        for day_idx, scene_dir in scenes_by_day.items():
            b = bin_of_day(day_idx, start, n_bins=P.N_BINS)
            if b < 0 or day_idx > end:
                continue
            values, valid = read_scene_patch(
                scene_dir, window, sensor=sensor_of(scene_dir), band_scale=band_scale,
            )
            per_bin[b].append((values, valid, sensor_of(scene_dir)))
            n_scenes_used += 1
        for b in range(P.N_BINS):
            entries = per_bin[b]
            if not entries:
                empty = P.aggregate_bin([], [], in_field=in_field)
                root["values"][fi, ci, b] = empty.values
                root["pixel_valid"][fi, ci, b, 0] = empty.pixel_valid
                root["n_obs"][fi, ci, b] = 0
                root["sensor_id"][fi, ci, b] = P.SENSOR_IDS["unknown"]
                continue
            agg = P.aggregate_bin(
                [e[0] for e in entries], [e[1] for e in entries],
                in_field=in_field, dtype=np.float16,
            )
            agg.sensor_id = P.majority_sensor([{"L8": P.SENSOR_IDS["L8"], "L9": P.SENSOR_IDS["L9"],
                                                "unknown": P.SENSOR_IDS["unknown"]}[s]
                                               for s in (e[2] for e in entries)])
            root["values"][fi, ci, b] = agg.values
            root["pixel_valid"][fi, ci, b, 0] = agg.pixel_valid
            root["n_obs"][fi, ci, b] = min(int(agg.n_obs), 255)
            root["sensor_id"][fi, ci, b] = agg.sensor_id
        field_values[ci] = root["values"][fi, ci]
    return {
        "field_id": int(field_id),
        "n_cycles": len(cycles_of_field),
        "n_scenes": n_scenes_used,
        "seconds": round(time.time() - t0, 2),
        "sha256": field_content_sha256(field_values),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "data" / "processed" / P.PATCH_STORE_NAME))
    ap.add_argument("--mask", default=str(ROOT / "data" / "interim" / "field_mask.tif"))
    ap.add_argument("--scenes-root", default="D:/RS/Thesis/Data/Metric/scenes")
    ap.add_argument("--cycles", default=str(ROOT / "data" / "processed" / "cycles_490.parquet"))
    ap.add_argument("--epoch", default=None,
                    help="archive epoch of the cycle offsets (default: locked base_date "
                         "with --splits, otherwise earliest unfiltered scene)")
    ap.add_argument("--band-scale", default="auto", choices=("auto", "native", "landsat"),
                    help="native = scenes are already reflectance/K (the shipped "
                         "archive); landsat = apply C2 L2 factors; auto = infer per scene")
    ap.add_argument("--splits", type=Path,
                    help="locked splits JSON; required for a training-compatible store")
    ap.add_argument("--fields", default=None, help="comma-separated field ids")
    ap.add_argument("--dates", default=None, help="comma-separated YYYY-MM-DD scene dates")
    ap.add_argument("--smoke", type=int, default=None, metavar="N",
                    help="first N fields and scenes only (writes to --out as usual)")
    ap.add_argument("--estimate-runtime", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--patch-size", type=int, default=P.DEFAULT_PATCH_SIZE)
    args = ap.parse_args(argv)

    store = Path(args.out)
    mask_path = Path(args.mask)
    if not mask_path.is_file():
        print(f"field mask not found: {mask_path}", file=sys.stderr)
        return 2
    cycle_source_hash = file_sha256(args.cycles)
    splits = None
    if args.splits is not None:
        splits = msplits.load_splits_locked(path=args.splits, verify_cycle_files=False)
        if cycle_source_hash != splits.get("cycle_file_hashes", {}).get("cycles_parquet_sha256"):
            raise ValueError("--cycles does not match the verified locked splits parquet hash")
    cycles = load_cycles(args.cycles, require_cycle_ids=splits is not None)
    scenes = discover_scenes(args.scenes_root)
    if not scenes:
        print(f"no scene directories under {args.scenes_root}", file=sys.stderr)
        return 2

    epoch = _date.fromisoformat(args.epoch) if args.epoch else scenes[0][0]
    if splits is not None:
        locked_epoch = _date.fromisoformat(splits["base_date"])
        if args.epoch and epoch != locked_epoch:
            raise ValueError("--epoch disagrees with the locked splits base_date")
        epoch = locked_epoch
    binding = {
        "cycle_epoch": epoch.isoformat(),
        "cycle_source_sha256": cycle_source_hash,
        "splits_manifest_sha256": splits["manifest_sha256"] if splits is not None else None,
    }

    field_ids = sorted({int(f) for f in np.unique(cycles[:, 0])})
    if args.fields:
        want = {int(x) for x in args.fields.split(",") if x.strip()}
        field_ids = [f for f in field_ids if f in want]
    if args.dates:
        want_dates = {_date.fromisoformat(x.strip()) for x in args.dates.split(",") if x.strip()}
        scenes = [s for s in scenes if s[0] in want_dates]
    if args.smoke:
        field_ids = field_ids[: args.smoke]
        scenes = scenes[: args.smoke]
    if not field_ids or not scenes:
        print("no fields or scenes remain after the requested selection", file=sys.stderr)
        return 2

    if args.estimate_runtime:
        est = estimate_runtime(len(field_ids), cycles[np.isin(cycles[:, 0], field_ids)],
                               scenes, epoch=epoch)
        print(json.dumps(est, indent=2))
        return 0

    from ssl_anomaly.io.field_mask import load_field_mask

    # A resumed extraction must use the same grid, source list and geometry.
    # The archive is treated as immutable; do not replace rasters mid-export.
    binding["export_selection_sha256"] = hashlib.sha256(json.dumps({
        "fields": field_ids,
        "mask_sha256": file_sha256(mask_path),
        "scenes": [(day.isoformat(), str(path.resolve())) for day, path in scenes],
        "band_scale": args.band_scale,
        "patch_size": args.patch_size,
    }, sort_keys=True).encode()).hexdigest()
    max_cycles = int(max(np.sum(cycles[:, 0] == f) for f in field_ids))
    if store.exists():
        if not args.resume:
            print("store already exists; use --resume with identical inputs or a new --out", file=sys.stderr)
            return 3
        root = P.open_store(store, mode="r+")
        if "cycle_end_day" not in root or any(root.attrs.get(k) != v for k, v in binding.items()):
            print("store cycle provenance or export selection differs; use a new --out path", file=sys.stderr)
            return 3
        P.validate_store(root, expected_fields=len(field_ids))
    else:
        root = P.create_store(store, field_ids=field_ids, max_cycles=max_cycles,
                              size=args.patch_size, attrs=binding)
    if not np.any(root["field_ids"][:]):
        # create_store allocates the array but cannot know the ids; they are
        # written here so a later --resume can prove it is the same selection.
        root["field_ids"][:] = np.asarray(field_ids, dtype=np.int64)
    if [int(x) for x in root["field_ids"][:]] != field_ids:
        print("store field_ids differ from this run's selection; refusing to mix runs",
              file=sys.stderr)
        return 3

    mask, _meta = load_field_mask(mask_path)
    already = done_fields(store) if args.resume else set()
    scenes_by_day = {day_index(d, epoch): p for d, p in scenes}
    provenance_extra = {
        "n_scenes_available": len(scenes),
        "scenes_root": str(args.scenes_root),
        "epoch": epoch.isoformat(),
        "band_scale": args.band_scale,
        "splits_path": str(args.splits) if args.splits else None,
        **binding,
    }

    n_done = 0
    for fi, fid in enumerate(field_ids):
        if fid in already:
            continue
        poly = mask == fid
        window = P.field_window(poly, size=args.patch_size)
        if window is None:
            print(f"[{fi + 1}/{len(field_ids)}] field {fid}: no pixels in the mask, skipped")
            continue
        root["in_field"][fi, 0] = P.patch_in_field_mask(poly, window)
        root["bbox_origin"][fi] = window.to_bbox_origin()
        rows = cycles[cycles[:, 0] == fid]
        root["cycle_valid"][fi] = 0  # mark partial work unavailable until all bins are written
        cycles_of_field = [(int(r[1]), int(r[2]), int(r[3])) for r in rows]
        for ci, (_cid, start, end) in enumerate(cycles_of_field):
            root["cycle_ids"][fi, ci] = _cid
            root["cycle_start_day"][fi, ci] = start
            root["cycle_end_day"][fi, ci] = end
        summary = export_field(
            root, fi, fid, mask=mask, cycles_of_field=cycles_of_field,
            scenes_by_day=scenes_by_day, size=args.patch_size, window=window,
            in_field=root["in_field"][fi, 0], band_scale=args.band_scale,
        )
        root["cycle_valid"][fi, :len(cycles_of_field)] = 1
        append_manifest(store, **summary)
        n_done += 1
        print(f"[{fi + 1}/{len(field_ids)}] field {fid}: {summary['n_scenes']} scene-reads, "
              f"{summary['seconds']:.1f}s, sha {summary['sha256'][:12]}")

    prov = P.Provenance(
        git_sha=git_sha(),
        cycles_sha256=cycle_source_hash,
        splits_sha256=binding["splits_manifest_sha256"] or "unspecified",
        source_products=[str(args.scenes_root)],
        scale_factors={
            "sr_scale": 0.0000275, "sr_offset": -0.2,
            "st_scale": 0.00341802, "st_offset": 149.0,
        },
        patch_size=args.patch_size,
        n_fields=len(field_ids),
        n_cycles=max_cycles,
        n_dates_done=len(scenes),
        output_sha256=P.output_sha256(root),
        created=_date.today().isoformat(),
        extra=provenance_extra,
    )
    prov.validate()
    (store / P.PROVENANCE_NAME).write_text(
        json.dumps(prov.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    report = P.validate_store(root, expected_fields=len(field_ids))
    print(json.dumps({"fields_written": n_done, "validation": report}, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
