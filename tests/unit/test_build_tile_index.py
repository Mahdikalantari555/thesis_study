"""Scene index generation tests (add-rgb-ndvi-tile-layer).

Builds a tiny synthetic scene tree (minimal GeoTIFFs + MTL.json files in a
tmp_path) and validates the manifest contract ``build_tile_index`` promises the
frontend: JSON structure, band flags, date parsing (MTL first, directory-name
fallback), canonical band order, deterministic date sorting, and the --limit
knob used by tests.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from build_tile_index import build_index, parse_mtl_date, scene_date  # type: ignore  # noqa: E402

# A small UTM 39N footprint near the real Khuzestan scenes keeps the EPSG:4326
# bounds in a plausible range without large files.
TRANSFORM = Affine(30.0, 0.0, 233010.0, 0.0, -30.0, 3443010.0)
SCENE_KEYS = {"date", "path", "bounds", "bands", "has_rgb", "has_ndvi"}


def write_band(scene_dir: Path, band: str) -> None:
    profile = dict(driver="GTiff", width=8, height=8, count=1, dtype="float32", crs="EPSG:32639", transform=TRANSFORM)
    with rasterio.open(scene_dir / f"{band}.tif", "w", **profile) as dst:
        dst.write(np.full((8, 8), 0.2, dtype="float32"), 1)


def write_mtl(scene_dir: Path, date: str | None = "2025-04-17") -> None:
    """Minimal collection-2 style MTL.json; ``None`` writes an unparseable one."""
    payload = (
        {"METADATA": {"PRODUCT_METADATA": {"ACQUISITION_DATE": date, "LANDSAT_PRODUCT_ID": f"LC08_L2SP_165039_{date.replace('-', '')}_02_T1"}}}
        if date
        else {"broken": True}
    )
    (scene_dir / "MTL.json").write_text(json.dumps(payload), encoding="utf-8")


def make_scene(scenes_dir: Path, name: str, bands: tuple[str, ...], date: str | None = "2025-04-17") -> Path:
    scene_dir = scenes_dir / name
    scene_dir.mkdir()
    for band in bands:
        write_band(scene_dir, band)
    write_mtl(scene_dir, date)
    return scene_dir


@pytest.fixture
def scenes_dir(tmp_path: Path) -> Path:
    """Three scenes + one non-scene dir, laid out like the real data tree."""
    root = tmp_path / "Data" / "Metric" / "scenes"
    root.mkdir(parents=True)
    make_scene(root, "landsat_20250417_165_039", ("blue", "green", "red", "nir08", "qa_pixel"))
    make_scene(root, "landsat_20250604_165_039", ("red", "nir08"), date="2025-06-04")
    # Unparseable MTL.json — the directory name must provide the date.
    make_scene(root, "landsat_20250722_165_039", ("blue", "green", "red", "nir08"), date=None)
    # Stray directory that matches no scene id pattern — skipped entirely.
    (root / "not_a_scene").mkdir()
    return root


def test_manifest_structure(scenes_dir: Path) -> None:
    manifest = build_index(scenes_dir)
    assert set(manifest.keys()) == {"scenes"}
    scenes = manifest["scenes"]
    assert len(scenes) == 3
    for scene in scenes:
        assert set(scene.keys()) == SCENE_KEYS
        assert isinstance(scene["bounds"], list) and len(scene["bounds"]) == 4
        assert isinstance(scene["bands"], list) and scene["bands"]
        assert isinstance(scene["has_rgb"], bool) and isinstance(scene["has_ndvi"], bool)
        assert scene["path"].endswith("/")


def test_band_flags(scenes_dir: Path) -> None:
    by_date = {s["date"]: s for s in build_index(scenes_dir)["scenes"]}
    full = by_date["2025-04-17"]
    assert full["has_rgb"] is True and full["has_ndvi"] is True
    assert full["bands"] == ["blue", "green", "red", "nir08", "qa_pixel"]
    red_nir = by_date["2025-06-04"]
    assert red_nir["has_rgb"] is False and red_nir["has_ndvi"] is True
    assert red_nir["bands"] == ["red", "nir08"]


def test_dates_sorted_and_mtl_parsed(scenes_dir: Path) -> None:
    scenes = build_index(scenes_dir)["scenes"]
    dates = [s["date"] for s in scenes]
    assert dates == sorted(dates)
    assert dates == ["2025-04-17", "2025-06-04", "2025-07-22"]
    # The third scene has a broken MTL.json — its date came from the dir name.
    assert parse_mtl_date(scenes_dir / "landsat_20250722_165_039") is None
    assert scene_date(scenes_dir / "landsat_20250722_165_039") == "2025-07-22"


def test_bounds_are_epsg4326(scenes_dir: Path) -> None:
    for scene in build_index(scenes_dir)["scenes"]:
        xmin, ymin, xmax, ymax = scene["bounds"]
        assert -180 <= xmin < xmax <= 180
        assert -90 <= ymin < ymax <= 90
    # First scene sits near the real Khuzestan footprint (~48E, ~31N).
    xmin, ymin, xmax, ymax = build_index(scenes_dir)["scenes"][0]["bounds"]
    assert 48.0 < xmin < xmax < 48.5 and 30.8 < ymin < ymax < 31.2


def test_limit_flag(scenes_dir: Path) -> None:
    assert len(build_index(scenes_dir, limit=2)["scenes"]) == 2
    assert len(build_index(scenes_dir, limit=99)["scenes"]) == 3


def test_non_scene_dirs_skipped(scenes_dir: Path) -> None:
    paths = {s["path"] for s in build_index(scenes_dir)["scenes"]}
    assert all("not_a_scene" not in p for p in paths)


def test_cli_writes_json(tmp_path: Path, scenes_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """main() honours --scenes-dir/--out and writes reviewable JSON."""
    import build_tile_index as mod

    out = tmp_path / "index.json"
    monkeypatch.setattr("sys.argv", ["build_tile_index.py", "--scenes-dir", str(scenes_dir), "--out", str(out)])
    mod.main()
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert len(manifest["scenes"]) == 3
    assert "wrote 3 scenes" in capsys.readouterr().out
