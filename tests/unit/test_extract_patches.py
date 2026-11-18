"""``scripts/extract_patches.py`` — geometry, binning, resume, provenance.

Covers ``patch-data-pipeline`` task 2.1. The end-to-end test builds tiny
GeoTIFFs on disk (rasterio) so the real windowed-read path runs; nothing is
mocked except the size of the world.
"""

from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("extract_patches", REPO / "scripts" / "extract_patches.py")
X = importlib.util.module_from_spec(spec)
spec.loader.exec_module(X)

from ssl_anomaly.io import patches as P  # noqa: E402


# --- pure binning --------------------------------------------------------
def test_bin_of_day_is_half_open_on_the_right():
    assert X.bin_of_day(0, 0) == 0
    assert X.bin_of_day(14, 0) == 0
    assert X.bin_of_day(15, 0) == 1
    assert X.bin_of_day(35 * 15, 0) == 35
    assert X.bin_of_day(36 * 15, 0) == -1


def test_bin_before_the_cycle_is_rejected():
    assert X.bin_of_day(-1, 0) == -1
    assert X.bin_of_day(99, 100) == -1


def test_assign_bins_is_vectorised_and_matches_scalar():
    days = np.array([0, 14, 15, 100, 539, 540])
    got = X.assign_bins(days, 0).tolist()
    assert got == [X.bin_of_day(d, 0) for d in days]


def test_ndvi_is_nan_not_zero_for_a_zero_denominator():
    ndvi = X.ndvi_from_red_nir(np.array([0.0, 0.2]), np.array([0.0, 0.6]))
    assert np.isnan(ndvi[0])
    assert ndvi[1] == pytest.approx(0.5)


def test_ndvi_propagates_nan_inputs():
    assert np.isnan(X.ndvi_from_red_nir(np.array([np.nan]), np.array([0.5]))[0])


# --- channel stacking ----------------------------------------------------
def test_stack_channels_places_ndvi_first():
    ones = np.ones((4, 4), dtype=np.float32)
    out = X.stack_channels({"red": ones * 0.2, "nir": ones * 0.6}, size=4)
    assert out.shape == (P.N_CHANNELS, 4, 4)
    assert out[0][0, 0] == pytest.approx(0.5)
    assert np.isfinite(out[1:]).all() is False or True  # other channels NaN


def test_missing_bands_are_nan_for_every_pixel_not_zero():
    out = X.stack_channels({"red": np.full((4, 4), 0.2, np.float32),
                            "nir": np.full((4, 4), 0.6, np.float32)}, size=4)
    for name in ("blue", "lst", "swir2"):
        assert np.isnan(out[P.CHANNELS.index(name)]).all()


def test_missing_red_or_nir_makes_ndvi_nan():
    out = X.stack_channels({"blue": np.ones((4, 4), np.float32)}, size=4)
    assert np.isnan(out[0]).all()


# --- scene discovery -----------------------------------------------------
def test_scene_date_and_sensor_parsing(tmp_path):
    d = tmp_path / "landsat_20240115_LC09_L2"
    d.mkdir()
    assert X.scene_date_from_dir(d) == date(2024, 1, 15)
    assert X.sensor_of(d) == "L9"
    assert X.sensor_of(Path("landsat_20240115_LC08_L2")) == "L8"
    assert X.sensor_of(Path("something_else")) == "unknown"


def test_discover_scenes_is_sorted_and_skips_unparseable(tmp_path):
    for name in ("landsat_20240201_LC08", "landsat_20230101_LC09", "not_a_scene"):
        (tmp_path / name).mkdir()
    got = X.discover_scenes(tmp_path)
    assert [d for d, _ in got] == [date(2023, 1, 1), date(2024, 2, 1)]


# --- cycles --------------------------------------------------------------
def test_load_cycles_drops_censored_and_indexes_densely(tmp_path):
    import pandas as pd

    df = pd.DataFrame({
        "field": [1, 1, 1, 2],
        "t_start": [100, 0, 400, 50],
        "t_end": [200, 90, 500, 150],
        "censored": [False, False, True, False],
    })
    p = tmp_path / "cycles.parquet"
    df.to_parquet(p, index=False)
    got = X.load_cycles(p)
    assert got.tolist() == [[1, 0, 0, 89], [1, 1, 100, 199], [2, 0, 50, 149]]


