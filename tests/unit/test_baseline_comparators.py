from __future__ import annotations

import numpy as np

from ssl_anomaly.baseline import (
    ECODDetector,
    IsolationForestDetector,
    bin_by_calendar_doy,
    bin_by_gdd,
    bin_by_landmarks,
    doy_from_datetime64,
    extract_cycle_features,
    fit_b0_calendar_baseline,
    gdd_progress,
    landmark_progress,
    score_b0_cycles,
)


def test_b0_calendar_doy_binning_and_scoring():
    times = np.array(
        ["2020-01-01", "2020-04-01", "2020-07-01", "2020-10-01", "2020-12-31"],
        dtype="datetime64[D]",
    )
    doys = doy_from_datetime64(times)
    assert doys[0] == 1
    # Also test direct calendar DOY binning on 2-D values
    b_doy, c_doy = bin_by_calendar_doy(times, np.ones((5, 2)), K=12)
    assert b_doy.shape == (12, 2)
    assert int(c_doy.sum()) == 5

    rng = np.random.default_rng(0)
    N, K, B = 20, 36, 4
    X_doy = np.zeros((N, K, B), dtype=np.float64)
    for i in range(N):
        phase = np.linspace(0, 2 * np.pi, K, endpoint=False)
        for b in range(B):
            X_doy[i, :, b] = 0.3 + 0.2 * np.sin(phase + b * 0.3) + rng.normal(0, 0.02, size=K)
    # Inject strong anomaly into cycle 0
    X_doy[0, 10:15, :] += 0.5
    fids = np.repeat(np.arange(1, 5), 5)

    bl = fit_b0_calendar_baseline(X_doy, fids, min_n=3)
    scores = score_b0_cycles(bl, X_doy, fids)
    assert scores[0]["max_score"] > max(s["max_score"] for s in scores[1:])
    assert scores[0]["burden"] > 0.0


def test_b2_gdd_and_landmark_progress():
    obs_days = np.arange(0, 361, 15, dtype=np.int64)
    weather_days = np.arange(0, 361, 1, dtype=np.int64)
    # Cold winter first half (14 C -> 2 GDD/day), hot summer second half (32 C -> 20 GDD/day)
    temp_c = np.where(weather_days < 180, 14.0, 32.0)
    tau_gdd = gdd_progress(obs_days, 0, 360, weather_days, temp_c, t_base_c=12.0)
    assert np.isclose(tau_gdd[0], 0.0)
    assert np.isclose(tau_gdd[-1], 1.0)
    assert np.all(np.diff(tau_gdd) >= 0.0)
    # Midpoint day=180 should have accumulated much less than 50% of total thermal time
    mid_idx = int(np.where(obs_days == 180)[0][0])
    assert tau_gdd[mid_idx] < 0.20

    # Landmark warping: peak at day 250 (~0.69 linear) should map near canonical 0.55
    ndvi = 0.15 + 0.65 * np.exp(-0.5 * ((obs_days - 250.0) / 55.0) ** 2)
    tau_lm = landmark_progress(obs_days, ndvi, 0, 360, canon_greenup=0.20, canon_peak=0.55)
    assert np.isclose(tau_lm[0], 0.0)
    assert np.isclose(tau_lm[-1], 1.0)
    assert np.all(np.diff(tau_lm) >= -1e-9)

    vals = np.column_stack([ndvi, ndvi * 0.5])
    b_gdd, _ = bin_by_gdd(obs_days, vals, 0, 360, weather_days, temp_c, K=12)
    b_lm, _ = bin_by_landmarks(obs_days, vals, ndvi, 0, 360, K=12)
    assert b_gdd.shape == (12, 2)
    assert b_lm.shape == (12, 2)


def test_b3_isolation_forest_and_ecod_flag_outlier_cycle():
    rng = np.random.default_rng(11)
    N_in, K, B = 40, 36, 5
    X_in = rng.normal(0.3, 0.03, size=(N_in, K, B))
    # Add normal seasonal arch in band 3 (NIR) and inverse in band 2 (Red)
    t = np.linspace(0, np.pi, K)
    X_in[:, :, 3] += 0.35 * np.sin(t)[None, :]
    X_in[:, :, 2] = 0.20 - 0.10 * np.sin(t)[None, :] + rng.normal(0, 0.015, size=(N_in, K))

    X_out = X_in[:4].copy()
    X_out[:, :, 3] *= 0.35  # collapsed canopy NIR
    X_out[:, :, 4] += 8.0   # extreme LST spike

    F_in = extract_cycle_features(X_in, durations=np.full(N_in, 340.0))
    F_out = extract_cycle_features(X_out, durations=np.full(4, 340.0))

    det_if = IsolationForestDetector(seed=42).fit(F_in)
    det_ecod = ECODDetector().fit(F_in)

    s_if_in = det_if.score_samples(F_in)
    s_if_out = det_if.score_samples(F_out)
    assert float(np.mean(s_if_out)) > float(np.percentile(s_if_in, 95))

    s_ec_in = det_ecod.score_samples(F_in)
    s_ec_out = det_ecod.score_samples(F_out)
    assert float(np.mean(s_ec_out)) > float(np.percentile(s_ec_in, 95))
