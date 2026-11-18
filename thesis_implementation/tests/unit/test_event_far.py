"""Event declustering + event-level FAR + Wilson CI tests (change
literature-grounded-severity-protocol, task 2.1; sktime FalseAlarmRate
semantics, POT declustering precedent)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ssl_anomaly.monitor import scoring as mscoring  # noqa: E402


# ---------------------------------------------------------------------------
# Decluster alarms into events (spec scenario 'Event declustering')
# ---------------------------------------------------------------------------
def test_decluster_adjacent_bins_one_event() -> None:
    """Consecutive alarmed bins are ONE event."""
    events = mscoring.decluster_events([5, 6, 7], gap=2)
    assert events == [(5, 7)]


def test_decluster_gap2_one_event_gap3_two_events() -> None:
    """Bin-index distance ≤ gap merges (spec: 'gap ≤ 2 bins → one event');
    a larger separation starts a new event."""
    assert mscoring.decluster_events([5, 7], gap=2) == [(5, 7)]
    assert mscoring.decluster_events([5, 8], gap=2) == [(5, 5), (8, 8)]
    # 4→7 is bin-distance 3 (> gap) → separate; 20→22 distance 2 → merged.
    assert mscoring.decluster_events([2, 4, 7, 20, 22], gap=2) == [(2, 4), (7, 7), (20, 22)]


def test_decluster_empty_and_single() -> None:
    assert mscoring.decluster_events([], gap=2) == []
    assert mscoring.decluster_events([9], gap=2) == [(9, 9)]


# ---------------------------------------------------------------------------
# Event-level FAR (sktime semantics)
# ---------------------------------------------------------------------------
def test_event_far_clean_cycle_all_events_false() -> None:
    """A clean cycle has no injection windows → every event is false."""
    paths = np.full((2, 36), np.nan)
    paths[0, 5:8] = 10.0
    paths[0, 20] = 10.0
    paths[1, 3] = 10.0
    res = mscoring.event_far_from_paths(paths, [None, None], tau=5.0)
    # Cycle 0: events (5-7) and (20) = 2 false; cycle 1: event (3) = 1 false.
    assert res["n_events"] == 3
    assert res["n_false_events"] == 3
    # Denominator = scored bins (finite statistic) = 3 + 1 + 1.
    assert res["n_scored_bins"] == 5
    assert res["event_far"] == pytest.approx(3.0 / 5.0)


def test_event_far_alarms_inside_hit_window_not_double_counted() -> None:
    """sktime semantics: alarms hitting an injection window are not false, and
    extra alarms inside an already-hit window are not double-counted."""
    paths = np.full((1, 36), np.nan)
    paths[0, [10, 11, 12, 15, 16]] = 10.0  # two events inside the window
    windows = [[(10, 17)]]  # injected bins 10..16 inclusive-exclusive
    res = mscoring.event_far_from_paths(paths, windows, tau=5.0)
    assert res["n_events"] == 2  # gap-2 declustering splits at the 12→15 distance-3 gap
    assert res["n_false_events"] == 0


def test_event_far_mixed_hit_and_false() -> None:
    paths = np.full((1, 36), np.nan)
    paths[0, [10, 11]] = 10.0   # hits the window
    paths[0, [25, 27]] = 10.0   # gap-2 event outside → false
    paths[0, [33]] = 10.0       # separate event outside → false
    res = mscoring.event_far_from_paths(paths, [[(10, 14)]], tau=5.0)
    assert res["n_events"] == 3
    assert res["n_false_events"] == 2
    assert res["event_far"] == pytest.approx(2.0 / 5.0)


def test_event_far_zero_alarms() -> None:
    paths = np.full((2, 36), np.nan)
    paths[0, :20] = 1.0
    res = mscoring.event_far_from_paths(paths, [None, [(5, 8)]], tau=5.0)
    assert res["n_events"] == 0 and res["n_false_events"] == 0
    assert res["event_far"] == 0.0


def test_event_far_nan_paths_ignored() -> None:
    """NaN bins are unscored and never alarms; they do not enter the
    denominator."""
    paths = np.full((1, 36), np.nan)
    paths[0, 10] = 10.0
    res = mscoring.event_far_from_paths(paths, [None], tau=5.0)
    assert res["n_scored_bins"] == 1
    assert res["event_far"] == 1.0


# ---------------------------------------------------------------------------
# Wilson score CI
# ---------------------------------------------------------------------------
def test_wilson_ci_basics() -> None:
    lo, hi = mscoring.wilson_ci(8, 10)
    assert 0.49 < lo < 0.55 and 0.85 < hi < 0.95
    lo0, hi0 = mscoring.wilson_ci(0, 10)
    assert lo0 == 0.0 and 0.0 < hi0 < 0.35
    lo1, hi1 = mscoring.wilson_ci(10, 10)
    assert 0.70 < lo1 < 1.0 and hi1 == pytest.approx(1.0)


def test_wilson_ci_edge_cases() -> None:
    assert np.isnan(mscoring.wilson_ci(0, 0)[0])
    assert np.isnan(mscoring.wilson_ci(0, 0)[1])
