"""ssl_anomaly — Self-supervised phenology-aware anomaly detection."""

from __future__ import annotations

import os as _os

# Windows/MKL guard — MUST run before numpy/scipy are imported anywhere.
# On Windows the Intel-MKL numpy build and torch each load their own OpenMP
# runtime; when both are present, LAPACK entry points (np.cov, np.linalg.svd,
# np.linalg.solve, np.linalg.inv — and therefore scipy.stats.spearmanr /
# pearsonr) abort the whole process with a native exception 0xC06D007F
# ("The application was unable to start correctly"), which surfaces as a
# silent exit code -1066598273 instead of a Python traceback.
# Pinning MKL to its sequential threading layer keeps LAPACK usable.
if _os.name == "nt":  # pragma: win32 cover
    _os.environ.setdefault("MKL_THREADING_LAYER", "SEQUENTIAL")

__version__ = "0.1.0"
__all__ = ["__version__"]
