"""Tests for the frozen training-holdout manifest (change training-holdout-invariant,
tasks 1.1–1.2 and spec "Frozen training-holdout manifest").

Synthetic split manifests are used throughout: the real
``data/processed/splits_locked.json`` is data and is not committed, so these
tests must not depend on it. The derivation is a pure function, which is what
makes this possible.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import holdout as mholdout  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def make_splits_manifest() -> dict:
    """A minimal locked-splits manifest with the keys the derivation reads."""
    manifest = {
        "version": 1,
        "created": "2026-11-14",
        "test_period_start": "2024-01-01",
        "kmeans": {
            "seed": 13,
            "n_blocks": 10,
            "test_block": 8,
            "dev_block": 4,
            "test_block_fields": [101, 102, 103],
            "dev_block_fields": [201, 202],
        },
        "test_fields": [101, 102, 103],
        "dev_fields": [201, 202, 301],
        "train_fields": [301, 302, 303],
        "monitoring_only_fields": [401],
        "counts": {"train": 12, "dev": 6, "test": 5, "monitoring_only": 3},
        "cycles": {
            "train": ["301:1", "302:1", "303:1"],
            "dev": ["201:1", "202:1", "301:2"],
            "test": ["101:1", "102:1", "103:1"],
            "monitoring_only": ["401:1"],
        },
        "cycle_file_hashes": {"cycles_parquet_sha256": "deadbeef"},
    }
    manifest["manifest_sha256"] = "f" * 64
    return manifest


@pytest.fixture
def splits_manifest() -> dict:
    return make_splits_manifest()


@pytest.fixture
def manifest(splits_manifest: dict) -> dict:
    return mholdout.build_holdout_manifest(splits_manifest, created="2026-11-16")


# ---------------------------------------------------------------------------
# Task 1.1 — derivation, hashing, rebuild discipline
# ---------------------------------------------------------------------------
def test_holdout_farms_equal_locked_test_block(manifest: dict, splits_manifest: dict) -> None:
    """The farm set is exactly the locked test-field set — no new semantics."""
    assert set(manifest["holdout_farms"]) == set(splits_manifest["kmeans"]["test_block_fields"])
    assert manifest["holdout_farms"] == sorted(manifest["holdout_farms"])


def test_holdout_date_start_equals_test_period_start(manifest: dict) -> None:
    assert manifest["holdout_date_start"] == "2024-01-01"
    assert manifest["derived_from"]["test_period_start"] == "2024-01-01"


def test_known_farms_cover_every_split(manifest: dict) -> None:
    known = set(manifest["known_farm_ids"])
    for fid in (101, 201, 301, 302, 303, 401):
        assert fid in known, f"farm {fid} should be known at freeze time"
    assert set(manifest["holdout_farms"]).issubset(known)


def test_derivation_is_pure_and_hashed(splits_manifest: dict) -> None:
    """Same input ⇒ same manifest hash (the date is the only variable)."""
    a = mholdout.build_holdout_manifest(splits_manifest, created="2026-11-16")
    b = mholdout.build_holdout_manifest(splits_manifest, created="2026-11-16")
    assert a == b
    assert a["manifest_sha256"] == mholdout.holdout_manifest_hash(a)
    c = mholdout.build_holdout_manifest(splits_manifest, created="2026-11-17")
    assert c["manifest_sha256"] != a["manifest_sha256"]


def test_derivation_records_splits_provenance(manifest: dict, splits_manifest: dict) -> None:
    derived = manifest["derived_from"]
    assert derived["splits_manifest_sha256"] == splits_manifest["manifest_sha256"]
    assert derived["n_test_fields"] == len(splits_manifest["kmeans"]["test_block_fields"])
    assert "rule" in derived and "test_block_fields" in derived["rule"]


def test_missing_split_key_is_refused(splits_manifest: dict) -> None:
    broken = dict(splits_manifest)
    broken.pop("test_period_start")
    with pytest.raises(KeyError, match="test_period_start"):
        mholdout.build_holdout_manifest(broken)


def test_no_known_farms_is_refused(splits_manifest: dict) -> None:
    """Without any known-farm list the derivation cannot label future farms."""
    broken = dict(splits_manifest)
    for key in ("train_fields", "dev_fields", "monitoring_only_fields"):
        broken.pop(key)
    broken["kmeans"] = {"test_block_fields": [], "dev_block_fields": []}
    broken["test_fields"] = []
    with pytest.raises(ValueError, match=r"no .*_fields|refusing"):
        mholdout.build_holdout_manifest(broken)


def test_empty_test_field_set_is_refused(splits_manifest: dict) -> None:
    """A split manifest with no spatial holdout cannot yield a holdout manifest."""
    broken = dict(splits_manifest)
    broken["test_fields"] = []
    broken["kmeans"] = dict(broken["kmeans"], test_block_fields=[])
    with pytest.raises(ValueError, match=r"no kmeans\.test_block_fields"):
        mholdout.build_holdout_manifest(broken)


def test_save_refuses_overwrite_without_force(manifest: dict, tmp_path: Path) -> None:
    path = tmp_path / "holdout_manifest.json"
    mholdout.save_holdout_manifest(manifest, path=path)
    with pytest.raises(FileExistsError, match="--force"):
        mholdout.save_holdout_manifest(manifest, path=path)


def test_save_force_requires_reason(manifest: dict, tmp_path: Path) -> None:
    path = tmp_path / "holdout_manifest.json"
    mholdout.save_holdout_manifest(manifest, path=path)
    with pytest.raises(ValueError, match="reason"):
        mholdout.save_holdout_manifest(manifest, path=path, force=True, reason="  ")


def test_save_force_records_rebuild_reason(manifest: dict, tmp_path: Path) -> None:
    path = tmp_path / "holdout_manifest.json"
    mholdout.save_holdout_manifest(manifest, path=path)
    rebuilt = mholdout.build_holdout_manifest(make_splits_manifest(), created="2026-12-01")
    mholdout.save_holdout_manifest(
        rebuilt, path=path, force=True, reason="split re-frozen after data refresh",
    )
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["rebuild_of"]["reason"] == "split re-frozen after data refresh"
    assert on_disk["rebuild_of"]["previous_manifest_sha256"] == manifest["manifest_sha256"]
    # The hash still verifies after the rebuild marker is added.
    assert mholdout.load_holdout_manifest(path=path)["manifest_sha256"] == on_disk["manifest_sha256"]


def test_load_missing_manifest_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="holdout manifest missing"):
        mholdout.load_holdout_manifest(path=tmp_path / "nope.json")


def test_load_detects_tampering(manifest: dict, tmp_path: Path) -> None:
    path = tmp_path / "holdout_manifest.json"
    mholdout.save_holdout_manifest(manifest, path=path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["holdout_farms"] = data["holdout_farms"][:-1]  # silently drop a held-out farm
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RuntimeError, match="self-hash"):
        mholdout.load_holdout_manifest(path=path)


def test_archive_end_recorded_when_given(splits_manifest: dict) -> None:
    m = mholdout.build_holdout_manifest(
        splits_manifest, created="2026-11-16", archive_end_date="2026-09-10",
    )
    assert m["archive_end_date"] == "2026-09-10"
    assert mholdout.build_holdout_manifest(
        splits_manifest, created="2026-11-16",
    )["archive_end_date"] is None


def test_spatial_block_not_row_derived_test_farms(splits_manifest):
    # 103 has no test row; 301 has some dates in test but is not in the block.
    splits_manifest["test_fields"] = [101, 102, 301]
    manifest = mholdout.build_holdout_manifest(splits_manifest)
    assert manifest["holdout_farms"] == [101, 102, 103]
    assert mholdout.train_only_mask([103, 301], manifest=manifest).tolist() == [False, True]


def test_legacy_extra_exclusions_unchanged_and_missing_members_rejected(manifest, splits_manifest):
    manifest["holdout_farms"].append(301)
    report = mholdout.audit_frozen_holdout(manifest, splits_manifest)
    assert report["extra_frozen_fields"] == [301]
    assert report["missing_spatial_fields"] == []
    mholdout.assert_frozen_holdout_matches_splits(manifest, splits_manifest)
    assert not mholdout.train_only_mask([301], manifest=manifest)[0]
    manifest["holdout_farms"].remove(103)
    with pytest.raises(mholdout.HoldoutViolationError, match=r"missing_spatial_fields.*103"):
        mholdout.assert_frozen_holdout_matches_splits(manifest, splits_manifest)
