"""Tests for the locked splits (tasks 1.1–1.3, spec model-development-protocol).

Archive checks inspect the untracked frozen split and cycle files without
rebuilding. Source-only access guards use an isolated split fixture.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import protocol as mproto  # noqa: E402
from ssl_anomaly.monitor import splits as msplits  # noqa: E402

MANIFEST_PATH = msplits.SPLITS_LOCKED_PATH


@pytest.fixture(scope="module")
def manifest() -> dict:
    if not MANIFEST_PATH.exists():
        pytest.fail(
            "data/processed/splits_locked.json missing — supply the original locked "
            "splits and cycle files from the authorized archive; do not regenerate them for this gate."
        )
    return msplits.load_splits_locked()


# ---------------------------------------------------------------------------
# Disjointness and coverage
# ---------------------------------------------------------------------------
@pytest.mark.real_data
def test_pairwise_disjoint(manifest: dict) -> None:
    id_sets = {name: set(manifest["cycles"][name]) for name in msplits.SPLIT_NAMES}
    for a in msplits.SPLIT_NAMES:
        for b in msplits.SPLIT_NAMES:
            if a < b:
                assert not (id_sets[a] & id_sets[b]), f"{a} and {b} overlap"


@pytest.mark.real_data
def test_uncensored_cycles_fully_covered(manifest: dict) -> None:
    """train+dev+test + cutoff-dropped + audit-excluded = uncensored count."""
    df = msplits.pd.read_parquet(msplits.CYCLES_PARQUET_PATH)
    n_uncensored = int((~df["censored"].astype(bool)).sum())
    assigned = sum(manifest["counts"][s] for s in ("train", "dev", "test"))
    dropped = manifest["n_dropped_train_cutoff"] + manifest["n_dropped_dev_cutoff"]
    excluded = manifest["audit_exclusions"]["n_excluded_from_metrics"]
    assert assigned + dropped + excluded == n_uncensored
    assert manifest["counts"]["monitoring_only"] >= int(df["censored"].astype(bool).sum())


@pytest.mark.real_data
def test_audit_exclusions_absent_from_metric_splits(manifest: dict) -> None:
    """Every exclusion-list cycle sits in monitoring_only (finding-14 D2)."""
    excl = msplits.load_audit_exclusions()
    if not excl["keys"]:
        pytest.skip("no exclusion list yet")
    for name in ("train", "dev", "test"):
        leaked = set(excl["keys"]) & set(manifest["cycles"][name])
        assert not leaked, f"{len(leaked)} audit-excluded cycles leaked into {name}"


@pytest.mark.real_data
def test_train_cycles_end_before_test_period(manifest: dict) -> None:
    """No train cycle may overlap the test period in time (D2)."""
    df = msplits.pd.read_parquet(msplits.CYCLES_PARQUET_PATH)
    df = df.assign(
        key=df["field"].astype(str) + ":" + df["cycle_id"].astype(str),
        end_date=msplits.BASE_DATE + msplits.pd.to_timedelta(df["t_end"], unit="D"),
    )
    train_keys = set(manifest["cycles"]["train"])
    sub = df[df["key"].isin(train_keys)]
    assert (msplits.pd.to_datetime(sub["end_date"]) < msplits.TEST_PERIOD_START).all()


@pytest.mark.real_data
def test_dev_cycles_end_before_test_period(manifest: dict) -> None:
    """Non-block dev cycles also end before the test period (recorded deviation)."""
    df = msplits.pd.read_parquet(msplits.CYCLES_PARQUET_PATH)
    df = df.assign(
        key=df["field"].astype(str) + ":" + df["cycle_id"].astype(str),
        end_date=msplits.BASE_DATE + msplits.pd.to_timedelta(df["t_end"], unit="D"),
    )
    dev_fields = set(manifest["kmeans"]["dev_block_fields"])
    dev_keys = set(manifest["cycles"]["dev"])
    non_block = df[df["key"].isin(dev_keys) & ~df["field"].isin(dev_fields)]
    assert (msplits.pd.to_datetime(non_block["end_date"]) < msplits.TEST_PERIOD_START).all()


@pytest.mark.real_data
def test_test_cycles_start_after_cutoff_or_in_test_block(manifest: dict) -> None:
    df = msplits.pd.read_parquet(msplits.CYCLES_PARQUET_PATH)
    df = df.assign(
        key=df["field"].astype(str) + ":" + df["cycle_id"].astype(str),
        start_date=msplits.BASE_DATE + msplits.pd.to_timedelta(df["t_start"], unit="D"),
    )
    test_fields = set(manifest["kmeans"]["test_block_fields"])
    test_keys = set(manifest["cycles"]["test"])
    sub = df[df["key"].isin(test_keys)]
    ok = (msplits.pd.to_datetime(sub["start_date"]) >= msplits.TEST_PERIOD_START) | sub["field"].isin(test_fields)
    assert ok.all()


@pytest.mark.real_data
def test_block_exclusivity(manifest: dict) -> None:
    """k-means block fields may appear ONLY in their own split (+ monitoring,
    where their censored cycles land). Non-block fields may legitimately span
    train/test via the date rule, so only BLOCK membership is exclusive."""
    test_fields = set(manifest["kmeans"]["test_block_fields"])
    dev_fields = set(manifest["kmeans"]["dev_block_fields"])
    assert not (test_fields & dev_fields)
    # Every block field that HAS uncensored, non-excluded cycles must sit in
    # its split (block fields whose cycles are all censored or audit-excluded
    # legitimately appear nowhere).
    df = msplits.pd.read_parquet(msplits.CYCLES_PARQUET_PATH)
    excl = set(msplits.load_audit_exclusions()["keys"])
    df = df.assign(key=df["field"].astype(str) + ":" + df["cycle_id"].astype(str))
    unc = df[(~df["censored"].astype(bool)) & (~df["key"].isin(excl))]
    has_unc = set(unc["field"].astype(int).unique())
    assert (test_fields & has_unc) <= set(manifest["test_fields"])
    assert (dev_fields & has_unc) <= set(manifest["dev_fields"])
    # …and no block field may appear in another metric split.
    for name in ("train", "dev"):
        fields = set(manifest[f"{name}_fields"])
        assert not (fields & test_fields), f"{name} contains test-block fields"
    for name in ("train", "test"):
        fields = set(manifest[f"{name}_fields"])
        assert not (fields & dev_fields), f"{name} contains dev-block fields"


@pytest.mark.real_data
def test_manifest_hash_and_drift(manifest: dict) -> None:
    expected = manifest["manifest_sha256"]
    assert msplits.manifest_hash(manifest) == expected
    # Tampering must break the hash.
    tampered = copy.deepcopy(manifest)
    tampered["counts"]["train"] += 1
    assert msplits.manifest_hash(tampered) != expected


@pytest.mark.real_data
def test_cycle_file_hash_guard(manifest: dict, tmp_path: Path) -> None:
    """A drift in the cycle file hash must refuse to load (manifest-drift req)."""
    bad = copy.deepcopy(manifest)
    bad["cycle_file_hashes"]["cycles_parquet_sha256"] = "0" * 64
    bad["manifest_sha256"] = msplits.manifest_hash(bad)
    p = tmp_path / "splits_locked.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(RuntimeError, match="drift"):
        msplits.load_splits_locked(path=p)


@pytest.mark.real_data
def test_frozen_holdout_covers_locked_spatial_block(manifest: dict) -> None:
    """Strict, read-only archive gate: hash, source, cutoff and spatial coverage."""
    from ssl_anomaly.monitor import holdout as H

    frozen = H.load_holdout_manifest()
    H.assert_frozen_holdout_matches_splits(frozen, manifest)


# ---------------------------------------------------------------------------
# Test-access guards
# ---------------------------------------------------------------------------
@pytest.fixture
def stub_manifest() -> dict:
    cycles = {"train": ["1:0", "1:1"], "dev": ["2:0"], "test": ["3:0"],
              "monitoring_only": ["4:0"]}
    return {"cycles": cycles, "counts": {name: len(keys) for name, keys in cycles.items()}}


def test_select_splits_refuses_test(stub_manifest: dict) -> None:
    data = {"cycle_keys": ["1:0", stub_manifest["cycles"]["test"][0]], "X": np.zeros((2, 2, 2), dtype=np.float32)}
    for key in ("M", "field_ids", "start_dates", "end_dates", "harvest_days"):
        data[key] = np.zeros(2, dtype=np.float32)
    data["cycle_keys"] = ["1:0", stub_manifest["cycles"]["test"][0]]
    with pytest.raises(RuntimeError, match="final-test"):
        mproto.select_splits(data, stub_manifest, splits=("test",))


def test_assert_no_test_cycles_names_entry_point(stub_manifest: dict) -> None:
    leaked = stub_manifest["cycles"]["test"][:1]
    with pytest.raises(RuntimeError, match=r"freeze_main_model\.py --final-test"):
        msplits.assert_no_test_cycles(leaked, stub_manifest, context="unit-test")


def test_select_splits_slices_requested_only(stub_manifest: dict) -> None:
    """Only requested-split rows survive the slice; test rows never included."""
    data = msplits_full_stub(stub_manifest)
    sel = mproto.select_splits(data, stub_manifest, splits=("train",))
    assert set(sel["cycle_keys"]) == set(stub_manifest["cycles"]["train"])
    assert len(sel["X"]) == stub_manifest["counts"]["train"]


def msplits_full_stub(manifest: dict) -> dict:
    """A tiny synthetic archive stub covering all splits."""
    all_keys = [k for name in msplits.SPLIT_NAMES for k in manifest["cycles"][name]]
    n = len(all_keys)
    return {
        "X": np.zeros((n, 36, 8), dtype=np.float32),
        "M": np.zeros((n, 36, 8), dtype=bool),
        "field_ids": np.zeros(n, dtype=np.int64),
        "start_dates": np.array(["2020-01-01"] * n, dtype=object),
        "end_dates": np.array(["2020-01-01"] * n, dtype=object),
        "harvest_days": np.zeros(n, dtype=np.int64),
        "cycle_keys": all_keys,
    }
