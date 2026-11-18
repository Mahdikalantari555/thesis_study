"""Deterministic seeding across numpy, random, torch."""

from __future__ import annotations

import logging
import os
import random

log = logging.getLogger("ssl_anomaly.seeds")


def seed_everything(seed: int = 42, *, deterministic_algo: bool = True) -> int:
    """Seed Python, numpy, and (if available) torch RNGs.

    Returns the seed used. When torch is present and ``deterministic_algo``
    is True, deterministic CuDNN/algorithms are requested (warn-only).
    """
    seed = int(seed)
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:  # pragma: no cover
        pass

    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            if deterministic_algo:
                try:
                    torch.use_deterministic_algorithms(True, warn_only=True)
                except Exception as exc:  # pragma: no cover
                    log.warning("Could not enable deterministic torch algorithms: %s", exc)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

    log.debug("Seeded everything with %d", seed)
    return seed


def current_seed() -> int | None:
    """Best-effort: return the seed from PYTHONHASHSEED if set, else None."""
    s = os.environ.get("PYTHONHASHSEED")
    return int(s) if s and s.isdigit() else None
