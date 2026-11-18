"""Per-scene zonal statistics via ``np.bincount``.

This is far faster than per-polygon rasterstats because it reduces each
scene to a single pass through the pixels with the pre-computed field
mask (spec L2). For each band we compute per-field mean, median, and
valid-pixel fraction.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

log = logging.getLogger("ssl_anomaly.io.zonal")


def zonal_scene(
    bands: dict[str, np.ndarray],
    valid: np.ndarray,
    labels: np.ndarray,
    n_fields: int,
    *,
    min_valid_fraction: float = 0.0,
) -> pd.DataFrame:
    """Compute per-field mean, median, and valid fraction for one scene.

    Parameters
    ----------
    bands:
        Band name → 2D array (same shape as labels). Values outside [valid]
        are masked. Nodata should already be NaN.
    valid:
        Boolean 2D array (True = good pixel: not cloud/shadow/...).
    labels:
        uint32 field-id raster (0 = outside any field).
    n_fields:
        Number of fields (max label value expected ≤ n_fields).
    min_valid_fraction:
        If set, bands for fields with valid_frac < threshold get NaN.

    Returns
    -------
    pd.DataFrame
        Columns: field, valid_frac, <band>_mean, <band>_median.
        Length = n_fields (fields 1..n_fields); field=0 is dropped.
    """
    if labels.shape != valid.shape:
        raise ValueError(
            f"labels shape {labels.shape} != valid shape {valid.shape}"
        )
    for name, arr in bands.items():
        if arr.shape != labels.shape:
            raise ValueError(
                f"band '{name}' shape {arr.shape} != labels shape {labels.shape}"
            )

    inside = labels > 0
    lab_inside = labels[inside]
    ok_inside = valid[inside]

    n_all = np.bincount(lab_inside, minlength=n_fields + 1)
    n_ok = np.bincount(lab_inside[ok_inside], minlength=n_fields + 1)
    valid_frac = n_ok / np.maximum(n_all, 1)

    out: dict[str, np.ndarray] = {
        "field": np.arange(1, n_fields + 1, dtype=np.int64),
        "valid_frac": valid_frac[1 : n_fields + 1],
    }

    ok_pixels = inside & valid  # inside-field AND valid
    lab_ok = labels[ok_pixels]
    for name, arr in bands.items():
        v = arr[ok_pixels].astype(np.float64)
        finite = np.isfinite(v)
        vf, lf = v[finite], lab_ok[finite]

        # mean: weighted sum / count
        wsum = np.bincount(lf, weights=vf, minlength=n_fields + 1)
        cnt = np.bincount(lf, minlength=n_fields + 1)
        mean = np.full(n_fields + 1, np.nan, dtype=np.float64)
        np.divide(wsum, np.maximum(cnt, 1), out=mean, where=cnt > 0)

        # median: via pandas groupby (fast enough given n_fields ~= 500)
        if lf.size > 0:
            med = (
                pd.Series(vf)
                .groupby(lf)
                .median()
                .reindex(np.arange(n_fields + 1))
                .to_numpy()
            )
        else:
            med = np.full(n_fields + 1, np.nan)

        if min_valid_fraction > 0:
            low = valid_frac < min_valid_fraction
            mean[low] = np.nan
            med[low] = np.nan

        out[f"{name}_mean"] = mean[1 : n_fields + 1].astype(np.float32)
        out[f"{name}_median"] = med[1 : n_fields + 1].astype(np.float32)

    return pd.DataFrame(out)


def zonal_scene_from_paths(
    scene_dir,
    field_mask_path,
    bands: list[str],
    quality_cfg,
    *,
    n_fields: int | None = None,
    min_valid_fraction: float = 0.0,
    scale_sr: float = 0.0000275,
    offset_sr: float = -0.2,
    scale_st: float = 0.00341802,
    offset_st: float = 149.0,
) -> pd.DataFrame | None:
    """Convenience: load scene + field mask and compute zonal stats.

    Returns None if the scene is missing or unreadable.
    """
    from .field_mask import load_field_mask
    from .landsat import load_scene

    labels, meta = load_field_mask(field_mask_path)
    nf = n_fields or int(meta["field_ids"].max())

    loaded = load_scene(
        scene_dir,
        bands=bands,
        cfg=quality_cfg,
        scale_sr=scale_sr,
        offset_sr=offset_sr,
        scale_st=scale_st,
        offset_st=offset_st,
    )
    if loaded is None:
        return None
    bands_dict, valid, scene_meta = loaded

    # Crop/pad scene to mask extents if necessary: reproject scene to mask grid.
    # For simplicity here we assume scenes are read in the same CRS and the
    # mask covers a small farm area within the scene. We crop the scene to
    # the mask's bounding box when the scene is larger.
    import rasterio
    from rasterio.windows import from_bounds

    # Find a reference band TIF to get scene transform
    scene_tifs = list(scene_dir.glob("*.TIF")) + list(scene_dir.glob("*.tif"))
    qa_tif = next(p for p in scene_tifs if "QA_PIXEL" in p.name)
    with rasterio.open(qa_tif) as src:
        scene_transform = src.transform
        scene_shape = src.shape
        scene_crs = src.crs

    mask_transform = meta["transform"]
    h, w = labels.shape

    # Map mask corners into scene pixel coordinates
    # We need to read the window of the scene that matches the mask.
    # For a production pipeline we'd use rasterio.warp.reproject to
    # resample onto the mask grid; here we do a cheap crop+read assuming
    # aligned grids (common when both are in same UTM zone with same pixel size).

    if str(scene_crs).upper() != str(meta["crs"]).upper():
        # If CRS differs, we need a warp. For v1 we skip scenes with differing CRS
        # (unlikely for Landsat ARD tiles).
        log.warning("Scene CRS (%s) != mask CRS (%s); skipping %s",
                     scene_crs, meta["crs"], scene_meta.scene_id)
        return None

    # Compute mask bounding box in scene crs coordinates
    from rasterio.transform import array_bounds

    mbounds = array_bounds(h, w, mask_transform)
    window = from_bounds(*mbounds, transform=scene_transform)
    window = window.round_offsets().round_lengths()
    row_off = int(max(0, window.row_off))
    col_off = int(max(0, window.col_off))
    win_h = int(min(scene_shape[0] - row_off, window.height))
    win_w = int(min(scene_shape[1] - col_off, window.width))
    if win_h <= 0 or win_w <= 0:
        log.warning("Scene %s does not intersect the field mask", scene_meta.scene_id)
        return None

    # Re-load QA and bands at the cropped window
    from .landsat import apply_scale_sr, apply_scale_st, quality_mask

    out_bands: dict[str, np.ndarray] = {}
    with rasterio.open(qa_tif) as src:
        qa_crop = src.read(1, window=((row_off, row_off + win_h), (col_off, col_off + win_w)))
    v_crop = quality_mask(qa_crop, quality_cfg)

    for b in bands:
        bpath = next((p for p in scene_tifs if p.stem.endswith("_" + b)), None)
        if bpath is None:
            continue
        with rasterio.open(bpath) as src:
            arr = src.read(1, window=((row_off, row_off + win_h), (col_off, col_off + win_w)))
        if b.startswith("ST_"):
            out_bands[b] = apply_scale_st(arr, scale_st, offset_st)
        else:
            out_bands[b] = apply_scale_sr(arr, scale_sr, offset_sr)

    # If crop size doesn't match mask, use a centered slice of the labels
    lab_crop = labels
    if (win_h, win_w) != (h, w):
        # Extract the same geographic window from labels
        label_window = from_bounds(
            *array_bounds(win_h, win_w, __import__("rasterio").windows.transform(window, scene_transform)),
            transform=mask_transform,
        )
        label_window = label_window.round_offsets().round_lengths()
        lr = int(max(0, label_window.row_off))
        lc = int(max(0, label_window.col_off))
        lh = int(min(h - lr, label_window.height))
        lw = int(min(w - lc, label_window.width))
        lab_crop = labels[lr : lr + lh, lc : lc + lw]
        v_crop = v_crop[:lh, :lw]
        out_bands = {k: v[:lh, :lw] for k, v in out_bands.items()}

    # Clip to common shape
    ch = min(lab_crop.shape[0], v_crop.shape[0])
    cw = min(lab_crop.shape[1], v_crop.shape[1])
    lab_crop = lab_crop[:ch, :cw]
    v_crop = v_crop[:ch, :cw]
    out_bands = {k: v[:ch, :cw] for k, v in out_bands.items()}

    df = zonal_scene(
        out_bands,
        v_crop,
        lab_crop,
        n_fields=nf,
        min_valid_fraction=min_valid_fraction,
    )
    df["scene_id"] = scene_meta.scene_id
    df["timestamp"] = scene_meta.timestamp
    df["sensor"] = scene_meta.sensor
    return df
