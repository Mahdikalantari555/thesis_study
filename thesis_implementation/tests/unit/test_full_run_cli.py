"""CLIs for ``patch-full-run-and-ablations`` 1.1 / 1.2 / 2.5.

``scripts/run_plan.py`` (register/verify/amend) and ``scripts/sensor_offset.py``
(pair finding + estimation against a real store). The store here is a tiny
synthetic one built with ``patches.create_store``, so the offset script's
loading path is exercised without the archive.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RP_CLI = _load("run_plan")
SO_CLI = _load("sensor_offset")

from ssl_anomaly.io import patches as P  # noqa: E402
from ssl_anomaly.train import run_plan as RP  # noqa: E402


# --- run_plan.py ----------------------------------------------------------
def test_register_writes_a_verifiable_plan(tmp_path, capsys):
    p = tmp_path / "plan.json"
    assert RP_CLI.main(["--register", "--plan", str(p), "--epochs", "10"]) == 0
    assert RP.load_plan(p)["cell_count"] > 0
    assert "total_hours" in capsys.readouterr().out


def test_registering_twice_is_refused(tmp_path, capsys):
    p = tmp_path / "plan.json"
    RP_CLI.main(["--register", "--plan", str(p)])
    assert RP_CLI.main(["--register", "--plan", str(p)]) == 2
    assert "already registered" in capsys.readouterr().err


def test_verify_passes_then_fails_after_an_edit(tmp_path):
    p = tmp_path / "plan.json"
    RP_CLI.main(["--register", "--plan", str(p)])
    assert RP_CLI.main(["--verify", "--plan", str(p)]) == 0
    payload = json.loads(p.read_text())
    payload["estimate"]["total_hours"] = 0.1
    p.write_text(json.dumps(payload))
    assert RP_CLI.main(["--verify", "--plan", str(p)]) == 1


def test_verify_of_a_missing_plan_is_an_error(tmp_path):
    assert RP_CLI.main(["--verify", "--plan", str(tmp_path / "nope.json")]) == 1


def test_show_prints_the_plan(tmp_path, capsys):
    p = tmp_path / "plan.json"
    RP_CLI.main(["--register", "--plan", str(p)])
    capsys.readouterr()
    assert RP_CLI.main(["--show", "--plan", str(p)]) == 0
    assert '"cells"' in capsys.readouterr().out


def test_amend_records_the_reason_and_changes_the_hash(tmp_path):
    p = tmp_path / "plan.json"
    RP_CLI.main(["--register", "--plan", str(p)])
    first = RP.load_plan(p)["sha256"]
    code = RP_CLI.main(["--amend", "--plan", str(p), "--run-id", "E3_tcn",
                        "--reason", "E3 trigger fired", "--approved-by", "owner"])
    assert code == 0
    after = RP.load_plan(p)
    assert after["sha256"] != first
    assert after["amendments"][0]["reason"] == "E3 trigger fired"


def test_amend_without_an_approver_is_refused(tmp_path, capsys):
    p = tmp_path / "plan.json"
    RP_CLI.main(["--register", "--plan", str(p)])
    assert RP_CLI.main(["--amend", "--plan", str(p), "--run-id", "x",
                        "--reason", "y"]) == 2


def test_include_tcn_adds_the_challenger_cell(tmp_path):
    p = tmp_path / "plan.json"
    RP_CLI.main(["--register", "--plan", str(p), "--include-tcn"])
    assert "E3_tcn" in {c["run_id"] for c in RP.load_plan(p)["cells"]}


# --- sensor_offset.py -----------------------------------------------------
def _pairs_store(tmp_path, *, n=12, offset_red=0.02):
    """Interleaved store: each L8 cycle has an L9 cycle one day later."""
    root = P.create_store(tmp_path / "p.zarr", field_ids=[7],
                          max_cycles=2 * n, size=4)
    root["field_ids"][:] = [7]
    inf = np.zeros((1, 1, 4, 4), dtype=np.uint8)      # in_field is (F, 1, S, S)
    inf[0, 0, 1:3, 1:3] = 1
    root["in_field"][:] = inf
    ci = P.CHANNELS.index("red")
    for j in range(2 * n):
        is_l8 = j % 2 == 0
        vals = np.full((P.N_BINS, P.N_CHANNELS, 4, 4), np.nan, dtype=np.float16)
        vals[:, ci, 1:3, 1:3] = 0.30 + (offset_red if is_l8 else 0.0)
        root["values"][0, j] = vals
        pv = np.zeros((P.N_BINS, 1, 4, 4), dtype=np.uint8)
        pv[:, 0, 1:3, 1:3] = 1
        root["pixel_valid"][0, j] = pv
        root["sensor_id"][0, j, :] = 1 if is_l8 else 2
        root["n_obs"][0, j, :] = 1
        root["cycle_start_day"][0, j] = 100 + j
        root["cycle_valid"][0, j] = 1
    return tmp_path / "p.zarr"


def test_load_cycles_skips_unknown_sensors_and_invalid_cycles(tmp_path):
    root = P.open_store(_pairs_store(tmp_path), mode="a")
    cycles, stats = SO_CLI.load_cycles(root)
    assert len(cycles) == 24
    assert {c.sensor for c in cycles} == {"L8", "L9"}
    assert stats["n_mixed_sensor_cycles"] == 0
    root["cycle_valid"][0, 0] = 0                    # invalid cycle
    root["sensor_id"][0, 1, :] = 0                   # unknown sensor
    cycles, stats = SO_CLI.load_cycles(root)
    assert len(cycles) == 22
    assert stats["n_unknown_sensor_cycles"] == 1


def test_a_cycle_spanning_both_sensors_is_skipped_and_counted(tmp_path):
    """sensor_id is PER BIN: L9 enters mid-cycle, so the cycle is not a pair."""
    root = P.open_store(_pairs_store(tmp_path), mode="a")
    root["sensor_id"][0, 0, 0] = 2                   # cycle 0 was L8, now mixed
    cycles, stats = SO_CLI.load_cycles(root)
    assert stats["n_mixed_sensor_cycles"] == 1
    assert all(c.cycle_id != 0 for c in cycles)


def test_a_cycle_with_no_observed_bin_is_skipped(tmp_path):
    root = P.open_store(_pairs_store(tmp_path), mode="a")
    root["n_obs"][0, 0, :] = 0
    cycles, stats = SO_CLI.load_cycles(root)
    assert stats["n_empty_cycles"] == 1
    assert all(c.cycle_id != 0 for c in cycles)


def test_dry_run_finds_pairs_and_writes_nothing(tmp_path, capsys):
    store = _pairs_store(tmp_path)
    out = tmp_path / "offsets.json"
    assert SO_CLI.main(["--store", str(store), "--out", str(out), "--dry-run"]) == 0
    assert not out.exists()
    assert "near-coincident pairs" in capsys.readouterr().out


def test_the_script_writes_a_table_with_the_comparison_plan(tmp_path):
    store = _pairs_store(tmp_path)
    out = tmp_path / "offsets.json"
    assert SO_CLI.main(["--store", str(store), "--out", str(out), "--bands", "red",
                        "--min-pairs", "5"]) == 0
    payload = json.loads(out.read_text())
    assert payload["bands"]["red"]["offset"] == pytest.approx(0.02, abs=5e-3)
    assert payload["reference_sensor"] == "L9"
    assert payload["comparison"]["arms"] == ["offsets_off", "offsets_on"]
    assert payload["n_pairs_found"] == 12


def test_bands_are_read_off_their_own_channel_row(tmp_path):
    """``red`` is channel 3, not channel 0 — the offset must come from red."""
    out = tmp_path / "o.json"
    SO_CLI.main(["--store", str(_pairs_store(tmp_path)), "--out", str(out),
                 "--bands", "red,nir", "--min-pairs", "5"])
    payload = json.loads(out.read_text())
    assert payload["bands"]["red"]["offset"] == pytest.approx(0.02, abs=5e-3)
    # nir has no finite value in this store: reported as skipped, not as zero
    assert payload["skipped_bands"] == ["nir"]


def test_require_resolved_fails_on_an_unresolved_band(tmp_path, capsys):
    store = _pairs_store(tmp_path, offset_red=0.0)      # no offset at all
    code = SO_CLI.main(["--store", str(store), "--out", str(tmp_path / "o.json"),
                        "--bands", "red", "--min-pairs", "5", "--require-resolved"])
    assert code == 2
    assert "refusing" in capsys.readouterr().err


def test_no_pairs_is_a_clean_failure(tmp_path, capsys):
    root = P.create_store(tmp_path / "q.zarr", field_ids=[7], max_cycles=2, size=4)
    root["field_ids"][:] = [7]
    root["cycle_valid"][:] = 0
    code = SO_CLI.main(["--store", str(tmp_path / "q.zarr"),
                        "--out", str(tmp_path / "o.json")])
    assert code == 1
    assert "no pairs" in capsys.readouterr().err
