from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = str(Path(__file__).resolve().parents[2] / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def test_parse_drop_spec_and_mini_ablation():
    from run_ablation import parse_drop_spec, run_ablation_suite

    assert parse_drop_spec("none") == (set(), True)
    assert parse_drop_spec("lst") == ({"ST_B10"}, True)
    assert parse_drop_spec("weather") == (set(), False)
    assert parse_drop_spec("lst+weather") == ({"ST_B10"}, False)
    assert parse_drop_spec("SR_B5") == ({"SR_B5"}, True)

    rep = run_ablation_suite(drops=["none", "lst", "weather"], seeds=[42, 43], epochs=3)
    assert set(rep["configs"].keys()) == {"none", "lst", "weather"}
    for k in ("none", "lst", "weather"):
        metrics = rep["configs"][k]["metrics"]
        assert "ssl_val_band_loss" in metrics
        assert len(metrics["ssl_val_band_loss"]["ci_95"]) == 2
        assert len(metrics["b1_auc_pr"]["delta_ci_95"]) == 2
