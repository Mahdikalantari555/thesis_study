"""Shared development-protocol helpers for the monitor scripts.

- ``load_protocol``: loads the locked split manifest (hash-verified), the
  masked cycle tensors, and slices ONLY the requested splits into memory
  (test isolation: requesting ``test`` without ``allow_test`` raises and
  names the allowed entry point).
- ``seed_everything``: deterministic seeding + cudnn/determinism flags
  (recorded in the run manifest, ML-hardening task 10.2).
- ``append_dev_log`` / ``DEV_LOG_COLUMNS``: the experiment-log schema
  (task 5b.6, validated in unit tests).
- ``config_hash``: stable hash of a run configuration.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import subprocess
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORTS_DIR = REPO_ROOT / "reports"
DEV_LOG_PATH = REPORTS_DIR / "dev_log.csv"
DEV_DIR = REPORTS_DIR / "dev"
CHECKPOINTS_DEV_DIR = REPO_ROOT / "checkpoints" / "dev"

SPLIT_NAMES = ("train", "dev", "test", "monitoring_only")

DEV_LOG_COLUMNS: tuple[str, ...] = (
    "run_id", "date", "model_id", "parent_run_id", "change_description",
    "config_hash", "seeds", "n_train_cycles", "n_dev_cycles",
    "primary_metric_mean", "primary_metric_std", "median_delay_days",
    "far_target", "far_achieved", "tau", "k",
    "aucpr_25", "aucpr_50", "aucpr_75",
    "nrmse_mean", "severity_0p5", "severity_1p5", "severity_2",
    "params", "wall_time_s", "device", "git_sha", "data_source",
    "splits_sha256", "ladder_rung",
    # Severity protocol (change literature-grounded-severity-protocol, task 2.3):
    # protocol/scorer identity, the verified-table hash, the independent
    # evaluation-subset hash and the MDM80 labels (JSON per family × index).
    "protocol", "scorer", "severity_table_sha256", "eval_subset_sha256", "mdm80",
    "notes",
)


def git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            return out.stdout.strip()[:8]
    except Exception:
        pass
    return "unknown"


def config_hash(cfg: dict) -> str:
    payload = json.dumps(cfg, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def seed_everything(seed: int) -> dict:
    """Seed python/numpy/torch; enable deterministic algorithms where supported.

    Returns the determinism flags for the run manifest.
    """
    random.seed(seed)
    np.random.seed(seed % (2**32 - 1))
    import torch

    torch.manual_seed(seed)
    flags = {
        "torch_num_threads": torch.get_num_threads(),
        "cudnn_deterministic": False,
        "cudnn_benchmark": False,
        "deterministic_algorithms": False,
    }
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        import torch.backends.cudnn as cudnn

        cudnn.deterministic = True
        cudnn.benchmark = False
        flags["cudnn_deterministic"] = True
    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
        flags["deterministic_algorithms"] = True
    except Exception:
        pass
    return flags


def select_splits(data: dict, manifest: dict, splits: tuple[str, ...], *, allow_test: bool = False) -> dict:
    """Slice the masked-cycle archive to the requested splits.

    Test isolation: ``test`` may only be requested with ``allow_test=True``
    (reserved for scripts/freeze_main_model.py --final-test). The archive is a
    single-file NPZ, so the full file is opened by the loader, but no test
    cycle row is accessed or used by any training/evaluation path.
    """
    from ssl_anomaly.monitor.splits import assert_no_test_cycles

    if "test" in splits and not allow_test:
        raise RuntimeError(
            "select_splits: split 'test' requested without allow_test. Test cycles may only "
            "be read by scripts/freeze_main_model.py --final-test."
        )
    key_to_idx = {k: i for i, k in enumerate(data["cycle_keys"])}
    idx: list[int] = []
    selected_keys: list[str] = []
    for name in splits:
        wanted = set(manifest["cycles"].get(name, []))
        for k in data["cycle_keys"]:
            if k in wanted:
                idx.append(key_to_idx[k])
                selected_keys.append(k)
    # Guard: none of the selected keys may be a test cycle outside allow_test.
    if not allow_test:
        assert_no_test_cycles(selected_keys, manifest, context=f"select_splits({splits})")
    idx_arr = np.array(sorted(set(idx)), dtype=np.int64)
    out = dict(data)
    out["X"] = data["X"][idx_arr]
    out["M"] = data["M"][idx_arr]
    out["field_ids"] = data["field_ids"][idx_arr]
    out["start_dates"] = data["start_dates"][idx_arr]
    out["end_dates"] = data["end_dates"][idx_arr]
    out["harvest_days"] = data["harvest_days"][idx_arr]
    out["cycle_keys"] = [data["cycle_keys"][i] for i in idx_arr]
    out["splits_requested"] = list(splits)
    return out


def append_dev_log(row: dict, *, path: Path = DEV_LOG_PATH) -> None:
    """Append one run row to reports/dev_log.csv (creating it with the schema)."""
    missing = [c for c in DEV_LOG_COLUMNS if c not in row]
    if missing:
        raise ValueError(f"dev_log row missing columns: {missing}")
    extra = [k for k in row if k not in DEV_LOG_COLUMNS]
    if extra:
        raise ValueError(f"dev_log row has unknown columns: {extra}")
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(DEV_LOG_COLUMNS))
        if is_new:
            w.writeheader()
        w.writerow({c: row[c] for c in DEV_LOG_COLUMNS})


def read_dev_log(*, path: Path = DEV_LOG_PATH) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def mean_std(values: list[float]) -> tuple[float, float]:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        raise ValueError("mean_std of empty list")
    if arr.size == 1:
        return float(arr.mean()), 0.0
    return float(arr.mean()), float(arr.std(ddof=1))
