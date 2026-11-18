"""Comprehensive unit tests for Phase 1–2 completion & RQ1–RQ8 empirical framework."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import torch
from click.testing import CliRunner
from omegaconf import OmegaConf

from ssl_anomaly.baseline import (
    CWSIThresholdAlarm,
    GBTBaseline,
    NDVIThresholdAlarm,
    RFBaseline,
    cusum_detector,
    ewma_detector,
    precision_at_alert_budget,
    recall_at_alert_budget,
)
from ssl_anomaly.cli import cli
from ssl_anomaly.eval import (
    analyze_false_alarm_confounders,
    build_expert_event_review_packet,
    cluster_field_ci,
    compare_detectors_wilcoxon_holm,
    evaluate_e_align_three_metrics,
    evaluate_e_norm_trimming_stability,
    evaluate_stress_validation_gate,
    generate_splits_dict,
    get_archive_provenance,
    load_real490_archive,
    require_real_archive,
    run_cloud_completeness_benchmark,
    run_contamination_sweep,
    run_loyo_early_detection,
    run_rq7_probing_suite,
    save_splits_json,
    simulate_490_field_archive,
    simulate_progressive_onset_archive,
    simulated_output_path,
    subsample_cloud_completeness,
)
from ssl_anomaly.io.era5 import compute_dynamic_gdd_from_era5, load_era5_zarr, write_era5_zarr
from ssl_anomaly.models import (
    PRETEXT_ARMS,
    PretextTransformer,
    info_nce_loss,
    score_cycle_pretext,
    train_pretext_arm,
)
from ssl_anomaly.phenology import savitzky_golay_8day
from ssl_anomaly.utils.tracking import log_run_metrics_and_artifacts, track_experiment_run
from ssl_anomaly.xai import (
    aggregate_to_sugarcane_stages,
    deletion_insertion_auc,
    integrated_gradients_attribution,
    physiology_sign_concordance,
    temporal_grad_cam_attribution,
    temporal_shap_attribution,
    weight_randomization_sanity_check,
    window_occlusion_attribution,
)


def test_cusum_ewma_and_savgol() -> None:
    clean = np.full(36, 0.4, dtype=np.float64)
    drifting = clean.copy()
    drifting[15:26] = 2.1  # sub-3.5-sigma sustained slow drift
    f_clean, stat_c = cusum_detector(clean, drift_k=1.0, decision_h=4.0)
    f_drift, stat_d = cusum_detector(drifting, drift_k=1.0, decision_h=4.0)
    assert not np.any(f_clean)
    assert np.any(f_drift)
    assert float(np.nanmax(stat_d)) > float(np.nanmax(stat_c))

    ef_clean, ew_c = ewma_detector(clean, alpha=0.3)
    ef_drift, ew_d = ewma_detector(drifting, alpha=0.3)
    assert not np.any(ef_clean)
    assert np.any(ef_drift)
    assert float(np.nanmax(ew_d)) > float(np.nanmax(ew_c))

    t_obs = np.array([0, 12, 24, 40, 56, 72, 88, 104], dtype=np.int64)
    v_obs = np.sin(np.linspace(0.1, 2.5, len(t_obs)))
    grid, sm = savitzky_golay_8day(t_obs, v_obs, window_length=5, polyorder=2)
    assert grid.shape == sm.shape
    assert np.all(np.isfinite(sm))


def test_standalone_era5_zarr_and_dynamic_gdd(tmp_path: Path) -> None:
    out = tmp_path / "era5.zarr"
    times = np.arange(np.datetime64("2022-01-01"), np.datetime64("2022-02-10"), dtype="datetime64[D]")
    n_t = len(times)
    write_era5_zarr(
        times,
        {"tmean": np.full(n_t, 22.0), "et0": np.full(n_t, 5.0), "rad": np.full(n_t, 20.0), "rh": np.full(n_t, 45.0)},
        out,
    )
    ds = load_era5_zarr(out)
    q_t = np.array([np.datetime64("2022-01-01"), np.datetime64("2022-01-11")], dtype="datetime64[D]")
    gdd_12 = compute_dynamic_gdd_from_era5(ds, np.datetime64("2022-01-01"), q_t, t_base=12.0)
    gdd_15 = compute_dynamic_gdd_from_era5(ds, np.datetime64("2022-01-01"), q_t, t_base=15.0)
    assert np.isclose(gdd_12[-1], 100.0)
    assert gdd_12[-1] > gdd_15[-1]


def test_operational_baselines_and_cv_splits(tmp_path: Path) -> None:
    arch = simulate_490_field_archive(n_fields=18, n_years=6.0, seed=7)
    X, y = arch["X"], arch["y_stress"]
    tr = y == 0

    ndvi_alarm = NDVIThresholdAlarm(ndvi_band_idx=7).fit(X[tr])
    cwsi_alarm = CWSIThresholdAlarm(lst_band_idx=6).fit(X[tr])
    s_ndvi = ndvi_alarm.score_cycles(X)
    s_cwsi = cwsi_alarm.score_cycles(X)
    assert s_ndvi.shape == (len(X),)
    assert s_cwsi.shape == (len(X),)

    rf = RFBaseline(seed=7).fit(X[:50], y[:50])
    gbt = GBTBaseline(seed=7).fit(X[:50], y[:50])
    s_rf = rf.score_cycles(X[50:])
    s_gbt = gbt.score_cycles(X[50:])
    assert np.all(np.isfinite(s_rf))
    assert np.all(np.isfinite(s_gbt))
    assert 0.0 <= recall_at_alert_budget(y[50:], s_gbt, 0.10) <= 1.0
    assert 0.0 <= precision_at_alert_budget(y[50:], s_gbt, 0.10) <= 1.0

    import pandas as pd

    cyc_df = pd.DataFrame(
        {
            "field": arch["field_ids"],
            "cycle_id": np.arange(len(X)),
            "censored": np.zeros(len(X), dtype=bool),
            "t_start": (arch["start_years"] - 2013) * 365,
        }
    )
    sp_path = tmp_path / "splits.json"
    sp = generate_splits_dict(cyc_df, np.datetime64("2013-01-01"))
    saved = save_splits_json(sp, sp_path)
    assert saved.exists()
    assert len(sp["splits_sha256"]) == 16

    m, lo, hi = cluster_field_ci(s_cwsi, arch["field_ids"], n_boot=100, seed=7)
    assert lo <= m <= hi
    comp = compare_detectors_wilcoxon_holm({"cwsi": s_cwsi, "ndvi": s_ndvi}, arch["field_ids"], "cwsi")
    assert len(comp) == 1
    assert "p_holm" in comp[0]


def test_rq2_three_pretext_arms() -> None:
    rng = np.random.default_rng(11)
    toks = [rng.normal(0, 1, size=(20, 8)).astype(np.float32) for _ in range(24)]
    z = torch.randn(8, 16)
    loss_nce = info_nce_loss(z, z + 0.1 * torch.randn(8, 16))
    assert float(loss_nce.item()) >= 0.0

    for arm in PRETEXT_ARMS:
        m = train_pretext_arm(arm, toks, n_bands=7, epochs=2, batch_size=12, seed=11)
        assert isinstance(m, PretextTransformer)
        sc = score_cycle_pretext(m, toks[0])
        assert np.isfinite(sc)


def test_rq4_cloud_and_rq5_early_detection() -> None:
    rng = np.random.default_rng(19)
    seq = rng.normal(0, 1, size=(30, 11)).astype(np.float32)
    sub, idx = subsample_cloud_completeness(seq, 0.50, rng)
    assert sub.shape[0] == len(idx) == 15

    X_ax = rng.normal(0, 1, size=(24, 18, 4))
    fids = np.repeat(np.arange(6), 4)
    ea = evaluate_e_align_three_metrics({"DSH": X_ax, "DOY": X_ax * 1.1}, fids, seed=19)
    assert "within_bin_normalized_mad" in ea["DSH"]
    en = evaluate_e_norm_trimming_stability(X_ax, fids, q_values=(0.0, 0.15, 0.25))
    assert np.isclose(en["q_0.15_vs_0.15_spearman"], 1.0)

    arch_c = simulate_490_field_archive(n_fields=12, n_years=5.0, seed=19)
    cb = run_cloud_completeness_benchmark(arch_c["X"], arch_c["y_stress"], epochs=2, seeds=(19,))
    assert "completeness_100pct" in cb
    assert "completeness_35pct" in cb

    prog = simulate_progressive_onset_archive(n_cycles=70, K=24, stress_frac=0.3, seed=19)
    res5 = run_loyo_early_detection(prog, false_alarm_budget=0.10, seed=19)
    assert "SSL_Causal_OpticalThermal" in res5["methods"]
    assert np.isfinite(res5["ssl_lead_time_vs_ndvi_mean_days"])


def test_rq6_temporal_xai_and_faithfulness() -> None:
    rng = np.random.default_rng(23)
    toks = [rng.normal(0, 0.4, size=(18, 8)).astype(np.float32) for _ in range(24)]
    model = train_pretext_arm("masked_recon", toks, n_bands=7, epochs=3, batch_size=12, seed=23)
    base = np.zeros((18, 8), dtype=np.float32)
    x_anom = base.copy()
    x_anom[6:10, 3] = -3.0  # NIR canopy loss
    x_anom[6:10, 6] = +3.2  # ST_B10 heating

    ig, grad = integrated_gradients_attribution(model, x_anom, base, steps=8)
    cam = temporal_grad_cam_attribution(model, x_anom, base)
    occ = window_occlusion_attribution(model, x_anom, base, window=2)
    shap_a = temporal_shap_attribution(model, x_anom, base, n_time_blocks=3, n_samples=24, seed=23)

    for a in (ig, grad, cam, occ, shap_a):
        assert a.shape == (18, 7)
        assert np.all(np.isfinite(a))

    st = aggregate_to_sugarcane_stages(ig)
    assert pytest.approx(sum(st.values()), rel=1e-4) == 1.0

    faith = deletion_insertion_auc(model, x_anom, base, ig, steps=5, seed=23)
    assert faith["deletion_auc"] < faith["random_deletion_auc"]
    san = weight_randomization_sanity_check(
        lambda m, x, b: window_occlusion_attribution(m, x, b, window=2), model, x_anom, base
    )
    assert "passes_sanity_threshold_0.35" in san

    bands = ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7", "ST_B10"]
    phys = physiology_sign_concordance(ig, x_anom, base, bands, np.arange(5, 11))
    assert phys["overall_physiology_sign_concordance"] >= 0.5


def test_validation_gate_rq7_probing_and_rq8_contamination() -> None:
    rng = np.random.default_rng(31)
    y = np.array([0] * 40 + [1] * 15)
    sc_full = y * 3.0 + rng.normal(0, 0.3, len(y))
    sc_opt = y * 2.5 + rng.normal(0, 0.4, len(y))
    eta_def = y * 0.4 + rng.normal(0, 0.05, len(y))
    cwsi = y * 0.5 + rng.normal(0, 0.05, len(y))

    # Circular CWSI-only MUST be rejected ("unvalidated_spectral_thermal_anomaly")
    g_bad = evaluate_stress_validation_gate(full_anomaly_scores=sc_full, cwsi_proxy=cwsi)
    assert not g_bad["gate_passed"]
    assert g_bad["permitted_terminology"] == "unvalidated_spectral_thermal_anomaly"

    # Non-circular multi-proxy gate MUST pass ("validated_crop_stress_indicator")
    g_ok = evaluate_stress_validation_gate(
        full_anomaly_scores=sc_full,
        optical_only_anomaly_scores=sc_opt,
        eta_deficit=eta_def,
        cwsi_proxy=cwsi,
        independent_stress_events=y,
        top_k=10,
    )
    assert g_ok["gate_passed"]
    assert g_ok["permitted_terminology"] == "validated_crop_stress_indicator"

    pkt = build_expert_event_review_packet(
        np.arange(len(y)), np.arange(len(y)) % 5, np.full(len(y), 2022), sc_full, eta_def, cwsi, top_k=8
    )
    assert len(pkt) >= 10
    assert "expert_label" in pkt.columns

    toks = [rng.normal(0, 1, size=(16, 8)).astype(np.float32) for _ in range(30)]
    rq7 = run_rq7_probing_suite(
        toks[:20],
        toks,
        n_bands=7,
        continuous_targets={"et0": rng.normal(5, 1, 30)},
        binary_targets={"late": np.array([0, 1] * 15)},
        epochs=2,
        seed=31,
    )
    assert len(rq7) == 5  # random + 4 SSL arms

    arch = simulate_490_field_archive(n_fields=20, n_years=6.0, stress_prevalence=0.25, seed=31)
    Xc = arch["X"][arch["y_stress"] == 0]
    Xs = arch["X"][arch["y_stress"] == 1]
    Xte = np.concatenate([Xc[-20:], Xs[-8:]], axis=0)
    yte = np.array([0] * 20 + [1] * 8)
    sw = run_contamination_sweep(Xc[:-20], Xs[:-8], Xte, yte, train_size=40, epochs=2, seed=31)
    assert len(sw) == 6
    cf = analyze_false_alarm_confounders(
        np.repeat(Xc[:30], 7, axis=0), Xs, band_names=arch["bands"], seed=31
    )
    assert "cohort_breakdown" in cf


def test_mlflow_sqlite_tracking_cli_and_hydra_configs(tmp_path: Path) -> None:
    db = tmp_path / "mlflow.db"
    art = tmp_path / "sample.txt"
    art.write_text("ok")
    with track_experiment_run("test_exp", "run_1", db_path=db, seed=42, params={"alpha": 0.1}) as run:
        log_run_metrics_and_artifacts({"auc_pr": 0.91}, artifacts=[art])
        assert run.info.run_id
    assert db.exists()

    base_cfg = OmegaConf.load("conf/base.yaml")
    assert "defaults" in base_cfg
    for grp in ("conf/phase_axis/dsh.yaml", "conf/model/ssl_masked_recon.yaml", "conf/eval/loyo.yaml", "conf/xai/default.yaml"):
        c = OmegaConf.load(grp)
        assert len(c) > 0

    runner = CliRunner()
    res = runner.invoke(cli, ["--help"])
    assert res.exit_code == 0
    assert {"ingest", "segment", "baseline", "train", "evaluate", "export"} <= set(res.output.split())


@pytest.mark.real_data
def test_real_archive_provenance_fields_complete() -> None:
    """R3: All provenance fields present and non-empty on real490 archive."""
    archive = load_real490_archive()
    prov = get_archive_provenance(archive)
    required = [
        "data_source", "n_fields", "n_cycles", "n_dates",
        "first_acquisition_date", "last_acquisition_date",
        "cycle_file_sha256", "git_sha", "splits_sha256",
        "seeds", "y_stress_proxy", "eta_deficit_source", "cwsi_source",
    ]
    for key in required:
        assert key in prov, f"Missing provenance field: {key}"
        assert prov[key] not in (None, ""), f"Empty provenance field: {key}"
    assert prov["data_source"] == "real490"
    assert prov["n_fields"] == 490
    assert prov["n_cycles"] == 799
    assert prov["n_dates"] == 538


def test_require_real_archive_fail_closed() -> None:
    """R1: Missing archive → SystemExit(1), no report written."""
    with pytest.raises(SystemExit) as excinfo:
        require_real_archive(stats_zarr_path=Path("/nonexistent/stats.zarr"))
    assert excinfo.value.code == 1


@pytest.mark.real_data
def test_real490_no_32farm_cwsi_et_borrow() -> None:
    """R4: No 32-farm cwsi_et reaches a 490 report; proxies absent."""
    archive = load_real490_archive()
    prov = archive["provenance"]
    assert prov["eta_deficit_source"] == "absent"
    assert prov["cwsi_source"] == "absent"
    assert prov["y_stress_proxy"] == "weak_proxy_top20pct_mean_cwsi_not_validated_stress"
    assert np.all(np.isnan(archive["eta_deficit"]))
    assert np.all(np.isnan(archive["cwsi"]))


def test_simulated_output_path_routes_to_reports_simulated() -> None:
    """R2: Simulated outputs route under reports/simulated/."""
    out = simulated_output_path(Path("reports/rq1_benchmark.json"))
    assert "simulated" in str(out)
    assert out.name == "rq1_benchmark.json"
