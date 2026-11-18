"""Pre-registered run plan + benchmark manifests for the full-run change.

Change ``patch-full-run-and-ablations`` tasks 1.1 and 1.2.

Two artifacts, both written BEFORE the first launch:

* **The run plan** (:func:`build_run_plan`) — every planned run with its
  factor, seeds, venue, estimate and output path, plus the PRUNING RULE
  written into the file (single-seed screening → 3 seeds for finalists). The
  plan is hash-recorded, so "we always intended to run these 34 cells" is a
  file on disk rather than a recollection.
* **The benchmark block** (:func:`benchmark_block`) — psutil RAM, CUDA VRAM,
  parameter count, MACs and per-field-cycle inference time, with the AGENTS.md
  §7 completeness rules encoded as :func:`validate_manifest`. A manifest that
  lacks a benchmarking field fails validation instead of being reported with a
  blank column.

``psutil`` is imported lazily: the module must be importable (and its validation
logic testable) on a machine without it, and a missing psutil must produce a
``None`` with a reason, never a fabricated zero.
"""

from __future__ import annotations

import hashlib
import json
import platform
import time
from datetime import UTC, datetime
from pathlib import Path

# AGENTS.md §7 report fields — the minimum a run manifest must carry. These
# are the keys ``scripts/train_patch.py`` actually writes (one run directory per
# seed, so provenance is ``seed`` plus the config/holdout/norm hashes).
REQUIRED_MANIFEST_FIELDS: tuple[str, ...] = (
    "arch", "seed", "n_parameters", "wall_time_s", "device", "git_sha",
    "data_source", "holdout_sha256", "norm_sha256", "config_hash",
)

# The benchmarking block (task 1.2). Distinguishes "measured" from "absent".
BENCHMARK_FIELDS: tuple[str, ...] = (
    "peak_ram_mb", "cuda_peak_mb", "n_parameters", "macs_per_forward",
    "ms_per_field_cycle", "device", "torch_version", "recorded_at",
)

PRUNING_RULE = (
    "Screening: every planned cell, ONE seed (13). Only cells that clear the "
    "screening criterion advance to the final stage; finalists run seeds "
    "{13, 42, 2026}. No cell is promoted after seeing its final-stage numbers, "
    "and every pruning decision is appended to reports/dev_log.csv with the "
    "screening value that justified it."
)

SCREENING_SEED = 13
FINAL_SEEDS = (13, 42, 2026)


# ---------------------------------------------------------------------------
# 1.1 The run plan
# ---------------------------------------------------------------------------
def _cell(run_id: str, factor: str, *, level: str, seeds, venue: str,
          estimate_s: float, out: str, notes: str = "") -> dict:
    return {
        "run_id": run_id, "factor": factor, "level": level,
        "seeds": list(seeds), "venue": venue,
        "estimate_seconds": float(estimate_s), "outputs": out, "notes": notes,
        "stage": "screening" if list(seeds) == [SCREENING_SEED] else "final",
    }


