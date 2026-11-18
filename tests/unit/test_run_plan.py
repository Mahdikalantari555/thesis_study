"""Pre-registered run plan + benchmark manifests.

Covers ``patch-full-run-and-ablations`` 1.1 and 1.2. The point of these tests
is that a plan/manifest cannot quietly lose information: a plan without its
hash is refused, an edited plan fails verification, a missing measurement is
None (never zero) and an incomplete manifest is rejected.
"""

from __future__ import annotations

import json

import pytest
import torch

from ssl_anomaly.models.patch_cnn_gru import build_patch_model
from ssl_anomaly.train import run_plan as RP


def _plan(**kw):
    base = {"seconds_per_epoch": 60.0, "epochs": 20, "seconds_per_eval": 30.0}
    base.update(kw)
    return RP.build_run_plan(**base)


# --- the plan ------------------------------------------------------------
def test_plan_names_every_ablation_axis():
    plan = _plan()
    factors = {c["factor"] for c in plan["cells"]}
    assert {"scale_up", "aux_weight", "channels", "covariates",
            "inner_buffer/burn_in", "sensor_offset", "ssl"} <= factors


def test_plan_writes_the_pruning_rule():
    plan = _plan()
    assert "ONE seed" in plan["pruning_rule"]
    assert plan["screening_seed"] == 13
    assert plan["final_seeds"] == [13, 42, 2026]
    assert plan["pre_named_finalists"]


def test_tcn_is_not_planned_unless_triggered():
    assert "E3_tcn" not in {c["run_id"] for c in _plan()["cells"]}
    assert "E3_tcn" in {c["run_id"] for c in _plan(include_tcn=True)["cells"]}


def test_every_cell_has_a_venue_estimate_and_output():
    for c in _plan()["cells"]:
        assert c["venue"] == "owner GPU"
        assert c["estimate_seconds"] > 0
        assert c["outputs"]
        assert c["stage"] in ("screening", "final")


def test_plan_hash_is_stable_and_content_sensitive():
    a, b = _plan(), _plan()
    # created timestamps differ; hash the payloads without them
    a.pop("created"), b.pop("created")
    assert RP.plan_sha256(a) == RP.plan_sha256(b)
    a["cells"][0]["estimate_seconds"] += 1
    assert RP.plan_sha256(a) != RP.plan_sha256(b)


def test_plan_roundtrip_and_verification(tmp_path):
    plan = _plan()
    p = RP.save_plan(plan, tmp_path / "plan.json")
    assert RP.load_plan(p)["sha256"] == plan["sha256"]


def test_an_edited_plan_fails_verification(tmp_path):
    plan = _plan()
    p = RP.save_plan(plan, tmp_path / "plan.json")
    payload = json.loads(p.read_text())
    payload["cells"][0]["seeds"] = [1, 2, 3]         # promote a cell after the fact
    p.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="hash mismatch"):
        RP.load_plan(p)


def test_a_plan_without_a_hash_is_not_pre_registered(tmp_path):
    plan = _plan()
    plan.pop("sha256")
    p = RP.save_plan(plan, tmp_path / "plan.json")
    with pytest.raises(ValueError, match="not pre-registered"):
        RP.load_plan(p)


def test_amendment_is_the_only_way_to_change_a_registered_plan():
    plan = _plan()
    amended = RP.amendment(plan, run_id="E3_tcn", reason="E3 trigger fired",
                           approved_by="owner")
    assert amended["sha256"] != plan["sha256"]
    assert amended["amendments"][0]["previous_sha256"] == plan["sha256"]
    assert plan["sha256"] == RP.plan_sha256(plan)     # original untouched
    with pytest.raises(ValueError, match="reason and an approver"):
        RP.amendment(plan, run_id="x", reason="", approved_by="owner")


def test_estimate_grows_with_epochs():
    a = _plan(epochs=10)["estimate"]["total_hours"]
    b = _plan(epochs=40)["estimate"]["total_hours"]
    assert b > a


