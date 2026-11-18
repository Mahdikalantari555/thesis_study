"""Discover and load trained anomaly-detector checkpoints for the platform exporter.

Two checkpoint families (contract v5):

* **Causal main checkpoints** (``checkpoints/masked_transformer_main.pt`` +
  ``.json`` sidecar, ``gru_ae_main.pt`` + ``.json``) written by
  ``scripts/train_main.py`` (format ``causal_monitor_v1``) and frozen by
  ``scripts/freeze_main_model.py``. They are reconstructed with
  ``ssl_anomaly.monitor.models.build_model`` + ``DeepCausalScorer`` and score
  MASKED (never-interpolated) cycle tensors causally; the sidecar carries the
  robust normalization (median/scale per phase bin x band), the calibrated
  tau/persistence-k threshold and the ladder rung. These load into
  :class:`LoadedCausalModel`, whose ``score_cycles`` returns RAW z-space
  per-bin scores (no squash — thresholds live on the raw axis).

* **Legacy literature checkpoints** (``sts_net_490.pt``, ``tiny_cnn_mamba_490.pt``,
  ``time2agri_490.pt``) saved by ``scripts/train_literature_checkpoints.py``
  with keys ``architecture``/``state_dict``/``center``/``scale``/``shape``/
  ``n_bands``. They load into :class:`LoadedModel` (MaskedSSL wrapper) and
  score the interpolated cycle tensors exactly as before.

Per-score provenance (see ``platform_channels.SCORE_REGISTRY``), contract v5:
  - checkpoint found and reconstructed      -> provenance ``"model"``
  - no artifact (or sidecar missing)        -> slot ``"absent"`` (score null)
  - artifact present but load failed        -> ``"absent"`` (never a faked score)
There is NO proxy fallback in v5: the CWSI proxy formula was removed
(circular with the model inputs; spec model-output-ingest).
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

import torch

from platform_channels import SCORE_CHECKPOINTS  # type: ignore

log = logging.getLogger("load_model_checkpoints")

DEFAULT_CHECKPOINT_DIR = ROOT_DIR / "checkpoints"

# MaskedSSL hyper-parameters used by train_literature_checkpoints.py; scoring
# must mirror the training-time masking (causal=True).
CAUSAL = True
BATCH_SIZE = 32

# Stems of the causal main checkpoints (format causal_monitor_v1, scored via
# ssl_anomaly.monitor.models.DeepCausalScorer on masked cycle tensors, raw
# z-space scores). Formula id "<stem>:causal_bin_mse".
CAUSAL_MODEL_STEMS = {"masked_transformer_main", "gru_ae_main"}

CAUSAL_FORMULA_SUFFIX = "causal_bin_mse"
LEGACY_FORMULA_SUFFIX = "bin_mse_1mexp"


def is_causal_stem(stem: str) -> bool:
    """True when the checkpoint stem is a causal main model (v5 scoring path)."""
    return stem in CAUSAL_MODEL_STEMS


def causal_formula_id(stem: str) -> str:
    """Formula id for observations scored by a causal main checkpoint."""
    return f"{stem}:{CAUSAL_FORMULA_SUFFIX}"


def model_formula_id(model_id: str) -> str:
    """Formula id recorded on observations scored by a loaded LEGACY checkpoint."""
    return f"{model_id}_490:{LEGACY_FORMULA_SUFFIX}"


def score_formula_id(score_key: str) -> Optional[str]:
    """Formula id a model-backed slot records on its scored observations.

    ``None`` for slots without a registered checkpoint (baseline heuristics).
    """
    stem = SCORE_CHECKPOINTS.get(score_key)
    if stem is None:
        return None
    if is_causal_stem(stem):
        return causal_formula_id(stem)
    return model_formula_id(score_key)


def squash_bin_error(err: float | np.ndarray) -> float | np.ndarray:
    """Map leave-one-bin-out reconstruction MSE (z-space, [0, inf)) to (0, 1).

    Monotone squash ``1 - exp(-err)`` so the platform's 0-1 score display,
    colours and ANOMALY_THRESHOLD stay meaningful; ranking is preserved.
    DISPLAY ONLY: the causal stress flag compares RAW scores against the
    sidecar threshold tau (calibrated on the raw axis).
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
    """A reconstructed LEGACY checkpoint exposing the MaskedSSL per-bin scoring interface."""

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


