"""Tests for MAD-scaled perturbations (task 3.1) and the dev-metric pieces
(detection delay, FAR calibration, forbidden targets — task 3.3)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import perturbations as mpert  # noqa: E402
from ssl_anomaly.monitor import scoring as mscoring  # noqa: E402

T, C = 36, 8
MAD_SCALE = np.full((T, C), 1.4826, dtype=np.float64)  # scale → MAD = 1.0 everywhere


def make_cycle(seed=0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    x = rng.normal(0.5, 0.05, size=(T, C)).astype(np.float32)
    x[:, 7] = rng.normal(28, 2, size=T)
    m = np.ones((T, C), dtype=bool)
    m[33:, :] = False  # tail unobserved
    m[10, 7] = False  # isolated unobserved LST bin
    x[~m] = np.nan  # values are NaN exactly where unobserved
    return x, m


# ---------------------------------------------------------------------------
# Injection correctness
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ptype", mpert.INTERIM_TYPES)
def test_injection_changes_intended_channels_only(ptype: str) -> None:
    x, m = make_cycle()
    res = mpert.inject_perturbation(
        x, m, pert_type=ptype, onset_bin=12, duration=3, severity=1.0, mad=MAD_SCALE,
    )
    channels = set(mpert.TYPE_CHANNELS[ptype])
    changed = {c for c in range(C) if not np.allclose(res.x[:, c][m[:, c]], x[:, c][m[:, c]])}
    assert changed <= channels, f"{ptype} modified foreign channels {changed - channels}"
    assert changed, f"{ptype} changed nothing"
    assert res.onset_bin == 12


def test_injection_respects_observation_mask() -> None:
    """Unobserved entries must never be created or destroyed."""
    x, m = make_cycle()
    for ptype in mpert.INTERIM_TYPES:
        res = mpert.inject_perturbation(
            x, m, pert_type=ptype, onset_bin=8, duration=4, severity=2.0, mad=MAD_SCALE,
        )
        assert np.array_equal(res.m, m)
        assert np.all(np.isnan(res.x[~m]))


def test_severity_scales_monotonically() -> None:
    """A 2xMAD perturbation moves values at least as far as 1xMAD."""
    x, m = make_cycle()
    r1 = mpert.inject_perturbation(x, m, pert_type="ndvi_drop", onset_bin=10, duration=3, severity=1.0, mad=MAD_SCALE)
    r2 = mpert.inject_perturbation(x, m, pert_type="ndvi_drop", onset_bin=10, duration=3, severity=2.0, mad=MAD_SCALE)
    d1 = np.abs(r1.x[:, 0][m[:, 0]] - x[:, 0][m[:, 0]]).sum()
    d2 = np.abs(r2.x[:, 0][m[:, 0]] - x[:, 0][m[:, 0]]).sum()
    assert d2 > d1 > 0


def test_phenology_delay_never_erases_observations() -> None:
    x, m = make_cycle()
    res = mpert.inject_perturbation(
        x, m, pert_type="phenology_delay", onset_bin=6, duration=5, severity=1.0, mad=MAD_SCALE,
    )
    was_obs = m[6:, :]
    still_finite = np.isfinite(res.x[6:, :]) | ~was_obs
    assert np.all(still_finite)


def test_mad_sizing_uses_train_stats() -> None:
    """severity x MAD: with scale=1.4826 (MAD=1), a 1-bin lst_rise adds 1.0 K."""
    x, m = make_cycle()
    before = float(x[12, 7])
    res = mpert.inject_perturbation(x, m, pert_type="lst_rise", onset_bin=12, duration=1, severity=1.0, mad=MAD_SCALE)
    assert res.x[12, 7] == pytest.approx(before + 1.0)


def test_inject_dataset_onset_and_phases() -> None:
    rng = np.random.default_rng(0)
    n = 20
    X = np.stack([make_cycle(seed=i)[0] for i in range(n)])
    M = np.stack([make_cycle(seed=i)[1] for i in range(n)])
    cfg = mpert.PerturbationConfig(n_per_stratum=n)
    results = mpert.inject_dataset(X, M, MAD_SCALE, cfg, rng)
    assert len(results) == n
    for r in results:
        assert r.pert_type in mpert.INTERIM_TYPES
        assert r.onset_bin in (6, 18, 30)  # early / mid / late


# ---------------------------------------------------------------------------
# Alarm rule and detection delay (hand-made cycles)
# ---------------------------------------------------------------------------
def test_first_alarm_bin_delay_handmade() -> None:
    """A hand-made cycle with an injected spike: delay measured from onset."""
    s = np.full(36, 0.5)
    s[20] = 5.0  # onset bin 20 carries the anomaly
    assert mscoring.first_alarm_bin(s, tau=2.0, k=1, onset_bin=20) == 20
    assert mscoring.first_alarm_bin(s, tau=2.0, k=1, onset_bin=0) == 20
    # k=2 needs two consecutive bins above τ.
    s2 = np.full(36, 0.5)
    s2[20] = 5.0
    assert mscoring.first_alarm_bin(s2, tau=2.0, k=2, onset_bin=0) == -1
    s2[21] = 5.0
    assert mscoring.first_alarm_bin(s2, tau=2.0, k=2, onset_bin=0) == 20
    # Unobserved bins break runs (NaN): the only above-τ pair straddles a NaN.
    s3 = np.full(36, 0.5)
    s3[14] = 5.0
    s3[15] = np.nan
    s3[16] = 5.0
    assert mscoring.first_alarm_bin(s3, tau=2.0, k=2, onset_bin=0) == -1
    s3[17] = 5.0
    assert mscoring.first_alarm_bin(s3, tau=2.0, k=2, onset_bin=0) == 16


def test_alarm_per_cycle_runs() -> None:
    s = np.array([np.nan, 1, 1, np.nan, 1, 1, 1])
    assert mscoring.alarm_per_cycle(s, tau=0.5, k=3)
    assert not mscoring.alarm_per_cycle(s, tau=0.5, k=4)
    s2 = np.array([1, np.nan, 1])  # NaN breaks the only candidate pair
    assert not mscoring.alarm_per_cycle(s2, tau=0.5, k=2)
    assert mscoring.alarm_per_cycle(np.array([1, 1]), tau=0.5, k=2)


# ---------------------------------------------------------------------------
# FAR calibration hits 5 % on synthetic normal scores
# ---------------------------------------------------------------------------
def test_far_calibration_hits_target() -> None:
    rng = np.random.default_rng(42)
    clean = [rng.normal(0.0, 1.0, size=36) for _ in range(400)]
    tau, achieved = mscoring.calibrate_threshold(clean, k=1, far_target=0.05)
    assert achieved <= 0.05
    # With n=400 the empirical FAR should be close to the target.
    assert achieved >= 0.02, f"tau too conservative: FAR {achieved}"


def test_far_calibration_k2() -> None:
    rng = np.random.default_rng(1)
    clean = [rng.normal(0.0, 1.0, size=36) for _ in range(400)]
    tau, achieved = mscoring.calibrate_threshold(clean, k=2, far_target=0.05)
    assert achieved <= 0.05


def test_choose_threshold_prefers_higher_detection() -> None:
    """k chosen by detection rate; tie → smaller k."""
    rng = np.random.default_rng(3)
    clean = [rng.normal(0.0, 1.0, size=36) for _ in range(200)]
    injected = []
    onsets = []
    for _ in range(60):
        s = rng.normal(0.0, 1.0, size=36)
        onset = 10
        s[onset:onset + 4] += 6.0  # easily detected at any k
        injected.append(s)
        onsets.append(onset)
    thr, per_k = mscoring.choose_threshold(clean, injected, onsets, far_target=0.05)
    assert thr.far_achieved <= 0.05
    assert thr.k in (1, 2)
    assert per_k["k1"]["detection_rate"] >= 0.9


# ---------------------------------------------------------------------------
# Partial AUC-PR
# ---------------------------------------------------------------------------
def test_aucpr_perfect_and_chance() -> None:
    clean = np.array([0.1, 0.2, 0.3, 0.4])
    inj = np.array([0.9, 1.0])
    assert mscoring.partial_auc_pr(clean, inj) == pytest.approx(1.0)
    rng = np.random.default_rng(0)
    c = rng.normal(0, 1, 500)
    i = rng.normal(0, 1, 50)
    ap = mscoring.partial_auc_pr(c, i)
    assert 0.0 <= ap <= 1.0
    # Chance level ≈ prevalence (0.5 / 5.5 ≈ 0.09), within noise.
    assert ap < 0.3


# ---------------------------------------------------------------------------
# Forbidden targets in development code (task 3.3)
# ---------------------------------------------------------------------------
FORBIDDEN_NAMES = {"cwsi", "eta_deficit", "y_stress", "eta_daily"}
ALLOWED_PATHS = [
    REPO_ROOT / "src/ssl_anomaly/monitor",
    REPO_ROOT / "scripts/train_main.py",
    REPO_ROOT / "scripts/eval_dev.py",
    REPO_ROOT / "scripts/run_dev_matrix.py",
    REPO_ROOT / "scripts/check_dev_env.py",
    REPO_ROOT / "scripts/freeze_main_model.py",
]


def test_no_forbidden_targets_in_dev_code() -> None:
    """AST scan: dev code must not reference CWSI/ETa/y_stress anywhere
    (names, attributes, string keys). Docstrings are excluded — they document
    the prohibition; any *use* (name, attribute, subscript key) fails."""
    offenders: list[str] = []
    for path in ALLOWED_PATHS:
        files = sorted(path.glob("*.py")) if path.is_dir() else [path]
        for f in files:
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            docstring_nodes = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    doc = ast.get_docstring(node, clean=False)
                    if doc is not None:
                        for stmt in node.body:
                            if (
                                isinstance(stmt, ast.Expr)
                                and isinstance(stmt.value, ast.Constant)
                                and isinstance(stmt.value.value, str)
                            ):
                                docstring_nodes.add(id(stmt.value))
            for node in ast.walk(tree):
                bad = None
                if isinstance(node, ast.Name) and node.id.lower() in FORBIDDEN_NAMES:
                    bad = node.id
                elif isinstance(node, ast.Attribute) and node.attr.lower() in FORBIDDEN_NAMES:
                    bad = node.attr
                elif isinstance(node, ast.Constant) and isinstance(node.value, str) \
                        and node.value.lower() in FORBIDDEN_NAMES and id(node) not in docstring_nodes:
                    bad = node.value
                if bad:
                    offenders.append(f"{f.name}:{node.lineno}: {bad}")
    assert not offenders, f"Forbidden targets referenced in dev code: {offenders}"


# ---------------------------------------------------------------------------
# Index-drop family (change literature-grounded-severity-protocol, task 1.2)
# Absolute-Δ injections on NDVI (channel 0) and SAVI (realized through the
# red/nir channels — never a fabricated savi channel).
# ---------------------------------------------------------------------------
def make_veg_cycle(seed=0) -> tuple[np.ndarray, np.ndarray]:
    """Cycle with plausible NDVI/red/nir trajectories for SAVI-solver tests."""
    rng = np.random.default_rng(seed)
    x, m = make_cycle(seed=seed)
    t = np.arange(T) / T
    x[:, 0] = 0.2 + 0.5 * np.exp(-((t - 0.55) ** 2) / 0.04)  # NDVI hump ≈0.7 mid
    x[:, 3] = np.clip(0.30 - 0.18 * np.exp(-((t - 0.55) ** 2) / 0.06), 0.05, None)  # red
    x[:, 4] = np.clip(0.25 + 0.30 * np.exp(-((t - 0.55) ** 2) / 0.06), 0.05, None)  # nir
    x[~m] = np.nan  # keep the mask/value consistency of the base fixture
    return x, m


def savi_of(x: np.ndarray, b: int, L: float = 0.5) -> float:
    return (1.0 + L) * (x[b, 4] - x[b, 3]) / (x[b, 4] + x[b, 3] + L)


def test_index_drop_ndvi_absolute_delta() -> None:
    """Acute NDVI drop: constant absolute Δ over the window, onset recorded."""
    x, m = make_veg_cycle()
    before = x[10:12, 0].copy()
    res = mpert.inject_index_drop(
        x, m, index="ndvi", onset_bin=10, duration=2, delta=0.08,
    )
    assert np.allclose(res.x[10:12, 0], before - 0.08)
    # Outside the window unchanged; other channels untouched.
    assert np.allclose(res.x[12:, 0][m[12:, 0]], x[12:, 0][m[12:, 0]])
    for c in range(1, C):
        assert np.allclose(res.x[:, c][m[:, c]], x[:, c][m[:, c]])
    assert np.array_equal(res.m, m)
    assert res.onset_bin == 10


def test_index_drop_persistent_variant() -> None:
    """Persistent family: same Δ held over the fixed persistent duration."""
    x, m = make_veg_cycle()
    res = mpert.inject_index_drop(
        x, m, index="ndvi", onset_bin=8, duration=mpert.PERSISTENT_DURATION_BINS,
        delta=0.16, family="persistent",
    )
    lo, hi = 8, 8 + mpert.PERSISTENT_DURATION_BINS
    assert np.allclose(res.x[lo:hi, 0], x[lo:hi, 0] - 0.16)
    assert res.meta["family"] == "persistent"


def test_index_drop_floors_at_physical_range_and_records_realized() -> None:
    """A drop larger than the observed value floors at the NDVI physical
    range and the REALIZED delta is recorded (never below range)."""
    x, m = make_veg_cycle()
    x[12, 0] = -0.7  # degenerate low NDVI: S6's -0.40 crosses the -1.0 floor
    res = mpert.inject_index_drop(x, m, index="ndvi", onset_bin=12, duration=1, delta=0.40)
    assert res.x[12, 0] == pytest.approx(mpert.NDVI_PHYSICAL_RANGE[0])
    assert res.meta["delta_realized"][0] == pytest.approx(-0.7 - mpert.NDVI_PHYSICAL_RANGE[0])
    assert res.meta["n_floored_bins"] == 1


def test_index_drop_respects_mask_and_never_erases() -> None:
    x, m = make_veg_cycle()
    m[13, 0] = False
    x[13, 0] = np.nan
    res = mpert.inject_index_drop(x, m, index="ndvi", onset_bin=12, duration=3, delta=0.05)
    assert np.isnan(res.x[13, 0])
    assert not res.m[13, 0]
    assert np.all(np.isnan(res.x[~m]))


def test_savi_axis_independent_of_ndvi_channel() -> None:
    """SAVI is injected by solving red/nir — the ndvi CHANNEL must stay
    exactly as observed (separate axes, no fabricated savi channel)."""
    x, m = make_veg_cycle()
    res = mpert.inject_index_drop(x, m, index="savi", onset_bin=10, duration=3, delta=0.08)
    assert np.allclose(res.x[:, 0][m[:, 0]], x[:, 0][m[:, 0]])
    changed = {c for c in range(C) if not np.allclose(res.x[:, c][m[:, c]], x[:, c][m[:, c]])}
    assert changed == {3, 4}, f"SAVI axis touched channels {changed}, expected red(3)+nir(4)"


def test_savi_solver_recovers_target_drop() -> None:
    """The red/nir scaling solver must realize the target ΔSAVI on normal
    bins (sum of reflectances held constant)."""
    x, m = make_veg_cycle()
    delta = 0.10
    res = mpert.inject_index_drop(x, m, index="savi", onset_bin=10, duration=3, delta=delta)
    for b in (10, 11, 12):
        if m[b, 3] and m[b, 4] and x[b, 4] + x[b, 3] + 0.5 > 0:
            assert savi_of(x, b) - savi_of(res.x, b) == pytest.approx(delta, abs=1e-6)
            # Sum of reflectances preserved (brightness unchanged).
            assert res.x[b, 3] + res.x[b, 4] == pytest.approx(x[b, 3] + x[b, 4], abs=1e-9)


def test_savi_solver_skips_bins_missing_a_channel() -> None:
    """Bins without BOTH red and nir observed cannot realize a SAVI drop —
    they stay untouched and are counted."""
    x, m = make_veg_cycle()
    m[11, 4] = False  # nir unobserved
    x[11, 4] = np.nan
    res = mpert.inject_index_drop(x, m, index="savi", onset_bin=10, duration=3, delta=0.08)
    assert np.isnan(res.x[11, 4])
    assert res.meta["n_skipped_bins"] == 1


def test_savi_solver_floors_physical_range() -> None:
    """red/nir stay inside the reflectance physical range after the solve.

    The sum-preserving solve cannot floor for normal vegetation bins (the
    target SAVI always stays inside the range achievable at the held sum);
    flooring is exercised on a degenerate bright-red bin (bare soil), where
    S6's -0.40 pushes red past 1.6."""
    x, m = make_veg_cycle()
    x[10, 3] = 1.55  # bright red (bare-soil signature)
    x[10, 4] = 0.20
    res = mpert.inject_index_drop(x, m, index="savi", onset_bin=10, duration=1, delta=0.40)
    lo, hi = mpert.REFLECTANCE_PHYSICAL_RANGE
    assert lo <= res.x[10, 3] <= hi
    assert lo <= res.x[10, 4] <= hi
    assert res.meta["n_floored_bins"] >= 1


