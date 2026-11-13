"""Train STS-Net, Tiny-CNN-Mamba, and Time2Agri on the train partition of growth_cycles_490.npz.

Saves checkpoints under checkpoints/:
  - checkpoints/sts_net_490.pt
  - checkpoints/tiny_cnn_mamba_490.pt
  - checkpoints/time2agri_490.pt
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import torch

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from ssl_anomaly.eval.growth_ssl import MaskedSSL
from ssl_anomaly.eval.growth_validation import temporal_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("train_literature_checkpoints")


def main() -> None:
    data_path = ROOT_DIR / "data/interim/growth_cycles_490.npz"
    ckpt_dir = ROOT_DIR / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    log.info("Loading %s", data_path)
    data = np.load(data_path)
    X = data["X"]  # (799, 36, 8)
    starts = data["start_dates"]
    ends = data["end_dates"]
    fids = data["field_ids"]

    # Spatial holdouts (e.g. block R04/L08 fields or arbitrary 20 fields)
    holdout_fields = [str(x) for x in range(1, 21)]
    split = temporal_split(
        starts,
        ends,
        fids,
        train_end="2021-12-31",
        val_end="2023-12-31",
        test_end="2026-12-31",
        holdout_fields=holdout_fields,
    )

    train_mask = split["train"]
    log.info(
        "Split counts: train=%d, val=%d, temporal_test=%d, spatial_test=%d",
        train_mask.sum(),
        split["validation"].sum(),
        split["temporal_test"].sum(),
        split["spatial_test"].sum(),
    )

    X_train = X[train_mask]

    models_to_train = [
        ("sts_net", "sts_net_490.pt"),
        ("tiny_cnn_mamba", "tiny_cnn_mamba_490.pt"),
        ("time2agri", "time2agri_490.pt"),
    ]

    for arch, fname in models_to_train:
        out_path = ckpt_dir / fname
        if out_path.exists():
            log.info("Checkpoint %s already exists, skipping...", out_path)
            continue
        log.info("Training %s for 15 epochs on %d train cycles...", arch, len(X_train))
        ssl_wrapper = MaskedSSL(
            architecture=arch,
            epochs=15,
            seed=42,
            batch_size=32,
            causal=True,
            train_enabled=True,
        )
        ssl_wrapper.fit(X_train)

        out_path = ckpt_dir / fname
        torch.save(
            {
                "architecture": arch,
                "state_dict": ssl_wrapper.model.state_dict(),
                "center": ssl_wrapper.center,
                "scale": ssl_wrapper.scale,
                "shape": ssl_wrapper.shape,
                "n_bands": ssl_wrapper.n_bands,
                "parameter_count": ssl_wrapper.parameter_count,
            },
            out_path,
        )
        log.info("Saved %s checkpoint to %s (params: %d)", arch, out_path, ssl_wrapper.parameter_count)

    log.info("All literature model checkpoints saved successfully.")


if __name__ == "__main__":
    main()