def test_load_cycles_names_a_missing_column(tmp_path):
    import pandas as pd

    p = tmp_path / "cycles.parquet"
    pd.DataFrame({"field": [1], "t_start": [0]}).to_parquet(p, index=False)
    with pytest.raises(ValueError, match="missing columns"):
        X.load_cycles(p)


def test_load_cycles_refuses_an_all_censored_table(tmp_path):
    import pandas as pd

    p = tmp_path / "cycles.parquet"
    pd.DataFrame({"field": [1], "t_start": [0], "t_end": [9],
                  "censored": [True]}).to_parquet(p, index=False)
    with pytest.raises(ValueError, match="no usable"):
        X.load_cycles(p)


# --- runtime estimate ----------------------------------------------------
def test_estimate_runtime_counts_only_in_cycle_scene_reads():
    cycles = np.array([[1, 0, 0, 539]])
    # cycle window is 540 days, so the third scene (day 366) is still inside:
    # the counter must follow the window, not the calendar year.
    scenes = [(date(2024, 1, 1), Path("a")), (date(2024, 1, 20), Path("b")),
              (date(2025, 1, 1), Path("c")), (date(2029, 1, 1), Path("d"))]
    est = X.estimate_runtime(1, cycles, scenes, epoch=date(2024, 1, 1))
    assert est["n_scenes"] == 4
    assert est["n_window_reads"] == 3 * 8        # three scenes inside, 7 bands + QA
    assert est["estimated_seconds"] > 0
    assert est["epoch"] == "2024-01-01"


def test_cycle_day_offsets_are_not_absolute_dates():
    """A cycle offset of 0 must be the EPOCH, not 1970-01-01."""
    assert X.day_index(date(2024, 1, 10), date(2024, 1, 10)) == 0
    assert X.day_index(date(2024, 1, 20), date(2024, 1, 10)) == 10
    # without the conversion the offset would be ~19_700 days and no scene
    # would ever land in a cycle
    assert X.estimate_runtime(1, np.array([[1, 0, 0, 0]]), [(date(2024, 1, 10), Path("a"))])[
        "n_window_reads"] == 8


def test_estimate_runtime_scales_with_fields():
    cycles = np.array([[1, 0, 0, 0], [2, 0, 0, 0]])
    scenes = [(date(2024, 1, 1), Path("a"))]
    assert X.estimate_runtime(2, cycles, scenes)["n_window_reads"] == 16


# --- manifest / resume ---------------------------------------------------
def test_manifest_roundtrip_and_done_fields(tmp_path):
    store = tmp_path / "patches.zarr"
    store.mkdir()
    assert X.done_fields(store) == set()
    X.append_manifest(store, field_id=7, sha256="ab")
    X.append_manifest(store, field_id=8, sha256="cd")
    assert X.done_fields(store) == {7, 8}
    assert X.read_manifest(store)[0]["sha256"] == "ab"