def test_index_drop_pct_of_own_grand_growth_median() -> None:
    """% drop is computed per field against ITS OWN grand-growth median."""
    x, m = make_veg_cycle()
    gg = x[12:24, 0][m[12:24, 0]]
    med = float(np.median(gg))
    res = mpert.inject_index_drop(x, m, index="ndvi", onset_bin=12, duration=2, delta=0.08)
    assert res.meta["pct_of_field_median"] == pytest.approx(100.0 * 0.08 / med, rel=1e-6)
    assert res.meta["field_median_source"] == "grand_growth_bins"


def test_index_drop_dataset_covers_all_cycles_and_rotates_phases() -> None:
    """One injection per cycle per round; onsets rotate through the phases."""
    n = 9
    X = np.stack([make_veg_cycle(seed=i)[0] for i in range(n)])
    M = np.stack([make_veg_cycle(seed=i)[1] for i in range(n)])
    results = mpert.inject_index_drop_dataset(
        X, M, level_id="S3", family="acute", index="ndvi", round_idx=0,
    )
    assert len(results) == n
    onsets = [r.onset_bin for r in results]
    assert set(onsets) == {6, 18, 30}
    assert all(abs(r.meta["delta_realized"][0] - 0.08) < 1e-6 or r.meta["n_floored_bins"] > 0
               for r in results)
    # Round 1 rotates the phase assignment deterministically.
    results_r1 = mpert.inject_index_drop_dataset(
        X, M, level_id="S3", family="acute", index="ndvi", round_idx=1,
    )
    assert [r.onset_bin for r in results_r1] != onsets


