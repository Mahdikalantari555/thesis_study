"""Scientific invariants for the isolated Landsat decomposition study."""

import json
from dataclasses import replace

import numpy as np
import pytest
import zarr

from ssl_anomaly.decomposition_study.data import BANDS, read_zonal, smoke_panel, split_panel
from ssl_anomaly.decomposition_study.decompose import METHODS, decompose, regular_grid
from ssl_anomaly.monitor.holdout import build_holdout_manifest, holdout_manifest_hash
from ssl_anomaly.monitor.splits import manifest_hash


def test_zonal_selection_quality_and_manifest(tmp_path):
    path = tmp_path / "stats.zarr"
    g = zarr.open_group(str(path), mode="w")
    names = (*reversed(BANDS), "lst")
    entries = {
        "field": [1, 2, 3],
        "time": [0, 15, 45],
        "band": names,
        "valid_frac": [[0.8, 0.2, 1], [1, 1, 1], [1, 1, 1]],
        "median": np.broadcast_to([0.12, 0.18, 0.4, 0.16, 0.14, 0.1, 300], (3, 3, 7)),
    }
    for k, v in entries.items():
        arr = np.asarray(v)
        g.create_dataset(k, shape=arr.shape, dtype=arr.dtype)[:] = arr
    manifest_path, splits_path = tmp_path / "holdout.json", tmp_path / "splits.json"
    with pytest.raises(RuntimeError, match="holdout manifest missing"):
        read_zonal(path, manifest_path, 0.5, splits_path=splits_path)
    splits = {
        "kmeans": {"test_block_fields": [2]},
        "train_fields": [1],
        "test_period_start": "2013-05-01",
    }
    splits["manifest_sha256"] = manifest_hash(splits)
    splits_path.write_text(json.dumps(splits))
    manifest = build_holdout_manifest(splits)
    manifest_path.write_text(json.dumps(manifest))
    panel = read_zonal(path, manifest_path, 0.5, splits_path=splits_path)
    assert panel.fields.tolist() == [1]
    assert panel.days.tolist() == [0, 15]
    assert panel.optical[0, 0].tolist() == pytest.approx([0.1, 0.14, 0.16, 0.4, 0.18, 0.12])
    assert np.isnan(panel.optical[0, 1]).all()
    assert panel.branch("indices")[0, 0].tolist() == pytest.approx(
        [0.24 / 0.56, 0.6 / 1.61, 0.22 / 0.58]
    )
    assert panel.branch("indices")[0, 1].tolist() == pytest.approx([np.nan] * 3, nan_ok=True)
    manifest["holdout_farms"] = [1]
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(RuntimeError, match="self-hash"):
        read_zonal(path, manifest_path, 0.5, splits_path=splits_path)
    manifest["manifest_sha256"] = holdout_manifest_hash(manifest)
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(RuntimeError, match="missing_spatial_fields"):
        read_zonal(path, manifest_path, 0.5, splits_path=splits_path)


def test_stl_gap_mask():
    grid, state = regular_grid(np.array([0, 3, 30, 135]), np.array([0.1, 0.3, 0.4, 0.8]), 11)
    assert state.tolist() == [1, 2, 1, 0, 0, 0, 0, 0, 0, 1, 0]
    assert grid[:3].tolist() == pytest.approx([0.2, 0.3, 0.4])
    assert np.isnan(grid[3:9]).all()


@pytest.fixture(scope="module")
def fixture():
    panel = smoke_panel()
    return panel, split_panel(panel, "2017-01-01", "2018-01-01")


@pytest.mark.parametrize("method", METHODS)
def test_decomposition_additive_field_local_and_causal(fixture, method):
    panel, split = fixture
    x = panel.optical[:2, :, 3:4]
    a = decompose(panel.days, x, split, method, "causal")
    observed = np.isfinite(a.residual)
    assert observed[:, split.cal_end :].any()
    np.testing.assert_allclose(
        (a.trend + a.seasonal + a.residual)[observed], x[observed], atol=2e-7
    )
    assert np.isnan(a.residual[~np.isfinite(x)]).all()
    assert (a.fit_before <= panel.days).all()
    changed = x.copy()
    changed[0, split.cal_end :] += 0.4
    b = decompose(panel.days, changed, split, method, "causal")
    for attr in ("trend", "seasonal", "residual"):
        np.testing.assert_array_equal(
            getattr(a, attr)[:, : split.cal_end], getattr(b, attr)[:, : split.cal_end]
        )
        np.testing.assert_array_equal(getattr(a, attr)[1], getattr(b, attr)[1])
    exact = split.cal_end + 3
    short = decompose(
        panel.days[:exact], x[:, :exact], replace(split, n_dates=exact), method, "causal"
    )
    np.testing.assert_array_equal(a.residual[:, :exact], short.residual)


