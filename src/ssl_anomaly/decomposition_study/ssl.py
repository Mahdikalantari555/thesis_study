"""Budget-matched causal GRU; loss is masked per raw target channel."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from tqdm import trange

from ssl_anomaly.models.gru_ae import CausalGRUAE

HIDDEN = 24
BATCH = 32
BLOCK = 32
WARMUP = 8
CONTEXT_DROP = 0.15
LR = 0.0015


def tokens(values: np.ndarray, slots: np.ndarray, gaps: np.ndarray) -> np.ndarray:
    mask = np.isfinite(values) & slots
    timing = np.broadcast_to(np.minimum(gaps / 60, 2)[None, :, None], (*mask.shape[:2], 1))
    return np.concatenate(
        (np.where(mask, np.clip(values, -12, 12), 0), mask, timing), axis=-1, dtype=np.float32
    )


def _batches(
    n_fields: int,
    start: int,
    stop: int,
    rng: np.random.Generator | None = None,
) -> Iterator[tuple[np.ndarray, int, int, int]]:
    blocks = np.arange(start, stop, BLOCK)
    fields = np.arange(n_fields)
    if rng is not None:
        rng.shuffle(blocks)
        rng.shuffle(fields)
    for a in blocks:
        for i in range(0, n_fields, BATCH):
            yield fields[i : i + BATCH], max(0, int(a) - WARMUP), int(a), min(int(a) + BLOCK, stop)


def masked_loss(pred: torch.Tensor, actual: torch.Tensor) -> torch.Tensor:
    observed = torch.isfinite(actual)
    return F.smooth_l1_loss(pred[observed], actual[observed])


def _model(width: int, targets: int, seed: int, device: str) -> CausalGRUAE:
    torch.manual_seed(seed)
    return CausalGRUAE(2 * width + 1, targets, d_model=HIDDEN, n_layers=1).to(device)


def train_model(
    features: np.ndarray,
    slots: np.ndarray,
    gaps: np.ndarray,
    target: np.ndarray,
    train_end: int,
    seed: int,
    epochs: int,
    device: str,
    checkpoint: Path,
    progress: Callable[..., None],
    *,
    show_progress: bool,
) -> tuple[CausalGRUAE, CausalGRUAE, dict]:
    width = features.shape[-1]
    random_model = _model(width, target.shape[-1], seed, device)
    model = _model(width, target.shape[-1], seed, device)
    opt = torch.optim.AdamW(model.parameters(), lr=LR)
    # No scheduler and no stochastic GPU ops in the forward pass. The seeded
    # NumPy stream is reconstructed from (seed, epoch) for every context draw.
    losses: list[float] = []
    elapsed = 0.0
    if checkpoint.exists():
        state = torch.load(checkpoint, map_location="cpu", weights_only=True)
        model.load_state_dict(state["model"])
        opt.load_state_dict(state["optimizer"])
        torch.set_rng_state(state["rng_cpu"])
        if device == "cuda":
            torch.cuda.set_rng_state_all(state["rng_cuda"])
        losses = state["losses"]
        elapsed = state["wall_seconds"]
    start = time.perf_counter()
    wall = elapsed
    initial_epoch = len(losses)
    bar = trange(
        initial_epoch,
        epochs,
        initial=initial_epoch,
        total=epochs,
        disable=not show_progress,
        desc=checkpoint.stem,
        leave=False,
    )
    for epoch in bar:
        model.train()
        rng = np.random.default_rng(np.random.SeedSequence([seed, epoch]))
        total, n = 0.0, 0
        for fields, lo, a, b in _batches(len(features), 0, train_end, rng):
            y = target[fields, a:b]
            count = int(np.isfinite(y).sum())
            if not count:
                continue
            x = tokens(features[fields, lo:b], slots, gaps[lo:b])
            drop = rng.random(x.shape[:2]) < CONTEXT_DROP
            x[..., :-1][drop] = 0  # preserve elapsed days; never change the target mask
            inp = torch.as_tensor(x, device=device)
            actual = torch.as_tensor(y, device=device)
            opt.zero_grad(set_to_none=True)
            loss = masked_loss(model(inp)[:, a - lo :], actual)
            if not torch.isfinite(loss):
                raise RuntimeError(f"Non-finite training loss at epoch {epoch + 1}")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
            opt.step()
            total += float(loss.detach()) * count
            n += count
        if not n:
            raise ValueError("No common observed training targets; inspect benchmark coverage")
        losses.append(total / n)
        wall = elapsed + time.perf_counter() - start
        eta = (time.perf_counter() - start) / (epoch + 1 - initial_epoch) * (epochs - epoch - 1)
        bar.set_postfix(loss=f"{losses[-1]:.4f}")
        pending = checkpoint.with_suffix(".tmp")
        torch.save(
            {
                "model": model.state_dict(),
                "optimizer": opt.state_dict(),
                "rng_cpu": torch.get_rng_state(),
                "rng_cuda": torch.cuda.get_rng_state_all() if device == "cuda" else [],
                "losses": losses,
                "wall_seconds": wall,
            },
            pending,
        )
        pending.replace(checkpoint)
        progress(
            event="epoch",
            epoch=epoch + 1,
            epochs=epochs,
            loss=losses[-1],
            eta_seconds=eta,
            target_cells=n,
        )
    return (
        model.eval(),
        random_model.eval(),
        {
            "parameters": sum(p.numel() for p in model.parameters()),
            "train_loss_by_epoch": losses,
            "train_seconds": wall,
            "checkpoint": checkpoint.name,
        },
    )


@torch.no_grad()
def predict(
    model: CausalGRUAE,
    features: np.ndarray,
    slots: np.ndarray,
    gaps: np.ndarray,
    target: np.ndarray,
    start: int,
    stop: int,
    device: str,
) -> np.ndarray:
    err = np.full_like(target, np.nan)
    for fields, lo, a, b in _batches(len(features), start, stop):
        x = tokens(features[fields, lo:b], slots, gaps[lo:b])
        pred = model(torch.as_tensor(x, device=device))[:, a - lo :].cpu().numpy()
        if not np.isfinite(pred).all():
            raise RuntimeError("Non-finite model prediction; the matched cohort cannot be scored")
        err[fields, a:b] = (pred - target[fields, a:b]) ** 2
    return err