# ---------------------------------------------------------------------------
# Gradual family (change gradual-severity-shape)
# ---------------------------------------------------------------------------
from ssl_anomaly.monitor.severity_table import (  # noqa: E402
    GRADUAL_FAMILY,
    GRADUAL_RAMP_BINS,
    PRIMARY_FAMILIES,
    SECONDARY_FAMILIES,
)


def test_gradual_family_is_registered_as_primary():
    assert GRADUAL_FAMILY in PRIMARY_FAMILIES
    assert GRADUAL_FAMILY not in SECONDARY_FAMILIES
    assert set(GRADUAL_RAMP_BINS) == {3, 4, 6}


@pytest.mark.parametrize(("round_idx", "d_expected"), list(enumerate(GRADUAL_RAMP_BINS)))
def test_gradual_ramp_matches_delta_times_min_one(round_idx, d_expected):
    x = np.zeros((4, 36, 8))
    x[:, :, 0] = 0.70
    m = np.ones((4, 36, 8), dtype=bool)
    results = mpert.inject_index_drop_dataset(
        x, m, level_id="S4", family=GRADUAL_FAMILY, index="ndvi", round_idx=round_idx,
    )
    r = results[0]
    assert r.meta["ramp_bins"] == d_expected
    assert r.meta["n_bins_window"] == d_expected
    got = x[0, :, 0] - r.x[:, 0]
    for t in range(d_expected):
        b = r.onset_bin + t
        assert got[b] == pytest.approx(0.16 * (t + 1) / d_expected, abs=1e-9)
    # held to cycle end (when the cycle still has bins after the ramp)
    after = r.onset_bin + d_expected
    if after < 36:
        assert got[after] == pytest.approx(0.16, abs=1e-9)


