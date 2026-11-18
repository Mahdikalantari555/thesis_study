"""``run_generalization_matrix.py``: plan / estimate / report modes.

Covers the data-free half of ``patch-generalization-suite`` 1.2: the CLI must
be able to plan the matrix, estimate its cost and aggregate artifacts without
touching a store — and ``--execute`` must REFUSE rather than silently train on
the held-out blocks.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "run_gen", REPO / "scripts" / "run_generalization_matrix.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)

from ssl_anomaly.monitor import generalization as G  # noqa: E402
from ssl_anomaly.monitor import generalization_matrix as GM  # noqa: E402


def _folds_file(tmp_path):
    xy = {b + 1: ((b // 2) * 100.0, (b % 2) * 100.0) for b in range(10)}
    block_of = {b + 1: b for b in range(10)}
    folds = G.build_folds(block_of, xy)
    p = tmp_path / "folds.json"
    R.save_folds(p, folds, source="test")
    return p, folds


def test_plan_writes_a_frozen_fold_file(tmp_path, capsys):
    p, folds = _folds_file(tmp_path)
    code = R.main(["--plan", "--folds", str(p)])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["folds_sha256"] == G.folds_sha256(folds)
    assert len(payload["cells"]) == 11


def test_fold_file_roundtrip_preserves_the_hash(tmp_path):
    p, folds = _folds_file(tmp_path)
    again = R.folds_from_file(p)
    assert G.folds_sha256(again) == G.folds_sha256(folds)


def test_plan_from_a_fields_parquet_builds_and_saves_folds(tmp_path, capsys):
    import pandas as pd

    rows = []
    for b in range(10):
        for k in range(2):
            rows.append({"field_id": b * 10 + k + 1, "block": b,
                         "x": (b // 2) * 100.0, "y": (b % 2) * 100.0 + k})
    f = tmp_path / "fields.parquet"
    pd.DataFrame(rows).to_parquet(f, index=False)
    out = tmp_path / "folds_built.json"
    code = R.main(["--plan", "--build-folds", str(f), "--out", str(out)])
    assert code == 0
    assert out.is_file()
    assert "folds_sha256" in json.loads(out.read_text())


def test_estimate_runtime_mode_reads_no_store(tmp_path, capsys):
    p, _ = _folds_file(tmp_path)
    code = R.main(["--estimate-runtime", "--folds", str(p),
                   "--seconds-per-epoch", "10", "--epochs", "2",
                   "--seconds-per-eval", "1"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["n_cells"] == 11
    assert payload["total_hours"] >= 0


def test_report_aggregates_artifacts_and_applies_acceptance(tmp_path, capsys):
    p, folds = _folds_file(tmp_path)
    cells = GM.plan_matrix(folds, temporal_cutoff_day=100)
    d = tmp_path / "artifacts"
    for cell in cells:
        GM.write_cell_artifact(d, arm="patch_cnn_gru", cell=cell, seed=13,
                               metrics={"mdm80": {"acute/ndvi": "S3"},
                                        "sensor_era": "L8"})
    code = R.main(["--report", "--dir", str(d), "--dev-se", "0.5", "--in-block", "3"])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["verdicts"]["patch_cnn_gru"]["pass"] is True
    report = json.loads((d / "matrix_report.json").read_text())
    assert report["n_records"] == len(cells)
    assert "confounded" in report["sensor_confound_note"]


def test_report_without_artifacts_is_a_clean_error(tmp_path, capsys):
    code = R.main(["--report", "--dir", str(tmp_path / "empty")])
    assert code == 2
    assert "no cell artifacts" in capsys.readouterr().err


@pytest.mark.parametrize("store_exists", [False, True])
def test_execute_refuses_without_fold_aware_evaluation(tmp_path, capsys, store_exists):
    """The critical guard: never train on the held-out blocks by omission."""
    p, folds = _folds_file(tmp_path)
    if store_exists:
        (tmp_path / "folds" / "fold_0.zarr").mkdir(parents=True)
    code = R.main(["--execute", "--folds", str(p), "--dir", str(tmp_path / "d"),
                   "--fold-store-dir", str(tmp_path / "folds")])
    assert code == 2
    assert not (tmp_path / "d").exists()
    err = capsys.readouterr().err
    assert "[blocked]" in err
    assert "leak" in err


def test_execute_dry_run_prints_the_plan(tmp_path, capsys):
    p, folds = _folds_file(tmp_path)
    code = R.main(["--execute", "--dry-run", "--folds", str(p),
                   "--dir", str(tmp_path / "d")])
    assert code == 0
    out = capsys.readouterr().out
    assert "would train" in out
    assert "patch_cnn_gru" in out
    assert "patch_pixelwise" in out


def test_no_mode_prints_help(tmp_path):
    assert R.main([]) == 2


def test_fields_file_without_blocks_is_named(tmp_path):
    import pandas as pd

    f = tmp_path / "f.parquet"
    pd.DataFrame({"field_id": [1], "x": [0.0], "y": [0.0]}).to_parquet(f, index=False)
    with pytest.raises(ValueError, match="block column"):
        R.load_field_coordinates(f)


def test_fields_file_without_coordinates_is_named(tmp_path):
    import pandas as pd

    f = tmp_path / "f.parquet"
    pd.DataFrame({"field_id": [1], "block": [0]}).to_parquet(f, index=False)
    with pytest.raises(ValueError, match="centroid"):
        R.load_field_coordinates(f)
