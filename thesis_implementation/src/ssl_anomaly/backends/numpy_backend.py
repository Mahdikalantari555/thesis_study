"""Reference NumPy backend — used everywhere in v1; parity-tested against future Rust."""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve


class NumpyBackend:
    name: str = "numpy"

    def whittaker_batch(self, y: np.ndarray, w: np.ndarray, lam: float) -> np.ndarray:
        """Vectorized Whittaker smoothing for a batch of equal-length signals.

        Parameters
        ----------
        y: (B, T) — signals (NaN → w=0)
        w: (B, T) — weights
        lam: smoothing parameter
        """
        y = np.asarray(y, dtype=np.float64)
        w = np.asarray(w, dtype=np.float64)
        if y.ndim == 1:
            y = y[None, :]
            w = w[None, :]
        B, T = y.shape
        # Build penalty matrix once
        D = sparse.eye(T, format="csr", dtype=np.float64)
        for _ in range(2):
            D = D[1:, :] - D[:-1, :]
        P = (D.T @ D).tocsc()
        out = np.empty_like(y)
        lamP = float(lam) * P
        for b in range(B):
            wb = w[b].copy()
            wb[~np.isfinite(y[b])] = 0.0
            yb = np.where(np.isfinite(y[b]), y[b], 0.0)
            W = sparse.diags(wb, format="csc", dtype=np.float64)
            A = W + lamP
            out[b] = spsolve(A, wb * yb)
        return out

    def robust_baseline(
        self, X: np.ndarray, min_n: int = 5
    ) -> tuple[np.ndarray, np.ndarray]:
        """Robust baseline (median, MAD_scale) per (bin, band).

        X: (cycles, bins, bands). Returns median (bins, bands), scale (bins, bands).
        Bins with fewer than min_n finite observations get NaN.
        """
        X = np.asarray(X, dtype=np.float64)
        if X.ndim != 3:
            raise ValueError(f"expected 3-D X (cycles, bins, bands); got shape {X.shape}")
        with np.errstate(all="ignore"):
            n = np.sum(np.isfinite(X), axis=0)
            med = np.nanmedian(X, axis=0)
            scale = np.nanmedian(np.abs(X - med[None, :, :]), axis=0) * 1.4826
        bad = n < min_n
        med[bad] = np.nan
        scale[bad] = np.nan
        return med, scale