@pytest.mark.parametrize("round_idx", list(range(len(GRADUAL_RAMP_BINS))))
def test_gradual_ramp_always_fits_inside_the_cycle(round_idx):
    x = np.zeros((2, 36, 8))
    x[:, :, 0] = 0.7
    m = np.ones((2, 36, 8), dtype=bool)
    results = mpert.inject_index_drop_dataset(
        x, m, level_id="S6", family=GRADUAL_FAMILY, index="ndvi", round_idx=round_idx,
    )
    for r in results:
        assert r.onset_bin + r.meta["ramp_bins"] <= 36
        assert len(r.meta["ramp_profile"]) == r.meta["ramp_bins"]


def test_gradual_savi_uses_the_solver_at_partial_magnitudes():
    x = np.zeros((2, 36, 8))
    x[:, :, 3] = 0.15
    x[:, :, 4] = 0.55
    m = np.ones((2, 36, 8), dtype=bool)
    r = mpert.inject_index_drop_dataset(
        x, m, level_id="S4", family=GRADUAL_FAMILY, index="savi", round_idx=1,
    )[0]
    base = mpert.savi_from_red_nir(0.15, 0.55)
    d = r.meta["ramp_bins"]
    for t in range(d):
        b = r.onset_bin + t
        got = base - mpert.savi_from_red_nir(r.x[b, 3], r.x[b, 4])
        assert got == pytest.approx(0.16 * (t + 1) / d, abs=1e-6)
        # brightness is preserved at every ramp bin
        assert r.x[b, 3] + r.x[b, 4] == pytest.approx(0.70, abs=1e-9)


