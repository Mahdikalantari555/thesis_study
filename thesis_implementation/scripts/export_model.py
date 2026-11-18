#!/usr/bin/env python3
"""Export a Lightning checkpoint to a SafeTensors release."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ssl_anomaly.config import default_config
from ssl_anomaly.export import export_release
from ssl_anomaly.train.lit_module import SSLLitModule
from ssl_anomaly.utils.logging import get_logger
from ssl_anomaly.utils.throttle import limit_threads

log = get_logger("ssl_anomaly.scripts.export")


def main() -> int:
    limit_threads(2)
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--model", default="transformer", choices=["gru_ae", "transformer"])
    p.add_argument("--d-in", type=int, default=None, help="Override token feature dim")
    args = p.parse_args()

    cfg = default_config()
    cfg.ssl.model = args.model
    d_in = args.d_in or 12  # default feature dim for synthetic data
    module = SSLLitModule.load_from_checkpoint(str(args.ckpt), d_in=d_in, cfg=cfg.ssl)
    export_release(
        module,
        model_config={"model": args.model, "d_in": d_in},
        norm_stats={"band_names": [], "note": "placeholder"},
        out_dir=args.out, seed=cfg.train.seed,
    )
    log.info("Exported to %s", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
