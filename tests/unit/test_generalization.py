"""Generalization folds, per-fold normalization, sensor eras and drift.

Covers ``patch-generalization-suite`` tasks 1.1 and 1.3 (data-free half).
"""

from __future__ import annotations

import numpy as np
import pytest

from ssl_anomaly.monitor import generalization as G

T, C, S = 36, 8, 4
NAMES = ("ndvi", "blue", "green", "red", "nir", "swir1", "swir2", "lst")


def _grid_world():
    """10 blocks on a 5x2 grid: adjacency is then unambiguous."""
    xy, block_of = {}, {}
    for b in range(10):
        cx, cy = (b // 2) * 100.0, (b % 2) * 100.0
        for k in range(3):
            fid = b * 10 + k + 1
            xy[fid] = (cx + k, cy)
            block_of[fid] = b
    return block_of, xy


# --- 1.1 fold construction -----------------------------------------------
def test_folds_partition_every_field_exactly_once():
    block_of, xy = _grid_world()
    folds = G.build_folds(block_of, xy)
    assert len(folds) == 5
    seen = [f for fold in folds for f in fold.held_out_fields]
    assert sorted(seen) == sorted(block_of)


def test_each_fold_holds_out_two_adjacent_blocks():
    block_of, xy = _grid_world()
    folds = G.build_folds(block_of, xy)
    for fold in folds:
        a, b = fold.blocks
        assert abs((a // 2) - (b // 2)) + abs((a % 2) - (b % 2)) == 1, (a, b)


def test_fold_train_blocks_are_the_complement():
    block_of, xy = _grid_world()
    for fold in G.build_folds(block_of, xy):
        assert sorted(fold.train_blocks + list(fold.blocks)) == list(range(10))
        assert not set(fold.held_out_fields) & set(fold.train_fields)


def test_holdout_is_contiguous_not_scattered():
    block_of, xy = _grid_world()
    for fold in G.build_folds(block_of, xy):
        assert fold.mean_intra_distance > 0
        # the pair is nearer to itself than the average other block
        assert fold.mean_intra_distance < fold.mean_inter_distance


def test_fold_definition_is_deterministic_and_hashed():
    block_of, xy = _grid_world()
    a = G.folds_sha256(G.build_folds(block_of, xy))
    b = G.folds_sha256(G.build_folds(block_of, xy))
    assert a == b
    other = dict(block_of)
    other[1] = 5                       # move one field to another block
    assert G.folds_sha256(G.build_folds(other, xy)) != a


def test_duplicate_field_across_folds_is_refused(monkeypatch):
    block_of, xy = _grid_world()
    orig = G.pair_blocks_by_adjacency
    monkeypatch.setattr(G, "pair_blocks_by_adjacency",
                        lambda *a, **k: [(0, 0)] + orig(*a, **k)[1:])
    with pytest.raises(ValueError, match=r"cannot be paired|held out by folds"):
        G.build_folds(block_of, xy)


def test_a_block_without_fields_is_refused():
    block_of, xy = _grid_world()
    for f in [f for f, b in block_of.items() if b == 7]:
        block_of.pop(f)
    with pytest.raises(ValueError, match="no field"):
        G.build_folds(block_of, xy)


def test_pairing_requires_the_right_block_count():
    with pytest.raises(ValueError, match="cannot be paired"):
        G.pair_blocks_by_adjacency(np.zeros((7, 2)))


def test_pairing_is_seed_recorded_but_deterministic():
    c = np.array([[0, 0], [1, 0], [10, 0], [11, 0], [20, 0], [21, 0],
                  [30, 0], [31, 0], [40, 0], [41, 0]], dtype=float)
    assert G.pair_blocks_by_adjacency(c, seed=13) == G.pair_blocks_by_adjacency(c, seed=99)
    assert G.pair_blocks_by_adjacency(c) == [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]


# --- per-fold normalization (leakage guard) ------------------------------
def _cycles(n=6, seed=0):
    g = np.random.default_rng(seed)
    v = g.normal(0.4, 0.05, (n, T, C, S, S))
    m = np.ones_like(v, dtype=bool)
    s = np.ones((n, T), dtype=np.int64)
    return v, m, s


def test_in_fold_norm_ignores_a_held_out_cycle():
    v, m, s = _cycles()
    keep = np.array([True, True, True, True, True, False])
    v[5] = 99.0                                  # a wildly different holdout cycle
    a = G.refit_norm_in_fold(v, m, s, keep, NAMES)
    b = G.refit_norm_in_fold(v, m, s, keep, NAMES)
    assert a == b
    # ...and the held-out cycle WOULD move the stats if it were included
    keep_all = np.ones(6, dtype=bool)
    c = G.refit_norm_in_fold(v, m, s, keep_all, NAMES)
    assert c["L8"]["ndvi"]["median"] > a["L8"]["ndvi"]["median"]


def test_norm_uses_only_in_fold_helper_proves_exclusion():
    v, m, s = _cycles()
    keep = np.array([True, True, True, True, True, False])
    a, b = G.norm_uses_only_in_fold(v, m, s, keep, NAMES, probe_row=0)
    # excluding an IN-FOLD row does change the fit (so the test is not vacuous)
    assert a != b


def test_in_fold_norm_refuses_an_empty_train_set():
    v, m, s = _cycles()
    with pytest.raises(ValueError, match="no in-fold train cycles"):
        G.refit_norm_in_fold(v, m, s, np.zeros(6, dtype=bool), NAMES)


def test_in_fold_norm_leaves_a_thin_cell_empty_instead_of_filling_it():
    v, m, s = _cycles(n=2)
    out = G.refit_norm_in_fold(v, m, s, np.array([True, True]), NAMES, min_n=1000)
    # 2 cycles x 36 bins x 4x4 pixels = 1152 samples, i.e. ABOVE a 1000 floor
    # (pixels are samples, not cycles) — so use a floor that actually excludes
    out = G.refit_norm_in_fold(v, m, s, np.array([True, True]), NAMES, min_n=5000)
    assert out["L8"]["ndvi"]["n"] == 1152
    assert out["L8"]["ndvi"]["median"] is None


def test_in_fold_norm_leaves_a_thin_cell_empty_for_real(tmp_path):
    v, m, s = _cycles(n=1)
    tiny = v[:, :, :, :2, :2]                      # 1 x 36 x 4 = 144 samples
    out = G.refit_norm_in_fold(tiny, np.ones_like(tiny, bool), s[:1],
                               np.array([True]), NAMES, min_n=1000)
    assert out["L8"]["ndvi"]["median"] is None


def test_in_fold_norm_shape_guard():
    v, m, s = _cycles()
    with pytest.raises(ValueError, match="in_fold_train"):
        G.refit_norm_in_fold(v, m, s, np.ones(3, dtype=bool), NAMES)


# --- 1.3 sensor eras -----------------------------------------------------
def _dates(n):
    return np.array([f"2024-{1 + (i // 28):02d}-{1 + i % 28:02d}" for i in range(n)],
                    dtype="datetime64[D]")


def test_sensor_era_splits_on_a_sensor_change():
    d = _dates(10)
    s = np.array([1] * 5 + [2] * 5)
    eras = G.sensor_era(d, s)
    assert [e.name for e in eras] == ["L8", "L9"]
    assert eras[0].n_cycles == 5
    assert eras[1].n_cycles == 5


def test_unknown_sensor_becomes_its_own_era_not_attributed():
    d = _dates(6)
    s = np.array([1, 1, 0, 0, 2, 2])
    eras = G.sensor_era(d, s)
    assert [e.name for e in eras] == ["L8", "unknown", "L9"]


def test_sensor_era_sorts_by_date_first():
    d = np.array(["2024-06-01", "2024-01-01", "2024-03-01"], dtype="datetime64[D]")
    s = np.array([2, 1, 2])
    eras = G.sensor_era(d, s)
    assert eras[0].name == "L8"
    assert eras[0].start == "2024-01-01"


def test_era_shares_sum_to_one():
    shares = G.era_shares(np.array([1, 1, 2, 2, 2, 0]))
    assert sum(shares.values()) == pytest.approx(1.0)
    assert shares["L9"] == pytest.approx(0.5)


def test_era_shape_guard():
    with pytest.raises(ValueError, match="must align"):
        G.sensor_era(_dates(3), np.array([1, 1]))


# --- year drift ----------------------------------------------------------
def test_year_drift_reports_shift_against_the_first_year():
    stat = np.array([1.0, 1.1, 2.0, 2.2])
    years = np.array([2023, 2023, 2025, 2025])
    out = G.year_drift(stat, years)
    assert out["reference_year"] == 2023
    assert out["per_year"]["2025"]["abs_shift"]["0.5"] == pytest.approx(1.05)
    assert out["per_year"]["2023"]["abs_shift"]["0.5"] == pytest.approx(0.0)


def test_year_drift_is_nan_safe():
    stat = np.array([1.0, np.nan, 2.0, np.nan])
    years = np.array([2023, 2023, 2024, 2024])
    out = G.year_drift(stat, years)
    assert out["per_year"]["2024"]["n"] == 1


def test_year_drift_shape_guard():
    with pytest.raises(ValueError, match="must align"):
        G.year_drift(np.zeros(3), np.zeros(2, dtype=int))


# --- threshold stability -------------------------------------------------
def _clean(n=20, T=T, seed=0, level=0.0):
    g = np.random.default_rng(seed)
    return g.normal(level, 0.05, (n, T))


def test_threshold_is_stable_when_years_look_alike():
    p = _clean(40)
    years = np.array([2023] * 20 + [2024] * 20)
    out = G.threshold_stability(p, tau=0.2, k=2, years=years)
    assert out["stable"] is True
    assert set(out["per_year"]) == {"2023", "2024"}


def test_threshold_instability_is_detected():
    p = np.concatenate([_clean(20, level=0.0), _clean(20, level=0.5)])
    years = np.array([2023] * 20 + [2024] * 20)
    out = G.threshold_stability(p, tau=0.2, k=2, years=years)
    assert out["stable"] is False
    assert out["per_year"]["2024"]["far"] > out["per_year"]["2023"]["far"]


def test_threshold_stability_uses_the_production_rule_not_a_moving_average():
    """A single spike must NOT alarm at k=3 (consecutive-run rule)."""
    p = np.zeros((5, T))
    p[:, 10] = 10.0
    out = G.threshold_stability(p, tau=1.0, k=3, years=np.array([2023] * 5))
    assert out["overall_far"] == 0.0


def test_threshold_stability_refuses_to_refit():
    p = _clean(10)
    out = G.threshold_stability(p, tau=0.2, k=2, years=np.array([2023] * 10))
    assert "tel:refit" not in out["note"]
    assert "NOT applied" in out["note"]
    assert out["tau"] == 0.2


def test_threshold_stability_shape_guards():
    with pytest.raises(ValueError, match=r"\(N, T\)"):
        G.threshold_stability(np.zeros(5), tau=1.0, k=1, years=np.zeros(5, dtype=int))
    with pytest.raises(ValueError, match="paths for"):
        G.threshold_stability(np.zeros((5, T)), tau=1.0, k=1, years=np.zeros(4, dtype=int))