@dataclass
class LoadedCausalModel:
    """A reconstructed causal main checkpoint (v5) with its sidecar metadata.

    Wraps ``ssl_anomaly.monitor.models.DeepCausalScorer``; the robust
    normalization (median/scale per phase bin x band) comes from the sidecar's
    ``normalization`` block and is applied INSIDE ``score_cycles`` — callers
    pass RAW (never-interpolated, NaN-where-unobserved) cycle values plus the
    observation mask and the harvest days.
    """

    model_id: str  # checkpoint id, e.g. "masked_transformer_main"
    score_key: str  # score slot in SCORE_REGISTRY, e.g. "masked_transformer"
    checkpoint_path: Path
    sidecar_path: Path
    sidecar: dict = field(repr=False, default_factory=dict)
    family: str = ""
    use_doy: bool = True
    _scorer: object = None
    _norm: dict = field(repr=False, default_factory=dict)

    def score_cycles(self, X_raw: np.ndarray, M: np.ndarray, harvest_days: np.ndarray) -> np.ndarray:
        """RAW per-bin causal scores ``(n_cycles, n_bins)`` (no squash).

        NaN at unobserved bins (mask all-False). Display squash
        (:func:`squash_bin_error`) is applied by the caller, never here — the
        sidecar threshold tau is calibrated on the raw axis.
        """
        from ssl_anomaly.monitor.inputs import apply_norm, doy_channels

        z = apply_norm(self._norm, np.asarray(X_raw), np.asarray(M, dtype=bool))
        doy = doy_channels(np.asarray(harvest_days, dtype=np.int64)) if self.use_doy else None
        scores, _ = self._scorer.loo_batch(z, np.asarray(M, dtype=bool), doy)
        return np.asarray(scores, dtype=np.float64)

    @property
    def parameter_count(self) -> int:
        return int(self.sidecar.get("parameter_count", 0) or 0)

    @property
    def ladder_rung(self) -> Optional[str]:
        rung = self.sidecar.get("ladder_rung")
        return str(rung) if rung else None

    @property
    def threshold(self) -> Optional[dict]:
        thr = self.sidecar.get("threshold")
        return dict(thr) if isinstance(thr, dict) else None


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


def _load_causal_one(score_key: str, stem: str, pt_path: Path, sidecar_path: Path) -> LoadedCausalModel:
    """Reconstruct a causal main checkpoint (``causal_monitor_v1``) + sidecar."""
    from ssl_anomaly.monitor.models import DeepCausalScorer, build_model

    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    ckpt = torch.load(str(pt_path), map_location="cpu", weights_only=False)
    if str(ckpt.get("format", "")) != "causal_monitor_v1":
        raise ValueError(f"unexpected checkpoint format {ckpt.get('format')!r} in {pt_path.name}")

    cfg = dict(ckpt["config"])
    family = str(sidecar.get("family") or ckpt.get("model_id") or stem.replace("_main", ""))

    # Architecture keys fall back to the monitor DEFAULT_CONFIGS when the saved
    # config lacks them (build_model fills from defaults for missing keys).
    arch_cfg = {k: cfg[k] for k in ("d_model", "n_layers", "d_ff", "n_heads", "dropout") if k in cfg}
    torch_model = build_model(family, d_in=int(cfg["d_in"]), n_out=int(cfg["n_out"]), cfg=arch_cfg)
    torch_model.load_state_dict(ckpt["state_dict"])
    torch_model.eval()
    use_doy = bool(cfg.get("use_doy", sidecar.get("use_doy_channels", True)))

    # Normalization lives INSIDE the loaded object (sidecar median/scale).
    norm_block = sidecar.get("normalization") or {}
    if "median" not in norm_block or "scale" not in norm_block:
        raise ValueError(f"sidecar {sidecar_path.name} lacks normalization median/scale")
    norm = {
        "median": np.asarray(norm_block["median"], dtype=np.float64),
        "scale": np.asarray(norm_block["scale"], dtype=np.float64),
        "robust_range": np.asarray(norm_block.get("robust_range", np.ones(8)), dtype=np.float64),
    }

    scorer = DeepCausalScorer(family, torch_model, use_doy=use_doy, device="cpu")
    torch.set_num_threads(1)
    return LoadedCausalModel(
        model_id=stem, score_key=score_key, checkpoint_path=pt_path,
        sidecar_path=sidecar_path, sidecar=sidecar, family=family,
        use_doy=use_doy, _scorer=scorer, _norm=norm,
    )


