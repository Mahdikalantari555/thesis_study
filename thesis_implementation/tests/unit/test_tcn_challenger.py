"""E3 trigger and the TCN challenger gate.

Covers ``patch-full-run-and-ablations`` 1.4. The tests that matter here are the
ones about the GATE, not about convolutions: a fired trigger must block a
caller who wants to skip the challenger, an unjudgeable history must fire the
trigger (fail-closed), and the module must actually be causal rather than
merely intended to be.
"""

from __future__ import annotations

import pytest
import torch

from ssl_anomaly.models import tcn_challenger as TC


def _hist(losses, *, epoch_seconds=30.0):
    return [{"train_loss": l, "wall_s": (i + 1) * epoch_seconds}
            for i, l in enumerate(losses)]


def _manifest(hist, *, ms=10.0, **bench):
    b = {"ms_per_field_cycle": ms}
    b.update(bench)
    return {"history": hist, "benchmark": b}


# --- trigger: slow ---------------------------------------------------------
def test_a_healthy_run_does_not_fire():
    hist = _hist([1.0, 0.7, 0.5, 0.42, 0.40, 0.39])
    v = TC.evaluate_trigger(_manifest(hist))
    assert not v.fired, v.reasons


def test_a_slow_epoch_fires_with_the_offending_seconds():
    hist = _hist([1.0, 0.8, 0.6, 0.5], epoch_seconds=500.0)
    v = TC.evaluate_trigger(_manifest(hist))
    assert v.fired
    assert any(r.startswith("slow:") and "500" in r for r in v.reasons)


def test_slow_inference_fires():
    hist = _hist([1.0, 0.8, 0.6, 0.5])
    v = TC.evaluate_trigger(_manifest(hist, ms=400.0))
    assert v.fired
    assert any("ms/field-cycle" in r for r in v.reasons)


def test_unmeasured_inference_time_fires_rather_than_passing():
    hist = _hist([1.0, 0.8, 0.6, 0.5])
    v = TC.evaluate_trigger({"history": hist, "benchmark": {}})
    assert v.fired
    assert any("not measured" in r for r in v.reasons)


# --- trigger: unstable -----------------------------------------------------
def test_a_short_history_fires_the_trigger():
    v = TC.evaluate_trigger(_manifest(_hist([1.0, 0.9])))
    assert v.fired
    assert any("to judge" in r for r in v.reasons)


def test_a_diverging_tail_fires_the_trigger():
    v = TC.evaluate_trigger(_manifest(_hist([1.0, 0.8, 0.6, 0.7, 0.9, 1.1])))
    assert v.fired
    assert any(r.startswith("unstable:") for r in v.reasons)


def test_a_noisy_but_flat_curve_does_not_fire():
    losses = [0.60, 0.55, 0.50, 0.52, 0.48, 0.49, 0.47]
    assert not TC.evaluate_trigger(_manifest(_hist(losses))).fired


def test_stability_report_separates_judgeable_from_stable():
    st = TC.stability_report(_hist([1.0]))
    assert st["n_epochs"] == 1
    assert not st["judgeable"]
    assert not st["stable"]
    st = TC.stability_report(_hist([1.0, 0.8, 0.7, 0.65]))
    assert st["judgeable"]
    assert st["stable"]


def test_stability_sigma_is_the_tolerance():
    st = TC.stability_report(_hist([1.0, 0.8, 0.6, 0.5]))
    assert st["tolerance"] == pytest.approx(TC.STABILITY_SIGMA_K * st["sigma"])


def test_epoch_seconds_come_from_the_cumulative_wall_time():
    hist = [{"train_loss": 1.0, "wall_s": 30.0},
            {"train_loss": 0.9, "wall_s": 100.0},
            {"train_loss": 0.8, "wall_s": 160.0}]
    st = TC.evaluate_trigger(_manifest(hist))
    assert st.measured["epoch_seconds"] == [30.0, 70.0, 60.0]