def test_retrospective_fit_ends_at_partition(fixture):
    panel, split = fixture
    x = panel.optical[:1, :, 3:4]
    a = decompose(panel.days, x, split, "robust_stl", "retrospective")
    b = decompose(
        panel.days,
        np.where(np.arange(len(panel.days))[None, :, None] >= split.cal_end, x * 3, x),
        split,
        "robust_stl",
        "retrospective",
    )
    np.testing.assert_array_equal(a.residual[:, : split.cal_end], b.residual[:, : split.cal_end])
    assert (a.fit_before[split.cal_end :] > panel.days[split.cal_end :]).all()


def test_real_archive_missing_never_uses_smoke(tmp_path):
    with pytest.raises(FileNotFoundError, match=r"stats\.zarr not found"):
        read_zonal(tmp_path / "missing.zarr", tmp_path / "holdout.json", 0.5)


def test_stats_lag_and_train_normalization(fixture):
    from ssl_anomaly.decomposition_study import features as ft

    panel, split = fixture
    raw = panel.branch("indices")
    x = raw.copy()
    t = split.cal_end + 2
    x[:, t:] += 3
    a, b = ft.statistics(panel.days, raw, split.train_end)
    new_a, new_b = ft.statistics(panel.days, x, split.train_end)
    np.testing.assert_array_equal(a, new_a)
    np.testing.assert_array_equal(b[:, : t + 1], new_b[:, : t + 1])
    np.testing.assert_array_equal(
        ft.Normalizer.fit(raw, split.train_end).scale, ft.Normalizer.fit(x, split.train_end).scale
    )
    rz = ft.residual_local_z(panel.days, raw)
    assert np.isfinite(rz[:, t:]).any()
    assert not np.allclose(raw, rz, equal_nan=True)


def test_masked_gru_and_arm_isolation(fixture):
    import torch

    from ssl_anomaly.decomposition_study import features as ft
    from ssl_anomaly.decomposition_study import ssl

    torch.set_num_threads(1)
    panel, split = fixture
    raw = panel.branch("indices")
    t = split.cal_end + 3
    x = raw.copy()
    x[:, t + 1 :] += 3
    gaps = np.diff(panel.days, prepend=panel.days[0])

    def features(values):
        comp = decompose(panel.days, values, split, "harmonic", "causal", capture_grid=False)
        stats = ft.statistics(panel.days, values, split.train_end)
        rz = ft.residual_local_z(panel.days, comp.residual)
        return ft.feature_groups(values, comp, stats, rz)

    groups = features(raw)
    norms = ft.fit_feature_norms(groups, split.train_end)
    a = ft.feature_tokens(groups, norms)
    b = ft.feature_tokens(features(x), norms)
    b1 = ft.arm_slots("B1", groups)
    c1 = ft.arm_slots("C1", groups)
    assert b1.sum() == raw.shape[-1]
    assert set(ft.ARMS["C1"]) == {"raw", "global", "local"}
    assert c1.sum() == raw.shape[-1] * (1 + 2 * len(ft.STAT_NAMES))
    assert not np.count_nonzero(ssl.tokens(a, c1, gaps)[..., : len(c1)][..., ~c1])
    active = ft.arm_slots("C3", groups)
    model = ssl._model(a.shape[-1], raw.shape[-1], 42, "cpu").eval()
    err = ssl.predict(
        model, a, active, gaps, norms["raw"].apply(raw), split.cal_end, split.n_dates, "cpu"
    )
    err_changed = ssl.predict(
        model, b, active, gaps, norms["raw"].apply(x), split.cal_end, split.n_dates, "cpu"
    )
    assert np.isfinite(err[:, t]).any()
    np.testing.assert_array_equal(err[:, : t + 1], err_changed[:, : t + 1])
    pred = torch.tensor([1.5, 9999.0], requires_grad=True)
    loss = ssl.masked_loss(pred, torch.tensor([1.0, float("nan")]))
    loss.backward()
    assert loss.item() == pytest.approx(0.125)
    assert pred.grad.tolist() == pytest.approx([0.5, 0])