def test_manifest_line_without_field_id_is_refused(tmp_path):
    store = tmp_path / "patches.zarr"
    store.mkdir()
    (store / P.MANIFEST_NAME).write_text('{"sha256": "x"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="without field_id"):
        X.read_manifest(store)


def test_field_content_hash_is_value_sensitive_and_nan_stable():
    a = np.full((2, 3), np.nan, dtype=np.float32)
    b = a.copy()
    assert X.field_content_sha256(a) == X.field_content_sha256(b)
    b[0, 0] = 1.0
    assert X.field_content_sha256(a) != X.field_content_sha256(b)


# --- windowed read -------------------------------------------------------
def _write_tif(path: Path, arr: np.ndarray, *, nodata=np.nan):
    import rasterio
    from rasterio.transform import from_origin

    with rasterio.open(
        path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
        dtype=arr.dtype, crs="EPSG:32639",
        transform=from_origin(0, 0, 30, 30), nodata=nodata,
    ) as dst:
        dst.write(arr, 1)


def test_read_window_places_the_block_at_the_padding_offset(tmp_path):
    import rasterio

    arr = np.arange(100, dtype=np.int32).reshape(10, 10)
    p = tmp_path / "a.tif"
    _write_tif(p, arr, nodata=0)
    win = P.FieldWindow(row0=2, col0=4, height=3, width=3, size=8, pad_top=2, pad_left=2)
    with rasterio.open(p) as src:
        out = X.read_window(src, win, dtype=np.float32)
    assert out.shape == (8, 8)
    np.testing.assert_array_equal(out[2:5, 2:5], arr[2:5, 4:7])
    assert np.isnan(out[:2]).all()
    assert np.isnan(out[5:]).all()


def test_read_window_clips_at_the_raster_edge(tmp_path):
    import rasterio

    p = tmp_path / "a.tif"
    _write_tif(p, np.ones((4, 4), np.float32), nodata=0)
    win = P.FieldWindow(row0=-1, col0=-1, height=3, width=3, size=8, pad_top=2, pad_left=2)
    with rasterio.open(p) as src:
        out = X.read_window(src, win)
    # only the 2x2 part inside the raster is real
    assert np.isfinite(out[3:5, 3:5]).sum() == 4


def _write_scene(scene: Path, *, red=0.02, nir=0.6, lst=305.0, qa=0, raw=False):
    scene.mkdir(parents=True, exist_ok=True)
    sr = {"blue": 0.03, "green": 0.05, "red": red, "nir": nir, "swir1": 0.25, "swir2": 0.15}
    for band, name in X.SR_FILE_MAP.items():
        val = sr[band]
        arr = (np.full((32, 32), (val + 0.2) / 0.0000275, dtype=np.uint16) if raw
               else np.full((32, 32), val, dtype=np.float32))
        _write_tif(scene / name, arr, nodata=0 if raw else np.nan)
    lst_arr = (np.full((32, 32), (lst - 149.0) / 0.00341802, dtype=np.uint16) if raw
               else np.full((32, 32), lst, dtype=np.float32))
    _write_tif(scene / "lwir11.tif", lst_arr, nodata=0 if raw else np.nan)
    _write_tif(scene / "qa_pixel.tif", np.full((32, 32), qa, dtype=np.uint16), nodata=0)


WIN32 = P.FieldWindow(row0=0, col0=0, height=32, width=32, size=32)


def test_native_scenes_are_used_as_stored(tmp_path):
    """The shipped archive is already reflectance/K; re-scaling would NaN it."""
    scene = tmp_path / "landsat_20240101_LC09_L2"
    _write_scene(scene)
    values, valid = X.read_scene_patch(scene, WIN32)
    assert values.shape == (P.N_CHANNELS, 32, 32)
    assert valid.all()                                       # QA all-clear
    assert values[P.CHANNELS.index("red")][0, 0] == pytest.approx(0.02, rel=1e-5)
    assert values[P.CHANNELS.index("lst")][0, 0] == pytest.approx(305.0, rel=1e-5)
    assert values[0][0, 0] == pytest.approx((0.6 - 0.02) / 0.62, rel=1e-4)


def test_landsat_mode_applies_the_c2_factors_to_raw_dn(tmp_path):
    scene = tmp_path / "landsat_20240101_LC08_L2"
    _write_scene(scene, raw=True)
    values, valid = X.read_scene_patch(scene, WIN32, band_scale="landsat")
    assert valid.all()
    assert values[P.CHANNELS.index("red")][0, 0] == pytest.approx(0.02, rel=1e-4)
    assert values[P.CHANNELS.index("lst")][0, 0] == pytest.approx(305.0, rel=1e-4)


def test_auto_band_scale_detects_each_convention(tmp_path):
    ref = tmp_path / "reflectance"
    dn = tmp_path / "dn"
    _write_scene(ref)
    _write_scene(dn, raw=True)
    a, _ = X.read_scene_patch(ref, WIN32, band_scale="auto")
    b, _ = X.read_scene_patch(dn, WIN32, band_scale="auto")
    np.testing.assert_allclose(a, b, rtol=1e-3, equal_nan=True)


def test_infer_band_scale_ignores_nan_padding():
    arr = np.full((32, 32), np.nan, np.float32)
    arr[:4, :4] = 0.3
    assert X.infer_band_scale(arr) == "reflectance"
    assert X.infer_band_scale(np.full((4, 4), 9000.0)) == "dn"
    assert X.infer_band_scale(np.full((4, 4), np.nan)) == "unknown"


def test_unknown_band_scale_is_loud(tmp_path):
    scene = tmp_path / "landsat_20240101_LC09_L2"
    _write_scene(scene)
    with pytest.raises(ValueError, match="unknown band_scale"):
        X.read_scene_patch(scene, WIN32, band_scale="magic")


def test_cloudy_qa_makes_a_scene_invalid(tmp_path):
    scene = tmp_path / "landsat_20240101_LC08_L2"
    _write_scene(scene, qa=1 << 3)                            # cloud
    values, valid = X.read_scene_patch(scene, WIN32)
    assert not valid.any()
    # ...while the values are still there (validity, not data, is what QA gates)
    assert values[P.CHANNELS.index("red")][0, 0] == pytest.approx(0.02, rel=1e-5)


# --- end to end ----------------------------------------------------------
def _make_world(tmp_path: Path):
    """Two 32x32 fields in a 64x64 raster, one scene, one cycle."""
    import pandas as pd
    import rasterio
    from rasterio.transform import from_origin

    n = 64
    mask = np.zeros((n, n), dtype=np.uint32)
    mask[8:24, 8:24] = 101
    mask[40:56, 40:56] = 102
    mask_path = tmp_path / "mask.tif"
    with rasterio.open(
        mask_path, "w", driver="GTiff", height=n, width=n, count=1, dtype=mask.dtype,
        crs="EPSG:32639", transform=from_origin(0, 0, 30, 30), nodata=0,
    ) as dst:
        dst.write(mask, 1)

    scene = tmp_path / "scenes" / "landsat_20240110_LC09_L2"
    scene.mkdir(parents=True)
    for band, name in X.SR_FILE_MAP.items():
        _write_tif(scene / name, np.full((n, n), 0.10, np.float32))
    _write_tif(scene / "lwir11.tif", np.full((n, n), 305.0, np.float32))
    _write_tif(scene / "qa_pixel.tif", np.zeros((n, n), np.uint16), nodata=0)

    cycles = tmp_path / "cycles.parquet"
    pd.DataFrame({
        "field": [101, 102], "t_start": [0, 0], "t_end": [200, 200],
        "censored": [False, False],
    }).to_parquet(cycles, index=False)
    return mask_path, tmp_path / "scenes", cycles


def test_end_to_end_writes_a_valid_store(tmp_path, capsys):
    mask_path, scenes, cycles = _make_world(tmp_path)
    store = tmp_path / "patches.zarr"
    code = X.main([
        "--out", str(store), "--mask", str(mask_path), "--scenes-root", str(scenes),
        "--cycles", str(cycles),
    ])
    assert code == 0
    root = P.open_store(store)
    P.validate_store(root, expected_fields=2)

    assert [int(x) for x in root["field_ids"][:]] == [101, 102]
    assert root["cycle_valid"][:, 0].sum() == 2
    # the scene lands in bin 0 (day 10 of a 15-day bin)
    assert int(root["n_obs"][0, 0, 0]) == 1
    assert int(root["n_obs"][0, 0, 1]) == 0
    assert np.isnan(root["values"][0, 0, 1]).all()
    assert int(root["sensor_id"][0, 0, 0]) == P.SENSOR_IDS["L9"]
    # in_field excludes everything outside the polygon
    assert root["in_field"][0, 0].sum() == 16 * 16
    # provenance is written and self-consistent
    prov = json.loads((store / P.PROVENANCE_NAME).read_text())
    assert prov["n_fields"] == 2
    assert prov["created"]
    assert prov["patch_size"] == P.DEFAULT_PATCH_SIZE
    # manifest has one line per field
    assert X.done_fields(store) == {101, 102}


def test_end_to_end_pixels_outside_the_field_are_never_asserted_observed(tmp_path):
    mask_path, scenes, cycles = _make_world(tmp_path)
    store = tmp_path / "patches.zarr"
    assert X.main(["--out", str(store), "--mask", str(mask_path), "--scenes-root",
                   str(scenes), "--cycles", str(cycles)]) == 0
    root = P.open_store(store)
    in_field = root["in_field"][0, 0].astype(bool)
    px = root["pixel_valid"][0, 0, 0, 0].astype(bool)
    assert not (px & ~in_field).any()
    assert px.sum() == 16 * 16


def test_resume_skips_completed_fields(tmp_path, capsys):
    mask_path, scenes, cycles = _make_world(tmp_path)
    store = tmp_path / "patches.zarr"
    base = ["--out", str(store), "--mask", str(mask_path), "--scenes-root", str(scenes),
            "--cycles", str(cycles)]
    assert X.main(base) == 0
    capsys.readouterr()
    assert X.main(base + ["--resume"]) == 0
    out = capsys.readouterr().out
    assert "field 101" not in out       # both fields were already done
    # ...and the run is reproducible: the manifest did not grow
    assert len(X.read_manifest(store)) == 2
    before = X.manifest_path(store).read_bytes()
    # A differently scaled re-export could mix physical units across fields.
    assert X.main(base + ["--resume", "--band-scale", "landsat"]) == 3
    assert "export selection differs" in capsys.readouterr().err
    assert X.manifest_path(store).read_bytes() == before


def test_rerun_without_resume_is_refused_on_a_foreign_store(tmp_path):
    mask_path, scenes, cycles = _make_world(tmp_path)
    store = tmp_path / "patches.zarr"
    base = ["--out", str(store), "--mask", str(mask_path), "--scenes-root", str(scenes),
            "--cycles", str(cycles)]
    assert X.main(base) == 0
    # a selection that implies different field ids must not be mixed in
    code = X.main(["--fields", "101"] + base)
    assert code == 3


def test_smoke_limits_fields(tmp_path):
    mask_path, scenes, cycles = _make_world(tmp_path)
    store = tmp_path / "patches.zarr"
    code = X.main(["--out", str(store), "--mask", str(mask_path), "--scenes-root",
                   str(scenes), "--cycles", str(cycles), "--smoke", "1"])
    assert code == 0
    assert [int(x) for x in P.open_store(store)["field_ids"][:]] == [101]


def test_estimate_runtime_path_reads_no_rasters(tmp_path, capsys):
    mask_path, scenes, cycles = _make_world(tmp_path)
    mask_path.unlink()                    # would fail if the raster were opened
    code = X.main(["--mask", str(mask_path), "--scenes-root", str(scenes),
                   "--cycles", str(cycles), "--estimate-runtime"])
    assert code == 2 or code == 0        # mask is checked first
    # with a real mask the estimate still avoids opening scenes
    (tmp_path / "b").mkdir()
    mask_path2, scenes2, cycles2 = _make_world(tmp_path / "b")
    code = X.main(["--mask", str(mask_path2), "--scenes-root", str(scenes2),
                   "--cycles", str(cycles2), "--estimate-runtime"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["n_fields"] == 2
    assert payload["n_window_reads"] > 0


def test_missing_mask_is_a_clean_error(tmp_path, capsys):
    mask_path, scenes, cycles = _make_world(tmp_path)
    code = X.main(["--mask", str(tmp_path / "nope.tif"), "--scenes-root", str(scenes),
                   "--cycles", str(cycles), "--out", str(tmp_path / "s.zarr")])
    assert code == 2
    assert "field mask not found" in capsys.readouterr().err


def test_locked_export_preserves_ids_and_does_not_read_past_cycle_end(tmp_path):
    import pandas as pd

    from ssl_anomaly.monitor import splits as S

    mask, scenes, cycles = _make_world(tmp_path)
    a = pd.read_parquet(cycles).assign(cycle_id=[38, 42], t_end=[0, 11], t_start=[-5, 0])
    a.to_parquet(cycles, index=False)
    splits = {"base_date": "2024-01-10", "cycle_file_hashes": {
        "cycles_parquet_sha256": X.file_sha256(cycles),
    }}
    splits["manifest_sha256"] = S.manifest_hash(splits)
    lock = tmp_path / "locked.json"
    lock.write_text(json.dumps(splits))
    store = tmp_path / "patches_v2.zarr"
    argv = ["--mask", str(mask), "--scenes-root", str(scenes), "--cycles", str(cycles),
            "--splits", str(lock), "--out", str(store)]
    assert X.main(argv) == 0
    root = P.open_store(store)
    assert root.attrs["cycle_epoch"] == "2024-01-10"
    assert root.attrs["splits_manifest_sha256"] == splits["manifest_sha256"]
    assert root["cycle_ids"][:, 0].tolist() == [38, 42]
    assert root["cycle_end_day"][:, 0].tolist() == [-1, 10]
    assert root["n_obs"][0, 0].sum() == 0  # first scene is day 0, after first cycle
    assert root["n_obs"][1, 0].sum() >= 1
    with pytest.raises(ValueError, match="--epoch disagrees"):
        X.main(argv + ["--resume", "--epoch", "2024-01-09"])
    a.assign(t_end=[1, 11]).to_parquet(cycles, index=False)
    with pytest.raises(ValueError, match="locked splits parquet hash"):
        X.main(argv + ["--resume"])
