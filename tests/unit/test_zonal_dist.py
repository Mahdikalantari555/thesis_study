"""Tests for the R0.5 zonal distribution-statistics representation
(change compare-spatial-representation-strategies, requirement
"Zonal distribution-statistics representation (R0.5)").

A fake ``StatsZarrReader`` stands in for the store, so the whole pipeline
(channel construction -> binning -> B1 scoring -> alarm rule) is exercised
without the data archive.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import zonal_dist as zd  # noqa: E402

N_FIELDS, N_DATES = 4, 40
BASE = pd.Timestamp("2020-01-01")


class FakeReader:
    """Minimal stand-in for StatsZarrReader (same attribute surface)."""

    def __init__(self, seed: int = 0, n_fields: int = N_FIELDS, n_dates: int = N_DATES):
        rng = np.random.default_rng(seed)
        self._bands = list(zd.BANDS)
        self._fields = np.arange(1, n_fields + 1, dtype=np.int64)
        self._dates = pd.date_range(BASE, periods=n_dates, freq="16D")
        base = rng.uniform(0.05, 0.35, size=(n_fields, n_dates, len(self._bands)))
        # A smooth seasonal hump so NDVI looks like a crop, not noise.
        phase = np.sin(np.linspace(0, 2 * np.pi, n_dates))[None, :, None]
        base = base + 0.08 * phase
        self._stats = {
            "median": base,
            "mean": base,
            "std": np.abs(base) * 0.1,
            "p10": base * 0.85,
            "p25": base * 0.92,
            "p75": base * 1.06,
            "p90": base * 1.12,
            "iqr": np.abs(base) * 0.14,
        }

    @property
    def fields(self):
        return self._fields

    @property
    def dates(self):
        return self._dates

    @property
    def bands(self):
        return list(self._bands)

    @property
    def band_index(self):
        return {b: i for i, b in enumerate(self._bands)}

    def get_stat(self, name: str = "median"):
        if name not in self._stats:
            raise KeyError(name)
        return self._stats[name]


def make_cycles_table(*, n_cycles_per_field: int = 1) -> pd.DataFrame:
    rows = []
    cycle_id = 0
    for fid in range(1, N_FIELDS + 1):
        for c in range(n_cycles_per_field):
            cycle_id += 1
            t_start = 16 * (c * 20)
            rows.append({
                "field": fid,
                "cycle_id": cycle_id,
                "t_start": t_start,
                "t_end": t_start + 16 * 30,      # 30 dates ≈ 480 days
                "start_harvest": t_start,
                "censored": False,
            })
    return pd.DataFrame(rows)


@pytest.fixture
def cycles_path(tmp_path: Path) -> Path:
    path = tmp_path / "cycles.parquet"
    make_cycles_table().to_parquet(path)
    return path


# ---------------------------------------------------------------------------
# Channel presets
# ---------------------------------------------------------------------------
def test_presets_have_the_documented_channel_counts() -> None:
    assert len(zd.channel_specs("level")) == 1 + len(zd.BANDS)      # ndvi + 7 bands
    assert len(zd.channel_specs("lower")) == 1 + len(zd.BANDS)
    assert len(zd.channel_specs("spread")) == 2 * len(zd.BANDS)     # std + iqr, no index
    assert len(zd.channel_specs("dist")) == 3 + 6 * len(zd.BANDS)   # see docstring


def test_level_preset_is_the_reference_median_representation() -> None:
    names = zd.channel_names("level")
    assert names[0] == "ndvi_median", "the thresholded NDVI channel must come first"
    assert names[1:] == [f"{b}_median" for b in zd.BANDS]


def test_lower_preset_scores_only_lower_quantiles() -> None:
    names = zd.channel_names("lower")
    assert names[0] == "ndvi_p10"
    assert all(n.endswith("_p10") for n in names), (
        "the prompt's lower-quantile question must not be diluted by other statistics"
    )


def test_unknown_preset_is_rejected() -> None:
    with pytest.raises(KeyError, match="unknown preset"):
        zd.channel_specs("nope")


def test_channels_are_built_from_the_requested_statistic() -> None:
    reader = FakeReader()
    specs = zd.channel_specs("level")
    cubes = {s: reader.get_stat(s) for s in sorted({x.stat for x in specs})}
    chans = zd.stat_channels(cubes, reader.band_index, specs)
    np.testing.assert_allclose(
        chans["red_median"], reader.get_stat("median")[:, :, reader.band_index["red"]],
    )
    # ndvi from median red/nir — not a fitted or fabricated quantity.
    red = chans["red_median"]
    nir = chans["nir_median"]
    np.testing.assert_allclose(chans["ndvi_median"], np.clip((nir - red) / (nir + red + 1e-8), -1, 1))


def test_missing_statistic_is_a_hard_error() -> None:
    reader = FakeReader()
    specs = zd.channel_specs("dist")
    cubes = {"median": reader.get_stat("median")}   # p10 etc. missing
    with pytest.raises(KeyError, match="never fabricate"):
        zd.stat_channels(cubes, reader.band_index, specs)


def test_no_std_of_ndvi_is_fabricated() -> None:
    """std(NDVI) is NOT std(nir)/std(red) — inventing it would be a data error."""
    names = zd.channel_names("dist")
    assert "ndvi_std" not in names
    assert "ndvi_iqr" not in names
    assert sum(n.startswith("ndvi_") for n in names) == 3   # median, p10, p25


# ---------------------------------------------------------------------------
# Binning contracts (must mirror monitor/inputs.rebuild_masked_cycles)
# ---------------------------------------------------------------------------
def test_bin_cycle_matches_channel_by_channel_nanmedian() -> None:
    times = np.arange(0, 40, 3, dtype=np.int64)
    vals = np.linspace(0.2, 0.8, times.size)
    chans = {"ndvi_median": vals, "red_median": vals / 2}
    out = zd.bin_cycle(
        chans, ["ndvi_median", "red_median"], times_days=times,
        start_day=0, end_day=120, harvest_day=0, n_bins=36,
    )
    assert out is not None
    x, m = out
    assert x.shape == (36, 2)
    assert m.shape == (36, 2)
    # Every observed bin holds the 15-day median of the raw values.
    b = 0
    sel = (times >= 0) & (times < 15)
    assert x[b, 0] == pytest.approx(float(np.nanmedian(vals[sel])))
    assert m[b, 0]
    assert m[b, 1]
    assert np.isnan(x[20:, 0]).all(), "bins past the cycle end stay unobserved"


def test_bin_cycle_nan_marks_unobserved_bins() -> None:
    times = np.array([0, 30, 45, 60], dtype=np.int64)
    vals = np.array([0.5, np.nan, 0.6, 0.7])
    chans = {"ndvi_median": vals}
    out = zd.bin_cycle(chans, ["ndvi_median"], times_days=times,
                       start_day=0, end_day=90, harvest_day=0)
    x, m = out
    assert np.isnan(x[2, 0]), "a bin with only NaN stays unobserved"
    assert not m[2, 0]
    assert m[0, 0]
    assert x[0, 0] == pytest.approx(0.5)


def test_bin_cycle_rejects_indicators_under_three_observed_bins() -> None:
    times = np.array([0, 20], dtype=np.int64)
    chans = {"ndvi_median": np.array([0.5, 0.6])}
    assert zd.bin_cycle(chans, ["ndvi_median"], times_days=times,
                        start_day=0, end_day=60, harvest_day=0) is None


def test_bin_cycle_requires_ndvi_first() -> None:
    chans = {"red_median": np.array([0.2, 0.2, 0.2, 0.2])}
    with pytest.raises(ValueError, match="ndvi channel"):
        zd.bin_cycle(chans, ["red_median"], times_days=np.array([0, 10, 20, 30]),
                     start_day=0, end_day=60, harvest_day=0)


# ---------------------------------------------------------------------------
# End-to-end build
# ---------------------------------------------------------------------------
def test_build_produces_cycles_on_the_canonical_grid(cycles_path: Path) -> None:
    reader = FakeReader()
    out = zd.build_distribution_cycles(
        reader=reader, cycles_parquet_path=cycles_path, preset="dist",
    )
    assert out["X"].shape[1:] == (zd.N_BINS, len(zd.channel_names("dist")))
    assert len(out["cycle_keys"]) == len(out["field_ids"])
    assert out["band_names"] == zd.channel_names("dist")
    assert out["preset"] == "dist"
    # Mask and finiteness must agree exactly for every channel.
    np.testing.assert_array_equal(np.isfinite(out["X"]), out["M"])


def test_build_mask_discipline_no_zero_fill(cycles_path: Path) -> None:
    out = zd.build_distribution_cycles(reader=FakeReader(), cycles_parquet_path=cycles_path)
    assert np.isnan(out["X"][~out["M"]]).all(), "every masked cell must be NaN, never 0"
    observed = out["X"][out["M"]]
    assert np.isfinite(observed).all()


def test_build_lower_preset_only_carries_p10(cycles_path: Path) -> None:
    out = zd.build_distribution_cycles(
        reader=FakeReader(), cycles_parquet_path=cycles_path, preset="lower",
    )
    assert out["stats_used"] == ["p10"]
    assert all(n.endswith("_p10") for n in out["band_names"])


def test_build_stats_override_selects_a_subset(cycles_path: Path) -> None:
    out = zd.build_distribution_cycles(
        reader=FakeReader(), cycles_parquet_path=cycles_path, preset="dist",
        stats=["p10"],
    )
    assert out["stats_used"] == ["p10"]


def test_build_reference_keys_mismatch_is_a_hard_error(cycles_path: Path) -> None:
    with pytest.raises(RuntimeError, match="SAME cycles"):
        zd.build_distribution_cycles(
            reader=FakeReader(), cycles_parquet_path=cycles_path,
            reference_keys=["1:999"],
        )


def test_build_reference_keys_match_passes(cycles_path: Path) -> None:
    first = zd.build_distribution_cycles(
        reader=FakeReader(), cycles_parquet_path=cycles_path, preset="level",
    )
    again = zd.build_distribution_cycles(
        reader=FakeReader(), cycles_parquet_path=cycles_path, preset="level",
        reference_keys=first["cycle_keys"],
    )
    assert again["cycle_keys"] == first["cycle_keys"]


def test_build_reports_missing_cycle_table(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="cycle table missing"):
        zd.build_distribution_cycles(
            reader=FakeReader(), cycles_parquet_path=tmp_path / "nope.parquet",
        )


def test_build_reports_missing_statistic_in_store(cycles_path: Path) -> None:
    reader = FakeReader()
    del reader._stats["p10"]
    with pytest.raises(RuntimeError, match="distribution statistics"):
        zd.build_distribution_cycles(
            reader=reader, cycles_parquet_path=cycles_path, preset="lower",
        )


def test_negative_spread_statistic_is_rejected(cycles_path: Path) -> None:
    reader = FakeReader()
    reader._stats["std"] = reader._stats["std"].copy()
    reader._stats["std"][0, 0, 0] = -0.01
    with pytest.raises(ValueError, match="negative"):
        zd.build_distribution_cycles(
            reader=reader, cycles_parquet_path=cycles_path, preset="spread",
        )


def test_censored_cycles_are_skipped(tmp_path: Path) -> None:
    path = tmp_path / "cycles.parquet"
    df = make_cycles_table()
    df.loc[0, "censored"] = True
    df.to_parquet(path)
    out = zd.build_distribution_cycles(reader=FakeReader(), cycles_parquet_path=path)
    assert len(out["cycle_keys"]) == len(df) - 1


# ---------------------------------------------------------------------------
# Scoring through the unchanged path
# ---------------------------------------------------------------------------
def test_fit_score_b1_is_train_only(cycles_path: Path) -> None:
    """Perturbing the non-train cycles must not move the fitted statistics."""
    cycles = zd.build_distribution_cycles(
        reader=FakeReader(), cycles_parquet_path=cycles_path, preset="level",
    )
    n = len(cycles["X"])
    train = np.zeros(n, dtype=bool)
    train[: n // 2] = True
    _, scorer_a = zd.fit_score_b1(cycles, train_mask=train)
    perturbed = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in cycles.items()}
    perturbed["X"][~train] += 5.0
    _, scorer_b = zd.fit_score_b1(perturbed, train_mask=train)
    np.testing.assert_allclose(scorer_a.median, scorer_b.median)
    np.testing.assert_allclose(scorer_a.scale, scorer_b.scale)


def test_fit_score_b1_reproduces_the_reference_path(cycles_path: Path) -> None:
    """The `level` preset through B1 IS the b1 arm — same numbers, by construction."""
    from ssl_anomaly.monitor.models import B1PhaseZCausal

    cycles = zd.build_distribution_cycles(
        reader=FakeReader(), cycles_parquet_path=cycles_path, preset="level",
    )
    n = len(cycles["X"])
    train = np.ones(n, dtype=bool)
    train[:1] = False
    scores, scorer = zd.fit_score_b1(cycles, train_mask=train)

    ref = B1PhaseZCausal(use_doy=False, min_n=8)
    ref.fit(cycles["X"][train], cycles["M"][train])
    for i in range(n):
        np.testing.assert_allclose(
            scores[i], ref.score_cycle(cycles["X"][i], cycles["M"][i], None), rtol=1e-6,
        )


def test_fit_score_b1_masks_unobserved_bins(cycles_path: Path) -> None:
    cycles = zd.build_distribution_cycles(
        reader=FakeReader(), cycles_parquet_path=cycles_path, preset="level",
    )
    train = np.ones(len(cycles["X"]), dtype=bool)
    scores, _ = zd.fit_score_b1(cycles, train_mask=train)
    unobserved = ~cycles["M"].any(axis=2)
    assert np.isnan(scores[unobserved]).all()


def test_fit_score_b1_validates_the_mask(cycles_path: Path) -> None:
    cycles = zd.build_distribution_cycles(
        reader=FakeReader(), cycles_parquet_path=cycles_path, preset="level",
    )
    with pytest.raises(ValueError, match="train_mask shape"):
        zd.fit_score_b1(cycles, train_mask=np.ones(3, dtype=bool))
    with pytest.raises(ValueError, match="selects no cycle"):
        zd.fit_score_b1(cycles, train_mask=np.zeros(len(cycles["X"]), dtype=bool))


def test_alarm_rates_uses_the_existing_persistence_rule(cycles_path: Path) -> None:
    cycles = zd.build_distribution_cycles(
        reader=FakeReader(), cycles_parquet_path=cycles_path, preset="level",
    )
    train = np.ones(len(cycles["X"]), dtype=bool)
    scores, _ = zd.fit_score_b1(cycles, train_mask=train)
    low = zd.alarm_rates(scores, tau=1e9, k=2)
    assert not low.any(), "an unreachable threshold must produce no alarm"
    high = zd.alarm_rates(scores, tau=-1.0, k=2)
    # Some cycles have >=2 observed bins, so a permissive tau must fire somewhere.
    assert high.any()


def test_lower_quantile_arm_detects_a_drop_the_mean_hides() -> None:
    """The prompt's core R0.5 hypothesis, as a unit test.

    A p10-only drop with the median untouched (deterioration of PART of the
    field) moves the lower-quantile score and leaves the median score flat.
    """
    reader = FakeReader()
    # Clean cycles for the median arm, then degrade only p10 at one field.
    p10 = reader._stats["p10"].copy()
    p10[:, :, :] *= 0.6                        # a 40 % lower-tail deterioration
    reader._stats["p10"] = p10

    level_specs = zd.channel_specs("level")
    lower_specs = zd.channel_specs("lower")
    bi = reader.band_index
    level = zd.stat_channels({s: reader.get_stat(s) for s in ("median",)},
                             bi, level_specs)
    lower = zd.stat_channels({s: reader.get_stat(s) for s in ("p10",)},
                             bi, lower_specs)
    # The lower-quantile statistics moved; the median statistics did not.
    assert not np.allclose(lower["red_p10"], level["red_median"] * 0.6)
    assert np.allclose(level["red_median"], reader.get_stat("median")[:, :, bi["red"]])


# ---------------------------------------------------------------------------
# b0_calendar variant + p10 path-max (compare-spatial-representation task 2.3)
# ---------------------------------------------------------------------------
def _cycles_for_scoring(n=6, seed=0):
    g = np.random.default_rng(seed)
    T, C = zd.N_BINS, len(zd.channel_specs("level"))
    X = np.abs(g.normal(0.5, 0.1, (n, T, C))).astype(np.float32)
    M = np.ones((n, T, C), dtype=bool)
    M[0, :4] = False
    return {"X": X, "M": M, "field_ids": np.arange(n), "cycle_keys": [f"f{i}:c" for i in range(n)]}


def test_calendar_bins_are_in_range_and_monotone_in_day():
    bins = np.arange(zd.N_BINS)
    a = zd.calendar_doy_bins(bins, start_day=0)
    b = zd.calendar_doy_bins(bins, start_day=0)
    assert a.min() >= 0
    assert a.max() < zd.N_BINS
    np.testing.assert_array_equal(a, b)
    # a later cycle start shifts the calendar assignment, never the cycle bins
    c = zd.calendar_doy_bins(bins, start_day=60)
    assert not np.array_equal(a, c)


def test_calendar_scorer_leaks_no_test_cycle():
    cyc = _cycles_for_scoring()
    train = np.array([True, True, True, False, False, False])
    starts = np.zeros(len(cyc["X"]), dtype=int)
    s1, _ = zd.fit_score_calendar(cyc, train_mask=train, start_days=starts, min_n=2)
    cyc2 = {k: (v.copy() if hasattr(v, "copy") else v) for k, v in cyc.items()}
    cyc2["X"][3:] *= 100.0
    s2, _ = zd.fit_score_calendar(cyc2, train_mask=train, start_days=starts, min_n=2)
    np.testing.assert_allclose(s1[:3], s2[:3], equal_nan=True)
    assert not np.allclose(s1[3:], s2[3:], equal_nan=True)


def test_calendar_scorer_rejects_an_empty_train_mask():
    cyc = _cycles_for_scoring()
    with pytest.raises(ValueError, match="selects no cycle"):
        zd.fit_score_calendar(cyc, train_mask=np.zeros(6, bool),
                              start_days=np.zeros(6, int))


def test_calendar_scorer_nan_where_unobserved():
    cyc = _cycles_for_scoring()
    scores, _ = zd.fit_score_calendar(
        cyc, train_mask=np.ones(6, bool), start_days=np.zeros(6, int), min_n=2,
    )
    assert np.isnan(scores[0, :4]).all()
    assert np.isfinite(scores[0, 4:]).all()


def test_pathmax_picks_the_single_channel_evidence():
    T, C = zd.N_BINS, 8
    z2 = np.zeros((2, T, C))
    z2[0, 5, 2] = 9.0           # one channel spikes
    z2[0, 5, 0] = 1.0
    m = np.ones((2, T, C), dtype=bool)
    out = zd.pathmax_scores(z2, [0, 2], m)
    assert out[0, 5] == 9.0
    mean = z2[0, 5].sum() / C
    assert out[0, 5] > mean     # the max is not diluted by the 8-channel mean


def test_pathmax_is_nan_when_no_subset_channel_is_observed():
    T, C = 4, 3
    z2 = np.ones((1, T, C))
    m = np.ones((1, T, C), dtype=bool)
    m[0, 2, :] = False
    assert np.isnan(zd.pathmax_scores(z2, [0, 1], m)[0, 2])


def test_pathmax_validates_channel_indices():
    with pytest.raises(ValueError, match="out of range"):
        zd.pathmax_scores(np.ones((1, 2, 3)), [7], np.ones((1, 2, 3), bool))


def test_channel_z2_matches_the_b1_decomposition():
    cyc = _cycles_for_scoring()
    scores, scorer = zd.fit_score_b1(cyc, train_mask=np.ones(6, bool))
    group = (np.asarray(scorer.season_group if callable(scorer.season_group) else 0))
    # no doy context was given, so every bin uses group 0
    z2 = zd.channel_z2(cyc, median=scorer.median, scale=scorer.scale,
                       group=np.zeros((6, zd.N_BINS), dtype=int))
    mean = z2.sum(axis=2) / np.maximum(cyc["M"].sum(axis=2), 1)
    np.testing.assert_allclose(mean, scores, atol=1e-6, equal_nan=True)


def test_pathmax_on_lower_still_sees_the_p10_signal():
    """The p10 arm scored by path-max must react to a p10 channel shift."""
    cyc = _cycles_for_scoring()
    names = zd.channel_names("lower")
    scores, scorer = zd.fit_score_b1(cyc, train_mask=np.ones(6, bool))
    z2 = zd.channel_z2(cyc, median=scorer.median, scale=scorer.scale,
                       group=np.zeros((6, zd.N_BINS), dtype=int))
    ndvi_p10 = names.index("ndvi_p10")
    base = zd.pathmax_scores(z2, [ndvi_p10], cyc["M"])

    cyc2 = dict(cyc.items())
    cyc2["X"] = cyc["X"].copy()
    cyc2["X"][1, 20, ndvi_p10] -= 1.0
    s2, scorer2 = zd.fit_score_b1(cyc2, train_mask=np.ones(6, bool))
    z2b = zd.channel_z2(cyc2, median=scorer2.median, scale=scorer2.scale,
                        group=np.zeros((6, zd.N_BINS), dtype=int))
    after = zd.pathmax_scores(z2b, [ndvi_p10], cyc["M"])
    assert after[1, 20] > base[1, 20]