# --- benchmarking --------------------------------------------------------
def test_ram_is_measured_or_absent_never_zero():
    v = RP.peak_ram_mb()
    assert v is None or v > 0


def test_cuda_peak_is_none_on_a_cpu_host_or_positive():
    v = RP.cuda_peak_mb()
    assert v is None or v > 0


def _model():
    torch.manual_seed(0)
    return build_patch_model(use_cnn=True, n_channels=8, d_model=8, n_horizons=2,
                             stem_widths=(8, 8))


def _example():
    """A forward-pass example: values float, pixel_valid BOOLEAN (the model's
    contract — a float mask raises 'where expected a boolean tensor')."""
    return torch.zeros(1, 4, 8, 32, 32), torch.ones(1, 4, 32, 32, dtype=torch.bool)


def test_macs_are_positive_and_scale_with_channels():
    m = _model()
    ex = _example()
    macs = RP.count_macs(m, ex)
    assert macs is not None
    assert macs > 0
    m2 = build_patch_model(use_cnn=True, n_channels=8, d_model=16, n_horizons=2,
                           stem_widths=(16, 16))
    assert RP.count_macs(m2, ex) > macs


def test_macs_returns_none_on_a_shape_mismatch_instead_of_guessing():
    m = _model()
    assert RP.count_macs(m, torch.zeros(1, 4, 3, 32, 32)) is None


def test_inference_time_is_positive():
    m = _model()
    ex = _example()
    ms = RP.time_inference(m, ex, repeats=2)
    assert ms is not None
    assert ms > 0


def test_benchmark_block_measures_what_it_can_and_leaves_the_rest_none():
    m = _model()
    b = RP.benchmark_block(m, _example())
    assert set(RP.BENCHMARK_FIELDS) <= set(b)
    assert b["n_parameters"] > 0
    assert b["macs_per_forward"] > 0
    assert b["torch_version"] == torch.__version__
    assert b["device"] in ("cpu", "cuda")


def test_benchmark_block_without_a_model_leaves_numbers_none():
    b = RP.benchmark_block()
    assert b["n_parameters"] is None
    assert b["macs_per_forward"] is None
    assert b["recorded_at"]


# --- manifest validation -------------------------------------------------
def _manifest(**over):
    base = {
        "arch": "patch_cnn_gru", "seed": 13,
        "n_parameters": 1000, "wall_time_s": 12.0, "device": "cpu",
        "git_sha": "abc", "data_source": "patches.zarr",
        "holdout_sha256": "h", "norm_sha256": "n",
        "config_hash": "c",
    }
    base.update(over)
    return base


def test_complete_manifest_validates():
    m = RP.attach_benchmark(_manifest(), RP.benchmark_block())
    assert RP.validate_manifest(m) == []


def test_a_manifest_may_carry_seeds_in_place_of_seed():
    m = _manifest()
    m.pop("seed")
    m["seeds"] = [13, 42]
    m["benchmark"] = RP.benchmark_block()
    assert RP.validate_manifest(m) == []


def test_missing_core_field_is_named():
    m = _manifest(git_sha="")
    m["benchmark"] = RP.benchmark_block()
    assert RP.validate_manifest(m) == ["git_sha"]
    # ...and attach_benchmark refuses to attach it in the first place
    with pytest.raises(ValueError, match="git_sha"):
        RP.attach_benchmark(_manifest(git_sha=""), RP.benchmark_block())


def test_absent_benchmark_block_is_rejected():
    assert "benchmark.peak_ram_mb" in RP.validate_manifest(_manifest())


def test_a_none_measurement_is_acceptable_but_a_missing_key_is_not():
    block = RP.benchmark_block()
    block["cuda_peak_mb"] = None                 # legitimate: no CUDA
    m = RP.attach_benchmark(_manifest(), block)
    assert RP.validate_manifest(m) == []
    block.pop("macs_per_forward")
    with pytest.raises(ValueError, match="manifest incomplete"):
        RP.attach_benchmark(_manifest(), block)


def test_legacy_manifests_can_skip_the_benchmark_check():
    assert RP.validate_manifest(_manifest(), require_benchmark=False) == []
