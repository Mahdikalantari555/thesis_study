"""Tests for utils.throttle."""

from __future__ import annotations

import os

from ssl_anomaly.utils.throttle import limit_threads, lower_priority, wait_for_headroom


def test_limit_threads_sets_env_vars() -> None:
    limit_threads(3)
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        assert os.environ[key] == "3"


def test_wait_for_headroom_returns_true() -> None:
    # With a very small min_free_gb should always return immediately
    assert wait_for_headroom(min_free_gb=0.01, poll_s=0.01, timeout_s=1.0) is True


def test_lower_priority_does_not_crash() -> None:
    # Should run without raising (may be a no-op without permissions)
    lower_priority()