def build_run_plan(
    *,
    seconds_per_epoch: float,
    epochs: int,
    seconds_per_eval: float,
    patch_model: str = "patch_cnn_gru",
    include_tcn: bool = False,
) -> dict:
    """Every planned run, with cost, before anything is launched.

    The factor axes are the change's ablations (E2 aux weight, E6 LST-off, E4
    covariate ladder incl. the ratoon/variety stratum, E5 inner-buffer/burn-in,
    the sensor-offset comparison, and the SSL-off control). ``include_tcn`` is
    OFF by default: the TCN challenger is built only if the E3 trigger fires,
    and a plan that pre-allocates its runs would quietly make that decision for
    the owner.
    """
    train_s = seconds_per_epoch * max(1, int(epochs))
    run_s = train_s + seconds_per_eval

    cells: list[dict] = []
    # Screening: one seed per cell; finalists are named in the pruning rule.
    cells.append(_cell("scaleup_all_train", "scale_up", level="all train fields",
                       seeds=(SCREENING_SEED,), venue="owner GPU",
                       estimate_s=run_s * 1.6,
                       out=f"checkpoints/patch/{patch_model}_seed13",
                       notes="winning PoC config on all train fields"))
    cells.append(_cell("E2_aux_0.0", "aux_weight", level="0.0", seeds=(SCREENING_SEED,),
                       venue="owner GPU", estimate_s=run_s,
                       out="checkpoints/patch/E2_aux_0.0"))
    cells.append(_cell("E2_aux_0.3", "aux_weight", level="0.3 (default)",
                       seeds=(SCREENING_SEED,), venue="owner GPU", estimate_s=run_s,
                       out="checkpoints/patch/E2_aux_0.3"))
    cells.append(_cell("E6_lst_off", "channels", level="no LST", seeds=(SCREENING_SEED,),
                       venue="owner GPU", estimate_s=run_s,
                       out="checkpoints/patch/E6_lst_off",
                       notes="feeds patch-independent-indicators (LST-on/off axis)"))
    for lvl in ("none", "+day-metadata", "+ratoon/variety stratum", "+weather last"):
        key = lvl.replace(" ", "_").replace("/", "_")
        cells.append(_cell(f"E4_{key}", "covariates", level=lvl,
                           seeds=(SCREENING_SEED,), venue="owner GPU",
                           estimate_s=run_s, out=f"checkpoints/patch/E4_{key}",
                           notes="conditioned AND unconditioned reported"))
    for lvl in ("no inner buffer", "burn-in 4", "burn-in 8 (default)"):
        key = lvl.replace(" ", "_")
        cells.append(_cell(f"E5_{key}", "inner_buffer/burn_in", level=lvl,
                           seeds=(SCREENING_SEED,), venue="owner GPU",
                           estimate_s=run_s, out=f"checkpoints/patch/E5_{key}"))
    cells.append(_cell("sensor_offset_compare", "sensor_offset",
                       level="applied vs not", seeds=(SCREENING_SEED,),
                       venue="owner GPU", estimate_s=run_s * 2,
                       out="reports/sensor_offset",
                       notes="near-coincident L8/L9 pairs over the AOI"))
    cells.append(_cell("ssl_off_control", "ssl", level="random init, same scoring",
                       seeds=(SCREENING_SEED,), venue="owner GPU",
                       estimate_s=run_s, out="checkpoints/patch/ssl_off",
                       notes="fairness control: same architecture and scorer"))
    if include_tcn:
        cells.append(_cell("E3_tcn", "challenger", level="TCN", seeds=(SCREENING_SEED,),
                           venue="owner GPU", estimate_s=run_s,
                           out="checkpoints/patch/E3_tcn",
                           notes="only if the E3 trigger fired"))

    screen_s = sum(c["estimate_seconds"] for c in cells)
    # Finalists: name them now, not later. Three cells are pre-named as the
    # likely finalists; promoting a different cell is a plan AMENDMENT that
    # must be recorded, which is the point of pre-registration.
    finalists = ["scaleup_all_train", "E2_aux_0.3", "ssl_off_control"]
    final_s = len(finalists) * len(FINAL_SEEDS) * run_s
    plan = {
        "protocol": "patch_full_run_plan_v1",
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "cell_count": len(cells),
        "cells": cells,
        "pruning_rule": PRUNING_RULE,
        "screening_seed": SCREENING_SEED,
        "final_seeds": list(FINAL_SEEDS),
        "pre_named_finalists": finalists,
        "include_tcn": bool(include_tcn),
        "estimate": {
            "seconds_per_training_run": round(run_s, 1),
            "screening_seconds": round(screen_s, 1),
            "final_seconds": round(final_s, 1),
            "total_hours": round((screen_s + final_s) / 3600.0, 2),
        },
        "assumptions": {
            "seconds_per_epoch": float(seconds_per_epoch), "epochs": int(epochs),
            "seconds_per_eval": float(seconds_per_eval),
        },
    }
    plan["sha256"] = plan_sha256(plan)
    return plan


