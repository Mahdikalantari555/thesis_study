"""Tests for fail-closed holdout enforcement (change training-holdout-invariant,
tasks 2.1 and spec "Fail-closed holdout enforcement in every training path").

The invariant: no training consumer may see a holdout farm or a holdout-period
cycle, and the failure must be a named error listing the offending pairs — never
a warning.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import holdout as mholdout  # noqa: E402


@pytest.fixture
def manifest() -> dict:
    splits = {
        "created": "2026-11-14",
        "test_period_start": "2024-01-01",
        "test_fields": [101, 102],
        "kmeans": {"test_block_fields": [101, 102]},
        "dev_fields": [201],
        "train_fields": [301, 302],
        "monitoring_only_fields": [401],
        "cycles": {},
    }
    splits["manifest_sha256"] = "f" * 64
    return mholdout.build_holdout_manifest(splits, created="2026-11-16")


# ---------------------------------------------------------------------------
# train_only_mask
# ---------------------------------------------------------------------------
def test_mask_accepts_clean_train_inputs(manifest: dict) -> None:
    mask = mholdout.train_only_mask(
        [301, 302], ["2022-03-01", "2022-05-01"], manifest=manifest,
    )
    assert mask.all()


def test_mask_rejects_holdout_farm(manifest: dict) -> None:
    mask = mholdout.train_only_mask([301, 101], manifest=manifest)
    assert list(mask) == [True, False]


def test_mask_rejects_future_unknown_farm(manifest: dict) -> None:
    """A farm registered after the freeze is holdout by default."""
    mask = mholdout.train_only_mask([301, 777], manifest=manifest)
    assert list(mask) == [True, False]


def test_mask_rejects_holdout_period(manifest: dict) -> None:
    mask = mholdout.train_only_mask(
        [301, 302], ["2022-06-01", "2024-02-01"], manifest=manifest,
    )
    assert list(mask) == [True, False]


def test_mask_accepts_cycle_starting_before_cutoff_only(manifest: dict) -> None:
    mask = mholdout.train_only_mask(
        [301, 302], ["2023-12-31", "2024-01-01"], manifest=manifest,
    )
    assert list(mask) == [True, False], "the cutoff is inclusive on the holdout side"


def test_mask_length_mismatch_raises(manifest: dict) -> None:
    with pytest.raises(ValueError, match="length"):
        mholdout.train_only_mask([301, 302], ["2022-01-01"], manifest=manifest)


# ---------------------------------------------------------------------------
# assert_train_only — the fail-closed proof
# ---------------------------------------------------------------------------
def test_assert_passes_clean_input(manifest: dict) -> None:
    mholdout.assert_train_only(
        [301, 302], ["301:1", "302:1"], ["2022-01-01", "2022-03-01"],
        manifest=manifest, context="unit-test",
    )


def test_assert_raises_named_error_for_holdout_farm(manifest: dict) -> None:
    with pytest.raises(mholdout.HoldoutViolationError) as excinfo:
        mholdout.assert_train_only(
            [301, 101], ["301:1", "101:7"], ["2022-01-01", "2020-04-01"],
            manifest=manifest, context="unit-test-dataset",
        )
    msg = str(excinfo.value)
    assert "101:7" in msg, "the offending (field, cycle) pair must be named"
    assert "holdout farm" in msg
    assert "unit-test-dataset" in msg, "the calling training path must be named"
    assert "aborted before the first batch" in msg


def test_assert_raises_for_holdout_period(manifest: dict) -> None:
    with pytest.raises(mholdout.HoldoutViolationError, match="holdout period"):
        mholdout.assert_train_only(
            [301], ["301:9"], ["2024-06-01"], manifest=manifest,
        )


def test_assert_raises_for_unknown_future_farm(manifest: dict) -> None:
    with pytest.raises(mholdout.HoldoutViolationError, match="future-by-default"):
        mholdout.assert_train_only([888], ["888:1"], manifest=manifest)


def test_assert_lists_every_violation_up_to_the_cap(manifest: dict) -> None:
    fields = [101, 102] + [900 + i for i in range(10)]
    keys = [f"{f}:1" for f in fields]
    with pytest.raises(mholdout.HoldoutViolationError) as excinfo:
        mholdout.assert_train_only(fields, keys, manifest=manifest, max_listed=4)
    msg = str(excinfo.value)
    assert msg.count(":1 (") == 4
    assert "+8 more" in msg
    assert "12 training input(s)" in msg


def test_assert_accepts_cycle_keys_only(manifest: dict) -> None:
    """Field ids may be omitted when cycle keys carry them."""
    mholdout.assert_train_only(
        None, ["301:1", "302:2"], manifest=manifest,
    )
    with pytest.raises(mholdout.HoldoutViolationError, match="101:1"):
        mholdout.assert_train_only(None, ["301:1", "101:1"], manifest=manifest)


def test_assert_requires_some_identifier(manifest: dict) -> None:
    with pytest.raises(ValueError, match="field_ids or cycle_keys"):
        mholdout.assert_train_only(manifest=manifest)


def test_assert_rejects_mismatched_key_count(manifest: dict) -> None:
    with pytest.raises(ValueError, match="cycle_keys length"):
        mholdout.assert_train_only([301], ["301:1", "302:1"], manifest=manifest)


# ---------------------------------------------------------------------------
# filter + guard (the shared Dataset base)
# ---------------------------------------------------------------------------
def test_filter_removes_holdout_and_asserting_the_result_passes(manifest: dict) -> None:
    fields = [301, 101, 302, 777]
    keys = ["301:1", "101:1", "302:1", "777:1"]
    starts = ["2022-01-01"] * 4
    kept = mholdout.filter_train_only(fields, keys, starts, manifest=manifest)
    assert kept == ["301:1", "302:1"]
    # Proving the filter worked — the enforcement point is the assertion.
    mholdout.assert_train_only(None, kept, ["2022-01-01", "2022-01-01"], manifest=manifest)


def test_holdout_guard_filters_then_asserts(manifest: dict) -> None:
    guard = mholdout.HoldoutGuard(manifest=manifest, context="patch-dataset")
    fields = [301, 101]
    keys = ["301:1", "101:1"]
    kept = guard.filter(fields, keys, ["2022-01-01", "2022-01-01"])
    assert kept == ["301:1"]
    guard.check(None, kept, ["2022-01-01"])  # clean input passes
    with pytest.raises(mholdout.HoldoutViolationError, match="patch-dataset"):
        guard.check(fields, keys, ["2022-01-01", "2022-01-01"])


def test_holdout_guard_records_manifest_sha(manifest: dict) -> None:
    guard = mholdout.HoldoutGuard(manifest=manifest)
    assert guard.holdout_manifest_sha256 == manifest["manifest_sha256"]


# ---------------------------------------------------------------------------
# train_main.py wiring (task 2.3) — asserted statically, no data needed
# ---------------------------------------------------------------------------
def test_train_main_asserts_holdout_before_first_batch() -> None:
    source = (REPO_ROOT / "scripts/train_main.py").read_text(encoding="utf-8")
    assert "mholdout.load_holdout_manifest()" in source
    assert "mholdout.assert_train_only(" in source
    # The assertion must precede the normalization fit (i.e. the first data use).
    assert source.index("assert_train_only(") < source.index("fit_robust_norm(")
    assert "cycle_end_dates=last_data_days" in source
    assert "holdout_manifest_sha256" in source, "manifest sha must reach the run manifest"


def test_main_rejects_cutoff_crossing_before_fitting_norm(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("train_main", REPO_ROOT / "scripts/train_main.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    splits = {"test_period_start": "2024-01-01", "kmeans": {"test_block_fields": [101]},
              "train_fields": [301], "manifest_sha256": "a" * 64}
    frozen = mholdout.build_holdout_manifest(splits)
    monkeypatch.setattr(mod.msplits, "load_splits_locked", lambda: splits)
    monkeypatch.setattr(mholdout, "load_holdout_manifest", lambda: frozen)
    monkeypatch.setattr(mod.minputs, "load_masked_cycles", lambda: {})
    monkeypatch.setattr(mod.mproto, "select_splits", lambda *_a, **_kw: {
        "field_ids": [301], "cycle_keys": ["301:7"],
        "start_dates": ["2023-07-01"], "end_dates": ["2024-01-02"],  # exclusive
    })
    monkeypatch.setattr(mod.minputs, "fit_robust_norm", lambda *_a, **_kw: pytest.fail("fit before admission"))
    monkeypatch.setattr(mod.mproto, "DEV_DIR", tmp_path / "report")
    monkeypatch.setattr(mod.mproto, "CHECKPOINTS_DEV_DIR", tmp_path / "ckpt")
    with pytest.raises(mholdout.HoldoutViolationError, match=r"301:7 \(cycle touches the holdout period"):
        mod.main(["--model", "gru_ae", "--smoke", "--device", "cpu"])


def test_build_holdout_manifest_script_is_dry_run_safe() -> None:
    """--dry-run must not write anything (it is how the owner inspects the sets)."""
    source = (REPO_ROOT / "scripts/build_holdout_manifest.py").read_text(encoding="utf-8")
    assert "--dry-run" in source
    assert "nothing written" in source
    assert "--force requires a non-empty --reason" in source or "requires --reason" in source


# ---------------------------------------------------------------------------
# build_holdout_manifest.py CLI behaviour (task 1.2)
# ---------------------------------------------------------------------------
def _import_build_script():
    spec = importlib.util.spec_from_file_location(
        "build_holdout_manifest", REPO_ROOT / "scripts/build_holdout_manifest.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _patch_loader(monkeypatch, mod, splits_manifest: dict) -> None:
    """Serve the synthetic split manifest instead of the (absent) real data."""
    def fake_loader(**kwargs):
        return splits_manifest

    monkeypatch.setattr(mod.msplits, "load_splits_locked", fake_loader)


def test_cli_writes_then_refuses_then_force_records_reason(
    monkeypatch, tmp_path: Path,
) -> None:
    mod = _import_build_script()
    splits = {
        "created": "2026-11-14",
        "test_period_start": "2024-01-01",
        "test_fields": [101, 102],
        "kmeans": {"test_block_fields": [101, 102]},
        "dev_fields": [201],
        "train_fields": [301],
        "monitoring_only_fields": [401],
        "cycles": {},
        "manifest_sha256": "f" * 64,
    }
    _patch_loader(monkeypatch, mod, splits)
    out = tmp_path / "holdout_manifest.json"

    assert mod.main(["--out", str(out)]) == 0
    assert out.exists()

    # Second write without --force fails with a clear code and message.
    assert mod.main(["--out", str(out)]) == 2

    # --force without --reason is refused.
    assert mod.main(["--out", str(out), "--force"]) == 2

    # --force with a reason succeeds and records it.
    assert mod.main(["--out", str(out), "--force", "--reason", "unit smoke"]) == 0
    rebuilt = __import__("json").loads(out.read_text(encoding="utf-8"))
    assert rebuilt["rebuild_of"]["reason"] == "unit smoke"
    assert mholdout.load_holdout_manifest(path=out)["manifest_sha256"] == rebuilt["manifest_sha256"]


def test_cli_dry_run_writes_nothing(monkeypatch, tmp_path: Path, capsys) -> None:
    mod = _import_build_script()
    splits = {
        "created": "2026-11-14",
        "test_period_start": "2024-01-01",
        "test_fields": [101],
        "kmeans": {"test_block_fields": [101]},
        "train_fields": [301],
        "cycles": {},
        "manifest_sha256": "f" * 64,
    }
    _patch_loader(monkeypatch, mod, splits)
    out = tmp_path / "holdout_manifest.json"
    assert mod.main(["--out", str(out), "--dry-run"]) == 0
    assert not out.exists(), "--dry-run must not write"
    assert "nothing written" in capsys.readouterr().out


def test_cli_skip_cycle_check_requires_dry_run(monkeypatch, tmp_path: Path, capsys) -> None:
    mod = _import_build_script()
    _patch_loader(monkeypatch, mod, {"test_fields": [1], "test_period_start": "2024-01-01"})
    rc = mod.main(["--out", str(tmp_path / "x.json"), "--skip-cycle-file-check"])
    assert rc == 2
    assert "--skip-cycle-file-check is only allowed for read-only inspection" in capsys.readouterr().err


def test_cli_reports_missing_splits_without_traceback(monkeypatch, tmp_path: Path, capsys) -> None:
    mod = _import_build_script()

    def boom(**kwargs):
        raise RuntimeError("splits_locked.json missing")

    monkeypatch.setattr(mod.msplits, "load_splits_locked", boom)
    assert mod.main(["--out", str(tmp_path / "x.json")]) == 2
    err = capsys.readouterr().err
    assert "cannot load the locked splits" in err


@pytest.mark.parametrize("end", ["2024-01-01", "2025-04-01", "2021-12-31", None])
def test_full_cycle_bounds_fail_closed(manifest, end):
    assert not mholdout.train_only_mask(
        [301], ["2022-01-01"], cycle_end_dates=[end], manifest=manifest,
    )[0]
    with pytest.raises(mholdout.HoldoutViolationError, match="301:7"):
        mholdout.assert_train_only(
            [301], ["301:7"], ["2022-01-01"], cycle_end_dates=[end], manifest=manifest,
        )


def test_archive_end_is_inclusive_for_cycle_bounds(manifest):
    manifest["archive_end_date"] = "2023-10-01"
    assert mholdout.train_only_mask(
        [301, 302], ["2022-01-01", "2022-01-01"],
        cycle_end_dates=["2023-10-01", "2023-10-02"], manifest=manifest,
    ).tolist() == [True, False]


def test_cli_audit_preserves_frozen_manifest_on_failure(monkeypatch, tmp_path, capsys):
    mod = _import_build_script()
    splits = {"test_period_start": "2024-01-01", "kmeans": {"test_block_fields": [101, 102]},
              "train_fields": [301], "manifest_sha256": "f" * 64}
    _patch_loader(monkeypatch, mod, splits)
    manifest = mholdout.build_holdout_manifest(splits)
    manifest["holdout_farms"] = [101, 301]
    manifest["manifest_sha256"] = mholdout.holdout_manifest_hash(manifest)
    path = mholdout.save_holdout_manifest(manifest, path=tmp_path / "holdout.json")
    before = path.read_bytes()
    capsys.readouterr()
    assert mod.main(["--audit-existing", "--skip-cycle-file-check", "--out", str(path)]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["missing_spatial_fields"] == [102]
    assert result["extra_frozen_fields"] == [301]
    assert path.read_bytes() == before