def test_field_reference_and_calibration_do_not_look_ahead(fixture):
    from ssl_anomaly.decomposition_study import scoring as sc

    panel, split = fixture
    raw = panel.branch("indices")
    t = split.cal_end + 1
    x = raw.copy()
    x[0, t:] += 50
    a = sc.reference_groups(panel.days, raw[..., 0], split.train_end)
    b = sc.reference_groups(panel.days, x[..., 0], split.train_end)
    np.testing.assert_array_equal(a["inferred_phase"][:, : t + 1], b["inferred_phase"][:, : t + 1])
    before = sc.HistoricalBank.fit(raw, a["annual"], split.train_end, "annual")
    after = sc.HistoricalBank.fit(x, b["annual"], split.train_end, "annual")
    np.testing.assert_array_equal(before.center, after.center)
    np.testing.assert_array_equal(before.scale, after.scale)
    assert not np.allclose(before.center[0], before.center[1])
    exact = before.score(x, np.full(raw.shape[:2], -1, dtype=int), np.isfinite(x))
    assert np.isnan(exact).all()

    scores = [np.arange(1, 31).reshape(2, 15).astype(float) * (k + 1) for k in range(4)]
    cal = slice(0, 8)
    hybrid = sc.HybridCalibration.fit(scores, cal)
    assert hybrid is not None
    threshold = sc.alarm_threshold(scores[0], cal)
    altered = [v.copy() for v in scores]
    altered[0][:, 8:] *= 100
    altered[-1][0, 8] = np.nan
    assert hybrid == sc.HybridCalibration.fit(altered, cal)
    assert threshold == sc.alarm_threshold(altered[0], cal)
    hybrid_scores = hybrid.apply(altered)
    assert np.isnan(hybrid_scores["equal"][0, 8])
    assert not np.allclose(hybrid_scores["equal"], hybrid_scores["emphasize_D1"], equal_nan=True)
    assert all(sum(w) == pytest.approx(1) for w in sc.WEIGHTS.values())


@pytest.mark.parametrize(
    "family", ["abrupt_drop", "gradual_drop", "oscillation", "seasonal_change", "persistent_trend"]
)
def test_injections_are_paired_evaluation_only(fixture, family):
    from ssl_anomaly.decomposition_study.data import NIR
    from ssl_anomaly.decomposition_study.validation import perturb

    panel, split = fixture
    view, changed = perturb(panel, split, family, 1.0)
    mild, mild_changed = perturb(panel, split, family, 0.5)
    assert changed.any()
    assert not changed[:, : split.cal_end].any()
    np.testing.assert_array_equal(
        view.optical[:, : split.cal_end], panel.optical[:, : split.cal_end]
    )
    np.testing.assert_array_equal(np.isfinite(view.optical), np.isfinite(panel.optical))
    np.testing.assert_array_equal(changed, mild_changed)
    np.testing.assert_allclose(
        np.abs(view.optical[..., NIR] - panel.optical[..., NIR])[changed],
        2 * np.abs(mild.optical[..., NIR] - panel.optical[..., NIR])[changed],
        atol=1e-7,
    )
    assert not np.allclose(view.branch("indices")[changed], panel.branch("indices")[changed])


def test_evidence_exact_join_and_missingness(tmp_path, fixture):
    from ssl_anomaly.decomposition_study.validation import (
        evidence_metrics,
        read_evidence,
        with_gaps,
    )

    panel, split = fixture
    altered = with_gaps(panel, split)
    np.testing.assert_array_equal(
        altered.optical[:, : split.cal_end], panel.optical[:, : split.cal_end]
    )
    removed = np.isfinite(panel.optical).any(axis=-1) & ~np.isfinite(altered.optical).any(axis=-1)
    assert removed.any()
    assert not removed[:, : split.cal_end].any()
    path = tmp_path / "indicators.csv"
    path.write_text(
        "field_id,date,indicator,value,observed,source\n"
        "1,2021-01-01,tvdi,0.1,true,METRIC overpass\n"
        "1,2021-01-02,tvdi,0.2,true,METRIC overpass\n"
        "1,2021-01-03,tvdi,0.3,true,METRIC overpass\n"
        "1,2021-01-02,cwsi,1,false,interpolated\n"
        "2,2021-01-03,eta,1,true,unmatched\n"
    )
    expected = np.array([[1, 2, 3.0]])
    dates = np.arange("2021-01-01", "2021-01-04", dtype="datetime64[D]")
    metrics = evidence_metrics(expected, np.array([1]), dates, read_evidence(path), None)
    assert metrics["indicator_agreement"]["tvdi"]["spearman"] == pytest.approx(1.0)
    assert metrics["indicator_agreement"]["cwsi"]["status"] == "absent"
    assert metrics["indicator_agreement"]["eta"]["status"] == "absent"
    np.testing.assert_array_equal(expected, [[1, 2, 3]])