def plan_sha256(plan: dict) -> str:
    payload = {k: v for k, v in plan.items() if k != "sha256"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def save_plan(plan: dict, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return p


def load_plan(path: str | Path, *, verify: bool = True) -> dict:
    p = Path(path)
    plan = json.loads(p.read_text(encoding="utf-8"))
    if verify:
        recorded = plan.get("sha256")
        if not recorded:
            raise ValueError(f"{p}: run plan has no sha256 — it was not pre-registered")
        if plan_sha256(plan) != recorded:
            raise ValueError(
                f"{p}: run plan hash mismatch — the plan was edited after "
                "registration; re-register explicitly instead of editing in place"
            )
    return plan


def amendment(plan: dict, *, run_id: str, reason: str, approved_by: str) -> dict:
    """Record a change to a registered plan (the only allowed way to change it)."""
    if not reason or not approved_by:
        raise ValueError("an amendment needs a reason and an approver")
    out = json.loads(json.dumps(plan))
    out.setdefault("amendments", []).append({
        "run_id": run_id, "reason": reason, "approved_by": approved_by,
        "at": datetime.now(UTC).isoformat(timespec="seconds"),
        "previous_sha256": plan.get("sha256"),
    })
    out["sha256"] = plan_sha256(out)
    return out


# ---------------------------------------------------------------------------
# 1.2 Benchmarking
# ---------------------------------------------------------------------------
def peak_ram_mb() -> float | None:
    """Peak RSS of this process in MB, or ``None`` with no psutil available."""
    try:
        import psutil
    except ImportError:
        return None
    return round(psutil.Process().memory_info().rss / (1024 * 1024), 1)


def cuda_peak_mb() -> float | None:
    """CUDA peak allocated memory, or ``None`` on a CPU-only host."""
    try:
        import torch
    except ImportError:                     # pragma: no cover - torch is required
        return None
    if not torch.cuda.is_available():
        return None
    return round(torch.cuda.max_memory_allocated() / (1024 * 1024), 1)


def count_macs(model, example_input, *, module_types=None) -> int | None:
    """Multiply-accumulates of one forward pass.

    Counts Conv2d and Linear flops from the module shapes and the example
    activation size. It is an ESTIMATE of dense MACs (mask-agnostic, no
    activation sparsity) and says so — a mask-aware count would make the
    number depend on the data and therefore not comparable across runs.
    """
    import torch
    import torch.nn as nn

    macs = 0
    hooks = []

    def conv_hook(mod, inp, out):
        nonlocal macs
        kh, kw = mod.kernel_size if isinstance(mod.kernel_size, tuple) else (mod.kernel_size,) * 2
        out_elems = out.shape[0] * out.shape[2] * out.shape[3]
        macs += int(out_elems * mod.in_channels * kh * kw / mod.groups)

    def linear_hook(mod, inp, out):
        nonlocal macs
        macs += int(out.numel() * mod.in_features)

    for m in model.modules():
        if isinstance(m, nn.Conv2d):
            hooks.append(m.register_forward_hook(conv_hook))
        elif isinstance(m, nn.Linear):
            hooks.append(m.register_forward_hook(linear_hook))
    was_training = model.training
    model.eval()
    with torch.no_grad():
        try:
            model(*example_input) if isinstance(example_input, tuple) else model(example_input)
        except Exception:
            for h in hooks:
                h.remove()
            model.train(was_training)
            return None                    # shape mismatch: report absent, not a guess
    for h in hooks:
        h.remove()
    model.train(was_training)
    return int(macs)


def time_inference(model, example_input, *, repeats: int = 3) -> float | None:
    """Milliseconds per forward pass (median of ``repeats``), or None."""
    try:
        import torch
    except ImportError:                     # pragma: no cover
        return None
    was_training = model.training
    model.eval()
    times = []
    with torch.no_grad():
        try:
            for _ in range(max(1, repeats)):
                t0 = time.perf_counter()
                model(*example_input) if isinstance(example_input, tuple) else model(example_input)
                times.append((time.perf_counter() - t0) * 1000.0)
        except Exception:
            model.train(was_training)
            return None
    model.train(was_training)
    return round(float(sorted(times)[len(times) // 2]), 3)


def benchmark_block(
    model=None,
    example_input=None,
    *,
    per_field_cycle_ms: float | None = None,
    macs: int | None = None,
) -> dict:
    """The benchmarking block for a manifest (task 1.2).

    Every field is either MEASURED or explicitly ``None``; a missing
    measurement is never zero, because a zero MACs figure would silently win
    every efficiency comparison.
    """
    block = {
        "peak_ram_mb": peak_ram_mb(),
        "cuda_peak_mb": cuda_peak_mb(),
        "n_parameters": None,
        "macs_per_forward": macs,
        "ms_per_field_cycle": per_field_cycle_ms,
        "device": None,
        "torch_version": None,
        "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    try:
        import torch

        block["torch_version"] = torch.__version__
        block["device"] = "cuda" if torch.cuda.is_available() else "cpu"
        if model is not None:
            block["n_parameters"] = int(sum(p.numel() for p in model.parameters()
                                            if p.requires_grad))
            if example_input is not None and macs is None:
                block["macs_per_forward"] = count_macs(model, example_input)
            if example_input is not None and per_field_cycle_ms is None:
                block["ms_per_field_cycle"] = time_inference(model, example_input)
    except ImportError:                     # pragma: no cover
        pass
    return block


def validate_manifest(manifest: dict, *, require_benchmark: bool = True) -> list[str]:
    """AGENTS.md §7 completeness check; returns the missing fields.

    ``require_benchmark`` defaults to True for the full-run manifests this
    change produces. The older dev manifests predate the block, so a caller
    validating them can pass False and still get the core-field check.
    """
    # "seeds" (plural) is the plan-level spelling; a manifest may use either.
    def _present(field: str) -> bool:
        if field == "seed":
            v = manifest.get("seed", manifest.get("seeds"))
        else:
            v = manifest.get(field)
        return v not in (None, "", [], {})

    missing = [f for f in REQUIRED_MANIFEST_FIELDS if not _present(f)]
    if require_benchmark:
        bench = manifest.get("benchmark") or {}
        # A measured value may legitimately be None (no CUDA); what is NOT
        # acceptable is the block being absent, or a field never recorded.
        missing += [f"benchmark.{f}" for f in BENCHMARK_FIELDS if f not in bench]
    return missing


def attach_benchmark(manifest: dict, block: dict, *, strict: bool = True) -> dict:
    """Add the benchmarking block, validating the completed manifest."""
    out = dict(manifest)
    out["benchmark"] = dict(block)
    missing = validate_manifest(out)
    if missing and strict:
        raise ValueError(f"manifest incomplete after attaching the benchmark: {missing}")
    return out


__all__ = [
    "BENCHMARK_FIELDS", "FINAL_SEEDS", "PRUNING_RULE", "REQUIRED_MANIFEST_FIELDS",
    "SCREENING_SEED", "amendment", "attach_benchmark", "benchmark_block",
    "build_run_plan", "count_macs", "cuda_peak_mb", "load_plan", "peak_ram_mb",
    "plan_sha256", "save_plan", "time_inference", "validate_manifest",
]
