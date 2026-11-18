"""Resource throttling: BLAS threads, process priority, memory headroom.

Call :func:`limit_threads` BEFORE importing numpy/torch so environment
variables take effect. This matches the laptop profile described in the
implementation plan (2 BLAS threads, low priority, wait for ≥2 GB free RAM).
"""

from __future__ import annotations

import logging
import os
import time

log = logging.getLogger("ssl_anomaly.throttle")

_THREAD_KEYS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "GDAL_NUM_THREADS",
)


def limit_threads(n: int = 2) -> None:
    """Cap BLAS / OpenMP / MKL / NumExpr threads. Call before numpy/torch import."""
    n = max(1, int(n))
    for key in _THREAD_KEYS:
        os.environ[key] = str(n)
    os.environ.setdefault("GDAL_CACHEMAX", "512")  # MB
    os.environ.setdefault("OMP_PROC_BIND", "TRUE")
    # On Windows the Intel-MKL numpy build and torch each ship their own OpenMP
    # runtime. When both are loaded, LAPACK calls (np.cov / np.linalg.svd /
    # solve / inv, and therefore scipy.stats.spearmanr) can abort the process
    # with a native exception (0xC06D007F, "application has failed to start").
    # Forcing MKL onto its sequential layer keeps LAPACK usable.
    if os.name == "nt":  # pragma: win32 cover
        os.environ.setdefault("MKL_THREADING_LAYER", "SEQUENTIAL")
    log.debug("Set BLAS/OpenMP threads to %d", n)


def lower_priority() -> None:
    """Lower process priority (nice 10 on POSIX, BELOW_NORMAL on Windows)."""
    try:
        import psutil

        p = psutil.Process()
        try:
            if os.name == "nt":  # pragma: win32 cover
                p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)  # type: ignore[attr-defined]
            else:
                p.nice(10)
            log.debug("Lowered process priority")
        except (PermissionError, psutil.AccessDenied):
            log.debug("Could not lower priority (permission denied); continuing")
    except ImportError:  # pragma: no cover
        log.debug("psutil unavailable; skipping priority adjustment")


def wait_for_headroom(
    min_free_gb: float = 2.0,
    poll_s: float = 5.0,
    timeout_s: float | None = None,
) -> bool:
    """Block until available memory >= min_free_gb. Returns True if headroom reached.

    If ``timeout_s`` is given and reached, returns False (caller can decide).
    """
    try:
        import psutil
    except ImportError:  # pragma: no cover
        return True  # can't check; proceed
    target = min_free_gb * 2 ** 30
    start = time.monotonic()
    while True:
        free = psutil.virtual_memory().available
        if free >= target:
            return True
        if timeout_s is not None and (time.monotonic() - start) > timeout_s:
            log.warning(
                "wait_for_headroom: only %.1f GB free after %.0f s (need %.1f GB); continuing",
                free / 2 ** 30,
                time.monotonic() - start,
                min_free_gb,
            )
            return False
        log.debug(
            "Low memory (%.2f GB free < %.2f GB); sleeping %.0fs",
            free / 2 ** 30,
            min_free_gb,
            poll_s,
        )
        time.sleep(poll_s)