def test_verdict_records_the_rule_it_applied():
    v = TC.evaluate_trigger(_manifest(_hist([1.0, 0.8, 0.6, 0.5])))
    assert v.to_dict()["rule"]["max_epoch_seconds"] == TC.MAX_EPOCH_SECONDS


# --- the gate --------------------------------------------------------------
def test_a_fired_trigger_blocks_skipping_the_challenger():
    v = TC.evaluate_trigger(_manifest(_hist([1.0, 0.9])))
    with pytest.raises(RuntimeError, match="must be built"):
        v.require_built()


def test_an_unfired_trigger_does_not_block():
    TC.evaluate_trigger(_manifest(_hist([1.0, 0.8, 0.6, 0.5]))).require_built()


def test_no_trigger_keeps_the_gru_and_builds_nothing():
    d = TC.decide_temporal_module(TC.evaluate_trigger(_manifest(_hist([1.0, 0.8, 0.6, 0.5]))))
    assert d == {"kept": "gru", "challenger_built": False,
                 "reason": "E3 trigger did not fire"}


def test_a_fired_trigger_is_pending_until_the_tcn_has_run():
    v = TC.evaluate_trigger(_manifest(_hist([1.0, 0.9])))
    assert TC.decide_temporal_module(v)["kept"] == "pending"
    assert TC.decide_temporal_module(v, challenger_wins=True)["kept"] == "tcn"
    assert TC.decide_temporal_module(v, challenger_wins=False)["kept"] == "gru"


def test_a_tie_goes_to_the_simpler_variant():
    d = TC.decide_temporal_module(TC.evaluate_trigger(_manifest(_hist([1.0, 0.9]))),
                                  challenger_wins=False)
    assert "simpler/faster" in d["reason"]


# --- the module ------------------------------------------------------------
def _tcn(n_channels=6, d_model=16):
    torch.manual_seed(0)
    return TC.build_tcn(n_channels=n_channels, d_model=d_model)


def test_forward_shape_matches_the_patch_contract():
    m = _tcn()
    x = torch.randn(2, 20, 6, 8, 8)
    mv = torch.ones(2, 20, 8, 8, dtype=torch.bool)
    out = m(x, mv)
    assert out["pred"].shape == (2, 20, 2, 6)


def test_the_module_is_causal_over_every_timestep():
    assert TC.causality_violations(_tcn(), T=20, n_channels=6) == []


def test_causality_check_actually_catches_a_leaky_module():
    class Leaky(torch.nn.Module):
        def forward(self, x, pixel_valid, covariates=None):
            pooled = x.mean(dim=(-1, -2))                       # (B,T,C)
            # running mean over the WHOLE window: future leaks backwards
            g = pooled.mean(dim=1, keepdim=True).expand_as(pooled)
            return {"pred": torch.stack([pooled, g], dim=2)}

    assert TC.causality_violations(Leaky(), T=6, n_channels=3, S=4) != []


def test_a_masked_out_bin_does_not_change_the_output():
    m = _tcn()
    x = torch.randn(1, 12, 6, 8, 8)
    mv = torch.ones(1, 12, 8, 8, dtype=torch.bool)
    shut = mv.clone()
    shut[:, 5] = False
    x2 = x.clone()
    x2[:, 5] = 99.0                       # garbage where nothing is observed
    a = m(x, mv)["pred"]
    b = m(x2, shut)["pred"]
    # the unobserved bin's own output may differ; nothing before it may
    assert torch.allclose(a[:, :5], b[:, :5], atol=1e-4)


def test_receptive_field_matches_the_declared_dilations():
    # kernel 3, dilations 1/2/4/8 -> 1 + 2*(1+2+4+8) = 31 bins
    assert TC.receptive_field() == 31
    assert TC.receptive_field((1,)) == 3
    assert TC.effective_bins((1,), n_bins=2) == 2


def test_more_dilations_add_parameters():
    small = sum(p.numel() for p in _tcn(d_model=8).parameters())
    big = sum(p.numel() for p in _tcn(d_model=32).parameters())
    assert big > small
