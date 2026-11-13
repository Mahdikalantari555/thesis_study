"""Discover and load trained anomaly-detector checkpoints for the platform exporter.

The literature checkpoints saved by ``scripts/train_literature_checkpoints.py``
are ``torch.save`` dicts with the keys ``architecture``/``state_dict``/``center``
/``scale``/``shape``/``n_bands`` (the MaskedSSL wrapper's normalization stats and
token shape). This module reconstructs each model from those artifacts and
exposes a ``LoadedModel.score_cycles`` interface used by
``scripts/export_platform_data.py`` to produce real anomaly scores.

Per-score provenance (see ``platform_channels.SCORE_REGISTRY``):
  - checkpoint found and reconstructed  -> provenance ``"model"``
  - no artifact for the score key       -> proxy formula (``"proxy"``)
  - artifact present but load failed    -> ``"absent"`` (never a faked score)
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

import torch

from platform_channels import SCORE_CHECKPOINTS, SCORE_NAMES  # type: ignore

log = logging.getLogger("load_model_checkpoints")

DEFAULT_CHECKPOINT_DIR = ROOT_DIR / "checkpoints"

# MaskedSSL hyper-parameters used by train_literature_checkpoints.py; scoring
# must mirror the training-time masking (causal=True).
CAUSAL = True
BATCH_SIZE = 32


def model_formula_id(model_id: str) -> str:
    """Formula id recorded on observations scored by a loaded checkpoint."""
    return f"{model_id}_490:bin_mse_1mexp"


def squash_bin_error(err: float | np.ndarray) -> float | np.ndarray:
    """Map leave-one-bin-out reconstruction MSE (z-space, [0, inf)) to (0, 1).

    Monotone squash ``1 - exp(-err)`` so the platform's 0-1 score display,
    colours and ANOMALY_THRESHOLD stay meaningful; ranking is preserved.
    """
    return 1.0 - np.exp(-err)


def _build_model(architecture: str, n_bands: int, shape: tuple[int, int]):
    """Construct the bare model exactly as ssl_anomaly.eval.growth_ssl.MaskedSSL.fit does."""
    import importlib

    d_in = 2 * n_bands + 1
    if architecture == "gru_ae":
        cls = importlib.import_module("ssl_anomaly.models.gru_ae").GRUAutoencoder
        return cls(d_in=d_in, d_model=32, n_layers=1, dropout=0)
    if architecture == "sts_net":
        cls = importlib.import_module("ssl_anomaly.models.sts_net").STSNetAutoencoder
        return cls(d_in=d_in, d_model=32, latent_dim=16)
    if architecture == "tiny_cnn_mamba":
        cls = importlib.import_module("ssl_anomaly.models.cnn_mamba").TinyCNNMamba
        return cls(d_in=d_in, d_model=32, d_state=8, n_layers=2, latent_dim=16)
    if architecture == "time2agri":
        cls = importlib.import_module("ssl_anomaly.models.pretexts").PretextTransformer
        return cls(
            d_in=d_in, n_bands=n_bands, d_model=32, n_heads=4, n_layers=2,
            d_ff=64, dropout=.1, max_len=max(128, shape[0]), arm="masked_recon",
        )
    raise ValueError(f"unsupported architecture {architecture}")


@dataclass
class LoadedModel:
    """A reconstructed checkpoint exposing the MaskedSSL per-bin scoring interface."""

    model_id: str
    checkpoint_path: Path
    architecture: str
    n_bands: int
    shape: tuple[int, int]
    center: np.ndarray
    scale: np.ndarray
    _wrapper: object

    def score_cycles(self, X: np.ndarray) -> np.ndarray:
        """Per-bin leave-one-time-bin-out reconstruction error, shape ``(n_cycles, n_bins)``."""
        return np.asarray(self._wrapper.score(X), dtype=np.float64)

    @property
    def parameter_count(self) -> int:
        return getattr(self._wrapper, "parameter_count", 0)


def _load_one(model_id: str, path: Path) -> LoadedModel:
    from ssl_anomaly.eval.growth_ssl import MaskedSSL

    ckpt = torch.load(str(path), map_location="cpu", weights_only=False)
    architecture = str(ckpt["architecture"])
    shape = tuple(int(v) for v in ckpt["shape"])
    n_bands = int(ckpt["n_bands"])

    # Reuse the MaskedSSL scoring implementation; fit() is never called, the
    # fitted attributes come straight from the checkpoint's sidecar stats.
    wrapper = MaskedSSL(
        architecture=architecture, epochs=1, seed=42,
        batch_size=BATCH_SIZE, causal=CAUSAL, train_enabled=False,
    )
    wrapper.shape = shape
    wrapper.n_bands = n_bands
    wrapper.center = np.asarray(ckpt["center"], dtype=np.float64)
    wrapper.scale = np.asarray(ckpt["scale"], dtype=np.float64)
    model = _build_model(architecture, n_bands, shape)
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    wrapper.model = model
    torch.set_num_threads(1)
    return LoadedModel(
        model_id=model_id, checkpoint_path=path, architecture=architecture,
        n_bands=n_bands, shape=shape, center=wrapper.center, scale=wrapper.scale,
        _wrapper=wrapper,
    )


def discover_checkpoints(ckpt_dir: Path | str | None = None) -> dict[str, Optional[Path]]:
    """Map each registered model id to its ``<id>_490.pt`` artifact (or None)."""
    base = Path(ckpt_dir) if ckpt_dir is not None else DEFAULT_CHECKPOINT_DIR
    found: dict[str, Optional[Path]] = {}
    for model_id, stem in SCORE_CHECKPOINTS.items():
        path = base / f"{stem}.pt"
        found[model_id] = path if path.exists() else None
    return found


def load_model_checkpoints(
    ckpt_dir: Path | str | None = None,
    model_ids: tuple[str, ...] | None = None,
) -> tuple[dict[str, Optional[LoadedModel]], dict[str, str]]:
    """Load every discoverable checkpoint.

    Returns ``(models, status)`` where ``models[model_id]`` is a
    :class:`LoadedModel` or ``None`` and ``status[model_id]`` is one of
    ``"loaded"`` | ``"missing"`` | ``"failed"``. A failed load is never
    silently converted into proxy numbers downstream (provenance ``"absent"``).
    """
    wanted = tuple(model_ids) if model_ids is not None else tuple(SCORE_CHECKPOINTS)
    discovered = discover_checkpoints(ckpt_dir)
    models: dict[str, Optional[LoadedModel]] = {}
    status: dict[str, str] = {}
    for model_id in wanted:
        path = discovered.get(model_id)
        if path is None:
            models[model_id] = None
            status[model_id] = "missing"
            log.warning(
                "No checkpoint for %s under %s (scores will fall back to the proxy formula)",
                model_id, Path(ckpt_dir) if ckpt_dir is not None else DEFAULT_CHECKPOINT_DIR,
            )
            continue
        try:
            models[model_id] = _load_one(model_id, path)
            status[model_id] = "loaded"
            log.info(
                "Loaded %s (%s, shape %s, %d params) from %s",
                model_id, models[model_id].architecture, models[model_id].shape,
                models[model_id].parameter_count, path,
            )
        except Exception as exc:  # noqa: BLE001 - any load failure must degrade gracefully
            models[model_id] = None
            status[model_id] = "failed"
            log.error("Checkpoint for %s could not be reconstructed from %s: %s", model_id, path, exc)
    return models, status


__all__ = [
    "LoadedModel", "DEFAULT_CHECKPOINT_DIR", "CAUSAL", "BATCH_SIZE",
    "discover_checkpoints", "load_model_checkpoints", "squash_bin_error",
    "model_formula_id",
]