def test_acute_and_persistent_metadata_is_unchanged():
    """The gradual work must not move the frozen families' recorded numbers."""
    x = np.zeros((2, 36, 8))
    x[:, :, 0] = 0.7
    m = np.ones((2, 36, 8), dtype=bool)
    acute = mpert.inject_index_drop_dataset(x, m, level_id="S4", family="acute", index="ndvi")[0]
    pers = mpert.inject_index_drop_dataset(
        x, m, level_id="S4", family="persistent", index="ndvi",
    )[0]
    assert acute.meta["n_bins_window"] == 2
    assert acute.meta["ramp_bins"] is None
    assert pers.meta["n_bins_window"] == mpert.PERSISTENT_DURATION_BINS
    assert pers.meta["ramp_bins"] is None
    assert acute.meta["ramp_profile"] is None


def test_gradual_active_span_is_recorded_beyond_the_ramp():
    x = np.zeros((1, 36, 8))
    x[:, :, 0] = 0.7
    m = np.ones((1, 36, 8), dtype=bool)
    r = mpert.inject_index_drop_dataset(
        x, m, level_id="S4", family=GRADUAL_FAMILY, index="ndvi", round_idx=0,
    )[0]
    assert r.meta["n_bins_active"] > r.meta["n_bins_window"]
    assert r.meta["n_bins_active"] == 36 - r.onset_bin


def test_gradual_never_warms_extraction_targets_or_masks():
    x = np.zeros((2, 36, 8))
    x[:, :, 0] = 0.7
    m = np.ones((2, 36, 8), dtype=bool)
    m[:, 5, :] = False
    results = mpert.inject_index_drop_dataset(
        x, m, level_id="S4", family=GRADUAL_FAMILY, index="ndvi", round_idx=2,
    )
    for r in results:
        np.testing.assert_array_equal(r.m, m[r.source_row])
