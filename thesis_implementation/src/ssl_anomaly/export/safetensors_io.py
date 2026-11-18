"""SafeTensors export/load for release artifacts (no pickle).

An exported release directory contains:
  model.safetensors    — state_dict (FP32)
  model_config.json    — architecture + hyperparameters
  norm_stats.json      — band order, robust center/scale, training meta
  meta.json            — git SHA, lock hash, seed, splits path, version
"""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

log = logging.getLogger("ssl_anomaly.export")


def _git_sha() -> str | None:
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        return sha or None
    except Exception:
        return None


def _lock_hash(lock_file: str | Path = "uv.lock") -> str | None:
    import hashlib

    p = Path(lock_file)
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def export_release(
    model: Any,
    model_config: dict,
    norm_stats: dict,
    out_dir: str | Path,
    *,
    splits_path: str | Path | None = None,
    seed: int | None = None,
) -> Path:
    """Export a PyTorch model as SafeTensors alongside config & norm stats.

    ``model`` must expose a ``state_dict()`` method (e.g., a Lightning module's
    underlying .model, or a plain nn.Module).
    """
    import torch
    from safetensors.torch import save_file

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Get plain nn.Module if given a Lightning wrapper
    raw = model
    while hasattr(raw, "model") and not isinstance(raw, torch.nn.Module):
        raw = raw.model
    if hasattr(model, "model") and isinstance(model.model, torch.nn.Module):
        raw = model.model

    state_dict = {
        k: v.detach().cpu().contiguous() for k, v in raw.state_dict().items()
    }
    save_file(state_dict, str(out_dir / "model.safetensors"))

    (out_dir / "model_config.json").write_text(json.dumps(model_config, indent=2, default=str))
    (out_dir / "norm_stats.json").write_text(_json_dump(norm_stats))

    meta = {
        "exported_at": datetime.now(UTC).isoformat(),
        "git_sha": _git_sha(),
        "uv_lock_hash": _lock_hash(),
        "seed": seed,
        "splits_path": str(splits_path) if splits_path else None,
        "format": "safetensors",
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, default=str))
    log.info("Exported model release to %s", out_dir)
    return out_dir


def load_release(build_model_fn, out_dir: str | Path, device: str = "cpu"):
    """Load a release directory: build model from config, load SafeTensors weights.

    ``build_model_fn(model_config) -> nn.Module`` is caller-provided so we
    don't need to hard-code class names. Returns (model, norm_stats, meta).
    """
    from safetensors.torch import load_file

    out_dir = Path(out_dir)
    if not (out_dir / "model.safetensors").exists():
        raise FileNotFoundError(f"model.safetensors not found in {out_dir}")
    if not (out_dir / "norm_stats.json").exists():
        raise FileNotFoundError(f"norm_stats.json required but missing in {out_dir}")
    cfg = json.loads((out_dir / "model_config.json").read_text())
    norm_stats = json.loads((out_dir / "norm_stats.json").read_text())
    meta = json.loads((out_dir / "meta.json").read_text()) if (out_dir / "meta.json").exists() else {}
    model = build_model_fn(cfg)
    state = load_file(str(out_dir / "model.safetensors"))
    model.load_state_dict(state)
    model.to(device).eval()
    return model, norm_stats, meta


def _json_dump(obj: Any) -> str:
    """JSON dump that tolerates numpy scalars/arrays."""

    def default(o: Any) -> Any:
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        if isinstance(o, Path):
            return str(o)
        raise TypeError(f"Object of type {type(o)} not JSON serializable")

    return json.dumps(obj, indent=2, default=default)
