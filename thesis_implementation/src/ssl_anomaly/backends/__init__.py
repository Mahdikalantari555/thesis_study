"""Backend abstraction for future Rust acceleration.

Implements the :class:`PhenologyBackend` Protocol and a Numpy reference
backend. A Rust backend stub is provided but raises NotImplementedError
until gate G3 is passed; it will live in a separate ``ssl_anomaly_rs``
package loaded at runtime.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np

from .numpy_backend import NumpyBackend


class PhenologyBackend(Protocol):
    """Interface shared by the numpy reference backend and any future Rust backend.

    Every method MUST produce bit-identical results (within rtol=1e-6) across
    backends; parity tests enforce this.
    """

    name: str

    def whittaker_batch(self, y: np.ndarray, w: np.ndarray, lam: float) -> np.ndarray:
        """Smooth a batch of 1-D signals. Inputs (B, T), outputs (B, T)."""
        ...

    def robust_baseline(
        self, X: np.ndarray, min_n: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute per-bin/band median and MAD scale. X: (cycles, bins, bands)."""
        ...


def get_backend(name: str = "numpy") -> PhenologyBackend:
    """Return the backend by name (``"numpy"`` or ``"rust"``). Rust is stub-only in v1."""
    if name == "numpy":
        return NumpyBackend()
    if name == "rust":
        try:
            from ssl_anomaly_rs import RustBackend  # type: ignore

            return RustBackend()
        except ImportError as exc:
            raise NotImplementedError(
                "Rust backend not installed; build & install ssl_anomaly_rs after gate G3."
            ) from exc
    raise ValueError(f"Unknown backend: {name!r}. Expected 'numpy' or 'rust'.")


__all__ = ["NumpyBackend", "PhenologyBackend", "get_backend"]