def discover_checkpoints(ckpt_dir: Path | str | None = None) -> dict[str, Optional[Path]]:
    """Map each registered model id to its artifact (or None).

    A causal main stem requires BOTH ``<stem>.pt`` and the ``<stem>.json``
    sidecar (normalization + threshold live there); either missing -> None.
    """
    base = Path(ckpt_dir) if ckpt_dir is not None else DEFAULT_CHECKPOINT_DIR
    found: dict[str, Optional[Path]] = {}
    for model_id, stem in SCORE_CHECKPOINTS.items():
        pt_path = base / f"{stem}.pt"
        if not pt_path.exists():
            found[model_id] = None
        elif is_causal_stem(stem):
            sidecar_path = base / f"{stem}.json"
            found[model_id] = pt_path if sidecar_path.exists() else None
            if not sidecar_path.exists():
                log.warning(
                    "Checkpoint %s.pt has no %s sidecar (normalization/threshold live there); "
                    "slot %s stays absent", stem, sidecar_path.name, model_id,
                )
        else:
            found[model_id] = pt_path
    return found


def load_model_checkpoints(
    ckpt_dir: Path | str | None = None,
    model_ids: tuple[str, ...] | None = None,
) -> tuple[dict[str, Optional[object]], dict[str, str]]:
    """Load every discoverable checkpoint.

    Returns ``(models, status)`` where ``models[model_id]`` is a
    :class:`LoadedModel` (legacy) or :class:`LoadedCausalModel` (v5 causal main)
    or ``None``, and ``status[model_id]`` is one of ``"loaded"`` | ``"missing"``
    | ``"failed"``. A missing/failed checkpoint degrades to provenance
    ``"absent"`` downstream — it NEVER falls back to a proxy formula (v5) and
    NEVER crashes the exporter.
    """
    wanted = tuple(model_ids) if model_ids is not None else tuple(SCORE_CHECKPOINTS)
    discovered = discover_checkpoints(ckpt_dir)
    models: dict[str, Optional[object]] = {}
    status: dict[str, str] = {}
    for model_id in wanted:
        path = discovered.get(model_id)
        if path is None:
            models[model_id] = None
            status[model_id] = "missing"
            log.warning(
                "No checkpoint (pt + sidecar) for %s under %s (slot stays absent)",
                model_id, Path(ckpt_dir) if ckpt_dir is not None else DEFAULT_CHECKPOINT_DIR,
            )
            continue
        try:
            stem = SCORE_CHECKPOINTS[model_id]
            if is_causal_stem(stem):
                models[model_id] = _load_causal_one(
                    model_id, stem, path, Path(path).with_suffix(".json"),
                )
            else:
                models[model_id] = _load_one(model_id, path)
            status[model_id] = "loaded"
            loaded = models[model_id]
            log.info(
                "Loaded %s (%s, %d params) from %s",
                model_id, getattr(loaded, "family", getattr(loaded, "architecture", "?")),
                loaded.parameter_count, path,
            )
        except Exception as exc:  # noqa: BLE001 - any load failure must degrade gracefully
            models[model_id] = None
            status[model_id] = "failed"
            log.error("Checkpoint for %s could not be reconstructed from %s: %s", model_id, path, exc)
    return models, status


__all__ = [
    "LoadedModel", "LoadedCausalModel", "DEFAULT_CHECKPOINT_DIR", "CAUSAL", "BATCH_SIZE",
    "CAUSAL_MODEL_STEMS", "discover_checkpoints", "load_model_checkpoints", "squash_bin_error",
    "model_formula_id", "causal_formula_id", "score_formula_id", "is_causal_stem",
]