def test_retrospective_support_does_not_define_causal_score_dates(fixture):
    from ssl_anomaly.decomposition_study.experiment import target_support

    panel, split = fixture
    x = panel.branch("indices")[:1, :, :1].copy()
    t = split.cal_end + 1
    # Later observations can extend a retrospective STL segment past its minimum
    # length. Withhold all future data: the causal mask for t must not change.
    a = decompose(panel.days, x, split, "stl", "causal", capture_grid=False)
    x[:, t + 1 :] = np.nan
    b = decompose(panel.days, x, split, "stl", "causal", capture_grid=False)
    full = target_support(panel.branch("indices")[:1, :, :1], a, split.train_end)
    partial = target_support(x, b, split.train_end)
    assert full[:, : t + 1].any()
    np.testing.assert_array_equal(full[:, : t + 1], partial[:, : t + 1])


def test_epoch_checkpoint_resume_matches_uninterrupted_run(tmp_path):
    import torch

    from ssl_anomaly.decomposition_study import ssl

    torch.set_num_threads(1)
    rng = np.random.default_rng(88)
    features = rng.normal(size=(2, 24, 2)).astype(np.float32)
    target = features.copy()
    target[0, 0, 0] = np.nan
    gaps = np.full(24, 13)
    events = []

    def log(**event):
        events.append(event)

    def train(path, epochs):
        return ssl.train_model(
            features,
            np.ones(2, dtype=bool),
            gaps,
            target,
            24,
            42,
            epochs,
            "cpu",
            path,
            log,
            show_progress=False,
        )

    interrupted = tmp_path / "resumed.pt"
    train(interrupted, 1)
    recovered, _, actual = train(interrupted, 2)
    expected, _, reference = train(tmp_path / "continuous.pt", 2)
    assert [r["epoch"] for r in events] == [1, 2, 1, 2]
    assert actual["train_loss_by_epoch"] == reference["train_loss_by_epoch"]
    for name, val in recovered.state_dict().items():
        torch.testing.assert_close(val, expected.state_dict()[name], rtol=0, atol=0)


def test_synthetic_ap_respects_observed_changes_and_pairs():
    from ssl_anomaly.decomposition_study.validation import synthetic_metrics

    clean = np.array([[0.0, 0.1, np.nan], [0.0, 0.2, 0.4]])
    injected = np.array([[3.0, 0.1, np.nan], [0.0, 4.0, 0.4]])
    changed = np.array([[True, False, True], [False, True, False]])
    result = synthetic_metrics(clean, injected, changed, threshold=0.5)
    assert result["n_common"] == 5
    assert result["n_changed"] == 3
    assert result["n_positive"] == 2
    assert result["ap_date"] == pytest.approx(1.0)
    assert result["ap_field"] == pytest.approx(1.0)
    assert result["changed_alarm_fraction"] == 1.0


def test_dose_response_uses_same_changed_rows_despite_varying_score_support():
    from ssl_anomaly.decomposition_study.validation import changed_uplift, matched_dose_response

    clean = np.zeros((2, 2))
    # Date (1, 1) is scored in all doses but was unchanged at the mild dose.
    changed = np.ones_like(clean, dtype=bool)
    mild_changed = changed.copy()
    mild_changed[1, 1] = False
    inputs = [
        np.array(x)
        for x in ([[1, 9], [10, 99]], [[2, 10], [np.nan, 99]], [[3, np.nan], [np.nan, 99]])
    ]
    uplift = [changed_uplift(clean, x, m) for x, m in zip(inputs, (mild_changed, changed, changed))]
    report = matched_dose_response(np.array([0.5, 1, 2]), uplift)
    assert (
        report["n_matched_field_dates"]
        == report["n_matched_fields"]
        == report["n_matched_dates"]
        == 1
    )
    assert [d["median_matched_uplift"] for d in report["doses"]] == [1, 2, 3]
    assert [d["n_excluded_by_matching"] for d in report["doses"]] == [2, 2, 1]
    assert report["spearman"] == pytest.approx(1)
    uplift[-1][0, 0] = np.nan
    empty = matched_dose_response(np.array([0.5, 1, 2]), uplift)
    assert empty["n_matched_field_dates"] == 0
    assert empty["spearman"] is None
    assert all(d["median_matched_uplift"] is None for d in empty["doses"])
